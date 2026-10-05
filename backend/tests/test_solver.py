"""Comprehensive unit tests for the IW-4 deterministic greedy route solver."""

import pytest

from app.models import CandidatePOI, Coordinate, POI, SelectedPOI, SolverResult
from app.solver import (
    DEFAULT_MAX_DETOUR_KM,
    DEFAULT_MAX_STOPS,
    DEFAULT_MIN_SPACING_KM,
    haversine_distance_km,
    solve_route_stops,
)

# Synthetic test geometry: A straight west-to-east route across Mumbai
# Origin: (19.0000, 72.8000), Dest: (19.0000, 72.9000)
# Intermediate road vertices
SYNTHETIC_ROUTE_GEOMETRY = [
    [72.8000, 19.0000],
    [72.8250, 19.0000],
    [72.8500, 19.0000],
    [72.8750, 19.0000],
    [72.9000, 19.0000],
]

ORIGIN = Coordinate(lat=19.0000, lng=72.8000)
DESTINATION = Coordinate(lat=19.0000, lng=72.9000)


def test_haversine_distance_accuracy():
    """Verify that haversine distance gives accurate geographic distance."""
    # 1 degree of latitude at equator is approximately 111.19 km
    dist = haversine_distance_km(0.0, 0.0, 1.0, 0.0)
    assert 110.0 < dist < 112.0

    # Same point distance should be 0.0
    assert haversine_distance_km(19.05, 72.84, 19.05, 72.84) == 0.0


def test_empty_candidate_list():
    """Empty candidate list should return solver_status='no_candidates'."""
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=[],
    )
    assert isinstance(result, SolverResult)
    assert result.solver_status == "no_candidates"
    assert result.selected_stops == []
    assert result.candidate_count == 0
    assert result.selected_count == 0
    assert result.total_estimated_detour_km == 0.0


def test_single_candidate():
    """Single feasible candidate should be selected."""
    candidates = [
        CandidatePOI(name="Midway Pharmacy", category="pharmacy", lat=19.0010, lng=72.8500)
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
    )
    assert result.solver_status == "success"
    assert result.selected_count == 1
    assert result.candidate_count == 1
    assert result.selected_stops[0].name == "Midway Pharmacy"
    assert 0.4 < result.selected_stops[0].route_fraction < 0.6
    assert result.selected_stops[0].estimated_detour_km > 0.0


def test_candidate_on_route():
    """Candidate directly on the route should have near-zero detour."""
    candidates = [
        CandidatePOI(name="On-Route Store", category="pharmacy", lat=19.0000, lng=72.8500)
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
    )
    assert result.solver_status == "success"
    assert len(result.selected_stops) == 1
    stop = result.selected_stops[0]
    assert stop.distance_from_route_km < 0.005
    assert stop.estimated_detour_km < 0.01


def test_candidate_slightly_off_route():
    """Candidate slightly off route has proportional detour."""
    # ~0.002 deg north is roughly ~220m off route => ~440m estimated detour
    candidates = [
        CandidatePOI(name="Near Store", category="pharmacy", lat=19.0020, lng=72.8500)
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
    )
    assert result.solver_status == "success"
    assert 0.15 < result.selected_stops[0].distance_from_route_km < 0.35
    assert 0.30 < result.selected_stops[0].estimated_detour_km < 0.70


def test_candidate_beyond_max_detour_rejected():
    """Candidate exceeding max_detour_km should be rejected as infeasible."""
    # ~0.05 deg away is roughly ~5.5 km off-route, far exceeding 2.0 km max detour
    candidates = [
        CandidatePOI(name="Far Pharmacy", category="pharmacy", lat=19.0500, lng=72.8500)
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
        max_detour_km=2.0,
    )
    assert result.solver_status == "no_feasible_stops"
    assert result.selected_count == 0
    assert result.candidate_count == 1
    assert result.selected_stops == []


def test_max_stops_limit():
    """Solver should respect the max_stops limit."""
    # 5 feasible candidates well-spaced along route
    candidates = [
        CandidatePOI(name="Stop 1", category="pharmacy", lat=19.0005, lng=72.8150),
        CandidatePOI(name="Stop 2", category="pharmacy", lat=19.0005, lng=72.8350),
        CandidatePOI(name="Stop 3", category="pharmacy", lat=19.0005, lng=72.8550),
        CandidatePOI(name="Stop 4", category="pharmacy", lat=19.0005, lng=72.8750),
        CandidatePOI(name="Stop 5", category="pharmacy", lat=19.0005, lng=72.8900),
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
        max_stops=2,
        min_spacing_km=1.0,
    )
    assert result.solver_status == "success"
    assert result.selected_count == 2
    assert len(result.selected_stops) == 2


def test_minimum_spacing_constraint():
    """Solver skips candidates too close to an already selected stop."""
    # Two candidates right next to each other at lng=72.8500 and lng=72.8505 (~50m apart)
    # Plus one well-spaced candidate at lng=72.8800 (~3.1km away)
    candidates = [
        CandidatePOI(name="Med A (Best)", category="pharmacy", lat=19.0001, lng=72.8500),
        CandidatePOI(name="Med B (Too close to A)", category="pharmacy", lat=19.0002, lng=72.8505),
        CandidatePOI(name="Med C (Spaced)", category="pharmacy", lat=19.0003, lng=72.8800),
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
        max_stops=3,
        min_spacing_km=1.0,
    )
    assert result.selected_count == 2
    selected_names = [s.name for s in result.selected_stops]
    assert "Med A (Best)" in selected_names
    assert "Med C (Spaced)" in selected_names
    assert "Med B (Too close to A)" not in selected_names


