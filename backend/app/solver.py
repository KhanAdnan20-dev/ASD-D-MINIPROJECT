"""Deterministic greedy multi-stop route solver (IW-4).

Projects candidate POIs onto the actual OSRM road route geometry, calculates
perpendicular off-route distances, approximates round-trip detour cost, filters
infeasible candidates, and greedily selects the minimum-detour stops while respecting
capacity and minimum spacing constraints.

Algorithmic Design:
1. Route Representation: OSRM coordinates are represented as a Shapely LineString
   in (longitude, latitude) coordinate order.
2. Route Projection: Each candidate POI Point(lng, lat) is projected onto the route
   polyline using scalar linear referencing (route.project).
3. Detour Estimation: Detour is estimated as 2 * distance_from_route_km (the lateral
   round-trip deviation).
4. Feasibility & Spacing: Candidates exceeding max_detour_km or violating minimum
   spacing with already chosen stops are excluded.
5. Deterministic Greedy Selection: Repeatedly picks the lowest-detour candidate,
   breaking ties deterministically by off-route distance, route fraction, and POI identifier.
6. Route Ordering: Final selected stops are sorted in ascending along-route order.

Complexity: O(k * n) where n is the number of candidates and k is max_stops.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import LineString, Point

from app.models import CandidatePOI, Coordinate, POI, SelectedPOI, SolverResult

DEFAULT_MAX_STOPS: int = 3
DEFAULT_MAX_DETOUR_KM: float = 2.0
DEFAULT_MIN_SPACING_KM: float = 1.0


def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two GPS coordinates in kilometres."""
    r = 6371.0088  # Mean Earth radius in kilometres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r * c


def _extract_coord(val: Any) -> tuple[float, float] | None:
    """Extract (lat, lng) from a Coordinate model, tuple, or dict."""
    if isinstance(val, Coordinate):
        return val.lat, val.lng
    if isinstance(val, (tuple, list)) and len(val) >= 2:
        lat, lng = float(val[0]), float(val[1])
        return lat, lng
    if isinstance(val, dict) and "lat" in val and "lng" in val:
        return float(val["lat"]), float(val["lng"])
    return None


def _is_valid_coordinate(lat: float, lng: float) -> bool:
    """Verify that latitude and longitude are valid finite numbers in acceptable ranges."""
    return (
        math.isfinite(lat)
        and math.isfinite(lng)
        and -90.0 <= lat <= 90.0
        and -180.0 <= lng <= 180.0
    )


def _poi_sort_id(val: Any) -> tuple[int, Any]:
    """Provide a consistent sorting key for integer or string identifiers."""
    if isinstance(val, int):
        return (0, val)
    try:
        return (0, int(val))
    except (ValueError, TypeError):
        return (1, str(val))


