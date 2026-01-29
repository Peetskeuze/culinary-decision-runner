# -------------------------------------------------
# Peet-Card — Vandaag (oude kwaliteit + nieuwe engine/PDF)
# -------------------------------------------------

import sys
from pathlib import Path
import json
import time
import hashlib
import streamlit as st

# -------------------------------------------------
# Bootstrap project root (lokaal + cloud)
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
# Helpers
# -------------------------------------------------
def qp(name: str, default: str = "") -> str:
    v = st.query_params.get(name, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


def to_int(val: str, default: int) -> int:
    try:
        return int(str(val).strip())
    except Exception:
        return default


def to_list(val: str) -> list[str]:
    if not val:
        return []
    return [p.strip().lower() for p in str(val).split(",") if p.strip()]


# -------------------------------------------------
# Oude rijke context terugbrengen (dit is de magie)
# -------------------------------------------------
def build_llm_context() -> str:
    """
    Vrije tekstcontext zoals de oude werkende versie.
    Geen JSON. Geen schema. Volledige sturing + variatie.
    """

    days = to_int(qp("days", "1"), 1)
    if days in (2, 3, 5):
        return "__FORWARD__"

    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))

    moment = qp("moment", "")
    kitchen = qp("kitchen", "")
    preference = qp("preference", "")
    vegetarian = qp("vegetarian", "")
    allergies = to_list(qp("allergies", ""))
    nogo = to_list(qp("nogo", ""))

    lines = []
    lines.append("CONTEXT VANDAAG:")
    lines.append(f"- persons: {persons}")

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

    lines.append("")
    lines.append("KIES VRIJ.")
    lines.append("GEEN STANDAARDGERECHTEN.")
    lines.append("GEEN HERHALING.")
    lines.append("RESPECTEER VEGETARISCH, ALLERGIEËN EN NO-GO’S VOLLEDIG.")

    return "\n".join(lines)


# -------------------------------------------------
# LLM call met veilige caching
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_peet_choice(context_sig: str, context_text: str):
    return call_peet_text(context_text)


# -------------------------------------------------
# App
# -------------------------------------------------
def main():

    st.set_page_config(
        page_title="Peet kiest",
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items={}
    )

    # ---------------- UI polish ----------------

    st.markdown("""
    <style>

    [data-testid="stHeader"] { display: none; }
    [data-testid="stDecoration"] { display: none; }

    .block-container { 
        padding-top: 1.2rem; 
        overflow-y: auto !important;
        max-height: 100vh;
    }

    h1 { font-size: 1.6rem !important; }
    h2, h3 { font-size: 1.5rem !important; line-height: 1.2; }

    * {
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
        overscroll-behavior: contain;
    }

    html, body {
        height: 100%;
        overflow: auto;
        -webkit-overflow-scrolling: touch;
    }

    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        height: 100vh;
    }

    [data-testid="stSpinner"] svg {
        width: 32px !important;
        height: 32px !important;
    }

    </style>
    """, unsafe_allow_html=True)


    # ---------------- Titel ----------------

    st.markdown(
        "<h1>Peet gaat voor je kiezen.</h1>",
        unsafe_allow_html=True
    )

    st.caption("Vandaag is het geregeld. Iedere dag weer iets nieuws.")

    # -------------------------------------------------


    # 1) Context bouwen (oude kwaliteit)
    # -------------------------------------------------
    llm_context = build_llm_context()

    if llm_context == "__FORWARD__":
        st.warning("Voor meerdere dagen: gebruik Peet Kiest Vooruit.")
        st.stop()

    # -------------------------------------------------
    # 2) Context signature → nieuwe keuze bij andere input
    # -------------------------------------------------
    context_sig = hashlib.md5(
        llm_context.encode("utf-8")
    ).hexdigest()

    if st.session_state.get("context_sig") != context_sig:
        st.session_state["context_sig"] = context_sig

        with st.spinner(
            "We hebben meer dan 1 miljoen gerechten en Peet zoekt nu de allerlekkerste voor je uit…"
        ):
            st.session_state["peet_raw"] = fetch_peet_choice(
                context_sig,
                llm_context
            )

        st.session_state.pop("pdf_path", None)

    free_text = st.session_state.get("peet_raw")

    # -------------------------------------------------
    # 3) JSON veilig parsen (van LLM)
    # -------------------------------------------------
    dish_name = "Peet kiest iets lekkers"
    ingredients = []
    recipe_steps = []

    try:
        data = free_text if isinstance(free_text, dict) else json.loads(free_text)

        if isinstance(data.get("dish_name"), str):
            dish_name = data["dish_name"].strip()

        if isinstance(data.get("ingredients"), list):
            ingredients = [
                item.strip()
                for item in data["ingredients"]
                if isinstance(item, str) and item.strip()
            ]

        if isinstance(data.get("preparation"), list):
            recipe_steps = [
                step.strip()
                for step in data["preparation"]
                if isinstance(step, str) and step.strip()
            ]

    except Exception:
        st.error("Er ging iets mis bij het verwerken van het gerecht.")
        return


    # -------------------------------------------------
    # 4) Engine aanroepen (nieuwe structuur behouden)
    # -------------------------------------------------
    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))

    engine_context = {
        "days": 1,
        "persons": persons,
        "dish_name": dish_name,
        "allergies": to_list(qp("allergies", "")),
        "nogo": to_list(qp("nogo", "")),
    }

    result = plan(engine_context)

    days = result.get("days", [])
    days_count = result.get("days_count", len(days))

    if not days:
        st.error("Geen gerecht gegenereerd.")
        return

    # Verrijk dag 1 met LLM output
    days[0]["dish_name"] = dish_name
    days[0]["ingredients"] = ingredients
    days[0]["preparation"] = "\n".join(recipe_steps)

    # -------------------------------------------------
    # Schermweergave
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

    prep = days[0].get("preparation", "").strip()

    if prep:
        for step in [s for s in prep.split("\n") if s.strip()]:
            st.write(step)
    else:
        st.write("Bereiding niet beschikbaar.")

    # -------------------------------------------------
    # PDF Knop
    # -------------------------------------------------

    import os

    if "pdf_path" not in st.session_state:
        st.session_state["pdf_path"] = build_plan_pdf(
            days=days,
            days_count=days_count,
        )

    pdf_path = st.session_state["pdf_path"]

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download als PDF",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()


