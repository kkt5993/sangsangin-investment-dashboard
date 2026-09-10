/* Page-cited local PDF extraction. The document never leaves the browser. */
(function(root){
 'use strict';const VERSION='6.3.289',MAX_PAGES=300,MAX_CHARS=200000,MAX_OCR_PAGES=30,PROFILE='hybrid-2';
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
  const mode=options.mode||'text',language=options.language||'kor+eng',layout=options.layout||'single',O=options.ocr||root.PDFOCR;
  if(!['text','auto','ocr'].includes(mode)||!['kor+eng','eng'].includes(language)||!['single','columns'].includes(layout)||![undefined,216,300].includes(options.dpi))throw Error('PDF 처리 방식·언어·배치를 확인하세요.');
  const profile=[PROFILE,mode,language,layout,options.dpi||300].join(':'),prior=options.previous;
  const cached=prior?.file_id===file_id&&prior.profile===profile&&!options.force?prior:null;
  const started=Date.now(),stats={elapsed_ms:0,parse_ms:0,ocr_ms:0,render_ms:0,worker_ms:0,cached_pages:0,ocr_attempts:0,rendered_pixels:0};
  let task,timer,rejectStop,stopped=false,worker,creating,activeCanvas;
  const stop=new Promise((_,reject)=>{rejectStop=reject;});
  const destroy=()=>{if(task)task.destroy().catch(()=>{});if(worker)worker.terminate().catch(()=>{});if(activeCanvas)activeCanvas.width=activeCanvas.height=0;};
  const cancel=()=>{stopped=true;rejectStop(Error('PDF 읽기를 취소했습니다.'));destroy();};
  const getWorker=async()=>{if(!creating){const start=Date.now();creating=O.create(language,{layout,logger:m=>{if(!stopped)options.onProgress?.({phase:'ocr-load',status:m.status});}}).then(w=>{worker=w;stats.worker_ms+=Date.now()-start;if(stopped){w.terminate().catch(()=>{});throw Error('PDF 읽기를 취소했습니다.');}return w;});}return creating;};
  const work=async()=>{
   if(options.signal?.aborted)throw Error('PDF 읽기를 취소했습니다.');
   const p=options.pdfjs||await library();if(stopped)throw Error('PDF 읽기를 취소했습니다.');
   const resources=options.resources||(base?{cMapUrl:new URL('vendor/pdfjs/cmaps/',base).href,standardFontDataUrl:new URL('vendor/pdfjs/standard_fonts/',base).href}:{});
   task=p.getDocument({data:new Uint8Array(buffer),...resources,cMapPacked:true,isEvalSupported:false,useWasm:false,disableFontFace:mode==='text',enableXfa:false,stopAtErrors:true,verbosity:0});
   const doc=await task.promise;const metadata=await doc.getMetadata().catch(()=>({info:{}})),labels=await doc.getPageLabels().catch(()=>null),pages=[];let characters=0,truncated=false;
   for(let number=1;number<=Math.min(doc.numPages,MAX_PAGES);number++){
    if(stopped)throw Error('PDF 읽기를 취소했습니다.');
    const old=cached?.pages[number-1];let text,details={method:'text',reason:'',confidence:null,elapsed_ms:0,dpi:0},page;
    const pageStart=Date.now();
    if(old&&!old.cut&&['text','ocr','blank'].includes(old.method)){text=old.text;details={method:old.method,reason:old.reason||'',confidence:old.confidence??null,elapsed_ms:old.elapsed_ms||0,dpi:old.dpi||0};stats.cached_pages++;}
    else try{
     page=await doc.getPage(number);const parseStart=Date.now();text=pageText((await page.getTextContent()).items);stats.parse_ms+=Date.now()-parseStart;
     if(mode!=='text'){
      if(!O)throw Error('OCR 처리기를 사용할 수 없습니다.');
      const detected=await O.reason(page,text,p),why=detected==='empty'?'':mode==='ocr'?'전체 OCR 선택':detected;
      if(detected==='empty'){details.method='blank';}
      if(why){details.reason=why;
       if(stats.ocr_attempts>=MAX_OCR_PAGES){details.method='pending';details.reason='이번 읽기의 OCR 30쪽 한도 · 다시 읽으면 이어서 처리';}
       else{let raster;try{
        options.onProgress?.({phase:'ocr',page:number,total:doc.numPages,characters});
        const renderStart=Date.now();raster=await O.render(page,options.dpi);activeCanvas=raster.canvas;if(stopped)throw Error('PDF 읽기를 취소했습니다.');stats.render_ms+=Date.now()-renderStart;stats.rendered_pixels+=raster.pixels;details.dpi=raster.dpi;
        if(O.blank(raster.canvas)){details.method='blank';}
        else{stats.ocr_attempts++;const w=await getWorker();if(stopped)throw Error('PDF 읽기를 취소했습니다.');const ocrStart=Date.now();const result=await w.recognize(raster.canvas,{},{text:true});stats.ocr_ms+=Date.now()-ocrStart;
         const recognized=String(result.data.text||'').replace(/\u0000/g,'').trim(),confidence=result.data.confidence;
         if(recognized){text=recognized;details.method='ocr';details.confidence=Number.isFinite(confidence)?Math.max(0,Math.min(100,confidence)):null;}
         else{details.method='error';details.reason='OCR에서 본문을 찾지 못했습니다. 원문 확인 필요';}
        }
       }catch(e){if(stopped)throw e;details.method='error';details.reason='OCR 실패 · 파서 본문 보존 · 다시 읽기 가능';}
       finally{if(raster)raster.canvas.width=raster.canvas.height=0;activeCanvas=null;}}
      }
     }
     details.elapsed_ms=Date.now()-pageStart;
    }finally{page?.cleanup();}
    const remaining=MAX_CHARS-characters,cut=text.length>remaining;
    if(cut){text=text.slice(0,remaining);if(/[\uD800-\uDBFF]$/.test(text))text=text.slice(0,-1);truncated=true;}
    pages.push({number,label:(String(labels?.[number-1]||number).trim().slice(0,80)||String(number)),text,cut,...details});characters+=text.length;
    options.onProgress?.({page:number,total:doc.numPages,characters});
    if(cut||characters>=MAX_CHARS){truncated ||=number<doc.numPages;break;}
   }
   truncated ||=pages.length<doc.numPages;
   stats.elapsed_ms=Date.now()-started;
   return {version:1,file_id,profile,stats,engine:'PDF.js '+VERSION+(mode==='text'?'':' + Tesseract.js 6.0.1'),extracted_at:new Date().toISOString(),page_count:doc.numPages,pages,characters,truncated,title:String(metadata.info?.Title||'').trim().slice(0,160),authors:String(metadata.info?.Author||'').trim().slice(0,200)};
  };
  options.signal?.addEventListener('abort',cancel,{once:true});
  const timeout=mode==='text'?90000:180000;
  timer=setTimeout(()=>{stopped=true;rejectStop(Error('PDF 읽기 시간 한도를 넘었습니다. 원문을 나누어 다시 시도하세요.'));destroy();},timeout);
  try{return await Promise.race([work(),stop]);}
  catch(e){if(e?.name==='PasswordException')throw Error('암호화된 PDF입니다. 이 화면은 문서 암호 입력을 지원하지 않습니다.');if(e?.name==='InvalidPDFException')throw Error('손상되었거나 읽을 수 없는 PDF입니다. 원문을 확인하세요.');throw e;}
  finally{clearTimeout(timer);options.signal?.removeEventListener('abort',cancel);stopped=true;destroy();}
 }
 function method(p){return ({text:'파서',ocr:'OCR',blank:'빈 페이지',pending:'OCR 대기',error:'OCR 확인 필요'})[p.method]||'파서';}
 function status(a){const empty=a.pages.filter(p=>!p.text.trim()).length,ocr=a.pages.filter(p=>p.method==='ocr').length,pending=a.pages.filter(p=>['pending','error'].includes(p.method)).length;return `${a.pages.length}/${a.page_count}쪽 · ${a.characters.toLocaleString()}자${a.truncated?' · 일부만 추출':''}${ocr?' · OCR '+ocr+'쪽':''}${empty?' · 본문 없는 페이지 '+empty+'쪽 (OCR 또는 원문 확인)':''}${pending?' · 다시 읽기 필요 '+pending+'쪽':''}${a.stats?' · '+(a.stats.elapsed_ms/1000).toFixed(1)+'초 · 재사용 '+a.stats.cached_pages+'쪽':''}`;}
 function plain(a,name){return `${name}\n${status(a)}\n${a.engine} · ${a.extracted_at}\nSHA-256 ${a.file_id}\n\n`+a.pages.map(p=>`[PDF ${p.number}쪽 · 문서 표기 ${p.label} · ${method(p)}]${p.cut?' (페이지 일부)':''}\n${p.text||'(텍스트 없음)'}\n`).join('\n');}
 function citation(a,name,page,text){return `[원문: ${name} · PDF ${page.number}쪽 · 표기 ${page.label} · ${method(page)}${page.method==='ocr'?' · 인식문 원문 대조 필요':''} · SHA-256 ${a.file_id}]\n${text.trim()}`;}
 function view(a,name){return `<details class="pdf-extraction"><summary>${E(name)} · ${E(status(a))}</summary><p class="quiet">${E(a.engine)} · ${E(a.extracted_at)} · 원문 배치·표의 읽기 순서는 별도 확인하세요.</p>${a.pages.map(p=>`<details><summary>PDF ${p.number}쪽 · 표기 ${E(p.label)} · ${method(p)}${p.confidence!==null&&p.confidence!==undefined?' · 인식 점수 '+p.confidence.toFixed(0):''}${p.cut?' · 페이지 일부':''}</summary><p class="quiet">${E(p.reason||'')}${p.method==='ocr'?' · 인식 점수는 정확도 확률이 아닙니다. 숫자·표를 원문과 대조하세요.':''}</p><pre>${E(p.text||'텍스트가 없습니다. 스캔·그림은 OCR이 필요합니다.')}</pre></details>`).join('')}</details>`;}
 root.PDFText={extract,pageText,status,plain,citation,view,method,MAX_PAGES,MAX_CHARS,MAX_OCR_PAGES,VERSION};
})(typeof window==='undefined'?globalThis:window);
