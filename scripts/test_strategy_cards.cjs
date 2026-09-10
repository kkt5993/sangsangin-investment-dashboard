'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),ctx=vm.createContext({window:{},console});
for(const f of ['charts','strategy-cards'])vm.runInContext(read('docs/'+f+'.js'),ctx);
const V=ctx.window.StrategyCards,data=JSON.parse(read('docs/data/strategies.json'));
const turn=data.sections.find(s=>s.type==='strategycards'&&s.kind==='turnaround'),pair=data.sections.find(s=>s.type==='strategycards'&&s.kind==='pairs'),pead=data.sections.find(s=>s.type==='strategycards'&&s.kind==='pead');
module.exports=(async()=>{
 assert(turn&&pair);assert.equal(pair.rows.length,13);
 for(const s of [turn,pair]){const h=V.render(s,0);assert(!/\b(NaN|Infinity|undefined)\b/.test(h));for(const c of s.rows){const svg=V.spark(c,s.kind);assert.equal((svg.match(/data-strategy-spark/g)||[]).length,c.spark.length>1?1:0);if(s.kind==='pairs'&&c.spark.length>1)assert(svg.includes('data-strategy-guide="midrange"'));}}
 const p=pair.rows.find(c=>c.spark.length);assert(p);assert(V.detail(p,'pairs').includes(String(p.beta)));assert(V.detail(p,'pairs').includes('120관측'));
 const card={id:'S0',symbol:'S0',name:'Sample',market:'US',blackink:true,score:3,score_parts:[1,1,1,0],annual:[['2023-12-31',100],['2024-12-31',-1],['2025-12-31',20]],currency:'USD',spark:Array.from({length:44},(_,i)=>['2026-07-'+String(i%28+1).padStart(2,'0'),100+i]),date:'2026-09-08',price:143,low:100,high:200,low_date:'2026-01-01',high_date:'2026-03-01',off_low:43,off_high:-28.5,ma200:120,est_growth:10,source:'https://finance.yahoo.com/quote/S0/financials/'};
 const s={...turn,rows:Array.from({length:11},(_,i)=>({...card,id:'S'+i,symbol:'S'+i,name:'Sample'+i,market:i%2?'KR':'US'}))};
 const box=parse(V.render(s,0));V.bind(box,[s]);const grid=box.querySelector('[data-strategy-cards]'),q=box.querySelector('[data-strategy-search]'),market=box.querySelector('[data-strategy-market]'),more=box.querySelector('[data-strategy-more]'),out=box.querySelector('[data-strategy-output]');
 const shown=()=>grid.querySelectorAll('[data-strategy-detail]').map(b=>b.dataset.strategyDetail);
 assert.equal(shown().length,8);await more.fire('click');assert.equal(shown().length,11);
 market.value='KR';await market.fire('change');assert.deepEqual(shown(),['S1','S3','S5','S7','S9']);
 q.value='Sample3';await q.fire('input');assert.deepEqual(shown(),['S3']);assert(out.innerHTML.includes('Sample3'));
 q.value='absent';await q.fire('input');assert.equal(shown().length,0);assert.equal(out.innerHTML,'');
 q.value='';market.value='all';await q.fire('input');await grid.querySelectorAll('[data-strategy-detail]')[4].fire('click');assert(out.innerHTML.includes('Sample4'));
 const bad={...card,name:'<script>alert(1)</script>',source:'javascript:alert(1)'};assert(!V.detail(bad,'turnaround').includes('<script>'));assert(!V.detail(bad,'turnaround').includes('href="javascript:'));
 assert(V.cards({...turn,rows:[]}).includes('후보가 없습니다'));
 assert(pead);assert.equal(pead.scope.expected,pead.rows.length+pead.scope.excluded.length);
 for(const c of pead.rows){const h=V.detail(c,'pead');assert(h.includes(String(c.display_return)));assert(h.includes('발표 전 포함'));assert(!/\b(NaN|Infinity|undefined)\b/.test(h));assert(!V.spark(c,'pead').includes('data-strategy-guide'));}
 const pc=pead.rows[0];assert(pc);const ps={...pead,rows:Array.from({length:15},(_,i)=>({...pc,id:'P'+i,symbol:'P'+i,name:'Pead'+i}))};
 const pb=parse(V.render(ps,0));V.bind(pb,[ps]);const pg=pb.querySelector('[data-strategy-cards]'),pm=pb.querySelector('[data-strategy-more]'),pq=pb.querySelector('[data-strategy-search]');
 assert.equal(pg.querySelectorAll('[data-strategy-detail]').length,12);await pm.fire('click');assert.equal(pg.querySelectorAll('[data-strategy-detail]').length,15);assert(pm.textContent.includes('12'));
 pq.value='Pead14';await pq.fire('input');assert.equal(pg.querySelectorAll('[data-strategy-detail]').length,1);assert(pb.querySelector('[data-strategy-output]').innerHTML.includes('Pead14'));
 assert(V.cards({...pead,rows:[{...pc,drift:-5}]}).includes('-5%'));
 console.log('Strategy cards: annual recovery,13fixed pairs,44point sparks/midrange,full-precision details,market/search/top8 toggles and escaping passed.');
})();
