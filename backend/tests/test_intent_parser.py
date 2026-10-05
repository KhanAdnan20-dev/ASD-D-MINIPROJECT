import pytest

from app.intent_parser import parse_intent


@pytest.mark.parametrize(
    "text",
    [
        "buy medicine",
        "purchase medicine",
        "buy medicines",
        "get medicine",
        "purchase some tablets",
        "buy tablets",
        "get tablets",
        "buy pharmacy items",
        "purchase tablets",
        "BUY MEDICINE",
    ],
)
def test_pharmacy_intents_map_to_pharmacy(text: str) -> None:
    assert parse_intent(text) == "pharmacy"


@pytest.mark.parametrize(
    "text",
    [
        "eat",
        "eat something",
        "have food",
        "have lunch",
        "have dinner",
        "get food",
        "find a restaurant",
        "go to a restaurant",
        "HAVE LUNCH",
    ],
)
def test_restaurant_intents_map_to_restaurant(text: str) -> None:
    assert parse_intent(text) == "restaurant"


@pytest.mark.parametrize(
    "text",
    [
        "visit a doctor",
        "see a doctor",
        "consult a doctor",
        "visit hospital",
        "go to hospital",
        "medical checkup",
        "see a physician",
        "I need to see a doctor",
        "please take me to a hospital",
    ],
)
def test_hospital_intents_map_to_hospital(text: str) -> None:
    assert parse_intent(text) == "hospital"


@pytest.mark.parametrize(
    "text",
    [
        "buy a new shirt",
        "hello",
        "random text",
        "",
        "   ",
        None,
    ],
)
def test_unknown_or_blank_intents_return_none(text: str | None) -> None:
    assert parse_intent(text) is None


@pytest.mark.parametrize(
    "text",
    [
        " BUY MEDICINE ",
        "Buy   Medicine!",
        "buy medicine",
        "buy medicine!!!",
    ],
)
def test_normalized_pharmacy_intents_map_to_pharmacy(text: str) -> None:
    assert parse_intent(text) == "pharmacy"


def test_intent_with_multiple_categories_returns_none() -> None:
    assert parse_intent("visit hospital and eat lunch") is None


def test_category_keywords_match_whole_words() -> None:
    assert parse_intent("buy tabletops") is None
