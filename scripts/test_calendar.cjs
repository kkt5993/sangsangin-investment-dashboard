'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{parse}=require('./test_dom_stub.cjs');
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),d=JSON.parse(read('docs/data/regime.json')),ctx=vm.createContext({window:{},console});
for(const f of ['charts','calendar-views'])vm.runInContext(read('docs/'+f+'.js'),ctx);
const V=ctx.window.CalendarViews,live=d.sections.find(s=>s.type==='releasecalendar');
const item=(id,region,day,at,category,name)=>({id,region,date:day,display_date:day,kst_at:at,category,name,notes:'',agency:region==='KR'?'한국은행':'FOMC',url:'https://www.bok.or.kr/fixture',observed_at:'2026-09-01T01:00:00Z',observed_kst_date:'2026-09-01',source_status:'ok',age_days:0,date_basis:region==='KR'?'한국시간':'미국 현지 날짜'});
const s={from_date:'2026-09-01',to_date:'2026-11-29',days:90,sources:[],note:'예정 일정',items:[item('a','KR','2026-09-01','2026-09-01T08:00:00+09:00','물가','소비자물가'),item('b','KR','2026-09-07',null,'정책회의','한국 회의'),item('c','US','2026-09-08',null,'정책회의','FOMC'),item('d','KR','2026-11-29',null,'정책회의','말일 회의')]};
module.exports=(async()=>{
 assert(live);const h=V.render(live,0);assert(!/\b(NaN|Infinity|undefined)\b/.test(h));assert.equal((h.match(/data-release-id=/g)||[]).length,live.items.length);
 assert.equal(V.filtered(s,'all',7).length,2);assert.equal(V.filtered(s,'all',90).length,4);assert.equal(V.filtered(s,'US',90).length,1);
 const box=parse(V.render(s,0));V.bind(box,[s]);const region=box.querySelector('[data-release-region]'),days=box.querySelector('[data-release-days]'),group=box.querySelector('[data-release-group]'),search=box.querySelector('[data-release-search]'),out=box.querySelector('[data-release-output]');
 const ids=()=>out.querySelectorAll('[data-release-id]').map(r=>r.dataset.releaseId);
 region.value='KR';await region.fire('change');assert.deepEqual(ids(),['a','b','d']);days.value='7';await days.fire('change');assert.deepEqual(ids(),['a','b']);group.value='정책회의';await group.fire('change');assert.deepEqual(ids(),['b']);
 search.value='nothing found';await search.fire('input');assert.equal(ids().length,0);assert(out.innerHTML.includes('조건에 맞는'));
 search.value='';days.value='90';region.value='US';await region.fire('change');assert.deepEqual(ids(),['c']);assert(out.innerHTML.includes('미국 현지 날짜 · 시각 미표기'));assert(!out.innerHTML.includes('00:00 KST'));
 const bad={...s.items[0],name:'<img src=x onerror=alert(1)>',url:'javascript:alert(1)',source_status:'stale',age_days:9};const html=V.rows([bad]);assert(!html.includes('<img'));assert(html.includes('&lt;img'));assert(!html.includes('href="javascript:'));assert(html.includes('이전 일정 유지'));assert(html.includes('9일 경과'));
 assert(read('docs/research-dashboard.js').includes('root.CalendarViews.bind(container,d.sections)'));
 console.log('Calendar: real releases,90/30/7day boundaries,region/category/search callbacks,unknown times,stale sources and escaping passed.');
})();
