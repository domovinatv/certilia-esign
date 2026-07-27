#!/usr/bin/env python3
"""Generira DOCX predložak 'Ugovor o zajmu s pravom konverzije' u stilu AKD kataloga:
placeholderi {snake_case}, signer1_* / signer2_* / signer3_*.

Bez vanjskih ovisnosti — DOCX se sastavlja kao ZIP s minimalnim OOXML-om.

    python3 templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py

Pravna podloga i rizici: vidi PRAVNA-ANALIZA.md u istom direktoriju.
"""
import json
import os
import zipfile
from xml.sax.saxutils import escape

OUT_DOCX = os.path.join(os.path.dirname(__file__), 'ugovor-o-zajmu-konvertibilni.docx')
OUT_JSON = os.path.join(os.path.dirname(__file__), 'ugovor-o-zajmu-konvertibilni.fields.json')
OUT_HTML = os.path.join(os.path.dirname(__file__), 'ugovor-o-zajmu-konvertibilni.html')

# --- Emiteri -----------------------------------------------------------------
# Svaki blok vraća {'docx': ..., 'html': ...} pa se isti sadržaj emitira u DOCX
# (za potpisivanje) i u HTML (iz kojega render-pdf.sh radi PDF pregled).
# Format prati uobičajeni raspored hrvatskih ugovora i Narodnih novina:
# naslov članka verzalom i centriran, ispod njega centrirano "Članak N.",
# tijelo obostrano poravnato, Times New Roman 12 pt.

def runs(text, bold=False):
    """Tekst → <w:r> elementi; **bold** unutar teksta prebacuje podebljanje."""
    out = []
    for i, part in enumerate(text.split('**')):
        if not part:
            continue
        b = bold != (i % 2 == 1)
        rpr = '<w:rPr><w:b/></w:rPr>' if b else ''
        out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(part)}</w:t></w:r>')
    return ''.join(out)


def runs_html(text, bold=False):
    out = []
    for i, part in enumerate(text.split('**')):
        if not part:
            continue
        b = bold != (i % 2 == 1)
        out.append(f'<strong>{escape(part)}</strong>' if b else escape(part))
    return ''.join(out)


def p(text='', bold=False, align='both', before=0, after=120, indent=0, cls='', keep=False):
    ind = f'<w:ind w:left="{indent}"/>' if indent else ''
    kn = '<w:keepNext/>' if keep else ''   # naslov članka ne smije ostati sam na dnu stranice
    docx = (f'<w:p><w:pPr>{kn}<w:jc w:val="{align}"/>{ind}'
            f'<w:spacing w:before="{before}" w:after="{after}"/></w:pPr>'
            f'{runs(text, bold)}</w:p>')
    css = {'both': 'j', 'center': 'c', 'left': 'l'}[align]
    klass = f'{css} {cls}'.strip()
    style = f' style="margin-left:{indent / 567:.1f}cm"' if indent else ''
    html = f'<p class="{klass}"{style}>{runs_html(text, bold) or "&nbsp;"}</p>'
    return {'docx': docx, 'html': html}


def h(text, before=280, after=120):
    """'Članak 6. — Pravo na konverziju' → centrirani naslov verzalom + centrirani broj članka."""
    if ' — ' in text:
        num, naslov = text.split(' — ', 1)
    else:
        num, naslov = text, ''
    blocks = []
    if naslov:
        blocks.append(p(naslov.upper(), bold=True, align='center', before=before, after=40,
                        cls='naslov', keep=True))
    blocks.append(p(num, bold=True, align='center',
                    before=0 if naslov else before, after=after, cls='clanak', keep=True))
    return {'docx': ''.join(b['docx'] for b in blocks),
            'html': ''.join(b['html'] for b in blocks)}


def title(text):
    docx = (f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="360"/></w:pPr>'
            f'<w:r><w:rPr><w:b/><w:sz w:val="28"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')
    return {'docx': docx, 'html': f'<h1>{escape(text)}</h1>'}


def pagebreak():
    return {'docx': '<w:p><w:r><w:br w:type="page"/></w:r></w:p>',
            'html': '<div class="pagebreak"></div>'}


