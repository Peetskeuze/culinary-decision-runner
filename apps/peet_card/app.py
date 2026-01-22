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
    Reduce raw input to an explicit, mode-dependent contract.
    - days == 1 (vandaag): ALLE relevante velden mogen mee
    - days > 1 (vooruit): ALLEEN persons, allergies, nogo
    """
    if "days" not in raw:
        raise ValueError("days ontbreekt")

    days = int(raw["days"])

    # -----------------------------
    # TODAY (days == 1)
    # -----------------------------
    if days == 1:
        allowed = {
            "mode",
            "days",
            "persons",
            "vegetarian",
            "preference",
            "kitchen",
            "fridge",
            "time",
            "moment",
            "ambition",
            "allergies",
            "nogo",
            "language",
        }

    # -----------------------------
    # FORWARD (days > 1)
    # -----------------------------
    else:
        allowed = {
            "mode",
            "days",
            "persons",
            "allergies",
            "nogo",
            "language",
        }

    reduced = {}
    for key in allowed:
        if key in raw and raw[key] not in (None, "", []):
            reduced[key] = raw[key]

    return reduced

# -------------------------------------------------
# Input normalization – Peet-Card
# -------------------------------------------------

def normalize_input(data: dict) -> dict:
    """
    Normalize reduced input to strict, engine-safe types.

    Guarantees:
    - ints are ints
    - bools are bools
    - lists are list[str]
    - language is 'nl' or 'en'
    """

    out: dict = {}

    # mode
    out["mode"] = data["mode"]

    # days
    if "days" in data:
        try:
            days = int(data["days"])
        except Exception:
            raise ValueError("days must be an integer")

        if days not in (1, 2, 3, 5):
            raise ValueError("days must be 1, 2, 3 or 5")

        out["days"] = days
    else:
        out["days"] = 1

    # persons
    try:
        persons = int(data.get("persons", 1))
    except Exception:
        raise ValueError("persons must be an integer")

    if persons < 1 or persons > 12:
        raise ValueError("persons must be between 1 and 12")

    out["persons"] = persons

    # vegetarian
    out["vegetarian"] = bool(data.get("vegetarian", False))

    # allergies / nogo
    def _norm_list(val) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip().lower() for v in val if str(v).strip()]
        if isinstance(val, str):
            return [v.strip().lower() for v in val.split(",") if v.strip()]
        raise ValueError("list fields must be list[str] or comma-separated string")

    if "allergies" in data:
        out["allergies"] = _norm_list(data.get("allergies"))
    else:
        out["allergies"] = []

    if "nogo" in data:
        out["nogo"] = _norm_list(data.get("nogo"))
    else:
        out["nogo"] = []

    # language
    language = str(data.get("language", "nl")).lower()
    if language not in ("nl", "en"):
        language = "nl"
    out["language"] = language

    # optional today-only fields
    if data["mode"] == "today":
        if "moment" in data:
            out["moment"] = str(data["moment"]).lower()
        if "time" in data:
            out["time"] = str(data["time"]).lower()
        if "ambition" in data:
            try:
                ambition = int(data["ambition"])
            except Exception:
                raise ValueError("ambition must be an integer")

            if ambition < 1 or ambition > 4:
                raise ValueError("ambition must be between 1 and 4")

            out["ambition"] = ambition

    return out
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


def build_context_from_query(query: dict) -> dict:
    """
    Keihard inputcontract voor Peet-Card.
    - days == 1  → vandaag: alles telt mee
    - days > 1   → vooruit: alleen persons, allergies, nogo
    """

    def clean_list(value: str) -> list:
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    # --- verplichte basis ---
    days = int(query.get("days", 1))
    persons = int(query.get("persons", 2))
    allergies = clean_list(query.get("allergies", ""))
    nogo = clean_list(query.get("nogo", ""))

    # =========================
    # DAG = VANDAAG
    # =========================
    if days == 1:
        context = {
            "mode": "today",
            "days": 1,
            "persons": persons,
            "allergies": allergies,
            "nogo": nogo,

            # alles mag meetellen
            "time": query.get("time"),
            "moment": query.get("moment"),
            "preference": query.get("preference"),
            "kitchen": query.get("kitchen"),
            "fridge": clean_list(query.get("fridge", "")),
            "ambition": int(query.get("ambition", 3)),
        }

        # expliciet verwijderen wat None is
        return {k: v for k, v in context.items() if v not in (None, "", [])}

    # =========================
    # DAG = VOORUIT
    # =========================
    context = {
        "mode": "forward",
        "days": days,
        "persons": persons,
        "allergies": allergies,
        "nogo": nogo,
    }

    return context

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

# 4) Context doorgeven aan engine (engine is leidend)
ctx = normalized_input

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
