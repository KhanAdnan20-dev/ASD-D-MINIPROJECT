import pytest
from pydantic import ValidationError

from app.models import Coordinate, RouteRequest


def test_coordinate_rejects_latitude_outside_valid_range() -> None:
    with pytest.raises(ValidationError):
        Coordinate(lat=91, lng=0)


def test_route_request_strips_intent_whitespace() -> None:
    request = RouteRequest(
        origin={"lat": 19.05, "lng": 72.83},
        destination={"lat": 19.06, "lng": 72.84},
        intents=[" buy medicine "],
        transport_mode="walking",
    )

    assert request.intents == ["buy medicine"]


def test_route_request_rejects_blank_intents() -> None:
    with pytest.raises(ValidationError):
        RouteRequest(
            origin={"lat": 19.05, "lng": 72.83},
            destination={"lat": 19.06, "lng": 72.84},
            intents=["   "],
            transport_mode="walking",
        )
