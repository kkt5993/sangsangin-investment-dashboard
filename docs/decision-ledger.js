/* Local decision records and dated entity cards. No orders or remote writes. */
(function(root){
 'use strict';
 const KEY='sangsangin-decisions-v2',LEGACY='sangsangin-journal-v1-dragonglass';
 const E=v=>root.ResearchCharts.esc(v??''),N=v=>typeof v==='number'&&Number.isFinite(v)?root.AnalysisCharts.n(v):'—';
 const now=()=>new Date().toISOString(),uid=()=>root.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
 const fail=m=>{throw Error(m);};
 const date=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))&&/^\d{4}-\d\d-\d\dT/.test(v);
 function text(v,max,required=false){if(typeof v!=='string'||v.length>max||(required&&!v.trim()))fail('문자 필드의 길이·형식이 올바르지 않습니다.');return v.trim();}
 function numeric(v,min,max){if(v===''||v===null||v===undefined)return null;const n=typeof v==='number'?v:typeof v==='string'?Number(v):NaN;if(!Number.isFinite(n)||n<min||n>max)fail('숫자 입력 범위를 확인하세요.');return n;}
 function validate(r){
  if(!r||typeof r!=='object'||Array.isArray(r))fail('결정 기록 형식 오류');
  const out={};for(const [k,n,required] of [['id',100,true],['object_id',120,false],['name',200,true],['thesis',12000,false],['catalyst',2000,false],['invalidate',2000,false]])out[k]=text(r[k],n,required);
  if(!['Long','Short',null].includes(r.direction)||!['제안','실행','청산'].includes(r.status)||!['단기','중기','장기',null].includes(r.horizon))fail('방향·시계·상태가 올바르지 않습니다.');
  Object.assign(out,{direction:r.direction,status:r.status,horizon:r.horizon,conviction:numeric(r.conviction,1,5),size:numeric(r.size,0,1000)});
  if(out.conviction!==null&&!Number.isInteger(out.conviction))fail('확신도는 1~5 정수입니다.');
  for(const k of ['created_at','updated_at']){if(!date(r[k]))fail('기록 시각이 올바르지 않습니다.');out[k]=r[k];}
  for(const k of ['closed_at','deleted_at']){if(r[k]!==null&&!date(r[k]))fail('상태 시각 오류');out[k]=r[k];}
  if(!Array.isArray(r.history)||r.history.length>50)fail('변경 이력 형식 오류');
  out.history=r.history.map(a=>{if(!date(a.at))fail('변경 시각 오류');return {at:a.at,action:text(a.action,60,true)};});
  out.upside=numeric(r.upside,0,1000);out.downside=numeric(r.downside,0,1000);out.probability=numeric(r.probability,0,100);
  return out;
 }
 function decode(raw){
  const a=JSON.parse(raw);if(!a||a.version!==2||!Array.isArray(a.entries)||typeof a.revision!=='string')fail('지원하지 않는 원장 형식입니다.');
  const entries=a.entries.map(validate);if(new Set(entries.map(a=>a.id)).size!==entries.length)fail('중복된 결정 ID가 있습니다.');return {version:2,revision:a.revision,entries};
 }
 function legacyRecords(a){
  if(!Array.isArray(a))fail('이전 메모 형식을 확인하세요.');
  return a.map(r=>{const t=now();return validate({id:uid(),object_id:'',name:text(r.title,160,true),thesis:text(r.body,12000,true),catalyst:'',invalidate:'',direction:null,conviction:null,horizon:null,size:null,status:'제안',created_at:date(r.date)?r.date:t,updated_at:t,closed_at:null,deleted_at:null,history:[{at:t,action:'이전 메모 가져오기'}],upside:null,downside:null,probability:null});});
 }
 function store(storage){
  let original=null,book;
  const reload=()=>{original=storage.getItem(KEY);book=original===null?{version:2,revision:'',entries:[]}:decode(original);return book.entries;};reload();
  const write=entries=>{
   const next={version:2,revision:uid(),entries:entries.map(validate)},raw=JSON.stringify(next);
   if(storage.getItem(KEY)!==original)fail('다른 창에서 원장이 바뀌었습니다. 새로 읽은 뒤 다시 저장하세요.');
   storage.setItem(KEY,raw);original=raw;book=next;return book.entries;
  };
  const update=(id,fn)=>{const a=book.entries.find(r=>r.id===id);if(!a)fail('결정을 찾을 수 없습니다.');const t=now(),next=fn({...a},t);return write(book.entries.map(r=>r.id===id?next:r));};
  const history=(r,t,action)=>({...r,updated_at:t,history:[...r.history,{at:t,action}].slice(-50)});
  return {
   entries:()=>book.entries.map(r=>structuredClone(r)),reload,
   save(input,entity,id=null){
    if(!entity||!input.thesis?.trim())fail('대상 종목과 투자 가설을 입력하세요.');
    const fields={object_id:entity.id,name:entity.name,thesis:input.thesis,catalyst:input.catalyst,invalidate:input.invalidate,direction:input.direction,conviction:input.conviction,horizon:input.horizon,size:input.size,upside:input.upside,downside:input.downside,probability:input.probability};
    if(id)return update(id,(r,t)=>history({...r,...fields},t,'내용 수정'));
    const t=now();return write([{...fields,id:uid(),status:'제안',created_at:t,updated_at:t,closed_at:null,deleted_at:null,history:[{at:t,action:'제안 생성'}]},...book.entries]);
   },
   action(id,action){return update(id,(r,t)=>{
    const targets={activate:'실행',close:'청산',reopen:'실행'};
    if(action==='activate'&&r.status!=='제안'||action==='close'&&r.status==='청산'||action==='reopen'&&r.status!=='청산')fail('현재 상태에서 실행할 수 없는 변경입니다.');
    if(action==='delete')r.deleted_at=t;else if(action==='restore')r.deleted_at=null;else if(targets[action]){r.status=targets[action];r.closed_at=r.status==='청산'?t:null;}else fail('지원하지 않는 동작입니다.');
    if(r.status==='실행'&&(!r.direction||!r.object_id))fail('먼저 종목과 방향을 지정하세요.');
    return history(r,t,{activate:'실행 상태 기록',close:'청산 상태 기록',reopen:'실행 재개',delete:'휴지통 이동',restore:'복원'}[action]);
   });},
   import(raw){
    const parsed=JSON.parse(raw),isLegacy=Array.isArray(parsed),incoming=isLegacy?legacyRecords(parsed):decode(raw).entries;
    const next=book.entries.map(r=>({...r}));let added=0;
    for(let r of incoming){if(isLegacy&&next.some(a=>a.name===r.name&&a.thesis===r.thesis&&a.created_at===r.created_at))continue;const existing=next.find(a=>a.id===r.id);if(existing&&JSON.stringify(existing)===JSON.stringify(r))continue;if(existing)r={...r,id:uid(),history:[...r.history,{at:now(),action:'ID 충돌 사본 가져오기'}].slice(-50)};next.push(r);added++;}
    write(next);return added;
   },
   export:()=>JSON.stringify(book,null,2)
  };
 }
 function portfolio(entries,entities,kr=-10,us=-10){
  const active=entries.filter(r=>r.status==='실행'&&!r.deleted_at),lookup=new Map(entities.map(e=>[e.id,e]));
  let gross=0,net=0,known=0,unknown=0,partial=0;const sectors=new Map(),rows=[];
  for(const r of active){const e=lookup.get(r.object_id),sign=r.direction==='Long'?1:r.direction==='Short'?-1:null;
   if(r.size===null||sign===null){unknown++;rows.push({name:r.name,contribution:null,size:r.size});continue;}
   gross+=r.size;net+=sign*r.size;const sector=e?e.market+' · '+e.sector:'현재 유니버스 밖';sectors.set(sector,(sectors.get(sector)||0)+r.size);
   const beta=e?.sensitivity?.beta,shock=e?.market==='KR'?kr:us,valid=typeof beta==='number'&&Number.isFinite(beta)&&['KR','US'].includes(e?.market);
   const contribution=r.size===0?0:valid?sign*r.size*beta*shock/100:null;
   if(contribution===null)unknown++;else {known+=r.size;partial+=contribution;}
   rows.push({name:r.name,contribution,size:r.size,market:e?.market,beta:valid?beta:null});
  }
  return {active:active.length,gross,net,known,unknown,partial,total:unknown?null:partial,rows,sectors:[...sectors].sort((a,b)=>b[1]-a[1])};
 }
 function intelligence(r){const complete=[r.upside,r.downside,r.probability].every(v=>typeof v==='number'&&Number.isFinite(v));return {rr:r.downside>0&&r.upside!==null?r.upside/r.downside:null,ev:complete?r.upside*r.probability/100-r.downside*(1-r.probability/100):null,checks:[['투자 가설',!!r.thesis],['촉매',!!r.catalyst],['무효화 조건',!!r.invalidate],['확신도',r.conviction!==null],['비중',r.size!==null]]};}
 const stamp=t=>t?new Date(t).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',hour12:false})+' KST':'—';
 const button=(action,label,id)=>`<button type="button" data-decision-action="${action}" data-decision-id="${E(id)}">${E(label)}</button>`;
 const download=(raw,name)=>{const url=URL.createObjectURL(new Blob([raw],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 function shell(){return `<div data-decisions><p class="scope-note">투자 판단을 제안 → 실행 → 청산 상태로 기록합니다. 이 브라우저에만 저장되며 주문을 전송하지 않습니다. JSON 내보내기로 백업·이동할 수 있습니다.</p><output data-ledger-status role="status"></output><div data-ledger-body></div></div>`;}
 function entityShell(s){return `<div data-entities><p class="quiet">${s.entities.length}개 종목 · ${Object.entries(s.coverage).map(([k,v])=>E(k)+' '+v.available+'/'+v.expected+' (구성 '+E(v.membership_as_of)+')').join(' · ')}</p><div class="analysis-controls"><label>종목 검색 <input data-entity-search type="search" placeholder="종목명·코드·업종"></label><label>시장 <select data-entity-market><option value="all">전체</option><option>KR</option><option>US</option></select></label><label>종목 <select data-entity-select></select></label></div><div data-entity-body></div></div>`;}
 const fields=['object_id','direction','conviction','horizon','size','thesis','catalyst','invalidate','upside','downside','probability'];
 function form(r,entities){
  const input=(key,label,max=2000)=>`<label class="ledger-wide">${label}<textarea data-field="${key}" maxlength="${max}" rows="${key==='thesis'?4:2}">${E(r[key]||'')}</textarea></label>`;
  const number=(key,label,min,max)=>`<label>${label}<input data-field="${key}" type="number" min="${min}" max="${max}" step="any" value="${E(r[key]??'')}"></label>`;
  const select=(key,label,options)=>`<label>${label}<select data-field="${key}">${options.map(([v,t])=>`<option value="${E(v)}" ${String(r[key])===String(v)?'selected':''}>${E(t)}</option>`).join('')}</select></label>`;
  return `<section class="panel"><h3>${r.id?'결정 수정':'새 결정'}</h3><div class="ledger-fields">${select('object_id','대상 종목',[['','선택하세요'],...entities.map(e=>[e.id,e.name+' · '+e.symbol])])}${select('direction','방향',[['Long','Long'],['Short','Short']])}${select('conviction','확신도 · 주관적 1~5',[1,2,3,4,5].map(n=>[n,n]))}${select('horizon','투자 시계',[['단기','단기 · 1주~1개월'],['중기','중기 · 반기 이상'],['장기','장기 · 2년 이상']])}${number('size','계획·기록 비중 %',0,1000)}${input('thesis','투자 가설',12000)}${input('catalyst','촉매')}${input('invalidate','무효화 조건')}</div><details><summary>손익비·가정 기대값 입력</summary><p class="quiet">방향을 반영한 포지션 이익·손실을 양수로 입력하세요. 성공확률은 사용자의 가정이며 확신도를 확률로 자동 변환하지 않습니다.</p><div class="ledger-fields">${number('upside','성공 시 이익 %',0,1000)}${number('downside','실패 시 손실 %',0,1000)}${number('probability','가정 성공확률 %',0,100)}</div></details><div class="note-actions">${button('save','저장',r.id||'')}${button('cancel','닫기',r.id||'')}</div></section>`;
 }
 function card(r,entities,lab){const it=intelligence(r),exists=entities.some(e=>e.id===r.object_id);return `<article class="panel ledger-card"><div class="title-row"><h3>${E(r.name)}</h3><span class="count-badge">${E(r.direction||'방향 미지정')} · ${E(r.status)}</span></div><p>확신도 ${r.conviction===null?'미설정':E('●'.repeat(r.conviction)+'○'.repeat(5-r.conviction))} · ${E(r.horizon||'시계 미설정')} · 비중 ${N(r.size)}%</p><p class="note-body">${E(r.thesis)}</p><dl><dt>촉매</dt><dd>${E(r.catalyst||'미기록')}</dd><dt>무효화 조건</dt><dd>${E(r.invalidate||'미기록')}</dd></dl><div class="tags">${it.checks.map(([k,v])=>`<span>${v?'✓':'○'} ${E(k)}</span>`).join('')}</div>${it.rr!==null||it.ev!==null?`<p>입력 가정 손익비 ${N(it.rr)}배 · 기대값 ${N(it.ev)}% · 이익 ${N(r.upside)}% / 손실 ${N(r.downside)}% / 확률 ${N(r.probability)}%</p>`:''}${root.RelationViews?.decisionNotes(r,lab)||''}<small>생성 ${E(stamp(r.created_at))}<br>수정 ${E(stamp(r.updated_at))}${r.closed_at?'<br>청산 기록 '+E(stamp(r.closed_at)):''}</small><div class="note-actions">${r.deleted_at?button('restore','휴지통에서 복원',r.id):button('edit','수정',r.id)+(r.status==='제안'?button('activate','실행 상태로 기록',r.id):'')+(r.status==='청산'?button('reopen','실행 재개 기록',r.id):button('close','청산 상태로 기록',r.id))+(exists?button('entity','기업 상세',r.id):'')+button('delete','휴지통으로',r.id)}</div><details><summary>변경 이력 · 최근 ${r.history.length}건</summary><ul>${r.history.map(a=>`<li>${E(stamp(a.at))} · ${E(a.action)}</li>`).join('')}</ul></details></article>`;}
 const ui={filter:'all',q:'',draft:null,entity:'',kr:-10,us:-10};
 function bind(container,d,navigate,selection={}){
  const entities=d.sections.find(s=>s.type==='entities')?.entities||[],lab=d.sections.find(s=>s.type==='relationlab');
  let vault=null,storageError='';try{vault=store(root.localStorage);}catch(e){storageError=e.message;}
  container.querySelectorAll('[data-entities]').forEach(box=>{
   const search=box.querySelector('[data-entity-search]'),market=box.querySelector('[data-entity-market]'),select=box.querySelector('[data-entity-select]');
   const show=()=>{const e=entities.find(e=>e.id===select.value);if(!e){box.querySelector('[data-entity-body]').innerHTML='<p>검색 조건에 해당하는 종목이 없습니다.</p>';return;}ui.entity=e.id;const f=e.financial,b=e.sensitivity,linked=vault?vault.entries().filter(r=>!r.deleted_at&&r.object_id===e.id):[];
    box.querySelector('[data-entity-body]').innerHTML=`<article class="panel"><div class="title-row"><h2>${E(e.name)} · ${E(e.symbol)}</h2><button data-entity-decision>이 종목으로 결정 기록</button></div><p>${E(e.market)} → ${E(e.sector)} → ${E(e.name)} · ${e.rs_universe==='추가 사업 관찰'?'사업 관찰 추가 · 공식 업종 미확보':'공식 업종 소속'}</p><div class="kpi-grid">${['1W %','1M %','3M %','YTD %','1Y %'].map((k,i)=>`<div class="kpi"><small>${k}</small><strong>${N(e.returns[i])}</strong></div>`).join('')}</div><p>RS ${N(e.rs)} (${E(e.rs_universe)} 단면) · RSI14 ${N(e.rsi)} · 52주 고점 대비 ${N(e.high52)}% · 가격 ${E(e.date)}</p>${root.AnalysisCharts.line({title:e.name+' · 3개월 조정가격',left:'시작=100',date_format:'day',series:[{name:e.name,axis:'left',points:e.curve}]})}<p class="quiet">64거래일에서 최대14개 시점을 표시했습니다. 배당·분할 조정가격 기준입니다.</p>${root.RelationViews?.entityNotes(e.id,lab)||''}${root.GuruViews?.entityNotes(e)||''}${root.AttentionViews?.entityNotes(e)||''}<h3>시장 민감도</h3><p>${b?'Beta '+N(b.beta)+' · R² '+N(b.r2)+' · '+b.observations+'개 공통 일 수익률 ('+E(b.start)+' ~ '+E(b.end)+')':'공통 관측 200개 이상 또는 벤치마크 변동 부족으로 미산출'} · 벤치마크 ${E(e.benchmark)}</p><h3>재무·추정 관측</h3>${f?`<p>최근 연간 순이익 ${N(f.net_income)} ${E(f.financial_currency)} · 결산일 ${E(f.report_date)}<br>영업이익률 ${N(f.margin)}% · FY1/FY2 EPS ${N(f.eps1)} / ${N(f.eps2)} ${E(f.estimate_currency)}<br>재무 수집 ${E(f.financial_as_of)}</p>`:'<p>현재 재무 수집 범위에 포함되지 않습니다.</p>'}<h3>예정 촉매 · 가격 기준일 다음90일</h3><p>${e.upcoming.length?e.upcoming.map(t=>'실적 예정 '+E(stamp(t))).join('<br>'):'확인된 향후90일 실적 일정이 없습니다.'}</p><small>일정 수집 ${E(stamp(e.events_retrieved))} · 제공처 예정일은 변경될 수 있습니다.</small><h3>연결된 결정 ${linked.length}건</h3>${linked.map(r=>`<p>${E(r.direction||'미지정')} · ${E(r.status)} · ${N(r.size)}% · ${E(r.thesis)}</p>`).join('')}<p><a href="https://finance.yahoo.com/quote/${encodeURIComponent(e.symbol)}/" target="_blank" rel="noopener noreferrer">시세·재무 제공처 ↗</a> · ${e.rs_universe==='추가 사업 관찰'?'공식 유니버스 외 추가 관찰':'업종은 공식 KRX/IVV 구성자료'}</p></article>`;
    box.querySelector('[data-entity-relation]')?.addEventListener('click',()=>navigate('관계 지도',{relationNode:e.id}));
    box.querySelector('[data-entity-decision]').addEventListener('click',()=>navigate('결정 원장',{decisionObject:e.id}));
   };
   const filter=()=>{const q=search.value.trim().toLocaleLowerCase(),list=entities.filter(e=>(market.value==='all'||e.market===market.value)&&(e.name+' '+e.symbol+' '+e.sector).toLocaleLowerCase().includes(q));select.innerHTML=list.map(e=>`<option value="${E(e.id)}">${E(e.name)} · ${E(e.symbol)}</option>`).join('');select.value=list.some(e=>e.id===ui.entity)?ui.entity:list[0]?.id||'';show();};
   ui.entity=selection.entity||ui.entity;search.addEventListener('input',filter);market.addEventListener('change',filter);select.addEventListener('change',show);filter();
  });
  container.querySelectorAll('[data-decisions]').forEach(box=>{
   const status=msg=>box.querySelector('[data-ledger-status]').textContent=msg,body=box.querySelector('[data-ledger-body]');
   if(!vault){body.innerHTML='<p>원장을 읽지 못했습니다. 기존 저장 내용은 변경하지 않았습니다.</p><button data-raw-export>기존 원문 JSON 내보내기</button>';status(storageError);body.querySelector('[data-raw-export]').addEventListener('click',()=>{try{download(root.localStorage.getItem(KEY)||'{}','decisions-recovery.json');}catch(e){status(e.message);}});return;}
   const blank=object_id=>({object_id:object_id||'',direction:'Long',conviction:3,horizon:'중기',size:null,thesis:'',catalyst:'',invalidate:'',upside:null,downside:null,probability:null});
   if(selection.decisionObject){if(ui.draft)status('작성 중인 결정이 있습니다. 저장하거나 닫은 뒤 새 결정을 추가하세요.');else ui.draft=blank(selection.decisionObject);delete selection.decisionObject;}
   const repaint=()=>{
    const entries=vault.entries(),open=entries.filter(r=>!r.deleted_at),p=portfolio(entries,entities,ui.kr,ui.us);
    const shown=entries.filter(r=>(ui.filter==='trash'?!!r.deleted_at:!r.deleted_at&&(ui.filter==='all'||r.status===ui.filter)));
    const legacy=root.localStorage.getItem(LEGACY);
    body.innerHTML=`<div class="note-actions">${button('new','새 결정','')}${button('reload','다시 읽기','')}${button('export','JSON 내보내기','')}<label class="import-label">JSON 가져오기 <input data-ledger-import type="file" accept="application/json,.json"></label></div><div class="kpi-grid">${['제안','실행','청산'].map(s=>`<div class="kpi"><small>${s}</small><strong>${open.filter(r=>r.status===s).length}</strong></div>`).join('')}</div><section class="panel"><h3>실행 기록 포트폴리오 · ${p.active}건</h3><p>확인 비중 총합 ${N(p.gross)}% · 순비중 ${N(p.net)}% · Beta 연결 비중 ${N(p.known)}% · 미산출 ${p.unknown}건</p><div class="analysis-controls"><label>한국 시장 충격 % <input data-ledger-shock="kr" type="number" min="-30" max="30" value="${ui.kr}"></label><label>미국 시장 충격 % <input data-ledger-shock="us" type="number" min="-30" max="30" value="${ui.us}"></label></div><div data-ledger-stress></div><p class="quiet">실행 상태 기록만 집계하며 제안·청산·휴지통은 제외합니다. 기여도=방향×비중%×Beta×시장충격%÷100. 통화별 현지시장 민감도이며 환율·비용은 제외합니다. 비중·Beta가 없으면 전체값을 산출하지 않습니다.</p><details><summary>시장·업종별 절대비중</summary>${p.sectors.map(([k,v])=>`<p>${E(k)} ${N(v)}%</p>`).join('')||'<p>기록 없음</p>'}</details></section>${root.RelationViews?.portfolioNotes(entries,lab)||''}${ui.draft?form(ui.draft,entities):''}<div class="analysis-controls"><label>상태 <select data-ledger-filter>${[['all','전체'],['제안','제안'],['실행','실행'],['청산','청산'],['trash','휴지통']].map(([v,l])=>`<option value="${v}" ${ui.filter===v?'selected':''}>${l}</option>`).join('')}</select></label><label>원장 검색 <input data-ledger-search type="search" value="${E(ui.q)}"></label></div><div data-ledger-cards>${shown.map(r=>card(r,entities,lab)).join('')||'<p>조건에 해당하는 결정이 없습니다.</p>'}</div>${legacy?`<details><summary>이전 자유 메모 · 원문 보존</summary><p>원본 저장 키를 유지합니다. 가져온 뒤 대상 종목과 방향을 지정할 수 있습니다.</p>${button('legacy','이전 메모 가져오기','')}<pre class="legacy-notes">${E(legacy)}</pre></details>`:''}`;
    const stress=()=>{const p=portfolio(vault.entries(),entities,ui.kr,ui.us);body.querySelector('[data-ledger-stress]').innerHTML=`<p>전체 가정 손익 ${N(p.total)}% NAV · 계산 가능 기록의 기여 합 ${N(p.partial)}%p</p>`+root.ResearchCharts.bars(p.rows.filter(r=>r.contribution!==null).map(r=>({name:r.name,value:r.contribution})),{title:'결정별 시장 충격 기여',unit:'%p NAV'});};stress();
    body.querySelectorAll('[data-ledger-shock]').forEach(el=>el.addEventListener('input',()=>{ui[el.dataset.ledgerShock]=Math.max(-30,Math.min(30,Number(el.value)||0));stress();}));
    body.querySelectorAll('[data-field]').forEach(el=>el.addEventListener('input',()=>{ui.draft[el.dataset.field]=el.value;}));
    body.querySelector('[data-ledger-filter]').addEventListener('change',e=>{ui.filter=e.target.value;repaint();});
    const filterCards=()=>{const q=ui.q.toLocaleLowerCase();body.querySelectorAll('.ledger-card').forEach(card=>{card.hidden=!card.textContent.toLocaleLowerCase().includes(q);});};filterCards();
    body.querySelector('[data-ledger-search]').addEventListener('input',e=>{ui.q=e.target.value;filterCards();});
    body.querySelectorAll('[data-decision-action]').forEach(b=>b.addEventListener('click',()=>{try{
     const {decisionAction:act,decisionId:id}=b.dataset;
     if(act==='save'){for(const k of fields)ui.draft[k]=body.querySelector('[data-field="'+k+'"]').value;vault.save(ui.draft,entities.find(e=>e.id===ui.draft.object_id),ui.draft.id);ui.draft=null;status('이 브라우저에 저장했습니다.');}
     else if(act==='new')ui.draft=blank();else if(act==='cancel')ui.draft=null;
     else if(act==='edit'){const r=vault.entries().find(r=>r.id===id);ui.draft={...r,direction:r.direction||'Long',conviction:r.conviction??3,horizon:r.horizon||'중기'};}
     else if(act==='entity'){navigate('기업 상세',{entity:vault.entries().find(r=>r.id===id).object_id});return;}
     else if(act==='export'){download(vault.export(),'sangsangin-decisions.json');return;}
     else if(act==='reload'){vault.reload();status('저장된 원장을 다시 읽었습니다. 작성 내용은 유지합니다.');}
     else if(act==='legacy'){const count=vault.import(legacy);status('이전 메모 '+count+'건을 가져왔습니다. 원문은 보존했습니다.');}
     else {vault.action(id,act);status('상태 변경을 저장했습니다.');}
     repaint();
    }catch(e){status('저장하지 못했습니다: '+e.message);}}));
    body.querySelector('[data-ledger-import]').addEventListener('change',async e=>{const file=e.target.files?.[0];if(!file)return;try{const count=vault.import(await file.text());status(count+'건을 가져왔습니다. 기존 ID 충돌은 별도 사본으로 보존합니다.');repaint();}catch(error){status('가져오지 못했습니다: '+error.message);}});
   };repaint();
  });
 }
 root.DecisionLedger={KEY,LEGACY,store,portfolio,intelligence,validate,decode,legacyRecords,shell,entityShell,bind,card,form};
})(typeof window==='undefined'?globalThis:window);
