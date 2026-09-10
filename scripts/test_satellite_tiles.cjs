/* Offline provider, cancellation, memory and geographic alignment tests. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const ctx=vm.createContext({window:{},AbortController,Blob,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/satellite-tiles.js'),'utf8'),ctx);
const T=ctx.window.SatelliteTiles,tick=()=>new Promise(r=>setImmediate(r));
const jpeg=()=>new Response(new Uint8Array([255,216,255,217]),{headers:{'content-type':'image/jpeg'}});
module.exports=(async()=>{
 const center={lon:0,lat:0,zoom:1};let p=T.plan(center,512,512);
 assert.equal(p.length,4);assert.deepEqual(Array.from(p,t=>t.key),['1/0/0','1/0/1','1/1/0','1/1/1']);
 assert.equal(p[0].left,0);assert.equal(p[0].top,0);assert.equal(p[0].size,256);
 assert.deepEqual(Array.from(T.plan({...center,lon:180},1000,760),t=>t.key),Array.from(T.plan({...center,lon:-180},1000,760),t=>t.key));
 for(const lon of [-179.99,0,179.99])for(const lat of [-90,-45,0,80,90])for(const zoom of [1,8,14,19]){
  p=T.plan({lon,lat,zoom},390,760);assert(p.length>0&&p.length<=100);assert(p.every(t=>t.y>=0&&t.y<2**t.z&&t.x>=0&&t.x<2**t.z&&t.z<=8));
  assert(p.every(t=>t.left<390&&t.left+t.size>0&&t.top<760&&t.top+t.size>0));
 }
 const close=T.plan({...center,zoom:14},1000,560);assert(close.every(t=>t.z===8&&t.size===16384));
 assert.equal(T.plan({...center,lat:NaN},1000,560).length,0);
 const revoked=[],urls={createObjectURL:()=>`blob:test-${Math.random()}`,revokeObjectURL:u=>revoked.push(u)};
 let calls=0;const loader=T.create({urls,fetch:async()=>{calls++;return jpeg();}});
 const tiles=T.plan({...center,zoom:3},1000,760);loader.pause(true);loader.update(tiles);await tick();assert.equal(calls,0);
 loader.pause(false);for(let i=0;i<20;i++)await tick();assert.equal(loader.status().loaded,new Set(tiles.map(t=>t.key)).size);
 const before=calls;loader.update(tiles);await tick();assert.equal(calls,before,'same tiles reused without requests');assert(loader.lookup(tiles[0].key).startsWith('blob:'));
 const cached=loader.status().cached;loader.dispose();assert.equal(revoked.length,cached);assert.equal(loader.status().bytes,0);
 let peak=0,current=0,started=0,aborted=0;
 const slow=T.create({urls,fetch:(url,{signal})=>new Promise((resolve,reject)=>{started++;current++;peak=Math.max(peak,current);signal.addEventListener('abort',()=>{current--;aborted++;reject(new Error('cancel'));},{once:true});})});
 slow.update(tiles);assert.equal(started,3);assert.equal(peak,3);slow.update([]);await tick();assert.equal(aborted,3);assert.equal(slow.status().failed,0);assert.equal(slow.status().active,0);slow.dispose();
 let limited=0;const blocked=T.create({urls,fetch:async()=>{limited++;return new Response('',{status:429});}});
 blocked.update(tiles);for(let i=0;i<5;i++)await tick();assert.equal(limited,3);assert.equal(blocked.status().halted,true);blocked.dispose();
 let badCalls=0;const bad=T.create({urls,fetch:async()=>{badCalls++;return new Response('html',{headers:{'content-type':'text/html'}});}});
 bad.update(tiles.slice(0,1));for(let i=0;i<5;i++)await tick();assert.equal(bad.status().failed,1);bad.update(tiles.slice(0,1));await tick();assert.equal(badCalls,1);bad.retry();await tick();assert.equal(badCalls,2);bad.dispose();
 const big=T.create({urls,fetch:async()=>new Response(new Uint8Array(1024*1024+1),{headers:{'content-type':'image/jpeg'}})});
 big.update(tiles.slice(0,1));for(let i=0;i<5;i++)await tick();assert.equal(big.status().failed,1);assert.equal(big.status().bytes,0);big.dispose();
 const split=T.create({urls,fetch:async()=>new Response(new ReadableStream({start(c){c.enqueue(new Uint8Array([255]));c.enqueue(new Uint8Array([216,255,217]));c.close();}}),{headers:{'content-type':'image/jpeg'}})});
 split.update(tiles.slice(0,1));for(let i=0;i<5;i++)await tick();assert.equal(split.status().loaded,1);split.dispose();
 const bounded=T.create({urls,fetch:async()=>jpeg()});
 for(let i=0;i<60;i++){bounded.update([{...tiles[0],key:'8/0/'+i}]);for(let j=0;j<3;j++)await tick();}
 assert.equal(bounded.status().cached,48);assert(bounded.status().bytes<=8*1024*1024);bounded.dispose();
 console.log('Satellite tiles: Mercator/date-line/polar/overzoom geometry, visible-only requests, reuse, 3-request ceiling, cancellation, retry, rate-limit halt, size and URL cleanup passed.');
})();
