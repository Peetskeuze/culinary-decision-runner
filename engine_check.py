from peet_engine.context import build_context
from peet_engine.engine import plan

ctx = build_context({
    "mode": "vooruit",
    "days": 3,
    "persons": 2,
    "vegetarian": True,
    "allergies": "pinda, schaaldieren",
    "moment": "weekend",
    "time": "normaal",
    "ambition": 3,
    "language": "nl",
})

print(plan(ctx))
