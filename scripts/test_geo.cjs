'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),d=JSON.parse(read('docs/data/geoecon.json')),ctx=vm.createContext({window:{},console});
for(const file of ['charts','analysis-charts','geo-views'])vm.runInContext(read('docs/'+file+'.js'),ctx);
const G=ctx.window.GeoViews,A=ctx.window.AnalysisCharts,s=d.sections;
module.exports=(async()=>{
 for(const [i,r] of s.entries())if(r.type.startsWith('geo')){const h=G.render(r,i);assert(h.length>100);assert(!/\b(NaN|undefined|Infinity)\b/.test(h));}
 const comp=s.find(r=>r.type==='geocomposites');assert.equal(comp.panels.length,3);for(const r of comp.panels){const h=A.line(r.chart);assert.equal((h.match(/data-value-band=/g)||[]).length,2);assert.equal((h.match(/data-analysis-series=/g)||[]).length,1);}
 const ki=s.findIndex(r=>r.type==='geokeywords'),kw=s[ki],kb=parse(G.render(kw,ki));G.bind(kb,s);
 const selector=kb.querySelector('[data-geo-keyword]'),output=kb.querySelector('[data-geo-keyword-output]');selector.value=kw.terms.at(-1).term;await selector.fire('change');assert(output.innerHTML.includes(kw.terms.at(-1).term));
 const button=kb.querySelector('[data-geo-term]');if(button){await button.fire('click');assert.equal(selector.value,button.dataset.geoTerm);assert(output.innerHTML.includes(button.dataset.geoTerm));}
 const ci=s.findIndex(r=>r.type==='geochannels'),cs=s[ci],cb=parse(G.render(cs,ci));G.bind(cb,s);const sel=cb.querySelector('[data-geo-channel]');sel.value=cs.channels.at(-1).id;await sel.fire('change');assert(cb.querySelector('[data-geo-channel-output]').innerHTML.includes(cs.channels.at(-1).name));assert.equal(cs.channels.length,6);
 const gi=s.findIndex(r=>r.type==='geogpr'),gp=s[gi],gb=parse(G.render(gp,gi));G.bind(gb,s);const months=gb.querySelector('[data-geo-months]');months.value='120';await months.fire('change');const long=gb.querySelector('[data-geo-gpr-output]').innerHTML;months.value='12';await months.fire('change');assert(long.length>gb.querySelector('[data-geo-gpr-output]').innerHTML.length);
 const charts=G.gprCharts(gp,12);assert.deepEqual(Array.from(charts,c=>c.series.length),[3,8,8]);assert(charts.every(c=>c.series.every(r=>r.points.length===12)));assert(charts[0].series[0].points.every(p=>new Date(Date.parse(p[0])+86400000).getUTCDate()===1),'GPR dates are period ends');
 const attack=structuredClone(kw);attack.news[0].title='<img src=x onerror=alert(1)>';attack.news[0].url='javascript:alert(1)';attack.terms[0].articles=[attack.news[0].id];const html=G.keywordDetail(attack.terms[0],attack);assert(!html.includes('<img'));assert(!html.includes('href="javascript:'));assert(html.includes('&lt;img'));
 assert(read('docs/research-dashboard.js').includes('root.GeoViews.bind(container,d.sections)'));
 console.log('Geoecon3composites/2bands,6channels,keyword callbacks,1/3/10Y GPR switches,source links and escaping passed.');
})();
