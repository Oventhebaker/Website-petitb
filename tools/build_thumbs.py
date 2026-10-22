#!/usr/bin/env python3
"""Make the small images the project galleries show as thumbnails.

A project page's thumbnail grid used to load every photo at full size
(up to 2560 px and 1.2 MB each) to draw squares a few dozen pixels wide:
opening "Mon ami Paul" meant ~20 MB. Each gallery photo now has a light
copy at images/_thumbs/<same path>.webp (shortest side 240 px), which is
what the grid shows (thumbOf() in index.html); the large image still uses
the original.

Run it again whenever gallery photos are added (it skips the thumbnails
that already exist):

  python3 tools/build_thumbs.py

Needs ImageMagick (`magick`).
"""
import pathlib
import re
import subprocess
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIDE = 240     # shortest side, px: 2× the largest thumbnail cell
QUALITY = 72


def gallery_paths(html):
    # Every photo listed in the GALLERY table, plus the ones added inline to
    # a project's gallery: [...] list.
    start = html.index('const GALLERY = {')
    end = html.index('\n};', start)
    chunks = [html[start:end]] + re.findall(r'gallery: \[[^\]]*\]', html)
    paths = set()
    for chunk in chunks:
        paths.update(re.findall(r"'(images/[^']+\.(?:webp|jpe?g|png))'", chunk))
    return sorted(paths)


def thumb_of(path):
    # Must match thumbOf() in index.html.
    return re.sub(r'\.(?:webp|jpe?g|png)$', '.webp', path.replace('images/', 'images/_thumbs/', 1))


def main():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    made = skipped = missing = 0
    for url in gallery_paths(html):
        src = ROOT / urllib.parse.unquote(url)
        dst = ROOT / urllib.parse.unquote(thumb_of(url))
        if not src.exists():
            print('missing:', src.relative_to(ROOT))
            missing += 1
            continue
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['magick', str(src), '-auto-orient', '-strip',
                        '-resize', f'{SIDE}x{SIDE}^', '-quality', str(QUALITY), str(dst)], check=True)
        made += 1
    print(f'{made} thumbnails made, {skipped} up to date, {missing} missing.')


if __name__ == '__main__':
    main()
