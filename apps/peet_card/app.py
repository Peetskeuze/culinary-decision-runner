# =========================================================
# PEET CARD — PRODUCTIE (lokaal)
# Carrd → Streamlit → Peet Engine → Render + PDF
# =========================================================

import sys
import json
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------
# PROJECT ROOT BOOTSTRAP
# ---------------------------------------------------------
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------
# ENGINE & RENDER IMPORTS
# ---------------------------------------------------------
from peet_engine.run import call_peet
from peet_engine.render_simple import render_plan
from peet_engine.render_pdf import build_plan_pdf

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Peet kiest. Jij hoeft alleen te koken.",
    page_icon="🍳",
    layout="centered",
)

st.title("Peet kiest. Jij hoeft alleen te koken.")
st.caption("Geen keuzestress. Geen gedoe.")

# ---------------------------------------------------------
# QUERY PARAMS
# ---------------------------------------------------------
qp = st.query_params


def get_param_str(key: str, default: str = "") -> str:
    return qp.get(key, default).strip() if key in qp else default


def get_param_int(key: str, default: int) -> int:
    try:
        return int(get_param_str(key, default))
    except Exception:
        return default


def get_param_list(key: str) -> list[str]:
    raw = get_param_str(key, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


# ---------------------------------------------------------
# INPUT
# ---------------------------------------------------------
days = get_param_int("days", 1)
persons = get_param_int("persons", 2)

time = get_param_str("time", "normaal")
moment = get_param_str("moment", "doordeweeks")
kitchen = get_param_str("kitchen", "")

fridge = get_param_list("fridge")
nogo = get_param_list("nogo")
allergies = get_param_list("allergies")

# ---------------------------------------------------------
# NORMALISATIE
# ---------------------------------------------------------
if days not in (1, 2, 3, 5):
    days = 2

persons = min(max(persons, 1), 8)
mode = "vooruit" if days > 1 else "vandaag"

# ---------------------------------------------------------
# CONTEXT
# ---------------------------------------------------------
context = {
    "mode": mode,
    "days": days,
    "persons": persons,
    "time": time,
    "moment": moment,
    "kitchen": kitchen or None,
    "fridge": fridge,
    "nogo": nogo,
    "allergies": allergies,
    "language": "nl",
}

context_json = json.dumps(context, ensure_ascii=False)

# ---------------------------------------------------------
# RUN → RENDER
# ---------------------------------------------------------
with st.spinner("Peet is aan het kiezen…"):
    result = call_peet(context_json)

render_plan(result)

# ---------------------------------------------------------
# PDF DOWNLOAD
# ---------------------------------------------------------
pdf_buffer = build_plan_pdf(result)

st.download_button(
    label="Download als PDF",
    data=pdf_buffer,
    file_name="Peet_kiest_menu.pdf",
    mime="application/pdf",
)
