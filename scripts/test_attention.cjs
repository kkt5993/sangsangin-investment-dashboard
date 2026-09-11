'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ctx=vm.createContext({window:{},URL});vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/attention-views.js'),'utf8'),ctx);const V=ctx.window.AttentionViews;
const p=[{date:'2026-09-01',views:0},{date:'2026-09-02',views:10},{date:'2026-09-04',views:20}];let h=V.plot(p);assert(h.includes('M50'));assert.equal((h.match(/<circle /g)||[]).length,3);assert(h.includes('2026-09-04'));assert(!h.includes('NaN'));assert(h.includes('L')&&h.includes('M'));
h=V.detail({title:'<script>bad</script>',pageid:1,wikidata:'Q1',points:p,metrics:{end:'2026-09-04',change:null,recent:null,previous:null},article_url:'javascript:alert(1)',source_url:'https://evil.example/'});assert(!h.includes('<script>'));assert(!h.includes('href="javascript:'));assert(!h.includes('href="https://evil'));assert(h.includes('미산출'));assert.equal(V.entityNotes({}),'');
console.log('PASS: attention UTC series, gaps/zero, unavailable changes, safe source links and entity content');
