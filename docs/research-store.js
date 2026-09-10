/* Local research and attachment store. No network, background upload or orders. */
(function(root){
 'use strict';
 const MAX_RECORDS=500,MAX_FILE=25*1024*1024,MAX_FILES=64*1024*1024,MAX_META=2*1024*1024,MAX_IMPORT=90*1024*1024;
 const MODULES=['principium','iw','ask_digest'],KINDS=['article','report','primer'];
 const uid=()=>root.crypto.randomUUID(),now=()=>new Date().toISOString(),copy=v=>structuredClone(v),fail=m=>{throw Error(m);};
 const bytes=s=>new TextEncoder().encode(s).length;
 const str=(v,n,required=false)=>{if(typeof v!=='string'||v.length>n||(required&&!v.trim()))fail('문자 필드의 길이·형식을 확인하세요.');return v.trim();};
 const time=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT/.test(v)&&Number.isFinite(Date.parse(v));
 const day=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\d$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v;
 function url(v){v=str(v||'',2000);if(v){let u;try{u=new URL(v);}catch{fail('출처 주소가 올바르지 않습니다.');}if(!['https:','http:'].includes(u.protocol)||u.username||u.password)fail('출처는 인증정보 없는 HTTP/HTTPS 주소만 사용할 수 있습니다.');}return v;}
 function extraction(a){
  if(!a||a.version!==1||!/^[a-f0-9]{64}$/.test(a.file_id)||!time(a.extracted_at)||!Number.isInteger(a.page_count)||a.page_count<1||a.page_count>1000000||!Array.isArray(a.pages)||a.pages.length<1||a.pages.length>Math.min(300,a.page_count))fail('PDF 추출 메타데이터 오류');
  const pages=a.pages.map((p,i)=>{if(p.number!==i+1||typeof p.text!=='string'||p.text.length>200000||typeof p.cut!=='boolean'||(p.cut&&i!==a.pages.length-1))fail('PDF 페이지·본문 형식 오류');return {number:p.number,label:str(p.label,80,true),text:p.text,cut:p.cut};});
  const characters=pages.reduce((n,p)=>n+p.text.length,0);
  if(characters>200000||characters!==a.characters||a.truncated!==(pages.length<a.page_count||pages.some(p=>p.cut)))fail('PDF 추출 길이·범위 오류');
  return {version:1,file_id:a.file_id,engine:str(a.engine,80,true),extracted_at:a.extracted_at,page_count:a.page_count,pages,characters,truncated:a.truncated,title:str(a.title,160),authors:str(a.authors,200)};
 }
 function entry(a){
  if(!a||Array.isArray(a)||typeof a!=='object')fail('기록 형식 오류');const r={};
  for(const [key,n,required] of [['id',100,true],['title',160,true],['source',200,false],['authors',200,false],['core',12000,true],['ideas',12000,false],['evidence',12000,false],['actions',12000,false],['invalidates',4000,false]])r[key]=str(a[key],n,required);
  if(!MODULES.includes(a.module)||!KINDS.includes(a.kind)||!['draft','active','reviewed'].includes(a.status))fail('분류·상태 오류');
  if(!['', '상승','중립','하락','혼합'].includes(a.direction)||!['','1W','1M','3M','12M'].includes(a.horizon))fail('방향·기간 오류');
  if(a.confidence!==null&&(!Number.isInteger(a.confidence)||a.confidence<1||a.confidence>5))fail('확신도는 1~5 정수입니다.');
  if(!day(a.date)||(a.review_date!==''&&!day(a.review_date)))fail('날짜를 확인하세요.');
  if(!time(a.created_at)||!time(a.updated_at)||(a.deleted_at!==null&&!time(a.deleted_at)))fail('저장 시각 오류');
  if(!Array.isArray(a.keywords)||a.keywords.length>20)fail('키워드는 최대20개입니다.');
  const seen=new Set();r.keywords=a.keywords.map(k=>str(k,40,true)).filter(k=>{const x=k.toLocaleLowerCase();if(seen.has(x))return false;seen.add(x);return true;});
  if(!Array.isArray(a.attachments)||a.attachments.length>12)fail('첨부는 기록당 최대12개입니다.');
  r.attachments=a.attachments.map(f=>{if(!/^[a-f0-9]{64}$/.test(f.id))fail('첨부 ID 오류');return {id:f.id,name:str(f.name,160,true)};});
  if(new Set(r.attachments.map(f=>f.id)).size!==r.attachments.length)fail('같은 첨부가 중복되었습니다.');
  if(a.extractions!==undefined&&(!Array.isArray(a.extractions)||a.extractions.length>12))fail('PDF 추출 연결 오류');
  r.extractions=(a.extractions||[]).map(extraction);
  if(new Set(r.extractions.map(x=>x.file_id)).size!==r.extractions.length||r.extractions.some(x=>!r.attachments.some(f=>f.id===x.file_id)))fail('PDF 추출의 원문 첨부가 누락·중복되었습니다.');
  if(!Array.isArray(a.history)||a.history.length>20)fail('변경 이력 오류');r.history=a.history.map(h=>{if(!time(h.at))fail('변경 시각 오류');return {at:h.at,action:str(h.action,80,true)};});
  for(const k of ['module','kind','status','direction','horizon','confidence','date','review_date','created_at','updated_at','deleted_at'])r[k]=a[k];
  r.url=url(a.url);return r;
 }
 function create(module,input={}){const t=now();return entry({id:uid(),module,kind:'report',title:'',source:'',authors:'',url:'',date:t.slice(0,10),core:'',ideas:'',evidence:'',actions:'',invalidates:'',keywords:[],direction:'',horizon:'',confidence:null,status:'draft',review_date:'',attachments:[],created_at:t,updated_at:t,deleted_at:null,history:[{at:t,action:'등록'}],...input});}
 const empty=()=>({version:2,revision:'',entries:[],files:[]});
 function validate(book){
  if(!book||![1,2].includes(book.version)||typeof book.revision!=='string'||!Array.isArray(book.entries)||book.entries.length>MAX_RECORDS||!Array.isArray(book.files))fail('노트북 형식·500건 한도를 확인하세요.');
  const b={version:2,revision:book.revision,entries:book.entries.map(entry),files:book.files.map(f=>{if(!f||!/^[a-f0-9]{64}$/.test(f.id)||!['application/pdf','image/png','image/jpeg','image/webp'].includes(f.mime)||!Number.isInteger(f.size)||f.size<1||f.size>MAX_FILE)fail('첨부 메타데이터 오류');return {id:f.id,mime:f.mime,size:f.size};})};
  if(new Set(b.entries.map(r=>r.id)).size!==b.entries.length||new Set(b.files.map(f=>f.id)).size!==b.files.length)fail('중복된 ID가 있습니다.');
  const ids=new Set(b.files.map(f=>f.id));for(const r of b.entries)for(const f of r.attachments)if(!ids.has(f.id))fail('본문에 연결된 첨부가 누락되었습니다.');
  for(const r of b.entries)for(const x of r.extractions)if(b.files.find(f=>f.id===x.file_id)?.mime!=='application/pdf')fail('추출 본문은 PDF 원문에만 연결할 수 있습니다.');
  if(b.files.reduce((n,f)=>n+f.size,0)>MAX_FILES)fail('첨부 전체 한도64MiB를 넘었습니다.');
  if(bytes(JSON.stringify(b))>MAX_META)fail('글·메타데이터 한도2MiB를 넘었습니다.');return b;
 }
 function signature(a){if(a[0]===0x25&&a[1]===0x50&&a[2]===0x44&&a[3]===0x46&&a[4]===0x2d)return 'application/pdf';if([137,80,78,71,13,10,26,10].every((v,i)=>a[i]===v))return 'image/png';if(a[0]===255&&a[1]===216&&a[2]===255)return 'image/jpeg';if(String.fromCharCode(...a.slice(0,4))==='RIFF'&&String.fromCharCode(...a.slice(8,12))==='WEBP')return 'image/webp';fail('PDF·PNG·JPEG·WebP 파일만 첨부할 수 있습니다.');}
 async function prepare(blob,name){if(!blob||!Number.isInteger(blob.size)||blob.size<1||blob.size>MAX_FILE)fail('파일당25MiB 이하만 첨부할 수 있습니다.');const buffer=await blob.arrayBuffer(),a=new Uint8Array(buffer),mime=signature(a),hash=await root.crypto.subtle.digest('SHA-256',buffer),id=Array.from(new Uint8Array(hash),v=>v.toString(16).padStart(2,'0')).join('');return {meta:{id,mime,size:blob.size},ref:{id,name:str(name,160,true)},blob:new Blob([buffer],{type:mime})};}
 const changed=(r,action)=>{const t=now();return {...r,updated_at:t,history:[...r.history,{at:t,action}].slice(-20)};};
 function update(book,id,fn){const r=book.entries.find(r=>r.id===id);if(!r)fail('기록을 찾지 못했습니다.');return {...book,entries:book.entries.map(a=>a.id===id?fn(copy(r)):a)};}
 function edit(book,record,prepared=[]){
  const next=entry(record),old=book.entries.find(r=>r.id===next.id);if(old&&(old.module!==next.module||old.created_at!==next.created_at))fail('기록 소유 분류·생성시각을 바꿀 수 없습니다.');
  if(old&&(old.updated_at!==next.updated_at||JSON.stringify(old.history)!==JSON.stringify(next.history)))fail('편집을 시작한 뒤 기록이 바뀌었습니다. 최신 기록을 다시 편집하거나 입력을 사본으로 저장하세요.');
  const files=[...book.files];for(const f of prepared)if(!files.some(a=>a.id===f.meta.id))files.push(f.meta);
  return {...book,files,entries:old?book.entries.map(r=>r.id===next.id?changed(next,'수정'):r):[next,...book.entries]};
 }
 function trash(book,id,restore=false){return update(book,id,r=>changed({...r,deleted_at:restore?null:now()},restore?'복원':'휴지통 이동'));}
 function purge(book,id){const r=book.entries.find(r=>r.id===id);if(!r?.deleted_at)fail('휴지통 기록만 영구 삭제할 수 있습니다.');return {...book,entries:book.entries.filter(r=>r.id!==id)};}
 function merge(book,incoming){
  const source=validate(incoming),result=copy(book);for(const f of source.files){const old=result.files.find(a=>a.id===f.id);if(old&&(old.size!==f.size||old.mime!==f.mime))fail('첨부 무결성 충돌');if(!old)result.files.push(f);}
  for(let r of source.entries){const same=result.entries.find(a=>a.id===r.id);if(same&&JSON.stringify(same)===JSON.stringify(r))continue;if(same)r=changed({...r,id:uid()},'충돌 사본 가져오기');result.entries.push(r);}return result;
 }
 async function legacy(raw,module){const list=JSON.parse(raw);if(!Array.isArray(list)||list.length>MAX_RECORDS)fail('이전 메모 형식을 확인하세요.');const entries=[];for(const a of list){const hash=await root.crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify([a.title,a.body,a.date]))),id='legacy-'+module+'-'+Array.from(new Uint8Array(hash),v=>v.toString(16).padStart(2,'0')).join('');if(entries.some(r=>r.id===id))continue;entries.push(create(module,{id,title:str(a.title,160,true),core:str(a.body,12000,true),date:time(a.date)?a.date.slice(0,10):now().slice(0,10),history:[{at:now(),action:'이전 메모 가져오기'}]}));}return {...empty(),entries};}
 function open(indexedDB=root.indexedDB,name='sangsangin-research-v1'){
  return new Promise((resolve,reject)=>{if(!indexedDB){reject(Error('이 브라우저에서 로컬 자료 저장을 사용할 수 없습니다.'));return;}const req=indexedDB.open(name,2);let abandoned=false;
   req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains('meta'))db.createObjectStore('meta');if(!db.objectStoreNames.contains('files'))db.createObjectStore('files');};req.onerror=()=>reject(req.error);req.onblocked=()=>{abandoned=true;reject(Error('다른 창의 이전 자료 연결을 닫고 새로고침하세요.'));};
   req.onsuccess=()=>{const db=req.result;if(abandoned){db.close();return;}db.onversionchange=()=>db.close();resolve(repository(db));};
  });
 }
 function repository(db){
  const read=()=>new Promise((resolve,reject)=>{const tx=db.transaction('meta','readonly'),req=tx.objectStore('meta').get('book');let value;req.onsuccess=()=>{try{value=validate(req.result||empty());}catch(e){reject(e);}};tx.oncomplete=()=>resolve(value);tx.onabort=()=>reject(tx.error||Error('자료를 읽지 못했습니다.'));});
  const commit=(revision,transform,prepared=[])=>new Promise((resolve,reject)=>{
   const tx=db.transaction(['meta','files'],'readwrite'),meta=tx.objectStore('meta'),files=tx.objectStore('files'),req=meta.get('book');let next,error;
   req.onsuccess=()=>{try{const current=validate(req.result||empty());if(current.revision!==revision)fail('다른 창에서 자료가 바뀌었습니다. 입력을 보관한 뒤 새로 읽어주세요.');
     next=transform(copy(current));const needed=new Set(next.entries.flatMap(r=>r.attachments.map(f=>f.id)));next.files=next.files.filter(f=>needed.has(f.id));next=validate({...next,revision:uid()});
     const supplied=new Map(prepared.map(p=>[p.meta.id,p]));for(const f of next.files)if(!current.files.some(a=>a.id===f.id)){const p=supplied.get(f.id);if(!p||p.meta.size!==f.size||p.meta.mime!==f.mime)fail('새 첨부의 원본 파일이 누락되었습니다.');files.put(p.blob,f.id);}
     for(const f of current.files)if(!needed.has(f.id))files.delete(f.id);meta.put(next,'book');
    }catch(e){error=e;tx.abort();}};
   tx.oncomplete=()=>resolve(copy(next));tx.onabort=()=>reject(error||tx.error||Error('저장하지 못했습니다. 기존 글과 첨부는 유지됩니다.'));
  });
  const blob=id=>new Promise((resolve,reject)=>{const tx=db.transaction('files','readonly'),req=tx.objectStore('files').get(id);let data;req.onsuccess=()=>{data=req.result;};tx.oncomplete=()=>data?resolve(data):reject(Error('첨부 원본을 찾지 못했습니다.'));tx.onabort=()=>reject(tx.error);});
  return {read,commit,blob,close:()=>db.close()};
 }
 async function encode(book,repo,module){const entries=book.entries.filter(r=>r.module===module),ids=new Set(entries.flatMap(r=>r.attachments.map(f=>f.id))),files=[];
  for(const f of book.files.filter(f=>ids.has(f.id))){const a=new Uint8Array(await (await repo.blob(f.id)).arrayBuffer());let s='';for(let i=0;i<a.length;i+=16384)s+=String.fromCharCode(...a.subarray(i,i+16384));files.push({...f,data:btoa(s)});}
  return JSON.stringify({format:'sangsangin-research',version:2,revision:book.revision,entries,files});
 }
 async function decode(raw){if(bytes(raw)>MAX_IMPORT)fail('가져오기 파일은90MiB 이하만 지원합니다.');const a=JSON.parse(raw);if(a?.format!=='sangsangin-research')fail('리서치 백업 파일이 아닙니다.');const book=validate(a),prepared=[];
  for(const f of a.files){if(typeof f.data!=='string'||f.data.length>Math.ceil(MAX_FILE/3)*4||!/^[A-Za-z0-9+/]*={0,2}$/.test(f.data))fail('첨부 인코딩 오류');const binary=atob(f.data),buffer=Uint8Array.from(binary,c=>c.charCodeAt(0)),p=await prepare(new Blob([buffer]),'backup');if(p.meta.id!==f.id||p.meta.size!==f.size||p.meta.mime!==f.mime)fail('첨부 파일의 해시·크기·형식이 일치하지 않습니다.');prepared.push(p);}
  return {book,prepared};
 }
 root.ResearchStore={open,create,entry,validate,extraction,edit,trash,purge,merge,legacy,prepare,encode,decode,empty,MAX_FILE,MAX_FILES,MAX_IMPORT,KINDS};
})(typeof window==='undefined'?globalThis:window);
