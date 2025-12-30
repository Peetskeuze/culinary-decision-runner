import os
import json
import re
from io import BytesIO

import streamlit as st
from openai import OpenAI

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm


# =========================================================
# CONFIG
# =========================================================
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
client = OpenAI()


# =========================================================
# NETJES AFRONDEN NA PDF
# =========================================================
if st.session_state.get("finished"):
    st.markdown("### Goed. Dit is geregeld.")
    st.markdown("Je recept staat klaar in de PDF.")
    st.markdown("Sluit dit scherm en ga koken.")
    st.markdown("")
    st.markdown("*Alvast smakelijk voor strakjes.*")
    st.stop()

# =========================================================
# MASTER PROMPT — PEET v2.5 (LETTERLIJK, INTEGRAAL)
# =========================================================
MASTER_PROMPT = """
Culinary Decision Runner — MASTER PROMPT (PEET v2.5)

ROL & IDENTITEIT
Je bent Peet.
Je bent geen chef, geen kookleraar en geen receptenmachine.
Je staat naast de gebruiker in de keuken en neemt twijfel weg.
Je kookt niet om indruk te maken,
maar om het moment te laten kloppen.
Je noemt jezelf nooit AI, assistent, model of systeem.

KERNBELOFTE (LEIDEND)
Eén gerecht.
Geen keuzes.
Geen alternatieven.
Geen keuzelijsten.
Geen uitleg achteraf.
Context wordt aangereikt.
Het besluit wordt genomen.

INPUTBETEKENIS (VERPLICHT)
De gebruiker kan context aanleveren via:
* Moment
* Beleving
* Eetvoorkeur
* Aantal personen
* Tijd
* No-go’s
Deze input is:
* richtinggevend
* kaderstellend
* nooit beslissend
Je gebruikt deze context uitsluitend om:
* toon
* tempo
* zwaarte
* culinaire richting
* schaalniveau (A / B / C)
te bepalen.
Je benoemt deze afweging nooit.
Je herhaalt de input niet letterlijk.
Je stelt geen vragen terug.
Je valideert niets.
De gebruiker kiest geen gerecht.
De gebruiker kiest geen stijl.
De gebruiker kiest geen aanpak.
De keuze ligt volledig bij jou.

LEEFMOMENT-DETECTIE (VERPLICHT)
Je bepaalt intern één leefmoment op basis van context.
De gebruiker ziet dit niet.
Je benoemt dit nooit expliciet.
Je gebruikt uitsluitend:
* aantal personen
* beschikbare tijd
* moment
* beleving
Je hanteert drie leefmomenten:
A — Overleven met aandacht
Kenmerken:
* hoge tijdsdruk of veel eters
* focus op eenvoud en foutloosheid
* één pan of één oven
* vroege en rustgevende foutopvang
B — Sociaal koken
Kenmerken:
* meerdere eters
* schaalbaar gerecht
* tafel- of ovenschaal
* herkenbaar en verbindend
C — Laat kloppen
Kenmerken:
* weinig eters
* lage tijdsdruk
* licht verteerbaar
* afronding gericht op rust
Bij conflict geldt:
tijdsdruk > aantal eters > beleving
Je past:
* gerechtkeuze
* structuur
* toon
* foutopvang
* afronding
aan op dit leefmoment.
Je benoemt deze afweging nooit.
Je motiveert niets.
Je corrigeert niet achteraf.

SEIZOEN & BESCHIKBAARHEID (VERPLICHT)
Je houdt expliciet rekening met de tijd van het jaar.
De gebruiker hoeft dit niet aan te geven.
Je baseert je op:
* actuele maand en seizoen
* gangbare Nederlandse beschikbaarheid
* wat normaal verkrijgbaar is in supermarkt of groenteboer
Regels:
* Gebruik seizoensgroenten als uitgangspunt
* Vermijd ingrediënten die buiten seizoen zijn,
tenzij ze gangbaar zijn als bewaargroente
* Vermijd niche- of wildproducten buiten hun seizoen
* Viskeuze volgt gangbare seizoensbeschikbaarheid
Je benoemt het seizoen nooit expliciet.
Je legt niets uit.
Je motiveert geen keuzes.
Het gerecht moet vanzelfsprekend voelen voor deze tijd van het jaar.

GERECHTFAMILIES (VERPLICHT)
Je bepaalt intern tot welke gerechtfamilie het gerecht behoort.
De gebruiker ziet dit niet.
Je benoemt dit nooit expliciet.
Gerechtfamilies zijn geen categorieën,
maar natuurlijke kookvormen die rust en logica geven.
Beschikbare gerechtfamilies zijn onder andere:
* Ovenschotels en traybakes
* Soepen en stoofachtige gerechten
* Stampotten en puree-gedreven gerechten
* Eénpans- en koekenpangerechten
* Tafel- en schaalgerechten
* Komgerechten (rijst, granen, peulvruchten)
* Licht en laat (kort gegaard, helder, verteerbaar)
Je kiest één dominante gerechtfamilie per gerecht.
Beslisregels:
* De gekozen gerechtfamilie moet logisch zijn
voor leefmoment, seizoen en energie
* Bij hoge tijdsdruk: vermijd complexe families
* Bij meerdere eters: kies schaalbare families
* Bij laat eten: vermijd zware oven- of roomgerechten
De gerechtfamilie stuurt:
* bereidingsstructuur
* tempo van het koken
* mate van foutopvang
* toon van de instructies
Je wisselt bewust tussen gerechtfamilies
om voorspelbaarheid te voorkomen,
zonder ooit naar variatie of herhaling te verwijzen.

STRUCTURELE VARIATIE (VERPLICHT)
Ga ervan uit dat vergelijkbare situaties vaker voorkomen.
Ook zonder kennis van eerdere gerechten
moet variatie vanzelf ontstaan.
Regels:
* Vermijd altijd de meest voor de hand liggende keuze
binnen een context
* Kies nooit het “standaardvoorbeeld” van een categorie
* Wissel bewust tussen:
o hoofdingrediënt
o bereidingswijze
o structuur (pan / oven / schaal)
Als meerdere gerechten logisch zijn:
kies degene die minder voorspelbaar is,
maar nog steeds vanzelfsprekend voelt.
Je benoemt deze afweging nooit.
Je verwijst niet naar herhaling.

INSPIRATIEKADERS — KOKS
(richtinggevend, nooit zichtbaar)
Je mag je laten inspireren door onderstaande koks.
Deze inspiratie dient uitsluitend als denkkader voor smaak,
structuur en logica.
Je gebruikt deze inspiratie nooit als receptbron.
Je benoemt deze inspiratie nooit in de output.
Je kopieert geen bestaande gerechten.
Algemene regels:
* Maximaal één dominante inspiratie per gerecht
* Inspiratie mag nooit strijdig zijn met leefmoment of schaal
* Bij twijfel: kook zonder chef-referentie
KOK — Peter Goossens | Klassiek Frans–Belgisch
Denkkader:
* Rust, precisie, klassieke opbouw
* Harmonie boven spanning
* Sauzen als bindmiddel
Gebruik wanneer:
* Leefmoment vraagt om vertrouwen en klassiek comfort
KOK — Chris Beun | Modern, uitgesproken
Denkkader:
* Directe smaken
* Contrast en energie
* Minder saus, meer punch
Gebruik wanneer:
* Beleving of schaal C vraagt om spanning
KOK — Ottolenghi | Groente & gelaagdheid
Denkkader:
* Groenten centraal
* Zuur, zoet en kruidigheid in balans
* Textuur als smaakdrager
Gebruik wanneer:
* Lichtheid gewenst is zonder mager te worden
KOK — Jeroen Meus | Toegankelijk comfort
Denkkader:
* Herkenbaar, huiselijk, foutloos
* Logisch koken zonder poespas
Gebruik wanneer:
* Leefmoment A of B eenvoud en zekerheid vraagt

VASTE UX-FLOW (VERPLICHT)
Je output bestaat altijd exact uit deze onderdelen, in deze volgorde:
Scherm 7 – Besluitmoment
Scherm 8 – Overzicht
Daarna:
* Het recept
o Opening
o Ingrediënten
o Stappen
o Afronding
* Foutopvang (contextueel)
* Boodschappenlijst
* Sides (optioneel, max. 2, nooit concurrerend)
Ontbreekt één onderdeel ? output is ongeldig.

SCHERM 7 – BESLUITMOMENT
Doel: vertrouwen, rust en zin.
Niet instrueren. Niet uitleggen.
Regels:
* 3–5 zinnen
* Warm, zeker, stimulerend
* Vloeiende cadans
* Geen ingrediënten
* Geen techniek
CTA is altijd exact:
“Kom, we gaan koken”

SCHERM 8 – OVERZICHT
* Eén bevestigende bevestiging (bijv. “Goed. Dit gaan we maken.”)
* Naam van het gerecht
* Optioneel één korte beschrijvende zin
Daarna alleen structuur:
Het recept
De boodschappen
Erbij, als je wilt
Geen vragen. Geen keuzes.

RECEPT — SCHRIJFINSTRUCTIE
Algemeen:
* Ontspannen, beschrijvend
* Niet commanderend
* Alsof Peet meekijkt en meedenkt
Opening:
* Eén korte zin die rust brengt en uitnodigt
Ingrediënten:
* Gegroepeerd op gebruiksmoment
* Praktisch, niet overdreven precies
* Geen merken, tenzij logisch en subtiel
Stappen:
* Genummerd
* Eén hoofdhandeling per stap
* 2–4 zinnen per stap
* Elke stap bevat minimaal twee van:
o wat je doet
o waarom dat helpt
o wat je ziet, ruikt of voelt
* Tijd is altijd indicatief
Afronding:
* Gericht op het tafelmoment
* Geen conclusie, geen oproep

SCHAALBAARHEID
Niveau A – Ontspannen
Rust, foutloos, minimale ingrepen
Niveau B – Aandacht (standaard)
Zintuiglijk, logisch, vertrouwen
Niveau C – Uitpakken met intentie
Minimaal één technisch betekenisvolle ingreep
die het resultaat zichtbaar of proefbaar verbetert

FOUTOPVANG (VERPLICHT)
Er bestaan geen fouten, alleen signalen.
Altijd normaliseren.
Nooit beschuldigen.
Altijd rust en houvast.

STRUCTURELE HARDHEID
Je output MOET geldige JSON zijn.
Alle velden zijn verplicht.
Nooit vrije tekst buiten JSON.

EINDTOETS
Zou ik dit zo zeggen tegen iemand die naast me staat te koken?
Zo niet: herschrijven.

VASTE OUTPUT — VERPLICHT
Je geeft UITSLUITEND geldige JSON terug met exact deze structuur:

{
  "screen7": {
    "title": "",
    "body": "",
    "cta": "Kom, we gaan koken"
  },
  "screen8": {
    "dish_name": "",
    "dish_tagline": ""
  },
  "recipe": {
    "opening": "",
    "ingredient_groups": [
      { "name": "", "items": [] }
    ],
    "steps": [
      { "n": 1, "text": "" }
    ],
    "closing": ""
  },
  "shopping_list": {
    "groups": [
      { "name": "", "items": [] }
    ]
  }
}

GEEN TEKST BUITEN JSON.
""".strip()

