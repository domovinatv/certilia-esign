/**
 * Dinamički odabir pozicije vizuala potpisa: renderira stranicu PDF-a (poppler
 * pdftoppm u PGM grayscale), izračuna mrežu lokacija identično algoritmu iz
 * Priloga A specifikacije (GetVisualGrid) i odabere najnižu ćeliju bez sadržaja
 * (desna prije lijeve). Ako nijedna ćelija nije prazna ili poppler nije
 * dostupan, vraća null — pozivatelj tada koristi pageNumber=0/pageLocation=0,
 * čime ePotpis dodaje praznu stranicu (garantirano bez preklapanja).
 */
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const run = promisify(execFile);

const POINTS_IN_MM = 2.83464567;
const MARGIN_PT = 10 * POINTS_IN_MM;
const VISUAL_W_PT = 248;
const VISUAL_H_PT = 122;
const RENDER_DPI = 50;
/** Udio "tamnih" piksela iznad kojeg ćeliju smatramo zauzetom. */
const INK_THRESHOLD = 0.004;
/** Piksel tamniji od ovoga (0-255) računa se kao sadržaj. */
const DARK_PIXEL = 225;
/** Dodatni razmak oko ćelije koji također mora biti prazan (pt). */
const PADDING_PT = 4;

interface Pgm {
  width: number;
  height: number;
  pixels: Uint8Array;
}

function parsePgm(buf: Buffer): Pgm {
  // P5 header: "P5" <ws> width <ws> height <ws> maxval <single ws> raster
  if (buf[0] !== 0x50 || buf[1] !== 0x35) throw new Error('Nije P5 PGM');
  const fields: number[] = [];
  let i = 2;
  while (fields.length < 3) {
    while (i < buf.length && /\s/.test(String.fromCharCode(buf[i]!))) i++;
    if (buf[i] === 0x23) {
      while (i < buf.length && buf[i] !== 0x0a) i++;
      continue;
    }
    let start = i;
    while (i < buf.length && !/\s/.test(String.fromCharCode(buf[i]!))) i++;
    fields.push(Number(buf.subarray(start, i).toString('ascii')));
  }
  i++; // jedan whitespace nakon maxval
  const [width, height, maxval] = fields as [number, number, number];
  if (maxval > 255) throw new Error('16-bitni PGM nije podržan');
  return { width, height, pixels: new Uint8Array(buf.subarray(i, i + width * height)) };
}

async function pageCount(pdfPath: string): Promise<number> {
  const { stdout } = await run('pdfinfo', [pdfPath]);
  const m = stdout.match(/^Pages:\s+(\d+)/m);
  if (!m) throw new Error('pdfinfo: ne mogu pročitati broj stranica');
  return Number(m[1]);
}

/** Mreža lokacija po algoritmu GetVisualGrid iz Priloga A (RelPos 1..N, red po red od vrha, s lijeva na desno). */
function visualGrid(pageWpt: number, pageHpt: number) {
  const horizCount = Math.floor((pageWpt - 2 * MARGIN_PT) / VISUAL_W_PT);
  const vertCount = Math.floor((pageHpt - 2 * MARGIN_PT) / VISUAL_H_PT);
  if (horizCount < 1 || vertCount < 1) return [];
  const horizSpace = horizCount > 1
    ? (pageWpt - (2 * MARGIN_PT + horizCount * VISUAL_W_PT)) / (horizCount - 1)
    : 0;
  const vertSpace = vertCount > 1
    ? (pageHpt - (2 * MARGIN_PT + vertCount * VISUAL_H_PT)) / (vertCount - 1)
    : 0;
  const cells: { relPos: number; leftPt: number; topPt: number }[] = [];
  let cnt = 1;
  let bottomStart = pageHpt - MARGIN_PT - VISUAL_H_PT;
  for (let row = 1; row <= vertCount; row++) {
    let leftStart = MARGIN_PT;
    for (let col = 1; col <= horizCount; col++) {
      cells.push({ relPos: cnt, leftPt: leftStart, topPt: pageHpt - (bottomStart + VISUAL_H_PT) });
      leftStart += horizSpace + VISUAL_W_PT;
      cnt++;
    }
    bottomStart -= vertSpace + VISUAL_H_PT;
  }
  return cells.filter((c) => c.relPos <= 12); // pageLocation API prima 0-12
}

function inkFraction(img: Pgm, x0: number, y0: number, x1: number, y1: number): number {
  const xa = Math.max(0, Math.round(x0));
  const ya = Math.max(0, Math.round(y0));
  const xb = Math.min(img.width, Math.round(x1));
  const yb = Math.min(img.height, Math.round(y1));
  let dark = 0;
  let total = 0;
  for (let y = ya; y < yb; y++) {
    const rowOff = y * img.width;
    for (let x = xa; x < xb; x++) {
      total++;
      if (img.pixels[rowOff + x]! < DARK_PIXEL) dark++;
    }
  }
  return total === 0 ? 1 : dark / total;
}

