import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Loop omhoog tot we de map met "core" vinden
while not (PROJECT_ROOT / "core").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



# -------------------------------------------------
# Imports
# -------------------------------------------------
import json
import hashlib
import os
import streamlit as st

from core.llm import call_peet_text
from peet_engine.engine import plan
from peet_engine.render_pdf import build_plan_pdf
from core.image_generator import generate_food_image


# -------------------------------------------------
# Query helpers
# -------------------------------------------------
def qp(name: str, default=""):
    v = st.query_params.get(name, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


def to_int(val, default):
    try:
        return int(str(val).strip())
    except Exception:
        return default


def to_list(val):
    if not val:
        return []
    return [p.strip().lower() for p in str(val).split(",") if p.strip()]


# -------------------------------------------------
# Context builder (vrije Peet-stijl)
# -------------------------------------------------
def build_llm_context():

    days = to_int(qp("days", "1"), 1)
    if days in (2, 3, 5):
        return "__FORWARD__"

    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))

    moment = qp("moment")
    kitchen = qp("kitchen")
    preference = qp("preference")
    vegetarian = qp("vegetarian")
    time_raw = qp("time")
    # -----------------------------
    # Kooktijd interpretatie
    # -----------------------------
    cook_time_text = ""

    if time_raw == "20":
        cook_time_text = "Het gerecht moet binnen maximaal 20 minuten klaar zijn."

    elif time_raw in ["30-45", "30_45", "30–45"]:
        cook_time_text = "Het gerecht moet binnen ongeveer 30 tot 45 minuten klaar zijn."

    elif time_raw in [">45", "45+", "meer dan 45"]:
        cook_time_text = "Het gerecht mag langer duren en mag uitgebreider zijn."

    allergies = to_list(qp("allergies"))
    nogo = to_list(qp("nogo"))

    lines = [
        "CONTEXT VANDAAG:",
        f"- persons: {persons}",
    ]

    if cook_time_text:
        lines.append(f"- kooktijd: {cook_time_text}")

    if moment:
        lines.append(f"- moment: {moment}")

    if kitchen:
        lines.append(f"- kitchen (inspiratie): {kitchen}")

    if preference:
        lines.append(f"- preference (inspiratie): {preference}")

    if vegetarian:
        lines.append(f"- vegetarian: {vegetarian}")

    if allergies:
        lines.append(f"- allergies: {', '.join(allergies)}")

    if nogo:
        lines.append(f"- no-go: {', '.join(nogo)}")

    lines.extend([
        "",
        "KIES VRIJ.",
        "GEEN STANDAARDGERECHTEN.",
        "GEEN HERHALING.",
        "RESPECTEER VEGETARISCH, ALLERGIEËN EN NO-GO’S VOLLEDIG."
    ])

    return "\n".join(lines)


# -------------------------------------------------
# Cached LLM call
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_peet_choice(context_text: str):
    return call_peet_text(context_text)



# -------------------------------------------------
# JSON parser (Peet Card contract)
# -------------------------------------------------
def parse_llm_output(raw_llm: str):
    """
    Verwacht geldige JSON volgens vaste structuur.
    Altijd veilige defaults.
    """

    try:
        data = json.loads(raw_llm)
    except Exception:
        return "", [], [], None, {}

    # -------------------------
    # Gerechtnaam
    # -------------------------
    dish_name = data.get("dish_name", "")

    # -------------------------
    # Nutrition
    # -------------------------
    nutrition = data.get("nutrition", {})

    calories = nutrition.get("calories_kcal", None)

    protein_g = nutrition.get("protein_g", 0)
    fat_g = nutrition.get("fat_g", 0)
    carbs_g = nutrition.get("carbs_g", 0)

    macro_ratio = nutrition.get("macro_ratio", {})

    protein_pct = macro_ratio.get("protein_pct", 0)
    fat_pct = macro_ratio.get("fat_pct", 0)
    carbs_pct = macro_ratio.get("carbs_pct", 0)

    nutrition_clean = {
        "calories_kcal": calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
        "macro_ratio": {
            "protein_pct": protein_pct,
            "fat_pct": fat_pct,
            "carbs_pct": carbs_pct,
        },
    }

    # -------------------------
    # Ingrediënten
    # -------------------------
    ingredients = data.get("ingredients", [])

    if not isinstance(ingredients, list):
        ingredients = []

    # -------------------------
    # Bereiding
    # -------------------------
    steps = data.get("steps", [])

    if not steps:
        steps = data.get("preparation", [])

    if not isinstance(steps, list):
        steps = []

    return dish_name, ingredients, steps, calories, nutrition_clean
