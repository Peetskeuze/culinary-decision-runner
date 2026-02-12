from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


ZONES_ORDER = [
    "AGF",
    "Brood & ontbijt",
    "Zuivel & eieren",
    "Vlees/vis/vega",
    "Houdbaar",
    "Kruiden & oliën",
    "Koeling/diepvries",
    "Overig",
]


def _safe_str(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def build_vooruit_pdf(
    out_path: str,
    days: List[Dict[str, Any]],
    persons: int,
    shopping_list: List[Dict[str, Any]],
    title: str = "PeetKiest Vooruit",
) -> str:
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    def header(page_title: str):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, h - 60, page_title)
        c.setFont("Helvetica", 10)
        c.drawString(50, h - 78, f"Voor {persons} persoon/personen • {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    def wrap_lines(text: str, max_chars: int = 95) -> List[str]:
        text = text.replace("\n", " ").strip()
        if not text:
            return []
        words = text.split()
        lines, line = [], []
        for w0 in words:
            trial = (" ".join(line + [w0])).strip()
            if len(trial) <= max_chars:
                line.append(w0)
            else:
                lines.append(" ".join(line))
                line = [w0]
        if line:
            lines.append(" ".join(line))
        return lines

    # Pagina per dag
    for d in days:
        day_no = int(d.get("day", 0) or 0)
        kitchen = _safe_str(d.get("kitchen", ""))
        dish_name = _safe_str(d.get("dish_name", ""))
        nutrition = d.get("nutrition", {}) or {}
        ingredients = d.get("ingredients", []) or []
        prep = d.get("preparation", []) or []

        header(f"{title} • Dag {day_no}")
        y = h - 115

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, dish_name)
        y -= 18

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Keuken: {kitchen}")
        y -= 16

        c.setFont("Helvetica", 11)
        kcal = nutrition.get("calories_kcal", 0)
        p = nutrition.get("protein_g", 0)
        f = nutrition.get("fat_g", 0)
        cb = nutrition.get("carbs_g", 0)
        c.drawString(50, y, f"Voeding (per gerecht, schatting toegestaan): {kcal} kcal • P {p} g • V {f} g • KH {cb} g")
        y -= 22

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Ingrediënten")
        y -= 16

        c.setFont("Helvetica", 10)
        for ing in ingredients:
            amount = _safe_str(ing.get("amount", "")) if isinstance(ing, dict) else ""
            item = _safe_str(ing.get("item", "")) if isinstance(ing, dict) else _safe_str(ing)
            line = f"• {amount} {item}".strip()
            if y < 70:
                c.showPage()
                header(f"{title} • Dag {day_no} (vervolg)")
                y = h - 115
                c.setFont("Helvetica", 10)
            c.drawString(55, y, line[:120])
            y -= 13

        y -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Zo pak je het aan")
        y -= 16

        c.setFont("Helvetica", 10)
        step_no = 1
        for step in prep:
            for ln in wrap_lines(_safe_str(step), max_chars=100):
                if y < 70:
                    c.showPage()
                    header(f"{title} • Dag {day_no} (vervolg)")
                    y = h - 115
                    c.setFont("Helvetica", 10)
                prefix = f"{step_no}. " if ln == wrap_lines(_safe_str(step), 100)[0] else "   "
                c.drawString(55, y, (prefix + ln)[:130])
                y -= 13
            step_no += 1

        c.showPage()

    # Shopping list pagina
    header(f"{title} • Boodschappenlijst")
    y = h - 115

    # Groepeer per zone
    by_zone: Dict[str, List[Dict[str, Any]]] = {z: [] for z in ZONES_ORDER}
    other: List[Dict[str, Any]] = []

    for it in shopping_list:
        zone = _safe_str(it.get("zone", "Overig")) or "Overig"
        if zone in by_zone:
            by_zone[zone].append(it)
        else:
            other.append(it)

    def draw_zone(zone: str, items: List[Dict[str, Any]], y0: int) -> int:
        y1 = y0
        if not items:
            return y1
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y1, zone)
        y1 -= 16
        c.setFont("Helvetica", 10)
        for it in items:
            item = _safe_str(it.get("item", ""))
            amount = _safe_str(it.get("amount", ""))
            line = f"• {item} — {amount}".strip(" —")
            if y1 < 70:
                c.showPage()
                header(f"{title} • Boodschappenlijst (vervolg)")
                y1 = h - 115
                c.setFont("Helvetica", 10)
            c.drawString(55, y1, line[:130])
            y1 -= 13
        y1 -= 6
        return y1

    for zone in ZONES_ORDER:
        y = draw_zone(zone, by_zone.get(zone, []), y)

    if other:
        y = draw_zone("Overig", other, y)

    c.save()
    return out_path
