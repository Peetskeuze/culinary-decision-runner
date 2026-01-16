import streamlit as st
import streamlit as st

# =========================================================
# DEV WAARSCHUWING
# =========================================================
st.warning("⚠️ DEV-versie (peet-card). Niet delen met testers.")

st.title("Peet Card — DEV input check")

# =========================================================
# QUERY PARAMS → NORMALISATIE
# =========================================================

qp = st.experimental_get_query_params()

def get_param_str(key, default=""):
    return qp.get(key, [default])[0].strip()

def get_param_int(key, default):
    try:
        return int(get_param_str(key, default))
    except ValueError:
        return default

def get_param_list(key):
    raw = get_param_str(key, "")
    return [i.strip() for i in raw.split(",") if i.strip()]

# =========================================================
# PARSE INPUT (Carrd → Streamlit)
# =========================================================

days = get_param_int("days", 1)
persons = get_param_int("persons", 2)

time = get_param_str("time", "normaal")
moment = get_param_str("moment", "doordeweeks")
preference = get_param_str("preference", "")
kitchen = get_param_str("kitchen", "")

fridge = get_param_list("fridge")
nogo = get_param_list("nogo")
allergies = get_param_list("allergies")

context = {
    "days": days,
    "persons": persons,
    "time": time,
    "moment": moment,
    "preference": preference,
    "kitchen": kitchen,
    "fridge": fridge,
    "nogo": nogo,
    "allergies": allergies,
}

# =========================================================
# TONEN OP SCHERM (TESTFASE)
# =========================================================

st.subheader("Ontvangen input vanuit Carrd")

st.write("Aantal dagen:", days)
st.write("Aantal personen:", persons)
st.write("Tijd/tempo:", time)
st.write("Moment:", moment)
st.write("Voorkeur:", preference)
st.write("Keuken:", kitchen)

st.write("Koelkast:", fridge if fridge else "—")
st.write("Niet toegestaan:", nogo if nogo else "—")
st.write("Allergieën:", allergies if allergies else "—")

st.divider()

st.caption("⬆️ Als dit klopt, is de Carrd → Streamlit koppeling stabiel.")

st.set_page_config(
    page_title="Peet DEV — niet voor testers",
    page_icon="🧪"
=======
# =========================================================
# PEET DEV APP
# Doel: veilige ontwikkelomgeving
# - Output identiek aan stabiele app
# - Input-gateway voorbereid (nog niet actief)
# - NIET delen met testers
# =========================================================

import os
import sys
from pathlib import Path
import streamlit as st



# ---------------------------------------------------------
# PROJECT ROOT BOOTSTRAP (Cloud + lokaal)
# ---------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------
# DEV MARKERING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Peet DEV — niet voor testers",
    page_icon="🧪",
    layout="centered",
>>>>>>> 2fb2802 (Add clean peet_dev app (no secrets))
)

st.warning("⚠️ Dit is de DEV-versie. Niet delen met testers.")

<<<<<<< HEAD
import os
import json
import re
import base64
from io import BytesIO

import streamlit as st
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


# =========================================================
# MASTER PROMPT — PEET v2.5 (INTEGRAAL, ONGWIJZIGD)
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
* Gebruik dit alleen als het logisch past
* Forceer het nooit
* Integreer het natuurlijk of laat het stilzwijgend los

KEUKEN — RICHTING, GEEN KEUZE
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
    """
    Return raw PNG/JPG bytes. Uses b64_json (no external requests).
    """
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

st.title("Wat moeten we vandaag weer eten?")
st.caption("Geen gedoe. Geen stress. Peet staat naast je in de keuken.")

# ---------------- FORM ----------------
with st.form("context"):
    people = st.number_input("Hoeveel mensen schuiven er aan?", min_value=1, max_value=10, value=2)

    time = st.selectbox(
        "Hoeveel tijd heb je?",
        ["Max 20 min", "30–45 min", "Ik neem er de tijd voor"],
    )

    moment = st.selectbox(
        "Wat voor dag is het?",
        ["Doordeweeks", "Weekend", "Iets te vieren"],
    )

    beleving = st.selectbox(
        "Hoe wil je dat het voelt?",
        ["ff rustig eten", "Comfort", "Gezellig", "Uitpakken"],
    )

    voorkeur = st.selectbox(
        "Waar heb je zin in?",
        ["Alles", "Vegetarisch", "Vis", "Vlees"],
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
            "Midden-Oosters",
        ],
    )

    extra_ingredient = st.text_input(
        "Is er één ingrediënt dat je graag terugziet? (mag leeg blijven)",
        "",
    )

    no_gos = st.text_input("Is er iets wat absoluut niet mag?", "")

    submitted = st.form_submit_button("Peet, neem het over")

