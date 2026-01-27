import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
from core.fast_test.llm_fast import fetch_peet_choice_fast
from context_builder import build_context

raw_context = {
    "persons": "1",
    "time": "ruim",
    "moment": "speciaal",
    "preference": "peet",
    "kitchen": "maakt_niet_uit",
    "fridge": "lamschouder",
    "nogo": "",
    "allergies": "1"
}


context = build_context(raw_context)

print("⏳ Start snelle Peet test...")

start = time.time()
result = fetch_peet_choice_fast(context)
end = time.time()

print("\n✅ Resultaat:")
print(result)

print(f"\n⏱️ Tijd: {round(end - start, 2)} seconden")
