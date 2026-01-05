import os
import json
import re
import base64
import time
from io import BytesIO

import streamlit as st
st.set_page_config(
    page_title="Peet Kiest",
    layout="centered"
)

from openai import OpenAI

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Image as RLImage,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from datetime import date


# =========================================================
# CONFIG
# =========================================================
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================================================
# SESSION STATE – veilig over reruns
# =========================================================
_defaults = {
    "result": None,
    "dish_image_bytes": None,
    "wants_image": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

#=======================================================
# Culinary Decision Runner - MASTER PROMPT (PEET v2.6)
#=======================================================

MASTER_PROMPT = """
ROL & IDENTITEIT
Je bent Peet.
Je bent geen chef, geen kookleraar en geen receptenmachine.
Je staat naast de gebruiker in de keuken en neemt twijfel weg.
Je kookt niet om indruk te maken,
maar om het moment te laten kloppen.
Je noemt jezelf nooit AI, assistent, model of systeem.

KERNBELOFTE (LEIDEND)
Een gerecht.
Geen keuzes.
Geen alternatieven.
Geen keuzelijsten.
Geen uitleg achteraf.
Context wordt aangereikt.
Het besluit wordt genomen.

Je:
- verantwoordt geen keuzes
- motiveert niets richting de gebruiker
- legt nooit uit waarom dit gerecht is gekozen

INPUTBETEKENIS (VERPLICHT)
De gebruiker kan context aanleveren via:
* Moment
* Beleving
* Eetvoorkeur
* Aantal personen
* Tijd
* No-gos

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


SCHRIJFSTRATEGIE (VERPLICHT)
Schrijf helder, menselijk en natuurlijk.
Schrijf begeleidend, niet verklarend.
Vermijd afrondende of samenvattende zinnen.
Vermijd herhaling.
Probeer niets "mooi af te maken".
De tekst mag voelen alsof je bezig bent, niet alsof je presenteert.


BEREIDING — TAALRITME (VERPLICHT)

Schrijf de bereiding als een doorlopend kookverhaal.
Gebruik GEEN vaste stapmarkeerders zoals:
- Dan
- Vervolgens
- Daarna

Gebruik overgangen alleen als ze natuurlijk nodig zijn,
en begin in andere gevallen direct met de handeling.

Voorbeelden van toegestane openingen:
- We beginnen met...
- Intussen...
- Ondertussen...
- In dezelfde pan...
- Terwijl dat loopt...
- Zodra dat zover is...
- Nu...
- Tot slot...

Als handelingen logisch op elkaar volgen,
laat de overgang volledig weg.

De tekst moet leesbaar blijven als één vloeiende handeling,
niet als een lijst instructies.

BEREIDING - VORM
De bereiding mag verhalend zijn.
Schrijf alsof je samen kookt en vooruitkijkt,
niet alsof je opdrachten afwerkt.
Gebruik alleen duidelijke momenten waar het nodig is,
en laat de rest vloeien in logisch kooktempo.
De tekst blijft praktisch, maar leest als begeleiding.


BEREIDING — STRUCTUUR
De bereiding wordt geschreven in logische kookfases.
Elke entry in "steps" beschrijft een fase,
geen vaste stap en geen afvinkmoment.
Het aantal fases volgt het gerecht,
niet een vooraf bepaald aantal.
Binnen een fase mag de tekst vloeien,
vooruitdenken en handelingen combineren.
De tekst mag voelen alsof Peet vooruit kijkt terwijl hij kookt.


VARIATIE - VERPLICHT
Vermijd het automatisch kiezen van standaard hoofdingredienten
zoals citroen, rijst, pasta, orzo en milde witvis, prei, mosterd.
Gebruik deze alleen als ze functioneel nodig zijn
voor het gekozen moment of de bereiding.
Zoek actief naar alternatieven in:
- groente
- peulvruchten
- aardappelvarianten
- granen
- minder voor de hand liggende vis- of vleessoorten
Herhaling op hoofdingredient-niveau moet worden vermeden.


SEIZOEN - IMPLICIET
Als een datum is aangeleverd:
- bepaal je intern het seizoen
- gebruik je dit als extra kader voor:
  * ingredienten
  * bereidingstechniek
  * zwaarte
- je benoemt het seizoen nooit expliciet
- je noemt geen maanden of jaargetijden in de output


VASTE OUTPUT - VERPLICHT
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

--- UITBREIDING (ADDITIEF, NIET TER VERVANGING) ---

OPTIONEEL INGREDIENT - GEDRAG
Als de gebruiker een ingredient aanlevert:
* Gebruik dit alleen als het logisch past
* Forceer het nooit
* Integreer het natuurlijk of laat het stilzwijgend los

KEUKEN - RICHTING, GEEN KEUZE
Gebruik dit uitsluitend als smaakanker.
""".strip()



# =========================================================
# HELPERS
# =========================================================
def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Geen JSON gevonden in model-output.")
    return json.loads(text[start : end + 1])


def call_peet(context: str) -> dict:
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": MASTER_PROMPT},
            {"role": "user", "content": context},
        ],
    )
    return _extract_json(resp.output_text)


