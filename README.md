# RAISA — Restricted Records Archive

Unofficial SCP Foundation fan experience. Vanilla HTML / CSS / JavaScript. No build step, dependencies, accounts, trackers, external fonts, paid APIs, or backend. 36 dossiers and 72 locally authored SVG scenes, plus 36 accessible still variants.

## Preview

```sh
cd /workspace/scp-archive
python3 -m http.server 8771 --bind 0.0.0.0
```

Open http://localhost:8771. Do not open index.html directly: JSON uses fetch.
All application paths are relative, including `.nojekyll` for an eventual GitHub Pages deployment. Nothing has been published and no repository has been created.

## Contents

- `data.json`: original dossier summaries, two original fictional incident vignettes per entry, classes, sources, and visual paths.
- `assets/videos/`: one short silent overview film per entry (`overview` field in `data.json`), played in-file with a native `<video>` player. Original AI-generated fan reconstructions animated from the archive's own illustrations; not downloaded from the wiki, YouTube, or any third-party channel.
- `assets/`: one original specimen illustration and one original animated capability panel per entry. Not photographs, official assets, or downloaded wiki art.
- `build_assets.py`: reproducible illustration and dataset generator; automatically runs `enhance_plates.py` to add the 36 individual behavioral diagrams. Python standard library only.
- `app.js`: records search, class filters, full-page dossier viewer, keyboard navigation, and original Web Audio synthesis.
- `style.css`: responsive archive and document styles. Respects reduced-motion preferences (using an explicit static source for embedded SVG plates).
- `credits.html`: source record links and licensing details.
- `verify.py`: Playwright end-to-end smoke checks. Requires installed Python Playwright and `/usr/bin/google-chrome`. Run while server is running.

Audio starts only after Enter Facility. The persistent mute setting is stored locally on the device; no information is transmitted. Synthesis is deliberately quiet: low industrial hum, short paper/static rustles and a low stamp impact. Background tabs suspend audio. Escape returns from a file.

## Copyright / attribution

This is **unofficial fan work**, not the SCP Wiki or a real Foundation service. SCP concepts are derived from [SCP Foundation](https://scp-wiki.wikidot.com/) and the contributors to the individual articles linked in every dossier and `credits.html`. See each source article's attribution / license history for its contributors. Adapted material and the fan-created writing, art, and implementation in this folder are shared under [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

No article passages or canonical logs have been transcribed. Summaries are original compressed interpretations. Incident vignettes are newly invented fan scenes, not a canonical timeline. Blacked-out dates are dramatic framing, not historical assertions. Every illustration is original procedural SVG art; no SCP images or official logos were downloaded. The R seal is an original RAISA-inspired monogram, not the Foundation logo.

There are no SCP-001 proposals, logins, data collection, jump scares, or gore imagery. The SCP-2521 dossier uses pictographic / redacted body records.
