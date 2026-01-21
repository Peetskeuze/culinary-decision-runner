# =========================================================
# PEET CARD — LOKAAL (STABIEL)
# Carrd → Streamlit → Peet Engine → Render + PDF
# =========================================================

import sys
from pathlib import Path
from datetime import datetime
import locale
import streamlit as st



# ---------------------------------------------------------
# LOCALE
# ---------------------------------------------------------
try:
    locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")
except Exception:
    pass

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------
# ENGINE IMPORTS
# ---------------------------------------------------------
from peet_engine.run import call_peet
from peet_engine.context import build_context, build_context_text
from peet_engine.render_pdf import build_plan_pdf

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Peet kiest. Jij hoeft alleen te koken.",
    page_icon="🍳",
    layout="centered",
)

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
# INPUT (UIT CARRD / URL)
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

# ---------------------------------------------------------
# CONTEXT — KEUZELOGICA (LEIDEND)
# ---------------------------------------------------------

if days == 1:
    # Vandaag = alles mag
    ctx = build_context({
        "mode": "vandaag",
        "days": 1,
        "persons": persons,
        "time": time,
        "moment": moment,
        "kitchen": kitchen,
        "fridge": fridge,
        "nogo": nogo,
        "allergies": allergies,
        "vegetarian": False,
        "language": "nl",
    })

else:
    # Vooruit = minimale input, Peet bepaalt
    ctx = build_context({
        "mode": "vooruit",
        "days": days,
        "persons": persons,
        "allergies": allergies,
        "nogo": nogo,
        "language": "nl",
    })


context_text = build_context_text(ctx)

# ---------------------------------------------------------
# TITEL
# ---------------------------------------------------------
if ctx["days"] == 1:
    st.title("Peet kiest. Jij hoeft alleen te koken.")
    st.caption("Vandaag geregeld.")
else:
    st.title(f"Peet plant vooruit · {ctx['days']} dagen")
    st.caption("Peet bewaakt balans en variatie.")

# ---------------------------------------------------------
# RUN ENGINE
# ---------------------------------------------------------
import json

with st.spinner("Peet is aan het kiezen…"):
    result = call_peet(
        json.dumps(ctx, ensure_ascii=False)
    )


# ---------------------------------------------------------
# RENDER RESULTAAT
# ---------------------------------------------------------
days_out = result.get("days", [])

for i, day in enumerate(days_out, start=1):
    if ctx["days"] > 1:
        st.markdown(f"## Dag {i}")

    st.markdown(f"### {day.get('dish_name', '')}")

    if day.get("why"):
        st.markdown(day["why"])

    if day.get("description"):
        st.markdown(day["description"])

    st.markdown("---")

# ---------------------------------------------------------
# PDF DOWNLOAD
# ---------------------------------------------------------
pdf_buffer = build_plan_pdf(result)

now = datetime.now()
weekday = now.strftime("%A").capitalize()
date_str = now.strftime("%d-%m-%Y")

if ctx["days"] == 1:
    pdf_name = f"Peet_koos_vandaag_{weekday}_{date_str}.pdf"
else:
    pdf_name = f"Peet_koos_{ctx['days']}_dagen_vooruit_vanaf_{date_str}.pdf"

st.download_button(
    label="Download als PDF",
    data=pdf_buffer,
    file_name=pdf_name,
    mime="application/pdf",
)
