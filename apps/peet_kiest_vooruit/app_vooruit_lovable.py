import sys
import os

# =========================================================
# PROJECT ROOT FIX (nodig voor imports uit /core)
# =========================================================
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =========================================================
# STANDAARD IMPORTS
# =========================================================
import json
import re
import base64
from io import BytesIO
from datetime import date

import streamlit as st
from openai import OpenAI

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.prompts import PEET_KIEST_VOORUIT_PROMPT

# =========================================================
# PAGE CONFIG (MOET ALS EERSTE)
# =========================================================
st.set_page_config(
    page_title="Peet Kiest – Vooruit",
    layout="centered"
)

# =========================================================
# GLOBAL STYLING
# =========================================================
st.markdown("""
<style>
.block-container { max-width: 680px; padding-top: 2.5rem; padding-bottom: 3rem; }
html, body, [class*="css"] { font-size: 17px; line-height: 1.55; }
h1 { font-size: 1.9rem; font-weight: 600; margin-bottom: 0.9rem; }
h2 { font-size: 1.4rem; font-weight: 600; margin-top: 2.2rem; margin-bottom: 0.6rem; }
h3 { font-size: 1.1rem; font-weight: 600; margin-top: 1.6rem; }
p { margin-bottom: 1.1rem; }
.stButton > button { width: 100%; padding: 0.75rem; font-size: 1rem; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# IMPORT PROMPT
# =========================================================
from core.prompts import PEET_KIEST_VOORUIT_PROMPT

# =========================================================
# CONFIG
# =========================================================
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================================================
# URL PARAMETERS (LOVABLE VOORDEUR)
# =========================================================
params = st.query_params

# days
try:
    days_from_url = int(params.get("days"))
    if days_from_url not in [1, 2, 3, 4, 5]:
        days_from_url = None
except Exception:
    days_from_url = None

# people
try:
    people_from_url = int(params.get("people"))
    if people_from_url < 1 or people_from_url > 10:
        people_from_url = 2
except Exception:
    people_from_url = 2

# =========================================================
# SESSION STATE
# =========================================================
if "result" not in st.session_state:
    st.session_state.result = None

# =========================================================
# HELPERS
# =========================================================
def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Geen JSON gevonden in model-output.")
    return json.loads(text[start:end + 1])

def call_peet(context: str) -> dict:
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": PEET_KIEST_VOORUIT_PROMPT},
            {"role": "user", "content": context},
        ],
    )
    return _extract_json(resp.output_text)

def generate_dish_image_bytes(dish_name: str) -> bytes | None:
    try:
        img = client.images.generate(
            model="gpt-image-1",
            prompt=(
                f"Fotografisch realistisch gerecht: {dish_name}. "
                "Warm natuurlijk licht, thuiskeuken, op een bord. "
                "Geen tekst, geen mensen, geen handen."
            ),
            size="1024x1024",
        )
        return base64.b64decode(img.data[0].b64_json)
    except Exception:
        return None

# =========================================================
# HEADER
# =========================================================
st.title("Peet Kiest – Vooruit")
st.caption("Meerdere dagen geregeld. Geen planning. Geen stress.")

# =========================================================
# FORM
# =========================================================
with st.form("context"):
    day_options = [1, 2, 3, 4, 5]
    default_day_index = (
        day_options.index(days_from_url)
        if days_from_url in day_options
        else 0
    )

    days = st.selectbox(
        "Voor hoeveel dagen zal ik kiezen?",
        day_options,
        index=default_day_index
    )

    people = st.number_input(
        "Hoeveel mensen schuiven er aan?",
        min_value=1,
        max_value=10,
        value=people_from_url
    )

    veggie = st.selectbox(
        "Wil je vegetarisch eten?",
        ["Nee, laat Peet kiezen", "Ja, vegetarisch"],
    )

    keuken = st.selectbox(
        "Moet ik aan een bepaalde keuken denken?",
        [
            "Laat Peet beslissen",
            "Nederlands / Belgisch",
            "Frans",
            "Italiaans",
            "Mediterraan",
            "Aziatisch",
            "Midden-Oosters",
        ],
    )

    extra_ingredient = st.text_input(
        "Heb je al iets in huis waar ik rekening mee kan houden?",
        placeholder="Bijvoorbeeld prei, kip, feta…"
    )

    no_gos = st.text_input(
        "Is er iets dat ik beter niet kan gebruiken?",
        placeholder="Allergie of liever niet…"
    )

    submitted = st.form_submit_button("Peet, neem het over")

# =========================================================
# CALL PEET
# =========================================================
if submitted:
    st.session_state.result = None

    context = f"""
DATUM: {date.today().isoformat()}
AANTAL DAGEN: {days}
AANTAL PERSONEN: {people}
STANDAARD TIJD: 30 minuten
KEUKENVOORKEUR: {keuken}
OPTIONEEL INGREDIËNT: {extra_ingredient}
NO-GOS: {no_gos}
""".strip()

    st.markdown("**Goed. Ik regel dit voor je.**")

    with st.spinner("Peet zet het voor je klaar…"):
        try:
            st.session_state.result = call_peet(context)
        except Exception as e:
            st.error("Peet raakte even de draad kwijt. Probeer het opnieuw.")
            st.stop()

# =========================================================
# RESULT
# =========================================================
result = st.session_state.get("result")
if not result:
    st.stop()

for day in result.get("days", []):
    st.markdown(f"## Dag {day['day']}")
    st.markdown(f"**{day['screen8']['dish_name']}**")

    if day.get("description"):
        st.markdown(day["description"])

    if st.button(f"Laat een foto zien (Dag {day['day']})", key=f"img_{day['day']}"):
        img = generate_dish_image_bytes(day["screen8"]["dish_name"])
        if img:
            st.image(img, width="stretch")

    st.divider()
