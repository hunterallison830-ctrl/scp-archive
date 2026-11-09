#!/usr/bin/env python3
"""Build the sourced-image layer and the two new collections.

Inputs: a private research cache (default /workspace/scp-research) holding
downloaded source pages, parsed directories and downloaded images.
Outputs, all inside this repository:
  assets/sourced/{scp,goi,mtf}/*.webp  - resized WebP copies of sourced images
  assets/sourced/foundation-emblem.webp
  collections.json                     - groups, task forces, media and credits
  credits.html                         - full static attribution register
data.json is never written: the 36 dossiers stay byte-identical.
"""
import html, json, os, re, sys
from pathlib import Path
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
RES = Path(os.environ.get('SCP_RESEARCH', '/workspace/scp-research'))
sys.path.insert(0, str(Path(__file__).parent))
from scp_media import MEDIA            # noqa: E402
from goi_content import GOI, FEATURED  # noqa: E402
from mtf_content import SPECIALTY      # noqa: E402

WIKI = 'https://scp-wiki.wikidot.com'
MTF_DIR = WIKI + '/task-forces'
GOI_DIR = WIKI + '/groups-of-interest'
LIC = {'CC BY-SA 3.0': 'https://creativecommons.org/licenses/by-sa/3.0/', 'CC BY 3.0': 'https://creativecommons.org/licenses/by/3.0/',
       'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/', 'Public domain': ''}
MODIFIED = 'Resized and converted to WebP for this archive; otherwise unmodified.'


def slug(s):
    s = s.lower().replace('ē', 'e').replace('ä', 'a')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def to_webp(src, dst, max_side, fit_bg=None):
    src, dst = Path(src), Path(dst)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime and not os.environ.get('FORCE_IMAGES'):
        return Image.open(dst).size
    im = Image.open(src)
    if getattr(im, 'is_animated', False):
        im = next(ImageSequence.Iterator(im))
    im = im.convert('RGBA') if ('A' in im.getbands() or im.mode == 'P') else im.convert('RGB')
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, 'WEBP', quality=84, method=6)
    return im.size


def plate_for(rel):
    """Pick a light (tile) or dark (steel) plate so a transparent emblem stays visible."""
    im = Image.open(ROOT / rel).convert('RGBA')
    im.thumbnail((128, 128))
    data = im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()
    px = [(r, g, b) for r, g, b, a in data if a > 128]
    if len(px) > 0.97 * im.width * im.height:
        return 'opaque'
    lum = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in px) / max(1, len(px))
    return 'dark' if lum > 150 else 'light'


def norm_license(s):
    s = (s or '').strip()
    low = s.lower().replace('-', ' ')
    if 'by sa 3' in low or low in ('cc by sa', 'cc by sa 3.0'):
        return 'CC BY-SA 3.0'
    if 'by 3' in low:
        return 'CC BY 3.0'
    if 'public' in low:
        return 'Public domain'
    return s


def wiki_credit(entry, page, url, title=None, basis='license-box', note=''):
    lic = norm_license(entry.get('License') or entry.get('Licence'))
    deriv = entry.get('Derivative of') or entry.get('Derivative Of')
    n = note
    if deriv:
        n = (n + ' ' if n else '') + f'Derivative of: {deriv}.'
    return dict(title=title or entry.get('Name') or entry.get('Filename'), author=entry.get('Author') or entry.get('Authors') or 'Not listed',
                page=page, url=url, license=lic, licenseUrl=LIC.get(lic, 'https://creativecommons.org/licenses/by-sa/3.0/'),
                basis=basis, note=n.strip(), modified=MODIFIED, listedSource=entry.get('Source Link') or entry.get('Source') or '')


def commons_credit(meta, title, note=''):
    m = meta[title]
    lic = m['license'] if m['license'] != 'Public domain' else 'Public domain'
    return dict(title=title.replace('File:', ''), author=re.sub(r'\s+', ' ', m['artist']).strip(), page=m['page'],
                url=m['url'].split('?')[0], license=lic, licenseUrl=m.get('licenseurl', '') or LIC.get(lic, ''),
                basis='commons', note=note, modified=MODIFIED, listedSource=m.get('credit', ''))


