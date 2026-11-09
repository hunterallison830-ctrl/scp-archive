"""Real-browser smoke checks + screenshots for the overhauled archive.

Run against a local preview (python3 -m http.server 8781 --bind 127.0.0.1):
    python3 verify.py
Needs Python Playwright and /usr/bin/google-chrome. Writes screenshots to
/workspace/scp-archive-shots and a summary to verification-results.json.
NOTE: written during the overhaul but NOT executed by the build agent; the
first run of this script is the first real-browser test.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

import os
BASE = os.environ.get('RAISA_BASE', 'http://127.0.0.1:8781')
SHOTS = Path('/workspace/scp-archive-shots'); SHOTS.mkdir(exist_ok=True)
checks = []
def passed(msg):
    checks.append(msg); print('PASS:', msg, flush=True)
def no_overflow(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'horizontal overflow'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    for vw, vh, tag in [(390, 844, 'mobile'), (1280, 900, 'desktop')]:
        ctx = browser.new_context(viewport={'width': vw, 'height': vh}, reduced_motion='reduce')
        page = ctx.new_page(); errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE); page.wait_for_function('!document.querySelector("#enter").disabled')
        assert page.evaluate('audio.ctx === null')
        page.screenshot(path=str(SHOTS / f'{tag}-splash.png'))
        page.locator('#enter').click()
        assert page.locator('#grid .card').count() == 36; no_overflow(page)
        page.screenshot(path=str(SHOTS / f'{tag}-hero.png'))
        page.locator('#collection').scroll_into_view_if_needed(); page.screenshot(path=str(SHOTS / f'{tag}-anomalies.png'))
        assert page.evaluate('''async()=>{for(const i of document.querySelectorAll('#grid img')){i.loading='eager';await i.decode();if(!i.naturalWidth)return false}return true}''')
        passed(f'{tag}: 36 anomaly cards with decoded sourced images, no overflow')
        page.locator('#search').fill('173'); assert page.locator('#grid .card').count() == 1
        page.locator('#search').fill(''); page.locator('#chips [data-tag="Keter"]').click(); assert 0 < page.locator('#grid .card').count() < 36
        page.locator('#chips [data-tag="all"]').click()
        page.locator('#grid .card[data-id="173"]').click()
        assert page.locator('#dossier[open]').count() == 1 and page.locator('#dossier-title').inner_text() == 'SCP-173'
        page.screenshot(path=str(SHOTS / f'{tag}-dossier-173.png'))
        page.locator('#tab-original').click()
        page.wait_for_function('document.querySelector("#panel-original video").getAttribute("src")')
        page.screenshot(path=str(SHOTS / f'{tag}-dossier-173-original.png'))
        page.keyboard.press('Escape'); assert page.locator('#dossier[open]').count() == 0
        assert page.evaluate('[...document.querySelectorAll("video")].every(v=>!v.getAttribute("src"))')
        assert page.evaluate('document.activeElement.dataset.id') == '173'
        passed(f'{tag}: dossier opens, Original artwork tab loads film, Escape closes, film unloaded, focus restored')
        page.locator('.section-nav [data-section="groups"]').click(); assert page.locator('#grid .card').count() == 56; no_overflow(page)
        page.screenshot(path=str(SHOTS / f'{tag}-groups.png'))
        page.locator('#grid .card[data-id="global-occult-coalition"]').click(); no_overflow(page)
        page.screenshot(path=str(SHOTS / f'{tag}-dossier-goc.png'), full_page=False)
        page.keyboard.press('Escape')
        page.locator('.section-nav [data-section="task-forces"]').click(); assert page.locator('#grid .card').count() == 108; no_overflow(page)
        page.screenshot(path=str(SHOTS / f'{tag}-task-forces.png'))
        page.locator('#grid .card[data-id="alpha-1"]').click()
        assert 'Red Right Hand' in page.locator('#dossier-title').inner_text()
        page.screenshot(path=str(SHOTS / f'{tag}-dossier-alpha-1.png'))
        page.keyboard.press('Escape')
        passed(f'{tag}: groups (56) and task forces (108) sections and dossiers')
        assert page.evaluate('''async()=>{const c=await (await fetch('collections.json')).json();for(const p of [...c.groups.map(g=>g.image),...c.taskForces.map(t=>t.insignia)]){const i=new Image();i.src=p;await i.decode();if(!i.naturalWidth)return false}return true}''')
        passed(f'{tag}: all emblem and insignia images decode')
        page.goto(BASE + '/#file-079'); page.wait_for_function('!document.querySelector("#enter").disabled'); page.locator('#enter').click()
        assert page.locator('#dossier-title').inner_text() == 'SCP-079'
        passed(f'{tag}: legacy #file-079 deep link opens the dossier')
        page.keyboard.press('Escape')
        before = page.evaluate('localStorage.getItem("raisa-muted")')
        page.locator('#mute').click(); assert page.evaluate('localStorage.getItem("raisa-muted")') != before
        assert not errors, errors
        passed(f'{tag}: no JavaScript errors')
        ctx.close()
    browser.close()
Path('/workspace/scp-archive/verification-results.json').write_text(json.dumps({'status': 'passed', 'checks': checks, 'screenshots': str(SHOTS)}, indent=2))
