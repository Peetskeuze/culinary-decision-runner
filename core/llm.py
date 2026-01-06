# core/llm.py

import os
from openai import OpenAI
from core.prompts import PROMPT_PEET_KIEST
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
