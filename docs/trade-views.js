/* Annual merchandise exports. Each arrow retains its reporter and denominator. */
(function(root){
 'use strict';
 const E=root.ResearchCharts.esc,rad=Math.PI/180;let coastPromise;const disposers=[];
 const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
 const width=usd=>1.2+Math.min(3.6,Math.log10(Number(usd)/1e9+1)*1.5);
 const bn=v=>v==null?'미확보':(Number(v)/1e9).toLocaleString('ko-KR',{maximumFractionDigits:3});
 function exact(v){if(v==null)return '미확보';const [a,b]=String(v).split('.');return a.replace(/\B(?=(\d{3})+(?!\d))/g,',')+(b&&!/^0+$/.test(b)?'.'+b:'');}
 function flows(s,st){
  const home=s.areas.find(a=>a.id===st.area)||s.areas[0],incoming=st.direction==='in';
  return s.areas.filter(a=>a.id!==home.id).map(a=>{
   const from=incoming?a:home,to=incoming?home:a,r=from.exports.find(r=>r[0]===to.id);
   return {from,to,partner:a,usd:r?.[1]??null,reported:r?.[2]??null,aggregate:r?.[3]??null,
    share:r&&Number(from.world_usd)>0?Number(r[1])/Number(from.world_usd)*100:null};
  }).filter(r=>[r.partner.id,r.partner.code,r.partner.name,r.partner.official_name].join(' ').toLocaleLowerCase().includes(st.query.toLocaleLowerCase()))
   .sort((a,b)=>st.sort==='name'?a.partner.name.localeCompare(b.partner.name,'ko'):
    a.usd==null?(b.usd==null?a.partner.id.localeCompare(b.partner.id):1):b.usd==null?-1:
    (Number(b.usd)-Number(a.usd))*(st.sort==='asc'?-1:1));
 }
 function greatCircle(a,b){
  const vec=c=>[Math.cos(c.lat*rad)*Math.cos(c.lon*rad),Math.cos(c.lat*rad)*Math.sin(c.lon*rad),Math.sin(c.lat*rad)];
  const x=vec(a),y=vec(b),omega=Math.acos(clamp(x.reduce((s,v,i)=>s+v*y[i],0),-1,1)),sin=Math.sin(omega);
  if(omega<1e-9||Math.abs(sin)<1e-9)return [];
  return Array.from({length:81},(_,i)=>{const t=i/80,u=Math.sin((1-t)*omega)/sin,v=Math.sin(t*omega)/sin,p=x.map((q,k)=>u*q+v*y[k]);return [Math.atan2(p[1],p[0])/rad,Math.atan2(p[2],Math.hypot(p[0],p[1]))/rad];});
 }
 function map(s,st,coasts=[]){
  const cx=320,cy=255,R=230*st.zoom,lon=st.lon*rad,lat=st.lat*rad;
  const project=([x,y])=>{const l=x*rad-lon,f=y*rad;return [Math.cos(f)*Math.sin(l),-(Math.cos(lat)*Math.sin(f)-Math.sin(lat)*Math.cos(f)*Math.cos(l)),Math.sin(lat)*Math.sin(f)+Math.cos(lat)*Math.cos(f)*Math.cos(l)];};
  const screen=p=>[cx+R*p[0],cy+R*p[1]];
  const edge=(a,b)=>{const t=a[2]/(a[2]-b[2]),x=a[0]+t*(b[0]-a[0]),y=a[1]+t*(b[1]-a[1]),n=Math.hypot(x,y);return [x/n,y/n,0];};
  function path(coords){let prior=null,started=false,out='';const add=(p,move)=>{const [x,y]=screen(p);out+=(move?'M':'L')+x.toFixed(2)+','+y.toFixed(2);};
   for(const c of coords){const p=project(c);if(p[2]>=0){if(prior&&prior[2]<0){add(edge(prior,p),true);started=true;}add(p,!started);started=true;}
    else{if(prior&&prior[2]>=0)add(edge(prior,p),false);started=false;}prior=p;}return out;
  }
  let out=`<circle cx="${cx}" cy="${cy}" r="${R}" fill="#ecf4f6" stroke="#90b0bc"/>`;
  for(let f=-80;f<=80;f+=10)out+=`<path d="${path(Array.from({length:181},(_,i)=>[-180+i*2,f]))}" fill="none" stroke="#d5e4e8" stroke-width=".6"/>`;
  for(let l=-180;l<180;l+=10)out+=`<path d="${path(Array.from({length:91},(_,i)=>[l,-90+i*2]))}" fill="none" stroke="#d5e4e8" stroke-width=".6"/>`;
  out+=coasts.map(c=>`<path d="${path(c)}" fill="none" stroke="#809d9b" stroke-width=".8"/>`).join('');
  let rows=flows(s,st).filter(r=>Number(r.usd)>0).sort((a,b)=>Number(b.usd)-Number(a.usd));
  if(st.partner)rows=rows.filter(r=>r.partner.id===st.partner);
  else if(st.limit!=='all')rows=rows.slice(0,Number(st.limit));
  for(const r of rows){const coords=greatCircle(r.from,r.to),w=width(r.usd),color=st.direction==='in'?'#946842':'#197f96';
   out+=`<path data-trade-arc="${E(r.from.id+'>'+r.to.id)}" d="${path(coords)}" fill="none" stroke="${color}" stroke-opacity=".7" stroke-width="${w}"><title>${E(r.from.name)} → ${E(r.to.name)} · ${s.year} · ${E(exact(r.usd))} USD</title></path>`;
   // A tangent triangle points along the geodesic in export order, even when the destination is behind the globe.
   const index=[56,40,24,8,72].find(i=>coords[i]&&project(coords[i])[2]>.05&&project(coords[i-1])[2]>0);
   if(index!==undefined){const [x,y]=screen(project(coords[index])),[a,b]=screen(project(coords[index-1])),theta=Math.atan2(y-b,x-a)*180/Math.PI;
    out+=`<path data-trade-arrow d="M 5 0 L -5 -3.5 L -5 3.5 Z" transform="translate(${x},${y}) rotate(${theta})" fill="${color}"/>`;}
  }
  for(const a of s.areas){const p=project([a.lon,a.lat]);if(p[2]<0)continue;const [x,y]=screen(p),selected=a.id===st.area;
   out+=`<g data-trade-area="${E(a.id)}" tabindex="0" role="button" aria-label="${E(a.name)} 선택"><circle cx="${x}" cy="${y}" r="${selected?7:4}" fill="${selected?'#b76531':a.world_usd?'#1c667b':'#788891'}" stroke="white" stroke-width="1.3"/>${selected||a.id===st.partner?`<text x="${x+10}" y="${y-8}" font-size="12" fill="#264a5b">${E(a.name)}</text>`:''}<title>${E(a.name)} · UN ${a.code} · ${s.year}</title></g>`;
  }
  return `<svg viewBox="0 0 640 530" role="img" aria-label="${s.year}년 국가 간 상품 수출 정사영 지구본">${out}<text x="12" y="520" font-size="10" fill="#547181">Natural Earth · 곡선=국가 간 수출 방향 · 물리적 항로 아님</text></svg>`;
 }
 function summary(s,st){const home=s.areas.find(a=>a.id===st.area),out=home.exports.reduce((v,r)=>v+Number(r[1]),0),n=home.exports.length;
  return `<div class="trade-kpis"><p><small>자료 연도 / 보고 지역</small><strong>${s.year} / ${s.areas.filter(a=>a.world_usd!=null).length}·45</strong></p><p><small>${E(home.name)} 대세계 수출</small><strong>${bn(home.world_usd)} <small>USD bn</small></strong></p><p><small>선택 ${s.areas.length-1}개 파트너의 수출 비중</small><strong>${home.world_usd?(out/Number(home.world_usd)*100).toFixed(2)+'%':'미확보'} <small>${n}개 관측</small></strong></p></div>`;
 }
 function ledger(s,st){const rows=flows(s,st);return `<p class="quiet">${st.direction==='in'?'상대국 → 선택국 · 상대국의 수출 보고':'선택국 → 상대국'} · ${rows.filter(r=>r.usd!=null).length}/${rows.length}개 관측 · 표는 모든 검색 결과, 지도는 금액 상위 ${st.limit==='all'?'전체':st.limit}개</p>
  <div class="table-scroll trade-ledger"><table class="data-table" aria-label="국가 간 수출 원장"><thead><tr><th>상대국·통계지역</th><th>수출액 USD bn</th><th>수출국 전체 대비 %</th></tr></thead><tbody>${rows.map(r=>`<tr data-trade-row="${E(r.partner.id)}" ${st.partner===r.partner.id?'class="selected"':''}><td><button type="button" data-trade-partner="${E(r.partner.id)}">${E(r.partner.name)}</button></td><td title="${E(exact(r.usd))} USD">${bn(r.usd)}</td><td>${r.share==null?'—':r.share.toFixed(3)}</td></tr>`).join('')||'<tr><td colspan="3">검색 결과가 없습니다.</td></tr>'}</tbody></table></div>`;
 }
 function detail(s,st){const home=s.areas.find(a=>a.id===st.area),row=flows(s,{...st,query:''}).find(r=>r.partner.id===st.partner);
  if(!row)return `<p>상대국을 선택하면 정확한 금액·분모·보고 범위를 확인할 수 있습니다.</p><p>${E(home.official_name||home.name)} · UN ${home.code} · ${E(home.coverage||'자료 미확보')}</p>`;
  const link=s.source+'?period='+s.year+'&reporterCode='+row.from.code+'&partnerCode='+row.to.code+'&cmdCode=TOTAL&flowCode=X&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500';
  return `<h3>${E(row.from.name)} → ${E(row.to.name)}</h3><p class="trade-exact"><b>${E(exact(row.usd))} USD</b> · ${s.year}년 상품 총수출</p><p>분모: ${E(row.from.name)} 대세계 수출 ${E(exact(row.from.world_usd))} USD · ${row.share==null?'비중 미산출':row.share.toFixed(6)+'%'}</p>
   <p>수출 보고지역: ${E(row.from.official_name||row.from.name)} (UN ${row.from.code})<br>${E(row.from.coverage||'자료 미확보')}<br>목적 통계지역: ${E(row.to.official_name||row.to.name)} (UN ${row.to.code})</p>
   <p>자료 확보: ${E(row.from.retrieved_at||'미확보')} · 확인: ${E(row.from.checked_at||'미확인')}<br>HS 분류 ${E(row.from.classifications.join(' / ')||'미확보')} · 직접 보고 플래그 ${row.reported==null?'—':row.reported?'true':'false'} · 집계 플래그 ${row.aggregate==null?'—':row.aggregate?'true':'false'}</p>
   <p>${row.usd==null?'이 방향의 관측값이 없습니다. 0 또는 상대국 수입값으로 채우지 않았습니다.':'TOTAL은 모든 상품의 합계입니다. 집계 플래그는 합산 여부이며 추정치 여부를 뜻하지 않습니다.'}</p><a href="${E(link)}" target="_blank" rel="noopener noreferrer">UN Comtrade 조회 근거 ↗</a>`;
 }
 function render(s,i){return `<div class="trade-view" data-trade="${i}"><h2>${E(s.title)}</h2><p class="scope-note">${s.year}년 · 상품 총수출(HS TOTAL), 명목 USD · 국가·통계지역45개 · 자료가 없는 방향은 미확보</p><div data-trade-summary></div>
  <div class="trade-toolbar"><label>국가·통계지역 <select data-trade-home>${s.areas.map(a=>`<option value="${E(a.id)}">${E(a.name)}</option>`).join('')}</select></label><label>수출 방향 <select data-trade-direction><option value="out">선택국 → 상대국</option><option value="in">상대국 → 선택국</option></select></label><label>지도 표시 <select data-trade-limit><option value="10">상위10개</option><option value="20">상위20개</option><option value="all">전체</option></select></label><button type="button" data-trade-clear>상대국 선택 해제</button></div>
  <div class="trade-layout"><div><div data-trade-map tabindex="0" aria-label="교역 지구본 회전. 방향키 회전, 더하기와 빼기 확대, Home 초기화"></div><div class="trade-camera"><button type="button" data-trade-spin aria-pressed="false">자동 회전</button><button type="button" data-trade-zoom=".2" aria-label="지구본 확대">＋</button><button type="button" data-trade-zoom="-.2" aria-label="지구본 축소">−</button><button type="button" data-trade-reset>시점 초기화</button></div><div class="trade-camera"><label>경도 <input type="range" min="-180" max="180" data-trade-lon></label><label>위도 <input type="range" min="-80" max="80" data-trade-lat></label></div><p class="quiet" data-trade-map-note>드래그·방향키로 회전, 휠·±로 확대. 얇은 선 → 작은 수출액, 굵은 선 → 큰 수출액(로그 척도).</p><div class="trade-detail" data-trade-detail aria-live="polite"></div></div>
  <aside><div class="trade-toolbar"><label>상대국 검색 <input type="search" data-trade-search placeholder="국가명·코드"></label><label>정렬 <select data-trade-sort><option value="desc">금액 큰 순</option><option value="asc">금액 작은 순</option><option value="name">국가명</option></select></label></div><div data-trade-ledger></div></aside></div>
  <details><summary>통계·지도 범위</summary><p>${E(s.coordinate_note)}</p><p>UN490은 Other Asia, nes로 대만 및 아시아의 미지정 지역 보고가 포함될 수 있습니다. 미국·프랑스·스위스·노르웨이는 UN의 관세 통계지역을 사용하며 국가 선택 상세에 포함 범위를 표시합니다.</p><p>45개 지역의 파트너만 표시합니다. 대세계 수출과의 차이는 나머지 파트너·미분류 지역 등이며, 수입액·순수출·기업별 매출로 해석하지 않습니다. ${s.year}년 자료는30일마다 재확인하며 과거 수정 전 실시간 빈티지가 아닙니다.</p><a href="https://uncomtrade.org/docs/reporter-country-codes-and-their-custom-areas/" target="_blank" rel="noopener noreferrer">UN 통계지역 정의 ↗</a> · <a href="https://uncomtrade.org/docs/taiwan-province-of-china-trade-data/" target="_blank" rel="noopener noreferrer">UN490 정의 ↗</a></details></div>`;}
 function dispose(){while(disposers.length)disposers.pop()();}
 function bind(container,d,state={}){container.querySelectorAll('[data-trade]').forEach(box=>{
  const s=d.sections[+box.dataset.trade],st=state.trade||(state.trade={area:'KR',direction:'out',query:'',sort:'desc',limit:'20',partner:'',lon:128,lat:36,zoom:1}),q=sel=>box.querySelector(sel),canvas=q('[data-trade-map]');let coasts=[],active=true,spin=false,frame=0,last=0,drag=null,moved=false;
  const stop=()=>{spin=false;q('[data-trade-spin]').setAttribute('aria-pressed','false');if(frame)cancelAnimationFrame(frame);frame=0;};
  const draw=()=>{canvas.innerHTML=map(s,st,coasts);q('[data-trade-lon]').value=st.lon;q('[data-trade-lat]').value=st.lat;};
  const update=()=>{q('[data-trade-summary]').innerHTML=summary(s,st);q('[data-trade-ledger]').innerHTML=ledger(s,st);q('[data-trade-detail]').innerHTML=detail(s,st);draw();};
  const focusHome=()=>{const a=s.areas.find(a=>a.id===st.area);st.lon=a.lon;st.lat=a.lat;st.zoom=1;};
  const choose=id=>{stop();st.area=id;st.partner='';q('[data-trade-home]').value=id;focusHome();update();};
  for(const [sel,key] of [['home','area'],['direction','direction'],['limit','limit'],['sort','sort']]){const el=q('[data-trade-'+sel+']');el.value=st[key];el.addEventListener('change',()=>{if(sel==='home')choose(el.value);else{st[key]=el.value;if(sel==='direction')st.partner='';update();}});}
  q('[data-trade-search]').value=st.query;q('[data-trade-search]').addEventListener('input',e=>{st.query=e.target.value;st.partner='';update();});
  q('[data-trade-clear]').addEventListener('click',()=>{st.partner='';update();});
  q('[data-trade-ledger]').addEventListener('click',e=>{const b=e.target.closest('[data-trade-partner]');if(!b)return;stop();st.partner=b.dataset.tradePartner;update();});
  canvas.addEventListener('click',e=>{const b=e.target.closest('[data-trade-area]');if(b&&!moved)choose(b.dataset.tradeArea);});
  canvas.addEventListener('keydown',e=>{const b=e.target.closest('[data-trade-area]');if(b&&(e.key==='Enter'||e.key===' ')){e.preventDefault();choose(b.dataset.tradeArea);canvas.focus();return;}
   const keys={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,10],ArrowDown:[0,-10]};if(keys[e.key]){e.preventDefault();stop();st.lon=((st.lon+keys[e.key][0]+540)%360)-180;st.lat=clamp(st.lat+keys[e.key][1],-80,80);draw();}
   if(['+','=','-','Home'].includes(e.key)){e.preventDefault();stop();if(e.key==='Home')focusHome();else st.zoom=clamp(st.zoom+(e.key==='-'?-.2:.2),.7,2.5);draw();}});
  canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;stop();moved=false;drag={x:e.clientX,y:e.clientY,lon:st.lon,lat:st.lat,id:e.pointerId,area:e.target.closest('[data-trade-area]')?.dataset.tradeArea};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>4)moved=true;if(!moved)return;st.lon=((drag.lon-dx*.35+540)%360)-180;st.lat=clamp(drag.lat+dy*.25,-80,80);draw();});
  const release=e=>{if(drag?.id!==e.pointerId)return;const id=drag.area;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);drag=null;if(id&&!moved&&e.type==='pointerup'){choose(id);moved=true;}};canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);
  canvas.addEventListener('wheel',e=>{e.preventDefault();stop();st.zoom=clamp(st.zoom+(e.deltaY<0?.1:-.1),.7,2.5);draw();},{passive:false});
  box.querySelectorAll('[data-trade-zoom]').forEach(b=>b.addEventListener('click',()=>{stop();st.zoom=clamp(st.zoom+Number(b.dataset.tradeZoom),.7,2.5);draw();}));
  for(const key of ['lon','lat'])q('[data-trade-'+key+']').addEventListener('input',e=>{stop();st[key]=Number(e.target.value);draw();});
  q('[data-trade-reset]').addEventListener('click',()=>{stop();focusHome();draw();});
  const tick=t=>{if(!active||!spin||box.isConnected===false)return;if(t-last>90&&!document.hidden){st.lon=((st.lon+.4+540)%360)-180;draw();last=t;}frame=requestAnimationFrame(tick);};
  q('[data-trade-spin]').addEventListener('click',()=>{if(spin)stop();else{spin=true;q('[data-trade-spin]').setAttribute('aria-pressed','true');frame=requestAnimationFrame(tick);}});
  if(!coastPromise)coastPromise=fetch('data/coastlines.json').then(r=>{if(!r.ok)throw Error('coast');return r.json();});
  coastPromise.then(data=>{if(!active)return;coasts=data.arcs;draw();}).catch(()=>{coastPromise=null;if(active)q('[data-trade-map-note]').textContent='지도 경계를 불러오지 못했습니다. 교역선·국가 선택과 수출 원장은 사용할 수 있습니다.';});
  disposers.push(()=>{active=false;stop();});update();
 });}
 root.TradeViews={render,bind,dispose,map,flows,greatCircle,width,exact,summary,ledger,detail};
})(typeof window==='undefined'?globalThis:window);
