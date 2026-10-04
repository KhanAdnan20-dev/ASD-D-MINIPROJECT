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