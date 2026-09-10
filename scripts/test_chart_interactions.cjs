/* Optional real-browser QA. Start docs on CHART_QA_URL; install Playwright outside
   the public output and set CHART_QA_DIR to a private evidence directory. */
'use strict';
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const url=process.env.CHART_QA_URL||'http://127.0.0.1:8789/';
const out=process.env.CHART_QA_DIR;
if(!out)throw Error('CHART_QA_DIR must point outside the repository.');
const repo=path.resolve(__dirname,'..'),resolved=path.resolve(out);
if(resolved===repo||resolved.startsWith(repo+path.sep))throw Error('Keep browser evidence outside the repository.');
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:process.env.CHART_QA_CHANNEL||'msedge',headless:true});
 const report={viewports:[],interactions:[],errors:[]};
 try{
 for(const width of [1440,1024,390]){
  const page=await browser.newPage({viewport:{width,height:1000},hasTouch:width===390});
  page.on('pageerror',e=>report.errors.push(String(e)));
  // Do not request optional remote map imagery during layout QA.
  await page.route('**/*',route=>new URL(route.request().url()).origin===new URL(url).origin?route.continue():route.abort());
  for(const tab of ['growth','rs','dynamics','geoecon','regime']){
   await page.goto(url+'#'+tab);
   if(tab==='geoecon')await page.locator('[data-subview="시장 지표"]').click();
   if(tab==='regime')await page.locator('[data-subview="Soros 재귀성"]').click();
   const sample=page.locator(tab==='regime'?'[data-holo-canvas]':'.data-chart:visible').first();await sample.waitFor();
   if(tab==='growth'){
    const box=page.locator('[data-projection]').first(),canvas=box.locator('[data-projection-canvas]');
    const before=await canvas.innerHTML();await canvas.focus();await canvas.press('ArrowRight');
    await page.waitForFunction(()=>document.querySelector('[data-yaw]').value==='-55');
    await page.waitForTimeout(40);assert.notEqual(await canvas.innerHTML(),before);
    await canvas.press('+');assert.equal(await box.locator('[data-zoom]').inputValue(),'105');
    await canvas.press('Home');assert.equal(await box.locator('[data-zoom]').inputValue(),'100');
    await box.locator('[data-point-select]').selectOption({index:1});
    assert.equal(await canvas.locator('.point-selected').count(),1);
    assert((await box.locator('output').innerText()).includes('시총'));
    await canvas.scrollIntoViewIfNeeded();const r=await canvas.boundingBox();
    await page.mouse.move(r.x+80,r.y+80);await page.mouse.down();await page.mouse.move(r.x+160,r.y+82,{steps:8});await page.mouse.up();
    assert.notEqual(await box.locator('[data-yaw]').inputValue(),'-65');
    await box.locator('[data-projection-reset]').click();await page.waitForTimeout(40);
    assert.equal(await canvas.locator('.point-selected').count(),0);
    if(width===390){
     await canvas.scrollIntoViewIfNeeded();const t=await canvas.boundingBox(),cdp=await page.context().newCDPSession(page);
     await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:t.x+60,y:t.y+65}]});
     await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:t.x+150,y:t.y+65}]});
     await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
     assert.notEqual(await box.locator('[data-yaw]').inputValue(),'-65');await cdp.detach();
     await box.locator('[data-projection-reset]').click();
     await box.locator('[data-pan="1"]').click();assert((await canvas.evaluate(e=>e.scrollLeft))>0);
     await box.locator('[data-pan="-1"]').click();
    }
    report.interactions.push({width,growth:'keyboard zoom/reset, selection, mouse rotation, '+(width===390?'CDP touch rotation':'desktop')});
   }
   if(tab==='dynamics'){
    const box=page.locator('[data-projection]').first();await box.locator('[data-projection-canvas]').focus();
    await box.locator('[data-projection-canvas]').press('+');assert.equal(await box.locator('[data-zoom]').inputValue(),'105');
    await box.locator('[data-time]').fill('2');await box.locator('[data-time]').dispatchEvent('input');
    await box.locator('[data-projection-reset]').click();
    assert.equal(await box.locator('[data-time]').inputValue(),await box.locator('[data-time]').getAttribute('max'));
    report.interactions.push({width,surface:'zoom, time range, reset'});
   }
   if(tab==='geoecon'){
    const chart=page.locator('.analysis-line-wrap svg').first();
    if(await chart.count()){
     await chart.focus();await chart.press('End');assert.match(await page.locator('.analysis-readout').first().innerText(),/^\d{4}-/);
     const dates=await chart.evaluate(el=>[...new Set(Array.from(el.querySelectorAll('[data-observations]')).flatMap(p=>JSON.parse(p.dataset.observations).map(v=>v[0])))].sort());
     await chart.press('Home');await chart.press('ArrowRight');assert((await page.locator('.analysis-readout').first().innerText()).startsWith(dates[1]));
     // Replace markup exactly as a filter does; no explicit rebinding call.
     await chart.evaluate(el=>{const wrap=el.closest('.analysis-line-wrap');wrap.replaceWith(wrap.cloneNode(true));});
     const replaced=page.locator('.analysis-line-wrap svg').first();await replaced.focus();await replaced.press('End');
     assert((await page.locator('.analysis-readout').first().innerText()).startsWith(dates.at(-1)));
     report.interactions.push({width,line:'precise keyboard step, replacement chart delegation'});
    }
   }
   if(tab==='regime'){
    const box=page.locator('[data-hologram]').first(),canvas=box.locator('[data-holo-canvas]');
    await canvas.focus();await canvas.press('ArrowRight');assert.equal(await box.locator('[data-holo-yaw]').inputValue(),'70');
    await canvas.press('+');assert.equal(await box.locator('[data-holo-zoom]').inputValue(),'105');
    await canvas.press('Home');assert.equal(await box.locator('[data-holo-yaw]').inputValue(),'60');
    report.interactions.push({width,hologram:'keyboard rotation, zoom, reset'});
   }
   await sample.scrollIntoViewIfNeeded();
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
   report.viewports.push({width,tab,overflow});assert.equal(overflow,false,tab+' page overflow at '+width);
   await page.screenshot({path:path.join(out,`after-${tab}-${width}.png`)});
  }
  await page.close();
 }
 assert.deepEqual(report.errors,[]);
 console.log('PASS: real Edge layouts, keyboard, drag, touch, point selection, surface time and reset.');
 }finally{fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify(report,null,2));await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
