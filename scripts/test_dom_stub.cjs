/* Small offline event fixture; not a browser or layout engine. */
'use strict';
const unescape=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
class Node {
 constructor(tag='div',attrs={},text=''){this.tag=tag;this.attrs=attrs;this.children=[];this.events={};this.text=text;this.hidden=false;}
 get dataset(){return Object.fromEntries(Object.entries(this.attrs).filter(([k])=>k.startsWith('data-')).map(([k,v])=>[k.slice(5).replace(/-([a-z])/g,(_,a)=>a.toUpperCase()),v]));}
 set innerHTML(s){this.children=parse(s).children;this.raw=s;this.selectedValue=undefined;}
 get innerHTML(){return this.raw||'';}
 get textContent(){return this.text+this.children.map(n=>n.textContent).join('');}
 set textContent(s){this.children=[];this.text=s;}
 get value(){if(this.selectedValue!==undefined)return this.selectedValue;if(this.tag==='select'){const opts=this.querySelectorAll('option'),selected=opts.find(n=>'selected' in n.attrs)||opts[0];return selected?.attrs.value??selected?.textContent??'';}return this.attrs.value??(this.tag==='textarea'?this.textContent:'');}
 set value(v){this.selectedValue=String(v);}
 addEventListener(k,f){(this.events[k]??=[]).push(f);}
 async fire(k){for(const f of this.events[k]||[])await f({target:this,preventDefault(){}});}
 matches(s){if(s.startsWith('.'))return (this.attrs.class||'').split(' ').includes(s.slice(1));const m=s.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);if(m)return m[1] in this.attrs&&(m[2]===undefined||this.attrs[m[1]]===m[2]);return this.tag===s;}
 querySelectorAll(s){const out=[];const visit=n=>{if(n.matches(s))out.push(n);n.children.forEach(visit);};this.children.forEach(visit);return out;}
 querySelector(s){return this.querySelectorAll(s)[0]||null;}
}
function parse(html){const root=new Node(),stack=[root];for(const token of html.match(/<!--[\s\S]*?-->|<[^>]+>|[^<]+/g)||[]){if(token.startsWith('<!--'))continue;if(token.startsWith('</')){const tag=token.match(/^<\/([^\s>]+)/)[1];const at=stack.findLastIndex(n=>n.tag===tag);if(at>0)stack.length=at;continue;}if(token.startsWith('<')){const tag=token.match(/^<([^\s/>]+)/)[1],attrs={};const raw=token.slice(tag.length+1,-1);for(const m of raw.matchAll(/([^\s=/>]+)(?:="([^"]*)"|='([^']*)'|=([^\s>]+))?/g))attrs[m[1]]=unescape(m[2]??m[3]??m[4]??'');const n=new Node(tag,attrs);stack.at(-1).children.push(n);if(!['input','br','hr','img','meta','link'].includes(tag)&&!token.endsWith('/>'))stack.push(n);}else stack.at(-1).children.push(new Node('#text',{},unescape(token)));}return root;}
module.exports={parse,Node};
