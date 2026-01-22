# app.py — bootstrap
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# app.py
import streamlit as st
from typing import Dict, Any

from core.llm import call_peet
from core.engine import plan

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def get_query_params() -> Dict[str, Any]:
    q = st.query_params

    def _list(key: str):
        v = q.get(key)
        if not v:
            return []
        return [x.strip() for x in v.split(",") if x.strip()]

    return {
        "days": int(q.get("days", 1)),
        "persons": int(q.get("persons", 2)),
        "moment": q.get("moment", "doordeweeks"),
        "time": q.get("time", "normaal"),
        "preference": q.get("preference"),
        "kitchen": q.get("kitchen"),
        "vegetarian": q.get("vegetarian") == "true",
        "allergies": _list("allergies"),
        "nogo": _list("nogo"),
        "language": q.get("language", "nl"),
    }


def render_today(result: Dict[str, Any]):
    st.title("Peet kiest. Jij hoeft alleen te koken.")
    st.caption("Vandaag geregeld.")

    st.subheader(result["dish_name"])
    if result.get("why"):
        st.write(result["why"])

    st.divider()
    st.button("Download als PDF", disabled=True)


def render_forward(result: Dict[str, Any], days: int):
    st.title(f"Peet plant vooruit · {days} dagen")
    st.caption("Peet bewaakt balans en variatie.")

    for d in result["days"]:
        st.subheader(f"Dag {d['day']}")
        st.write(d["dish_name"])
        if d.get("why"):
            st.caption(d["why"])
        st.divider()

    st.button("Download als PDF", disabled=True)


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    ctx = get_query_params()
    days = ctx["days"]

    # =========================
    # VANDAAG → LLM (vrij)
    # =========================
    if days == 1:
        # Bewust BREDE, losse context
        prompt_context = f"""
Moment: {ctx['moment']}
Tijd: {ctx['time']}
Keukenvoorkeur: {ctx.get('kitchen') or 'vrij'}
Voorkeur: {ctx.get('preference') or 'geen vaste'}
Vegetarisch: {'ja' if ctx['vegetarian'] else 'nee'}
Allergieën: {', '.join(ctx['allergies']) or 'geen'}

Belangrijk:
- Kies elke keer iets anders
- Herhaling is fout
- Zwerven mag
- Geen veilige standaardgerechten
"""

        result = call_peet(prompt_context)
        render_today(result)
        return

    # =========================
    # VOORUIT → ENGINE
    # =========================
    engine_ctx = {
        "mode": "vooruit",
        "days": days,
        "persons": ctx["persons"],
        "vegetarian": ctx["vegetarian"],
        "allergies": ctx["allergies"],
        "nogo": ctx["nogo"],
        "moment": ctx["moment"],
        "time": ctx["time"],
        "language": ctx["language"],
        # GEEN variation_seed → engine bepaalt rust
    }

    result = plan(engine_ctx)
    render_forward(result, days)


if __name__ == "__main__":
    st.set_page_config(page_title="Peet kiest", layout="wide")
    main()
