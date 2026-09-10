/* Dated Sentinel observations over an optional NASA GIBS global context layer. */
(function(root){
 'use strict';const E=root.ResearchCharts.esc,R=6378137,S=2*Math.PI*R,heights=[400,560,760],MAX_LAT=85.0511287798066;let coastPromise;const disposers=[];
 const state={lon:0,lat:20,zoom:1,size:1,selected:'',mode:'rgb',background:'nasa',width:1000,initialized:false};
 const safe=u=>typeof u==='string'&&u.startsWith('https://')?u:'#';
 const asset=p=>/^data\/satellite\/ST_[A-Z_]+-(rgb|ndvi)\.png$/.test(p||'')?p:'';
 const pct=v=>typeof v==='number'?(v*100).toFixed(1)+'%':'—';
 const status={ok:'관측 확보',stale:'이전 관측 유지',pending_location:'위치 대조 중',not_collected:'관측 준비',no_clear_scene:'유효 영상 없음',error:'수집 실패',location_changed:'위치 재검증 중'};
 function merc(lon,lat){const f=Math.max(-MAX_LAT,Math.min(MAX_LAT,lat))*Math.PI/180;return [R*lon*Math.PI/180,R*Math.log(Math.tan(Math.PI/4+f/2))];}
 function inverse(x,y){return [x/R*180/Math.PI,(2*Math.atan(Math.exp(y/R))-Math.PI/2)*180/Math.PI];}
 function camera(c,dx=0,dy=0,dz=0){const z=Math.max(1,Math.min(19,c.zoom+dz)),scale=256*2**c.zoom/S,[x,y]=merc(c.lon,c.lat),[lon,lat]=inverse(x-dx/scale,y+dy/scale);return {...c,lon:((lon+180)%360+360)%360-180,lat:Math.max(-MAX_LAT,Math.min(MAX_LAT,lat)),zoom:z};}
 function focus(c,s){return s?.location_status==='reviewed'?{...c,lon:s.lon,lat:s.lat,zoom:14,selected:s.id}:s?{...c,selected:s.id}:c;}
 function fit(s,c){
  const pts=s.sites.filter(a=>a.location_status==='reviewed').map(a=>merc(a.lon,a.lat));if(!pts.length)return c;
  const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),w=Math.min(...xs),e=Math.max(...xs),so=Math.min(...ys),n=Math.max(...ys);
  const [lon,lat]=inverse((w+e)/2,(so+n)/2),scale=Math.min(((c.width||1000)-90)/Math.max(1,e-w),(heights[c.size]-90)/Math.max(1,n-so));
  return {...c,lon,lat,zoom:Math.max(1,Math.min(6,Math.floor(Math.log2(scale*S/256)))),selected:''};
 }
 function map(s,c=state,arcs=[],tiles=[]){
  const W=c.width||1000,H=heights[c.size],scale=256*2**c.zoom/S,center=merc(c.lon,c.lat),world=S*scale;
  const p=(x,y)=>[W/2+(x-center[0])*scale,H/2-(y-center[1])*scale];let body='';
  for(const t of tiles){if(/^blob:/.test(t.href||''))body+=`<image data-sat-tile="${E(t.key)}" href="${E(t.href)}" x="${t.left}" y="${t.top}" width="${t.size+.25}" height="${t.size+.25}" preserveAspectRatio="none"/>`;}
  // Repeat geographic overlays at the date line, with the same wrapped tile grid.
  const start=Math.floor((c.lon+180)/360-W/world/2),end=Math.floor((c.lon+180)/360+W/world/2);
  for(let copy=start;copy<=end;copy++){
   const ll=(lon,lat)=>{const q=p(...merc(lon,lat));return [q[0]+copy*world,q[1]];};
   if(c.zoom<10)for(const a of arcs){let path='',prev=null;for(const v of a){const q=ll(...v);path+=(prev&&Math.abs(q[0]-prev[0])<world/2?'L':'M')+q.map(n=>n.toFixed(2)).join(',');prev=q;}body+=`<path d="${path}" fill="none" stroke="${c.background==='nasa'?'#b7cbd0':'#a6bcc6'}" stroke-opacity=".65" stroke-width="1"/>`;}
   if(c.zoom<6&&c.background!=='nasa'){for(let lon=-180;lon<=180;lon+=30){const a=ll(lon,-MAX_LAT),b=ll(lon,MAX_LAT);body+=`<path d="M${a}L${b}" stroke="#d5e1e5"/>`;}for(let lat=-60;lat<=60;lat+=30){const a=ll(-180,lat),b=ll(180,lat);body+=`<path d="M${a}L${b}" stroke="#d5e1e5"/>`;}}
   for(const site of s.sites){
    const scene=site.scene;if(!scene)continue;
    const [w,so,e,n]=scene.bounds_mercator,[xx,y]=p(w,n),[xx1,y1]=p(e,so),x=xx+copy*world,x1=xx1+copy*world;
    if(x1<0||x>W||y1<0||y>H)continue;
    // An opaque matte prevents old basemap pixels from filling masked observations.
    body+=`<rect data-sat-mask="${E(site.id)}" x="${x}" y="${y}" width="${x1-x}" height="${y1-y}" fill="#e9edf0"/><image href="${E(asset(scene.images[c.mode]?.path))}" x="${x}" y="${y}" width="${x1-x}" height="${y1-y}" preserveAspectRatio="none"/><rect x="${x}" y="${y}" width="${x1-x}" height="${y1-y}" fill="none" stroke="#f6f0b5" stroke-width="1.2"/>`;
   }
   for(const site of s.sites.filter(a=>a.location_status==='reviewed')){const [x,y]=ll(site.lon,site.lat);if(x<0||x>W||y<0||y>H)continue;body+=`<g data-sat-marker="${E(site.id)}" role="button" tabindex="0" aria-label="${E(site.name)}"><circle cx="${x}" cy="${y}" r="${site.id===c.selected?9:6}" fill="${site.scene?'#145c78':'#8d7666'}" stroke="white" stroke-width="2"/><title>${E(site.name)}</title>${site.id===c.selected?`<text x="${x+14}" y="${y-14}" class="sat-map-label">${E(site.name)}</text>`:''}</g>`;}
  }
  const ground=S/(256*2**c.zoom)*Math.cos(c.lat*Math.PI/180),target=ground*120,power=10**Math.floor(Math.log10(target)),dist=[1,2,5,10].map(n=>n*power).filter(n=>n<=target).pop()||power,len=dist/ground;
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" role="img" aria-label="시설 관측 지도 · 확대 ${c.zoom}"><defs><clipPath id="sat-map-clip"><rect width="${W}" height="${H}"/></clipPath></defs><rect width="${W}" height="${H}" fill="#e9f0f3"/><g clip-path="url(#sat-map-clip)">${body}</g><rect x="16" y="${H-63}" width="260" height="45" rx="4" fill="white" fill-opacity=".86"/><path d="M25 ${H-35}v6h${len}v-6" fill="none" stroke="#193c50" stroke-width="2"/><text x="25" y="${H-42}" class="axis">${dist>=1000?dist/1000+'km':dist+'m'} · 중심 위도 기준</text><text x="${W-25}" y="30" text-anchor="end" class="sat-map-label">N ↑</text></svg>`;
 }
 function details(site,mode='rgb'){
  if(!site)return '<p>시설을 선택하세요.</p>';const a=site.scene;
  return `<article class="panel sat-facts"><h3>${E(site.name)}</h3><p>${E(site.category)} · ${E(site.address)}</p><p>${E(status[site.status]||site.status)}${a?' · 촬영 '+E(a.captured_at.replace('T',' ').replace('Z',' UTC')):''}</p>${a?`<img class="sat-detail-image" src="${E(asset(a.images[mode].path))}" alt="${E(site.name)} ${mode==='rgb'?'자연색':'NDVI'} 관측" width="400" height="400"><p>맑은 영역 ${pct(a.clear_fraction)} · 중심1km ${pct(a.core_clear_fraction)} · NDVI 유효 영역 ${pct(a.valid_fraction)} · 유효 화소 NDVI 중앙값 ${a.ndvi_median.toFixed(3)}</p><p class="quiet">RGB 표시 반사도0~${a.rgb_reflectance_max||.3} · 화소10m · 구름 분류20m · 북쪽이 위 · 투명/회색 영역은 관측 제외</p><a href="${E(safe(a.source))}" target="_blank" rel="noopener noreferrer">촬영 장면·원자료 메타데이터 ↗</a>`:'<p>이 시설의 사용할 수 있는 영상이 아직 없습니다.</p>'}<p>${E(site.scope)}</p><p class="quiet">${E(site.review_note)}</p>${site.lat!==null?`<p>관측 기준점 ${site.lat.toFixed(5)}, ${site.lon.toFixed(5)}</p><div class="tags"><a href="${E(safe(site.coordinate_source))}" target="_blank" rel="noopener noreferrer">위치 근거 ↗</a><a href="https://www.google.com/maps/@${site.lat},${site.lon},1500m/data=!3m1!1e3" target="_blank" rel="noopener noreferrer">외부 위성지도 ↗</a><a href="https://earth.google.com/web/@${site.lat},${site.lon},300a,1500d,35y,0h,0t,0r" target="_blank" rel="noopener noreferrer">Google Earth ↗</a></div>`:''}<ul>${site.sources.map(r=>`<li><a href="${E(safe(r.url))}" target="_blank" rel="noopener noreferrer">${E(r.title)}</a></li>`).join('')}</ul>${site.entity_id?`<button data-sat-company="${E(site.entity_id)}">관련 기업 Entity 360 · ${E(site.symbol)}</button>`:''}</article>`;
 }
 function cards(s){return `<div class="sat-grid">${s.sites.map(site=>{const a=site.scene;return `<article class="panel sat-card" data-sat-card="${E(site.id)}"><h3><button data-sat-focus="${E(site.id)}">${E(site.name)}</button></h3><p>${E(site.category)} · ${E(status[site.status]||site.status)}</p>${a?`<button data-sat-open="${E(site.id)}" class="sat-image-button" aria-label="${E(site.name)} 시설 상세"><img data-sat-image src="${E(asset(a.images.rgb.path))}" width="400" height="400" loading="lazy" alt="${E(site.name)} RGB 관측"></button><div class="title-row"><small>촬영 ${E(a.captured_at.slice(0,10))} UTC</small><button data-sat-toggle="${E(site.id)}" aria-pressed="false">NDVI</button></div><p class="quiet">맑은 영역 ${pct(a.clear_fraction)} · 중심1km ${pct(a.core_clear_fraction)}</p>`:`<p>${E(site.review_note)}</p><button data-sat-open="${E(site.id)}">시설 근거·진행 상태</button>`}</article>`;}).join('')}</div>`;}
 function render(s,i){
  if(s.type==='facilitydetail')return '<div data-facility-detail><label>시설 Entity <select data-facility-select><option value="">선택하세요</option></select></label><div data-facility-output></div></div>';
  return `<div data-satellite="${i}"><p>${s.image_count}/${s.sites.length}시설 관측 · ${s.location_count}곳 위치 대조 · 위치 검토 ${E(s.registry_reviewed_at)}</p><p class="quiet">${E(s.note)}</p><div class="sat-chips">${s.sites.map(a=>`<button data-sat-focus="${E(a.id)}" aria-pressed="${a.id===state.selected}">${E(a.name)}</button>`).join('')}</div><div class="sat-tools"><button data-sat-zoom="1" aria-label="지도 확대">＋</button><button data-sat-zoom="-1" aria-label="지도 축소">−</button><button data-sat-reset>전체 시설</button><button data-sat-size>지도 크기 ${heights[state.size]}px</button><label>배경 <select data-sat-background><option value="nasa">NASA 전 지구 · 2004년</option><option value="coast">해안선만</option></select></label><label>시설 관측 <select data-sat-mode><option value="rgb">RGB 자연색</option><option value="ndvi">NDVI 식생지수</option></select></label></div><p class="quiet">지도를 드래그하거나 방향키로 이동 · +/−로 확대/축소 · 시설 버튼으로 현장 이동</p><div class="sat-map" data-sat-map tabindex="0" aria-label="위성 지도 탐색">${map(s)}</div><p data-sat-basemap-note class="quiet"></p><div class="sat-credits"><a href="https://worldview.earthdata.nasa.gov/" target="_blank" rel="noopener noreferrer">배경: NASA GIBS · Blue Marble (2004-08, MODIS) ↗</a><span>시설: Copernicus Sentinel-2 · 각 촬영일 참조</span></div><p data-sat-map-status role="status"></p><button data-sat-retry hidden>배경 다시 읽기</button><div class="sat-legend"><span>NDVI −1</span><i></i><span>0</span><span>+1</span></div><p class="quiet">고정 색 범위 −1~+1 · 회색/투명: 제외 영역 · NDVI로 공장 가동률을 판정하지 않습니다.</p><div data-sat-detail>${details(s.sites.find(a=>a.id===state.selected),state.mode)}</div><h3>시설별 관측 영상</h3>${cards(s)}<small>${E(s.attribution)}</small></div>`;
 }
 function bind(container,d,navigate,selection={}){
  const s=d.sections.find(r=>r.type==='satellite');if(!s)return;
  const companies=box=>box.querySelectorAll('[data-sat-company]').forEach(b=>b.addEventListener('click',()=>navigate('Entity 360',{entity:b.dataset.satCompany,facility:''})));
  container.querySelectorAll('[data-facility-detail]').forEach(box=>{const select=box.querySelector('[data-facility-select]'),out=box.querySelector('[data-facility-output]');select.innerHTML='<option value="">선택하세요</option>'+s.sites.map(r=>`<option value="${E(r.id)}">${E(r.name)}</option>`).join('');select.value=selection.facility||'';const show=()=>{out.innerHTML=select.value?details(s.sites.find(r=>r.id===select.value)):'';companies(out);};select.addEventListener('change',show);show();});
  container.querySelectorAll('[data-satellite]').forEach(box=>{
   const surface=box.querySelector('[data-sat-map]'),detail=box.querySelector('[data-sat-detail]'),mode=box.querySelector('[data-sat-mode]'),background=box.querySelector('[data-sat-background]');let arcs=[],timer=null,drag=null,visible=true,ended=false,loader=null,resize=null,intersection=null;
   const statusEl=box.querySelector('[data-sat-map-status]'),retry=box.querySelector('[data-sat-retry]');mode.value=state.mode;background.value=state.background;
   state.width=surface.getBoundingClientRect?.().width||1000;if(!state.initialized){Object.assign(state,fit(s,state));state.initialized=true;}
   const tiles=()=>state.background==='nasa'&&root.SatelliteTiles?root.SatelliteTiles.plan(state,state.width,heights[state.size]):[];
   const paint=()=>{if(ended||box.isConnected===false)return;surface.innerHTML=map(s,state,arcs,tiles().map(t=>({...t,href:loader?.lookup(t.key)||''})));box.querySelectorAll('[data-sat-focus]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.satFocus===state.selected)));box.querySelector('[data-sat-basemap-note]').textContent=state.background==='nasa'?'배경은 2004년 8월 합성 지형 영상(원자료 약500m)입니다. 시설의 최근 관측과 날짜가 다르며, 확대해도 배경의 실제 해상도는 늘지 않습니다.':'외부 배경 요청 없이 해안선과 확보한 시설 관측을 표시합니다.';};
   const changed=st=>{paint();if(state.background!=='nasa'){statusEl.textContent='해안선 배경';retry.hidden=true;return;}statusEl.textContent=st.halted?'배경 서비스가 요청을 제한했습니다. 시설 관측은 계속 볼 수 있습니다.':`배경 ${st.loaded}/${st.total}장 표시`+(st.failed?` · ${st.failed}장 읽기 실패. 시설 관측은 계속 볼 수 있습니다.`:'');retry.hidden=!(st.failed||st.halted);};
   if(root.SatelliteTiles&&root.URL?.createObjectURL&&root.AbortController)loader=root.SatelliteTiles.create({onChange:changed});
   const request=()=>{timer=null;if(!loader||ended)return;loader.pause(true);loader.update(tiles());loader.pause(!visible||root.document?.hidden||state.background!=='nasa');};
   const draw=()=>{paint();if(loader){clearTimeout(timer);timer=setTimeout(request,180);}};
   const visibility=()=>{visible=intersection?visible:true;loader?.pause(!visible||root.document?.hidden||state.background!=='nasa');if(visible&&!root.document?.hidden)draw();};
   if(root.IntersectionObserver){intersection=new root.IntersectionObserver(entries=>{visible=entries.some(e=>e.isIntersecting);visibility();});intersection.observe(surface);visible=false;}
   if(root.ResizeObserver){resize=new root.ResizeObserver(()=>{const width=surface.getBoundingClientRect().width;if(width>0&&Math.abs(width-state.width)>1){state.width=width;draw();}});resize.observe(surface);}
   root.document?.addEventListener('visibilitychange',visibility);
   disposers.push(()=>{ended=true;clearTimeout(timer);loader?.dispose();resize?.disconnect();intersection?.disconnect();root.document?.removeEventListener('visibilitychange',visibility);});
   background.addEventListener('change',()=>{state.background=background.value==='nasa'?'nasa':'coast';loader?.pause(state.background!=='nasa');if(state.background!=='nasa'){loader?.update([]);statusEl.textContent='해안선 배경';retry.hidden=true;}draw();});
   retry.addEventListener('click',()=>{loader?.retry();});
   const choose=id=>{const site=s.sites.find(r=>r.id===id);if(!site)return;Object.assign(state,focus(state,site));detail.innerHTML=details(site,state.mode);companies(detail);draw();};
   box.querySelectorAll('[data-sat-focus]').forEach(b=>b.addEventListener('click',()=>choose(b.dataset.satFocus)));
   surface.addEventListener('click',e=>{const marker=e.target.closest?.('[data-sat-marker]');if(marker)choose(marker.dataset.satMarker);});
   surface.addEventListener('keydown',e=>{const marker=e.target.closest?.('[data-sat-marker]');if(marker&&(e.key==='Enter'||e.key===' ')){e.preventDefault();choose(marker.dataset.satMarker);return;}const moves={ArrowLeft:[100,0,0],ArrowRight:[-100,0,0],ArrowUp:[0,100,0],ArrowDown:[0,-100,0],'+':[0,0,1],'=':[0,0,1],'-':[0,0,-1]};if(moves[e.key]){e.preventDefault();Object.assign(state,camera(state,...moves[e.key]));draw();}});
   surface.addEventListener('pointerdown',e=>{if(e.target.closest?.('[data-sat-marker]'))return;drag={x:e.clientX,y:e.clientY,c:{...state},width:surface.getBoundingClientRect().width};loader?.pause(true);clearTimeout(timer);surface.setPointerCapture?.(e.pointerId);});
   surface.addEventListener('pointermove',e=>{if(!drag)return;const scale=state.width/Math.max(1,drag.width);Object.assign(state,camera(drag.c,(e.clientX-drag.x)*scale,(e.clientY-drag.y)*scale));paint();});
   ['pointerup','pointercancel','lostpointercapture'].forEach(type=>surface.addEventListener(type,()=>{if(!drag)return;drag=null;draw();}));
   box.querySelectorAll('[data-sat-zoom]').forEach(b=>b.addEventListener('click',()=>{Object.assign(state,camera(state,0,0,+b.dataset.satZoom));draw();}));
   box.querySelector('[data-sat-reset]').addEventListener('click',()=>{Object.assign(state,fit(s,state));detail.innerHTML=details(null);draw();});
   box.querySelector('[data-sat-size]').addEventListener('click',e=>{state.size=(state.size+1)%heights.length;e.target.textContent='지도 크기 '+heights[state.size]+'px';draw();});
   mode.addEventListener('change',()=>{state.mode=mode.value;detail.innerHTML=details(s.sites.find(a=>a.id===state.selected),state.mode);companies(detail);draw();});
   box.querySelectorAll('[data-sat-open]').forEach(b=>b.addEventListener('click',()=>navigate('Entity 360',{facility:b.dataset.satOpen})));
   box.querySelectorAll('[data-sat-toggle]').forEach(b=>b.addEventListener('click',()=>{const site=s.sites.find(r=>r.id===b.dataset.satToggle),on=b.getAttribute('aria-pressed')!=='true',img=b.closest('[data-sat-card]').querySelector('[data-sat-image]');b.setAttribute('aria-pressed',String(on));img.src=asset(site.scene.images[on?'ndvi':'rgb'].path);img.alt=site.name+(on?' NDVI':' RGB')+' 관측';b.textContent=on?'RGB':'NDVI';}));
   if(!coastPromise)coastPromise=fetch('data/coastlines.json').then(r=>{if(!r.ok)throw Error();return r.json();});coastPromise.then(data=>{arcs=data.arcs;if(box.isConnected!==false)draw();}).catch(()=>{box.querySelector('[data-sat-map-status]').textContent='해안선을 읽지 못했습니다. 시설 위치와 확보 영상은 볼 수 있습니다.';coastPromise=null;});companies(detail);draw();
  });
 }
 root.SatelliteViews={render,bind,map,details,cards,merc,inverse,camera,focus,fit,dispose:()=>{while(disposers.length)disposers.pop()();}};
})(typeof window!=='undefined'?window:globalThis);
