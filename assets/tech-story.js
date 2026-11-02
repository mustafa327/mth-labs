/* Scroll-linked 3D-like software story. No dependencies, reversible on scroll. */
(() => {
'use strict';
const section=document.querySelector('.tech-story');
if(!section)return;
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
const objects=[...section.querySelectorAll('.tech-code,.tech-network,.tech-dashboard')];
const steps=[...section.querySelectorAll('.tech-step')];
const desc=section.querySelector('#tech-story-description');
const descriptions=['Every reliable product starts with clear logic and thoughtful engineering.','APIs, databases and workflows connect into one dependable system.','The result: useful software, ready for real people and real work.'];
let ticking=false;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function render(){
ticking=false;
if(reduced.matches){objects.forEach((el,i)=>{el.style.opacity=i===2?'1':'0';el.style.transform='none'});steps.forEach((el,i)=>el.classList.toggle('is-current',i===2));desc.textContent=descriptions[2];return}
const rect=section.getBoundingClientRect();
const range=Math.max(1,section.offsetHeight-window.innerHeight);
const p=clamp(-rect.top/range,0,1);
const weights=[clamp(1-Math.abs(p-0)/.45,0,1),clamp(1-Math.abs(p-.5)/.32,0,1),clamp(1-Math.abs(p-1)/.45,0,1)];
const stage=p<.32?0:p<.68?1:2;
objects.forEach((el,i)=>{
const alpha=weights[i];const offset=(i===0?p*110:i===1?(p-.5)*110:(p-1)*110);
el.style.opacity=String(alpha);
el.style.transform='translate3d(0,'+(-offset)+'px,0) rotateX('+(offset*.09)+'deg) scale('+(0.83+alpha*.17)+')';
el.style.pointerEvents=alpha>.6?'auto':'none';
});
steps.forEach((el,i)=>el.classList.toggle('is-current',i===stage));
if(desc.textContent!==descriptions[stage])desc.textContent=descriptions[stage];
}
function request(){if(!ticking){ticking=true;requestAnimationFrame(render)}}
window.addEventListener('scroll',request,{passive:true});
window.addEventListener('resize',request,{passive:true});
reduced.addEventListener('change',request);
render();
})();