def test_correct_along_route_order():
    """Selected stops must be sorted by route_fraction ascending (travel order)."""
    # Provide candidates in reverse spatial order (East to West)
    candidates = [
        CandidatePOI(name="Eastern Stop (3rd)", category="pharmacy", lat=19.0002, lng=72.8800),
        CandidatePOI(name="Central Stop (2nd)", category="pharmacy", lat=19.0001, lng=72.8500),
        CandidatePOI(name="Western Stop (1st)", category="pharmacy", lat=19.0003, lng=72.8200),
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
        max_stops=3,
        min_spacing_km=1.0,
    )
    assert result.selected_count == 3
    assert result.selected_stops[0].name == "Western Stop (1st)"
    assert result.selected_stops[1].name == "Central Stop (2nd)"
    assert result.selected_stops[2].name == "Eastern Stop (3rd)"
    assert (
        result.selected_stops[0].route_fraction
        < result.selected_stops[1].route_fraction
        < result.selected_stops[2].route_fraction
    )


def test_deterministic_tie_breaking():
    """Identical detour cost candidates are broken deterministically by off-route dist, fraction, id."""
    cand1 = {"id": 10, "name": "Pharmacy Beta", "category": "pharmacy", "lat": 19.0010, "lng": 72.8500}
    cand2 = {"id": 2, "name": "Pharmacy Alpha", "category": "pharmacy", "lat": 19.0010, "lng": 72.8500}

    # Run multiple times with shuffled inputs
    res1 = solve_route_stops(ORIGIN, DESTINATION, SYNTHETIC_ROUTE_GEOMETRY, [cand1, cand2], max_stops=1)
    res2 = solve_route_stops(ORIGIN, DESTINATION, SYNTHETIC_ROUTE_GEOMETRY, [cand2, cand1], max_stops=1)

    assert res1.selected_stops[0].id == res2.selected_stops[0].id
    assert res1.selected_stops[0].id == 2  # Lower ID wins tie-break


def test_duplicate_pois_deduplicated():
    """Identical duplicate POIs in candidate input should be deduplicated."""
    cand = CandidatePOI(name="Exact Chemist", category="pharmacy", lat=19.0010, lng=72.8500)
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=[cand, cand, cand],
        max_stops=3,
    )
    assert result.selected_count == 1
    assert result.selected_stops[0].name == "Exact Chemist"


def test_malformed_coordinates_rejected():
    """Candidates with NaN, infinity, or out-of-range coordinates are rejected gracefully."""
    candidates = [
        {"id": 1, "name": "Bad Lat", "category": "pharmacy", "lat": float("nan"), "lng": 72.85},
        {"id": 2, "name": "Inf Lng", "category": "pharmacy", "lat": 19.0, "lng": float("inf")},
        {"id": 3, "name": "Out of Range", "category": "pharmacy", "lat": 95.0, "lng": 72.85},
        {"id": 4, "name": "Good POI", "category": "pharmacy", "lat": 19.0005, "lng": 72.85},
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
    )
    assert result.selected_count == 1
    assert result.selected_stops[0].name == "Good POI"


def test_degenerate_route_handling():
    """Degenerate/empty route geometries fall back gracefully without exceptions."""
    candidates = [
        CandidatePOI(name="Midway Chemist", category="pharmacy", lat=19.0005, lng=72.8500)
    ]
    # Empty geometry should fallback to straight line between origin and destination
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=[],
        candidate_pois=candidates,
    )
    assert result.solver_status == "success"
    assert result.selected_count == 1


def test_candidate_at_origin_rejected():
    """Candidate within 50m of origin is skipped as redundant with start point."""
    candidates = [
        CandidatePOI(name="Origin Chemist", category="pharmacy", lat=19.0000, lng=72.8001),
        CandidatePOI(name="Midway Chemist", category="pharmacy", lat=19.0005, lng=72.8500),
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
    )
    assert result.selected_count == 1
    assert result.selected_stops[0].name == "Midway Chemist"


def test_candidate_at_destination_rejected():
    """Candidate within 50m of destination is skipped as redundant with endpoint."""
    candidates = [
        CandidatePOI(name="Destination Chemist", category="pharmacy", lat=19.0000, lng=72.8999),
        CandidatePOI(name="Midway Chemist", category="pharmacy", lat=19.0005, lng=72.8500),
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
    )
    assert result.selected_count == 1
    assert result.selected_stops[0].name == "Midway Chemist"


def test_total_estimated_detour_calculation():
    """Total detour must equal the sum of individual stop estimated detours."""
    candidates = [
        CandidatePOI(name="Stop A", category="pharmacy", lat=19.0010, lng=72.8300),
        CandidatePOI(name="Stop B", category="pharmacy", lat=19.0015, lng=72.8700),
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=candidates,
        max_stops=2,
    )
    assert result.selected_count == 2
    sum_individual = round(sum(s.estimated_detour_km for s in result.selected_stops), 2)
    assert result.total_estimated_detour_km == sum_individual


def test_solver_with_poi_model_instances():
    """Solver supports legacy POI model instances with id, latitude, longitude attributes."""
    pois = [
        POI(id=101, name="Database Chemist", category="pharmacy", latitude=19.0005, longitude=72.8500)
    ]
    result = solve_route_stops(
        origin=ORIGIN,
        destination=DESTINATION,
        route_geometry=SYNTHETIC_ROUTE_GEOMETRY,
        candidate_pois=pois,
    )
    assert result.solver_status == "success"
    assert result.selected_count == 1
    assert result.selected_stops[0].id == 101
    assert result.selected_stops[0].name == "Database Chemist"
