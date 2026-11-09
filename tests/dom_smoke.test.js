// DOM smoke test in jsdom (NOT a real browser: no layout, media playback or CSS).
// Requires jsdom; run: NODE_PATH=/workspace/scp-overhaul-testdeps/node_modules node --test tests/dom_smoke.test.js
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.join(__dirname, '..');

function boot(hash = '') {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8').replace(/<script[^>]*><\/script>/g, '');
  const dom = new JSDOM(html, { url: 'http://127.0.0.1:8771/' + hash, runScripts: 'outside-only', pretendToBeVisual: true });
  const w = dom.window;
  const media = { pauses: 0, loads: 0 };
  w.HTMLMediaElement.prototype.pause = function () { media.pauses++; };
  w.HTMLMediaElement.prototype.load = function () { media.loads++; };
  w.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  w.HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
  w.matchMedia = () => ({ matches: false, addEventListener() {} });
  w.scrollTo = () => {};
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.fetch = async url => ({ ok: true, json: async () => JSON.parse(fs.readFileSync(path.join(root, String(url)), 'utf8')) });
  for (const f of ['archive-core.js', 'app.js']) w.eval(fs.readFileSync(path.join(root, f), 'utf8'));
  return { w, d: w.document, media };
}
const tick = () => new Promise(r => setTimeout(r, 30));
const click = (w, el) => el.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));

test('entry, three sections, search, filters, counts', async () => {
  const { w, d } = boot();
  await tick();
  const enter = d.querySelector('#enter');
  assert.equal(enter.disabled, false);
  click(w, enter); await tick();
  assert.equal(d.querySelector('#facility').hidden, false);
  assert.equal(w.location.hash, '#anomalies');
  assert.equal(d.querySelectorAll('#grid .card').length, 36);
  assert.ok([...d.querySelectorAll('#grid img')].every(i => i.getAttribute('src').startsWith('assets/sourced/scp/')), 'cards show sourced images, not generated art');
  const search = d.querySelector('#search');
  search.value = '173'; search.dispatchEvent(new w.Event('input', { bubbles: true }));
  assert.equal(d.querySelectorAll('#grid .card').length, 1);
  search.value = ''; search.dispatchEvent(new w.Event('input', { bubbles: true }));
  click(w, d.querySelector('#chips [data-tag="Keter"]'));
  const keter = d.querySelectorAll('#grid .card').length;
  assert.ok(keter > 0 && keter < 36);
  assert.match(d.querySelector('#result-count').textContent, new RegExp(`^${keter} records? shown of 36`));
  click(w, d.querySelector('.section-nav [data-section="groups"]'));
  assert.equal(w.location.hash, '#groups');
  assert.equal(d.querySelectorAll('#grid .card').length, 56);
  click(w, d.querySelector('.section-nav [data-section="task-forces"]'));
  assert.equal(d.querySelectorAll('#grid .card').length, 108);
  assert.equal(d.querySelector('#mtf-selects').hidden, false);
  search.value = 'red right hand'; search.dispatchEvent(new w.Event('input', { bubbles: true }));
  assert.deepEqual([...d.querySelectorAll('#grid .card')].map(c => c.dataset.id), ['alpha-1']);
  search.value = ''; search.dispatchEvent(new w.Event('input', { bubbles: true }));
  const greek = d.querySelector('#greek'); greek.value = 'Omega'; greek.dispatchEvent(new w.Event('change', { bubbles: true }));
  assert.ok([...d.querySelectorAll('#grid .card-title')].every(t => t.textContent.startsWith('Omega')));
  click(w, d.querySelector('.section-nav [data-section="anomalies"]'));
  assert.equal(d.querySelectorAll('#grid .card').length, keter, 'per-section filter state is kept');
});

test('anomaly dossier: image first, original artwork tab, video lifecycle, close and focus', async () => {
  const { w, d, media } = boot();
  await tick(); click(w, d.querySelector('#enter')); await tick();
  const card = d.querySelector('#grid .card[data-id="173"]');
  card.focus();
  click(w, card);
  const dlg = d.querySelector('#dossier');
  assert.ok(dlg.hasAttribute('open'));
  assert.equal(w.location.hash, '#scp-173');
  assert.equal(d.querySelector('#dossier-title').textContent, 'SCP-173');
  assert.equal(d.activeElement.id, 'dossier-title');
  assert.match(d.querySelector('#panel-image img').getAttribute('src'), /^assets\/sourced\/scp\/173\.webp$/);
  assert.match(d.querySelector('#panel-image .credit-line a[href^="credits.html#credit-scp-173"]').textContent, /Full credit/);
  assert.equal(d.querySelector('#panel-original').hidden, true);
  const video = d.querySelector('#panel-original video');
  assert.equal(video.getAttribute('src'), null, 'film does not load while hidden');
  click(w, d.querySelector('#tab-original'));
  assert.equal(d.querySelector('#panel-original').hidden, false);
  assert.equal(video.getAttribute('src'), 'assets/videos/173.mp4');
  assert.ok(d.querySelector('#panel-original img[src="assets/file-173.svg"]'), 'generated plate kept behind the tab');
  const p0 = media.pauses;
  click(w, d.querySelector('#tab-image'));
  assert.equal(video.getAttribute('src'), null, 'switching tab unloads the film');
  assert.ok(media.pauses > p0);
  click(w, d.querySelector('#tab-original'));
  const v2 = d.querySelector('#panel-original video');
  // switch straight to another dossier while the film is loaded
  click(w, d.querySelector('.section-nav [data-section="anomalies"]'));
  assert.equal(dlg.hasAttribute('open'), false);
  assert.equal(v2.getAttribute('src'), null, 'closing unloads the film');
  click(w, d.querySelector('#grid .card[data-id="096"]'));
  assert.equal(w.location.hash, '#scp-096');
  click(w, d.querySelector('#tab-original'));
  const v3 = d.querySelector('#panel-original video');
  dlg.dispatchEvent(new w.Event('cancel', { cancelable: true })); // Escape
  assert.equal(dlg.hasAttribute('open'), false);
  assert.equal(v3.getAttribute('src'), null);
  assert.equal(w.location.hash, '#anomalies');
  assert.equal(d.activeElement.dataset.id, '096', 'focus returns to the card that opened it');
});

