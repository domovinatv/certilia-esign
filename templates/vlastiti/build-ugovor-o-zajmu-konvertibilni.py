#!/usr/bin/env python3
"""Generira DOCX predložak 'Ugovor o zajmu s pravom konverzije' u stilu AKD kataloga:
placeholderi {snake_case}, signer1_* / signer2_* / signer3_*.

Bez vanjskih ovisnosti — DOCX se sastavlja kao ZIP s minimalnim OOXML-om.

    python3 templates/vlastiti/build-ugovor-o-zajmu-konvertibilni.py

Pravna podloga i rizici: vidi PRAVNA-ANALIZA.md u istom direktoriju.
"""
import json
import os
import sys
import zipfile
from xml.sax.saxutils import escape

# `--kamata` gradi inačicu s ugovornom kamatom umjesto beskamatnog čl. 3.
# (izlazi dobivaju sufiks -kamata; fill-ugovor.py bira predložak prema tome
# sadrži li ulazni JSON polje `kamatna_stopa`). Stopa se ne nameće zakonom —
# nepovezanim stranama je 0 % uredno — nego se ugovara u visini propisane
# stope za povezane osobe (ZPD čl. 14. st. 3.) kao porezno sigurna vrijednost.
KAMATA = '--kamata' in sys.argv
SUFFIX = '-kamata' if KAMATA else ''

OUT_DOCX = os.path.join(os.path.dirname(__file__), f'ugovor-o-zajmu-konvertibilni{SUFFIX}.docx')
OUT_JSON = os.path.join(os.path.dirname(__file__), f'ugovor-o-zajmu-konvertibilni{SUFFIX}.fields.json')
OUT_HTML = os.path.join(os.path.dirname(__file__), f'ugovor-o-zajmu-konvertibilni{SUFFIX}.html')

# `--mreza` iscrtava rezervirane ćelije mreže vizuala tankim okvirom, radi
# provjere rasporeda potpisne stranice. U dokumentu koji ide na potpis okvira
# nema — a i kad je uključen, siv je toliko da ga mjerenje tinte iz
# src/visual.ts ne vidi kao sadržaj (prag: piksel tamniji od 225).
SHOW_GRID = '--mreza' in sys.argv

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


def pagebreak(html=True):
    """Prijelom stranice. `html=False` kad HTML prijelom radi @page pravilo —
    dvostruki prijelom u Chromeu ostavlja praznu stranicu."""
    return {'docx': '<w:p><w:r><w:br w:type="page"/></w:r></w:p>',
            'html': '<div class="pagebreak"></div>' if html else ''}


