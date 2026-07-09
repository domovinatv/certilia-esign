# certilia-esign

Lokalni servis + CLI za **kvalificirano digitalno potpisivanje PDF dokumenata** putem
[AKD Certilia eSign (ePotpis)](https://developer.certilia.com) API-ja.

Implementirano prema službenoj specifikaciji: *„ePotpis — Tehnička specifikacija za
integraciju pružatelja e-Usluga", v4.0.13*
([PDF](https://www.certilia.com/external/ePotpis-Tehni%C4%8Dka_specifikacija_za_integraciju_4.0.pdf),
dostupan i na developer portalu pod eSign → Available documents).

## Može li 100% bez interakcije korisnika?

**Ne** — i to nije ograničenje API-ja nego eIDAS uredbe: kvalificirani potpis zahtijeva
*isključivu kontrolu potpisnika* (sole control), pa svaki potpis mora autorizirati osoba.
Realne opcije, od najmanje do najviše interakcije:

| Način | Interakcija | Napomena |
|---|---|---|
| `--mobile` (mobileSign) | **1 tap + PIN/biometrija u Certilia mobilnoj app** | Bez browsera; CLI čeka potvrdu. Zahtijeva udaljeni (mobile ID) certifikat. |
| `--mobile` + više PDF-ova | 1 potvrda za **N dokumenata** | Batch je moguć isključivo udaljenim certifikatima. |
| Browser tok | Otvoriš `signUrl`, biraš karticu/udaljeni potpis | Radi i s eOI / KID karticom + čitačem. |
| Potpuna automatizacija | — | Jedino elektronički **pečat na automatiziranoj infrastrukturi** (poseban ugovor s AKD-om); eSign API i za pečat traži potvrdu osobe. |

Dakle: najbliže „100% CLI" je `npm run sign -- dokument.pdf --mobile` → notifikacija na
mobitel → jedan tap → potpisani PDF se sam pojavi pored originala.

## Arhitektura / tok

```
CLI ──POST /api/sign──▶ lokalni server
                          │ 1. POST  esign.certilia.com/api/v2/epotpis        (systemId/serviceId/documentId → token + verificationCode)
                          │ 2. POST  api.certilia.com/pades/v2                (PreSign: PDF → hash, Bearer ADES token)
                          │ 3. PATCH esign.certilia.com/api/v2/epotpis/hash   (hash + mobileSign→push u Certilia app)
                          ▼
              korisnik potpiše (mobitel ili browser: esign.certilia.com/epotpis/?token=…)
                          │
AKD ──POST {PUBLIC_BASE_URL}/esign/signed-pdf──▶ lokalni server (signedHash + userCertificate)
                          │ 4. PATCH api.certilia.com/pades/v2                (PostSign: ugradnja potpisa, razina b/t/lt/lta)
                          ▼
                   <original>-potpisan.pdf
```

Endpointi koje server izlaže (AKD ih zove izvana → treba **javni HTTPS URL**):

| Endpoint | Uloga (polje u eSign aplikaciji) |
|---|---|
| `POST /esign/signed-pdf` | **Sign PDF URL** — AKD ovamo šalje potpisani hash |
| `GET /esign/success` | **Success URL** — redirect korisnika nakon potpisa |
| `GET /esign/error` | **Error URL** |
| `GET /esign/docs/<verificationCode>.pdf` | **Base download URL** — dohvat kod verifikacije (opcionalno) |
| `POST /api/sign`, `GET /api/jobs/:id` | lokalni API za CLI |

## Što ti je potrebno (jednokratno)

1. **Certilia certifikat za potpisivanje** — udaljeni/mobile ID certifikat (za `--mobile`
   i batch), ili eOI / KID kartica s čitačem (browser tok).
2. **Javni HTTPS URL** do ovog servera — najjednostavnije Cloudflare tunel:
   ```bash
   # brzi (privremeni) tunel:
   cloudflared tunnel --url http://localhost:3355
   # ispiše npr. https://nesto-random.trycloudflare.com  → to je PUBLIC_BASE_URL
   ```
   Za trajni setup koristi named tunnel na vlastitoj domeni (URL se ne mijenja, pa ga ne
   moraš ažurirati u eSign aplikaciji).
3. **eSign aplikacija na developer portalu** — [developer.certilia.com/services/esign/create](https://developer.certilia.com/services/esign/create):

   | Polje forme | Vrijednost |
   |---|---|
   | Your application owner name | npr. `iTalk d.o.o.` |
   | Your application name | npr. `certilia-esign CLI` |
   | Document type | npr. `Ponuda` (naziv tipa dokumenta koji potpisuješ) |
   | eSign package | trial paket |
   | Base URL | `https://<tvoj-tunel>` |
   | Sign PDF URL | `https://<tvoj-tunel>/esign/signed-pdf` |
   | Sign XML URL | (prazno) |
   | Success URL | `https://<tvoj-tunel>/esign/success` |
   | Error URL | `https://<tvoj-tunel>/esign/error` |
   | Base download URL | `https://<tvoj-tunel>/esign/docs/` |

   Nakon kreiranja subscription ti daje **System ID / Service ID / Document ID**, a gumb
   **„ADES WEB API"** generira Bearer token za PAdES API.
4. `.env` — kopiraj `.env.example` i popuni ID-eve, ADES token, svoj OIB.
5. (Opcionalno) **AKD TSA pristup** za razine potpisa `t`/`lt`/`lta` (vremenski žig) —
   zahtjev na certilia.com. Razina `b` (default) radi bez toga.

## Pokretanje

```bash
npm install
npm run server            # terminal 1 — lokalni servis (port 3355)
cloudflared tunnel --url http://localhost:3355   # terminal 2 (ili named tunnel)

# potpis jednog PDF-a, potvrda u Certilia mobilnoj aplikaciji:
npm run sign -- /putanja/do/dokument.pdf --mobile

# npr. ponuda iz drugog repoa:
npm run sign -- ~/git/stepanic/ms-toptal-projects/nabava/ponude/dgu-eckp-odrzavanje/ponuda-dgu-eckp-odrzavanje.pdf --mobile

# potpis kroz browser (kartica ili udaljeni potpis):
npm run sign -- dokument.pdf

# više dokumenata jednom potvrdom (samo udaljeni certifikat):
npm run sign -- a.pdf b.pdf c.pdf --mobile

# vizualni element potpisa u PDF-u — pozicija se određuje AUTOMATSKI:
# 1) pdftotext -bbox traži ime potpisnika (CERTILIA_NAME_SURNAME) na stranici
#    i vizual ide u praznu ćeliju najbližu potpisnom bloku (nikad iznad njega)
# 2) ako imena nema: najniža prazna ćelija (desna prije lijeve)
# 3) prazne ćelije se određuju renderiranjem stranice (poppler) po Certilia
#    mreži lokacija (Prilog A); ako prazne ćelije nema, ePotpis dodaje novu
#    praznu stranicu — vizual NIKAD ne prekriva sadržaj
npm run sign -- dokument.pdf --mobile --visual

# ručna pozicija (override auto): --page N + --location 0-12
# (A4 portrait mreža 2x6: 1,2 vrh ... 11 dolje lijevo, 12 dolje desno)
npm run sign -- dokument.pdf --mobile --visual --page 4 --location 5

# + vremenski žig (traži TSA pristup):
npm run sign -- dokument.pdf --mobile --visual --level t
```

Uz svaki potpisani PDF sprema se i **`*.dokaz.json`** — verifikacijski kod, token
transakcije, razina potpisa, pozicija vizuala, link za online provjeru i rezultat
lokalne `pdfsig` validacije.

> Za automatsko pozicioniranje vizuala i lokalnu validaciju potreban je poppler
> (`brew install poppler` — daje `pdftoppm`, `pdfinfo`, `pdfsig`). Bez njega sve
> radi, samo vizual ide na novu praznu stranicu (0/0), a validacija se preskače.

Rezultat: `dokument-potpisan.pdf` + `dokument-potpisan.dokaz.json` pored originala
(+ kopija u `data/signed/<verificationCode>.pdf` za dohvat kod verifikacije).
Provjera potpisa: Adobe Reader ili <https://esign.certilia.com/provjera>.

## Napomene iz specifikacije

- Hash mora biti 64-znakovni hex (SHA-256) — računa ga AKD-ov PAdES API, ne mi.
- Payload limit po pozivu ~35 MB; PDF-ove drži kompaktnima.
- Ako PDF nema potpisa, komponenta dodaje praznu A4 stranicu na kraj (ili
  `ADD_AUTO_ON_NO_SIGNATURES` opcijom stranicu u formatu zadnje stranice) — tamo ide vizual.
- `--visual` uz potpis šalje `personNaturalData` (PIN = **OIB**), uz pečat `personLegalData`
  (VAT = OIB tvrtke); podaci se provjeravaju protiv certifikata potpisnika.
- Token transakcije ima ograničen rok (`expireAt` u odgovoru) — potpiši dok ne istekne.
- TEST okolina: `esign.test.certilia.com` / `api.test.certilia.com` (`CERTILIA_ENV=test`).

## Ograničenja / TODO

- Jobovi su u memoriji — restart servera gubi transakcije u tijeku (potpisani PDF-ovi na disku ostaju).
- XAdES (XML) potpisivanje nije implementirano (endpoint `api.certilia.com/xades/v1` je analogan PAdES-u).
- `LOCAL_API_KEY` env postavi ako je tunel javno izložen (štiti `POST /api/sign` headerom `X-Api-Key`).
