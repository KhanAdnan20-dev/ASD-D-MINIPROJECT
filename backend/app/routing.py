"""Road routing via the OSRM public demo API.

Fetches real road-network route geometry, distance, and duration
between GPS coordinates and multi-stop waypoints.
"""

import httpx

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1"
_TIMEOUT = 15.0

_PROFILE_MAP: dict[str, str] = {
    "driving": "driving",
    "walking": "foot",
    "cycling": "bike",
}


def get_road_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    transport_mode: str = "driving",
) -> dict | None:
    """Fetch a real road route from the OSRM public API.

    Returns a dict with:
    - ``coordinates``: list of ``[lng, lat]`` pairs (GeoJSON order)
    - ``distance_km``: total route distance in kilometres
    - ``duration_mins``: estimated travel time in minutes

    Returns ``None`` when OSRM cannot produce a route.
    """
    return get_multi_stop_route(
        [(origin_lat, origin_lng), (dest_lat, dest_lng)],
        transport_mode=transport_mode,
    )


def get_multi_stop_route(
    waypoints: list[tuple[float, float]],
    transport_mode: str = "driving",
) -> dict | None:
    """Fetch a real multi-waypoint road route from the OSRM API.

    *waypoints* is a sequence of ``(lat, lng)`` tuples in order:
    ``[origin, stop1, stop2, ..., destination]``.

    Returns a dict with:
    - ``coordinates``: list of ``[lng, lat]`` pairs (GeoJSON order)
    - ``distance_km``: total route distance in kilometres
    - ``duration_mins``: estimated travel time in minutes

    Returns ``None`` when OSRM cannot produce a route.
    """
    if len(waypoints) < 2:
        return None

    profile = _PROFILE_MAP.get(transport_mode, "driving")
    coords_str = ";".join(f"{lng},{lat}" for lat, lng in waypoints)

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.get(
                f"{OSRM_BASE_URL}/{profile}/{coords_str}",
                params={
                    "overview": "full",
                    "geometries": "geojson",
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route = data["routes"][0]
    return {
        "coordinates": route["geometry"]["coordinates"],
        "distance_km": round(route["distance"] / 1000, 2),
        "duration_mins": round(route["duration"] / 60, 1),
    }
