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
import difflib, html, json, os, re, sys, unicodedata
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


# Directory logos with no license-box entry anywhere we could find.
GOI_SUBJECT_MATCH = {
    'vikander-kneed': ('VKlogotransparent', 'Matched by subject: the hub license box lists "VKlogotransparent" (the Vikander-Kneed logo) by Grigori Karpin, CC BY 3.0, note "created by me". This is the directory copy of that logo (vikander-kneed-1.png); the hub file itself no longer resolves, so the two were not compared byte-for-byte.'),
}
GOI_WITHHELD = {
    'sapphire': 'The directory logo has no license-box entry on the directory or the SAPHIR Centre hub, so it is withheld rather than published without a confirmed license.',
    'wilsons-wildlife': "The directory logo has no license-box entry on the directory, and the Wilson's Wildlife Solutions hub has no license box, so it is withheld rather than published without a confirmed license.",
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
                    credits[cid]['author'] = 'Aelanna (per the GOC hub license box, the source this Commons file cites); Commons file page lists DrClef'
                    credits[cid]['note'] = ('Downloaded file: the Wikimedia Commons copy (400x400 WebP). Its Commons source field is the GOC hub page, whose license box '
                                            'credits GOC-Logo-v4.png to Aelanna, CC BY-SA 3.0; the Commons author field says DrClef. Both licenses agree (CC BY-SA 3.0). '
                                            'Aelanna is credited first because that is the attribution at the cited source; DrClef is kept as the Commons record.')
            elif u[1] == 'hub':
                credits[cid] = wiki_credit(u[2], u[4], u[3], title=u[2]['Filename'], note=u[5])
            else:
                e = next(x for x in o['hub_credits'] if x['Filename'] == u[2])
                credits[cid] = wiki_credit(e, o['hub'], u[3], title=u[2], note='Higher-resolution logo from the group hub page.')
        else:
            src = RES / o['local_raw']
            if o.get('credit'):
                credits[cid] = wiki_credit(o['credit'], GOI_DIR, o['image'], title=o['credit'].get('Filename'))
            elif a in GOI_SUBJECT_MATCH:
                fn, note = GOI_SUBJECT_MATCH[a]
                e = next(x for x in o['hub_credits'] if x['Filename'] == fn)
                credits[cid] = wiki_credit(e, o['hub'], o['image'], title=o['image'].rsplit('/', 1)[-1], note=note)
            elif a in GOI_WITHHELD:
                src = None
                gaps.append(a)
            else:
                credits[cid] = dict(title=o['image'].rsplit('/', 1)[-1], author='Not listed in the directory or hub license box', page=GOI_DIR,
                                    url=o['image'], license='CC BY-SA 3.0 (page license)', licenseUrl=LIC['CC BY-SA 3.0'], basis='page-license',
                                    note='PENDING: directory logo with no license-box entry on the directory or the group hub. Credited to the hosting page only; author not confirmed.', modified=MODIFIED)
                gaps.append(a)
        if src is None:
            (ROOT / rel).unlink(missing_ok=True)
            rel, w, h, cid = None, None, None, None
        else:
            w, h = to_webp(src, ROOT / rel, 720)
            credits[cid]['subject'] = o['name']
        paras = [clean_text(x) for x in o['paras']]
        text = '\n\n'.join(paras)
        f = fa.get(re.sub(r'\s*\(.*\)$', '', o['name'])) or fa.get(o['name']) or fa.get(re.sub(r'^The ', '', o['name']))
        out.append(dict(
            id=a, name=o['name'], order=idx, section='additional' if a in ('asci', 'british-occult-service', 'joicl', 'obskura', 'pentagram') else 'main',
            categories=cat_of.get(a, ['Other']), featured=a in FEATURED, international=o['international'],
            image=rel, w=w, h=h, fit='contain', plate=plate_for(rel) if rel else 'withheld', credit=cid,
            mediaWithheld=(GOI_WITHHELD[a] if rel is None else None),
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


MTF_COMPLETE = WIKI + '/task-forces-complete-list'
MTF_COMPLETE_LICBOX = MTF_COMPLETE  # its license box is included on the page itself
# Insignia missing from the directory license box but listed in the license box of
# "A Comprehensive List of Mobile Task Forces" (fragment above) and captioned "Logo by ..."
# on its image supplement (fragment:task-forces-complete-list-supplement).
COMPLETE_LIST_CREDITS = {
    'Delta-14': ('EstrellaYoshte', 'http://scp-wiki.wikidot.com/desk-of-junior-designer-s-yvonne',
                 'Matched by unit name: the Comprehensive List license box lists MTF Delta-14 ("Winter Wonderland") by EstrellaYoshte, CC BY-SA 3.0, and its supplement captions the logo "Logo by EstrellaYoshte". The supplement shows delta-14.png from the artist\'s page; this is the directory copy (Delta14.png). The two files were not compared byte-for-byte.'),
    'Pi-1': ('SunnyClockwork', 'http://scp-wiki.wikidot.com/sunny-art-tales',
             'Comprehensive List license box: MTF Pi-1 ("City Slickers") by SunnyClockwork, CC BY-SA 3.0. Its supplement shows this same file (task-forces/Pi1.png) captioned "Logo by SunnyClockwork".'),
}


MTF_WITHHELD = {'Nu-3'}  # insignia on the directory with no license entry anywhere we could find


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
        insignia, has_insignia, withheld = emblem, True, False
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
                elif d in COMPLETE_LIST_CREDITS:
                    author, src, note = COMPLETE_LIST_CREDITS[d]
                    cr = dict(title=o['image'].rsplit('/', 1)[-1], author=author, page=MTF_COMPLETE_LICBOX, url=o['image'],
                              license='CC BY-SA 3.0', licenseUrl=LIC['CC BY-SA 3.0'], basis='license-box', note=note,
                              modified=MODIFIED, listedSource=src)
                elif d in MTF_WITHHELD:
                    cr = None
                else:
                    cr = dict(title=o['image'].rsplit('/', 1)[-1], author='Not listed in the directory license box', page=MTF_DIR, url=o['image'],
                              license='CC BY-SA 3.0 (page license)', licenseUrl=LIC['CC BY-SA 3.0'], basis='page-license',
                              note='PENDING: insignia shown on the directory with no entry in the directory license box or the Comprehensive List license box; author not confirmed.', modified=MODIFIED)
                    gaps.append(dict(id=sid, gap='insignia credit not in license box'))
            if cr is None:
                (ROOT / rel).unlink(missing_ok=True)
                insignia, has_insignia, cid, withheld = emblem, False, 'foundation-emblem', True
                gaps.append(dict(id=sid, gap='insignia withheld: no license entry found; shared Foundation emblem shown'))
            else:
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
            insigniaStatus='sourced' if has_insignia else 'withheld' if withheld else 'none', coverage='dossier',
            mission=mission or None, missionSource=MTF_DIR, purpose=pick_purpose(sentences),
            specialty=specialty, roles=roles, gearQuotes=gear, utilizing=links.get('Utilizing Objects', []),
            deployments=links.get('Known Deployments', []), assisting=links.get('Assisting in Containment of Objects', []),
            reports=links.get('Action Reports', [])))
    return out, gaps


# ------------------------------------------------- comprehensive list (sparse)
LIST_PREFIX = re.compile(r'^([A-Z]{2,5})(?:[-\s]+)(.+)$')
ALIAS_PAT = re.compile(r',|\s/\s|\baka\b|\balso known as\b|\bformerly\b', re.I)


def designation_key(designation):
    """Number part only, folded: 'MTF-Alpha-9', 'CTF Alpha-9' and 'Alpha-9' share 'alpha9'."""
    d = LIST_PREFIX.match(designation.strip())
    core = d.group(2) if d else designation
    core = unicodedata.normalize('NFD', core)
    core = ''.join(ch for ch in core if not unicodedata.combining(ch))
    core = re.sub(r'-0+(\d)', r'-\1', core)
    return re.sub(r'[^a-z0-9]+', '', core.lower())


def build_list_mtf(credits, rich):
    """Every task-force row of the Comprehensive List that is not one of the 108 directory units.

    Only the list entry itself is used: designation, codename, the pages it links,
    its one-line scope, and the list's verified marker. Linked pages are not read.
    """
    rows = json.loads((RES / 'mtflist/complete_rows.json').read_text())
    sup = json.loads((RES / 'mtflist/insignia_match.json').read_text())
    files = json.loads((RES / 'mtflist/insignia_files.json').read_text())
    excluded = {'Vehicles': 0, 'Joke': 0}
    rich_by_anchor = {}
    for t in rich:
        rich_by_anchor[slug(t['designation'])] = rich_by_anchor.get(slug(t['designation']), []) + [t]
    seen = {t['id']: 1 for t in rich}
    out, main_hits = [], 0

    def norm(x):
        return re.sub(r'[^a-z0-9]+', '', re.sub(r'\bthe\b', '', html.unescape(x).lower().replace("'s", 's')))

    for idx, r in enumerate(rows):
        if r['group'] in excluded:
            excluded[r['group']] += 1
            continue
        if r['main']:
            anchor = next((l['url'].split('#', 1)[1] for l in r['pages'] if '#' in l['url']), '')
            cands = [t for t in rich if 'listScope' not in t and (slug(t['designation']) == anchor or t['id'] == anchor)]
            cands = cands or [t for t in rich if 'listScope' not in t and norm(t['callsign']) == norm(r['codename'])]
            assert cands, ('main row not matched', r)
            t = max(cands, key=lambda t: difflib.SequenceMatcher(None, norm(t['callsign']), norm(r['codename'])).ratio())
            t['listVerified'] = r['verified']
            t['listScope'] = r['scope']
            t['listGroup'] = r['group']
            main_hits += 1
            continue
        m = LIST_PREFIX.match(r['designation'])
        kind, des = (m.group(1), m.group(2)) if m else ('', r['designation'])
        code = r['codename'].strip()
        base = slug(f'{kind} {des} {code}') or slug(f'{kind} {des}') or f'row-{idx}'
        sid, k = 'tf-' + base, 2
        while sid in seen:
            sid, k = f'tf-{base}-{k}', k + 1
        seen[sid] = 1
        scope = clean_text(r['scope'])
        undocumented = not scope or scope.lower().startswith('no description given')
        spec = re.search(r'speciali[sz]\w*\s+in\s+(.+?)(?:\.\s|\.$|$)', scope, re.I)
        roles = [x for x, pat in ROLE_RULES if re.search(pat, scope + ' ' + code, re.I)] or (['Undocumented'] if undocumented else ['General containment'])
        greek = r['group'] if r['group'] in GREEK else 'Other'
        # insignia: only a supplement image with a license-box entry on the Comprehensive List
        key = norm(LIST_PREFIX.sub(r'\2', r['designation'].strip())) + '|' + norm(code)
        sm = sup.get(key)
        status, insignia, cid = 'none', 'assets/sourced/foundation-emblem.webp', 'foundation-emblem'
        if sm:
            best = sm['best']
            f = files.get(best['img']) if best else None
            if best and f and 'size' in f:
                rel = f'assets/sourced/mtf-list/{sid}.webp'
                to_webp(RES / f['file'], ROOT / rel, 400)
                e = best['license']
                cid = f'mtf-{sid}'
                credits[cid] = wiki_credit(e, MTF_COMPLETE, best['img'], title=e.get('Name') or e.get('Filename'),
                                           note='License-box entry on A Comprehensive List of Mobile Task Forces; image from its logo supplement.')
                credits[cid]['subject'] = f'{kind} {des} "{code}"'.strip()
                status, insignia = 'sourced', rel
            else:
                status = 'withheld'
        out.append(dict(
            id=sid, coverage='list', designation=des, callsign=code, kind=kind,
            listedAs=r['designation'], section='list', order=10000 + idx, greek=greek, listGroup=r['group'],
            number=''.join(re.findall(r'-(.+)$', des)), pick=False, verified=r['verified'],
            insignia=insignia, plate=plate_for(insignia) if status == 'sourced' else 'dark',
            hasInsignia=status == 'sourced', insigniaStatus=status, credit=cid,
            scope=None if undocumented else scope, specialty=spec.group(1).strip().rstrip('.') if spec else None,
            roles=roles, pages=[dict(href=l['url'], label=l['label']) for l in r['pages']],
            pagesText=None if r['pages'] else (r['pagesText'] or None),
            aliasNote=bool(ALIAS_PAT.search(code)), source=MTF_COMPLETE))
    assert main_hits == len(rich), (main_hits, len(rich))
    # designations reused by more than one entry (directory + list)
    allt = rich + out
    groups = {}
    for t in allt:
        groups.setdefault(designation_key(t['designation']), []).append(t)
    shared = 0
    for t in allt:
        others = [o for o in groups[designation_key(t['designation'])] if o is not t]
        t['sharedDesignation'] = [dict(id=o['id'], label=f'{o["kind"]} {o["designation"]}'.strip() + (f' “{o["callsign"]}”' if o['callsign'] else '')) for o in others[:12]]
        t['sharedCount'] = len(others)
        shared += bool(others)
    for t in rich:
        t.setdefault('listVerified', None)
    stats = dict(listRows=len(rows), excluded=excluded, directory=len(rich), listOnly=len(out), total=len(allt),
                 withScope=sum(1 for t in out if t['scope']), undocumented=sum(1 for t in out if not t['scope']),
                 verified=sum(1 for t in out if t['verified']),
                 insignia=dict(sourced=sum(1 for t in out if t['insigniaStatus'] == 'sourced'),
                               withheld=sum(1 for t in out if t['insigniaStatus'] == 'withheld'),
                               none=sum(1 for t in out if t['insigniaStatus'] == 'none')),
                 sharedDesignationEntries=shared, designationGroupsShared=sum(1 for g in groups.values() if len(g) > 1),
                 aliasEntries=sum(1 for t in out if t['aliasNote']))
    return out, stats


# ----------------------------------------------------------------- credits
BASIS_LABELS = {
    'license-box': 'Page license box',
    'commons': 'Wikimedia Commons metadata',
    'source-license': 'License on source page',
    'artist-page': "Artist's own page (page license)",
    'page-license': 'Pending: no per-file license',
}


def render_credits(media, groups, mtf, credits, anomalies, list_stats):
    e = html.escape
    def row(cid, label, anchor):
        if cid is None:
            return (f'<tr id="{e(anchor)}"><th scope="row">{e(label)}</th><td colspan="4">Logo withheld — not published.</td>'
                    f'<td><span class="basis basis-page-license">Withheld</span> No license entry was found for the directory logo.</td></tr>')
        c = credits[cid]
        basis = BASIS_LABELS[c['basis']]
        comp = ''.join(f'<li>{e(x["name"] or "")} — {e(x["author"] or "")} ({e(x["license"] or "")})</li>' for x in c.get('components', []))
        comp = f'<details><summary>Components ({len(c["components"])})</summary><ul>{comp}</ul></details>' if comp else ''
        lic = f'<a href="{e(c["licenseUrl"])}" rel="noopener license">{e(c["license"])}</a>' if c.get('licenseUrl') else e(c['license'])
        return (f'<tr id="{e(anchor)}"><th scope="row">{e(label)}</th><td>{e(c["title"])}</td><td>{e(c["author"])}</td><td>{lic}</td>'
                f'<td><a href="{e(c["page"])}" rel="noopener">Source page</a><br><a class="mono" href="{e(c["url"])}" rel="noopener">Image file</a></td>'
                f'<td><span class="basis basis-{c["basis"]}">{basis}</span>{(" " + e(c["note"])) if c.get("note") else ""}{comp}</td></tr>')
    head = '<thead><tr><th scope="col">Entry</th><th scope="col">Image</th><th scope="col">Author / credit</th><th scope="col">License</th><th scope="col">Links</th><th scope="col">Basis &amp; notes</th></tr></thead>'
    a_rows = ''.join(row(media[x['id']]['credit'], f'{x["itemNumber"]} · {x["name"]}', f'credit-scp-{x["id"]}') for x in anomalies)
    g_rows = ''.join(row(g['credit'], g['name'], f'credit-goi-{g["id"]}') for g in groups)
    def mlabel(t):
        tail = '' if t['hasInsignia'] else ' (insignia withheld — shared emblem)' if t['insigniaStatus'] == 'withheld' else ' (no insignia — shared emblem)'
        return f'{t["kind"]} {t["designation"]}'.strip() + (f' “{t["callsign"]}”' if t['callsign'] else '') + tail
    m_rows = row('foundation-emblem', 'Shared Foundation emblem (placeholder)', 'credit-foundation-emblem')
    m_rows += ''.join(row(t['credit'], mlabel(t), f'credit-mtf-{t["id"]}') for t in mtf if t['coverage'] == 'dossier' or t['hasInsignia'])
    counts = {b: sum(1 for c in credits.values() if c['basis'] == b) for b in BASIS_LABELS}
    src_rows = ''.join(f'<li><a href="{e(x["source"])}" rel="noopener">{e(x["itemNumber"])} — {e(x["name"])}</a></li>' for x in anomalies)
    tpl = (ROOT / 'tools/credits.template.html').read_text()
    return (tpl.replace('{{ANOMALY_ROWS}}', a_rows).replace('{{GROUP_ROWS}}', g_rows).replace('{{MTF_ROWS}}', m_rows).replace('{{HEAD}}', head)
            .replace('{{SOURCE_LIST}}', src_rows).replace('{{N_BOX}}', str(counts['license-box'])).replace('{{N_COMMONS}}', str(counts['commons']))
            .replace('{{N_SOURCE}}', str(counts['source-license'])).replace('{{N_ARTIST}}', str(counts['artist-page']))
            .replace('{{N_PAGE}}', str(counts['page-license'])).replace('{{N_TOTAL}}', str(len(credits)))
            .replace('{{N_GOI}}', str(len(groups))).replace('{{N_MTF}}', str(len(mtf)))
            .replace('{{N_MTF_DIR}}', str(list_stats['directory'])).replace('{{N_MTF_LIST}}', str(list_stats['listOnly']))
            .replace('{{N_MTF_LIST_INSIGNIA}}', str(list_stats['insignia']['sourced'])).replace('{{N_MTF_LIST_WITHHELD}}', str(list_stats['insignia']['withheld']))
            .replace('{{N_MTF_LIST_NONE}}', str(list_stats['insignia']['none'])))


def main():
    meta = json.loads((RES / 'commons_meta.json').read_text())
    credits = {}
    media = build_anomalies(credits)
    groups, goi_gaps = build_groups(credits, meta)
    mtf, mtf_gaps = build_mtf(credits, meta)
    mtf_list, list_stats = build_list_mtf(credits, mtf)
    anomalies = sorted(json.loads((ROOT / 'data.json').read_text()), key=lambda x: int(x['id']))
    coll = dict(generated='tools/build_collections.py', sources=dict(groups=GOI_DIR, taskForces=MTF_DIR, taskForcesComplete=MTF_COMPLETE,
                taskForcesNote=('Full dossiers for the 108 units on the Mobile Task Forces directory, plus every other task-force row of A Comprehensive List '
                                'of Mobile Task Forces as a sparse entry (designation, codename, linked pages, one-line scope). Vehicles and joke task forces '
                                'on that list are excluded. The list calls itself a writers\' tool, not a canonical record.')),
                taskForceStats=list_stats,
                anomalyMedia=media, groups=groups, taskForces=mtf + mtf_list, credits=credits,
                gaps=dict(groupLogoCredit=goi_gaps, taskForces=mtf_gaps))
    (ROOT / 'collections.json').write_text(json.dumps(coll, ensure_ascii=False, indent=1) + '\n')
    (ROOT / 'credits.html').write_text(render_credits(media, groups, mtf + mtf_list, credits, anomalies, list_stats))
    print(f'anomalies={len(media)} groups={len(groups)} taskForces={len(mtf)}+{len(mtf_list)} credits={len(credits)} goiGaps={goi_gaps} mtfGaps={len(mtf_gaps)}')
    print(json.dumps(list_stats))


if __name__ == '__main__':
    main()
