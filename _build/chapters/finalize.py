"""Final presentation and graceful-fallback adjustments before screenshot tests."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'assets/oceanbond-chapters/viewer.js';s=p.read_text()
s=s.replace("target:[0,1.55,0],az:2.65,el:.24,dist:8.1", "target:[0,1.55,0],az:.55,el:.42,dist:8.7")
s=s.replace("target:[0,1.65,0],az:.62,el:.31,dist:9.5", "target:[0,1.65,0],az:.62,el:.43,dist:9.5")
s=s.replace("function fail(s){$('#loading').hidden=true;", "function fail(s){if(parent!==window&&location.origin!=='null')parent.postMessage({type:'ob-model-error',scene:kind},location.origin);$('#loading').hidden=true;")
p.write_text(s)
p=ROOT/'assets/oceanbond-chapters/page.js';s=p.read_text()
if 'ob-model-error' not in s:
 s=s.replace("const year=document.querySelector('#year');", "window.addEventListener('message',event=>{if(event.origin!==location.origin||event.data?.type!=='ob-model-error')return;for(const [panel,frame]of frames){if(frame.contentWindow===event.source){frame.hidden=true;panel.classList.remove('is-ready');announce(panel,'STILL PREVIEW · 3D UNAVAILABLE');panel.querySelector('.placeholder').textContent='Your browser could not start 3D. The model preview and chapter remain available.'}}});\nconst year=document.querySelector('#year');")
p.write_text(s)
p=ROOT/'assets/oceanbond-chapters/page.css';s=p.read_text()
if '/* Fallback framing */' not in s:s+='\n/* Fallback framing */\n.model-cover img{object-fit:contain}@media(max-width:700px){.model-box{height:430px}}\n'
p.write_text(s)
p=ROOT/'assets/oceanbond-chapters/viewer.css';s=p.read_text()
if '/* Touch controls */' not in s:s+='\n/* Touch controls */\n@media(max-width:440px){.toolbar button,.toolbar>a{min-height:40px;display:inline-flex;align-items:center}}\n'
p.write_text(s)
p=ROOT/'_build/raft/verify_live.py';s=p.read_text().replace('id="red-sail-model"','id="sailing"');p.write_text(s)
print('Applied readable combat camera, static fallback and current raft regression anchor')
