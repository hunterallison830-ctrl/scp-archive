'use strict';
/* RAISA archive UI. Pure logic lives in archive-core.js (window.ArchiveCore). */
const { SECTIONS, SECTION_KEYS, OBJECT_CLASSES, escapeHTML: e, buildIndex, filterEntries, tagCounts, parseHash, hashFor } = window.ArchiveCore;
const $ = s => document.querySelector(s);

const GOI_CATEGORIES = ['Foundation Precursors', 'Government', 'Corporate', 'Religious', 'Educational', 'Research', 'Artistic', 'Media', 'Online', 'Non-Profit', 'Criminal', 'Insurgents', 'Alternate Realities', 'Other', 'International'];
const MTF_ROLES = ['Combat & rapid response', 'Command & oversight', 'Undercover & intelligence', 'GoI counter-operations', 'Mind, memetic & info hazards', 'Occult & reality', 'Environment specialists', 'Bio & physical hazards', 'General containment'];
const DIRECTORY_SECTIONS = { main: 'Main directory', additional: 'Additional MTFs', distributed: 'Distributed Task Force', special: 'Special Task Force' };
const SECTION_COPY = {
  anomalies: { eyebrow: 'Containment records', heading: 'Anomalies', lede: 'Thirty-six containment dossiers. Every card shows a credited community image of that SCP. Open a dossier to read it, or switch to the original artwork tab.' },
  groups: { eyebrow: 'Intelligence division', heading: 'Groups of Interest', lede: 'Every organisation in the official Groups of Interest directory, from the Global Occult Coalition to the Serpent\u2019s Hand. Each dossier covers lore, origins and purpose, specialties, and documented gear.' },
  'task-forces': { eyebrow: 'Operations directory', heading: 'Mobile Task Forces', lede: 'Every unit on the official Mobile Task Forces directory page, with its designation, callsign and insignia, from Alpha-1 \u201cRed Right Hand\u201d onward.' },
};

const state = {
  index: null, collections: null, entered: false, section: 'anomalies', open: null, returnFocus: null,
  filters: { anomalies: { query: '', tag: 'all' }, groups: { query: '', tag: 'all' }, 'task-forces': { query: '', tag: 'all', greek: 'all', directory: 'all' } },
};

