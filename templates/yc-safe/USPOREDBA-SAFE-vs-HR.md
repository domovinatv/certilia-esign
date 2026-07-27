# YC SAFE vs. hrvatski konvertibilni zajam

Zašto `../vlastiti/ugovor-o-zajmu-konvertibilni.docx` **nije** prijevod SAFE-a i ne može biti.
Pravne reference po hrvatskim propisima provjerene 27.07.2026. na pročišćenim tekstovima (zakon.hr);
detalji u `../vlastiti/PRAVNA-ANALIZA.md`.

## Tri strukturne razlike

### 1. SAFE nije dug — naš instrument jest

SAFE nema dospijeće, nema kamatu i **nema pravo na povrat novca**. Ulagač koji potpiše SAFE ne može
tražiti svoj novac natrag ni u jednom scenariju osim Liquidity/Dissolution Eventa. Naš ugovor ima
fiksni dan dospijeća i obvezu povrata glavnice.

Posljedica: naš instrument je **povoljniji za ulagača** nego SAFE — ima i zaštitu prema dolje
(povrat) i izloženost prema gore (opcija). SAFE ima samo drugo.

### 2. SAFE konvertira automatski — kod nas to nije moguće

SAFE, čl. 1(a): na prvom zatvaranju Equity Financinga instrument se **automatski** pretvara u
dionice. Nitko ništa ne izjavljuje ni ne glasa.

U hrvatskom d.o.o.-u svako izdavanje novog poslovnog udjela je povećanje temeljnog kapitala i traži:

| korak | ZTD |
|---|---|
| odluka članova o izmjeni društvenog ugovora | čl. 457. st. 1. |
| većina od 3/4 danih glasova | čl. 455. st. 1. |
| izričito navođenje uloga u pravima + rok unosa | čl. 457. st. 7. |
| izjava o preuzimanju udjela — javnobilježnički akt ili solemnizirana isprava | čl. 457. st. 5. |
| prijava registru s ispravom o ulaganju | čl. 458. st. 2. |
| potpun tekst društvenog ugovora u obliku javnobilježničke isprave | čl. 456. |

Ništa se od toga ne može ugovorno preskočiti. Zato naši čl. 7.–11. (obveze činjenja, obveza
glasovanja člana, obavijest o rundi, ugovorna kazna, fikcija ispunjenja uvjeta po ZOO čl. 297. st. 4.)
postoje isključivo da **simuliraju ono što SAFE-u američko pravo daje besplatno**. SAFE je kratak jer
mu ne treba prisila; naš je dug jer mu treba.

### 3. SAFE je post-money — naš je pre-money

Post-money SAFE fiksira postotak u trenutku potpisa: `udio = Purchase Amount / Post-Money Valuation Cap`.
Razvodnjavanje od runde koja slijedi pada na osnivače, ne na ulagača.

Naš ugovor konvertira po **pre-money** vrijednosti prije/istodobno s rundom, pa ulagača runda
razvodni kao i svakog drugog člana. Kod 7.000 EUR i capa od 20 M: post-money SAFE = trajnih 0,035 %;
naš model = 0,0377 % prije runde → ~0,0343 % nakon runde od 2 M.

Dodatno ograničenje kojega SAFE nema: **ZTD čl. 390. st. 3.** traži da temeljni kapital i poslovni
udjeli glase na pune iznose eura, pa se ciljani postotak može pogoditi samo do granularnosti od
1 EUR nominale. Kod malog temeljnog kapitala to mjerljivo odmakne stvarni postotak od ciljanog.

## Što SAFE ima, a mi (ne) možemo imati

| SAFE | naš predložak | izvedivo u RH? |
|---|---|---|
| automatska konverzija u rundi | opcija + obveze + ugovorna kazna | ne — ovo je maksimum |
| post-money zaključan postotak | pre-money | da, formulom u čl. 6. |
| Liquidity Event: veće od uloga ili as-converted | **dodano** (čl. 10.) | da |
| Dissolution Event payout prije članova | djelomično — tražbina ionako ide prije članova | da |
| liquidation preference, non-participating preferred | nema | ne bez pretvorbe u d.d. |
| MFN klauzula | nema | da, lako |
| pro rata pravo (side letter) | nema | da, lako |
| Unissued Option Pool u kapitalizaciji | nema — ESOP ne postoji u d.o.o. | samo phantom/bonus shema |
| ograničenje prijenosa instrumenta | **dodano** (čl. 13., ZOO čl. 80. st. 2.) | da |

## Zašto je u SAD-u / UK-u / na Caymanu jednostavnije

Odobreni (authorized) kapital + izdavanje dionica odlukom uprave, bez javnog bilježnika i bez suda.
Cap table je privatna evidencija, ne javni registar. Preferred stock s likvidacijskom preferencijom
je standardni proizvod, option pool normalna stavka kapitalizacije.

U RH je svaka promjena vlasništva javnobilježnički i sudsko-registarski događaj — traje tjednima i
košta po transakciji. Zato startupi na VC putu rade flip u Delaware ili na Cayman; YC zato i ima
Cayman, Singapore i kanadsku inačicu, ali EU/hrvatske nema.

**Za flip je važno:** konvertibilni zajam je flip-safe jer ulagač drži tražbinu, a ne udio —
tražbina se preuzima na razini nove holding strukture bez izlaska iz sudskog registra.

## Stock options u RH

U d.o.o.-u nema ESOP-a u američkom smislu. Praktično: **phantom stock / bonus vezan uz izlaz**
(ugovorno, bez udjela — najčešće), stvarni udjeli zaposlenicima (svaki ulaz/izlaz kod bilježnika,
neupotrebljivo iznad par ljudi), ili pretvorba u d.d. (skupo, ali daje dionice i opcije). Ozbiljan
ESOP u praksi ide preko holdinga u Delawareu ili UK-u.