def visual_space():
    """Prazan prostor za vizual kvalificiranog elektroničkog potpisa.

    Prilog A ePotpis specifikacije: vizual je 248×122 pt (≈ 87×43 mm), a A4 portrait
    je podijeljen na 2 stupca × 6 redaka uz marginu 10 mm. Ovdje se rezervira jedna
    ćelija te mreže ispod svakog potpisnika; src/visual.ts bira slobodnu ćeliju
    najbližu imenu potpisnika i nikad iznad njega.

    U DOCX-u (dokument koji se stvarno potpisuje) prostor je prazan; u HTML/PDF
    pregledu se iscrtava iscrtkani okvir da se vidi gdje vizual sjeda.
    """
    docx = ('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '</w:pPr></w:p>' * 6)
    html = ('<div class="vizual"><span>prostor za vizual kvalificiranog<br>'
            'elektroničkog potpisa (Certilia)</span></div>')
    return {'docx': docx, 'html': html}


def signature_block():
    """Blok potpisa: Zajmodavac lijevo, Zajmoprimac desno, Član u trećem redu,
    a ispod svakog potpisnika rezerviran prostor za Certilia vizual."""
    parties = [
        [('Za Zajmodavca:', '{signer1_organization}', '{signer1_full_name}'),
         ('Za Zajmoprimca:', '{signer2_organization}', '{signer2_full_name}')],
        [('Za Člana:', '', '{signer3_full_name}'), None],
    ]
    rows_docx, rows_html = [], []
    for row in parties:
        tc, td = [], []
        for cell in row:
            if cell is None:
                tc.append('<w:tc><w:tcPr><w:tcW w:w="4600" w:type="dxa"/></w:tcPr>'
                          + p('', after=0)['docx'] + '</w:tc>')
                td.append('<td></td>')
                continue
            label, org, name = cell
            inner = [p(label, bold=True, align='left', after=60)]
            if org:
                inner.append(p(org, align='left', after=300))
            else:
                inner.append(p('', align='left', after=300))
            inner += [p('_______________________________', align='left', after=60),
                      p(name, align='left', after=120),
                      visual_space()]
            tc.append('<w:tc><w:tcPr><w:tcW w:w="4600" w:type="dxa"/></w:tcPr>'
                      + ''.join(b['docx'] for b in inner) + '</w:tc>')
            td.append('<td>' + ''.join(b['html'] for b in inner) + '</td>')
        rows_docx.append(f'<w:tr>{"".join(tc)}</w:tr>')
        rows_html.append(f'<tr>{"".join(td)}</tr>')
    docx = ('<w:tbl><w:tblPr><w:tblW w:w="9200" w:type="dxa"/>'
            '<w:tblLayout w:type="fixed"/></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="4600"/><w:gridCol w:w="4600"/></w:tblGrid>'
            + ''.join(rows_docx) + '</w:tbl>')
    return {'docx': docx, 'html': f'<table class="potpisi">{"".join(rows_html)}</table>'}


# --- Tekst ugovora -----------------------------------------------------------

BODY = []
A = BODY.append

A(title('UGOVOR O ZAJMU S PRAVOM KONVERZIJE U POSLOVNI UDIO'))

A(p('sklopljen u {mjesto_sklapanja}, dana {datum_sklapanja} godine, između:', after=200))

A(p('1. {signer1_organization}, sa sjedištem u {signer1_address}, OIB: {signer1_organization_oib}, '
    'upisano u sudski registar pod MBS: {signer1_mbs}, koje zastupa {signer1_full_name} '
    '(u daljnjem tekstu: **Zajmodavac**), i', after=120))
A(p('2. {signer2_organization}, sa sjedištem u {signer2_address}, OIB: {signer2_organization_oib}, '
    'upisano u sudski registar pod MBS: {signer2_mbs}, koje zastupa {signer2_full_name} '
    '(u daljnjem tekstu: **Zajmoprimac**), te', after=120))
A(p('3. {signer3_full_name}, OIB: {signer3_oib}, iz {signer3_address}, koji je član Zajmoprimca s '
    'poslovnim udjelom od {signer3_udio_postotak}% temeljnog kapitala (u daljnjem tekstu: **Član**), '
    'koji ovaj Ugovor sklapa isključivo radi preuzimanja obveza iz članaka 8. i 10. ovoga Ugovora', after=120))
A(p('(zajedno: **Ugovorne strane**).', after=240))

A(h('Članak 1. — Uvodne odredbe'))
A(p('(1) Zajmodavac i Zajmoprimac trgovci su u smislu propisa Republike Hrvatske te je ovaj Ugovor '
    'trgovački ugovor.'))
A(p('(2) Zajmoprimcu su potrebna sredstva za {svrha_zajma}, a Zajmodavac mu je ta sredstva spreman '
    'pozajmiti pod uvjetima iz ovoga Ugovora, uz pravo da tražbinu po ovom Ugovoru, po vlastitom '
    'izboru, pretvori u poslovni udio u Zajmoprimcu.'))
A(p('(3) Ugovor se sklapa na temelju načela slobode uređivanja obveznih odnosa iz članka 2. Zakona o '
    'obveznim odnosima, a na njega se primjenjuju odredbe članaka 499. do 508. istoga Zakona o '
    'ugovoru o zajmu.'))

A(h('Članak 2. — Predmet Ugovora i isplata zajma'))
A(p('(1) Zajmodavac se obvezuje Zajmoprimcu predati u zajam iznos od {iznos_zajma} EUR '
    '(slovima: {iznos_zajma_slovima}) (u daljnjem tekstu: **Glavnica**), a Zajmoprimac se obvezuje '
    'Glavnicu vratiti pod uvjetima iz ovoga Ugovora ili omogućiti njezino pretvaranje u poslovni udio '
    'sukladno članku 6. ovoga Ugovora.'))
A(p('(2) Zajmodavac će Glavnicu isplatiti bezgotovinski, u roku od {rok_isplate_dana} dana od dana '
    'sklapanja ovoga Ugovora, na transakcijski račun Zajmoprimca IBAN: {signer2_iban}.'))
A(p('(3) Danom isplate smatra se dan odobrenja računa Zajmoprimca. Zajmoprimac na primljenom iznosu '
    'stječe pravo vlasništva (članak 499. stavak 2. Zakona o obveznim odnosima).'))

A(h('Članak 3. — Kamata'))
A(p('(1) Zajam je **beskamatan**. Ugovorne strane izričito isključuju primjenu članka 500. stavka 2. '
    'Zakona o obveznim odnosima, prema kojemu u trgovačkim ugovorima zajmoprimac duguje kamate iako '
    'nisu ugovorene, te suglasno utvrđuju da Zajmoprimac po ovom Ugovoru ne duguje nikakvu ugovornu '
    'kamatu ni naknadu.'))
A(p('(2) Ugovorne strane izjavljuju da nisu povezane osobe u smislu članka 13. stavka 2. Zakona o '
    'porezu na dobit te da beskamatnost zajma predstavlja rezultat njihove slobodne poslovne odluke, '
    'pri čemu je protučinidba Zajmodavcu pravo na konverziju iz članka 6. ovoga Ugovora.'))

A(h('Članak 4. — Rok i način vraćanja'))
A(p('(1) Zajmoprimac se obvezuje Glavnicu vratiti jednokratno, najkasnije do {datum_dospijeca} '
    '(u daljnjem tekstu: **Dan dospijeća**), uplatom na račun Zajmodavca IBAN: {signer1_iban}.'))
A(p('(2) Zajmoprimac ima pravo Glavnicu vratiti i prije Dana dospijeća, u cijelosti ili djelomično, '
    'bez ikakve naknade ili obveze naknade štete, uz pisanu obavijest Zajmodavcu najmanje '
    '{rok_obavijesti_dana} dana unaprijed. Ugovorne strane time izričito odstupaju od članka 507. '
    'Zakona o obveznim odnosima.'))
A(p('(3) Obavijest iz stavka 2. ovoga članka Zajmodavcu daje priliku da prije povrata iskoristi pravo '
    'na konverziju iz članka 6. ovoga Ugovora. Ako Zajmodavac u roku iz stavka 2. ne dostavi Izjavu o '
    'konverziji, Zajmoprimac Glavnicu vraća, a pravo na konverziju u vraćenom dijelu prestaje.'))
A(p('(4) Vraćanjem Glavnice u cijelosti prestaju sve obveze Zajmoprimca i Člana iz ovoga Ugovora, '
    'osim obveze čuvanja povjerljivosti.'))

A(h('Članak 5. — Zakašnjenje'))
A(p('(1) Zakasni li Zajmoprimac s vraćanjem Glavnice, duguje zatezne kamate po stopi određenoj '
    'člankom 29. stavkom 2. Zakona o obveznim odnosima za odnose iz trgovačkih ugovora, od dana '
    'zakašnjenja do isplate.'))
A(p('(2) Zakašnjenje Zajmoprimca ne utječe na pravo Zajmodavca na konverziju iz članka 6. ovoga '
    'Ugovora; to pravo traje do isteka roka iz članka 6. stavka 2., neovisno o dospijeću Glavnice.'))

A(h('Članak 6. — Pravo na konverziju (opcija Zajmodavca)'))
A(p('(1) Zajmodavac ima pravo, ali ne i obvezu, zahtijevati da se njegova tražbina na povrat Glavnice, '
    'u cijelosti ili djelomično, pretvori u poslovni udio u Zajmoprimcu (u daljnjem tekstu: '
    '**Konverzija**). Konverzija se provodi povećanjem temeljnog kapitala Zajmoprimca ulaganjem prava '
    '— unosom tražbine Zajmodavca u društvo, sukladno članku 457. stavku 7. Zakona o trgovačkim '
    'društvima.'))
A(p('(2) Pravo na konverziju Zajmodavac ostvaruje pisanom, neopozivom izjavom upućenom Zajmoprimcu i '
    'Članu (u daljnjem tekstu: **Izjava o konverziji**), i to najkasnije do {rok_opcije_datum}, '
    'odnosno u kraćem roku iz članka 4. stavka 2. ili članka 9. stavka 2. ovoga Ugovora, ovisno o tome '
    'koji rok nastupi prije.'))
A(p('(3) Vrijednost Zajmoprimca za potrebe Konverzije Ugovorne strane sporazumno i unaprijed utvrđuju '
    'u iznosu od {valuacija_pre_money} EUR (slovima: {valuacija_pre_money_slovima}) prije ulaganja '
    '(pre-money vrijednost) (u daljnjem tekstu: **Ugovorena vrijednost**). Ugovorena vrijednost '
    'primjenjuje se neovisno o vrijednosti utvrđenoj u bilo kojoj kasnijoj investicijskoj rundi.'))
A(p('(4) Postotak sudjelovanja Zajmodavca u temeljnom kapitalu Zajmoprimca nakon Konverzije (P) '
    'izračunava se kako slijedi:'))
A(p('P = C / V', bold=True, align='center', after=60))
A(p('gdje je C iznos tražbine koja se konvertira, a V Ugovorena vrijednost.', align='center', after=120))
A(p('(5) Nominalni iznos novog poslovnog udjela (N) koji Zajmodavac preuzima izračunava se prema '
    'formuli N = K × P / (1 − P), gdje je K iznos temeljnog kapitala Zajmoprimca prije povećanja, koji '
    'na dan sklapanja ovoga Ugovora iznosi {signer2_temeljni_kapital} EUR. Dobiveni iznos zaokružuje '
    'se na najbliži puni euro, a ne može biti niži od 1,00 EUR, sve sukladno članku 390. stavku 3. '
    'Zakona o trgovačkim društvima.'))
A(p('(6) Razlika između iznosa tražbine koja se konvertira i nominalnog iznosa novog poslovnog udjela '
    '(C − N) unosi se u kapitalne rezerve Zajmoprimca kao uplata iznad nominalnog iznosa. Zajmodavac '
    'po toj osnovi nema pravo na povrat niti na bilo kakvu naknadu.'))
A(p('(7) Zbog zaokruživanja iz stavka 5. ovoga članka stvarni postotak Zajmodavca može neznatno '
    'odstupati od izračunatog postotka P. Ugovorne strane takvo odstupanje prihvaćaju i ono ne '
    'predstavlja povredu ovoga Ugovora.'))
A(p('(8) Ako Zajmodavac ne dostavi Izjavu o konverziji u roku iz stavka 2. ovoga članka, pravo na '
    'konverziju prestaje, a Zajmoprimac Glavnicu vraća sukladno članku 4. ovoga Ugovora.'))

A(h('Članak 7. — Provedba konverzije'))
A(p('(1) U roku od {rok_provedbe_dana} dana od primitka Izjave o konverziji Zajmoprimac je dužan '
    'poduzeti sve radnje potrebne za provedbu Konverzije, a osobito:'))
A(p('a) sazvati skupštinu i donijeti odluku o povećanju temeljnog kapitala izmjenom društvenog '
    'ugovora (članak 457. stavak 1. Zakona o trgovačkim društvima), u kojoj se izričito navodi da se '
    'kapital povećava ulaganjem prava — unosom tražbine Zajmodavca po ovom Ugovoru — te se određuje '
    'rok unosa (članak 457. stavak 7. istoga Zakona);', indent=340))
A(p('b) u odluci o povećanju isključiti pravo prvenstva postojećih članova društva na preuzimanje '
    'novih poslovnih udjela (članak 457. stavak 4. Zakona o trgovačkim društvima);', indent=340))
A(p('c) omogućiti Zajmodavcu davanje izjave o preuzimanju poslovnog udjela u obliku '
    'javnobilježničkog akta ili privatne isprave koju potvrdi javni bilježnik (članak 457. stavak 5. '
    'istoga Zakona);', indent=340))
A(p('d) podnijeti registarskom sudu prijavu za upis povećanja temeljnog kapitala sa svim prilozima iz '
    'članka 458. stavka 2. Zakona o trgovačkim društvima, uključujući ovaj Ugovor kao ispravu o '
    'ulaganju;', indent=340))
A(p('e) po provedenom upisu Zajmodavcu bez odgode dostaviti izvadak iz sudskog registra i popis '
    'članova društva.', indent=340))
A(p('(2) Troškove javnog bilježnika, sudskih pristojbi i objave snosi Zajmoprimac. Svaka strana snosi '
    'troškove vlastitih pravnih savjetnika.'))
A(p('(3) Danom upisa povećanja temeljnog kapitala u sudski registar tražbina Zajmodavca u '
    'konvertiranom iznosu prestaje, a Zajmodavac postaje član Zajmoprimca. Ako je konvertiran samo dio '
    'Glavnice, preostali dio Zajmoprimac vraća sukladno članku 4. ovoga Ugovora.'))
A(p('(4) Ako registarski sud zatraži dodatnu dokumentaciju, procjenu vrijednosti unesene tražbine ili '
    'ispravak isprava, Ugovorne strane obvezuju se bez odgode postupiti po zahtjevu suda i po potrebi '
    'sklopiti dodatak ovom Ugovoru kojim se postiže isti gospodarski učinak.'))

A(h('Članak 8. — Obveze Člana'))
A(p('(1) Član se obvezuje na skupštini Zajmoprimca glasovati za sve odluke potrebne za provedbu '
    'Konverzije, uključujući odluku o povećanju temeljnog kapitala i izmjeni društvenog ugovora, za '
    'koju je potrebna većina od najmanje tri četvrtine danih glasova (članak 455. stavak 1. Zakona o '
    'trgovačkim društvima).'))
A(p('(2) Član se izričito i neopozivo odriče prava prvenstva pri preuzimanju novih poslovnih udjela '
    'koji nastaju Konverzijom (članak 457. stavak 4. Zakona o trgovačkim društvima).'))
A(p('(3) Član se obvezuje da neće glasovati za odluke niti poduzimati radnje kojima bi se onemogućila '
    'ili otežala Konverzija, uključujući smanjenje temeljnog kapitala, statusne promjene ili prijenos '
    'imovine izvan redovnog poslovanja, bez prethodne pisane suglasnosti Zajmodavca.'))
A(p('(4) Ako se do trenutka Konverzije promijeni sastav članova Zajmoprimca, Zajmoprimac se obvezuje '
    'da će svaki novi član pisano pristupiti obvezama iz ovoga članka.'))

A(h('Članak 9. — Obavijest o investicijskoj rundi'))
A(p('(1) Zajmoprimac se obvezuje pisano obavijestiti Zajmodavca o svakom pregovoru o ulaganju u '
    'temeljni kapital Zajmoprimca u iznosu većem od {prag_kvalificirane_runde} EUR, kao i o svakom '
    'namjeravanom povećanju temeljnog kapitala, statusnoj promjeni ili prodaji većinskog udjela, i to '
    'najkasnije {rok_obavijesti_dana} dana prije sklapanja odgovarajućeg pravnog posla.'))
A(p('(2) Po primitku obavijesti iz stavka 1. Zajmodavac može u roku od {rok_obavijesti_dana} dana '
    'dostaviti Izjavu o konverziji, u kojem slučaju se Konverzija provodi prije, odnosno istodobno s '
    'ulaganjem novog ulagatelja, po Ugovorenoj vrijednosti iz članka 6. stavka 3. ovoga Ugovora.'))
A(p('(3) Propuštanje obavijesti iz stavka 1. ovoga članka smatra se sprječavanjem ispunjenja uvjeta '
    'protivno načelu savjesnosti i poštenja u smislu članka 297. stavka 4. Zakona o obveznim odnosima.'))

A(h('Članak 10. — Ugovorna kazna'))
A(p('(1) Ako Zajmoprimac ili Član ne ispune obveze iz članaka 7., 8. ili 9. ovoga Ugovora, obvezuju se '
    'Zajmodavcu solidarno platiti ugovornu kaznu u iznosu od {ugovorna_kazna_iznos} EUR '
    '(slovima: {ugovorna_kazna_iznos_slovima}).'))
A(p('(2) Ugovorna kazna iz stavka 1. ugovorena je za neispunjenje nenovčanih obveza (provedbu '
    'Konverzije i s njom povezanih radnji), sukladno članku 350. Zakona o obveznim odnosima, i ne '
    'odnosi se na obvezu vraćanja Glavnice.'))
A(p('(3) Zajmodavac ima pravo i na naknadu štete koja premašuje iznos ugovorne kazne, kao i pravo '
    'zahtijevati ispunjenje obveze.'))
A(p('(4) U slučaju neispunjenja obveza iz članaka 7. ili 8. Zajmodavac može, umjesto ili uz ugovornu '
    'kaznu, tražbinu na povrat Glavnice proglasiti dospjelom i zahtijevati njezin povrat u roku od 15 '
    'dana, uvećan za zatezne kamate od dana dostave Izjave o konverziji.'))

A(h('Članak 11. — Izjave i jamstva Zajmoprimca i Člana'))
A(p('(1) Zajmoprimac jamči da je uredno osnovan i upisan u sudski registar, da nad njim nije otvoren '
    'stečajni, predstečajni ni likvidacijski postupak i da mu nije blokiran račun, te da sklapanje '
    'ovoga Ugovora ne predstavlja povredu njegova društvenog ugovora ni bilo kojeg drugog ugovora.'))
A(p('(2) Zajmoprimac jamči da temeljni kapital na dan sklapanja ovoga Ugovora iznosi '
    '{signer2_temeljni_kapital} EUR te da ne postoje prava trećih osoba na stjecanje poslovnih udjela '
    '(opcije, konvertibilni zajmovi, opcijski programi) koja nisu objavljena Zajmodavcu prije '
    'sklapanja ovoga Ugovora.'))
A(p('(3) Član jamči da je nositelj poslovnog udjela od {signer3_udio_postotak}% temeljnog kapitala '
    'Zajmoprimca, da udio nije opterećen ni založen i da je ovlašten preuzeti obveze iz članka 8. '
    'ovoga Ugovora.'))
A(p('(4) Osobe koje potpisuju ovaj Ugovor jamče da su ovlaštene za zastupanje i sklapanje ovoga '
    'pravnog posla.'))

A(h('Članak 12. — Povjerljivost'))
A(p('(1) Ugovorne strane obvezuju se sadržaj ovoga Ugovora i podatke o poslovanju druge strane čuvati '
    'kao poslovnu tajnu, osim prema poreznim, računovodstvenim i pravnim savjetnicima, javnom '
    'bilježniku, registarskom sudu i nadležnim tijelima, te kada je objava obvezna po zakonu.'))
A(p('(2) Zajmoprimac je ovlašten postojanje i uvjete ovoga Ugovora priopćiti potencijalnim '
    'ulagateljima u postupku dubinskog snimanja (due diligence).'))

A(h('Članak 13. — Obavijesti'))
A(p('(1) Obavijesti po ovom Ugovoru dostavljaju se pisano, na adrese iz zaglavlja ovoga Ugovora ili '
    'elektroničkom poštom na adrese: Zajmodavac {signer1_email}, Zajmoprimac {signer2_email}, '
    'Član {signer3_email}.'))
A(p('(2) Izjava o konverziji, obavijest iz članka 9. i izjava o raskidu valjane su i kada su dane '
    'elektroničkom poštom, uz uvjet da su potpisane kvalificiranim elektroničkim potpisom sukladno '
    'Uredbi (EU) br. 910/2014 (eIDAS). Smatra se da su dostavljene danom slanja.'))
A(p('(3) Svaka strana dužna je promjenu adrese ili adrese elektroničke pošte priopćiti drugim stranama '
    'u roku od 8 dana.'))

A(h('Članak 14. — Mjerodavno pravo i rješavanje sporova'))
A(p('(1) Na ovaj Ugovor primjenjuje se pravo Republike Hrvatske.'))
A(p('(2) Sporove će Ugovorne strane nastojati riješiti sporazumno, a ako u tome ne uspiju u roku od 30 '
    'dana, nadležan je stvarno nadležni sud u {nadlezni_sud_grad}.'))

A(h('Članak 15. — Završne odredbe'))
A(p('(1) Izmjene i dopune ovoga Ugovora valjane su samo u pisanom obliku, uz potpis svih Ugovornih '
    'strana.'))
A(p('(2) Ako pojedina odredba ovoga Ugovora bude ništetna ili neprovediva, ostale odredbe ostaju na '
    'snazi, a Ugovorne strane ništetnu odredbu zamijenit će valjanom koja najbliže odgovara njihovoj '
    'namjeri.'))
A(p('(3) Ovaj Ugovor sklapa se u elektroničkom obliku i potpisuje kvalificiranim elektroničkim '
    'potpisom, koji sukladno članku 25. Uredbe (EU) br. 910/2014 (eIDAS) ima pravni učinak jednak '
    'vlastoručnom potpisu. Na zahtjev bilo koje strane sastavit će se i {broj_primjeraka} '
    '(slovima: {broj_primjeraka_slovima}) papirnata primjerka, po jedan za svaku stranu.'))
A(p('(4) Ovaj Ugovor stupa na snagu danom kada ga potpišu sve Ugovorne strane.'))
A(p('(5) Ugovorne strane suglasno utvrđuju da su ovaj Ugovor pročitale, razumjele i da on odgovara '
    'njihovoj pravoj volji, u znak čega ga potpisuju.', after=400))

A(pagebreak())
A(p('POTPISI UGOVORNIH STRANA', bold=True, align='center', after=60, cls='naslov', keep=True))
A(p('U {mjesto_sklapanja}, dana {datum_sklapanja}', align='center', after=240, keep=True))
A(signature_block())

# --- Sastavljanje DOCX-a -----------------------------------------------------

DOC = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body>' + ''.join(b['docx'] for b in BODY) +
    '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417" w:header="709" w:footer="709"/>'
    '</w:sectPr></w:body></w:document>'
)

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>'
)

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)

