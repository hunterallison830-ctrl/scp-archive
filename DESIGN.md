# Architecture and design notes

## Overhaul (November 2026)

**Goal:** image-led cards with credited community images, two new collections (Groups of Interest, Mobile Task Forces) built on the same dossier pattern, and a Foundation-interior visual identity.

### Shape

- **Data stays separated by provenance.** `data.json` (the original 36 dossiers) is untouched. Everything new is generated into `collections.json` by `tools/build_collections.py`, from a private cache of downloaded directory pages, license boxes, Commons metadata and images. That makes "dossier content preserved" checkable: `tests/static_check.py` compares `data.json` byte for byte against commit `ef0bfc1`.
- **One card-entry shape for all three sections** (`archive-core.js#buildIndex`): `{section, id, record, title, subtitle, tags, search}`. Search, filtering, counts and routing work on that shape, so the three sections share one code path.
- **One dossier lifecycle.** `openDossier(section, id)` and `closeDossier()` are the only transitions. They are driven by clicks, the hash router and `popstate`. A native `<dialog>` opened with `showModal()` provides the modal semantics: inert background, focus containment, and Escape via the `cancel` event. Focus goes to the dossier title on open and back to the opening card on close.
- **Video lifecycle.** The overview film lives under the "Original artwork" tab. Its `<video>` only gets a `src` while that tab is visible. Switching tabs, switching dossiers, closing, or hiding the page pauses it and removes the `src`.
- **Credits are data.** Each card image points to a credit id in `collections.json.credits`. The dossier caption and the generated `credits.html` row both come from that one record.

### Decision: modal over full page

The earlier version used a full-page dossier to avoid a hand-rolled focus trap. Native `<dialog>` removes that cost. On screens 720px wide or narrower, the dialog is full-screen with a sticky header, so mobile scrolling behaves like a page, while desktop keeps the archive context behind a backdrop.

### Visual system

- **Graphite steel** (`#121517` to `#3c444b`) for chrome and panels, with vertical panel seams drawn in CSS gradients.
- **White tile** (`#e9ecea` with `#c3cac8` grout, drawn in CSS) for the hero wall, the emblem plates and active chips: the containment-chamber wall.
- **Concrete grey** for secondary text and outlines, and a steel wainscot band at the foot of the hero.
- **Restrained hazard accent**: amber `#f0b400` for eyebrows and focus, and a thin black-and-yellow stripe on the splash, the hero floor line, dossier headers and the footer.
- **Type**: a condensed uppercase display stack for headings, a system sans for reading, and a mono face for labels and designations. No web fonts are downloaded.
- **Emblem plates** pick a light (tile) or dark (steel) background per image. The build measures the luminance of each emblem's opaque pixels, so transparent logos stay visible.

Design references (inspiration only, not shown on the site) are listed in `credits.html#design`.

### Known limits

- Task-force "role" groupings are editorial keyword groupings, not official.
- Sixteen images rely only on the hosting page's license, with no per-file entry. Eight task forces have insignia gaps or uncredited insignia. Three group logos have no license-box credit. All are listed in `collections.json.gaps` and flagged in `credits.html`.
