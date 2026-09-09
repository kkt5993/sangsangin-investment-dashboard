/* Real snapshot render checks without browser or external calls. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const modules=JSON.parse(read('docs/modules.js').replace(/^const MODULES = /,'').trim().replace(/;$/,''));
const data=Object.fromEntries(fs.readdirSync(path.join(root,'docs/data')).filter(n=>n.endsWith('.json')).map(n=>[n.slice(0,-5),JSON.parse(read('docs/data/'+n))]));
let requests=0;const context=vm.createContext({window:{},location:{hash:''},console,fetch:async url=>{requests++;return {ok:true,json:async()=>data[path.basename(url,'.json')]};}});
for(const file of ['charts','analysis-charts','network-views','research-dashboard'])vm.runInContext(read('docs/'+file+'.js'),context);
function container(){return {innerHTML:'',querySelectorAll(){return [];},querySelector(){return null;}};}
(async()=>{
 let count=0;
 for(const m of modules){const d=data[m.id];if(d?.schema_version!==2)continue;const c=container();context.location.hash='#'+m.id;await context.window.ResearchDashboard.render(c,m);
  assert(c.innerHTML.includes('<h1>'),m.id);assert(!c.innerHTML.includes('role="alert"'),m.id);assert(!/\b(NaN|Infinity|undefined)\b|\[object Object\]/.test(c.innerHTML),m.id+' invalid rendering');assert(c.innerHTML.includes('data/'+m.id+'.json'),m.id);
  // Render every subview, not only the initially selected group.
  for(const [i,s] of d.sections.entries()){const h=context.window.ResearchDashboard.section(s,i,{});assert(typeof h==='string'&&h.length,m.id);assert(!/\b(NaN|Infinity|undefined)\b|\[object Object\]/.test(h),m.id+' '+s.title);}
  await context.window.ResearchDashboard.render(c,m);count++;
 }
 assert.equal(requests,count,'one local request per module across repeated navigation');
 const A=context.window.AnalysisCharts;
 const dyn=data.dynamics.sections[0];assert.equal(dyn.surface.windows.length,8);assert.equal(dyn.phase.length,60);assert(A.surface(dyn.surface).includes('data-chart-type="surface"'));
 const watch=data.watch.sections[0];assert.equal(watch.candles.length,120);assert.equal(watch.weekly.length,52);assert.equal((A.candles(watch).match(/data-volume="1"/g)||[]).length,120);
 assert(data.watch.sections.some(s=>s.pattern&&A.candles(s).includes('data-pattern="1"')),'geometric candidates have overlays');
 const ml=data.ml.sections.find(s=>s.type==='ml');assert(A.forecast(ml).includes('data-interval="90"'));assert(A.forecast(ml).includes('data-interval="68"'));assert(A.forecast(ml).includes('data-prediction="1"'));
 assert(A.line({title:'test',left:'%',right:'index',guides:[0],series:[{name:'left',axis:'left',points:[['2026-01-01',1],['2026-02-01',2]]},{name:'right',axis:'right',points:[['2026-01-01',100],['2026-02-01',200]]}]}).includes('data-axis="right"'));
 const xss=context.window.ResearchDashboard.section({type:'table',title:'<img>',columns:['x'],rows:[['<script>alert(1)</script>']]},0,{});assert(!xss.includes('<script>'));assert(xss.includes('&lt;script&gt;'));
 console.log('PASS:',count,'new tabs, every subview, cache, real SVG structures, 120D/52W candles, dual axes, 3D surface, 68/90 bands and escaping.');
})().catch(e=>{console.error(e);process.exitCode=1;});
