# =========================================================
# Peet kiest voor je — hoofdapp (Streamlit)
# Optie 3: Invoer als default, Carrd als snelle launcher
# =========================================================

import sys
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------
# Project root bootstrap (Cloud + lokaal)
# ---------------------------------------------------------
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------
# Imports (na bootstrap)
# ---------------------------------------------------------
from peet_engine.context import build_context, build_context_text
from peet_engine.engine import plan
from core.llm import call_peet

def is_dev():
    try:
        host = st.runtime.scriptrunner.get_script_run_ctx().request.host
        return "localhost" in host or "127.0.0.1" in host
    except Exception:
        return False

# ---------------------------------------------------------
# Page config (MOET bovenaan)
# ---------------------------------------------------------
st.title("Peet kiest voor je")

if is_dev():
    st.caption("🧪 DEV — lokale versie")

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
qp = st.query_params

def q(name, default=None):
    v = qp.get(name)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default

from_carrd = bool(q("days") or q("persons") or q("moment"))

# ---------------------------------------------------------
# Titel
# ---------------------------------------------------------
st.title("Peet kiest voor je")
st.caption("Rustig. Zonder keuzestress. Ik kijk even met je mee.")

# ---------------------------------------------------------
# Invoer (alleen tonen als we NIET via Carrd komen)
# ---------------------------------------------------------
if not from_carrd:
    st.markdown("### Even afstemmen")

    persons = st.number_input(
        "Voor hoeveel personen?",
        min_value=1,
        max_value=8,
        value=2,
        step=1,
    )

    days = st.selectbox(
        "Voor hoeveel dagen?",
        options=[1, 2, 3, 5],
        index=0,
    )

    moment = st.selectbox(
        "Wanneer?",
        options=["doordeweeks", "weekend"],
        index=0,
    )

    run = st.button("Laat Peet kiezen")

    if not run:
        st.stop()

else:
    # Carrd → defaults + params
    persons = int(q("persons", 2))
    days = int(q("days", 1))
    moment = q("moment", "doordeweeks")

# ---------------------------------------------------------
# Build raw_input (enige waarheid)
# ---------------------------------------------------------
raw_input = {
    "mode": "vooruit" if days > 1 else "vandaag",
    "days": days,
    "persons": persons,
    "vegetarian": False,
    "allergies": q("allergies", ""),
    "moment": moment,
    "time": q("time", "normaal"),
    "ambition": 3,
    "language": "nl",
}

kitchen = q("kitchen", "").strip()
if kitchen:
    raw_input["keuken"] = kitchen

# ---------------------------------------------------------
# Engine run
# ---------------------------------------------------------
with st.spinner("Peet denkt even…"):
    ctx = build_context(raw_input)
    context_text = build_context_text(ctx)
    engine_choice = plan(ctx)

    first_day = engine_choice["days"][0]

    result = call_peet(context_text)

# ---------------------------------------------------------
# Presentatie (GEEN JSON dump)
# ---------------------------------------------------------
st.markdown("### Vandaag doen we dit")

if isinstance(result, dict):
    st.subheader(result.get("title", ""))

    subtitle = result.get("subtitle")
    if subtitle:
        st.caption(subtitle)

    st.markdown("**Ingrediënten**")
    for i in result.get("ingredients", []):
        st.write(f"• {i}")

    st.markdown("**Zo pakken we het aan**")
    for idx, step in enumerate(result.get("steps", []), start=1):
        st.write(f"{idx}. {step}")

else:
    # fallback — mag eigenlijk niet meer voorkomen
    st.write(result)
