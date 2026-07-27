# Tokenizacija vlasništva u d.o.o. — Njemačka, Austrija, Hrvatska

Istraženo **27.07.2026.** Polazište: [tokenize.it](https://tokenize.it/en/fundraise) — je li isti model
moguć za hrvatski d.o.o.? Sve pravne tvrdnje provjerene na tekstovima propisa (zakon.hr,
gesetze-im-internet.de, RIS, EUR-Lex); gdje izvor nije primaran ili je nalaz neizvjestan, to je
izrijekom označeno.

**Kratki zaključak:** model se u RH **ne može preslikati**. Blokira ga ZTD čl. 412. st. 3. (javnobilježnička
forma i za samu *obvezu* prijenosa udjela) i ZTD čl. 385. st. 1. (poslovni udjeli se ne mogu izraziti u
vrijednosnim papirima). Približiti mu se može isključivo **ugovorno**, uz bilježnika koji se vraća pri
svakoj konverziji.

---

## 1. Kako tokenize.it stvarno radi (Njemačka)

Uobičajena predodžba — „njemački zakon dopušta pool virtualnih dionica unutar firme" — **nije točna.**
Ne postoji poseban zakon. Konstrukcija je ova:

**Token nosi Genussrecht** — participacijsko pravo na dobit, dividendu, izlaz i likvidacijski ostatak,
uz ograničena informacijska prava. **Bez glasačkih prava, bez statusa člana, bez upisa u
Handelsregister.** Genussrechte su čisto obveznopravni i **bezformalni**, pa
[§ 15 GmbHG](https://www.gesetze-im-internet.de/gmbhg/__15.html) (javnobilježnička forma za prijenos
udjela *i* za obvezu prijenosa) uopće ne dolazi u primjenu. Model ga ne zaobilazi — ostaje izvan njega.

**Nosivi element je Auslobung,** [§ 657 BGB](https://www.gesetze-im-internet.de/bgb/__657.html): javno
obećanje nagrade obvezuje **bez ugovora i bez prihvata**, „auch wenn dieser nicht mit Rücksicht auf die
Auslobung gehandelt hat". Društvo javno obeća Genussrecht *onome tko drži token*, pa pravo putuje s
tokenom i sekundarni prijenos ne traži cesiju između prodavatelja i kupca. Tek to čini tokene stvarno
zamjenjivima. **Bilježnik ne sudjeluje ni pri izdavanju ni pri prijenosu.**

### Što se nije potvrdilo

**Kvartalna/godišnja skupna konverzija imatelja u prave članove preko bilježnika nije javno
dokumentirana.** Postoji mogućnost da imatelj *zatraži* konverziju i put opcija iznad praga koji
određuje društvo; frekvencija, mehanika i raspodjela troškova nigdje nisu objavljene. Sekundarni izvori
spominju kvartalne prozore — tretirati kao marketing dok se ne potvrdi.

Kad se konverzija provede, vrijede obična pravila: forma po § 15 Abs. 3, a popis članova
(Gesellschafterliste) potpisuje i podnosi **bilježnik**, ne uprava (§ 40 Abs. 2 GmbHG); prema
§ 16 Abs. 1 članom se prema društvu smatra samo osoba iz podnesenog popisa.

**Otvoreni pravni rizik:** je li Auslobung koji obećava *udio* sam po sebi aktivira § 15 Abs. 4 GmbHG,
u doktrini je sporno — a to je upravo put-noga konstrukcije.

### Regulatorni okvir (DE)

| Propis | Nalaz |
|---|---|
| **eWpG** | Ne primjenjuje se. § 1 taksativno: obveznice na donositelja, dionice na ime, dionice na donositelja u središnjem registru (dionice dodane Zukunftsfinanzierungsgesetzom, 15.12.2023.). GmbH udjeli i Genussrechte su izvan. |
| **Prospekt** | Njemački prag od 8 M **ukinut** (§ 3 WpPG „weggefallen"). Vrijedi izuzeće do **12 M EUR / 12 mj.** po čl. 3(2)(b) Uredbe 2017/1129 (Listing Act, Uredba 2024/2809), uz obvezni **WIB** koji BaFin mora odobriti (§ 4 WpPG). *Oprez: BaFin-ove stranice još navode 8 M.* |
| **VermAnlG** | Supsidijaran; ne primjenjuje se ako je instrument Wertpapier sui generis. |
| **MiCA** | Ne primjenjuje se — čl. 2(4)(a) Uredbe 2023/1114 isključuje financijske instrumente; ide MiFID II. |
| **KWG** | Nema licence: Genussrecht koji sudjeluje u tekućim gubicima nije „unbedingt rückzahlbar" (BaFin Merkblatt Einlagengeschäft). |

### Tehnički sloj

Ethereum Mainnet + Gnosis Chain; plaćanje u EURe/EUROC/USDC. **Obični ERC-20** (ne ERC-1400, ne
ERC-3643): `ERC20Permit` + `Snapshot` + `Pausable` + `AccessControl` + UUPS, uz vlastiti sloj
ograničenja. Repo: <https://github.com/corpus-io/tokenize.it-smart-contracts> (AGPL-3.0). KYC preko
`AllowList.sol` — bitmaska atributa po adresi; prijenos prolazi ako obje strane zadovolje `requirements`.

**Dvije koncentracije rizika:** jedna jedina AllowList instanca u vlasništvu platforme služi sve
izdavatelje, a `BURNER_ROLE` može spaliti tokene s **bilo koje** adrese („planned for legal purposes and
error recovery").

---

## 2. Austrija — FlexCo ne rješava problem

- [§ 76 Abs. 2 GmbHG (AT)](https://www.ris.bka.gv.at/eli/rgbl/1906/58/P76/NOR40233217) i dalje traži
  **Notariatsakt**. FlexKapGG ga nije dirao.
- **§ 12 FlexKapGG** (BGBl. I 179/2023, na snazi 1.1.2024.) ne uvodi bezformalni prijenos, nego
  **alternativu**: ispravu koju sastavi bilježnik **ili odvjetnik**, uz provjeru identiteta, poučavanje
  obiju strana i pohranu u arhiv. Vratar i naknada ostaju; vrijedi samo za FlexKapG, ne za obični GmbH.
- **Unternehmenswert-Anteile (§§ 9–10 FlexKapGG)** — najbliži analogon: bez glasačkih prava, ograničeni
  na iznos koji **ne doseže 25 %** temeljnog kapitala, prijenos u **pisanom obliku** bez bilježnika,
  vode se u Anteilsbuchu (ne pojedinačno u Firmenbuchu), uz obvezni tag-along. Ali su i dalje
  **registarski** — token ih može samo zrcaliti, nikad konstituirati ni prenijeti naslov.
- Austrija **nema** ekvivalent eWpG-a. *Ispravak česte tvrdnje: Austrija nije izdavala državne papire na
  blockchainu — OeKB je 2018. samo hashirao podatke aukcija na lanac kao sloj ovjere.*
- *Neprovjereno:* Auslobung + Genussrecht konstrukcija **vjerojatno** je replikabilna za austrijski GmbH
  (austrijska Genussrechte su također bezformalna), ali nije nađen nijedan austrijski primarni izvor ni
  mišljenje prakse koji to potvrđuje. Ne oslanjati se bez austrijskog odvjetnika.

---

## 3. Hrvatska — što zakon dopušta

### Forma (ZTD) — utvrđeno

> **ZTD čl. 412. st. 3.:** „Za prijenos poslovnog udjela potreban je ugovor sklopljen u obliku
> javnobilježničkog akta ili privatne isprave koju potvrdi javni bilježnik ili sudska odluka koja
> zamjenjuje takav ugovor. **Takav ugovor potreban je i za preuzimanje obveze da će se prenijeti
> poslovni udio.**"

Druga rečenica ubija tokenize.it mehaniku u korijenu: **sam token je obveza prijenosa.** Punomoć traži
javnobilježnički ovjeren potpis (st. 7.), zalog istu formu (st. 6.).

> **ZTD čl. 385. st. 1.:** „Poslovni udjeli se ne mogu izraziti u vrijednosnim papirima."

Udio u d.o.o.-u ne može se sekuritizirati. Točka.

Povećanje kapitala i ulazak novog člana: odluka o izmjeni društvenog ugovora u javnobilježničkom obliku
(čl. 454. st. 1.), **3/4 danih glasova** (čl. 455. st. 1.), potpun tekst društvenog ugovora u
javnobilježničkoj ispravi (čl. 456. st. 1.), **izjava o preuzimanju udjela u obliku javnobilježničkog
akta ili solemnizirane isprave** (čl. 457. st. 5.), prijava registru (čl. 458. st. 2. t. 1.).

**Novost koja je korisna:** **ZTD čl. 458.a** (NN 130/23) uvodi **odobreni kapital** — uprava se može
ovlastiti na povećanje kroz pet godina, do **polovice** postojećeg temeljnog kapitala. To uklanja korak
glasovanja članova, **ali ne i javnobilježničku formu iz čl. 457. st. 5.**

### Rute do prenosivog instrumenta bez bilježnika po transakciji

| Ruta | Ocjena |
|---|---|
| **Ugovorna participacija / phantom equity** | **Izvedivo.** Obveznopravna tražbina na udio u dobiti/izlazu; nema forme po ZTD-u, ustupiva po **ZOO čl. 80. st. 1.** Imatelji nemaju članska prava. *Sivo:* agresivno oponašanje equityja može se prekvalificirati u izvedenicu po **ZTK čl. 3. t. 24(d)** — u RH neispitano. |
| **Tajno društvo** (hrv. termin je *tajno*, ne „tiho") | **ZTD čl. 148.–157.** Ulog ulazi u imovinu poduzetnika, tajni član sudjeluje u dobiti i gubitku, nema pravne osobnosti ni upisa u sudski registar; kopija ugovora ide Poreznoj u 15 dana. **Nema forme.** *Ali:* prijenos ugovornog položaja traži pristanak poduzetnika (**ZOO čl. 127. st. 1.**) — dakle nije slobodno prenosivo. |
| **Konvertibilni zajam** | Zajam je bezforman, ali obveza konverzije je „preuzimanje obveze da će se prenijeti poslovni udio" → čl. 412. st. 3., ili put preko povećanja kapitala po čl. 457. **Odgađa bilježnika, ne uklanja ga.** (Ovo je model iz `../vlastiti/`.) |
| **d.d. umjesto d.o.o.** | **Jedina ruta do stvarno prenosivog equityja.** Minimalni kapital **25.000 EUR** (čl. 162.), nominala po dionici min. 1,00 EUR (čl. 163. st. 2.); prijenos nematerijaliziranih dionica **ne traži bilježnika** (čl. 227. st. 1.). |
| **AIF / SPV drži udio, tokeni su udjeli u fondu** | Pravno koherentno, ali teško: osnivanje AIF-a traži odobrenje HANFA-e (ZAIF čl. 209. st. 1.), upravitelj odobrenje ili barem registraciju kao mali UAIF (čl. 16.). Udjeli u fondu su financijski instrument (ZTK čl. 3. t. 24(c)) → MiFID II. |

### Tržište kapitala

**ZTK čl. 3. t. 87.** definira prenosive vrijednosne papire kao one „prenosive na tržištu kapitala".
Token na d.o.o. udio pada izvan točke (a) zbog ZTD čl. 385. st. 1. — *napomena: to je zaključak iz dvije
odredbe, nijedan propis to ne kaže tim riječima.* Token vezan uz dionice d.d.-a može pasti pod točku (c).

**Prospektni prag: 8.000.000 EUR / 12 mjeseci — ZTK čl. 409. st. 1.** Između **4 M i 8 M** obvezan je
*informacijski dokument* na hrvatskom (st. 3.) uz obavijest HANFA-i (st. 2., čl. 427.). **Hrvatska nije
implementirala prag od 12 M** iz Listing Acta — „12.000.000" se u pročišćenom ZTK-u ne pojavljuje.

**Crowdfunding:** Zakon o provedbi Uredbe (EU) 2020/1503, NN 144/2021 (izm. 83/23), čl. 5. st. 1. —
nadležna je HANFA; strop ECSPR-a je **5 M EUR / 12 mj.**

> **Najvažniji otvoreni nalaz.** ECSPR čl. 2(1)(n) poznaje „admitted instruments for crowdfunding
> purposes" — **udjele u društvima s ograničenom odgovornošću** koji nisu podvrgnuti ograničenjima koja
> bi stvarno spriječila prijenos — a čl. 2(2) dopušta nacionalnom regulatoru da ih uključi.
> **Hrvatska ih nije uključila.** Prema ESMA-inoj tablici (ESMA35-42-1305, ažurirano 27.07.2026.), redak
> za Hrvatsku glasi: *„Currently in the process of communicating with the Ministry of Justice regarding
> the inclusion of limited liability companies… "*. Estonija, Španjolska, Italija, Latvija, Nizozemska,
> Rumunjska, Irska i Danska jesu. **Ovo je živa stvar i vrijedi izravan upit HANFA-i.**

### MiCA

**Ne primjenjuje se** na tokene koji predstavljaju equity — čl. 2(4)(a) Uredbe 2023/1114 isključuje
financijske instrumente (definicija preko čl. 3(1)(49) → MiFID II čl. 4(1)(15)). Hrvatski provedbeni
propis: NN 85/2024, čl. 6. — HANFA (glave II, V, VI), HNB (glave III, IV).

### Registri i DLT

**Nisu sve dionice d.d.-a obvezno u SKDD-u.** ZTK čl. 525. st. 4. nabraja tko *mora* (uklj. izdavatelje
s javnom ponudom), st. 7. dodaje uvrštene; **čl. 527. st. 1.** ostalima dopušta izdavanje po ZTD-u,
papirnato ili imobilizirano. Dakle **privatni d.d. bez javne ponude nije obvezan koristiti SKDD** —
malo poznata, korisna činjenica. Prava se prenose upisom (čl. 530. st. 1.).

**Hrvatski ekvivalent eWpG-a ne postoji.** Nema propisa koji blockchain registar stavlja umjesto CSD-a.
ZTK čl. 523. t. 2. i čl. 525. st. 1. spominju „drugi registar propisan posebnim zakonom", ali čl. 525.
st. 3. to zatvara za papire u dosegu CSDR-a, a takav poseban zakon ne postoji. *Kuka je teorijska.*

**DLT Pilot Regime** (Uredba 2022/858) transponiran je u ZTK čl. 684.a (nadležna HANFA). U cijeloj EU
odobreno je **šest** DLT infrastruktura (CSD Prague, 21X, 360X, Axiology, LISE, Securitize Europe).
**U Hrvatskoj nijedna.**

### Bilježnik na daljinu i troškovi

Elektronički javnobilježnički akt moguć je **samo gdje je posebno propisan** (ZJB čl. 52.a st. 1., uz
videokonferenciju po st. 2.). U pravu društava to je propisano **samo za osnivanje** — ZTD čl. 397.a–397.e
(osnivanje na daljinu bez bilježnika, preko portala sudskog registra i eID-a visoke razine) i čl. 397.f
(uz bilježnika videovezom), na snazi od 1.8.2023. **Za prijenos poslovnog udjela ne postoji.**
*To je zaključak iz izostanka ovlašćujuće norme, nije izričita zabrana — ali je sigurno čitanje.* Strani
ulagatelj radi preko **punomoći s ovjerenim potpisom** (ZTD čl. 412. st. 7.), izvedivo u inozemstvu uz
apostille.

Tarifa (Pravilnik o privremenoj javnobilježničkoj tarifi, čl. 40.: 1 bod = 2,00 EUR; solemnizacija 50 %
po čl. 16. st. 1.):

| Vrijednost posla | JB akt | Solemnizacija |
|---|---|---|
| 10.000 EUR | 212 EUR | 106 EUR |
| 100.000 EUR | 590 EUR | 295 EUR |

Uz to PDV 25 % u praksi (*nije u Pravilniku — praksa, neprovjereno*). Sudska pristojba za prijavu je
13,27 EUR, odnosno 6,64 EUR preko e-Tvrtke.

---

## 4. Presuda

**Klon tokenize.it-a na hrvatskom d.o.o.-u ne može se napraviti.** Blokada je dvostruka i nije
zaobilazna ugovorom:

1. **ZTD čl. 412. st. 3.** — javnobilježnička forma potrebna je i za **obvezu** prijenosa udjela, a token
   upravo to jest;
2. **ZTD čl. 385. st. 1.** — udio se ne može izraziti u vrijednosnom papiru.

**Najbliže izvedivo danas:** tokenizirana **ugovorna participacija** u dobiti i izlazu (phantom equity),
slobodno ustupiva po ZOO čl. 80., uz **ovlaštenje za odobreni kapital po ZTD čl. 458.a** držano u
pripravi za povremenu skupnu konverziju zainteresiranih imatelja preko bilježnika. Svaku emisiju držati
**ispod 4 M EUR** da se ostane izvan obveza iz ZTK čl. 409.

**Ako su prava člana potrebna od prvog dana:** pretvorba u **d.d.** (25.000 EUR kapitala), ostati
privatan i bez javne ponude pa vrijedi ZTK čl. 527. i SKDD je neobvezan.

**Za pratiti:** HANFA–Ministarstvo pravosuđa o uključivanju d.o.o. udjela u ECSPR „admitted instruments".
Ako to prođe, slika se bitno mijenja.

---

## Izvori

Njemačka: § 15, § 40, § 16 GmbHG · § 657 BGB · § 1 eWpG · § 3, § 4 WpPG · § 1 VermAnlG · § 1 KWG +
BaFin Merkblatt Einlagengeschäft · Uredba 2017/1129 (izm. 2024/2809) · Uredba 2023/1114 · ESMA
75-453128700-1323 · corpus-io/tokenize.it-smart-contracts.
Austrija: § 76 GmbHG (AT) · FlexKapGG §§ 9, 10, 12, 28 (BGBl. I 179/2023) · DepotG § 1 Abs. 4.
Hrvatska: ZTD čl. 148.–157., 162., 163., 227., 385., 389., 390.a, 397.a–397.f, 412., 454.–458.a ·
ZOO čl. 80., 127. · ZTK čl. 3., 5., 6., 409., 427., 523.–530., 684.a · ZAIF čl. 8., 16., 209. ·
ZJB čl. 52.a · NN 144/2021, NN 85/2024 · Uredba 2020/1503 · Uredba 2022/858 · ESMA35-42-1305.
