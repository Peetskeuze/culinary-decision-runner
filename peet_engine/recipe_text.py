from typing import Dict


RECIPES: Dict[str, Dict[str, str]] = {
    "Citroen couscous met kruiden en groenten": {
        "opening": (
            "Dit is zo’n gerecht dat licht aanvoelt, maar toch vult. "
            "Fris door de citroen, warm door de kruiden en met genoeg groenten "
            "om er zonder nadenken van te eten.\n\n"
            "Ideaal voor doordeweeks, wanneer je iets goeds wilt maken "
            "zonder dat het ingewikkeld wordt."
        ),
        "preparation": (
            "Zo pak je dit aan.\n\n"
            "Begin met de couscous. Giet er heet water over en laat hem "
            "rustig wellen terwijl jij de rest voorbereidt. "
            "Snijd de groenten in grove stukken en bak ze in een ruime pan "
            "met olijfolie en kruiden. Geef ze de tijd om zacht te worden "
            "en kleur te krijgen.\n\n"
            "Maak de couscous los met een vork, rasp er wat citroenschil over "
            "en schep alles samen. Proef, stel bij en stop zodra het klopt. "
            "Dit gerecht hoeft niet af om goed te zijn."
        ),
    },

    "Geroosterde bloemkool met kruidige yoghurt en citroen": {
        "opening": (
            "Bloemkool is zo’n groente die het goed doet als je hem met rust laat. "
            "In de oven geroosterd wordt hij nootachtig en vol van smaak, "
            "zonder dat je er veel aan hoeft te doen.\n\n"
            "Met frisse yoghurt en citroen voelt dit als een complete maaltijd, "
            "niet als een compromis."
        ),
        "preparation": (
            "Zo pakken we dit aan.\n\n"
            "Verwarm de oven voor en snijd de bloemkool in flinke roosjes. "
            "Meng ze met olijfolie, kruiden, zout en peper en spreid ze uit "
            "op een bakplaat. De oven doet nu het werk. Laat de bloemkool "
            "rustig roosteren tot hij goudbruin is en zacht van binnen.\n\n"
            "Meng ondertussen de yoghurt met knoflook, citroen en een scheut "
            "olijfolie. Haal de bloemkool uit de oven, geef alles even rust "
            "en serveer het samen. Meer hoeft het niet te zijn."
        ),
    },
}


def get_recipe(dish_name: str) -> Dict[str, str]:
    return RECIPES.get(
        dish_name,
        {
            "opening": (
                "Dit is een gerecht dat je zonder nadenken op tafel zet. "
                "Rustig, logisch en precies goed voor het moment."
            ),
            "preparation": (
                "Zo pak je dit aan.\n\n"
                "Bereid het gerecht stap voor stap op een manier die voor jou "
                "logisch voelt. Neem de tijd waar het kan en stop zodra het klopt."
            ),
        },
    )
