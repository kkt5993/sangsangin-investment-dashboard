/* Local formula/surface capture and explicit instrument links. */
(function(root){
 'use strict';const jobs=new Set(),N=v=>root.AnalysisCharts.n(v);
 function selected(sections,location=root.location){
  if(!location?.href)return null;
  try{const url=new URL(location.href);if(url.hash!=='#dynamics')return null;return sections.find(s=>s.type==='dynamics'&&s.symbol===url.searchParams.get('dynamics'))||null;}catch{return null;}
 }
 function link(s,location=root.location){const url=new URL(location.pathname,location.origin);url.searchParams.set('dynamics',s.symbol);url.hash='dynamics';return url.href;}
 function controls(s,i){return `<div class="analysis-controls" data-dynamics-export="${i}"><button type="button" data-dynamics-capture>수식·표면 PNG 저장</button><button type="button" data-dynamics-share>종목 링크 복사</button><output data-dynamics-export-status role="status"></output><label data-dynamics-link-box hidden>선택 종목 링크 <input data-dynamics-link readonly aria-label="선택 종목 공유 링크"></label></div>`;}
 function lines(s,through){return [
  `${s.title} (${s.symbol}) · 시장 역학`,
  `실제 가격 ${s.price_date} · 최신 신호 ${s.date} · 표면 표시 ${s.surface.dates[0]} ~ ${through}`,
  'β = mean(r, 21) / sd(r, 21) × √252 · α = β(t) − β(t−5)',
  '∇τ = sd(|r(t)−r(t−1)|, 21) / mean(|r(t)|, 21)',
  '취약성 = 100 × logistic(z∇τ − 0.5zβ − 0.5zα)',
  '목표 노출 = min(1.5, 15% / 연변동성) × (1 − 0.6 × 취약성/100)',
  '모집단 표준편차 · 과거 확장창 252개 이상 · 당일에는 전일 목표 노출 적용',
  `최신 신호: 취약성 ${N(s.current.risk)}/100 (${s.current.state}) · β ${N(s.current.beta)} · α ${N(s.current.alpha)} · ∇τ ${N(s.current.tau)} · 노출 ${N(s.current.exposure*100)}%`,
  'X: 룩백 기간(거래일) · Y: 실제 월 관측일 · Z: 연환산 변동성(%)',
  '취약성은 확정된 붕괴확률이 아닙니다. 표면 과거 시점과 최신 신호를 구분합니다.'
 ];}
 function wrap(ctx,text,width){const rows=[];let line='';for(const ch of text){if(line&&ctx.measureText(line+ch).width>width){rows.push(line);line=ch;}else line+=ch;}if(line)rows.push(line);return rows;}
 function snapshot(svg){
  const clone=svg.cloneNode(true),a=[svg,...svg.querySelectorAll('*')],b=[clone,...clone.querySelectorAll('*')];
  const props=['fill','fill-opacity','stroke','stroke-width','stroke-opacity','stroke-dasharray','opacity','font-family','font-size','font-weight','text-anchor','dominant-baseline','visibility'];
  a.forEach((el,i)=>{const style=root.getComputedStyle(el);for(const p of props)b[i].style.setProperty(p,style.getPropertyValue(p));});
  clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('width','900');clone.setAttribute('height','450');
  return new XMLSerializer().serializeToString(clone);
 }
 async function capture(s,section){
  const svg=section.querySelector('[data-projection-canvas] svg');if(!svg)throw Error('저장할 표면이 없습니다.');
  const through=s.surface.dates[+section.querySelector('[data-time]').value-1],source=snapshot(svg),job={cancelled:false,cancel:null};jobs.add(job);
  let imageURL=null,pngURL=null,timer=null,img=null,rejectImage=null;
  const stop=()=>{job.cancelled=true;if(rejectImage)rejectImage(Error('cancelled'));};job.cancel=stop;
  try{
   imageURL=URL.createObjectURL(new Blob([source],{type:'image/svg+xml;charset=utf-8'}));img=new Image();
   await new Promise((resolve,reject)=>{rejectImage=reject;img.onload=resolve;img.onerror=()=>reject(Error('표면 이미지를 읽지 못했습니다.'));timer=root.setTimeout(()=>reject(Error('표면 저장 시간이 초과됐습니다.')),10000);img.src=imageURL;});
   root.clearTimeout(timer);timer=null;rejectImage=null;if(job.cancelled)return false;
   const canvas=root.document.createElement('canvas'),ctx=canvas.getContext('2d');if(!ctx)throw Error('이 브라우저에서 PNG 저장을 사용할 수 없습니다.');
   const font='"Pretendard Variable", "Malgun Gothic", sans-serif',text=lines(s,through),layout=[];let y=34;
   text.forEach((value,i)=>{const size=i===0?23:i===1?13:15;ctx.font=`${i===0?'600':'400'} ${size}px ${font}`;for(const row of wrap(ctx,value,836)){layout.push({row,y,size,bold:i===0});y+=i===0?32:23;}if(i===1||i===6)y+=7;});
   const top=y+15,height=top+450+55;canvas.width=1800;canvas.height=height*2;ctx.scale(2,2);ctx.fillStyle='#ffffff';ctx.fillRect(0,0,900,height);
   for(const t of layout){ctx.font=`${t.bold?'600':'400'} ${t.size}px ${font}`;ctx.fillStyle=t.bold?'#29251f':'#625b50';ctx.fillText(t.row,32,t.y);}
   ctx.drawImage(img,0,top,900,450);ctx.font=`12px ${font}`;ctx.fillStyle='#746e63';ctx.fillText('상상인 투자 리서치 · PC 계산 스냅샷 · Yahoo Finance · KRX 가격 검증 · 연환산 252거래일',32,height-24);
   const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(job.cancelled)return false;if(!blob)throw Error('PNG 파일을 만들지 못했습니다.');
   pngURL=URL.createObjectURL(blob);const a=root.document.createElement('a');a.href=pngURL;a.download=`market-dynamics-${s.symbol.replace(/[^a-zA-Z0-9.-]/g,'_')}-${through}.png`;a.click();
   const downloadURL=pngURL;pngURL=null;root.setTimeout(()=>URL.revokeObjectURL(downloadURL),1000);return true;
  }catch(error){if(job.cancelled)return false;throw error;}finally{if(timer!==null)root.clearTimeout(timer);if(img){img.onload=null;img.onerror=null;}if(imageURL)URL.revokeObjectURL(imageURL);if(pngURL)URL.revokeObjectURL(pngURL);jobs.delete(job);}
 }
 function bind(container,d){container.querySelectorAll('[data-dynamics-export]').forEach(box=>{const s=d.sections[+box.dataset.dynamicsExport],status=box.querySelector('[data-dynamics-export-status]'),button=box.querySelector('[data-dynamics-capture]');
  button.addEventListener('click',async()=>{button.disabled=true;status.textContent='수식과 현재 표면을 저장하고 있습니다…';try{const done=await capture(s,box.closest('[data-section]'));if(box.isConnected)status.textContent=done?'PNG를 저장했습니다.':'';}catch{if(box.isConnected)status.textContent='PNG 저장에 실패했습니다. 다시 시도해 주세요.';}finally{if(box.isConnected)button.disabled=false;}});
  box.querySelector('[data-dynamics-share]').addEventListener('click',async()=>{const url=link(s),input=box.querySelector('[data-dynamics-link]');input.value=url;box.querySelector('[data-dynamics-link-box]').hidden=false;
   try{if(!root.navigator?.clipboard?.writeText)throw Error('clipboard unavailable');await root.navigator.clipboard.writeText(url);if(box.isConnected)status.textContent='선택 종목 링크를 복사했습니다. 링크는 열 때의 최신 스냅샷을 표시합니다.';}
   catch{if(box.isConnected){status.textContent='아래 링크를 선택해 복사해 주세요. 열 때의 최신 스냅샷을 표시합니다.';input.focus();input.select();}}
  });
 });}
 function dispose(){for(const job of jobs)job.cancel();}
 root.DynamicsExport={selected,link,controls,lines,wrap,capture,bind,dispose,activeCount:()=>jobs.size};
})(typeof window==='undefined'?globalThis:window);
