#!/usr/bin/env bash
# HTML inačicu predloška (koju generira build-*.py, isti sadržaj kao DOCX)
# pretvara u PDF za pregled — placeholderi ostaju vidljivi.
#
# Za pravi pipeline (popunjena polja → PDF → potpis) koristi LibreOffice nad
# popunjenim DOCX-om: soffice --headless --convert-to pdf <file.docx>
set -euo pipefail

cd "$(dirname "$0")"
HTML="${1:-ugovor-o-zajmu-konvertibilni.html}"
PDF="${HTML%.html}.pdf"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

[ -f "$HTML" ] || { echo "nema $HTML — prvo pokreni build-${HTML%.html}.py" >&2; exit 1; }
[ -x "$CHROME" ] || { echo "nema Chromea na $CHROME" >&2; exit 1; }

"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/$PDF" "file://$PWD/$HTML" 2>/dev/null

echo "$PDF — $(pdfinfo "$PDF" | awk '/^Pages/{print $2" str."}')"