/**
 * Nađi poziciju imena potpisnika na stranici (pdftotext -bbox, koordinate u pt,
 * ishodište gore-lijevo). Vraća centar najniže pojave imena — potpisni blokovi
 * su u pravilu pri dnu stranice. null ako imena nema na stranici.
 */
async function findSignerAnchor(pdfPath: string, page: number, name: string): Promise<{ x: number; y: number } | null> {
  const tokens = name.normalize('NFC').toLowerCase().split(/\s+/).filter((t) => t.length > 2);
  if (tokens.length === 0) return null;
  const { stdout } = await run('pdftotext', ['-f', String(page), '-l', String(page), '-bbox', pdfPath, '-']);
  const words = [...stdout.matchAll(/<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)<\/word>/g)]
    .map((m) => ({ x0: +m[1]!, y0: +m[2]!, x1: +m[3]!, y1: +m[4]!, text: m[5]!.normalize('NFC').toLowerCase().replace(/[.,;:]+$/, '') }))
    .filter((w) => tokens.includes(w.text));
  if (words.length === 0) return null;
  const bottom = words.reduce((a, b) => (b.y1 > a.y1 ? b : a));
  const cluster = words.filter((w) => Math.abs(w.y0 - bottom.y0) < 20);
  return {
    x: cluster.reduce((s, w) => s + (w.x0 + w.x1) / 2, 0) / cluster.length,
    y: (bottom.y0 + bottom.y1) / 2,
  };
}

export interface VisualPlacement {
  pageNumber: number;
  pageLocation: number;
  inkFraction: number;
  anchored: boolean;
}

/**
 * Nađi najbolju praznu lokaciju za vizual na zadnjoj (ili zadanoj) stranici.
 * Ako je zadano ime potpisnika i pronađeno je na stranici, bira se prazna
 * ćelija najbliža potpisnom bloku (ispod/uz ime); inače najniža prazna ćelija,
 * desna prije lijeve. null = nema prazne ćelije ili analiza nije moguća →
 * pozivatelj neka koristi 0/0 (prazna stranica).
 */
export async function pickVisualPlacement(pdfPath: string, page?: number, signerName?: string): Promise<VisualPlacement | null> {
  try {
    const target = page ?? (await pageCount(pdfPath));
    const { stdout } = await run(
      'pdftoppm',
      ['-f', String(target), '-l', String(target), '-r', String(RENDER_DPI), '-gray', pdfPath],
      { encoding: 'buffer', maxBuffer: 64 * 1024 * 1024 },
    );
    const img = parsePgm(stdout as unknown as Buffer);
    const scale = RENDER_DPI / 72; // px po pt
    const pageWpt = img.width / scale;
    const pageHpt = img.height / scale;
    const pad = PADDING_PT;

    const cells = visualGrid(pageWpt, pageHpt).map((c) => ({
      ...c,
      ink: inkFraction(
        img,
        (c.leftPt - pad) * scale,
        (c.topPt - pad) * scale,
        (c.leftPt + VISUAL_W_PT + pad) * scale,
        (c.topPt + VISUAL_H_PT + pad) * scale,
      ),
    }));
    const freeCells = cells.filter((c) => c.ink <= INK_THRESHOLD);
    if (freeCells.length === 0) return null;

    const anchor = signerName ? await findSignerAnchor(pdfPath, target, signerName).catch(() => null) : null;
    if (anchor) {
      // ćelija najbliža potpisnom bloku; ćelije iznad imena su penalizirane
      // (vizual ide ispod/uz potpis, ne iznad njega)
      const scored = freeCells.map((c) => {
        const cx = c.leftPt + VISUAL_W_PT / 2;
        const cy = c.topPt + VISUAL_H_PT / 2;
        const above = cy < anchor.y - 20 ? 10_000 : 0;
        return { c, score: Math.hypot(cx - anchor.x, cy - anchor.y) + above };
      });
      scored.sort((a, b) => a.score - b.score);
      const best = scored[0]!.c;
      return { pageNumber: target, pageLocation: best.relPos, inkFraction: best.ink, anchored: true };
    }

    // bez sidra: najniži red prvi, unutar reda desno prije lijevog
    freeCells.sort((a, b) => b.relPos - a.relPos);
    const free = freeCells[0]!;
    return { pageNumber: target, pageLocation: free.relPos, inkFraction: free.ink, anchored: false };
  } catch {
    return null; // poppler nedostupan ili nečitljiv PDF → sigurni fallback
  }
}
