# core/llm.py
import os
from openai import OpenAI

from core.prompt import PROMPT_PEET_CARD_TEXT


MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_peet_text(user_context: str, *, system_prompt: str = PROMPT_PEET_CARD_TEXT) -> str:
    """
    Peet-Card (vandaag) — vrije tekst.
    GEEN JSON parsing. GEEN extract_json.

    user_context: string met context + variatie nonce.
    """
    resp = _client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_context},
        ],
    )
    text = (resp.output_text or "").strip()
    if not text:
        return "Peet is even stil. Refresh nog een keer."
    return text
