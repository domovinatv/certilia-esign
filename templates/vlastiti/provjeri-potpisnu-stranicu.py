#!/usr/bin/env python3
"""Provjerava je li potpisna stranica PDF-a ostavila slobodne ćelije mreže vizuala.

    python3 templates/vlastiti/provjeri-potpisnu-stranicu.py ugovori/zajam.pdf [--celije 5,6,9]

Ponavlja algoritam iz `src/visual.ts` (GetVisualGrid iz Priloga A + mjerenje tinte),
pa daje isti odgovor kakav će dati i server pri odabiru pozicije vizuala:

  * udio tamnih piksela po ćeliji (prag 0,004 — iznad toga ćelija je „zauzeta");
  * riječi koje upadaju u rezervirane ćelije (pdftotext -bbox).

Ovisi samo o poppleru (pdfinfo, pdftoppm, pdftotext), bez Python paketa.
"""
import re
import subprocess
import sys

POINTS_IN_MM = 2.83464567
MARGIN_PT = 10 * POINTS_IN_MM
VISUAL_W_PT, VISUAL_H_PT = 248.0, 122.0
RENDER_DPI = 50
INK_THRESHOLD = 0.004
DARK_PIXEL = 225
PADDING_PT = 4


def visual_grid(page_w, page_h):
    """Ćelije mreže (relPos 1..12, red po red od vrha), ishodište gore-lijevo."""
    horiz = int((page_w - 2 * MARGIN_PT) // VISUAL_W_PT)
    vert = int((page_h - 2 * MARGIN_PT) // VISUAL_H_PT)
    if horiz < 1 or vert < 1:
        return []
    hspace = (page_w - (2 * MARGIN_PT + horiz * VISUAL_W_PT)) / (horiz - 1) if horiz > 1 else 0
    vspace = (page_h - (2 * MARGIN_PT + vert * VISUAL_H_PT)) / (vert - 1) if vert > 1 else 0
    cells, cnt = [], 1
    bottom = page_h - MARGIN_PT - VISUAL_H_PT
    for _ in range(vert):
        left = MARGIN_PT
        for _ in range(horiz):
            cells.append({'pos': cnt, 'x': left, 'y': page_h - (bottom + VISUAL_H_PT)})
            left += hspace + VISUAL_W_PT
            cnt += 1
        bottom -= vspace + VISUAL_H_PT
    return [c for c in cells if c['pos'] <= 12]


def parse_pgm(buf):
    if buf[:2] != b'P5':
        raise SystemExit('pdftoppm nije vratio P5 PGM')
    fields, i = [], 2
    while len(fields) < 3:
        while buf[i:i + 1].isspace():
            i += 1
        if buf[i:i + 1] == b'#':
            i = buf.index(b'\n', i) + 1
            continue
        start = i
        while not buf[i:i + 1].isspace():
            i += 1
        fields.append(int(buf[start:i]))
    i += 1
    w, h, _ = fields
    return w, h, buf[i:i + w * h]


def ink_fraction(px, w, h, x0, y0, x1, y1):
    xa, ya = max(0, round(x0)), max(0, round(y0))
    xb, yb = min(w, round(x1)), min(h, round(y1))
    dark = total = 0
    for y in range(ya, yb):
        row = px[y * w + xa:y * w + xb]
        total += len(row)
        dark += sum(1 for v in row if v < DARK_PIXEL)
    return 1.0 if total == 0 else dark / total


def words_on_page(pdf, page):
    out = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', pdf, '-'],
                         capture_output=True, text=True, check=True).stdout
    return [{'x0': float(m[0]), 'y0': float(m[1]), 'x1': float(m[2]), 'y1': float(m[3]), 'text': m[4]}
            for m in re.findall(
                r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', out)]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = dict(a.split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
    if not args:
        sys.exit(__doc__)
    pdf = args[0]
    info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True, check=True).stdout
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
    page = int(args[1]) if len(args) > 1 else pages
    reserved = [int(x) for x in opts.get('--celije', '5,6,9').split(',') if x]

    raw = subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', str(RENDER_DPI), '-gray', pdf],
                         capture_output=True, check=True).stdout
    w, h, px = parse_pgm(raw)
    scale = RENDER_DPI / 72
    page_w, page_h = w / scale, h / scale
    cells = visual_grid(page_w, page_h)

    print(f'{pdf}, stranica {page} od {pages} ({page_w:.0f}×{page_h:.0f} pt)\n')
    print('ćelija    x        y        tinta     stanje')
    free = []
    for c in cells:
        ink = ink_fraction(px, w, h, (c['x'] - PADDING_PT) * scale, (c['y'] - PADDING_PT) * scale,
                           (c['x'] + VISUAL_W_PT + PADDING_PT) * scale,
                           (c['y'] + VISUAL_H_PT + PADDING_PT) * scale)
        c['ink'] = ink
        if ink <= INK_THRESHOLD:
            free.append(c['pos'])
        mark = 'slobodna' if ink <= INK_THRESHOLD else 'ZAUZETA'
        star = ' ←rezervirana' if c['pos'] in reserved else ''
        print(f"{c['pos']:>4}   {c['x']:6.1f}   {c['y']:6.1f}   {ink:7.4f}   {mark}{star}")

    print(f'\nslobodne ćelije: {free or "nijedna"}')
    ok = True
    for pos in reserved:
        if pos not in free:
            ok = False
            print(f'GREŠKA: rezervirana ćelija {pos} nije slobodna')

    words = words_on_page(pdf, page)
    for c in cells:
        if c['pos'] not in reserved:
            continue
        hits = [x for x in words
                if x['x1'] > c['x'] and x['x0'] < c['x'] + VISUAL_W_PT
                and x['y1'] > c['y'] and x['y0'] < c['y'] + VISUAL_H_PT]
        if hits:
            ok = False
            print(f"GREŠKA: u ćeliju {c['pos']} upadaju riječi: "
                  + ', '.join(f"„{x['text']}\" ({x['x0']:.0f},{x['y0']:.0f})" for x in hits[:8]))

    print('\nOK — rezervirane ćelije su prazne.' if ok else '\nNIJE OK.')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
