#!/usr/bin/env python3
"""Static integrity checks for the archive. Run from the repo root: python3 tests/static_check.py"""
import json, re, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
fail = []
def check(cond, msg):
    if not cond:
        fail.append(msg)

data = json.loads((ROOT / 'data.json').read_text())
coll = json.loads((ROOT / 'collections.json').read_text())

# 1. data.json is byte-identical to the pre-overhaul commit (dossier content preserved)
head = subprocess.run(['git', 'show', 'ef0bfc1:data.json'], cwd=ROOT, capture_output=True).stdout
check(head == (ROOT / 'data.json').read_bytes(), 'data.json differs from ef0bfc1')

# 2. counts
check(len(data) == 36, 'anomaly count')
check(len(coll['anomalyMedia']) == 36 and set(coll['anomalyMedia']) == {d['id'] for d in data}, 'anomaly media coverage')
check(len(coll['groups']) == 56, 'group count')
st = coll['taskForceStats']
dossiers = [t for t in coll['taskForces'] if t['coverage'] == 'dossier']
listed = [t for t in coll['taskForces'] if t['coverage'] == 'list']
check(len(dossiers) == 108, 'directory task force count')
check(len(listed) == st['listOnly'] and len(coll['taskForces']) == st['total'], 'list task force count')
check(st['listRows'] == st['total'] + st['excluded']['Vehicles'] + st['excluded']['Joke'], 'every list row accounted for')
check(len({g['id'] for g in coll['groups']}) == 56, 'unique group ids')
check(len({t['id'] for t in coll['taskForces']}) == len(coll['taskForces']), 'unique task force ids')

# 3. every referenced local file exists and every image decodes
refs = set()
for d in data:
    refs |= {d['icon'], d['capability'], d['capabilityStill'], d['overview']}
for m in coll['anomalyMedia'].values():
    refs.add(m['image'])
for g in coll['groups']:
    if g['image']:
        refs.add(g['image'])
    else:
        check(g['credit'] is None and g['mediaWithheld'], f'withheld logo {g["id"]} is explained')
for t in coll['taskForces']:
    refs.add(t['insignia'])
decoded = 0
for r in sorted(refs):
    p = ROOT / r
    check(p.is_file(), f'missing {r}')
    if p.suffix in ('.webp', '.png', '.jpg') and p.is_file():
        try:
            with Image.open(p) as im:
                im.load(); decoded += 1
        except Exception as ex:
            fail.append(f'decode {r}: {ex}')
videos = [d['overview'] for d in data]
check(len(set(videos)) == 36 and all((ROOT / v).stat().st_size > 10000 for v in videos), '36 overview videos present')

# 4. every card image has a credit with the required fields; no generated art passed off as sourced
for key, cid in [(f'scp-{k}', v['credit']) for k, v in coll['anomalyMedia'].items()] + [(g['id'], g['credit']) for g in coll['groups'] if g['image']] + [(t['id'], t['credit']) for t in coll['taskForces']]:
    c = coll['credits'].get(cid)
    check(c is not None, f'no credit for {key}')
    if c:
        for f in ('title', 'author', 'page', 'url', 'license', 'basis'):
            check(bool(c.get(f)), f'credit {cid} missing {f}')
        check(c['url'].startswith('https://') or c['url'].startswith('http://'), f'credit {cid} url')
for m in coll['anomalyMedia'].values():
    check(m['image'].startswith('assets/sourced/'), 'sourced image path')
check('Izumi' not in json.dumps(coll['credits']['scp-173']) or 'not the Izumi' in coll['credits']['scp-173']['note'], '173 credit')
check('Kato' not in coll['credits']['scp-173']['author'], 'SCP-173 not Izumi Kato image')

# 5. no hotlinked images or scripts in the app
for f in ('index.html', 'app.js', 'archive-core.js', 'style.css', 'credits.html'):
    s = (ROOT / f).read_text()
    check(not re.search(r'<(img|script|source|video|link)[^>]+(src|href|srcset)="https?://', s), f'{f} hotlinks a resource')
    check(not re.search(r'url\(\s*["\']?https?://', s), f'{f} css hotlink')

# 6. credits.html has a row for every card
ch = (ROOT / 'credits.html').read_text()
for k in coll['anomalyMedia']:
    check(f'id="credit-scp-{k}"' in ch, f'credits row scp-{k}')
for g in coll['groups']:
    check(f'id="credit-goi-{g["id"]}"' in ch, f'credits row goi {g["id"]}')
for t in coll['taskForces']:
    if t['coverage'] == 'dossier' or t['hasInsignia']:
        check(f'id="credit-mtf-{t["id"]}"' in ch, f'credits row mtf {t["id"]}')
    else:
        check(t['credit'] == 'foundation-emblem', f'placeholder credit {t["id"]}')
check('id="credit-foundation-emblem"' in ch, 'shared emblem credit row')
# no unconfirmed licenses published: nothing pending, every non-placeholder image has a per-file or artist basis
check(all(c['basis'] != 'page-license' for c in coll['credits'].values()), 'a pending (page-license) credit is still published')
# withheld/unlicensed media is not shipped
check(not (ROOT / 'assets/sourced/goi/sapphire.webp').exists() and not (ROOT / 'assets/sourced/goi/wilsons-wildlife.webp').exists(), 'withheld group logos removed')
check(not (ROOT / 'assets/sourced/mtf/nu-3.webp').exists(), 'withheld Nu-3 insignia removed')
shipped = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets/sourced').rglob('*.webp')}
check(shipped <= refs, f'unreferenced sourced files shipped: {sorted(shipped - refs)[:5]}')
check('{{' not in ch, 'unfilled template placeholder')

# 7. dossier text fields present (lore, purpose, specialties, gear stance)
for g in coll['groups']:
    check(g['lore'] and g['purpose'] and g['specialties'], f'group fields {g["id"]}')
for t in listed:
    check(t['listedAs'] and t['source'].endswith('task-forces-complete-list'), f'list source {t["id"]}')
    check('mission' not in t and 'gearQuotes' not in t, f'list entry {t["id"]} carries directory-only fields')
for t in dossiers:
    check(t['mission'] or t['id'] in ('rho-43', 'chi-7', 'chi-9', 'sigma-66-steel-veil', 'sigma-6'), f'mission {t["id"]}')

print(f'refs={len(refs)} images_decoded={decoded} credits={len(coll["credits"])} groups={len(coll["groups"])} taskForces={len(coll["taskForces"])} (dossiers={len(dossiers)} list={len(listed)})')
print('gaps:', json.dumps(coll['gaps']))
if fail:
    print('FAIL', len(fail)); [print(' -', x) for x in fail]; sys.exit(1)
print('STATIC CHECKS PASSED')
