"""Verify the public raft model, motion, controls, and embedded OceanBond page."""
import hashlib
import json
import pathlib
import time
import urllib.request
from playwright.sync_api import sync_playwright

BASE = 'https://mustafa327.github.io/mth-labs/'
OUT = pathlib.Path('raft-verification')
OUT.mkdir(exist_ok=True)
report = {'base_url': BASE, 'checks': {}, 'errors': [], 'failed_http_responses': []}


def get(path):
    req = urllib.request.Request(BASE + path, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=40) as response:
        assert response.status == 200, (path, response.status)
        return response.read()


def state_at(page, timestamp):
    # Wait for a rendered frame, not just a changed simulation clock.
    count = page.evaluate('window.__frame.frames')
    page.evaluate('(t) => window.__test.setTime(t)', timestamp)
    page.wait_for_function(
        '([count, t]) => window.__frame.frames > count && Math.abs(window.__frame.time-t)<0.00001',
        arg=[count, timestamp], timeout=30000)
    # Transfer an immutable JSON snapshot instead of object handles.
    return json.loads(page.evaluate('JSON.stringify(window.__test.state())'))


try:
    html = get('oceanbond.html?check=' + str(int(time.time()))).decode()
    assert 'id="red-sail-model"' in html, 'Raft section missing from OceanBond page'
    asset = get('oceanbond-raft/assets/red-sail-raft.glb')
    checksum = hashlib.sha256(asset).hexdigest()
    report['checks']['model_bytes'] = len(asset)
    report['checks']['model_sha256'] = checksum
    assert checksum == 'c8ebcc90f8095aa6069cd3b6c986bf63d0c90bf6643d7b74d493cd9ce1660373', 'Hosted GLB differs from approved model'
    report['checks']['approved_asset_exact_match'] = True
    assert 'oceanbond-raft/' in get('sitemap.xml').decode(), 'Raft URL missing from sitemap'
    report['checks']['sitemap'] = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        page = context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        page.on('console', lambda msg: report['errors'].append(msg.text) if msg.type == 'error' else None)
        page.on('response', lambda response: report['failed_http_responses'].append([response.status, response.url]) if response.status >= 400 else None)
        page.goto(BASE + 'oceanbond-raft/?verify=retry', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_function('window.__ready===true && window.__frame && window.__frame.frames>2', timeout=60000)
        report['checks']['loaded_asset'] = page.evaluate('window.__asset')
        assert report['checks']['loaded_asset']['images'] == 9
        assert report['checks']['loaded_asset']['triangles'] == 146192
        assert report['checks']['loaded_asset']['clips'] == ['Wind_and_Waves_8s']
        before = page.evaluate('window.__frame.time')
        page.wait_for_function('(t) => window.__frame.time>t+0.1', arg=before, timeout=30000)
        report['checks']['animation_advances'] = True
        page.locator('#play').click()
        page.wait_for_function('window.__frame.paused===true', timeout=30000)
        frozen = page.evaluate('window.__frame.time')
        page.wait_for_timeout(400)
        assert page.evaluate('window.__frame.time') == frozen, 'Paused clock advanced'
        report['checks']['pause_freezes_motion'] = True
        state_a = state_at(page, 0.4)
        state_b = state_at(page, 1.5)
        (OUT / 'animation-states.json').write_text(json.dumps({'at_0_4': state_a, 'at_1_5': state_b}, indent=2))
        changed_nodes = [a['name'] for a, b in zip(state_a, state_b) if a != b]
        report['checks']['animated_nodes_changed'] = changed_nodes
        page.screenshot(path=str(OUT / 'desktop-full.png'))
        assert changed_nodes, 'No node transform or morph weight changed between two rendered timestamps'
        report['checks']['baked_model_state_changes'] = True
        for view in ['full', 'sail', 'detail']:
            page.locator('[data-view="' + view + '"]').click()
            page.wait_for_function('(v) => window.__frame.view===v', arg=view, timeout=30000)
            page.wait_for_timeout(1300)
            assert page.evaluate('window.__frame.glError') == 0, 'WebGL error in ' + view
            page.screenshot(path=str(OUT / ('desktop-' + view + '.png')))
        report['checks']['three_camera_views'] = True
        page.locator('#environment').click()
        page.wait_for_function('window.__frame.mode==="studio"', timeout=30000)
        page.screenshot(path=str(OUT / 'desktop-studio.png'))
        report['checks']['studio_lighting'] = True
        page.locator('#play').click()
        page.wait_for_function('window.__frame.paused===false', timeout=30000)
        resumed = page.evaluate('window.__frame.time')
        page.wait_for_function('(t) => window.__frame.time>t+0.1', arg=resumed, timeout=30000)
        report['checks']['resume_advances_motion'] = True
        page.locator('#quality').click()
        assert page.locator('#quality').inner_text() == 'Detail: light'
        page.locator('#focus').click()
        assert page.locator('body').evaluate('(el) => el.classList.contains("focus")')
        page.keyboard.press('Escape')
        assert not page.locator('body').evaluate('(el) => el.classList.contains("focus")')
        report['checks']['quality_and_focus_controls'] = True
        page.locator('#environment').click()
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#reset').click()
        page.wait_for_function('window.__frame.view==="full"', timeout=30000)
        page.wait_for_timeout(1300)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Mobile horizontal overflow'
        assert page.evaluate('window.__frame.glError') == 0
        page.screenshot(path=str(OUT / 'mobile.png'))
        report['checks']['mobile_layout'] = True
        page.goto(BASE + 'oceanbond.html?verify=embed', wait_until='domcontentloaded', timeout=60000)
        frame_element = page.locator('iframe.ob-raft-frame')
        frame_element.scroll_into_view_if_needed()
        frame = frame_element.element_handle().content_frame()
        frame.wait_for_function('window.__ready===true && window.__frame && window.__frame.frames>2', timeout=60000)
        assert frame.evaluate('window.__frame.glError') == 0
        assert page.locator('a[href="oceanbond-world.html"]').count()>0
        page.screenshot(path=str(OUT / 'mobile-embedded.png'))
        report['checks']['embedded_viewer'] = True
        report['checks']['original_island_link_preserved'] = True
        context.close()
        reduced = browser.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce')
        rp = reduced.new_page()
        rp.goto(BASE + 'oceanbond-raft/?verify=reduced', wait_until='domcontentloaded', timeout=60000)
        rp.wait_for_function('window.__ready===true && window.__frame', timeout=60000)
        assert rp.evaluate('window.__frame.paused') is True
        report['checks']['reduced_motion_starts_paused'] = True
        reduced.close()
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['failed_http_responses'], report['failed_http_responses']
    report['result'] = 'PASS'
except Exception as exc:
    report['result'] = 'FAIL'
    report['failure'] = str(exc)
    raise
finally:
    (OUT / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
