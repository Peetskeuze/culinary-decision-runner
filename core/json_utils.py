# core/json_utils.py

import json

def extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Geen JSON gevonden.")
    return json.loads(text[start:end + 1])
