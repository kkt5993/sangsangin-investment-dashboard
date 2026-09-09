'use strict';
const GROUPS={special:'PLATFORM',regime:'REGIME',momentum:'MOMENTUM',context:'CONTEXT',opportunity:'OPPORTUNITY',other:'INTERNAL'};
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const content=document.querySelector('#content');
const built=id=>BUILD_STATUS.modules[id]&&BUILD_STATUS.modules[id].status!=='blocked';
const statusLabel=id=>({operational:'계산·화면 연결',partial:'부분 구현 · 실데이터',blocked:'추가 데이터 필요'}[BUILD_STATUS.modules[id]?.status]||'구현 가이드');
let group='all';
const stages=[['01 / REGIME','국면을 읽다','성장·물가·금리·유동성'],['02 / MOMENTUM','주도를 찾다','상대강도·실적·로테이션'],['03 / CONTEXT','맥락을 확인하다','자산 간 관계·위험·쏠림'],['04 / OPPORTUNITY','판단을 기록하다','종목 발굴·전략·검증']];
function pipeline(){return '<div class="pipeline">'+stages.map(([a,b,c],i)=>`<div class="stage"><small>${a}</small><b>${b}</b><p>${c}</p>${i<3?'<span class="arrow">→</span>':''}</div>`).join('')+'</div>';}
function roadmap(){return `<div class="roadmap">${[
 ['구조와 화면을 이해하기','탭별 목적·공개 데이터 계약·계산 방법과 미확인 사항을 문서화한다.','가이드 준비'],
 ['가격 기반 모듈 구현','공식 유니버스의 RS·모멘텀·ETF·퀀트·시장 역학을 계산한다.','연결'],
 ['거시·실적·위험 연결','FRED·ECOS·재무제표와 별도 컨센서스 빈티지를 표시한다.','연결'],
 ['예측과 의사결정 검증','시간순 기준모형과 로컬 기록을 연결했다. 원본 고급 모델의 동등성은 별도 검증한다.','기준모형']
 ].map(([a,b,c],i)=>`<article><div><h3>${a}</h3><p>${b}</p></div><span class="phase ${i===0?'done':''}">${c}</span></article>`).join('')}</div>`;}
