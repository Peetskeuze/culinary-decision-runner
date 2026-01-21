# peet_engine/canon.py
"""
Peet Canon — hoeveelheden per persoon (culinair uitgangspunt)

Dit bestand bevat de vaste, culinaire bandbreedtes.
Geen context, geen personen, geen afronding.
Deze waarden zijn de ENIGE waarheid voor hoeveelheden.
"""

CANON = {
    "aardappelen": {
        "rauw": (250, 300),
        "gekookt": (200, 250),
        "gebakken": (180, 220),
    },
    "groenten": {
        "totaal": (200, 250),
        "hoofdgerecht_min": 150,
        "praktisch_min": 150,
    },
    "granen": {
        "droog": (70, 80),
        "gekookt": (180, 220),
    },
    "pasta": {
        "droog_normaal": (75, 90),
        "droog_hoofdgerecht": (90, 100),
        "gekookt": (200, 230),
    },
    "vlees": {
        "doordeweeks": (100, 125),
        "lekker_eten": 150,
        "gegaard": (80, 110),
    },
    "vis": {
        "witvis": (140, 160),
        "vet": (125, 150),
        "gegaard": (110, 130),
    },
    "vega_eiwit": {
        "tofu_tempeh": (125, 150),
        "peulvruchten": (150, 200),
    },
}
