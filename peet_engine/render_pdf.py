import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(
    TTFont("RobotoCondensed", "peet_engine/fonts/RobotoCondensed-Regular.ttf")
)

pdfmetrics.registerFont(
    TTFont("RobotoCondensed-Bold", "peet_engine/fonts/RobotoCondensed-Bold.ttf")
)




def build_plan_pdf(dish_name, nutrition, ingredients, preparation, image_path=None) -> str:
    if not dish_name:
        return ""

    # Bestandsnaam veilig maken
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

    # -------------------------------------------------
    # Stijlen
    # -------------------------------------------------

    styles.add(ParagraphStyle(
        name="DishTitle",
        fontSize=18,
        leading=22,
        spaceAfter=6,
        fontName="RobotoCondensed-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Tagline",
        fontSize=10.5,
        leading=14,
        spaceAfter=10,
        textColor=colors.grey
    ))

    styles.add(ParagraphStyle(
        name="Macros",
        fontSize=11,
        leading=15,
        spaceAfter=16,
        spaceBefore=6
    ))

    styles.add(ParagraphStyle(
        name="Section",
        fontSize=13,
        leading=16,
        spaceBefore=16,
        spaceAfter=8,
        fontName="RobotoCondensed-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontSize=10.5,
        leading=13,
        spaceAfter=6
    ))

    story = []

    # -------------------------------------------------
    # Afbeelding
    # -------------------------------------------------

    from reportlab.platypus import Image

    if image_path and os.path.exists(image_path):
        story.append(Image(image_path, width=12 * cm, height=8 * cm))
        story.append(Spacer(1, 10))

    story.append(Paragraph(dish_name, styles["DishTitle"]))
    story.append(Paragraph("Peet kiest iets dat vandaag past.", styles["Tagline"]))


    # -------------------------------------------------
    # Macro blok
    # -------------------------------------------------

    if isinstance(nutrition, dict):
        kcal = nutrition.get("calories_kcal", "")
        protein = nutrition.get("protein_g", "")
        fat = nutrition.get("fat_g", "")
        carbs = nutrition.get("carbs_g", "")

        macro_block = f"""
        <b>{kcal} kcal</b><br/>
        Eiwit: {protein} g<br/>
        Vet: {fat} g<br/>
        Koolhydraten: {carbs} g
        """

        story.append(Paragraph(macro_block, styles["Macros"]))

    # -------------------------------------------------
    # Ingrediënten
    # -------------------------------------------------

    story.append(Paragraph("Ingrediënten", styles["Section"]))

    if ingredients and isinstance(ingredients, list):

        rows = []

        for ing in ingredients:

            if isinstance(ing, dict):
                amount = str(ing.get("amount", "")).strip()
                item = str(ing.get("item", "")).strip()

                if amount and item:
                    rows.append([
                        Paragraph(amount, styles["Body"]),
                        Paragraph(item, styles["Body"])
                    ])

            elif isinstance(ing, str) and ing.strip():
                rows.append([
                    Paragraph("", styles["Body"]),
                    Paragraph(ing.strip(), styles["Body"])
                ])

        if rows:
            table = Table(
                rows,
                colWidths=[4.5 * cm, 9.5 * cm]   # 👈 breder + beter in balans
            )

            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]))

            story.append(table)

    else:
        story.append(Paragraph("Geen ingrediënten beschikbaar.", styles["Body"]))
        

    # -------------------------------------------------
    # Kleine scheidingsruimte (polish 2)
    # -------------------------------------------------

    story.append(Spacer(1, 8))

    # -------------------------------------------------
    # Bereiding
    # -------------------------------------------------

    story.append(Paragraph("Zo pak je het aan", styles["Section"]))

    if preparation and isinstance(preparation, list):
        for step in preparation:
            if isinstance(step, str) and step.strip():
                story.append(Paragraph(step.strip(), styles["Body"]))
    else:
        story.append(Paragraph("Bereiding niet beschikbaar.", styles["Body"]))

    # -------------------------------------------------
    # Build PDF
    # -------------------------------------------------

    doc.build(story)

    return path
