#!/usr/bin/env bash
# Markdown članak → PDF s renderiranim mermaid dijagramima.
#
#   ./render-pdf.sh [pozajmice-i-kamate-u-rh.md]
#
# Tijek: pandoc (GFM → HTML fragment) → omot s tiskovnim CSS-om i mermaidom
# (CDN, ESM) → Chrome headless ispis u PDF. Mermaid se izvršava u Chromeu, pa
# je za dijagrame potreban pristup mreži; --virtual-time-budget drži stranicu
# živom dok se SVG-ovi ne iscrtaju.
set -euo pipefail
cd "$(dirname "$0")"

MD="${1:-pozajmice-i-kamate-u-rh.md}"
BASE="${MD%.md}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

[ -f "$MD" ] || { echo "nema $MD" >&2; exit 1; }
command -v pandoc >/dev/null || { echo "treba pandoc (brew install pandoc)" >&2; exit 1; }
[ -x "$CHROME" ] || { echo "nema Chromea na $CHROME" >&2; exit 1; }

# Pandoc mermaid fence pretvara u <pre class="mermaid"><code>…</code></pre>;
# mermaid od <code> omota javlja "Syntax error in text", pa ga skidamo
# (provjereno: bez omota, uz HTML entitete, svi dijagrami se iscrtaju).
BODY="$(pandoc -f gfm -t html5 "$MD" | python3 -c '
import re, sys
t = sys.stdin.read()
t = re.sub(r"(<pre class=\"mermaid\">)<code>(.*?)</code>(</pre>)",
           lambda m: m.group(1) + m.group(2) + m.group(3), t, flags=re.S)
sys.stdout.write(t)')"

cat > "$BASE.html" <<HTML
<!doctype html>
<html lang="hr"><head><meta charset="utf-8">
<title>Pozajmice i kamate u RH</title>
<style>
@page { size: A4; margin: 18mm 16mm; }
html { font-size: 10.5pt; }
body { font-family: Georgia, "Times New Roman", serif; line-height: 1.45;
       color: #1a1a1a; margin: 0; max-width: 100%; }
h1 { font-size: 1.7rem; line-height: 1.25; margin: 0 0 .8rem; }
h2 { font-size: 1.25rem; margin: 1.6rem 0 .5rem; border-bottom: 1.5px solid #1a1a1a;
     padding-bottom: .15rem; break-after: avoid; }
h3 { font-size: 1.05rem; margin: 1.1rem 0 .4rem; break-after: avoid; }
p { margin: 0 0 .55rem; text-align: justify; }
a { color: #0b4a8b; text-decoration: none; }
blockquote { margin: .8rem 0; padding: .5rem .9rem; border-left: 3px solid #0b4a8b;
             background: #f2f6fb; font-size: .95rem; }
blockquote p { text-align: left; }
table { border-collapse: collapse; width: 100%; margin: .6rem 0 1rem; font-size: .88rem; }
th, td { border: .5pt solid #999; padding: .28rem .45rem; vertical-align: top; text-align: left; }
th { background: #eef1f5; }
tr { break-inside: avoid; }
code { font-family: "SF Mono", Menlo, monospace; font-size: .85em; background: #f4f4f4;
       padding: 0 .2em; }
pre.mermaid, .mermaid-done { display: flex; justify-content: center; background: none;
              break-inside: avoid; margin: .9rem 0; }
.mermaid-done .mermaid { width: 100%; display: flex; justify-content: center; }
pre.mermaid svg, .mermaid-done svg { max-width: 100%; height: auto; }
ol, ul { margin: 0 0 .6rem; padding-left: 1.3rem; }
li { margin-bottom: .25rem; }
hr { border: 0; border-top: .5pt solid #999; margin: 1.2rem 0; }
</style>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({ startOnLoad: true, theme: "neutral",
                       flowchart: { htmlLabels: true, useMaxWidth: true } });
</script>
</head><body>
$BODY
</body></html>
HTML

# Mermaid pod --virtual-time-budget staje nakon 2 dijagrama na istoj stranici
# (izmjereno; budget ne pomaže), a pojedinačno svaki uredno završi. Zato se
# svaki dijagram renderira u zasebnoj stranici, gotov SVG se ugradi u statični
# HTML bez skripti, i tek se on ispisuje u PDF.
python3 - "$BASE" "$CHROME" <<'PY'
import html as H, pathlib, re, subprocess, sys, tempfile

base, chrome = sys.argv[1], sys.argv[2]
doc = pathlib.Path(f'{base}.html').read_text(encoding='utf8')
blocks = re.findall(r'<pre class="mermaid">.*?</pre>', doc, re.S)
INIT = ('<script type="module">import m from '
        '"https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";'
        'm.initialize({startOnLoad:true, theme:"neutral",'
        'flowchart:{htmlLabels:true, useMaxWidth:true}});</script>')

with tempfile.TemporaryDirectory() as td:
    for i, block in enumerate(blocks):
        page = pathlib.Path(td) / f'd{i}.html'
        page.write_text(f'<!doctype html><html><body>{block}{INIT}</body></html>',
                        encoding='utf8')
        dom = subprocess.run([chrome, '--headless=new', '--disable-gpu',
                              '--virtual-time-budget=20000', '--dump-dom',
                              f'file://{page}'],
                             capture_output=True, text=True, check=True).stdout
        m = re.search(r'<div class="mermaid"[^>]*>.*?</div>\s*(?=<script|</body)', dom, re.S) \
            or re.search(r'<svg.*?</svg>', dom, re.S)
        if not m or 'viewBox' not in m.group(0):
            sys.exit(f'dijagram {i + 1} se nije iscrtao')
        doc = doc.replace(block, f'<div class="mermaid-done">{m.group(0)}</div>', 1)

doc = doc.replace('<script type="module">', '<script type="module" data-skip>', 1)
doc = re.sub(r'<script type="module" data-skip>.*?</script>', '', doc, flags=re.S)
pathlib.Path(f'{base}.static.html').write_text(doc, encoding='utf8')
print(f'  ugrađeno dijagrama: {len(blocks)}')
PY

"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/$BASE.pdf" "file://$PWD/$BASE.static.html" 2>/dev/null
rm "$BASE.static.html"

echo "$BASE.pdf — $(pdfinfo "$BASE.pdf" | awk '/^Pages/{print $2" str."}')"
