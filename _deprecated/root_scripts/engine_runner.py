from peet_engine.context import build_context, build_context_text
from peet_engine.engine import plan
from core.llm import call_peet


def run_local():
    # =========================================================
    # 1. RAW INPUT (zoals Carrd)
    # =========================================================
    raw_input = {
        "mode": "vooruit",
        "days": 3,
        "persons": 2,
        "vegetarian": True,
        "allergies": "pinda, schaaldieren",
        "moment": "weekend",
        "time": "normaal",
        "ambition": 3,
        "language": "nl",
        "keuken": "midden_oosten",
    }

    print("\n=== RAW INPUT ===")
    print(raw_input)

    # =========================================================
    # 2. CONTEXT — WAARHEID (STAP 1)
    # =========================================================
    ctx = build_context(raw_input)

    print("\n=== NORMALIZED CONTEXT ===")
    print(ctx)

    # =========================================================
    # 3. CONTEXT — BETEKENIS (STAP 2)
    # =========================================================
    context_text = build_context_text(ctx)

    print("\n=== CONTEXT TEXT (MODEL) ===")
    print(context_text)

    # =========================================================
    # 4. ENGINE BESLISSING (STAP 3)
    # =========================================================
    engine_choice = plan(ctx)

    print("\n=== ENGINE CHOICE ===")
    print(engine_choice)

    # =========================================================
    # 5. PROFIEL-SPECIFIEKE BEREIDING (STAP 4)
    # =========================================================
    # We gebruiken het profiel van dag 1 als leidend
    profile = engine_choice["days"][0]["profile"]

    BEREIDINGS_INTENTIE = {
        "licht": (
            "Houd de bereiding fris en overzichtelijk. "
            "Werk met weinig pannen, rustig tempo en zonder overbodige handelingen."
        ),
        "vol": (
            "Geef iets meer aandacht aan opbouw en smaak. "
            "Neem de tijd voor kruiden en garing, zonder complex te worden."
        ),
        "afronding": (
            "Laat de bereiding comfortabel en ontspannen aanvoelen. "
            "Geen haast, iets meer zachtheid en afronding in smaak."
        ),
    }

    bereidings_hint = BEREIDINGS_INTENTIE.get(profile, "")

    # =========================================================
    # 6. USER PROMPT BOUWEN
    # =========================================================
    fixed_title = engine_choice["days"][0]["dish_name"]

    days_block = []
    for d in engine_choice["days"]:
        days_block.append(
            f"Dag {d['day']}: {d['dish_name']} "
            f"({d['profile']}, ambitie {d['ambition']}). "
            f"Reden: {d['why']}"
        )

    days_text = "\n".join(days_block)

    keuken_map = {
        "nl": "Nederlands",
        "frans": "Frans",
        "italiaans": "Italiaans",
        "mediterraan": "Mediterraan",
        "midden_oosten": "Midden-Oosten",
        "aziatisch": "Aziatisch",
    }

    keuken_label = keuken_map.get(ctx.get("keuken"), "Algemeen")

    user_prompt = f"""
De onderstaande gerechtnaam is vast en mag NIET worden aangepast.
Gebruik deze exact als titel in de output.

Titel (vast):
"{fixed_title}"

Geef naast de vaste titel één korte subtitel (max. 12 woorden).
De subtitel:
- beschrijft de keuken en sfeer
- introduceert GEEN nieuwe gerechtnaam
- is aanvullend, niet creatief herschrijvend

Volg exact de onderstaande keuze van Peet.
Verzin geen ander gerecht.

{days_text}

Werk dit gerecht uit in de volgende keuken/stijl:
Keuken: {keuken_label}
Stijl: groente-gedreven, kruidig, gelaagd

De gekozen keuken beïnvloedt alleen:
- kruiden
- smaakmakers
- sauzen en afwerking

Het is toegestaan om hoofdcomponenten toe te voegen
(zoals granen, rijst, brood of peulvruchten),
mits ze logisch passen bij het gerecht en de gekozen keuken.

Gebruik hoofdcomponenten als ondersteuning van het gerecht,
niet als dominante basis.
Houd de balans groente-gedreven.
Bij een licht-profiel: wees terughoudend met hoofdcomponenten.
Bij een afronding-profiel: comfort en verzadiging mogen iets meer aandacht krijgen.

Bereidingsintentie voor vandaag:
{bereidings_hint}

Voor {ctx['persons']} personen.

Geef de output als JSON met exact deze keys:
- title
- subtitle
- meal_type
- ingredients
- steps

Schrijf de bereiding alsof Peet naast iemand in de keuken staat.

Toon en stijl:
- warm, rustig en licht informeel
- geen haast, geen stress
- alsof je over iemands schouder meekijkt en zachtjes meepraat

Schrijfwijze:
- volledige zinnen, niet te kort
- leg uit wáárom je iets doet
- geruststellende opmerkingen zijn welkom

Structuur:
- 6 tot 8 stappen
- elke stap 2 tot 4 zinnen
- begin elke stap met een duidelijke actie, daarna uitleg

Vermijd:
- kookjargon zonder uitleg
- dwingende toon
- lijstjes binnen de stappen

Het gevoel moet zijn:
“Dit lukt altijd. Ik blijf even bij je.”

Als één van deze keys ontbreekt of anders heet,
is de output ongeldig.

Sluit af met één korte Peet-zin.
Plaats deze NA het JSON-object, niet erin.
"""

    print("\n=== USER PROMPT ===")
    print(user_prompt)

    # =========================================================
    # 7. LLM AANROEP
    # =========================================================
    result = call_peet(
        system_context=context_text,
        user_prompt=user_prompt,
    )

    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    run_local()
