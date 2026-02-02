import os
import json
import re
from io import BytesIO
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from core.nutrition_prompt import NUTRITION_SYSTEM_PROMPT


# ----------------------------
# Env + OpenAI client
# ----------------------------
ROOT = Path(__file__).resolve().parents[1]  # ...\peet_nutrion_app
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY ontbreekt. Zet hem in .env in de project root.")

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
    styles = getSampleStyleSheet()
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
st.set_page_config(page_title="Nutrition Planner", layout="centered")

if "last_request_key" not in st.session_state:
    st.session_state.last_request_key = None
if "result" not in st.session_state:
    st.session_state.result = None

st.title("Nutrition Planner")
st.caption("Echte gerechten, slim gestuurd op calorieën en macro’s. Volledig los van PeetKiest.")

moment = st.radio("Wanneer eet je dit?", ["Ontbijt", "Lunch", "Diner"], horizontal=True)

max_kcal = st.slider(
    "Maximale calorieën voor dit gerecht",
    min_value=250,
    max_value=900,
    step=25,
    value=450,
)

hint = st.text_input(
    "Optionele hint (smaak of ingrediënt)",
    placeholder="Bijv. iets Aziatisch, kip, vegetarisch, kruidig, fris, tomaat",
)

# Request key om dubbele calls te beperken
request_key = json.dumps(
    {"moment": moment, "max_kcal": max_kcal, "hint": hint.strip()},
    sort_keys=True,
    ensure_ascii=False,
)

if st.button("Kies een gerecht", use_container_width=True):
    st.session_state.result = None
    st.session_state.last_request_key = request_key

    with st.spinner("Even kiezen..."):
        try:
            st.session_state.result = call_nutrition(moment, max_kcal, hint)
        except Exception as e:
            msg = str(e)
            if "insufficient_quota" in msg or "429" in msg:
                st.error("API limiet op. Probeer later opnieuw.")
            elif "authentication" in msg.lower() or "api_key" in msg.lower():
                st.error("OpenAI sleutel klopt niet. Check je .env (OPENAI_API_KEY).")
            else:
                st.error("Er ging iets mis bij het genereren. Probeer nog eens.")
            with st.expander("Technische info", expanded=False):
                st.write(msg)
            st.stop()

# Resultaat tonen
result = st.session_state.get("result")
if isinstance(result, dict):
    dish = result.get("dish_name", "")
    kitchen = result.get("kitchen", "")
    n = result.get("nutrition", {})

    st.header(dish)
    st.caption(f"Keuken: {kitchen}")

    st.markdown(
        f"**Kcal:** {n.get('calories_kcal')}  \n"
        f"**Eiwit:** {n.get('protein_g')} g  \n"
        f"**Vet:** {n.get('fat_g')} g  \n"
        f"**Koolhydraten:** {n.get('carbs_g')} g"
    )

    st.subheader("Ingrediënten")
    lines = []
    for i in result.get("ingredients", []):
        if isinstance(i, dict):
            item = (i.get("item") or "").strip()
            amt = (i.get("amount") or "").strip()
            if item and amt:
                lines.append(f"- **{item}** – {amt}")
            elif item:
                lines.append(f"- **{item}**")
        else:
            lines.append(f"- {i}")
    st.markdown("\n".join(lines))

    st.subheader("Bereiding")
    for step in result.get("steps", []):
        st.markdown(f"- {step}")

    st.divider()

    pdf_buf = build_pdf(result, moment=moment, max_kcal=max_kcal)
    filename = safe_filename(result.get("dish_name", ""))

    st.download_button(
        label="Download PDF (recept + macro’s)",
        data=pdf_buf.getvalue(),
        file_name=filename,
        mime="application/pdf",
        use_container_width=True,
    )

