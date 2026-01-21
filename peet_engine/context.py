# =========================================================
# CONTEXT — WAARHEID + BESLISLOGICA (PEET-CARD)
# =========================================================

from typing import Dict, Any, List
from peet_engine.shared.parsing import safe_int, split_list, normalize_str


# ---------------------------------------------------------
# CONSTANTEN — LEIDEND
# ---------------------------------------------------------
ALLOWED_DAYS = (1, 2, 3, 5)

DEFAULTS = {
    "days": 1,
    "persons": 2,
    "vegetarian": False,
    "allergies": [],
    "nogo": [],
    "moment": "doordeweeks",
    "time": "normaal",
    "ambition": 2,
    "language": "nl",
    "kitchen": None,     # alleen bij 1 dag
    "kitchens": [],     # alleen bij vooruit
}

# Vooruit-profielen: Peet beslist
FORWARD_KITCHENS = {
    2: ["nl_be", "italiaans"],
    3: ["nl_be", "italiaans", "aziatisch"],
    5: ["nl_be", "italiaans", "mediterraans", "frans", "nl_be"],
}


# ---------------------------------------------------------
# PUBLIC API — CONTEXT BOUWEN
# ---------------------------------------------------------
def build_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bouwt de enige geldige context voor Peet-Card.
    Afdwinging van 1 dag vs vooruit zit hier.
    """

    ctx = dict(DEFAULTS)

    # -----------------------------
    # DAYS
    # -----------------------------
    days = safe_int(raw.get("days", ctx["days"]), ctx["days"])
    if days not in ALLOWED_DAYS:
        days = 1
    ctx["days"] = days

    # -----------------------------
    # PERSONS
    # -----------------------------
    persons = safe_int(raw.get("persons", ctx["persons"]), ctx["persons"])
    ctx["persons"] = min(8, max(1, persons))

    # -----------------------------
    # ALLERGIES & NO-GO
    # -----------------------------
    ctx["allergies"] = split_list(raw.get("allergies", []))
    ctx["nogo"] = split_list(raw.get("nogo", []))

    # =====================================================
    # DAG-LOGICA — HIER WORDT HET VERSCHIL AFGEDWONGEN
    # =====================================================

    # -----------------------------------------------------
    # 1 DAG → GEBRUIKER STUURT
    # -----------------------------------------------------
    if ctx["days"] == 1:
        ctx["vegetarian"] = _to_bool(raw.get("vegetarian", False))
        ctx["moment"] = normalize_str(raw.get("moment", ctx["moment"]))
        ctx["time"] = normalize_str(raw.get("time", ctx["time"]))

        ambition = safe_int(raw.get("ambition", ctx["ambition"]), ctx["ambition"])
        ctx["ambition"] = min(4, max(1, ambition))

        kitchen = raw.get("kitchen")
        ctx["kitchen"] = normalize_str(kitchen) if kitchen else None

        ctx["kitchens"] = []

    # -----------------------------------------------------
    # VOORUIT (2 / 3 / 5) → PEET BESLIST
    # -----------------------------------------------------
    else:
        ctx["vegetarian"] = False
        ctx["moment"] = None
        ctx["time"] = None
        ctx["ambition"] = 2
        ctx["kitchen"] = None

        ctx["kitchens"] = FORWARD_KITCHENS.get(ctx["days"], [])

    # -----------------------------
    # LANGUAGE
    # -----------------------------
    lang = normalize_str(raw.get("language", ctx["language"]))
    ctx["language"] = "en" if lang == "en" else "nl"

    return ctx


# ---------------------------------------------------------
# PUBLIC API — CONTEXT → TEKST VOOR MODEL
# ---------------------------------------------------------
def build_context_text(ctx: Dict[str, Any]) -> str:
    """
    Zet context om naar verhalende instructie voor Peet.
    Leest ctx, muteert niets.
    """

    lines: List[str] = []

    days = ctx["days"]
    persons = ctx["persons"]

    # Basis
    if days == 1:
        lines.append("De gebruiker vraagt om een keuze voor vandaag.")
    else:
        lines.append(f"De gebruiker vraagt om een vooruit-planning voor {days} dagen.")

    lines.append(
        f"Er wordt gekookt voor {persons} persoon{'en' if persons > 1 else ''}."
    )

    # Allergieën & no-go
    if ctx["allergies"]:
        lines.append(
            f"De gerechten mogen geen {_list_to_sentence(ctx['allergies'])} bevatten."
        )

    if ctx["nogo"]:
        lines.append(
            f"Vermijd nadrukkelijk {_list_to_sentence(ctx['nogo'])}."
        )

    # 1 dag → gebruiker stuurt
    if days == 1:
        if ctx["vegetarian"]:
            lines.append("De gerechten moeten volledig vegetarisch zijn.")

        if ctx["kitchen"]:
            lines.append(
                f"De smaakrichting is {ctx['kitchen'].replace('_', ' ')}."
            )

        lines.append(
            "Het gerecht moet passen bij dit moment en praktisch zijn om thuis te koken."
        )

    # Vooruit → Peet beslist
    else:
        kitchens = ctx["kitchens"]
        if kitchens:
            lines.append(
                "Gebruik de volgende keukenprofielen per dag, in deze volgorde:"
            )
            for i, k in enumerate(kitchens, start=1):
                lines.append(f"Dag {i}: {k.replace('_', ' ')}")

        lines.append(
            "Zorg voor variatie tussen dagen zonder herhaling van dominante ingrediënten "
            "of kruiden. De reeks moet rustig en samenhangend aanvoelen."
        )

    lines.append(
        "Kies gerechten zonder uitleg of verantwoording in de output."
    )

    return "\n".join(lines)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value == 1
    v = normalize_str(value)
    return v in ("1", "true", "yes", "ja", "y", "on")


def _list_to_sentence(items: List[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " en " + items[-1]
