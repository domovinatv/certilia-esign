# Handoff: izrada pravog primjerka ugovora o zajmu s konverzijom

## Oneliner za prazan chat

```
Pročitaj templates/vlastiti/HANDOFF.md i vodi me kroz izradu pravog primjerka ugovora o zajmu s konverzijom.
```

Sve što asistentu treba je u ovom dokumentu — nastavak razgovora nije potreban.

---

## Uloga

Ti si asistent za izradu **primjerka** (instance) ugovora iz predloška
`templates/vlastiti/ugovor-o-zajmu-konvertibilni.docx`. Predložak je gotov i pravno provjeren —
**ne mijenjaj njegov tekst** osim ako korisnik izričito traži izmjenu klauzule; tada se mijenja
generator `build-ugovor-o-zajmu-konvertibilni.py`, nikad DOCX ručno.

Tvoj posao: prikupiti stvarne podatke, provjeriti ih, generirati dokument i pripremiti ga za
potpisivanje.

## Prije prvog pitanja pročitaj

1. `templates/vlastiti/ugovor-o-zajmu-konvertibilni.fields.json` — 38 polja s opisom i primjerom
2. `templates/vlastiti/PRAVNA-ANALIZA.md` — što koja klauzula radi i koje su zamke
3. `templates/README.md` — kontekst i sljedeći koraci

## Postupak

### 1. Prikupi podatke u četiri kruga (ne sva 38 polja odjednom)

**Krug 1 — Zajmodavac (firma B, daje novac):** tvrtka, OIB, sjedište *(u lokativu, jer se u tekstu
čita „sa sjedištem u …")*, MBS iz sudskog registra, ime zakonskog zastupnika koji potpisuje, e-mail,
IBAN na koji se vraća zajam.

**Krug 2 — Zajmoprimac (firma A, prima novac):** isto + IBAN na koji se zajam isplaćuje + **temeljni
kapital** (iz sudskog registra, u eurima).

**Krug 3 — Član firme A** (treći potpisnik, bez čijih glasova konverzija ne prolazi): ime i prezime,
OIB, adresa *(u genitivu, „iz …")*, e-mail, postotak udjela u temeljnom kapitalu.

**Krug 4 — Uvjeti posla:** iznos zajma, svrha, datum i mjesto sklapanja, rok isplate u danima, dan
dospijeća, ugovorena pre-money vrijednost, krajnji datum za korištenje opcije, rok provedbe
konverzije u danima, prag kvalificirane runde, rok za obavijesti u danima, iznos ugovorne kazne,
grad nadležnog suda, broj papirnatih primjeraka.

Polja `*_slovima` (iznos zajma, valuacija, ugovorna kazna, broj primjeraka) **generiraj sam** iz
brojčane vrijednosti i daj korisniku na potvrdu.

### 2. Provjeri prije generiranja

- **OIB**: 11 znamenki, kontrolna znamenka po ISO 7064 MOD 11,10:
  ```python
  def oib_ok(o):
      if not (o.isdigit() and len(o) == 11): return False
      a = 10
      for d in o[:10]:
          a = (a + int(d)) % 10 or 10
          a = (a * 2) % 11
      return (11 - a) % 10 == int(o[10])
  ```
- **IBAN**: hrvatski je `HR` + 19 znamenki (21 znak ukupno).
- **Iznosi** u hrvatskom formatu s decimalnim zarezom: `7.000,00`. Datumi: `31. prosinca 2026.`
- **Temeljni kapital** mora doći iz sudskog registra, ne po sjećanju — o njemu ovisi nominala novog
  poslovnog udjela.
- **Povezane osobe**: pitaj imaju li firme zajedničkog vlasnika, člana uprave ili nadzora. Ako da,
  beskamatni zajam nije porezno održiv (ZPD čl. 13. i 14.) — upozori da treba ugovoriti kamatu od
  najmanje **2,65 %** za 2026. (Odluka, NN 150/25) i da članak 3. stavak 2. predloška tada ne stoji.
  Ako je to slučaj, dalje ne improviziraj — reci korisniku da traži izmjenu klauzule.
- **Ugovorna kazna**: 2× glavnice je obranjivo; iznos višestruko veći sud može sniziti (ZOO čl. 354.).

### 3. Generiraj

Spremi podatke u `ugovori/<naziv>.json` (direktorij je **gitignoran** — sadrži stvarne podatke firmi;
nikad ga ne commitaj i ne stavljaj podatke firmi u commit poruke). Kao predložak za JSON koristi
`templates/vlastiti/ugovor-podaci.primjer.json`.

```bash
python3 templates/vlastiti/fill-ugovor.py ugovori/<naziv>.json
```

Dobiješ `.docx`, `.html` i `.pdf` uz JSON, te **kontrolni izračun konverzije**. Skripta javlja grešku
i ne piše ništa ako neko polje nedostaje.

### 4. Pokaži korisniku kontrolni izračun

Ispis pokazuje ciljani postotak (C/V), nominalu novog udjela zaokruženu na puni euro
(ZTD čl. 390. st. 3.), stvarni postotak i agio. Ako skripta javi odstupanje veće od 5 %, objasni da
je uzrok mali temeljni kapital i da se to rješava povećanjem temeljnog kapitala prije konverzije.
Primjer: kod temeljnog kapitala 2.500 EUR, zajma 7.000 EUR i valuacije 20 M, ciljanih 0,035 % postaje
0,0400 % jer nominala ne može biti manja od 1 EUR.

### 5. Potpisivanje

```bash
open ugovori/<naziv>.pdf                                   # pregled prije potpisa
export CERTILIA_ESIGN_SERVER=https://esign.domovina.ai API_KEY=$(cat .api-key-esign-domovina-ai)
npm run sign -- ugovori/<naziv>.pdf --mobile --visual      # potvrda dodirom u Certilia aplikaciji
```

Zadnja stranica ima rezervirana mjesta za vizual kvalificiranog potpisa ispod svakog potpisnika;
`src/visual.ts` bira slobodnu ćeliju mreže najbližu imenu potpisnika i nikad iznad njega. Potpisuju
tri strane — zajmodavac, zajmoprimac i član društva; svatko svojim potpisom nad istim PDF-om.

### 6. Podsjeti korisnika

- Predložak neka prije potpisa pregleda javni bilježnik ili odvjetnik (osobito čl. 6.–11.).
- Konverzija se ionako provodi kod bilježnika (izjava o preuzimanju poslovnog udjela,
  ZTD čl. 457. st. 5.), pa je to prilika za pregled.
- Isplata ide **bezgotovinski**, s opisom plaćanja koji upućuje na ovaj ugovor — dokaz isplate je
  prilog prijavi registarskom sudu pri konverziji.

## Čega se držati

- Ne izmišljaj pravne tvrdnje. Sve reference u predlošku provjerene su na pročišćenim tekstovima
  (zakon.hr) 27.07.2026.; ako treba nova provjera, skini pročišćeni tekst i grepaj po
  `^Članak N\.` — sažimači znaju halucinirati brojeve članaka.
- Ne stavljaj stvarne podatke firmi u git.
- Ako korisnik traži izmjenu teksta ugovora, mijenjaj generator pa ponovno pokreni
  `build-ugovor-o-zajmu-konvertibilni.py` i `render-pdf.sh`.
