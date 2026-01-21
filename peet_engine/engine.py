from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


# -----------------------------
# Contract constants
# -----------------------------
ALLOWED_DAYS = (1, 2, 3, 5)
ALLOWED_TIME = ("snel", "normaal", "uitgebreid")
ALLOWED_MOMENT = ("doordeweeks", "weekend", "iets_te_vieren")
ALLOWED_LANG = ("nl", "en")
ALLOWED_MODE = ("vandaag", "vooruit")


# -----------------------------
# Stap 3 — Semantisch dagritme
# -----------------------------
def determine_day_profiles(days: int) -> List[str]:
    """
    Semantisch dagritme:
    licht → vol → afronding
    """
    if days <= 1:
        return ["licht"]

    if days == 2:
        return ["licht", "afronding"]

    if days == 3:
        return ["licht", "vol", "afronding"]

    if days == 5:
        return ["licht", "vol", "licht", "vol", "afronding"]

    return ["licht"] * days

def determine_kitchen_sequence(days: int) -> list[str]:
    if days == 1:
        return ["vrij"]

    if days == 2:
        return ["nl_be", "italiaans"]

    if days == 3:
        return ["nl_be", "italiaans", "aziatisch"]

    if days == 5:
        return ["nl_be", "italiaans", "mediterraan", "frans", "nl_be"]

    raise ValueError("Ongeldig aantal dagen")



# Ambitie-cap per moment
MOMENT_AMBITION_CAP = {
    "doordeweeks": 2,
    "weekend": 3,
    "iets_te_vieren": 4,
}

# Ranking om fallback “dichtbij” te houden
PROFILE_RANK = {"licht": 1, "vol": 2, "afronding": 3}


# -----------------------------
# Dish catalog (names only)
# -----------------------------
@dataclass(frozen=True)
class Dish:
    name_nl: str
    name_en: str
    profile: str  # licht | vol | afronding
    veg: bool
    tags: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()


DISHES: List[Dish] = [
    # Licht
    Dish("Citroen couscous met kruiden en groenten", "Lemon couscous with herbs and vegetables", "licht", True, tags=("fris",)),
    Dish("Tomatensoep met basilicum en brood", "Tomato soup with basil and bread", "licht", True, tags=("soep",)),
    Dish("Geroosterde groente met yoghurt citroen", "Roasted vegetables with lemon yoghurt", "licht", True, tags=("oven",)),
    Dish("Zalm uit de oven met groene salade", "Oven salmon with green salad", "licht", False, tags=("vis",)),
    Dish("Kip citroen knoflook met sperziebonen", "Lemon garlic chicken with green beans", "licht", False, tags=("kip",)),

    # Vol
    Dish("Pasta arrabbiata met extra groenten", "Arrabbiata pasta with extra vegetables", "vol", True, tags=("pasta",)),
    Dish("Rijstbowl met tofu en gember", "Rice bowl with tofu and ginger", "vol", True, tags=("bowl",)),
    Dish("Kip tikka met rijst en komkommer", "Chicken tikka with rice and cucumber", "vol", False, tags=("kruidig",)),
    Dish("Bolognese met salade", "Bolognese with salad", "vol", False, tags=("pasta",)),

    # Afronding
    Dish("Romige risotto met paddenstoelen", "Creamy mushroom risotto", "afronding", True, tags=("romig",)),
    Dish("Ovenschotel met aardappel en groenten", "Traybake with potatoes and vegetables", "afronding", True, tags=("oven",)),
    Dish("Stoofpotje met rund en wortel", "Beef and carrot stew", "afronding", False, tags=("stoof",)),
]

