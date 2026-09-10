/* Routing, resource bounds, resumption and cancellation without network/OCR cost. */
'use strict';const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict'),{webcrypto}=require('node:crypto');
module.exports=(async()=>{
 const c=vm.createContext({crypto:webcrypto,URL,Blob,setTimeout,clearTimeout,AbortController,console});for(const f of ['pdf-text','pdf-ocr','research-store'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/'+f+'.js'),'utf8'),c);
 const P=c.PDFText,O=c.PDFOCR,S=c.ResearchStore,blob=new Blob(['%PDF-ocr-fixture']);let created=0,terminated=0,recognized=0,rendered=0,cleaned=0;const canvases=[];
 const ops={save:1,restore:2,transform:3,paintImageXObject:4,paintInlineImageXObject:5,paintImageMaskXObject:6};
 function fixture(texts){return {OPS:ops,getDocument(){return {promise:Promise.resolve({numPages:texts.length,getMetadata:async()=>({info:{}}),getPageLabels:async()=>null,getPage:async n=>({getTextContent:async()=>({items:[{str:texts[n-1]}]}),getOperatorList:async()=>({fnArray:[3,4],argsArray:[[100,0,0,100,0,0],[]]}),getViewport:()=>({width:100,height:100}),cleanup(){cleaned++;}})}),destroy:async()=>{}};}};}
 const ocr={...O,render:async()=>{rendered++;const canvas={width:100,height:100};canvases.push(canvas);return {canvas,pixels:10000,dpi:300};},blank:()=>false,create:async()=>{created++;return {recognize:async()=>{recognized++;return {data:{text:'매출 1,234.50 | -5.25%',confidence:89}};},terminate:async()=>{terminated++;}};}};
 const native='정상 본문 '.repeat(100),a=await P.extract(blob,{mode:'auto',pdfjs:fixture([native,'','짧은 표지']),ocr});
 assert.deepEqual(Array.from(a.pages,p=>p.method),['text','ocr','ocr']);assert.equal(created,1);assert.equal(recognized,2);assert.equal(terminated,1);assert.equal(cleaned,3);assert(canvases.every(x=>!x.width&&!x.height));assert.equal(a.pages[0].text,native.trim());
 const saved=S.extraction(a);assert.equal(saved.profile,a.profile);assert.equal(saved.pages[1].confidence,89);assert(P.citation(a,'검증.pdf',a.pages[1],'인식문').includes('원문 대조'));
 const reused=await P.extract(blob,{mode:'auto',pdfjs:fixture([native,'','짧은 표지']),ocr,previous:saved});assert.equal(reused.stats.cached_pages,3);assert.equal(created,1);assert.equal(reused.stats.rendered_pixels,0);
 const changed=await P.extract(blob,{mode:'text',pdfjs:fixture([native,'','짧은 표지']),ocr,previous:saved});assert.equal(changed.stats.cached_pages,0);assert.equal(changed.pages[1].text,'');assert.equal(created,1);
 const many=Array(32).fill(''),first=await P.extract(blob,{mode:'auto',pdfjs:fixture(many),ocr});assert.equal(first.stats.ocr_attempts,30);assert.equal(first.pages.filter(p=>p.method==='pending').length,2);
 const next=await P.extract(blob,{mode:'auto',pdfjs:fixture(many),ocr,previous:S.extraction(first)});assert.equal(next.stats.cached_pages,30);assert.equal(next.stats.ocr_attempts,2);assert(next.pages.every(p=>p.method==='ocr'));
 const badOCR={...ocr,create:async()=>({recognize:async()=>{throw Error('fixture failure');},terminate:async()=>{}})};
 const failed=await P.extract(blob,{mode:'ocr',pdfjs:fixture(['원문 보존']),ocr:badOCR});assert.equal(failed.pages[0].method,'error');assert.equal(failed.pages[0].text,'원문 보존');assert(canvases.every(x=>!x.width&&!x.height));
 const abort=new AbortController();let stopped=0;const stalled={...ocr,create:async()=>({recognize:async()=>{queueMicrotask(()=>abort.abort());return new Promise(()=>{});},terminate:async()=>{stopped++;}})};
 await assert.rejects(P.extract(blob,{mode:'auto',pdfjs:fixture(['']),ocr:stalled,signal:abort.signal}),/취소/);assert(stopped>=1);assert(canvases.every(x=>!x.width&&!x.height),'cancel must release active raster even if recognition never settles');
 assert.equal(O.imageCoverage({fnArray:[1,3,4,2],argsArray:[[],[100,0,0,80,0,0],[],[]]},ops,10000),.8);
 const blankPage={getOperatorList:async()=>({fnArray:[],argsArray:[]})};assert.equal(await O.reason(blankPage,'',{OPS:ops}),'empty');
 assert.equal(await O.reason({},'\uFFFD'.repeat(20),{OPS:ops}),'문자 매핑 불량');
 assert.equal(O.blank({width:1,height:1,getContext:()=>({getImageData:()=>({data:[255,255,255,255]})})}),true);
 assert.equal(O.blank({width:1,height:1,getContext:()=>({getImageData:()=>({data:[0,0,0,255]})})}),false);
 for(const mutate of [a=>a.pages[0].confidence=101,a=>a.stats.elapsed_ms=-1,a=>a.pages[0].method='fabricated']){const bad=JSON.parse(JSON.stringify(saved));mutate(bad);assert.throws(()=>S.extraction(bad),/PDF/);}
 console.log('PASS: PDF/OCR routing, worker reuse, cached pages, 30-page resumption, failed OCR preserves text, cancellation, blank detection and backup validation.');
})().catch(e=>{console.error(e);process.exitCode=1;});
