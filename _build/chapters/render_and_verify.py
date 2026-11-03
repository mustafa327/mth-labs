"""Render actual model posters and test the consolidated site before publishing."""
from pathlib import Path
import json, subprocess, time, urllib.request, struct, hashlib, os
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'chapters-verification';OUT.mkdir(exist_ok=True)
POSTERS=ROOT/'assets/oceanbond-chapters/posters';POSTERS.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('OB_TEST_BASE','http://127.0.0.1:8765/')
KINDS=['farming','combat','crafting','settlement','sailing']
report={'result':'RUNNING','models':{},'checks':{},'errors':[]}
server=None
if not os.environ.get('OB_TEST_BASE'):
 server=subprocess.Popen(['python','-m','http.server','8765','--bind','127.0.0.1','--directory',str(ROOT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
 try:
  urllib.request.urlopen(BASE+'oceanbond.html',timeout=2);break
 except Exception:time.sleep(.2)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  errors=[];bad=[]
  for kind in KINDS:
   page=browser.new_page(viewport={'width':1000,'height':720},device_scale_factor=1)
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m: errors.append(m.text) if m.type=='error' else None)
   page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
   page.goto(BASE+'assets/oceanbond-chapters/viewer.html?scene='+kind,wait_until='domcontentloaded',timeout=60000)
   page.wait_for_function('window.__ready && window.__frame && window.__frame.frames>2',timeout=60000)
   asset=page.evaluate('window.__asset');assert asset['meshes']>1 and asset['images']>=9 and len(asset['clips'])==1
   start=page.evaluate('window.__frame.time');page.wait_for_function('(t)=>window.__frame.time>t',arg=start,timeout=30000)
   page.locator('#play').click();page.wait_for_function('window.__frame.paused===true',timeout=15000)
   frozen=page.evaluate('window.__frame.time');page.wait_for_timeout(350);assert page.evaluate('window.__frame.time')==frozen
   states=[]
   for stamp in [.4,1.3]:
    before=page.evaluate('window.__frame.frames');page.evaluate('(t)=>window.__test.setTime(t)',stamp)
    page.wait_for_function('(x)=>window.__frame.frames>x.f && Math.abs(window.__frame.time-x.t)<.0001',arg={'f':before,'t':stamp},timeout=30000)
    states.append(page.evaluate('JSON.stringify(window.__test.state())'))
   assert states[0]!=states[1],kind+' has no model animation change'
   assert page.evaluate('window.__frame.glError')==0
   page.screenshot(path=str(OUT/(kind+'-viewer.png')))
   page.add_style_tag(content='header,.toolbar,footer,.interact-hint{visibility:hidden!important}')
   page.screenshot(path=str(OUT/(kind+'-model.png')))
   Image.open(OUT/(kind+'-model.png')).convert('RGB').save(POSTERS/(kind+'.jpg'),quality=87,optimize=True)
   report['models'][kind]={'asset':asset,'animation_advances':True,'paused_clock_stops':True,'model_transforms_change':True,'webgl_error':0}
   page.close();print('PASS MODEL',kind,flush=True)
  report['checks']['all_five_models_render']=True
  page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
  page.goto(BASE+'oceanbond.html',wait_until='domcontentloaded',timeout=60000)
  assert page.locator('.chapter').count()==5
  assert page.locator('a[href="oceanbond-world.html"],a[href="oceanbond-trailer.html"]').count()==0
  for kind in KINDS:
   page.evaluate('(k)=>window.scrollTo({top:document.getElementById(k).offsetTop-78,behavior:"instant"})',kind)
   page.wait_for_selector('#'+kind+' .model-box.is-ready',timeout=60000)
   frame=page.locator('#'+kind+' iframe').element_handle().content_frame()
   frame.wait_for_function('window.__frame && window.__frame.frames>1',timeout=30000)
   assert frame.evaluate('window.__frame.scene')==kind
   assert frame.evaluate('window.__frame.glError')==0
   assert page.locator('.model-box iframe').count()<=2
   page.wait_for_timeout(300);page.screenshot(path=str(OUT/('desktop-'+kind+'.png')))
   print('PASS CHAPTER',kind,flush=True)
  report['checks']['embedded_models_correct']=True;report['checks']['at_most_two_contexts']=True
  page.evaluate('window.scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(400)
  page.screenshot(path=str(OUT/'desktop-top.png'))
  page.set_viewport_size({'width':390,'height':844})
  for kind in ['farming','combat','sailing']:
   page.evaluate('(k)=>document.querySelector("#"+k+" .model-box").scrollIntoView({block:"center",behavior:"instant"})',kind)
   page.wait_for_selector('#'+kind+' .model-box.is-ready',timeout=60000)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   frame=page.locator('#'+kind+' iframe').element_handle().content_frame()
   assert frame.evaluate('window.__frame.glError')==0
   page.screenshot(path=str(OUT/('mobile-'+kind+'.png')))
  report['checks']['mobile_layout']=True
  # Reduced-motion users see a paused model but can explicitly play it.
  context=browser.new_context(viewport={'width':900,'height':650},reduced_motion='reduce')
  rp=context.new_page();rp.goto(BASE+'assets/oceanbond-chapters/viewer.html?scene=farming',wait_until='domcontentloaded')
  rp.wait_for_function('window.__frame',timeout=60000);assert rp.evaluate('window.__frame.paused')
  report['checks']['reduced_motion_paused']=True;context.close()
  context=browser.new_context(java_script_enabled=False)
  np=context.new_page();np.goto(BASE+'oceanbond.html',wait_until='domcontentloaded');assert np.locator('.chapter').count()==5 and np.locator('.model-cover img').count()==5
  report['checks']['no_js_readable']=True;context.close()
  browser.close()
  report['errors']=errors;report['failed_responses']=bad
  assert not errors,errors
  assert not bad,bad
 # Verify the retired pages are absent from published sources, without deleting business pages.
 for name in ['oceanbond-world.html','oceanbond-trailer.html','assets/oceanbond-world.css','assets/oceanbond-world.js','assets/oceanbond-trailer.js']:
  assert not (ROOT/name).exists(),name+' was not retired'
 for name in ['index.html','projects.html','privacy.html','404.html','oceanbond-raft/index.html']:
  assert (ROOT/name).is_file(),name+' was incorrectly removed'
 report['checks']['safe_cleanup']=True
 report['result']='PASS'
except Exception as e:
 report['result']='FAIL';report['failure']=str(e);raise
finally:
 (OUT/'report.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2),flush=True)
 if server:server.terminate()
