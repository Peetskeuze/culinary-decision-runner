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
    Deterministic engine: context -> choice plan (names only).
    No LLM. No UI.
    """
    ctx = _normalize_context(context)
    days = ctx["days"]

    # Stap 3: semantisch ritme
    profiles = determine_day_profiles(days)

    # ambition normalization
    ambition = _apply_ambition_caps(ctx)
    ambition_by_day = _spread_ambition(days=days, base=ambition)

    out_days: List[Dict[str, Any]] = []
    used_names: set[str] = set()

    for idx, profile in enumerate(profiles, start=1):
        day_amb = ambition_by_day[idx - 1]

        dish = _pick_dish(
            profile=profile,
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
                vegetarian=ctx["vegetarian"],
                allergies=ctx["allergies"],
                language=ctx["language"],
                used_names=used_names,
                target_profile=profile,
            )

        name = dish.name_en if ctx["language"] == "en" else dish.name_nl
        used_names.add(name)

        out_days.append(
            {
                "day": idx,
                "profile": profile,
                "dish_name": name,
                "ambition": day_amb,
                "why": _why_line(
                    language=ctx["language"],
                    profile=profile,
                    moment=ctx["moment"],
                    time=ctx["time"],
                    ambition=day_amb,
                ),
            }
        )

    return {"days": out_days}


# -----------------------------
# Internals
# -----------------------------
def _normalize_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(raw.get("mode", "vandaag")).lower()
    if mode not in ALLOWED_MODE:
        mode = "vandaag"

    days = int(raw.get("days", 1))
    if mode == "vandaag":
        days = 1
    if days not in ALLOWED_DAYS:
        days = 1

    vegetarian = bool(raw.get("vegetarian", False))
    allergies = [str(a).strip().lower() for a in raw.get("allergies", []) if str(a).strip()]

    moment = str(raw.get("moment", "doordeweeks")).lower()
    if moment not in ALLOWED_MOMENT:
        moment = "doordeweeks"

    time = str(raw.get("time", "normaal")).lower()
    if time not in ALLOWED_TIME:
        time = "normaal"

    ambition = int(raw.get("ambition", 2))
    ambition = max(1, min(4, ambition))

    language = str(raw.get("language", "nl")).lower()
    if language not in ALLOWED_LANG:
        language = "nl"

    return {
        "mode": mode,
        "days": days,
        "vegetarian": vegetarian,
        "allergies": allergies,
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


def _pick_dish(
    profile: str,
    vegetarian: bool,
    allergies: List[str],
    language: str,
    used_names: set[str],
    moment: str,
    time: str,
    ambition: int,
) -> Optional[Dish]:
    candidates = []
    for d in DISHES:
        if d.profile != profile:
            continue
        if vegetarian and not d.veg:
            continue
        if _hits_allergy(d, allergies):
            continue
        name = d.name_en if language == "en" else d.name_nl
        if name in used_names:
            continue
        candidates.append(d)

    if not candidates:
        return None

    candidates.sort(key=lambda d: d.name_nl if language == "nl" else d.name_en)
    return candidates[0]


def _fallback_pick(
    vegetarian: bool,
    allergies: List[str],
    language: str,
    used_names: set[str],
    target_profile: str,
) -> Dish:
    pool = [
        d for d in DISHES
        if (not vegetarian or d.veg) and not _hits_allergy(d, allergies)
    ]

    if not pool:
        return Dish(
            name_nl="Eenvoudige, veilige groenteschotel",
            name_en="Simple, safe vegetable dish",
            profile=target_profile,
            veg=True,
        )

    pool.sort(
        key=lambda d: (
            abs(PROFILE_RANK[d.profile] - PROFILE_RANK[target_profile]),
            d.name_nl if language == "nl" else d.name_en,
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


def _why_line(language: str, profile: str, moment: str, time: str, ambition: int) -> str:
    if language == "en":
        return f"{profile.capitalize()} profile for a {moment.replace('_', ' ')} moment. Time: {time}. Ambition: {ambition}."
    moment_txt = "iets te vieren" if moment == "iets_te_vieren" else moment
    return f"{profile.capitalize()} profiel, passend bij {moment_txt}. Tijd: {time}. Ambitie: {ambition}."
