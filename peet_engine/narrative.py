# peet_engine/narrative.py
"""
Peet Narrative — toon & verhaal

Dit bestand bevat de vaste Peet-stem:
- zin om te koken
- coachende bereiding
- rustige afsluiting

Geen UI, geen hoeveelheden, geen contextlogica.
"""

def intro(dish_name: str, mood: str | None = None) -> str:
    """
    Opening die vertrouwen en zin geeft.
    """
    base = (
        f"{dish_name}\n\n"
        "Dit is zo’n gerecht dat je zonder nadenken maakt, "
        "maar waar je toch even bij blijft hangen. "
        "Geen gedoe, geen ingewikkelde stappen — gewoon goed eten "
        "dat klopt."
    )

    if mood:
        return f"{base} Het past precies bij een {mood} moment."
    return base


def preparation_story(steps: list[str]) -> str:
    """
    Zet losse stappen om in een vloeiende, coachende bereiding.
    """
    if not steps:
        return ""

    story_lines = []
    for step in steps:
        line = step.strip()
        if not line.endswith("."):
            line += "."
        story_lines.append(line)

    return (
        "Zo pak je dit aan:\n\n"
        + " ".join(story_lines)
    )


def closing() -> str:
    """
    Rustige, zelfverzekerde afsluiting.
    """
    return (
        "Meer hoeft het niet te zijn. "
        "Zet het op tafel, proef even en weet: dit is precies goed. "
        "Dit lukt altijd."
    )
