from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint_describes_the_project() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "project": "IntentWay",
        "status": "foundation-ready",
        "service": "intentway-backend",
    }


def test_health_endpoint_reports_process_availability() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "intentway-backend"}


def test_plan_route_endpoint_success_with_solver():
    """Test full /api/route/plan endpoint flow with mocked external APIs."""
    mock_origin_geo = {
        "lat": 19.0269,
        "lng": 72.8759,
        "display_name": "Wadala, Mumbai",
    }
    mock_dest_geo = {
        "lat": 19.0549,
        "lng": 72.8402,
        "display_name": "Bandra, Mumbai",
    }
    mock_route = {
        "coordinates": [
            [72.8759, 19.0269],
            [72.8580, 19.0400],
            [72.8402, 19.0549],
        ],
        "distance_km": 8.96,
        "duration_mins": 10.6,
    }
    mock_pois = [
        {"name": "Noble Plus", "category": "pharmacy", "lat": 19.0401, "lng": 72.8581},
        {"name": "Far Away Chemist", "category": "pharmacy", "lat": 19.2000, "lng": 72.8580},
    ]

    def mock_geocode(name: str):
        if "wadala" in name.lower():
            return mock_origin_geo
        return mock_dest_geo

    with (
        patch("app.main.geocode", side_effect=mock_geocode),
        patch("app.main.get_road_route", return_value=mock_route),
        patch("app.main.discover_pois_along_route", return_value=mock_pois),
    ):
        response = client.post(
            "/api/route/plan",
            json={
                "origin": "Wadala",
                "destination": "Bandra",
                "intent": "Find a pharmacy from Wadala to Bandra",
                "transport_mode": "driving",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["origin"]["name"] == "Wadala"
        assert data["destination"]["name"] == "Bandra"
        assert data["parsed_category"] == "pharmacy"
        assert data["distance_km"] == 8.96
        assert data["duration_mins"] == 10.6
        assert len(data["route_geometry"]) == 3
        assert len(data["candidate_pois"]) == 2
        assert data["solver_status"] == "success"
        assert len(data["selected_pois"]) == 1
        assert data["selected_pois"][0]["name"] == "Noble Plus"
        assert data["selected_pois"][0]["estimated_detour_km"] >= 0.0
        assert data["total_estimated_detour_km"] >= 0.0


def test_plan_route_endpoint_no_candidates():
    """Test /api/route/plan when Overpass finds no matching candidate POIs."""
    mock_origin_geo = {"lat": 19.0269, "lng": 72.8759, "display_name": "Wadala, Mumbai"}
    mock_dest_geo = {"lat": 19.0549, "lng": 72.8402, "display_name": "Bandra, Mumbai"}
    mock_route = {
        "coordinates": [[72.8759, 19.0269], [72.8402, 19.0549]],
        "distance_km": 5.0,
        "duration_mins": 8.0,
    }

    with (
        patch("app.main.geocode", return_value=mock_origin_geo),
        patch("app.main.get_road_route", return_value=mock_route),
        patch("app.main.discover_pois_along_route", return_value=[]),
    ):
        response = client.post(
            "/api/route/plan",
            json={
                "origin": "Wadala",
                "destination": "Bandra",
                "intent": "buy medicine",
                "transport_mode": "driving",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["candidate_pois"] == []
        assert data["selected_pois"] == []
        assert data["solver_status"] == "no_candidates"
        assert data["total_estimated_detour_km"] == 0.0


def test_plan_route_endpoint_geocoding_failure():
    """Test /api/route/plan when origin cannot be geocoded."""
    with patch("app.main.geocode", return_value=None):
        response = client.post(
            "/api/route/plan",
            json={
                "origin": "NonExistentPlaceXYZ123",
                "destination": "Bandra",
                "intent": "buy medicine",
            },
        )
        assert response.status_code == 422
        assert "Could not geocode origin" in response.json()["detail"]