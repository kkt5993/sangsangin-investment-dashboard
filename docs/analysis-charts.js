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
  let body='';
  for(let i=0;i<6;i++){let v=lr[0]+(lr[1]-lr[0])*i/5,y=Y(v);body+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" class="grid-line"/><text x="${L-8}" y="${y+4}" text-anchor="end" class="axis">${n(v)}</text>`;if(vals('right').length)body+=`<text x="${W-R+8}" y="${y+4}" class="axis">${n(rr[0]+(rr[1]-rr[0])*i/5)}</text>`;}
  for(let i=0;i<6;i++){const date=new Date(t0+(t1-t0)*i/5).toISOString().slice(0,10);body+=`<text x="${X(date)}" y="${H-24}" text-anchor="middle" class="axis">${date.slice(0,7)}</text>`;}
  body+=(c.guides||[]).map(v=>`<line data-guide="${v}" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" class="reference-line" stroke-dasharray="5 5"/>`).join('');
  series.forEach((s,i)=>{const color=colors[i%colors.length];body+=`<polyline data-analysis-series="${E(s.name)}" data-axis="${E(s.axis)}" points="${s.points.map(p=>`${X(p[0]).toFixed(2)},${Y(p[1],s.axis).toFixed(2)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="1.9"/><text x="${L+i*190}" y="20" fill="${color}" class="axis">${E(s.name)}</text>`;const last=s.points.at(-1);body+=`<circle cx="${X(last[0])}" cy="${Y(last[1],s.axis)}" r="3" fill="${color}"><title>${E(s.name)} · ${last[0]} · ${n(last[1])}</title></circle>`;});
  body+=`<text x="${L}" y="${H-5}" class="axis">${E(c.left||'')}</text><text x="${W-R}" y="${H-5}" text-anchor="end" class="axis">${E(c.right||'')}</text>`;
  return svg(body,c.title,W,H,'data-chart-type="line"');
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
  return svg(b,c.title,W,H,'data-chart-type="scatter"');
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
 function project3d(x,y,z,yaw,tilt=.48,zoom=1){const rx=x*Math.cos(yaw)-y*Math.sin(yaw),ry=x*Math.sin(yaw)+y*Math.cos(yaw);return [450+rx*480*zoom,300+ry*125*zoom-z*175*zoom,ry];}
 function surface(c,yaw=-.8,count=null){
  const surf=c.values.slice(0,count||c.values.length),nt=surf.length,nw=c.windows.length;if(nt<2)return empty();
  const vals=surf.flat().filter(finite),lo=Math.max(0,Math.min(...vals)),hi=Math.max(lo+.1,...vals),P=(i,t,z)=>project3d(i/(nw-1)-.5,t/(nt-1)-.5,(z-lo)/(hi-lo),yaw);
  let quads=[];for(let t=0;t<nt-1;t++)for(let k=0;k<nw-1;k++){const z=[surf[t][k],surf[t][k+1],surf[t+1][k+1],surf[t+1][k]];if(!z.every(finite))continue;const p=[P(k,t,z[0]),P(k+1,t,z[1]),P(k+1,t+1,z[2]),P(k,t+1,z[3])];quads.push({p,z:z.reduce((a,b)=>a+b)/4,depth:p.reduce((a,b)=>a+b[2],0)});}
  quads.sort((a,b)=>a.depth-b.depth);let b=quads.map(q=>`<polygon points="${q.p.map(p=>p.slice(0,2).join(',')).join(' ')}" fill="hsl(${220-(q.z-lo)/(hi-lo)*185} 48% 55%)" stroke="#ffffff55" stroke-width=".5"><title>연환산 변동성 ${n(q.z)}%</title></polygon>`).join('');
  c.windows.forEach((w,i)=>{let p=P(i,0,lo);b+=`<text x="${p[0]}" y="${p[1]+21}" text-anchor="middle" class="axis">${w}D</text>`;});
  const current=P(nw-1,nt-1,surf[nt-1][nw-1]),floor=P(nw-1,nt-1,lo);b+=`<line x1="${floor[0]}" y1="${floor[1]}" x2="${current[0]}" y2="${current[1]}" stroke="#ba812d" stroke-width="2"/><circle cx="${current[0]}" cy="${current[1]}" r="5" fill="#c08a32"/><text x="${current[0]+10}" y="${current[1]-8}" class="axis">현재</text>`;
  b+=`<text x="30" y="30" class="axis">Z: 변동성 ${n(lo)} ~ ${n(hi)}%</text><text x="30" y="425" class="axis">X: 룩백 기간 · Y: ${c.dates[0]} → ${c.dates[nt-1]}</text>`;
  return svg(b,'기간 × 시간 × 변동성',900,450,'data-chart-type="surface"');
 }
 function scatter3d(c,yaw=-.8,zoom=1){
  const pts=c.points.filter(p=>[p.x,p.y,p.z].every(finite));if(!pts.length)return empty();const ranges=['x','y','z'].map(k=>range(pts.map(p=>p[k]),true));
  const project=p=>project3d((p.x-ranges[0][0])/(ranges[0][1]-ranges[0][0])-.5,(p.y-ranges[1][0])/(ranges[1][1]-ranges[1][0])-.5,(p.z-ranges[2][0])/(ranges[2][1]-ranges[2][0]),yaw,.48,zoom);
  const max=Math.max(1,...pts.map(p=>p.size||0));const group=[...new Set(pts.map(p=>p.country||p.group))];
  let b='';const origin=project3d(-.5,-.5,0,yaw,.48,zoom);[[.5,-.5,0],[-.5,.5,0],[-.5,-.5,1]].forEach((v,i)=>{const end=project3d(...v,yaw,.48,zoom);b+=`<line x1="${origin[0]}" y1="${origin[1]}" x2="${end[0]}" y2="${end[1]}" stroke="#99aabc"/><text x="${end[0]}" y="${end[1]-10}" text-anchor="middle" class="axis">${E([c.x_label,c.y_label,c.z_label][i])}</text>`;});
  pts.map(p=>({p,xy:project(p)})).sort((a,b)=>a.xy[2]-b.xy[2]).forEach(({p,xy})=>{const radius=p.size?4+15*Math.sqrt(p.size/max):4;b+=`<circle data-point="${E(p.name)}" cx="${xy[0]}" cy="${xy[1]}" r="${radius}" fill="${colors[group.indexOf(p.country||p.group)%colors.length]}" opacity=".65" stroke="#fff"><title>${E(p.name)} · x ${n(p.x)} · y ${n(p.y)} · z ${n(p.z)} · 시총 ${n(p.size)}</title></circle>`;});
  b+=`<text x="25" y="450" class="axis">${ranges.map((r,i)=>`${['X','Y','Z'][i]} ${n(r[0])} ~ ${n(r[1])}`).join(' · ')} · 원 크기=시총, 없는 경우 동일 크기</text>`;
  return svg(b,c.title,900,480,'data-chart-type="scatter3d"');
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
 function hologram(c,yaw=.6){
  const rows=c.rows.filter(r=>['cognition','acceleration','fragility'].every(k=>finite(r.z[k])));if(!rows.length)return empty();
  const clamp=v=>Math.max(-3,Math.min(3,v)),P=r=>project3d(clamp(r.z.cognition)/6,clamp(r.z.acceleration)/6,(clamp(r.z.fragility)+3)/6,yaw);
  const corners=[[-.5,-.5,0],[.5,-.5,0],[.5,.5,0],[-.5,.5,0]].map(p=>project3d(...p,yaw));
  let b=`<polygon points="${corners.map(p=>p.slice(0,2).join(',')).join(' ')}" fill="#eef3f7" stroke="#aab8c4"/>`;
  [[0,0,'자기강화 가속','#e9d5d7'],[0,-.5,'건전 추세','#d8e8dd'],[-.5,0,'관성 과열','#efe3cd'],[-.5,-.5,'균형·잠복','#d9e3ee']].forEach(([x,z,label,color])=>{const q=[[x,z,0],[x+.5,z,0],[x+.5,z+.5,0],[x,z+.5,0]].map(p=>project3d(...p,yaw)),at=project3d(x+.25,z+.25,0,yaw);b+=`<polygon data-holo-quadrant="${label}" points="${q.map(p=>p.slice(0,2).join(',')).join(' ')}" fill="${color}" stroke="#c0cbd2"/><text x="${at[0]}" y="${at[1]}" text-anchor="middle" class="axis">${label}</text>`;});
  const origin=project3d(0,0,0,yaw);[[.5,0,0],[0,.5,0],[0,0,1]].forEach((p,i)=>{const end=project3d(...p,yaw);b+=`<line x1="${origin[0]}" y1="${origin[1]}" x2="${end[0]}" y2="${end[1]}" stroke="#718597"/><text x="${end[0]}" y="${end[1]-15}" text-anchor="middle" class="axis">${['X 인지 게인','깊이 Z 초지수성','높이 Y 취약성'][i]}</text>`;});
  b+=`<polyline data-holo-trajectory="1" points="${rows.map(r=>P(r).slice(0,2).join(',')).join(' ')}" fill="none" stroke="#7295a9" stroke-width="1.5"/>`;
  const latest=rows.at(-1),top=P(latest),foot=project3d(clamp(latest.z.cognition)/6,clamp(latest.z.acceleration)/6,0,yaw);b+=`<line x1="${top[0]}" y1="${top[1]}" x2="${foot[0]}" y2="${foot[1]}" stroke="#b28325" stroke-dasharray="4 4"/>`;
  rows.forEach((r,i)=>{const p=P(r),v=r.z.volatility,color=finite(r.z.herding)?`hsl(${210-(clamp(r.z.herding)+3)*30} 58% 46%)`:'#9ea5ab',radius=finite(v)?3+(clamp(v)+3):3;b+=`<circle data-holo-date="${r.date}" cx="${p[0]}" cy="${p[1]}" r="${i===rows.length-1?10:radius}" fill="${i===rows.length-1?'#b28325':color}" opacity="${.3+.7*i/Math.max(1,rows.length-1)}"><title>${r.date} · ${c.axes.map(a=>a.name+' '+n(r.raw[a.key])+' '+a.unit).join(' · ')}</title></circle>`;});
  b+=`<text x="35" y="406" class="axis">좌표=36개월 z · 색=허딩(회색: 자료 부족) · 크기=60일 변동성</text><text x="35" y="430" class="axis">각 축 표시 범위 −3~+3z · 밝기=최근 · 황색=현재</text>`;
  return svg(b,c.title+' · 3D 궤적',900,450,'data-chart-type="hologram"');
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
 root.AnalysisCharts={line,scatter,candles,grouped,surface,scatter3d,forecast,spark,hologram,radar,optionProfile,rebalancing,n,empty};
})(typeof window==='undefined'?globalThis:window);
