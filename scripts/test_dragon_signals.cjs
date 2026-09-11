'use strict';
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const c=vm.createContext({URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/dragon-signals.js'),'utf8'),c);const S=c.DragonSignals;
const row={id:'stock:A',name:'A <script>',symbol:'A',market:'US',sector:'IT',date:'2026-09-10',observed_score:4,hits:[{id:'leaders',label:'RS',weight:2,date:'2026-09-10',detail:'x'},{id:'discovery',label:'발굴',weight:2,date:'2026-09-10',detail:'y'}],degree:1,documents:1,evidence_score:8.2,suppliers:[],customers:[],documents_detail:[{title:'<bad>',url:'javascript:alert(1)',date:'2026-09-09'}]};
const html=S.card(row,0);assert(!html.includes('<script>'));assert(!html.includes('javascript:'));assert(html.includes('전체 점수 미산출'));assert(html.includes('#rs'));assert(html.includes('#discovery'));assert.equal(S.filter([row],'US','발굴').length,1);assert.equal(S.filter([row],'KR','').length,0);assert.equal(S.filter([row],'all','none').length,0);
console.log('PASS: signal card escaping, unknown full score, source links, market and signal search.');
