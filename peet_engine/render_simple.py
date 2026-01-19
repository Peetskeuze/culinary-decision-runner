import streamlit as st
from typing import Dict, Any
from peet_engine.recipe_text import get_recipe


def render_plan(result: Dict[str, Any]) -> None:
    days = result.get("days", [])

    for day in days:
        dish = day.get("dish_name", "")
        why = day.get("why", "")

        recipe = get_recipe(dish)

        st.subheader(dish)
        st.markdown(recipe["opening"])
        st.markdown("**Zo pak je dit aan**")
        st.markdown(recipe["preparation"])


        st.divider()
