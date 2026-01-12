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
# IMPORTS CORE
# =========================================================
from core.prompts import PEET_KIEST_VOORUIT_PROMPT
from core.images import generate_dish_image_bytes

# =========================================================
# CONFIG
# =========================================================
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# =========================================================
# PAGE CONFIG (MOET ALS EERSTE)
# =========================================================
st.set_page_config(
    page_title="Peet Kiest – Vooruit",
    layout="centered"
)

# =========================================================
# ROUTER — MODE & EFFECTIVE DAYS (SLUITEND)
# =========================================================

query_params = st.query_params

def first_value(key):
    v = query_params.get(key)
    if isinstance(v, list) and v and v[0]:
        return v[0]
    return None

raw_mode = first_value("mode")
mode = raw_mode if raw_mode in ("vandaag", "vooruit") else "vooruit"

raw_days = first_value("days")
try:
    days = int(raw_days) if raw_days is not None else None
except Exception:
    days = None

if mode == "vandaag":
    effective_days = 1
else:
    effective_days = days if days in (2, 3, 5) else None

# ============================================================
# SESSION STATE — STABIELE DEFAULTS
# ============================================================

_defaults = {
    "people": 2,
    "veggie": False,
    "allergies": "",
    "result": None,
    "last_request_key": None,
}

for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# QUERY → STATE SYNC (ÉÉNMALIG PER URL)
# ============================================================

query_params = st.query_params

def _to_int(val, default):
    try:
        return int(val)
    except Exception:
        return default

def _clean_text(val):
    return val.strip() if isinstance(val, str) else ""

if st.session_state.result is None:
    if "people" in query_params:
        st.session_state.people = _to_int(
            query_params.get("people"), st.session_state.people
        )

    if "veggie" in query_params:
        st.session_state.veggie = query_params.get("veggie") == "checked"

    if "allergies" in query_params:
        st.session_state.allergies = _clean_text(
            query_params.get("allergies")
        )

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

# =========================================================
# INPUTS — BRON VAN WAARHEID = SESSION_STATE
# =========================================================
people = st.session_state.people
veggie = st.session_state.veggie
allergies = st.session_state.allergies

# ============================================================
# INPUTS → VALIDATION → REQUEST KEY (SLUITEND)
# ============================================================

people = st.session_state.people
veggie = st.session_state.veggie
allergies = st.session_state.allergies

inputs_ready = (
    isinstance(people, int)
    and people > 0
)

request_payload = {
    "days": effective_days,
    "people": people,
    "veggie": veggie,
    "allergies": allergies,
}

request_key = json.dumps(request_payload, sort_keys=True)

should_generate = (
    inputs_ready
    and request_key != st.session_state.last_request_key
)

# ============================================================
# BOVENBLOK — EVEN AFSTEMMEN (UI)
# ============================================================

st.subheader("Even afstemmen")

st.number_input(
    "Voor hoeveel personen?",
    min_value=1,
    max_value=6,
    step=1,
    key="people"
)

st.checkbox(
    "Ben je vegetarisch?",
    key="veggie"
)

st.text_input(
    "Allergieën of dingen die ik moet vermijden",
    key="allergies"
)
# ============================================================
# ACTIE — AUTO-RUN (DETERMINISTISCH)
# ============================================================

if should_generate:
    with st.spinner("Peet is aan het kiezen…"):
        context = json.dumps(request_payload)
        st.session_state.result = call_peet(context)
        st.session_state.last_request_key = request_key

# ============================================================
# RESULT — UIT SESSION HALEN (SLUITEND)
# ============================================================

result = st.session_state.get("result")

if not result:
    st.stop()

days_data = result.get("days")

if not isinstance(days_data, list) or not days_data:
    st.stop()

# =========================================================
# RESULT CARDS
# =========================================================

for day in days_data:
    with st.container(border=True):
        # Titel
        st.markdown(f"### Dag {day['day']}")
        st.markdown(f"**{day['screen8']['dish_name']}**")

        # Beschrijving
        if day.get("description"):
            st.markdown(day["description"])

        # Motivatie (rustig, ondergeschikt)
        if day.get("motivation"):
            st.caption(day["motivation"])

        # Afbeelding pas op expliciete actie
        if st.button(
            "Laat een foto zien",
            key=f"img_{day['day']}",
            use_container_width=True
        ):
            with st.spinner("Even zoeken…"):
                img = generate_dish_image_bytes(
                    day["screen8"]["dish_name"]
                )
                if img:
                    st.image(img, use_container_width=True)

    # Ruimte tussen cards
    st.markdown(
        "<div style='height: 1.5rem'></div>",
        unsafe_allow_html=True
    )




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
# PDF CARD
# =========================================================

with st.container(border=True):
    st.markdown("### Alles bij elkaar")

    if pdf_path:
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Bekijk recept & boodschappen (PDF)",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True
            )

