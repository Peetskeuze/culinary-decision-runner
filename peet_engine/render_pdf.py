from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os


def build_plan_pdf(days: list, days_count: int) -> str:
    if not days:
        return ""

    day = days[0]

    dish_name = day.get("dish_name", "Peet kiest iets lekkers")

    # FAST kan preparation als list geven; classic vaak als string met \n
    preparation_raw = day.get("preparation", "")
    if isinstance(preparation_raw, list):
        steps = [s.strip() for s in preparation_raw if isinstance(s, str) and s.strip()]
    elif isinstance(preparation_raw, str):
        steps = [s.strip() for s in preparation_raw.split("\n") if s.strip()]
    else:
        steps = []

    ingredients = day.get("ingredients", [])
    if not isinstance(ingredients, list):
        ingredients = []

    why = day.get("why", "")
    if not isinstance(why, str):
        why = ""

    persons = day.get("persons", "")
    persons_label = f" (voor {persons} personen)" if persons else ""

    # Bestandsnaam = gerecht
    safe_name = "".join(c for c in dish_name if c.isalnum() or c in " -_").rstrip()
    filename = f"{safe_name}.pdf"

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    styles = getSampleStyleSheet()

    # Titels wat strakker en rustiger
    styles.add(ParagraphStyle(
        name="DishTitle",
        fontSize=18,
        leading=22,
        spaceAfter=10,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Why",
        fontSize=10.5,
        leading=15,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="Section",
        fontSize=13,
        leading=16,
        spaceBefore=14,
        spaceAfter=8,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontSize=10.5,
        leading=15,
        spaceAfter=4
    ))

    story = []

    # Titel
    story.append(Paragraph(dish_name, styles["DishTitle"]))

    # Why (Peet-zin)
    if why.strip():
        story.append(Paragraph(why.strip(), styles["Why"]))

    # Ingrediënten
    story.append(Paragraph(f"Ingrediënten{persons_label}", styles["Section"]))

    if ingredients:
        for item in ingredients:
            if isinstance(item, str) and item.strip():
                story.append(Paragraph(f"• {item.strip()}", styles["Body"]))
    else:
        story.append(Paragraph("Geen ingrediënten beschikbaar.", styles["Body"]))

    # Bereiding
    story.append(Paragraph("Zo pakken we het aan", styles["Section"]))

    if steps:
        nr = 1
        for step in steps:
            story.append(Paragraph(f"{nr}. {step}", styles["Body"]))
            nr += 1
    else:
        story.append(Paragraph("Bereiding niet beschikbaar.", styles["Body"]))

    doc.build(story)
    return path
