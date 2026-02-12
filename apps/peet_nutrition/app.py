import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


import os
import json
import re
from io import BytesIO

import streamlit as st
from openai import OpenAI


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from core.nutrition_prompt import NUTRITION_SYSTEM_PROMPT


# ----------------------------
# OpenAI client (Streamlit Cloud compatible)
# ----------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY ontbreekt in Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)


# ----------------------------
# Helpers
# ----------------------------
def _extract_json(text: str) -> dict:
    """
    Robuuste JSON extractie.
    Pakt het eerste '{' en de laatste '}' en probeert dat te parsen.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Lege model-output.")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Geen JSON gevonden in model-output.")

    candidate = text[start : end + 1].strip()
    return json.loads(candidate)


def _validate_result(data: dict) -> dict:
    """
    Minimale validatie, zodat UI/PDF niet crasht.
    """
    if not isinstance(data, dict):
        raise ValueError("Resultaat is geen dict.")

    required_top = ["dish_name", "kitchen", "nutrition", "ingredients", "steps"]
    for k in required_top:
        if k not in data:
            raise ValueError(f"JSON mist veld: {k}")

    n = data.get("nutrition", {})
    for k in ["calories_kcal", "protein_g", "fat_g", "carbs_g"]:
        if k not in n:
            raise ValueError(f"nutrition mist veld: {k}")

    if not isinstance(data.get("ingredients"), list) or not data["ingredients"]:
        raise ValueError("ingredients moet een niet-lege lijst zijn.")

    if not isinstance(data.get("steps"), list) or not data["steps"]:
        raise ValueError("steps moet een niet-lege lijst zijn.")

    return data


def safe_filename(title: str) -> str:
    if not title:
        return "nutrition-plan.pdf"
    name = title.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return f"{name}.pdf"


def build_pdf(result: dict, moment: str, max_kcal: int) -> BytesIO:
    buf = BytesIO()
    from reportlab.lib import colors

    styles = getSampleStyleSheet()

    styles["Title"].textColor = colors.HexColor("#0f766e")
    styles["Heading2"].textColor = colors.HexColor("#0f766e")
    styles["BodyText"].textColor = colors.HexColor("#111827")

    story = []

    dish = result.get("dish_name", "").strip()
    kitchen = result.get("kitchen", "").strip()
    n = result.get("nutrition", {})

    story.append(Paragraph(dish, styles["Title"]))
    story.append(Spacer(1, 10))

    meta = f"Moment: {moment} | Richtwaarde: max {max_kcal} kcal | Keuken: {kitchen}"
    story.append(Paragraph(meta, styles["BodyText"]))
    story.append(Spacer(1, 12))

    macros = (
        f"Kcal: {n.get('calories_kcal')} | "
        f"Eiwit: {n.get('protein_g')} g | "
        f"Vet: {n.get('fat_g')} g | "
        f"Koolhydraten: {n.get('carbs_g')} g"
    )
    story.append(Paragraph(macros, styles["BodyText"]))
    story.append(Spacer(1, 14))

    # Ingrediënten
    story.append(Paragraph("Ingrediënten", styles["Heading2"]))
    ing_lines = []
    for i in result.get("ingredients", []):
        if isinstance(i, dict):
            item = (i.get("item") or "").strip()
            amt = (i.get("amount") or "").strip()
            if item and amt:
                ing_lines.append(f"{item} – {amt}")
            elif item:
                ing_lines.append(item)
        else:
            ing_lines.append(str(i))

    story.append(
        ListFlowable(
            [ListItem(Paragraph(x, styles["BodyText"])) for x in ing_lines],
            bulletColor=colors.HexColor("#0f766e"),
            bulletType="bullet",
            leftIndent=14,
        )
    )
    story.append(Spacer(1, 16))

    # Bereiding
    story.append(Paragraph("Bereiding", styles["Heading2"]))
    for step in result.get("steps", []):
        story.append(Paragraph(str(step), styles["BodyText"]))
        story.append(Spacer(1, 6))

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )
    doc.build(story)
    buf.seek(0)
    return buf


def call_nutrition(moment: str, max_kcal: int, hint: str) -> dict:
    # User context blijft klein en helder, de system prompt doet het zware werk.
    user_context = {
        "moment": moment,
        "max_calories_kcal": max_kcal,
    }
    if hint.strip():
        user_context["hint"] = hint.strip()

    resp = client.responses.create(
        model=MODEL,
        temperature=0.3,
        input=[
            {"role": "system", "content": NUTRITION_SYSTEM_PROMPT.strip()},
            {"role": "user", "content": json.dumps(user_context, ensure_ascii=False)},
        ],
    )

    data = _extract_json(resp.output_text)
    return _validate_result(data)


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Peet – Nutrition", layout="centered")

# ----------------------------
# FIT / SPORT / DOELGERICHTE STYLING (SCHOON)
# ----------------------------
st.markdown("""
<style>

