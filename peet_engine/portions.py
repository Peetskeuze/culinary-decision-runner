# peet_engine/portions.py

"""
Peet Canon — vaste hoeveelheden per persoon.
Dit is de ENIGE waarheid voor porties.
"""

PORTIONS = {
    "aardappelen": {
        "raw_g": (250, 300),
        "cooked_g": (200, 250),
    },
    "groenten": {
        "total_g": (200, 250),
        "main_g": 150,
    },
    "granen": {
        "dry_g": (70, 80),
        "cooked_g": (180, 220),
    },
    "pasta": {
        "dry_g": (75, 90),
        "heavy_dry_g": (90, 100),
        "cooked_g": (200, 230),
    },
    "vlees": {
        "weekday_raw_g": (100, 125),
        "comfort_raw_g": 150,
        "cooked_g": (80, 110),
    },
    "vis": {
        "whitefish_raw_g": (140, 160),
        "fatty_raw_g": (125, 150),
        "cooked_g": (110, 130),
    },
    "vega": {
        "tofu_tempeh_g": (125, 150),
        "legumes_cooked_g": (150, 200),
    },
}