# ----------------------------------------------------------------- anomalies
def build_anomalies(credits):
    data = json.loads((ROOT / 'data.json').read_text())
    ids = {d['id'] for d in data}
    assert ids == set(MEDIA), ids ^ set(MEDIA)
    media = {}
    for sid, m in MEDIA.items():
        rel = f'assets/sourced/scp/{sid}.webp'
        w, h = to_webp(RES / 'dl/scp' / m['file'], ROOT / rel, 1100)
        cid = f'scp-{sid}'
        credits[cid] = dict(title=m['title'], author=m['author'], page=m['page'], url=m['url'], license=m['license'],
                            licenseUrl=m['licenseUrl'], basis=m['basis'], note=m['note'], modified=MODIFIED, subject=f'SCP-{sid}')
        media[sid] = dict(image=rel, w=w, h=h, fit=m['fit'], pos=m['pos'], credit=cid)
    return media


# ---------------------------------------------------------------- groups
def goi_categories():
    s = (RES / 'groups-of-interest.html').read_text(errors='ignore')
    i = s.find('The following list identifies Groups of Interest')
    t = html.unescape(re.sub(r'<[^>]+>', '|', s[i:i + 60000]))
    t = re.sub(r'\|[\s|]*', '|', t)
    cats = ['Foundation Precursors', 'Government', 'Corporate', 'Religious', 'Educational', 'Research', 'Artistic', 'Media', 'Online',
            'Non-Profit', 'Criminal', 'Insurgents', 'Alternate Realities', 'Other', 'International']
    end = t.find('Groups of Interest are listed in order of their first appearance')
    body, first = t[:end], t[end:]
    out = {}
    for n, c in enumerate(cats):
        a = body.find('|' + c + '|')
        b = body.find('|' + cats[n + 1] + '|', a + 1) if n + 1 < len(cats) else len(body)
        items = [x for x in body[a:b].split('|')[3:] if x and x not in '()' and x not in ('Japanese', 'Italian', 'German', 'French')]
        out[c] = items
    return out, first


def first_appearances(first, groups):
    # "Name|(|4th September|by Author)|" blocks grouped under year markers.
    parts = first.split('|')
    year, res = None, {}
    for k, p in enumerate(parts):
        if re.fullmatch(r'(19|20)\d\d', p):
            year = p
            continue
        if year and k + 2 < len(parts) and parts[k + 1] == '(':
            date = parts[k + 2]
            by = parts[k + 3] if k + 3 < len(parts) and parts[k + 3].startswith('by ') else ''
            res[p] = dict(year=year, date=date if re.search(r'\d', date) else '', by=by[3:].rstrip(')').strip() if by else '')
    return res


NAME_ALIASES = {'FBI Unusual Incidents Unit': 'unusual-incidents-unit', 'Obskurakorps': 'obskura', 'The Hunter\'s Black Lodge (Sarkic Cult)': 'sarkic',
                'Shark Punching Center (SPC)': 'shark-punching-center', 'Medician Academy of Occult Art': 'madao'}

GOI_UPGRADES = {  # anchor -> (file in dl/goi_hi, credit builder)
    'global-occult-coalition': ('global-occult-coalition', 'commons', "File:Global Occult Coalition logo v4.webp",
        'The GOC hub license box credits GOC-Logo-v4.png to Aelanna (CC BY-SA 3.0); the Commons copy lists DrClef. Attribution conflict recorded; both named.'),
    'serpents-hand': ('serpents-hand', 'hub', dict(Filename='shlogo3---Cutout2.png', Author="Not listed in the hub license box; the directory derivative of this logo (serpents-hand-1.png) is credited to Zyn, edited by Jerden", License='CC BY-SA 3.0'),
        'https://scp-wiki.wdfiles.com/local--files/serpent-s-hand-hub/shlogo3---Cutout2.png', WIKI + '/serpent-s-hand-hub', "Also mirrored on Wikimedia Commons as \"Serpent's Hand logo.png\" (CC BY-SA 3.0)."),
    'chaos-insurgency': ('chaos-insurgency', 'commons', 'File:Chaos Insurgency logo.png', 'Commons source: the Chaos Insurgency hub.'),
    'broken-god': ('broken-god', 'commons', 'File:Church of the Broken God logo.png', 'Commons source: SCP-JP storage file.'),
    'alexylva': ('alexylva', 'commons', 'File:Alexylva University logo.png', 'Commons source: SCP-CN Alexylva University hub.'),
    'anderson': ('anderson', 'commons', 'File:Anderson Robotics logo (2014).png', ''),
    'are-we-cool-yet': ('are-we-cool-yet', 'commons', 'File:AWCY? logo.png', 'Still frame of the animated AWCY? logo by ukwhatn.'),
    'dr-wondertainment': ('dr-wondertainment', 'commons', 'File:Dr. Wondertainment logo (Tannerbanner).png', ''),
    'marshall-carter-and-dark': ('marshall-carter-and-dark', 'commons', 'File:Marshall, Carter, & Dark Ltd. logo.jpg', ''),
    'alcur-hospital': ('alcur-hospital', 'hubbox', 'AlcurLogo.png', 'https://scp-wiki.wdfiles.com/local--files/the-alcur-hospital-hub/Alcur%20Logo.png'),
    'mages-academy': ('mages-academy', 'hubbox', 'magierakademie-symbol.png', 'https://scp-wiki-de.wdfiles.com/local--files/magierakademie-hub/magierakademie-symbol.png'),
    'pseudogenesis': ('pseudogenesis', 'hubbox', 'Pseudogenesis_Logo_Flatter.png', 'https://scp-wiki.wdfiles.com/local--files/pseudogenesis-productions-hub/Pseudogenesis_Logo_Flatter.png'),
    'second-hytoth': ('second-hytoth', 'hubbox', 'second_hytoth_logo2.png', 'https://scp-wiki.wdfiles.com/local--files/second-hytoth-hub/second_hytoth_logo2.png'),
    'hmfscp': ('hmfscp', 'hubbox', 'HMFSCP2.png', 'https://scp-wiki.wdfiles.com/local--files/her-majesty-s-foundation-hub/HMFSCP2.png'),
}


