// jsdom smoke for the offline single-file preview (NOT a real browser).
// Run: NODE_PATH=/workspace/scp-overhaul-testdeps/node_modules node --test tests/standalone_smoke.test.js
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.env.STANDALONE || path.join(__dirname, '..', '..', 'scp-archive-offline', 'index.html');

test('offline single file boots with embedded data and data: URLs only', async () => {
  const errors = [];
  const vc = new VirtualConsole(); vc.on('jsdomError', e => errors.push(e.message)); vc.on('error', e => errors.push(String(e)));
  const html = fs.readFileSync(file, 'utf8');
  assert.ok(!/(src|href)="assets\//.test(html), 'no relative asset references in markup');
  const dom = new JSDOM(html, { url: 'file:///preview/index.html', runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) {
      w.Response = Response; w.fetch = undefined;
      w.HTMLMediaElement.prototype.pause = function () {}; w.HTMLMediaElement.prototype.load = function () {};
      w.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
      w.HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
      w.matchMedia = () => ({ matches: false, addEventListener() {} }); w.scrollTo = () => {};
      w.HTMLElement.prototype.scrollIntoView = function () {};
    } });
  const w = dom.window, d = w.document;
  await new Promise(r => setTimeout(r, 200));
  const click = el => el.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  assert.equal(d.querySelector('#enter').disabled, false, 'data loaded through the embedded fetch shim');
  click(d.querySelector('#enter')); await new Promise(r => setTimeout(r, 30));
  const counts = {};
  for (const s of ['anomalies', 'groups', 'task-forces']) {
    click(d.querySelector(`.section-nav [data-section="${s}"]`)); await new Promise(r => setTimeout(r, 30));
    counts[s] = d.querySelectorAll('#grid .card').length;
    assert.ok([...d.querySelectorAll('#grid img')].every(i => i.getAttribute('src').startsWith('data:image/')), `${s} images are embedded`);
  }
  assert.deepEqual(counts, { anomalies: 36, groups: 56, 'task-forces': 60 }, 'task forces render the first page of 60 dossiers');
  click(d.querySelector('.section-nav [data-section="anomalies"]')); await new Promise(r => setTimeout(r, 30));
  click(d.querySelector('#grid .card[data-id="173"]')); await new Promise(r => setTimeout(r, 30));
  const dlg = d.querySelector('dialog');
  assert.ok(dlg.hasAttribute('open'), 'dossier opens');
  const vids = [...dlg.querySelectorAll('video')].flatMap(v => [v.dataset.src, v.getAttribute('poster')]);
  assert.ok(vids.length && vids[0].startsWith('data:video/mp4') && vids[1].startsWith('data:image/'), 'film and poster embedded');
  assert.deepEqual(errors, []);
  console.log('counts', counts, 'html MB', (html.length / 1e6).toFixed(1));
});
