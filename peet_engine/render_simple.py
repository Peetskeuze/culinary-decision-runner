import streamlit as st
from typing import Dict, Any

from peet_engine.recipe_text import get_recipe


def render_plan(result: Dict[str, Any]) -> None:
    days = result.get("days", [])

    for day in days:
        dish = day.get("dish_name", "")
        recipe = get_recipe(dish)

        # Titel
        st.markdown(f"## {dish}")

        # Opening (zin om te koken)
        st.markdown(recipe["opening"])

        # Bereiding (verhalend, coachend)
        st.markdown(recipe["preparation"])

        st.divider()
