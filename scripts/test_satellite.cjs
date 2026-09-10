'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{Node,parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const ctx=vm.createContext({window:{},console,setTimeout,clearTimeout,fetch:async url=>{assert.equal(url,'data/coastlines.json');return {ok:true,json:async()=>JSON.parse(read(url.replace('data/','docs/data/')))};}});
for(const f of ['charts','satellite-views'])vm.runInContext(read('docs/'+f+'.js'),ctx);
const V=ctx.window.SatelliteViews;
Node.prototype.setAttribute=function(k,v){this.attrs[k]=String(v);};Node.prototype.getAttribute=function(k){return this.attrs[k];};
function annotate(n,parent=null){n.parent=parent;n.closest=function(s){let p=this;while(p){if(p.matches(s))return p;p=p.parent;}return null;};n.children.forEach(c=>annotate(c,n));}
module.exports=(async()=>{
 const d=JSON.parse(read('docs/data/dragonglass.json')),s=d.sections.find(s=>s.type==='satellite');assert(s);assert.equal(s.sites.length,22);
 const html=V.render(s,0);assert.equal((html.match(/data-sat-card=/g)||[]).length,22);assert.equal((html.match(/data-sat-toggle=/g)||[]).length,s.image_count);assert(!/\b(NaN|Infinity|undefined)\b/.test(html));
 for(const [lon,lat]of [[0,0],[121,24],[-112,34]]){const [x,y]=V.merc(lon,lat),p=V.inverse(x,y);assert(Math.abs(p[0]-lon)<1e-8);assert(Math.abs(p[1]-lat)<1e-8);}
 const base={lon:0,lat:20,zoom:1,size:1,selected:'',mode:'rgb'},site=s.sites.find(r=>r.scene),focused=V.focus(base,site);assert.equal(focused.zoom,14);assert.equal(focused.lon,site.lon);assert.equal(V.camera(focused,0,0,100).zoom,19);assert.equal(V.camera(base,0,0,-10).zoom,1);
 const box=parse(html);annotate(box);const nav=[];V.bind(box,{sections:[s]},(...x)=>nav.push(x));
 await box.querySelector('[data-sat-focus="'+site.id+'"]').fire('click');assert(box.querySelector('[data-sat-detail]').innerHTML.includes(site.name));assert(box.querySelector('[data-sat-map]').innerHTML.includes('확대 14'));
 const mode=box.querySelector('[data-sat-mode]');mode.value='ndvi';await mode.fire('change');assert(box.querySelector('[data-sat-detail]').innerHTML.includes(site.id+'-ndvi.png'));
 const card=box.querySelector('[data-sat-card="'+site.id+'"]'),toggle=card.querySelector('[data-sat-toggle]'),img=card.querySelector('[data-sat-image]');await toggle.fire('click');assert.equal(img.src,site.scene.images.ndvi.path);await toggle.fire('click');assert.equal(img.src,site.scene.images.rgb.path);
 await card.querySelector('[data-sat-open]').fire('click');assert.equal(nav.at(-1)[0],'Entity 360');assert.equal(nav.at(-1)[1].facility,site.id);
 const surface=box.querySelector('[data-sat-map]');await surface.events.keydown[0]({target:surface,key:'-',preventDefault(){}});assert(surface.innerHTML.includes('확대 13'));
 surface.getBoundingClientRect=()=>({width:1000});surface.events.pointerdown[0]({target:surface,clientX:100,clientY:100,pointerId:1});const before=surface.innerHTML;surface.events.pointermove[0]({clientX:160,clientY:140});assert.notEqual(surface.innerHTML,before);surface.events.pointerup[0]({});
 await box.querySelector('[data-sat-size]').fire('click');assert(surface.innerHTML.includes('height="760"'));await box.querySelector('[data-sat-reset]').fire('click');assert(surface.innerHTML.includes('확대 '+V.fit(s,base).zoom));
 assert(V.camera({...base,lon:179,zoom:1},-100,0).lon<0,'date line wraps');
 const fitted=V.fit(s,base);assert(fitted.zoom>=1&&fitted.zoom<=6);
 const pngMap=V.map(s,focused,[],[{key:'x',href:'blob:test',left:0,top:0,size:256}]);
 assert(pngMap.indexOf('data-sat-tile=')<pngMap.indexOf('data-sat-mask='));
 assert(pngMap.indexOf('data-sat-mask=')<pngMap.indexOf(site.scene.images.rgb.path),'opaque cloud mask precedes observation');
 assert(!V.map(s,focused,[],[{key:'x',href:'javascript:bad',left:0,top:0,size:256}]).includes('javascript:'));
 const background=box.querySelector('[data-sat-background]');background.value='coast';await background.fire('change');assert(box.querySelector('[data-sat-basemap-note]').textContent.includes('외부 배경 요청 없이'));
 V.dispose();
 const pending=s.sites.find(r=>r.location_status!=='reviewed');if(pending){await box.querySelector('[data-sat-focus="'+pending.id+'"]').fire('click');assert(box.querySelector('[data-sat-detail]').innerHTML.includes(pending.name));assert(!box.querySelector('[data-sat-detail]').innerHTML.includes('<img'));}
 const f=parse(V.render({type:'facilitydetail'},1));V.bind(f,{sections:[s]},(...x)=>nav.push(x),{facility:site.id});assert(f.querySelector('[data-facility-output]').innerHTML.includes(site.scene.id)||f.querySelector('[data-facility-output]').innerHTML.includes(site.scene.source));
 const bad={...site,name:'<script>alert(1)</script>',sources:[{title:'bad',url:'javascript:alert(1)'}],coordinate_source:'javascript:bad'};const escaped=V.details(bad);assert(!escaped.includes('<script>'));assert(!escaped.includes('href="javascript:'));
 assert(read('docs/research-dashboard.js').includes('root.SatelliteViews?.bind(container,d,navigate,st)'));
 console.log('Satellite:22facility slots,real image metadata,map projection/pan/zoom/size,RGB-NDVI toggles,facility navigation,pending states and escaping passed.');
})();
