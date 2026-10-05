from decimal import Decimal

import pytest
from pydantic import ValidationError
from shapely.geometry import LineString, Point

from app.models import Coordinate
from app.spatial_filter import (
    DEFAULT_CORRIDOR_BUFFER,
    build_corridor,
    build_route_line,
    filter_pois_along_corridor,
)

ORIGIN = Coordinate(lat=19.05, lng=72.82)
DESTINATION = Coordinate(lat=19.06, lng=72.84)


class FakeCursor:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.rows = rows
        self.query: str | None = None
        self.parameters: tuple[object, ...] | None = None
        self.entered = False
        self.closed = False

    def __enter__(self) -> "FakeCursor":
        self.entered = True
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.closed = True

    def execute(self, query: str, parameters: tuple[object, ...]) -> None:
        self.query = query
        self.parameters = parameters

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor
        self.entered = False
        self.closed = False

    def __enter__(self) -> "FakeConnection":
        self.entered = True
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.closed = True

    def cursor(self) -> FakeCursor:
        return self.fake_cursor


def test_route_line_uses_longitude_then_latitude() -> None:
    route = build_route_line(ORIGIN, DESTINATION)

    assert list(route.coords) == [(72.82, 19.05), (72.84, 19.06)]


def test_corridor_has_area_for_a_normal_route() -> None:
    corridor = build_corridor(build_route_line(ORIGIN, DESTINATION))

    assert corridor.area > 0
    assert DEFAULT_CORRIDOR_BUFFER == 0.015


def test_same_origin_and_destination_creates_a_point_centered_corridor() -> None:
    route = build_route_line(ORIGIN, ORIGIN)
    corridor = build_corridor(route)

    assert corridor.area > 0
    assert corridor.covers(Point(ORIGIN.lng, ORIGIN.lat))


def test_reversed_route_creates_an_equivalent_corridor() -> None:
    forward = build_corridor(build_route_line(ORIGIN, DESTINATION))
    reverse = build_corridor(build_route_line(DESTINATION, ORIGIN))

    assert forward.equals(reverse)


def test_very_short_route_creates_a_valid_corridor() -> None:
    nearby = Coordinate(lat=19.050001, lng=72.820001)

    corridor = build_corridor(build_route_line(ORIGIN, nearby))

    assert corridor.is_valid
    assert corridor.area > 0


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (float("nan"), 72.82),
        (19.05, float("inf")),
        (91, 72.82),
        (19.05, 181),
    ],
)
def test_invalid_coordinate_values_are_rejected(
    latitude: float,
    longitude: float,
) -> None:
    invalid_origin = Coordinate.model_construct(lat=latitude, lng=longitude)

    with pytest.raises(ValueError, match="Invalid"):
        build_route_line(invalid_origin, DESTINATION)


def test_coordinate_model_rejects_out_of_range_latitude() -> None:
    with pytest.raises(ValidationError):
        Coordinate(lat=91, lng=72.82)


@pytest.mark.parametrize("category", ["", "   ", "BUY MEDICINE", "unknown", None])
def test_invalid_categories_are_rejected_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
    category: str | None,
) -> None:
    def unexpected_connection() -> None:
        pytest.fail("Database should not be accessed for an invalid category.")

    monkeypatch.setattr("app.spatial_filter.get_connection", unexpected_connection)

    with pytest.raises(ValueError, match="Category"):
        filter_pois_along_corridor(ORIGIN, DESTINATION, category)  # type: ignore[arg-type]


@pytest.mark.parametrize("corridor_buffer", [-0.1, float("nan"), float("inf"), "0.01"])
def test_invalid_buffers_are_rejected(corridor_buffer: object) -> None:
    route = build_route_line(ORIGIN, DESTINATION)

    with pytest.raises(ValueError, match="buffer"):
        build_corridor(route, corridor_buffer)  # type: ignore[arg-type]


def test_decimal_buffer_is_supported() -> None:
    corridor = build_corridor(
        build_route_line(ORIGIN, DESTINATION),
        Decimal("0.01"),
    )

    assert corridor.area > 0


def test_zero_buffer_keeps_the_exact_route_geometry() -> None:
    route = build_route_line(ORIGIN, DESTINATION)

    assert build_corridor(route, 0).equals(route)


def test_corridor_includes_inside_and_boundary_points_but_not_outside_points() -> None:
    route = LineString([(72.8, 19.0), (73.0, 19.0)])
    corridor = build_corridor(route, 0.015)

    inside = Point(72.9, 19.01)
    boundary = Point(72.9, 19.015)
    outside = Point(72.9, 19.02)

    assert corridor.covers(inside)
    assert corridor.covers(boundary)
    assert not corridor.covers(outside)


@pytest.mark.parametrize(
    "category",
    ["pharmacy", "restaurant", "hospital"],
)
def test_category_is_parameterized_in_postgis_query(
    monkeypatch: pytest.MonkeyPatch,
    category: str,
) -> None:
    cursor = FakeCursor([])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(
        "app.spatial_filter.get_connection",
        lambda: connection,
    )

    result = filter_pois_along_corridor(ORIGIN, DESTINATION, category)

    assert result == []
    assert cursor.parameters is not None
    assert cursor.parameters[0] == category


def test_query_uses_spatial_predicate_and_parameterized_corridor_wkt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = FakeCursor([])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(
        "app.spatial_filter.get_connection",
        lambda: connection,
    )

    filter_pois_along_corridor(ORIGIN, DESTINATION, "pharmacy")

    assert cursor.query is not None
    assert "FROM poi" in cursor.query
    assert "ST_Intersects" in cursor.query
    assert "ST_GeomFromText(%s, 4326)" in cursor.query
    assert "category = %s" in cursor.query
    assert "ORDER BY id" in cursor.query
    assert cursor.parameters is not None
    assert len(cursor.parameters) == 2
    assert cursor.parameters[0] == "pharmacy"
    assert isinstance(cursor.parameters[1], str)
    assert cursor.parameters[1].startswith("POLYGON")


def test_database_rows_map_to_poi_models_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = FakeCursor(
        [
            (2, "Second Pharmacy", "pharmacy", 19.06, 72.83),
            (5, "Fifth Pharmacy", "pharmacy", 19.055, 72.825),
        ]
    )
    monkeypatch.setattr(
        "app.spatial_filter.get_connection",
        lambda: FakeConnection(cursor),
    )

    pois = filter_pois_along_corridor(ORIGIN, DESTINATION, "pharmacy")

    assert [poi.id for poi in pois] == [2, 5]
    assert pois[0].model_dump() == {
        "id": 2,
        "name": "Second Pharmacy",
        "category": "pharmacy",
        "latitude": 19.06,
        "longitude": 72.83,
    }


def test_connection_and_cursor_are_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = FakeCursor([])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(
        "app.spatial_filter.get_connection",
        lambda: connection,
    )

    filter_pois_along_corridor(ORIGIN, DESTINATION, "pharmacy")

    assert connection.entered
    assert connection.closed
    assert cursor.entered
    assert cursor.closed


def test_database_errors_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_connect() -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.spatial_filter.get_connection", fail_to_connect)

    with pytest.raises(RuntimeError, match="database unavailable"):
        filter_pois_along_corridor(ORIGIN, DESTINATION, "pharmacy")