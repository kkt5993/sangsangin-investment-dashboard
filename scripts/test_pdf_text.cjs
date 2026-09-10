/* Run the shipped Mozilla parser on real synthetic Latin/Korean/scanned PDFs. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{pathToFileURL}=require('node:url'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),data=process.env.SANGSANGIN_DATA_DIR||path.resolve(root,'../sangsangin-investment-data'),dir=path.join(data,'runtime/pdf-fixtures');
module.exports=(async()=>{
 execFileSync(process.env.PYTHON_EXECUTABLE||'python',[path.join(__dirname,'make_pdf_fixtures.py')],{encoding:'utf8'});
 const pdfjs=await import(pathToFileURL(path.join(root,'docs/vendor/pdfjs/legacy/build/pdf.min.mjs')).href);
 pdfjs.GlobalWorkerOptions.workerSrc=pathToFileURL(path.join(root,'docs/vendor/pdfjs/legacy/build/pdf.worker.min.mjs')).href;
 require('../docs/pdf-text.js');const P=globalThis.PDFText,options={pdfjs,resources:{cMapUrl:path.join(root,'docs/vendor/pdfjs/cmaps').replaceAll(path.sep,'/')+'/',standardFontDataUrl:path.join(root,'docs/vendor/pdfjs/standard_fonts').replaceAll(path.sep,'/')+'/'}};
 const originalFetch=globalThis.fetch;globalThis.fetch=()=>{throw Error('PDF extraction attempted a network request');};
 try{
  const progress=[],a=await P.extract(new Blob([fs.readFileSync(path.join(dir,'mixed.pdf'))]),{...options,onProgress:p=>progress.push(p)});
  assert.equal(a.page_count,3);assert.equal(a.pages.length,3);assert.equal(a.pages[0].label,'i');assert.equal(a.pages[1].label,'ii');assert.equal(a.truncated,false);
  assert(a.pages[0].text.includes('1,234.50'));assert(a.pages[0].text.includes('-5.25%'));assert(a.pages[1].text.includes('한국 금리 연구'));assert(a.pages[1].text.includes('-123억 원'));assert.equal(a.pages[2].text,'');
  assert.equal(a.title,'한국 금리 연구');assert.equal(a.authors,'상상인 테스트');assert.equal(progress.at(-1).page,3);assert.equal(a.characters,a.pages.reduce((n,p)=>n+p.text.length,0));
  assert(P.status(a).includes('OCR'));assert(P.plain(a,'문서.pdf').includes('PDF 2쪽'));assert(P.citation(a,'문서.pdf',a.pages[1],'발췌').includes(a.file_id));
  assert(!P.view({...a,pages:[{number:1,label:'<script>',text:'<img src=x onerror=alert(1)>',cut:false}]},'<script>').includes('<script>'));
  const long=await P.extract(new Blob([fs.readFileSync(path.join(dir,'long.pdf'))]),options);assert.equal(long.page_count,302);assert.equal(long.pages.length,300);assert(long.truncated);assert(long.pages.at(-1).text.includes('300'));
  for(const [file,pattern] of [['encrypted.pdf',/암호/],['invalid.pdf',/손상|읽을 수/]])await assert.rejects(P.extract(new Blob([fs.readFileSync(path.join(dir,file))]),options),pattern);
  const abort=new AbortController();abort.abort();await assert.rejects(P.extract(new Blob([fs.readFileSync(path.join(dir,'mixed.pdf'))]),{...options,signal:abort.signal}),/취소/);
  let destroyed=0;const mid=new AbortController(),pending=P.extract(new Blob(['%PDF-test']),{signal:mid.signal,pdfjs:{getDocument(){queueMicrotask(()=>mid.abort());return {promise:new Promise(()=>{}),destroy:async()=>{destroyed++;}};}}});await assert.rejects(pending,/취소/);assert(destroyed>=1);
  const capped=await P.extract(new Blob(['%PDF-test']),{pdfjs:{getDocument(){return {promise:Promise.resolve({numPages:1,getMetadata:async()=>({info:{}}),getPageLabels:async()=>null,getPage:async()=>({getTextContent:async()=>({items:[{str:'a'.repeat(200001)}]}),cleanup(){}})}),destroy:async()=>{}};}}});assert.equal(capped.characters,200000);assert(capped.truncated);assert(capped.pages[0].cut);
  fs.writeFileSync(path.join(dir,'extraction.json'),JSON.stringify(a));
  console.log('PASS: shipped PDF.js parser; Latin/Korean, page labels, image-only page, metadata, limits, encrypted/invalid files, cancellation, escaping and zero network.');
 }finally{globalThis.fetch=originalFetch;}
})().catch(e=>{console.error(e);process.exitCode=1;});
