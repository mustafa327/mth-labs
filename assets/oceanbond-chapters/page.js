/* Separate chapter models. Only the visible panel animates; at most two WebGL
   contexts remain resident. No analytics, storage or external dependencies. */
(()=>{'use strict';
const panels=[...document.querySelectorAll('.model-box')];
const frames=new Map();let active=null,scheduled=false;
const nav=[...document.querySelectorAll('.chapter-nav a')];
function announce(panel,text){panel.closest('.model-stage').querySelector('.model-status').textContent=text}
function send(frame,visible){try{frame.contentWindow.postMessage({type:'ob-visibility',visible},location.origin)}catch{}}
function load(panel){
 if(frames.has(panel))return frames.get(panel);
 const frame=document.createElement('iframe');frame.title=panel.dataset.title;
 frame.src=panel.dataset.src;frame.setAttribute('allow','fullscreen');frame.setAttribute('allowfullscreen','');frame.setAttribute('tabindex','0');frame.loading='eager';
 frame.addEventListener('load',()=>send(frame,active===panel));panel.append(frame);frames.set(panel,frame);announce(panel,'LOADING 3D MODEL');
 while(frames.size>2){const candidate=[...frames.keys()].filter(p=>p!==panel&&p!==active).sort((a,b)=>Math.abs(b.getBoundingClientRect().top)-Math.abs(a.getBoundingClientRect().top))[0];if(!candidate)break;const old=frames.get(candidate);send(old,false);old.remove();frames.delete(candidate);candidate.classList.remove('is-ready');announce(candidate,'SCROLL TO EXPLORE')}
 return frame;
}
function update(){scheduled=false;let chosen=null,score=Infinity;const vh=innerHeight;
 for(const panel of panels){const r=panel.getBoundingClientRect();const amount=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,65));if(amount>Math.min(100,r.height*.25)){const s=Math.abs((r.top+r.bottom)/2-vh/2);if(s<score){score=s;chosen=panel}}}
 if(chosen!==active){active=chosen;if(active)load(active);for(const [p,f] of frames)send(f,p===active)}
 let section=null;for(const el of document.querySelectorAll('.chapter')){if(el.getBoundingClientRect().top<innerHeight*.5)section=el}
 nav.forEach(a=>{if(section&&a.hash==='#'+section.id)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current')});
}
function request(){if(!scheduled){scheduled=true;requestAnimationFrame(update)}}
window.addEventListener('scroll',request,{passive:true});window.addEventListener('resize',request,{passive:true});
window.addEventListener('message',event=>{if(event.origin!==location.origin||event.data?.type!=='ob-model-ready')return;for(const [panel,frame] of frames){if(frame.contentWindow===event.source){panel.classList.add('is-ready');announce(panel,'LIVE 3D · DRAG TO ROTATE');send(frame,panel===active)}}});
document.addEventListener('visibilitychange',()=>{for(const [panel,frame] of frames)send(frame,!document.hidden&&panel===active);if(!document.hidden)request()});
if(location.hash==='#red-sail-model')location.replace('#sailing');
window.addEventListener('message',event=>{if(event.origin!==location.origin||event.data?.type!=='ob-model-error')return;for(const [panel,frame]of frames){if(frame.contentWindow===event.source){frame.hidden=true;panel.classList.remove('is-ready');announce(panel,'STILL PREVIEW · 3D UNAVAILABLE');panel.querySelector('.placeholder').textContent='Your browser could not start 3D. The model preview and chapter remain available.'}}});
const year=document.querySelector('#year');if(year)year.textContent=new Date().getFullYear();request();
})();
