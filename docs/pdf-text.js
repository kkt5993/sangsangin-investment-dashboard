/* Page-cited local PDF extraction. The document never leaves the browser. */
(function(root){
 'use strict';const VERSION='6.3.289',MAX_PAGES=300,MAX_CHARS=200000;
 const base=typeof document==='undefined'||!document.currentScript?.src?null:new URL('.',document.currentScript.src);let parser;
 const E=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 async function library(){
  if(!parser)parser=import(new URL('vendor/pdfjs/legacy/build/pdf.min.mjs',base).href).then(p=>{p.GlobalWorkerOptions.workerSrc=new URL('vendor/pdfjs/legacy/build/pdf.worker.min.mjs',base).href;return p;}).catch(e=>{parser=null;throw e;});
  return parser;
 }
 function pageText(items){let out='',previous=null;
  for(const item of items){if(typeof item.str!=='string')continue;const text=item.str.replace(/\u0000/g,'');
   if(text&&previous&&out&&!/\s$/.test(out)&&!/^\s/.test(text)){
    const a=previous.transform,b=item.transform,h=Math.max(1,Math.abs(item.height||0));
    if(a&&b&&Math.abs(a[5]-b[5])>h*.65)out+='\n';
    else if(!a||!b||b[4]-(a[4]+previous.width)>Math.max(.5,h*.08))out+=' ';
   }
   out+=text;if(item.hasEOL)out+='\n';previous=item;
  }
  return out.replace(/[ \t]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').trim();
 }
 async function extract(blob,options={}){
  if(!blob||blob.size<5||blob.size>25*2**20)throw Error('PDF는 파일당25MiB 이하만 읽을 수 있습니다.');
  const buffer=await blob.arrayBuffer();if(String.fromCharCode(...new Uint8Array(buffer,0,5))!=='%PDF-')throw Error('PDF 파일 형식을 확인하세요.');
  const hash=await root.crypto.subtle.digest('SHA-256',buffer),file_id=Array.from(new Uint8Array(hash),v=>v.toString(16).padStart(2,'0')).join('');
  let task,timer,rejectStop,stopped=false;
  const stop=new Promise((_,reject)=>{rejectStop=reject;});
  const cancel=()=>{stopped=true;rejectStop(Error('PDF 읽기를 취소했습니다.'));if(task)task.destroy().catch(()=>{});};
  const work=async()=>{
   if(options.signal?.aborted)throw Error('PDF 읽기를 취소했습니다.');
   const p=options.pdfjs||await library();if(stopped)throw Error('PDF 읽기를 취소했습니다.');
   const resources=options.resources||(base?{cMapUrl:new URL('vendor/pdfjs/cmaps/',base).href,standardFontDataUrl:new URL('vendor/pdfjs/standard_fonts/',base).href}:{});
   task=p.getDocument({data:new Uint8Array(buffer),...resources,cMapPacked:true,isEvalSupported:false,useWasm:false,disableFontFace:true,enableXfa:false,stopAtErrors:true,verbosity:0});
   const doc=await task.promise;const metadata=await doc.getMetadata().catch(()=>({info:{}})),labels=await doc.getPageLabels().catch(()=>null),pages=[];let characters=0,truncated=false;
   for(let number=1;number<=Math.min(doc.numPages,MAX_PAGES);number++){
    if(stopped)throw Error('PDF 읽기를 취소했습니다.');
    const page=await doc.getPage(number);let text;
    try{text=pageText((await page.getTextContent()).items);}finally{page.cleanup();}
    const remaining=MAX_CHARS-characters,cut=text.length>remaining;
    if(cut){text=text.slice(0,remaining);if(/[\uD800-\uDBFF]$/.test(text))text=text.slice(0,-1);truncated=true;}
    pages.push({number,label:(String(labels?.[number-1]||number).trim().slice(0,80)||String(number)),text,cut});characters+=text.length;
    options.onProgress?.({page:number,total:doc.numPages,characters});
    if(cut||characters>=MAX_CHARS){truncated ||=number<doc.numPages;break;}
   }
   truncated ||=pages.length<doc.numPages;
   return {version:1,file_id,engine:'PDF.js '+VERSION,extracted_at:new Date().toISOString(),page_count:doc.numPages,pages,characters,truncated,title:String(metadata.info?.Title||'').trim().slice(0,160),authors:String(metadata.info?.Author||'').trim().slice(0,200)};
  };
  options.signal?.addEventListener('abort',cancel,{once:true});
  timer=setTimeout(()=>{stopped=true;rejectStop(Error('PDF 읽기 시간90초를 넘었습니다. 원문을 나누어 다시 시도하세요.'));if(task)task.destroy().catch(()=>{});},90000);
  try{return await Promise.race([work(),stop]);}
  catch(e){if(e?.name==='PasswordException')throw Error('암호화된 PDF입니다. 이 화면은 문서 암호 입력을 지원하지 않습니다.');if(e?.name==='InvalidPDFException')throw Error('손상되었거나 읽을 수 없는 PDF입니다. 원문을 확인하세요.');throw e;}
  finally{clearTimeout(timer);options.signal?.removeEventListener('abort',cancel);if(task)await task.destroy().catch(()=>{});}
 }
 function status(a){const empty=a.pages.filter(p=>!p.text.trim()).length;return `${a.pages.length}/${a.page_count}쪽 · ${a.characters.toLocaleString()}자${a.truncated?' · 일부만 추출':''}${empty?' · 본문 없는 페이지 '+empty+'쪽 (스캔·그림은 OCR 필요)':''}`;}
 function plain(a,name){return `${name}\n${status(a)}\n${a.engine} · ${a.extracted_at}\nSHA-256 ${a.file_id}\n\n`+a.pages.map(p=>`[PDF ${p.number}쪽 · 문서 표기 ${p.label}]${p.cut?' (페이지 일부)':''}\n${p.text||'(텍스트 없음)'}\n`).join('\n');}
 function citation(a,name,page,text){return `[원문: ${name} · PDF ${page.number}쪽 · 표기 ${page.label} · SHA-256 ${a.file_id}]\n${text.trim()}`;}
 function view(a,name){return `<details class="pdf-extraction"><summary>${E(name)} · ${E(status(a))}</summary><p class="quiet">${E(a.engine)} · ${E(a.extracted_at)} · 원문 배치·표의 읽기 순서는 별도 확인하세요.</p>${a.pages.map(p=>`<details><summary>PDF ${p.number}쪽 · 표기 ${E(p.label)}${p.cut?' · 페이지 일부':''}</summary><pre>${E(p.text||'텍스트가 없습니다. 스캔·그림은 OCR이 필요합니다.')}</pre></details>`).join('')}</details>`;}
 root.PDFText={extract,pageText,status,plain,citation,view,MAX_PAGES,MAX_CHARS,VERSION};
})(typeof window==='undefined'?globalThis:window);
