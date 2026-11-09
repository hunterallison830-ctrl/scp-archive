# RAISA — Foundation Records Archive

An unofficial SCP Foundation fan archive, built with plain HTML, CSS and JavaScript. It has no build step at runtime, no dependencies, accounts, trackers, external fonts or backend, and it hotlinks nothing.

It has three sections:

- **Anomalies (36).** Each containment dossier's card shows a credited community image of that SCP, downloaded and served locally. Inside a dossier, a small **Original artwork** tab holds the archive's own generated plates and the six-second overview film.
- **Groups of Interest (56).** Every entry in the official [Groups of Interest directory](https://scp-wiki.wikidot.com/groups-of-interest) (51 main + 5 additional). Each dossier quotes the official brief and adds origins and purpose, specialties, and gear and weapons. When the brief documents no gear, the dossier says "Not specified". Contested canon gets a continuity note.
- **Mobile Task Forces (108).** Every entry on the main [Mobile Task Forces directory](https://scp-wiki.wikidot.com/task-forces): 89 listed units, 17 "Additional MTFs", 1 DTF and 1 STF. Each shows its designation, callsign and insignia, for example Alpha-1 "Red Right Hand". The wiki's longer [complete list](https://scp-wiki.wikidot.com/task-forces-complete-list) is **not** covered. Five units have no insignia on the directory page; they show the shared Foundation emblem with a text overlay.

## Preview

```sh
cd /workspace/scp-archive
python3 -m http.server 8781 --bind 127.0.0.1
```

Open http://127.0.0.1:8781. Opening `index.html` directly will not work, because the JSON is loaded with `fetch`.

## Files

| Path | Role |
|---|---|
| `index.html` | Splash, top bar with section nav and mute, tiled hero with route tiles, one collection panel, and a `<dialog>` for dossiers. |
| `archive-core.js` | Pure logic with no DOM access: normalises data into card entries, search (case-, accent- and punctuation-insensitive), filters, tag counts, and the hash grammar. Used by the browser and by Node tests. |
| `app.js` | UI rendering, the dossier lifecycle (`openDossier` / `closeDossier`), the media tab and video lifecycle, routing, and `FacilityAudio` (unchanged behaviour, same `raisa-muted` key). |
| `style.css` | Graphite steel, concrete and white-tile theme. Mobile first, with reduced-motion and forced-colors support. |
| `data.json` | The 36 original dossiers. **Byte-identical to the pre-overhaul commit.** |
| `collections.json` | Generated: per-anomaly sourced image and credit, 56 groups, 108 task forces, 196 credit records, and known gaps. |
| `credits.html` | Generated: the full image register (author, source page, actual image URL, license, basis, notes), plus text license and design references. |
| `assets/sourced/` | Resized WebP copies of the sourced images (`scp/`, `goi/`, `mtf/`, `foundation-emblem.webp`). |
| `assets/*.svg`, `assets/videos/*.mp4` | The archive's original generated plates and films. They appear only under "Original artwork". |
| `tools/build_collections.py` | Rebuilds `collections.json`, `credits.html` and `assets/sourced/` from the private research cache (`SCP_RESEARCH`, default `/workspace/scp-research`). |
| `tools/scp_media.py`, `tools/goi_content.py`, `tools/mtf_content.py` | Hand-curated image picks and credits, group dossier fields, and task-force specialty lines. |
| `tests/` | `core.test.js` (unit), `dom_smoke.test.js` (jsdom, not a browser), and `static_check.py` (integrity). |
| `verify.py` | Real-browser Playwright checks and screenshots. Not yet run against the overhaul. |

## Routes

`#anomalies`, `#groups`, `#task-forces`, `#scp-173`, `#goi-serpents-hand`, `#mtf-alpha-1`. The old links `#file-173` and `#records` still work.

## Tests

```sh
node --check archive-core.js && node --check app.js
node --test tests/core.test.js
NODE_PATH=/path/to/node_modules/with/jsdom node --test tests/dom_smoke.test.js
python3 tests/static_check.py
python3 tools/build_standalone.py            # offline single-file preview -> ../scp-archive-offline/
NODE_PATH=/path/to/node_modules/with/jsdom node --test tests/standalone_smoke.test.js
```

`tools/build_standalone.py` writes a review copy that opens from `file://` with no server: data, images and films are embedded as data URLs and only `fetch` for the two JSON files is shimmed. It does not change the site files.

## Copyright and attribution

This is **unofficial fan work**. It is not the SCP Wiki or affiliated with it. SCP concepts, group briefs and task-force mission statements come from the [SCP Wiki](https://scp-wiki.wikidot.com/) community under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), and quoted text is credited in each dossier. Every sourced image is credited in `credits.html` with author, source page, image URL, license and the basis for that license. Each credit states its basis: page license box, Wikimedia Commons, a license on the off-wiki source page, the artist's own wiki page, or **pending** when no per-file author/license statement was found. Pending images are not treated as cleared. The SCP-173 card does not use the Izumi Kato sculpture photograph. The archive's own writing, generated art, films, sound synthesis and code are shared under CC BY-SA 3.0.