def gear_sentences(text):
    pat = re.compile(r'\b(weapon\w*|armed|equipped|eigenmech\w*|technolog\w*|augment\w*|prosthe\w*|artifact\w*|paratechnolog\w*|Maps of the Multiverse|thaumaturg\w*)', re.I)
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if pat.search(s)][:3]


def build_groups(credits, meta):
    raw = json.loads((RES / 'goi_parsed.json').read_text())
    cats, first = goi_categories()
    fa = first_appearances(first, raw)
    name_to_anchor = {}
    for o in raw:
        for v in {o['name'], re.sub(r'^The ', '', o['name']), re.sub(r'\s*\(.*\)$', '', o['name'])}:
            name_to_anchor[v] = o['anchor']
            name_to_anchor['The ' + v] = o['anchor']
    name_to_anchor.update(NAME_ALIASES)
    cat_of = {}
    for c, names in cats.items():
        for n in names:
            a = name_to_anchor.get(n) or name_to_anchor.get(re.sub(r'\s*\(.*\)$', '', n))
            if a:
                cat_of.setdefault(a, [])
                if c not in cat_of[a]:
                    cat_of[a].append(c)
    out, gaps = [], []
    for idx, o in enumerate(raw):
        a = o['anchor']
        c = GOI[a]
        rel = f'assets/sourced/goi/{a}.webp'
        cid = f'goi-{a}'
        if a in GOI_UPGRADES:
            u = GOI_UPGRADES[a]
            src = RES / 'dl/goi_hi' / u[0]
            if u[1] == 'commons':
                credits[cid] = commons_credit(meta, u[2], u[3])
                if a == 'global-occult-coalition':
                    credits[cid]['author'] = 'Aelanna (GOC hub license box); the Commons copy lists DrClef'
            elif u[1] == 'hub':
                credits[cid] = wiki_credit(u[2], u[4], u[3], title=u[2]['Filename'], note=u[5])
            else:
                e = next(x for x in o['hub_credits'] if x['Filename'] == u[2])
                credits[cid] = wiki_credit(e, o['hub'], u[3], title=u[2], note='Higher-resolution logo from the group hub page.')
        else:
            src = RES / o['local_raw']
            if o.get('credit'):
                credits[cid] = wiki_credit(o['credit'], GOI_DIR, o['image'], title=o['credit'].get('Filename'))
            else:
                credits[cid] = dict(title=o['image'].rsplit('/', 1)[-1], author='Not listed in the directory or hub license box', page=GOI_DIR,
                                    url=o['image'], license='CC BY-SA 3.0 (page license)', licenseUrl=LIC['CC BY-SA 3.0'], basis='page-license',
                                    note='Directory logo with no license-box entry. Credited to the hosting page; author still to be confirmed.', modified=MODIFIED)
                gaps.append(a)
        w, h = to_webp(src, ROOT / rel, 720)
        credits[cid]['subject'] = o['name']
        paras = [clean_text(x) for x in o['paras']]
        text = '\n\n'.join(paras)
        f = fa.get(re.sub(r'\s*\(.*\)$', '', o['name'])) or fa.get(o['name']) or fa.get(re.sub(r'^The ', '', o['name']))
        out.append(dict(
            id=a, name=o['name'], order=idx, section='additional' if a in ('asci', 'british-occult-service', 'joicl', 'obskura', 'pentagram') else 'main',
            categories=cat_of.get(a, ['Other']), featured=a in FEATURED, international=o['international'],
            image=rel, w=w, h=h, fit='contain', plate=plate_for(rel), credit=cid,
            lore=paras, loreSource=GOI_DIR + '#' + a, hub=o['hub'],
            purpose=c['purpose'], specialties=c['specialties'], gear=c['gear'],
            gearQuotes=gear_sentences(text), continuity=c.get('continuity'),
            firstAppearance=f))
    return out, gaps


