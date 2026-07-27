#!/usr/bin/env bash
# DOCX predložak → PDF za pregled (placeholderi ostaju vidljivi).
# Koristi pandoc za docx→html i headless Chrome za html→pdf, jer LibreOffice
# nije nužno instaliran. Za pravi pipeline (popunjena polja → PDF → potpis)
# koristi LibreOffice: soffice --headless --convert-to pdf <file.docx>
set -euo pipefail

cd "$(dirname "$0")"
DOCX="${1:-ugovor-o-zajmu-konvertibilni.docx}"
PDF="${DOCX%.docx}.pdf"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/style.css" <<'CSS'
@page { size: A4; margin: 20mm 18mm; }
body { font-family: "Calibri","Helvetica Neue",Arial,sans-serif; font-size: 11pt;
       line-height: 1.45; color: #111; text-align: justify; }
p { margin: 0 0 7pt; }
body > p:first-child { text-align: center; font-size: 14pt; margin-bottom: 16pt; }
strong { font-weight: 600; }
table { width: 100%; margin-top: 18pt; }
td { vertical-align: top; width: 50%; padding-right: 12pt; }
CSS

pandoc "$DOCX" -f docx -t html5 -o "$TMP/body.html"
{
  echo '<!doctype html><html lang="hr"><head><meta charset="utf-8">'
  echo '<link rel="stylesheet" href="style.css"></head><body>'
  cat "$TMP/body.html"
  echo '</body></html>'
} > "$TMP/doc.html"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/$PDF" "file://$TMP/doc.html" 2>/dev/null

echo "$PDF — $(pdfinfo "$PDF" | awk '/^Pages/{print $2" str."}')"
