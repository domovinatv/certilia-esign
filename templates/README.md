# Predlošci ugovora

Dvije stvari žive ovdje: offline kopija AKD-ovog kataloga predložaka (referenca) i vlastiti
predlošci koji se generiraju iz skripte i potpisuju kroz `npm run sign`.

```
templates/
├── certilia-katalog/   12 DOCX-eva iz Certilia Doc kataloga + catalog.json (metapodaci, polja)
├── yc-safe/            YC standardni dokumenti (referenca) + usporedba sa SAFE-om
├── tokenizacija/       pravna analiza tokenizacije d.o.o. (DE/AT/HR) i EU Inc. 28. režima
└── vlastiti/           vlastiti predlošci — generator, DOCX, PDF pregled, pravna analiza
```

## `certilia-katalog/` — referenca

Skinuto 27.07.2026. iz [Certilia Doc](https://doc.certilia.com/templates) (beta). Detalji, sintaksa
placeholdera i pravna napomena AKD-a: `certilia-katalog/README.md`.

**Same `.docx` datoteke nisu u gitu** (`.gitignore`) — uz njih ne dolazi licenca koja bi dopuštala
redistribuciju, a ovaj repo je javan. U gitu su `catalog.json` (imena, opisi, kategorije, verzije i
puni popis polja za svih 12) i README, što je dovoljno za rad na vlastitim predlošcima. Kopiju
DOCX-eva obnavljaš snippetom iz `certilia-katalog/README.md` (konzola prijavljene kartice na
doc.certilia.com).

## `vlastiti/` — naši predlošci

| datoteka | što je |
|---|---|
| `build-ugovor-o-zajmu-konvertibilni.py` | generator (bez ovisnosti); isti sadržaj emitira u DOCX i HTML |
| `ugovor-o-zajmu-konvertibilni.docx` | predložak za potpisivanje, 17 članaka, 38 polja `{snake_case}` |
| `ugovor-o-zajmu-konvertibilni.html` | isti tekst u HTML-u — izvor za PDF pregled |
| `ugovor-o-zajmu-konvertibilni.fields.json` | opis i primjer vrijednosti za svako polje |
| `ugovor-o-zajmu-konvertibilni.pdf` | PDF za pregled (placeholderi vidljivi) |
| `render-pdf.sh` | HTML → PDF (headless Chrome) |
| `fill-ugovor.py` | popunjava predložak stvarnim podacima → DOCX + HTML + PDF + kontrolni izračun |
| `ugovor-podaci.primjer.json` | predložak ulaznog JSON-a sa svih 38 polja |
| `HANDOFF.md` | vođeni postupak izrade pravog primjerka (oneliner za prazan chat) |
| `provjeri-potpisnu-stranicu.py` | provjera da rezervirane ćelije mreže vizuala ostaju prazne |
| `HANDOFF-POTPISNA-STRANICA.md` | zapis o doradi potpisne stranice (riješeno 27.07.2026.) |
| `PRAVNA-ANALIZA.md` | provjera po ZOO/ZTD/ZPD s referencama na članke i NN |

Izrada pravog primjerka — izlaz ide u **gitignoran `ugovori/`** jer sadrži stvarne podatke firmi:

```bash
cp templates/vlastiti/ugovor-podaci.primjer.json ugovori/zajam-2026-08.json
$EDITOR ugovori/zajam-2026-08.json
python3 templates/vlastiti/fill-ugovor.py ugovori/zajam-2026-08.json
```

Skripta odbija generirati dokument ako neko polje nedostaje i uz dokument ispisuje kontrolni izračun
konverzije (nominala novog udjela, stvarni postotak, agio), s upozorenjem kad zaokruživanje na puni
euro odmakne stvarni postotak više od 5 % od ciljanog.

**Format** prati uobičajeni raspored hrvatskih ugovora i Narodnih novina: Times New Roman 12 pt,
naslov članka verzalom i centriran, ispod njega centrirano „Članak N.", tijelo obostrano poravnato,
margine 25 mm. Naslovi imaju `keepNext` (DOCX) odnosno `break-after: avoid` (HTML) da ne ostanu sami
na dnu stranice.

### Potpisna stranica

Potpisna stranica je zasebna i složena je **na mreži vizuala iz Priloga A**: svaki potpisnik je jedna
ćelija te mreže (248 × 122 pt ≈ 87 × 43 mm) koja ostaje prazna da vizual kvalificiranog potpisa sjedne
u nju. Iznad ćelije stoji uloga i tvrtka, ispod nje crta i ime potpisnika — dakle klasično potpisno
mjesto, samo što je „prostor za rukopis" ovdje točno ćelija mreže. Raspored: **5 = Zajmodavac,
6 = Zajmoprimac, 9 = Član**, a 10 ostaje slobodna kao pričuva. `src/visual.ts` bira slobodnu ćeliju
najbližu imenu potpisnika i nikad iznad njega.

Tri zamke koje su ovdje riješene i koje treba znati prije bilo kakve izmjene rasporeda:

- **Mreža ima marginu 10 mm, tekst 25 mm.** Ako se rezervirani prostor slaže po toku teksta, nikad se
  ne poklopi s ćelijom i ePotpis smjesti vizual preko imena potpisnika (tako je ispalo na prvom
  stvarnom potpisivanju 27.07.2026.). Zato potpisna stranica ima **vlastitu marginu od 10 mm**
  (`@page potpisna` + `page: potpisna`), pa se ćelija i stupac teksta poklapaju do na desetinku točke.
- **Preljev preko margine skalira cijeli dokument.** Dok je raspored pokušavao izaći iz margine od
  25 mm negativnim `left`, Chrome je pri ispisu smanjio **sve stranice** faktorom ≈ 0,9 (shrink to
  fit) — pa se ništa nije poklapalo s mrežom, a k tome je i sadržaj bio odrezan na rubu margine.
  Isto vrijedi za zadanu marginu `body` od 8 px: pomicala je cijeli raspored za 6 pt, pa je sada
  `html, body { margin: 0 }`.
- **Sve tamnije od 225 računa se kao sadržaj.** `src/visual.ts` ćeliju smatra zauzetom iznad 0,4 %
  tamnih piksela u pravokutniku ćelije **proširenom za 4 pt**. Iscrtkani okvir `#bbb` s natpisom
  „prostor za vizual" padao je u tu granicu, pa je automatika izbjegavala upravo rezervirane ćelije.
  Sada u ćeliji nema ničega, a crta ispod imena namjerno je 7 pt ispod ćelije — izvan mjerenog pojasa,
  pa smije biti tamna.

Provjera nakon svake izmjene rasporeda (ponavlja algoritam iz `src/visual.ts`, bez potpisivanja):

```bash
python3 templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py --mreza  # okviri ćelija radi pregleda
./templates/vlastiti/render-pdf.sh
python3 templates/vlastiti/provjeri-potpisnu-stranicu.py templates/vlastiti/ugovor-o-zajmu-konvertibilni.pdf
```

Skripta ispisuje tintu po ćeliji, popis slobodnih ćelija i riječi koje upadaju u rezervirane ćelije;
izlazni kod je 1 ako 5, 6 ili 9 nisu čiste. Zadnji korak je pogledati stranicu očima
(`pdftoppm -f 9 -l 9 -r 80 -png`).

Promjena teksta ugovora ide **u generatoru**, ne u DOCX-u:

```bash
python3 templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py   # regenerira DOCX + fields.json
./templates/vlastiti/render-pdf.sh                                 # regenerira PDF za pregled
```

## Nalazi iz istraživanja (27.07.2026.)

- **AKD/Certilia nemaju službeni open source.** Nema GitHub orga; javno postoje samo community
  repozitoriji (Nix pakiranje zatvorenog middlewarea) i naši (`stepanic/flutter_certilia`,
  `domovinatv/certilia-esign`). Integracijski materijal AKD isporučuje kao PDF specifikacije.
- **API Certilia Doc-a nije javan proizvod.** `GET /api/templates`, `GET /api/templates/{id}/download`,
  `GET /api/templates/library-disclaimer` rade samo iz prijavljene sesije (cookie); bez nje 401. Nema
  API ključeva (`/api/api-keys`, `/api/tokens` → 404), nema OpenAPI/Swaggera, i ništa od toga nije u
  javnoj ePotpis specifikaciji v4.0.13. Koristivo za jednokratni dohvat, neupotrebljivo za produkciju
  bez dogovora s AKD-om.
- Backend ima rate limit — kod dohvata više predložaka ostavi ~0,5 s između zahtjeva, inače vraća
  `{"error":"Previše zahtjeva, pokušajte za nekoliko minuta."}` (61 B umjesto DOCX-a).
- Chrome blokira višestruka automatska preuzimanja s iste stranice; treba jednom ručno dopustiti
  preuzimanje za `doc.certilia.com`.
- **LibreOffice nije instaliran** na razvojnom Macu (`soffice` u `/opt/homebrew/bin` je slomljen shim),
  pa `render-pdf.sh` PDF radi headless Chromeom iz HTML inačice koju generator ionako emitira. Za
  pravi pipeline popunjeni-DOCX → PDF treba `brew install --cask libreoffice`.

## Sljedeći koraci

- [x] Prvi stvarni primjerak izrađen i potpisan (27.07.2026.) — postupak je u `vlastiti/HANDOFF.md`.
- [ ] Predložak dati bilježniku/odvjetniku na pregled (čl. 6.–11.) — konverzija ionako ide preko
      bilježnika, pa je to prilika.
- [x] Doraditi izgled potpisne stranice (27.07.2026.) — vlastita margina od 10 mm, prostor za vizual
      iznad crte s imenom, provjera skriptom `vlastiti/provjeri-potpisnu-stranicu.py`.
- [ ] Razmotriti dopune po uzoru na SAFE koje su u RH izvedive: post-money formula, MFN klauzula,
      pro rata pravo (vidi `../yc-safe/USPOREDBA-SAFE-vs-HR.md`).
- [ ] `src/generate.ts`: docxtemplater (delimiteri `{` `}`) → LibreOffice → PDF → `npm run sign --
      --mobile --visual`, da je put od popunjenih polja do potpisanog PDF-a jedna naredba.
