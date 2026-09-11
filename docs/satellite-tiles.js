/* NASA GIBS viewport tiles. No prefetch, persistent storage, credentials or proxy. */
(function(root){
 'use strict';
 const MAX_LAT=85.0511287798066,MAX_NATIVE=8;
 const BASE='https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/';
 const wrap=lon=>((lon+180)%360+360)%360-180;
 function plan(c,width,height){
  if(![c.lon,c.lat,c.zoom,width,height].every(Number.isFinite)||width<=0||height<=0)return [];
  const zoom=Math.max(1,Math.min(19,Math.floor(c.zoom))),z=Math.min(zoom,MAX_NATIVE),n=2**z,size=256*2**(zoom-z);
  const lat=Math.max(-MAX_LAT,Math.min(MAX_LAT,c.lat))*Math.PI/180;
  const cx=(wrap(c.lon)+180)/360*n*size,cy=(1-Math.asinh(Math.tan(lat))/Math.PI)/2*n*size;
  const left=cx-width/2,top=cy-height/2,out=[];
  for(let y=Math.max(0,Math.floor(top/size));y<=Math.min(n-1,Math.ceil((top+height)/size)-1);y++){
   for(let x=Math.floor(left/size);x<=Math.ceil((left+width)/size)-1;x++){
    const col=((x%n)+n)%n,key=`${z}/${y}/${col}`;
    out.push({key,url:BASE+key+'.jpeg',z,x:col,y,left:x*size-left,top:y*size-top,size});
    if(out.length>100)return [];
   }
  }
  return out;
 }
 function create(options={}){
  const get=options.fetch||root.fetch.bind(root),urls=options.urls||root.URL,notify=options.onChange||(()=>{});
  const cache=new Map(),active=new Map(),failed=new Set();let wanted=new Map(),disposed=false,paused=false,halted=false;
  const trim=()=>{for(const [key,item]of cache){if(cache.size<=48)break;if(wanted.has(key))continue;urls.revokeObjectURL(item.href);cache.delete(key);}};
  function status(){return {total:wanted.size,loaded:[...wanted.keys()].filter(k=>cache.has(k)).length,failed:[...wanted.keys()].filter(k=>failed.has(k)).length,active:active.size,cached:cache.size,halted};}
  function pump(){
   if(disposed||paused||halted)return;
   for(const [key,tile]of wanted){
    if(active.size>=3)break;
    if(cache.has(key)||active.has(key)||failed.has(key))continue;
    const controller=new AbortController();active.set(key,controller);
    const timeout=setTimeout(()=>controller.abort('timeout'),12000);
    (async()=>{
     try{
      const r=await get(tile.url,{signal:controller.signal,credentials:'omit',referrerPolicy:'no-referrer',cache:'default'});
      if([401,403,429,503].includes(r.status))halted=true;
      if(!r.ok||!(r.headers.get('content-type')||'').toLowerCase().startsWith('image/jpeg'))throw Error('Tile unavailable');
      const reader=r.body.getReader(),chunks=[];let count=0;
      try{while(true){const {done,value}=await reader.read();if(done)break;count+=value.byteLength;chunks.push(value);}}catch(e){await reader.cancel();throw e;}finally{reader.releaseLock();}
      if(disposed||controller.signal.aborted||!wanted.has(key))return;
      // JPEG signature; malformed image decoding is handled by the browser.
      const prefix=[];for(const chunk of chunks){for(const v of chunk){prefix.push(v);if(prefix.length===2)break;}if(prefix.length===2)break;}
      if(count<3||prefix[0]!==255||prefix[1]!==216)throw Error('Invalid JPEG');
      const blob=new Blob(chunks,{type:'image/jpeg'});
      cache.set(key,{href:urls.createObjectURL(blob)});trim();
     }catch(e){if(!disposed&&wanted.has(key)&&!paused&&(!controller.signal.aborted||controller.signal.reason==='timeout'))failed.add(key);}
     finally{clearTimeout(timeout);if(active.get(key)===controller)active.delete(key);if(!disposed){notify(status());pump();}}
    })();
   }
  }
  return {
   update(tiles){if(disposed)return;wanted=new Map(tiles.map(t=>[t.key,t]));for(const [key,c]of active)if(!wanted.has(key))c.abort('view');for(const key of failed)if(!wanted.has(key))failed.delete(key);trim();pump();notify(status());},
   lookup(key){const item=cache.get(key);if(item){cache.delete(key);cache.set(key,item);}return item?.href||'';},
   pause(value){paused=value;if(paused)for(const c of active.values())c.abort('pause');else pump();},
   retry(){failed.clear();halted=false;pump();},status,
   dispose(){disposed=true;for(const c of active.values())c.abort('dispose');active.clear();for(const item of cache.values())urls.revokeObjectURL(item.href);cache.clear();wanted.clear();failed.clear();}
  };
 }
 root.SatelliteTiles={plan,create,wrap,MAX_LAT,MAX_NATIVE};
})(typeof window!=='undefined'?window:globalThis);