# ------------------------------------------------------------ task forces
ROLE_RULES = [
    ('Combat & rapid response', r'\b(armed|battalion|rapid[- ]response|first deployed|air support|overwhelming force|elite fighting|special ops|special operations|combat|military-grade)'),
    ('Command & oversight', r'\b(O5 Council|Ethics Committee|Administrator|internal security|infiltration within Foundation|secrecy of the O5)'),
    ('Undercover & intelligence', r'\b(undercover|covert|deep-cover|intel|infiltrat|disinformation|monitors|monitoring)'),
    ('GoI counter-operations', r'\b(GoI|Group of Interest|Groups of Interest|Sarkic|Chaos Insurgency|Marshall, Carter|Church of the Broken God|Serpent|Wilson|Library|Black Lodge|Alexylva|Ambrose)'),
    ('Mind, memetic & info hazards', r'\b(memetic|meme|cognitohazard|amnestic|mnestic|informational|information leaks|internet|cyber|computer|psionic|psychic|dream|Oneiroi|anomalous objects and media|social media|auditory|visual)'),
    ('Occult & reality', r'\b(thaumaturg|demon|religio|reality bend|reality|spacetime|topolog|incorporeal|occult|timeline|extra-dimensional|alt-dimensional|dimensional)'),
    ('Environment specialists', r'\b(swamp|forest|deep-sea|ocean|marine|underground|subzero|cold|urban|rural|lake|zero-gravity|vacuum|Venus|terrain|exploration|wetland|Toronto|Lake)'),
    ('Bio & physical hazards', r'\b(biolog|chemical|radiolog|plant|vermin|avian|disease|epidemiolog|incendiary|high-temperature|geological|prehistoric|fauna|animal)'),
]
PICKS = ['Alpha-1', 'Epsilon-11', 'Nu-7', 'Omega-1', 'Eta-10', 'Beta-7', 'Tau-5', 'Xi-8', 'Psi-9', 'Omega-7', 'Lambda-5', 'Kappa-10', 'Rēsh-1', 'Omega-9', 'Zeta-9', 'Gamma-5']
GREEK = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho',
         'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega']
GEAR_PAT = re.compile(r'\b(armed|weapon\w*|incendiar\w*|corrosive|amnestic\w*|artillery|armou?r\w*|vehicle\w*|helicopter\w*|tank|equipped|cyborg\w*|AICs?|DMT|aerial|air support|naval|nuclear|CBRN|Identity Warfare|Counter Occult|utiliz\w* SCP|forgers?)', re.I)


PURPOSE_PAT = re.compile(r'\b(tasked|created|formed|purpose|dedicated|responsible|deployed|charged|used in|designed|empowered|handles|reports directly|serving as)\b', re.I)


def pick_purpose(sentences):
    """The sentence that states what the unit is for; falls back to the first sentence."""
    if not sentences:
        return None
    return next((x for x in sentences if PURPOSE_PAT.search(x)), sentences[0])


def clean_text(t):
    t = re.sub(r'\s+([,.;:!?)])', r'\1', t)
    t = t.replace('( ', '(')
    t = re.sub(r'(?<=\s)"\s+([^"]+?)\s+"(?=[\s,.;])', r'"\1"', t)
    return re.sub(r'\s{2,}', ' ', t).strip()


