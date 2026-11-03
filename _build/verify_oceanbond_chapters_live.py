"""Read-only browser checks against the published OceanBond chapters."""
import hashlib, json, pathlib, time, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
BASE='https://mustafa327.github.io/mth-labs/'
OUT=pathlib.Path('chapters-live-verification');OUT.mkdir(exist_ok=True)
report={'base':BASE,'checks':{},'models':{},'errors':[]}
def get(path):
 req=urllib.request.Request(BASE+path,headers={'Cache-Control':'no-cache'})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read()
try:
 for i in range(60):
  try:
   html=get('oceanbond.html?chapters='+str(int(time.time()))).decode()
   js=get('assets/oceanbond-chapters/viewer.js').decode()
   if 'id="farming"' in html and 'ob-model-error' in js:break
  except (urllib.error.URLError,TimeoutError):pass
  time.sleep(5)
 else:raise AssertionError('New chapters not available on Pages yet')
 for kind in ['farming','combat','crafting','settlement']:
  hosted=get('assets/oceanbond-chapters/models/'+kind+'.glb')
  expected=pathlib.Path('assets/oceanbond-chapters/models/'+kind+'.glb').read_bytes()
  assert hashlib.sha256(hosted).digest()==hashlib.sha256(expected).digest(),kind+' served a different model'
 report['checks']['hosted_models_match_verified_build']=True
 sitemap=get('sitemap.xml').decode()
 for old in ['oceanbond-world.html','oceanbond-trailer.html']:
  assert old not in sitemap and ('href="'+old+'"') not in html
 report['checks']['old_pages_removed_from_navigation_and_sitemap']=True
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
  errors=[];bad=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
  page.goto(BASE+'oceanbond.html?check=live-chapters',wait_until='domcontentloaded',timeout=60000)
  assert page.locator('.chapter').count()==5
  for kind in ['farming','combat','crafting','settlement','sailing']:
   page.evaluate('(k)=>window.scrollTo({top:document.getElementById(k).offsetTop-78,behavior:"instant"})',kind)
   page.wait_for_selector('#'+kind+' .model-box.is-ready',timeout=90000)
   f=page.locator('#'+kind+' iframe').element_handle().content_frame()
   f.wait_for_function('window.__frame && window.__frame.frames>2',timeout=30000)
   assert f.evaluate('window.__frame.scene')==kind
   before=f.evaluate('window.__frame.time');f.wait_for_function('(t)=>window.__frame.time>t',arg=before,timeout=30000)
   f.locator('#play').click();f.wait_for_function('window.__frame.paused',timeout=30000)
   stamp=f.evaluate('window.__frame.time');page.wait_for_timeout(250);assert f.evaluate('window.__frame.time')==stamp
   f.locator('#play').click();f.wait_for_function('!window.__frame.paused',timeout=30000)
   assert f.evaluate('window.__frame.glError')==0
   assert page.locator('.model-box iframe').count()<=2
   report['models'][kind]={'loaded':True,'motion':True,'pause_resume':True,'glError':0,'asset':f.evaluate('window.__asset')}
   page.screenshot(path=str(OUT/('desktop-'+kind+'.png')))
   print('PASS LIVE',kind,flush=True)
  page.set_viewport_size({'width':390,'height':844})
  for kind in ['farming','combat','sailing']:
   page.evaluate('(k)=>document.querySelector("#"+k+" .model-box").scrollIntoView({block:"center",behavior:"instant"})',kind)
   page.wait_for_selector('#'+kind+' .model-box.is-ready',timeout=90000)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.screenshot(path=str(OUT/('mobile-'+kind+'.png')))
  report['checks']['phone_sized_layout']=True
  report['errors']=errors;report['failed_responses']=bad
  assert not errors,errors
  assert not bad,bad
  page.close()
  # Removed direct URLs use the same-site custom 404 fallback to preserve bookmarks.
  rp=browser.new_page()
  for old,anchor in [('oceanbond-world.html','farming'),('oceanbond-trailer.html','sailing')]:
   rp.goto(BASE+old,wait_until='domcontentloaded',timeout=60000)
   rp.wait_for_url('**/oceanbond.html#'+anchor,timeout=30000)
  report['checks']['retired_bookmarks_redirect']=True
  rp.close();browser.close()
 report['result']='PASS'
except Exception as e:
 report['result']='FAIL';report['failure']=str(e);raise
finally:
 (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
