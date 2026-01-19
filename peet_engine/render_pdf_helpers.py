# =========================================================
# PEET — PDF HELPERS
# Categorisatie & winkelvolgorde
# =========================================================

CATEGORY_ORDER = [
    "Groente & fruit",
    "Vlees / Vis / Vega",
    "Zuivel",
    "Koeling / Diepvries",
    "Houdbaar",
    "Kruiden & smaakmakers",
    "Overig",
]


def categorize(item: str) -> str:
    i = item.lower()

    if any(x in i for x in ["kip", "vlees", "gehakt", "tofu", "tempeh", "linzen"]):
        return "Vlees / Vis / Vega"

    if any(x in i for x in ["yoghurt", "room", "kaas", "zuivel", "crème"]):
        return "Zuivel"

    if any(x in i for x in ["doperwten", "diepvries"]):
        return "Koeling / Diepvries"

    if any(
        x in i
        for x in [
            "ui",
            "knoflook",
            "prei",
            "paprika",
            "tomaat",
            "citroen",
            "wortel",
            "aubergine",
            "bloemkool",
        ]
    ):
        return "Groente & fruit"

    if any(x in i for x in ["olie", "rijst", "pasta", "brood", "couscous", "linzen"]):
        return "Houdbaar"

    if any(x in i for x in ["komijn", "paprika", "peper", "zout", "tijm", "kruiden"]):
        return "Kruiden & smaakmakers"

    return "Overig"
