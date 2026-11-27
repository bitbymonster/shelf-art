#!/usr/bin/env python3
"""Make the static files a Shelf art server hosts (README: Network art, docs/art-fetch.md).

    mkpack.py OUTDIR --from PICTURES [--band top|middle|bottom] [--sheet FILE.png]
    mkpack.py OUTDIR --test COUNT          (made-up pictures, for experiments)

  art.idx  "SAI1", u32 count, then count x (u32 key, u32 offset into art.pak), sorted by key
  art.pak  the pictures: 72x36, 8 bits a pixel in the Next's palette (RRRGGGBB), rows bottom up, 2592 bytes each: the pixel
           data of a BMP (Shelf turns it the right way up when it stores it)

PICTURES is a folder of images (png, bmp, gif, jpg; whatever Pillow reads, e.g. what tools/shotart.py made): each file's name
(without .ext) is the game's title. Shelf finds a picture by the key of the title: djb2 (h = (h * 33) ^ c from 5381, 32 bits)
over its letters and digits in lower case, so "Manic Miner", "ManicMiner" and "manic_miner.bmp" are the same game. A picture that
is not 2:1 gets a 2:1 band cut from it (--band, the top by default: titles are usually there), then it is scaled to 72x36.
Two files with one key: the first is used. Put art.idx and art.pak where Shelf looks (NET_DIR in src/ovl3.c; the Makefile's
NET_HOST, NET_PORT, NET_DIR).
"""
import argparse, os, struct, sys, zlib

PIC = 2592


TITLE_MAX = 30  # Shelf keeps the first 30 characters of a long name (LFN_SHOW), and keys that


def tkey(title):
    h = 5381
    for ch in title[:TITLE_MAX]:
        c = ch.lower()
        if ('a' <= c <= 'z') or ('0' <= c <= '9'):
            h = (((h << 5) + h) ^ ord(c)) & 0xFFFFFFFF
    return h


def next_palette():
    from PIL import Image
    flat = []
    for n in range(256):
        flat += [(n >> 5) * 255 // 7, ((n >> 2) & 7) * 255 // 7, (n & 3) * 255 // 3]
    pal = Image.new('P', (1, 1))
    pal.putpalette(flat)
    return pal


def make_picture(path, band):
    from PIL import Image
    im = Image.open(path).convert('RGB')
    w, h = im.size
    bh = w // 2
    if bh < h:  # a 2:1 band
        y = {'top': 0, 'middle': (h - bh) // 2, 'bottom': h - bh}[band]
        im = im.crop((0, y, w, y + bh))
    elif bh > h:  # wider than 2:1: cut the sides
        bw = h * 2
        im = im.crop(((w - bw) // 2, 0, (w - bw) // 2 + bw, h))
    im = im.resize((72, 36), Image.LANCZOS)
    q = im.quantize(palette=next_palette(), dither=Image.Dither.FLOYDSTEINBERG)
    px = q.tobytes()
    rows = [px[y * 72:(y + 1) * 72] for y in range(36)]
    return b''.join(reversed(rows)), im  # BMP order: the bottom row first


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out')
    ap.add_argument('--from', dest='src')
    ap.add_argument('--band', default='top', choices=['top', 'middle', 'bottom'])
    ap.add_argument('--sheet')
    ap.add_argument('--test', type=int)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pics = {}  # key -> (name, bytes)
    if a.test:
        for i in range(a.test * 2):
            k = zlib.crc32(b"game %d" % i)
            if k not in pics and len(pics) < a.test:
                pics[k] = ("test %d" % i, struct.pack("<I", k) + bytes([len(pics) & 255]) * (PIC - 4))
    elif a.src:
        thumbs = []
        for f in sorted(os.listdir(a.src)):
            stem, ext = os.path.splitext(f)
            if ext.lower() not in ('.png', '.bmp', '.gif', '.jpg', '.jpeg'):
                continue
            k = tkey(stem)
            if k in pics:
                print('skipped %s: the same key as %s' % (f, pics[k][0]))
                continue
            data, im = make_picture(os.path.join(a.src, f), a.band)
            pics[k] = (stem, data)
            thumbs.append((stem, im))
        if a.sheet:
            from PIL import Image
            cols = 6
            rows = (len(thumbs) + cols - 1) // cols
            sh = Image.new('RGB', (cols * 152 + 8, rows * 84 + 8), (40, 40, 80))
            for i, (n, im) in enumerate(thumbs):
                sh.paste(im.resize((144, 72), Image.NEAREST), (8 + (i % cols) * 152, 8 + (i // cols) * 84))
            sh.save(a.sheet)
    else:
        ap.error('--from or --test')
    keys = sorted(pics)
    with open(os.path.join(a.out, 'art.idx'), 'wb') as idx, open(os.path.join(a.out, 'art.pak'), 'wb') as pak:
        idx.write(b'SAI1' + struct.pack('<I', len(keys)))
        for i, k in enumerate(keys):
            idx.write(struct.pack('<II', k, i * PIC))
            pak.write(pics[k][1])
    print('%d pictures, art.idx %d bytes, art.pak %d bytes' % (len(keys), 8 + 8 * len(keys), PIC * len(keys)))


if __name__ == '__main__':
    main()
