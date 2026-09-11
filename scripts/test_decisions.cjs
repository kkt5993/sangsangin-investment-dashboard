/* Decision lifecycle, persistence failure, imports and portfolio arithmetic. Offline. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=path.join(__dirname,'..'),context=vm.createContext({window:{},TextEncoder,structuredClone,console});
for(const file of ['charts','analysis-charts','decision-ledger'])vm.runInContext(fs.readFileSync(path.join(base,'docs',file+'.js'),'utf8'),context);
const D=context.window.DecisionLedger,memory=new Map(),storage={getItem:k=>memory.get(k)??null,setItem:(k,v)=>memory.set(k,v)};
const entities=[{id:'stock:A',name:'Alpha',market:'US',sector:'IT',sensitivity:{beta:2}},{id:'stock:B',name:'Beta',market:'KR',sector:'산업',sensitivity:{beta:1}}];
const input={thesis:'수요 증가 <script>',catalyst:'실적',invalidate:'매출 감소',direction:'Long',conviction:4,horizon:'중기',size:10,upside:20,downside:10,probability:60};
const vault=D.store(storage);vault.save(input,entities[0]);const id=vault.entries()[0].id;
assert.equal(vault.entries()[0].status,'제안');assert.equal(D.portfolio(vault.entries(),entities).active,0);
vault.action(id,'activate');let p=D.portfolio(vault.entries(),entities,-10,-5);assert.equal(p.total,-1);assert.equal(p.gross,10);assert.equal(p.known,10);
vault.save({...input,direction:'Short',size:20},entities[1]);const shortId=vault.entries()[0].id;vault.action(shortId,'activate');
p=D.portfolio(vault.entries(),entities,-10,-5);assert.equal(p.total,1);assert.equal(p.net,-10);assert.equal(p.gross,30);
vault.save({...input,direction:'Short',size:0},entities[1],shortId);assert.equal(D.portfolio(vault.entries(),entities,-10,-5).total,-1,'zero is not defaulted to 1%');
vault.save({...input,size:''},entities[0],id);p=D.portfolio(vault.entries(),entities);assert.equal(p.total,null);assert.equal(p.unknown,1);
vault.save(input,entities[0],id);assert.equal(D.portfolio(vault.entries(),entities.slice(1)).total,null,'missing Beta is not zero sensitivity');
vault.action(id,'close');assert(vault.entries().find(r=>r.id===id).closed_at);assert.equal(D.portfolio(vault.entries(),entities).gross,0);
vault.action(id,'reopen');assert.equal(vault.entries().find(r=>r.id===id).closed_at,null);vault.action(id,'delete');assert.equal(D.portfolio(vault.entries(),entities).gross,0);vault.action(id,'restore');assert.equal(D.portfolio(vault.entries(),entities).gross,10);
assert.throws(()=>vault.action(id,'activate'));const before=vault.export();assert.throws(()=>vault.save({...input,size:-1},entities[0],id));assert.equal(vault.export(),before);
assert.equal(D.intelligence(vault.entries().find(r=>r.id===id)).ev,8);assert.equal(D.intelligence({...vault.entries()[0],probability:null}).ev,null);
const html=D.card(vault.entries().find(r=>r.id===id),entities);assert(html.includes('&lt;script&gt;'));assert(!html.includes('<script>'));
const form=D.form(input,entities);for(const key of ['object_id','direction','conviction','horizon','size','thesis','catalyst','invalidate'])assert(form.includes('data-field="'+key+'"'));
assert.equal(vault.import(vault.export()),0,'identical import is idempotent');
const conflicting=JSON.parse(vault.export());conflicting.entries[0].thesis='Changed in another copy';assert.equal(vault.import(JSON.stringify(conflicting)),1);assert.equal(new Set(vault.entries().map(r=>r.id)).size,3);assert(vault.entries().some(r=>r.thesis==='Changed in another copy'));
const legacy=JSON.stringify([{title:'Old memo',body:'Original body',date:'2026-09-01T00:00:00Z'}]);storage.setItem(D.LEGACY,legacy);assert.equal(vault.import(legacy),1);assert.equal(vault.import(legacy),0);assert.equal(storage.getItem(D.LEGACY),legacy);assert.equal(vault.entries().find(r=>r.name==='Old memo').direction,null);
const largeBook=JSON.parse(vault.export());largeBook.entries=Array.from({length:501},(_,i)=>({...largeBook.entries[0],id:'large-'+i,thesis:'한'.repeat(12000)}));const largeMemory=new Map(),largeVault=D.store({getItem:k=>largeMemory.get(k)??null,setItem:(k,v)=>largeMemory.set(k,v)});assert.equal(largeVault.import(JSON.stringify(largeBook)),501);assert.equal(largeVault.reload().length,501);
const saveBefore=storage.getItem(D.KEY);assert.throws(()=>vault.import('{bad'));assert.equal(storage.getItem(D.KEY),saveBefore);assert.throws(()=>vault.import(JSON.stringify({version:7,entries:[]})));
const broken=JSON.parse(vault.export());broken.entries[0].size={value:3};assert.throws(()=>vault.import(JSON.stringify(broken)));assert.equal(storage.getItem(D.KEY),saveBefore);
const duplicate=JSON.parse(vault.export());duplicate.entries.push(duplicate.entries[0]);assert.throws(()=>vault.import(JSON.stringify(duplicate)));
// A stale tab and a full browser quota never mutate the in-memory or persisted book.
const stale=D.store(storage);vault.save(input,entities[0]);const after=storage.getItem(D.KEY);assert.throws(()=>stale.save(input,entities[0]),/다른 창/);assert.equal(storage.getItem(D.KEY),after);stale.reload();
const failing=D.store({getItem:storage.getItem,setItem(){throw Error('QuotaExceededError');}}),failedBefore=failing.export();assert.throws(()=>failing.save(input,entities[0]),/Quota/);assert.equal(failing.export(),failedBefore);assert.equal(storage.getItem(D.KEY),after);
storage.setItem(D.KEY,'{corrupt');assert.throws(()=>D.store(storage));assert.equal(storage.getItem(D.KEY),'{corrupt');
console.log('PASS: decision lifecycle, JSON/legacy preservation, collision copies, stale-tab/quota rollback, XSS, signed NAV and missing coverage.');

// Invoke actual form/card/navigation callbacks on parsed markup, without a browser.
(async()=>{
 const {parse}=require('./test_dom_stub.cjs');memory.delete(D.KEY);memory.delete(D.LEGACY);context.window.localStorage=storage;
 const view=parse(D.shell()),snapshot={sections:[{type:'entities',entities}]},navigations=[];
 D.bind(view,snapshot,(group,state)=>navigations.push({group,state}));
 const click=action=>view.querySelector('[data-decision-action="'+action+'"]').fire('click');
 await click('new');
 for(const [k,v] of Object.entries({...input,object_id:entities[0].id})){const el=view.querySelector('[data-field="'+k+'"]');el.value=v;await el.fire('input');}
 await click('save');assert.equal(D.store(storage).entries().length,1);assert.equal(D.store(storage).entries()[0].thesis,input.thesis);
 await click('activate');assert.equal(D.store(storage).entries()[0].status,'실행');assert(view.querySelector('[data-ledger-stress]').textContent.includes('-2'));
 const shock=view.querySelector('[data-ledger-shock="us"]');shock.value=10;await shock.fire('input');assert(view.querySelector('[data-ledger-stress]').textContent.includes('2'));
 await click('entity');assert.equal(navigations[0].group,'Entity 360');assert.equal(navigations[0].state.entity,entities[0].id);
 const search=view.querySelector('[data-ledger-search]');search.value='no match';await search.fire('input');assert(view.querySelector('.ledger-card').hidden);search.value='';await search.fire('input');assert(!view.querySelector('.ledger-card').hidden);
 await click('close');await click('reopen');await click('delete');assert.equal(view.querySelectorAll('.ledger-card').length,0);
 const filter=view.querySelector('[data-ledger-filter]');filter.value='trash';await filter.fire('change');await click('restore');assert(!D.store(storage).entries()[0].deleted_at);
 filter.value='all';await filter.fire('change');await click('edit');view.querySelector('[data-field="thesis"]').value='Edited through form';await click('save');assert.equal(D.store(storage).entries()[0].thesis,'Edited through form');
 const edata={...entities[0],symbol:'A',date:'2026-09-08',rs_universe:'US',rs:80,rsi:55,high52:-4,returns:[1,2,3,4,5],curve:[['2026-06-01',100],['2026-09-08',103]],benchmark:'SPY',upcoming:[],events_retrieved:null,financial:null,sensitivity:{beta:2,r2:.8,observations:252,start:'2025-09-01',end:'2026-09-08'}};
 const es={type:'entities',entities:[edata],coverage:{US:{available:1,expected:1,membership_as_of:'2026-09-08'}}},ev=parse(D.entityShell(es));
 D.bind(ev,{sections:[es]},(group,state)=>navigations.push({group,state}),{entity:edata.id});assert(ev.querySelector('[data-entity-body]').textContent.includes('Edited through form'));
 await ev.querySelector('[data-entity-decision]').fire('click');assert.equal(navigations.at(-1).state.decisionObject,edata.id);
 const esearch=ev.querySelector('[data-entity-search]');esearch.value='missing';await esearch.fire('input');assert(ev.querySelector('[data-entity-body]').textContent.includes('해당하는 종목이 없습니다'));esearch.value='Alpha';await esearch.fire('input');assert(ev.querySelector('[data-entity-body]').textContent.includes('Beta 2'));
 console.log('PASS: actual decision form save/edit, status controls, shock inputs, search reset, trash restoration and Entity 360 navigation callbacks.');
})().catch(e=>{console.error(e);process.exitCode=1;});