/* ---------------------------------------------------------------- audio */
class FacilityAudio {
  constructor() { this.ctx = null; this.master = null; this.muted = false; try { this.muted = localStorage.getItem('raisa-muted') === 'true'; } catch { /* storage unavailable */ } }
  async start() {
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.master = this.ctx.createGain(); this.master.gain.value = this.muted ? 0 : 0.12; this.master.connect(this.ctx.destination);
      await this.ctx.resume();
      [42, 84].forEach((f, i) => { const osc = this.ctx.createOscillator(), g = this.ctx.createGain(); osc.type = 'sine'; osc.frequency.value = f; g.gain.value = i ? 0.025 : 0.065; osc.connect(g); g.connect(this.master); osc.start(); });
      this.effect('entry');
    } catch { this.muted = true; }
    this.update();
  }
  effect(kind) {
    if (!this.ctx || this.ctx.state !== 'running' || this.muted) return;
    const c = this.ctx, t = c.currentTime, d = kind === 'entry' ? 0.65 : kind === 'close' ? 0.35 : 0.18;
    const buffer = c.createBuffer(1, Math.floor(c.sampleRate * d), c.sampleRate), data = buffer.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / data.length, 3);
    const source = c.createBufferSource(), filter = c.createBiquadFilter(), gain = c.createGain();
    source.buffer = buffer; filter.type = 'lowpass'; filter.frequency.value = kind === 'entry' ? 850 : 1400;
    gain.gain.setValueAtTime(kind === 'file' ? 0.55 : 0.28, t); gain.gain.exponentialRampToValueAtTime(0.001, t + d);
    source.connect(filter); filter.connect(gain); gain.connect(this.master); source.start(t); source.stop(t + d);
    source.onended = () => { source.disconnect(); filter.disconnect(); gain.disconnect(); };
    const tone = (f0, f1, start, len, peak) => { const o = c.createOscillator(), g = c.createGain(); o.frequency.setValueAtTime(f0, start); if (f1) o.frequency.exponentialRampToValueAtTime(f1, start + len * 0.8); g.gain.setValueAtTime(0.001, start); g.gain.linearRampToValueAtTime(peak, start + 0.02); g.gain.exponentialRampToValueAtTime(0.001, start + len); o.connect(g); g.connect(this.master); o.start(start); o.stop(start + len + 0.01); o.onended = () => { o.disconnect(); g.disconnect(); }; };
    if (kind === 'entry') [330, 247].forEach((f, i) => tone(f, 0, t + i * 0.22, 0.3, 0.035));
    if (kind === 'file') tone(115, 48, t, 0.12, 0.28);
  }
  toggle() {
    this.muted = !this.muted;
    try { localStorage.setItem('raisa-muted', String(this.muted)); } catch { /* storage unavailable */ }
    if (this.ctx) { this.ctx.resume().catch(() => {}); this.master.gain.setTargetAtTime(this.muted ? 0 : 0.12, this.ctx.currentTime, 0.08); }
    this.update();
  }
  update() {
    document.querySelectorAll('video').forEach(v => { v.muted = this.muted; });
    const b = $('#mute');
    b.setAttribute('aria-pressed', String(this.muted));
    b.setAttribute('aria-label', this.muted ? 'Unmute facility audio' : 'Mute facility audio');
    b.querySelector('.mute-label').textContent = this.muted ? 'Muted' : 'Audio on';
    b.classList.toggle('is-muted', this.muted);
  }
}
const audio = new FacilityAudio();

/* ---------------------------------------------------------------- helpers */
const credits = id => state.collections.credits[id];
const classSlug = cl => cl.toLowerCase();
const count = (n, noun) => `${n} ${noun}${n === 1 ? '' : 's'}`;
const linkOut = (href, label) => `<a href="${e(href)}" target="_blank" rel="noopener">${e(label)}</a>`;
const shortLicense = l => l.replace(' (page license)', '');

function creditLine(cid, anchor) {
  const c = credits(cid);
  return `<p class="credit-line"><span class="credit-k">Image</span> ${e(c.author)} · ${e(shortLicense(c.license))} · ${linkOut(c.page, 'Source')} · <a href="credits.html#${e(anchor)}">Full credit</a></p>`;
}

