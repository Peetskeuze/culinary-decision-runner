from peet_engine.portions import PORTIONS

CATEGORY_ORDER = [
    "Groenten",
    "Granen",
    "Vlees / Vis / Vega",
    "Zuivel",
    "Kruiden & smaakmakers",
    "Overig",
]


def categorize(item_name: str) -> str:
    name = item_name.lower()

    if name in ("rijst", "couscous", "bulgur", "quinoa", "pasta"):
        return "Granen"
    if name in ("kip", "rund", "varken", "vis", "zalm", "tofu", "tempeh"):
        return "Vlees / Vis / Vega"
    if name in ("room", "yoghurt", "kaas", "boter"):
        return "Zuivel"
    if name in ("ui", "prei", "bloemkool", "paprika", "doperwten"):
        return "Groenten"

    return "Overig"


def amount_for_item(name: str, persons: int) -> str:
    n = name.lower()

    if n in ("rijst", "couscous", "bulgur", "quinoa"):
        low, high = PORTIONS["granen"]["dry_g"]
        return f"{persons * low}–{persons * high} g"

    if n == "pasta":
        low, high = PORTIONS["pasta"]["dry_g"]
        return f"{persons * low}–{persons * high} g"

    if n in ("aardappel", "aardappelen"):
        low, high = PORTIONS["aardappelen"]["raw_g"]
        return f"{persons * low}–{persons * high} g"

    if n in ("kip", "rund", "varken"):
        low, high = PORTIONS["vlees"]["weekday_raw_g"]
        return f"{persons * low}–{persons * high} g"

    if n in ("vis", "zalm", "witvis"):
        low, high = PORTIONS["vis"]["whitefish_raw_g"]
        return f"{persons * low}–{persons * high} g"

    if n in ("tofu", "tempeh"):
        low, high = PORTIONS["vega"]["tofu_tempeh_g"]
        return f"{persons * low}–{persons * high} g"

    return ""
