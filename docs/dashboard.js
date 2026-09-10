/* Operational price modules; guides remain accessible through a details section. */
(function(){
 'use strict';
 const C=ResearchCharts,E=C.esc,F=C.fmt;
 const cache=new Map();let request=0;
 const state={rs:{market:'all'},momentum:{group:'all'}};
 const groupNames={country:'국가·지역',sector:'섹터 로테이션',factor:'팩터(스타일)',asset:'자산군',KR:'한국',US:'미국'};
 const valid=r=>typeof r.z==='number'&&Number.isFinite(r.z);
 const sortZ=rows=>[...rows].sort((a,b)=>(b.z??-Infinity)-(a.z??-Infinity));
 const heading=(title,note='')=>`<div class="section-head"><h2>${E(title)}</h2>${note?`<span>${E(note)}</span>`:''}</div>`;
 const chartCard=(title,body,note='')=>`<figure class="data-chart"><figcaption>${E(title)}</figcaption>${body}${note?`<p class="chart-note">${E(note)}</p>`:''}</figure>`;
 const kpi=(label,value,sub)=>`<article class="kpi"><small>${E(label)}</small><strong>${E(value)}</strong><span>${E(sub)}</span></article>`;
 function controls(id,values,key){return `<div class="group-filter dashboard-filter" role="group" aria-label="${id==='rs'?'시장 필터':'모멘텀 그룹 필터'}">${values.map(([v,l])=>`<button data-filter="${v}" aria-pressed="${state[id][key]===v}" class="${state[id][key]===v?'active':''}">${E(l)}</button>`).join('')}</div>`;}
 function header(d,title){return `<p class="eyebrow">PRICE RESEARCH / ${d.module.toUpperCase()}</p><div class="title-row"><div><h1>${title}</h1><p class="lead">${d.module==='rs'?'한국·미국 섹터와 스타일의 상대강도':'국가·섹터·팩터·자산군의 주도 흐름'}</p></div><span class="count-badge">실데이터 · 부분 구현</span></div><div class="data-meta"><span>가격 기준 <b>${E(d.as_of)}</b></span><span>출처 ${E(d.source)}</span><a href="data/${d.module}.json" download="${d.module}-${d.as_of}.json">계산 결과 JSON ↓</a></div><p class="scope-note">${E(d.method_note)}</p>`;}
 function method(d){return `<details class="method-details"><summary>계산 기준 · 데이터 수집 상태</summary><div class="method-body"><p>기간수익률: 1W 5일 · 1M 21일 · 3M 63일 · 1Y 252일. z-score: 3M 수익률 차이의 1,260개 관측치, 모집단 표준편차. 두 종목의 공통 거래일만 사용합니다.</p><p>원본 기준일 대조에 따라 국내 ETF는 배당 조정가격, 미국 ETF는 배당 재투자를 제외한 종가를 사용합니다. KOSPI는 가격지수입니다. 국가·팩터·자산군의 비교 통화는 USD입니다.</p><p>RS 차트는 ±1σ·±2σ 기준선, 순위 막대는 원본의 ±1·±2.58 표식을 유지합니다. 원본의 두 기준이 달라 하나로 합치지 않았습니다.</p><p>가격은 수집 당시의 수정계열입니다. 현재 보이는 과거값이 해당 과거 시점에 알려진 데이터였음을 뜻하지 않습니다. 부족한 역사 구간은 연장하거나 채우지 않습니다.</p><a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/PRICE_CONTRACT.md">계산식·미확인 설정·종목 식별 근거 ↗</a><div class="table-scroll"><table class="data-table"><thead><tr><th>종목</th><th>통화</th><th>관측 수</th><th>마지막 가격</th><th>상태</th></tr></thead><tbody>${d.quality.map(q=>`<tr><td>${E(q.symbol)}</td><td>${E(q.currency||'—')}</td><td>${E(q.rows||'—')}</td><td>${E(q.last_date||'—')}</td><td>${E(q.status)}</td></tr>`).join('')}</tbody></table></div></div></details>`;}
 function pairTable(rows){return `<div class="table-scroll"><table class="data-table"><caption>페어별 수치 · 수익률 차이와 z-score</caption><thead><tr><th>시장</th><th>페어 / 종목</th><th>3M 차이 (%p)</th><th>z (σ)</th><th>Δz 1W (σ)</th><th>판정 / 기준일</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${E(r.market)}</td><th scope="row">${E(r.name)}<small>${E(r.a||'미확인')} / ${E(r.b||'미확인')}</small></th><td>${F(r.spread_pp)}</td><td>${F(r.z,'',2)}</td><td>${F(r.dz_1w,'',2)}</td><td><span class="zone">${E(r.zone)}</span><small>${E(r.reason||r.as_of||'')}</small></td></tr>`).join('')}</tbody></table></div>`;}
 function rs(d){
  const all=sortZ(d.pairs),rows=all.filter(r=>state.rs.market==='all'||r.market===state.rs.market);
  const leaders=['KR','US'].map(m=>all.find(r=>r.market===m&&valid(r))),weak=all.filter(valid).at(-1);
  const stock=d.stock_rankings?.KOSPI200?.leaders?.[0];
  const cards=leaders.map((r,i)=>kpi(`${i?'US':'KR'} 상대강도 1위`,r?.name||'산출 불가',r?`z ${F(r.z,'σ',2)} · ${r.zone}`:'가격 확인 필요')).join('')+kpi('최약세 · 전체',weak?.name||'산출 불가',weak?`z ${F(weak.z,'σ',2)} · ${weak.zone}`:'')+kpi('KOSPI200 · 오닐 RS 1위',stock?.name||'산출 대기',stock?`RS ${F(stock.rs,'',0)} · YTD ${F(stock.ytd,'%')}`:'KRX 공식 KOSPI200 기준');
  const hm=['KR','US'].flatMap(m=>rows.filter(r=>r.market===m).map(r=>({group:groupNames[m],name:r.name,values:[r.spread_pp,r.z,r.dz_1w]})));
  return header(d,'주간 상대강도 (RS)')+`<div class="kpi-grid">${cards}</div><div class="coverage-note">페어 ${d.coverage.pairs}/${d.coverage.expected_pairs} 산출 · 확인되지 않은 페어도 목록에 표시합니다.</div>`+controls('rs',[['all','전체'],['KR','한국'],['US','미국']],'market')+
   `<div class="chart-grid summary-charts">${chartCard('섹터·스타일 z-score 상위 14',C.bars(rows.filter(valid).slice(0,14).map(r=>({name:r.name,value:r.z})),{unit:'σ',markers:[-2.58,-1,1,2.58],title:'상대강도 순위'}),'3M 기간수익률 스프레드의 5Y z-score')}${['KR','US'].filter(m=>state.rs.market==='all'||m===state.rs.market).map(m=>{const r=d.stock_rankings[m];return chartCard(m+' 대형주 · 1M 수익률 Top / Worst',r?C.bars([...r.strong,...r.weak].map(a=>({name:a.name,value:a.r1m})),{unit:'%',title:m+' 대형주'}):C.line({reason:'가격 수집 대기'}),'1W로 선별한 강세 8·약세 6종목의 1M 수익률');}).join('')}</div>`+stockTables(d.stock_rankings)+
   heading('상대강도 히트맵','열별 색상 스케일 · 숫자와 단위를 함께 비교')+C.heatmap(hm,['3M 차이 (%p)','z (σ)','Δz 1W (σ)'],'한국·미국 섹터와 스타일')+
   heading('페어별 상세 수치')+pairTable(rows)+heading('5년 상대강도 추이','고정 축 −3.2~+3.2σ · 축 밖 값은 툴팁·표에서 확인')+
   `<div class="chart-grid">${rows.map(r=>chartCard(`${r.market} · ${r.name} · z ${F(r.z,'',2)}`,C.line(d.series[r.id]||{reason:r.reason},{title:r.name,kind:'rs'}),r.reason||`${r.a} / ${r.b} · 3M 차이 ${F(r.spread_pp,'%p')} · 기준 ${r.as_of}`)).join('')}</div>`+method(d);
 }
 function weeklyTables(rankings){return ['KR','US'].filter(m=>state.rs.market==='all'||m===state.rs.market).map(m=>{
  const r=rankings[m];if(!r)return '';
  return `<div class="chart-grid">${[['강세',r.strong],['약세',r.weak_table||r.weak]].map(([label,rows])=>`<section>${heading(`${m} · 1W ${label} 8종목`)}<div class="table-scroll"><table class="data-table" data-weekly-table="${m}-${label}"><thead><tr><th>종목 / 공식 업종</th><th>1W %</th><th>1M %</th><th>기준일</th></tr></thead><tbody>${rows.map(a=>`<tr><th>${E(a.name)}<small>${E(a.symbol)} · ${E(a.sector)}</small></th><td>${F(a.r1w)}</td><td>${F(a.r1m)}</td><td>${E(a.as_of)}</td></tr>`).join('')}</tbody></table></div></section>`).join('')}</div>`;
 }).join('');}
 function stockTables(rankings){return weeklyTables(rankings)+['KR','US','KOSPI200'].filter(m=>state.rs.market==='all'||m===state.rs.market||(m==='KOSPI200'&&state.rs.market==='KR')).map(m=>{const r=rankings[m];if(!r)return '';return heading(m+' · 오닐 RS 상위 15',`${r.available}/${r.expected}종목 산출 · 구성 기준 ${r.membership_as_of}`)+`<div class="table-scroll"><table class="data-table"><thead><tr><th>종목</th><th>공식 업종</th><th>RS</th><th>1W %</th><th>1M %</th><th>3M %</th><th>1Y %</th></tr></thead><tbody>${r.leaders.map(a=>`<tr><th>${E(a.name)}<small>${E(a.symbol)}</small></th><td>${E(a.sector)}</td><td>${F(a.rs,'',0)}</td><td>${F(a.r1w)}</td><td>${F(a.r1m)}</td><td>${F(a.r3m)}</td><td>${F(a.r1y)}</td></tr>`).join('')}</tbody></table></div><p class="chart-note">KRX 공식 구성종목 / 미국 IVV 공시 주식. 주가 3·6·9·12M 가중 40·20·20·20%, 유니버스 내 1–99 백분위. 현재 구성종목 기준이며 역사 구성종목 백테스트가 아닙니다.</p>${r.excluded?.length?`<details class="method-details"><summary>산출 제외 ${r.excluded.length}종목</summary><ul>${r.excluded.map(a=>`<li>${E(a.name)} (${E(a.symbol)}) · ${a.observations}개 관측 · ${E(a.reason)}</li>`).join('')}</ul></details>`:''}`;}).join('');}
 function momentum(d){
  const sel=state.momentum.group,assets=['country','factor','asset'].flatMap(g=>d.assets.filter(a=>a.group===g&&(sel==='all'||g===sel)).sort((a,b)=>(b.returns['3M']??-Infinity)-(a.returns['3M']??-Infinity))),sectors=sortZ(d.sectors);
  const top=g=>d.assets.filter(a=>a.group===g&&a.returns['3M']!==null).sort((a,b)=>b.returns['3M']-a.returns['3M'])[0];
  const country=top('country'),factor=top('factor'),leader=sectors.find(valid);
  const cards=kpi('국가 3M 1위',country?.name||'—',country?F(country.returns['3M'],'%'):'')+kpi('섹터 z-score 1위',leader?.name||'—',leader?F(leader.z,'σ',2):'')+kpi('팩터 3M 1위',factor?.name||'—',factor?F(factor.returns['3M'],'%'):'')+kpi('3M 절대강세',`${d.assets.filter(a=>a.returns['3M']>0).length} / ${d.coverage.assets}`,'관측 가능한 32개 자산 중 양의 수익률');
  const charts=['country','sector','factor','asset'].filter(g=>sel==='all'||g===sel).map(g=>{
   if(g==='sector')return chartCard('섹터 로테이션 · 3M 상대강도 z',C.bars(sectors.map(r=>({name:r.name,value:r.z})),{unit:'σ',markers:[-2.58,-1,1,2.58],title:'섹터 로테이션'}),`원본 24개 중 ${d.coverage.sectors}개 산출 · 기준일 ${d.as_of}`);
   const rows=d.assets.filter(a=>a.group===g).sort((a,b)=>(b.returns['3M']??-Infinity)-(a.returns['3M']??-Infinity)).slice(0,g==='country'?12:99);
   return chartCard(`${groupNames[g]} · 3M 수익률${g==='country'?' 상위 12':''}`,C.bars(rows.map(a=>({name:`${a.name} (${a.symbol})`,value:a.returns['3M']})),{unit:'%',title:groupNames[g]}),`공통 기준일 ${d.asset_as_of} · USD 표시 ETF / BTC`);
  }).join('');
  let html=header(d,'모멘텀')+`<div class="kpi-grid">${cards}</div><div class="coverage-note">국가·팩터·자산 ${d.coverage.assets}/${d.coverage.expected_assets} · 섹터 ${d.coverage.sectors}/${d.coverage.expected_sectors} · 3M/6M 차트 ${d.coverage.charts}/${d.coverage.expected_charts}<br>국가·팩터·자산 공통 기준일 ${d.asset_as_of} · 섹터 기준일 ${d.as_of}. 자산별 휴장·제공 시차를 반영했습니다.</div>`+controls('momentum',[['all','전체'],['country','국가·지역'],['sector','섹터 로테이션'],['factor','팩터(스타일)'],['asset','자산군']],'group')+`<div class="chart-grid summary-charts">${charts}</div>`;
  if(assets.length){
   const cols=['1W','1M','3M','YTD','1Y'];
   html+=heading('기간별 수익률 히트맵','열별 색상 스케일 · %')+C.heatmap(assets.map(a=>({group:groupNames[a.group],name:`${a.name} (${a.symbol})`,values:cols.map(c=>a.returns[c])})),cols.map(c=>c+' (%)'),'절대 수익률 · USD')+
    heading('기간 수익률 · 벤치마크 비교')+`<div class="table-scroll"><table class="data-table"><thead><tr><th>구분</th><th>이름</th><th>1M (%)</th><th>3M (%)</th><th>3M SPY 대비 (%p)</th><th>기준일 / 상태</th></tr></thead><tbody>${assets.map(a=>`<tr><td>${groupNames[a.group]}</td><th scope="row">${E(a.name)}<small>${E(a.symbol)}</small></th><td>${F(a.returns['1M'])}</td><td>${F(a.returns['3M'])}</td><td>${F(a.excess_3m_pp)}</td><td>${E(a.reason||a.as_of)}</td></tr>`).join('')}</tbody></table></div>`;
  }
  if(sel==='all'||sel==='sector'){
   html+=heading('섹터별 상대강도')+pairTable(sectors)+heading('섹터별 누적 초과수익','강세 8·약세 8개 · 왼쪽 3M / 오른쪽 6M')+`<div class="chart-grid">${d.chart_pairs.map(id=>{const r=sectors.find(x=>x.id===id);return [3,6].map(n=>{const c=d.curves[id]?.[String(n)];return chartCard(`${r.name} · ${n}M · 누적초과 ${F(c?.last,'%')}`,C.line(c,{kind:'momentum',title:`${r.name} ${n}M`}),`${r.a} / ${r.b} · 가격비의 시작점 대비 변화율 · 0 기준 양/음 영역`);}).join('');}).join('')}</div>`;
  }
  return html+method(d);
 }
 function guide(m){return `<details class="method-details"><summary>기존 구현 가이드</summary><div class="method-body"><p>${E(m.purpose)}</p><ol>${m.build.map(s=>`<li>${E(s)}</li>`).join('')}</ol><a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/modules/${m.id}.md">탭별 문서 ↗</a></div></details>`;}
 function paint(container,m,d){C.reset();container.innerHTML=(m.id==='rs'?rs(d):momentum(d))+guide(m);C.bind(container);container.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{state[m.id][m.id==='rs'?'market':'group']=b.dataset.filter;paint(container,m,d);}));}
 async function render(container,m){
  const token=++request;
  container.innerHTML=`<h1>${E(m.title)}</h1><p role="status">저장된 계산 결과를 불러옵니다…</p>`;
  try{
   if(!cache.has(m.id)){const response=await fetch(`data/${m.id}.json`);if(!response.ok)throw new Error('HTTP '+response.status);const d=await response.json();if(d.schema_version!==1||d.module!==m.id)throw new Error('Data schema mismatch');cache.set(m.id,d);}
   if(token!==request||location.hash.slice(1)!==m.id)return;
   paint(container,m,cache.get(m.id));
  }catch(error){if(token!==request||location.hash.slice(1)!==m.id)return;container.innerHTML=`<h1>${E(m.title)}</h1><div class="empty" role="alert">계산 결과를 읽을 수 없습니다. <button id="retry-data">다시 불러오기</button></div>`;container.querySelector('#retry-data').addEventListener('click',()=>render(container,m));}
 }
 window.PriceDashboard={render,cancel:()=>{request++;C.reset();}};
})();
