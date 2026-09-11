/* Independent chart primitives for multi-panel, dual-axis and 3D research views. */
(function(root){
 'use strict';
 const C=root.ResearchCharts,E=C.esc,finite=v=>typeof v==='number'&&Number.isFinite(v);
 const colors=['#227d9c','#cf6c43','#735da7','#368169','#ab7832','#ab5776','#53647d'];
 const n=v=>finite(v)?Math.abs(v)>=1e9?(v/1e9).toFixed(1)+'B':Math.abs(v)>=1e6?(v/1e6).toFixed(1)+'M':Math.abs(v)>=1e3?(v/1e3).toFixed(1)+'k':v.toFixed(Math.abs(v)<5?2:1):'—';
 const empty=()=>'<div class="chart-empty">해당 조건의 관측값이 없습니다.</div>';
 const svg=(body,title,W=900,H=420,attrs='')=>`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${E(title)}" ${attrs}><title>${E(title)}</title>${body}</svg>`;
 function range(values,zero=false){let lo=Math.min(...values),hi=Math.max(...values);if(zero){lo=Math.min(0,lo);hi=Math.max(0,hi);}if(lo===hi){lo-=1;hi+=1;}const pad=(hi-lo)*.07;return [lo-pad,hi+pad];}
 function line(c){
  const series=(c.series||[]).map(s=>({...s,points:s.points.filter(p=>finite(p[1])&&Number.isFinite(Date.parse(p[0])))})).filter(s=>s.points.length);
  if(!series.length)return empty();
  const W=900,H=420,L=72,R=80,T=37,B=51;
  const times=series.flatMap(s=>s.points.map(p=>Date.parse(p[0]))),t0=Math.min(...times),t1=Math.max(...times),X=t=>L+(Date.parse(t)-t0)/Math.max(86400000,t1-t0)*(W-L-R);
  const vals=a=>series.filter(s=>(s.axis||'left')===a).flatMap(s=>s.points.map(p=>p[1]));
  const lr=c.limits||range([...vals('left'),...(c.guides||[])]),rr=vals('right').length?range(vals('right')):lr;
  const Y=(v,a='left')=>{const [lo,hi]=a==='right'?rr:lr;return T+(hi-v)/(hi-lo)*(H-T-B);};
  let body=(Array.isArray(c.bands)?c.bands:[]).filter(b=>finite(b.low)&&finite(b.high)&&b.high>b.low).map(b=>{const top=Math.max(T,Y(b.high)),bottom=Math.min(H-B,Y(b.low));return bottom>top?`<rect data-value-band="${b.low}:${b.high}" x="${L}" y="${top}" width="${W-L-R}" height="${bottom-top}" fill="${E(b.color||'#e4eee8')}"/>`:'';}).join('');
  body+=(c.zones||[]).map(z=>{const a=Math.max(L,X(z.start)),b=Math.min(W-R,X(z.end));return b>a?`<rect data-time-zone="${E(z.kind)}" x="${a}" y="${T}" width="${b-a}" height="${H-T-B}" fill="${z.kind==='high'?'#e1efe8':'#f3e4e9'}"/>`:'';}).join('');
  for(let i=0;i<6;i++){let v=lr[0]+(lr[1]-lr[0])*i/5,y=Y(v);body+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" class="grid-line"/><text x="${L-8}" y="${y+4}" text-anchor="end" class="axis">${n(v)}</text>`;if(vals('right').length)body+=`<text x="${W-R+8}" y="${y+4}" class="axis">${n(rr[0]+(rr[1]-rr[0])*i/5)}</text>`;}
  for(let i=0;i<6;i++){const date=new Date(t0+(t1-t0)*i/5).toISOString().slice(0,10);body+=`<text x="${X(date)}" y="${H-24}" text-anchor="middle" class="axis">${c.date_format==='day'?date.slice(5):date.slice(0,7)}</text>`;}
  body+=(c.guides||[]).map(v=>`<line data-guide="${v}" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="reference-line" stroke-dasharray="5 5"/>`).join('');
  series.forEach((s,i)=>{const color=E(s.color||colors[i%colors.length]);body+=`<polyline data-analysis-series="${E(s.name)}" data-observations="${E(JSON.stringify(s.points))}" data-axis="${E(s.axis)}" points="${s.points.map(p=>`${X(p[0]).toFixed(2)},${Y(p[1],s.axis).toFixed(2)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="${s.width||1.9}" opacity="${s.opacity??1}" ${s.dashed?'stroke-dasharray="6 4"':''}/>`;const dots=c.markers&&i===0?s.points:[s.points.at(-1)];body+=dots.map(p=>`<circle data-line-marker="1" cx="${X(p[0])}" cy="${Y(p[1],s.axis)}" r="3" fill="${color}"><title>${E(s.name)} · ${p[0]} · ${n(p[1])}</title></circle>`).join('');});
  body+=`<text x="${L}" y="${H-5}" class="axis">${E(c.left||'')}</text><text x="${W-R}" y="${H-5}" text-anchor="end" class="axis">${E(c.right||'')}</text>`;
  body+=`<line data-analysis-cursor hidden="hidden" y1="${T}" y2="${H-B}" class="crosshair"/>`;
  const legend=series.map((s,i)=>s.legend===false?'':`<span><i style="border-color:${E(s.color||colors[i%colors.length])};border-top-style:${s.dashed?'dashed':'solid'}"></i>${E(s.name)}${s.axis==='right'?' · 우축':''}</span>`).join('');
  return `<div class="analysis-line-wrap"><div class="analysis-legend" aria-label="계열 범례">${legend}</div><div class="chart-viewport">${svg(body,c.title,W,H,'data-chart-type="line" tabindex="0"')}</div><output class="analysis-readout">포인터 또는 ← → 키로 관측값 확인 · Home/End 처음/마지막</output></div>`;
 }
 function scatter(c){
  const pts=(c.points||[]).filter(p=>finite(p.x)&&finite(p.y));if(!pts.length)return empty();
  const W=900,H=460,L=78,R=28,T=32,B=60,[xl,xh]=range(pts.map(p=>p.x),true),[yl,yh]=range(pts.map(p=>p.y),true);
  const X=v=>L+(v-xl)/(xh-xl)*(W-L-R),Y=v=>T+(yh-v)/(yh-yl)*(H-T-B);
  let b=`<line x1="${X(0)}" x2="${X(0)}" y1="${T}" y2="${H-B}" class="reference-line"/><line x1="${L}" x2="${W-R}" y1="${Y(0)}" y2="${Y(0)}" class="reference-line"/>`;
  for(let i=0;i<5;i++){const x=xl+(xh-xl)*i/4,y=yl+(yh-yl)*i/4;b+=`<text x="${X(x)}" y="${H-B+20}" text-anchor="middle" class="axis">${n(x)}</text><text x="${L-12}" y="${Y(y)+4}" text-anchor="end" class="axis">${n(y)}</text>`;}
  if(c.trajectory)b+=`<polyline points="${pts.map(p=>`${X(p.x)},${Y(p.y)}`).join(' ')}" fill="none" stroke="#a1acb8"/>`;
  pts.forEach((p,i)=>{b+=`<circle data-point="${E(p.name)}" cx="${X(p.x)}" cy="${Y(p.y)}" r="${i===pts.length-1?7:3.5}" fill="${colors[Math.floor(i/6)%colors.length]}" opacity=".8"><title>${E(p.name)} · x ${n(p.x)} · y ${n(p.y)}</title></circle>`;});
  b+=`<text x="${W/2}" y="${H-6}" text-anchor="middle" class="axis">${E(c.x_label)}</text><text transform="translate(18 ${H/2}) rotate(-90)" text-anchor="middle" class="axis">${E(c.y_label)}</text>`;
  return `<div class="chart-viewport">${svg(b,c.title,W,H,'data-chart-type="scatter"')}</div>`;
 }
 function candles(c,weekly=false){
  const rows=weekly?c.weekly:c.candles;if(!rows?.length)return empty();const W=800,H=540,L=68,R=15,T=32,PB=366,VT=411,VB=500;
  const [lo,hi]=range([...rows.flatMap(r=>[r[2],r[3]]),...(!weekly?(c.lines||[]).flatMap(s=>s.points.map(p=>p[1])):[])]),X=i=>L+(i+.5)/rows.length*(W-L-R),Y=v=>T+(hi-v)/(hi-lo)*(PB-T),vol=Math.max(1,...rows.map(r=>r[5])),bw=Math.max(1,(W-L-R)/rows.length*.65);
  let b=`<text x="${L}" y="20" class="axis">${weekly?'주봉 (52주)':'일봉 (120거래일)'} · 배당·분할 조정</text>`;
  for(let i=0;i<5;i++){let v=lo+(hi-lo)*i/4,y=Y(v);b+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" class="grid-line"/><text x="${L-8}" y="${y+4}" text-anchor="end" class="axis">${n(v)}</text>`;}
  rows.forEach((r,i)=>{const color=r[4]>=r[1]?'#278878':'#bf6677',x=X(i),y=Math.min(Y(r[1]),Y(r[4]));b+=`<g><title>${r[0]} · O ${n(r[1])} H ${n(r[2])} L ${n(r[3])} C ${n(r[4])} · V ${n(r[5])}</title><line x1="${x}" x2="${x}" y1="${Y(r[2])}" y2="${Y(r[3])}" stroke="${color}"/><rect x="${x-bw/2}" y="${y}" width="${bw}" height="${Math.max(1,Math.abs(Y(r[1])-Y(r[4])))}" fill="${color}"/><rect data-volume="1" x="${x-bw/2}" y="${VB-r[5]/vol*(VB-VT)}" width="${bw}" height="${r[5]/vol*(VB-VT)}" fill="${color}" opacity=".5"/></g>`;});
  if(!weekly)(c.lines||[]).forEach((s,i)=>{const positions=new Map(rows.map((r,j)=>[r[0],j]));b+=`<polyline points="${s.points.filter(p=>positions.has(p[0])).map(p=>`${X(positions.get(p[0]))},${Y(p[1])}`).join(' ')}" fill="none" stroke="${colors[(i+1)%colors.length]}" stroke-width="1.4"/><text x="${L+i*140}" y="${PB+20}" fill="${colors[i+1]}" class="axis">${E(s.name)}</text>`;});
  if(!weekly&&c.pattern){const positions=new Map(rows.map((r,i)=>[r[0],i])),pts=c.pattern.points.filter(p=>positions.has(p[0]));b+=`<polyline data-pattern="1" points="${pts.map(p=>`${X(positions.get(p[0]))},${Y(p[1])}`).join(' ')}" fill="none" stroke="#b9892f" stroke-width="2.2" stroke-dasharray="5 3"/><line x1="${L}" x2="${W-R}" y1="${Y(c.pattern.neckline)}" y2="${Y(c.pattern.neckline)}" stroke="#b9892f" stroke-dasharray="3 5"><title>저항 ${n(c.pattern.neckline)}</title></line>`;}
  [0,Math.floor(rows.length/2),rows.length-1].forEach(i=>{b+=`<text x="${X(i)}" y="${H-14}" text-anchor="${i===0?'start':i===rows.length-1?'end':'middle'}" class="axis">${rows[i][0]}</text>`;});
  b+=`<text x="${L}" y="${VT-8}" class="axis">거래량 · 최대 ${n(vol)}</text>`;
  return svg(b,c.title+(weekly?' 주봉':' 일봉'),W,H,'data-chart-type="candles"');
 }
 function grouped(c){
  if(!c.rows.length)return empty();const W=1000,L=160,R=70,T=42,rh=65,H=T+c.rows.length*rh+30,vals=c.rows.flatMap(r=>r.values).filter(finite),[lo,hi]=range(vals,true),X=v=>L+(v-lo)/(hi-lo)*(W-L-R);
  let b=c.labels.map((l,i)=>`<text x="${L+i*170}" y="20" fill="${colors[i]}" class="axis">${E(l)}</text>`).join('');
  c.rows.forEach((r,i)=>{const y=T+i*rh;b+=`<text x="${L-12}" y="${y+29}" text-anchor="end" class="bar-name">${E(r.name)}</text>`;r.values.forEach((v,j)=>{if(!finite(v))return;b+=`<rect x="${Math.min(X(0),X(v))}" y="${y+j*18}" width="${Math.abs(X(v)-X(0))}" height="14" fill="${colors[j]}"><title>${E(r.name)} ${E(c.labels[j])}: ${n(v)} ${E(c.unit)}</title></rect>`;});});
  b+=`<line x1="${X(0)}" x2="${X(0)}" y1="${T}" y2="${H-10}" class="reference-line"/><text x="${W-R}" y="${H-5}" text-anchor="end" class="axis">${E(c.unit)}</text>`;
  return svg(b,c.title,W,H,'data-chart-type="groupedbars"');
 }
 function project3d(x,y,z,yaw,tilt=.48,zoom=1){const rx=x*Math.cos(yaw)-y*Math.sin(yaw),ry=x*Math.sin(yaw)+y*Math.cos(yaw);const depth=ry*Math.cos(tilt)+(z-.5)*Math.sin(tilt),perspective=2.8/(2.8-depth);return [450+rx*440*zoom*perspective,230+(ry*210*Math.sin(tilt)-(z-.5)*250*Math.cos(tilt))*zoom*perspective,depth];}
 function spatialFrame(P){
  const face=points=>points.map(v=>P(...v).slice(0,2).join(',')).join(' ');
  let b=`<g class="spatial-frame" aria-hidden="true"><polygon points="${face([[-.5,-.5,0],[.5,-.5,0],[.5,.5,0],[-.5,.5,0]])}" fill="#456a9b" fill-opacity=".18"/><polygon points="${face([[-.5,.5,0],[.5,.5,0],[.5,.5,1],[-.5,.5,1]])}" fill="#5877a8" fill-opacity=".07"/>`;
  for(let i=0;i<=4;i++){const t=i/4;for(const pair of [[[t-.5,-.5,0],[t-.5,.5,0]],[[-.5,t-.5,0],[.5,t-.5,0]],[[-.5,.5,t],[.5,.5,t]],[[-.5,-.5,t],[-.5,.5,t]]]){const [a,z]=pair.map(v=>P(...v));b+=`<line x1="${a[0]}" y1="${a[1]}" x2="${z[0]}" y2="${z[1]}" stroke="#8fa9c0" stroke-opacity=".38" stroke-width=".8"/>`;}}
  for(const x of [-.5,.5])for(const y of [-.5,.5]){const a=P(x,y,0),z=P(x,y,1);b+=`<line x1="${a[0]}" y1="${a[1]}" x2="${z[0]}" y2="${z[1]}" stroke="#8fa9c0" stroke-opacity=".4" stroke-dasharray="3 5"/>`;}
  return b+'</g>';
 }
 function surface(c,yaw=-.65,count=null,zoom=1,tilt=.48){
  const surf=c.values.slice(0,count||c.values.length),nt=surf.length,nw=c.windows.length;if(nt<2)return empty();
  const vals=surf.flat().filter(finite),lo=Math.max(0,Math.min(...vals)),hi=Math.max(lo+.1,...vals),P=(i,t,z)=>project3d(i/(nw-1)-.5,t/(nt-1)-.5,(z-lo)/(hi-lo),yaw,tilt,zoom);
  let quads=[];for(let t=0;t<nt-1;t++)for(let k=0;k<nw-1;k++){const z=[surf[t][k],surf[t][k+1],surf[t+1][k+1],surf[t+1][k]];if(!z.every(finite))continue;const p=[P(k,t,z[0]),P(k+1,t,z[1]),P(k+1,t+1,z[2]),P(k,t+1,z[3])];quads.push({p,t,k,z:z.reduce((a,b)=>a+b)/4,depth:p.reduce((a,b)=>a+b[2],0)});}
  quads.sort((a,b)=>a.depth-b.depth);let b=spatialFrame((x,y,z)=>project3d(x,y,z,yaw,tilt,zoom))+quads.map(q=>`<polygon data-surface-cell="${q.t}:${q.k}" points="${q.p.map(p=>p.slice(0,2).join(',')).join(' ')}" fill="hsl(${222+(q.z-lo)/(hi-lo)*38} 55% ${79-(q.z-lo)/(hi-lo)*29}%)" stroke="#ffffff55" stroke-width=".5"><title>${E(c.dates[q.t])} → ${E(c.dates[q.t+1])} · ${c.windows[q.k]}D~${c.windows[q.k+1]}D · 네 꼭짓점 평균 변동성 ${n(q.z)}%</title></polygon>`).join('');
  c.windows.forEach((w,i)=>{let p=P(i,0,lo);b+=`<text x="${p[0]}" y="${p[1]+21}" text-anchor="middle" class="axis">${w}D</text>`;});
  const current=P(nw-1,nt-1,surf[nt-1][nw-1]),floor=P(nw-1,nt-1,lo);b+=`<line x1="${floor[0]}" y1="${floor[1]}" x2="${current[0]}" y2="${current[1]}" stroke="#ba812d" stroke-width="2"/><circle cx="${current[0]}" cy="${current[1]}" r="5" fill="#c08a32"/><text x="${current[0]+10}" y="${current[1]-8}" class="axis">현재</text>`;
  b+=`<text x="30" y="30" class="axis">Z: 변동성 ${n(lo)} ~ ${n(hi)}%</text><text x="30" y="425" class="axis">X: 룩백 기간 · Y: ${c.dates[0]} → ${c.dates[nt-1]}</text>`;
  return svg(b,'기간 × 시간 × 변동성',900,450,'data-chart-type="surface"');
 }
 function scatter3d(c,yaw=-.65,zoom=1,tilt=.48){
  const pts=c.points.filter(p=>[p.x,p.y,p.z].every(finite));if(!pts.length)return empty();const ranges=['x','y','z'].map(k=>range(pts.map(p=>p[k]),true));
  const project=p=>project3d((p.x-ranges[0][0])/(ranges[0][1]-ranges[0][0])-.5,(p.y-ranges[1][0])/(ranges[1][1]-ranges[1][0])-.5,(p.z-ranges[2][0])/(ranges[2][1]-ranges[2][0]),yaw,tilt,zoom);
  const max=Math.max(1,...pts.map(p=>p.size||0));const group=[...new Set(pts.map(p=>p.country||p.group))];
  const P=(x,y,z)=>project3d(x,y,z,yaw,tilt,zoom),paint=orbPaint(colors,c.title);
  let b=paint.defs+spatialFrame(P);
  for(let j=0;j<5;j++){const t=j/4;for(const pair of [[[t-.5,-.5,0],[t-.5,.5,0]],[[-.5,t-.5,0],[.5,t-.5,0]]]){const [a,z]=pair.map(v=>P(...v));b+=`<line x1="${a[0]}" y1="${a[1]}" x2="${z[0]}" y2="${z[1]}" class="grid-line"/>`;}}
  const origin=P(-.5,-.5,0);[[.5,-.5,0],[-.5,.5,0],[-.5,-.5,1]].forEach((v,i)=>{const end=P(...v);b+=`<line x1="${origin[0]}" y1="${origin[1]}" x2="${end[0]}" y2="${end[1]}" stroke="#71889b"/><text x="${end[0]}" y="${end[1]+(i===1?38:-22)}" text-anchor="middle" class="axis">${E([c.x_label,c.y_label,c.z_label][i])}</text>`;
   for(let j=0;j<3;j++){const t=j/2,q=[-.5,-.5,0];q[i]+=t;const p=P(...q);b+=`<text data-3d-tick="${i}" x="${p[0]+(i===2?-9:j===0?(i===0?28:-28):0)}" y="${p[1]+(i===2?4:j===0&&i===0?32:16)}" text-anchor="${i===2?'end':'middle'}" class="axis">${n(ranges[i][0]+t*(ranges[i][1]-ranges[i][0]))}</text>`;}
  });
  b+=group.map((g,i)=>`<text x="${25+i%5*170}" y="${24+Math.floor(i/5)*20}" style="fill:${colors[i%colors.length]}" class="chart-legend">● ${E(g||'미분류')}</text>`).join('');
  pts.map(p=>({p,xy:project(p)})).sort((a,b)=>a.xy[2]-b.xy[2]).forEach(({p,xy})=>{const radius=p.size?4+15*Math.sqrt(p.size/max):4;b+=`<circle data-point="${E(p.name)}" cx="${xy[0]}" cy="${xy[1]}" r="${radius}" fill="${paint.fills[group.indexOf(p.country||p.group)%colors.length]}" opacity="${Math.max(.55,Math.min(.95,.55+(xy[2]+.71)/1.42*.4))}" stroke="#fff"><title>${E(p.name)} · x ${n(p.x)} · y ${n(p.y)} · z ${n(p.z)} · 시총 ${n(p.size)}</title></circle>`;});
  b+=`<text x="25" y="510" class="axis">${ranges.map((r,i)=>`${['X','Y','Z'][i]} ${n(r[0])} ~ ${n(r[1])}`).join(' · ')} · 원 크기=시총, 없는 경우 동일 크기</text>`;
  return svg(b,c.title,900,535,'data-chart-type="scatter3d"');
 }
 function forecast(c){
  const rows=c.records.filter(r=>finite(r.prediction));if(!rows.length)return empty();const W=1000,H=410,L=60,R=25,T=30,B=42,values=rows.flatMap(r=>[r.prediction,r.actual,...Object.values(r.interval)]).filter(finite),[lo,hi]=range(values,true),X=i=>L+(i+.5)/rows.length*(W-L-R),Y=v=>T+(hi-v)/(hi-lo)*(H-T-B),width=(W-L-R)/rows.length*.65;
  let b='';for(let i=0;i<5;i++){let v=lo+(hi-lo)*i/4;b+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="grid-line"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end" class="axis">${n(v)}%</text>`;}
  for(const [a,z,opacity] of [['0.05','0.95',.10],['0.16','0.84',.2]]){const valid=rows.map((r,i)=>({r,i})).filter(o=>finite(o.r.interval[a])&&finite(o.r.interval[z]));if(valid.length)b+=`<polygon data-interval="${a==='0.05'?'90':'68'}" points="${valid.map(o=>`${X(o.i)},${Y(o.r.interval[a])}`).concat([...valid].reverse().map(o=>`${X(o.i)},${Y(o.r.interval[z])}`)).join(' ')}" fill="#357992" opacity="${opacity}"/>`;}
  rows.forEach((r,i)=>{const x=X(i),hit=Math.sign(r.actual)===Math.sign(r.prediction);if(finite(r.actual))b+=`<rect data-actual="1" x="${x-width/2}" y="${Math.min(Y(0),Y(r.actual))}" width="${width}" height="${Math.abs(Y(r.actual)-Y(0))}" fill="${r.actual>=0?'#73ac92':'#b28398'}" opacity=".55"/>`;b+=`<circle cx="${x}" cy="${Y(r.prediction)}" r="4" fill="${finite(r.actual)?hit?'#2b9b76':'#be5b6d':'#d09326'}"><title>${r.origin} → ${r.target} · 예측 ${n(r.prediction)}% · 실제 ${n(r.actual)}% · P상승 ${n(r.probability)}%</title></circle>`;if(i%6===0||i===rows.length-1)b+=`<text x="${x}" y="${H-17}" text-anchor="middle" class="axis">${r.target.slice(0,7)}</text>`;});
  b+=`<polyline data-prediction="1" points="${rows.map((r,i)=>`${X(i)},${Y(r.prediction)}`).join(' ')}" fill="none" stroke="#287c96" stroke-width="2"/><line x1="${L}" x2="${W-R}" y1="${Y(0)}" y2="${Y(0)}" class="reference-line"/><text x="${L}" y="18" class="axis">실제 수익률 막대 · 예측 선 · 68%/90% 구간 · 점=방향 적중/실패</text>`;
  return svg(b,c.title+' 예측',W,H,'data-chart-type="forecast"');
 }
 function spark(points,title){
  const a=points.filter(p=>finite(p[1]));if(!a.length)return empty();const W=310,H=115,[lo,hi]=range(a.map(p=>p[1])),t0=Date.parse(a[0][0]),t1=Date.parse(a.at(-1)[0]),X=p=>10+(Date.parse(p[0])-t0)/Math.max(1,t1-t0)*290,Y=p=>14+(hi-p[1])/(hi-lo)*72;
  return svg(`<polyline points="${a.map(p=>`${X(p)},${Y(p)}`).join(' ')}" fill="none" stroke="#287c96" stroke-width="2"/><text x="10" y="108" class="axis">${a[0][0].slice(0,7)}</text><text x="300" y="108" text-anchor="end" class="axis">${a.at(-1)[0].slice(0,7)}</text>`,title,W,H,'data-chart-type="spark"');
 }
 function hologram(c,yaw=.6,zoom=1,tilt=.48){
  const keys=['cognition','acceleration','fragility'],rows=c.rows.filter(r=>keys.every(k=>finite(r.z[k])));if(!rows.length)return empty();
  const domains=keys.map(k=>range(rows.map(r=>r.z[k]),true)),norm=(v,i)=>(v-domains[i][0])/(domains[i][1]-domains[i][0])-(i===2?0:.5),project=(x,y,z)=>project3d(x,y,z,yaw,tilt,zoom),P=r=>project(...keys.map((k,i)=>norm(r.z[k],i))),zero=keys.map((k,i)=>norm(0,i)),clamp=v=>Math.max(-3,Math.min(3,v));
  const paint=orbPaint(rows.map((r,i)=>i===rows.length-1?'#e7b362':finite(r.z.herding)?`hsl(${210-(clamp(r.z.herding)+3)*30} 65% 60%)`:'#9ea5ab'),c.title+'-holo');
  let b=paint.defs+spatialFrame(project);
  const quadrants=[[zero[0],zero[1],.5,.5,'자기강화 가속','#d495b6'],[zero[0],-.5,.5,zero[1],'건전 추세','#83c9b6'],[-.5,zero[1],zero[0],.5,'관성 과열','#e7c78c'],[-.5,-.5,zero[0],zero[1],'균형·잠복','#83a9e4']];
  quadrants.forEach(([x,y,ex,ey,label,color])=>{const q=[[x,y,zero[2]],[ex,y,zero[2]],[ex,ey,zero[2]],[x,ey,zero[2]]].map(p=>project(...p)),at=project((x+ex)/2,(y+ey)/2,zero[2]);b+=`<polygon data-holo-quadrant="${label}" points="${q.map(p=>p.slice(0,2).join(',')).join(' ')}" fill="${color}" fill-opacity=".16" stroke="#b8cbe1" stroke-opacity=".3"/><text x="${at[0]}" y="${at[1]}" text-anchor="middle" class="axis">${label}</text>`;});
  keys.forEach((key,i)=>{const base=i===1?[.5,-.5,0]:[-.5,.5,0],end=[...base];end[i]+=1;const start=project(...base),last=project(...end);b+=`<line x1="${start[0]}" y1="${start[1]}" x2="${last[0]}" y2="${last[1]}" stroke="#99b6de"/>`;for(let j=0;j<3;j++){const q=[...base];q[i]+=j/2;const at=project(...q);b+=`<text data-holo-tick="${i}" x="${at[0]+(i===2?-10:0)}" y="${at[1]+(i===2?4:22)}" text-anchor="${i===2?'end':'middle'}" class="axis">${n(domains[i][0]+(domains[i][1]-domains[i][0])*j/2)}</text>`;}const labelPos=i===2?last:project(...base.map((v,j)=>j===i?v+.5:v));b+=`<text x="${labelPos[0]}" y="${labelPos[1]+(i===2?-18:43)}" text-anchor="middle" class="axis">${['X 인지 게인','깊이 Z 초지수성','높이 Y 취약성'][i]}</text>`;});
  let d='',active=false;for(const row of c.rows){if(!keys.every(k=>finite(row.z[k]))){active=false;continue;}const p=P(row);d+=(active?' L ':' M ')+p.slice(0,2).join(',');active=true;}
  b+=`<path data-holo-trajectory="1" d="${d}" fill="none" stroke="#6584a6" stroke-width="1.5"/>`;
  const latest=rows.at(-1),top=P(latest),foot=project(norm(latest.z.cognition,0),norm(latest.z.acceleration,1),zero[2]);b+=`<line x1="${top[0]}" y1="${top[1]}" x2="${foot[0]}" y2="${foot[1]}" stroke="#d6b46e" stroke-dasharray="4 4"/>`;
  rows.map((r,i)=>({r,i,p:P(r)})).sort((a,b)=>a.p[2]-b.p[2]).forEach(({r,i,p})=>{const v=r.z.volatility,radius=finite(v)?3+(clamp(v)+3):3;b+=`<circle data-holo-date="${r.date}" cx="${p[0]}" cy="${p[1]}" r="${i===rows.length-1?10:radius}" fill="${paint.fills[i]}" stroke="${i===rows.length-1?'#f3d291':'#c3d8ee'}" stroke-width=".7" opacity="${.3+.7*i/Math.max(1,rows.length-1)}"><title>${r.date} · ${c.axes.map(a=>E(a.name)+' '+n(r.raw[a.key])+' '+E(a.unit)).join(' · ')}</title></circle>`;});
  b+=`<text x="35" y="486" class="axis">좌표=36개월 z · 색=허딩(회색: 자료 부족) · 크기=60일 변동성</text><text x="35" y="512" class="axis">전체 관측에 축 맞춤 · 0 포함 · 표시 절단 없음 · 밝기=최근 · 황색=현재</text>`;
  return svg(b,c.title+' · 3D 궤적',900,535,'data-chart-type="hologram"');
 }
 function radar(c){
  const W=500,H=450,cx=250,cy=208,rad=140,xy=(i,r)=>[cx+Math.sin(i*Math.PI*2/5)*r,cy-Math.cos(i*Math.PI*2/5)*r],rr=z=>(Math.max(-3,Math.min(3,z))+3)/6*rad;
  let b='';[0,.5,1].forEach((v,j)=>{const pts=c.axes.map((a,i)=>xy(i,rad*v));b+=`<polygon points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="#ccd7df"/><text x="${cx+5}" y="${cy-rad*v}" class="axis">${[-3,0,3][j]}z</text>`;});
  c.axes.forEach((a,i)=>{const p=xy(i,rad+24),end=xy(i,rad);b+=`<line x1="${cx}" y1="${cy}" x2="${end[0]}" y2="${end[1]}" stroke="#c9d3db"/><text x="${p[0]}" y="${p[1]}" text-anchor="middle" class="axis">${E(a.name)}</text>`;});
  const indices=[24,12,6,0].map(n=>Math.max(0,c.rows.length-1-n));indices.forEach((ix,j)=>{const r=c.rows[ix],valid=c.axes.every(a=>finite(r.z[a.key]));if(valid)b+=`<polygon data-radar-date="${r.date}" points="${c.axes.map((a,i)=>xy(i,rr(r.z[a.key])).join(',')).join(' ')}" fill="${colors[j]}" fill-opacity=".06" stroke="${colors[j]}" stroke-width="${j===3?2.5:1.5}"/>`;b+=`<text x="30" y="${373+j*18}" fill="${colors[j]}" class="axis">${r.date}${valid?'':' · 일부 축 미수집으로 오각형 생략'}</text>`;});
  return svg(b,c.title+' · 4시점 5축 레이더',W,H,'data-chart-type="radar"');
 }
 function optionProfile(c){
  const rows=c.profile;if(!rows?.length)return empty();const W=1000,H=c.mode==='oi'?330:410,L=75,R=32,T=57,B=63,xmin=Math.min(...rows.map(r=>r.strike)),xmax=Math.max(...rows.map(r=>r.strike)),X=k=>L+(k-xmin)/Math.max(1,xmax-xmin)*(W-L-R),max=c.mode==='oi'?Math.max(1,...rows.flatMap(r=>[r.call_oi,r.put_oi])):Math.max(.001,...rows.map(r=>finite(r.gex)?Math.abs(r.gex):0)),mid=T+(H-T-B)/2,scale=(H-T-B)*.43/max,Y=v=>mid-v*scale,bw=Math.max(.8,Math.min(12,(W-L-R)/rows.length*.65));
  let b='';if(c.em_low!==null&&c.em_high!==null&&c.mode==='gamma'){const lo=Math.max(xmin,c.em_low),hi=Math.min(xmax,c.em_high);if(hi>lo)b+=`<rect data-expected-band="1" x="${X(lo)}" y="${T}" width="${X(hi)-X(lo)}" height="${H-T-B}" fill="#e5cb84" opacity=".22"/>`;}
  for(const q of [-1,-.5,0,.5,1]){const v=q*max;b+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="grid-line"/><text x="${L-8}" y="${Y(v)+4}" text-anchor="end" class="axis">${n(c.mode==='oi'?Math.abs(v):v)}</text>`;}
  b+=`<line x1="${L}" x2="${W-R}" y1="${mid}" y2="${mid}" class="reference-line"/>`;
  rows.forEach(r=>{const values=c.mode==='oi'?[[r.call_oi,'call','#287c96'],[-r.put_oi,'put','#ba6879']]:[[r.gex,'gamma',r.gex>=0?'#287c96':'#ba6879']];values.forEach(([v,side,color])=>{if(!finite(v))return;b+=`<rect data-option-bar="${side}" x="${X(r.strike)-bw/2}" y="${Math.min(mid,Y(v))}" width="${bw}" height="${Math.abs(Y(v)-mid)}" fill="${color}"><title>행사가 ${r.strike} · ${side} ${n(c.mode==='oi'?Math.abs(v):v)}${c.mode==='oi'?' 계약':' USD bn/1%'}</title></rect>`;});});
  const markers=c.mode==='oi'?[[c.spot,'현물','#ad8628'],[c.call_wall,'콜 OI 최대','#287c96'],[c.put_wall,'풋 OI 최대','#ba6879']]:[[c.spot,'현물','#ad8628'],[c.flip,'감마플립','#7768a9']];
  markers.forEach(([k,label,color],i)=>{if(!finite(k)||k<xmin||k>xmax)return;b+=`<line data-option-marker="${label}" x1="${X(k)}" x2="${X(k)}" y1="${T}" y2="${H-B}" stroke="${color}" stroke-dasharray="4 3"/><text x="${X(k)}" y="${18+i*16}" text-anchor="middle" class="axis">${label} ${n(k)}</text>`;});
  for(let i=0;i<7;i++){const k=xmin+(xmax-xmin)*i/6;b+=`<text x="${X(k)}" y="${H-B+24}" text-anchor="middle" class="axis">${n(k)}</text>`;}
  b+=`<text x="${L}" y="${H-16}" class="axis">행사가 USD → · ${c.mode==='oi'?'콜 위 / 풋 아래 · 계약 수(방향 의미 없음)':'GEX USD bn / 현물 1% · 음영=ATM IV 기반30D 기대폭'}</text>`;
  return svg(b,c.title,W,H,'data-chart-type="optionprofile"');
 }
 function rebalancing(c,shock=5){
  const rows=c.stocks;if(!rows.length)return empty();shock=Math.max(-20,Math.min(20,Number(shock)||0));
  const W=Math.max(900,rows.length*66+125),H=380,L=70,R=68,T=39,B=63;
  const flows=rows.map(r=>r.coefficient*shock/100/1e6),advs=rows.map((r,i)=>r.adv?flows[i]*1e6/r.adv*100:null),maxF=Math.max(1,...flows.map(Math.abs))*1.15,maxP=Math.max(1,...advs.filter(finite).map(Math.abs))*1.22;
  const Y=(v,max)=>shock<0?T+(-v)/max*(H-T-B):H-B-v/max*(H-T-B),X=i=>L+(i+.5)*(W-L-R)/rows.length,y0=Y(0,maxF),bw=Math.min(39,(W-L-R)/rows.length*.55);let b='';
  for(let i=0;i<=4;i++){const f=maxF*i/4*(shock<0?-1:1),p=maxP*i/4*(shock<0?-1:1),y=Y(f,maxF);b+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" class="grid-line"/><text x="${L-8}" y="${y+4}" text-anchor="end" class="axis">${n(f)}</text><text x="${W-R+8}" y="${y+4}" class="axis">${n(p)}%</text>`;}
  rows.forEach((r,i)=>{const x=X(i),y=Y(flows[i],maxF),p=advs[i],py=p===null?0:Y(p,maxP);b+=`<rect data-flow-value="${flows[i]}" x="${x-bw/2}" y="${Math.min(y,y0)}" width="${bw}" height="${Math.abs(y0-y)}" fill="#6fabc1"><title>${E(r.name)} · ${n(flows[i])} USD mn</title></rect><text x="${x}" y="${H-B+24}" text-anchor="middle" class="axis">${E(r.name)}</text>`;if(p!==null)b+=`<path data-adv-value="${p}" d="M ${x} ${py-6} l 6 6 -6 6 -6 -6 Z" fill="#b96d65" stroke="white"><title>${E(r.name)} · ${n(p)}% ADV</title></path>`;});
  b+=`<text x="${L}" y="20" class="axis">■ 일일 리밸런싱 USD mn</text><text x="${W-R}" y="20" text-anchor="end" class="axis">◆ % ADV</text><text x="${W/2}" y="${H-10}" text-anchor="middle" class="axis">기초자산 ${shock}% 가정 · 수집된 ETF 표본 합계</text>`;
  return '<div class="bar-scroll">'+svg(b,c.title,W,H,`data-chart-type="rebalancing" style="min-width:${W}px"`)+'</div>';
 }
 function valuation(c,months=180){
  const rows=c.rows.slice(-months);if(!rows.length)return empty();const W=780,H=655,L=65,R=78,T=35,ih=140,step=211;
  const t0=Date.parse(rows[0].date),t1=Date.parse(rows.at(-1).date),X=d=>L+(Date.parse(d)-t0)/Math.max(1,t1-t0)*(W-L-R);
  const scale=(vals,panel,log=false,zero=false)=>{const [lo,hi]=range(vals.filter(finite).map(v=>log?Math.log(v):v),zero);return {lo,hi,Y:v=>panel*step+T+ih-( (log?Math.log(v):v)-lo)/(hi-lo)*ih};};
  const price=scale(rows.map(r=>r.price),0,true),earn=scale(rows.map(r=>r.earnings),0,true),ratio=scale(rows.map(r=>r.ratio),1),macro=scale(rows.flatMap(r=>[r.inflation,r.rate]),2,false,true);
  const path=(key,Y,include=()=>true)=>{let d='',on=false;rows.forEach((r,i)=>{if(!finite(r[key])||!include(r,i)){on=false;return;}d+=(on?'L':'M')+X(r.date).toFixed(2)+' '+Y(r[key]).toFixed(2)+' ';on=true;});return d;};
  let b='';const axis=(s,panel,side,log=false)=>{let out='';for(let i=0;i<4;i++){const raw=s.lo+(s.hi-s.lo)*i/3,v=log?Math.exp(raw):raw,y=s.Y(v);out+=`<text x="${side==='right'?W-R+8:L-8}" y="${y+4}" text-anchor="${side==='right'?'start':'end'}" class="axis">${n(v)}</text>`;if(side==='left')out+=`<line class="grid-line" x1="${L}" x2="${W-R}" y1="${y}" y2="${y}"/>`;}return `<g data-valuation-axis="${side}" data-scale="${log?'log':'linear'}">${out}</g>`;};
  b+=`<g data-valuation-panel="1">${axis(price,0,'left',true)}${axis(earn,0,'right',true)}`;
  b+=`<path d="${path('price',price.Y)}" fill="none" stroke="#287b9f" stroke-width="2" data-valuation-line="price"/><path d="${path('earnings',earn.Y,r=>!r.carry)}" fill="none" stroke="#328c75" stroke-width="2" data-valuation-line="profit"/>`;
  const lastReal=rows.findLastIndex(r=>!r.carry);b+=`<path d="${path('earnings',earn.Y,(r,i)=>r.carry||i===lastReal)}" fill="none" stroke="#328c75" stroke-width="2" stroke-dasharray="5 4" data-valuation-line="carry"/>`;
  b+=`<text x="${L}" y="17" fill="#287b9f" font-size="13">① ${E(c.name)} 지수 pt · 좌 로그축</text><text x="${W-R}" y="17" text-anchor="end" fill="#328c75" font-size="13">이익 ${E(c.profit_unit)} · 우 로그축</text><text x="${L}" y="195" class="axis">이익 관측기간 말 ${E(c.last_profit_period)} · 점선: 최근 실적 유지</text></g>`;
  const values=rows.map(r=>r.ratio).sort((a,z)=>a-z),q=p=>values[Math.floor((values.length-1)*p)],top=step+T,bottom=top+ih;
  b+=`<g data-valuation-panel="2"><rect data-valuation-zone="upper" x="${L}" y="${top}" width="${W-L-R}" height="${ratio.Y(q(.75))-top}" fill="#f5e8e7"/><rect data-valuation-zone="lower" x="${L}" y="${ratio.Y(q(.25))}" width="${W-L-R}" height="${bottom-ratio.Y(q(.25))}" fill="#e4f1eb"/>${axis(ratio,1,'left')}`;
  for(const p of [.25,.5,.75])b+=`<line data-valuation-quantile="${p}" x1="${L}" x2="${W-R}" y1="${ratio.Y(q(p))}" y2="${ratio.Y(q(p))}" stroke="#8198a5" stroke-dasharray="4 4"/>`;
  const latest=rows.at(-1),rank=values.filter(v=>v<=latest.ratio).length/values.length*100;
  b+=`<path d="${path('ratio',ratio.Y)}" fill="none" stroke="#b78c34" stroke-width="2"/><circle cx="${X(latest.date)}" cy="${ratio.Y(latest.ratio)}" r="4" fill="#b78c34"/><text x="${L}" y="${step+17}" class="axis">② 지수/이익 · pt / ${E(c.profit_unit)}</text><text x="${W-R}" y="${step+17}" text-anchor="end" class="axis">현재 ${n(latest.ratio)} · 백분위 ${n(rank)}</text><text x="${L}" y="${step+195}" class="axis">선택기간25/50/75분위 · 지수 P/E와 다른 수치비</text></g>`;
  b+=`<g data-valuation-panel="3">${axis(macro,2,'left')}<path d="${path('inflation',macro.Y)}" fill="none" stroke="#be715e" stroke-width="2" data-valuation-line="inflation"/><path d="${path('rate',macro.Y)}" fill="none" stroke="#758da4" stroke-width="2" data-valuation-line="policy"/><line x1="${L}" x2="${W-R}" y1="${macro.Y(0)}" y2="${macro.Y(0)}" class="reference-line"/><text x="${L}" y="${step*2+17}" fill="#be715e" font-size="13">③ CPI YoY %</text><text x="${W-R}" y="${step*2+17}" text-anchor="end" fill="#758da4" font-size="13">${c.region==='KR'?'한국은행 기준금리':'월평균 Fed funds'} %</text>`;
  for(let i=0;i<5;i++){const row=rows[Math.round((rows.length-1)*i/4)];b+=`<text x="${X(row.date)}" y="${H-28}" text-anchor="middle" class="axis">${row.date.slice(0,7)}</text>`;}
  b+=`</g><text x="${L}" y="${H-5}" class="axis">${E(c.profit_name)} · ${rows[0].date} ~ ${latest.date}</text>`;
  return svg(b,c.name+' 3단 비교',W,H,'data-chart-type="valuation"');
 }
 function scanCandles(c){
  const rows=c.candles;if(!rows?.length)return empty();
  const W=660,H=290,L=12,R=75,T=29,B=28,values=rows.flatMap(r=>r.slice(1)).concat(c.lines.flatMap(a=>a.values||a.points.map(p=>p[1])).filter(finite)),[lo,hi]=range(values);
  const X=i=>L+(i+.5)/rows.length*(W-L-R),Y=v=>T+(hi-v)/(hi-lo)*(H-T-B),width=Math.max(1,(W-L-R)/rows.length*.6);
  let b='';for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;b+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="grid-line"/><text data-price-axis="right" x="${W-R+8}" y="${Y(v)+4}" class="axis">${n(v)}</text>`;}
  rows.forEach((r,i)=>{const color=r[4]>=r[1]?'#237965':'#b75b69',x=X(i);b+=`<g data-scan-candle="${E(r[0])}"><title>${E(r[0])} · O ${n(r[1])} H ${n(r[2])} L ${n(r[3])} C ${n(r[4])}</title><line x1="${x}" x2="${x}" y1="${Y(r[2])}" y2="${Y(r[3])}" stroke="${color}"/><rect x="${x-width/2}" y="${Math.min(Y(r[1]),Y(r[4]))}" width="${width}" height="${Math.max(1,Math.abs(Y(r[1])-Y(r[4])))}" fill="${color}"/></g>`;});
  for(const [i,line] of c.lines.entries()){const coords=(line.values?line.values.map((v,j)=>[j,v]):line.points.map(p=>[rows.findIndex(r=>r[0]===p[0]),p[1]])).filter(p=>p[0]>=0&&finite(p[1]));b+=`<polyline data-scan-ma="${E(line.name)}" points="${coords.map(([j,v])=>X(j)+','+Y(v)).join(' ')}" stroke="${colors[i]}" fill="none" stroke-dasharray="4 3"/><text x="${L+i*120}" y="17" fill="${colors[i]}" class="axis">${E(line.name)}</text>`;}
  for(let i=0;i<5;i++){const j=Math.round(i*(rows.length-1)/4);b+=`<text x="${X(j)}" y="${H-6}" text-anchor="${i===0?'start':i===4?'end':'middle'}" class="axis">${E(rows[j][0].slice(5))}</text>`;}
  return svg(b,c.name+' · 90봉 OHLC·MA20/60',W,H,'data-chart-type="scan-candles"');
 }
 function modelLeaderboard(c){return c.panels.map(p=>{const W=520,H=445,L=45,R=15,T=32,B=115,values=p.rows.flatMap(r=>r.values).filter(finite),lo=Math.min(35,...values)-1,hi=Math.max(75,...values)+1,Y=v=>T+(hi-v)/(hi-lo)*(H-T-B),step=(W-L-R)/p.rows.length,bw=step*.35;let b=`<text x="${L}" y="18" class="axis">${E(p.name)} · OOS 방향 적중 %</text>`;for(let j=0;j<5;j++){const v=lo+(hi-lo)*j/4;b+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="grid-line"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end" class="axis">${n(v)}</text>`;}p.rows.forEach((r,i)=>{const x=L+(i+.5)*step;r.values.forEach((v,j)=>{if(finite(v))b+=`<rect data-model-bar="${j===0?1:3}M" x="${x+(j-1)*bw}" y="${Y(v)}" width="${bw}" height="${Y(lo)-Y(v)}" fill="${j?'#b89137':'#328aaa'}"><title>${E(r.name)} ${j+1===1?'1M':'3M'} ${n(v)}%</title></rect>`;});b+=`<text transform="translate(${x+3} ${H-B+14}) rotate(-48)" text-anchor="end" font-size="10" class="axis">${E(r.name)}</text>`;});b+=`<line data-model-chance="50" x1="${L}" x2="${W-R}" y1="${Y(50)}" y2="${Y(50)}" stroke="#ad566b" stroke-dasharray="5 4"/><text x="${W-100}" y="18" fill="#328aaa">1M</text><text x="${W-58}" y="18" fill="#b89137">3M</text>`;return svg(b,p.name+' · 1M/3M 모형 적중률',W,H,'data-chart-type="model-leaderboard"');}).join('');}
 function lagCorrelation(c){const W=900,H=300,L=62,R=20,T=24,B=46,[lo,hi]=range([0,...c.rows.map(r=>r.value).filter(finite)]),Y=v=>T+(hi-v)/(hi-lo)*(H-T-B),step=(W-L-R)/c.rows.length;let b='';for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;b+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="grid-line"/><text x="${L-8}" y="${Y(v)+4}" text-anchor="end" class="axis">${n(v)}</text>`;}c.rows.forEach((r,i)=>{const x=L+(i+.5)*step;if(finite(r.value))b+=`<rect data-lag="${E(r.name)}" x="${x-step*.36}" y="${Math.min(Y(0),Y(r.value))}" width="${step*.72}" height="${Math.abs(Y(r.value)-Y(0))}" fill="${+r.name>=0?'#3b947d':'#8b9cad'}"><title>L=${E(r.name)} · r=${n(r.value)} · n=${r.observations}</title></rect>`;b+=`<text x="${x}" y="${H-23}" text-anchor="middle" class="axis">${E(r.name)}</text>`;});b+=`<text x="${W/2}" y="${H-4}" text-anchor="middle" class="axis">L개월 · 양수는 ML이 수익률보다 선행</text>`;return svg(b,c.title,W,H,'data-chart-type="lag-correlation"');}
 function shap(c){if(!c.rows.length)return empty();const gradient='shap-'+Array.from(c.title).reduce((h,ch)=>(Math.imul(h,31)+ch.codePointAt(0))>>>0,0);const W=980,L=225,R=95,T=36,B=48,rh=40,H=T+c.rows.length*rh+B,values=c.rows.flatMap(r=>r.points.map(p=>p[0])),[lo,hi]=range([0,...values]),X=v=>L+(v-lo)/(hi-lo)*(W-L-R),color=v=>`rgb(${Math.round(45+170*v)},${Math.round(118-66*v)},${Math.round(207-78*v)})`;let b=`<defs><linearGradient id="${gradient}" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="${color(0)}"/><stop offset="100%" stop-color="${color(1)}"/></linearGradient></defs><line x1="${X(0)}" x2="${X(0)}" y1="${T-14}" y2="${H-B}" stroke="#8e9faa"/>`;c.rows.forEach((r,i)=>{const y=T+(i+.5)*rh,bins=new Map();b+=`<text x="${L-12}" y="${y+4}" text-anchor="end" class="axis">${E(r.name)}</text><line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" class="grid-line" stroke-dasharray="2 4"/>`;r.points.forEach(([v,z],j)=>{const x=X(v),bin=Math.round(x/5),count=bins.get(bin)||0;bins.set(bin,count+1);const jitter=count===0?0:Math.min(rh*.35,Math.ceil(count/2)*2.7)*(count%2?1:-1);b+=`<circle data-shap-value="${v}" cx="${x}" cy="${y+jitter}" r="2.8" fill="${color(z)}" opacity=".72"><title>${E(r.name)} · ${E(c.dates[j])} · 기여 ${n(v)}%p</title></circle>`;});});for(let j=0;j<5;j++){const v=lo+(hi-lo)*j/4;b+=`<text x="${X(v)}" y="${H-B+22}" text-anchor="middle" class="axis">${n(v)}</text>`;}b+=`<rect x="${W-R+22}" y="${T}" width="11" height="${H-T-B}" fill="url(#${gradient})"/><text x="${W-R+38}" y="${T+8}" class="axis">높음</text><text x="${W-R+38}" y="${H-B}" class="axis">낮음</text><text x="${L+(W-L-R)/2}" y="${H-5}" text-anchor="middle" class="axis">SHAP 기여 · 다음1개월 수익률 %p</text>`;return svg(b,c.title,W,H,'data-chart-type="shap-beeswarm"');}
 function featureSelection(c){const W=620,L=235,R=32,T=30,B=40,rh=24,H=T+c.rows.length*rh+B,X=v=>L+v/c.repeats*(W-L-R);let b='';for(let v=0;v<=c.repeats;v+=2)b+=`<line x1="${X(v)}" x2="${X(v)}" y1="${T-10}" y2="${H-B}" class="grid-line"/><text x="${X(v)}" y="${H-B+20}" text-anchor="middle" class="axis">${v}</text>`;c.rows.forEach((r,i)=>{const y=T+i*rh;b+=`<text x="${L-10}" y="${y+rh*.65}" text-anchor="end" class="axis">${E(r.name)}</text><rect data-shadow-wins="${r.value}" x="${X(0)}" y="${y+3}" width="${X(r.value)-X(0)}" height="${rh-6}" fill="${r.forced?'#bc9848':'#388dad'}"><title>${E(r.name)} · ${r.value}/${c.repeats}회${r.forced?' · 강제 포함':''}</title></rect>`;});b+=`<text x="${L}" y="${H-3}" class="axis">shadow 최대 중요도 초과 횟수 / ${c.repeats}회</text>`;return svg(b,c.title,W,H,'data-chart-type="feature-selection"');}
 function moeFan(c){
  const rows=c.history;if(!rows?.length)return empty();const W=1100,H=440,L=75,R=105,T=40,B=48,F=150;
  const values=rows.map(r=>r[1]).filter(finite).concat(Object.values(c.bands).flat()).concat(finite(c.forecast)?[c.forecast]:[]),[lo,hi]=range(values),Y=v=>T+(hi-v)/(hi-lo)*(H-T-B),X=i=>L+i/Math.max(1,rows.length-1)*(W-L-R-F),xf=W-R,last=rows.at(-1),lx=X(rows.length-1);let b='';
  for(let j=0;j<4;j++){const v=lo+(hi-lo)*j/3;b+=`<line x1="${L}" x2="${xf}" y1="${Y(v)}" y2="${Y(v)}" class="grid-line"/><text x="${L-5}" y="${Y(v)+4}" text-anchor="end" class="axis">${n(v)}</text>`;}
  for(const [key,label,opacity] of [['1.96','95',.13],['1','68',.27]]){const band=c.bands[key];if(band&&finite(last[1]))b+=`<polygon data-moe-band="${label}" points="${lx},${Y(last[1])} ${xf},${Y(band[1])} ${xf},${Y(band[0])}" fill="#6f86ef" opacity="${opacity}"/>`;}
  let path='',active=false;rows.forEach(([t,v],i)=>{if(!finite(v)){active=false;return;}path+=(active?' L ':' M ')+X(i)+','+Y(v);active=true;if(t.slice(5,7)==='01'||i===0)b+=`<text x="${X(i)}" y="${H-12}" text-anchor="middle" class="axis">${E(t.slice(0,7))}</text>`;});
  b+=`<path data-moe-history="1" d="${path}" stroke="#398bea" stroke-width="2.7" fill="none"/>`;
  if(finite(c.forecast)&&finite(last[1])){b+=`<line data-moe-projection="1" x1="${lx}" x2="${xf}" y1="${Y(last[1])}" y2="${Y(c.forecast)}" stroke="#b38732" stroke-width="2" stroke-dasharray="4 3"/><circle data-moe-forecast="1" cx="${xf}" cy="${Y(c.forecast)}" r="4" fill="#b38732"><title>${E(c.target)} · ${n(c.forecast)} ${E(c.unit)}</title></circle><text x="${xf+8}" y="${Math.min(H-B-12,Math.max(T+12,Y(c.forecast)+4))}" class="axis">${n(c.forecast)}</text>`;}
  b+=`<text x="${xf}" y="${H-12}" text-anchor="middle" class="axis">1M</text><text x="${L}" y="15" class="axis">${E(c.unit)} · 월별 관측 / 68·95% 팬</text>`;return svg(b,c.name+' · 실제3년과1M 예측',W,H,'data-chart-type="moe-fan"');
 }
 function moeTopology(cards){
  const W=1100,H=620,ix=95,ex=415,gx=760,ox=985,names=cards[0]?.experts.map(r=>r.name)||[];if(!names.length)return empty();
  const weight=name=>cards.reduce((sum,c)=>sum+(c.experts.find(r=>r.name===name)?.weight||0),0)/cards.length;
  let b='';
  for(const [x,label] of [[ix,'입력'],[ex,'10개 전문가'],[gx,'가중 결합'],[ox,'예측']])b+=`<text x="${x}" y="34" text-anchor="middle" font-size="15" font-weight="500" fill="#6e6e73">${label}</text>`;
  names.forEach((name,i)=>{const y=78+i*49,w=weight(name);for(const iy of [210,410])b+=`<path d="M ${ix+67} ${iy} C 245 ${iy},235 ${y},${ex-110} ${y}" fill="none" stroke="#d5dce4" stroke-width="1"/>`;b+=`<path data-moe-edge="${E(name)}" d="M ${ex+110} ${y} C 640 ${y},630 310,${gx-58} 310" fill="none" stroke="#668cb9" stroke-width="${.6+w/8}" opacity=".65"><title>${E(name)} · 평균 가중치 ${n(w)}%</title></path>`;});
  cards.forEach((c,i)=>{const y=cards.length===1?310:170+i*280/(cards.length-1);b+=`<path d="M ${gx+58} 310 C 870 310,875 ${y},${ox-67} ${y}" stroke="#729e98" stroke-width="1.6" fill="none"/><g data-moe-output="${E(c.symbol)}"><rect x="${ox-67}" y="${y-27}" width="134" height="54" rx="10" fill="#f0f6f4" stroke="#cadbd6"/><text x="${ox}" y="${y+5}" text-anchor="middle" font-size="16" fill="#315c54">${E(c.name)}</text></g>`;});
  b+=`<rect x="${gx-58}" y="272" width="116" height="76" rx="12" fill="#eff3fa" stroke="#b9cce4"/><text x="${gx}" y="307" text-anchor="middle" font-size="17" fill="#2d547f">GATE</text><text x="${gx}" y="329" text-anchor="middle" font-size="12" fill="#6e6e73">가중 결합</text>`;
  names.forEach((name,i)=>{const y=78+i*49,w=weight(name);b+=`<g><rect data-moe-expert="${E(name)}" x="${ex-110}" y="${y-19}" width="220" height="38" rx="8" fill="white" stroke="#d9dfe7"/><rect x="${ex-109}" y="${y-7}" width="3" height="14" rx="1.5" fill="#7195c1"/><text x="${ex-94}" y="${y+5}" font-size="14" fill="#3d4652">${E(name)}</text><text x="${ex+94}" y="${y+5}" text-anchor="end" font-size="14" fill="#365e8c">${n(w)}%</text></g>`;});
  for(const [y,label] of [[210,'경제·거시 R'],[410,'기술·시장 I']])b+=`<rect x="${ix-67}" y="${y-27}" width="134" height="54" rx="10" fill="#f5f6f8" stroke="#d9dfe7"/><text x="${ix}" y="${y+5}" text-anchor="middle" font-size="16" fill="#414c5a">${label}</text>`;
  b+=`<text x="28" y="599" font-size="13" fill="#6e6e73">선 두께=평균 가중치 · 완료된 캐시 기준 · 여러 대상이면 평균</text>`;
  return svg(b,'입력→10전문가→게이트→예측',W,H,'data-chart-type="moe-topology"');
 }
 function stateTimeline(s){
  if(!s.rows.length)return empty();const W=1100,H=545,L=22,R=190,T=48,step=143,bar=103,bw=(W-L-R)/s.rows.length,palette=[['#69ad99','#78b5ce','#d298a8','#929acc'],['#69ad99','#e3c16d','#d49b72','#929acc'],['#69ad99','#e3c16d','#cf8e99']];let body='';
  s.panels.forEach((p,i)=>{const y=T+i*step;body+=`<text data-timeline-panel="${i}" x="${L}" y="${y-12}" class="axis">${E(p.name)}</text>`;
   s.rows.forEach((r,j)=>{const v=r[i+1],label=v===null?'미산출':p.labels[v];body+=`<rect data-timeline-cell="${i}-${j}" x="${L+j*bw}" y="${y}" width="${bw}" height="${bar}" fill="${v===null?'#e0e5e9':palette[i][v]}" stroke="white" stroke-width=".7"><title>${E(r[0])} · ${E(label)}</title></rect>`;});
   let start=0;for(let j=1;j<=s.rows.length;j++){if(j<s.rows.length&&s.rows[j][i+1]===s.rows[start][i+1])continue;const value=s.rows[start][i+1],label=value===null?'미산출':p.labels[value],width=(j-start)*bw;if(width>label.length*10+14)body+=`<text x="${L+(start+j)*bw/2}" y="${y+bar/2+4}" text-anchor="middle" fill="#1d3c4b" font-size="12">${E(label)}</text>`;start=j;}
   p.labels.forEach((label,j)=>{body+=`<rect x="${W-R+15}" y="${y+7+j*23}" width="13" height="13" fill="${palette[i][j]}"/><text x="${W-R+35}" y="${y+18+j*23}" class="axis">${E(label)}</text>`;});
  });
  s.rows.forEach((r,i)=>{if(i%3===0||i===s.rows.length-1){const x=L+(i+.5)*bw,y=T+2*step+bar+16;body+=`<text x="${x}" y="${y}" transform="rotate(-40 ${x} ${y})" text-anchor="end" class="axis">${E(r[0].slice(2,7))}</text>`;}});
  body+=`<text x="${L}" y="${H-12}" class="axis">회색: 필수 입력 미산출 · 각 칸은 완료된 한 달</text>`;return svg(body,s.title,W,H,'data-chart-type="state-timeline"');
 }
 // Shared camera input for existing spatial renderers; no data transformation.
 function bindCamera(canvas,options){
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),wrap=v=>((v+Math.PI)%(2*Math.PI)+2*Math.PI)%(2*Math.PI)-Math.PI;
  let pending=null,disposed=false,moved=false,panX=0,panY=0,pinch=null,center=null,observer=null,tip=null,inertia=null,velocity=[0,0];const contacts=new Map();
  const applyPan=()=>{const el=canvas.querySelector?.('svg');if(!el)return;const base=el.getAttribute('data-camera-box')||el.getAttribute('viewBox');if(!base)return;el.setAttribute('data-camera-box',base);const a=base.split(/\s+/).map(Number);el.setAttribute('viewBox',`${a[0]-panX} ${a[1]-panY} ${a[2]} ${a[3]}`);};
  const pan=(dx,dy)=>{const el=canvas.querySelector?.('svg'),box=el?.getAttribute('data-camera-box')?.split(/\s+/).map(Number),scale=box?box[2]/Math.max(1,el.getBoundingClientRect().width):1;panX+=dx*scale;panY+=dy*scale;applyPan();};
  const draw=()=>{pending=null;if(!disposed&&canvas.isConnected!==false){options.draw();applyPan();}};
  const schedule=()=>{if(pending===null)pending=root.requestAnimationFrame?root.requestAnimationFrame(draw):(draw(),null);};
  const update=patch=>{const next={...options.read(),...patch};next.yaw=wrap(next.yaw);next.pitch=clamp(next.pitch,options.minPitch??-.9,options.maxPitch??1.15);next.zoom=clamp(next.zoom,options.minZoom??.5,options.maxZoom??2.5);options.write(next);schedule();};
  const stopMotion=()=>{if(inertia!==null)root.cancelAnimationFrame?.(inertia);inertia=null;velocity=[0,0];};
  const coast=()=>{inertia=null;if(disposed||canvas.isConnected===false)return;velocity=velocity.map(v=>v*.88);if(Math.hypot(...velocity)<.0006)return;const state=options.read();update({yaw:state.yaw+velocity[0],pitch:state.pitch+velocity[1]});inertia=root.requestAnimationFrame(coast);};
  const reset=()=>{stopMotion();if(pending!==null)root.cancelAnimationFrame?.(pending);pending=null;contacts.clear();pinch=null;center=null;options.start?.();panX=panY=0;options.reset();applyPan();canvas.scrollLeft=0;if(tip)tip.hidden=true;};
  const gesture=()=>{const [a,b]=contacts.values();return a&&b?{distance:Math.hypot(a.x-b.x,a.y-b.y),x:(a.x+b.x)/2,y:(a.y+b.y)/2}:null;};
  canvas.setAttribute('tabindex','0');canvas.setAttribute('role','group');canvas.setAttribute('aria-label',options.label||'3D 차트. 드래그 회전과 기울기, 클릭 후 휠 확대, Shift 드래그 이동. 방향키와 +/−, Home도 사용 가능합니다.');if(canvas.style){canvas.style.touchAction='none';canvas.style.cursor='grab';}
  canvas.addEventListener('pointerdown',e=>{if(e.button!==undefined&&![0,1,2].includes(e.button))return;stopMotion();canvas.focus?.({preventScroll:true});options.start?.();if(tip)tip.hidden=true;canvas.classList?.add('scene-engaged');contacts.set(e.pointerId??0,{x:e.clientX,y:e.clientY||0,startX:e.clientX,startY:e.clientY||0,pan:e.shiftKey||e.button===1||e.button===2});moved=false;const g=gesture();pinch=g?.distance;center=g;});
  canvas.addEventListener('pointermove',e=>{const id=e.pointerId??0,previous=contacts.get(id);if(!previous){if(tip){const target=e.target.closest?.('[data-state-date],[data-worm-symbol],[data-point],[data-node],[data-country],[data-holo-date],[data-surface-cell]'),text=target?.querySelector('title')?.textContent;if(text){tip.textContent=text;tip.hidden=false;const r=canvas.parentNode.getBoundingClientRect();tip.style.left=Math.max(12,Math.min(e.clientX-r.left+16,r.width-Math.min(300,r.width-24)-12))+'px';tip.style.top=Math.max(12,e.clientY-r.top-70)+'px';}else tip.hidden=true;}return;}
   const x=e.clientX,y=e.clientY||0;contacts.set(id,{...previous,x,y});const g=gesture(),state=options.read();
   if(g&&pinch){moved=true;canvas.setPointerCapture?.(id);if(center)pan(g.x-center.x,g.y-center.y);update({zoom:state.zoom*g.distance/pinch});pinch=g.distance;center=g;return;}
   if(Math.hypot(x-previous.startX,y-previous.startY)<4&&!moved)return;moved=true;canvas.setPointerCapture?.(id);canvas.classList?.add('scene-dragging');if(previous.pan){pan(x-previous.x,y-previous.y);return;}velocity=[(x-previous.x)*.004,(y-previous.y)*.003];update({yaw:state.yaw+(x-previous.x)*.008,pitch:state.pitch+(y-previous.y)*.006});
  });
  const end=e=>{contacts.delete(e.pointerId??0);const g=gesture();pinch=g?.distance;center=g;if(!contacts.size){canvas.classList?.remove('scene-dragging');if(e.type==='pointerup'&&moved&&root.requestAnimationFrame&&!root.matchMedia?.('(prefers-reduced-motion: reduce)').matches&&Math.hypot(...velocity)>.0006)inertia=root.requestAnimationFrame(coast);}};
  for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,end);
  canvas.addEventListener('pointerleave',()=>{if(tip)tip.hidden=true;});
  canvas.addEventListener('blur',()=>{stopMotion();canvas.classList?.remove('scene-engaged');if(tip)tip.hidden=true;});
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('click',e=>{if(moved){e.preventDefault();e.stopImmediatePropagation();}},{capture:true});
  canvas.addEventListener('dblclick',reset);
  canvas.addEventListener('wheel',e=>{if(options.wheelRequiresCtrl!==false&&!e.ctrlKey&&canvas.ownerDocument?.activeElement!==canvas)return;e.preventDefault();stopMotion();options.start?.();if(tip)tip.hidden=true;update({zoom:options.read().zoom*Math.exp(-e.deltaY*.0015)});},{passive:false});
  canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','Home','Escape'].includes(e.key))return;if(e.target!==canvas&&e.key!=='Home')return;e.preventDefault();stopMotion();options.start?.();const v=options.read();if(e.key==='Escape'){canvas.blur?.();return;}if(e.key==='Home')reset();else if(['+','=','-'].includes(e.key))update({zoom:v.zoom+(e.key==='-'?-.05:.05)});else if(e.shiftKey)pan(e.key==='ArrowLeft'?-20:e.key==='ArrowRight'?20:0,e.key==='ArrowUp'?-20:e.key==='ArrowDown'?20:0);else update({yaw:v.yaw+(e.key==='ArrowLeft'?-.1:e.key==='ArrowRight'?.1:0),pitch:v.pitch+(e.key==='ArrowDown'?-.08:e.key==='ArrowUp'?.08:0)});});
  if(canvas.ownerDocument){
   const doc=canvas.ownerDocument,wrapper=doc.createElement('div'),dock=doc.createElement('div');wrapper.className='scene-view scene-direct';canvas.classList.add('scene-fit');dock.className='scene-dock';dock.innerHTML='<span class="scene-input-hint">드래그 회전 · 클릭 후 휠 확대 · 두 손가락 확대/이동</span><button type="button" data-camera-reset aria-label="카메라 위치 복원" title="시점 복원 · 더블클릭 또는 Home">↺</button><button type="button" data-scene-full aria-label="차트 전체 화면" title="전체 화면">⛶</button>';
   canvas.parentNode.insertBefore(wrapper,canvas);wrapper.append(canvas,dock);dock.querySelector('[data-camera-reset]').addEventListener('click',reset);
   tip=doc.createElement('div');tip.setAttribute('role','tooltip');tip.className='scene-object-tip';tip.hidden=true;wrapper.append(tip);
   observer=new MutationObserver(applyPan);observer.observe(canvas,{childList:true,subtree:true});applyPan();
   const full=dock.querySelector('[data-scene-full]');full.addEventListener('click',async()=>{try{if(doc.fullscreenElement===wrapper)await doc.exitFullscreen();else await wrapper.requestFullscreen();}catch{full.title='전체 화면 사용 불가';}});
   wrapper.addEventListener('keydown',e=>{if(e.key==='Escape'&&doc.fullscreenElement===wrapper){e.preventDefault();doc.exitFullscreen().catch(()=>{});}});
   wrapper.addEventListener('fullscreenchange',()=>{full.setAttribute('aria-label',doc.fullscreenElement===wrapper?'전체 화면 닫기':'차트 전체 화면');});
  }
  return {reset,update,dispose(){disposed=true;stopMotion();observer?.disconnect();if(pending!==null)root.cancelAnimationFrame?.(pending);contacts.clear();}};
 }
 // Compatibility API: matte color preserves category/value encodings without spherical lighting.
 function orbPaint(palette,key){return {fills:palette.map(E),defs:''};}
 function bindLines(container){container.querySelectorAll('.analysis-line-wrap').forEach(wrap=>{
  const chart=wrap.querySelector('svg'),output=wrap.querySelector('output');let cache=null,index=0;
  const read=()=>{if(cache)return cache;const series=Array.from(chart.querySelectorAll('[data-observations]')).map(el=>({name:el.dataset.analysisSeries,axis:el.dataset.axis,points:new Map(JSON.parse(el.dataset.observations))})),dates=[...new Set(series.flatMap(s=>Array.from(s.points.keys())))].sort();return cache={series,dates,times:dates.map(Date.parse)};};
  const show=i=>{const {series,dates}=read();index=Math.max(0,Math.min(dates.length-1,i));const date=dates[index],{times}=read(),x=72+(times[index]-times[0])/Math.max(86400000,times.at(-1)-times[0])*748,cursor=chart.querySelector('[data-analysis-cursor]');cursor.removeAttribute('hidden');cursor.setAttribute('x1',x);cursor.setAttribute('x2',x);output.textContent=date+' · '+series.map(s=>s.name+(s.axis==='right'?' (우축)':'')+': '+(s.points.has(date)?String(s.points.get(date)):'관측 없음')).join(' · ');};
  chart.addEventListener('pointermove',e=>{const {times}=read(),box=chart.getBoundingClientRect(),ratio=Math.max(0,Math.min(1,((e.clientX-box.left)/box.width*900-72)/748)),t=times[0]+ratio*(times.at(-1)-times[0]);let lo=0,hi=times.length-1;while(lo<hi){const mid=(lo+hi)>>1;if(times[mid]<t)lo=mid+1;else hi=mid;}show(lo>0&&Math.abs(times[lo-1]-t)<Math.abs(times[lo]-t)?lo-1:lo);});
  chart.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();show(e.key==='Home'?0:e.key==='End'?Infinity:index+(e.key==='ArrowLeft'?-1:1));}});
 });}
 root.AnalysisCharts={bindCamera,orbPaint,bindLines,line,scatter,candles,grouped,surface,scatter3d,forecast,spark,hologram,radar,optionProfile,rebalancing,valuation,scanCandles,modelLeaderboard,lagCorrelation,shap,featureSelection,moeFan,moeTopology,stateTimeline,n,empty};
})(typeof window==='undefined'?globalThis:window);