# ---------------- SUBMIT LOGIC ----------------
if submitted:
    # Reset alleen bij een nieuwe keuze
    st.session_state.result = None
    st.session_state.dish_image_bytes = None
    st.session_state.wants_image = False

    context = f"""
AANTAL PERSONEN: {people}
TIJD: {time}
MOMENT: {moment}
BELEVING: {beleving}
EETVOORKEUR: {voorkeur}
KEUKEN: {keuken}
OPTIONEEL INGREDIËNT: {extra_ingredient}
NO-GOS: {no_gos}
""".strip()

    with st.spinner("Momentje. We hebben meer dan een miljoen gerechten. Peet zoekt nu de lekkerste voor dit moment voor je uit."):
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

# ---------------- RESULTAAT ----------------
st.header(data["screen7"]["title"])
st.write(data["screen7"]["body"])
st.success(data["screen7"]["cta"])

st.divider()

st.subheader(data["screen8"]["dish_name"])
st.write(data["screen8"]["dish_tagline"])

st.markdown("### Peet staat naast je")
st.write(data["recipe"]["opening"])

# Ingrediënten op het scherm
st.markdown("### Ingrediënten")
for grp in data["recipe"].get("ingredient_groups", []):
    name = grp.get("name", "").strip() or "Benodigd"
    st.markdown(f"**{name}**")
    items = grp.get("items", []) or []
    if items:
        for it in items:
            st.write(f"• {it}")
    else:
        st.write("• —")

st.divider()

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

# ---------------- BEREIDING OP HET SCHERM ----------------
st.subheader("Zo pakken we het aan")

st.caption("Geen stress. Dit lukt altijd.")

st.write(
    "We doen dit stap voor stap. "
    "Lees één stap, doe ’m rustig, en kijk dan pas weer verder. "
    "Ik blijf even bij je."
)

st.divider()

for s in data["recipe"].get("steps", []):
    st.markdown(f"**Stap {s.get('n','')}**")
    st.write(s.get("text", ""))
    st.write("")

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
=======
# ---------------------------------------------------------
# IMPORTS (identiek aan stabiele app)
# ---------------------------------------------------------
# NB: Deze imports veronderstellen dezelfde modules
# als in de stabiele app. Pas hier niets aan.
from core.llm import call_peet
from core.json_utils import extract_json
from core.prompts import SYSTEM_PROMPT
from core.images import generate_image_if_needed
from core.pdf import render_pdf
from core.shopping_list import build_shopping_list

# ---------------------------------------------------------
# INPUT GATEWAY (VOORBEREID — NOG NIET ACTIEF)
# ---------------------------------------------------------
def input_gateway(query_params: dict) -> dict:
    """
    Leest input uit query params en normaliseert.
    LET OP: momenteel passief; we gebruiken defaults
    zodat gedrag identiek blijft aan de stabiele app.
    """
    # Defaults (identiek aan stabiele app)
    context = {
        "mode": "vandaag",
        "days": 1,
        "persons": 2,
        "time": "normaal",
        "moment": "doordeweeks",
        "preference": "peet",
        "kitchen": None,
        "fridge": [],
        "allergies": [],
        "nogo": [],
        "language": "nl",
    }

    # Voor later: hier kunnen we query_params mappen
    # zonder de engine of output te breken.

    return context

# ---------------------------------------------------------
# UI — IDENTIEK AAN STABIELE APP
# ---------------------------------------------------------
def render_ui():
    st.title("Peet kiest")
    st.caption("Rust in je hoofd. Eten zonder gedoe.")

    # (Laat dit blok identiek aan de stabiele app)
    with st.form("peet_form", clear_on_submit=False):
        persons = st.number_input("Voor hoeveel personen?", min_value=1, max_value=8, value=2)
        submit = st.form_submit_button("Laat Peet kiezen")

    return submit, persons

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    query_params = st.query_params

    # Input gateway (passief)
    context = input_gateway(query_params)

    # UI
    submit, persons = render_ui()
    context["persons"] = persons

    if submit:
        with st.spinner("Peet denkt even na…"):
            # Engine call (identiek)
            raw = call_peet(
                system_prompt=SYSTEM_PROMPT,
                context=context,
            )

            data = extract_json(raw)

        # Resultaat tonen (identiek)
        st.subheader(data.get("title", ""))
        st.write(data.get("description", ""))

        # Afbeelding (on-demand)
        generate_image_if_needed(data)

        # Boodschappenlijst
        shopping = build_shopping_list(data)
        st.markdown("### Boodschappenlijst")
        st.write(shopping)

        # PDF
        pdf_bytes = render_pdf(data, shopping)
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="peet_kiest.pdf",
            mime="application/pdf",
        )

# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    main()
>>>>>>> 2fb2802 (Add clean peet_dev app (no secrets))
