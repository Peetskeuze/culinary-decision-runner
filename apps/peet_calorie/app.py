import streamlit as st
import sys
from pathlib import Path
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

import re

def safe_filename(title: str) -> str:
    if not title:
        return "recept.pdf"
    name = title.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return f"{name}.pdf"

def build_pdf(result: dict) -> BytesIO:
    buf = BytesIO()
    styles = getSampleStyleSheet()
    story = []

    # Titel
    story.append(Paragraph(result.get("title", ""), styles["Title"]))
    story.append(Spacer(1, 12))

    # Calorie-duiding
    cd = result.get("calorie_duiding")
    if cd:
        story.append(
            Paragraph(
                f"{cd.get('range_kcal','')} – {cd.get('toelichting','')}",
                styles["BodyText"]
            )
        )
        story.append(Spacer(1, 14))

    # Ingrediënten
    story.append(Paragraph("Ingrediënten", styles["Heading2"]))
    items = []
    for i in result.get("ingredients", []):
        if isinstance(i, dict):
            items.append(f"{i.get('item','')} – {i.get('amount','')}")
        else:
            items.append(str(i))

    story.append(
        ListFlowable(
            [ListItem(Paragraph(x, styles["BodyText"])) for x in items],
            bulletType="bullet",
            leftIndent=14,
        )
    )
    story.append(Spacer(1, 16))

    # Bereiding
    story.append(Paragraph("Bereiding", styles["Heading2"]))
    for step in result.get("steps", []):
        story.append(Paragraph(step, styles["BodyText"]))
        story.append(Spacer(1, 6))

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    doc.build(story)
    buf.seek(0)
    return buf


    # Titel
    story.append(Paragraph(result.get("title", ""), styles["Title"]))
    story.append(Spacer(1, 10))

    # Calorie-duiding
    cd = result.get("calorie_duiding")
    if cd:
        story.append(
            Paragraph(
                f"{cd.get('range_kcal','')} – {cd.get('toelichting','')}",
                styles["BodyText"]
            )
        )
        story.append(Spacer(1, 12))

    # Ingrediënten
    story.append(Paragraph("Ingrediënten", styles["Heading2"]))
    items = []
    for i in result.get("ingredients", []):
        if isinstance(i, dict):
            items.append(f"{i.get('item','')} – {i.get('amount','')}")
        else:
            items.append(str(i))

    story.append(
        ListFlowable(
            [ListItem(Paragraph(x, styles["BodyText"])) for x in items],
            bulletType="bullet",
            leftIndent=14,
        )
    )
    story.append(Spacer(1, 14))

    # Bereiding
    story.append(Paragraph("Bereiding", styles["Heading2"]))
    for step in result.get("steps", []):
        story.append(Paragraph(step, styles["BodyText"]))
        story.append(Spacer(1, 6))

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )
    doc.build(story)
    buf.seek(0)
    return buf

    # --- project root for Streamlit Cloud ---
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from core.llm import call_peet



# --- pagina ---
st.set_page_config(page_title="Peet Calorie")

st.title("Peet Calorie")
st.caption("Kiezen op calorieën – met gezond verstand")

# --- invoer ---
moment = st.radio(
    "Wanneer eet je dit?",
    ["Ontbijt", "Lunch", "Diner"],
    horizontal=True
)

max_cal = st.slider(
    "Wat is je maximale calorie-inname?",
    min_value=250,
    max_value=650,
    step=25,
    value=400
)

ingredient_hint = st.text_input(
    "Heb je ergens zin in waar ik rekening mee kan houden ?",
    placeholder="Bijv. kip, champignons, iets fris, kruidig, vegetarisch"
)


if st.button("Peet, kies voor mij"):
    context = f"""
    Moment: {moment}
    Max calorieën: {max_cal}
    """

    if ingredient_hint.strip():
        context += f"\nIngrediënthint: {ingredient_hint.strip()}\n"

    context += """
    Richtlijn:
    - Ontbijt is licht en energiek
    - Lunch is voedend maar niet zwaar
    - Diner is volwaardig en warm

    Kies één gerecht dat logisch past bij dit moment.
    """

    with st.spinner("Peet denkt even na..."):
        try:
            result = call_peet(context)
        except Exception as e:
            st.error("Peet raakte even de draad kwijt.")
            st.write(e)
            st.stop()


    # Titel van het gerecht
    if "title" in result:
        st.header(result["title"])

        if "meal_type" in result:
            st.caption(result["meal_type"])

    # Calorie-duiding
    cd = result.get("calorie_duiding")
    if cd:
        st.markdown(
            f"**Calorie-inschatting:** {cd.get('range_kcal')}\n\n"
            f"{'Past binnen je grens.' if cd.get('past_binnen_grens') else ''}\n\n"
            f"{cd.get('toelichting')}"
        )

    # Ingrediënten
    st.subheader("Ingrediënten")

    ingredients_md = []
    for i in result.get("ingredients", []):
        if isinstance(i, dict):
            ingredients_md.append(f"- **{i.get('item','')}** – {i.get('amount','')}")
        else:
            ingredients_md.append(f"- {i}")

    st.markdown("\n".join(ingredients_md))

    # Bereiding
    st.subheader("Bereiding")
    for step in result.get("steps", []):
        st.markdown(f"- {step}")

    st.divider()

    pdf_buffer = build_pdf(result)
    pdf_bytes = pdf_buffer.getvalue()
    filename = safe_filename(result.get("title"))

    st.download_button(
        label="Download boodschappenlijst + bereiding (PDF)",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
    )
