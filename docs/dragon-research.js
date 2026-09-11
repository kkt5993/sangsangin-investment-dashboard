/* Public evidence and an explicitly loaded, read-only local research catalog. */
(function(root){
 'use strict';
 const E=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const kinds={all:'전체',linked:'객체 연결',official:'공식 근거',team:'팀 방법론',local:'로컬 리서치 자료실'};
 const url=value=>{try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:'';}catch{return '';}};
 function filter(rows,kind,query){const q=query.trim().toLocaleLowerCase();return rows.filter(r=>(kind==='all'||kind==='linked'&&r.targets.length||r.kind===kind)&&[r.title,r.source,r.core,...r.evidence,...r.targets.map(t=>t.name)].join(' ').toLocaleLowerCase().includes(q));}
 function card(r){const href=url(r.url);return `<article class="panel dragon-research-card" data-dr-document="${E(r.id)}"><p class="quiet">${E(kinds[r.kind])} · ${E(r.date_kind)} ${E(r.date||'미확인')}${r.published_on?' · 발표 '+E(r.published_on):''}${r.period_end?' · 보고기간 말 '+E(r.period_end):''}</p><h3>${E(r.title)}</h3><p class="quiet">${E(r.source)}</p>${r.direction?`<p>사용자 입력: ${E(r.direction)} · ${E(r.horizon||'기간 미입력')} · 확신 ${E(r.confidence??'미입력')}/5</p>`:''}<p>${E(r.core)}</p><div class="tags">${r.targets.length?r.targets.map(t=>t.entity?`<button type="button" data-dr-entity="${E(t.id)}">${E(t.name)} →</button>`:`<span>${E(t.name)}</span>`).join(''):'<span>객체 미연결</span>'}</div><details><summary>근거·내용 보기</summary>${r.evidence.map(t=>`<p style="white-space:pre-wrap">${E(t)}</p>`).join('')}${(r.attachments||[]).map(f=>`<button type="button" data-dr-file="${E(f.id)}" data-dr-name="${E(f.name)}">첨부 내려받기 · ${E(f.name)}</button>`).join('')}</details>${href?`<p><a href="${E(href)}" target="_blank" rel="noopener noreferrer">${r.kind==='official'?'공식 원문':'참고 출처'} ↗</a></p>`:''}${r.kind==='team'||r.kind==='local'?'<p><a href="#principium">리서치 자료실 기록 화면 →</a></p>':''}</article>`;}
 function render(s,index){return `<div data-dr-research="${index}"><p>${E(s.scope)}</p><div class="section-controls"><label>분류 <select data-dr-kind>${Object.entries(kinds).map(([k,n])=>`<option value="${k}">${n}</option>`).join('')}</select></label><label>문서·기업 검색 <input type="search" data-dr-search placeholder="제목, 기업, 근거"></label><button type="button" data-dr-load>이 브라우저의 리서치 불러오기</button></div><p class="quiet" data-dr-message>개인 기록은 아직 읽지 않았습니다.</p><p role="status" data-dr-count></p><div class="detail-grid" data-dr-cards>${s.items.map(card).join('')}</div></div>`;}
 function localRows(book,entities){
  const lookup=new Map();for(const e of entities)for(const key of [e.id,e.symbol,e.name])if(key)lookup.set(key.toLocaleLowerCase(),e);
  return book.entries.filter(r=>r.module==='principium'&&!r.deleted_at).map(r=>{
   const targets=new Map();for(const k of r.keywords){const e=lookup.get(k.toLocaleLowerCase());if(e)targets.set(e.id,{id:e.id,name:e.name,entity:true});}
   return {id:'local:'+r.id,kind:'local',title:r.title,source:[r.source,r.authors].filter(Boolean).join(' · ')||'이 브라우저의 개인 기록',date:r.date,date_kind:'사용자 기록일',url:r.url||'',
    targets:[...targets.values()],core:r.core,evidence:[r.ideas&&'아이디어\n'+r.ideas,r.evidence&&'근거\n'+r.evidence,r.actions&&'시사점\n'+r.actions,r.invalidates&&'무효화 조건\n'+r.invalidates].filter(Boolean),
    attachments:r.attachments,direction:r.direction,horizon:r.horizon,confidence:r.confidence};
  });
 }
 function bind(container,snapshot,navigate){container.querySelectorAll('[data-dr-research]').forEach(box=>{
  const s=snapshot.sections[+box.dataset.drResearch],kind=box.querySelector('[data-dr-kind]'),search=box.querySelector('[data-dr-search]'),message=box.querySelector('[data-dr-message]'),load=box.querySelector('[data-dr-load]');let rows=s.items.slice(),loading=false;
  const draw=()=>{const visible=filter(rows,kind.value,search.value);box.querySelector('[data-dr-cards]').innerHTML=visible.map(card).join('')||'<p>일치하는 문서가 없습니다.</p>';box.querySelector('[data-dr-count]').textContent=`${visible.length} / ${rows.length}편 · 객체 연결 ${rows.filter(r=>r.targets.length).length}편`;for(const o of kind.options){const n=o.value==='all'?rows.length:o.value==='linked'?rows.filter(r=>r.targets.length).length:rows.filter(r=>r.kind===o.value).length;o.textContent=kinds[o.value]+' '+n;}};
  kind.addEventListener('change',draw);search.addEventListener('input',draw);
  load.addEventListener('click',async()=>{if(loading)return;loading=true;load.disabled=true;let repo;try{
   repo=await root.ResearchStore.open();const book=await repo.read();if(box.isConnected===false)return;
   const entities=snapshot.sections.find(x=>x.type==='entities')?.entities||[];rows=s.items.concat(localRows(book,entities));draw();message.textContent='로컬 기록을 읽었습니다. 키워드가 기업명·티커·객체 ID와 정확히 일치하면 연결합니다. 개인 기록과 첨부를 서버에 전송하지 않습니다.';
  }catch(e){if(box.isConnected!==false)message.textContent='로컬 기록을 읽지 못했습니다: '+e.message;}finally{repo?.close();loading=false;if(box.isConnected!==false)load.disabled=false;}});
  box.addEventListener('click',async event=>{const entity=event.target.closest('[data-dr-entity]');if(entity){navigate?.('기업 상세',{entity:entity.dataset.drEntity});return;}const file=event.target.closest('[data-dr-file]');if(!file||file.disabled)return;file.disabled=true;let repo,object;
   try{repo=await root.ResearchStore.open();const blob=await repo.blob(file.dataset.drFile);if(box.isConnected===false)return;object=URL.createObjectURL(blob);const a=document.createElement('a');a.href=object;a.download=file.dataset.drName;a.click();setTimeout(()=>URL.revokeObjectURL(object),1000);}
   catch(e){if(box.isConnected!==false)message.textContent='첨부를 읽지 못했습니다: '+e.message;}finally{repo?.close();if(box.isConnected!==false)file.disabled=false;}
  });draw();
 });}
 root.DragonResearch={render,bind,card,filter,localRows};
})(typeof window==='undefined'?globalThis:window);
