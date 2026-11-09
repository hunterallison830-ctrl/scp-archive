"""Build a single-file offline preview of the archive for file:// viewing.

Production files are read, never modified. The output inlines style.css,
archive-core.js, app.js, data.json and collections.json, and turns every
local asset path found in the JSON or index.html into a data: URL, so the
page needs no server and no network. Only `fetch` for the two JSON files is
shimmed; app logic is the same code the site ships.

Usage: python3 tools/build_standalone.py [OUT_DIR]   (default: ../scp-archive-offline)
"""
import base64, json, mimetypes, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / 'scp-archive-offline'
MIME = {'.webp': 'image/webp', '.svg': 'image/svg+xml', '.mp4': 'video/mp4', '.png': 'image/png', '.jpg': 'image/jpeg'}
cache = {}


def data_url(rel):
    if rel not in cache:
        p = ROOT / rel
        mime = MIME.get(p.suffix.lower()) or mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
        cache[rel] = f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode()
    return cache[rel]


def inline_paths(node):
    if isinstance(node, dict):
        return {k: inline_paths(v) for k, v in node.items()}
    if isinstance(node, list):
        return [inline_paths(v) for v in node]
    if isinstance(node, str) and node.startswith('assets/') and (ROOT / node).is_file():
        return data_url(node)
    return node


def script_safe(text):
    return text.replace('</', '<\\/')


def main():
    records = inline_paths(json.loads((ROOT / 'data.json').read_text()))
    collections = inline_paths(json.loads((ROOT / 'collections.json').read_text()))
    html = (ROOT / 'index.html').read_text()
    html = re.sub(r'(src|href)="(assets/[^"]+)"', lambda m: f'{m.group(1)}="{data_url(m.group(2))}"', html)
    shim = ('<script>/* offline preview: serve the two JSON files from memory */\n'
            f'window.__RAISA_EMBED__={{"data.json":{script_safe(json.dumps(records))},"collections.json":{script_safe(json.dumps(collections))}}};\n'
            '(function(){const real=window.fetch&&window.fetch.bind(window);window.fetch=function(u,o){const k=String(u).split("/").pop();'
            'if(Object.prototype.hasOwnProperty.call(window.__RAISA_EMBED__,k)){return Promise.resolve(new Response(JSON.stringify(window.__RAISA_EMBED__[k]),{status:200,headers:{"Content-Type":"application/json"}}));}'
            'return real?real(u,o):Promise.reject(new Error("offline"));};'
            '/* some engines refuse history updates on file:// pages; keep the app working and just skip the URL update */'
            '["pushState","replaceState"].forEach(function(n){const f=history[n].bind(history);history[n]=function(){try{return f.apply(null,arguments);}catch(e){if(e&&e.name==="SecurityError")return;throw e;}};});'
            '})();</script>')
    css = (ROOT / 'style.css').read_text()
    assert 'url(assets' not in css.replace(' ', ''), 'style.css references assets; inline them too'
    html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>\n{css}\n</style>')
    core = script_safe((ROOT / 'archive-core.js').read_text())
    app = script_safe((ROOT / 'app.js').read_text())
    html = html.replace('<script src="archive-core.js" defer></script>', shim)
    # defer semantics: run the app after the DOM is parsed, in the original order.
    html = html.replace('<script src="app.js" defer></script>', '')
    html = html.replace('</body>', f'<script>\n{core}\n</script>\n<script>\n{app}\n</script>\n</body>')
    assert 'src="assets/' not in html and 'href="assets/' not in html
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(html)
    shutil.copy(ROOT / 'credits.html', OUT / 'credits.html')
    css_link = '<link rel="stylesheet" href="style.css">'
    cred = (OUT / 'credits.html').read_text()
    if css_link in cred:
        (OUT / 'credits.html').write_text(cred.replace(css_link, f'<style>\n{css}\n</style>'))
    cred = (OUT / 'credits.html').read_text()
    cred = re.sub(r'(src|href)="(assets/[^"]+)"', lambda m: f'{m.group(1)}="{data_url(m.group(2))}"', cred)
    (OUT / 'credits.html').write_text(cred)
    (OUT / 'README.txt').write_text(
        'RAISA archive - offline preview\n\n'
        'Open index.html directly in a browser (double-click, or file:///.../index.html).\n'
        'Everything (data, images, videos) is embedded; no server or network is needed.\n'
        'credits.html is the attribution register and opens from the in-page links.\n'
        'This is a review copy of the private build, not a deployment.\n')
    print(f'wrote {OUT/"index.html"} ({(OUT/"index.html").stat().st_size/1e6:.1f} MB), embedded {len(cache)} files')


if __name__ == '__main__':
    main()
