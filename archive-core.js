/* RAISA archive core: pure data, search, filter and routing logic.
   No DOM access. Loaded by app.js in the browser and by tests in Node. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ArchiveCore = api;
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /** @typedef {'anomalies'|'groups'|'task-forces'} SectionKey */
  const SECTIONS = Object.freeze({
    anomalies: Object.freeze({ key: 'anomalies', prefix: 'scp', label: 'Anomalies', noun: 'record' }),
    groups: Object.freeze({ key: 'groups', prefix: 'goi', label: 'Groups of Interest', noun: 'group' }),
    'task-forces': Object.freeze({ key: 'task-forces', prefix: 'mtf', label: 'Mobile Task Forces', noun: 'task force' }),
  });
  const SECTION_KEYS = Object.freeze(Object.keys(SECTIONS));
  const PREFIX_TO_SECTION = Object.freeze(Object.fromEntries(SECTION_KEYS.map(k => [SECTIONS[k].prefix, k])));
  const OBJECT_CLASSES = Object.freeze(['Safe', 'Euclid', 'Keter', 'Thaumiel']);

  const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ESCAPES[c]);

  /** Lowercase, strip diacritics and curly quotes so "Rēsh" matches "resh". */
  const fold = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[“”‘’]/g, '').toLowerCase();
  /** Alphanumeric-only form so "alpha1", "Alpha 1" and "alpha-1" all match. */
  const compact = value => fold(value).replace(/[^a-z0-9]+/g, '');

  function haystack(parts) {
    const text = parts.filter(Boolean).join(' ');
    return { folded: fold(text), compacted: compact(text) };
  }

  /** Normalise the three sources into one card-entry shape per section. */
  function buildIndex(records, collections) {
    const media = collections.anomalyMedia;
    const anomalies = records.slice().sort((a, b) => Number(a.id) - Number(b.id)).map(r => {
      const m = media[r.id];
      if (!m) throw new Error(`No sourced image for SCP-${r.id}`);
      return {
        section: 'anomalies', id: r.id, record: r, media: m, title: r.itemNumber, subtitle: r.name,
        tags: [r.objectClass],
        search: haystack([r.itemNumber, r.name, r.id, String(Number(r.id)), r.objectClass]),
      };
    });
    const groups = collections.groups.map(g => ({
      section: 'groups', id: g.id, record: g, title: g.name, subtitle: g.categories.join(' · '),
      tags: [...g.categories, ...(g.featured ? ['Featured'] : [])],
      search: haystack([g.name, g.id, ...g.categories, ...g.specialties, g.purpose]),
    }));
    const taskForces = collections.taskForces.map(t => ({
      section: 'task-forces', id: t.id, record: t, title: t.designation, subtitle: t.callsign,
      tags: [...t.roles, ...(t.pick ? ['Archive picks'] : [])],
      search: haystack([t.kind, t.designation, t.listedAs, t.callsign, `${t.designation} ${t.callsign}`, t.greek, t.specialty, t.scope, t.listScope, ...t.roles]),
    }));
    return { anomalies, groups, 'task-forces': taskForces };
  }

  function matchesQuery(entry, query) {
    const q = fold(query).trim();
    if (!q) return true;
    const terms = q.split(/\s+/);
    return terms.every(term => entry.search.folded.includes(term) || (compact(term) && entry.search.compacted.includes(compact(term))));
  }

  /**
   * Task-force coverage: 'directory' = full dossiers from the directory page,
   * 'list' = sparse Comprehensive List entries, 'all' = both; any other value is one directory list.
   */
  function matchesCoverage(record, directory) {
    if (!directory || directory === 'all') return true;
    if (directory === 'directory') return record.coverage !== 'list';
    return record.section === directory;
  }

  /**
   * @param {Array} entries one section's entries
   * @param {{query?:string, tag?:string, greek?:string, directory?:string}} f
   */
  function filterEntries(entries, f = {}) {
    const tag = f.tag || 'all';
    return entries.filter(e =>
      (tag === 'all' || e.tags.includes(tag)) &&
      (!f.greek || f.greek === 'all' || e.record.greek === f.greek) &&
      matchesCoverage(e.record, f.directory) &&
      matchesQuery(e, f.query || ''));
  }

  /** Count entries per tag value, keeping first-seen order unless `order` is given. */
  function tagCounts(entries, order) {
    const counts = new Map((order || []).map(t => [t, 0]));
    entries.forEach(e => e.tags.forEach(t => counts.set(t, (counts.get(t) || 0) + 1)));
    return counts;
  }

  /**
   * Hash grammar:
   *   #anomalies | #groups | #task-forces          collection view
   *   #scp-173 | #goi-serpents-hand | #mtf-alpha-1 dossier
   *   #file-173 (legacy) -> #scp-173 ; #records (legacy) -> #anomalies
   * @returns {{section: SectionKey, id: (string|null)}|null}
   */
  function parseHash(hash) {
    const h = decodeURIComponent(String(hash || '').replace(/^#/, ''));
    if (!h) return null;
    if (h === 'records') return { section: 'anomalies', id: null };
    if (SECTIONS[h]) return { section: h, id: null };
    const legacy = h.match(/^file-(\d{3,4})$/);
    if (legacy) return { section: 'anomalies', id: legacy[1] };
    const m = h.match(/^(scp|goi|mtf)-([a-z0-9-]+)$/);
    if (m) return { section: PREFIX_TO_SECTION[m[1]], id: m[2] };
    return null;
  }

  function hashFor(section, id) {
    if (!SECTIONS[section]) throw new Error(`Unknown section ${section}`);
    return id ? `#${SECTIONS[section].prefix}-${id}` : `#${section}`;
  }

  return Object.freeze({ SECTIONS, SECTION_KEYS, OBJECT_CLASSES, escapeHTML, fold, compact, buildIndex, matchesQuery, filterEntries, tagCounts, parseHash, hashFor });
}));
