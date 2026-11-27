#!/usr/bin/env python3
"""Check the pictures a pull request adds, and show what Shelf will make of them.

    check.py PICTURES_DIR --out OUTDIR [--changed FILE ...]

Every picture in PICTURES_DIR is checked for key collisions (two files that are one game to Shelf); the files named by --changed
(all of them if none are) are checked in full and drawn, enlarged, on OUTDIR/preview.png as Shelf's 72x36 will show them. OUTDIR/
report.md is the text for the pull request. Exit status 1 if anything is wrong (a warning is not).
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mkpack  # noqa: E402
from PIL import Image  # noqa: E402

Image.MAX_IMAGE_PIXELS = 16_000_000  # a larger picture is refused (decompression bombs)
EXTS = ('.png', '.bmp', '.gif', '.jpg', '.jpeg')
MAX_BYTES = 500_000
BAD_CHARS = '/\\:*?"<>|'


def check_one(dirpath, f):
    """(errors, warnings) for one picture."""
    errs, warns = [], []
    stem, ext = os.path.splitext(f)
    path = os.path.join(dirpath, f)
    if ext.lower() not in EXTS:
        return ['not a png, bmp, gif or jpg file'], warns
    if os.path.getsize(path) > MAX_BYTES:
        errs.append('larger than %d KB' % (MAX_BYTES // 1000))
    if not stem.strip() or not any(c.isalnum() for c in stem):
        errs.append('the name has no letters or digits')
    if any(c in stem for c in BAD_CHARS) or any(ord(c) < 32 for c in stem):
        errs.append('the name has a character a file name cannot have')
    if len(stem) > mkpack.TITLE_MAX:
        warns.append('the name is longer than %d characters: Shelf only sees the first %d' % (mkpack.TITLE_MAX, mkpack.TITLE_MAX))
    if errs:
        return errs, warns
    try:
        with Image.open(path) as im:
            im.load()
            w, h = im.size
    except Exception as e:  # noqa: BLE001  (whatever Pillow says)
        return errs + ['cannot be read as a picture (%s)' % e.__class__.__name__], warns
    if w < 144 or h < 72:
        warns.append('only %dx%d: it will be scaled to 72x36 and may look soft' % (w, h))
    if not 1.8 <= w / h <= 2.2:
        warns.append('%dx%d is not 2:1: a 2:1 band is cut from it (top by default)' % (w, h))
    return errs, warns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pictures')
    ap.add_argument('--out', required=True)
    ap.add_argument('--changed', nargs='*', default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files = sorted(f for f in os.listdir(a.pictures) if not f.startswith('.'))
    changed = files if a.changed is None else [os.path.basename(c) for c in a.changed if os.path.basename(c) in files]
    bad, lines, tiles = 0, [], []
    owner = {}
    for f in files:  # collisions: across everything
        owner.setdefault(mkpack.tkey(os.path.splitext(f)[0]), []).append(f)
    for f in changed:
        errs, warns = check_one(a.pictures, f)
        same = [g for g in owner.get(mkpack.tkey(os.path.splitext(f)[0]), []) if g != f]
        if same:
            errs.append('the same game as %s to Shelf (a title key is its letters and digits, whatever the case or spacing)' %
                        ', '.join('`%s`' % g for g in same))
        mark = 'FAIL' if errs else ('warn' if warns else 'ok')
        lines.append('- **%s** `%s`' % (mark, f))
        lines += ['  - ERROR: ' + e for e in errs] + ['  - warning: ' + w for w in warns]
        bad += bool(errs)
        if not errs:
            try:
                tiles.append((os.path.splitext(f)[0], Image.open(os.path.join(a.pictures, f)), mkpack.make_picture(
                    os.path.join(a.pictures, f), 'top')[1]))
            except Exception as e:  # noqa: BLE001
                lines.append('  - ERROR: could not be converted (%s)' % e.__class__.__name__)
                bad += 1
    head = ['## Picture check', '', '%d picture(s) in this change, %d with errors. %d in the library.' % (len(changed), bad, len(files)), '']
    if not changed:
        head.append('No pictures changed.')
    open(os.path.join(a.out, 'report.md'), 'w').write('\n'.join(head + lines) + '\n')
    if tiles:  # the original (reduced) beside what Shelf will show (4x), a row each
        row_h = 36 * 4 + 8
        sheet = Image.new('RGB', (2 * 288 + 3 * 8, len(tiles) * row_h + 8), (40, 40, 80))
        for i, (name, src, thumb) in enumerate(tiles):
            o = src.convert('RGB')
            o.thumbnail((288, 144))
            sheet.paste(o, (8, 8 + i * row_h))
            sheet.paste(thumb.resize((288, 144), Image.NEAREST), (16 + 288, 8 + i * row_h))
        sheet.save(os.path.join(a.out, 'preview.png'))
    sys.stdout.write(open(os.path.join(a.out, 'report.md')).read())
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
