import sys
from pathlib import Path

# Zorg dat projectroot in sys.path zit
sys.path.append(str(Path(__file__).resolve().parents[1]))

from context_builder import build_context


def test_vandaag_card_minimaal():
    raw = {
        "persons": "2",
        "time": "kort",
        "moment": "doordeweeks",
    }

    ctx = build_context(raw)

    assert ctx["mode"] == "vandaag"
    assert ctx["days"] == 1
    assert ctx["persons"] == 2
    assert ctx["vegetarian"] is False
    assert ctx["allergies"] == []
    assert ctx["kitchen"] is None


def test_vooruit_card_2_dagen():
    raw = {
        "days": "2",
        "persons": "3",
        "time": "normaal",
        "moment": "weekend",
    }

    ctx = build_context(raw)

    assert ctx["mode"] == "vooruit"
    assert ctx["days"] == 2
    assert ctx["persons"] == 3


def test_preference_veggie_mapping():
    raw = {
        "days": "3",
        "preference": "veggie",
    }

    ctx = build_context(raw)

    assert ctx["vegetarian"] is True


def test_checkbox_vegetarian_on():
    raw = {
        "days": "3",
        "vegetarian": "on",
    }

    ctx = build_context(raw)

    assert ctx["vegetarian"] is True


def test_allergies_and_nogo_combined():
    raw = {
        "days": "2",
        "allergies": "schaaldieren",
        "nogo": "pinda",
    }

    ctx = build_context(raw)

    assert sorted(ctx["allergies"]) == ["pinda", "schaaldieren"]
