/* Research-sector directory. Company evidence and national trade stay distinct. */
(function(root){
 'use strict';
 const E=root.ResearchCharts.esc,RAD=Math.PI/180,clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
 let coastPromise;const disposers=[];
 const num=v=>v==null?'미확보':Number(v).toLocaleString('ko-KR',{maximumFractionDigits:0});
 const time=v=>v?new Date(v*1000).toISOString().replace('T',' ').replace('.000Z',' UTC'):'미확보';
 const link=(url,label)=>url&&/^https?:\/\//.test(url)?`<a href="${E(url)}" target="_blank" rel="noopener noreferrer">${E(label)} ↗</a>`:E(label);
 function cities(s){const found=new Map();for(const c of s.companies){if(!c.location)continue;const id=c.location.id;if(!found.has(id))found.set(id,{...c.location,companies:[]});found.get(id).companies.push(c);}return [...found.values()];}
 function routes(s,st){
  const c=s.companies.find(c=>c.symbol===st.symbol);if(!c)return [];
  const company=symbol=>s.companies.find(c=>c.symbol===symbol),area=code=>s.trade_areas.find(a=>a.id===code),companyArea=code=>(s.company_areas||[]).find(a=>a.id===code)||area(code);
  const out=s.relations.filter(r=>r.source===c.symbol||r.target===c.symbol).map(r=>({...r,
   from:companyArea(company(r.source)?.country_code),to:companyArea(company(r.target)?.country_code),
   label:company(r.source)?.name+' → '+company(r.target)?.name+' · '+r.label}));
  const home=area(c.country_code);
  if(home)out.push(...[...home.exports].sort((a,b)=>Number(b[1])-Number(a[1])).slice(0,5).map((r,i)=>({
   id:'trade-'+i,kind:'export',from:home,to:area(r[0]),usd:r[1],label:'소재국 상품 총수출 · '+s.trade_year+'년',
   evidence:{title:'UN Comtrade 국가 총수출',url:'https://comtradeapi.un.org/public/v1/preview/C/A/HS?period='+s.trade_year+'&reporterCode='+home.code+'&partnerCode='+area(r[0])?.code+'&cmdCode=TOTAL&flowCode=X&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500'}})));
  return out;
 }
 function map(s,st,coasts=[]){
  const cx=320,cy=255,radius=244*st.zoom,lon=st.lon*RAD,lat=st.lat*RAD;
  const project=([x,y])=>{const l=x*RAD-lon,f=y*RAD;return [Math.cos(f)*Math.sin(l),-(Math.cos(lat)*Math.sin(f)-Math.sin(lat)*Math.cos(f)*Math.cos(l)),Math.sin(lat)*Math.sin(f)+Math.cos(lat)*Math.cos(f)*Math.cos(l)];};
  const screen=p=>[cx+radius*p[0],cy+radius*p[1]];
  const edge=(a,b)=>{const t=a[2]/(a[2]-b[2]),x=a[0]+t*(b[0]-a[0]),y=a[1]+t*(b[1]-a[1]),n=Math.hypot(x,y);return [x/n,y/n,0];};
  function path(points){let prev=null,started=false,out='';const add=(p,move)=>{const [x,y]=screen(p);out+=(move?'M':'L')+x.toFixed(2)+','+y.toFixed(2);};
   for(const coords of points){const p=project(coords);if(p[2]>=0){if(prev&&prev[2]<0){add(edge(prev,p),true);started=true;}add(p,!started);started=true;}else{if(prev&&prev[2]>=0)add(edge(prev,p),false);started=false;}prev=p;}return out;}
  let out=`<circle cx="${cx}" cy="${cy}" r="${radius}" fill="#edf5f5" stroke="#86a2a9"/>`;
  for(let f=-80;f<=80;f+=10)out+=`<path d="${path(Array.from({length:181},(_,i)=>[-180+i*2,f]))}" fill="none" stroke="#d1e1e5" stroke-width=".6"/>`;
  for(let l=-180;l<180;l+=10)out+=`<path d="${path(Array.from({length:91},(_,i)=>[l,-90+i*2]))}" fill="none" stroke="#d1e1e5" stroke-width=".6"/>`;
  out+=coasts.map(c=>`<path d="${path(c)}" fill="none" stroke="#789690" stroke-width=".8"/>`).join('');
  const colors={valuechain:'#905825',export:'#147587',logistics:'#7061a3'},endpoints=new Map();
  for(const r of routes(s,st)){if(!st.kinds[r.kind]||!r.from||!r.to||r.from.id===r.to.id)continue;
   const points=root.TradeViews.greatCircle(r.from,r.to);out+=`<path data-chain-arc="${E(r.kind)}" d="${path(points)}" fill="none" stroke="${colors[r.kind]}" stroke-opacity=".8" stroke-width="${r.kind==='export'?root.TradeViews.width(r.usd):1.8}"><title>${E(r.label)}</title></path>`;
   endpoints.set(r.from.id,r.from);endpoints.set(r.to.id,r.to);
  }
  for(const a of endpoints.values()){const p=project([a.lon,a.lat]);if(p[2]<0)continue;const [x,y]=screen(p);out+=`<circle cx="${x}" cy="${y}" r="3" fill="#b27a1e"/><text x="${x+7}" y="${y-7}" font-size="11" fill="#324b57">${E(a.name)}</text>`;}
  for(const city of cities(s).sort((a,b)=>Number(a.companies.some(c=>c.symbol===st.symbol))-Number(b.companies.some(c=>c.symbol===st.symbol)))){const p=project([city.lon,city.lat]);if(p[2]<0)continue;const [x,y]=screen(p),selected=city.companies.some(c=>c.symbol===st.symbol);
   out+=`<g role="button" tabindex="0" data-chain-city="${E(city.id)}" aria-label="${E(city.name)} · ${city.companies.length}개 기업"><circle cx="${x}" cy="${y}" r="${selected?7:Math.min(3+.6*city.companies.length,7)}" fill="${selected?'#bb7627':'#196d80'}" stroke="white" stroke-width="1"/><title>${E(city.name)} · ${E(city.companies.slice(0,6).map(c=>c.name).join(', '))}${city.companies.length>6?' 외 '+(city.companies.length-6)+'개':''}</title></g>`;
  }
  return `<svg viewBox="0 0 640 520" role="img" aria-label="기업 도시 및 국가 관계 정사영 지구본">${out}</svg>`;
 }
 function detail(s,st){const c=s.companies.find(c=>c.symbol===st.symbol);if(!c)return '<p>기업을 선택하면 소재지·시가총액·사업 분류와 관계 근거를 확인할 수 있습니다.</p>';
  const all=routes(s,st),location=c.location;
  return `<h3>${E(c.name)} <small>${E(c.symbol)}</small></h3>${c.previous_symbol?'<p>'+link(c.symbol_source,c.previous_symbol+' → '+c.symbol+' 종목코드 변경')+'</p>':''}<p>프로필 소재지: ${E(c.city||'도시 미확보')} · ${E(c.country||'국가 미확보')}${location?' · '+link(location.source,'도시 대표 좌표'):' · 좌표 미확인'}</p>
   <p>시가총액: <b>${num(c.market_cap)} ${E(c.cap_currency||'')}</b>${c.cap_unit_pending?' · 통화 단위 확인 필요':''}<br>시장 시각 ${time(c.quote_time)} · 프로필 확인 ${E(c.checked_at||'미확보')}${c.stale?' · 7일 이상 경과':''}</p>
   <p>공급자 사업 분류: ${E([c.sector,c.industry].filter(Boolean).join(' / ')||'미확보')}<br>${link('https://finance.yahoo.com/quote/'+encodeURIComponent(c.symbol)+'/profile/','Yahoo 기업 프로필')} · ${link(c.website,'회사 웹사이트')}</p>
   ${['valuechain','export','logistics'].map(kind=>{const rows=all.filter(r=>r.kind===kind),title={valuechain:'공급 관계 근거',export:'소재국 교역 맥락',logistics:'물류·공급 경로 근거'}[kind];return `<section class="chain-route-section"><h4>${title}</h4>${kind==='export'?'<p class="quiet">소재국의 상위5개 상대 지역 총수출입니다. 선택 기업의 수출액·상품별 무역·실제 운송 경로를 뜻하지 않습니다.</p>':''}${rows.length?`<ul>${rows.map(r=>`<li>${E(r.label)}${r.usd?' · '+E(r.from.name)+' → '+E(r.to?.name||'미확인')+' · '+num(r.usd)+' USD':''}<br>${link(r.evidence?.url,r.evidence?.title||'근거 미확보')}${r.from&&r.to&&r.from.id===r.to.id?' · 동일 국가 소재 기업 관계':''}</li>`).join('')}</ul>`:'<p class="quiet">확인된 관계 근거가 아직 없습니다.</p>'}</section>`;}).join('')}
   <p class="scope-note">사업 분류는 경쟁우위 평가가 아닙니다. 회사 소재지와 공장 위치·실제 공급 경로는 다를 수 있으며, 회사 웹사이트 링크 자체를 공급 계약의 근거로 사용하지 않습니다.</p>`;
 }
 function tables(s){const bySymbol=new Map(s.companies.map(c=>[c.symbol,c]));return s.groups.map(g=>`<section class="chain-sector-group"><h3>${E(g.name)}</h3>${s.sectors.filter(a=>a.group===g.id).map(a=>`<section id="chain-${E(a.id)}" class="chain-sector"><h4 tabindex="-1">${E(a.name)}</h4><div class="table-scroll"><table class="data-table" aria-label="${E(a.name)} 기업"><thead><tr><th>번호</th><th>기업</th><th>프로필 소재지</th><th>시가총액·표시 통화</th><th>사업 분류·참조</th></tr></thead><tbody>${a.symbols.map((symbol,i)=>{const c=bySymbol.get(symbol);return `<tr><td>${i+1}</td><td><button type="button" data-chain-company="${E(symbol)}">${E(c.name)}</button><small>${E(symbol)}</small></td><td>${E(c.country||'미확보')}<br>${E(c.city||'도시 미확보')}</td><td title="확인 ${E(c.checked_at||'미확보')}">${num(c.market_cap)} ${E(c.cap_currency||'')}<small>${c.cap_unit_pending?'단위 확인 필요':c.stale?'7일 이상 경과':c.checked_at?.slice(0,10)||''}</small></td><td>${E(c.industry||'분류 미확보')}<br>${link(c.website,'회사 웹사이트')}</td></tr>`;}).join('')}</tbody></table></div></section>`).join('')}</section>`).join('');}
 function render(s,i){const count=cities(s),mapped=s.companies.filter(c=>c.location).length;return `<div class="chain-view" data-chain="${i}"><h2>${E(s.title)}</h2>
  <div class="chain-kpis"><p><strong>${s.sectors.length}</strong> 세부 업종</p><p><strong>${s.companies.length}</strong> 기업 · ${s.sectors.reduce((n,a)=>n+a.symbols.length,0)}개 배치</p><p><strong>${count.length}</strong> 확인된 도시 · ${mapped}/${s.companies.length}기업 좌표</p></div>
  <p class="scope-note">${E(s.scope)}. 업종 내 번호는 탐색 순서입니다. 프로필 소재지와 도시 대표 좌표를 연결하며 본사 건물 위치·생산시설 위치와 구분합니다.</p>
  <div class="chain-layout"><div><label class="chain-picker">기업 선택 <select data-chain-select><option value="">전체 도시 탐색</option>${s.companies.map(c=>`<option value="${E(c.symbol)}">${E(c.name)} (${E(c.symbol)})</option>`).join('')}</select></label>
   <label class="chain-picker">도시 선택 <select data-chain-city-select><option value="">지도에서 도시 선택</option>${count.sort((a,b)=>a.name.localeCompare(b.name)).map(a=>`<option value="${E(a.id)}">${E(a.name)} · ${E(a.country)} (${a.companies.length})</option>`).join('')}</select></label>
   <div class="chain-map" data-chain-map tabindex="0" aria-label="기업 지구본. 방향키 회전, 더하기와 빼기 확대, Home 초기화"></div>
   <div class="chain-controls"><button type="button" data-chain-spin aria-pressed="false">자동 회전</button><button type="button" data-chain-zoom=".2" aria-label="기업 지구본 확대">＋</button><button type="button" data-chain-zoom="-.2" aria-label="기업 지구본 축소">−</button><button type="button" data-chain-reset>초기화</button><button type="button" data-chain-clear>선택 해제</button></div>
   <div class="chain-controls">${[['valuechain','공급 관계'],['export','소재국 총수출'],['logistics','물류·공급']].map(([k,n])=>`<label><input type="checkbox" data-chain-kind="${k}" checked> ${n}</label>`).join('')}</div>
   <p class="quiet" data-chain-map-note>도시를 누르면 해당 기업들을 선택할 수 있습니다. 관계선의 끝점은 국가 대표점이며 실제 운송 경로가 아닙니다.</p><div data-chain-city-options></div>
   <div class="chain-detail" data-chain-detail aria-live="polite"></div></div>
   <nav class="chain-index" aria-label="세부 업종 바로가기">${s.groups.map(g=>`<div><h3>${E(g.name)}</h3>${s.sectors.filter(a=>a.group===g.id).map(a=>`<button type="button" data-chain-sector="${E(a.id)}">${E(a.name)}</button>`).join('')}</div>`).join('')}</nav></div>
  <p class="quiet">좌표: ${link('https://www.geonames.org/','GeoNames')} · ${link('https://creativecommons.org/licenses/by/4.0/','CC BY 4.0')} · 지명 데이터 ${E(s.geo_source.retrieved_at?.slice(0,10)||'미확보')} · 국가 경계 Natural Earth. 프로필은 PC에서24시간마다 확인합니다.</p>${tables(s)}</div>`;}
 function dispose(){while(disposers.length)disposers.pop()();}
 function bind(container,data,state={}){container.querySelectorAll('[data-chain]').forEach(box=>{
  const s=data.sections[+box.dataset.chain],q=sel=>box.querySelector(sel),canvas=q('[data-chain-map]');
  const st=state.chain||(state.chain={symbol:'',city:'',lon:10,lat:20,zoom:1,kinds:{valuechain:true,export:true,logistics:true}});
  let active=true,coasts=[],spin=false,frame=0,last=0,drag=null,moved=false;
  const stop=()=>{spin=false;q('[data-chain-spin]').setAttribute('aria-pressed','false');if(frame)cancelAnimationFrame(frame);frame=0;};
  const draw=()=>{canvas.innerHTML=map(s,st,coasts);};
  const update=()=>{q('[data-chain-select]').value=st.symbol;q('[data-chain-city-select]').value=st.city;q('[data-chain-detail]').innerHTML=detail(s,st);
   const city=cities(s).find(c=>c.id===st.city);q('[data-chain-city-options]').innerHTML=city?`<p>${E(city.name)} · ${city.companies.map(c=>`<button type="button" data-chain-company="${E(c.symbol)}">${E(c.name)}</button>`).join(' ')}</p>`:'';draw();};
  const choose=symbol=>{stop();st.symbol=symbol;st.city='';const c=s.companies.find(c=>c.symbol===symbol),a=c?.location||(s.company_areas||[]).find(a=>a.id===c?.country_code)||s.trade_areas.find(a=>a.id===c?.country_code);if(a){st.lon=a.lon;st.lat=a.lat;st.zoom=1;}update();};
  const chooseCity=id=>{stop();st.city=id;const city=cities(s).find(c=>c.id===id);if(city){st.lon=city.lon;st.lat=city.lat;}update();};
  q('[data-chain-select]').addEventListener('change',e=>choose(e.target.value));
  q('[data-chain-city-select]').addEventListener('change',e=>chooseCity(e.target.value));
  box.addEventListener('click',e=>{const company=e.target.closest('[data-chain-company]'),sector=e.target.closest('[data-chain-sector]'),city=e.target.closest('[data-chain-city]');
   if(company){choose(company.dataset.chainCompany);q('[data-chain-select]').scrollIntoView({block:'center'});q('[data-chain-select]').focus();}
   else if(sector){const heading=q('#chain-'+sector.dataset.chainSector+' h4');heading.scrollIntoView({block:'start'});heading.focus({preventScroll:true});}
   else if(city&&!moved)chooseCity(city.dataset.chainCity);});
  box.querySelectorAll('[data-chain-kind]').forEach(c=>{c.checked=st.kinds[c.dataset.chainKind];c.addEventListener('change',()=>{st.kinds[c.dataset.chainKind]=c.checked;draw();});});
  q('[data-chain-clear]').addEventListener('click',()=>choose(''));
  const reset=()=>{stop();st.lon=10;st.lat=20;st.zoom=1;draw();};q('[data-chain-reset]').addEventListener('click',reset);
  box.querySelectorAll('[data-chain-zoom]').forEach(b=>b.addEventListener('click',()=>{stop();st.zoom=clamp(st.zoom+Number(b.dataset.chainZoom),.8,3);draw();}));
  canvas.addEventListener('keydown',e=>{const city=e.target.closest('[data-chain-city]');if(city&&['Enter',' '].includes(e.key)){e.preventDefault();chooseCity(city.dataset.chainCity);canvas.focus();return;}
   const turns={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,10],ArrowDown:[0,-10]};if(turns[e.key]){e.preventDefault();stop();st.lon=((st.lon+turns[e.key][0]+540)%360)-180;st.lat=clamp(st.lat+turns[e.key][1],-80,80);draw();}
   if(['+','=','-','Home'].includes(e.key)){e.preventDefault();if(e.key==='Home')reset();else{stop();st.zoom=clamp(st.zoom+(e.key==='-'?-.2:.2),.8,3);draw();}}});
  canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;stop();moved=false;drag={x:e.clientX,y:e.clientY,lon:st.lon,lat:st.lat,id:e.pointerId,city:e.target.closest('[data-chain-city]')?.dataset.chainCity};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>4)moved=true;if(moved){st.lon=((drag.lon-dx*.35+540)%360)-180;st.lat=clamp(drag.lat+dy*.25,-80,80);draw();}});
  const release=e=>{if(drag?.id!==e.pointerId)return;const id=drag.city;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);drag=null;if(id&&!moved&&e.type==='pointerup'){chooseCity(id);moved=true;}};
  canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);
  canvas.addEventListener('wheel',e=>{e.preventDefault();stop();st.zoom=clamp(st.zoom+(e.deltaY<0?.1:-.1),.8,3);draw();},{passive:false});
  const tick=t=>{if(!active||!spin||box.isConnected===false)return;if(t-last>90&&!document.hidden){st.lon=((st.lon+.4+540)%360)-180;draw();last=t;}frame=requestAnimationFrame(tick);};
  q('[data-chain-spin]').addEventListener('click',()=>{if(spin)stop();else{spin=true;q('[data-chain-spin]').setAttribute('aria-pressed','true');frame=requestAnimationFrame(tick);}});
  if(!coastPromise)coastPromise=fetch('data/coastlines.json').then(r=>{if(!r.ok)throw Error('map');return r.json();});
  coastPromise.then(d=>{if(active){coasts=d.arcs;draw();}}).catch(()=>{coastPromise=null;if(active)q('[data-chain-map-note]').textContent='지도 경계를 불러오지 못했습니다. 기업 표와 도시 선택은 계속 사용할 수 있습니다.';});
  disposers.push(()=>{active=false;stop();});update();
 });}
 root.ChainViews={render,bind,dispose,cities,routes,map,detail,tables};
})(typeof window==='undefined'?globalThis:window);