function renderNav(){
 const q=document.querySelector('#search').value.trim().toLowerCase();
 let last='';
 const items=MODULES.filter(m=>!['overview','glance'].includes(m.id)&&(`${m.title} ${m.purpose}`).toLowerCase().includes(q));
 document.querySelector('#module-nav').innerHTML=items.map(m=>{
  const head=last!==m.group?`<div class="nav-group">${GROUPS[m.group]}</div>`:'';last=m.group;
  return head+`<a class="module-link" href="#${m.id}">${escapeHTML(m.title)}${built(m.id)?'<span class="running-mark">연결</span>':'<span class="pending-label">대기</span>'}</a>`;
 }).join('')||'<p>일치하는 화면이 없습니다.</p>';
 setActive();
}
function setActive(){const id=location.hash.slice(1)||'overview';document.querySelectorAll('.module-link,.toplink').forEach(a=>{const active=a.hash==='#'+id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});}
function renderCatalog(){
 const q=document.querySelector('#search').value.trim().toLowerCase();
 const items=MODULES.filter(m=>(group==='all'||m.group===group)&&(`${m.title} ${m.purpose}`).toLowerCase().includes(q));
 const box=document.querySelector('#catalog');if(!box)return;
 box.innerHTML=items.map(m=>`<a class="module-card ${built(m.id)?'built':''}" href="#${m.id}"><small>${GROUPS[m.group]} / ${escapeHTML(m.id.toUpperCase())}</small><h3>${escapeHTML(m.title)}</h3><p>${escapeHTML(m.purpose)}</p><div class="card-foot"><span>${statusLabel(m.id)}</span><span>↗</span></div></a>`).join('')||'<div class="empty">일치하는 화면이 없습니다.</div>';
 document.querySelectorAll('[data-group]').forEach(b=>{b.classList.toggle('active',b.dataset.group===group);b.setAttribute('aria-pressed',String(b.dataset.group===group));});
}
function overview(){
 content.innerHTML=`<p class="eyebrow">SANGSANGIN / INVESTMENT RESEARCH</p><div class="title-row"><div><h1>투자 리서치 대시보드</h1><p class="lead">국면·주도·실적·위험을 같은 근거 위에서 비교합니다.</p></div><span class="count-badge">가격 기준 ${BUILD_STATUS.as_of}</span></div>
 <div class="build-entry"><a href="#rs"><small>실데이터 · 부분 구현</small><strong>주간 상대강도 (RS) ↗</strong><span>한국·미국 페어 · 5년 z-score · 순위와 히트맵</span></a><a href="#momentum"><small>실데이터 · 부분 구현</small><strong>모멘텀 ↗</strong><span>국가·섹터·팩터·자산 · 3M/6M 누적 초과수익</span></a></div>
 <div class="metrics"><div class="metric"><b>${BUILD_STATUS.implemented}</b><span>계산·콘텐츠 연결 탭</span><small>완료 범위와 남은 항목은 탭마다 표시</small></div><div class="metric"><b>${BUILD_STATUS.price_series}</b><span>로컬 가격 시계열</span><small>거시 ${BUILD_STATUS.macro_series}계열 · 재무 ${BUILD_STATUS.financial_companies}기업</small></div><div class="metric"><b>${MODULES.length}</b><span>전체 화면 가이드</span><small>원자료 PC 보관 · 평일 08:00·18:00 갱신</small></div></div>
 <div class="summary-facts"><a href="#regime"><b>경제·시장 국면 ↗</b><p>한국은행 ECOS · 미국 FRED</p></a><a href="#growth"><b>성장 컨센서스 ↗</b><p>3D FY1/FY2 · 기준 ${BUILD_STATUS.consensus_as_of}</p></a><a href="#dynamics"><b>시장 역학 ↗</b><p>변동성 표면 · 위상공간 · 노출 조절</p></a><a href="#quant"><b>퀀트 전략 ↗</b><p>5개 선별 화면 · 가격과 거래량</p></a><a href="#ml"><b>예측 검증 ↗</b><p>시간순 OOS · 학습 타깃 시차</p></a><a href="#etfmon"><b>ETF 모니터 ↗</b><p>9개 분류 · 분배금·수익률·현금흐름</p></a></div>
 <div id="overview-state"><p class="quiet">거시·시장 좌표를 읽는 중…</p></div><div class="refresh-status" id="refresh-status">정기 갱신: 평일 08:00·18:00 (한국시간) · PC와 Codex 앱 실행 필요 · 수집→계산→검증→게시</div><div class="section-head"><h2>전체 탭</h2><span>구현 상태와 문서를 확인하세요</span></div>
 <div class="group-filter" aria-label="화면 분류">${[['all','전체'],['special','플랫폼'],['regime','국면'],['momentum','주도'],['context','맥락'],['opportunity','기회']].map(([k,t])=>`<button type="button" data-group="${k}">${t}</button>`).join('')}</div><div id="catalog" class="catalog"></div>
 <div class="section-head"><h2>데이터 기준</h2></div><p class="quiet">한국 대형주는 KRX 공식 구성목록, 미국은 IVV 공시 주식과 GICS 분류를 사용합니다. 가격·경제지표 관측일과 컨센서스 빈티지는 다를 수 있으며 화면에 구분합니다. 비공개 원본 모델을 복제했다고 주장하지 않습니다.</p>`;
 OverviewViews.mount(document.querySelector('#overview-state'));
 fetch('data/refresh.json').then(r=>r.ok?r.json():null).then(r=>{const box=document.querySelector('#refresh-status');if(box&&r)box.textContent='정기 갱신: 평일08:00·18:00 · 마지막 검증 '+r.completed_at+' · 가격 기준 '+r.as_of+' · 수집·계산·검증 통과본';}).catch(()=>{});
 content.querySelectorAll('[data-group]').forEach(b=>b.addEventListener('click',()=>{group=b.dataset.group;renderCatalog();}));renderCatalog();
}
function glance(){
 content.innerHTML=`<p class="eyebrow">AT A GLANCE</p><h1>데이터에서 판단까지</h1><p class="lead">수집, 계산, 설명, 화면을 나누면 각 결과의 근거를 확인하고 같은 조건으로 다시 계산할 수 있습니다.</p>${pipeline()}
 <div class="section-head"><h2>플랫폼의 기본 구조</h2></div><div class="flow"><div><b>데이터 수집</b><small>제공처 · 발표일 · 단위</small></div><div><b>분석 모듈</b><small>지표 · 룰 · 모델</small></div><div><b>스냅샷 발행</b><small>JSON · 차트 · 버전</small></div><div><b>리서치 화면</b><small>비교 · 근거 · 판단 기록</small></div></div>
 <div class="detail-grid"><section class="panel"><h2>구현 원칙</h2><ol class="steps"><li>가격·거시·재무의 데이터 계약과 단위를 먼저 확정합니다.</li><li>관측일과 이용 가능일을 구분하고 최신 수정 빈티지의 한계를 표시합니다.</li><li>공식 구성종목과 분류, 데이터 출처, 코드 버전을 결과에 연결합니다.</li><li>예측은 시간순으로 학습·평가하고 실패와 관측 수를 함께 기록합니다.</li></ol></section><section class="panel"><h2>현재 구현 범위</h2><p>${BUILD_STATUS.implemented}개 분석·콘텐츠 탭, 가격 ${BUILD_STATUS.price_series}개, 거시 ${BUILD_STATUS.macro_series}개 계열을 연결했습니다. 화면은 PC에서 저장한 계산 결과를 읽으며 수집·검증·게시 파이프라인은 평일08:00·18:00에 실행합니다.</p><div class="quiet">원본과 축·기간·패널 구조를 대조합니다. 공개되지 않은 모델, 교역·위성·개인 기록은 탭의 남은 항목에 표시합니다. 기준모형을 원본 엔진과 같은 모델로 표시하지 않습니다.</div></section></div>
 <p class="quiet">가격 품질: KRX 공식값으로 ${BUILD_STATUS.price_quality?.corrected||0}개 관측을 보정하고, 정렬이 불가능한 ${BUILD_STATUS.price_quality?.quarantined||0}개 관측을 제외했습니다. 원자료·보정 해시는 별도 보존합니다.</p><div class="section-head"><h2>데이터 소스</h2></div><div class="source-list">${['KRX · 구성종목·업종','iShares · 미국 대형주 공시','Yahoo Finance · 가격·재무·EPS 추정','FRED · 미국 거시·EPU','ECOS · 한국 거시','로컬 QuantiWise · 국내 컨센서스','CFTC · 주간 선물 포지션','공식 기관·BBC·DW RSS · 뉴스 제목','Natural Earth · 지도 경계'].map(t=>`<span>${t}</span>`).join('')}</div><p class="quiet">원자료와 수집 이력은 PC에 보관하고, GitHub에는 계산 코드·문서·차트용 결과를 게시합니다. 기록 화면의 개인 메모는 브라우저에만 저장됩니다.</p><p><a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/DATA_DEFINITIONS.md">공식 정의·단위·시차 문서 ↗</a> · <a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/IMPLEMENTATION_STATUS.md">탭별 구현 현황 ↗</a> · <a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/SUBVIEWS.md">세부 화면 연결 현황 ↗</a> · <a href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/UPDATE_PIPELINE.md">갱신 파이프라인 ↗</a></p>
 <div class="section-head"><h2>구현 순서</h2></div>${roadmap()}`;
}
function detail(m){
 content.innerHTML=`<p class="eyebrow">${GROUPS[m.group]} / ${escapeHTML(m.id.toUpperCase())}</p><div class="title-row"><div><h1>${escapeHTML(m.title)}</h1><p class="lead">${escapeHTML(m.purpose)}</p></div><span class="count-badge">구현 가이드</span></div>
 <div class="detail-grid"><section class="panel"><h2>어떻게 만들면 되는가</h2><ol class="steps">${m.build.map(s=>`<li>${escapeHTML(s)}</li>`).join('')}</ol><a class="method-link" href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/modules/${m.id}.md">Markdown 문서 ↗</a></section><section class="panel"><h2>검증할 것</h2><ul class="checklist">${m.checks.map(s=>`<li>${escapeHTML(s)}</li>`).join('')}</ul><div class="quiet"><h3>확인이 더 필요한 부분</h3>${escapeHTML(m.gap)}</div></section></div><div class="intro-note">공개된 화면 구조와 설명을 바탕으로 한 재작성 가이드입니다. 투자 신호의 실제 성능을 검증한 결과는 아닙니다.</div>`;
}
function render(){
 PriceDashboard.cancel();ResearchDashboard.cancel();OverviewViews.cancel();
 const id=location.hash.slice(1)||'overview';const m=MODULES.find(x=>x.id===id);
 if(!m){content.innerHTML='<h1>화면을 찾을 수 없습니다.</h1><a class="method-link" href="#overview">전체 보기</a>';return;}
 document.querySelector('#breadcrumb').textContent=id.toUpperCase();document.title=m.title+' · 상상인 투자 리서치';
 if(id==='overview')overview();else if(id==='glance')glance();else if(['rs','momentum'].includes(id))PriceDashboard.render(content,m);else if(built(id))ResearchDashboard.render(content,m);else detail(m);setActive();
}
document.querySelector('#search').addEventListener('input',()=>{renderNav();renderCatalog();});
document.querySelector('.skip').addEventListener('click',event=>{event.preventDefault();content.focus();content.scrollIntoView();});
window.addEventListener('hashchange',()=>{render();document.querySelector('#content').focus({preventScroll:true});window.scrollTo(0,0);});
renderNav();render();
