'use strict';
const assert=require('node:assert/strict'),P=require('../docs/presentation.js');
for(const color of ['#0071e3','#abc','#a5b9df','#0071e355','rgb(0, 102, 204)','rgba(50,90,190,.4)','hsl(216 44% 40%)']){
 const next=P.warmColor(color);assert.notEqual(next,color);const hue=+next.match(/^hsl\(([\d.]+)/)[1];assert(hue<165||hue>285,'cool colors cannot survive the palette');assert.equal(P.warmColor(next),next,'palette is idempotent');
}
for(const color of ['#fff','#1d1d1d','#b86428','rgb(60,100,55)','hsl(30 20% 45%)'])assert.equal(P.warmColor(color),color);
assert(P.warmColor('rgba(50,90,190,.4)').endsWith('/ 0.4000)'),'alpha is preserved');
assert.equal(P.warmValue('url(#series-fill)'), 'url(#series-fill)');
assert.equal(P.warmValue('var(--date-color)'), 'var(--date-color)');
assert.equal(P.warmValue('1.25 -2.75 2026-09-08'), '1.25 -2.75 2026-09-08');
console.log('PASS: warm palette covers hex/RGB/HSL, keeps opacity and warm categories, and is idempotent.');
