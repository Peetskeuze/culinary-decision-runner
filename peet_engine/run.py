# =========================================================
# PEET ENGINE — RUN ENTRYPOINT
# Publieke interface voor UI (Streamlit, tests, Carrd)
# =========================================================

import json
from typing import Dict, Any

from peet_engine.context import build_context
from peet_engine.engine import plan


def call_peet(raw_input: str | Dict[str, Any]) -> Dict[str, Any]:
    """
    Stabiele entrypoint voor Peet Engine.

    raw_input:
      - JSON string (van Streamlit / Carrd)
      - of dict (bij interne calls / tests)
    """

    # 1. JSON → dict indien nodig
    if isinstance(raw_input, str):
        try:
            raw_input = json.loads(raw_input)
        except Exception as e:
            raise ValueError("Ongeldige JSON input voor Peet Engine") from e

    # 2. Context bouwen
    context = build_context(raw_input)

    # 3. Engine uitvoeren (juiste API)
    result = plan(context)

    return result
