from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def build_plan_pdf(days, days_count, output_path):
    """
    Bouwt een PDF op basis van EXACT dezelfde days
    die ook op het scherm worden getoond.
    """

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # =========================
    # GERECHTEN PER DAG
    # =========================
    for idx, day in enumerate(days, start=1):

        if days_count > 1:
            story.append(Paragraph(f"Dag {idx}", styles["Heading1"]))
            story.append(Spacer(1, 8))

        dish_name = day.get("dish_name") or "Onbekend gerecht"
        story.append(Paragraph(dish_name, styles["Heading2"]))
        story.append(Spacer(1, 6))

        why = day.get("why")
        if why:
            story.append(Paragraph(why, styles["Normal"]))
            story.append(Spacer(1, 6))

        # -------------------------
        # INGREDIËNTEN
        # -------------------------
        ingredients = day.get("ingredients", [])
        if ingredients:
            story.append(Paragraph("Ingrediënten", styles["Heading3"]))
            story.append(Spacer(1, 6))

            for item in ingredients:
                if isinstance(item, str):
                    name = item.strip()
                elif isinstance(item, dict):
                    name = (item.get("name") or "").strip()
                else:
                    name = ""

                if name:
                    story.append(Paragraph(f"• {name}", styles["Normal"]))

            story.append(Spacer(1, 10))

        # -------------------------
        # BEREIDING
        # -------------------------
        preparation = day.get("preparation")
        if preparation:
            story.append(Paragraph("Bereiding", styles["Heading3"]))
            story.append(Spacer(1, 6))

            for step in preparation.split("\n"):
                step = step.strip()
                if step:
                    story.append(Paragraph(step, styles["Normal"]))
                    story.append(Spacer(1, 6))

        story.append(PageBreak())

    doc.build(story)