def build_mtf(credits, meta):
    raw = json.loads((RES / 'mtf_parsed.json').read_text())
    lic = json.loads((RES / 'mtf_licbox.json').read_text())
    seen, out, gaps = {}, [], []
    emblem = 'assets/sourced/foundation-emblem.webp'
    to_webp(RES / 'dl/goi_hi/_foundation', ROOT / emblem, 480)
    credits['foundation-emblem'] = commons_credit(meta, 'File:SCP Foundation (emblem).svg',
        'Shared emblem used, with a text overlay, for task forces that have no insignia on the directory page.')
    credits['foundation-emblem']['subject'] = 'Shared Foundation emblem'
    dup = {}
    for o in raw:
        dup[o['designation']] = dup.get(o['designation'], 0) + 1
    for idx, o in enumerate(raw):
        d = o['designation']
        sid = slug(d) if dup[d] == 1 else slug(d + '-' + o['callsign'])
        assert sid not in seen, sid
        seen[sid] = 1
        mission = o['fields'].get('Task Force Mission', {}).get('text', '').strip()
        mission = re.sub(r'\s+([,.;:])', r'\1', mission).replace('( ', '(').replace(' )', ')').strip()
        mission = re.sub(r'(SCP-\d+) -(?=\w)', r'\1-', mission)
        mission = re.sub(r'(?<=\s)"\s+([^"]+?)\s+"(?=[\s,.;])', r'"\1"', mission)
        links = {}
        for k, v in o['fields'].items():
            if k == 'Task Force Mission':
                continue
            key = 'Assisting in Containment of Objects' if k.lower().startswith('assisting') else k
            links.setdefault(key, [])
            links[key] += [dict(href=WIKI + h if h.startswith('/') else h, label=l) for h, l in v['links']]
        cid = f'mtf-{sid}'
        insignia, has_insignia = emblem, True
        if o.get('local_raw'):
            rel = f'assets/sourced/mtf/{sid}.webp'
            to_webp(RES / o['local_raw'], ROOT / rel, 520)
            insignia = rel
            if o['credit']:
                cr = wiki_credit(o['credit']['main'], MTF_DIR, o['image'], title=o['credit']['main'].get('Filename'))
                if o['credit']['deriv']:
                    cr['components'] = [dict(name=x.get('Filename'), author=x.get('Author'), license=x.get('License'), source=x.get('Source Link')) for x in o['credit']['deriv']]
            else:
                e = next((x for x in lic if d == 'Phi-Eolh' and x['Filename'] == 'PhiEloh.png'), None)
                if e:
                    cr = wiki_credit(e, MTF_DIR, o['image'], title='PhiEloh.png', note='License-box entry spelled "Phi-Eloh"; matched to this insignia.')
                else:
                    cr = dict(title=o['image'].rsplit('/', 1)[-1], author='Not listed in the directory license box', page=MTF_DIR, url=o['image'],
                              license='CC BY-SA 3.0 (page license)', licenseUrl=LIC['CC BY-SA 3.0'], basis='page-license',
                              note='Insignia shown on the directory without a license-box entry; author still to be confirmed.', modified=MODIFIED)
                    gaps.append(dict(id=sid, gap='insignia credit not in license box'))
            cr['subject'] = f'{o["kind"]} {d} "{o["callsign"]}"'
            credits[cid] = cr
        else:
            has_insignia = False
            cid = 'foundation-emblem'
            gaps.append(dict(id=sid, gap='no insignia on directory page; shared Foundation emblem with text overlay'))
        text = mission
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', text) if s]
        m = re.search(r'speciali[sz]\w*\s+in\s+(.+?)(?:\.\s|\.$|$)', text, re.I)
        specialty = SPECIALTY.get(sid) or (m.group(1).strip().rstrip('.') if m else None)
        roles = [r for r, p in ROLE_RULES if re.search(p, text + ' ' + o['callsign'], re.I)] or ['General containment']
        gear = [s for s in sentences if GEAR_PAT.search(s)]
        greek = next((g for g in GREEK if d.startswith(g)), 'Other')
        if d.startswith('Omicron Rho'):
            greek = 'Omicron'
        num = ''.join(re.findall(r'-(.+)$', d))
        out.append(dict(
            id=sid, designation=d, callsign=o['callsign'], kind=o['kind'], section=o['section'], order=idx,
            greek=greek, number=num, pick=d in PICKS and not (d == 'Gamma-4'),
            insignia=insignia, plate=plate_for(insignia) if has_insignia else 'dark', hasInsignia=has_insignia, credit=cid,
            mission=mission or None, missionSource=MTF_DIR, purpose=pick_purpose(sentences),
            specialty=specialty, roles=roles, gearQuotes=gear, utilizing=links.get('Utilizing Objects', []),
            deployments=links.get('Known Deployments', []), assisting=links.get('Assisting in Containment of Objects', []),
            reports=links.get('Action Reports', [])))
    return out, gaps


