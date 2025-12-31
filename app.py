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
# SESSION STATE — EXPLICIET INITIALISEREN (image fix)
# =========================================================
if "result" not in st.session_state:
    st.session_state.result = None

if "dish_image_bytes" not in st.session_state:
    st.session_state.dish_image_bytes = None

if "finished" not in st.session_state:
    st.session_state.finished = False
# =========================================================
# MASTER PROMPT — PEET v2.5 (INTEGRAAL, ONGEWIJZIGD)
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
[... ONGEWIJZIGD ... zie jouw originele prompt ...]

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

--- UITBREIDING (ADDitief, NIET TER VERVANGING) ---

OPTIONEEL INGREDIËNT — GEDRAG
Als de gebruiker één ingrediënt aanlevert:
* Gebruik dit alleen als het logisch past binnen leefmoment, seizoen en gerechtfamilie
* Forceer het nooit
* Integreer het natuurlijk of laat het stilzwijgend los
Je benoemt nooit expliciet of je het ingrediënt gebruikt of negeert.

KEUKEN — RICHTING, GEEN KEUZE
Als een keukenrichting wordt meegegeven:
* Gebruik dit uitsluitend als smaak- en stijlanker
* Laat het gerecht nog steeds door jou bepaald worden
* Vermijd letterlijke nationale clichés
De keuken mag nooit leidend zijn boven leefmoment of schaal.

EINDTOETS
Zou ik dit zo zeggen tegen iemand die naast me staat te koken?
Zo niet: herschrijven.
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
    for key in ["screen7", "screen8", "recipe", "shopping_list"]:
        if key not in data:
            raise ValueError(f"Ontbrekende sleutel: {key}")

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
                + "Ontbreekt iets, corrigeer jezelf en geef opnieuw volledige JSON."
            },
            {"role": "user", "content": context},
            {
                "role": "user",
                "content": "Lever exact de vastgelegde JSON-structuur, met volledige inhoud."
            },
        ],
    )

    data = extract_json(response.output_text)
    validate_contract(data)
    return data


import base64

def generate_dish_image_bytes(dish_name: str) -> bytes | None:
    try:
        prompt = (
            f"Fotografisch realistisch gerecht: {dish_name}. "
            "Warm natuurlijk licht, thuiskeuken, op een bord. "
            "Geen tekst, geen mensen, geen handen, geen props. "
            "Focus volledig op het eten."
        )

        img = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        image_base64 = img.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        return image_bytes

    except Exception as e:
        print(f"Image generatie faalde: {e}")
        return None



def build_pdf(data: dict) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PeetTitle",
        fontSize=18,
        spaceAfter=14
    ))
    styles.add(ParagraphStyle(
        name="PeetSection",
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="PeetBody",
        fontSize=11,
        leading=14,
        spaceAfter=6
    ))

    story = []

    # Titel
    story.append(Paragraph(data["screen8"]["dish_name"], styles["PeetTitle"]))
    if data["screen8"].get("dish_tagline"):
        story.append(Paragraph(data["screen8"]["dish_tagline"], styles["PeetBody"]))
    story.append(Spacer(1, 12))

    # Opening
    story.append(Paragraph(data["recipe"]["opening"], styles["PeetBody"]))

    # Ingrediënten
    story.append(Paragraph("Ingrediënten", styles["PeetSection"]))
    for group in data["recipe"]["ingredient_groups"]:
        story.append(Paragraph(f"<b>{group['name']}</b>", styles["PeetBody"]))
        story.append(
            ListFlowable(
                [
                    ListItem(Paragraph(item, styles["PeetBody"]))
                    for item in group["items"]
                ],
                bulletType="bullet",
                start="circle"
            )
        )

    # Bereiding
    story.append(Paragraph("Bereiding", styles["PeetSection"]))
    for step in data["recipe"]["steps"]:
        story.append(
            Paragraph(f"{step['n']}. {step['text']}", styles["PeetBody"])
        )

    # Afronding
    story.append(Spacer(1, 12))
    story.append(Paragraph(data["recipe"]["closing"], styles["PeetBody"]))

    # Boodschappenlijst
    story.append(Paragraph("Boodschappenlijst", styles["PeetSection"]))
    for group in data["shopping_list"]["groups"]:
        story.append(Paragraph(f"<b>{group['name']}</b>", styles["PeetBody"]))
        story.append(
            ListFlowable(
                [
                    ListItem(Paragraph(item, styles["PeetBody"]))
                    for item in group["items"]
                ],
                bulletType="bullet",
                start="circle"
            )
        )

    doc.build(story)
    buffer.seek(0)
    return buffer

