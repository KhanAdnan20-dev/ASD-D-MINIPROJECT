"""Forward geocoding via the Nominatim (OpenStreetMap) API.

Resolves a human-readable place name to latitude/longitude coordinates.
Uses the public Nominatim instance with a polite User-Agent header.
"""

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "IntentWay/0.1 (BTech university project)"
_TIMEOUT = 10.0


def geocode(place_name: str) -> dict | None:
    """Resolve a place name to coordinates using Nominatim.

    Returns a dict with ``lat``, ``lng``, and ``display_name`` on success,
    or ``None`` when the location cannot be found.
    """
    if not isinstance(place_name, str) or not place_name.strip():
        return None

    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.get(
            NOMINATIM_URL,
            params={
                "q": place_name.strip(),
                "format": "json",
                "limit": 1,
            },
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
        results = response.json()

    if not results:
        return None

    return {
        "lat": float(results[0]["lat"]),
        "lng": float(results[0]["lon"]),
        "display_name": results[0].get("display_name", place_name.strip()),
    }
