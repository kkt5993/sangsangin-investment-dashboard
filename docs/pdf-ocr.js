/* Lazy, same-origin OCR. One LSTM worker per document; no document upload. */
(function(root){
 'use strict';const VERSION='6.0.1',DPI=300,MAX_PIXELS=8000000;
 const base=typeof document==='undefined'||!document.currentScript?.src?null:new URL('.',document.currentScript.src);let library;
 function load(){if(!library)library=new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=new URL('vendor/ocr/tesseract.min.js',base).href;s.onload=()=>resolve(root.Tesseract);s.onerror=()=>{library=null;s.remove();reject(Error('OCR 처리기를 불러오지 못했습니다. 연결을 확인하고 다시 읽으세요.'));};document.head.append(s);});return library;}
 function quality(text){const compact=text.replace(/\s/g,''),bad=(compact.match(/[\uFFFD\u0000-\u0008\uE000-\uF8FF]/g)||[]).length;return {characters:compact.length,readable:(compact.match(/[\p{L}\p{N}]/gu)||[]).length,bad:bad/Math.max(1,compact.length)};}
 function imageCoverage(list,ops,area){let matrix=[1,0,0,1,0,0],stack=[],sum=0;
  for(let i=0;i<list.fnArray.length;i++){const op=list.fnArray[i],v=list.argsArray[i];if(op===ops.save)stack.push([...matrix]);else if(op===ops.restore)matrix=stack.pop()||[1,0,0,1,0,0];else if(op===ops.transform){const a=matrix,b=v;matrix=[a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]];}else if([ops.paintImageXObject,ops.paintInlineImageXObject,ops.paintImageMaskXObject].includes(op))sum+=Math.abs(matrix[0]*matrix[3]-matrix[1]*matrix[2]);}
  return Math.min(1,sum/Math.max(1,area));
 }
 async function reason(page,text,pdfjs){const q=quality(text);if(q.bad>.02)return '문자 매핑 불량';if(q.characters<300){const list=await page.getOperatorList();if(!list.fnArray.length&&!text.trim())return 'empty';const v=page.getViewport({scale:1}),coverage=imageCoverage(list,pdfjs.OPS,v.width*v.height);if(!q.readable)return '본문 없음';if(coverage>.5)return '큰 이미지와 짧은 본문';}return '';}
 async function render(page,dpi=DPI){const v=page.getViewport({scale:1}),scale=Math.min(dpi/72,Math.sqrt(MAX_PIXELS/(v.width*v.height))),viewport=page.getViewport({scale}),canvas=document.createElement('canvas');canvas.width=Math.floor(viewport.width);canvas.height=Math.floor(viewport.height);
  try{await page.render({canvasContext:canvas.getContext('2d',{willReadFrequently:true}),viewport,background:'rgb(255,255,255)'}).promise;return {canvas,dpi:Math.round(scale*72),pixels:canvas.width*canvas.height};}catch(e){canvas.width=canvas.height=0;throw e;}
 }
 function blank(canvas){const context=canvas.getContext('2d');for(let y=0;y<canvas.height;y+=64){const block=context.getImageData(0,y,canvas.width,Math.min(64,canvas.height-y)).data;for(let i=0;i<block.length;i+=4)if(block[i]+block[i+1]+block[i+2]<690)return false;}return true;}
 async function create(language,options={}){const T=await load(),worker=await T.createWorker(language,1,{workerPath:new URL('vendor/ocr/worker.min.js',base).href,corePath:new URL('vendor/ocr/core/',base).href,langPath:new URL('vendor/ocr/lang',base).href,cachePath:'sangsangin-engfast-korbest-4.1.0',workerBlobURL:false,legacyCore:false,legacyLang:false,logger:options.logger,errorHandler:()=>{}});try{await worker.setParameters({tessedit_pageseg_mode:options.layout==='columns'?'3':'6',preserve_interword_spaces:'1'});return worker;}catch(e){await worker.terminate();throw e;}}
 root.PDFOCR={create,reason,quality,imageCoverage,render,blank,VERSION,DPI,MAX_PIXELS};
})(typeof window==='undefined'?globalThis:window);
