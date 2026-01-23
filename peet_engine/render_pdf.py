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
    preparation = day.get("preparation", "")
    ingredients = day.get("ingredients", [])

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

    styles.add(ParagraphStyle(
        name="DishTitle",
        fontSize=18,
        leading=22,
        spaceAfter=16,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Section",
        fontSize=13,
        leading=16,
        spaceBefore=18,
        spaceAfter=8,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontSize=10.5,
        leading=15,
        spaceAfter=6
    ))

    story = []

    # Titel
    story.append(Paragraph(dish_name, styles["DishTitle"]))

    # Ingrediënten
    story.append(Paragraph("Ingrediënten", styles["Section"]))

    if ingredients:
        for item in ingredients:
            if isinstance(item, str) and item.strip():
                story.append(Paragraph(f"• {item.strip()}", styles["Body"]))
    else:
        story.append(Paragraph("Geen ingrediënten beschikbaar.", styles["Body"]))

    # Bereiding
    story.append(Paragraph("Zo pak je het aan", styles["Section"]))

    if preparation:
        steps = [s.strip() for s in preparation.split("\n") if s.strip()]
        for step in steps:
            story.append(Paragraph(step, styles["Body"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Bereiding niet beschikbaar.", styles["Body"]))

    doc.build(story)
    return path
