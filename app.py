# =========================================================
# STREAMLIT CLOUD IMPORT BOOTSTRAP (ALLEEN PAD-FIX)
# Doel: projectroot altijd in sys.path, zodat imports overal werken (Cloud + lokaal)
# =========================================================
import os
import sys
from pathlib import Path

def _bootstrap_project_root() -> None:
    # Dit bestand = C:\culinary_decision_suite\app.py
    # Root = map waar dit bestand in staat
    root = Path(__file__).resolve().parent

    # Werkdirectory gelijkzetten (helpt bij relatieve paden)
    try:
        os.chdir(root)
    except Exception:
        pass

    # Root vóóraan in sys.path (zodat "apps", "core", "shared", etc. gevonden worden)
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

_bootstrap_project_root()

import streamlit as st
from datetime import date

from peet_engine.context import build_context, build_context_text
from peet_engine.engine import plan
from core.llm import call_peet


# =========================================================
# Page config (MOET BOVENAAN)
# =========================================================
st.set_page_config(
    page_title="Peet kiest voor je",
    page_icon="🍳",
    layout="centered",
)


# =========================================================
# Query param helpers (Carrd → Streamlit)
# =========================================================
qp = st.query_params

def q(name, default=None):
    v = qp.get(name)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


# =========================================================
# Detect Carrd-start
# =========================================================
from_carrd = bool(q("days") or q("persons") or q("moment"))


# =========================================================
# Build raw_input (enige waarheid)
# =========================================================
raw_input = {
    "mode": "vooruit",
    "days": int(q("days", 1)),
    "persons": int(q("persons", 2)),
    "vegetarian": False,                 # Carrd stuurt dit nu niet mee
    "allergies": q("allergies", ""),
    "moment": q("moment", "doordeweeks"),
    "time": q("time", "normaal"),
    "ambition": 3,
    "language": "nl",
}

# Keuken is optioneel → alleen zetten als er iets is
kitchen = q("kitchen", "").strip()
if kitchen:
    raw_input["keuken"] = kitchen


# =========================================================
# UI
# =========================================================
st.title("Peet kiest voor je")
st.caption("Rustig. Zonder keuzestress. Ik kijk even met je mee.")


# =========================================================
# Run engine
# =========================================================
with st.spinner("Peet denkt even…"):
    # Stap 1 — Context (waarheid)
    ctx = build_context(raw_input)

    # Stap 2 — Context (betekenis)
    context_text = build_context_text(ctx)

    # Stap 3 — Dagplanning
    engine_choice = plan(ctx)

    # Stap 4 — User prompt bouwen
    first_day = engine_choice["days"][0]
    profile = first_day["profile"]

    BEREIDINGS_INTENTIE = {
        "licht": (
            "Houd de bereiding fris en overzichtelijk. "
            "Werk rustig, met weinig pannen en zonder haast."
        ),
        "vol": (
            "Geef iets meer aandacht aan opbouw en smaak. "
            "Neem de tijd, maar houd het toegankelijk."
        ),
        "afronding": (
            "Laat de bereiding comfortabel en ontspannen aanvoelen. "
            "Zacht, rond en geruststellend."
        ),
    }

    bereidings_hint = BEREIDINGS_INTENTIE.get(profile, "")

    days_block = []
    for d in engine_choice["days"]:
        days_block.append(
            f"Dag {d['day']}: {d['dish_name']} "
            f"({d['profile']}, ambitie {d['ambition']}). "
            f"Reden: {d['why']}"
        )

    days_text = "\n".join(days_block)

    user_prompt = f"""
De onderstaande gerechtnaam is vast en mag NIET worden aangepast.
Gebruik deze exact als titel in de output.

Titel (vast):
"{first_day['dish_name']}"

Geef naast de vaste titel één korte subtitel (max. 12 woorden).
De subtitel beschrijft keuken en sfeer, zonder nieuwe gerechtnaam.

Volg exact de onderstaande keuze van Peet.
Verzin geen ander gerecht.

{days_text}

Keuken:
{ctx.get("keuken", "vrij gekozen door Peet")}

De keuken beïnvloedt alleen:
- kruiden
- smaakmakers
- sauzen en afwerking

Het is toegestaan om hoofdcomponenten voor te stellen
(zoals granen, brood of peulvruchten),
mits ondersteunend en groente-gedreven.
Bij licht-profiel terughoudend.
Bij afronding-profiel iets meer comfort.

Bereidingsintentie:
{bereidings_hint}

Voor {ctx['persons']} personen.

Geef de output als JSON met exact deze keys:
- title
- subtitle
- meal_type
- ingredients
- steps

Schrijf de bereiding alsof Peet naast iemand in de keuken staat.
Rustig, warm, zonder stress.
Leg kort uit waarom je iets doet.

Sluit af met één korte Peet-zin.
Plaats die NA het JSON-object, niet erin.
""".strip()

    # Stap 5 — LLM
    result = call_peet(
        system_context=context_text,
        user_prompt=user_prompt,
    )


# =========================================================
# Render output
# =========================================================
st.markdown("### Vandaag doen we dit")
st.write(result)
