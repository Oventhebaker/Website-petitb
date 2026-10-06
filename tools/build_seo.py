#!/usr/bin/env python3
"""Regenerate sitemap.xml, the legacy redirects in _redirects and the
<noscript> project list in index.html from the site's real project list.

The project slugs come from the live layout (a project's slug is its canvas
coordinate, e.g. e-9e, computed by the page's JavaScript), so the list is
exported from the running site rather than re-derived here:

  1. Open the site in a browser (local preview is fine) and, in the console:
       copy(JSON.stringify(__pbProjects(), null, 1))
  2. Paste that into tools/projects.json
  3. python3 tools/build_seo.py

Run it again whenever a project is added, renamed or moves cell (a new cell
means a new URL). Each run rewrites only the parts between the BEGIN/END
markers, and sets every <lastmod> to today.
"""
import datetime
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://petitbouquetin.fr'
CAT_ORDER = ['edito', 'docu', 'poesie', 'manifeste']
CAT_LABEL = {'edito': 'Éditorial', 'docu': 'Documentaire', 'poesie': 'Poésie', 'manifeste': 'Manifeste'}


def legacy_slug(pcode):
    # E013 -> e-013: the old sequential URL. A project's pcode is its old
    # number (each zone's order has never changed — checked against git
    # history back to the first sitemap), so this maps every old link.
    return pcode[0].lower() + '-' + pcode[1:]


def replace_between(text, begin, end, body):
    pattern = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.S)
    assert pattern.search(text), f'markers not found: {begin}'
    return pattern.sub(lambda _: begin + body + end, text, count=1)


def first_sentence(text):
    m = re.match(r'(.{40,}?[.!?…])(\s|$)', text)
    return m.group(1) if m else text


def main():
    projects = json.loads((ROOT / 'tools' / 'projects.json').read_text(encoding='utf-8'))
    projects.sort(key=lambda p: (CAT_ORDER.index(p['cat']), p['pcode']))
    today = datetime.date.today().isoformat()

    slugs = [p['slug'] for p in projects]
    assert len(slugs) == len(set(slugs)), 'duplicate slugs'

    # ---- sitemap.xml ---------------------------------------------------
    def url(loc, priority):
        return (f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n'
                f'    <changefreq>monthly</changefreq>\n    <priority>{priority}</priority>\n  </url>\n')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += url(SITE + '/', '1.0')
    for p in projects:
        xml += url(f"{SITE}/projets/{p['slug']}", '0.8')
    xml += '</urlset>\n'
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')

    # ---- _redirects: old sequential slugs -> current slugs ---------------
    lines = ''.join(
        f"/projets/{legacy_slug(p['pcode'])}  /projets/{p['slug']}  301\n"
        for p in projects if legacy_slug(p['pcode']) != p['slug'])
    red = (ROOT / '_redirects').read_text(encoding='utf-8')
    red = replace_between(red, '# BEGIN legacy project slugs (tools/build_seo.py)\n',
                          '# END legacy project slugs\n', lines)
    (ROOT / '_redirects').write_text(red, encoding='utf-8')

    # ---- <noscript> project list in index.html ---------------------------
    out = ['<noscript>\n<main>\n<h1>Petit Bouquetin, studio créatif à Paris</h1>\n',
           '<p>Petit Bouquetin est un studio créatif fondé à Paris par Léonard Videt : '
           'éditoriaux de mode, films documentaires, direction artistique et photographie.</p>\n']
    for cat in CAT_ORDER:
        items = [p for p in projects if p['cat'] == cat and p['cat'] != 'manifeste']
        if not items:
            continue
        out.append(f'<h2>{CAT_LABEL[cat]}</h2>\n<ul>\n')
        for p in items:
            out.append(f"<li><a href=\"/projets/{p['slug']}\">{html.escape(p['title'])}</a> — "
                       f"{html.escape(first_sentence(p['intention']))}</li>\n")
        out.append('</ul>\n')
    pages = [p for p in projects if p['cat'] == 'manifeste']
    out.append('<p>' + ' · '.join(
        f"<a href=\"/projets/{p['slug']}\">{'Manifeste' if p['title'] == 'Petit Bouquetin' else html.escape(p['title'])}</a>"
        for p in pages) + '</p>\n</main>\n</noscript>\n')
    idx = (ROOT / 'index.html').read_text(encoding='utf-8')
    idx = replace_between(idx, '<!-- BEGIN project list for crawlers (tools/build_seo.py) -->\n',
                          '<!-- END project list for crawlers -->\n', ''.join(out))
    (ROOT / 'index.html').write_text(idx, encoding='utf-8')

    print(f'{len(projects)} projects — sitemap, _redirects and <noscript> list updated ({today}).')


if __name__ == '__main__':
    main()
