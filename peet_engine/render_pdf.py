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




def build_plan_pdf(
    dish_name,
    nutrition,
    ingredients,
    preparation,

    cook_time_min=None,
    cook_time_max=None,

    calories_kcal=None,
    persons=1,

    protein_g=0,
    fat_g=0,
    carbs_g=0,

    protein_pct=0,
    fat_pct=0,
    carbs_pct=0,

    image_path=None
) -> str:


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
    
    #---------------------------------------------------
    # Kooktijd + kcal per persoon (header)
    #---------------------------------------------------

    header_line = ""

    if cook_time_min and cook_time_max:
        if cook_time_min == cook_time_max:
            header_line = f"{cook_time_max} min"
        else:
            header_line = f"{cook_time_min}–{cook_time_max} min"

    if calories_kcal:
        kcal_pp = round(calories_kcal / max(1, persons))
        if header_line:
            header_line += " • "
        header_line += f"± {kcal_pp} kcal per persoon"

    if header_line:
        story.append(Paragraph(header_line, styles["Body"]))
        story.append(Spacer(1, 6))


    #---------------------------------------------------
    # Macro’s per persoon + percentages
    #---------------------------------------------------

    macro_block = f"""
    <b>Eiwit:</b> {protein_g} g ({protein_pct}%) &nbsp;&nbsp;
    <b>Vet:</b> {fat_g} g ({fat_pct}%) &nbsp;&nbsp;
    <b>Koolhydraten:</b> {carbs_g} g ({carbs_pct}%)
    """

    story.append(Paragraph(macro_block, styles["Macros"]))
    story.append(Spacer(1, 12))


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
    story.append(Paragraph("Zo pak je het aan", styles["Section"]))

    if preparation:

        if isinstance(preparation, list):
            for step in preparation:
                if str(step).strip():
                    story.append(Paragraph(step, styles["Body"]))

        elif isinstance(preparation, str):
            for line in preparation.split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, styles["Body"]))

    else:
        story.append(Paragraph("Bereiding niet beschikbaar.", styles["Body"]))




    # -------------------------------------------------
    # Build PDF
    # -------------------------------------------------

    doc.build(story)

    return path
