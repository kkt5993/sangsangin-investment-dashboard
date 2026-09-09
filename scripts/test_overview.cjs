'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),data=JSON.parse(read('docs/data/overview_state.json'));
function context(){let requests=0,resolve;const frames=new Map();let fid=0;const ctx=vm.createContext({window:{requestAnimationFrame:f=>{frames.set(++fid,f);return fid;},cancelAnimationFrame:id=>frames.delete(id),fetch:()=>{requests++;return new Promise(r=>{resolve=()=>r({ok:true,json:async()=>data});});}}});
 for(const n of ['charts','analysis-charts','overview-views'])vm.runInContext(read('docs/'+n+'.js'),ctx);return {V:ctx.window.OverviewViews,frames,requests:()=>requests,resolve:()=>resolve(),ctx};}
async function checks(){
 const {V,frames}=context(),p=data.panels[0],crowd=data.panels[1];
 for(const a of data.panels){const h=V.hologram(a),r=V.radar(a);assert.equal((h.match(/data-state-quadrant=/g)||[]).length,4);assert.equal((h.match(/data-state-date=/g)||[]).length,36);assert.equal((r.match(/data-stacked-date=/g)||[]).length,4);assert.equal((r.match(/data-radar-wall=/g)||[]).length,a.axes.length*3);assert(!/NaN|undefined|Infinity/.test(h+r));}
 assert.equal((V.hologram(p).match(/data-state-halo=/g)||[]).length,36);assert.equal((V.hologram(crowd).match(/data-state-halo=/g)||[]).length,0);
 const missing=structuredClone(p);missing.rows[15].z.growth=null;assert.equal((V.hologram(missing).match(/data-state-segment=/g)||[]).length,33,'missing point breaks both adjacent lines');missing.milestones[0].z.profits=null;assert.equal((V.radar(missing).match(/data-stacked-date=/g)||[]).length,3,'no zero filled radar');
 const html=V.view(data);assert(!/NaN|undefined|Infinity/.test(html));const unsafe=structuredClone(data);unsafe.leaders.stocks[0].name='<script>alert(1)</script>';assert(!V.view(unsafe).includes('<script>'));assert(V.view(unsafe).includes('&lt;script&gt;'));
 const c=parse(html);V.bind(c,data);const panels=c.querySelectorAll('[data-coordinate]');assert.equal(panels.length,2);
 for(const panel of panels){const slider=panel.querySelector('[data-state-yaw]'),graph=panel.querySelector('[data-state-holo]'),before=graph.innerHTML;slider.value='120';await slider.fire('input');assert.notEqual(graph.innerHTML,before);
  graph.events.pointerdown[0]({clientX:0});graph.events.pointermove[0]({clientX:30});graph.events.pointerup[0]({});await panel.querySelector('[data-state-reset]').fire('click');assert.equal(slider.value,'60');assert.equal(graph.innerHTML,before);
  await panel.querySelector('[data-state-spin]').fire('click');}
 assert.equal(frames.size,2);const worm=panels[1].querySelector('[data-worm-symbol]');await worm.fire('click');assert(panels[1].querySelector('[data-worm-detail]').innerHTML.includes('USD bn'));V.cancel();assert.equal(frames.size,0);
 const a=context(),first=parse('<div></div>'),second=parse('<div></div>');first.innerHTML='untouched';const one=a.V.mount(first),two=a.V.mount(second);assert.equal(a.requests(),1,'concurrent mounts share one local fetch');a.resolve();await Promise.all([one,two]);assert.equal(first.innerHTML,'untouched','stale route must not receive render');assert(second.innerHTML.includes('TESSERACT'));a.V.cancel();await a.V.mount(first);assert.equal(a.requests(),1,'cached navigation');a.V.cancel();
 const b=context(),out=parse('<div></div>');out.innerHTML='preserve';const pending=b.V.mount(out);b.V.cancel();b.resolve();await pending;assert.equal(out.innerHTML,'preserve','route cancellation while loading');
 assert(read('docs/app.js').includes("OverviewViews.mount(document.querySelector('#overview-state'))"));assert(read('docs/app.js').includes('ResearchDashboard.cancel();OverviewViews.cancel();'));
 console.log('Overview6/5 axes, four stacked milestones, trajectory gaps, source dates, rotation/leader selection, frame cleanup and fetch race tests passed.');
}
module.exports=checks();module.exports.catch(e=>{console.error(e);process.exitCode=1;});