def generate_dish_image_bytes(dish_name: str) -> bytes | None:
    # Return raw PNG or JPG image bytes.
    # Uses b64_json output from the Images API.
    # No external requests are made.
    try:
        img = client.images.generate(
        model="gpt-image-1",
        prompt=(
            f"Fotografisch realistisch gerecht: {dish_name}. "
            "Warm natuurlijk licht, thuiskeuken, op een bord. "
            "Geen tekst, geen mensen, geen handen, geen props. "
            "Focus volledig op het eten."
        ),
        size="1024x1024",
    )

        return base64.b64decode(img.data[0].b64_json)
    except Exception:
        return None


def safe_filename(name: str) -> str:
    name = (name or "recept").lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    if not name:
        name = "recept"
    return f"{name}.pdf"


def _as_listflow(items: list[str], styles):
    li = [ListItem(Paragraph(str(x), styles["BodyText"])) for x in items]
    return ListFlowable(li, bulletType="bullet", leftIndent=14)


def build_pdf(data: dict, image_bytes: bytes | None = None) -> BytesIO:
    buf = BytesIO()
    styles = getSampleStyleSheet()

    # Kleine stijl voor wat compactere lijsten
    compact = ParagraphStyle(
        "Compact",
        parent=styles["BodyText"],
        leading=13,
        spaceAfter=4,
    )

    story = []
    story.append(Paragraph(data["screen8"]["dish_name"], styles["Title"]))
    story.append(Paragraph(data["screen8"].get("dish_tagline", ""), styles["BodyText"]))
    story.append(Spacer(1, 10))

    # Optioneel: image in PDF (alleen als aanwezig)
    if image_bytes:
        try:
            img_buf = BytesIO(image_bytes)
            rl_img = RLImage(img_buf, width=12.5 * cm, height=12.5 * cm)
            story.append(rl_img)
            story.append(Spacer(1, 10))
        except Exception:
            # Als reportlab het niet lust, gewoon overslaan
            pass

    story.append(Paragraph(data["recipe"]["opening"], styles["BodyText"]))
    story.append(Spacer(1, 10))

    # Ingrediënten (groups)
    story.append(Paragraph("Ingrediënten", styles["Heading2"]))
    for grp in data["recipe"].get("ingredient_groups", []):
        name = grp.get("name", "").strip() or "Benodigd"
        items = grp.get("items", []) or []
        story.append(Paragraph(name, styles["Heading3"]))
        if items:
            story.append(_as_listflow(items, styles))
        else:
            story.append(Paragraph("—", compact))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 6))

    # Bereiding
    story.append(Paragraph("Bereiding", styles["Heading2"]))
    for step in data["recipe"].get("steps", []):
        n = step.get("n", "")
        txt = step.get("text", "")
        story.append(Paragraph(f"{n}. {txt}", styles["BodyText"]))
    story.append(Spacer(1, 10))

    # Boodschappenlijst
    story.append(Paragraph("Boodschappenlijst", styles["Heading2"]))
    for grp in data.get("shopping_list", {}).get("groups", []):
        name = grp.get("name", "").strip() or "Algemeen"
        items = grp.get("items", []) or []
        story.append(Paragraph(name, styles["Heading3"]))
        if items:
            story.append(_as_listflow(items, styles))
        else:
            story.append(Paragraph("—", compact))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(Paragraph(data["recipe"]["closing"], styles["BodyText"]))

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )
    doc.build(story)
    buf.seek(0)
    return buf


# =========================================================
# UI
# =========================================================
st.set_page_config(page_title="Wat eten we vandaag?", layout="centered")

st.title("Peet Kiest wat we eten vandaag.")
st.caption("Geen gedoe. Geen stress. Peet staat naast je in de keuken.")

# ---------------- FORM ----------------
with st.form("context"):
    people = st.number_input("Hoeveel mensen schuiven er aan?", min_value=1, max_value=10, value=2)

    time = st.selectbox(
        "Hoeveel tijd heb je?",
        ["Max 20 min", "30–45 min", "Ik kan er vandaag de tijd voor nemen"],
    )

    moment = st.selectbox(
        "Wat voor dag is het?",
        ["Doordeweeks", "Weekend", "Iets te vieren"],
    )

    beleving = st.selectbox(
        "Hoe ga je straks eten?",
        ["Snel, want ik moet weer door",
        "Gewoon eten, bord op schoot kan ook",
        "Gezellig, we nemen er even de tijd voor",
        "Dit is iets speciaals"],
    )

    voorkeur = st.selectbox(
        "Waar heb je zin in. Vis, Vlees, Veggie, of laat je Peet kiezen?",
        ["Laat Peet kiezen", "Vegetarisch", "Vis", "Vlees"],
    )

    keuken = st.selectbox(
        "Moet ik aan een bepaalde keuken denken?",
        [
            "Laat Peet beslissen",
            "Nederlands / Belgisch",
            "Frans",
            "Italiaans",
            "Mediterraan",
            "Aziatisch",
            "Midden-Oosters",
        ],
    )

    extra_ingredient = st.text_input(
        "Heb je al iets in huis waar ik rekening mee houden?",
        placeholder="Bijvoorbeeld prei, kip, feta…"
    )

    no_gos = st.text_input("Is er iets dat ik beter niet kan gebruiken, bijvoorbeeld vanwege een allergie of omdat je het niet lust?")

    submitted = st.form_submit_button("Peet, neem het over")

