# core/llm.py

import os
from openai import OpenAI
from core.prompt import PROMPT_PEET_KIEST
from core.json_utils import extract_json

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_peet(context: str) -> dict:
    resp = _client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": PROMPT_PEET_KIEST},
            {"role": "user", "content": context},
        ],
    )
    return extract_json(resp.output_text)

# -------------------------------------------------
# New API — cached single-call variant (opt-in)
# -------------------------------------------------

import json
import hashlib
from typing import Dict, Any

_LLM_CACHE: dict[str, dict] = {}


def _make_cache_key(context: Dict[str, Any]) -> str:
    """
    Stable hash for full, normalized context.
    """
    payload = json.dumps(context, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def call_peet_cached(
    *,
    system_prompt: str,
    user_prompt: str,
    cache_context: Dict[str, Any],
) -> dict:
    """
    Cached, single-call LLM invocation.

    - Parallel to call_peet()
    - Does NOT affect existing apps
    - Only used by Peet-Kiest-Vooruit v2
    """

    cache_key = _make_cache_key(cache_context)

    if cache_key in _LLM_CACHE:
        return _LLM_CACHE[cache_key]

    resp = _client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    result = extract_json(resp.output_text)

    _LLM_CACHE[cache_key] = result
    return result

