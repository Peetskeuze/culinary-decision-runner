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
# SESSION STATE INIT — VERPLICHT VOOR EERSTE RUN
# =========================================================

if "last_request_key" not in st.session_state:
    st.session_state.last_request_key = None

if "result" not in st.session_state:
    st.session_state.result = None

# ============================================================
# UI — GROTERE SPINNERTEKST
# ============================================================

st.markdown(
    """
    <style>
    /* Spinner tekst */
    div[data-testid="stSpinner"] > div > div {
        font-size: 1.8rem;      /* pas aan: 1.2 / 1.4 / 1.6 */
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#
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
        temperature=0.2,
        input=[
            {
                "role": "system",
                "content": PEET_KIEST_VOORUIT_PROMPT.strip()
            },
            {
                "role": "user",
                "content": context
            }
        ]
    )

    return _extract_json(resp.output_text)

# ============================================================
# CARRD → QUERY PARAMS (ROBUST) + AUTO-RUN (NOOIT WIT SCHERM)
# ============================================================

st.title("Peet is aan het kiezen")
st.write("We hebben meer dan 1 miljoen recepten, dus het kan ff duren. Geen stress, Peet regelt het.")

params = st.query_params

def _first(key: str, default: str) -> str:
    """
    Streamlit kan query params als str of als list[str] teruggeven.
    Deze helper pakt altijd de 'eerste' waarde.
    """
    v = params.get(key, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default

# --- Days (Carrd: days) ---
# Carrd stuurt days=2|3|5. Als days ontbreekt: default 2.
try:
    days_from_query = int(_first("days", "2"))
except Exception:
    days_from_query = 2

# Normaliseer days alvast
if days_from_query not in (1, 2, 3, 5):
    days_from_query = 2

# --- Mode ---
# We willen GEEN verplichte mode. Als mode ontbreekt: afleiden op basis van days.
mode_raw = _first("mode", "").strip().lower()
if mode_raw in ("vandaag", "vooruit"):
    mode = mode_raw
else:
    mode = "vooruit" if days_from_query in (2, 3, 5) else "vandaag"

# Effective days — leidend op days uit query
try:
    days = int(days_from_query)
except Exception:
    days = 2

if days not in (1, 2, 3, 5):
    days = 2

# --- People (Carrd: persons) ---
try:
    people = int(_first("persons", "2"))
except Exception:
    people = 2
people = max(1, min(10, people))

# --- Veggie (Carrd: vegetarian) ---
# Carrd checkbox kan o.a. "checked" of "on" sturen.
veggie_raw = _first("vegetarian", "false").strip().lower()
veggie = veggie_raw in ("true", "1", "yes", "y", "on", "checked")

# --- Allergies (Carrd: allergies) ---
allergies = _first("allergies", "").strip()

# ============================================================
# SESSION STATE = ENIGE BRON VAN WAARHEID
# ============================================================

st.session_state.mode = mode
st.session_state.days = days
st.session_state.people = people
st.session_state.veggie = veggie
st.session_state.allergies = allergies

request_key = json.dumps(
    {
        "mode": st.session_state.mode,
        "days": st.session_state.days,
        "people": st.session_state.people,
        "veggie": st.session_state.veggie,
        "allergies": st.session_state.allergies,
    },
    sort_keys=True
)

# Alleen opnieuw genereren als de request echt anders is
if st.session_state.last_request_key != request_key:
    st.session_state.result = None
    st.session_state.last_request_key = request_key

# ============================================================
# AUTO-RUN: als er nog geen resultaat is -> call_peet
# ============================================================

if st.session_state.result is None:
    try:
        with st.spinner("Peet is aan het kiezen…"):
            context = json.dumps(
                {
                    "mode": st.session_state.mode,
                    "days": st.session_state.days,
                    "people": st.session_state.people,
                    "veggie": st.session_state.veggie,
                    "allergies": st.session_state.allergies,
                },
                ensure_ascii=False
            )
            st.session_state.result = call_peet(context)
    except Exception as e:
        msg = str(e)
        if "insufficient_quota" in msg or "429" in msg:
            st.error("Ik kan nu even geen keuze maken omdat de API-limiet op is. Probeer later opnieuw.")
        elif "api_key" in msg.lower() or "authentication" in msg.lower():
            st.error("De app kan OpenAI niet gebruiken: check je Streamlit Secrets (OPENAI_API_KEY).")
        else:
            st.error("Er ging iets mis bij het kiezen. Probeer nog een keer.")
        with st.expander("Technische info (handig voor debug)", expanded=False):
            st.write("Query params:")
            st.write(dict(params))
            st.write("Foutmelding:")
            st.write(msg)
        st.stop()

# ============================================================
# RESULT VALIDATIE (NOOIT STIL STOPPEN)
# ============================================================

result = st.session_state.get("result")
if not isinstance(result, dict):
    st.error("Ik kreeg geen bruikbaar resultaat terug. Probeer nog eens.")
    with st.expander("Technische info", expanded=False):
        st.write(result)
    st.stop()

days_data = result.get("days")
if not isinstance(days_data, list) or not days_data:
    st.error("Ik kreeg een resultaat terug, maar niet in het verwachte formaat.")
    with st.expander("Technische info (resultaat)", expanded=False):
        st.json(result)
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

