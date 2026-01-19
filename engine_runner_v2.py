# =========================================================
# Engine Runner v2 — Peet-Kiest-Vooruit (productie)
#
# Doel:
# - Eén LLM-call
# - Cachebaar op volledige context
# - Geen debug / prints
# - Geen UX-tekst in LLM
# - Volledig backwards-safe
# =========================================================

from typing import Dict, Any

from peet_engine.context import build_context, build_context_text
from peet_engine.engine import plan

# Nieuwe, parallelle LLM-API (cached)
from core.llm import call_peet_cached

# Vast system prompt (licht, strak)
from core.prompts import PEET_KIEST_VOORUIT_PROMPT

# ---------------------------------------------------------
# Public entry point
# ---------------------------------------------------------
def run(context_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Productierunner voor Peet-Kiest-Vooruit v2.

    Flow:
    1. Context normaliseren
    2. Dagprofielen bepalen (deterministisch, geen LLM)
    3. User prompt bouwen (alleen beslisinformatie)
    4. Eén gecachete LLM-call
    """

    # 1. Context (genormaliseerd, stabiel)
    ctx = build_context(context_input)

    # 2. Dagplanning (licht → voller → afronding)
    choice_plan = plan(ctx)

    # 3. User prompt (geen UX, geen uitleg)
    days_requested = ctx["days"]

    user_prompt = (
        build_context_text(ctx)
        + "\n\n"
        + f"Maak exact {days_requested} dag(en). "
          "Voeg geen extra dagen toe. "
          "De output moet exact dit aantal dagen bevatten.\n\n"
        + f"Variatie-profiel: {variatie_profiel}.\n"
          "Gebruik dit profiel subtiel voor toon, ingrediëntenkeuze en accenten. "
          "Blijf binnen dezelfde stijl en keuken.\n\n"
    )

    # Kooktechniek-regels
    if not (ctx.get("moment") == "weekend" and ctx.get("time") == "ruim"):
        user_prompt += (
            "Vermijd expliciet de volgende technieken en instructies:\n"
            "- reduceren tot stroperig\n"
            "- schuimen\n"
            "- sous-vide\n"
            "- emulsies uitleggen\n"
            "- lange rusttijden of wachttijden (zoals 45 minuten laten rusten)\n"
            "Houd alle bereidingen direct, begrijpelijk en huiselijk."
        )
    else:
        user_prompt += (
            "Omdat dit een weekendmoment met voldoende tijd is, "
            "mag iets extra aandacht worden genomen in smaak en afwerking, "
            "maar blijf altijd binnen huiselijk koken "
            "zonder professionele of chef-achtige technieken."
        )

)
    # 4. Cache-context (alles wat output beïnvloedt)
    cache_context = {
        **ctx,
        "days_plan": choice_plan,

        # Klaar voor Stap B:
        # "variatie_profiel": "licht | comfort | speels"
    }

    # 5. Exact één LLM-call (met cache)

    raw_result = call_peet_cached(
        system_prompt=PEET_KIEST_VOORUIT_PROMPT,
        user_prompt=user_prompt,
        cache_context=cache_context,
    )

    # Maak een veilige kopie zodat we de cache niet muteren
    import copy
    result = copy.deepcopy(raw_result)

    # 6. Post-process: afdwingen exact aantal dagen
    days_requested = ctx["days"]

    days = result.get("days", [])
    if len(days) > days_requested:
        days = days[:days_requested]

    result["days"] = days
    result["meta"] = {
        "days_count": len(days)
    }

    return result