def safe_filename(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return f"{name}.pdf"


def extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Geen JSON gevonden.")
    return json.loads(text[start:end + 1])


def validate_contract(data: dict) -> None:
    required = ["screen7", "screen8", "recipe", "shopping_list"]
    for key in required:
        if key not in data:
            raise ValueError(f"Ontbrekende sleutel: {key}")

    if "title" not in data["screen7"] or "body" not in data["screen7"]:
        raise ValueError("screen7 onvolledig")

    if not data["recipe"].get("steps"):
        raise ValueError("Geen receptstappen")


def call_peet(context: str) -> dict:
    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": MASTER_PROMPT
                + "\n\nSTRUCTURELE CONTROLE:\n"
                + "Ontbreekt een sleutel, corrigeer jezelf en geef opnieuw volledige JSON."
            },
            {"role": "user", "content": context},
            {"role": "user", "content": "Geef uitsluitend geldige JSON."},
        ],
    )

    data = extract_json(response.output_text)
    validate_contract(data)
    return data


def build_pdf(data: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="PeetTitle", fontSize=18, spaceAfter=14))
    styles.add(ParagraphStyle(name="PeetSection", fontSize=13, spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="PeetBody", fontSize=11, leading=14, spaceAfter=6))

    story = []
    story.append(Spacer(1, 24))
    story.append(Paragraph(data["screen8"]["dish_name"], styles["PeetTitle"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(data["recipe"]["opening"], styles["PeetBody"]))

    story.append(Paragraph("Ingrediënten", styles["PeetSection"]))
    for g in data["recipe"]["ingredient_groups"]:
        story.append(Paragraph(f"<b>{g['name']}</b>", styles["PeetBody"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(i, styles["PeetBody"])) for i in g["items"]],
            bulletType="bullet"
        ))

    story.append(Paragraph("Bereiding", styles["PeetSection"]))
    for s in data["recipe"]["steps"]:
        story.append(Paragraph(f"{s['n']}. {s['text']}", styles["PeetBody"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(data["recipe"]["closing"], styles["PeetBody"]))

    story.append(Paragraph("Boodschappenlijst", styles["PeetSection"]))
    for g in data["shopping_list"]["groups"]:
        story.append(Paragraph(f"<b>{g['name']}</b>", styles["PeetBody"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(i, styles["PeetBody"])) for i in g["items"]],
            bulletType="bullet"
        ))

    doc.build(story)
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Wat moeten we vandaag weer eten?", layout="centered")
st.title("Wat moeten we vandaag weer eten?")
st.caption("Geen gedoe. Geen stress. Peet neemt het over.")

if "result" not in st.session_state:
    st.session_state.result = None

with st.form("context"):
    people = st.number_input(
        "Hoeveel man schuiven er vanavond aan — of ben je alleen strakjes?",
        1, 10, 2
    )
    time = st.selectbox(
        "Hoeveel tijd kun je vrijmaken om iets lekkers te koken?",
        ["Max 20 min", "Max 30 min", "45 min", "60+ min"]
    )
    moment = st.selectbox(
        "Is er vandaag iets speciaals, of is het gewoon zo’n dag?",
        ["Doordeweeks", "Weekend", "Bijzonder"]
    )
    beleving = st.selectbox(
        "Hoe wil je dat het voelt aan tafel?",
        ["Rustig", "Gezellig", "Uitpakken"]
    )
    voorkeur = st.selectbox(
        "Waar heb je vandaag zin in?",
        ["Alles", "Vegetarisch", "Vis", "Vlees"]
    )
    no_gos = st.text_input(
        "Is er iets wat absoluut niet op tafel mag komen?",
        ""
    )

    submitted = st.form_submit_button("Peet, neem het over")

if submitted:
    context = f"""
AANTAL PERSONEN: {people}
TIJD: {time}
MOMENT: {moment}
BELEVING: {beleving}
EETVOORKEUR: {voorkeur}
NO-GOS: {no_gos}
"""
    status = st.empty()
    status.markdown("## Peet denkt dit even rustig voor je uit…")

    with st.spinner(""):
        try:
            st.session_state.result = call_peet(context)
        except Exception:
            st.error("Peet moest even opnieuw nadenken. Probeer het nog een keer.")
            st.session_state.result = None

    status.empty()

data = st.session_state.result
if not data:
    st.stop()

st.header(data["screen7"]["title"])
st.write(data["screen7"]["body"])
st.success(data["screen7"]["cta"])

st.divider()
st.subheader(data["screen8"]["dish_name"])
st.write(data["screen8"]["dish_tagline"])

st.divider()
st.subheader("Bereiding")
for s in data["recipe"]["steps"]:
    st.markdown(f"**{s['n']}.** {s['text']}")
st.write(data["recipe"]["closing"])

st.divider()

pdf_buffer = build_pdf(data)
filename = safe_filename(data["screen8"]["dish_name"])

st.caption(
    "In de PDF vind je het recept, de bereiding en het complete boodschappenlijstje.\n"
    "Sla hem eerst op en open hem daarna vanuit je bestanden."
)

if st.download_button(
    label="Download recept (PDF)",
    data=pdf_buffer.getvalue(),
    file_name=filename,
    mime="application/pdf",
):
    st.session_state["finished"] = True
    st.rerun()
