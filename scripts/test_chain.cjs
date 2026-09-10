'use strict';
const assert=require('node:assert/strict');
module.exports=(context,data)=>{
 const C=context.window.ChainViews,s=data.globe.sections.find(s=>s.type==='chainuniverse');
 assert.equal(s.groups.length,20);assert.equal(s.sectors.length,53);assert.equal(s.companies.length,151);
 assert.equal(s.sectors.reduce((n,a)=>n+a.symbols.length,0),159);
 const state={symbol:'NVDA',city:'',lon:-98,lat:39,zoom:1,kinds:{valuechain:true,export:true,logistics:true}};
 const routes=C.routes(s,state),supply=routes.filter(r=>r.kind==='valuechain'),exports=routes.filter(r=>r.kind==='export');
 assert.equal(supply.length,4);assert.equal(exports.length,5);assert.equal(supply.find(r=>r.source==='TSM').target,'NVDA');
 assert(supply.every(r=>r.evidence.url.startsWith('https://www.sec.gov/')));
 const map=C.map(s,state,data.coastlines.arcs);assert(!/NaN|Infinity|undefined/.test(map));
 assert.equal((map.match(/data-chain-arc="valuechain"/g)||[]).length,3); // US-to-US Micron is kept in the ledger.
 assert.equal((map.match(/data-chain-arc="export"/g)||[]).length,5);
 assert.equal((C.map(s,{...state,kinds:{}}).match(/data-chain-arc=/g)||[]).length,0);
 assert.equal(C.routes(s,{...state,symbol:''}).length,0);
 assert(C.detail(s,state).includes('기업의 수출액'));assert(C.detail(s,state).includes('실제 운송 경로'));
 const tables=C.tables(s);assert.equal((tables.match(/data-chain-company=/g)||[]).length,159);
 assert.equal((tables.match(/<table /g)||[]).length,53);
 assert.equal((C.render(s,0).match(/data-chain-sector=/g)||[]).length,53);
 const bad=JSON.parse(JSON.stringify(s));bad.companies[0].name='<img src=x onerror=alert(1)>';
 bad.companies[0].website='javascript:alert(1)';
 assert(!C.render(bad,0).includes('<img'));assert(!C.render(bad,0).includes('href="javascript:'));
 const points=C.cities(s);assert.equal(new Set(points.map(p=>p.id)).size,points.length);
 assert.equal(points.reduce((n,c)=>n+c.companies.length,0),s.companies.filter(c=>c.location).length);
 console.log('chain directory, national context, evidence, map clipping and escaping: passed');
};
