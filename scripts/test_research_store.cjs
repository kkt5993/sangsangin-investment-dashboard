/* Exercise actual IndexedDB transactions with the in-memory standard API adapter. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{webcrypto}=require('node:crypto');
const root=path.resolve(__dirname,'..');let IDB;
try{IDB=require('fake-indexeddb');}catch{const data=process.env.SANGSANGIN_DATA_DIR||path.resolve(root,'../sangsangin-investment-data');IDB=require(path.resolve(data,'../sangsangin-investment-tools/test-dependencies/fake-indexeddb'));}
const c=vm.createContext({console,crypto:webcrypto,indexedDB:IDB.indexedDB,structuredClone,TextEncoder,TextDecoder,URL,Blob,atob,btoa});
vm.runInContext(fs.readFileSync(path.join(root,'docs/research-store.js'),'utf8'),c);const S=c.ResearchStore;
const plain=v=>JSON.parse(JSON.stringify(v));
module.exports=(async()=>{
 const repo=await S.open(),second=await S.open();let book=await repo.read();assert.equal(book.entries.length,0);
 const source='Text <img onerror=alert(1)>',r=S.create('principium',{title:'금리 연구',core:source,keywords:['금리','금리','RS'],url:'https://fred.stlouisfed.org/'});
 assert.equal(r.keywords.length,2);assert.equal(r.core,source);
 for(const bad of ['javascript:alert(1)','data:text/html,test','https://name:password@example.com'])assert.throws(()=>S.create('principium',{title:'x',core:'y',url:bad}));
 assert.throws(()=>S.create('iw',{title:'x',core:'y',date:'2026-02-31'}));assert.throws(()=>S.create('iw',{title:'x',core:'y',confidence:0}));
 const pdf=await S.prepare(new Blob(['%PDF-1.7\nlocal fixture\n%%EOF']),'연구.pdf'),png=await S.prepare(new Blob([new Uint8Array([137,80,78,71,13,10,26,10,0])]),'chart.png');
 assert.equal(pdf.meta.mime,'application/pdf');assert.equal(pdf.meta.id.length,64);
 await assert.rejects(S.prepare(new Blob(['<svg onload="alert(1)">']),'fake.png'));
 await assert.rejects(S.prepare(new Blob([new Uint8Array(S.MAX_FILE+1)]),'big.pdf'));
 r.attachments=[pdf.ref];book=await repo.commit(book.revision,b=>S.edit(b,r,[pdf]),[pdf]);assert.equal(book.files.length,1);assert.equal(await (await repo.blob(pdf.meta.id)).text(),'%PDF-1.7\nlocal fixture\n%%EOF');
 const stale=await second.read();book=await repo.commit(book.revision,b=>S.edit(b,{...r,title:'수정'}));await assert.rejects(second.commit(stale.revision,b=>S.trash(b,r.id)),/다른 창/);assert.equal((await repo.read()).entries[0].title,'수정');
 const before=plain(book),put=IDB.IDBObjectStore.prototype.put;
 IDB.IDBObjectStore.prototype.put=function(...args){if(this.name==='meta')throw new DOMException('fixture quota','QuotaExceededError');return put.apply(this,args);};
 const r2=S.create('iw',{title:'주간 판단',core:'테스트',attachments:[png.ref]});
 try{await assert.rejects(repo.commit(book.revision,b=>S.edit(b,r2,[png]),[png]),/quota/);}finally{IDB.IDBObjectStore.prototype.put=put;}
 assert.deepEqual(plain(await repo.read()),before);await assert.rejects(repo.blob(png.meta.id));
 book=await repo.commit(book.revision,b=>S.trash(b,r.id));assert(book.entries[0].deleted_at);assert.equal(book.files.length,1);
 book=await repo.commit(book.revision,b=>S.trash(b,r.id,true));assert.equal(book.entries[0].deleted_at,null);
 const backup=await S.encode(book,repo,'principium'),decoded=await S.decode(backup);assert.equal(decoded.prepared.length,1);
 const damaged=JSON.parse(backup);damaged.files[0].data=btoa('%PDF-1.7\naltered');await assert.rejects(S.decode(JSON.stringify(damaged)),/일치/);
 const transferred=await S.open(IDB.indexedDB,'transfer');let other=await transferred.read();other=await transferred.commit(other.revision,b=>S.merge(b,decoded.book),decoded.prepared);assert.equal(other.entries.length,1);assert.equal((await transferred.blob(pdf.meta.id)).size,pdf.meta.size);
 other=await transferred.commit(other.revision,b=>S.merge(b,decoded.book),decoded.prepared);assert.equal(other.entries.length,1,'identical import is idempotent');
 const conflict=plain(decoded.book);conflict.entries[0].title='conflicting import';other=await transferred.commit(other.revision,b=>S.merge(b,conflict),decoded.prepared);assert.equal(other.entries.length,2);assert.equal(new Set(other.entries.map(r=>r.id)).size,2);
 const old='[{"title":"old","body":"preserve","date":"2026-09-08T00:00:00.000Z"}]',a=await S.legacy(old,'iw'),b=await S.legacy(old,'iw');assert.equal(a.entries[0].id,b.entries[0].id);assert.equal(a.entries[0].core,'preserve');
 assert.throws(()=>S.validate({...S.empty(),entries:[{...r,attachments:[png.ref]}]}),/누락/);
 assert.throws(()=>S.validate({...S.empty(),entries:Array.from({length:501},(_,i)=>({...r,id:String(i),attachments:[]}))}),/500/);
 const korean='한'.repeat(12000);assert.throws(()=>S.validate({...S.empty(),entries:Array.from({length:16},(_,i)=>({...r,id:String(i),core:korean,ideas:korean,evidence:korean,actions:korean,attachments:[]}))}),/2MiB/);
 assert.throws(()=>S.validate({...S.empty(),files:Array.from({length:9},(_,i)=>({id:String(i).padStart(64,'0'),mime:'application/pdf',size:S.MAX_FILE}))}),/64MiB/);
 book=await repo.commit(book.revision,b=>S.trash(b,r.id));book=await repo.commit(book.revision,b=>S.purge(b,r.id));assert.equal(book.entries.length,0);assert.equal(book.files.length,0);await assert.rejects(repo.blob(pdf.meta.id));
 repo.close();second.close();transferred.close();console.log('PASS: research records, attachment hashes, atomic quota rollback, stale-tab rejection, backup round trip, collision copies, trash/restore/purge and legacy identity.');
})().catch(e=>{console.error(e);process.exitCode=1;});