def solve_route_stops(
    origin: Coordinate | tuple[float, float] | dict[str, float],
    destination: Coordinate | tuple[float, float] | dict[str, float],
    route_geometry: list[list[float]],
    candidate_pois: list[CandidatePOI | POI | dict[str, Any]],
    max_stops: int = DEFAULT_MAX_STOPS,
    max_detour_km: float = DEFAULT_MAX_DETOUR_KM,
    min_spacing_km: float = DEFAULT_MIN_SPACING_KM,
) -> SolverResult:
    """Solve multi-stop POI selection along a road route using a deterministic greedy heuristic.

    Args:
        origin: Journey starting coordinate.
        destination: Journey destination coordinate.
        route_geometry: List of [lng, lat] coordinate pairs from OSRM.
        candidate_pois: Candidate places along the corridor.
        max_stops: Maximum number of intermediate stops to recommend.
        max_detour_km: Maximum acceptable estimated detour in kilometres.
        min_spacing_km: Minimum distance between any two selected stops.

    Returns:
        SolverResult containing selected stops in travel order, total detour, and solver metrics.
    """
    total_candidates = len(candidate_pois) if candidate_pois else 0
    if not candidate_pois:
        return SolverResult(
            selected_stops=[],
            total_estimated_detour_km=0.0,
            candidate_count=0,
            selected_count=0,
            solver_status="no_candidates",
        )

    orig_coord = _extract_coord(origin)
    dest_coord = _extract_coord(destination)

    # Build Shapely LineString for route in (longitude, latitude) order
    valid_coords: list[tuple[float, float]] = []
    if route_geometry:
        for pt in route_geometry:
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                lng, lat = float(pt[0]), float(pt[1])
                if _is_valid_coordinate(lat, lng):
                    valid_coords.append((lng, lat))

    if len(valid_coords) < 2:
        # Fallback to straight origin -> destination line if geometry is degenerate
        if (
            orig_coord
            and dest_coord
            and _is_valid_coordinate(*orig_coord)
            and _is_valid_coordinate(*dest_coord)
        ):
            valid_coords = [
                (orig_coord[1], orig_coord[0]),
                (dest_coord[1], dest_coord[0]),
            ]
        else:
            return SolverResult(
                selected_stops=[],
                total_estimated_detour_km=0.0,
                candidate_count=total_candidates,
                selected_count=0,
                solver_status="no_feasible_stops",
            )

    route_line = LineString(valid_coords)
    route_length_deg = route_line.length

    # ── Evaluate and filter candidates ──────────────────────────────────────
    feasible_candidates: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for idx, poi in enumerate(candidate_pois):
        # Extract POI properties
        if isinstance(poi, dict):
            poi_id = poi.get("id", idx + 1)
            name = poi.get("name", "Unnamed POI")
            category = poi.get("category", "unknown")
            lat = float(poi.get("lat", poi.get("latitude", 0.0)))
            lng = float(poi.get("lng", poi.get("longitude", 0.0)))
        elif isinstance(poi, POI):
            poi_id = poi.id
            name = poi.name
            category = poi.category
            lat = poi.latitude
            lng = poi.longitude
        elif isinstance(poi, CandidatePOI):
            poi_id = idx + 1
            name = poi.name
            category = poi.category
            lat = poi.lat
            lng = poi.lng
        else:
            continue

        if not _is_valid_coordinate(lat, lng):
            continue

        # Exclude exact duplicates
        dedup_key = f"{name.strip().casefold()}_{round(lat, 5)}_{round(lng, 5)}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        # Exclude candidates too close to origin or destination (< 50m)
        if orig_coord and haversine_distance_km(lat, lng, orig_coord[0], orig_coord[1]) < 0.05:
            continue
        if dest_coord and haversine_distance_km(lat, lng, dest_coord[0], dest_coord[1]) < 0.05:
            continue

        # Project POI onto route LineString
        poi_point = Point(lng, lat)
        route_pos = route_line.project(poi_point)
        route_fraction = (
            min(1.0, max(0.0, route_pos / route_length_deg))
            if route_length_deg > 0
            else 0.0
        )

        nearest_pt = route_line.interpolate(route_pos)
        distance_from_route_km = haversine_distance_km(lat, lng, nearest_pt.y, nearest_pt.x)
        estimated_detour_km = 2.0 * distance_from_route_km

        # Check detour feasibility threshold
        if estimated_detour_km > max_detour_km:
            continue

        feasible_candidates.append(
            {
                "id": poi_id,
                "name": name,
                "category": category,
                "lat": lat,
                "lng": lng,
                "route_fraction": round(route_fraction, 4),
                "distance_from_route_km": round(distance_from_route_km, 3),
                "estimated_detour_km": round(estimated_detour_km, 3),
            }
        )

    if not feasible_candidates:
        return SolverResult(
            selected_stops=[],
            total_estimated_detour_km=0.0,
            candidate_count=total_candidates,
            selected_count=0,
            solver_status="no_feasible_stops",
        )

    # ── Deterministic Greedy Selection ──────────────────────────────────────
    selected_raw: list[dict[str, Any]] = []

    while len(selected_raw) < max_stops:
        eligible: list[dict[str, Any]] = []
        for cand in feasible_candidates:
            if any(cand["id"] == s["id"] for s in selected_raw):
                continue

            # Enforce minimum spacing constraint against all already selected stops
            too_close = False
            for s in selected_raw:
                dist = haversine_distance_km(cand["lat"], cand["lng"], s["lat"], s["lng"])
                if dist < min_spacing_km:
                    too_close = True
                    break

            if not too_close:
                eligible.append(cand)

        if not eligible:
            break

        # Pick candidate minimizing detour, with deterministic tie-breaking
        best = min(
            eligible,
            key=lambda c: (
                c["estimated_detour_km"],
                c["distance_from_route_km"],
                c["route_fraction"],
                _poi_sort_id(c["id"]),
                c["name"],
            ),
        )
        selected_raw.append(best)

    # ── Final Route-Ordered Sorting ─────────────────────────────────────────
    selected_raw.sort(key=lambda s: (s["route_fraction"], s["estimated_detour_km"]))

    selected_stops = [SelectedPOI(**s) for s in selected_raw]
    total_detour = round(sum(s.estimated_detour_km for s in selected_stops), 2)

    status = "success" if selected_stops else "no_feasible_stops"

    return SolverResult(
        selected_stops=selected_stops,
        total_estimated_detour_km=total_detour,
        candidate_count=total_candidates,
        selected_count=len(selected_stops),
        solver_status=status,
    )
