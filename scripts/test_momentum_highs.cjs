/* Real snapshot plus deterministic event fixtures, without a browser. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..'),ctx=vm.createContext({window:{},console});
for(const name of ['charts','momentum-highs'])vm.runInContext(fs.readFileSync(path.join(root,'docs',name+'.js'),'utf8'),ctx);
const H=ctx.window.MomentumHighs,d=JSON.parse(fs.readFileSync(path.join(root,'docs/data/momentum.json'),'utf8')).new_highs;
assert.deepEqual(d.groups.map(g=>g.universe),['us100','kospi200']);
const html=H.render(d,{market:'all'});assert.equal((html.match(/data-high-symbol=/g)||[]).length,d.groups.reduce((n,g)=>n+g.selected,0));
assert(!/NaN|Infinity|undefined/.test(html));
for(const g of d.groups)for(const r of g.rows){
 assert(r.rs>=65&&r.from_high>=-5);assert.equal(r.spark.length,44);
 assert.equal(r.spark.at(-1)[0],r.as_of);assert.equal(r.spark.at(-1)[1],r.price);
 const svg=H.spark(r);assert.equal((svg.match(/data-high-price=/g)||[]).length,1);assert.equal((svg.match(/data-high-guide=/g)||[]).length,1);
 assert(svg.includes('stroke-dasharray="4 3"'));
}
const row={symbol:'TST',name:'Fixture <script>',sector:'Financials',rs:90,price:100,high52:100,from_high:0,new_high:true,as_of:'2026-09-08',high_window_start:'2025-09-01',high_date:'2026-09-08',spark:[['2026-03-03',80],['2026-09-08',100]]};
const fixture={note:'fixture',groups:['US','KR'].map(m=>({market:m,universe:m,title:m,rows:[{...row,symbol:m,name:m+' <script>'},{...row,symbol:m+'OLD',new_high:false}],expected:2,eligible:2,selected:2,members:[],excluded:[]}))};
const target=(value='')=>({value,checked:false,events:{},addEventListener(k,f){this.events[k]=f;},fire(k){this.events[k]({target:this});}});
const market=target('all'),search=target(),only=target(),out={innerHTML:''};
const box={querySelector:s=>({'[data-high-market-filter]':market,'[data-high-search]':search,'[data-high-new]':only,'[data-high-output]':out}[s])};
const state={market:'all',q:'',onlyNew:false};H.bind({querySelector:()=>box},fixture,state);
market.value='KR';market.fire('change');assert(out.innerHTML.includes('data-high-market="KR"'));assert(!out.innerHTML.includes('data-high-market="US"'));
only.checked=true;only.fire('change');assert.equal((out.innerHTML.match(/data-high-symbol=/g)||[]).length,1);assert(out.innerHTML.includes('장중 고점 갱신'));
search.value='financials';search.fire('input');assert.equal((out.innerHTML.match(/data-high-symbol=/g)||[]).length,1);
search.value='not found';search.fire('input');assert(out.innerHTML.includes('해당하는 종목이 없습니다'));assert.equal((out.innerHTML.match(/data-high-symbol=/g)||[]).length,0);
assert.equal(search.value,'not found','typing keeps the same input element and focus target');
assert(!H.render(fixture,state).includes('<script>'));
console.log('PASS: official US100/KOSPI200 screen, high guides/dated points, market/search/breakout events, empty states and escaping.');
