import os
import base64
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Gerecht uit Peet Kiest ===
dish_name = "Kruidige kippendij met geroosterde groenten en yoghurtsaus"

# === Peet Kiest vaste beeldprompt ===
prompt = f"""
Maak een realistische foodfoto van {dish_name}.
Het gerecht is huisgemaakt en ziet eruit alsof het net thuis is gekookt.
Het ligt casual opgediend op een normaal keramisch bord of in een pan op een houten keukentafel.
Gebruik natuurlijk daglicht dat zacht vanuit een raam komt, met lichte schaduwen en warme kleuren.
De presentatie is niet perfect: kleine imperfecties zijn zichtbaar.
De texturen van het eten zijn echt en herkenbaar.
De sfeer is gezellig, warm en uitnodigend.
Geen restaurantstijl, geen studio belichting, geen glamour.
"""

print("Bezig met afbeelding genereren...")

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024"
)

# 👉 Haal base64 data op
image_base64 = result.data[0].b64_json

# 👉 Decode naar echte PNG
image_bytes = base64.b64decode(image_base64)

with open("peet_test_image.png", "wb") as f:
    f.write(image_bytes)

print("Klaar! Afbeelding opgeslagen als peet_test_image.png")
