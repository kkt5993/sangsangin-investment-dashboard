/* PDF extraction controls shared by research, weekly notes and questions. */
(function(root){
 'use strict';const E=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function form(){return `<section class="notebook-pdf"><h4>PDF 본문 읽기</h4><p class="quiet">첨부를 선택하면 이 브라우저에서 읽습니다. 최대300쪽·20만자이며 스캔 이미지의 OCR·AI 요약은 별도 기능입니다. 본문·페이지 번호는 기록을 저장할 때 함께 보관합니다.</p><label>읽을 PDF<select data-nb-pdf-select><option value="">PDF를 첨부하세요</option></select></label><div class="note-actions"><button type="button" data-nb-pdf-extract>선택 PDF 본문 읽기</button><button type="button" data-nb-pdf-cancel disabled>읽기 취소</button></div><output data-nb-pdf-status role="status"></output><div data-nb-pdf-result hidden><label>페이지<select data-nb-pdf-page></select></label><label>근거로 가져올 원문 (필요한 부분만 남기세요)<textarea data-nb-pdf-quote rows="9" maxlength="12000"></textarea></label><div class="note-actions"><button type="button" data-nb-pdf-evidence>근거에 원문·페이지 추가</button><button type="button" data-nb-pdf-download>추출 본문 TXT ↓</button></div></div></section>`;}
 function mount(el,o){
  const q=s=>el.querySelector(s),P=root.PDFText,S=root.ResearchStore,select=q('[data-nb-pdf-select]'),pages=q('[data-nb-pdf-page]'),status=q('[data-nb-pdf-status]'),result=q('[data-nb-pdf-result]'),quote=q('[data-nb-pdf-quote]'),cancel=q('[data-nb-pdf-cancel]');
  cancel.disabled=true;let extracts=[],controller=null,disposed=false,lastID='';const hashes=new WeakMap();
  const files=()=>[...(q('[data-nb-upload]').files||[])];
  const chosen=()=>{const key=select.value;if(key.startsWith('new:')){const f=files()[+key.slice(4)];return f?{id:hashes.get(f),name:f.name,blob:f}:null;}const ref=o.refs().find(f=>f.id===key);return ref?{...ref}:null;};
  const current=()=>{const f=chosen();return f?{file:f,data:extracts.find(x=>x.file_id===f.id)}:{};};
  const pageText=()=>{const {data}=current(),page=data?.pages.find(p=>p.number===+pages.value);quote.value=page?.text||'';};
  const show=()=>{const {data}=current();result.hidden=!data;if(!data){status.textContent='PDF를 선택하고 본문 읽기를 실행하세요.';pages.innerHTML='';quote.value='';return;}status.textContent=P.status(data)+' · 저장 버튼을 눌러 본문과 첨부를 보관하세요.';const old=lastID===data.file_id?pages.value:'1';lastID=data.file_id;pages.innerHTML=data.pages.map(p=>`<option value="${p.number}">PDF ${p.number}쪽 · 표기 ${E(p.label)}${p.cut?' · 일부':''}${p.text?'':' · 텍스트 없음'}</option>`).join('');pages.value=data.pages.some(p=>String(p.number)===old)?old:'1';pageText();};
  function refresh(){const old=select.value,list=o.refs().filter(f=>o.book().files.some(a=>a.id===f.id&&a.mime==='application/pdf')).map(f=>({value:f.id,name:f.name}));files().forEach((f,i)=>{if(f.type==='application/pdf'||/\.pdf$/i.test(f.name))list.push({value:'new:'+i,name:f.name+' · 새 첨부'});});select.innerHTML=list.length?list.map(f=>`<option value="${E(f.value)}">${E(f.name)}</option>`).join(''):'<option value="">PDF를 첨부하세요</option>';if(list.some(f=>f.value===old))select.value=old;show();}
  select.addEventListener('change',show);pages.addEventListener('change',pageText);q('[data-nb-upload]').addEventListener('change',refresh);
  cancel.addEventListener('click',()=>controller?.abort());
  q('[data-nb-pdf-extract]').addEventListener('click',()=>o.run(async()=>{
   const f=chosen();if(!f)throw Error('먼저 읽을 PDF를 첨부·선택하세요.');
   controller=new AbortController();cancel.disabled=false;
   try{const blob=f.blob||await o.repo.blob(f.id),a=await (o.extract||P.extract)(blob,{signal:controller.signal,onProgress:p=>{if(!disposed)status.textContent=`PDF ${p.page}/${p.total}쪽 읽는 중 · ${p.characters.toLocaleString()}자`;}});
    if(disposed||!o.active())return;if(f.id&&a.file_id!==f.id)throw Error('PDF 원문 해시가 일치하지 않습니다.');
    S.extraction(a);if(f.blob)hashes.set(f.blob,a.file_id);extracts=[...extracts.filter(x=>x.file_id!==a.file_id),a];
    if(!o.field('title').value.trim())o.field('title').value=a.title||f.name.replace(/\.pdf$/i,'').slice(0,160);
    if(!o.field('authors').value.trim())o.field('authors').value=a.authors;
    if(!o.field('core').value.trim())o.field('core').value='PDF 본문 추출 기록 · '+f.name+' · '+P.status(a)+'\n아래 추출 본문과 원문을 검토하세요. 자동 요약이 아닙니다.';
    show();o.message('PDF를 읽었습니다. 본문을 확인한 뒤 기록을 저장하세요.');
   }catch(e){if(!disposed)status.textContent=e.message||'PDF를 읽지 못했습니다.';throw e;}
   finally{controller=null;cancel.disabled=true;}
  }));
  q('[data-nb-pdf-evidence]').addEventListener('click',()=>{const {file,data}=current(),page=data?.pages.find(p=>p.number===+pages.value);if(!data||!page||!quote.value.trim()){o.message('근거로 가져올 텍스트가 없습니다.');return;}const field=o.field('evidence'),text=(field.value?field.value+'\n\n':'')+P.citation(data,file.name,page,quote.value);if(text.length>12000){o.message('근거 필드의12000자 한도를 넘습니다. 필요한 원문 부분만 남겨 주세요.');return;}field.value=text;o.message('원문·페이지·파일 해시를 근거에 추가했습니다. 저장하면 반영됩니다.');});
  q('[data-nb-pdf-download]').addEventListener('click',()=>{const {file,data}=current();if(data)o.download(new Blob([P.plain(data,file.name)],{type:'text/plain;charset=utf-8'}),file.name+'.txt');});
  return {fill:r=>{extracts=structuredClone(r?.extractions||[]);lastID='';refresh();},refresh,forFiles:refs=>extracts.filter(x=>refs.some(f=>f.id===x.file_id)),dispose:()=>{disposed=true;controller?.abort();}};
 }
 root.NotebookPDF={form,mount};
})(typeof window==='undefined'?globalThis:window);
