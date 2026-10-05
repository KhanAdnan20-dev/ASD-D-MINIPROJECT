"""Discover real POIs from OpenStreetMap via the Overpass API.

Reuses the IW-3 spatial corridor geometry (``build_route_line`` and
``build_corridor`` from ``app.spatial_filter``) to scope Overpass
results to the route corridor.
"""

import httpx
from shapely.geometry import Point

from app.models import Coordinate
from app.spatial_filter import build_corridor, build_route_line

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
_TIMEOUT = 20.0

_OSM_TAG_MAP: dict[str, list[tuple[str, str]]] = {
    "pharmacy": [("amenity", "pharmacy")],
    "restaurant": [
        ("amenity", "restaurant"),
        ("amenity", "fast_food"),
        ("amenity", "cafe"),
    ],
    "hospital": [
        ("amenity", "hospital"),
        ("amenity", "clinic"),
        ("amenity", "doctors"),
    ],
    "grocery": [
        ("shop", "supermarket"),
        ("shop", "convenience"),
        ("shop", "grocery"),
    ],
}


def _bbox_from_geometry(geometry) -> tuple[float, float, float, float]:
    """Extract ``(south, west, north, east)`` from a Shapely geometry."""
    west, south, east, north = geometry.bounds
    return round(south, 5), round(west, 5), round(north, 5), round(east, 5)


def discover_pois_along_route(
    origin: Coordinate,
    destination: Coordinate,
    category: str,
    corridor_buffer: float = 0.02,
    limit: int = 15,
) -> list[dict]:
    """Discover real OSM POIs of *category* inside the route corridor.

    Uses IW-3 ``build_route_line`` and ``build_corridor`` to construct
    the Shapely corridor polygon, then queries the Overpass API within
    its bounding box and filters results to only include POIs that fall
    inside the corridor.

    Returns a list of dicts with ``name``, ``category``, ``lat``, ``lng``.
    Returns an empty list when no matching POIs are found or when the
    category is unknown.
    """
    tags = _OSM_TAG_MAP.get(category)
    if not tags:
        return []

    # Build corridor using existing IW-3 spatial logic
    route_line = build_route_line(origin, destination)
    corridor = build_corridor(route_line, corridor_buffer)
    south, west, north, east = _bbox_from_geometry(corridor)

    # Build Overpass QL query for all matching OSM tag combinations
    node_queries = "\n".join(
        f'  node["{key}"="{value}"]({south},{west},{north},{east});'
        for key, value in tags
    )
    query = f"""[out:json][timeout:15];
(
{node_queries}
);
out body {limit};
"""

    headers = {
        "User-Agent": "IntentWay/0.1 (BTech university project; contact@intentway.local)",
    }

    data: dict = {}
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                response = client.post(
                    endpoint,
                    data={"data": query},
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    break
        except Exception:
            continue

    # Filter results through the Shapely corridor polygon (IW-3 reuse)
    pois: list[dict] = []
    for element in data.get("elements", []):
        if "lat" not in element or "lon" not in element:
            continue

        point = Point(element["lon"], element["lat"])
        if not corridor.covers(point):
            continue

        name = element.get("tags", {}).get("name")
        if not name:
            continue

        pois.append(
            {
                "name": name,
                "category": category,
                "lat": element["lat"],
                "lng": element["lon"],
            }
        )

    return pois[:limit]
