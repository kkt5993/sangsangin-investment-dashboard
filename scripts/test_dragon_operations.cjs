'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const ctx=vm.createContext({window:{},URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/dragon-operations.js'),'utf8'),ctx);const V=ctx.window.DragonOperations;
for(const [now,next] of [['2026-09-10T22:59:00Z','2026-09-10T23:00:00.000Z'],['2026-09-10T23:00:00Z','2026-09-11T09:00:00.000Z'],['2026-09-11T09:00:00Z','2026-09-13T23:00:00.000Z'],['2026-09-12T01:00:00Z','2026-09-13T23:00:00.000Z']])assert.equal(V.nextRun(new Date(now)).toISOString(),next);
const rows=[{date:'2026-09-01',objects:1,links:2,research:3,signals:0,sites:4,countries:0,insights:null},{date:'2026-09-11',objects:2,links:3,research:3,signals:1,sites:4,countries:0,insights:null}];
let html=V.chart(rows);assert(html.includes('data-history-series="insights" d=""'));assert(!html.includes('NaN'));assert.equal((html.match(/data-history-series=/g)||[]).length,7);assert(V.chart(rows,7).includes('1개 관측일'));
html=V.cards([{id:'x',name:'<script>alert(1)</script>',url:'javascript:alert(1)',detail:'X',status:'unknown',age_hours:null,count:null,cadence_hours:24}]);assert(!html.includes('<script>'));assert(!html.includes('href="javascript:'));assert(html.includes('미확인'));
console.log('PASS: operations schedule KST/weekends, dated growth/null, source provenance and escaping');