# ----------------------------------------------------------------- credits
def render_credits(media, groups, mtf, credits, anomalies):
    e = html.escape
    def row(cid, label, anchor):
        c = credits[cid]
        basis = {'license-box': 'Page license box', 'commons': 'Wikimedia Commons metadata', 'page-license': 'Page license only (no per-file entry)'}[c['basis']]
        comp = ''.join(f'<li>{e(x["name"] or "")} — {e(x["author"] or "")} ({e(x["license"] or "")})</li>' for x in c.get('components', []))
        comp = f'<details><summary>Components ({len(c["components"])})</summary><ul>{comp}</ul></details>' if comp else ''
        lic = f'<a href="{e(c["licenseUrl"])}" rel="noopener license">{e(c["license"])}</a>' if c.get('licenseUrl') else e(c['license'])
        return (f'<tr id="{e(anchor)}"><th scope="row">{e(label)}</th><td>{e(c["title"])}</td><td>{e(c["author"])}</td><td>{lic}</td>'
                f'<td><a href="{e(c["page"])}" rel="noopener">Source page</a><br><a class="mono" href="{e(c["url"])}" rel="noopener">Image file</a></td>'
                f'<td><span class="basis basis-{c["basis"]}">{basis}</span>{(" " + e(c["note"])) if c.get("note") else ""}{comp}</td></tr>')
    head = '<thead><tr><th scope="col">Entry</th><th scope="col">Image</th><th scope="col">Author / credit</th><th scope="col">License</th><th scope="col">Links</th><th scope="col">Basis &amp; notes</th></tr></thead>'
    a_rows = ''.join(row(media[x['id']]['credit'], f'{x["itemNumber"]} · {x["name"]}', f'credit-scp-{x["id"]}') for x in anomalies)
    g_rows = ''.join(row(g['credit'], g['name'], f'credit-goi-{g["id"]}') for g in groups)
    m_rows = ''.join(row(t['credit'], f'{t["kind"]} {t["designation"]} “{t["callsign"]}”' + ('' if t['hasInsignia'] else ' (no insignia — shared emblem)'), f'credit-mtf-{t["id"]}') for t in mtf)
    counts = {b: sum(1 for c in credits.values() if c['basis'] == b) for b in ('license-box', 'commons', 'page-license')}
    src_rows = ''.join(f'<li><a href="{e(x["source"])}" rel="noopener">{e(x["itemNumber"])} — {e(x["name"])}</a></li>' for x in anomalies)
    tpl = (ROOT / 'tools/credits.template.html').read_text()
    return (tpl.replace('{{ANOMALY_ROWS}}', a_rows).replace('{{GROUP_ROWS}}', g_rows).replace('{{MTF_ROWS}}', m_rows).replace('{{HEAD}}', head)
            .replace('{{SOURCE_LIST}}', src_rows).replace('{{N_BOX}}', str(counts['license-box'])).replace('{{N_COMMONS}}', str(counts['commons']))
            .replace('{{N_PAGE}}', str(counts['page-license'])).replace('{{N_TOTAL}}', str(len(credits)))
            .replace('{{N_GOI}}', str(len(groups))).replace('{{N_MTF}}', str(len(mtf))))


def main():
    meta = json.loads((RES / 'commons_meta.json').read_text())
    credits = {}
    media = build_anomalies(credits)
    groups, goi_gaps = build_groups(credits, meta)
    mtf, mtf_gaps = build_mtf(credits, meta)
    anomalies = sorted(json.loads((ROOT / 'data.json').read_text()), key=lambda x: int(x['id']))
    coll = dict(generated='tools/build_collections.py', sources=dict(groups=GOI_DIR, taskForces=MTF_DIR,
                taskForcesNote='The directory lists the most notable task forces; a longer list exists at ' + WIKI + '/task-forces-complete-list. This archive covers every entry on the main directory page only.'),
                anomalyMedia=media, groups=groups, taskForces=mtf, credits=credits,
                gaps=dict(groupLogoCredit=goi_gaps, taskForces=mtf_gaps))
    (ROOT / 'collections.json').write_text(json.dumps(coll, ensure_ascii=False, indent=1) + '\n')
    (ROOT / 'credits.html').write_text(render_credits(media, groups, mtf, credits, anomalies))
    print(f'anomalies={len(media)} groups={len(groups)} taskForces={len(mtf)} credits={len(credits)} goiGaps={goi_gaps} mtfGaps={len(mtf_gaps)}')


if __name__ == '__main__':
    main()
