/* Actual calculation/DOM callbacks with local snapshots; no browser or network. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),data=JSON.parse(read('docs/data/dragonglass.json')),g=data.sections.find(s=>s.type==='relationlab');
assert(g,'relation snapshot required');
const frames=new Map(),memory=new Map();let frameId=0;
const ctx=vm.createContext({window:{atob,requestAnimationFrame:f=>{frames.set(++frameId,f);return frameId;},cancelAnimationFrame:id=>frames.delete(id),localStorage:{getItem:k=>memory.get(k)??null,setItem:(k,v)=>memory.set(k,v)}},TextEncoder,console});
for(const f of ['charts','analysis-charts','relation-views','decision-ledger'])vm.runInContext(read('docs/'+f+'.js'),ctx);
const R=ctx.window.RelationViews,plain=x=>JSON.parse(JSON.stringify(x));
for(const s of g.scenarios)assert.deepEqual(plain(R.runScenario(g,s.seeds)),s.impacts,s.id+' Python / JS exact published parity');
const small={nodes:['A','B','C'].map(id=>({id})),links:[{id:'a',source:'A',target:'B',relation:'supplies',weight:1},{id:'b',source:'B',target:'C',relation:'competes',weight:1}]};
assert.equal(R.propagate(small,'A',1,1).B.value,.2016);assert.equal(R.propagate(small,'B').A.value,.5184);assert.equal(R.propagate(small,'A').C.value,-.072576);
assert(!R.propagate(small,'A',1,1).C);assert(!R.propagate(small,'A',0).B);assert.throws(()=>R.propagate(small,'A',NaN));assert.throws(()=>R.propagate(small,'A',1,4));assert.throws(()=>R.runScenario(small,[{id:'A',value:1},{id:'A',value:-1}]));
const negative={nodes:small.nodes.slice(0,2),links:[{id:'n',source:'A',target:'B',relation:'correlated',corr:-.9,weight:1}]};assert.equal(Object.keys(R.propagate(negative,'A')).length,0);assert(R.propagate(negative,'A',1,3,true).B.value<0);
const cancel={nodes:small.nodes,links:[{id:'a',source:'A',target:'C',relation:'exposed-to',weight:1},{id:'b',source:'B',target:'C',relation:'exposed-to',weight:1}]};assert.equal(R.runScenario(cancel,[{id:'A',value:1},{id:'B',value:-1}],1).C.value,0);
const entry=(object_id,size=10,status='실행',direction='Long')=>({object_id,name:object_id,size,status,direction});
const impacts={A:{value:-.5}},p=R.portfolioImpact([entry('A'),entry('B',20,'제안'),entry('C',20,'청산'),entry('outside',0)],small,impacts);assert.equal(p.total,-.05);assert.equal(p.rows.length,2);
assert.equal(R.portfolioImpact([entry('outside',0,'실행',null)],small,{}).total,0);assert.equal(R.portfolioImpact([entry('outside',5)],small,{}).total,null);assert.equal(R.portfolioImpact([entry('A',null)],small,{}).total,null);assert.equal(R.portfolioImpact([entry('B',5)],small,{}).rows[0].reason,'모형 경로 없음');assert.equal(R.portfolioImpact([entry('A',10,'실행','Short')],small,impacts).total,.05);
const pack=g.portfolio_correlations,get=R.decodeMatrix(pack),bytes=Buffer.from(pack.correlations,'base64'),counts=Buffer.from(pack.counts,'base64');
assert.equal(R.decodeMatrix({ids:['flat'],correlations:'',counts:'',diagonal:[252],diagonal_valid:[false],minimum:200,scale:10000,missing:32767})('flat','flat').corr,null);
for(const [i,j] of [[1,0],[20,5],[pack.ids.length-1,15]]){const k=i*(i-1)/2+j,v=bytes.readInt16LE(k*2);assert.equal(get(pack.ids[i],pack.ids[j]).corr,v===32767||counts[k]<200?null:v/10000);assert.equal(get(pack.ids[i],pack.ids[j]).corr,get(pack.ids[j],pack.ids[i]).corr);}
const crowd=R.crowding([entry('stock:NVDA'),entry('stock:MSFT'),entry('stock:NVDA'),entry('outside')],g);assert.equal(crowd.objects,3);assert.equal(crowd.expected,3);assert.equal(crowd.available,1);assert(crowd.mean!==null);
assert(R.portfolioNotes([entry('outside')],g).includes('미산출'));assert(R.decisionNotes(entry('stock:NVDA'),g).includes('프리모템'));assert(R.entityNotes('stock:NVDA',g).includes('sec.gov'));
const unsafe={...g,nodes:g.nodes.map((n,i)=>i===0?{...n,name:'<script>alert(1)</script>'}:n)};assert(!R.graphSVG(unsafe).includes('<script>'));assert(R.graphSVG(unsafe).includes('&lt;script&gt;'));
async function checks(){
 let navigation;const c=parse(R.render(g,0));R.bind(c,data,(...args)=>{navigation=args;});let box=c.querySelector('[data-relation-view]');
 const find=s=>box.querySelector(s),all=s=>box.querySelectorAll(s);assert(find('[data-relation-graph]').innerHTML.includes('data-rnode='));assert(find('[data-relation-output]').innerHTML.includes('단일 충격'));
 find('[data-rcontrol="hops"]').value='1';await find('[data-rcontrol="hops"]').fire('change');assert(find('[data-relation-output]').innerHTML.includes('1단계'));
 find('[data-rshock]').value='';await find('[data-rshock]').fire('input');assert(find('[data-relation-output]').innerHTML.includes('범위'));find('[data-rshock]').value='-1';await find('[data-rshock]').fire('input');
 find('[data-rcontrol="kind"]').value='theme';await find('[data-rcontrol="kind"]').fire('change');assert.equal(all('[data-rnode]').length,g.nodes.filter(n=>n.kind==='theme').length);
 find('[data-rsearch]').value='nothing matches 498231';await find('[data-rsearch]').fire('input');assert.equal(all('[data-rnode]').length,0);find('[data-rsearch]').value='';await find('[data-rsearch]').fire('input');
 find('[data-rcontrol="kind"]').value='all';await find('[data-rcontrol="kind"]').fire('change');
 find('[data-rcontrol="relation"]').value='supplies';await find('[data-rcontrol="relation"]').fire('change');assert.equal(all('[data-redge]').length,4);
 await find('[data-rnode="stock:TSM"]').fire('click');assert.equal(find('[data-rcontrol="node"]').value,'stock:TSM');assert(find('[data-relation-detail]').innerHTML.includes('TSMC'));await find('[data-rentity]').fire('click');assert.equal(navigation[0],'Entity 360');
 find('[data-rcorr]').checked=true;await find('[data-rcorr]').fire('change');assert(find('[data-relation-output]').innerHTML.includes('음의 부호 보존'));
 const chart=find('[data-relation-graph]'),before=chart.innerHTML;chart.events.pointerdown[0]({clientX:0,clientY:0});chart.events.pointermove[0]({clientX:40,clientY:10});chart.events.pointerup[0]({});assert.notEqual(chart.innerHTML,before);
 chart.events.wheel[0]({deltaY:200,preventDefault(){}});assert(+find('[data-rzoom]').value<100);await find('[data-rreset]').fire('click');assert.equal(find('[data-rzoom]').value,'100');
 chart.events.pointerdown[0]({pointerId:1,clientX:0,clientY:0});chart.events.pointerdown[0]({pointerId:2,clientX:100,clientY:0});chart.events.pointermove[0]({pointerId:2,clientX:150,clientY:0});assert.equal(+find('[data-rzoom]').value,150);chart.events.pointerup[0]({pointerId:2});chart.events.pointerup[0]({pointerId:1});
 await find('[data-rspin]').fire('click');assert.equal(frames.size,1);R.dispose();assert.equal(frames.size,0,'navigation stops animation');
 const s=parse(R.render({type:'relationscenario',title:'8 scenarios'},1));R.bind(s,data,()=>{});box=s.querySelector('[data-relation-view]');
 for(const scenario of g.scenarios){find('[data-rcontrol="scenario"]').value=scenario.id;await find('[data-rcontrol="scenario"]').fire('change');assert(find('[data-relation-output]').innerHTML.includes(scenario.name));}
 R.dispose();assert.equal(memory.size,0,'read-only diagnostics never write to user storage');console.log('Relation engine, 8 Python/JS scenarios, packed correlations, ledger coverage and offline UI callbacks passed.');
}
module.exports=checks();module.exports.catch(e=>{console.error(e);process.exitCode=1;});
