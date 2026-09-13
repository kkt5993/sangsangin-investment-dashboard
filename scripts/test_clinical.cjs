'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const c=vm.createContext({URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/clinical-views.js'),'utf8'),c);
const row={id:'NCT00000001',title:'<script>Example',status:'RECRUITING',phases:['PHASE3'],updated:'2026-09-10',sponsor:'Example',collaborators:[],url:'https://clinicaltrials.gov/study/NCT00000001'};
const tracked={...row,changed_fields:['status'],history:[{...row,first_observed_at:'2026-09-09T00:00:00+00:00',last_observed_at:'2026-09-09T00:00:00+00:00',last_data_version:'2026-09-09T09:00:04'},{...row,status:'COMPLETED',first_observed_at:'2026-09-10T00:00:00+00:00',last_observed_at:'2026-09-11T00:00:00+00:00',last_data_version:'2026-09-10T09:00:04'}]};
const h=c.ClinicalViews.studies({latest:[tracked]});assert(h.includes('&lt;script&gt;'));assert(!h.includes('<script>'));assert(h.includes('NCT00000001'));assert(h.includes('PHASE3'));assert(h.includes('표본 관측 이력 2개 상태'));assert(h.includes('이번 상태 변경 상태'));assert(h.includes('COMPLETED'));assert(!c.ClinicalViews.studies({latest:[{...row,url:'javascript:alert(1)'}]}).includes('javascript:'));assert(c.ClinicalViews.studies({latest:[]}).includes('없습니다'));
console.log('PASS: clinical source identity, phase/status/date labels, sample history, empty sample and escaping.');
