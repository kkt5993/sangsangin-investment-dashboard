/* Isolated browser integration/benchmark; runs only when explicitly requested. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..'),DATA=process.env.SANGSANGIN_DATA_DIR||path.resolve(ROOT,'../sangsangin-investment-data'),DIR=path.join(DATA,'runtime/pdf-ocr-fixtures');
function cer(actual,expected){const a=actual.normalize('NFKC').replace(/\s/g,''),b=expected.normalize('NFKC').replace(/\s/g,'');let row=Array.from({length:a.length+1},(_,i)=>i);for(let j=0;j<b.length;j++){const next=[j+1];for(let i=0;i<a.length;i++)next[i+1]=Math.min(next[i]+1,row[i+1]+1,row[i]+(a[i]===b[j]?0:1));row=next;}return b.length?row[a.length]/b.length:(a.length?1:0);}
(async()=>{
 const server=http.createServer((req,res)=>{const name=decodeURIComponent(new URL(req.url,'http://local').pathname);let file;
  if(name==='/')return res.end('<!doctype html><meta charset="utf-8"><script src="/pdf-ocr.js"></script><script src="/pdf-text.js"></script><input id="file" type="file">');
  if(name==='/vendor/ocr/lang/kor.traineddata.gz'&&process.env.PDF_KOREAN_MODEL){res.setHeader('Content-Type','application/gzip');return res.end(fs.readFileSync(process.env.PDF_KOREAN_MODEL));}
  file=path.resolve(ROOT,'docs','.'+name);if(!file.startsWith(path.join(ROOT,'docs')+path.sep)||!fs.existsSync(file)){res.writeHead(404);return res.end();}
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.js':'text/javascript','.mjs':'text/javascript','.gz':'application/gzip','.ttf':'font/ttf'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));
 });await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=(process.env.PDF_TEST_URL||'http://127.0.0.1:'+server.address().port).replace(/\/$/,'');
 let browser;try{
  browser=await chromium.launch({channel:process.env.PDF_TEST_BROWSER||'msedge',headless:true});const context=await browser.newContext(),page=await context.newPage();const requests=[],errors=[];
  await context.route('**/*',route=>{const url=route.request().url();requests.push(url);if(url.startsWith(origin+'/')&&route.request().method()==='GET')return route.continue();errors.push(url);return route.abort();});page.on('pageerror',e=>errors.push(e.message));
  if(!process.env.PDF_TEST_URL){await page.goto(origin);await page.locator('#file').setInputFiles(path.join(DIR,'comparison.pdf'));}const gold=JSON.parse(fs.readFileSync(path.join(DIR,'expected.json'))),runs=[];
  for(const spec of (process.env.PDF_TEST_URL?[]:[{mode:'text'},{mode:'ocr',dpi:216},{mode:'ocr',dpi:300},{mode:'auto',dpi:300},{mode:'auto',dpi:300,reuse:true}])){
   const before=requests.length;
   const result=await page.evaluate(async spec=>{const blob=document.querySelector('#file').files[0];const a=await PDFText.extract(blob,{...spec,previous:spec.reuse?globalThis.previous:undefined,language:'kor+eng'});globalThis.previous=a;return a;},spec);
   const metrics=result.pages.map((p,i)=>({page:i+1,method:p.method,confidence:p.confidence,cer:cer(p.text,gold[i]),numbers:['1,234.50','-123.45','-5.25%','2.50%','2026-09-08'].filter(x=>gold[i].includes(x)).map(x=>({value:x,found:p.text.includes(x)}))}));
   runs.push({spec,stats:result.stats,pages:metrics,asset_requests:requests.length-before});fs.writeFileSync(path.join(DIR,`result-${spec.mode}-${spec.dpi||0}${spec.reuse?'-reuse':''}.json`),JSON.stringify(result));console.log(JSON.stringify(runs.at(-1)));
   if(spec.mode==='text')assert(!requests.slice(before).some(x=>x.includes('/vendor/ocr/')),'parser must not load OCR');
   if(spec.mode==='auto'&&!spec.reuse){assert.deepEqual(result.pages.map(p=>p.method),['text','text','ocr','ocr','ocr','blank']);assert(metrics.every(p=>p.cer<.08),'hybrid text error exceeds fixture limit');}
   if(spec.reuse){assert.equal(result.stats.cached_pages,6);assert.equal(result.stats.ocr_attempts,0);assert.equal(result.stats.rendered_pixels,0);}
  }
  const ui=await context.newPage();ui.on('pageerror',e=>errors.push(e.message));await ui.goto(origin+'/index.html#principium');
  await ui.locator('[data-nb-upload]').setInputFiles(path.join(DIR,'comparison.pdf'));await ui.locator('[data-nb-pdf-extract]').click();
  await ui.waitForFunction(()=>document.querySelector('[data-nb-pdf-status]')?.textContent.includes('OCR 3쪽'),{},{timeout:60000});
  await ui.locator('[data-nb-pdf-page]').selectOption('3');assert((await ui.locator('[data-nb-pdf-quote]').inputValue()).includes('1,234.50'));
  await ui.locator('[data-nb-pdf-evidence]').click();assert((await ui.locator('[data-nb-field="evidence"]').inputValue()).includes('인식문 원문 대조'));
  await ui.locator('[data-nb-field="title"]').fill('OCR 합성 비교 검증');await ui.locator('[data-nb-save]').click();
  await ui.waitForFunction(()=>document.querySelector('[data-nb-list]')?.textContent.includes('OCR 합성 비교 검증'));
  await ui.reload();await ui.locator('[data-nb-filter]').selectOption('mine');await ui.locator('[data-nb-search]').fill('1,234.50');
  const card=ui.locator('[data-note-id]').filter({hasText:'OCR 합성 비교 검증'});await card.locator('summary').first().click();await card.locator('[data-nb-edit]').click();await ui.locator('[data-nb-pdf-extract]').click();
  await ui.waitForFunction(()=>document.querySelector('[data-nb-pdf-status]')?.textContent.includes('재사용 6쪽'));
  await ui.locator('[data-nb-pdf-page]').selectOption('4');await ui.locator('.notebook-pdf').screenshot({path:path.join(DIR,process.env.PDF_TEST_URL?'notebook-ocr-site.png':'notebook-ocr.png')});
  assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync(path.join(DIR,process.env.PDF_TEST_URL?'site-qa.json':process.env.PDF_KOREAN_MODEL?'benchmark-best.json':'benchmark.json'),JSON.stringify({browser:await browser.version(),runs,external_requests:errors.length,ui:'file selection, hybrid OCR, cited page, save, reload, body search and cached reread passed'},null,2));
 }finally{await browser?.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