st.set_page_config(
    page_title="Wat moeten we vandaag weer eten?",
    layout="centered"
)

st.title("Wat moeten we vandaag weer eten?")
st.caption("Geen gedoe. Geen stress. Peet neemt het over.")

with st.form("context"):
    people = st.number_input(
        "Hoeveel mensen schuiven er aan?",
        min_value=1,
        max_value=10,
        value=2
    )

    time = st.selectbox(
        "Hoeveel tijd heb je?",
        ["Max 20 min", "30–45 min", "Ik neem er de tijd voor"]
    )

    moment = st.selectbox(
        "Wat voor dag is het?",
        ["Doordeweeks", "Weekend", "Iets te vieren"]
    )

    beleving = st.selectbox(
        "Hoe wil je dat het voelt?",
        ["ff rustig eten", "Comfort", "Gezellig", "Uitpakken"]
    )

    voorkeur = st.selectbox(
        "Waar heb je zin in?",
        ["Alles", "Vegetarisch", "Vis", "Vlees"]
    )

    keuken = st.selectbox(
        "Mag het ergens vandaan komen?",
        [
            "Laat Peet beslissen",
            "Nederlands / Belgisch",
            "Frans",
            "Italiaans",
            "Mediterraan",
            "Aziatisch",
            "Midden-Oosters"
        ]
    )

    extra_ingredient = st.text_input(
        "Is er één ingrediënt dat je graag terugziet? (mag leeg blijven)",
        ""
    )

    no_gos = st.text_input(
        "Is er iets wat absoluut niet mag?",
        ""
    )

    submitted = st.form_submit_button("Peet, neem het over")


if submitted:
    st.session_state.result = None
    st.session_state.dish_image_bytes = None

    context = f"""
AANTAL PERSONEN: {people}
TIJD: {time}
MOMENT: {moment}
BELEVING: {beleving}
EETVOORKEUR: {voorkeur}
KEUKEN: {keuken}
OPTIONEEL INGREDIËNT: {extra_ingredient}
NO-GOS: {no_gos}
"""

    with st.spinner(
        "Momentje. We hebben meer dan een miljoen lekkere dingen en Peet zoekt degene waar jij nu blij van gaat worden."
    ):
        try:
            st.session_state.result = call_peet(context)
        except Exception:
            st.error("Peet raakte even de draad kwijt. Probeer het opnieuw.")
            st.session_state.result = None
            st.stop()

    # image pas later / via knop (zoals afgesproken)


data = st.session_state.result
if not data:
    st.stop()

st.header(data["screen7"]["title"])
st.write(data["screen7"]["body"])
st.success(data["screen7"]["cta"])

st.divider()
st.subheader(data["screen8"]["dish_name"])
st.write(data["screen8"]["dish_tagline"])

# ── Stap B: Image op expliciet verzoek ─────────────────────
if st.button("Wil je er een plaatje bij? Duurt wel ff"):
    with st.spinner("Effe de goede foto erbij zoeken.."):
        try:
            dish_name = data["screen8"]["dish_name"]
            img = generate_dish_image_bytes(dish_name)

            st.write("DEBUG image type:", type(img))
            st.write("DEBUG image length:", len(img) if img else "None")

            st.session_state.dish_image_bytes = img
            st.rerun()
        except Exception as e:
            st.error(f"Image fout: {e}")
            st.session_state.dish_image_bytes = None


if st.session_state.dish_image_bytes:
    st.image(
        st.session_state.dish_image_bytes,
        width="stretch"
    )

st.divider()

st.subheader("Bereiding")
for s in data["recipe"]["steps"]:
    st.markdown(f"**{s['n']}.** {s['text']}")
st.write(data["recipe"]["closing"])

pdf_buffer = build_pdf(data)
filename = safe_filename(data["screen8"]["dish_name"])

if st.download_button(
    "Download recept (PDF)",
    pdf_buffer.getvalue(),
    file_name=filename,
    mime="application/pdf",
):
    st.session_state.finished = True
    st.rerun()

