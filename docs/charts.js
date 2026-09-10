/* Independent SVG charts. No chart CDN, tracking or remote price request. */
(function(root){
 'use strict';
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const ok=v=>typeof v==='number'&&Number.isFinite(v);
 const fmt=(v,unit='',digits=1)=>ok(v)?`${v>0?'+':''}${v.toFixed(digits)}${unit}`:'—';
 let sequence=0;
 const registry=new Map();
 function empty(reason){return `<div class="chart-empty">${esc(reason||'산출 가능한 데이터가 없습니다.')}</div>`;}
 function line(data,{title='',kind='rs'}={}){
  const pts=(data?.points||[]).filter(p=>ok(p[1])&&Number.isFinite(Date.parse(p[0])));
  if(!pts.length)return empty(data?.reason);
  const id='series-'+(++sequence), W=800,H=390,L=64,R=22,T=20,B=50;
  const minT=Date.parse(data.start||pts[0][0]),maxT=Date.parse(data.end||pts.at(-1)[0]);
  const span=Math.max(86400000,maxT-minT),values=pts.map(p=>p[1]);
  let lo=Math.min(0,...values),hi=Math.max(0,...values),yStep=1;
  if(kind==='rs'){[lo,hi]=data.y_domain||[-3.2,3.2];}
  else {const raw=(hi-lo)/6||1,scale=10**Math.floor(Math.log10(raw));yStep=[1,2,2.5,5,10].map(v=>v*scale).find(v=>v>=raw);lo=Math.floor(lo/yStep)*yStep-yStep*.15;hi=Math.ceil(hi/yStep)*yStep+yStep*.15;}
  if(hi===lo){hi++;lo--;}
  const X=d=>L+(Date.parse(d)-minT)/span*(W-L-R),Y=v=>T+(hi-v)/(hi-lo)*(H-T-B);
  const tick=(v,y)=>`<text x="${L-10}" y="${y+4}" text-anchor="end" class="axis">${v.toFixed(kind==='rs'?0:1)}</text>`;
  let axes='';
  const yTicks=kind==='rs'?Array.from({length:Math.floor(hi)-Math.ceil(lo)+1},(_,i)=>Math.ceil(lo)+i):Array.from({length:Math.floor(hi/yStep)-Math.ceil(lo/yStep)+1},(_,i)=>(Math.ceil(lo/yStep)+i)*yStep);
  for(const v of yTicks){const y=Y(v);axes+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" class="grid-line"/>${tick(v,y)}`;}
  // Calendar year/month ticks preserve the reference's time-axis structure.
  const dates=[];
  if(kind==='rs'){for(let y=new Date(minT).getUTCFullYear();y<=new Date(maxT).getUTCFullYear();y++){const d=`${y}-01-01`;if(Date.parse(d)>=minT&&Date.parse(d)<=maxT)dates.push([d,String(y)]);}}
  else {let d=new Date(minT);d.setUTCDate(1);while(d.getTime()<=maxT){if(d.getTime()>=minT)dates.push([d.toISOString().slice(0,10),`${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,'0')}`]);d.setUTCMonth(d.getUTCMonth()+1);}}
  if(!dates.length)dates.push([pts[0][0],pts[0][0]]);
  for(const [d,label] of dates)axes+=`<text x="${X(d)}" y="${H-B+25}" text-anchor="middle" class="axis">${label}</text>`;
  const guides=(kind==='rs'?[-2,-1,0,1,2]:[0]).map(v=>`<line data-guide="${v}" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="reference-line ${v===0?'zero-line':''}" ${v?'stroke-dasharray="5 5"':''}/>${kind==='rs'&&v?`<text x="${L+8}" y="${Y(v)-5}" class="axis">${fmt(v,'σ',0)}</text>`:''}`).join('');
  const coordinates=pts.map(([d,v])=>`${X(d).toFixed(2)},${Y(v).toFixed(2)}`).join(' ');
  let area='';
  if(kind==='momentum'){
   const areaPath=`M ${X(pts[0][0])},${Y(0)} L ${coordinates.replaceAll(' ',' L ')} L ${X(pts.at(-1)[0])},${Y(0)} Z`;
   area=`<defs><clipPath id="${id}-positive"><rect x="${L}" y="${T}" width="${W-L-R}" height="${Math.max(0,Y(0)-T)}"/></clipPath><clipPath id="${id}-negative"><rect x="${L}" y="${Y(0)}" width="${W-L-R}" height="${H-B-Y(0)}"/></clipPath></defs><path data-area="positive" d="${areaPath}" fill="#c6e9df" clip-path="url(#${id}-positive)"/><path data-area="negative" d="${areaPath}" fill="#e7d8ef" clip-path="url(#${id}-negative)"/>`;
  }else area=`<rect data-band="-2:2" x="${L}" y="${Y(2)}" width="${W-L-R}" height="${Y(-2)-Y(2)}" fill="#f0f5f7"/>`;
  const label=data.y_label||(kind==='rs'?'RS z-score (5Y)':'누적 초과수익률 (%)');
  registry.set(id,{pts,X,Y,L,R,W,H});
  const clip=`<defs><clipPath id="${id}-plot"><rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}"/></clipPath></defs>`;
  return `<div class="line-wrap"><svg data-series="${id}" data-kind="${kind}" data-y-min="${lo}" data-y-max="${hi}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)} · ${esc(label)} · ${pts[0][0]} ~ ${pts.at(-1)[0]} · 마지막 ${fmt(pts.at(-1)[1])}" tabindex="0"><title>${esc(title)}</title>${clip}${area}${axes}${guides}<polyline data-price-series="1" clip-path="url(#${id}-plot)" points="${coordinates}" fill="none" stroke="#246a91" stroke-width="1.8" stroke-linejoin="round"/><text transform="translate(16 ${H/2}) rotate(-90)" text-anchor="middle" class="axis">${esc(label)}</text><line class="crosshair" x1="0" x2="0" y1="${T}" y2="${H-B}" hidden="hidden"/><circle class="crosspoint" clip-path="url(#${id}-plot)" r="4" hidden="hidden"/></svg><output class="chart-tooltip" aria-live="off">${pts.at(-1)[0]} · ${fmt(pts.at(-1)[1],kind==='rs'?'σ':'%')}</output></div>`;
 }
 function bars(items,{unit='',markers=[],title='',digits=1,valueUnit=unit}={}){
  const rows=items.filter(r=>ok(r.value));if(!rows.length)return empty();
  const W=800,L=215,R=85,T=markers.length?34:16,rowH=33,H=T+rows.length*rowH+36;
  const extent=Math.max(1,...rows.map(r=>Math.abs(r.value)),...markers.map(Math.abs))*1.1;
  const labelGutter=70;
  const X=v=>L+labelGutter+(v+extent)/(2*extent)*(W-L-R-labelGutter),zero=X(0);
  const refs=[...new Set([0,...markers])].map(v=>`<line data-bar-guide="${v}" x1="${X(v)}" x2="${X(v)}" y1="${T-6}" y2="${H-28}" class="reference-line" stroke-dasharray="${v?'3 4':'0'}"/>${v?`<text x="${X(v)}" y="${T-13}" text-anchor="middle" class="axis">${fmt(v,'',Math.abs(v)%1?2:0)}</text>`:''}`).join('');
  const body=rows.map((r,i)=>{const y=T+i*rowH,end=X(r.value);return `<g><title>${esc(r.name)}: ${fmt(r.value,unit,2)}</title><text x="${L-10}" y="${y+18}" text-anchor="end" class="bar-name">${esc(r.name)}</text><rect data-bar-value="${r.value}" x="${Math.min(zero,end)}" y="${y+3}" width="${Math.max(.8,Math.abs(end-zero))}" height="23" fill="${r.value>=0?'#288376':'#9a6da2'}"/><text x="${end+(r.value>=0?7:-7)}" y="${y+19}" text-anchor="${r.value>=0?'start':'end'}" class="bar-value">${fmt(r.value,valueUnit,digits)}</text></g>`;}).join('');
  return `<div class="bar-scroll"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)} · ${esc(unit)}"><title>${esc(title)}</title>${refs}${body}<text x="${zero}" y="${H-7}" text-anchor="middle" class="axis">0 ${esc(unit)}</text></svg></div>`;
 }
 function heatmap(rows,cols,title){
  const max=cols.map((_,c)=>Math.max(.5,...rows.map(r=>ok(r.values[c])?Math.abs(r.values[c]):0)));
  let last='';
  return `<div class="table-scroll"><table class="heatmap"><caption>${esc(title)}</caption><thead><tr><th scope="col">구분 / 항목</th>${cols.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>{
   let group='';if(r.group!==last){last=r.group;group=`<tr class="table-group"><th colspan="${cols.length+1}" scope="rowgroup">${esc(r.group)}</th></tr>`;}
   return group+`<tr><th scope="row">${esc(r.name)}</th>${r.values.map((v,c)=>{const t=ok(v)?Math.min(1,Math.abs(v)/max[c]):0;return `<td style="background:${ok(v)?`hsl(${v>=0?163:282} 36% ${96-28*t}%)`:'#f0f2f4'}" title="${esc(cols[c])}: ${fmt(v,'',3)}">${fmt(v)}</td>`;}).join('')}</tr>`;
  }).join('')}</tbody></table></div>`;
 }
 function bind(container){
  container.querySelectorAll('svg[data-series]').forEach(svg=>{
   const r=registry.get(svg.dataset.series);if(!r)return;
   let current=r.pts.length-1;
   const show=index=>{current=Math.max(0,Math.min(r.pts.length-1,index));const [d,v]=r.pts[current],line=svg.querySelector('.crosshair'),dot=svg.querySelector('.crosspoint');line.removeAttribute('hidden');dot.removeAttribute('hidden');line.setAttribute('x1',r.X(d));line.setAttribute('x2',r.X(d));dot.setAttribute('cx',r.X(d));dot.setAttribute('cy',r.Y(v));svg.parentElement.querySelector('output').textContent=`${d} · ${fmt(v,svg.dataset.kind==='rs'?'σ':'%',2)}`;};
   svg.addEventListener('pointermove',e=>{const box=svg.getBoundingClientRect(),x=(e.clientX-box.left)/box.width*r.W;let best=0;for(let i=1;i<r.pts.length;i++)if(Math.abs(r.X(r.pts[i][0])-x)<Math.abs(r.X(r.pts[best][0])-x))best=i;show(best);});
   svg.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();show(current+(e.key==='ArrowLeft'?-1:1));}else if(e.key==='Home'||e.key==='End'){e.preventDefault();show(e.key==='Home'?0:r.pts.length-1);}});
  });
 }
 function reset(){registry.clear();}
 const api={line,bars,heatmap,bind,reset,fmt,esc};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchCharts=api;
})(typeof window==='undefined'?globalThis:window);
