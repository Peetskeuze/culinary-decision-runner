from __future__ import annotations

from core.peet_theme import render_peet_hero

import json
import os
import hashlib
import requests
import urllib.parse
import streamlit as st

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


from core.llm import call_peet_vooruit
from apps.Peet_Kiest_Vooruit.vooruit_context import (
    parse_query_params,
    compute_kitchen_plan,
    next_rotation_index,
)
from apps.Peet_Kiest_Vooruit.pdf_vooruit import build_vooruit_pdf


# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="PeetKiest Vooruit",
    page_icon="🍽️",
    layout="centered",
)


# -------------------------------------------------
# Helpers
# -------------------------------------------------
import re

def simplify_dish_name(dish_name: str, vegetarian: bool = False) -> str:
    name = dish_name.lower()

    # Hoofdingrediënten eerst (prioriteit!)
    primary_map = {
        "witloof": "chicory endive",
        "zalm": "salmon fillet",
        "kabeljauw": "cod fillet",
        "mosselen": "mussels",
        "boerenkool": "kale",
        "hutspot": "carrot potato mash",
        "stamppot": "mashed potatoes",
    }

    # Secundaire componenten
    secondary_map = {
        "aardappel": "potatoes",
        "puree": "potato puree",
        "friet": "fries",
        "frieten": "fries",
        "prei": "leek",
        "roomsaus": "cream sauce",
        "jus": "gravy",
        "gehakt": "ground beef",
        "worst": "sausage",
        "runderworst": "sausage",
        "champignon": "mushrooms",
    }

    # Vegetarische correctie
    if vegetarian:
        secondary_map.update({
            "worst": "vegetarian sausage",
            "runderworst": "vegetarian sausage",
            "gehakt": "plant based ground beef",
            "jus": "vegetarian gravy",
        })

    primary = None
    secondary = []

    # Zoek primary eerst
    for nl, en in primary_map.items():
        if nl in name:
            primary = en
            break

    # Zoek secundaire ingrediënten
    for nl, en in secondary_map.items():
        if nl in name:
            secondary.append(en)

    keywords = []

    if primary:
        keywords.append(primary)

    if secondary:
        keywords.extend(secondary[:2])  # max 2 extra

    if not keywords:
        keywords.append(name)

    return " ".join(keywords) + " plated restaurant meal close up"


def build_image_url(dish_name: str, vegetarian: bool = False) -> str:
    api_key = os.getenv("PEXELS_API_KEY")

    if not api_key or not dish_name:
        return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1200&q=80"

    search_query = simplify_dish_name(dish_name, vegetarian)

    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={
                "query": search_query,
                "per_page": 5,
                "orientation": "landscape",
                "size": "large",
                "locale": "en-US"
            },
            timeout=5,
        )

        data = response.json()

        if "photos" in data and len(data["photos"]) > 0:
            return data["photos"][0]["src"]["landscape"]

    except Exception:
        pass

    return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1200&q=80"