/* ---------------------------------------------------------------- cards */
function cardHTML(entry, i) {
  const lazy = i > 7 ? 'loading="lazy"' : '';
  if (entry.section === 'anomalies') {
    const r = entry.record, m = entry.media;
    return `<li><button class="card card-anomaly" data-section="anomalies" data-id="${e(r.id)}" aria-label="Open ${e(r.itemNumber)}, ${e(r.name)}, object class ${e(r.objectClass)}">
      <span class="card-media media-${e(m.fit)}"><img src="${e(m.image)}" alt="" width="${m.w}" height="${m.h}" style="object-position:${e(m.pos)}" ${lazy} decoding="async"></span>
      <span class="card-shade" aria-hidden="true"></span>
      <span class="card-top"><span class="card-num">${e(r.itemNumber)}</span><span class="class-badge class-${classSlug(r.objectClass)}">${e(r.objectClass)}</span></span>
      <span class="card-foot"><span class="card-title">${e(r.name)}</span><span class="card-meta">${e(r.stamp)}</span></span></button></li>`;
  }
  if (entry.section === 'groups') {
    const g = entry.record;
    return `<li><button class="card card-emblem card-group" data-section="groups" data-id="${e(g.id)}" aria-label="Open ${e(g.name)} dossier">
      <span class="emblem-plate plate-${e(g.plate)}"><img src="${e(g.image)}" alt="" width="${g.w}" height="${g.h}" ${lazy} decoding="async"></span>
      <span class="card-foot"><span class="card-kicker">${e(g.categories[0])}${g.featured ? ' · Featured' : ''}</span><span class="card-title">${e(g.name)}</span></span></button></li>`;
  }
  const t = entry.record;
  return `<li><button class="card card-emblem card-mtf${t.hasInsignia ? '' : ' no-insignia'}" data-section="task-forces" data-id="${e(t.id)}" aria-label="Open ${e(t.kind)} ${e(t.designation)} “${e(t.callsign)}” dossier">
    <span class="emblem-plate plate-${e(t.plate)}">${t.hasInsignia ? '' : `<span class="emblem-overlay" aria-hidden="true">${e(t.designation)}</span>`}<img src="${e(t.insignia)}" alt="" width="480" height="480" ${lazy} decoding="async"></span>
    <span class="card-foot"><span class="card-kicker">${e(t.kind)} · ${e(t.greek)}${t.section !== 'main' ? ` · ${e(DIRECTORY_SECTIONS[t.section])}` : ''}</span><span class="card-title mono">${e(t.designation)}</span><span class="card-callsign">“${e(t.callsign)}”</span></span></button></li>`;
}

/* ---------------------------------------------------------------- toolbar */
function chip(tag, label, n, active) {
  return `<button type="button" class="chip${active ? ' active' : ''}" data-tag="${e(tag)}" aria-pressed="${active}">${tag !== 'all' && OBJECT_CLASSES.includes(tag) ? `<i class="class-dot class-${classSlug(tag)}" aria-hidden="true"></i>` : ''}${e(label)} <span class="chip-count">${n}</span></button>`;
}

function renderToolbar() {
  const s = state.section, f = state.filters[s], list = state.index[s];
  const order = s === 'anomalies' ? OBJECT_CLASSES : s === 'groups' ? ['Featured', ...GOI_CATEGORIES] : ['Archive picks', ...MTF_ROLES];
  const counts = tagCounts(list, order);
  $('#chips').innerHTML = chip('all', 'All', list.length, f.tag === 'all') + order.filter(t => counts.get(t)).map(t => chip(t, t, counts.get(t), f.tag === t)).join('');
  $('#chips').setAttribute('aria-label', s === 'anomalies' ? 'Filter by object class' : s === 'groups' ? 'Filter by directory category' : 'Filter by role (editorial grouping)');
  $('#search').value = f.query;
  $('#search').placeholder = s === 'anomalies' ? 'Item number or name, e.g. 173' : s === 'groups' ? 'Name, category or specialty' : 'Designation or callsign, e.g. Alpha-1';
  $('#search-label').textContent = `Search ${SECTIONS[s].label.toLowerCase()}`;
  const extra = $('#mtf-selects');
  extra.hidden = s !== 'task-forces';
  if (s === 'task-forces') {
    const greekCounts = new Map();
    list.forEach(x => greekCounts.set(x.record.greek, (greekCounts.get(x.record.greek) || 0) + 1));
    $('#greek').innerHTML = `<option value="all">All letters (${list.length})</option>` + [...greekCounts].map(([g, n]) => `<option value="${e(g)}">${e(g)} (${n})</option>`).join('');
    $('#greek').value = f.greek;
    const dirCounts = new Map();
    list.forEach(x => dirCounts.set(x.record.section, (dirCounts.get(x.record.section) || 0) + 1));
    $('#directory').innerHTML = `<option value="all">Whole directory (${list.length})</option>` + Object.entries(DIRECTORY_SECTIONS).map(([k, l]) => `<option value="${k}">${e(l)} (${dirCounts.get(k) || 0})</option>`).join('');
    $('#directory').value = f.directory;
  }
}

