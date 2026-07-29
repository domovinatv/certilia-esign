# Kamate na pozajmice u RH — sve kombinacije strana (stanje: srpanj 2026.)

> Javna, proširena verzija s mermaid dijagramima, NN poveznicama i razradom mitova
> (obveza kamate p2p, „kreditna institucija", povrat unutar godine):
> **[`clanci/pozajmice-i-kamate-u-rh.md`](../../clanci/pozajmice-i-kamate-u-rh.md)**.
> Ovaj dokument je interna kratka referenca uz ugovor ITalk ↔ PALKOM.

Provjereno **29.07.2026.** na zakon.hr (ZOO, ZPDoh), Poreznoj upravi i TEB-ovim pregledima stopa.
Dopuna uz `PRAVNA-ANALIZA.md` (koja pokriva konkretan slučaj d.o.o. ↔ d.o.o., ITalk ↔ PALKOM).
**Ovo nije pravni savjet.**

## Dva odvojena pitanja koja se stalno miješaju

1. **Civilnopravno (ZOO)** — smije li kamata biti 0 %? **Da, uvijek.** Kamata na zajam postoji samo
   ako je ugovorena (ZOO čl. 500. st. 1.). Jedina zamka: u **trgovačkim ugovorima** (obje strane
   trgovci, ugovor u obavljanju djelatnosti) kamata se duguje i kad nije ugovorena (čl. 500. st. 2.)
   — pa se mora **izričito isključiti**, kao u čl. 3. st. 1. našeg predloška. „Minimalna zakonska
   kamata" kao civilna obveza **ne postoji**; postoje samo porezne posljedice.
2. **Porezno** — hoće li Porezna kod 0 % nekome pripisati prihod/dohodak? Ovisi o kombinaciji strana,
   po dva režima:
   - **ZPD (porez na dobit)**: povezane osobe → propisana stopa **2,65 % za 2026.** (Odluka, NN
     150/25; čl. 14. st. 3. ZPD). Za **dva tuzemna rezidenta** vrijedi samo ako jedna strana ima
     povlašteni porezni položaj — preneseni gubitak, oslobođenje ili nižu stopu (čl. 13. st. 5.).
     Umjesto propisane stope može se dokazivati tržišna kamata transfernim cijenama (čl. 14. st. 4.).
   - **ZPDoh (porez na dohodak)**: „povoljnija kamata" fizičkoj osobi → prag **2 % godišnje**
     (čl. 21. st. 3.): razlika do 2 % je radniku **plaća u naravi**, a članu društva **izuzimanje**
     (dohodak od kapitala, **36 %**).

## Brojke za 2026. (drugo polugodište)

| Stopa | Iznos | Osnova |
|---|---:|---|
| Povezane osobe (porez na dobit) | **2,65 %** | ZPD čl. 14. st. 3.; Odluka NN 150/25 |
| Prag „povoljnije kamate" fizičkim osobama | **2 %** | ZPDoh čl. 21. st. 3. |
| Referentna stopa (ESB, 1.7.2026.) | 2,40 % | ZOO čl. 29. st. 8. |
| Zatezna — trgovački ugovori i osobe javnog prava | **10,40 %** | ZOO čl. 29. st. 2. (ref. + 8 p.b.) |
| Zatezna — ostali odnosi (uklj. zajmove fizičkim osobama) | **5,40 %** | ZOO čl. 29. st. 2. (ref. + 3 p.b.) |
| **Najviša** ugovorna — barem jedna strana nije trgovac | **8,10 %** | ZOO čl. 26. st. 1. (zatezna + ½) |
| **Najviša** ugovorna — trgovci međusobno | **18,20 %** | ZOO čl. 26. st. 2. (zatezna + ¾) |
| Kamata ugovorena, ali stopa nije određena | 1,35 % / 5,20 % | ZOO čl. 26. st. 3. (¼ odn. ½ zatezne) |
| Porez na primljene kamate fizičke osobe | **12 %** | ZPDoh čl. 65., čl. 70. (dohodak od kapitala) |
| Izuzimanja (skrivene isplate dobiti) | **36 %** | ZPDoh čl. 66., čl. 70. |

Propisana stopa za povezane osobe mijenja se **svake godine** (odluka ministra financija, objava u NN
krajem godine), a zatezne se preračunavaju **1.1. i 1.7.** prema stopi ESB-a.

## Tablica kombinacija (zajmodavac → zajmoprimac)

| # | Zajmodavac → Zajmoprimac | 0 % dopušten bez poreznih posljedica? | Što se dogodi kod 0 % | Minimalna kamata da nema posljedica |
|---|---|---|---|---|
| 1 | Fizička → fizička (obje privatno) | **DA** | Ništa. Oprez samo kod **oprosta duga** → darovanje (porez na darovanja 4 %, uz oslobođenja za bliske srodnike) | — |
| 2 | Fizička → pravna osoba (nepovezane) | **DA** | Ništa | — |
| 3 | Fizička **vlasnik/član** → svoje društvo | **DA** | Ništa — imputacije nema kad je fizička osoba *davatelj* pogodnosti | — (ako se kamata ugovori: društvu je priznat rashod **max 2,65 %**; kod udjela ≥ 25 % i zajma > 4× udjela u kapitalu kamata uopće nije priznata — ZPD čl. 8.) |
| 4 | Radnik → svoj poslodavac | **DA** | Ništa | — |
| 5 | Pravna → **radniku** | **NE** | Razlika do 2 % = **plaća u naravi** → doprinosi + porez na dohodak kao na plaću (JOPPD) | **2 %** (ZPDoh čl. 21. st. 3.) |
| 6 | Pravna → **vlasniku/članu** (fizičkoj) | **NE** | Razlika do 2 % = **izuzimanje** → dohodak od kapitala **36 %**; bez pisanog ugovora, roka i stvarnog vraćanja rizik da se **cijeli iznos** prekvalificira u izuzimanje | **2 %** |
| 7 | Pravna → fizičkoj **nepovezanoj** (nije ni radnik ni član) | **DA** (formalno) | Nema propisane imputacije; oprez: opetovano kreditiranje potrošača kao djelatnost traži odobrenje (ZPK/HANFA) — beskamatni krediti bez naknada su **izvan** ZPK-a | — |
| 8 | Pravna → pravna, **nepovezane** | **DA** — naš slučaj ITalk ↔ PALKOM | Ništa; obavezno izričito isključiti ZOO čl. 500. st. 2. | — |
| 9 | Pravna → pravna, **povezane, obje tuzemne, obje „uredne"** (nema gubitka, oslobođenja, niže stope) | **DA** | Transferna pravila se ne primjenjuju (ZPD čl. 13. st. 5.) — ali status provjeriti **svake godine** (gubitak jedne strane aktivira pravilo) | — |
| 10 | Pravna → pravna, **povezane + jedna u povlaštenom položaju** ili **jedna nerezident** | **NE** | Zajmodavcu se imputira prihod od kamate (min 2,65 %), zajmoprimcu se rashod priznaje max do 2,65 % → korekcije porezne osnovice | **2,65 %** (ili dokazana tržišna po TP studiji, čl. 14. st. 4.) |
| 11 | Obrt / OPG **„dohodaš"** (bilo koja strana) | Kao fizička osoba | Nema ZPD imputacije; primljene kamate su poslovni primitak (zajam iz sredstava obrta) odnosno dohodak od kapitala 12 % (privatno) | — (prema svojim radnicima vrijedi prag 2 %) |
| 12 | Obrt / OPG **„dobitaš"** (obveznik poreza na dobit) | Kao pravna osoba | Vrijede redci 8–10 (povezane osobe, 2,65 %) i redci 5–6 prema radnicima/članovima obitelji | 2,65 % ako povezan + uvjet iz čl. 13. st. 5. |

Dopunska pravila neovisna o kombinaciji:

- **Ako se kamata ugovara**, gornje granice iz ZOO čl. 26. (8,10 % / 18,20 %) su prisilne — na više
  ugovoreno primjenjuje se najviša dopuštena (čl. 26. st. 4.). Obrtnik u obavljanju djelatnosti
  računa se kao trgovac.
- **Kamata fizičkoj osobi** (kad je zajmodavac fizička): isplatitelj pravna osoba obračunava porez po
  odbitku 12 % (dohodak od kapitala) kroz JOPPD; između dvije fizičke osobe primatelj kamate sam
  prijavljuje.
- **Kamata nerezidentu pravnoj osobi**: porez po odbitku (u pravilu 15 %), osim ako ugovor o
  izbjegavanju dvostrukog oporezivanja ili EU direktiva određuju drukčije.
- **Primanje pozajmica od šireg kruga fizičkih osoba** može zapeti o zabranu primanja depozita od
  javnosti (Zakon o kreditnim institucijama) — pojedinačne pozajmice člana ili poslovnog partnera
  nisu problem.

## Primjena na naš ugovor (ITalk ↔ PALKOM)

Redak 8: nepovezana društva, 0 % uredno — uz uvjete koje ugovor već ispunjava (čl. 3. st. 1.
isključuje ZOO čl. 500. st. 2., čl. 3. st. 2. sadrži izjavu o nepovezanosti). Ako bi se ikad pokazalo
da su strane povezane **i** jedna ima povlašteni porezni položaj → redak 10: kamata min 2,65 %.

## Izvori

- [TEB — Kamate prema poreznim propisima u 2026.](https://www.teb.hr/novosti/2025/kamate-prema-poreznim-propisima-u-2026-godini/)
- [TEB — Zatezne i ugovorne kamate od 1.7.2026. do 31.12.2026.](https://www.teb.hr/novosti/2026/zatezne-i-ugovorne-kamate-od-172026-do-31122026/)
- [ZOO — pročišćeni tekst, zakon.hr](https://www.zakon.hr/z/75/Zakon-o-obveznim-odnosima) (čl. 26., 29., 499.–508.)
- [ZPDoh — pročišćeni tekst, zakon.hr](https://www.zakon.hr/z/85/zakon-o-porezu-na-dohodak) (čl. 21., 65., 66., 70.)
- [Porezna uprava — dohodak od kapitala po osnovi izuzimanja](https://porezna-uprava.gov.hr/hr/dohodak-od-kapitala-po-osnovi-izuzimanja-imovine-i-koristenja-usluga/4652)
- Odluka o objavi kamatne stope na zajmove između povezanih osoba za 2026. (NN 150/25) — 2,65 %
