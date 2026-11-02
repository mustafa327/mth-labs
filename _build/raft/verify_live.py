"""Verify the public OceanBond raft deployment without modifying website data."""
import hashlib
import json
import pathlib
import time
import urllib.request
from playwright.sync_api import sync_playwright

BASE = 'https://mustafa327.github.io/mth-labs/'
OUT = pathlib.Path('raft-verification')
OUT.mkdir(exist_ok=True)
report = {'base_url': BASE, 'checks': {}, 'errors': []}

def get(path):
    request = urllib.request.Request(BASE + path, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=40) as response:
        assert response.status == 200
        return response.read()

try:
    # Wait only for this deployment's identifiable content; never change the site.
    for attempt in range(24):
        try:
            page_html = get('oceanbond.html?raft-check=' + str(int(time.time()))).decode()
            js = get('oceanbond-raft/assets/viewer.js').decode()
            if 'id="red-sail-model"' in page_html and 'window.__ready=true' in js:
                break
        except Exception:
            pass
        time.sleep(5)
    else:
        raise AssertionError('Published page and raft script are not available yet')
    asset = get('oceanbond-raft/assets/red-sail-raft.glb')
    report['checks']['model_bytes'] = len(asset)
    report['checks']['model_sha256'] = hashlib.sha256(asset).hexdigest()
    assert report['checks']['model_sha256'] == 'c8ebcc90f8095aa6069cd3b6c986bf63d0c90bf6643d7b74d493cd9ce1660373', 'Hosted model differs from approved asset'
    report['checks']['approved_asset_exact_match'] = True
    report['checks']['sitemap'] = 'oceanbond-raft/' in get('sitemap.xml').decode()
    assert report['checks']['sitemap']
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        page = context.new_page()
        errors = []
        failed_responses = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.on('response', lambda response: failed_responses.append([response.status, response.url]) if response.status >= 400 else None)
        page.goto(BASE + 'oceanbond-raft/?verify=desktop', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_function('window.__ready === true && window.__frame && window.__frame.frames > 2', timeout=60000)
        report['checks']['loaded_asset'] = page.evaluate('window.__asset')
        assert report['checks']['loaded_asset']['images'] == 9
        assert report['checks']['loaded_asset']['triangles'] == 146192
        assert report['checks']['loaded_asset']['clips'] == ['Wind_and_Waves_8s']
        before = page.evaluate('window.__frame.time')
        page.wait_for_timeout(700)
        assert page.evaluate('window.__frame.time') > before
        report['checks']['animation_advances'] = True
        page.locator('#play').click()
        page.wait_for_timeout(200)
        frozen = page.evaluate('window.__frame.time')
        page.wait_for_timeout(400)
        assert page.evaluate('window.__frame.paused') is True
        assert page.evaluate('window.__frame.time') == frozen
        report['checks']['pause_freezes_motion'] = True
        page.evaluate('window.__test.setTime(0.4)')
        page.wait_for_timeout(150)
        state_a = page.evaluate('window.__test.state()')
        page.evaluate('window.__test.setTime(1.5)')
        page.wait_for_timeout(150)
        state_b = page.evaluate('window.__test.state()')
        assert state_a != state_b
        report['checks']['baked_model_state_changes'] = True
        for view in ['full', 'sail', 'detail']:
            page.locator('[data-view="' + view + '"]').click()
            page.wait_for_timeout(1100)
            assert page.evaluate('window.__frame.view') == view
            assert page.evaluate('window.__frame.glError') == 0
            page.screenshot(path=str(OUT / ('desktop-' + view + '.png')))
        report['checks']['three_camera_views'] = True
        page.locator('#environment').click()
        page.wait_for_timeout(200)
        assert page.evaluate('window.__frame.mode') == 'studio'
        page.screenshot(path=str(OUT / 'desktop-studio.png'))
        report['checks']['studio_lighting'] = True
        page.locator('#reset').click()
        page.locator('#play').click()
        page.wait_for_timeout(200)
        assert page.evaluate('window.__frame.paused') is False
        page.locator('#quality').click()
        assert page.locator('#quality').inner_text() == 'Detail: light'
        page.locator('#focus').click()
        assert page.locator('body').evaluate('(el) => el.classList.contains("focus")')
        page.keyboard.press('Escape')
        assert not page.locator('body').evaluate('(el) => el.classList.contains("focus")')
        report['checks']['resume_quality_focus'] = True
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#reset').click()
        page.wait_for_timeout(1200)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.evaluate('window.__frame.glError') == 0
        page.screenshot(path=str(OUT / 'mobile.png'))
        report['checks']['mobile_layout'] = True
        page.goto(BASE + 'oceanbond.html?verify=embed', wait_until='domcontentloaded', timeout=60000)
        frame_element = page.locator('iframe.ob-raft-frame')
        frame_element.scroll_into_view_if_needed()
        frame = frame_element.element_handle().content_frame()
        frame.wait_for_function('window.__ready === true && window.__frame && window.__frame.frames > 2', timeout=60000)
        assert frame.evaluate('window.__frame.glError') == 0
        assert page.locator('a[href="oceanbond-world.html"]').count() > 0
        page.screenshot(path=str(OUT / 'mobile-embedded.png'))
        report['checks']['embedded_viewer'] = True
        report['checks']['original_island_link_preserved'] = True
        reduced = browser.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce')
        rp = reduced.new_page()
        rp.goto(BASE + 'oceanbond-raft/?verify=reduced', wait_until='domcontentloaded', timeout=60000)
        rp.wait_for_function('window.__ready === true && window.__frame', timeout=60000)
        assert rp.evaluate('window.__frame.paused') is True
        report['checks']['reduced_motion_starts_paused'] = True
        reduced.close()
        context.close()
        browser.close()
        report['errors'] = errors
        report['failed_http_responses'] = failed_responses
        assert not errors, errors
        assert not failed_responses, failed_responses
    report['result'] = 'PASS'
except Exception as exc:
    report['result'] = 'FAIL'
    report['failure'] = str(exc)
    raise
finally:
    (OUT / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
