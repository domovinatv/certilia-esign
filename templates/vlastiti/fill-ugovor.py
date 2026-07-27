#!/usr/bin/env python3
"""Popunjava predložak ugovora stvarnim podacima i radi DOCX + HTML + PDF primjerak.

    python3 templates/vlastiti/fill-ugovor.py ugovori/zajam-2026-08.json

Ulaz je JSON s vrijednostima svih polja iz `ugovor-o-zajmu-konvertibilni.fields.json`
(primjer: `ugovor-podaci.primjer.json`). Izlaz ide u isti direktorij kao ulazni JSON,
pod istim imenom — a taj direktorij (`ugovori/`) je gitignoran jer sadrži stvarne
podatke firmi.

Uz dokument ispisuje i kontrolni izračun konverzije (nominala novog poslovnog udjela,
stvarni postotak, agio) prema članku 6. ugovora i ZTD čl. 390. st. 3.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TPL_DOCX = os.path.join(HERE, 'ugovor-o-zajmu-konvertibilni.docx')
TPL_HTML = os.path.join(HERE, 'ugovor-o-zajmu-konvertibilni.html')
FIELDS = os.path.join(HERE, 'ugovor-o-zajmu-konvertibilni.fields.json')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def num(value):
    """'2.500,00' → 2500.0 (hrvatski format)."""
    return float(re.sub(r'[^0-9,.-]', '', str(value)).replace('.', '').replace(',', '.'))


def eur(value):
    return f'{value:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')


def substitute(text, data):
    missing = set()

    def repl(m):
        key = m.group(1)
        if key not in data:
            missing.add(key)
            return m.group(0)
        return data[key]

    return re.sub(r'\{([a-z0-9_]+)\}', repl, text), missing


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    data_path = os.path.abspath(sys.argv[1])
    data = json.load(open(data_path, encoding='utf8'))
    schema = json.load(open(FIELDS, encoding='utf8'))['fields']

    unknown = sorted(set(data) - set(schema))
    if unknown:
        print(f'upozorenje: polja koja predložak ne poznaje: {", ".join(unknown)}', file=sys.stderr)

    base = os.path.splitext(data_path)[0]
    out_docx, out_html, out_pdf = base + '.docx', base + '.html', base + '.pdf'

    # HTML
    html, missing = substitute(open(TPL_HTML, encoding='utf8').read(), data)
    # DOCX
    zin = zipfile.ZipFile(TPL_DOCX)
    with zipfile.ZipFile(out_docx, 'w', zipfile.ZIP_DEFLATED) as zo:
        for name in zin.namelist():
            blob = zin.read(name)
            if name == 'word/document.xml':
                text, m2 = substitute(blob.decode('utf8'), data)
                missing |= m2
                blob = text.encode('utf8')
            zo.writestr(name, blob)

    if missing:
        os.remove(out_docx)
        sys.exit('nedostaju polja u ulaznom JSON-u:\n  ' + '\n  '.join(
            f'{k} — {schema.get(k, {}).get("opis", "?")}' for k in sorted(missing)))

    open(out_html, 'w', encoding='utf8').write(html)

    if os.path.exists(CHROME):
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={out_pdf}', 'file://' + out_html],
                       check=True, capture_output=True)
    elif shutil.which('soffice'):
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                        '--outdir', os.path.dirname(out_docx), out_docx], check=True)
    else:
        out_pdf = None

    print('Generirano:')
    for f in (out_docx, out_html, out_pdf):
        if f:
            print(f'  {f}  ({os.path.getsize(f)} B)')

    # --- kontrolni izračun konverzije (čl. 6. ugovora) ---
    try:
        C = num(data['iznos_zajma'])
        V = num(data['valuacija_pre_money'])
        K = num(data['signer2_temeljni_kapital'])
    except (KeyError, ValueError):
        return
    P = C / V
    N = max(1, round(K * P / (1 - P)))
    stvarni = N / (K + N)
    print('\nKontrolni izračun konverzije (čl. 6.):')
    print(f'  zajam C                        {eur(C)} EUR')
    print(f'  ugovorena vrijednost V         {eur(V)} EUR')
    print(f'  temeljni kapital K             {eur(K)} EUR')
    print(f'  ciljani postotak P = C/V       {P * 100:.4f} %')
    print(f'  nominala novog udjela N        {N} EUR (zaokruženo na puni euro, ZTD čl. 390. st. 3.)')
    print(f'  stvarni postotak N/(K+N)       {stvarni * 100:.4f} %')
    print(f'  agio u kapitalne rezerve       {eur(C - N)} EUR')
    if abs(stvarni - P) / P > 0.05:
        print('  NAPOMENA: odstupanje od ciljanog postotka veće od 5 % zbog zaokruživanja —')
        print('            razmotri povećanje temeljnog kapitala prije konverzije.')


if __name__ == '__main__':
    main()
