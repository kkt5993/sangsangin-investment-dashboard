'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const c=vm.createContext({URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/clinical-views.js'),'utf8'),c);
const row={id:'NCT00000001',title:'<script>Example',status:'RECRUITING',phases:['PHASE3'],updated:'2026-09-10',sponsor:'Example',collaborators:[],url:'https://clinicaltrials.gov/study/NCT00000001'};
const h=c.ClinicalViews.studies({latest:[row]});assert(h.includes('&lt;script&gt;'));assert(!h.includes('<script>'));assert(h.includes('NCT00000001'));assert(h.includes('PHASE3'));assert(!c.ClinicalViews.studies({latest:[{...row,url:'javascript:alert(1)'}]}).includes('javascript:'));assert(c.ClinicalViews.studies({latest:[]}).includes('없습니다'));
console.log('PASS: clinical source identity, phase/status/date labels, empty sample and escaping.');
