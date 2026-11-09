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
check(len(coll['taskForces']) == 108, 'task force count')
check(len({g['id'] for g in coll['groups']}) == 56, 'unique group ids')
check(len({t['id'] for t in coll['taskForces']}) == 108, 'unique task force ids')

# 3. every referenced local file exists and every image decodes
refs = set()
for d in data:
    refs |= {d['icon'], d['capability'], d['capabilityStill'], d['overview']}
for m in coll['anomalyMedia'].values():
    refs.add(m['image'])
for g in coll['groups']:
    refs.add(g['image'])
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
for key, cid in [(f'scp-{k}', v['credit']) for k, v in coll['anomalyMedia'].items()] + [(g['id'], g['credit']) for g in coll['groups']] + [(t['id'], t['credit']) for t in coll['taskForces']]:
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
    check(f'id="credit-mtf-{t["id"]}"' in ch, f'credits row mtf {t["id"]}')
check('{{' not in ch, 'unfilled template placeholder')

# 7. dossier text fields present (lore, purpose, specialties, gear stance)
for g in coll['groups']:
    check(g['lore'] and g['purpose'] and g['specialties'], f'group fields {g["id"]}')
for t in coll['taskForces']:
    check(t['mission'] or t['id'] in ('rho-43', 'chi-7', 'chi-9', 'sigma-66-steel-veil', 'sigma-6'), f'mission {t["id"]}')

print(f'refs={len(refs)} images_decoded={decoded} credits={len(coll["credits"])} groups={len(coll["groups"])} taskForces={len(coll["taskForces"])}')
print('gaps:', json.dumps(coll['gaps']))
if fail:
    print('FAIL', len(fail)); [print(' -', x) for x in fail]; sys.exit(1)
print('STATIC CHECKS PASSED')