def _qp(name: str, default: str = "") -> str:
    v = st.query_params.get(name, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


def _qp_dict() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in st.query_params.keys():
        out[k] = _qp(k, "")
    return out


def _safe_json_load(raw: Any) -> Dict[str, Any]:
    try:
        if isinstance(raw, dict):
            return raw
        s = str(raw or "").strip()
        if s.startswith("```"):
            s = s.replace("```json", "").replace("```", "").strip()
        return json.loads(s)
    except Exception:
        return {}


def _ensure_output_dirs() -> Path:
    base = Path("output") / "vooruit"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _signature(inp: Dict[str, Any], rotation_index: int) -> str:
    payload = json.dumps(
        {"inp": inp, "rot": rotation_index},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _build_prompt(context: Dict[str, Any]) -> str:
    days = int(context["days"])
    persons = int(context["persons"])
    vegetarian = bool(context["vegetarian"])
    allergies = context.get("allergies", [])
    nogo = context.get("nogo", [])
    fridge = str(context.get("fridge", "") or "").strip()
    kitchen_plan = context["kitchen_plan"]

    kp_lines = "\n".join(
        [f"- Dag {d}: {kitchen_plan.get(d, 'NL/BE')}" for d in range(1, days + 1)]
    )

    diet_line = "vegetarisch" if vegetarian else "vlees/vis/vega toegestaan"
    allergies_line = ", ".join(allergies) if allergies else "geen"
    nogo_line = ", ".join(nogo) if nogo else "geen"
    fridge_line = fridge if fridge else "niets specifieks"

    return f"""
Je bent PeetKiest Vooruit. Jij maakt een meerdaagse planning. Jij kiest, geen opties.

OUTPUT REGEL:
- Je output is ALLEEN geldige JSON
- Geen markdown, geen tekst buiten JSON

Plan {days} dagen vooruit voor {persons} personen.

KEUKENPLAN:
{kp_lines}

DIEET:
- stijl: {diet_line}
- allergieën: {allergies_line}
- no-go: {nogo_line}
- in huis: {fridge_line}

KWALITEIT:
- Exact 1 gerecht per dag
- Variatie in hoofdcomponent
- Kcal en macro’s verplicht

BEREIDINGSTOON:
- De bereidingswijze is geschreven in Peet-stijl.
- Gebruik de titel: "Zo pakken we het aan"
- Spreek licht begeleidend, alsof Peet naast je staat.
- Geen droge instructies, maar korte, duidelijke zinnen.
- Zelfverzekerd, rustig en praktisch.
- Geen overdreven gezelligheid, geen emoji’s.
- Geen uitleg waarom iets gezond is.
- Gewoon koken, helder en prettig.


JSON SCHEMA:
{{
  "days": [
    {{
      "day": 1,
      "kitchen": "NL/BE",
      "dish_name": "...",
      "nutrition": {{
        "calories_kcal": 0,
        "protein_g": 0,
        "fat_g": 0,
        "carbs_g": 0
      }},
      "ingredients": [{{"amount": "...", "item": "..."}}],
      "preparation": ["..."]
    }}
  ],
  "shopping_list": [
    {{"zone": "AGF", "item": "uien", "amount": "..."}}
  ]
}}
""".strip()


@st.cache_data(show_spinner=False)
def _call_llm_cached(prompt: str) -> str:
    return call_peet_vooruit(prompt, system_prompt=prompt)


def _normalize_day_preparation(day: Dict[str, Any]) -> Dict[str, Any]:
    if "preparation" not in day and "steps" in day:
        day["preparation"] = day.get("steps", [])
        day.pop("steps", None)
    return day


def normalize_vooruit_output(raw: Dict[str, Any], expected_days: int):
    if not isinstance(raw, dict):
        return None

    if isinstance(raw.get("days"), list) and raw["days"]:
        return raw

    if "dish_name" in raw and expected_days > 0:
        days = []
        for i in range(1, expected_days + 1):
            entry = raw.copy()
            entry["day"] = i
            entry.setdefault("kitchen", "")
            days.append(entry)
        return {"days": days, "shopping_list": raw.get("shopping_list", [])}

    return None


# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("PeetKiest Vooruit")
st.caption("Dagen vooruit gepland met Eén boodschappenlijst.")

qp = _qp_dict()
inp = parse_query_params(qp)

if "pk_v_rot" not in st.session_state:
    st.session_state["pk_v_rot"] = 0

rotation_index = int(st.session_state["pk_v_rot"])
kitchen_plan = compute_kitchen_plan(inp.days, rotation_index)

context = {
    "days": inp.days,
    "persons": inp.persons,
    "vegetarian": inp.vegetarian,
    "allergies": inp.allergies,
    "nogo": inp.nogo,
    "fridge": inp.fridge,
    "kitchen_plan": kitchen_plan,
}


with st.expander("Invoer", expanded=False):
    st.write(context)


col1, col2 = st.columns(2)
with col1:
    regen = st.button("Maak planning", use_container_width=True)
with col2:
    if st.button("Nieuwe variant", use_container_width=True):
        st.session_state["pk_v_rot"] = next_rotation_index(st.session_state["pk_v_rot"])
        st.rerun()


auto_run = bool(qp.get("days")) and bool(qp.get("persons"))
should_run = regen or auto_run


if should_run:
    prompt = _build_prompt(context)
    sig = _signature(context, rotation_index)

    if st.session_state.get("pk_v_sig") != sig:
        st.session_state["pk_v_sig"] = sig
        with st.spinner("Peet kiest en plant…"):
            st.session_state["pk_v_raw"] = _call_llm_cached(prompt)
        st.session_state.pop("pk_v_pdf", None)




raw = _safe_json_load(st.session_state.get("pk_v_raw"))
normalized = normalize_vooruit_output(raw, inp.days)

if not normalized:
    st.info("Geef days/persons mee via Carrd of klik op ‘Maak planning’.")
    st.stop()

days_out = [_normalize_day_preparation(d) for d in normalized["days"]]
shopping_list = normalized.get("shopping_list", [])


for d in days_out:
    day_no = d.get("day", "?")
    kitchen = d.get("kitchen", "")
    dish_name = d.get("dish_name", "")

    nutr = d.get("nutrition", {}) or {}

    #-------------------------------------------------
    # Bouw dynamische afbeelding op basis van gerecht
    #-------------------------------------------------

    image_url = build_image_url(dish_name)

    render_peet_hero(
        title=dish_name,
        subtitle=f"Dag {day_no} • {kitchen}",
        image_url=image_url,
        kcal=nutr.get("calories_kcal"),
        protein=nutr.get("protein_g"),
        fat=nutr.get("fat_g"),
        carbs=nutr.get("carbs_g"),
    )

    # -------------------------
    # Ingrediënten
    # -------------------------
    st.markdown("**Ingrediënten**")

    ingredients = d.get("ingredients", [])

    if ingredients:

        clean_ingredients = []

        for ing in ingredients:
            if isinstance(ing, dict):
                amount = str(ing.get("amount", "")).strip()
                item = str(ing.get("item", "")).strip()
                if amount and item:
                    clean_ingredients.append(f"{amount} {item}")
                elif item:
                    clean_ingredients.append(item)

        mid = (len(clean_ingredients) + 1) // 2
        col1_items = clean_ingredients[:mid]
        col2_items = clean_ingredients[mid:]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                "<div style='line-height:1.2; font-size:15px;'>"
                + "<br>".join(col1_items)
                + "</div>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                "<div style='line-height:1.2; font-size:15px;'>"
                + "<br>".join(col2_items)
                + "</div>",
                unsafe_allow_html=True
            )

    # -------------------------
    # Bereiding
    # -------------------------
    st.markdown("**Zo pakken we het aan.**")

    for i, step in enumerate(d.get("preparation", []), 1):
        st.markdown(f"{i}. {step}")

    st.divider()