test('opening one dossier from another stops the previous film', async () => {
  const { w, d } = boot('#scp-049');
  await tick(); click(w, d.querySelector('#enter')); await tick();
  assert.equal(d.querySelector('#dossier-title').textContent, 'SCP-049');
  click(w, d.querySelector('#tab-original'));
  const v = d.querySelector('#panel-original video');
  assert.ok(v.getAttribute('src'));
  w.history.pushState({}, '', '#scp-682');
  w.dispatchEvent(new w.PopStateEvent('popstate'));
  assert.equal(d.querySelector('#dossier-title').textContent, 'SCP-682');
  assert.equal(v.getAttribute('src'), null);
});

test('group and task force dossiers have lore, purpose, specialties and gear', async () => {
  const { w, d } = boot('#goi-serpents-hand');
  await tick(); click(w, d.querySelector('#enter')); await tick();
  const dlg = d.querySelector('#dossier');
  assert.ok(dlg.hasAttribute('open'));
  const heads = [...dlg.querySelectorAll('.d-section h3')].map(h => h.textContent);
  assert.deepEqual(heads.map(h => h.replace(/^\d+/, '')), ['Lore — official directory brief', 'Origins & purpose', 'Specialties', 'Gear & weapons']);
  assert.ok(dlg.querySelector('a[href="credits.html#credit-goi-serpents-hand"]'));
  w.history.pushState({}, '', '#mtf-alpha-1'); w.dispatchEvent(new w.PopStateEvent('popstate'));
  assert.match(d.querySelector('#dossier-title').textContent, /Alpha-1\s+“Red Right Hand”/);
  assert.equal(dlg.querySelectorAll('.d-section').length, 5);
  w.history.pushState({}, '', '#mtf-lambda-9'); w.dispatchEvent(new w.PopStateEvent('popstate'));
  assert.ok(dlg.querySelector('.emblem-figure.no-insignia .emblem-overlay'));
  assert.match(dlg.querySelector('.gap-note').textContent, /no insignia/);
  w.history.pushState({}, '', '#groups'); w.dispatchEvent(new w.PopStateEvent('popstate'));
  assert.equal(dlg.hasAttribute('open'), false);
  assert.equal(d.querySelectorAll('#grid .card').length, 56);
});

test('legacy #file- links still open the dossier; bad ids fall back to the section', async () => {
  const a = boot('#file-096'); await tick(); click(a.w, a.d.querySelector('#enter')); await tick();
  assert.equal(a.d.querySelector('#dossier-title').textContent, 'SCP-096');
  assert.equal(a.w.location.hash, '#scp-096');
  const b = boot('#mtf-not-a-unit'); await tick(); click(b.w, b.d.querySelector('#enter')); await tick();
  assert.equal(b.d.querySelector('#dossier').hasAttribute('open'), false);
  assert.equal(b.w.location.hash, '#task-forces');
});

test('mute preference persists under the existing raisa-muted key', async () => {
  const { w, d } = boot(); await tick(); click(w, d.querySelector('#enter')); await tick();
  const before = w.localStorage.getItem('raisa-muted');
  click(w, d.querySelector('#mute'));
  assert.notEqual(w.localStorage.getItem('raisa-muted'), before);
  assert.equal(d.querySelector('#mute').getAttribute('aria-pressed'), w.localStorage.getItem('raisa-muted'));
});

test('every one of the 200 dossiers renders with a title, an image and a credit link, with unique ids', async () => {
  const { w, d } = boot(); await tick(); click(w, d.querySelector('#enter')); await tick();
  const c = JSON.parse(fs.readFileSync(path.join(root, 'collections.json'), 'utf8'));
  const routes = [...Object.keys(c.anomalyMedia).map(id => `#scp-${id}`), ...c.groups.map(g => `#goi-${g.id}`), ...c.taskForces.map(t => `#mtf-${t.id}`)];
  assert.equal(routes.length, 200);
  for (const r of routes) {
    w.history.pushState({}, '', r); w.dispatchEvent(new w.PopStateEvent('popstate'));
    const dlg = d.querySelector('#dossier');
    assert.ok(dlg.hasAttribute('open'), r);
    assert.ok(d.querySelector('#dossier-title').textContent.trim().length > 2, r);
    assert.ok(dlg.querySelector('.dossier-media img'), r);
    assert.ok(dlg.querySelector('a[href^="credits.html#credit-"]'), r);
    const ids = [...d.querySelectorAll('[id]')].map(x => x.id);
    assert.equal(new Set(ids).size, ids.length, `duplicate id in ${r}`);
    assert.ok(!/undefined|\[object Object\]|null/.test(dlg.textContent.replace(/nullif/gi, '')), `stray value in ${r}`);
  }
});