# -------------------------------------------------
# CSS styling (Roboto Condensed)
# -------------------------------------------------
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@300;400;700&display=swap');

    html, body, [class*="css"], p, div, span {
        font-family: 'Roboto Condensed', sans-serif;
        font-weight: 400;
    }

    h1, h2, h3, h4, h5 {
        font-family: 'Roboto Condensed', sans-serif;
        font-weight: 700;
        letter-spacing: 0.2px;
    }

    /* iets compacter gevoel zoals PDF */
    p {
        line-height: 1.35;
    }

    /* Ingrediënten strakker in kolommen */

    .ingredients-list {
        margin-top: 8px;
    }

    .ingredients-row {
        display: flex;
        gap: 12px;
        margin-bottom: 4px;
    }

    .ingredients-amount {
        min-width: 90px;
        font-weight: 500;
        color: #222;
    }

    .ingredients-item {
        flex: 1;
    }

    </style>
    """, unsafe_allow_html=True)

#--------------------------------------------------
# Extra helpers
#--------------------------------------------------
@st.cache_resource(show_spinner=False)
def async_generate_image(dish_name):
    return generate_food_image(dish_name)

# -------------------------------------------------
# Main app
# -------------------------------------------------
def main():
    calories = None

    st.set_page_config(
        page_title="Peet kiest",
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items={}
    )

    inject_css()

    st.markdown("<h1>Peet gaat voor je kiezen.</h1>", unsafe_allow_html=True)
    st.caption("Iedere dag weer anders. Iedere keer weer iets lekkers.")

    # -------------------------------------------------
    # Build context
    # -------------------------------------------------
    llm_context = build_llm_context()

    if llm_context == "__FORWARD__":
        st.warning("Voor meerdere dagen: gebruik Peet Kiest Vooruit.")
        st.stop()

    # -------------------------------------------------
    # Signature → nieuwe keuze bij andere input
    # -------------------------------------------------
    context_sig = hashlib.md5(llm_context.encode("utf-8")).hexdigest()

    if st.session_state.get("context_sig") != context_sig:

        st.session_state["context_sig"] = context_sig

        with st.spinner(
            "We hebben meer dan 1 miljoen gerechten en Peet zoekt nu de allerlekkerste voor je uit…"
        ):
            st.session_state["raw_llm"] = fetch_peet_choice(llm_context)

        st.session_state.pop("pdf_path", None)

    raw_llm = st.session_state.get("raw_llm")

    if not raw_llm:
        st.info("Peet is een gerecht aan het kiezen…")
        st.stop()


    # -------------------------------------------------
    # Parse LLM output
    # -------------------------------------------------
    dish_name, ingredients, preparation, calories, nutrition = parse_llm_output(raw_llm)

    if not dish_name:
        st.error("Er ging iets mis bij het verwerken van het gerecht.")
        return

    # -------------------------
    # Calorieën normaliseren
    # -------------------------
    calories_kcal = None
    if calories is not None:
        try:
            calories_kcal = int(float(str(calories).strip()))
        except Exception:
            calories_kcal = None


    # -------------------------
    # Macro’s ophalen
    # -------------------------
    protein_g = nutrition.get("protein_g", 0)
    fat_g = nutrition.get("fat_g", 0)
    carbs_g = nutrition.get("carbs_g", 0)

    # -------------------------
    # Percentages altijd zelf berekenen
    # -------------------------
    protein_pct = 0
    fat_pct = 0
    carbs_pct = 0

    try:
        protein_kcal = protein_g * 4
        carbs_kcal = carbs_g * 4
        fat_kcal = fat_g * 9

        total_kcal = protein_kcal + carbs_kcal + fat_kcal

        if total_kcal > 0:
            protein_pct = round(protein_kcal / total_kcal * 100)
            fat_pct = round(fat_kcal / total_kcal * 100)
            carbs_pct = round(carbs_kcal / total_kcal * 100)

    except Exception:
        pass

    # -------------------------------------------------
    # Engine call
    # -------------------------------------------------
    persons = max(1, min(12, to_int(qp("persons", "2"), 2)))

    engine_context = {
        "days": 1,
        "persons": persons,
        "dish_name": dish_name,
        "allergies": to_list(qp("allergies")),
        "nogo": to_list(qp("nogo")),
    }

    result = plan(engine_context)

    days = result.get("days", [])
    days_count = result.get("days_count", len(days))

    if not days:
        st.error("Geen gerecht gegenereerd.")
        return

    # Verrijk dag 1 met LLM details
    days[0].update({
        "dish_name": dish_name,
        "ingredients": ingredients,
        "preparation": "\n".join(preparation),
    })

    # -------------------------------------------------
    # Screen rendering
    # -------------------------------------------------
    st.subheader(dish_name)
    st.divider()

    # -------------------------
    # Afbeelding (on demand – stabiel & snel UX)
    # -------------------------
    img_slot = st.empty()

    if "image_path" not in st.session_state:
        st.session_state["image_path"] = None

    if st.button("Toon afbeelding van dit gerecht"):

        with st.spinner("Peet zet het gerecht alvast op tafel…"):
            image_path = async_generate_image(dish_name)
            st.session_state["image_path"] = image_path

    if st.session_state["image_path"] and os.path.exists(st.session_state["image_path"]):
        img_slot.image(st.session_state["image_path"], use_column_width=True)

    image_path = st.session_state["image_path"]

    # -------------------------
    # Calorieën + macro’s
    # -------------------------
    if calories_kcal is not None:

        st.caption(f"Bevat {calories_kcal} kcal")

        st.markdown(
            f"""
    **Eiwit:** {protein_g} g ({protein_pct}%)  
    **Vet:** {fat_g} g ({fat_pct}%)  
    **Koolhydraten:** {carbs_g} g ({carbs_pct}%)
    """
        )

    # -------------------------
    # Ingrediënten
    # -------------------------
    st.subheader(f"Ingrediënten (voor {persons} personen)")

    if ingredients:

        st.markdown('<div class="ingredients-list">', unsafe_allow_html=True)


    for ing in ingredients:

        amount = ""
        item = ""

        # Nieuwe JSON structuur (dict)
        if isinstance(ing, dict):

            amount = str(ing.get("amount", "")).strip()
            item = str(ing.get("item", "")).strip()

        # Oude string structuur
        elif isinstance(ing, str):

            import re

            text = ing.strip()

            amount = ""
            item = ""

            # 1) Pak hoeveelheid vooraan
            m = re.match(
                r"^([\d.,\/\-\s]*(?:g|kg|ml|l|tl|el|teen|snuf|blokje|stuk|stuks)?(?:\s*\(.*?\))?)\s*(.*)$",
                text,
                re.IGNORECASE
            )

            if not m:
                amount = ""
                item = text

            else:
                amount = m.group(1).strip()
                rest = m.group(2).strip()

                # 2) Alles na komma’s = toevoegingen
                parts = [p.strip() for p in rest.split(",")]

                core = parts[0]
                extras = parts[1:]

                # 3) Zet toevoegingen altijd achteraan
                if extras:
                    item = core + ", " + ", ".join(extras)
                else:
                    item = core

        # Render alleen als er iets zinnigs staat
        if item:

            st.markdown(
                f"""
                <div class="ingredients-row">
                    <div class="ingredients-amount">{amount}</div>
                    <div class="ingredients-item">{item}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


    else:
        st.write("Geen ingrediënten beschikbaar.")

    # -------------------------
    # Bereiding
    # -------------------------
    if cook_time_min == cook_time_max:
        st.subheader(f"Zo pak je het aan, reken op ± {cook_time_max} min")
    else:
        st.subheader(f"Zo pak je het aan, reken op ± {cook_time_min}–{cook_time_max} min")

    prep_text = days[0].get("preparation", "").strip()

    if prep_text:
        for step in [s for s in prep_text.split("\n") if s.strip()]:
            st.write(step)
    else:
        st.write("Bereiding niet beschikbaar.")


    # -------------------------------------------------
    # PDF (eerst zonder beeld, later automatisch met beeld)
    # -------------------------------------------------
    has_image = bool(image_path and os.path.exists(image_path))

    if ("pdf_path" not in st.session_state) or (has_image and not st.session_state.get("_pdf_has_image", False)):

        st.session_state["pdf_path"] = build_plan_pdf(
            dish_name=dish_name,
            nutrition=nutrition,
            ingredients=ingredients,
            preparation=preparation,
            image_path=image_path if has_image else None
        )

        st.session_state["_pdf_has_image"] = has_image
         
    pdf_path = st.session_state["pdf_path"]

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download als PDF",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
            )

if __name__ == "__main__":
    main()
