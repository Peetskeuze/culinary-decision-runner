# apps/peet_card/app.py
# -------------------------------------------------
# Peet-Card — Vandaag
# LLM kiest vrij, engine werkt uit (bereiding + PDF)
# -------------------------------------------------

import sys
from pathlib import Path
import json
import time
import streamlit as st

# -----------------------------
# Font gelijk aan Carrd (Roboto Condensed)
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@300;400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto Condensed', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Roboto Condensed', sans-serif;
        font-weight: 700;
    }

    p, div, span, label {
        font-family: 'Roboto Condensed', sans-serif;
        font-weight: 400;
    }
    </style>
    """,
    unsafe_allow_html=True
)

import time
import hashlib


# -------------------------------------------------
# Bootstrap: project-root in sys.path (lokaal + cloud)
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
# LLM call met cache (voorkomt dubbele calls)
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def get_peet_choice_cached(context_hash: str, context_text: str):
    return call_peet_text(context_text)



# -------------------------------------------------
# Rate guard (simpele bescherming)
# -------------------------------------------------
def rate_guard(min_seconds=10):
    now = time.time()
    last = st.session_state.get("last_call", 0)

    if now - last < min_seconds:
        st.warning("Peet is net bezig geweest. Even rustig aan 🙂")
        st.stop()

    st.session_state["last_call"] = now

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


def build_llm_context() -> str:
    """
    Bouwt een vrije tekstcontext voor Peet (vandaag).
    GEEN JSON, GEEN schema. Alleen richting en vrijheid.
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
    lines.append("KIES VRIJ. GEEN STANDAARDGERECHTEN. GEEN HERHALING.")

    return "\n".join(lines)


# -------------------------------------------------
# App
# -------------------------------------------------
def main():
    st.session_state.pop("peet_result", None)

    st.set_page_config(
        page_title="Peet kiest",
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items={}
    )

    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Peet gaat voor je kiezen.")
    st.caption("Vandaag is het geregeld. Iedere dag weer iets nieuws.")

    llm_context = build_llm_context()

    if llm_context == "__FORWARD__":
        st.warning("Voor 2/3/5 dagen vooruit: gebruik Peet Kiest Vooruit.")
        st.stop()

    # -------------------------------------------------
    # LLM – Peet kiest (met veilige caching)
    # -------------------------------------------------

    @st.cache_data(show_spinner=False)
    def fetch_peet_choice(context: str):
        return call_peet_text(context)


    # Forceer nieuwe keuze per page load
    if "peet_result" not in st.session_state:
        with st.spinner("We hebben meer dan 1 miljoen recepten en Peet zoek de allerlekkerste voor je op dit moment"):
            st.session_state["peet_result"] = fetch_peet_choice(llm_context)

    free_text = st.session_state["peet_result"]

    # -------------------------------------------------
    # 2) JSON veilig parsen (LLM → app)
    # -------------------------------------------------
    dish_name = "Peet kiest iets lekkers"
    recipe_text = ""
    ingredients = []

    try:
        data = json.loads(free_text)

        if isinstance(data.get("dish_name"), str):
            dish_name = data["dish_name"].strip()

        if isinstance(data.get("recipe_steps"), list):
            recipe_text = "\n\n".join(
                step.strip()
                for step in data["recipe_steps"]
                if isinstance(step, str) and step.strip()
            )

        if isinstance(data.get("ingredients"), list):
            ingredients = [
                item.strip()
                for item in data["ingredients"]
                if isinstance(item, str) and item.strip()
            ]

    except Exception:
        recipe_text = ""
        ingredients = []

    # -------------------------------------------------
    # 3) Engine (beslissing & structuur)
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

    # -------------------------------------------------
    # 4) Centrale data
    # -------------------------------------------------
    days = result.get("days", [])
    days_count = result.get("days_count", len(days))

    if not days:
        st.error("Geen gerecht gegenereerd.")
        return

    # Verrijk day[0] expliciet met LLM-output
    days[0]["dish_name"] = dish_name
    days[0]["preparation"] = recipe_text
    days[0]["ingredients"] = ingredients

    # -----------------------------
    # Schermweergave
    # -----------------------------
    st.subheader(dish_name)
    st.divider()

    # Ingrediënten
    st.subheader(f"Ingrediënten (voor {persons} personen)")

    ingredients = days[0].get("ingredients", [])
    if ingredients:
        ingred_text = "\n".join(f"- {item}" for item in ingredients)
        st.markdown(ingred_text)
    else:
        st.write("Geen ingrediënten beschikbaar.")


    st.divider()

    # Bereiding
    st.subheader("Zo pak je het aan")

    prep = days[0].get("preparation", "").strip()

    if prep:
        steps = [s.strip() for s in prep.split("\n") if s.strip()]
        for step in steps:
            st.write(step)
    else:
        st.write("Bereiding niet beschikbaar.")

    # -------------------------------------------------
    # 6) PDF
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
