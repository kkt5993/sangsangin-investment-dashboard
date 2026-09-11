/* Topic queries and local title matches retain separate evidence and date bases. */
(function(root){
 'use strict';
 const E=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const kinds={theme:'테마',country:'국가',geo:'지정학',policy:'정책'},N=v=>Number.isFinite(v)?v.toFixed(3):'—';
 function link(url,label){try{const u=new URL(url);if(u.protocol==='https:'&&!u.username&&!u.password)return `<a href="${E(u.href)}" target="_blank" rel="noopener noreferrer">${E(label)} ↗</a>`;}catch{}return E(label);}
 function articles(rows){return rows.map(a=>`<li data-topic-article="${E(a.id)}">${link(a.url,a.title)}<br><small>${E(a.time_basis)} ${E(a.time)} · ${E(a.publisher||a.source)}${a.matched_terms?'<br>제목 일치: '+E(a.matched_terms.join(' · ')):''}</small>${root.CompanyNews.tone(a)}</li>`).join('')||'<li>선택한 표본과 기간에 관측한 기사가 없습니다.</li>';}
 function detail(topic,provider,section){
  const data=topic.sets[provider],local=provider==='local',ready=local||topic.data_available,t=data.tone_summary;
  const status=local?'기존 기업·정책 RSS 제목에서 찾은 표본':topic.available?'최근 GDELT 검색 관측':topic.data_available?'이전 검색 자료 보존 · 현재 조회 미확인':'GDELT 검색 결과 미확보';
  return `<article class="panel" data-topic-detail="${E(topic.id)}"><h3>${E(topic.name)} · ${E(kinds[topic.kind])}</h3><p>${status} · ${E(section.start)} ~ ${E(section.end)} UTC<br>${ready?'관측 '+data.count+'건':'관측 수 —'}${!local&&topic.capped?' · 제공처 반환 상한250개 도달, 전체 건수 아님':''}</p>${!local?`<p class="quiet">성공 조회 ${E(topic.retrieved_at||'미확보')} · 최근 시도 ${E(topic.checked_at||section.collection.attempted_at||'미확보')}<br>수집 상태 ${E(topic.error||section.collection.status||'미조회')} · 실패 시 이전 자료를 보존합니다.</p>`:''}<details><summary>검색식·일치 기준</summary><p>GDELT 검색: <code>${E(topic.query)}</code></p><p>기존 기사: 각 괄호에서 하나 이상 제목 일치 · ${E(topic.title_groups.map(g=>'('+g.join(' 또는 ')+')').join(' 그리고 '))}</p><p>본문 일치 여부나 사실성을 판정하지 않습니다. 두 표본의 기사 수를 합산하지 않습니다.</p></details><p data-topic-tone>${t.available?'제목 톤 '+N(t.score)+' · 중복 제목 제외 '+t.classified+'/'+t.total+'개 분류':'제목 톤 미산출'} · 매매 신호 가산 없음</p>${ready?'<ol>'+articles(data.items.slice(0,5))+'</ol>':'<p>검색 결과를 아직 확보하지 못했습니다.</p>'}${data.items.length>5?`<details data-topic-more><summary>나머지 ${data.items.length-5}개 기사</summary><ol start="6">${articles(data.items.slice(5))}</ol></details>`:''}</article>`;
 }
 function render(s,i){return `<div data-topic-news="${i}"><p class="scope-note">${E(s.note)}</p><div class="analysis-controls"><label>주제·기사 검색 <input data-topic-search type="search"></label><label>분류 <select data-topic-kind><option value="all">전체</option>${Object.entries(kinds).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>표본 <select data-topic-provider><option value="local">기존 RSS 제목 일치</option><option value="gdelt">GDELT 주제 검색</option></select></label></div><p data-topic-count role="status"></p><div class="table-scroll"><table class="data-table"><thead><tr><th>주제</th><th>분류</th><th>기존 제목 일치</th><th>GDELT 검색 관측</th></tr></thead><tbody data-topic-rows></tbody></table></div><div data-topic-output></div></div>`;}
 function bind(container,snapshot){container.querySelectorAll('[data-topic-news]').forEach(box=>{
  const s=snapshot.sections[+box.dataset.topicNews],search=box.querySelector('[data-topic-search]'),kind=box.querySelector('[data-topic-kind]'),provider=box.querySelector('[data-topic-provider]'),output=box.querySelector('[data-topic-output]');let selected=s.items[0]?.id;
  function draw(){const q=search.value.trim().toLocaleLowerCase(),items=s.items.filter(r=>(kind.value==='all'||r.kind===kind.value)&&[r.name,r.query,...Object.values(r.sets).flatMap(x=>x.items.map(a=>a.title))].join(' ').toLocaleLowerCase().includes(q));if(!items.some(r=>r.id===selected))selected=items[0]?.id;
   box.querySelector('[data-topic-count]').textContent=`${items.length}/${s.items.length}개 주제 · 검색 결과 미확보와 관측0건을 구분합니다.`;
   box.querySelector('[data-topic-rows]').innerHTML=items.map(r=>`<tr><td><button data-topic-select="${E(r.id)}" aria-pressed="${r.id===selected}">${E(r.name)}</button></td><td>${E(kinds[r.kind])}</td><td>${r.sets.local.count}</td><td>${r.data_available?r.sets.gdelt.count+(r.available?'':' · 이전 자료'):'— 미확보'}</td></tr>`).join('');
   output.innerHTML=items.length?detail(items.find(r=>r.id===selected),provider.value,s):'<p>검색 조건에 해당하는 주제가 없습니다.</p>';
  }
  search.addEventListener('input',draw);kind.addEventListener('change',draw);provider.addEventListener('change',draw);box.querySelector('[data-topic-rows]').addEventListener('click',e=>{const b=e.target.closest('[data-topic-select]');if(b){selected=b.dataset.topicSelect;draw();}});draw();
 });}
 root.TopicNews={render,bind,detail,articles};
})(typeof window==='undefined'?globalThis:window);
