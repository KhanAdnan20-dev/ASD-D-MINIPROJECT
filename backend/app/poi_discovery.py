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
    "pharmacy": [
        ("amenity", "pharmacy"),
        ("healthcare", "pharmacy"),
        ("shop", "chemist"),
        ("shop", "medical_supply"),
    ],
    "restaurant": [
        ("amenity", "restaurant"),
        ("amenity", "fast_food"),
        ("amenity", "cafe"),
        ("amenity", "food_court"),
    ],
    "hospital": [
        ("amenity", "hospital"),
        ("amenity", "clinic"),
        ("amenity", "doctors"),
        ("healthcare", "hospital"),
        ("healthcare", "clinic"),
    ],
    "grocery": [
        ("shop", "supermarket"),
        ("shop", "convenience"),
        ("shop", "grocery"),
    ],
    "supermarket": [
        ("shop", "supermarket"),
        ("shop", "convenience"),
        ("shop", "grocery"),
    ],
    "cafe": [
        ("amenity", "cafe"),
    ],
    "fuel": [
        ("amenity", "fuel"),
    ],
    "bank": [
        ("amenity", "bank"),
        ("amenity", "atm"),
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
    corridor_buffer: float = 0.035,
    limit: int = 25,
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

    # Build Overpass QL query across nodes, ways, and relations (nwr)
    nwr_queries = "\n".join(
        f'  nwr["{key}"="{value}"]({south},{west},{north},{east});'
        for key, value in tags
    )
    query = f"""[out:json][timeout:15];
(
{nwr_queries}
);
out center {limit * 3};
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
    seen_coords: set[tuple[float, float]] = set()

    for element in data.get("elements", []):
        lat = element.get("lat")
        lon = element.get("lon")
        if lat is None or lon is None:
            center = element.get("center")
            if center:
                lat = center.get("lat")
                lon = center.get("lon")

        if lat is None or lon is None:
            continue

        coord_key = (round(lat, 4), round(lon, 4))
        if coord_key in seen_coords:
            continue

        point = Point(lon, lat)
        if not corridor.covers(point):
            continue

        tags_dict = element.get("tags", {})
        name = (
            tags_dict.get("name")
            or tags_dict.get("brand")
            or tags_dict.get("operator")
        )
        if not name:
            street = tags_dict.get("addr:street")
            if street:
                name = f"{category.title()} on {street}"
            else:
                name = f"{category.title()} (OSM #{element.get('id', 'Place')})"

        seen_coords.add(coord_key)
        pois.append(
            {
                "name": name,
                "category": category,
                "lat": float(lat),
                "lng": float(lon),
            }
        )

    return pois[:limit]
