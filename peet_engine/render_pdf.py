from io import BytesIO
from datetime import datetime
import locale

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# Deze helpers moeten al bestaan in je project
# - categorize(name)
# - amount_for_item(name, persons)
# - CATEGORY_ORDER
# ---------------------------------------------------------
# BOODSCHAPPEN CATEGORIEËN (VASTE VOLGORDE)
# ---------------------------------------------------------
CATEGORY_ORDER = [
    "Groente & fruit",
    "Brood & ontbijt",
    "Zuivel & eieren",
    "Vlees, vis & vega",
    "Houdbaar",
    "Kruiden & oliën",
    "Koeling / diepvries",
    "Overig",
]


def build_plan_pdf(result: dict) -> BytesIO:
    buffer = BytesIO()

    # =========================
    # DOCUMENT SETUP
    # =========================
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Locale NL (fallback ok)
    try:
        locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")
    except Exception:
        pass

    # =========================
    # VOORPAGINA
    # =========================
    now = datetime.now()
    weekday = now.strftime("%A").capitalize()
    date_str = now.strftime("%d-%m-%Y")

    days_list = result.get("days", [])
    days_count = result.get("days_count") or len(days_list)

    if days_count == 1:
        cover_title = "Peet koos vandaag"
        cover_subtitle = f"{weekday} {date_str}"
    else:
        cover_title = f"Peet koos {days_count} dagen vooruit"
        cover_subtitle = f"Vanaf {date_str}"

    story.append(Spacer(1, 120))
    story.append(
        Paragraph(
            f"<b><font size='22'>{cover_title}</font></b>",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 24))
    story.append(
        Paragraph(
            f"<font size='14'>{cover_subtitle}</font>",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 200))
    story.append(
        Paragraph(
            "<font size='10'>Peet kiest. Jij hoeft alleen te koken.</font>",
            styles["Normal"],
        )
    )
    story.append(PageBreak())

    # =========================
    # GERECHTEN PER DAG
    # =========================
    for idx, day in enumerate(days_list, start=1):
        if days_count > 1:
            story.append(
                Paragraph(f"Dag {idx}", styles["Heading1"])
            )
            story.append(Spacer(1, 8))

        dish_name = day.get("dish_name")
        if dish_name:
            story.append(
                Paragraph(f"<b>{dish_name}</b>", styles["Heading2"])
            )
            story.append(Spacer(1, 6))

        why = day.get("why")
        if why:
            story.append(Paragraph(why, styles["Normal"]))
            story.append(Spacer(1, 6))

        description = day.get("description")
        if description:
            story.append(Paragraph(description, styles["Normal"]))
            story.append(Spacer(1, 12))

        story.append(Spacer(1, 12))

    story.append(PageBreak())

    # =========================
    # BOODSCHAPPENLIJST
    # =========================
    persons = result.get("persons", 1)

    story.append(Paragraph("Boodschappenlijst", styles["Title"]))
    story.append(Spacer(1, 12))

    categorized = {}

    for day in days_list:
        for item in day.get("ingredients", []):
            name = item.get("name")
            if not name:
                continue

            category = categorize(name)

            if category not in categorized:
                categorized[category] = {}

            if name not in categorized[category]:
                categorized[category][name] = amount_for_item(name, persons)

    for category in CATEGORY_ORDER:
        items = categorized.get(category)
        if not items:
            continue

        story.append(Spacer(1, 12))
        story.append(Paragraph(category, styles["Heading2"]))

        for name, amount in items.items():
            line = f"- {name}"
            if amount:
                line += f": {amount}"
            story.append(Paragraph(line, styles["Normal"]))

    # =========================
    # PDF AFRONDEN
    # =========================
    doc.build(story)
    buffer.seek(0)
    return buffer
