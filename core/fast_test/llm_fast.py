from openai import OpenAI
import json
from core.fast_test.prompt_fast import PEET_PROMPT_FAST

# Client
_client = OpenAI()

# Sneller en lichter model (perfect voor koken)
FAST_MODEL = "gpt-4o-mini"


def fetch_peet_choice_fast(context: dict) -> dict:
    """
    Snelle testversie van Peet LLM call
    """

    # Context netjes als tekst toevoegen
    context_text = json.dumps(context, ensure_ascii=False)

    full_prompt = f"""
{PEET_PROMPT_FAST}

Context:
{context_text}
"""

    response = _client.responses.create(
        model=FAST_MODEL,
        input=full_prompt,
        max_output_tokens=800,  # begrens output (scheelt tijd!)
    )

    # Output ophalen
    raw = response.output_text

    try:
        return json.loads(raw)
    except Exception:
        # fallback als model kleine rommel meegeeft
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
