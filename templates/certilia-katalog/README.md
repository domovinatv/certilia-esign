# Certilia Doc — katalog predložaka (offline kopija)

12 DOCX predložaka iz "Kataloga predložaka" u [Certilia Doc](https://doc.certilia.com/templates) (beta),
skinuto **2026-07-27**. Služe kao offline baza za generiranje i pisanje vlastitih predložaka
koji se onda potpisuju kroz `npm run sign` (ePotpis / eSign API).

## Sadržaj

| id | kategorija | predložak | polja | datoteka |
|---:|---|---|---:|---|
| 1 | Radni odnosi | Ugovor o radu na neodređeno vrijeme | 24 | `1-ugovor-o-radu-na-neodredeno-vrijeme.docx` |
| 4 | Radni odnosi | Ugovor o radu na određeno vrijeme | 30 | `4-ugovor-o-radu-na-odredeno-vrijeme.docx` |
| 7 | Radni odnosi | Sporazum o prestanku ugovora o radu | 19 | `7-sporazum-o-prestanku-ugovora-o-radu.docx` |
| 10 | Radni odnosi | Ugovor o stipendiranju | 14 | `10-ugovor-o-stipendiranju.docx` |
| 13 | Nekretnine | Predugovor o kupoprodaji nekretnine (s kaparom) | 32 | `13-predugovor-o-kupoprodaji-nekretnina.docx` |
| 16 | Nekretnine | Ugovor o kupoprodaji nekretnine (1 prodavatelj, 2 kupca) | 30 | `16-ugovor-o-kupoprodaji-nekretnine.docx` |
| 19 | Nekretnine | Ugovor o zakupu poslovnog prostora | 32 | `19-ugovor-o-zakupu-poslovnog-prostora-1.docx` |
| 22 | Nekretnine | Ugovor o zakupu poslovnog prostora (jednostavni) | 29 | `22-ugovor-o-zakupu-poslovnog-prostora-2.docx` |
| 25 | Poslovni ugovori | Ugovor o tajnosti podataka (NDA) | 12 | `25-ugovor-o-tajnosti-podataka.docx` |
| 28 | Poslovni ugovori | Ugovor o poslovnoj suradnji | 18 | `28-ugovor-o-poslovnoj-suradnji-1.docx` |
| 31 | Poslovni ugovori | Ugovor o poslovnoj suradnji (s ugovornom kaznom) | 23 | `31-ugovor-o-poslovnoj-suradnji-2.docx` |
| 34 | Poslovni ugovori | Ugovor o licenci | 21 | `34-ugovor-o-licenci.docx` |

Sve metapodatke (opis, kategorija, verzija, popis polja po predlošku) ima `catalog.json`.

> **Napomena:** same `.docx` datoteke su u `.gitignore` i postoje samo lokalno — repo je javan, a uz
> predloške ne dolazi licenca za redistribuciju (vidi pravnu napomenu na dnu). U gitu su `catalog.json`
> i ovaj README. Ako radiš na čistom klonu, DOCX-eve dohvati snippetom iz odjeljka „Osvježavanje kopije".

## Placeholderi

Sintaksa je **`{ime_polja}`** — jednostruke vitičaste zagrade, tj. docxtemplater default (bez
`{{...}}`). Provjereno na sva 24 XML dijela: nijedan placeholder nije razbijen preko više `<w:r>`
runova, i popis polja iz API-ja se **1:1 poklapa** s onim što stvarno piše u DOCX-u (`only_in_api`
i `only_in_docx` su prazni za svih 12).

Konvencije imenovanja koje AKD koristi:

- `signer1_*`, `signer2_*`, `signer3_*` — strane koje potpisuju
  (`_full_name`, `_oib`, `_address`, `_organization`, `_organization_oib`)
- ostatak je domenski, snake_case, hrvatski: `datum_sklapanja`, `mjesto_sklapanja`,
  `nadlezni_sud_grad`, `broj_primjeraka` + `broj_primjeraka_slovima` (iznosi/brojevi
  koji se u ugovoru pišu i slovima imaju zaseban `_slovima` par)

Generiranje s docxtemplater:

```js
import Docxtemplater from 'docxtemplater'
import PizZip from 'pizzip'
const zip = new PizZip(fs.readFileSync('templates/certilia-katalog/25-ugovor-o-tajnosti-podataka.docx'))
const doc = new Docxtemplater(zip, { delimiters: { start: '{', end: '}' }, paragraphLoop: true, linebreaks: true })
doc.render({ signer1_organization: 'DOMOVINA d.o.o.', signer1_organization_oib: '...', /* ... */ })
fs.writeFileSync('nda.docx', doc.toBuffer())
// dalje: docx → PDF (libreoffice --headless --convert-to pdf) → npm run sign -- nda.pdf --mobile --visual
```

## Odakle je skinuto

Interni API Certilia Doc aplikacije — **nije javno dokumentiran, nema API ključeve, traži prijavljenu
sesiju (cookie), inače 401.** Nije dio javne ePotpis specifikacije v4.0.13 i može se promijeniti bez najave.

```
GET /api/templates                      → JSON popis (account_id: null = library predlošci)
GET /api/templates/{id}/download        → DOCX
GET /api/templates/library-disclaimer   → pravna napomena AKD-a
```

Osvježavanje kopije (iz konzole prijavljene kartice na `doc.certilia.com`, Chrome traži dozvolu za
preuzimanje više datoteka):

```js
const all = await (await fetch('/api/templates')).json()
for (const t of all.filter(t => t.account_id === null)) {
  const b = await (await fetch(`/api/templates/${t.id}/download`)).blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(b); a.download = `${t.id}-${t.file_name}`; a.click()
  await new Promise(r => setTimeout(r, 500))   // ispod rate limita
}
```

## Pravna napomena (AKD, uz katalog)

> AKD d.o.o., OIB: 58843087891, Zagreb, Savska cesta 31 u potpunosti isključuje odgovornost za bilo
> kakvu izravnu ili neizravnu štetu koja korisniku može nastati korištenjem dostupnog sadržaja.
> Sadržaj je isključivo informativnog karaktera te ne predstavlja niti može zamijeniti profesionalnu
> pravnu pomoć. Sukladno članku 313. Kaznenog zakona, svako neovlašteno pružanje pravne pomoći uz
> nagradu predstavlja kazneno djelo. AKD d.o.o. otklanja odgovornost za privremenu neusklađenost
> sadržaja nastalu uslijed zakonodavnih promjena te pridržava pravo na razuman rok za tehničko i
> pravno usklađivanje.

Uz predloške ne dolazi licenca koja bi dopuštala redistribuciju. Kopija je ovdje za internu upotrebu
i kao osnova za vlastite predloške; za objavu ili preprodaju treba suglasnost AKD-a.