DOC_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>'
)

STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:docDefaults><w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/>'
    '<w:lang w:val="hr-HR"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
    '</w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
    '</w:styles>'
)

with zipfile.ZipFile(OUT_DOCX, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CONTENT_TYPES)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/_rels/document.xml.rels', DOC_RELS)
    z.writestr('word/styles.xml', STYLES)
    z.writestr('word/document.xml', DOC)

# --- HTML inačica (izvor za PDF pregled) -------------------------------------

HTML = '''<!doctype html>
<html lang="hr"><head><meta charset="utf-8"><title>Ugovor o zajmu s pravom konverzije</title>
<style>
@page { size: A4; margin: 25mm; }
body { font-family: "Times New Roman", Times, serif; font-size: 12pt; line-height: 1.32; color: #000; }
h1 { font-size: 14pt; font-weight: bold; text-align: center; margin: 0 0 18pt; }
p { margin: 0 0 6pt; }
p.j { text-align: justify; }
p.c { text-align: center; }
p.l { text-align: left; }
p.naslov { margin-top: 14pt; margin-bottom: 2pt; }
p.clanak { margin-bottom: 6pt; }
p.naslov, p.clanak { break-after: avoid; page-break-after: avoid; }
table.potpisi { width: 100%; margin-top: 8pt; }
table.potpisi td { vertical-align: top; width: 50%; padding-right: 14pt; }
.pagebreak { break-before: page; page-break-before: always; height: 0; }
.vizual { height: 43mm; margin: 4pt 14pt 10pt 0; border: 1px dashed #bbb; border-radius: 2px;
          display: flex; align-items: center; justify-content: center; text-align: center;
          color: #999; font-size: 8pt; font-style: italic; }
</style></head><body>
''' + ''.join(b['html'] for b in BODY) + '\n</body></html>\n'

