# =========================================================
# PEET CARD — SCHONE APP
# Carrd → Streamlit → Peet Engine → Render + PDF
# =========================================================

import sys
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------
# PROJECT ROOT (voor Streamlit Cloud)
# ---------------------------------------------------------
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------
# ENGINE IMPORTS (ENIGE WAARHEID)
# ---------------------------------------------------------
from peet_engine.context import build_context
from peet_engine.run import call_peet
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
# INPUT — ALLEEN VIA URL (CARRD)
# ---------------------------------------------------------
query = st.query_params.to_dict()

if not query:
    st.error("Geen invoer ontvangen. Start Peet via de website.")
    st.stop()

# ---------------------------------------------------------
# CONTEXT — ENIGE PAD
# ---------------------------------------------------------
try:
    context = build_context(query)
except Exception:
    st.error("Ongeldige invoer. Gebruik de Peet-startpagina.")
    st.stop()

# ---------------------------------------------------------
# TITEL
# ---------------------------------------------------------
if context["days"] == 1:
    st.title("Peet kiest. Jij hoeft alleen te koken.")
    st.caption("Vandaag geregeld.")
else:
    st.title(f"Peet plant vooruit · {context['days']} dagen")
    st.caption("Peet bewaakt balans en variatie.")

# ---------------------------------------------------------
# RUN ENGINE
# ---------------------------------------------------------
with st.spinner("Peet is aan het kiezen…"):
    result = call_peet(context)

# ============================
# RESULTAAT RENDEREN (ALLE DAGEN)
# ============================

days = result.get("days", [])

if not days:
    st.error("Peet kon geen gerechten kiezen.")
else:
    for day in days:
        day_nr = day.get("day")
        dish_name = day.get("dish_name", "")
        why = day.get("why", "")

        st.markdown(f"## Dag {day_nr}")
        st.markdown(f"### {dish_name}")

        if why:
            st.markdown(why)

        st.markdown("---")


# ---------------------------------------------------------
# PDF DOWNLOAD
# ---------------------------------------------------------
pdf_buffer, pdf_filename = build_plan_pdf(result)

st.download_button(
    label="Download als PDF",
    data=pdf_buffer,
    file_name=pdf_filename,
    mime="application/pdf",
)
