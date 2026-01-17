# =========================================================
# BOOTSTRAP — Streamlit Cloud safe
# =========================================================
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# =========================================================
# APP CONFIG — DEV
# =========================================================
st.set_page_config(
    page_title="Peet Card — DEV",
    page_icon="🧪",
)

st.warning("⚠️ DEV-versie (peet-card). Niet delen met testers.")
st.title("Peet Card — DEV input check")

# =========================================================
# QUERY PARAMS (nieuw API)
# =========================================================
qp = st.query_params

def get_param_str(key, default=""):
    return qp.get(key, default).strip() if key in qp else default

def get_param_int(key, default):
    try:
        return int(get_param_str(key, default))
    except Exception:
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
# OUTPUT — CHECK
# =========================================================
st.subheader("Ontvangen input vanuit Carrd")

st.write("Aantal dagen:", days)
st.write("Aantal personen:", persons)
st.write("Tijd / tempo:", time)
st.write("Moment:", moment)
st.write("Voorkeur:", preference or "—")
st.write("Keuken:", kitchen or "—")

st.write("Koelkast:", fridge if fridge else "—")
st.write("Niet toegestaan:", nogo if nogo else "—")
st.write("Allergieën:", allergies if allergies else "—")

st.divider()
st.caption("⬆️ Als dit klopt, is de Carrd → Streamlit koppeling stabiel.")
