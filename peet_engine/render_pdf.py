from io import BytesIO
from typing import Dict, Any, List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from peet_engine.recipe_text import get_recipe
from peet_engine.render_pdf_helpers import categorize, CATEGORY_ORDER


def build_plan_pdf(result: Dict[str, Any]) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title",
            parent=base_styles["Title"],
            fontSize=20,
            spaceAfter=18,
        ),
        "dish": ParagraphStyle(
            "dish",
            parent=base_styles["Heading2"],
            fontSize=15,
            spaceBefore=18,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base_styles["Heading3"],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base_styles["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=6,
        ),
        "list": ParagraphStyle(
            "list",
            parent=base_styles["BodyText"],
            fontSize=10.5,
            leading=14,
            leftIndent=10,
            spaceAfter=4,
        ),
    }

    story: List = []

    # Titel
    story.append(Paragraph("Peet kiest. Jij hoeft alleen te koken.", styles["title"]))

    combined_items: Dict[str, str] = {}

    # Per gerecht
    for day in result.get("days", []):
        dish = day.get("dish_name", "")
        recipe = get_recipe(dish)

        story.append(Paragraph(dish, styles["dish"]))
        story.append(Paragraph(recipe["opening"], styles["body"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Zo pak je dit aan", styles["section"]))
        for paragraph in recipe["preparation"].split("\n\n"):
            story.append(Paragraph(paragraph, styles["body"]))

        story.append(Spacer(1, 8))
        story.append(Paragraph("Ingrediënten", styles["section"]))

        for item, qty in recipe.get("ingredients", {}).items():
            story.append(Paragraph(f"{item} — {qty}", styles["list"]))
            combined_items.setdefault(item, qty)

        story.append(Spacer(1, 14))

    # Gecombineerde boodschappenlijst
    if combined_items:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Gecombineerde boodschappenlijst", styles["dish"]))

        categorized: Dict[str, List[str]] = {k: [] for k in CATEGORY_ORDER}
        for item, qty in combined_items.items():
            cat = categorize(item)
            categorized[cat].append(f"{item} — {qty}")

        for category in CATEGORY_ORDER:
            items = categorized.get(category, [])
            if not items:
                continue

            story.append(Paragraph(category, styles["section"]))
            for line in sorted(items):
                story.append(Paragraph(line, styles["list"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer
