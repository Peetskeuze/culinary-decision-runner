# peet_engine/shared/parsing.py

from typing import Any, List


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, int):
            return value
        return int(str(value).strip().split()[0])
    except Exception:
        return default


def split_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_str(v) for v in value if normalize_str(v)]
    if isinstance(value, str):
        return [normalize_str(v) for v in value.replace(";", ",").split(",") if normalize_str(v)]
    return []


def normalize_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()
