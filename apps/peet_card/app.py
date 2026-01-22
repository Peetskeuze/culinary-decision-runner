# apps/peet_card/app.py
# -------------------------------------------------
# Peet-Card — Vandaag
# LLM kiest vrij, engine werkt uit (bereiding + PDF)
# -------------------------------------------------

import sys
from pathlib import Path
import streamlit as st

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
from peet_engine.render_pdf import render_pdf

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
    st.set_page_config(page_title="Peet kiest", layout="centered")

    st.title("Peet kiest. Jij hoeft alleen te koken.")
    st.caption("Vandaag geregeld. Elke refresh mag echt anders zijn.")

    llm_context = build_llm_context()

    if llm_context == "__FORWARD__":
        st.warning("Voor 2/3/5 dagen vooruit: gebruik Peet Kiest Vooruit.")
        st.stop()

    # 1) Peet kiest vrij (LLM)
    with st.spinner("Peet is aan het kiezen…"):
        free_text = call_peet_text(llm_context)

    # Verwacht: eerste regel = gerechtnaam, rest = korte motivatie
    lines = [l.strip() for l in free_text.splitlines() if l.strip()]
    dish_name = lines[0]
    narrative = " ".join(lines[1:]) if len(lines) > 1 else ""

    st.subheader(dish_name)
    if narrative:
        st.write(narrative)

    st.divider()

    # 2) Engine werkt uit (bereiding + structuur)
    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))
    engine_context = {
        "days": 1,
        "persons": persons,
        "dish_name": dish_name,
        "allergies": to_list(qp("allergies", "")),
        "nogo": to_list(qp("nogo", "")),
    }

    result = plan(engine_context)

    # Bereiding op scherm
    st.subheader("Zo pak je het aan")
    st.write(result.get("recipe_text", "Bereiding niet beschikbaar."))

    # 3) PDF
    pdf_bytes = render_pdf(result)
    st.download_button(
        label="Download recept & boodschappen (PDF)",
        data=pdf_bytes,
        file_name="Peet_Kiest_Vandaag.pdf",
        mime="application/pdf",
    )


if __name__ == "__main__":
    main()