# -----------------------------
# Public API
# -----------------------------
def plan(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic engine: context -> choice plan.
    No LLM. No UI.
    """
    ctx = _normalize_context(context)
    days = ctx["days"]

    # -----------------------------
    # Vast ritme (afdwingen)
    # -----------------------------
    profiles = determine_day_profiles(days)
    kitchens = determine_kitchen_sequence(days)

    # ambition normalization
    ambition = _apply_ambition_caps(ctx)
    ambition_by_day = _spread_ambition(days=days, base=ambition)

    out_days: List[Dict[str, Any]] = []
    used_names: set[str] = set()

    # -----------------------------
    # Dag-voor-dag keuze
    # -----------------------------
    for idx, (profile, kitchen) in enumerate(
        zip(profiles, kitchens), start=1
    ):
        day_amb = ambition_by_day[idx - 1]

        dish = _pick_dish(
            profile=profile,
            kitchen=kitchen,
            vegetarian=ctx["vegetarian"],
            allergies=ctx["allergies"],
            language=ctx["language"],
            used_names=used_names,
            moment=ctx["moment"],
            time=ctx["time"],
            ambition=day_amb,
        )

        if dish is None:
            dish = _fallback_pick(
                profile=profile,
                kitchen=kitchen,
                vegetarian=ctx["vegetarian"],
                allergies=ctx["allergies"],
                language=ctx["language"],
                used_names=used_names,
            )

        name = dish.name_en if ctx["language"] == "en" else dish.name_nl
        used_names.add(name)

        out_days.append(
            {
                "day": idx,
                "profile": profile,
                "kitchen": kitchen,
                "dish_name": name,
                "ambition": day_amb,
                "why": _why_line(
                    language=ctx["language"],
                    profile=profile,
                    kitchen=kitchen,
                    moment=ctx["moment"],
                    time=ctx["time"],
                    ambition=day_amb,
                ),
            }
        )

    return {
        "days_count": days,
        "persons": ctx["persons"],
        "days": out_days,
    }



# -----------------------------
# Internals
# -----------------------------
def _normalize_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    # -----------------------------
    # Mode & days
    # -----------------------------
    mode = str(raw.get("mode", "vandaag")).lower()
    if mode not in ALLOWED_MODE:
        mode = "vandaag"

    days = int(raw.get("days", 1))
    if mode == "vandaag":
        days = 1
    if days not in ALLOWED_DAYS:
        days = 1

    # -----------------------------
    # Persons (ALTJD aanwezig)
    # -----------------------------
    try:
        persons = int(raw.get("persons", 2))
    except Exception:
        persons = 2
    persons = max(1, min(8, persons))

    # -----------------------------
    # Dietary & restrictions
    # -----------------------------
    vegetarian = bool(raw.get("vegetarian", False))

    allergies = [
        str(a).strip().lower()
        for a in raw.get("allergies", [])
        if str(a).strip()
    ]

    nogo = [
        str(n).strip().lower()
        for n in raw.get("nogo", [])
        if str(n).strip()
    ]

    # -----------------------------
    # Contextual signals
    # -----------------------------
    moment = str(raw.get("moment", "doordeweeks")).lower()
    if moment not in ALLOWED_MOMENT:
        moment = "doordeweeks"

    time = str(raw.get("time", "normaal")).lower()
    if time not in ALLOWED_TIME:
        time = "normaal"

    ambition = int(raw.get("ambition", 2))
    ambition = max(1, min(4, ambition))

    # -----------------------------
    # Language
    # -----------------------------
    language = str(raw.get("language", "nl")).lower()
    if language not in ALLOWED_LANG:
        language = "nl"

    return {
        "mode": mode,
        "days": days,
        "persons": persons,
        "vegetarian": vegetarian,
        "allergies": allergies,
        "nogo": nogo,
        "moment": moment,
        "time": time,
        "ambition": ambition,
        "language": language,
    }


def _apply_ambition_caps(ctx: Dict[str, Any]) -> int:
    ambition = ctx["ambition"]

    if ctx["time"] == "snel":
        ambition = min(ambition, 2)
    elif ctx["time"] == "normaal":
        ambition = min(ambition, 3)

    ambition = min(ambition, MOMENT_AMBITION_CAP[ctx["moment"]])
    return max(1, min(4, ambition))


def _spread_ambition(days: int, base: int) -> List[int]:
    if days == 1:
        return [base]

    if base <= 2:
        return [base] * days

    highlight_index = 1 if days in (2, 3) else 3
    arr = [2] * days
    arr[highlight_index] = base
    return arr


from typing import Optional


def _pick_dish(
    profile: str,
    kitchen: str,
    vegetarian: bool,
    allergies: list,
    language: str,
    used_names: set,
    moment: str,
    time: str,
    ambition: int,
) -> Optional[Dish]:
    candidates: list[Dish] = []

    for d in DISHES:
        # profiel afdwingen
        if d.profile != profile:
            continue

        # keuken afdwingen (behalve bij 'vrij')
        if kitchen != "vrij" and d.kitchen != kitchen:
            continue

        # vegetarisch
        if vegetarian and not d.veg:
            continue

        # allergieën
        if _hits_allergy(d, allergies):
            continue

        # geen herhaling
        name = d.name_en if language == "en" else d.name_nl
        if name in used_names:
            continue

        candidates.append(d)

    if not candidates:
        return None

    # deterministisch: alfabetisch
    candidates.sort(
        key=lambda d: d.name_en if language == "en" else d.name_nl
    )

    return candidates[0]



from typing import List


def _fallback_pick(
    profile: str,
    kitchen: str,
    vegetarian: bool,
    allergies: List[str],
    language: str,
    used_names: set[str],
) -> Dish:
    pool = []

    for d in DISHES:
        # vegetarisch
        if vegetarian and not d.veg:
            continue

        # allergieën
        if _hits_allergy(d, allergies):
            continue

        # keuken afdwingen (behalve bij 'vrij')
        if kitchen != "vrij" and d.kitchen != kitchen:
            continue

        # geen herhaling
        name = d.name_en if language == "en" else d.name_nl
        if name in used_names:
            continue

        pool.append(d)

    if not pool:
        # ultieme noodfallback (veilig, maar zeldzaam)
        return Dish(
            name_nl="Eenvoudige, veilige groenteschotel",
            name_en="Simple, safe vegetable dish",
            profile=profile,
            kitchen=kitchen,
            veg=True,
        )

    # zo dicht mogelijk bij gewenst profiel
    pool.sort(
        key=lambda d: (
            abs(PROFILE_RANK[d.profile] - PROFILE_RANK[profile]),
            d.name_en if language == "en" else d.name_nl,
        )
    )

    return pool[0]



def _hits_allergy(dish: Dish, allergies: List[str]) -> bool:
    text = " ".join(
        [
            dish.name_nl.lower(),
            dish.name_en.lower(),
            " ".join(dish.tags).lower(),
            " ".join(dish.avoid).lower(),
        ]
    )
    return any(a in text for a in allergies)


def _why_line(
    language: str,
    profile: str,
    kitchen: str,
    moment: str,
    time: str,
    ambition: int,
) -> str:
    """
    Korte duiding waarom dit gerecht hier past.
    Rustig, niet uitleggerig.
    """

    if language == "en":
        base = "Fits well"
    else:
        base = "Past goed"

    parts = []

    # keuken (alleen als expliciet)
    if kitchen and kitchen != "vrij":
        if language == "en":
            parts.append(f"within a {kitchen.replace('_', ' ')} style")
        else:
            parts.append(f"binnen een {kitchen.replace('_', ' ')} keuken")

    # profiel
    if profile == "licht":
        parts.append("licht van karakter")
    elif profile == "vol":
        parts.append("wat steviger")
    elif profile == "afronding":
        parts.append("fijn om mee af te sluiten")

    # moment / tijd
    if moment == "weekend":
        parts.append("past bij het weekend")
    else:
        parts.append("geschikt voor doordeweeks")

    if time == "kort":
        parts.append("en snel klaar")
    elif time == "ruim":
        parts.append("met ruimte om rustig te koken")

    return f"{base} omdat het " + ", ".join(parts) + "."

