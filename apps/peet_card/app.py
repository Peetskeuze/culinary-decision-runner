# apps/peet_card/app.py
# Peet-Card — Vandaag (vrije tekst, variatiegericht)

import sys
from pathlib import Path
import time
import random
import streamlit as st

# -------------------------------------------------
# Bootstrap: project-root in sys.path (Cloud + lokaal)
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.llm import call_peet_text


def _qp(name: str, default: str = "") -> str:
    val = st.query_params.get(name, default)
    if isinstance(val, list):
        return val[0] if val else default
    return val if val is not None else default


def _to_int(s: str, default: int) -> int:
    try:
        return int(str(s).strip())
    except Exception:
        return default


def _to_bool(s: str, default: bool = False) -> bool:
    if s is None or s == "":
        return default
    v = str(s).strip().lower()
    if v in ("1", "true", "yes", "y", "on", "ja"):
        return True
    if v in ("0", "false", "no", "n", "off", "nee"):
        return False
    return default


def _to_list(s: str) -> list[str]:
    if not s:
        return []
    return [p.strip().lower() for p in str(s).split(",") if p.strip()]


def build_user_context() -> str:
    """
    Bouwt een compacte contextstring voor de LLM.
    Doel: vrijheid + variatie, zonder schema/JSON.
    """

    days = _to_int(_qp("days", "1"), 1)
    persons = _to_int(_qp("persons", "2"), 2)
    persons = max(1, min(12, persons))

    # Vandaag is days=1. Als iemand days>1 meegeeft, blokkeren we (vooruit blijft ongemoeid).
    if days in (2, 3, 5):
        return "__FORWARD__"

    moment = _qp("moment", "")
    time_pref = _qp("time", "")
    kitchen = _qp("kitchen", "")
    preference = _qp("preference", "")
    vegetarian = _to_bool(_qp("vegetarian", ""), False)

    allergies = _to_list(_qp("allergies", ""))
    nogo = _to_list(_qp("nogo", ""))
    fridge = _to_list(_qp("fridge", ""))

    # Variatie-injectie: elke run andere richting
    random.seed(time.time_ns())
    chef_mood = random.choice([
        "thuiskoken NL/BE met karakter",
        "Italiaans comfort maar niet standaard",
        "mediterraan fris en licht",
        "Aziatische punch zonder clichés",
        "Frans bistro, simpel maar raak",
        "vegetarisch met diepgang (niet salade-achtig)",
        "visgerecht met spanning (geen standaard citroen-yoghurt)",
    ])
    technique = random.choice([
        "bakken", "roosteren", "stoven", "grillen", "oven", "kort en heet", "langzaam en zacht"
    ])
    flavour = random.choice([
        "fris", "hartig", "romig", "kruidig", "umami", "licht", "diep"
    ])

    # Nonce: expliciet anders laten zijn per refresh
    nonce = str(time.time_ns())

    # Compacte context (geen JSON!)
    lines = []
    lines.append("CONTEXT (vandaag):")
    lines.append(f"- persons: {persons}")
    if moment:
        lines.append(f"- moment: {moment}")
    if time_pref:
        lines.append(f"- time: {time_pref}")
    if kitchen:
        lines.append(f"- kitchen (inspiratie): {kitchen}")
    if preference:
        lines.append(f"- preference (inspiratie): {preference}")
    lines.append(f"- vegetarian: {'ja' if vegetarian else 'nee'}")
    if allergies:
        lines.append(f"- allergies: {', '.join(allergies)}")
    if nogo:
        lines.append(f"- nogo: {', '.join(nogo)}")
    if fridge:
        lines.append(f"- fridge: {', '.join(fridge)}")

    lines.append("")
    lines.append("VRIJE VARIATIE (kies bewust anders dan vorige runs):")
    lines.append(f"- chef_mood: {chef_mood}")
    lines.append(f"- technique_hint: {technique}")
    lines.append(f"- flavour_angle: {flavour}")
    lines.append(f"- VARIATION_NONCE: {nonce}")

    return "\n".join(lines)


def main():
    st.set_page_config(page_title="Peet kiest", layout="centered")

    st.markdown("## Peet kiest. Jij hoeft alleen te koken.")
    st.caption("Vandaag geregeld. Elke refresh mag echt anders zijn.")

    user_context = build_user_context()

    if user_context == "__FORWARD__":
        st.warning("Voor 2/3/5 dagen vooruit: gebruik Peet Kiest Vooruit. Peet-Card is vandaag.")
        st.stop()

    with st.spinner("Peet is aan het kiezen…"):
        text = call_peet_text(user_context)

    st.markdown(text)


if __name__ == "__main__":
    main()
