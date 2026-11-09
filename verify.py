"""Run against the live preview: python3 verify.py. No network dependency beyond localhost."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8771'
SHOTS=Path('/workspace/scp-archive-shots');SHOTS.mkdir(exist_ok=True)
checks=[]
def passed(message):
    checks.append(message);print('PASS:',message,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,reduced_motion='reduce')
    page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(BASE);page.locator('#enter').wait_for(state='visible');page.wait_for_function('!document.querySelector("#enter").disabled')
    assert page.locator('#splash').is_visible() and page.locator('#facility').is_hidden()
    assert page.evaluate('audio.ctx === null')
    page.screenshot(path=str(SHOTS/'splash.png'))
    passed('390×844 splash; audio context absent before entry')
    page.locator('#enter').click();assert page.locator('.file-card').count()==36
    assert page.locator('.card-class .class-glyph').count()==36
    assert page.evaluate('audio.ctx !== null')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(SHOTS/'archive-grid.png'))
    passed('36 records, visible class glyphs, first-gesture audio, no mobile horizontal overflow')
    page.locator('#search').fill('sculpture');assert page.locator('.file-card').count()==1
    assert page.locator('.card-item').inner_text()=='SCP-173'
    page.locator('#search').fill('999');assert page.locator('.file-card').count()==1
    page.locator('#search').fill('');page.locator('[data-class="Safe"]').click()
    assert page.locator('.file-card').count()==6
    page.locator('[data-class="Thaumiel"]').click();assert page.locator('.file-card').count()==1
    page.locator('[data-class="all"]').click();page.locator('#search').fill('no such record')
    assert page.locator('#empty').is_visible();page.locator('#reset').click();assert page.locator('.file-card').count()==36
    passed('Search, Safe/Thaumiel filters, empty state, and reset')
    for ident,cl,name in [('999','Safe','file-safe'),('173','Euclid','file-euclid'),('682','Keter','file-keter')]:
        page.locator(f'.file-card[data-id="{ident}"]').click()
        assert page.locator('#file-title').inner_text()==f'SCP-{ident}'
        assert cl.upper() in page.locator('.file-class-stamp').inner_text()
        assert page.locator('.paper-dossier h2').count()==3
        assert page.locator('.incident').count()==2
        assert page.locator('.capability-panel img').evaluate('async(el)=>{await el.decode();return el.complete && el.naturalWidth>0}')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(SHOTS/f'{name}.png'),full_page=True)
        if name!='file-euclid':page.screenshot(path=str(SHOTS/f'{name}-viewport.png'))
        page.keyboard.press('Escape');assert page.locator('#records').is_visible()
    passed('Safe 999, Euclid 173, Keter 682: containment/lore/two histories/animated visual and Escape return')
    page.locator('#mute').click();assert page.locator('#mute').get_attribute('aria-pressed')=='true'
    assert page.evaluate('audio.muted && localStorage.getItem("raisa-muted")==="true"')
    page.reload();page.locator('#enter').click();assert page.locator('#mute').get_attribute('aria-pressed')=='true'
    page.locator('#mute').click();assert page.locator('#mute').get_attribute('aria-pressed')=='false'
    passed('Mute toggles and persists after reload')
    # Verify every image and file, not just the first viewport's lazy-loaded cards.
    assert page.evaluate('''async()=>{for(const d of state.entries){for(const path of [d.icon,d.capability,d.capabilityStill]){const i=new Image();i.src=path;await i.decode();if(!i.naturalWidth)return false}}return true}''')
    for x in page.evaluate('state.entries.map(x=>x.id)'):
        page.evaluate('(id)=>openFile(id)',x)
        assert page.locator('.incident').count()==2
        assert len(page.locator('.paper-dossier').inner_text())>130
        page.evaluate('closeFile()')
    passed('All 108 SVG assets decode; all 36 dossiers render with histories')
    page.set_viewport_size({'width':1280,'height':900});page.evaluate('window.scrollTo(0,0)')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(SHOTS/'desktop-wide.png'))
    page.locator('[data-id="106"]').click();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(SHOTS/'desktop-file.png'),full_page=True)
    passed('1280px archive and full dossier responsive layout')
    page.goto(BASE+'/?deep-test#file-079');page.locator('#enter').click();assert page.locator('#file-title').inner_text()=='SCP-079'
    passed('Deep-linked record opens after entry, with splash retained before gesture')
    assert page.evaluate('audio.ctx.state')=='running'
    page.emulate_media(reduced_motion='no-preference')
    page.evaluate('openFile("999")')
    page.locator('.capability-panel img').evaluate('el=>el.decode()')
    visual=page.locator('.capability-panel img')
    frame_a=visual.screenshot()
    page.wait_for_timeout(1300)
    frame_b=visual.screenshot()
    assert frame_a != frame_b
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_function('document.querySelector(".capability-panel img").currentSrc.includes("static.svg")')
    visual.evaluate('el=>el.decode()')
    frame_a=visual.screenshot()
    page.wait_for_timeout(350)
    frame_b=visual.screenshot()
    assert frame_a == frame_b
    passed('SVG motion changes rendered pixels; reduced motion freezes it; Web Audio context running')
    assert not errors,errors
    passed('No browser JavaScript errors')
    browser.close()
Path('/workspace/scp-archive/verification-results.json').write_text(json.dumps({'status':'passed','checks':checks,'screenshots':str(SHOTS),'mobileViewport':'390x844','desktopViewport':'1280x900'},indent=2))
