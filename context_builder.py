import unicodedata
import re

ALLOWED_KITCHENS = {
    "verrassing",
    "belgisch_nederlands",
    "frans",
    "italiaans",
    "mediterraan",
    "midden_oosten",
    "aziatisch",
}

KITCHEN_SYNONYMS = {
    "ik laat me verrassen": "verrassing",
    "verassen": "verrassing",
    "belgisch nederlands": "belgisch_nederlands",
    "belgisch-nederlands": "belgisch_nederlands",
    "italiaan": "italiaans",
    "mediteraan": "mediterraan",
}

def normalize_str(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"\s+", " ", value)
    return value

def split_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [normalize_str(v) for v in value if v]
    return [normalize_str(v) for v in value.split(",") if v.strip()]

def to_int(value):
    try:
        return int(value)
    except Exception:
        return None

def build_context(raw: dict) -> dict:
    data = {}
    for key, value in raw.items():
        k = normalize_str(str(key))
        data[k] = normalize_str(value) if isinstance(value, str) else value

    persons_raw = to_int(data.get("persons"))
    persons = persons_raw if persons_raw is not None else 2
    persons = max(1, min(persons, 8))

    

    time = data.get("time") if data.get("time") in ("kort", "normaal", "ruim") else "normaal"
    moment = data.get("moment") if data.get("moment") in ("doordeweeks", "weekend") else "doordeweeks"

    vegetarian = False
    if data.get("preference") == "veggie":
        vegetarian = True
    if data.get("vegetarian") in ("on", "true", "yes", "1"):
        vegetarian = True

    allergies = set()
    allergies.update(split_list(data.get("allergies")))
    allergies.update(split_list(data.get("nogo")))

    fridge = split_list(data.get("fridge"))

    kitchen = None
    kitchen_raw = data.get("kitchen")
    if kitchen_raw:
        kitchen_raw = KITCHEN_SYNONYMS.get(kitchen_raw, kitchen_raw)
        if kitchen_raw in ALLOWED_KITCHENS:
            kitchen = kitchen_raw

    days_raw = to_int(data.get("days"))
    if days_raw is None or days_raw == 1:
        mode = "vandaag"
        days = 1
    else:
        mode = "vooruit"
        days = days_raw if days_raw in (2, 3, 5) else 2

    return {
        "mode": mode,
        "days": days,
        "persons": persons,
        "vegetarian": vegetarian,
        "allergies": sorted(allergies),
        "moment": moment,
        "time": time,
        "ambition": 2,
        "language": "nl",
        "kitchen": kitchen,
        "fridge": fridge,
    }

def validate_context(context: dict) -> None:
    """
    Valideert of context voldoet aan het Peet Kiest data-contract.
    Gooit ValueError bij afwijkingen.
    """

    required_keys = {
        "mode",
        "days",
        "persons",
        "vegetarian",
        "allergies",
        "moment",
        "time",
        "ambition",
        "language",
        "kitchen",
        "fridge",
    }

    missing = required_keys - context.keys()
    if missing:
        raise ValueError(f"Context mist verplichte velden: {missing}")

    # -----------------------------
    # MODE / DAYS
    # -----------------------------
    if context["mode"] not in ("vandaag", "vooruit"):
        raise ValueError(f"Ongeldige mode: {context['mode']}")

    if context["mode"] == "vandaag" and context["days"] != 1:
        raise ValueError("Mode 'vandaag' vereist days=1")

    if context["mode"] == "vooruit" and context["days"] not in (2, 3, 5):
        raise ValueError("Mode 'vooruit' vereist days in (2, 3, 5)")

    # -----------------------------
    # PERSONS
    # -----------------------------
    if not isinstance(context["persons"], int):
        raise ValueError("persons moet een integer zijn")

    if not (1 <= context["persons"] <= 8):
        raise ValueError("persons moet tussen 1 en 8 liggen")

    # -----------------------------
    # BOOLEANS / LISTS
    # -----------------------------
    if not isinstance(context["vegetarian"], bool):
        raise ValueError("vegetarian moet boolean zijn")

    if not isinstance(context["allergies"], list):
        raise ValueError("allergies moet een lijst zijn")

    if not isinstance(context["fridge"], list):
        raise ValueError("fridge moet een lijst zijn")

    # -----------------------------
    # ENUMS
    # -----------------------------
    if context["moment"] not in ("doordeweeks", "weekend"):
        raise ValueError("moment moet 'doordeweeks' of 'weekend' zijn")

    if context["time"] not in ("kort", "normaal", "ruim"):
        raise ValueError("time moet 'kort', 'normaal' of 'ruim' zijn")

    if context["language"] not in ("nl", "en"):
        raise ValueError("language moet 'nl' of 'en' zijn")

    if not isinstance(context["ambition"], int) or not (1 <= context["ambition"] <= 4):
        raise ValueError("ambition moet integer 1–4 zijn")

    # -----------------------------
    # KITCHEN
    # -----------------------------
    if context["kitchen"] is not None and context["kitchen"] not in ALLOWED_KITCHENS:
        raise ValueError(f"Ongeldige kitchen: {context['kitchen']}")
