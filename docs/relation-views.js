/* Source-backed graph + explicit relative-shock assumptions. No network or storage writes. */
(function(root){
 'use strict';
 const E=root.ResearchCharts.esc,N=root.AnalysisCharts.n,finite=v=>typeof v==='number'&&Number.isFinite(v),round=v=>Math.round(v*1e6)/1e6;
 const safe=u=>/^https?:\/\/[^\s]+$/i.test(u||'')?u:'#';
 const kinds={company:'기업',theme:'사업 테마',macro:'거시',commodity:'원자재',assumption:'가정 입력'};
 const colors={company:'#50a9cb',theme:'#c0a366',macro:'#a391ce',commodity:'#6db899',assumption:'#a2a7b2'};
 const transfer={'supplies':[.28,.72],'competes':[-.5,-.5],'part-of':[.42,.55],'exposed-to':[.5,.5],'powers':[.28,.62],'correlated':[.62,.62],'builds':[.22,.5],'hosts':[.58,.30],'pressures':[-.55,-.20],'drives':[.62,.30],'comention':[.45,.45],'collaborates':[.35,.35]};
 function adjacency(g,correlated=false){
  const adj=new Map(g.nodes.map(n=>[n.id,[]])),seen=new Set(),coeff=g.parameters?.transfer||transfer;
  if(adj.size!==g.nodes.length)throw Error('중복 객체');
  for(const e of [...g.links].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0)){
   const w=e.weight??1,pair=coeff[e.relation];
   if(seen.has(e.id)||!adj.has(e.source)||!adj.has(e.target)||e.source===e.target||!pair||!finite(w)||w<1||w>3)throw Error('잘못된 관계');
   seen.add(e.id);let sign=1;
   if(e.relation==='correlated'){if(!finite(e.corr)||Math.abs(e.corr)>1)throw Error('상관 관측 필요');if(!correlated)continue;sign=Math.sign(e.corr);}
   [[e.source,e.target,0],[e.target,e.source,1]].forEach(([from,to,side])=>adj.get(from).push({target:to,edge:e.id,relation:e.relation,coefficient:pair[side]*(.7+.1*w)*.9*sign}));
  }return adj;
 }
 function propagate(g,start,shock=1,hops=3,correlated=false){
  if(!finite(shock)||Math.abs(shock)>2||!Number.isInteger(hops)||hops<1||hops>3)throw Error('강도 ±2, 단계 1~3 범위');
  const adj=adjacency(g,correlated);if(!adj.has(start))throw Error('미연결 객체');
  const best={};let frontier=[{value:shock,path:[start],edges:[],relations:[]}];
  for(let hop=1;hop<=hops;hop++){const next=[];for(const prefix of frontier)for(const e of adj.get(prefix.path.at(-1))){
   if(prefix.path.includes(e.target))continue;const value=prefix.value*e.coefficient;if(Math.abs(value)<.03)continue;
   const r={value,hop,path:[...prefix.path,e.target],edges:[...prefix.edges,e.edge],relations:[...prefix.relations,e.relation]},old=best[e.target],tie=old&&Math.abs(Math.abs(value)-Math.abs(old.value))<=1e-12;
   if(!old||Math.abs(value)>Math.abs(old.value)+1e-12||tie&&(hop<old.hop||hop===old.hop&&r.edges.join('\u0001')<old.edges.join('\u0001')))best[e.target]=r;
   next.push(r);
  }frontier=next;}
  return Object.fromEntries(Object.keys(best).sort().map(id=>[id,{...best[id],value:round(best[id].value)}]));
 }
 function runScenario(g,seeds,hops=3,correlated=false){
  if(new Set(seeds.map(s=>s.id)).size!==seeds.length)throw Error('중복 일차 충격');const out={};
  for(const seed of seeds){const impacts=propagate(g,seed.id,seed.value,hops,correlated);impacts[seed.id]={value:seed.value,hop:0,path:[seed.id],edges:[],relations:[]};
   for(const [id,r] of Object.entries(impacts)){const v=out[id]??={value:0,seed:false,contributions:[]};v.value+=r.value;v.seed||=id===seed.id;v.contributions.push({...r,source:seed.id});}
  }
  for(const r of Object.values(out)){r.value=round(r.value);r.contributions.sort((a,b)=>Math.abs(b.value)-Math.abs(a.value)||a.hop-b.hop||(a.source<b.source?-1:a.source>b.source?1:0));const top=r.contributions[0];Object.assign(r,{path:top.path,edges:top.edges,hop:top.hop});}
  return Object.fromEntries(Object.keys(out).sort().map(id=>[id,out[id]]));
 }
 const matrices=new WeakMap();
 function decodeMatrix(p){
  if(matrices.has(p))return matrices.get(p);
  const bytes=s=>Uint8Array.from(root.atob(s),c=>c.charCodeAt(0)),raw=bytes(p.correlations),counts=bytes(p.counts),length=p.ids.length*(p.ids.length-1)/2;
  if(raw.length!==length*2||counts.length!==length||new Set(p.ids).size!==p.ids.length)throw Error('상관 행렬 형식 오류');
  const view=new DataView(raw.buffer),ids=new Map(p.ids.map((id,i)=>[id,i]));
  const get=(a,b)=>{let i=ids.get(a),j=ids.get(b);if(i===undefined||j===undefined)return {corr:null,observations:0};
   if(i===j)return {corr:p.diagonal_valid[i]&&p.diagonal[i]>=p.minimum?1:null,observations:p.diagonal[i]};
   if(i<j)[i,j]=[j,i];const k=i*(i-1)/2+j,v=view.getInt16(k*2,true),n=counts[k];return {corr:v===p.missing||n<p.minimum?null:v/p.scale,observations:n};};
  matrices.set(p,get);return get;
 }
 const active=entries=>entries.filter(r=>!r.deleted_at&&r.status==='실행');
 function portfolioImpact(entries,g,impacts){
  const ids=new Set(g.nodes.map(n=>n.id));let partial=0,unknown=0;const rows=active(entries).map(r=>{
   const sign=r.direction==='Long'?1:r.direction==='Short'?-1:null;let value=null,reason='';
   if(r.size===0){value=0;reason='0 비중';}
   else if(!finite(r.size)||sign===null)reason='비중·방향 미입력';
   else if(!ids.has(r.object_id))reason='관계망 미연결';
   else {value=sign*r.size/100*(impacts[r.object_id]?.value??0);reason=impacts[r.object_id]?'가정 경로 연결':'모형 경로 없음';}
   if(value===null)unknown++;else partial+=value;return {id:r.object_id,name:r.name,size:r.size,value,reason};
  });return {rows,unknown,partial,total:unknown?null:partial};
 }
 function crowding(entries,g){
  const ids=[...new Set(active(entries).filter(r=>r.direction==='Long'&&finite(r.size)&&r.size>0).map(r=>r.object_id))],pairs=[];
  const get=decodeMatrix(g.portfolio_correlations);let total=0;
  for(let i=0;i<ids.length;i++)for(let j=0;j<i;j++){total++;const r=get(ids[i],ids[j]);if(r.corr!==null)pairs.push({a:ids[i],b:ids[j],...r});}
  return {objects:ids.length,expected:total,available:pairs.length,mean:pairs.length?pairs.reduce((a,r)=>a+r.corr,0)/pairs.length:null,pairs:pairs.sort((a,b)=>b.corr-a.corr)};
 }
 const name=(g,id)=>g.nodes.find(n=>n.id===id)?.name||id;
 function edgeHTML(g,id){const e=g.links.find(r=>r.id===id);if(!e)return '';
  return `<li>${E(name(g,e.source))} → ${E(name(g,e.target))} · ${E(g.relation_labels[e.relation])}: ${E(e.basis)} ${e.url?`<a href="${E(safe(e.url))}" target="_blank" rel="noopener noreferrer">${E(e.evidence)} ↗</a>`:E(e.evidence)} · 확인 ${E(e.reviewed_at)}${finite(e.corr)?` · ρ ${N(e.corr)} (${e.correlation_observations??e.observations}개, ${E(e.correlation_start??e.start)} ~ ${E(e.correlation_end??e.end)})`:''}</li>`;
 }
 function paths(g,r){return `<details><summary>일차 충격별 영향 경로 ${r.contributions.length}개</summary>${r.contributions.map(c=>`<p>${N(c.value)} · ${c.hop}단계 · ${c.path.map(id=>E(name(g,id))).join(' → ')}</p><ul>${c.edges.map(id=>edgeHTML(g,id)).join('')||'<li>일차 가정 직접 입력</li>'}</ul>`).join('')}</details>`;}
 function rankings(g,impacts){
  const rows=Object.entries(impacts).filter(([id])=>g.nodes.find(n=>n.id===id)?.kind==='company').map(([id,r])=>({id,name:name(g,id),...r}));
  const side=sign=>rows.filter(r=>sign*r.value>=.06).sort((a,b)=>sign*(b.value-a.value)).slice(0,8);
  return `<p>기업 도달 범위 |강도|≥0.12: ${rows.filter(r=>Math.abs(r.value)>=.12).length}개 · 아래 순위 |강도|≥0.06, 방향별 최대8개</p><div class="relation-columns">${[1,-1].map(sign=>`<section><h3>${sign===1?'양의 가정 영향':'음의 가정 영향'}</h3>${root.ResearchCharts.bars(side(sign),{title:sign===1?'양의 영향':'음의 영향',unit:'상대 강도',valueUnit:'',digits:3})}${side(sign).map(r=>`<article class="relation-path"><strong>${E(r.name)} ${N(r.value)}</strong>${paths(g,r)}</article>`).join('')}</section>`).join('')}</div><details><summary>전체 객체의 전파 원장 (${Object.keys(impacts).length})</summary>${Object.entries(impacts).map(([id,r])=>`<div class="relation-path"><b>${E(name(g,id))} ${N(r.value)}</b>${paths(g,r)}</div>`).join('')}</details>`;
 }
 function decisionNotes(r,g){
  if(!g)return '';const sign=r.direction==='Long'?1:r.direction==='Short'?-1:null;
  if(!g.nodes.some(n=>n.id===r.object_id)||sign===null)return '<p class="quiet">관계 프리모템: 대상 관계 또는 방향이 없어 미산출.</p>';
  const list=g.scenarios.map(s=>({s,r:s.impacts[r.object_id],value:sign*(s.impacts[r.object_id]?.value??0)})).sort((a,b)=>a.value-b.value),worst=list[0];
  return `<details><summary>관계 프리모템 · ${E(worst.s.name)} ${N(worst.value)}</summary><p>8개 기본 가정 중 이 방향에 가장 불리한 상대 강도입니다. 손실률·발생확률 추정이 아닙니다. 경로가 없으면 모형 강도는0이며 위험이 없다는 뜻은 아닙니다.</p>${worst.r?paths(g,worst.r):'<p>3단계 내 모형 경로 없음.</p>'}</details>`;
 }
 function portfolioNotes(entries,g){
  if(!g)return '';let c;try{c=crowding(entries,g);}catch(e){return '<p>상관 행렬을 읽지 못했습니다. '+E(e.message)+'</p>';}
  const rows=g.scenarios.map(s=>({name:s.name,...portfolioImpact(entries,g,s.impacts)}));
  return `<section class="panel"><h3>결정 원장 · 관계 시나리오와 상관 집중</h3><p>실행 상태만 집계. 전체 비중·방향·관계가 확인되어야 전체 강도를 표시합니다. 0 비중은0이며 알려진 객체의 경로 없음과 미연결 객체를 구분합니다.</p><div class="table-scroll"><table class="data-table"><thead><tr><th>가정</th><th>전체 강도 × NAV비중</th><th>계산 가능한 부분합</th><th>미산출 기록</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${E(r.name)}</td><td>${N(r.total)}</td><td>${N(r.partial)}</td><td>${r.unknown}</td></tr>`).join('')}</tbody></table></div><p class="quiet">금액·% NAV 손익이 아닙니다. 기본3단계·상관 전파 제외. 현재 기록 비중을 사용하며 여러 기록을 순상계하지 않습니다.</p><h4>실행 Long 종목 간 관측 상관</h4><p>양의 비중 ${c.objects}종목 · 가용 쌍 ${c.available}/${c.expected} · 가용 쌍 단순평균 ${N(c.mean)}${c.available<c.expected?' · 일부 상관 결측':''}</p><p class="quiet">${E(g.portfolio_correlations.start)} ~ ${E(g.portfolio_correlations.end)} · 최근252개 관측일 창, 쌍별200개 이상. 현지 통화 수익률이며 비중 가중 또는 인과 효과가 아닙니다.</p>${c.pairs.slice(0,8).map(p=>`<p>${E(name(g,p.a))} ↔ ${E(name(g,p.b))}: ρ ${N(p.corr)} · ${p.observations}개</p>`).join('')}</section>`;
 }
 function entityNotes(id,g){if(!g)return '';const links=g.links.filter(e=>e.source===id||e.target===id);return `<section><h3>사업·공급·경쟁 관계 ${links.length}개</h3>${g.nodes.some(n=>n.id===id)?'<button type="button" data-entity-relation>관계 지도에서 보기</button>':'<p>현재 근거 관계망 범위 밖입니다.</p>'}<ul>${links.map(e=>edgeHTML(g,e.id)).join('')}</ul></section>`;}
 function insights(g){
  const observed=g.links.filter(e=>finite(e.corr)),formal=observed.filter(e=>e.relation!=='correlated'),hidden=observed.filter(e=>e.relation==='correlated'),divergent=formal.filter(e=>e.corr*Math.sign(g.parameters.transfer[e.relation][0])<0);
  return `<details><summary>관계와 가격 상관 대조 · 일치 ${formal.length-divergent.length} / 불일치 ${divergent.length} / 추가 관측 연결 ${hidden.length}</summary><p>순방향 가정계수와 실제 상관의 부호만 대조합니다. 같은 부호도 관계의 인과 증명이 아닙니다. 추가 관측 연결은 최근3개월 |ρ|≥0.6인 쌍 중 공식 관계가 없는 쌍입니다. 동일 시장 선행·후행 탐색은 상단 별도 패널에서 검정 표본과 함께 확인합니다.</p><h4>가정과 부호가 다른 관측</h4><ul>${divergent.map(e=>edgeHTML(g,e.id)).join('')||'<li>해당 없음</li>'}</ul><h4>추가 가격 상관 연결</h4><ul>${hidden.map(e=>edgeHTML(g,e.id)).join('')||'<li>해당 없음</li>'}</ul></details>`;
 }
 function graphSVG(g,st={}){
  const yaw=st.yaw??.5,pitch=st.pitch??-.22,zoom=st.zoom??1,size=st.size??1,selected=st.node||'',kind=st.kind||'all',rel=st.relation||'all',q=(st.q||'').toLocaleLowerCase();
  const nodes=g.nodes.filter(n=>(kind==='all'||n.kind===kind)&&(!q||(n.name+' '+(n.symbol||'')+' '+n.role).toLocaleLowerCase().includes(q))),ids=new Set(nodes.map(n=>n.id));
  const edges=g.links.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(rel==='all'||e.relation===rel));
  const neighbors=new Set(edges.filter(e=>e.source===selected||e.target===selected).flatMap(e=>[e.source,e.target]));
  const pos=new Map(nodes.map(n=>{const [a,b,c]=n.position,x=a*Math.cos(yaw)+c*Math.sin(yaw),z=-a*Math.sin(yaw)+c*Math.cos(yaw),y=b*Math.cos(pitch)-z*Math.sin(pitch),depth=b*Math.sin(pitch)+z*Math.cos(pitch),scale=1/(1+depth*.2);return [n.id,{x:450+x*300*zoom*scale,y:275+y*230*zoom*scale,z:depth,r:(5+Math.sqrt(n.degree||0))*size*scale}];}));
  const boxes=[],labels=new Map(),overlap=(a,b)=>Math.max(0,Math.min(a.x+a.w/2,b.x+b.w/2)-Math.max(a.x-a.w/2,b.x-b.w/2))*Math.max(0,Math.min(a.y+4,b.y+4)-Math.max(a.y-11,b.y-11));
  for(const n of [...nodes].sort((a,b)=>(b.id===selected)-(a.id===selected)||Number(neighbors.has(b.id))-Number(neighbors.has(a.id)))){
   const p=pos.get(n.id),text=n.id===selected?n.name:n.symbol||n.name,w=[...text].reduce((v,c)=>v+(c.charCodeAt(0)>255?11:6.4),8);let best=null;
   for(const step of [0,14,28,42,56])for(const [dx,dy] of [[0,p.r+14+step],[0,-p.r-6-step],[w/2+p.r+5+step,4],[-w/2-p.r-5-step,4]]){
    const candidate={x:Math.max(w/2+12,Math.min(888-w/2,p.x+dx)),y:Math.max(20,Math.min(518,p.y+dy)),w,text},score=boxes.reduce((v,b)=>v+overlap(candidate,b),0)*100+Math.hypot(dx,dy);
    if(!best||score<best.score)best={...candidate,score};
   }labels.set(n.id,best);boxes.push(best);
  }
  const edge=(e)=>{const a=pos.get(e.source),b=pos.get(e.target),on=neighbors.has(e.source)&&neighbors.has(e.target)&&(e.source===selected||e.target===selected);return `<line data-redge="${E(e.id)}" x1="${a.x.toFixed(2)}" y1="${a.y.toFixed(2)}" x2="${b.x.toFixed(2)}" y2="${b.y.toFixed(2)}" stroke="${e.relation==='correlated'?'#a894c6':e.relation==='competes'?'#bf758c':'#547688'}" stroke-width="${on?2.4:1}" opacity="${on?.9:.35}" ${e.relation==='correlated'?'stroke-dasharray="4 4"':''}><title>${E(name(g,e.source)+' → '+name(g,e.target)+' · '+g.relation_labels[e.relation])}</title></line>`;};
  const paint=root.AnalysisCharts.orbPaint(Object.values(colors),'relation');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" class="relation-svg" role="img" aria-label="사업 관계망 3차원 투영. 객체 선택, 드래그 회전, 휠 확대."><rect width="900" height="560" rx="14" fill="#fafbfd"/>${paint.defs}${edges.map(edge).join('')}${[...nodes].sort((a,b)=>pos.get(b.id).z-pos.get(a.id).z).map(n=>{const p=pos.get(n.id),label=labels.get(n.id),on=n.id===selected;return `<g data-rnode="${E(n.id)}" tabindex="0" role="button" aria-label="${E(n.name)} 관계 선택" transform="translate(${p.x.toFixed(2)} ${p.y.toFixed(2)})" opacity="${!selected||on||neighbors.has(n.id)?1:.56}"><circle r="${p.r.toFixed(2)}" fill="${paint.fills[Object.keys(colors).indexOf(n.kind)]}" stroke="${on?'#245f9e':'#ffffff'}" stroke-width="${on?3:1}"/><text x="${(label.x-p.x).toFixed(2)}" y="${(label.y-p.y).toFixed(2)}" text-anchor="middle" fill="#465b70" font-size="11">${E(label.text)}</text><title>${E(n.role)}${n.date?' · '+E(n.date):''}</title></g>`;}).join('')}<text x="18" y="540" fill="#738092" font-size="12">표시 ${nodes.length}객체 · ${edges.length}관계 · 점선: 가격 상관 · 드래그 회전 / 휠 확대</text></svg>`;
 }
 const states={},disposers=[];
 function dispose(){while(disposers.length)disposers.pop()();}
 function render(s,i){return `<section class="panel" data-relation-view="${s.type}" data-relation-index="${i}"><h2>${E(s.title)}</h2><div data-relation-controls></div><div data-relation-content></div></section>`;}
 function bind(container,d,navigate,selection={}){
  const g=d.sections.find(s=>s.type==='relationlab');if(!g)return;
  container.querySelectorAll('[data-relation-view]').forEach(box=>{
   const mode=box.dataset.relationView,st=states[mode]??={node:'stock:NVDA',scenario:g.scenarios[0].id,hops:3,correlated:false,shock:-.5,yaw:.5,pitch:-.22,zoom:1,size:1,kind:'all',relation:'all',q:''};
   if(selection.relationNode&&mode==='relationlab'){st.node=selection.relationNode;st.kind='all';st.q='';delete selection.relationNode;}
   const controls=box.querySelector('[data-relation-controls]'),body=box.querySelector('[data-relation-content]');let disposed=false,frame=null,spin=false,drag=null,dragged=false;
   const select=(key,label,options,value)=>`<label>${label}<select data-rcontrol="${key}">${options.map(([v,t])=>`<option value="${E(v)}" ${v===String(value)?'selected':''}>${E(t)}</option>`).join('')}</select></label>`;
   const shared=select('hops','전파 단계',[['1','1단계'],['2','2단계'],['3','3단계']],st.hops)+`<label><input data-rcorr type="checkbox" ${st.correlated?'checked':''}>실현 상관도 전파에 포함</label>`;
   controls.innerHTML=`<p class="scope-note">${E(g.note)}</p><div class="analysis-controls">${mode==='relationlab'?select('kind','객체 종류',[['all','전체'],...Object.entries(kinds)],st.kind)+select('relation','관계 종류',[['all','전체'],...Object.entries(g.relation_labels).filter(([k])=>g.links.some(e=>e.relation===k))],st.relation)+`<label>검색 <input data-rsearch type="search" value="${E(st.q)}" placeholder="객체·사업 설명"></label>`:select('scenario','시나리오',g.scenarios.map(s=>[s.id,s.name]),st.scenario)}${shared}</div>`;
   if(mode==='relationlab')body.innerHTML=`<div class="relation-hubs"><strong>시스템 중심성 · 기본3단계</strong>${g.hubs.filter(h=>h.score>0).slice(0,6).map(h=>`<button data-rhub="${E(h.id)}">${E(name(g,h.id))} ${N(h.score)} · ${h.breadth}객체</button>`).join('')}</div><p class="quiet">점수=도달 |강도| 합+0.15×객체 수 (|강도|≥0.05). 모형 연결성 순위입니다. 상관 전파 선택과 무관한 기본값입니다.</p><div class="analysis-controls">${select('node','객체',g.nodes.map(n=>[n.id,n.name]),st.node)}<label>단일 충격 <input data-rshock type="number" min="-2" max="2" step="0.1" value="${st.shock}"></label><input data-rzoom type="hidden" value="${st.zoom*100}"><label>크기 <input data-rsize type="range" min="60" max="180" value="${st.size*100}"></label><button data-rspin>자동 회전 시작</button><button data-rreset>시점 초기화</button></div><p class="quiet">종류·관계·검색은 지도 표시 필터입니다. 충격 계산은 전체 근거 관계망에서 수행합니다.</p><div data-relation-graph></div><div class="network-legend">${Object.entries(kinds).map(([key,label])=>`<span style="color:${colors[key]}">● ${E(label)}</span>`).join('')}</div><div data-relation-detail></div><div data-relation-output></div>`;
   else body.innerHTML='<div data-relation-output></div>';
   if(mode==='relationlab')body.innerHTML+=insights(g);
   const output=box.querySelector('[data-relation-output]'),graph=box.querySelector('[data-relation-graph]');
   const readEntries=()=>{try{return {entries:root.DecisionLedger.store(root.localStorage).entries()};}catch(e){return {entries:[],error:e.message};}};
   const draw=()=>{if(!graph||disposed)return;graph.innerHTML=graphSVG(g,st);graph.querySelectorAll('[data-rnode]').forEach(el=>{
    const choose=()=>{st.node=el.dataset.rnode;box.querySelector('[data-rcontrol="node"]').value=st.node;detail();update();draw();};
    el.addEventListener('click',()=>{if(!dragged)choose();});el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
   });};
   const detail=()=>{if(!graph)return;const n=g.nodes.find(n=>n.id===st.node),links=g.links.filter(e=>e.source===st.node||e.target===st.node);box.querySelector('[data-relation-detail]').innerHTML=n?`<article class="panel"><h3>${E(n.name)} · ${E(kinds[n.kind])}</h3><p>${E(n.role)}${n.date?' · 관측 '+E(n.date):n.reviewed_at?' · 근거 확인 '+E(n.reviewed_at):''}</p>${n.kind==='company'?`<p>1M ${N(n.r1m)}% · 3M ${N(n.r3m)}% · RS ${N(n.rs)}</p>`:finite(n.value)?`<p>최근 관측 ${N(n.value)}${n.id==='macro:ust10'?'%':n.id==='commodity:gold'?' USD/트로이온스':''}</p>`:''}${n.entity?'<button data-rentity>기업 상세 · 결정 기록</button>':''}<ul>${links.map(e=>edgeHTML(g,e.id)).join('')||'<li>확인된 연결 없음. 관계를 가정해서 보충하지 않았습니다.</li>'}</ul></article>`:'<p>객체를 선택하세요.</p>';box.querySelector('[data-rentity]')?.addEventListener('click',()=>navigate('기업 상세',{entity:n.id}));};
   const update=()=>{
    const s=mode==='relationscenario'?g.scenarios.find(s=>s.id===st.scenario):{name:name(g,st.node)+' 단일 충격',seeds:[{id:st.node,value:st.shock}]};
    let impacts;try{impacts=runScenario(g,s.seeds,st.hops,st.correlated);}catch(e){output.innerHTML='<p role="status">'+E(e.message)+'</p>';return;}
    const stored=readEntries(),p=portfolioImpact(stored.entries,g,impacts);
    output.innerHTML=`<h3>${E(s.name)}</h3><p>일차 가정: ${s.seeds.map(r=>E(name(g,r.id))+' '+N(r.value)).join(' · ')}</p><p class="quiet">${st.hops}단계 · 상관 전파 ${st.correlated?'포함 (음의 부호 보존)':'제외'} · 한 일차 입력당 최강 절대 경로, 여러 일차 입력은 합산. 순위는 상대 강도이며 수익률이 아닙니다.</p>${rankings(g,impacts)}<h3>실행 원장에 적용</h3>${stored.error?'<p>원장 읽기 불가: '+E(stored.error)+'</p>':`<p>전체 ${N(p.total)} · 계산 가능한 부분합 ${N(p.partial)} · 미산출 ${p.unknown}건 · 상대 강도 × NAV비중</p>${p.rows.map(r=>`<p>${E(r.name)}: ${N(r.value)} · ${E(r.reason)}</p>`).join('')||'<p>실행 기록 없음.</p>'}`}<details><summary>전달계수와 해석</summary><p>관계별 순방향/역방향 계수 × (0.7+0.1×관계가중치)×0.9. 가중치1은 존재를 반영한 가정이고 거래금액이 아닙니다. |강도|0.03 미만 경로는 중단하며 경로 내 객체 재방문을 제외합니다.</p><ul>${Object.entries(g.parameters.transfer).map(([k,v])=>`<li>${E(g.relation_labels[k])}: ${v.join(' / ')}</li>`).join('')}</ul></details>`;
   };
   box.querySelectorAll('[data-rcontrol]').forEach(el=>el.addEventListener('change',()=>{const k=el.dataset.rcontrol;st[k]=k==='hops'?+el.value:el.value;draw();detail();update();}));
   const corr=box.querySelector('[data-rcorr]');corr.checked=st.correlated;corr.addEventListener('change',()=>{st.correlated=corr.checked;update();});
   box.querySelector('[data-rsearch]')?.addEventListener('input',e=>{st.q=e.target.value;draw();});
   box.querySelector('[data-rshock]')?.addEventListener('input',e=>{st.shock=e.target.value.trim()===''?null:Number(e.target.value);update();});
   box.querySelectorAll('[data-rhub]').forEach(el=>el.addEventListener('click',()=>{st.node=el.dataset.rhub;box.querySelector('[data-rcontrol="node"]').value=st.node;draw();detail();update();}));
   box.querySelector('[data-rzoom]')?.addEventListener('input',e=>{st.zoom=Number(e.target.value)/100;draw();});
   box.querySelector('[data-rsize]')?.addEventListener('input',e=>{st.size=Number(e.target.value)/100;draw();});
   const tick=()=>{if(!spin||disposed)return;st.yaw+=.003;draw();frame=root.requestAnimationFrame(tick);};
   const stop=()=>{spin=false;if(frame!==null)root.cancelAnimationFrame?.(frame);frame=null;const b=box.querySelector('[data-rspin]');if(b)b.textContent='자동 회전 시작';};
   box.querySelector('[data-rspin]')?.addEventListener('click',e=>{if(spin)stop();else if(root.requestAnimationFrame){spin=true;e.target.textContent='자동 회전 중지';frame=root.requestAnimationFrame(tick);}});
   box.querySelector('[data-rreset]')?.addEventListener('click',()=>{stop();Object.assign(st,{yaw:.5,pitch:-.22,zoom:1,size:1});box.querySelector('[data-rzoom]').value='100';box.querySelector('[data-rsize]').value='100';draw();});
   const camera=graph?root.AnalysisCharts.bindCamera(graph,{read:()=>({yaw:st.yaw,pitch:st.pitch,zoom:st.zoom}),write:v=>{Object.assign(st,v);box.querySelector('[data-rzoom]').value=String(Math.round(st.zoom*100));},draw,start:stop,reset:()=>{box.querySelector('[data-rreset]').click();},minPitch:-1.4,maxPitch:1.4,maxZoom:2.4,free:true,wheelRequiresCtrl:false}):null;

   disposers.push(()=>{disposed=true;stop();camera?.dispose();});draw();detail();update();
  });
 }
 root.RelationViews={adjacency,propagate,runScenario,decodeMatrix,portfolioImpact,crowding,portfolioNotes,decisionNotes,entityNotes,rankings,graphSVG,render,bind,dispose};
})(typeof window==='undefined'?globalThis:window);