# ---------------- SUBMIT LOGIC ----------------
if submitted:
    # Reset alleen bij een nieuwe keuze
    st.session_state.result = None
    st.session_state.dish_image_bytes = None
    st.session_state.wants_image = False

    today = date.today().isoformat()

    context = f"""
DATUM: {today}
AANTAL PERSONEN: {people}
TIJD: {time}
MOMENT: {moment}
BELEVING: {beleving}
EETVOORKEUR: {voorkeur}
KEUKEN: {keuken}
OPTIONEEL INGREDIËNT: {extra_ingredient}
NO-GOS: {no_gos}
""".strip()

    # --- EERSTE PEET-ZIN (DIRECT FEEDBACK) ---
    st.markdown("**Goed. Ik ben bezig. Ik neem het over.**")

    with st.spinner(
        "We hebben meer dan een miljoen gerechten. "
        "Peet zoekt nu de lekkerste voor dit moment voor je uit."
    ):
        try:
            st.session_state.result = call_peet(context)
        except Exception as e:
            st.session_state.result = None
            st.error("Peet raakte even de draad kwijt. Probeer het opnieuw.")
            st.caption(f"Debug: {e}")
            st.stop()

# Als er nog geen resultaat is, stoppen we hier (form blijft zichtbaar)
if st.session_state.result is None:
    st.stop()

data = st.session_state.result


# ---------------- BOVENKANT RECEPT ----------------

# Titel
st.title(data["screen8"]["dish_name"])

# Tagline (rustig, geen kop)
if data["screen8"].get("dish_tagline"):
    st.caption(data["screen8"]["dish_tagline"])

# Praktische startzin
if data["recipe"].get("opening"):
    st.write(data["recipe"]["opening"])


#------------- INTRO VOOR INGREDIËNTEN ---------------------------

st.subheader("Zo pakken we het aan")
st.caption("Geen stress. Dit lukt altijd.")

st.write(
    "We doen dit stap voor stap. "
    "Tip van Peet: lees het recept eerst één keer helemaal door. "
    "Daarna maak je het jezelf makkelijk: zorg dat alles klaarstaat, eventueel al gesneden. "
    "Lees één stap, doe ’m op je gemak, en kijk dan pas weer verder."
)

st.divider()

#------------- INGREDIËNTEN OP HET SCHERM -------------------------

st.markdown("### Ingrediënten")

for grp in data["recipe"].get("ingredient_groups", []):
    name = grp.get("name", "").strip() or "Benodigd"
    items = grp.get("items", []) or []

    ingredient_text = f"**{name}**\n"
    if items:
        ingredient_text += "\n".join(f"- {it}" for it in items)
    else:
        ingredient_text += "- —"

    st.markdown(ingredient_text)

st.divider()

# ---------------- BEREIDING OP HET SCHERM ------------------------

steps = data["recipe"].get("steps", [])

for s in data["recipe"].get("steps", []):
    text = s.get("text", "").strip()
    st.markdown(text)


st.write(data["recipe"]["closing"])

# ---------------- PDF ----------------
pdf_buffer = build_pdf(data, image_bytes=st.session_state.dish_image_bytes)
filename = safe_filename(data["screen8"]["dish_name"])

st.download_button(
    "Download recept + boodschappenlijst (PDF)",
    pdf_buffer.getvalue(),
    file_name=filename,
    mime="application/pdf",
)
# ---------------- FOTO OP KNOP ----------------
st.markdown("### Wil je ‘m ook even zien?")
if st.button("Wil je er een plaatje bij? Duurt wel ff"):
    st.session_state.wants_image = True

if st.session_state.wants_image and st.session_state.dish_image_bytes is None:
    with st.spinner("Effe de goede foto erbij zoeken…"):
        st.session_state.dish_image_bytes = generate_dish_image_bytes(
            data["screen8"]["dish_name"]
        )
        if st.session_state.dish_image_bytes is None:
            st.error("Peet kreeg de foto net niet te pakken. Probeer het nog eens.")

if st.session_state.dish_image_bytes:
    st.image(st.session_state.dish_image_bytes, width="stretch")

st.divider()