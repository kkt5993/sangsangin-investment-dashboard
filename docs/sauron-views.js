/* Independent Cesium scene. Orbital positions are SGP4 calculations, not telemetry. */
(function(root){
 'use strict';const E=root.ResearchCharts.esc,disposers=[],searchCache=new Map();let loader;
 const STYLES=[['normal','기본','none'],['night','야간투시','brightness(1.25) saturate(.35) sepia(1) hue-rotate(55deg) contrast(1.5)'],['thermal','열화상','contrast(1.5) saturate(2.2) hue-rotate(160deg) brightness(1.1)'],['noir','느와르','grayscale(1) contrast(1.45) brightness(.92)'],['crt','CRT','saturate(1.5) contrast(1.25) brightness(1.05)'],['snow','스노우','brightness(1.22) saturate(.4) contrast(.9)']];
 const COLORS={'반도체':'#5493d3','데이터센터':'#51b8a9','휴머노이드':'#cf82ae','우주':'#ab87d2','에너지':'#d0ae5b'};
 const epoch=p=>Date.parse(p.EPOCH.endsWith('Z')?p.EPOCH:p.EPOCH+'Z');
 function position(p,at,S,maxDays=7){
  const age=(at.getTime()-epoch(p))/864e5;
  if(!Number.isFinite(age)||age < -1||age>maxDays)return {status:'epoch_stale',age};
  const rec=S.json2satrec(p),pv=S.propagate(rec,at);
  if(!pv?.position||rec.error)return {status:'propagation_failed',age,error:rec.error};
  const gd=S.eciToGeodetic(pv.position,S.gstime(at)),lon=S.degreesLong(gd.longitude),lat=S.degreesLat(gd.latitude),height=gd.height;
  if(![lon,lat,height].every(Number.isFinite)||height<=0||height>100000||Math.abs(lat)>90||Math.abs(lon)>180)return {status:'invalid_position',age};
  return {status:'ok',lon,lat,height_km:height,age,at:at.toISOString()};
 }
 function coordinates(text){const m=text.trim().match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);if(!m)return null;const lat=Number(m[1]),lon=Number(m[2]);return Math.abs(lat)<=90&&Math.abs(lon)<=180?{name:'입력 좌표',lat,lon,range:5000,source:'사용자 입력'}:null;}
 function places(data,lang){return Object.values(data.query?.pages||{}).sort((a,b)=>a.index-b.index).flatMap(p=>{const c=p.coordinates?.find(c=>c.globe==='earth'&&Number.isFinite(c.lat)&&Number.isFinite(c.lon)&&Math.abs(c.lat)<=90&&Math.abs(c.lon)<=180);return c?[{name:p.title,lat:c.lat,lon:c.lon,range:150000,source:'Wikipedia 문서 대표 좌표',url:`https://${lang}.wikipedia.org/?curid=${Number(p.pageid)}`}]:[];});}
 async function wikiSearch(text,lang,signal,fetcher=fetch){
  async function query(language,params){
   const url=new URLSearchParams({action:'query',format:'json',origin:'*',...params});
   const response=await fetcher(`https://${language}.wikipedia.org/w/api.php?${url}`,{signal,headers:{'Api-User-Agent':'SangsanginDashboard/1.0 (https://github.com/kkt5993/sangsangin-investment-dashboard)'}});
   if(!response.ok)throw Error('검색 공급자 오류');const body=await response.text();if(body.length>65536)throw Error('검색 응답 크기 초과');const data=JSON.parse(body);if(data.error)throw Error('검색 자료 오류');return data;
  }
  const data=await query(lang,{generator:'search',gsrsearch:text,gsrnamespace:'0',gsrlimit:'5',prop:lang==='ko'?'coordinates|langlinks':'coordinates',colimit:'max',...(lang==='ko'?{lllang:'en',lllimit:'5'}:{})});
  const direct=places(data,lang);if(direct.length||lang!=='ko')return direct;
  const linked=Object.values(data.query?.pages||{}).sort((a,b)=>a.index-b.index).flatMap(p=>{const title=p.langlinks?.find(l=>l.lang==='en')?.['*'];return title?[{title,name:p.title,index:p.index}]:[];}).slice(0,5);
  if(!linked.length)return [];
  const fallback=await query('en',{titles:linked.map(p=>p.title).join('|'),prop:'coordinates',colimit:'max',redirects:'1'});
  return places(fallback,'en').map(p=>{const match=linked.find(l=>l.title===p.name);return {...p,name:match?.name||p.name,index:match?.index||99};}).sort((a,b)=>a.index-b.index);
 }
 async function libraries(){if(!loader)loader=(async()=>{
  const base=new URL('vendor/cesium/',document.baseURI).href;root.CESIUM_BASE_URL=base;
  if(!document.querySelector('[data-cesium-css]')){const css=document.createElement('link');css.rel='stylesheet';css.href=base+'Widgets/widgets.css';css.dataset.cesiumCss='';document.head.append(css);}
  if(!root.Cesium)await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src=base+'Cesium.js';script.onload=resolve;script.onerror=()=>{script.remove();reject(Error('3D 라이브러리를 읽지 못했습니다.'));};document.head.append(script);});
  const baseSat=new URL('vendor/satellite/',document.baseURI).href;
  const modules=await Promise.all([import(baseSat+'io.js'),import(baseSat+'propagation.js'),import(baseSat+'transforms.js')]);
  return {C:root.Cesium,S:Object.assign({},...modules)};
 })().catch(e=>{loader=null;throw e;});return loader;}
 function render(s,i){return `<div class="sauron-view" data-sauron="${i}"><h2>${E(s.title)}</h2><p class="scope-note">시설 ${s.sites.length} · USGS 지진 ${s.quakes.length}(M≥2.5) · 궤도 요소 ${s.elements.length}개 · PC 관측 스냅샷 / 궤도 위치는 현재 UTC 계산</p>
  <div class="sauron-stage" tabindex="0" aria-label="SAURON 3D 지구본. 방향키 회전, 더하기/빼기 확대, 숫자1~6 화면 효과, H 정보 표시">
   <div class="sauron-canvas" data-sau-canvas><p class="sauron-loading">3D 지구본을 준비합니다…</p></div><div class="sauron-scan"></div>
   <div class="sauron-hud"><div class="sauron-hud-title">SAURON <small>시설 · 지진 · 궤도</small></div><form data-sau-search><label>시설·지명 또는 위도,경도 <input name="place" maxlength="120" placeholder="예: TSMC, 서울, Taipei" autocomplete="off"></label><button type="submit">검색</button></form><div data-sau-search-results aria-live="polite"></div><label>관심 시설 <select data-sau-site><option value="">시설 선택</option>${s.sites.map(a=>`<option value="${E(a.id)}">${E(a.name)} (${E(a.category)})</option>`).join('')}</select></label>
    <div class="sauron-layer-bar">${[['sites','투자 시설',s.sites.length],['quakes','지진',s.quakes.length],['sats','궤도 위성',s.elements.length]].map(([k,n,v])=>`<button type="button" data-sau-layer="${k}" aria-pressed="true">${n} <b data-sau-count="${k}">${v}</b></button>`).join('')}</div>
    <label>지도 배경 <select data-sau-base><option value="natural">Natural Earth (로컬)</option><option value="osm">OpenStreetMap 거리 지도</option></select></label><small class="sauron-help">지명 검색: Wikipedia 대표 좌표 · 직접 주소 검색과 다릅니다.</small>
   </div><div class="sauron-sensors">${STYLES.map(([id,name])=>`<button type="button" data-sau-style="${id}" aria-pressed="${id==='normal'}">${name}</button>`).join('')}<small>색상 효과 · 실제 센서 영상 아님</small></div>
   <div class="sauron-controls">${[['spin','자동 회전'],['in','＋'],['out','−'],['tiltup','경사 ↑'],['tiltdown','경사 ↓'],['left','↺'],['right','↻'],['tour','시설 투어'],['reset','전체 지구'],['hud','정보 표시'],['full','전체화면']].map(([k,n])=>`<button type="button" data-sau-control="${k}" ${['spin','tour'].includes(k)?'aria-pressed="false"':''} aria-label="${E({in:'SAURON 확대',out:'SAURON 축소',left:'SAURON 왼쪽 회전',right:'SAURON 오른쪽 회전'}[k]||n)}">${n}</button>`).join('')}</div>
   <div class="sauron-attribution">Cesium · Natural Earth · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors</a></div>
  </div><p class="sauron-instructions">드래그 회전 · 휠 확대 · Ctrl+드래그 경사 · 마커 상세 · 숫자1~6 효과 · H 정보 · Esc 전체 지구. 화면 조작은 자동 회전과 투어를 중지합니다.</p><output class="sauron-clock" data-sau-clock aria-live="off"></output><div class="sauron-detail" data-sau-detail aria-live="polite">시설·지진·위성을 선택하면 위치·시각·근거를 표시합니다.</div>
  <details class="sauron-ledgers"><summary>관측 원장 · WebGL을 쓸 수 없어도 조회 가능</summary><h3>USGS 지진 · 제공 시점 ${E(s.quake_generated||'미확보')} 직전24시간</h3><div class="table-scroll"><table class="data-table" aria-label="SAURON 지진 원장"><thead><tr><th>위치</th><th>규모/형식</th><th>깊이 km</th><th>발생 UTC</th><th>상태</th></tr></thead><tbody>${s.quakes.map(a=>`<tr><td><a href="${E(a.url)}" target="_blank" rel="noopener noreferrer">${E(a.name)}</a></td><td>${a.mag} ${E(a.mag_type)}</td><td>${a.depth_km}</td><td>${E(a.time)}</td><td>${E(a.status)}</td></tr>`).join('')}</tbody></table></div><h3>궤도 요소 · 자료 확보 ${E(s.stations_retrieved||'미확보')}</h3><div class="table-scroll"><table class="data-table" aria-label="SAURON 궤도 원장"><thead><tr><th>객체</th><th>NORAD</th><th>요소 기준 UTC</th><th>회전/일</th><th>경사 °</th></tr></thead><tbody>${s.elements.map(a=>`<tr><td>${E(a.OBJECT_NAME)}</td><td>${E(a.NORAD_CAT_ID)}</td><td>${E(a.EPOCH)}</td><td>${E(a.MEAN_MOTION)}</td><td>${E(a.INCLINATION)}</td></tr>`).join('')}</tbody></table></div><h3>자료 수집</h3><ul>${s.collection.map(a=>`<li>${E(a.key)} · ${E(a.state)} · 확인 ${E(a.checked_at||'미확인')}</li>`).join('')}</ul><p>위성 위치는 SGP4/SDP4와 GMST 좌표변환으로 계산합니다. 관측 텔레메트리가 아니며, 요소가7일을 넘거나 궤도 계산에 실패하면 위치를 표시하지 않습니다. 고도를200km로 강제 보정하지 않습니다. 지진 표시는 진앙이며 깊이는 원장에 별도 기록합니다.</p></details></div>`;}
 function dispose(){while(disposers.length)disposers.pop()();}
 function bind(container,d,state={}){container.querySelectorAll('[data-sauron]').forEach(box=>{
  const s=d.sections[+box.dataset.sauron],q=sel=>box.querySelector(sel),stage=q('.sauron-stage'),canvas=q('[data-sau-canvas]'),st=state.sauron||(state.sauron={style:'normal',base:'natural',layers:{sites:true,quakes:true,sats:true}});
  let alive=true,viewer,C,S,sets={},spin=false,tour=null,orbitalTimer=null,rotationTimer=null,selected=null,searchAbort=null,searchLast=0,placeResults=[];
  const status=text=>{q('[data-sau-clock]').textContent=text;};
  const pressed=(key,on)=>q(`[data-sau-control="${key}"]`).setAttribute('aria-pressed',String(on));
  const stop=()=>{spin=false;pressed('spin',false);if(rotationTimer)clearInterval(rotationTimer);rotationTimer=null;if(tour)clearTimeout(tour);tour=null;pressed('tour',false);if(viewer&&!viewer.isDestroyed())viewer.camera.cancelFlight();};
  const sensor=id=>{st.style=id;const entry=STYLES.find(a=>a[0]===id)||STYLES[0];if(viewer)viewer.scene.canvas.style.filter=entry[2];stage.classList.toggle('sauron-crt',id==='crt');box.querySelectorAll('[data-sau-style]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sauStyle===id)));};
  function detail(kind,a,extra){selected={kind,id:kind==='sats'?a.NORAD_CAT_ID:a.id};
   if(kind==='sites')q('[data-sau-detail]').innerHTML=`<h3>${E(a.name)}</h3><p>${E(a.category)} · ${E(a.symbol||'상장코드 미표시')} · ${a.lat}, ${a.lon}</p><p>${E(a.scope)}</p><p>${E(a.review_note)}</p>${a.sources.map(r=>`<a href="${E(r.url)}" target="_blank" rel="noopener noreferrer">${E(r.title)} ↗</a>`).join(' · ')}<p><a href="${E(a.coordinate_source)}" target="_blank" rel="noopener noreferrer">좌표 근거 ↗</a></p>`;
   else if(kind==='quakes')q('[data-sau-detail]').innerHTML=`<h3>M ${a.mag} · ${E(a.name)}</h3><p>형식 ${E(a.mag_type)} · 진원 깊이 ${a.depth_km}km · 진앙 ${a.lat}, ${a.lon}</p><p>발생 ${E(a.time)} · 수정 ${E(a.updated)} · ${E(a.status)}</p><a href="${E(a.url)}" target="_blank" rel="noopener noreferrer">USGS 관측 ↗</a>`;
   else{const p=extra||position(a,new Date(),S,s.config.max_epoch_age_days);q('[data-sau-detail]').innerHTML=`<h3>${E(a.OBJECT_NAME)} · NORAD ${E(a.NORAD_CAT_ID)}</h3><p>요소 기준 ${E(a.EPOCH)} · 자료 확보 ${E(s.stations_retrieved||'미확보')}</p><p>${p.status==='ok'?`SGP4 계산 위치 ${p.lat.toFixed(4)}°, ${p.lon.toFixed(4)}° · 고도 ${p.height_km.toFixed(3)}km<br>계산 UTC ${E(p.at)}`:'현재 위치 미표시: '+E(p.status)}</p><p>요소 경과 ${Number.isFinite(p.age)?p.age.toFixed(3):'—'}일 · 관측 텔레메트리 아님</p><a href="https://celestrak.org/NORAD/documentation/gp-data-formats.php" target="_blank" rel="noopener noreferrer">CelesTrak 궤도 정의 ↗</a>`;}
  }
  function fly(place,range=4200){if(!viewer){status('3D 지구본 준비 후 이동할 수 있습니다.');return;}stop();viewer.camera.flyToBoundingSphere(new C.BoundingSphere(C.Cartesian3.fromDegrees(place.lon,place.lat),range*.5),{offset:new C.HeadingPitchRange(C.Math.toRadians(28),C.Math.toRadians(-32),range),duration:1.8});viewer.scene.requestRender();}
  function home(){stop();viewer.camera.flyTo({destination:C.Cartesian3.fromDegrees(...s.config.home),duration:1.2});}
  function orbit(action){const camera=viewer.camera,cv=viewer.scene.canvas,ray=camera.getPickRay(new C.Cartesian2(cv.clientWidth/2,cv.clientHeight/2)),center=viewer.scene.globe.pick(ray,viewer.scene),angle=C.Math.toRadians(6);
   if(center)camera.lookAtTransform(C.Transforms.eastNorthUpToFixedFrame(center));
   if(action==='tiltup')camera.rotateUp(angle);else if(action==='tiltdown')camera.rotateDown(angle);else if(action==='left')camera.rotateLeft(angle);else camera.rotateRight(angle);
   if(center)camera.lookAtTransform(C.Matrix4.IDENTITY);viewer.scene.requestRender();}
  async function basemap(id){st.base=id;q('[data-sau-base]').value=id;if(!viewer)return;
   let provider;if(id==='osm')provider=new C.OpenStreetMapImageryProvider({url:s.config.osm_url,maximumLevel:18,credit:'© OpenStreetMap contributors'});
   else provider=await C.TileMapServiceImageryProvider.fromUrl(new URL('vendor/cesium/Assets/Textures/NaturalEarthII/',document.baseURI).href);
   if(!alive||st.base!==id)return;viewer.imageryLayers.removeAll();viewer.imageryLayers.addImageryProvider(provider);viewer.scene.globe.maximumScreenSpaceError=id==='osm'?3:2;
   viewer.scene.globe.preloadAncestors=false;viewer.scene.globe.preloadSiblings=false;viewer.scene.requestRender();
  }
  function tick(){if(!alive||!viewer||!sets.sats||document.hidden)return;const now=new Date();let count=0,stale=0;
   for(const item of s.elements){let p;try{p=position(item,now,S,s.config.max_epoch_age_days);}catch(_){p={status:'propagation_failed'};}const id=String(item.NORAD_CAT_ID),entity=sets.sats.entities.getById(id);
    if(p.status!=='ok'){stale++;if(entity)entity.show=false;if(selected?.kind==='sats'&&selected.id===item.NORAD_CAT_ID)detail('sats',item,p);continue;}count++;
    const loc=C.Cartesian3.fromDegrees(p.lon,p.lat,p.height_km*1000);
    if(entity){entity.position=loc;entity.show=true;}else{const hi=/ISS|ZARYA|CSS|TIANHE|TIANGONG/i.test(item.OBJECT_NAME);sets.sats.entities.add({id,name:item.OBJECT_NAME,position:loc,point:{pixelSize:hi?10:5,color:C.Color.fromCssColorString(hi?'#69e0c9':'#9fc4f0'),outlineColor:C.Color.WHITE,outlineWidth:hi?2:1},label:/^(ISS \(ZARYA\)|CSS \(TIANHE\))$/.test(item.OBJECT_NAME)?{text:item.OBJECT_NAME,font:'12px sans-serif',fillColor:C.Color.WHITE,showBackground:true,pixelOffset:new C.Cartesian2(0,-18)}:undefined,properties:{kind:'sats',index:s.elements.indexOf(item)}});}
    if(selected?.kind==='sats'&&selected.id===item.NORAD_CAT_ID)detail('sats',item,p);
   }
   q('[data-sau-count="sats"]').textContent=count;status(`궤도 계산 UTC ${now.toISOString()} · 유효 ${count}/${s.elements.length} · 미표시 ${stale} · 지진 제공 ${s.quake_generated||'미확보'}`);viewer.scene.requestRender();
  }
  async function search(event){event.preventDefault();searchAbort?.abort();searchAbort=null;q('[data-sau-search] button').disabled=false;const text=q('[data-sau-search] input').value.trim();if(!text)return;const local=s.sites.filter(a=>[a.name,a.address,a.symbol].join(' ').toLocaleLowerCase().includes(text.toLocaleLowerCase()));const coord=coordinates(text);
   if(!coord&&/^[-\d.,\s]+$/.test(text)){q('[data-sau-search-results]').textContent='위도 -90~90, 경도 -180~180을 쉼표로 구분해 입력하세요.';return;}if(coord){placeResults=[coord];}else if(local.length){placeResults=local.map(a=>({...a,site_id:a.id,range:4200}));}
   else{const lang=/[가-힣]/.test(text)?'ko':'en',key=lang+':'+text.toLocaleLowerCase();if(searchCache.has(key))placeResults=searchCache.get(key);
    else{if(Date.now()-searchLast<2000)return;searchLast=Date.now();searchAbort?.abort();searchAbort=new AbortController();const token=searchAbort,deadline=setTimeout(()=>token.abort(),15000);const button=q('[data-sau-search] button');button.disabled=true;q('[data-sau-search-results]').textContent='공개 지명 좌표 검색 중…';
     try{const found=await wikiSearch(text,lang,token.signal);if(!alive||token!==searchAbort)return;placeResults=found;searchCache.set(key,placeResults);if(searchCache.size>50)searchCache.delete(searchCache.keys().next().value);}
     catch(e){if(alive&&token===searchAbort)q('[data-sau-search-results]').textContent='지명 좌표를 읽지 못했습니다. 시설명 또는 위도,경도를 사용할 수 있습니다.';return;}finally{clearTimeout(deadline);if(alive&&token===searchAbort)button.disabled=false;}
    }
   }
   q('[data-sau-search-results]').innerHTML=placeResults.map((a,i)=>`<button type="button" data-sau-place="${i}">${E(a.name)} →</button>`).join('')||'좌표가 있는 결과가 없습니다.';
  }
  q('[data-sau-search]').addEventListener('submit',search);q('[data-sau-search-results]').addEventListener('click',e=>{const b=e.target.closest('[data-sau-place]');if(!b)return;const a=placeResults[Number(b.dataset.sauPlace)];fly(a,a.range);if(a.site_id)detail('sites',a);else q('[data-sau-detail]').innerHTML=`<h3>${E(a.name)}</h3><p>${a.lat}, ${a.lon} · ${E(a.source||'대표 좌표')}</p>${a.url?`<a href="${E(a.url)}" target="_blank" rel="noopener noreferrer">좌표 문서 ↗</a>`:''}`;});
  q('[data-sau-site]').addEventListener('change',e=>{const a=s.sites.find(a=>a.id===e.target.value);if(a){fly(a);detail('sites',a);}});
  q('[data-sau-base]').addEventListener('change',e=>basemap(e.target.value).catch(()=>status('지도 배경을 불러오지 못했습니다. 다른 배경을 선택할 수 있습니다.')));
  box.querySelectorAll('[data-sau-style]').forEach(b=>b.addEventListener('click',()=>sensor(b.dataset.sauStyle)));
  box.querySelectorAll('[data-sau-layer]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.sauLayer;st.layers[key]=!st.layers[key];b.setAttribute('aria-pressed',String(st.layers[key]));if(sets[key])sets[key].show=st.layers[key];viewer?.scene.requestRender();}));
  function control(action){if(action==='hud'){stage.classList.toggle('sauron-hud-off');return;}if(action==='full'){const action=document.fullscreenElement===stage?document.exitFullscreen?.():stage.requestFullscreen?.();Promise.resolve(action).catch(()=>status('이 브라우저는 전체화면을 허용하지 않습니다.'));return;}if(!viewer)return;
   if(action==='spin'){if(spin){stop();return;}stop();spin=true;pressed('spin',true);rotationTimer=setInterval(()=>{if(!alive||document.hidden)return;viewer.camera.rotate(C.Cartesian3.UNIT_Z,-.0005);viewer.scene.requestRender();},50);return;}
   if(action==='tour'){if(tour){stop();return;}stop();let index=0;const step=()=>{if(!alive||index>=s.sites.length){tour=null;pressed('tour',false);return;}const a=s.sites[index++];fly(a);detail('sites',a);pressed('tour',true);tour=setTimeout(step,4200);};step();return;}
   stop();if(action==='reset')home();else if(action==='in'||action==='out'){const step=Math.max(1000,viewer.camera.positionCartographic.height*.35);viewer.camera[action==='in'?'zoomIn':'zoomOut'](step);viewer.scene.requestRender();}else orbit(action);
  }
  box.querySelectorAll('[data-sau-control]').forEach(b=>b.addEventListener('click',()=>control(b.dataset.sauControl)));
  stage.addEventListener('keydown',e=>{if(e.target.closest('input,select,textarea'))return;if(/^[1-6]$/.test(e.key)){e.preventDefault();sensor(STYLES[Number(e.key)-1][0]);}else{const action={h:'hud',H:'hud',Escape:'reset',Home:'reset','+':'in','=':'in','-':'out',ArrowLeft:'left',ArrowRight:'right',ArrowUp:'tiltup',ArrowDown:'tiltdown'}[e.key];if(action){e.preventDefault();control(action);}}});
  const visibility=()=>{if(viewer){viewer.useDefaultRenderLoop=!document.hidden;if(!document.hidden){viewer.resize();tick();}}};document.addEventListener('visibilitychange',visibility);
  disposers.push(()=>{alive=false;stop();searchAbort?.abort();if(orbitalTimer)clearInterval(orbitalTimer);document.removeEventListener('visibilitychange',visibility);if(viewer&&!viewer.isDestroyed())viewer.destroy();});
  libraries().then(async libs=>{if(!alive)return;({C,S}=libs);C.Ion.defaultAccessToken='';canvas.innerHTML='';
   viewer=new C.Viewer(canvas,{baseLayer:false,baseLayerPicker:false,geocoder:false,homeButton:false,sceneModePicker:false,navigationHelpButton:false,animation:false,timeline:false,fullscreenButton:false,infoBox:false,selectionIndicator:true,requestRenderMode:true,maximumRenderTimeChange:Infinity,shouldAnimate:false,skyBox:false});
   viewer.targetFrameRate=24;viewer.resolutionScale=Math.min(1,1.5/(root.devicePixelRatio||1));viewer.scene.globe.enableLighting=true;viewer.scene.backgroundColor=C.Color.WHITE;if(viewer.scene.skyAtmosphere)viewer.scene.skyAtmosphere.show=false;viewer.camera.setView({destination:C.Cartesian3.fromDegrees(...s.config.home)});
   for(const key of ['sites','quakes','sats']){sets[key]=new C.CustomDataSource(key);sets[key].show=st.layers[key];await viewer.dataSources.add(sets[key]);if(!alive)return;q(`[data-sau-layer="${key}"]`).setAttribute('aria-pressed',String(st.layers[key]));}
   for(const [key,rows] of [['sites',s.sites],['quakes',s.quakes]])rows.forEach((a,index)=>sets[key].entities.add({id:a.id,name:a.name,position:C.Cartesian3.fromDegrees(a.lon,a.lat,0),point:{pixelSize:key==='sites'?10:4+a.mag*2.2,color:C.Color.fromCssColorString(key==='sites'?(COLORS[a.category]||'#71b6a7'):a.mag>=6?'#e65a65':a.mag>=4.5?'#e8944f':'#d1b758'),outlineColor:C.Color.WHITE,outlineWidth:1},label:key==='sites'?{text:a.name,font:'12px sans-serif',fillColor:C.Color.WHITE,showBackground:true,pixelOffset:new C.Cartesian2(0,-17),distanceDisplayCondition:new C.DistanceDisplayCondition(0,8e6)}:undefined,properties:{kind:key,index}}));
   viewer.scene.renderError.addEventListener(()=>status('3D 화면 오류가 발생했습니다. 아래 관측 원장을 이용하거나 다른 탭에서 다시 진입하세요.'));
   viewer.selectedEntityChanged.addEventListener(entity=>{if(!entity?.properties)return;const p=entity.properties.getValue(viewer.clock.currentTime);const a=(p.kind==='sites'?s.sites:p.kind==='quakes'?s.quakes:s.elements)[p.index];if(a)detail(p.kind,a);});
   viewer.scene.canvas.addEventListener('pointerdown',stop,{passive:true});viewer.scene.canvas.addEventListener('wheel',stop,{passive:true});sensor(st.style);try{await basemap(st.base);}catch(_){if(alive)status('지도 배경을 읽지 못했습니다. 관측 마커와 원장은 사용할 수 있습니다.');}if(!alive)return;
   q('[data-sau-canvas]').dataset.ready='true';tick();orbitalTimer=setInterval(tick,s.config.orbit_tick_ms);visibility();
  }).catch(e=>{if(alive){if(viewer&&!viewer.isDestroyed())viewer.destroy();viewer=null;canvas.innerHTML='<p class="sauron-loading">3D 화면을 시작하지 못했습니다. 아래 관측 원장은 계속 사용할 수 있습니다.</p>';status(e.message||'WebGL 초기화 실패');}});
 });}
 root.SauronViews={render,bind,dispose,position,coordinates,places,wikiSearch,STYLES};
})(typeof window==='undefined'?globalThis:window);
