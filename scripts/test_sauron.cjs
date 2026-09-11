'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{pathToFileURL}=require('node:url');
module.exports=(async()=>{
 const root=path.resolve(__dirname,'..'),ctx=vm.createContext({window:{},console,URLSearchParams});
 for(const file of ['charts','sauron-views'])vm.runInContext(fs.readFileSync(path.join(root,'docs',file+'.js'),'utf8'),ctx);
 const V=ctx.window.SauronViews,base=pathToFileURL(path.join(root,'docs/vendor/satellite/')).href;
 const S=Object.assign({},...await Promise.all(['io.js','propagation.js','transforms.js'].map(p=>import(base+p))));
 const vectors=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/sauron-orbits.json'),'utf8'));
 let samples=0,maxError=0;
 for(const record of vectors.records)for(const sample of record.samples){
  const p=S.sgp4(S.json2satrec(record.omm),sample.minutes);
  for(const kind of ['position','velocity'])for(const axis of ['x','y','z']){
   const error=Math.abs(p[kind][axis]-sample[kind][axis]);maxError=Math.max(error,maxError);assert(error<1e-6,kind+axis+error);
  }
  // Coordinates are checked independently of the SGP4 elapsed-minute result.
  const at=new Date(sample.at),actual=V.position(record.omm,at,S);
  assert.equal(actual.status,'ok');assert(Math.abs(actual.height_km-sample.height)<.01);
  assert(Math.abs(actual.lon-S.degreesLong(sample.longitude))<.001);assert(Math.abs(actual.lat-S.degreesLat(sample.latitude))<.001);samples++;
 }
 const p=vectors.records[0].omm,epoch=new Date(p.EPOCH+'Z');
 assert.equal(V.position(p,new Date(epoch.getTime()+8*864e5),S).status,'epoch_stale');
 const fake={json2satrec:()=>({}),propagate:()=>({position:{}}),eciToGeodetic:()=>({longitude:0,latitude:0,height:150}),gstime:()=>0,degreesLong:x=>x,degreesLat:x=>x};
 assert.equal(V.position(p,epoch,fake).height_km,150);fake.eciToGeodetic=()=>({longitude:0,latitude:0,height:-1});assert.equal(V.position(p,epoch,fake).status,'invalid_position');
 assert.equal(V.coordinates('37.5,127').lat,37.5);assert.equal(V.coordinates('91,127'),null);
 assert.equal(V.places({query:{pages:{1:{index:1,title:'Seoul',pageid:1,coordinates:[{globe:'earth',lat:37.5,lon:127}]},2:{index:2,coordinates:[{globe:'moon',lat:0,lon:0}]}}}},'en').length,1);
 const requests=[],reply=data=>({ok:true,text:async()=>JSON.stringify(data)}),fetcher=async(url,options)=>{
  requests.push(url);assert(options.headers['Api-User-Agent'].includes('SangsanginDashboard/'));
  return reply(url.startsWith('https://ko.')?{query:{pages:{1:{pageid:1,index:1,title:'서울특별시',langlinks:[{lang:'en','*':'Seoul'}]}}}}:{query:{pages:{2:{pageid:2,title:'Seoul',coordinates:[{globe:'earth',lat:37.5,lon:127}]}}}});
 };
 const korean=await V.wikiSearch('서울','ko',undefined,fetcher);assert.equal(requests.length,2);assert.equal(korean[0].name,'서울특별시');assert.equal(korean[0].lat,37.5);assert(korean[0].url.startsWith('https://en.'));
 await assert.rejects(()=>V.wikiSearch('fail','en',undefined,async()=>({ok:false})),/공급자/);
 const section=JSON.parse(fs.readFileSync(path.join(root,'docs/data/globe.json'),'utf8')).sections.find(s=>s.type==='sauron'),html=V.render(section,0);
 assert.equal((html.match(/data-sau-layer=/g)||[]).length,3);assert.equal((html.match(/data-sau-style=/g)||[]).length,6);assert.equal((html.match(/data-sau-control=/g)||[]).length,11);
 const escaped=JSON.parse(JSON.stringify(section));escaped.sites[0].name='<img src=x onerror=alert(1)>';assert(!V.render(escaped,0).includes('<img'));
 console.log('PASS: SAURON',samples,'independent orbit vectors, max TEME error',maxError,'km; coordinates, stale/failed positions, UI contract and escaping.');
})();
