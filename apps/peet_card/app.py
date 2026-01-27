# -------------------------------------------------
# Peet-Card — Vandaag (FAST FLOW + PDF)
# -------------------------------------------------

import sys
from pathlib import Path
import os
import time
import hashlib
import streamlit as st

# -----------------------------
# Font (Carrd stijl)
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@300;400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto Condensed', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* Verberg Streamlit header (Share + menu) */
    header {visibility: hidden;}
    
    /* Verberg footer */
    footer {visibility: hidden;}
    
    /* Trek content iets omhoog */
    .block-container {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------------------------------
# Bootstrap project root
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -------------------------------------------------
# Imports
# -------------------------------------------------
from core.llm import call_peet_text
from core.fast_test.llm_fast import fetch_peet_choice_fast
from context_builder import build_context
from peet_engine.render_pdf import build_plan_pdf

USE_FAST = True

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

    st.title("Peet gaat voor je kiezen.")
    st.caption("Vandaag is het geregeld. Iedere dag weer iets nieuws.")

    # -------------------------------------------------
    # Context uit query params
    # -------------------------------------------------
    raw_context = {
        "persons": max(1, min(12, to_int(qp("persons", "2"), 2))),
        "time": qp("time", ""),
        "moment": qp("moment", ""),
        "preference": qp("preference", ""),
        "kitchen": qp("kitchen", ""),
        "fridge": qp("fridge", ""),
        "nogo": qp("nogo", ""),
        "allergies": qp("allergies", ""),
    }

    llm_context = build_context(raw_context)

    if llm_context == "__FORWARD__":
        st.warning("Voor meerdere dagen: gebruik Peet Kiest Vooruit.")
        st.stop()

    # -------------------------------------------------
    # FAST FLOW
    # -------------------------------------------------
    @st.cache_data(show_spinner=False)
    def fetch_peet_choice(context: dict):
        if USE_FAST:
            return fetch_peet_choice_fast(context)
        return call_peet_text(context)

    if "peet_result" not in st.session_state:
        with st.spinner("Peet zoekt de allerlekkerste keuze voor je uit..."):
            st.session_state["peet_result"] = fetch_peet_choice(llm_context)

    free_text = st.session_state["peet_result"]

    if not isinstance(free_text, dict) or not free_text:
        st.error("Geen geldig resultaat ontvangen. Refresh even.")
        st.stop()

    # -------------------------------------------------
    # Data uit FAST output
    # -------------------------------------------------
    dish_name = free_text.get("dish_name", "Peet kiest iets lekkers")
    why = free_text.get("why", "")
    ingredients = free_text.get("ingredients", [])
    recipe_steps = free_text.get("preparation", [])
    persons_label = llm_context.get("persons", "")

    # -------------------------------------------------
    # Render scherm
    # -------------------------------------------------
    st.subheader(dish_name)

    if isinstance(why, str) and why.strip():
        st.caption(why.strip())

    st.markdown("---")

    st.markdown(f"### Ingrediënten (voor {persons_label} personen)")

    if isinstance(ingredients, list) and ingredients:
        for item in ingredients:
            if isinstance(item, str) and item.strip():
                st.write(f"• {item.strip()}")
    else:
        st.write("Geen ingrediënten beschikbaar.")

    st.markdown("---")

    st.markdown("### Zo pak je het aan")

    if isinstance(recipe_steps, list) and recipe_steps:
        for step in recipe_steps:
            if isinstance(step, str) and step.strip():
                st.write(step.strip())
    else:
        st.write("Bereiding niet beschikbaar.")

    # -------------------------------------------------
    # PDF vanuit FAST output
    # -------------------------------------------------
    days = [{
        "dish_name": dish_name,
        "ingredients": ingredients,
        "preparation": recipe_steps,
        "why": why,
        "persons": persons_label,
    }]

    if "pdf_path" not in st.session_state:
        st.session_state["pdf_path"] = build_plan_pdf(
            days=days,
            days_count=1,
        )

    pdf_path = st.session_state["pdf_path"]

    if pdf_path and os.path.exists(pdf_path):

        btn_key = hashlib.md5(
            f"{dish_name}|{pdf_path}".encode("utf-8")
        ).hexdigest()

        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download als PDF",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_download_{btn_key}",
            )


# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    main()
