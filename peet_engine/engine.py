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
from typing import Dict, Any, List, Set


def plan(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic engine: context -> choice plan.
    - Geen UI
    - Geen LLM-calls hier
    - Wel: expliciete output voor UI en PDF
    """

    # =============================
    # 1. Context normalisatie
    # =============================
    ctx = _normalize_context(context)

    days: int = ctx["days"]
    persons: int = ctx["persons"]
    language: str = ctx["language"]

    # =============================
    # 2. Vast ritme afdwingen
    # =============================
    profiles: List[str] = determine_day_profiles(days)
    kitchens: List[str] = determine_kitchen_sequence(days)

    # Ambition: genormaliseerd + gespreid
    base_ambition: int = _apply_ambition_caps(ctx)
    ambition_by_day: List[int] = _spread_ambition(
        days=days,
        base=base_ambition,
    )

    # =============================
    # 3. Dag-voor-dag keuzes
    # =============================
    out_days: List[Dict[str, Any]] = []
    used_names: Set[str] = set()

    for idx in range(days):
        profile = profiles[idx]
        kitchen = kitchens[idx]
        day_ambition = ambition_by_day[idx]

        dish = _pick_dish(
            profile=profile,
            kitchen=kitchen,
            vegetarian=ctx["vegetarian"],
            allergies=ctx["allergies"],
            language=language,
            used_names=used_names,
            moment=ctx["moment"],
            time=ctx["time"],
            ambition=day_ambition,
            variation_seed=ctx.get("variation_seed", 0) + idx + 1,
        )

        # Harde fallback (mag nooit None blijven)
        if dish is None:
            dish = _fallback_pick(
                profile=profile,
                kitchen=kitchen,
                vegetarian=ctx["vegetarian"],
                allergies=ctx["allergies"],
                language=language,
                used_names=used_names,
            )

        dish_name = dish.name_en if language == "en" else dish.name_nl
        used_names.add(dish_name)

        # =============================
        # 4. Dag-output (rijk, maar stabiel)
        # =============================
        day_out: Dict[str, Any] = {
            "day": idx + 1,
            "profile": profile,
            "kitchen": kitchen,
            "dish_name": dish_name,
            "ambition": day_ambition,
            "why": _why_line(
                language=language,
                profile=profile,
                kitchen=kitchen,
                moment=ctx["moment"],
                time=ctx["time"],
                ambition=day_ambition,
            ),
        }

        # Optioneel verrijken (alleen als aanwezig)
        if hasattr(dish, "recipe_text") and dish.recipe_text:
            day_out["recipe_text"] = dish.recipe_text

        if hasattr(dish, "recipe_steps") and dish.recipe_steps:
            day_out["recipe_steps"] = dish.recipe_steps

        if hasattr(dish, "ingredients") and dish.ingredients:
            day_out["ingredients"] = dish.ingredients

        out_days.append(day_out)

    # =============================
    # 5. Resultaat (engine-contract)
    # =============================
    result: Dict[str, Any] = {
        "days_count": days,
        "persons": persons,
        "days": out_days,
    }

    # Convenience voor Peet-Card (dag 1 centraal)
    if out_days:
        first_day = out_days[0]
        if "recipe_text" in first_day:
            result["recipe_text"] = first_day["recipe_text"]
        if "recipe_steps" in first_day:
            result["recipe_steps"] = first_day["recipe_steps"]

    return result


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
        # 🔽 ESSENTIEEL: variatie-seed doorgeven
        "variation_seed": int(raw.get("variation_seed", 0)),
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
    variation_seed: int,
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

    # VARIATIE-SEED (deterministisch, niet random)
    seed = variation_seed or 0


    # vaste, stabiele sortering
    candidates.sort(
        key=lambda d: d.name_en if language == "en" else d.name_nl
    )

    # seed bepaalt startpunt
    index = seed % len(candidates)

    return candidates[index]



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

def build_plan_pdf(result):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit
    from datetime import date

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    day = result["days"][0]
    dish_name = day.get("dish_name", "")
    preparation = day.get("preparation", "")
    ingredients = day.get("ingredients", [])

    # ===============================
    # PAGINA 1 — GERECHT
    # ===============================
    y = height - 50

    # Titel
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, dish_name)
    y -= 30

    # Ingrediënten
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Ingrediënten")
    y -= 18

    c.setFont("Helvetica", 10)
    for item in ingredients:
        c.drawString(55, y, f"- {item}")
        y -= 14
        if y < 100:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 10)

    y -= 20

    # Bereiding
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Bereiding")
    y -= 18

    c.setFont("Helvetica", 10)
    max_width = width - 95
    line_height = 13

    steps = [s.strip() for s in preparation.split("\n") if s.strip()]

    for step in steps:
        lines = simpleSplit(step, "Helvetica", 10, max_width)
        for line in lines:
            c.drawString(55, y, line)
            y -= line_height
            if y < 100:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 10)
        y -= 10

    # ===============================
    # PAGINA 2 — BOODSCHAPPENLIJST
    # ===============================
    c.showPage()
    y = height - 50

    c.setFont("Helvetica-Bold", 15)
    c.drawString(40, y, "Boodschappenlijst")
    y -= 30

    c.setFont("Helvetica", 10)
    for item in ingredients:
        c.drawString(55, y, f"- {item}")
        y -= 14
        if y < 100:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 10)

    c.save()
    buffer.seek(0)

    filename = f"Peet_Kiest_{date.today().strftime('%Y%m%d')}.pdf"
    return buffer, filename
