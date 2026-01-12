import base64
from openai import OpenAI

client = OpenAI()

def generate_dish_image_bytes(dish_name: str) -> bytes | None:
    """
    Genereert één gerecht-afbeelding op aanvraag.
    Retourneert raw image bytes of None bij fout.
    """

    prompt = (
        f"Maak een realistische, smakelijke foto van het gerecht '{dish_name}'. "
        "Neutrale achtergrond, natuurlijk licht, geen tekst, geen mensen."
    )

    try:
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        b64 = resp.data[0].b64_json
        return base64.b64decode(b64)

    except Exception as e:
        # Geen crash in de app, alleen stil falen
        print(f"[image-gen] {e}")
        return None
