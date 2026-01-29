# -------------------------------------------------
# Peet-Card — Vandaag (cleaned architecture)
# -------------------------------------------------

import sys
import json
import hashlib
from pathlib import Path
import os
import streamlit as st

# -------------------------------------------------
# Bootstrap project root (local + cloud)
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -------------------------------------------------
# Imports
# -------------------------------------------------
from core.llm import call_peet_text
from peet_engine.engine import plan
from peet_engine.render_pdf import build_plan_pdf


# -------------------------------------------------
# Query helpers
# -------------------------------------------------
def qp(name: str, default=""):
    v = st.query_params.get(name, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


def to_int(val, default):
    try:
        return int(str(val).strip())
    except Exception:
        return default


def to_list(val):
    if not val:
        return []
    return [p.strip().lower() for p in str(val).split(",") if p.strip()]


# -------------------------------------------------
# Context builder (vrije Peet-stijl)
# -------------------------------------------------
def build_llm_context():

    days = to_int(qp("days", "1"), 1)
    if days in (2, 3, 5):
        return "__FORWARD__"

    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))

    moment = qp("moment")
    kitchen = qp("kitchen")
    preference = qp("preference")
    vegetarian = qp("vegetarian")

    allergies = to_list(qp("allergies"))
    nogo = to_list(qp("nogo"))

    lines = [
        "CONTEXT VANDAAG:",
        f"- persons: {persons}",
    ]

    if moment:
        lines.append(f"- moment: {moment}")

    if kitchen:
        lines.append(f"- kitchen (inspiratie): {kitchen}")

    if preference:
        lines.append(f"- preference (inspiratie): {preference}")

    if vegetarian:
        lines.append(f"- vegetarian: {vegetarian}")

    if allergies:
        lines.append(f"- allergies: {', '.join(allergies)}")

    if nogo:
        lines.append(f"- no-go: {', '.join(nogo)}")

    lines.extend([
        "",
        "KIES VRIJ.",
        "GEEN STANDAARDGERECHTEN.",
        "GEEN HERHALING.",
        "RESPECTEER VEGETARISCH, ALLERGIEËN EN NO-GO’S VOLLEDIG."
    ])

    return "\n".join(lines)


# -------------------------------------------------
# Cached LLM call
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_peet_choice(context_text: str):
    return call_peet_text(context_text)


# -------------------------------------------------
# JSON parser (veilig)
# -------------------------------------------------
def parse_llm_output(raw):

    dish_name = "Peet kiest iets lekkers"
    ingredients = []
    preparation = []

    try:
        data = raw if isinstance(raw, dict) else json.loads(raw)

        if isinstance(data.get("dish_name"), str):
            dish_name = data["dish_name"].strip()

        if isinstance(data.get("ingredients"), list):
            ingredients = [
                i.strip() for i in data["ingredients"]
                if isinstance(i, str) and i.strip()
            ]

        if isinstance(data.get("preparation"), list):
            preparation = [
                p.strip() for p in data["preparation"]
                if isinstance(p, str) and p.strip()
            ]

    except Exception:
        return None, None, None

    return dish_name, ingredients, preparation


# -------------------------------------------------
# UI polish
# -------------------------------------------------
def inject_css():

    st.markdown("""
    <style>

    [data-testid="stHeader"],
    [data-testid="stDecoration"] {
        display: none;
    }

    .block-container { 
        padding-top: 1.2rem; 
        max-height: 100vh;
        overflow-y: auto !important;
    }

    * {
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
        overscroll-behavior: contain;
    }

    h1 { font-size: 1.6rem !important; }
    h2, h3 { font-size: 1.5rem !important; }

    </style>
    """, unsafe_allow_html=True)


# -------------------------------------------------
# Main app
# -------------------------------------------------
def main():

    st.set_page_config(
        page_title="Peet kiest",
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items={}
    )

    inject_css()

    st.markdown("<h1>Peet gaat voor je kiezen.</h1>", unsafe_allow_html=True)
    st.caption("Vandaag is het geregeld. Iedere dag weer iets nieuws.")

    # -------------------------------------------------
    # Build context
    # -------------------------------------------------
    llm_context = build_llm_context()

    if llm_context == "__FORWARD__":
        st.warning("Voor meerdere dagen: gebruik Peet Kiest Vooruit.")
        st.stop()

    # -------------------------------------------------
    # Signature → nieuwe keuze bij andere input
    # -------------------------------------------------
    context_sig = hashlib.md5(llm_context.encode("utf-8")).hexdigest()

    if st.session_state.get("context_sig") != context_sig:

        st.session_state["context_sig"] = context_sig

        with st.spinner(
            "We hebben meer dan 1 miljoen gerechten en Peet zoekt nu de allerlekkerste voor je uit…"
        ):
            st.session_state["raw_llm"] = fetch_peet_choice(llm_context)

        st.session_state.pop("pdf_path", None)

    raw_llm = st.session_state.get("raw_llm")

    # -------------------------------------------------
    # Parse LLM output
    # -------------------------------------------------
    dish_name, ingredients, preparation = parse_llm_output(raw_llm)

    if not dish_name:
        st.error("Er ging iets mis bij het verwerken van het gerecht.")
        return

    # -------------------------------------------------
    # Engine call
    # -------------------------------------------------
    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))

    engine_context = {
        "days": 1,
        "persons": persons,
        "dish_name": dish_name,
        "allergies": to_list(qp("allergies")),
        "nogo": to_list(qp("nogo")),
    }

    result = plan(engine_context)

    days = result.get("days", [])
    days_count = result.get("days_count", len(days))

    if not days:
        st.error("Geen gerecht gegenereerd.")
        return

    # Verrijk dag 1 met LLM details
    days[0].update({
        "dish_name": dish_name,
        "ingredients": ingredients,
        "preparation": "\n".join(preparation),
    })

    # -------------------------------------------------
    # Screen rendering
    # -------------------------------------------------
    st.subheader(dish_name)
    st.divider()

    st.subheader(f"Ingrediënten (voor {persons} personen)")

    if ingredients:
        st.markdown("\n".join(f"- {i}" for i in ingredients))
    else:
        st.write("Geen ingrediënten beschikbaar.")

    st.divider()
    st.subheader("Zo pak je het aan")

    prep_text = days[0].get("preparation", "").strip()

    if prep_text:
        for step in [s for s in prep_text.split("\n") if s.strip()]:
            st.write(step)
    else:
        st.write("Bereiding niet beschikbaar.")

    # -------------------------------------------------
    # PDF
    # -------------------------------------------------
    if "pdf_path" not in st.session_state:

        st.session_state["pdf_path"] = build_plan_pdf(
            days=days,
            days_count=days_count,
        )

    pdf_path = st.session_state["pdf_path"]

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download als PDF",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
            )


# -------------------------------------------------
if __name__ == "__main__":
    main()