with open(OUT_HTML, 'w', encoding='utf8') as f:
    f.write(HTML)

# --- Popis polja -------------------------------------------------------------

FIELDS = {
    'mjesto_sklapanja': ['Mjesto sklapanja ugovora', 'Zagreb'],
    'datum_sklapanja': ['Datum sklapanja', '27. srpnja 2026.'],
    'signer1_organization': ['Zajmodavac — tvrtka', 'FIRMA B d.o.o.'],
    'signer1_organization_oib': ['Zajmodavac — OIB', '12345678901'],
    'signer1_address': ['Zajmodavac — sjedište (u lokativu: „sa sjedištem u …")', 'Zagrebu, Ilica 1'],
    'signer1_mbs': ['Zajmodavac — MBS iz sudskog registra', '080123456'],
    'signer1_full_name': ['Zajmodavac — ime zakonskog zastupnika', 'Ivan Ivić'],
    'signer1_email': ['Zajmodavac — e-mail za obavijesti', 'ivan@firmab.hr'],
    'signer1_iban': ['Zajmodavac — IBAN za povrat', 'HR1210010051863000160'],
    'signer2_organization': ['Zajmoprimac — tvrtka', 'FIRMA A d.o.o.'],
    'signer2_organization_oib': ['Zajmoprimac — OIB', '10987654321'],
    'signer2_address': ['Zajmoprimac — sjedište (u lokativu)', 'Zagrebu, Savska 32'],
    'signer2_mbs': ['Zajmoprimac — MBS iz sudskog registra', '080654321'],
    'signer2_full_name': ['Zajmoprimac — ime zakonskog zastupnika', 'Matija Stepanić'],
    'signer2_email': ['Zajmoprimac — e-mail za obavijesti', 'matija@firmaa.hr'],
    'signer2_iban': ['Zajmoprimac — IBAN za isplatu zajma', 'HR1723600001101234565'],
    'signer2_temeljni_kapital': ['Temeljni kapital Zajmoprimca u EUR (ključno za izračun udjela)', '2.500,00'],
    'signer3_full_name': ['Član Zajmoprimca — ime i prezime', 'Matija Stepanić'],
    'signer3_oib': ['Član — OIB', '11223344556'],
    'signer3_address': ['Član — adresa (u genitivu: „iz …")', 'Zagreba, Savska 32'],
    'signer3_email': ['Član — e-mail', 'matija@firmaa.hr'],
    'signer3_udio_postotak': ['Član — postotak udjela u temeljnom kapitalu', '100'],
    'iznos_zajma': ['Iznos zajma u EUR', '7.000,00'],
    'iznos_zajma_slovima': ['Iznos zajma slovima', 'sedamtisućaeura'],
    'svrha_zajma': ['Svrha zajma', 'financiranje tekućeg poslovanja i obrtnih sredstava'],
    'rok_isplate_dana': ['Rok isplate zajma u danima od sklapanja', '5'],
    'datum_dospijeca': ['Dan dospijeća povrata', '31. prosinca 2026.'],
    'valuacija_pre_money': ['Ugovorena pre-money vrijednost društva u EUR', '20.000.000,00'],
    'valuacija_pre_money_slovima': ['Vrijednost slovima', 'dvadesetmilijunaeura'],
    'rok_opcije_datum': ['Krajnji datum za korištenje prava na konverziju', '31. prosinca 2026.'],
    'rok_provedbe_dana': ['Rok za provedbu konverzije u danima od Izjave', '45'],
    'prag_kvalificirane_runde': ['Prag ulaganja koji aktivira obavijest, u EUR', '500.000,00'],
    'rok_obavijesti_dana': ['Rok za obavijest / reakciju u danima', '15'],
    'ugovorna_kazna_iznos': ['Ugovorna kazna u EUR', '14.000,00'],
    'ugovorna_kazna_iznos_slovima': ['Ugovorna kazna slovima', 'četrnaesttisućaeura'],
    'nadlezni_sud_grad': ['Grad stvarno nadležnog suda', 'Zagrebu'],
    'broj_primjeraka': ['Broj papirnatih primjeraka', '3'],
    'broj_primjeraka_slovima': ['Broj primjeraka slovima', 'tri'],
}

with open(OUT_JSON, 'w', encoding='utf8') as f:
    json.dump({
        'name': 'Ugovor o zajmu s pravom konverzije u poslovni udio',
        'description': 'B2B beskamatni zajam između dva hrvatska d.o.o. s opcijom zajmodavca da tražbinu '
                       'konvertira u poslovni udio po unaprijed ugovorenoj pre-money vrijednosti.',
        'category': 'Poslovni ugovori',
        'version': '1.0',
        'placeholder_syntax': '{ime_polja}',
        'signers': ['Zajmodavac (firma B)', 'Zajmoprimac (firma A)', 'Član firme A'],
        'fields': {k: {'opis': v[0], 'primjer': v[1]} for k, v in FIELDS.items()},
    }, f, ensure_ascii=False, indent=2)

print(f'{OUT_DOCX} ({os.path.getsize(OUT_DOCX)} B), polja: {len(FIELDS)}')
