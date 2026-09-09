'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),d=JSON.parse(read('docs/data/earnings.json')),ctx=vm.createContext({window:{},console});
for(const file of ['charts','analysis-charts','earnings-views'])vm.runInContext(read('docs/'+file+'.js'),ctx);
const V=ctx.window.EarningsViews,sections=d.sections;
module.exports=(async()=>{
 for(const [i,s] of sections.entries())if(s.type.startsWith('earnings')){const h=V.render(s,i);assert(h.length>100);assert(!/\b(NaN|Infinity|undefined)\b/.test(h));}
 const global=sections.find(s=>s.type==='earningsglobal'),g=V.globalBars(global);assert.equal((g.match(/data-earn-actual/g)||[]).length,global.rows.length);assert.equal((g.match(/data-earn-overlay="1"/g)||[]).length,global.rows.filter(r=>r.values[1]!==null).length);
 const kr=sections.find(s=>s.type==='earningsestimates'&&s.market==='KR'),us=sections.find(s=>s.type==='earningsestimates'&&s.market==='US');assert.equal(kr.cards.length,2);assert.equal(us.cards.length,10);assert(kr.cards.every(c=>c.metrics.length===2));assert(us.cards.every(c=>c.metrics.length===2));
 const nv=us.cards.find(c=>c.symbol==='NVDA');assert.equal(nv.projection.forecasts[0].period.slice(5,7),'01');assert(V.estimateCard(nv,'US').includes('EPS 성장률')||V.estimateCard(nv,'US').includes('예상 EPS/전년 EPS'));
 const neg=V.annualBars({name:'loss',unit:'bn',rows:[{label:'A',kind:'actual',value:-10},{label:'E',kind:'estimate',value:20},{label:'M',kind:'estimate',value:null}]}),np=parse(neg);assert.equal(np.querySelectorAll('[data-earn-bar]').length,2);const bars=np.querySelectorAll('[data-earn-bar]');assert(+bars[0].attrs.x<+bars[1].attrs.x);assert(+bars[0].attrs.width>0);assert(!neg.includes('width="-'));
 const gn=structuredClone(global);gn.rows=[{...global.rows[0],values:[5,-10,20]}];const ng=V.globalBars(gn);assert.equal((ng.match(/data-earn-overlay=/g)||[]).length,2);assert(!ng.includes('width="-'));
 const ai=sections.findIndex(s=>s.type==='earningsactual'),a=sections[ai],box=parse(V.render(a,ai));V.bind(box,sections);const select=box.querySelector('[data-earnings-company]'),mode=box.querySelector('[data-earnings-mode]'),out=box.querySelector('[data-earnings-output]'),search=box.querySelector('[data-earnings-search]');
 select.value='000660.KS';await select.fire('change');assert(out.innerHTML.includes('000660.KS'));mode.value='quarterly';await mode.fire('change');assert(out.innerHTML.includes('개별 분기'));assert.equal((out.innerHTML.match(/<svg /g)||[]).length,3);
 search.value='NVDA';await search.fire('input');assert.equal(select.value,'NVDA');assert(out.innerHTML.includes('개별 분기'));search.value='NOT-A-COMPANY-XYZ';await search.fire('input');assert(out.innerHTML.includes('일치하는 기업이 없습니다'));search.value='';await search.fire('input');assert(select.value);assert(out.innerHTML.includes('<svg '));
 const bad=structuredClone(nv);bad.name='<img src=x onerror=alert(1)>';bad.source='javascript:alert(1)';const html=V.estimateCard(bad,'US');assert(!html.includes('<img'));assert(!html.includes('href="javascript:'));assert(html.includes('&lt;img'));
 assert(read('docs/research-dashboard.js').includes('root.EarningsViews.bind(container,d.sections)'));
 console.log('Earnings paired overlays,12two-metric cards,negative/missing bars,fiscal periods,company search and annual/quarter callbacks passed.');
})();
