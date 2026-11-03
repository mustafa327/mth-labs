"""Reuse the approved raft renderer for focused gameplay model studies."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'assets/oceanbond-chapters';out.mkdir(parents=True,exist_ok=True)
s=(root/'oceanbond-raft/assets/viewer.js').read_text()
start="const reduced=matchMedia('(prefers-reduced-motion: reduce)');"
assert start in s
config="""const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const query = new URLSearchParams(location.search);
const catalogue = {
 farming:{label:'Farming · The growing plot',file:'models/farming.glb',target:[0,1.0,0],az:.55,el:.58,dist:8.3,sea:false},
 combat:{label:'Combat · The training ground',file:'models/combat.glb',target:[0,1.55,0],az:2.65,el:.24,dist:8.1,sea:false},
 crafting:{label:'Crafting · The workbench',file:'models/crafting.glb',target:[0,1.4,0],az:.52,el:.42,dist:8.2,sea:false},
 settlement:{label:'Settlement · The first home',file:'models/settlement.glb',target:[0,1.65,0],az:.62,el:.31,dist:9.5,sea:false},
 sailing:{label:'Sailing · The red sail',file:'../../oceanbond-raft/assets/red-sail-raft.glb',target:[-.4,2.8,0],az:.60,el:.16,dist:15.4,sea:true}
};
const kind = Object.hasOwn(catalogue,query.get('scene')) ? query.get('scene') : 'farming';
const config = catalogue[kind];
document.title = config.label + ' | OceanBond';
$('#model-name').textContent=config.label;
$('#back').href='../../oceanbond.html#'+kind;
$('#download').href=config.file;
$('#model-file-fallback').href=config.file;
canvas.setAttribute('aria-label',config.label+'. Animated three-dimensional model. Drag or use arrow keys to rotate. Plus and minus zoom. Space pauses.');
if(!config.sea)$('#environment').hidden=true;
"""
s=s.replace(start,config)
s=s.replace("powerPreference:'high-performance'","powerPreference:'low-power'")
s=s.replace("This interactive model needs WebGL 2. The still preview and downloadable model remain available.","This interactive model needs WebGL 2. You can read the chapter and download the model without it.")
s=s.replace('uniform vec4 base;uniform vec3 eye;', 'uniform vec4 base;uniform vec3 eye,emissive;')
s=s.replace('rgb=tone(rgb*1.15);','rgb=tone((rgb+emissive)*1.15);')
s=s.replace('const N=128;', 'const N=config.sea?100:2;')
s=s.replace('const m=item.material,b=m.pbrMetallicRoughness;', "const m=item.material,b=m.pbrMetallicRoughness;u3(p,'emissive',m.emissiveFactor||[0,0,0]);")
a=s.index('const presets=');b=s.index('function pause(v)',a)
s=s[:a]+"""const basePreset={target:config.target,az:config.az,el:config.el,dist:config.dist};
const presets={full:basePreset,detail:{...basePreset,dist:config.dist*.77},sail:basePreset};
let current='full',az=config.az,el=config.el,dist=config.dist,target=[...config.target],want={...basePreset,target:[...basePreset.target]},mode=config.sea?'sea':'studio',paused=reduced.matches,clock=0,last=0,raf=0,visible=true,externalVisible=true,dragging=false,changed=true,quality='high',timeScale=1;
function setView(name){current=name;want={...presets[name],target:[...presets[name].target]};
 const aspect=canvas.clientWidth/Math.max(1,canvas.clientHeight);
 if(aspect<1.05)want.dist*=Math.min(1.4,1.05/aspect);
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));changed=true;request()}
"""+s[b:]
s=s.replace("$('#download').download='OceanBond-Red-Sail-Animated.glb';", "$('#download').download='OceanBond-'+kind+'.glb';")
s=s.replace("ready=true;$('#loading').hidden=true;", "ready=true;$('#loading').hidden=true;if(parent!==window&&location.origin!=='null')parent.postMessage({type:'ob-model-ready',scene:kind},location.origin);")
s=s.replace('ready&&visible&&!document.hidden','ready&&visible&&externalVisible&&!document.hidden')
s=s.replace('if(!visible||document.hidden||!ready)return','if(!visible||!externalVisible||document.hidden||!ready)return')
s=s.replace("if(canvas.clientWidth>950&&current==='full'&&!document.body.classList.contains('focus'))projection[8]=-.20;", '// Center the model in its chapter panel.')
s=s.replace('let frames=0;', "let frames=0;\nwindow.addEventListener('message',e=>{if(e.origin!==location.origin||e.source!==parent||e.data?.type!=='ob-visibility')return;externalVisible=Boolean(e.data.visible);last=0;if(externalVisible)request();else{cancelAnimationFrame(raf);raf=0}});")
s=s.replace('glError:gl.getError(),paused,mode,view:current','glError:gl.getError(),paused,mode,view:current,scene:kind,visible:visible&&externalVisible')
s=s.replace("canvas.addEventListener('wheel',e=>{e.preventDefault();", "canvas.addEventListener('wheel',e=>{if(document.activeElement!==canvas&&!e.ctrlKey)return;e.preventDefault();")
s=s.replace("const r=await fetch('assets/red-sail-raft.glb')", 'const r=await fetch(config.file)')
s=s.replace('For an offline preview use the single-file HTML supplied in the package.', 'Open the standalone viewer or download the model using the link below.')
s=s.replace("mode=mode==='sea'?'studio':'sea';", "mode=config.sea?(mode==='sea'?'studio':'sea'):'studio';")
s=s.replace('window.__test={', 'window.__test={get scene(){return kind},')
s=s.replace("await loadGLB(data);setView('full');pause(reduced.matches);", "await loadGLB(data);setView('full');dist=want.dist;pause(reduced.matches);")
(out/'viewer.js').write_text(s)
(out/'viewer.html').write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,follow"><meta name="theme-color" content="#12272c"><title>OceanBond · Interactive model</title><link rel="icon" href="../mark.svg"><link rel="stylesheet" href="viewer.css"><script src="viewer.js" defer></script></head>
<body><main class="experience"><canvas id="scene" tabindex="0" aria-label="Animated OceanBond model"></canvas>
<div class="loading" id="loading" role="status"><span></span><p>LOADING THE MODEL</p><small>Textured geometry · Continuous motion</small></div>
<div class="error" id="error" hidden role="alert"><h1>The 3D view could not start.</h1><p id="error-text"></p><a id="model-file-fallback" href="models/farming.glb">Download this model instead</a></div>
<header><span id="model-name">OceanBond model study</span><a id="back" href="../../oceanbond.html" target="_top" aria-label="Return to OceanBond">↗</a></header>
<div class="interact-hint">Drag to orbit · Click, then scroll to zoom</div>
<div class="toolbar" id="controls" role="group" aria-label="3D model controls"><button id="play" type="button" aria-pressed="true">Pause motion</button><button id="reset" type="button">Reset view</button><button id="fullscreen" type="button" aria-label="Fullscreen model">⛶</button><button id="quality" type="button">Detail: full</button><a id="download" href="models/farming.glb" download aria-label="Download animated GLB model">GLB ↓</a>
<button id="environment" type="button" aria-pressed="false">Studio lighting</button>
<div hidden><button id="focus">Focus model</button><label for="speed">Speed<input id="speed" type="range" min=".3" max="1.6" step=".1" value="1"><span id="speed-value">1.0×</span></label></div></div>
<footer><span id="status" role="status" aria-live="polite">LOADING</span><span>INTERACTIVE MODEL STUDY</span></footer>
</main></body></html>''')
(out/'viewer.css').write_text('''*{box-sizing:border-box}html,body{height:100%;margin:0;background:#12262d;color:#eee9db;font-family:system-ui,-apple-system,sans-serif;overflow:hidden}.experience{height:100%;min-height:280px;position:relative}canvas{display:block;width:100%;height:100%;touch-action:pan-y;cursor:grab;outline-offset:-4px}canvas:active{cursor:grabbing}header{position:absolute;inset:18px 20px auto;display:flex;justify-content:space-between;align-items:center;font-size:10px;letter-spacing:.12em;pointer-events:none;text-shadow:0 1px 8px #102630}header a{pointer-events:auto;font-size:17px;text-decoration:none;color:inherit}button,a{color:inherit}button{cursor:pointer;font:500 10px system-ui;min-height:36px}button,a:focus-visible{outline-offset:3px}button:focus-visible,a:focus-visible,canvas:focus-visible{outline:2px solid #efdaa6}.toolbar{position:absolute;bottom:36px;left:18px;right:18px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}.toolbar button,.toolbar>a{border:1px solid #e8e6cf40;background:#112c38b8;border-radius:5px;padding:8px 12px;color:#fff5df;backdrop-filter:blur(8px);text-decoration:none;font-size:10px}.toolbar button:hover,.toolbar>a:hover{background:#355258}.toolbar [hidden],.loading[hidden],.error[hidden]{display:none}.interact-hint{position:absolute;right:20px;bottom:88px;font-size:9px;color:#cad7d0;pointer-events:none;text-shadow:0 1px 4px #123}footer{position:absolute;bottom:12px;left:20px;right:20px;display:flex;justify-content:space-between;gap:10px;font-size:7px;letter-spacing:.11em;color:#c8d5d0;pointer-events:none}.loading{position:absolute;inset:0;background:#162d33;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;z-index:10}.loading span{border:1px solid #d8c9a84a;border-top-color:#eddaae;width:28px;height:28px;border-radius:50%;animation:spin 1s linear infinite}.loading p{font-size:10px;letter-spacing:.22em;margin:0}.loading small{font-size:10px;color:#a8bbb9}.error{position:absolute;inset:10%;padding:22px;background:#162f36f5;border:1px solid #78958b;border-radius:10px;z-index:20}.error h1{font:24px Georgia}.error p,.error a{font-size:13px;line-height:1.7}.focus header,.focus footer,.focus .interact-hint{display:none}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:440px){.toolbar{left:12px;right:12px;gap:4px;bottom:33px}.toolbar button,.toolbar>a{padding:6px 8px;font-size:9px}.interact-hint{bottom:79px;right:12px;font-size:8px}header{inset:14px 14px auto;font-size:8px}footer{left:14px;right:14px;font-size:6px}}@media(prefers-reduced-motion:reduce){.loading span{animation:none}}''')
print('Generated shared viewer:',len(s),'characters')
