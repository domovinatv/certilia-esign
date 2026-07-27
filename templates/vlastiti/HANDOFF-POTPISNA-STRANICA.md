# Potpisna stranica — što je napravljeno i zašto (riješeno 27.07.2026.)

Zadatak iz ovog handoffa je odrađen; dokument je zadržan jer objašnjava **zašto** je raspored ovakav.
Sažetak je u `templates/README.md`, odjeljak „Potpisna stranica".

## Kako izgleda sada

Svaki potpisnik je jedna ćelija mreže vizuala (248 × 122 pt), a oko nje klasično potpisno mjesto:

```
Za Zajmodavca:
FIRMA B d.o.o.
                          ← ćelija 5/6/9: ostaje prazna, tu sjeda vizual
──────────────────────────
Ivan Ivić
kvalificirani elektronički potpis
```

Zaglavlje (uloga + tvrtka) sidreno je na **donji** rub, podnožje (crta + ime) na **gornji**, pa dugačak
naziv tvrtke ili ime raste od ćelije prema van i nikad ne uđe u rezervirani prostor. Raspored:
ćelija 5 = Zajmodavac, 6 = Zajmoprimac, 9 = Član; 10 ostaje slobodna kao pričuva za automatski odabir.

## Što je bio pravi uzrok neurednog izgleda

Sve tri stavke iz starog popisa nedostataka („lijevi stupac se ne može poravnati", „vertikalni odmak
~6 pt", „neujednačeni razmaci") imale su isti korijen:

1. **Chrome pri ispisu smanjuje cijeli dokument ako sadržaj prelazi marginu.** Stari raspored izlazio
   je iz margine od 25 mm negativnim `left`, pa je Chrome sve stranice skalirao faktorom **≈ 0,9**
   (mjereno: tekst je umjesto na 70,9 pt počinjao na 75,9 pt) — i k tome odrezao dio koji viri preko
   margine. Zato ništa nije sjedalo na mrežu.
2. **`body` ima zadanu marginu 8 px = 6 pt.** To je bio onaj „vertikalni odmak od ~6 pt".

Rješenje: potpisna stranica dobila je **vlastitu marginu od 10 mm** — istu koju ima mreža vizuala —
kroz imenovanu stranicu:

```css
@page potpisna { size: A4; margin: 10mm; }
.sigpage { page: potpisna; }
html, body { margin: 0; }
```

Time je mreža ujedno i raspored stranice: ćelija = stupac teksta, bez ijednog preljeva. Koordinate
ćelija više se ne hardkodiraju nego ih računa `grid_cell()` (prijepis `GetVisualGrid` iz Priloga A,
isti algoritam kao `visualGrid()` u `src/visual.ts`).

Nuspojava koju treba znati: bez skaliranja od 0,9 tekst je u punoj veličini, pa ugovor ima **9 stranica**
umjesto dotadašnjih 8. Potpisna stranica je i dalje zadnja.

## Zamke koje i dalje vrijede

- **Ne slagati rezervirani prostor po toku teksta** — mreža ima marginu 10 mm, tekst 25 mm; poklopiti
  se mogu samo ako se stranici promijeni margina.
- **Prag tinte:** `src/visual.ts` ćeliju smatra zauzetom iznad 0,4 % piksela tamnijih od 225, i to u
  pravokutniku ćelije **proširenom za 4 pt**. U ćeliji zato nema ničega, a crta ispod imena je 7 pt
  ispod ćelije — izvan mjerenog pojasa, pa smije biti tamna (`0.75pt solid #333`).
- **Ne dirati tekst ugovora ni numeraciju članaka** (pravna analiza referira na brojeve članaka), broj
  polja (38) ni imena placeholdera.

## Provjera nakon svake izmjene (bez trošenja potpisa)

```bash
python3 templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py   # dodaj --mreza za okvire ćelija
./templates/vlastiti/render-pdf.sh
python3 templates/vlastiti/provjeri-potpisnu-stranicu.py templates/vlastiti/ugovor-o-zajmu-konvertibilni.pdf
pdftoppm -f 9 -l 9 -r 80 -png templates/vlastiti/ugovor-o-zajmu-konvertibilni.pdf /tmp/sig && open /tmp/sig-*.png
```

`provjeri-potpisnu-stranicu.py` ponavlja algoritam iz `src/visual.ts`: ispisuje tintu po ćeliji, popis
slobodnih ćelija i riječi koje upadaju u rezervirane ćelije. Trenutačno stanje: ćelije 5, 6 i 9 imaju
tintu 0,0000, a slobodne su 5, 6, 9, 10 i 12.

Potpisivanje radi provjere rasporeda nije potrebno — svako traži potvrdu dodirom u Certilia aplikaciji.
Kad raspored zadovolji:

```bash
export CERTILIA_ESIGN_SERVER=https://esign.domovina.ai API_KEY=$(cat .api-key-esign-domovina-ai)
npm run sign -- ugovori/<naziv>.pdf --mobile --visual --page 9 --location 6
npm run sign -- ugovori/<naziv>-potpisan.pdf --mobile --visual --page 9 --location 9
```
