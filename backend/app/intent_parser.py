"""Deterministically map simple user requests to canonical POI categories.

This lightweight parser uses keyword and phrase matching without external NLP
or LLM dependencies.
"""

import string


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pharmacy": (
        "medicine",
        "medicines",
        "tablet",
        "tablets",
        "pharmacy items",
    ),
    "restaurant": (
        "eat",
        "food",
        "lunch",
        "dinner",
        "restaurant",
    ),
    "hospital": (
        "doctor",
        "physician",
        "hospital",
        "medical checkup",
        "checkup",
    ),
}

_PUNCTUATION_TRANSLATION = str.maketrans(
    string.punctuation,
    " " * len(string.punctuation),
)


def parse_intent(text: str | None) -> str | None:
    """Return one matching POI category, or None for unknown/ambiguous input."""
    if not isinstance(text, str):
        return None

    normalized = " ".join(
        text.casefold().translate(_PUNCTUATION_TRANSLATION).split()
    )
    if not normalized:
        return None

    padded_text = f" {normalized} "
    matches = [
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(f" {keyword} " in padded_text for keyword in keywords)
    ]
    return matches[0] if len(matches) == 1 else None
