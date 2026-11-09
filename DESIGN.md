# Architecture / local production notes

Greenfield local-only implementation. No source-control repository or external account is involved.

## Phase checklist

- [x] Ground: isolated static folder; no existing application to integrate.
- [x] Sketch: compare full-page record view with a floating document overlay.
- [x] Agree: select full-page record view; no approval checkpoint needed for reversible local files.
- [x] Implement: dataset, original plates, archive renderer, audio engine.
- [x] Verify: real Chromium checks at 390×844 and 1280×900; all records and visual paths.

The two interface alternatives were considered locally, not by cloud agents (none of their tools were available). A full-page dossier was chosen over a floating overlay: it preserves mobile scrolling, avoids a focus-trapping dialog, gives the paper document space, and keeps the atmospheric UI coherent. No repository or deployment was created.

## Small module boundaries

- `data.json`: one record owns identity, canonical class, original text, fictional incident vignettes, source link, and its two artwork paths.
- `build_assets.py`: data authoring plus one original SVG icon and base capability stage per record; invokes `enhance_plates.py`.
- `enhance_plates.py`: one unique capability label and animated operational diagram per record. Never run it repeatedly on already-enhanced plates; regenerate via `build_assets.py` instead.
- `app.js`: app state and archive rendering; `openFile(id, updateHash)` / `closeFile(updateHash)` are the only record transitions. Browser history maps to full-page file selection. The archive is hidden while a dossier is open; returning restores focus and scroll.
- `FacilityAudio`: local-only sound lifecycle and persistent mute preference. It owns the single AudioContext, master gain, quiet oscillators, short source envelopes, and background-tab suspension. No context exists before the entry gesture.
- `style.css`: layout, object-class symbols, aged archive / document styling, and motion/accessibility accommodations; a picture source explicitly selects a static SVG variant for reduced-motion preferences.
- `verify.py`: deterministic real-browser checks and screenshot capture, including all 108 asset decodes.

The immutable data is the source of truth. Search and class filters derive a visible subset without changing the records. All user-derived search strings are treated as query text; every rendered text field is HTML-escaped. The only local storage is the audio mute boolean. No submissions, analytics, authentication, backend, or external API calls exist.
