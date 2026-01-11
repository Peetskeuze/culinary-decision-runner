import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import os
import json
import re
import base64
from io import BytesIO
from datetime import date

import streamlit as st
from openai import OpenAI

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# =========================================================
# PAGE CONFIG (MOET ALS EERSTE)
# =========================================================
st.set_page_config(
    page_title="Peet Kiest – Vooruit",
    layout="centered"
)

# =========================================================
# QUERY PARAMS (DAYS UIT CARRD)
# =========================================================
query_params = st.query_params

try:
    days_from_query = int(query_params.get("days", ["1"])[0])
except Exception:
    days_from_query = 1

if days_from_query not in (1, 2, 3, 5):
    days_from_query = 1

# =========================================================
# GLOBAL STYLING (TYPOGRAFIE & LAYOUT)
# =========================================================
st.markdown("""
<style>
.block-container { max-width: 680px; padding-top: 2.5rem; padding-bottom: 3rem; }
html, body, [class*="css"] { font-size: 17px; line-height: 1.55; }
h1 { font-size: 1.9rem; font-weight: 600; margin-bottom: 0.9rem; }
h2 { font-size: 1.4rem; font-weight: 600; margin-top: 2.2rem; margin-bottom: 0.6rem; }
h3 { font-size: 1.1rem; font-weight: 600; margin-top: 1.6rem; }
p { margin-bottom: 1.1rem; }
.stButton > button { width: 100%; padding: 0.75rem; font-size: 1rem; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# IMPORTS CORE
# =========================================================
from core.prompts import PEET_KIEST_VOORUIT_PROMPT

# =========================================================
# CONFIG
# =========================================================
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================================================
# SESSION STATE
# =========================================================
_defaults = {
    "result": None,
    "dish_image_bytes": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# HELPERS
# =========================================================
def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Geen JSON gevonden in model-output.")
    return json.loads(text[start:end + 1])

def call_peet(context: str) -> dict:
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": PEET_KIEST_VOORUIT_PROMPT},
            {"role": "user", "content": context},
        ],
    )
    return _extract_json(resp.output_text)

def generate_dish_image_bytes(dish_name: str) -> bytes | None:
    try:
        img = client.images.generate(
            model="gpt-image-1",
            prompt=(
                f"Fotografisch realistisch gerecht: {dish_name}. "
                "Warm natuurlijk licht, thuiskeuken, op een bord. "
                "Geen tekst, geen mensen, geen handen, geen props."
            ),
            size="1024x1024",
        )
        return base64.b64decode(img.data[0].b64_json)
    except Exception:
        return None

# =========================================================
# UI – HEADER
# =========================================================
st.title("Peet Kiest – Vooruit")
st.caption("Meerdere dagen geregeld. Geen planning. Geen stress.")

# =========================================================
# FORM
# =========================================================
with st.form("context"):
    days = st.selectbox(
        "Voor hoeveel dagen zal ik kiezen?",
        [1, 2, 3, 4, 5],
        index=0
    )

    people = st.number_input("Hoeveel mensen schuiven er aan?", min_value=1, max_value=10, value=2)

    veggie = st.selectbox(
        "Wil je vegetarisch eten?",
        ["Nee, laat Peet kiezen", "Ja, vegetarisch"],
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
        "Heb je al iets in huis waar ik rekening mee kan houden?"
        " Of wat je misschien hartstikke lekker vindt? ",
        placeholder="Bijvoorbeeld prei, kip, feta…"
    )

    no_gos = st.text_input(
        "Is er iets dat ik beter niet kan gebruiken?",
        placeholder="Allergie of liever niet…"
    )

    submitted = st.form_submit_button("Peet, neem het over")

# =========================================================
# SUBMIT & CALL PEET
# =========================================================

if submitted:
    # reset vorige run
    st.session_state.result = None

    today = date.today().isoformat()

    context = f"""
DATUM: {today}
AANTAL DAGEN: {days}
AANTAL PERSONEN: {people}
STANDAARD TIJD: 30 minuten
KEUKENVOORKEUR: {keuken if keuken else "Peet bepaalt"}
OPTIONEEL INGREDIËNT: {extra_ingredient}
NO-GOS: {no_gos}
""".strip()

    st.markdown("**Goed. Ik regel dit voor je.**")

    with st.spinner("Peet zet het voor je klaar…"):
        try:
            st.session_state.result = call_peet(context)
        except Exception as e:
            st.error("Peet raakte even de draad kwijt. Probeer het opnieuw.")
            st.caption(f"Debug: {e}")
            st.stop()


# =========================================================
# RESULT UIT SESSION HALEN
# =========================================================

result = st.session_state.get("result")

if result is None:
    st.stop()

days_data = result.get("days", [])


# =========================================================
# RESULT WEERGEVEN OP SCHERM
# =========================================================

for day in days_data:
    st.markdown(f"## Dag {day['day']}")
    st.markdown(f"**{day['screen8']['dish_name']}**")

    if day.get("description"):
        st.markdown(day["description"])

    if day.get("motivation"):
        st.caption(day["motivation"])

    if st.button(f"Laat een foto zien (Dag {day['day']})", key=f"img_{day['day']}"):
        with st.spinner("Even zoeken…"):
            img = generate_dish_image_bytes(day["screen8"]["dish_name"])
            if img:
                st.image(img, width="stretch")

    st.divider()


# =========================================================
# PDF MAKEN – FUNCTIES
# =========================================================

def build_vooruit_pdf(days_data):
    pdf_days = []

    for day in days_data:
        pdf_days.append({
            "day": day["day"],
            "dish_name": day["screen8"]["dish_name"],
            "ingredient_groups": day["recipe"]["ingredient_groups"],
            "steps": day["recipe"]["steps"],
        })

    return {
        "title": "Peet Kiest – Vooruit",
        "date": date.today().isoformat(),
        "days": pdf_days,
    }


def build_combined_shopping_list(days_data):
    # vaste winkelcategorieën (volgorde = winkel-logica)
    categories = {
        "Groente & fruit": set(),
        "Vlees, vis & vega": set(),
        "Zuivel & eieren": set(),
        "Kruiden, sauzen & olie": set(),
        "Houdbaar": set(),
        "Overig": set(),
    }

    keyword_map = {
        "Groente & fruit": [
            "ui", "knoflook", "prei", "paprika", "tomaat", "wortel",
            "courgette", "aubergine", "spinazie", "sla", "citroen",
            "citroensap", "doperwt", "boon", "broccoli", "bloemkool",
            "venkel", "appel", "krieltjes", "aardappel", "kruimige",
            "peterselie", "dille", "boerenkool", "champignons", "bleekselderij"
        ],
        "Vlees, vis & vega": [
            "kip", "gehakt", "rund", "varken", "worst", "braadworst",
            "vis", "zalm", "tonijn", "tofu", "tempeh", "vega"
        ],
        "Zuivel & eieren": [
            "melk", "room", "kaas", "yoghurt", "boter", "ei", "eieren"
        ],
        "Kruiden, sauzen & olie": [
            "olie", "olijfolie", "zout", "peper", "mosterd",
            "kerrie", "paprika", "komijn", "saus",
            "sojasaus", "azijn", "nootmuskaat"
        ],
        "Houdbaar": [
            "pasta", "rijst", "couscous", "bulgur", "linzen",
            "bonen", "tomatenblok", "bouillon", "blik",
            "bloem"
        ],
    }

    def normalize(item: str) -> str:
        return item.lower().strip()

    def map_category(item: str) -> str:
        item_lc = normalize(item)
        for cat, keywords in keyword_map.items():
            if any(k in item_lc for k in keywords):
                return cat
        return "Overig"

    for day in days_data:
        for grp in day["recipe"]["ingredient_groups"]:
            for item in grp.get("items", []):
                cat = map_category(item)
                categories[cat].add(item)

    # Overig alleen tonen als er écht iets in zit
    return {
        cat: sorted(items)
        for cat, items in categories.items()
        if items and not (cat == "Overig" and len(items) == 0)
    }


def render_vooruit_pdf(pdf_data, shopping_list):
    from reportlab.lib.utils import simpleSplit

    output_dir = "output/peet_kiest_vooruit"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"Peet_Kiest_Vooruit_{date.today().strftime('%Y%m%d')}.pdf"
    path = os.path.join(output_dir, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # ===============================
    # PER DAG: ELK GERECHT OP EIGEN PAGINA
    # ===============================
    for idx, day in enumerate(pdf_data["days"]):

        # Vanaf dag 2 pas een nieuwe pagina
        if idx > 0:
            c.showPage()

        y = height - 40

        # Dagkop
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, f"Dag {day['day']} – {day['dish_name']}")
        y -= 30

        # Ingrediënten
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Ingrediënten")
        y -= 18

        c.setFont("Helvetica", 10)
        for grp in day["ingredient_groups"]:
            c.drawString(50, y, grp["name"])
            y -= 14
            for it in grp["items"]:
                c.drawString(65, y, f"- {it}")
                y -= 12
            y -= 6

        y -= 10

        # Bereiding
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Bereiding")
        y -= 18

        c.setFont("Helvetica", 10)
        max_width = width - 90
        line_height = 12

        for step in day["steps"]:
            lines = simpleSplit(step["text"], "Helvetica", 10, max_width)
            for line in lines:
                c.drawString(50, y, line)
                y -= line_height
            y -= 8

    # ===============================
    # BOODSCHAPPENLIJST OP EIGEN PAGINA
    # ===============================
    c.showPage()
    y = height - 40

    c.setFont("Helvetica-Bold", 15)
    c.drawString(40, y, "Gecombineerde boodschappenlijst")
    y -= 30

    c.setFont("Helvetica", 10)
    for grp, items in shopping_list.items():
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, grp)
        y -= 16

        c.setFont("Helvetica", 10)
        for it in items:
            c.drawString(55, y, f"- {it}")
            y -= 12

            if y < 120:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 10)

        y -= 12

    c.save()
    return path

# =========================================================
# PDF DATA BOUWEN (TOP-LEVEL)
# =========================================================

pdf_data = build_vooruit_pdf(days_data)
shopping_list = build_combined_shopping_list(days_data)
pdf_path = render_vooruit_pdf(pdf_data, shopping_list)


# =========================================================
# PDF DOWNLOAD KNOP (TOP-LEVEL)
# =========================================================

if pdf_path:
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="Bekijk recept & boodschappen (PDF)",
            data=f,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf"
        )
