from io import BytesIO
from datetime import datetime
import locale

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from peet_engine.render_pdf_helpers import CATEGORY_ORDER, categorize, amount_for_item


def build_plan_pdf(result: dict) -> tuple[BytesIO, str]:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Locale NL (best effort)
    try:
        locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")
    except Exception:
        pass

    now = datetime.now()
    weekday = now.strftime("%A").capitalize()
    date_str = now.strftime("%d-%m-%Y")

    days = result.get("days", []) or []
    days_count = result.get("days_count") or len(days) or 1
    persons = int(result.get("persons", 1) or 1)

    if days_count == 1:
        cover_title = "Peet koos vandaag"
        cover_subtitle = f"{weekday} {date_str}"
        filename = f"Peet_koos_vandaag_{weekday}_{date_str}.pdf"
    else:
        cover_title = f"Peet koos {days_count} dagen vooruit"
        cover_subtitle = f"Vanaf {date_str}"
        filename = f"Peet_koos_{days_count}_dagen_vooruit_{date_str}.pdf"

    # =========================
    # VOORPAGINA
    # =========================
    story.append(Spacer(1, 120))
    story.append(Paragraph(f"<b><font size='22'>{cover_title}</font></b>", styles["Title"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph(f"<font size='14'>{cover_subtitle}</font>", styles["Normal"]))
    story.append(Spacer(1, 200))
    story.append(Paragraph("<font size='10'>Peet kiest. Jij hoeft alleen te koken.</font>", styles["Normal"]))
    story.append(PageBreak())

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

        description = day.get("description")
        if description:
            story.append(Paragraph(description, styles["Normal"]))
            story.append(Spacer(1, 10))

        # Optioneel: ingrediënten per dag (als aanwezig)
        ingredients = day.get("ingredients") or []
        if ingredients:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Ingrediënten (globaal)", styles["Heading3"]))
            for item in ingredients:
                name = (item.get("name") or "").strip()
                if name:
                    story.append(Paragraph(f"• {name}", styles["Normal"]))
            story.append(Spacer(1, 10))

        story.append(Spacer(1, 12))

    story.append(PageBreak())

    # =========================
    # BOODSCHAPPENLIJST
    # =========================
    story.append(Paragraph("Boodschappenlijst", styles["Title"]))
    story.append(Spacer(1, 12))

    categorized: dict[str, dict[str, str]] = {}

    for day in days:
        for item in day.get("ingredients", []) or []:
            name = (item.get("name") or "").strip()
            if not name:
                continue

            cat = categorize(name)
            if cat not in categorized:
                categorized[cat] = {}

            if name not in categorized[cat]:
                categorized[cat][name] = amount_for_item(name, persons)

    if not categorized:
        story.append(Paragraph("Geen boodschappenlijst beschikbaar in deze build.", styles["Normal"]))
    else:
        for cat in CATEGORY_ORDER:
            items = categorized.get(cat)
            if not items:
                continue

            story.append(Spacer(1, 10))
            story.append(Paragraph(cat, styles["Heading2"]))

            for name, amount in items.items():
                line = f"• {name}"
                if amount:
                    line += f": {amount}"
                story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer, filename