def visual_space():
    """Prazan prostor za vizual kvalificiranog elektroničkog potpisa (DOCX).

    DOCX se ne potpisuje (potpisuje se PDF), pa je ovdje dovoljno šest praznih
    redaka; PDF raspored je apsolutan i složen u signature_block()."""
    return ('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '</w:pPr></w:p>' * 6)


# --- Mreža vizuala (Prilog A) ------------------------------------------------
# Vizual je 248×122 pt, mreža ima marginu 10 mm od ruba stranice, a A4 portrait
# daje 2 stupca × 6 redaka (RelPos 1–12, red po red od vrha, 11 = dolje lijevo).
# Rezervirani prostor mora pasti TOČNO na ćeliju mreže — inače ePotpis smjesti
# vizual preko imena potpisnika (naučeno na primjerku od 27.07.2026., gdje su
# ćelije 4 i 7 sjele na imena).
#
# Zato potpisna stranica ima vlastitu marginu od 10 mm (@page potpisna), pa je
# mreža ujedno i raspored stranice: ćelija = stupac teksta. Tekst se ne smije
# proširiti izvan te margine — Chrome pri ispisu skalira CIJELI dokument da
# ugura preljev (mjereno: faktor 0,9), pa se onda ništa ne poklapa s mrežom.
POINTS_IN_MM = 2.83464567
PAGE_W_PT, PAGE_H_PT = 595.276, 841.89     # A4 portrait
GRID_MARGIN_PT = 10 * POINTS_IN_MM         # margina mreže vizuala = margina potpisne stranice
VISUAL_W_PT, VISUAL_H_PT = 248.0, 122.0
# ćelije rezervirane za vizuale: 5 = Zajmodavac, 6 = Zajmoprimac, 9 = Član
# (10 ostaje slobodna kao pričuva za automatski odabir iz src/visual.ts)
CELL_ZAJMODAVAC, CELL_ZAJMOPRIMAC, CELL_CLAN = 5, 6, 9


def grid_cell(pos):
    """RelPos (1–12) → (x, y) ćelije u točkama stranice, ishodište gore-lijevo.

    Prijepis GetVisualGrid iz Priloga A — isti algoritam kao visualGrid() u
    src/visual.ts. Računa se, a ne hardkodira, jer ovisi o formatu stranice."""
    cols = int((PAGE_W_PT - 2 * GRID_MARGIN_PT) // VISUAL_W_PT)
    rows = int((PAGE_H_PT - 2 * GRID_MARGIN_PT) // VISUAL_H_PT)
    hgap = ((PAGE_W_PT - 2 * GRID_MARGIN_PT - cols * VISUAL_W_PT) / (cols - 1)) if cols > 1 else 0
    vgap = ((PAGE_H_PT - 2 * GRID_MARGIN_PT - rows * VISUAL_H_PT) / (rows - 1)) if rows > 1 else 0
    row, col = divmod(pos - 1, cols)
    return (GRID_MARGIN_PT + col * (VISUAL_W_PT + hgap),
            GRID_MARGIN_PT + row * (VISUAL_H_PT + vgap))


def _rel(page_pt):
    """Koordinata stranice → koordinata unutar sadržaja potpisne stranice."""
    return round(page_pt - GRID_MARGIN_PT, 2)


def signature_block():
    """Potpisna stranica: uloga i tvrtka iznad praznog prostora za vizual, ispod
    prostora crta i ime potpisnika — klasičan raspored potpisnog mjesta, samo što
    je „prostor za rukopis" ovdje točno jedna ćelija mreže vizuala.

    DOCX zadržava tablični raspored (DOCX se ne potpisuje — potpisuje se PDF)."""
    parties = [
        ('Za Zajmodavca:', '{signer1_organization}', '{signer1_full_name}', CELL_ZAJMODAVAC),
        ('Za Zajmoprimca:', '{signer2_organization}', '{signer2_full_name}', CELL_ZAJMOPRIMAC),
        ('Za Člana:', '', '{signer3_full_name}', CELL_CLAN),
    ]

    # --- DOCX: tablica 2×2, isti redoslijed elemenata kao na potpisnoj stranici
    def cell_docx(party):
        label, org, name = party[:3]
        inner = [p(label, bold=True, align='left', after=60)['docx'],
                 p(org, align='left', after=60)['docx'],
                 visual_space(),
                 p('_______________________________', align='left', after=60)['docx'],
                 p(name, align='left', after=0)['docx'],
                 p('kvalificirani elektronički potpis', align='left', after=240)['docx']]
        return ('<w:tc><w:tcPr><w:tcW w:w="4600" w:type="dxa"/></w:tcPr>'
                + ''.join(inner) + '</w:tc>')

    rows_docx = [f'<w:tr>{cell_docx(parties[0])}{cell_docx(parties[1])}</w:tr>',
                 '<w:tr>' + cell_docx(parties[2])
                 + '<w:tc><w:tcPr><w:tcW w:w="4600" w:type="dxa"/></w:tcPr>'
                 + p('', after=0)['docx'] + '</w:tc></w:tr>']
    docx = (p('POTPISI UGOVORNIH STRANA', bold=True, align='center', after=60,
              cls='naslov', keep=True)['docx']
            + p('U {mjesto_sklapanja}, dana {datum_sklapanja}', align='center',
                after=60, keep=True)['docx']
            + p('Prostor iznad crte s imenom potpisnika rezerviran je za vizual kvalificiranog '
                'elektroničkog potpisa.', align='center', after=240, keep=True)['docx']
            + '<w:tbl><w:tblPr><w:tblW w:w="9200" w:type="dxa"/>'
              '<w:tblLayout w:type="fixed"/></w:tblPr>'
              '<w:tblGrid><w:gridCol w:w="4600"/><w:gridCol w:w="4600"/></w:tblGrid>'
            + ''.join(rows_docx) + '</w:tbl>')

    # --- HTML/PDF: svaki potpisnik je jedna ćelija mreže; zaglavlje raste prema
    # gore, podnožje prema dolje, pa duga tvrtka ili ime ne mogu ući u prostor
    # rezerviran za vizual.
    def unit(label, org, name, pos):
        x, y = grid_cell(pos)
        return (f'<div class="potpisnik" style="left:{_rel(x)}pt;top:{_rel(y)}pt">'
                f'<div class="zaglavlje"><p class="uloga">{label}</p>'
                f'<p class="tvrtka">{org or "&nbsp;"}</p></div>'
                f'<div class="podnozje"><p class="ime">{name}</p>'
                f'<p class="napomena">kvalificirani elektronički potpis</p></div>'
                + ('<div class="mreza"></div>' if SHOW_GRID else '')
                + '</div>')

    html = ('<div class="sigpage">'
            + '<div class="sighead"><p class="c"><strong>POTPISI UGOVORNIH STRANA</strong></p>'
            + '<p class="c">U {mjesto_sklapanja}, dana {datum_sklapanja}</p>'
            + '<p class="c uputa">Prostor iznad crte s imenom potpisnika rezerviran je za vizual '
              'kvalificiranog elektroničkog potpisa.</p></div>'
            + ''.join(unit(*party) for party in parties)
            + '</div>')
    return {'docx': docx, 'html': html}


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
    'koji ovaj Ugovor sklapa isključivo radi preuzimanja obveza iz članaka 8., 10. i 11. ovoga Ugovora', after=120))
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
if KAMATA:
    A(p('(1) Na Glavnicu teče ugovorna kamata po fiksnoj stopi od {kamatna_stopa}% godišnje '
        '(u daljnjem tekstu: **Kamata**). Stopa je ugovorena u visini kamatne stope na zajmove između '
        'povezanih osoba propisane na temelju članka 14. stavka 3. Zakona o porezu na dobit '
        '({kamatna_stopa_izvor}) i ne prelazi najvišu dopuštenu ugovornu kamatnu stopu iz članka 26. '
        'stavka 2. Zakona o obveznim odnosima.'))
    A(p('(2) Kamata se obračunava na neotplaćeni iznos Glavnice, od dana isplate Glavnice (članak 2. '
        'stavak 3.) do dana povrata, odnosno — u slučaju Konverzije iz članka 6. ovoga Ugovora — do '
        'dana upisa povećanja temeljnog kapitala u sudski registar, proporcionalnom metodom uz '
        'stvarni broj dana i godinu od 365 dana.'))
    A(p('(3) Kamata dospijeva i plaća se u novcu istodobno s povratom Glavnice, a u slučaju '
        'Konverzije u roku od 15 dana od upisa povećanja temeljnog kapitala u sudski registar. '
        'Tražbina Kamate ne ulazi u iznos koji se konvertira (C iz članka 6. stavka 4.), osim ako '
        'Ugovorne strane naknadno pisano ne ugovore drukčije.'))
    A(p('(4) Ugovorne strane izjavljuju da nisu povezane osobe u smislu članka 13. stavka 2. Zakona o '
        'porezu na dobit; Kamata u visini stope propisane za povezane osobe ugovorena je kao mjera '
        'opreza, njihovom slobodnom poslovnom odlukom.'))
else:
    A(p('(1) Zajam je **beskamatan**. Ugovorne strane izričito isključuju primjenu članka 500. stavka 2. '
        'Zakona o obveznim odnosima, prema kojemu u trgovačkim ugovorima zajmoprimac duguje kamate iako '
        'nisu ugovorene, te suglasno utvrđuju da Zajmoprimac po ovom Ugovoru ne duguje nikakvu ugovornu '
        'kamatu ni naknadu.'))
    A(p('(2) Ugovorne strane izjavljuju da nisu povezane osobe u smislu članka 13. stavka 2. Zakona o '
        'porezu na dobit te da beskamatnost zajma predstavlja rezultat njihove slobodne poslovne odluke, '
        'pri čemu je protučinidba Zajmodavcu pravo na konverziju iz članka 6. ovoga Ugovora.'))

A(h('Članak 4. — Rok i način vraćanja'))
A(p('(1) Zajmoprimac se obvezuje Glavnicu' + (', zajedno s Kamatom iz članka 3.,' if KAMATA else '')
    + ' vratiti jednokratno, najkasnije do {datum_dospijeca} '
    '(u daljnjem tekstu: **Dan dospijeća**), uplatom na račun Zajmodavca IBAN: {signer1_iban}.'))
A(p('(2) Zajmoprimac ima pravo Glavnicu vratiti i prije Dana dospijeća, u cijelosti ili djelomično, '
    'bez ikakve naknade ili obveze naknade štete, uz pisanu obavijest Zajmodavcu najmanje '
    '{rok_obavijesti_dana} dana unaprijed. Ugovorne strane time izričito odstupaju od članka 507. '
    'Zakona o obveznim odnosima.'))
A(p('(3) Obavijest iz stavka 2. ovoga članka Zajmodavcu daje priliku da prije povrata iskoristi pravo '
    'na konverziju iz članka 6. ovoga Ugovora. Ako Zajmodavac u roku iz stavka 2. ne dostavi Izjavu o '
    'konverziji, Zajmoprimac Glavnicu vraća, a pravo na konverziju u vraćenom dijelu prestaje.'))
A(p('(4) Vraćanjem Glavnice u cijelosti' + (' i plaćanjem Kamate' if KAMATA else '')
    + ' prestaju sve obveze Zajmoprimca i Člana iz ovoga Ugovora, '
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

A(h('Članak 10. — Likvidnosni događaj'))
A(p('(1) Likvidnosnim događajem smatra se, dok traje pravo na konverziju iz članka 6. ovoga Ugovora: '
    'a) prodaja ili drugi prijenos poslovnih udjela koji zajedno predstavljaju više od 50% temeljnog '
    'kapitala Zajmoprimca; b) prodaja ili drugo raspolaganje cjelokupnom ili pretežnim dijelom imovine '
    'Zajmoprimca; c) pripajanje, spajanje ili druga statusna promjena nakon koje dotadašnji članovi '
    'Zajmoprimca ne zadržavaju većinu glasova u društvu koje nastavlja poslovanje.'))
A(p('(2) O namjeravanom Likvidnosnom događaju Zajmoprimac i Član obavještavaju Zajmodavca sukladno '
    'članku 9. stavku 1. ovoga Ugovora. Zajmodavac u roku od {rok_obavijesti_dana} dana od primitka '
    'obavijesti pisano bira između:'))
A(p('a) povrata Glavnice, koja u tom slučaju dospijeva istodobno s Likvidnosnim događajem; ili',
    indent=340))
A(p('b) isplate Konverzijskog iznosa iz stavka 3. ovoga članka.', indent=340))
A(p('(3) Konverzijski iznos jednak je umnošku Neto naknade i postotka koji bi Zajmodavac imao u '
    'temeljnom kapitalu Zajmoprimca da je Konverzija provedena neposredno prije Likvidnosnog događaja, '
    'izračunatog prema članku 6. stavcima 4. i 5. ovoga Ugovora. Neto naknada je ukupna naknada koju u '
    'Likvidnosnom događaju primaju članovi Zajmoprimca, odnosno Zajmoprimac u slučaju iz stavka 1. '
    'točke b), umanjena za razumne i dokazane troškove transakcije.'))
A(p('(4) Konverzijski iznos isplaćuje se istodobno s primitkom naknade, a najkasnije u roku od '
    '{rok_obavijesti_dana} dana od tog primitka. Obvezu isplate imaju: u slučajevima iz stavka 1. '
    'točaka a) i c) Član i svaki drugi član koji prima naknadu, razmjerno primljenom, a u slučaju iz '
    'točke b) Zajmoprimac. Zajmoprimac i Član za tu obvezu odgovaraju solidarno.'))
A(p('(5) Ako naknada nije novčana, Zajmodavac ima pravo na novčanu protuvrijednost pripadajućeg dijela '
    'naknade, utvrđenu po vrijednosti primijenjenoj u samoj transakciji.'))
A(p('(6) Zajmodavac ne može istodobno ostvariti pravo iz ovoga članka i provesti Konverziju po istoj '
    'osnovi. Isplatom po ovome članku prestaju sva prava i obveze iz ovoga Ugovora, osim obveze '
    'čuvanja povjerljivosti.'))
A(p('(7) Ako Zajmodavac u roku iz stavka 2. ne izjasni izbor, smatra se da je izabrao povrat Glavnice.'))
A(p('(8) Obveza isplate iz ovoga članka novčana je obveza; na zakašnjenje s njezinim ispunjenjem '
    'primjenjuje se članak 5. ovoga Ugovora.'))

A(h('Članak 11. — Ugovorna kazna'))
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

A(h('Članak 12. — Izjave i jamstva Zajmoprimca i Člana'))
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

A(h('Članak 13. — Prijenos prava i obveza'))
A(p('(1) Zajmodavac ne može tražbinu po ovom Ugovoru, pravo na konverziju iz članka 6. niti bilo koje '
    'drugo pravo iz ovoga Ugovora prenijeti, ustupiti ni založiti bez prethodne pisane suglasnosti '
    'Zajmoprimca. Ugovorne strane izričito ugovaraju zabranu ustupanja u smislu članka 80. stavka 2. '
    'Zakona o obveznim odnosima, tako da ugovor o ustupanju sklopljen bez takve suglasnosti nema '
    'učinak prema Zajmoprimcu.'))
A(p('(2) Suglasnost iz stavka 1. ne može se uskratiti bez opravdanog razloga kada se prijenos obavlja '
    'na društvo koje je s Zajmodavcem povezano u smislu propisa o trgovačkim društvima, ni kada do '
    'prijenosa dolazi statusnom promjenom Zajmodavca, univerzalnim pravnim sljedništvom ili '
    'nasljeđivanjem; u tim slučajevima Zajmodavac o prijenosu obavještava Zajmoprimca u roku od '
    '{rok_obavijesti_dana} dana.'))
A(p('(3) Zajmoprimac i Član ne mogu svoje obveze iz ovoga Ugovora prenijeti na treće osobe bez '
    'prethodne pisane suglasnosti Zajmodavca.'))

A(h('Članak 14. — Povjerljivost'))
A(p('(1) Ugovorne strane obvezuju se sadržaj ovoga Ugovora i podatke o poslovanju druge strane čuvati '
    'kao poslovnu tajnu, osim prema poreznim, računovodstvenim i pravnim savjetnicima, javnom '
    'bilježniku, registarskom sudu i nadležnim tijelima, te kada je objava obvezna po zakonu.'))
A(p('(2) Zajmoprimac je ovlašten postojanje i uvjete ovoga Ugovora priopćiti potencijalnim '
    'ulagateljima u postupku dubinskog snimanja (due diligence).'))

A(h('Članak 15. — Obavijesti'))
A(p('(1) Obavijesti po ovom Ugovoru dostavljaju se pisano, na adrese iz zaglavlja ovoga Ugovora ili '
    'elektroničkom poštom na adrese: Zajmodavac {signer1_email}, Zajmoprimac {signer2_email}, '
    'Član {signer3_email}.'))
A(p('(2) Izjava o konverziji, obavijest iz članka 9. i izjava o raskidu valjane su i kada su dane '
    'elektroničkom poštom, uz uvjet da su potpisane kvalificiranim elektroničkim potpisom sukladno '
    'Uredbi (EU) br. 910/2014 (eIDAS). Smatra se da su dostavljene danom slanja.'))
A(p('(3) Svaka strana dužna je promjenu adrese ili adrese elektroničke pošte priopćiti drugim stranama '
    'u roku od 8 dana.'))

A(h('Članak 16. — Mjerodavno pravo i rješavanje sporova'))
A(p('(1) Na ovaj Ugovor primjenjuje se pravo Republike Hrvatske.'))
A(p('(2) Sporove će Ugovorne strane nastojati riješiti sporazumno, a ako u tome ne uspiju u roku od 30 '
    'dana, nadležan je stvarno nadležni sud u {nadlezni_sud_grad}.'))

A(h('Članak 17. — Završne odredbe'))
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

A(pagebreak(html=False))   # u HTML-u prijelom radi @page potpisna
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
/* Potpisna stranica ima marginu mreže vizuala (10 mm), pa se rezervirani prostor
   poklapa s ćelijom, a tekst potpisnika s njezinim lijevim rubom. */
@page potpisna { size: A4; margin: 10mm; }
html, body { margin: 0; padding: 0; }   /* 8px zadane margine bi pomaknule cijeli raspored */
body { font-family: "Times New Roman", Times, serif; font-size: 12pt; line-height: 1.32; color: #000; }
h1 { font-size: 14pt; font-weight: bold; text-align: center; margin: 0 0 18pt; }
p { margin: 0 0 6pt; }
p.j { text-align: justify; }
p.c { text-align: center; }
p.l { text-align: left; }
p.naslov { margin-top: 14pt; margin-bottom: 2pt; }
p.clanak { margin-bottom: 6pt; }
p.naslov, p.clanak { break-after: avoid; page-break-after: avoid; }
.pagebreak { break-before: page; page-break-before: always; height: 0; }
/* Potpisna stranica: raspored je apsolutan i vezan na mrežu vizuala iz Priloga A.
   .potpisnik JEST ćelija mreže (248×122 pt) — ostaje prazna da vizual sjedne u
   nju; zaglavlje s ulogom i tvrtkom raste od nje prema gore, a crta s imenom
   prema dolje, pa duži tekst nikad ne uđe u rezervirani prostor. Crta je 7 pt
   ispod ćelije, izvan pojasa koji mjerenje tinte iz src/visual.ts gleda
   (ćelija + 4 pt), pa smije biti tamna. */
.sigpage { page: potpisna; position: relative; height: 700pt; }
.sighead { position: absolute; left: 0; top: 41.75pt; width: 100%; }  /* isti vrh teksta kao na ostalim stranicama */
.sighead p { margin: 0 0 6pt; }
.sighead p.uputa { font-size: 9.5pt; color: #444; margin-top: 10pt; }
.potpisnik { position: absolute; width: 248pt; height: 122pt; }
.potpisnik p { margin: 0; text-align: left; }
.zaglavlje { position: absolute; left: 0; bottom: 100%; width: 248pt; padding-bottom: 12pt; }
.zaglavlje .uloga { font-weight: bold; }
.podnozje { position: absolute; left: 0; top: 100%; width: 248pt;
            margin-top: 7pt; padding-top: 5pt; border-top: 0.75pt solid #333; }
.podnozje .napomena { font-size: 8pt; font-style: italic; color: #666; margin-top: 2pt; }
.mreza { position: absolute; left: 0; top: 0; width: 100%; height: 100%;
         box-sizing: border-box; border: 1px solid #ececec; }
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

if KAMATA:
    FIELDS['kamatna_stopa'] = [
        'Ugovorna kamatna stopa, % godišnje (hrvatski zapis, npr. 2,65)', '2,65']
    FIELDS['kamatna_stopa_izvor'] = [
        'Izvor propisane stope za povezane osobe (odluka ministra financija)',
        'za 2026. objavljena u Narodnim novinama 150/25']

with open(OUT_JSON, 'w', encoding='utf8') as f:
    json.dump({
        'name': 'Ugovor o zajmu s pravom konverzije u poslovni udio'
                + (' (s ugovornom kamatom)' if KAMATA else ''),
        'description': ('B2B zajam uz ugovornu kamatu u visini propisane stope za povezane osobe'
                        if KAMATA else 'B2B beskamatni zajam') +
                       ' između dva hrvatska d.o.o. s opcijom zajmodavca da tražbinu '
                       'konvertira u poslovni udio po unaprijed ugovorenoj pre-money vrijednosti.',
        'category': 'Poslovni ugovori',
        'version': '2.0' if KAMATA else '1.0',
        'placeholder_syntax': '{ime_polja}',
        'signers': ['Zajmodavac (firma B)', 'Zajmoprimac (firma A)', 'Član firme A'],
        'fields': {k: {'opis': v[0], 'primjer': v[1]} for k, v in FIELDS.items()},
    }, f, ensure_ascii=False, indent=2)

print(f'{OUT_DOCX} ({os.path.getsize(OUT_DOCX)} B), polja: {len(FIELDS)}')
