'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{webcrypto}=require('node:crypto'),{parse}=require('./test_dom_stub.cjs');
const root=path.resolve(__dirname,'..'),data=process.env.SANGSANGIN_DATA_DIR||path.resolve(root,'../sangsangin-investment-data');let IDB;
try{IDB=require('fake-indexeddb');}catch{IDB=require(path.resolve(data,'../sangsangin-investment-tools/test-dependencies/fake-indexeddb'));}
const downloads=[],c=vm.createContext({console,crypto:webcrypto,indexedDB:IDB.indexedDB,structuredClone,TextEncoder,TextDecoder,URL,Blob,atob,btoa,setTimeout,clearTimeout,AbortController,confirm:()=>true,localStorage:{getItem:()=>null},document:{createElement:()=>({click(){downloads.push(this.download);}})}});
for(const f of ['research-store','pdf-text','notebook-pdf','research-notes'])vm.runInContext(fs.readFileSync(path.join(root,'docs',f+'.js'),'utf8'),c);
module.exports=(async()=>{
 await require('./test_pdf_text.cjs');
 const S=c.ResearchStore,N=c.ResearchNotes,a=JSON.parse(fs.readFileSync(path.join(data,'runtime/pdf-fixtures/extraction.json'),'utf8')),seed={mode:'principium',items:[]};
 const repo=await S.open(IDB.indexedDB,'pdf-notebook-ui'),el=parse(N.view(seed,0));let signal;
 await N.mount(el,seed,{repo,extract:async(blob,o)=>{signal=o.signal;o.onProgress({page:3,total:3,characters:a.characters});return structuredClone(a);}});
 const q=s=>el.querySelector(s),field=k=>q('[data-nb-field="'+k+'"]'),click=k=>q('[data-nb-'+k+']').fire('click');
 const file=new Blob([fs.readFileSync(path.join(data,'runtime/pdf-fixtures/mixed.pdf'))],{type:'application/pdf'});file.name='한글 연구.pdf';q('[data-nb-upload]').files=[file];await q('[data-nb-upload]').fire('change');
 assert.equal(q('[data-nb-pdf-select]').value,'new:0');await click('pdf-extract');assert(signal);assert.equal(field('title').value,'한국 금리 연구');assert.equal(field('authors').value,'상상인 테스트');assert(field('core').value.includes('자동 요약이 아닙니다'));assert.equal(q('[data-nb-pdf-result]').hidden,false);
 q('[data-nb-pdf-page]').value='2';await q('[data-nb-pdf-page]').fire('change');assert(q('[data-nb-pdf-quote]').value.includes('-123억 원'));
 field('evidence').value='기존 근거';await click('pdf-evidence');assert(field('evidence').value.startsWith('기존 근거'));assert(field('evidence').value.includes('PDF 2쪽'));assert(field('evidence').value.includes(a.file_id));
 await click('pdf-download');assert.equal(downloads.at(-1),'한글 연구.pdf.txt');await click('save');q('[data-nb-upload]').files=[];
 let book=await repo.read();assert.equal(book.version,2);assert.equal(book.entries.length,1);assert.equal(book.entries[0].extractions[0].pages[1].text,a.pages[1].text);assert(q('[data-nb-list]').innerHTML.includes('PDF 2쪽'));
 const id=book.entries[0].id;q('[data-nb-search]').value='1,234.50';await q('[data-nb-search]').fire('input');assert.equal(el.querySelectorAll('[data-note-id]').length,1,'extracted body must be searchable');q('[data-nb-search]').value='';await q('[data-nb-search]').fire('input');
 await q('[data-nb-edit="'+id+'"]').fire('click');field('title').value='검토자가 입력한 제목';field('authors').value='직접 작성';await click('pdf-extract');assert.equal(field('title').value,'검토자가 입력한 제목');assert.equal(field('authors').value,'직접 작성');
 q('[data-nb-pdf-quote]').value='x'.repeat(12000);const before=field('evidence').value;await click('pdf-evidence');assert.equal(field('evidence').value,before);assert(q('[data-nb-message]').textContent.includes('한도'));
 const backup=await S.encode(book,repo,'principium'),decoded=await S.decode(backup);assert.equal(decoded.book.entries[0].extractions[0].file_id,a.file_id);assert.equal(decoded.book.entries[0].extractions[0].pages[0].text,a.pages[0].text);
 for(const change of [x=>x.characters++,x=>x.pages[1].number=1,x=>x.file_id='0'.repeat(64),x=>x.truncated=true]){const bad=JSON.parse(backup);change(bad.entries[0].extractions[0]);await assert.rejects(S.decode(JSON.stringify(bad)),/PDF/);}
 const legacy=JSON.parse(backup);legacy.version=1;delete legacy.entries[0].extractions;const old=await S.decode(JSON.stringify(legacy));assert.equal(old.book.version,2);assert.equal(old.book.entries[0].extractions.length,0);assert.equal(old.prepared[0].meta.id,a.file_id);
 // Upgrade the existing DB, preserving its records and binary attachments.
 const oldDB=await new Promise((resolve,reject)=>{const req=IDB.indexedDB.open('pdf-migration',1);req.onupgradeneeded=()=>{req.result.createObjectStore('meta');req.result.createObjectStore('files');};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});
 await new Promise((resolve,reject)=>{const tx=oldDB.transaction(['meta','files'],'readwrite');tx.objectStore('meta').put({...old.book,version:1},'book');tx.objectStore('files').put(old.prepared[0].blob,a.file_id);tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error);});oldDB.onversionchange=()=>oldDB.close();
 const migrated=await S.open(IDB.indexedDB,'pdf-migration'),m=await migrated.read();assert.equal(m.entries[0].title,book.entries[0].title);assert.equal((await migrated.blob(a.file_id)).size,file.size);assert.equal(m.version,2);migrated.close();
 await q('[data-nb-remove]').fire('click');await click('save');book=await repo.read();assert.equal(book.entries[0].attachments.length,0);assert.equal(book.entries[0].extractions.length,0);
 N.dispose();repo.close();console.log('PASS: PDF selection/extraction, metadata preservation, page citations, body search, saved text, backup/migration integrity and attachment removal; actual UI callbacks.');
})().catch(e=>{console.error(e);process.exitCode=1;});
