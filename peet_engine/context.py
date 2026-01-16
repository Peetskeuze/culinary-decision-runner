# =========================================================
# CONTEXT — WAARHEID + BETEKENIS (STAP 1 + STAP 2)
# =========================================================

from typing import Dict, Any, List
from peet_engine.shared.parsing import safe_int, split_list, normalize_str


# --------------------------------------------------
# DEFAULTS — één plek, leidend (STAP 1)
# --------------------------------------------------
DEFAULTS = {
    "mode": "vandaag",          # vandaag | vooruit
    "days": 1,                  # 1 | 2 | 3 | 5
    "persons": 2,               # int >= 1
    "vegetarian": False,        # bool
    "allergies": [],            # list[str]
    "moment": "diner",          # ontbijt | lunch | diner
    "time": "normaal",          # snel | normaal | uitgebreid
    "ambition": 2,              # 1..4
    "language": "nl",            # nl | en
    "keuken": None,              # optioneel, stijl (geen ingrediënten)
}

ALLOWED_DAYS = (1, 2, 3, 5)
ALLOWED_MODES = ("vandaag", "vooruit")


# --------------------------------------------------
# PUBLIC API — STAP 1
# --------------------------------------------------
def build_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bouwt een stabiele, genormaliseerde context.
    Geen betekenis, geen interpretatie.
    """

    ctx = dict(DEFAULTS)

    # --- mode ---
    mode = normalize_str(raw.get("mode", ctx["mode"]))
    if mode not in ALLOWED_MODES:
        mode = ctx["mode"]
    ctx["mode"] = mode

    # --- days ---
    days_raw = raw.get("days", ctx["days"])
    days = safe_int(days_raw, ctx["days"])
    if ctx["mode"] == "vandaag":
        days = 1
    if days not in ALLOWED_DAYS:
        days = ctx["days"]
    ctx["days"] = days

    # --- persons ---
    persons = safe_int(raw.get("persons", ctx["persons"]), ctx["persons"])
    ctx["persons"] = max(1, persons)

    # --- vegetarian ---
    ctx["vegetarian"] = _to_bool(raw.get("vegetarian", ctx["vegetarian"]))

    # --- allergies ---
    ctx["allergies"] = split_list(raw.get("allergies", []))

    # --- moment ---
    ctx["moment"] = normalize_str(raw.get("moment", ctx["moment"]))

    # --- time ---
    ctx["time"] = normalize_str(raw.get("time", ctx["time"]))

    # --- ambition ---
    ambition = safe_int(raw.get("ambition", ctx["ambition"]), ctx["ambition"])
    ctx["ambition"] = min(4, max(1, ambition))

    # --- language ---
    lang = normalize_str(raw.get("language", ctx["language"]))
    ctx["language"] = "en" if lang == "en" else "nl"

    # --- keuken ---
    kitchen = raw.get("keuken")
    ctx["keuken"] = normalize_str(kitchen) if kitchen else None

    return ctx


# --------------------------------------------------
# PUBLIC API — STAP 2 (BETEKENISLAAG)
# --------------------------------------------------
def build_context_text(ctx: Dict[str, Any]) -> str:
    """
    Bouwt een verhalende contexttekst voor het model.
    Leest ctx, muteert niets.
    """

    lines: List[str] = []

    days = ctx["days"]
    persons = ctx["persons"]
    vegetarian = ctx["vegetarian"]
    allergies = ctx["allergies"]
    moment = ctx["moment"]
    time = ctx["time"]
    ambition = ctx["ambition"]
    kitchen = ctx["keuken"]

    # --- Basis ---
    if days > 1:
        lines.append("De gebruiker vraagt om een vooruit-keuze voor meerdere dagen.")
    else:
        lines.append("De gebruiker vraagt om een keuze voor vandaag.")

    lines.append(
        f"Er wordt gekookt voor {persons} persoon{'en' if persons > 1 else ''}."
    )

    # --- Moment & tijd ---
    if moment == "weekend":
        lines.append(
            "De context is een ontspannen weekendsetting met ruimte voor aandacht en smaak."
        )
    else:
        lines.append(
            "De context is doordeweeks en vraagt om praktische, realistische gerechten."
        )

    if time == "snel":
        lines.append(
            "Er is beperkte kooktijd; eenvoud en tempo zijn belangrijk."
        )
    else:
        lines.append(
            "Er is voldoende tijd om te koken, zonder behoefte aan complexiteit of gedoe."
        )

    # --- Dieet & allergieën ---
    if vegetarian:
        lines.append("De gerechten moeten volledig vegetarisch zijn.")

    if allergies:
        lines.append(
            f"De gerechten mogen geen {_list_to_sentence(allergies)} bevatten. "
            "Dit zijn harde grenzen."
        )

    # --- Keuken ---
    if kitchen:
        lines.append(
            f"De gebruiker kiest voor de {kitchen.replace('_', ' ')} keuken als smaakrichting."
        )
        lines.append(
            "De keuken bepaalt de stijl en signatuur van de gerechten, "
            "niet vaste ingrediënten of structuren."
        )
        lines.append(
            "Vermijd stereotiepe herhaling en clichés."
        )

    # --- Variatie ---
    if days > 1:
        lines.append(
            "Variatie tussen dagen is belangrijk. Gerechten mogen verschillen in karakter "
            "en opbouw, maar moeten samenhangend aanvoelen als één reeks."
        )
        lines.append(
            "De eerste dag mag lichter zijn, opvolgende dagen iets voller, "
            "zonder zwaarder of ingewikkelder te worden."
        )

    # --- Ambitie ---
    if ambition <= 2:
        lines.append(
            "Het ambitieniveau is laag: focus op comfort, helderheid en rust."
        )
    elif ambition == 3:
        lines.append(
            "Het ambitieniveau is middelmatig: aandacht voor smaak en balans, "
            "zonder specialistische technieken."
        )
    else:
        lines.append(
            "Het ambitieniveau is hoger: meer gelaagdheid en verfijning, "
            "maar altijd haalbaar voor een thuiskok."
        )

    # --- Verwachting ---
    lines.append(
        "Kies gerechten die realistisch zijn om thuis te koken en die passen bij dit moment, "
        "zonder uitleg of verantwoording in de output."
    )

    return "\n".join(lines)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
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
