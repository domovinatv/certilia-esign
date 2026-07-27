# Predlošci ugovora

Dvije stvari žive ovdje: offline kopija AKD-ovog kataloga predložaka (referenca) i vlastiti
predlošci koji se generiraju iz skripte i potpisuju kroz `npm run sign`.

```
templates/
├── certilia-katalog/   12 DOCX-eva iz Certilia Doc kataloga + catalog.json (metapodaci, polja)
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
| `ugovor-o-zajmu-konvertibilni.docx` | predložak za potpisivanje, 15 članaka, 38 polja `{snake_case}` |
| `ugovor-o-zajmu-konvertibilni.html` | isti tekst u HTML-u — izvor za PDF pregled |
| `ugovor-o-zajmu-konvertibilni.fields.json` | opis i primjer vrijednosti za svako polje |
| `ugovor-o-zajmu-konvertibilni.pdf` | PDF za pregled (placeholderi vidljivi) |
| `render-pdf.sh` | HTML → PDF (headless Chrome) |
| `fill-ugovor.py` | popunjava predložak stvarnim podacima → DOCX + HTML + PDF + kontrolni izračun |
| `ugovor-podaci.primjer.json` | predložak ulaznog JSON-a sa svih 38 polja |
| `HANDOFF.md` | vođeni postupak izrade pravog primjerka (oneliner za prazan chat) |
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

**Potpisna stranica** je zasebna (page break) i ispod svakog potpisnika ima rezerviranu praznu ćeliju
za vizual kvalificiranog potpisa (≈ 87 × 43 mm, jedna ćelija Certilia mreže iz Priloga A). U DOCX-u
je taj prostor prazan, u HTML/PDF pregledu se iscrtava iscrtkani okvir da se vidi gdje vizual sjeda.
`src/visual.ts` bira slobodnu ćeliju najbližu imenu potpisnika i nikad iznad njega.

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

- [ ] Upisati stvarni **temeljni kapital firme A** u `signer2_temeljni_kapital` — o njemu ovisi izračun
      nominale novog poslovnog udjela (vidi tablicu zaokruživanja u `PRAVNA-ANALIZA.md`).
- [ ] Popuniti podatke firmi A i B te direktora koji potpisuju, generirati primjerak za potpis —
      vođeni postupak je u `vlastiti/HANDOFF.md`.
- [ ] Predložak dati bilježniku/odvjetniku na pregled prije potpisa (čl. 6.–10.).
- [ ] `src/generate.ts`: docxtemplater (delimiteri `{` `}`) → LibreOffice → PDF → `npm run sign --
      --mobile --visual`, da je put od popunjenih polja do potpisanog PDF-a jedna naredba.
