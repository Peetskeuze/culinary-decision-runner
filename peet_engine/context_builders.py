from typing import Dict, Any


def build_today_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context voor 'Vandaag' (1 dag).
    Alle opties van de gebruiker zijn leidend.
    """
    return {
        "mode": "vandaag",
        "days": 1,

        "persons": int(raw.get("persons", 2)),
        "vegetarian": bool(raw.get("vegetarian", False)),
        "allergies": raw.get("allergies", []),
        "nogo": raw.get("nogo", []),

        "moment": raw.get("moment", "doordeweeks"),
        "time": raw.get("time", "normaal"),
        "ambition": int(raw.get("ambition", 2)),

        "language": raw.get("language", "nl"),
    }


def build_forward_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context voor 'Vooruit' (2 / 3 / 5 dagen).
    Alleen toegestane inputs worden gebruikt.
    """
    days = int(raw.get("days", 2))
    if days not in (2, 3, 5):
        days = 2

    return {
        "mode": "vooruit",
        "days": days,

        "persons": int(raw.get("persons", 2)),
        "allergies": raw.get("allergies", []),
        "nogo": raw.get("nogo", []),

        "vegetarian": False,
        "moment": "auto",
        "time": "normaal",
        "ambition": 2,
        "language": "nl",
    }
