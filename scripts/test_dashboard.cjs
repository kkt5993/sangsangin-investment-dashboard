/* Offline HTML-output integration checks. This is not a browser visual test. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path'),root=path.join(__dirname,'..');
const modules=JSON.parse(fs.readFileSync(path.join(root,'docs/modules.js'),'utf8').replace(/^const MODULES = /,'').trim().replace(/;$/,''));
const datasets=Object.fromEntries(['rs','momentum'].map(id=>[id,JSON.parse(fs.readFileSync(path.join(root,`docs/data/${id}.json`),'utf8'))]));
function container(){
 let html='',buttons=[];
 return {get innerHTML(){return html;},set innerHTML(s){html=s;buttons=[...s.matchAll(/<button data-filter="([^"]+)"/g)].map(m=>({dataset:{filter:m[1]},addEventListener(type,fn){this.click=fn;}}));},querySelectorAll(sel){return sel==='[data-filter]'?buttons:[];}};
}
let requests=0;
const ctx=vm.createContext({console,window:{},location:{hash:'#rs'},fetch:async url=>{requests++;const id=url.split('/').at(-1).split('.')[0];return {ok:true,json:async()=>datasets[id]};}});
vm.runInContext(fs.readFileSync(path.join(root,'docs/charts.js'),'utf8'),ctx);
ctx.ResearchCharts=ctx.window.ResearchCharts;
vm.runInContext(fs.readFileSync(path.join(root,'docs/dashboard.js'),'utf8'),ctx);
(async()=>{
 const c=container(),D=ctx.window.PriceDashboard;
 await D.render(c,modules.find(m=>m.id==='rs'));
 assert.equal((c.innerHTML.match(/data-kind="rs"/g)||[]).length,datasets.rs.coverage.pairs);
 assert(c.innerHTML.includes('KRX 공식 구성종목'));
 assert.equal(datasets.rs.stock_rankings.KR.expected,100);
 assert.equal(datasets.rs.stock_rankings.US.expected,504);
 assert.equal(datasets.rs.stock_rankings.KR.strong.length,8);
 assert.equal(datasets.rs.stock_rankings.US.weak.length,6);
 assert(!c.innerHTML.includes('[object Object]')&&!c.innerHTML.includes('NaN'));
 c.querySelectorAll('[data-filter]').find(b=>b.dataset.filter==='US').click();
 assert.equal((c.innerHTML.match(/data-kind="rs"/g)||[]).length,17);
 assert.equal(requests,1,'local filters must not fetch again');
 ctx.location.hash='#momentum';await D.render(c,modules.find(m=>m.id==='momentum'));
 assert.equal((c.innerHTML.match(/data-kind="momentum"/g)||[]).length,32);
 assert.equal((c.innerHTML.match(/data-area="positive"/g)||[]).length,32);
 assert(c.innerHTML.includes('1Y (%)')&&c.innerHTML.includes('3M SPY 대비 (%p)'));
 for(const [g,n] of [['country',13],['factor',10],['asset',9]]){
  c.querySelectorAll('[data-filter]').find(b=>b.dataset.filter===g).click();
  assert.equal((c.innerHTML.match(/data-kind="momentum"/g)||[]).length,0);
  assert.equal((c.innerHTML.match(/<th scope="row">/g)||[]).length,n*2);
 }
 c.querySelectorAll('[data-filter]').find(b=>b.dataset.filter==='sector').click();
 assert.equal((c.innerHTML.match(/data-kind="momentum"/g)||[]).length,32);
 assert.equal(requests,2);
 assert(!c.innerHTML.includes('[object Object]')&&!c.innerHTML.includes('undefined'));
 // A late network response must not replace another route.
 let release;const fresh=vm.createContext({window:{},location:{hash:'#rs'},fetch:()=>new Promise(resolve=>{release=resolve;}),console});
 vm.runInContext(fs.readFileSync(path.join(root,'docs/charts.js'),'utf8'),fresh);fresh.ResearchCharts=fresh.window.ResearchCharts;
 vm.runInContext(fs.readFileSync(path.join(root,'docs/dashboard.js'),'utf8'),fresh);
 const delayed=container(),pending=fresh.window.PriceDashboard.render(delayed,modules.find(m=>m.id==='rs'));
 fresh.window.PriceDashboard.cancel();fresh.location.hash='#regime';delayed.innerHTML='other route';
 release({ok:true,json:async()=>datasets.rs});await pending;assert.equal(delayed.innerHTML,'other route');
 console.log('PASS: real snapshot renders, 17 US RS lines, 32 sector charts, all 4 momentum filters, cache and route guard.');
})().catch(error=>{console.error(error);process.exitCode=1;});
