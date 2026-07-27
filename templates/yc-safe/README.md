# YC SAFE — referenca

Offline kopija Y Combinatorovih standardnih dokumenata s <https://www.ycombinator.com/documents>,
skinuto **27.07.2026.** Služi kao referenca pri radu na vlastitim predlošcima u `../vlastiti/`.

**Same datoteke nisu u gitu** (`.gitignore`) — isto pravilo kao za `../certilia-katalog/`: repo je
javan, a tuđe predloške ne redistribuiramo. YC ih objavljuje besplatno i mijenja rijetko, pa se
kopija obnavlja skriptom niže. U gitu ostaje ovaj README i `USPOREDBA-SAFE-vs-HR.md` — znanje, ne
binarni sadržaj.

## Što je skinuto

| datoteka | što je |
|---|---|
| `postmoney-safe-valuation-cap-only.docx` | **najkorišteniji** — post-money SAFE s valuation capom, bez diskonta |
| `postmoney-safe-discount-only.docx` | diskont na cijenu runde, bez capa |
| `postmoney-safe-mfn-only.docx` | „uncapped MFN" — bez capa i diskonta, uz pravo na bolje uvjete kasnijih ulagača |
| `pro-rata-side-letter.docx` | zasebno pravo na sudjelovanje u budućim rundama |
| `safe-user-guide.pdf` | YC-jev vodič kroz mehaniku i primjere izračuna |
| `postmoney-safe-valuation-cap-only-cayman.docx` | Cayman inačica |
| `postmoney-safe-valuation-cap-only-singapore.docx` | Singapur inačica |

YC ima i kanadsku inačicu; EU ni hrvatske **nema** — razlog je objašnjen u
`USPOREDBA-SAFE-vs-HR.md`.

## Obnavljanje kopije

URL-ovi sadrže hash sadržaja pa se mijenjaju sa svakom revizijom dokumenta. Popis dohvati sa
stranice, pa preuzmi:

```bash
curl -s https://www.ycombinator.com/documents            # ili WebFetch — stranica je JS-renderirana
curl -sS "<url s hashom>" -o templates/yc-safe/<ime>.docx
```

Tekst DOCX-a bez vanjskih ovisnosti:

```bash
python3 -c "import zipfile,re,html,sys;x=zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode();\
print(html.unescape(re.sub(r'<[^>]+>','',re.sub(r'</w:p>','\n',x))))" templates/yc-safe/postmoney-safe-valuation-cap-only.docx
```

## Napomena

SAFE je pisan za **američku korporaciju** (Delaware C-corp) i pretpostavlja odobreni kapital,
izdavanje dionica odlukom uprave, preferred stock i option pool. Ništa od toga ne postoji u
hrvatskom d.o.o.-u. Ne prevodi SAFE — pročitaj usporedbu i koristi konvertibilni zajam iz
`../vlastiti/`.
