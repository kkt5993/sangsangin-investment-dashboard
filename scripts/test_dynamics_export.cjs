'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const ctx=vm.createContext({window:{AnalysisCharts:{n:v=>String(v)}},URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/dynamics-export.js'),'utf8'),ctx);
const D=ctx.window.DynamicsExport,sections=[{type:'dynamics',symbol:'^KS11',group:'KOSPI'},{type:'dynamics',symbol:'005930.KS',group:'삼성전자'}];
for(const s of sections){const href=D.link(s,{pathname:'/sangsangin-investment-dashboard/',origin:'https://example.com',search:'?secret=no'});assert.equal(D.selected(sections,{href}),s);const u=new URL(href);assert.equal(u.pathname,'/sangsangin-investment-dashboard/');assert.deepEqual([...u.searchParams.keys()],['dynamics']);assert.equal(u.hash,'#dynamics');}
for(const href of ['bad-url','https://example.com/?dynamics=NVDA#dynamics','https://example.com/?dynamics=%5EKS11#risk','https://example.com/?dynamics=%3Cscript%3E#dynamics'])assert.equal(D.selected(sections,{href}),null);
assert.equal(D.selected(sections),null);assert.deepEqual([...D.wrap({measureText:s=>({width:[...s].length*10})},'가나다😀라',30)],['가나다','😀라']);
console.log('PASS dynamics export: exact known instruments, repository path, clean shared query, malformed routes and Unicode wrapping');
