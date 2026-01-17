# =========================================================
# BOOTSTRAP — fix imports for Streamlit Cloud
# =========================================================
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# =========================================================
# PAGE CONFIG — DEV
# =========================================================
st.set_page_config(
    page_title="Peet Card — DEV",
    page_icon="🧪",
)

st.warning("⚠️ DEV-versie (peet-card). Niet delen met testers.")
st.title("Peet Card — DEV input check")

# =========================================================
# QUERY PARAMS → NORMALISATIE
# =========================================================
qp = st.query_params

def get_param_str(key: str, default: str = "") -> str:
    return qp.get(key, [default])[0].strip()

def get_param_int(key: str, default: int) -> int:
    try:
        return int(get_param_str(key, default))
    except Exception:
        return default

def get_param_list(key: str) -> list[str]:
    raw = get_param_str(key, "")
    return [i.strip() for i in raw.split(",") if i.strip()]

# =========================================================
# PARSE INPUT (Carrd → Streamlit)
# =========================================================
context = {
    "days": get_param_int("days", 1),
    "persons": get_param_int("persons", 2),
    "time": get_param_str("time", "normaal"),
    "moment": get_param_str("moment", "doordeweeks"),
    "preference": get_param_str("preference", ""),
    "kitchen": get_param_str("kitchen", ""),
    "fridge": get_param_list("fridge"),
    "nogo": get_param_list("nogo"),
    "allergies": get_param_list("allergies"),
}

# =========================================================
# TONEN OP SCHERM — TESTFASE
# =========================================================
st.subheader("Ontvangen input vanuit Carrd")

st.write("Aantal dagen:", context["days"])
st.write("Aantal personen:", context["persons"])
st.write("Tijd / tempo:", context["time"])
st.write("Moment:", context["moment"])
st.write("Voorkeur:", context["preference"] or "—")
st.write("Keuken:", context["kitchen"] or "—")

st.write("Koelkast:", context["fridge"] or "—")
st.write("Niet toegestaan:", context["nogo"] or "—")
st.write("Allergieën:", context["allergies"] or "—")

st.divider()
st.caption("⬆️ Als dit klopt, is de Carrd → Streamlit koppeling stabiel.")
