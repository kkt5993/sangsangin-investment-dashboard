/* OEF/KRX new-high screen. All points and ranks are supplied by the local pipeline. */
(function(root){
 'use strict';
 const C=root.ResearchCharts,E=C.esc,F=C.fmt,ok=v=>typeof v==='number'&&Number.isFinite(v);
 const price=(v,market)=>ok(v)?(market==='US'?'$':'₩')+v.toLocaleString('ko-KR',{maximumFractionDigits:market==='US'?2:0}):'—';
 function spark(row){
  const pts=(row.spark||[]).filter(p=>ok(p[1]));if(pts.length<2||!ok(row.high52))return '';
  const W=264,H=88,P=7,lo=Math.min(...pts.map(p=>p[1])),hi=Math.max(row.high52,...pts.map(p=>p[1])),range=hi-lo||1;
  const min=Date.parse(pts[0][0]),span=Math.max(86400000,Date.parse(pts.at(-1)[0])-min);
  const X=d=>P+(Date.parse(d)-min)/span*(W-2*P),Y=v=>H-P-(v-lo)/range*(H-2*P);
  const line=pts.map(([d,v])=>`${X(d).toFixed(2)},${Y(v).toFixed(2)}`).join(' ');
  return `<svg data-high-spark="${E(row.symbol)}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${E(row.name)} · ${E(pts[0][0])}~${E(pts.at(-1)[0])} · 52주 고점 ${E(row.high52)}"><title>${E(row.name)} · 가격 ${E(row.price)} · 52주 고점 ${E(row.high52)}</title><line data-high-guide="${row.high52}" x1="${P}" x2="${W-P}" y1="${Y(row.high52)}" y2="${Y(row.high52)}" stroke="#b17a29" stroke-width="1" stroke-dasharray="4 3"/><polyline data-high-price="1" points="${line}" fill="none" stroke="${pts.at(-1)[1]>=pts[0][1]?'#258273':'#ad5773'}" stroke-width="1.8" stroke-linejoin="round"/>${pts.map(([d,v])=>`<circle cx="${X(d)}" cy="${Y(v)}" r="3.5" fill="transparent"><title>${E(d)} · ${E(v)}</title></circle>`).join('')}<circle cx="${X(pts.at(-1)[0])}" cy="${Y(pts.at(-1)[1])}" r="2.5" fill="#b17a29"/></svg>`;
 }
 function matches(row,state){const q=(state.q||'').toLocaleLowerCase();return (!state.onlyNew||row.new_high)&&[row.symbol,row.name,row.sector].join(' ').toLocaleLowerCase().includes(q);}
 function card(r,market){return `<article class="high-card" data-high-symbol="${E(r.symbol)}"><div class="high-card-head"><h4>${E(r.symbol)}<small>${E(r.name)}</small></h4><span class="high-rs">RS ${F(r.rs,'',0)}</span></div>${spark(r)}<div class="high-card-foot"><span>${r.new_high?'<b>장중 고점 갱신</b>':'고점 대비 '+F(r.from_high,'%')}</span><strong>${price(r.price,market)}</strong></div><small class="high-date">가격 ${E(r.as_of)} · ${E(r.sector)}</small><details><summary>가격·선별 근거</summary><p>52주 고점 ${price(r.high52,market)} · ${E(r.high_date)}<br>관측창 ${E(r.high_window_start)}~${E(r.as_of)}<br>RS ${F(r.rs,'',2)} ≥65 · 고점 대비 ${F(r.from_high,'%',2)} ≥−5%</p><div class="table-scroll high-price-history"><table class="data-table"><caption>미니 차트의 관측 날짜와 가격</caption><thead><tr><th>날짜</th><th>가격</th></tr></thead><tbody>${r.spark.map(([d,p])=>`<tr><td>${E(d)}</td><td>${price(p,market)}</td></tr>`).join('')}</tbody></table></div></details></article>`;}
 function output(data,state){return data.groups.filter(g=>!state.market||state.market==='all'||state.market===g.market).map(g=>{
  const rows=g.rows.filter(r=>matches(r,state));
  const failed=g.collection&&g.collection.status!=='ok';
  return `<section class="high-market" data-high-market="${E(g.market)}"><h3>${E(g.title)} <small>${rows.length}/${g.selected}종목 표시</small></h3><p class="chart-note">공식 ${g.expected}개 · RS 산출 ${g.eligible}개 · 고점 비교 ${g.high_eligible??0}개 · 구성 ${E(g.membership_as_of||'미확보')}${failed?` · 최근 수집 ${E(g.collection.status)} (${g.membership_as_of?'이전 구성 유지':'구성 자료 없음'})`:''}</p>${g.reason?`<p class="chart-empty">${E(g.reason)}</p>`:`<div class="high-grid">${rows.map(r=>card(r,g.market)).join('')}</div>${rows.length?'':'<p class="quiet" role="status">현재 조건에 해당하는 종목이 없습니다.</p>'}`}</section>`;
 }).join('');}
 function universe(g){const url=typeof g.source==='string'&&/^https:\/\//.test(g.source)?g.source:null;return `<details class="method-details"><summary>${E(g.title)} · 전체 비교 대상과 제외 사유</summary><p>구성 기준 ${E(g.membership_as_of||'미확보')} · 수집 ${E(g.membership_retrieved_at||'미확인')}${url?` · <a href="${E(url)}" target="_blank" rel="noopener noreferrer">공식 구성 원문 ↗</a>`:''}</p><div class="table-scroll"><table class="data-table"><thead><tr><th>종목</th><th>공식 섹터</th><th>RS</th><th>고점 대비 %</th><th>가격일 / 상태</th></tr></thead><tbody>${g.members.map(r=>`<tr><th>${E(r.symbol)} · ${E(r.name)}</th><td>${E(r.sector)}</td><td>${F(r.rs,'',2)}</td><td>${F(r.from_high,'%',2)}</td><td>${E(r.reason||r.as_of)}</td></tr>`).join('')}</tbody></table></div>${g.excluded.length?`<ul>${g.excluded.map(r=>`<li>${E(r.symbol)} · ${E(r.name)} · ${E(r.reason)}</li>`).join('')}</ul>`:''}</details>`;}
 function render(data,state={}){
  if(!data)return '<p class="chart-empty">신고가 계산 자료 미확보</p>';
  return `<section class="new-high-screen" data-high-screen><h2>신고가 발굴 · 오닐 RS</h2><p class="scope-note">${E(data.note)}</p><div class="analysis-controls"><label>시장 <select data-high-market-filter>${[['all','한국·미국'],['US','미국 S&P100'],['KR','한국 KOSPI200']].map(([k,v])=>`<option value="${k}" ${(state.market||'all')===k?'selected':''}>${v}</option>`).join('')}</select></label><label>종목·업종 <input data-high-search type="search" value="${E(state.q||'')}" placeholder="종목명·티커·공식 섹터"></label><label><input data-high-new type="checkbox" ${state.onlyNew?'checked':''}> 당일 장중 고점 갱신만</label></div><div data-high-output>${output(data,state)}</div><p class="chart-note">실선: 최근130거래 관측의44개 표본(끝점 포함) · 점선: 최근252관측 장중 고점 · 가격축: 배당·분할 조정 OHLC를 최신 시장종가 척도로 환산. 장중 고점 갱신은 전일까지의252관측 고가를 초과한 경우이며, 종가 돌파와 구분합니다.</p>${data.groups.map(universe).join('')}<a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/NEW_HIGHS_CONTRACT.md">신고가 계산·유니버스·기간 계약 ↗</a></section>`;
 }
 function bind(container,data,state){
  const box=container.querySelector('[data-high-screen]');if(!box)return;
  const update=()=>{box.querySelector('[data-high-output]').innerHTML=output(data,state);};
  box.querySelector('[data-high-market-filter]').addEventListener('change',e=>{state.market=e.target.value;update();});
  box.querySelector('[data-high-search]').addEventListener('input',e=>{state.q=e.target.value;update();});
  box.querySelector('[data-high-new]').addEventListener('change',e=>{state.onlyNew=e.target.checked;update();});
 }
 const api={render,bind,spark,output,matches};root.MomentumHighs=api;
 if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='undefined'?globalThis:window);
