# Handoff: dorada izgleda potpisne stranice i vizuala potpisa

## Oneliner za prazan chat

```
Pročitaj templates/vlastiti/HANDOFF-POTPISNA-STRANICA.md i doradi izgled potpisne stranice ugovora.
```

Sve što treba je u ovom dokumentu.

---

## Zadatak

Potpisna stranica **funkcionira** — vizuali sjedaju u prazno i ne prekrivaju tekst — ali izgleda
neuredno. Cilj je da izgleda kao dokument, ne kao mreža s nalijepljenim karticama. Tekst ugovora
(članci 1.–17.) **ne dirati**; ovo je isključivo raspored zadnje stranice.

## Kontekst: kako sustav radi

Potpisuje se **PDF**, a PDF nastaje iz HTML-a koji emitira generator. Dakle mijenja se generator, nikad
DOCX ili PDF ručno:

```bash
python3 templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py   # DOCX + HTML + fields.json
./templates/vlastiti/render-pdf.sh                                 # PDF pregled
python3 templates/vlastiti/fill-ugovor.py ugovori/<naziv>.json     # primjerak s podacima
```

Potpisna stranica složena je u `signature_block()` u
`templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py`. DOCX grana zadržava tablični raspored (DOCX
se ne potpisuje), HTML grana slaže blokove **apsolutno**.

### Mreža Priloga A — zašto je raspored apsolutan

ePotpis vizual je **248 × 122 pt**, a stranicu dijeli na mrežu s marginom **10 mm** od ruba: A4 portrait
daje 2 stupca × 6 redaka, `pageLocation` 1–12, red po red od vrha (11 = dolje lijevo, 12 = dolje desno).
Koordinate ćelija na A4 (595 × 842 pt), y od vrha:

| ćelija | x | y |
|---|---|---|
| 5 (lijevo) / 6 (desno) | 28,3–276,3 / 318,6–566,6 | 293,6–415,6 |
| 7 / 8 | isto | 426,3–548,3 |
| 9 / 10 | isto | 558,9–680,9 |

Trenutni raspored: **ćelija 5 = Zajmodavac, 6 = Zajmoprimac, 9 = Član**. Konstante su u generatoru
(`GRID_COL`, `GRID_ROW_3`, `GRID_ROW_5`, `PAGE_MARGIN_PT`, `_rel()`).

### Dvije zamke koje su već skupo naučene (27.07.2026.)

1. **Slaganje po tekstualnom toku ne radi.** Tekst ima marginu 25 mm, mreža 10 mm — nikad se ne poklope
   i ePotpis smjesti vizual **preko imena potpisnika**. Zato je HTML apsolutno pozicioniran.
2. **Okvir-podsjetnik ne smije biti tamniji od praga tinte.** `src/visual.ts` ćeliju smatra zauzetom
   iznad **0,4 %** piksela tamnijih od **225**. Iscrtkani okvir `#bbb` s natpisom „prostor za vizual"
   padao je u tu granicu, pa je automatika izbjegavala **upravo rezervirane ćelije**. Sada je okvir
   `#ececec` bez natpisa i izmjerena tinta je 0,0000.

## Poznati nedostaci koje treba riješiti

- **Lijevi stupac se ne može poravnati vodoravno.** Mreža počinje na x = 28,3 pt, a sadržaj stranice
  tek na 70,9 pt (margina 25 mm), pa okvir u lijevom stupcu ne doseže do stvarnog ruba ćelije i vizual
  „strši" ulijevo u odnosu na okvir. Mogućnosti: smanjiti marginu samo na potpisnoj stranici (npr.
  `@page` pravilo ili zaseban HTML kontejner s negativnim marginama), ili priznati odmak i okvir
  namjerno crtati samo kao podnožnu crtu umjesto pravokutnika.
- **Vertikalni odmak od ~6 pt** između zadanog `top` i stvarno renderiranog položaja (kontejner ne
  počinje točno na vrhu sadržaja). Izmjeriti i kompenzirati.
- **Razmaci su neujednačeni:** ime → traka je 70,6 pt gore i 43,1 pt dolje.
- **Estetika:** razmotriti tanku sivu crtu iznad svake trake umjesto pravokutnika, dosljedan razmak,
  i po mogućnosti sva tri potpisnika u istom vizualnom ritmu (sada su dva gore, jedan dolje).

## Obavezna provjera nakon svake izmjene

```bash
# 1. nijedna riječ ne smije upadati u pravokutnike ćelija 5, 6 i 9
pdftotext -f <zadnja> -l <zadnja> -bbox ugovori/<naziv>.pdf - | grep '<word'
# 2. tinta u tim ćelijama mora biti <= 0,004 (algoritam je u src/visual.ts)
pdftoppm -f <zadnja> -l <zadnja> -r 50 -gray ugovori/<naziv>.pdf
# 3. vizualna provjera
pdftoppm -f <zadnja> -l <zadnja> -r 80 -png ugovori/<naziv>.pdf /tmp/sig && open /tmp/sig-*.png
```

Skripte za 1. i 2. lako se napišu u Pythonu bez ovisnosti — mreža se računa po algoritmu iz
`visualGrid()` u `src/visual.ts`.

## Testiranje bez trošenja potpisa

Svako potpisivanje traži potvrdu dodirom u Certilia aplikaciji, pa **ne potpisuj radi provjere
rasporeda**. Render + gornje tri provjere dovoljni su. Tek kad raspored zadovolji:

```bash
export CERTILIA_ESIGN_SERVER=https://esign.domovina.ai API_KEY=$(cat .api-key-esign-domovina-ai)
npm run sign -- ugovori/<naziv>.pdf --mobile --visual --page <zadnja> --location 6
npm run sign -- ugovori/<naziv>-potpisan.pdf --mobile --visual --page <zadnja> --location 9
```

`--page`/`--location` zaobilaze automatiku; bez njih server sam bira ćeliju po imenu potpisnika.

## Što ne dirati

- Tekst ugovora i numeraciju članaka (pravna analiza referira na brojeve članaka).
- Broj polja (38) i imena placeholdera — postojeći primjerci u `ugovori/` moraju i dalje raditi.
- Već potpisane PDF-ove u `ugovori/` i `ugovori/arhiva-stare-verzije/`.

Kontekst zašto stranica izgleda ovako i koje su odluke već donesene: `templates/README.md`, odjeljak o
potpisnoj stranici.
