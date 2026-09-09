'use strict';
const GROUPS={special:'PLATFORM',regime:'REGIME',momentum:'MOMENTUM',context:'CONTEXT',opportunity:'OPPORTUNITY',other:'INTERNAL'};
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const content=document.querySelector('#content');
let group='all';
const stages=[['01 / REGIME','국면을 읽다','성장·물가·금리·유동성'],['02 / MOMENTUM','주도를 찾다','상대강도·실적·로테이션'],['03 / CONTEXT','맥락을 확인하다','자산 간 관계·위험·쏠림'],['04 / OPPORTUNITY','판단을 기록하다','종목 발굴·전략·검증']];
function pipeline(){return '<div class="pipeline">'+stages.map(([a,b,c],i)=>`<div class="stage"><small>${a}</small><b>${b}</b><p>${c}</p>${i<3?'<span class="arrow">→</span>':''}</div>`).join('')+'</div>';}
function roadmap(){return `<div class="roadmap">${[
 ['구조와 화면을 이해하기','탭별 목적·공개 데이터 계약·계산 방법과 미확인 사항을 문서화한다.','가이드 준비'],
 ['가격 기반 모듈 구현','RS·모멘텀·ETF부터 공통 데이터 패널과 계산 검증을 만든다.','다음 단계'],
 ['거시·실적·위험 연결','발표일과 단위, 데이터 수정 이력을 보존하는 수집기를 구성한다.','계획'],
 ['예측과 의사결정 검증','작은 기준 모델에서 시작해 시간순 평가와 근거를 갖춘 팀 원장으로 확장한다.','계획']
 ].map(([a,b,c],i)=>`<article><div><h3>${a}</h3><p>${b}</p></div><span class="phase ${i===0?'done':''}">${c}</span></article>`).join('')}</div>`;}
