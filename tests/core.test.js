// Unit tests for archive-core.js. Run: node --test tests/
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../archive-core.js');
const root = path.join(__dirname, '..');
const records = JSON.parse(fs.readFileSync(path.join(root, 'data.json'), 'utf8'));
const coll = JSON.parse(fs.readFileSync(path.join(root, 'collections.json'), 'utf8'));
const idx = C.buildIndex(records, coll);

test('collection sizes: 36 dossiers, 56 groups, 108 directory task forces + Comprehensive List entries', () => {
  assert.equal(idx.anomalies.length, 36);
  assert.equal(idx.groups.length, 56);
  const st = coll.taskForceStats;
  assert.equal(idx['task-forces'].length, st.total);
  assert.equal(st.directory, 108);
  assert.equal(st.directory + st.listOnly, st.total);
  assert.equal(st.listRows, st.total - 108 + 108 + st.excluded.Vehicles + st.excluded.Joke, 'every list row is a directory unit, a list entry, or an excluded vehicle/joke row');
  assert.equal(C.filterEntries(idx['task-forces'], { directory: 'directory' }).length, 108);
  assert.equal(C.filterEntries(idx['task-forces'], { directory: 'list' }).length, st.listOnly);
  assert.equal(C.filterEntries(idx['task-forces'], { directory: 'all' }).length, st.total);
});

test('list entries never claim research they did not get', () => {
  const list = coll.taskForces.filter(t => t.coverage === 'list');
  for (const t of list) {
    assert.ok(t.listedAs && t.source.endsWith('/task-forces-complete-list'), t.id);
    assert.ok(!('mission' in t) && !('gearQuotes' in t), `${t.id} has no directory-only fields`);
    if (!t.hasInsignia) assert.equal(t.credit, 'foundation-emblem', `${t.id} placeholder is the shared emblem`);
    else assert.equal(coll.credits[t.credit].basis, 'license-box', `${t.id} insignia is license-box credited`);
  }
  for (const t of coll.taskForces.filter(x => x.coverage === 'dossier')) assert.ok(typeof t.listScope === 'string', `${t.id} matched to its list row`);
});

test('ids are unique within each section', () => {
  for (const k of C.SECTION_KEYS) assert.equal(new Set(idx[k].map(x => x.id)).size, idx[k].length, k);
});

test('every task force has a designation and a callsign; example Alpha-1 "Red Right Hand"', () => {
  for (const t of coll.taskForces) { assert.ok(t.designation); if (t.coverage === 'dossier') assert.ok(t.callsign); }
  const a1 = coll.taskForces.find(t => t.id === 'alpha-1');
  assert.equal(a1.designation, 'Alpha-1'); assert.equal(a1.callsign, 'Red Right Hand');
});

test('search: number, name, designation and callsign forms', () => {
  const ids = (s, q) => C.filterEntries(idx[s], { query: q, ...(s === 'task-forces' ? { directory: 'directory' } : {}) }).map(x => x.id);
  const all = q => C.filterEntries(idx['task-forces'], { query: q, directory: 'all' }).map(x => x.id);
  assert.deepEqual(ids('anomalies', '173'), ['173']);
  assert.ok(ids('anomalies', 'scp 682').includes('682'));
  assert.equal(ids('task-forces', 'red right hand')[0], 'alpha-1');
  assert.equal(ids('task-forces', 'Alpha1')[0], 'alpha-1');
  assert.ok(ids('task-forces', 'nine-tailed fox').includes('epsilon-11'));
  assert.ok(ids('task-forces', 'Rēsh').includes('resh-1'));
  assert.ok(all('backstreet boys').includes('tf-mtf-alpha-0-backstreet-boys'), 'list entries are searchable under All');
  assert.ok(all('alpha-9').length > ids('task-forces', 'alpha-9').length, 'reused designations surface under All');
  assert.ok(ids('groups', 'serpent').includes('serpents-hand'));
  assert.ok(ids('groups', 'GOC').includes('global-occult-coalition'));
  assert.equal(ids('groups', 'zzzz-no-match').length, 0);
});

test('filters: object class, category, role, greek letter, directory list', () => {
  const keter = C.filterEntries(idx.anomalies, { tag: 'Keter' });
  assert.ok(keter.length > 0 && keter.every(x => x.record.objectClass === 'Keter'));
  const gov = C.filterEntries(idx.groups, { tag: 'Government' });
  assert.ok(gov.some(x => x.id === 'global-occult-coalition'));
  const omega = C.filterEntries(idx['task-forces'], { greek: 'Omega' });
  assert.ok(omega.length >= 5 && omega.every(x => x.record.greek === 'Omega'));
  assert.equal(C.filterEntries(idx['task-forces'], { directory: 'additional' }).length, 17);
  assert.equal(C.filterEntries(idx['task-forces'], { directory: 'main' }).length, 89);
  const sum = C.OBJECT_CLASSES.reduce((n, c) => n + C.filterEntries(idx.anomalies, { tag: c }).length, 0);
  assert.equal(sum, 36);
});

test('hash routing round-trips and accepts legacy links', () => {
  assert.deepEqual(C.parseHash('#file-173'), { section: 'anomalies', id: '173' });
  assert.deepEqual(C.parseHash('#records'), { section: 'anomalies', id: null });
  for (const k of C.SECTION_KEYS) {
    assert.deepEqual(C.parseHash(C.hashFor(k)), { section: k, id: null });
    for (const e of idx[k]) assert.deepEqual(C.parseHash(C.hashFor(k, e.id)), { section: k, id: e.id });
  }
  assert.equal(C.parseHash('#nope'), null);
  assert.equal(C.parseHash(''), null);
});

test('escapeHTML neutralises markup', () => {
  assert.equal(C.escapeHTML(`<img src=x onerror="a('b')">&`), '&lt;img src=x onerror=&quot;a(&#39;b&#39;)&quot;&gt;&amp;');
});
