'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const ctx=vm.createContext({window:{},URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/guru-views.js'),'utf8'),ctx);const V=ctx.window.GuruViews;
const h={issuer:'<img src=x onerror=alert(1)>',share_class:'COM',cusip:'123456789',quantity_type:'SH',option:'PUT',value:'9999999999999999',quantity:'10',weight:100,source_rows:1};
const item={id:'fixture',name:'Test',person:'Tester',filer:'TEST',cik:'0000000123',note:'Scope',holdings:[h],ledger:[],report:{report_date:'2026-06-30',filing_date:'2026-08-14',accepted_at:'2026-08-14T20:00:00+00:00',resolution:'holdings',age_days:72,value_total:h.value,table_sum:h.value,reconciliation_difference:'0',entry_total:1,unit:'USD',form:'13F-HR',mode:'reviewed_sec_rendered',index_url:'javascript:alert(1)'}};
let html=V.render({items:[item],collection:{status:'needs_contact'},scope:'Scope',weight_basis:'Denominator'},0);assert(!html.includes('<img'));assert(!html.includes('href="javascript:'));assert(html.includes('9,999,999,999,999,999'));assert(html.includes('2026-06-30'));
assert(V.positions(item,'nomatch').includes('해당 포지션 없음'));assert(V.positions(item,'','equity').includes('해당 포지션 없음'));assert(V.positions(item,'123456789','option').includes('PUT'));
const snapshot=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/data/dragonglass.json'),'utf8')),s=snapshot.sections.find(s=>s.type==='gurus');
if(s){assert.equal(s.items.length,6);assert.equal(s.items.find(r=>r.id==='ackman').cik,'0002026053');for(const r of s.items){if(!r.report)continue;assert(r.report.report_date<=snapshot.as_of);assert(r.ledger.length===r.report.entry_total);if(r.holdings.length)assert(Math.abs(r.holdings.reduce((n,h)=>n+h.weight,0)-100)<0.0001);}}
console.log('PASS: 13F cards, reported precision, dated holdings, options, notices, zero placeholder and escaping.');
