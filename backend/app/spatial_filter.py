"""Build a straight route corridor and select matching POIs with PostGIS."""

import math
from decimal import Decimal
from numbers import Real

from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from app.database import get_connection
from app.models import Coordinate, POI

DEFAULT_CORRIDOR_BUFFER = 0.015
_SUPPORTED_CATEGORIES = frozenset(
    {"pharmacy", "restaurant", "hospital", "grocery"}
)


def _validate_coordinate(coordinate: Coordinate) -> None:
    if not isinstance(coordinate, Coordinate):
        raise ValueError("Origin and destination must be Coordinate values.")

    for value, minimum, maximum, name in (
        (coordinate.lat, -90, 90, "latitude"),
        (coordinate.lng, -180, 180, "longitude"),
    ):
        if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
            raise ValueError(f"Invalid {name}: {value!r}.")
        numeric_value = float(value)
        if (
            not math.isfinite(numeric_value)
            or not minimum <= numeric_value <= maximum
        ):
            raise ValueError(f"Invalid {name}: {value!r}.")


def _validate_buffer(corridor_buffer: int | float | Decimal) -> float:
    if isinstance(corridor_buffer, bool) or not isinstance(
        corridor_buffer, (Real, Decimal)
    ):
        raise ValueError("Corridor buffer must be a finite non-negative number.")

    buffer_value = float(corridor_buffer)
    if not math.isfinite(buffer_value) or buffer_value < 0:
        raise ValueError("Corridor buffer must be a finite non-negative number.")
    return buffer_value


def build_route_line(origin: Coordinate, destination: Coordinate) -> LineString:
    """Create a route LineString, using (longitude, latitude) coordinate order."""
    _validate_coordinate(origin)
    _validate_coordinate(destination)
    return LineString(
        [
            (origin.lng, origin.lat),
            (destination.lng, destination.lat),
        ]
    )


def build_corridor(
    route_line: LineString,
    corridor_buffer: int | float | Decimal = DEFAULT_CORRIDOR_BUFFER,
) -> BaseGeometry:
    """Buffer the route in degree units; a zero-length route becomes a point."""
    buffer_value = _validate_buffer(corridor_buffer)
    if not isinstance(route_line, LineString) or route_line.is_empty:
        raise ValueError("Route must be a non-empty LineString.")

    if buffer_value == 0:
        if route_line.length == 0:
            return Point(route_line.coords[0])
        return route_line

    if route_line.length == 0:
        return Point(route_line.coords[0]).buffer(buffer_value)
    return route_line.buffer(buffer_value)


def filter_pois_along_corridor(
    origin: Coordinate,
    destination: Coordinate,
    category: str,
    corridor_buffer: int | float | Decimal = DEFAULT_CORRIDOR_BUFFER,
) -> list[POI]:
    """Return database POIs of one category intersecting the route corridor.

    PostGIS ``ST_Intersects`` includes points on the corridor boundary. Database
    errors are allowed to propagate; an ordinary no-match result is an empty list.
    """
    _validate_coordinate(origin)
    _validate_coordinate(destination)
    buffer_value = _validate_buffer(corridor_buffer)
    if not isinstance(category, str) or category not in _SUPPORTED_CATEGORIES:
        raise ValueError(
            "Category must be one of: "
            + ", ".join(sorted(_SUPPORTED_CATEGORIES))
            + "."
        )

    corridor = build_corridor(
        build_route_line(origin, destination),
        buffer_value,
    )
    query = """
        SELECT id, name, category, latitude, longitude
        FROM poi
        WHERE category = %s
          AND ST_Intersects(
              location,
              ST_GeomFromText(%s, 4326)
          )
        ORDER BY id
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (category, corridor.wkt))
            rows = cursor.fetchall()

    return [
        POI(
            id=row[0],
            name=row[1],
            category=row[2],
            latitude=row[3],
            longitude=row[4],
        )
        for row in rows
    ]