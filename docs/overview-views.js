/* Overview state coordinates; one cached local snapshot, no external data requests. */
(function(root){
 'use strict';const E=root.ResearchCharts.esc,N=root.AnalysisCharts.n,valid=v=>typeof v==='number'&&Number.isFinite(v),clip=(v,a,b)=>Math.max(a,Math.min(b,v)),times=['#647fc4','#3f9e98','#cc9655','#c5a438'];
 const svg=(body,title,w,h)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${E(title)}"><rect width="${w}" height="${h}" rx="12" fill="#f6f9fc"/>${body}</svg>`;
 const color=z=>valid(z)?`hsl(${215-clip((z+1.5)/3,0,1)*180} 60% 49%)`:'#8a929b';
 function quadrant(p,row=p.rows.at(-1)){
  const roles=Object.fromEntries(p.axes.map(a=>[a.role,a.key])),x=row.z[roles.x],z=row.z[roles.z];if(!valid(x)||!valid(z))return '필수 축 미산출';
  return p.id==='tesseract'?(x>=0?(z>=0?'과열 방향':'회복 방향'):(z>=0?'스태그 방향':'둔화 방향')):(x>=0?(z>=0?'과열·집중':'광범위 강세'):(z>=0?'소수 주도':'과열·집중 낮음'));
 }
 function hologram(p,yaw=.6,zoom=1,pitch=.38){
  const W=750,H=450,roles=Object.fromEntries(p.axes.map(a=>[a.role,a.key]));
  const P=(x,z,y)=>{const rx=x*Math.cos(yaw)-z*Math.sin(yaw),rz=x*Math.sin(yaw)+z*Math.cos(yaw);const depth=rz*Math.cos(pitch)+y*Math.sin(pitch),perspective=5/(5-depth);return [W/2+rx*165*zoom*perspective,H*.51+(rz*71*Math.sin(pitch)/Math.sin(.38)-y*104*Math.cos(pitch)/Math.cos(.38))*zoom*perspective];};
  const point=r=>[roles.x,roles.z,roles.y].every(k=>valid(r.z[k]))?P(...[roles.x,roles.z,roles.y].map(k=>clip(r.z[k]/2,-1.1,1.1))):null;
  const qnames=p.id==='tesseract'?['과열','회복','스태그','둔화']:['과열·집중','광범위 강세','소수 주도','분산·냉각'];
  const paint=root.AnalysisCharts.orbPaint(p.rows.map(row=>color(row.z[roles.color])),'overview-'+p.id);let b=paint.defs;[[0,0],[0,-1],[-1,0],[-1,-1]].forEach(([x,z],i)=>{const corners=[[x,z],[x+1,z],[x+1,z+1],[x,z+1]].map(([a,c])=>P(a,c,0)),label=P(x+.5,z+.5,0);b+=`<polygon data-state-quadrant="${i}" points="${corners.map(a=>a.join(',')).join(' ')}" fill="${['#f1dddd','#dceae1','#f0e7d7','#dce5f0'][i]}" stroke="#c3cfda"/><text x="${label[0]}" y="${label[1]}" fill="#61778a" text-anchor="middle" font-size="16">${qnames[i]}</text>`;});
  const origin=P(0,0,0);[[1.16,0,0,'x'],[0,1.16,0,'z'],[0,0,1.3,'y']].forEach(([x,z,y,role])=>{const a=P(x,z,y),label=p.axes.find(n=>n.role===role).name;b+=`<line x1="${origin[0]}" y1="${origin[1]}" x2="${a[0]}" y2="${a[1]}" stroke="#71899d"/><text x="${a[0]}" y="${a[1]-13}" fill="#344f65" font-size="16" text-anchor="middle">${role.toUpperCase()} ${E(label)}</text>`;});
  for(let i=1;i<p.rows.length;i++){const a=point(p.rows[i-1]),c=point(p.rows[i]);if(a&&c)b+=`<line data-state-segment="${i}" x1="${a[0]}" y1="${a[1]}" x2="${c[0]}" y2="${c[1]}" stroke="#6d8ba2" opacity="${.25+.65*i/p.rows.length}" stroke-width="2"/>`;}
  p.rows.forEach((row,i)=>{const pt=point(row);if(!pt)return;const size=row.z[roles.size],halo=roles.halo?row.z[roles.halo]:null,r=valid(size)?3+clip((size+1.5)/3,0,1)*6:4,last=i===p.rows.length-1;
   if(valid(halo))b+=`<circle data-state-halo="${row.date}" cx="${pt[0]}" cy="${pt[1]}" r="${r+5+clip(halo+1,0,3)*4}" fill="#dd8e56" opacity="${clip((halo+1)/10,0,.3)}"/>`;
   b+=`<circle data-state-date="${row.date}" cx="${pt[0]}" cy="${pt[1]}" r="${r}" fill="${paint.fills[i]}" stroke="${last?'#b88a11':'#f5f8fa'}" stroke-width="${last?3:1}" opacity="${last?1:.35+.6*i/p.rows.length}"><title>${E(row.date)} · ${p.axes.map(a=>E(a.name)+' '+N(row.raw[a.key])+' '+E(a.unit)+' (z '+N(row.z[a.key])+')').join(' · ')}</title></circle>`;
   if(last){const floor=P(clip(row.z[roles.x]/2,-1.1,1.1),clip(row.z[roles.z]/2,-1.1,1.1),0);b+=`<line x1="${pt[0]}" y1="${pt[1]}" x2="${floor[0]}" y2="${floor[1]}" stroke="#b88a11" stroke-dasharray="4 4"/>`;}
  });
  p.milestones.forEach((m,i)=>{const pt=point(m);if(pt)b+=`<g data-state-milestone="${i}"><circle cx="${pt[0]}" cy="${pt[1]}" r="11" fill="none" stroke="${times[i]}" stroke-width="2"/><circle cx="523" cy="${28+i*22}" r="4" fill="${times[i]}"/><text x="535" y="${33+i*22}" fill="${times[i]}" font-size="14">${E(m.label)} · ${E(m.date)}</text></g>`;});
  b+=`<text x="24" y="408" fill="#4f6a7f" font-size="15">36시점 · 좌표 z −2.2~+2.2 · 금색 테두리=현재</text><text x="24" y="431" fill="#4f6a7f" font-size="15">색=${E(p.axes.find(a=>a.role==='color').name)} · 크기=${E(p.axes.find(a=>a.role==='size').name)}${roles.halo?' · 후광=모멘텀':''} · 결측은 이어 그리지 않음</text>`;
  return svg(b,p.title+' · 36개월3D 궤적',W,H);
 }
 function radar(p,rotation=0,zoom=1,tilt=.46){
  const W=400,H=420,cx=200,base=322,gap=54,R=111*zoom,n=p.axes.length,angle=i=>-Math.PI/2+i*2*Math.PI/n+rotation;
  const P=(i,z,level)=>{const r=Math.max(4,(clip(z,-2,2)+2)/4*R);return [cx+Math.cos(angle(i))*r,base-level*gap+Math.sin(angle(i))*r*tilt];};
  let b='';for(const z of [0,1,2])b+=`<polygon points="${p.axes.map((a,i)=>P(i,z,0).join(',')).join(' ')}" fill="none" stroke="#bccbd8"/>`;
  p.axes.forEach((a,i)=>{const at=P(i,2,0),label=P(i,2.6,0);b+=`<line x1="${cx}" y1="${base}" x2="${at[0]}" y2="${at[1]}" stroke="#c7d3de"/><text x="${label[0]}" y="${label[1]+(Math.sin(angle(i))<0?-9:18)}" text-anchor="middle" fill="#385a70" font-size="14">${E(a.name)}</text>`;});
  const ms=p.milestones;
  ms.forEach((m,j)=>{
   const level=ms.length-1-j,points=p.axes.map((a,i)=>valid(m.z[a.key])?P(i,m.z[a.key],level):null);
   if(j<ms.length-1)p.axes.forEach((a,i)=>{const k=(i+1)%n,next=ms[j+1],v=[points[i],points[k],valid(next.z[p.axes[k].key])?P(k,next.z[p.axes[k].key],level-1):null,valid(next.z[a.key])?P(i,next.z[a.key],level-1):null];if(v.every(Boolean))b+=`<polygon data-radar-wall="${j}:${i}" points="${v.map(a=>a.join(',')).join(' ')}" fill="${times[j+1]}" fill-opacity=".10" stroke="${times[j+1]}" stroke-opacity=".2"/>`;});
   if(points.every(Boolean))b+=`<polygon data-stacked-date="${m.date}" points="${points.map(a=>a.join(',')).join(' ')}" fill="${times[j]}" fill-opacity="${j===ms.length-1?.2:.07}" stroke="${times[j]}" stroke-width="${j===ms.length-1?2.5:1.5}"/>`;
   points.forEach(pt=>{if(pt)b+=`<circle cx="${pt[0]}" cy="${pt[1]}" r="3" fill="${times[j]}"/>`;});
   b+=`<text x="15" y="${base-level*gap-12}" fill="${times[j]}" font-size="13">${E(m.label)}</text>`;
  });
  b+=`<text x="20" y="404" fill="#526d81" font-size="14">${n}축 × 4시점 · 위=과거 / 아래=현재 · 반경 −2~+2z</text>`;
  return svg(b,p.title+' · 4시점 적층 레이더',W,H);
 }
 function wormhole(l,phase=.3,zoom=1,tilt=.47){
  if(!l.stocks.length)return '<p>주도주 입력 부족</p>';const W=440,H=440,cx=220,cy=210,R=180*zoom,flat=tilt,logs=l.stocks.map(s=>Math.log(s.cap_usd_bn)),lo=Math.min(...logs),hi=Math.max(...logs),center=u=>cy-R*.42*(1-u);let b='';const paint=root.AnalysisCharts.orbPaint(l.stocks.map(s=>color(s.momentum/55)),'leaders');b+=paint.defs;
  for(let k=18;k>=1;k--){const u=k/18,r=R*u**1.35;b+=`<ellipse cx="${cx}" cy="${center(u)}" rx="${r}" ry="${r*flat}" fill="none" stroke="#6589b4" opacity="${.12+(1-u)*.5}"/>`;}
  b+=`<ellipse cx="${cx}" cy="${center(0)}" rx="30" ry="14" fill="#203950"/>`;
  const occupied=[];
  l.stocks.map((s,i)=>({s,i,depth:1-(Math.log(s.cap_usd_bn)-lo)/(hi-lo||1)})).sort((a,b)=>a.depth-b.depth).forEach(({s,i,depth})=>{const u=.18+.82*depth,r=R*u**1.12,a=phase+i*2*Math.PI/l.stocks.length,x=cx+Math.cos(a)*r,y=center(u)+Math.sin(a)*r*flat,radius=(5+clip(s.growth/250,0,1)*13)*(.5+.62*u);
   let labelY=y-radius-9;const width=s.symbol.replace('.KS','').length*8;for(let j=0;j<10&&occupied.some(r=>Math.abs(r.y-labelY)<17&&Math.abs(r.x-x)<(r.width+width)/2+5);j++)labelY-=18;labelY=Math.max(22,labelY);occupied.push({x,y:labelY,width});
   b+=`<g data-worm-symbol="${E(s.symbol)}" tabindex="0" role="button" aria-label="${E(s.name)} 관측 보기"><line x1="${x}" y1="${y}" x2="${cx}" y2="${center(0)}" stroke="#b3c4d4"/><circle cx="${x}" cy="${y}" r="${radius}" fill="${paint.fills[i]}" stroke="#f9fafc" stroke-width="2"/><text x="${x}" y="${labelY}" text-anchor="middle" font-size="13" fill="#233e54">${E(s.symbol.replace('.KS',''))}</text><title>${E(s.name)} · 시총 ${N(s.cap_usd_bn)} USD bn · 모멘텀 ${N(s.momentum)}% · 분기 NI 성장 ${N(s.growth)}% · 주도력 ${N(s.score)}</title></g>`;
  });
  b+=`<text x="20" y="362" fill="#4d6a80" font-size="14">중심=시총 최대 · 색=12M 모멘텀</text><text x="20" y="386" fill="#4d6a80" font-size="14">크기=분기 순이익 성장 · 선택/호버=관측 수치</text><text x="20" y="411" fill="#4d6a80" font-size="14">현재 재무 캐시 내 시총50개 표본 → 상위10</text>`;return svg(b,'주도주 · 시총/모멘텀/실적성장',W,H);
 }
 const table=(title,cols,rows)=>`<div class="table-scroll"><table class="data-table"><caption>${E(title)}</caption><thead><tr>${cols.map(c=>`<th>${E(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${typeof v==='number'?N(v):E(v??'—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
 function panelHTML(p,leaders){const latest=p.rows.at(-1);return `<section class="panel overview-coordinate" data-coordinate="${p.id}"><h2>${E(p.title)}</h2><p><strong>${E(quadrant(p))}</strong> · 각 축의 과거 평균 대비 위치 · 기준 ${E(latest.date)}${latest.partial_month?' (월중 관측)':''}</p><div class="analysis-controls"><label>회전 <input data-state-yaw type="range" min="-314" max="314" value="60"></label><label>기울기 <input data-state-pitch type="range" min="15" max="85" value="38"></label><label>확대 <input data-state-zoom type="range" min="50" max="140" value="100"></label><label>관측일 <select data-state-select><option value="">날짜 선택</option>${p.rows.map(r=>`<option>${E(r.date)}</option>`).join('')}</select></label><button data-state-spin>자동 회전 시작</button><button data-state-reset>시점 초기화</button></div><div class="overview-holo-grid ${p.id==='crowding'?'has-worm':''}"><figure><figcaption>36개월 상태 궤적</figcaption><div data-state-holo>${hologram(p)}</div></figure>${p.id==='crowding'?`<figure><figcaption>주도주 · 3개 시각 변수</figcaption><div data-state-worm>${wormhole(leaders)}</div><div data-worm-detail></div></figure>`:''}<figure><figcaption>${p.axes.length}축 적층 레이더</figcaption><div data-state-radar>${radar(p)}</div></figure></div><output class="projection-detail" data-state-detail aria-live="polite">관측일을 선택하거나 점을 눌러 원수치를 확인하세요.</output><div class="kpi-grid">${p.axes.map(a=>`<div class="kpi"><small>${E(a.name)} · ${E(a.role)}</small><strong>${N(latest.raw[a.key])} <small>${E(a.unit)}</small></strong><span>z ${N(latest.z[a.key])}</span></div>`).join('')}</div>${table('시점별 원단위 관측', ['시점','날짜',...p.axes.map(a=>a.name+' '+a.unit)],p.milestones.map(m=>[m.label,m.date,...p.axes.map(a=>m.raw[a.key])]))}<details><summary>축별 정의·관측 기간·팀 이용 시점</summary>${table('현재 관측의 출처 기간',['축','정의','관측 기간 끝','팀 이용 시점'],p.axes.map(a=>{const r=latest.provenance[a.key];return [a.name,a.definition,r.period,r.available];}))}<pre class="state-provenance">${E(JSON.stringify(latest.provenance,null,2))}</pre></details><p class="quiet">${E(p.note)}</p></section>`;}
 function view(d){return `<div class="section-head"><h2>거시·시장 상태와 주도주</h2><span>가격 기준 ${E(d.as_of)}</span></div>${d.panels.map(p=>panelHTML(p,d.leaders)).join('')}<details><summary>주도주 표본·계산·관측 원장</summary><p>${E(d.leaders.note)}</p><p>재무 캐시 ${d.leaders.cached}개 · 시총 풀 ${d.leaders.pool}개 · 필요 항목 가용 ${d.leaders.eligible}개</p>${table('표본 내 주도력 상위10',['종목','USD bn','12M %','분기 NI YoY %','주도력','결산일','재무 수집 시각'],d.leaders.stocks.map(s=>[s.name,s.cap_usd_bn,s.momentum,s.growth,s.score,s.profit_period,s.financial_as_of]))}</details><details><summary>자료 출처와 남은 차이</summary><ul>${d.sources.map(s=>`<li><a href="${E(/^https:\/\//.test(s.url)?s.url:'#')}" target="_blank" rel="noopener noreferrer">${E(s.name)} ↗</a></li>`).join('')}</ul><ul>${d.missing.map(t=>`<li>${E(t)}</li>`).join('')}</ul></details>`;}
 let cached=null,pending=null,request=0;const disposers=[];
 function cancel(){request++;while(disposers.length)disposers.pop()();}
 function bind(box,d){box.querySelectorAll('[data-coordinate]').forEach(el=>{
  const p=d.panels.find(p=>p.id===el.dataset.coordinate),slider=el.querySelector('[data-state-yaw]'),zoomInput=el.querySelector('[data-state-zoom]'),pitchInput=el.querySelector('[data-state-pitch]'),picker=el.querySelector('[data-state-select]');let wormView={yaw:.6,pitch:.47,zoom:1},zoom=1,pitch=.38,selected='',yaw=.6,spin=false,frame=null,disposed=false,drag=null;
  const draw=()=>{if(disposed)return;el.querySelector('[data-state-holo]').innerHTML=hologram(p,yaw,zoom,pitch);el.querySelectorAll('[data-state-date]').forEach(n=>n.classList?.toggle('point-selected',n.dataset.stateDate===selected));const worm=el.querySelector('[data-state-worm]');if(worm){worm.innerHTML=wormhole(d.leaders,wormView.yaw,wormView.zoom,wormView.pitch);worm.querySelectorAll('[data-worm-symbol]').forEach(n=>{const show=()=>{const s=d.leaders.stocks.find(s=>s.symbol===n.dataset.wormSymbol);el.querySelector('[data-worm-detail]').innerHTML=`<p><b>${E(s.name)}</b><br>시총 ${N(s.cap_usd_bn)} USD bn · 12M ${N(s.momentum)}%<br>분기 NI YoY ${N(s.growth)}% (${E(s.profit_period)})<br>가격 ${E(s.price_date)} · 재무 수집 ${E(s.financial_as_of)}</p>`;};n.addEventListener('click',show);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show();}});});}};
  const stop=()=>{spin=false;if(frame!==null)root.cancelAnimationFrame?.(frame);frame=null;el.querySelector('[data-state-spin]').textContent='자동 회전 시작';};
  const tick=()=>{if(!spin||disposed)return;yaw+=.004;draw();frame=root.requestAnimationFrame(tick);};
  slider.addEventListener('input',()=>{stop();yaw=+slider.value/100;draw();});el.querySelector('[data-state-spin]').addEventListener('click',e=>{if(spin)stop();else if(root.requestAnimationFrame){spin=true;e.target.textContent='자동 회전 중지';frame=root.requestAnimationFrame(tick);}});
  el.querySelector('[data-state-reset]').addEventListener('click',()=>{stop();yaw=.6;zoom=1;pitch=.38;wormView={yaw:.6,pitch:.47,zoom:1};selected='';slider.value='60';zoomInput.value='100';pitchInput.value='38';picker.value='';el.querySelector('[data-state-detail]').textContent='관측일을 선택하거나 점을 눌러 원수치를 확인하세요.';draw();});
  const graph=el.querySelector('[data-state-holo]');
  const camera=root.AnalysisCharts.bindCamera(graph,{read:()=>({yaw,pitch,zoom}),write:v=>{yaw=v.yaw;pitch=v.pitch;zoom=v.zoom;slider.value=String(Math.round(yaw*100));zoomInput.value=String(Math.round(zoom*100));pitchInput.value=String(Math.round(pitch*100));},draw,start:stop,reset:()=>{el.querySelector('[data-state-reset]').click();},minPitch:.15,maxPitch:.85});
  zoomInput.addEventListener('input',()=>{stop();zoom=+zoomInput.value/100;draw();});pitchInput.addEventListener('input',()=>{stop();pitch=+pitchInput.value/100;draw();});
  const choose=date=>{stop();selected=date;picker.value=date;const row=p.rows.find(r=>r.date===date);el.querySelector('[data-state-detail]').textContent=row?date+' · '+p.axes.map(a=>a.name+': '+(row.raw[a.key]??'미산출')+' '+a.unit).join(' · '):'관측일을 선택하거나 점을 눌러 원수치를 확인하세요.';draw();};
  picker.addEventListener('change',()=>choose(picker.value));graph.addEventListener('click',e=>{const point=e.target.closest('[data-state-date]');if(point)choose(point.dataset.stateDate);});
  const radarBox=el.querySelector('[data-state-radar]');let rv={yaw:0,pitch:.46,zoom:1};const radarCamera=root.AnalysisCharts.bindCamera(radarBox,{read:()=>rv,write:v=>{rv=v;},draw:()=>{radarBox.innerHTML=radar(p,rv.yaw,rv.zoom,rv.pitch);},reset:()=>{rv={yaw:0,pitch:.46,zoom:1};radarBox.innerHTML=radar(p);},minPitch:.2,maxPitch:.7,maxZoom:1.15});

  const wormBox=el.querySelector('[data-state-worm]'),wormCamera=wormBox?root.AnalysisCharts.bindCamera(wormBox,{read:()=>wormView,write:v=>{wormView=v;},draw,reset:()=>{wormView={yaw:.6,pitch:.47,zoom:1};draw();},minPitch:.25,maxPitch:.7,maxZoom:1.15}):null;
  disposers.push(()=>{disposed=true;stop();camera.dispose();radarCamera.dispose();wormCamera?.dispose();});draw();
 });}
 async function mount(box){const token=++request;try{
  if(!cached){pending??=root.fetch('data/overview_state.json').then(r=>{if(!r.ok)throw Error('상태 데이터 읽기 실패');return r.json();}).then(d=>{cached=d;return d;}).finally(()=>{pending=null;});await pending;}
  if(token!==request)return;box.innerHTML=view(cached);bind(box,cached);
 }catch(e){if(token===request)box.innerHTML='<p>상태 차트를 읽지 못했습니다. '+E(e.message)+'</p>';}}
 root.OverviewViews={hologram,radar,wormhole,quadrant,view,bind,mount,cancel};
})(typeof window==='undefined'?globalThis:window);
