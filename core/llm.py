# -------------------------------------------------
# core/llm.py — production safe
# -------------------------------------------------

import os
import time
from openai import OpenAI, RateLimitError, APIError, APITimeoutError

from core.prompt import PROMPT


# -------------------------------------------------
# Config
# -------------------------------------------------
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
API_KEY = os.getenv("OPENAI_API_KEY")

_client = OpenAI(api_key=API_KEY)

MAX_RETRIES = 3
RETRY_DELAY = 1.5  # seconden (exponentieel)

# -------------------------------------------------
# Public API (unchanged for other scripts)
# -------------------------------------------------
def call_peet_text(user_context: str, *, system_prompt: str = PROMPT):

    """
    Peet-Card (vandaag)

    - veilig
    - retry bij tijdelijke errors
    - backwards compatible
    """

    if not API_KEY:
        return "Peet kan even geen verbinding maken. API-sleutel ontbreekt."

    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            resp = _client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context},
                ],
                max_output_tokens=1500,   # ruim genoeg voor recept
            )


            text = (resp.output_text or "").strip()

            if not text:
                return "Peet is even stil. Refresh nog een keer."

            return text

        except RateLimitError:
            # quota / tijdelijke limiet
            attempt += 1
            if attempt >= MAX_RETRIES:
                return "Peet heeft het druk. Probeer het zo nog eens."

            time.sleep(RETRY_DELAY * attempt)

        except APITimeoutError:
            attempt += 1
            if attempt >= MAX_RETRIES:
                return "Peet deed er te lang over. Probeer opnieuw."

            time.sleep(RETRY_DELAY * attempt)

        except APIError:
            attempt += 1
            if attempt >= MAX_RETRIES:
                return "Peet had een technisch probleem. Nog een keer proberen helpt meestal."

            time.sleep(RETRY_DELAY * attempt)

        except Exception:
            # onbekende fout → geen crash
            return "Peet kon het gerecht niet ophalen. Refresh even."


# -------------------------------------------------
