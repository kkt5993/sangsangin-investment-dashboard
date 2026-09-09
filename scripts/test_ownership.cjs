'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),d=JSON.parse(read('docs/data/strategies.json')),ctx=vm.createContext({window:{},console});
for(const file of ['charts','analysis-charts','ownership-views'])vm.runInContext(read('docs/'+file+'.js'),ctx);
const V=ctx.window.OwnershipViews,live=d.sections.find(s=>s.type==='ownership');
// Fixed source-review fixture keeps filter checks independent of a moving90day window.
const facts=JSON.parse(read('config/sec_ownership_reviews.json')).filings.map(f=>({...f,reasons:f.accepted_at?[]:['SEC 접수 시각 미확보'],transactions:f.transactions.map(r=>({...r,amount:r.shares*r.price}))}));
const curve=[0,1,2,3].map(x=>({x,y:x*.1,name:'2026-09-0'+(x+1)})),study={first_session:'2026-09-01',reaction:1,drift:2,d5:null,d20:null,excess20:null,curve};
const cards=[...new Set(facts.filter(f=>f.accepted_at).map(f=>f.symbol))].map(symbol=>{const filings=facts.filter(f=>f.symbol===symbol).map(f=>({...f,study}));return {symbol,name:filings[0].issuer_name,buyers:new Set(filings.flatMap(f=>f.owners.map(o=>o.cik))).size,filing_count:filings.length,transaction_count:filings.reduce((n,f)=>n+f.transactions.length,0),amount_mn:filings.reduce((n,f)=>n+f.transactions.reduce((n,r)=>n+r.amount,0),0)/1e6,off_low:3,price_date:'2026-09-08',spark:Array.from({length:44},(_,i)=>[new Date(Date.UTC(2026,6,1+i)).toISOString().slice(0,10),100+i*.1]),filings};});
const s={...live,cards,pending:facts.filter(f=>!f.accepted_at),scope:{...live.scope,confirmed_filings:7,confirmed_rows:9}},i=0,sections=[s];
module.exports=(async()=>{
 assert(live);const current=V.render(live,0);assert(!/\b(NaN|Infinity|undefined)\b/.test(current));
 for(const c of live.cards)assert.equal((V.spark(c).match(/data-ownership-spark=/g)||[]).length,c.spark.length>=2?1:0);
 const html=V.render(s,i);assert(!/\b(NaN|Infinity|undefined)\b/.test(html));assert(html.includes('공개 원문 대조 기록'));assert(html.includes('https://www.sec.gov/Archives/'));
 assert.equal(s.cards.length,4);assert.equal(s.cards.find(c=>c.symbol==='PFE').buyers,3);assert.equal(s.scope.confirmed_rows,9);assert.equal(s.scope.confirmed_filings,7);
 for(const c of s.cards){const svg=V.spark(c);assert.equal((svg.match(/data-ownership-spark=/g)||[]).length,1);assert(c.spark.length<=44);assert(!/NaN|Infinity/.test(svg));}
 assert(V.spark({...s.cards[0],spark:[]}).includes('미확보'));
 const box=parse(html);V.bind(box,sections);const q=box.querySelector('[data-ownership-search]'),filter=box.querySelector('[data-ownership-filter]'),grid=box.querySelector('[data-ownership-cards]'),out=box.querySelector('[data-ownership-output]');
 const symbols=()=>grid.querySelectorAll('[data-ownership-detail]').map(b=>b.dataset.ownershipDetail);
 filter.value='cluster';await filter.fire('change');assert.deepEqual(symbols(),['PFE']);assert(out.innerHTML.includes('0001225208-26-007083'));
 filter.value='all';await filter.fire('change');q.value='VST';await q.fire('input');assert.deepEqual(symbols(),['VST']);assert(out.innerHTML.includes('2026-08-31'));assert(out.innerHTML.includes('2026-09-01'));
 q.value='none-found-9234';await q.fire('input');assert.equal(symbols().length,0);assert(out.innerHTML.includes('현재 필터'));
 q.value='';await q.fire('input');const c=grid.querySelectorAll('[data-ownership-detail]').find(b=>b.dataset.ownershipDetail==='CEG');await c.fire('click');assert(out.innerHTML.includes('0000905148-26-003642'));
 assert.equal(s.pending.length,1);assert.equal(s.pending[0].symbol,'AVGO');assert(!symbols().includes('AVGO'));assert(V.filing(s.pending[0]).includes('집계 제외'));
 const first=s.cards[0].filings[0];assert(first.study.curve.length>2);assert(V.filing(first).includes('SPY 대비 누적 %p'));
 const bad=structuredClone(first);bad.owners[0].name='<img src=x onerror=alert(1)>';bad.source_url='javascript:alert(1)';const safe=V.filing(bad);assert(!safe.includes('<img'));assert(safe.includes('&lt;img'));assert(!safe.includes('href="javascript:'));
 assert(read('docs/research-dashboard.js').includes('root.OwnershipViews.bind(container,d.sections)'));
 const empty={...s,cards:[],pending:[],comparison:[],scope:{...s.scope,confirmed_filings:0,confirmed_rows:0}};assert(V.render(empty,0).includes('확인 공시가 없어'));assert(!/NaN|Infinity|undefined/.test(V.render(empty,0)));
 console.log('Ownership: verified filings/trade rows,44point sparks,reporter filters,search/detail callbacks,exclusions and escaping passed.');
})();
