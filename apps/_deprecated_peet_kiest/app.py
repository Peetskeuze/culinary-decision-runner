import streamlit as st
import sys
from pathlib import Path

# --- core beschikbaar maken ---
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from core.llm import call_peet

# --- pagina ---
st.set_page_config(page_title="Peet Kiest – Suite")

st.title("Peet Kiest")
st.caption("Schone suite-versie")

# --- formulier ---
with st.form("peet_form"):
    moment = st.selectbox(
        "Welk moment is het?",
        ["Doordeweeks", "Weekend", "Speciaal"]
    )

    tijd = st.slider(
        "Hoeveel tijd heb je?",
        min_value=10,
        max_value=90,
        step=5,
        value=30
    )

    personen = st.number_input(
        "Voor hoeveel personen?",
        min_value=1,
        max_value=6,
        value=2
    )

    submit = st.form_submit_button("Peet, kies voor mij")

# --- actie ---
if submit:
    context = f"""
    Moment: {moment}
    Tijd: {tijd} minuten
    Personen: {personen}
    """

    with st.spinner("Peet denkt even na..."):
        try:
            result = call_peet(context)
        except Exception as e:
            st.error("Peet raakte even de draad kwijt.")
            st.write(e)
            st.stop()

    # --- resultaat ---
    st.subheader(result.get("dish", ""))
    st.caption(f"{result.get('time', '')} · {result.get('serves', '')} personen")

    st.subheader("Ingrediënten")
    for i in result.get("ingredients", []):
        if isinstance(i, dict):
            item = i.get("item", "")
            amount = i.get("amount", "")
            st.markdown(f"- **{item}** – {amount}")
        else:
            st.markdown(f"- {i}")


    st.subheader("Bereiding")
    for step in result.get("steps", []):
        st.markdown(f"- {step}")
