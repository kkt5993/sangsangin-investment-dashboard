/* Real snapshot render checks without browser or external calls. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
require('./test_decisions.cjs');
require('./test_dragon_research.cjs');
require('./test_dragon_signals.cjs');
require('./test_clinical.cjs');
require('./test_guru.cjs');
require('./test_dragon_operations.cjs');
require('./test_attention.cjs');
require('./test_chart_readability.cjs');
require('./test_presentation.cjs');
const relationChecks=require('./test_relations.cjs');
const overviewChecks=require('./test_overview.cjs');
const geoChecks=require('./test_geo.cjs');
const earningsChecks=require('./test_earnings.cjs');
const ownershipChecks=require('./test_ownership.cjs');
const strategyChecks=require('./test_strategy_cards.cjs');
const calendarChecks=require('./test_calendar.cjs');
const satelliteChecks=require('./test_satellite.cjs');
const tradeChecks=require('./test_trade.cjs');
const chainChecks=require('./test_chain.cjs');
const sauronChecks=require('./test_sauron.cjs');
const satelliteTileChecks=require('./test_satellite_tiles.cjs');
const pdfChecks=require('./test_notebook_pdf.cjs');
const ocrChecks=require('./test_pdf_ocr.cjs');
const researchChecks=Promise.resolve().then(()=>require('./test_research_store.cjs')).then(()=>require('./test_research_notes.cjs'));
const root=path.join(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const modules=JSON.parse(read('docs/modules.js').replace(/^const MODULES = /,'').trim().replace(/;$/,''));
const data=Object.fromEntries(fs.readdirSync(path.join(root,'docs/data')).filter(n=>n.endsWith('.json')).map(n=>[n.slice(0,-5),JSON.parse(read('docs/data/'+n))]));
let requests=0;const context=vm.createContext({window:{},location:{hash:''},console,fetch:async url=>{requests++;return {ok:true,json:async()=>data[path.basename(url,'.json')]};}});
for(const file of ['charts','analysis-charts','network-views','sauron-views','trade-views','chain-views','relation-views','decision-ledger','research-store','pdf-text','notebook-pdf','research-notes','geo-views','earnings-views','ownership-views','strategy-cards','calendar-views','satellite-views','dragon-research','dragon-signals','clinical-views','guru-views','dragon-operations','attention-views','relation-discovery','research-dashboard'])vm.runInContext(read('docs/'+file+'.js'),context);
tradeChecks(context,data);
chainChecks(context,data);
function container(){return {innerHTML:'',querySelectorAll(){return [];},querySelector(){return null;}};}
// Minimal event targets exercise the actual tab and scenario callbacks offline.
function interactiveContainer(){
 const attr=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
 const node=(value='',dataset={})=>({value,dataset,innerHTML:'',events:{},setAttribute(k,v){this[k]=v;},addEventListener(k,f){this.events[k]=f;},fire(k){this.events[k]?.({target:this});}});
 const c={html:'',buttons:[],boxes:[],select:node('all'),get innerHTML(){return this.html;},set innerHTML(h){
  this.html=h;this.select=node('all');this.income=node(h.match(/id="income-amount"[^>]*value="([^"]+)"/)?.[1]||'');this.buttons=[...h.matchAll(/data-subview="([^"]+)"/g)].map(m=>node('',{subview:attr(m[1])}));
  this.boxes=[...h.matchAll(/data-scenario="(\d+)"/g)].map(m=>{const market=node('KR'),shock=node('-10'),output=node();return {dataset:{scenario:m[1]},market,shock,output,querySelector:s=>({'[data-scenario-market]':market,'[data-shock]':shock,'[data-scenario-output]':output}[s]||null),querySelectorAll:()=>[market,shock]};});
  this.moes=[...h.matchAll(/data-moe="(\d+)"/g)].map(m=>{const section=data.maximus.sections[+m[1]],selector=section.select_target?node(section.cards[0].symbol):null,output=node();return {dataset:{moe:m[1]},selector,output,querySelector:s=>s==='[data-moe-target]'?selector:output,querySelectorAll:()=>[]};});
  this.reviews=[...h.matchAll(/data-review-charts="(\d+)"/g)].map(m=>{const selector=node('latest'),output=node();return {dataset:{reviewCharts:m[1]},selector,output,querySelector:s=>s==='[data-review-date]'?selector:output};});
  this.digests=[...h.matchAll(/data-digest-trends="(\d+)"/g)].map(m=>{const selector=node('short'),output=node();return {dataset:{digestTrends:m[1]},selector,output,querySelector:s=>s==='[data-digest-horizon]'?selector:output,querySelectorAll:()=>[]};});
  this.holos=[...h.matchAll(/data-hologram="(\d+)"/g)].map(m=>{const yaw=node('60'),output=node();return {dataset:{hologram:m[1]},yaw,output,querySelector:s=>s==='[data-holo-yaw]'?yaw:output};});
  this.rebals=[...h.matchAll(/data-rebalancing="(\d+)"/g)].map(m=>{const shock=node('5'),output=node();return {dataset:{rebalancing:m[1]},shock,output,querySelector:s=>s==='[data-rebal-shock]'?shock:output};});
  this.discoveries=[...h.matchAll(/data-discovery="(\d+)"/g)].map(m=>{const section=data.discovery.sections[+m[1]],markets=['all','US','KR'].map(v=>node('',{discoveryMarket:v})),buckets=section.buckets.map(b=>node('',{discoveryBucket:b.name})),counts=section.buckets.map(b=>node('',{bucketCount:b.name})),search=node(),all=node(),more=node(),output=node();return {dataset:{discovery:m[1]},markets,buckets,counts,search,all,more,output,querySelector:s=>({'[data-discovery-search]':search,'[data-discovery-all]':all,'[data-discovery-more]':more,'[data-discovery-output]':output}[s]),querySelectorAll:s=>({'[data-discovery-market]':markets,'[data-discovery-bucket]':buckets,'[data-bucket-count]':counts}[s]||[])};});
  this.scanners=[...h.matchAll(/data-scanner="(\d+)"/g)].map(m=>{const pattern=node('all'),group=node('all'),count=node('9'),output=node();return {dataset:{scanner:m[1]},pattern,group,count,output,querySelector:s=>({'[data-scan-pattern]':pattern,'[data-scan-group]':group,'[data-scan-count]':count,'[data-scan-output]':output}[s]),querySelectorAll:s=>s==='select'?[pattern,group,count]:[]};});
  this.valuations=[...h.matchAll(/data-valuation="(\d+)"/g)].map(m=>{const months=node('180'),output=node();return {dataset:{valuation:m[1]},months,output,querySelector:s=>s==='[data-valuation-months]'?months:output};});
  this.industries=[...h.matchAll(/data-industries="(\d+)"/g)].map(m=>{const sector=node('all'),role=node('all'),cards=[...h.matchAll(/data-industry="([^"]+)" data-indicator-role="([^"]+)"/g)].map(a=>node('',{industry:a[1],indicatorRole:a[2]}));return {sector,role,cards,querySelector:s=>s==='[data-industry-filter]'?sector:role,querySelectorAll:s=>s==='select'?[sector,role]:cards};});
 },querySelector(s){return s==='#analysis-group'?this.select:s==='#income-amount'?this.income:null;},querySelectorAll(s){return s==='[data-digest-trends]'?this.digests:s==='[data-review-charts]'?this.reviews:s==='[data-subview]'?this.buttons:s==='[data-scenario]'?this.boxes:s==='[data-hologram]'?this.holos:s==='[data-moe]'?this.moes:s==='[data-industries]'?this.industries:s==='[data-rebalancing]'?this.rebals:s==='[data-valuation]'?this.valuations:s==='[data-scanner]'?this.scanners:s==='[data-discovery]'?this.discoveries:[];}};
 return c;
}
(async()=>{
 await sauronChecks;await relationChecks;await overviewChecks;await geoChecks;await earningsChecks;await ownershipChecks;await strategyChecks;await calendarChecks;await satelliteChecks;await satelliteTileChecks;await researchChecks;await pdfChecks;await ocrChecks;
 let count=0;
 for(const m of modules){const d=data[m.id];if(d?.schema_version!==2)continue;const c=container();context.location.hash='#'+m.id;await context.window.ResearchDashboard.render(c,m);
  assert(c.innerHTML.includes('<h1>'),m.id);assert(!c.innerHTML.includes('role="alert"'),m.id);assert(!/\b(NaN|Infinity|undefined)\b|\[object Object\]/.test(c.innerHTML),m.id+' invalid rendering');assert(c.innerHTML.includes('data/'+m.id+'.json'),m.id);
  // Render every subview, not only the initially selected group.
  for(const [i,s] of d.sections.entries()){const h=context.window.ResearchDashboard.section(s,i,{});assert(typeof h==='string'&&h.length,m.id);assert(!/\b(NaN|Infinity|undefined)\b|\[object Object\]/.test(h),m.id+' '+s.title);}
  await context.window.ResearchDashboard.render(c,m);count++;
 }
 assert.equal(requests,count,'one local request per module across repeated navigation');
 const monitor=data.multiasset.sections.find(s=>s.type==='assetmonitor');assert(monitor);
 const monitorHTML=context.window.ResearchDashboard.section(monitor,0,{});
 assert.equal((monitorHTML.match(/data-monitor-kpi/g)||[]).length,4);
 assert.equal((monitorHTML.match(/class="table-group"/g)||[]).length,6);
 assert.equal((monitorHTML.match(/data-bar-value=/g)||[]).length,monitor.rows.filter(r=>r.values[2]!==null).length);
 for(const r of monitor.rows)assert(monitorHTML.includes(r.name.replace('&','&amp;'))&&monitorHTML.includes(r.symbol.replace('&','&amp;')));
 assert(monitorHTML.indexOf('자산군 × 기간 수익률')<monitorHTML.indexOf('멀티에셋 · 1개월 수익률'));
 assert(monitorHTML.includes('data-bar-guide="0"'));
 for(const r of monitor.rows)for(const v of [r.market_close,r.price,r.ma50,r.ma200,r.observations].filter(v=>v!==null))assert(monitorHTML.includes('data-value="'+v+'">'+v+'</td>'),'exact monitor price and count display');
 for(const r of monitor.rows.filter(r=>r.values[2]!==null))assert(monitorHTML.includes('data-bar-signal="'+r.signal+'"'));
 const unsafe=JSON.parse(JSON.stringify(monitor));unsafe.rows[0].name='<script>alert(1)</script>';unsafe.rows[0].source='javascript:alert(1)';
 const escaped=context.window.ResearchDashboard.section(unsafe,0,{});assert(!escaped.includes('<script>'));assert(!escaped.includes('href="javascript:'));
 const interactive=interactiveContainer();context.location.hash='#dragonglass';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='dragonglass'));
 interactive.buttons.find(b=>b.dataset.subview==='시장 Beta 민감도').fire('click');assert.equal(interactive.boxes.length,1);
 const box=interactive.boxes[0],scenario=data.dragonglass.sections.find(s=>s.type==='scenario');
 assert(box.output.innerHTML.includes('data-bar-value="'+scenario.rows.find(r=>r.market==='KR').beta*-10+'"'));
 box.market.value='US';box.shock.value='-20';box.shock.fire('input');assert(box.output.innerHTML.includes('data-bar-value="'+scenario.rows.find(r=>r.market==='US').beta*-20+'"'));
 interactive.select.value='all';interactive.select.fire('change');assert(interactive.innerHTML.includes('지금 주목 · 신호·관계·근거')&&interactive.innerHTML.includes('data-scenario='),'all view survives repaint');
 context.location.hash='#discovery';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='discovery'));
 const db=interactive.discoveries[0],di=data.discovery.sections[0].items,shown=()=>[...db.output.innerHTML.matchAll(/data-discovery-symbol="([^"]+)"/g)].map(m=>m[1]);
 assert.equal(shown().length,Math.min(30,di.filter(r=>r.market==='US').length));
 db.markets[0].fire('click');db.more.fire('click');assert.equal(shown().length,Math.min(60,di.length));
 for(const b of db.buckets){b.fire('click');const expected=di.filter(r=>r.bucket===b.dataset.discoveryBucket).slice(0,30).map(r=>r.symbol);assert.deepEqual(shown(),expected);}
 db.all.fire('click');db.markets[2].fire('click');assert(shown().every(s=>di.find(r=>r.symbol===s).market==='KR'));
 db.search.value='no matching stock 478291';db.search.fire('input');assert.equal(shown().length,0);assert(db.more.hidden);
 db.search.value='';db.search.fire('input');assert(shown().length>0);assert.equal((db.output.innerHTML.match(/data-discovery-lens=/g)||[]).length,shown().length*3);
 const A=context.window.AnalysisCharts;
 context.location.hash='#ask_digest';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='ask_digest'));
 interactive.buttons.find(b=>b.dataset.subview==='기간별 추세').fire('click');const digestBox=interactive.digests[0],digestPanels=data.ask_digest.sections.find(s=>s.type==='digesttrends').panels,trendHtml=[];
 for(const p of digestPanels){digestBox.selector.value=p.id;digestBox.selector.fire('change');const h=digestBox.output.innerHTML;assert(h.includes(context.window.ResearchCharts.esc(p.title)));assert.equal((h.match(/data-bar-value=/g)||[]).length,p.rows.length);trendHtml.push(h);}
 assert.equal(new Set(trendHtml).size,3);
 for(const group of ['시장 브리프','테마 관찰','종목 관찰','크로스에셋','위험 요약','핵심 차트','모듈 요약']){interactive.buttons.find(b=>b.dataset.subview===group).fire('click');assert(!interactive.innerHTML.includes('role="alert"'));}
 const badTheme=JSON.parse(JSON.stringify(data.ask_digest.sections.find(s=>s.type==='digestthemes')));badTheme.items[0].members[0].source='javascript:alert(1)';badTheme.items[0].name='<script>bad</script>';const safeTheme=context.window.ResearchDashboard.section(badTheme,0,{});assert(!safeTheme.includes('href="javascript:'));assert(!safeTheme.includes('<script>bad'));assert(safeTheme.includes('&lt;script&gt;bad'));
 context.location.hash='#iw';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='iw'));
 interactive.buttons.find(b=>b.dataset.subview==='이번 주의 그림').fire('click');const reviewBox=interactive.reviews[0],reviews=data.iw.sections.find(s=>s.type==='reviewcharts');
 for(const value of ['latest',reviews.archives[0].period,reviews.archives.at(-1).period]){reviewBox.selector.value=value;reviewBox.selector.fire('change');const h=reviewBox.output.innerHTML;assert.equal((h.match(/data-timeline-cell=/g)||[]).length,108);assert(!/NaN|Infinity|undefined/.test(h));const expected=value==='latest'?reviews.latest:reviews.archives.find(r=>r.period===value).charts;assert(h.includes(expected[0].rows[0][0]));}
 const missingTimeline=JSON.parse(JSON.stringify(reviews.latest[0]));missingTimeline.rows[0][1]=null;assert(A.stateTimeline(missingTimeline).includes('미산출'));assert.equal((A.stateTimeline(reviews.latest[0]).match(/data-timeline-panel=/g)||[]).length,3);
 context.location.hash='#multiasset';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='multiasset'));interactive.buttons.find(b=>b.dataset.subview==='패턴 스캐너').fire('click');
 const sb=interactive.scanners[0],scan=data.multiasset.sections.find(s=>s.type==='scanner');assert.equal((sb.output.innerHTML.match(/data-chart-type="scan-candles"/g)||[]).length,9);sb.count.value='all';sb.count.fire('change');assert.equal((sb.output.innerHTML.match(/data-chart-type="scan-candles"/g)||[]).length,37);sb.pattern.value=scan.items[0].pattern;sb.pattern.fire('change');assert.equal((sb.output.innerHTML.match(/data-chart-type="scan-candles"/g)||[]).length,scan.items.filter(r=>r.pattern===sb.pattern.value).length);
 const scanSvg=A.scanCandles(scan.items[0]);assert.equal((scanSvg.match(/data-scan-candle=/g)||[]).length,90);assert(scanSvg.includes('data-price-axis="right"'));assert(scanSvg.includes('data-scan-ma="MA20"')&&scanSvg.includes('data-scan-ma="MA60"'));
 const pref=context.window.ResearchDashboard.section({type:'preference',title:'test',columns:['up','down','flat','missing'],rows:[{name:'regime',values:[.3,-.3,.1,null]}]},0,{});assert(pref.includes('● 0.30')&&pref.includes('▽ -0.30')&&pref.includes('· 0.10'));
 context.location.hash='#risk';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='risk'));
 interactive.buttons.find(b=>b.dataset.subview==='KOSPI 숏감마').fire('click');
 const kr=data.risk.sections.filter(s=>s.group==='KOSPI 숏감마');
 assert.equal(kr.find(s=>s.title==='KOSPI 숏감마 · 8개 관측').rows.length,8);
 assert(interactive.innerHTML.includes('KOSPI 숏감마 · 8개 관측')&&interactive.innerHTML.includes('공식 ETF 대상'));
 assert(!interactive.innerHTML.includes('자료 연결 준비 중'));assert(!/NaN|Infinity|undefined/.test(interactive.innerHTML));
 const krLines=kr.filter(s=>s.type==='line');assert(krLines.length<=2);
 for(const s of krLines){const svg=context.window.AnalysisCharts.line(s);assert(svg.includes('<svg'));assert(!/NaN|Infinity|undefined/.test(svg));}
 if(krLines.length){assert.deepEqual(krLines[0].limits,[0,100]);assert.deepEqual(krLines[0].guides,[45,70]);assert.equal(krLines[1].series.length,2);}
 interactive.buttons.find(b=>b.dataset.subview==='비펀더멘탈 수급').fire('click');assert.equal(interactive.rebals.length,1);
 const rb=interactive.rebals[0],rc=data.risk.sections.find(s=>s.type==='rebalancing');rb.shock.value='-5';rb.shock.fire('input');
 assert(rb.output.innerHTML.includes('data-flow-value="'+rc.stocks[0].coefficient*-.05/1e6+'"'));assert(rb.output.innerHTML.includes('data-adv-value='));
 rb.shock.value='0';rb.shock.fire('input');assert(rb.output.innerHTML.includes('data-flow-value="0"'));assert(!/NaN|Infinity/.test(rb.output.innerHTML));
 context.location.hash='#regime';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='regime'));
 interactive.buttons.find(b=>b.dataset.subview==='밸류에이션').fire('click');assert.equal(interactive.valuations.length,1);
 const vb=interactive.valuations[0];vb.months.value='60';vb.months.fire('change');assert.equal((vb.output.innerHTML.match(/data-valuation-panel=/g)||[]).length,9);
 assert(vb.output.innerHTML.includes('data-scale="log"'));const firstVal=vb.output.innerHTML;vb.months.value='180';vb.months.fire('change');assert.notEqual(firstVal,vb.output.innerHTML);
 interactive.buttons.find(b=>b.dataset.subview==='Soros 재귀성').fire('click');assert.equal(interactive.holos.length,3);
 const hbox=interactive.holos[0];hbox.yaw.value='100';hbox.yaw.fire('input');assert(hbox.output.innerHTML.includes('data-holo-quadrant'));
 interactive.buttons.find(b=>b.dataset.subview==='산업별 핵심지표').fire('click');assert.equal(interactive.industries.length,1);
 const ibox=interactive.industries[0];ibox.sector.value='반도체·IT';ibox.sector.fire('change');assert.equal(ibox.cards.filter(c=>!c.hidden).length,3);
 ibox.role.value='Q';ibox.role.fire('change');assert.equal(ibox.cards.filter(c=>!c.hidden).length,1);
 const holos=data.regime.sections.filter(s=>s.type==='hologram');assert.equal(holos.length,3);
 const opt=data.risk.sections.filter(s=>s.type==='optionprofile');assert.equal(opt.length,7);
 for(const s of opt){const h=A.optionProfile(s);assert(h.includes('data-option-marker="현물"'));assert(h.includes('data-option-bar="'+(s.mode==='oi'?'put':'gamma')+'"'));if(s.mode==='gamma'&&s.em!==null)assert(h.includes('data-expected-band'));}
 for(const h of holos){assert.equal(h.rows.length,36);assert(A.hologram(h).includes('data-holo-trajectory'));assert(A.radar(h).includes('data-radar-date'));assert.notEqual(A.hologram(h,0),A.hologram(h,1));}
 assert.equal(data.regime.sections.find(s=>s.type==='industry').items.length,39);
 for(const g of ['PM 키 게이지','금리·성장','크로스에셋 속보','CTA 시스템 트렌드','매크로 z-score','다이버전스·실적'])assert(data.pm_weekend.sections.some(s=>s.group===g),g);
 const dyn=data.dynamics.sections[0];assert.equal(dyn.surface.windows.length,8);assert.equal(dyn.phase.length,60);assert(A.surface(dyn.surface).includes('data-chart-type="surface"'));
 const watch=data.watch.sections[0];assert.equal(watch.candles.length,120);assert.equal(watch.weekly.length,52);assert.equal((A.candles(watch).match(/data-volume="1"/g)||[]).length,120);
 assert(data.watch.sections.some(s=>s.pattern&&A.candles(s).includes('data-pattern="1"')),'geometric candidates have overlays');
 const ml=data.ml.sections.find(s=>s.type==='ml');assert(A.forecast(ml).includes('data-interval="90"'));assert(A.forecast(ml).includes('data-interval="68"'));assert(A.forecast(ml).includes('data-prediction="1"'));
 const board=data.ml.sections.find(s=>s.type==='modelleaderboard'),boardSVG=A.modelLeaderboard(board);
 assert.equal((boardSVG.match(/data-chart-type="model-leaderboard"/g)||[]).length,3);
 assert.equal((boardSVG.match(/data-model-bar="1M"/g)||[]).length,39);assert.equal((boardSVG.match(/data-model-bar="3M"/g)||[]).length,39);
 assert.equal((boardSVG.match(/data-model-chance="50"/g)||[]).length,3);assert(boardSVG.includes('Transformer'));
 const composite=data.ml.sections.find(s=>s.type==='line'&&s.group==='전망 요약');assert.equal(composite.series.length,7);
 assert.equal(composite.series.filter(s=>s.dashed).length,3);assert(A.line(composite).includes('data-time-zone='));
 const lag=data.ml.sections.find(s=>s.type==='lagcorrelation');assert.equal((A.lagCorrelation(lag).match(/data-lag=/g)||[]).length,6);
 const explanations=data.ml.sections.filter(s=>s.type==='shap');assert.equal(explanations.length,2);
 const shapIds=[];for(const s of explanations){const svg=A.shap(s);assert.equal((svg.match(/data-shap-value=/g)||[]).length,15*120);shapIds.push(svg.match(/linearGradient id="([^"]+)"/)[1]);}
 assert.equal(new Set(shapIds).size,2);
 for(const p of data.ml.sections.find(s=>s.type==='featureselection').panels){const svg=A.featureSelection(p);assert.equal((svg.match(/data-shadow-wins=/g)||[]).length,p.rows.length);assert(!svg.includes('width="-'));}
 for(const s of data.ml.sections.filter(s=>s.type==='ml')){assert.equal(s.detail_table.rows.length,24);assert.equal(s.charts[0].series.length,2);assert(s.charts[0].series.every(a=>a.axis==='left'));assert.equal(s.charts[1].series[0].points.length,36);assert.equal((A.line(s.charts[1]).match(/data-line-marker=/g)||[]).length,37);assert(A.line(s.charts[1]).includes('data-axis="right"'));}
 context.location.hash='#ml';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='ml'));
 for(const group of ['모델 비교','변수 선택','SHAP 해석',...data.ml.sections.filter(s=>s.type==='ml').map(s=>s.group)]){interactive.buttons.find(b=>b.dataset.subview===group).fire('click');assert(!interactive.innerHTML.includes('role="alert"'));assert(interactive.innerHTML.includes(context.window.ResearchCharts.esc(group)));}
 context.location.hash='#etfmon';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='etfmon'));
 for(const section of data.etfmon.sections){
  interactive.buttons.find(b=>b.dataset.subview===section.group).fire('click');
  assert.equal((interactive.innerHTML.match(/data-etf-symbol=/g)||[]).length,section.rows.length);
  assert.equal((interactive.innerHTML.match(/data-etf-history=/g)||[]).length,section.rows.length);
  assert(interactive.innerHTML.includes('배당락일별 현금분배 (지급일 아님)'));
  let last=-1;for(const r of section.rows){const at=interactive.innerHTML.indexOf('data-etf-symbol="'+r.symbol+'"');assert(at>last);last=at;}
 }
 const monthlySection=data.etfmon.sections.find(s=>s.id==='monthly');interactive.buttons.find(b=>b.dataset.subview===monthlySection.group).fire('click');
 for(const amount of [20000000,0]){
  interactive.income.value=String(amount);interactive.income.fire('change');
  const r=monthlySection.rows.find(r=>r.yield_pct>0),row=interactive.innerHTML.split('data-etf-symbol="'+r.symbol+'"')[1].split('</tr>')[0];
  assert(row.includes(Math.round(amount*r.yield_pct/1200).toLocaleString('ko-KR')+'원'));
 }
 const absent={...monthlySection,rows:[{...monthlySection.rows[0],yield_pct:null,payments:null,reason:'missing',events:[],returns:[null,null,null,null]}]};
 const absentHTML=context.window.ResearchDashboard.section(absent,0,{amount:10000000});
 assert(!absentHTML.includes('data-value="0"'),'unknown distribution must not become a zero cash flow');
 assert(!/NaN|Infinity|undefined/.test(absentHTML));
 const moeGroups=data.maximus.sections.filter(s=>s.type==='moe');assert(moeGroups.length>=3);
 assert.equal(moeGroups.find(s=>s.group==='지수').cards.length,2);assert.equal(moeGroups.find(s=>s.group==='매크로').cards.length,6);
 for(const s of moeGroups){const graph=A.moeTopology(s.cards);assert.equal((graph.match(/data-moe-expert=/g)||[]).length,10);assert.equal((graph.match(/data-moe-output=/g)||[]).length,s.cards.length);for(const c of s.cards){const fan=A.moeFan(c);assert(fan.includes('data-moe-history='));if(c.bands['1'])assert(fan.includes('data-moe-band="68"')&&fan.includes('data-moe-band="95"'));}}
 context.location.hash='#maximus';await context.window.ResearchDashboard.render(interactive,modules.find(m=>m.id==='maximus'));
 interactive.buttons.find(b=>b.dataset.subview==='종목').fire('click');const stockBox=interactive.moes.find(b=>b.selector),stockCards=moeGroups.find(s=>s.group==='종목').cards;
 for(const c of [stockCards[0],stockCards.at(-1)]){stockBox.selector.value=c.symbol;stockBox.selector.fire('change');assert(stockBox.output.innerHTML.includes('data-moe-card="'+c.symbol+'"'));assert.equal((stockBox.output.innerHTML.match(/data-moe-card=/g)||[]).length,1);assert(!/NaN|Infinity|undefined/.test(stockBox.output.innerHTML));}
 const missingCard=JSON.parse(JSON.stringify(stockCards[0]));missingCard.current=null;missingCard.forecast=null;missingCard.bands={};missingCard.probability=null;missingCard.metrics={};
 const missingMoE=context.window.ResearchDashboard.section({type:'moe',title:'missing',cards:[missingCard]},0,{});assert(!/NaN|Infinity|undefined/.test(missingMoE));assert(!missingMoE.includes('<progress max="100" >'));
 assert(A.line({title:'test',left:'%',right:'index',guides:[0],series:[{name:'left',axis:'left',points:[['2026-01-01',1],['2026-02-01',2]]},{name:'right',axis:'right',points:[['2026-01-01',100],['2026-02-01',200]]}]}).includes('data-axis="right"'));
 const xss=context.window.ResearchDashboard.section({type:'table',title:'<img>',columns:['x'],rows:[['<script>alert(1)</script>']]},0,{});assert(!xss.includes('<script>'));assert(xss.includes('&lt;script&gt;'));
 console.log('PASS:',count,'new tabs, every subview, cache, real SVG structures, 120D/52W candles, dual axes, 3D surface, 68/90 bands and escaping.');
})().catch(e=>{console.error(e);process.exitCode=1;});
