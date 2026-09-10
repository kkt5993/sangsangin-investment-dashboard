'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const base=path.join(__dirname,'..'),context=vm.createContext({window:{ResearchCharts:require('../docs/charts.js')}});
vm.runInContext(fs.readFileSync(path.join(base,'docs/analysis-charts.js'),'utf8'),context);
const A=context.window.AnalysisCharts;
const growth=JSON.parse(fs.readFileSync(path.join(base,'docs/data/growth.json'),'utf8')).sections.find(s=>s.type==='scatter3d');
const before=JSON.stringify(growth),valid=growth.points.filter(p=>[p.x,p.y,p.z].every(Number.isFinite));
for(const yaw of [-3.14,-.65,0,3.14])for(const zoom of [.5,1,1.4]){
 const html=A.scatter3d(growth,yaw,zoom);
 assert.equal((html.match(/data-point=/g)||[]).length,valid.length);
 assert.equal((html.match(/data-3d-tick=/g)||[]).length,9);
 assert(!html.includes('NaN')&&!html.includes('Infinity'));
}
assert.equal(JSON.stringify(growth),before);
const input={title:'<unsafe>',left:'%',right:'pt',guides:[0,2],series:[{name:'긴 계열 <이름>',points:[['2026-01-01',1.234567],['2026-02-01',2]]},{name:'우축',axis:'right',dashed:true,points:[['2026-01-01',100],['2026-02-01',101]]}]};
const html=A.line(input);
assert.equal((html.match(/data-analysis-series=/g)||[]).length,2);
assert.equal((html.match(/data-guide=/g)||[]).length,2);
assert(html.includes('analysis-legend')&&html.includes('우축')&&html.includes('1.234567'));
assert(!html.includes('<unsafe>')&&!html.includes('<이름>'));
console.log('PASS: rotated/zoomed 3D point coverage, finite ticks, immutable inputs, wrapped legends and precise dual-axis observations.');
