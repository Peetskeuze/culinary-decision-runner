from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from datetime import date
import os


def build_plan_pdf(days: list, days_count: int) -> str:
    """
    Bouwt een keukenproof PDF voor 1 dag.
    Verwacht:
      days[0]["dish_name"]
      days[0]["preparation"]  -> string met \n
      days[0]["ingredients"]  -> lijst strings
    """

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

    # Bereiding
    story.append(Paragraph("Zo pak je het aan", styles["Section"]))

    if preparation:
        steps = [s.strip() for s in preparation.split("\n") if s.strip()]
        for step in steps:
            story.append(Paragraph(step, styles["Body"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Bereiding niet beschikbaar.", styles["Body"]))

    # Nieuwe pagina voor boodschappen
    story.append(PageBreak())

    # Boodschappenlijst
    story.append(Paragraph("Boodschappenlijst", styles["Section"]))

    if ingredients:
        items = []
        for item in ingredients:
            if isinstance(item, str) and item.strip():
                items.append(
                    ListItem(
                        Paragraph(item.strip(), styles["Body"]),
                        leftIndent=12
                    )
                )

        story.append(
            ListFlowable(
                items,
                bulletType="bullet",
                start="bullet",
                leftIndent=0
            )
        )
    else:
        story.append(Paragraph("Geen ingrediënten beschikbaar.", styles["Body"]))

    doc.build(story)

    return path
def build_plan_pdf(...):
    ...
    return path

