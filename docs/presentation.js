/* Presentation-only palette. Data, labels, coordinates and quantitative values are never rewritten. */
(function(root){
 'use strict';
 const cache=new Map(),named={blue:'#0000ff',navy:'#000080',royalblue:'#4169e1',dodgerblue:'#1e90ff',steelblue:'#4682b4',lightblue:'#add8e6',skyblue:'#87ceeb',cyan:'#00ffff',aqua:'#00ffff',teal:'#008080',indigo:'#4b0082'};
 function warmColor(input){
  if(cache.has(input))return cache.get(input);if(named[input.toLowerCase()])return warmColor(named[input.toLowerCase()]);
  let h,s,l,a=1,m=input.match(/^#([\da-f]{3,8})$/i),rgb;
  if(m){let x=m[1];if(x.length===3||x.length===4)x=[...x].map(c=>c+c).join('');if(x.length!==6&&x.length!==8)return input;rgb=[0,2,4].map(i=>parseInt(x.slice(i,i+2),16)/255);if(x.length===8)a=parseInt(x.slice(6,8),16)/255;}
  else if((m=input.match(/^rgba?\(([^)]+)\)$/i))){const v=m[1].split(/[\s,/]+/).filter(Boolean);if(v.length<3)return input;rgb=v.slice(0,3).map(x=>parseFloat(x)/(x.includes('%')?100:255));if(v[3])a=parseFloat(v[3])/(v[3].includes('%')?100:1);}
  else if((m=input.match(/^hsla?\(([^)]+)\)$/i))){const v=m[1].split(/[\s,/]+/).filter(Boolean);h=+v[0];s=parseFloat(v[1])/100;l=parseFloat(v[2])/100;if(v[3])a=parseFloat(v[3])/(v[3].includes('%')?100:1);}
  else return input;
  if(rgb){const max=Math.max(...rgb),min=Math.min(...rgb),d=max-min;l=(max+min)/2;s=d===0?0:d/(1-Math.abs(2*l-1));h=d===0?0:max===rgb[0]?60*((rgb[1]-rgb[2])/d%6):max===rgb[1]?60*((rgb[2]-rgb[0])/d+2):60*((rgb[0]-rgb[1])/d+4);}
  h=(h%360+360)%360;
  if(![h,s,l,a].every(Number.isFinite)||h<165||h>285||s<.015){cache.set(input,input);return input;}
  const hue=l>.88?38:h<210?125:h<250?32:8,sat=l>.88?Math.min(s*100,12):Math.min(s*100,24);
  const output=`hsl(${hue} ${sat.toFixed(2)}% ${(l*100).toFixed(2)}% / ${a.toFixed(4)})`;
  cache.set(input,output);return output;
 }
 const tokens=/#(?:[\da-f]{8}|[\da-f]{6}|[\da-f]{4}|[\da-f]{3})(?![\da-f])|\b(?:rgb|hsl)a?\([^()]+\)/gi;
 const warmValue=value=>named[value.toLowerCase()]?warmColor(value):value.replace(tokens,warmColor);
 const properties=['color','background','background-color','background-image','border-color','border-top-color','border-right-color','border-bottom-color','border-left-color','outline-color','box-shadow','text-shadow','accent-color','caret-color','fill','stroke','stop-color','flood-color','--date-color'];
 function styleColors(style){if(!style)return;for(const p of [...properties,...Array.from({length:style.length},(_,i)=>style[i]).filter(p=>p.startsWith('--'))]){const value=style.getPropertyValue(p);if(!value||value.includes('url('))continue;const next=warmValue(value);if(next!==value)style.setProperty(p,next,style.getPropertyPriority(p));}}
 function rules(list){for(const rule of list){styleColors(rule.style);if(rule.cssRules)rules(rule.cssRules);}}
 function elementColors(el){if(el.nodeType!==1)return;for(const name of ['fill','stroke','stop-color','flood-color','color']){const value=el.getAttribute(name);if(value&&!value.startsWith('url(')){const next=warmValue(value);if(next!==value)el.setAttribute(name,next);}}styleColors(el.style);}
 function tree(el){elementColors(el);el.querySelectorAll?.('[fill],[stroke],[stop-color],[flood-color],[color],[style]').forEach(elementColors);}
 function install(){
  if(!root.document||!root.MutationObserver)return;
  for(const sheet of root.document.styleSheets){try{rules(sheet.cssRules);}catch{/* Cross-origin media styles are not controlled by this application. */}}
  tree(root.document.body);
  new root.MutationObserver(records=>{for(const record of records){if(record.type==='attributes')elementColors(record.target);else for(const node of record.addedNodes)if(node.nodeType===1)tree(node);}}).observe(root.document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['style','fill','stroke','stop-color','flood-color','color']});
 }
 const api={warmColor,warmValue,install};if(typeof module==='object'&&module.exports)module.exports=api;else{root.Presentation=api;install();}
})(typeof window==='undefined'?globalThis:window);
