# core/image_generator.py

import os
import base64
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY")

_client = OpenAI(api_key=API_KEY)

OUTPUT_DIR = "output/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_food_image(dish_name: str) -> str:
    """
    Genereert een food afbeelding op basis van gerechtnaam.
    Geeft pad naar lokaal PNG bestand terug.
    """

    if not dish_name:
        return ""

    filename = "".join(c for c in dish_name if c.isalnum() or c in " -_").rstrip()
    path = os.path.join(OUTPUT_DIR, f"{filename}.png")

    # Cache: als al bestaat → niet opnieuw genereren
    if os.path.exists(path):
        return path

    prompt = f"""
    Maak een realistische foodfoto van {dish_name}.
    Het gerecht is huisgemaakt en ziet eruit alsof het net thuis is gekookt.
    Het ligt casual opgediend op een normaal keramisch bord of in een pan op een houten keukentafel.
    Gebruik natuurlijk daglicht dat zacht vanuit een raam komt, met lichte schaduwen en warme kleuren.
    De presentatie is niet perfect met lichte imperfecties.
    De texturen zijn echt en herkenbaar.
    De sfeer is warm en uitnodigend.
    Geen restaurantstijl, geen studio belichting, geen glamour.
    """

    result = _client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    with open(path, "wb") as f:
        f.write(image_bytes)

    return path