function renderGrid() {
  const s = state.section, results = filterEntries(state.index[s], state.filters[s]);
  $('#grid').className = `grid grid-${s}`;
  $('#grid').innerHTML = results.map(cardHTML).join('');
  $('#result-count').textContent = `${count(results.length, SECTIONS[s].noun)} shown of ${state.index[s].length}`;
  $('#empty').hidden = results.length > 0;
  document.querySelectorAll('#chips .chip').forEach(b => { const on = b.dataset.tag === state.filters[s].tag; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
}

function renderSection(section, { focus = false } = {}) {
  state.section = section;
  const copy = SECTION_COPY[section];
  $('#collection-eyebrow').textContent = copy.eyebrow;
  $('#collection-title').textContent = copy.heading;
  $('#collection-lede').textContent = copy.lede;
  $('#collection').dataset.section = section;
  document.querySelectorAll('.section-link').forEach(a => { const on = a.dataset.section === section; a.classList.toggle('active', on); if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  $('#mtf-note').hidden = section !== 'task-forces';
  renderToolbar();
  renderGrid();
  document.title = `${SECTIONS[section].label} · RAISA Archive`;
  if (focus) $('#collection-title').focus({ preventScroll: true });
}

/* ---------------------------------------------------------------- dossiers */
function linkList(items, label, limit = 14) {
  if (!items.length) return '';
  const li = x => `<li>${linkOut(x.href, x.label)}</li>`;
  const head = items.slice(0, limit).map(li).join(''), rest = items.slice(limit);
  return `<div class="link-group"><h4>${e(label)} <span class="muted">(${items.length})</span></h4><ul class="link-chips">${head}</ul>${rest.length ? `<details><summary>Show ${rest.length} more</summary><ul class="link-chips">${rest.map(li).join('')}</ul></details>` : ''}</div>`;
}

function dossierShell({ eyebrow, title, subtitle, badges = '', media, body, kind }) {
  return `<div class="dossier dossier-${kind}">
    <header class="dossier-head"><div class="hazard" aria-hidden="true"></div>
      <div class="dossier-head-inner"><div><p class="eyebrow">${eyebrow}</p><h2 id="dossier-title" tabindex="-1">${title}</h2>${subtitle ? `<p class="dossier-subtitle">${subtitle}</p>` : ''}${badges ? `<div class="badges">${badges}</div>` : ''}</div>
      <button type="button" class="close-dossier" data-close aria-label="Close dossier"><span aria-hidden="true">✕</span><span class="close-text">Close</span></button></div></header>
    <div class="dossier-grid"><aside class="dossier-media">${media}</aside><article class="dossier-body">${body}</article></div>
    <footer class="dossier-foot"><span class="mono tiny">RAISA / READ-ONLY COPY</span><button type="button" class="outline-button" data-close>Close dossier</button></footer></div>`;
}

function section(index, heading, inner) {
  return `<section class="d-section"><h3><span class="d-index">${index}</span>${e(heading)}</h3>${inner}</section>`;
}

function anomalyDossier(r, m) {
  const media = `<div class="media-tabs" role="tablist" aria-label="Visual record">
      <button type="button" role="tab" id="tab-image" aria-controls="panel-image" aria-selected="true" class="media-tab">Image</button>
      <button type="button" role="tab" id="tab-original" aria-controls="panel-original" aria-selected="false" tabindex="-1" class="media-tab media-tab-small">Original artwork</button></div>
    <div role="tabpanel" id="panel-image" aria-labelledby="tab-image" class="media-panel">
      <figure class="sourced-figure media-${e(m.fit)}"><img src="${e(m.image)}" alt="Credited community image of ${e(r.itemNumber)}, ${e(r.name)}" width="${m.w}" height="${m.h}"></figure>
      ${creditLine(m.credit, `credit-scp-${r.id}`)}</div>
    <div role="tabpanel" id="panel-original" aria-labelledby="tab-original" class="media-panel" hidden>
      <p class="original-note">Original artwork made for this archive: a six-second overview film and two illustrated plates. These are not downloaded images.</p>
      ${r.overview ? `<figure class="original-figure"><video class="overview-video" data-src="${e(r.overview)}" poster="${e(r.icon)}" controls playsinline preload="none" aria-label="Original overview film for ${e(r.itemNumber)}"></video><figcaption>Overview film · original reconstruction · 0:06</figcaption></figure>` : ''}
      <div class="original-pair"><figure class="original-figure"><img src="${e(r.icon)}" alt="Original illustration of ${e(r.name)}" width="480" height="360" loading="lazy"><figcaption>Specimen plate</figcaption></figure>
      <figure class="original-figure"><picture><source media="(prefers-reduced-motion: reduce)" srcset="${e(r.capabilityStill)}"><img src="${e(r.capability)}" alt="Original behavioural reconstruction for ${e(r.itemNumber)}" width="480" height="360" loading="lazy"></picture><figcaption>${e(r.capabilityLabel || 'Behavioural reconstruction')}</figcaption></figure></div></div>`;
  const body = section('01', 'Special containment procedures', `<p>${e(r.containment)}</p>`)
    + section('02', 'Description', `<p>${e(r.description)}</p>`)
    + section('03', 'History / incident log', r.incidentHistory.map(l => `<div class="incident"><time>${e(l.date)}</time><p>${e(l.text)}</p></div>`).join('') + '<p class="fine">Incident vignettes are original fan fiction, not canon.</p>')
    + `<p class="source-row">${linkOut(r.source, `Read ${r.itemNumber} on the SCP Wiki ↗`)}</p>`;
  return dossierShell({ kind: 'anomaly', eyebrow: `Containment dossier · ${r.id === '2521' ? '◼◼◼' : e(r.stamp)}`, title: e(r.itemNumber), subtitle: e(r.name),
    badges: `<span class="class-badge class-${classSlug(r.objectClass)}">Object class: ${e(r.objectClass)}</span>`, media, body });
}

function gearBlock(summary, quotes, emptyText) {
  const q = quotes.length ? `<div class="evidence"><p class="evidence-k">Documented in the directory entry</p>${quotes.map(x => `<blockquote>${e(x)}</blockquote>`).join('')}</div>` : '';
  if (summary) return `<p>${e(summary)}</p>${q}`;
  return quotes.length ? q : `<p class="not-specified">${e(emptyText)}</p>`;
}

function groupDossier(g) {
  const fa = g.firstAppearance;
  const media = `<figure class="emblem-figure plate-${e(g.plate)}"><img src="${e(g.image)}" alt="Emblem of ${e(g.name)}" width="${g.w}" height="${g.h}"></figure>${creditLine(g.credit, `credit-goi-${g.id}`)}
    <dl class="facts"><dt>Directory</dt><dd>${g.section === 'main' ? 'Main list' : 'Additional Groups of Interest'}</dd>
    <dt>Categories</dt><dd>${g.categories.map(e).join(', ')}</dd>
    ${fa ? `<dt>First wiki appearance</dt><dd>${e([fa.date, fa.year].filter(Boolean).join(' '))}${fa.by ? ` · by ${e(fa.by)}` : ''}</dd>` : ''}
    ${g.international ? '<dt>Origin</dt><dd>Translated from another SCP Wiki branch</dd>' : ''}</dl>`;
  const body = section('01', 'Lore — official directory brief', `<blockquote class="lore">${g.lore.map(p => `<p>${e(p)}</p>`).join('')}</blockquote><p class="fine">Quoted from the ${linkOut(g.loreSource, 'Groups of Interest directory')} (SCP Wiki community, CC BY-SA 3.0).</p>`)
    + section('02', 'Origins & purpose', `<p>${e(g.purpose)}</p>`)
    + section('03', 'Specialties', `<ul class="spec-list">${g.specialties.map(x => `<li>${e(x)}</li>`).join('')}</ul>`)
    + section('04', 'Gear & weapons', gearBlock(g.gear, g.gear ? [] : g.gearQuotes, 'Not specified in the primary directory entry.'))
    + (g.continuity ? `<aside class="continuity" role="note"><strong>Continuity note</strong><p>${e(g.continuity)}</p></aside>` : '')
    + `<p class="source-row">${linkOut(g.hub, 'Open the group hub ↗')} ${linkOut(g.loreSource, 'Directory entry ↗')}</p>`;
  return dossierShell({ kind: 'group', eyebrow: 'Group of Interest · intelligence file', title: e(g.name), badges: `${g.featured ? '<span class="tag tag-hazard">Featured</span>' : ''}${g.categories.map(c => `<span class="tag">${e(c)}</span>`).join('')}`, media, body });
}

function mtfDossier(t) {
  const media = `<figure class="emblem-figure plate-${e(t.plate)}${t.hasInsignia ? '' : ' no-insignia'}">${t.hasInsignia ? '' : `<span class="emblem-overlay" aria-hidden="true">${e(t.designation)}</span>`}<img src="${e(t.insignia)}" alt="${t.hasInsignia ? `Insignia of ${e(t.kind)} ${e(t.designation)}` : 'Shared Foundation emblem (no unit insignia on the directory)'}" width="480" height="480"></figure>
    ${t.hasInsignia ? '' : '<p class="gap-note">This unit has no insignia on the directory page, so the shared Foundation emblem is shown instead.</p>'}
    ${creditLine(t.credit, t.hasInsignia ? `credit-mtf-${t.id}` : `credit-mtf-${t.id}`)}
    <dl class="facts"><dt>Designation</dt><dd class="mono">${e(t.kind)} ${e(t.designation)}</dd><dt>Callsign</dt><dd>“${e(t.callsign)}”</dd>
    <dt>Directory</dt><dd>${e(DIRECTORY_SECTIONS[t.section])}</dd><dt>Role grouping</dt><dd>${t.roles.map(e).join(', ')} <span class="muted">(editorial)</span></dd></dl>`;
  const lore = t.mission ? `<blockquote class="lore"><p>${e(t.mission)}</p></blockquote><p class="fine">Mission statement quoted from the ${linkOut(t.missionSource, 'Mobile Task Forces directory')} (SCP Wiki community, CC BY-SA 3.0).</p>`
    : '<p class="not-specified">The directory entry gives no mission statement for this unit. Its linked articles are listed below.</p>';
  const gearSummary = t.utilizing.length ? `The directory lists ${count(t.utilizing.length, 'anomalous object')} this unit uses in the field (below).` : null;
  const body = section('01', 'Lore — directory mission', lore)
    + section('02', 'Purpose', t.purpose ? `<p>${e(t.purpose)}</p>` : '<p class="not-specified">Not stated in the directory entry.</p>')
    + section('03', 'Specialty', t.specialty ? `<p>Specializes in ${e(t.specialty)}.</p>` : '<p class="not-specified">Not stated in the directory entry.</p>')
    + section('04', 'Gear & weapons', gearBlock(gearSummary, t.gearQuotes, 'Not specified in the directory entry. No canonical loadout is listed.') + linkList(t.utilizing, 'Objects utilized'))
    + section('05', 'Documented in', (linkList(t.deployments, 'Known deployments') + linkList(t.assisting, 'Assisting in containment of') + linkList(t.reports, 'Action reports')) || '<p class="not-specified">No linked articles.</p>');
  return dossierShell({ kind: 'mtf', eyebrow: `${e(t.kind)} · operations file`, title: `<span class="mono">${e(t.designation)}</span> <span class="callsign">“${e(t.callsign)}”</span>`,
    badges: `${t.pick ? '<span class="tag tag-hazard">Archive pick</span>' : ''}<span class="tag">${e(DIRECTORY_SECTIONS[t.section])}</span>`, media, body });
}

/* Video and tab lifecycle: the film element only receives a src while its tab is visible. */
function stopVideos(root = $('#dossier')) {
  root.querySelectorAll('video').forEach(v => { v.pause(); if (v.getAttribute('src')) { v.removeAttribute('src'); v.load(); } });
}

function selectMediaTab(tab, { focus = false } = {}) {
  const dialog = $('#dossier');
  dialog.querySelectorAll('[role="tab"]').forEach(t => {
    const on = t === tab;
    t.setAttribute('aria-selected', String(on)); t.tabIndex = on ? 0 : -1;
    const panel = document.getElementById(t.getAttribute('aria-controls'));
    panel.hidden = !on;
    if (!on) stopVideos(panel);
    else panel.querySelectorAll('video[data-src]').forEach(v => { if (!v.getAttribute('src')) { v.src = v.dataset.src; v.muted = audio.muted; } });
  });
  if (focus) tab.focus();
}

function findEntry(section, id) { return state.index[section].find(x => x.id === id); }

function openDossier(section, id, { updateHash = true, opener = null } = {}) {
  const entry = findEntry(section, id);
  if (!entry) return false;
  const dialog = $('#dossier');
  stopVideos();
  if (!dialog.open) state.returnFocus = opener || document.activeElement;
  if (state.section !== section) renderSection(section);
  const r = entry.record;
  dialog.innerHTML = section === 'anomalies' ? anomalyDossier(r, entry.media) : section === 'groups' ? groupDossier(r) : mtfDossier(r);
  dialog.scrollTop = 0;
  state.open = { section, id };
  if (!dialog.open) dialog.showModal();
  document.documentElement.classList.add('modal-open');
  audio.effect('file');
  if (updateHash) history.pushState({ section, id }, '', hashFor(section, id));
  document.title = `${entry.title}${entry.section === 'task-forces' ? ` “${r.callsign}”` : ''} · RAISA Archive`;
  $('#dossier-title').focus({ preventScroll: true });
  return true;
}

function closeDossier({ updateHash = true } = {}) {
  const dialog = $('#dossier');
  if (!state.open) return;
  stopVideos();
  const { section, id } = state.open;
  state.open = null;
  if (dialog.open) dialog.close();
  dialog.innerHTML = '';
  document.documentElement.classList.remove('modal-open');
  audio.effect('close');
  if (updateHash) history.pushState({ section }, '', hashFor(section));
  document.title = `${SECTIONS[section].label} · RAISA Archive`;
  // Return focus to the opener; Safari does not focus buttons on click, so fall back to the matching card.
  const opener = state.returnFocus?.isConnected && state.returnFocus !== document.body ? state.returnFocus : null;
  const target = opener || document.querySelector(`.card[data-section="${section}"][data-id="${id}"]`) || $('#collection-title');
  target.focus({ preventScroll: true });
}

/* ---------------------------------------------------------------- routing */
function applyRoute(hash, { initial = false } = {}) {
  const route = parseHash(hash);
  if (!route) { closeDossier({ updateHash: false }); renderSection(state.section); if (initial) history.replaceState({}, '', hashFor(state.section)); return; }
  if (route.id) {
    if (!openDossier(route.section, route.id, { updateHash: false })) { closeDossier({ updateHash: false }); renderSection(route.section); history.replaceState({}, '', hashFor(route.section)); }
    else if (initial && hash !== hashFor(route.section, route.id)) history.replaceState({}, '', hashFor(route.section, route.id));
    return;
  }
  closeDossier({ updateHash: false });
  renderSection(route.section, { focus: !initial });
  if (initial && hash !== hashFor(route.section)) history.replaceState({}, '', hashFor(route.section));
}

/* ---------------------------------------------------------------- events */
function bind() {
  $('#enter').addEventListener('click', () => {
    state.entered = true; $('#splash').hidden = true; $('#facility').hidden = false; audio.start();
    applyRoute(location.hash, { initial: true });
    if (!state.open) { window.scrollTo(0, 0); $('#hero-title').focus({ preventScroll: true }); }
  });
  $('#mute').addEventListener('click', () => audio.toggle());
  document.querySelectorAll('.section-link, .brand').forEach(a => a.addEventListener('click', ev => {
    ev.preventDefault();
    const s = a.dataset.section;
    if (state.open) closeDossier({ updateHash: false });
    history.pushState({ section: s }, '', hashFor(s));
    renderSection(s, { focus: true });
    audio.effect('filter');
    if (a.closest('.hero')) $('#collection').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }));
  $('#search').addEventListener('input', ev => { state.filters[state.section].query = ev.target.value; renderGrid(); });
  $('#chips').addEventListener('click', ev => { const b = ev.target.closest('[data-tag]'); if (!b) return; state.filters[state.section].tag = b.dataset.tag; audio.effect('filter'); renderGrid(); });
  $('#greek').addEventListener('change', ev => { state.filters['task-forces'].greek = ev.target.value; renderGrid(); });
  $('#directory').addEventListener('change', ev => { state.filters['task-forces'].directory = ev.target.value; renderGrid(); });
  $('#reset').addEventListener('click', () => { Object.assign(state.filters[state.section], { query: '', tag: 'all', ...(state.section === 'task-forces' ? { greek: 'all', directory: 'all' } : {}) }); renderToolbar(); renderGrid(); $('#search').focus(); });
  $('#grid').addEventListener('click', ev => { const c = ev.target.closest('.card'); if (c) openDossier(c.dataset.section, c.dataset.id, { opener: c }); });
  const dialog = $('#dossier');
  dialog.addEventListener('click', ev => {
    if (ev.target.closest('[data-close]') || ev.target === dialog) { closeDossier(); return; }
    const tab = ev.target.closest('[role="tab"]'); if (tab) selectMediaTab(tab);
  });
  dialog.addEventListener('keydown', ev => {
    const tab = ev.target.closest('[role="tab"]'); if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(ev.key)) return;
    const tabs = [...dialog.querySelectorAll('[role="tab"]')], i = tabs.indexOf(tab);
    const next = ev.key === 'Home' ? 0 : ev.key === 'End' ? tabs.length - 1 : (i + (ev.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    ev.preventDefault(); selectMediaTab(tabs[next], { focus: true });
  });
  dialog.addEventListener('cancel', ev => { ev.preventDefault(); closeDossier(); }); // Escape
  window.addEventListener('popstate', () => { if (state.entered) applyRoute(location.hash); });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) document.querySelectorAll('video').forEach(v => v.pause());
    if (!audio.ctx) return;
    if (document.hidden) audio.ctx.suspend().catch(() => {}); else if (!audio.muted) audio.ctx.resume().catch(() => {});
  });
}

function fillHeroCounts() {
  SECTION_KEYS.forEach(k => { document.querySelectorAll(`[data-count="${k}"]`).forEach(n => { n.textContent = String(state.index[k].length); }); });
}

async function load() {
  try {
    const [records, collections] = await Promise.all(['data.json', 'collections.json'].map(async url => { const r = await fetch(url); if (!r.ok) throw new Error(url); return r.json(); }));
    state.collections = collections;
    state.index = buildIndex(records, collections);
    fillHeroCounts();
    bind();
    renderSection('anomalies');
    $('#enter').disabled = false; $('#enter').textContent = 'Enter facility';
  } catch {
    $('#enter').textContent = 'Terminal unavailable';
    const err = $('#load-error'); err.hidden = false; err.textContent = 'Records could not be loaded. Serve this folder with a local web server and reload.';
  }
}
load();
