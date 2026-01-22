import sys
from pathlib import Path

# Zorg dat project-root op sys.path staat (voor Streamlit Cloud)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from datetime import datetime

from peet_engine.run import call_peet
from peet_engine.render_pdf import build_plan_pdf

# -------------------------------------------------
# Input reduction – Peet-Card
# -------------------------------------------------

def reduce_input(raw: dict) -> dict:
    """
    Reduce raw input (query params / form input) to the explicit
    input contract for Peet-Card.

    - Drops all unknown keys
    - Enforces today vs forward separation
    - Applies minimal, explicit defaults only
    """

    if not isinstance(raw, dict):
        raise ValueError("Input must be a dict")

    mode = raw.get("mode")

    if mode not in ("today", "forward"):
        raise ValueError("Invalid or missing mode")

    reduced = {"mode": mode}

    if mode == "today":
        allowed = {
            "persons",
            "moment",
            "time",
            "vegetarian",
            "allergies",
            "nogo",
            "ambition",
            "language",
        }

        for key in allowed:
            if key in raw:
                reduced[key] = raw[key]

        # minimal defaults
        reduced.setdefault("vegetarian", False)
        reduced.setdefault("language", "nl")

    elif mode == "forward":
        allowed = {
            "days",
            "persons",
            "vegetarian",
            "allergies",
        }

        for key in allowed:
            if key in raw:
                reduced[key] = raw[key]

        # minimal defaults
        reduced.setdefault("vegetarian", False)

        if "days" not in reduced:
            raise ValueError("Forward mode requires 'days'")

        if reduced["days"] not in (2, 3, 5):
            raise ValueError("Forward mode allows only 2, 3 or 5 days")

    return reduced

# =========================================================
# Helpers
# =========================================================
def _qp_get(name: str, default: str | None = None) -> str | None:
    """
    Streamlit query params can be str or list[str] depending on version.
    Normalize to a single string.
    """
    qp = st.query_params
    if name not in qp:
        return default
    val = qp.get(name)
    if isinstance(val, list):
        return val[0] if val else default
    return val if val is not None else default


def _to_int(val: str | None, default: int) -> int:
    try:
        return int(str(val).strip())
    except Exception:
        return default


def _to_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "y", "on", "ja"):
        return True
    if v in ("0", "false", "no", "n", "off", "nee"):
        return False
    return default


def _to_list(val: str | None) -> list[str]:
    if not val:
        return []
    parts = [p.strip().lower() for p in str(val).split(",")]
    return [p for p in parts if p]


def _effective_days() -> int:
    """
    Contract:
    - days=1 => vandaag
    - days in (2,3,5) => vooruit
    - alles anders => 1
    """
    days_raw = _qp_get("days", "1")
    days = _to_int(days_raw, 1)
    if days in (2, 3, 5):
        return days
    return 1

# =========================================================
# Variatie-seed (Stap 1)
# =========================================================
def _variation_seed(days: int) -> int:
    """
    Zorgt voor gecontroleerde variatie.
    - 1 dag: veel variatie (tijd-gebaseerd)
    - 2/3/5 dagen: stabiel per dag, maar wisselt per kalenderdag
    """
    now = datetime.now()

    if days == 1:
        # verandert elke run / refresh
        return int(now.timestamp())

    # vooruit: elke dag andere seed, maar stabiel binnen die dag
    return int(now.strftime("%Y%m%d"))


