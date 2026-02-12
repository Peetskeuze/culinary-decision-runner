from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import re


ACCENT_POOL: List[str] = ["Italiaans", "Mediterraans", "Aziatisch"]


def _safe_int(x: Any, default: int) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return default


def _split_list(v: Any) -> List[str]:
    if not v:
        return []
    if isinstance(v, list):
        out = []
        for item in v:
            s = str(item).strip()
            if s:
                out.append(s)
        return out
    s = str(v).strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts if parts else [s]


def _parse_days(v: Any) -> int:
    # Carrd kan geven: "2 dagen" of "2+dagen"
    if isinstance(v, int):
        d = v
    else:
        s = str(v or "").replace("+", " ")
        m = re.search(r"(\d+)", s)
        d = int(m.group(1)) if m else 2
    return d if d in (2, 3, 4, 5) else 2


def _parse_checked(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("checked", "on", "true", "1", "yes")


def _clamp_persons(n: int) -> int:
    return max(1, min(int(n), 8))


def compute_kitchen_plan(days: int, rotation_index: int) -> Dict[int, str]:
    """
    Jouw keukenlogica:
    - 2 dagen: beide NL/BE
    - 3 dagen: dag 1 en 3 NL/BE, dag 2 accent
    - 4 dagen: dag 1 en 3 NL/BE, dag 2 en 4 accent
    - 5 dagen: dag 1, 3 en 5 NL/BE, dag 2 en 4 accent
    - FR vermijden (zit niet in accent pool)
    - Rotatie voorkomt dat dag 2 altijd Italiaans is als iemand dit wekelijks herhaalt
    """
    if days == 2:
        nlbe_days = {1, 2}
    elif days in (3, 4):
        nlbe_days = {1, 3}
    else:  # 5
        nlbe_days = {1, 3, 5}

    accent_days = [d for d in range(1, days + 1) if d not in nlbe_days]

    plan: Dict[int, str] = {}
    for day in range(1, days + 1):
        if day in nlbe_days:
            plan[day] = "NL/BE"
        else:
            # accent per accent_day in volgorde, zonder dubbele binnen 1 run
            idx = accent_days.index(day)
            plan[day] = ACCENT_POOL[(rotation_index + idx) % len(ACCENT_POOL)]
    return plan


def next_rotation_index(current: int) -> int:
    return (int(current) + 1) % len(ACCENT_POOL)


@dataclass(frozen=True)
class VooruitInput:
    days: int
    persons: int
    vegetarian: bool
    allergies: List[str]
    nogo: List[str]
    fridge: str


def parse_query_params(qp: Dict[str, Any]) -> VooruitInput:
    days = _parse_days(qp.get("days", 2))
    persons = _clamp_persons(_safe_int(qp.get("persons", 2), 2))
    vegetarian = _parse_checked(qp.get("vegetarian"))
    allergies = _split_list(qp.get("allergies"))
    nogo = _split_list(qp.get("nogo"))
    fridge = str(qp.get("fridge", "") or "").strip()
    return VooruitInput(
        days=days,
        persons=persons,
        vegetarian=vegetarian,
        allergies=allergies,
        nogo=nogo,
        fridge=fridge,
    )