function renderNav(){
 const q=document.querySelector('#search').value.trim().toLowerCase();
 let last='';
 const items=MODULES.filter(m=>!['overview','glance'].includes(m.id)&&(`${m.title} ${m.purpose}`).toLowerCase().includes(q));
 document.querySelector('#module-nav').innerHTML=items.map(m=>{
  const head=last!==m.group?`<div class="nav-group">${GROUPS[m.group]}</div>`:'';last=m.group;
  return head+`<a class="module-link" href="#${m.id}">${escapeHTML(m.title)}</a>`;
 }).join('')||'<p>일치하는 화면이 없습니다.</p>';
 setActive();
}
function setActive(){const id=location.hash.slice(1)||'overview';document.querySelectorAll('.module-link,.toplink').forEach(a=>{const active=a.hash==='#'+id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});}
function renderCatalog(){
 const q=document.querySelector('#search').value.trim().toLowerCase();
 const items=MODULES.filter(m=>(group==='all'||m.group===group)&&(`${m.title} ${m.purpose}`).toLowerCase().includes(q));
 const box=document.querySelector('#catalog');if(!box)return;
 box.innerHTML=items.map(m=>`<a class="module-card" href="#${m.id}"><small>${GROUPS[m.group]} / ${escapeHTML(m.id.toUpperCase())}</small><h3>${escapeHTML(m.title)}</h3><p>${escapeHTML(m.purpose)}</p><div class="card-foot"><span>구현 가이드</span><span>↗</span></div></a>`).join('')||'<div class="empty">일치하는 화면이 없습니다.</div>';
 document.querySelectorAll('[data-group]').forEach(b=>{b.classList.toggle('active',b.dataset.group===group);b.setAttribute('aria-pressed',String(b.dataset.group===group));});
}
function overview(){
 content.innerHTML=`<p class="eyebrow">BUILDING OUR RESEARCH SYSTEM</p><div class="title-row"><div><h1>투자 리서치, 구조부터 시작합니다.</h1><p class="lead">국면을 읽고, 주도를 찾고, 근거를 확인하는 팀의 공통 도구.<br>화면별 설계와 구현 순서를 한곳에서 살펴봅니다.</p></div><span class="count-badge">IMPLEMENTATION GUIDE</span></div>
 <div class="metrics"><div class="metric"><b>26</b><span>화면 가이드</span><small>목적 · 구조 · 검증</small></div><div class="metric"><b>4</b><span>투자 프로세스</span><small>국면에서 기회까지</small></div><div class="metric"><b>01</b><span>현재 단계</span><small>학습과 설계</small></div></div>
 ${pipeline()}<div class="section-head"><h2>화면별 구현 가이드</h2><span>모듈을 선택해 만드는 방법을 확인하세요</span></div>
 <div class="group-filter" aria-label="화면 분류">${[['all','전체'],['special','플랫폼'],['regime','국면'],['momentum','주도'],['context','맥락'],['opportunity','기회']].map(([k,t])=>`<button type="button" data-group="${k}">${t}</button>`).join('')}</div><div id="catalog" class="catalog"></div>
 <div class="section-head"><h2>구현 순서</h2></div>${roadmap()}`;
 content.querySelectorAll('[data-group]').forEach(b=>b.addEventListener('click',()=>{group=b.dataset.group;renderCatalog();}));renderCatalog();
}
function glance(){
 content.innerHTML=`<p class="eyebrow">AT A GLANCE</p><h1>데이터에서 판단까지</h1><p class="lead">수집, 계산, 설명, 화면을 나누면 각 결과의 근거를 확인하고 같은 조건으로 다시 계산할 수 있습니다.</p>${pipeline()}
 <div class="section-head"><h2>플랫폼의 기본 구조</h2></div><div class="flow"><div><b>데이터 수집</b><small>제공처 · 발표일 · 단위</small></div><div><b>분석 모듈</b><small>지표 · 룰 · 모델</small></div><div><b>스냅샷 발행</b><small>JSON · 차트 · 버전</small></div><div><b>리서치 화면</b><small>비교 · 근거 · 판단 기록</small></div></div>
 <div class="detail-grid"><section class="panel"><h2>구현 원칙</h2><ol class="steps"><li>가격 기반 모듈부터 작게 완성하고, 동일한 데이터 계약 위에 거시·실적·모델을 추가합니다.</li><li>관측일과 실제 이용 가능일을 구분합니다. 수정된 데이터로 과거 예측을 다시 쓴 결과는 별도로 표시합니다.</li><li>화면의 수치를 계산식, 데이터 출처, 모델 버전까지 추적할 수 있게 만듭니다.</li><li>모델 선택과 최종 평가 구간을 분리하고 거래비용과 예측 실패를 함께 기록합니다.</li></ol></section><section class="panel"><h2>현재 구현 범위</h2><p>이 페이지는 화면별 구현 가이드입니다. 실시간 데이터 수집과 모델 실행은 다음 구현 단계입니다.</p><div class="quiet">ARAGORN-INVESTIUM의 공개 설계를 학습의 출발점으로 삼아 팀의 코드와 검증 체계를 작성합니다. 원본 계산 서버와 학습 모델은 공유되지 않았습니다.</div></section></div>
 <div class="section-head"><h2>학습 설계에 등장하는 데이터 소스</h2></div><div class="source-list">${['FRED','ECOS','Yahoo Finance','FinanceDataReader','Naver Finance','SEC EDGAR','FMP','CBOE','UN Comtrade','EPU / GPR','뉴스 RSS'].map(t=>`<span>${t}</span>`).join('')}</div><p class="quiet">원본이 안내하는 제공처 목록입니다. 실제 사용 시 지표별 접근 조건·제공 범위·단위를 확인하며, 현재 페이지에는 수집기가 연결되어 있지 않습니다.</p>
 <div class="section-head"><h2>구현 순서</h2></div>${roadmap()}`;
}
function detail(m){
 content.innerHTML=`<p class="eyebrow">${GROUPS[m.group]} / ${escapeHTML(m.id.toUpperCase())}</p><div class="title-row"><div><h1>${escapeHTML(m.title)}</h1><p class="lead">${escapeHTML(m.purpose)}</p></div><span class="count-badge">구현 가이드</span></div>
 <div class="detail-grid"><section class="panel"><h2>어떻게 만들면 되는가</h2><ol class="steps">${m.build.map(s=>`<li>${escapeHTML(s)}</li>`).join('')}</ol><a class="method-link" href="https://github.com/kkt5993/sangsangin-investment-dashboard/blob/main/research/modules/${m.id}.md">Markdown 문서 ↗</a></section><section class="panel"><h2>검증할 것</h2><ul class="checklist">${m.checks.map(s=>`<li>${escapeHTML(s)}</li>`).join('')}</ul><div class="quiet"><h3>확인이 더 필요한 부분</h3>${escapeHTML(m.gap)}</div></section></div><div class="intro-note">공개된 화면 구조와 설명을 바탕으로 한 재작성 가이드입니다. 투자 신호의 실제 성능을 검증한 결과는 아닙니다.</div>`;
}
function render(){
 const id=location.hash.slice(1)||'overview';const m=MODULES.find(x=>x.id===id);
 if(!m){content.innerHTML='<h1>화면을 찾을 수 없습니다.</h1><a class="method-link" href="#overview">전체 보기</a>';return;}
 document.querySelector('#breadcrumb').textContent=id.toUpperCase();document.title=m.title+' · 상상인 투자 리서치';
 if(id==='overview')overview();else if(id==='glance')glance();else detail(m);setActive();
}
document.querySelector('#search').addEventListener('input',()=>{renderNav();renderCatalog();});
document.querySelector('.skip').addEventListener('click',event=>{event.preventDefault();content.focus();content.scrollIntoView();});
window.addEventListener('hashchange',()=>{render();document.querySelector('#content').focus({preventScroll:true});window.scrollTo(0,0);});
renderNav();render();