def _build_context() -> dict:
    days = _effective_days()
    mode = "vooruit" if days in (2, 3, 5) else "vandaag"

    variation_seed = _variation_seed(days)

    persons = _to_int(_qp_get("persons", "2"), 2)
    persons = max(1, min(12, persons))

    vegetarian = _to_bool(_qp_get("vegetarian", None), False)
    allergies = _to_list(_qp_get("allergies", ""))

    # 2/3/5 dagen: alleen contractvelden doorgeven, rest negeren
    if mode == "vooruit":
        language = (_qp_get("language", "nl") or "nl").lower()
        if language not in ("nl", "en"):
            language = "nl"

        return {
            "mode": "vooruit",
            "days": days,
            "persons": persons,
            "vegetarian": vegetarian,
            "allergies": allergies,
            "language": language,
            "variation_seed": variation_seed,
}


    # 1 dag: alles mag mee
    moment = (_qp_get("moment", "doordeweeks") or "doordeweeks").lower()
    time = (_qp_get("time", "normaal") or "normaal").lower()
    ambition = _to_int(_qp_get("ambition", "2"), 2)
    ambition = max(1, min(4, ambition))

    language = st.query_params.get("language", "nl").lower()
    if language not in ("nl", "en"):
        language = "nl"

    # Extra velden (engine mag ze negeren, maar app accepteert ze)
    preference = _qp_get("preference", "")
    kitchen = _qp_get("kitchen", "")
    fridge = _qp_get("fridge", "")
    nogo = _qp_get("nogo", "")

    return {
        "mode": "vandaag",
        "days": 1,
        "persons": persons,
        "vegetarian": vegetarian,
        "allergies": allergies,
        "moment": moment,
        "time": time,
        "ambition": ambition,
        "language": language,
        "preference": preference,
        "kitchen": kitchen,
        "fridge": fridge,
        "nogo": nogo,
        "variation_seed": variation_seed,
    }

# =========================================================
# UI
# =========================================================
st.set_page_config(page_title="Peet kiest", page_icon="🍽️", layout="centered")

# -------------------------------------------------
# Enforced input flow (contract → reduction → normalize → context)
# -------------------------------------------------

# 1) Rauwe input verzamelen (query params)
raw_input = {
    "mode": "forward" if _effective_days() in (2, 3, 5) else "today",
    "days": _effective_days(),
    "persons": _to_int(_qp_get("persons", "2"), 2),
    "vegetarian": _to_bool(_qp_get("vegetarian", None), False),
    "allergies": _to_list(_qp_get("allergies", "")),
    "moment": _qp_get("moment", None),
    "time": _qp_get("time", None),
    "ambition": _to_int(_qp_get("ambition", None), 2),
    "language": (_qp_get("language", "nl") or "nl").lower(),
    "nogo": _qp_get("nogo", None),
}

# 2) Reduceren naar expliciet contract
try:
    reduced_input = reduce_input(raw_input)
except ValueError as e:
    st.error(str(e))
    st.stop()

# 3) Normalisatie (alleen op gereduceerde input)
normalized_input = normalize_input(reduced_input)

# 4) Context bouwen (engine ziet NOOIT raw input)
ctx = build_context(normalized_input)

days = ctx.get("days", 1)

if days == 1:
    st.title("Peet kiest. Jij hoeft alleen te koken.")
    st.caption("Vandaag geregeld.")
else:
    st.title(f"Peet plant vooruit · {days} dagen")
    st.caption("Peet bewaakt balans en variatie.")

with st.spinner("Peet is aan het kiezen…"):
    result = call_peet(ctx)

days_out = result.get("days", [])
if not days_out:
    st.error("Geen dagen gevonden in engine-output.")
    st.stop()

# Resultaten
for d in days_out:
    day_nr = d.get("day")
    if days > 1 and day_nr:
        st.subheader(f"Dag {day_nr}")
    dish = d.get("dish_name") or "Onbekend gerecht"
    st.markdown(f"### {dish}")
    why = d.get("why")
    if why:
        st.write(why)
    desc = d.get("description")
    if desc:
        st.write(desc)

    st.divider()

# PDF
try:
    pdf_out = build_plan_pdf(result)

    if isinstance(pdf_out, tuple) and len(pdf_out) == 2:
        pdf_buffer, pdf_filename = pdf_out
    else:
        pdf_buffer = pdf_out
        today = datetime.now().strftime("%d-%m-%Y")
        pdf_filename = f"Peet_plan_{today}.pdf"

    st.download_button(
        label="Download als PDF",
        data=pdf_buffer.getvalue(),
        file_name=pdf_filename,
        mime="application/pdf",
        use_container_width=False,
    )
except Exception as e:
    st.error(f"PDF maken ging mis: {e}")