/* Pagina achtergrond */
section.main {
    background-color: #f2f4f7;
    padding-top: 3rem;
}

/* Centrale coach-card */
.block-container {
    max-width: 900px;
    background: #ffffff;
    padding: 2.5rem 2.75rem;
    border-radius: 18px;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.15);
}

/* Titels */
h1 {
    font-weight: 700;
    color: #1f2933;
}

h2, h3 {
    color: #1f2933;
}

/* Subtitel / captions */
.stCaption {
    color: #6b7280;
}

/* CTA button – professioneel petrol */
div.stButton > button {
    background: linear-gradient(90deg, #0f766e, #115e59);
    color: #ffffff;
    font-weight: 600;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    border: none;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #115e59, #0f766e);
    color: #ffffff;
}

/* Accentkleur (fit / sport) */
:root {
    --accent: #0f766e; /* fris sport-groen */
}

/* Radio buttons (moment) */
div[role="radiogroup"] label[data-checked="true"] {
    color: var(--accent);
    font-weight: 600;
}

/* Slider thumb */
input[type=range]::-webkit-slider-thumb {
    background-color: var(--accent);
}

/* Doel-header (DINER • 640 KCAL) */
.goal-header {
    font-size: 0.8rem;
    letter-spacing: 0.12em;
    color: #6b7280;
    margin-bottom: 0.4rem;
}

/* Macro dashboard */
.macro-line {
    font-weight: 600;
    letter-spacing: 0.3px;
    color: #111827;
    margin: 0.75rem 0 1.25rem 0;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# Titel
# ----------------------------
st.title("Peet – Nutrition")
st.caption("Eten dat past bij je doel.")

# ----------------------------
# Moment-keuze
# ----------------------------
moment = st.radio(
    "Moment",
    ["Ontbijt", "Lunch", "Diner"],
    horizontal=True,
    label_visibility="collapsed",
)

# ----------------------------
# Calorie-budget
# ----------------------------
max_kcal = st.slider(
    "Calorie-budget voor deze maaltijd",
    min_value=250,
    max_value=900,
    step=25,
    value=450,
)

st.markdown(
    f"""
<div style="background:linear-gradient(90deg,#0f766e,#115e59);color:white;padding:14px 18px;border-radius:12px;margin:1.2rem 0 1.6rem 0;">
  <div style="font-size:0.75rem;letter-spacing:0.12em;opacity:0.9;">
    JOUW {moment.upper()}
  </div>
  <div style="font-size:1.15rem;font-weight:600;margin-top:2px;">
    Maximaal {max_kcal} kcal · gericht op jouw doel
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# Optionele hint
# ----------------------------
hint = st.text_input(
    "Optionele hint (smaak of ingrediënt)",
    placeholder="Bijv. iets Aziatisch, kip, vegetarisch, kruidig, fris, tomaat",
)


# ----------------------------
# CTA (coachend) + call
# ----------------------------
cta_label = f"Maak mijn {moment.lower()}"

if st.button(cta_label.capitalize(), use_container_width=True):
    # Reset alleen bij nieuwe actie
    st.session_state.result = None

    with st.spinner("Even kiezen..."):
        try:
            result = call_nutrition(moment, max_kcal, hint)
            st.session_state.result = result

        except Exception as e:
            msg = str(e)

            if "insufficient_quota" in msg or "429" in msg:
                st.error("API-limiet bereikt. Probeer later opnieuw.")
            elif "authentication" in msg.lower() or "api_key" in msg.lower():
                st.error("OpenAI-sleutel ontbreekt of is ongeldig.")
            else:
                st.error("Er ging iets mis bij het genereren. Probeer nog eens.")

            with st.expander("Technische info"):
                st.write(msg)

            st.stop()

# ----------------------------
# Resultaat tonen (performance-modus)
# ----------------------------
result = st.session_state.get("result")
if isinstance(result, dict):

    dish = result.get("dish_name", "")
    kitchen = result.get("kitchen", "")
    n = result.get("nutrition", {})

    calories = n.get("calories_kcal")
    protein = n.get("protein_g")
    fat = n.get("fat_g")
    carbs = n.get("carbs_g")

    # Focus header
    st.markdown(
        f"""
        <div style="
            margin:1rem 0 1.2rem 0;
            padding:0.9rem 1.1rem;
            background:#ecfdf3;
            border-left:5px solid #0f766e;
            border-radius:8px;
            font-size:0.9rem;
            color:#065f46;
            font-weight:600;
        ">
            Vandaag eet je <strong>{moment.lower()}</strong> • maximaal <strong>{max_kcal} kcal</strong>
        </div>
        """,
        unsafe_allow_html=True
    )


    # Macro score (compact)
    st.markdown(
        f"""
        <div style="
            margin:0.6rem 0 1rem 0;
            font-size:0.85rem;
            color:#334155;
        ">
            <b>{calories} kcal</b> ·
            {protein}g eiwit ·
            {fat}g vet ·
            {carbs}g kh
        </div>
        """,
        unsafe_allow_html=True
    )

    # Gerecht
    st.markdown(f"""
    <h2 style="margin-top:0.6rem;margin-bottom:0.2rem;">
        {dish}
    </h2>
    <div style="color:#64748b;font-size:0.85rem;margin-bottom:0.4rem;">
        {moment.capitalize()} • {kitchen}
    </div>
    <div style="color:#64748b;font-size:0.85rem;margin-bottom:0.8rem;">
        Licht, eiwitrijk en passend bij je doel.
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # Ingrediënten – 2 kolommen, compact
    # ----------------------------
    st.subheader("Ingrediënten")

    ingredients = result.get("ingredients", [])

    # Normaliseer naar (item, amount)
    rows = []
    for i in ingredients:
        if isinstance(i, dict):
            item = (i.get("item") or "").strip()
            amt = (i.get("amount") or "").strip()
            if item:
                rows.append((item, amt))
        else:
            rows.append((str(i), ""))

    half = (len(rows) + 1) // 2
    left = rows[:half]
    right = rows[half:]

    col1, col2 = st.columns(2)

    def render_items(col, data):
        with col:
            for item, amt in data:
                if amt:
                    html = f"""
                    <div style="margin:2px 0;font-size:0.9rem;line-height:1.3;">
                        <b>{item}</b>
                        <span style="color:#64748b"> – {amt}</span>
                    </div>
                    """
                else:
                    html = f"""
                    <div style="margin:2px 0;font-size:0.9rem;line-height:1.3;">
                        <b>{item}</b>
                    </div>
                    """
                st.markdown(html, unsafe_allow_html=True)

    render_items(col1, left)
    render_items(col2, right)

    # ----------------------------
    # Bereiding
    # ----------------------------
    steps = result.get("steps", [])

    if steps:
        st.subheader("Bereiding")

        st.subheader("Zo maak je het")

        for i, step in enumerate(steps, start=1):
            prefix = "Begin:" if i == 1 else f"Stap {i}:"
            st.markdown(f"""
            <div style="
                margin:6px 0;
                padding:6px 10px;
                background:#f8fafc;
                border-left:3px solid #0f766e;
                border-radius:6px;
                font-size:0.95rem;
            ">
                <b>{prefix}</b> {step}
            </div>
            """, unsafe_allow_html=True)

    # PDF
    pdf_buf = build_pdf(result, moment=moment, max_kcal=max_kcal)
    filename = safe_filename(result.get("dish_name", ""))

    st.download_button(
        label="Download PDF (recept + macro’s)",
        data=pdf_buf.getvalue(),
        file_name=filename,
        mime="application/pdf",
        use_container_width=True,
    )
