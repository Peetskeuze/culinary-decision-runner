from typing import Dict


RECIPES: Dict[str, Dict[str, object]] = {
    "Citroen couscous met kruiden en groenten": {
        "opening": (
            "Dit is zo’n gerecht dat licht aanvoelt, maar toch vult. "
            "Fris door de citroen, warm door de kruiden en met genoeg groenten "
            "om er zonder nadenken van te eten.\n\n"
            "Perfect voor dagen waarop je wel iets goeds wilt, "
            "maar het simpel wilt houden."
        ),
        "preparation": (
            "Begin met het klaarmaken van de couscous, zodat die rustig kan wellen. "
            "Snijd ondertussen de groenten en bak ze in een ruime pan met olijfolie "
            "en de kruiden die je lekker vindt. Laat ze zacht worden, zonder te haasten.\n\n"
            "Meng de couscous los met een vork, rasp er citroenschil over en schep "
            "alles samen. Proef, breng op smaak en stop zodra het klopt. "
            "Dit gerecht hoeft niet perfect te zijn om goed te zijn."
        ),
        "ingredients": {
            "Couscous": "ongeveer 80–100 g per persoon",
            "Citroen": "1 stuk",
            "Paprika": "2 stuks",
            "Courgette": "1 stuk",
            "Rode ui": "1 stuk",
            "Olijfolie": "naar behoefte",
            "Kruiden (komijn, koriander, paprikapoeder)": "naar smaak",
            "Zout en peper": "naar smaak",
        },
    },

    "Geroosterde bloemkool met kruidige yoghurt en citroen": {
        "opening": (
            "Bloemkool kan veel meer zijn dan een bijgerecht. In de oven geroosterd "
            "krijgt hij iets nootachtigs en stevigs, bijna vanzelf. "
            "Gecombineerd met kruidige yoghurt en citroen voelt dit als een "
            "volwaardige maaltijd.\n\n"
            "Vegetarisch, zonder dat je het idee hebt dat je iets inlevert."
        ),
        "preparation": (
            "Zet de oven aan en snijd de bloemkool in flinke roosjes. Meng ze met "
            "olijfolie, kruiden, zout en peper en spreid alles uit op een bakplaat. "
            "De oven doet nu het werk; laat de bloemkool rustig roosteren tot hij "
            "goudbruin is.\n\n"
            "Terwijl dat gebeurt, maak je de yoghurt fris en romig met knoflook, "
            "citroen en een scheut olijfolie. Haal de bloemkool uit de oven en "
            "serveer met de yoghurt en iets erbij wat je fijn vindt."
        ),
        "ingredients": {
            "Bloemkool": "1 grote",
            "Griekse yoghurt": "1 bak",
            "Citroen": "1 stuk",
            "Knoflook": "1–2 tenen",
            "Olijfolie": "naar behoefte",
            "Paprikapoeder": "1 tl",
            "Komijn": "1 tl",
            "Zout en peper": "naar smaak",
            "Platbrood of couscous": "ongeveer 80–100 g per persoon",
        },
    },
}


def get_recipe(dish_name: str) -> Dict[str, object]:
    return RECIPES.get(
        dish_name,
        {
            "opening": "Een gerecht dat rustig op tafel komt en precies doet wat het moet doen.",
            "preparation": "Bereid dit gerecht op een manier die voor jou logisch voelt.",
            "ingredients": {},
        },
    )
