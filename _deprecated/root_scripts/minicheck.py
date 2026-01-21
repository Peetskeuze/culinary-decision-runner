from peet_engine.context import build_context

test = build_context({
    "mode": "vooruit",
    "days": "3 dagen",
    "persons": "2",
    "vegetarian": "yes",
    "allergies": "pinda, schaaldieren"
})

print(test)
