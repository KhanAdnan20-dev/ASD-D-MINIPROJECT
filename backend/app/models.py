from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Coordinate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class POI(BaseModel):
    id: int
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    intents: list[str] = Field(min_length=1)
    transport_mode: Literal["walking", "driving", "cycling"]

    @field_validator("intents")
    @classmethod
    def validate_intents(cls, intents: list[str]) -> list[str]:
        if not intents or any(not intent.strip() for intent in intents):
            raise ValueError("At least one non-empty intent is required.")
        return [intent.strip() for intent in intents]


# ---------------------------------------------------------------------------
# Route planning models (used by POST /api/route/plan)
# ---------------------------------------------------------------------------


class PlanRequest(BaseModel):
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    transport_mode: Literal["walking", "driving", "cycling"] = "driving"


class GeocodedLocation(BaseModel):
    name: str
    display_name: str
    lat: float
    lng: float


class CandidatePOI(BaseModel):
    name: str
    category: str
    lat: float
    lng: float


class SelectedPOI(BaseModel):
    id: int | str = Field(description="Unique identifier or sequence index of the POI")
    name: str
    category: str
    lat: float
    lng: float
    route_fraction: float = Field(ge=0.0, le=1.0, description="Normalized position along the route (0.0=origin, 1.0=dest)")
    distance_from_route_km: float = Field(ge=0.0, description="Perpendicular distance from the nearest point on the route in km")
    estimated_detour_km: float = Field(ge=0.0, description="Estimated round-trip detour cost (2 * distance_from_route_km)")


class SolverResult(BaseModel):
    selected_stops: list[SelectedPOI]
    total_estimated_detour_km: float = 0.0
    candidate_count: int = 0
    selected_count: int = 0
    solver_status: str = Field(description="Status of the solver: success, no_candidates, or no_feasible_stops")


class PlanResponse(BaseModel):
    origin: GeocodedLocation
    destination: GeocodedLocation
    parsed_category: str | None
    route_geometry: list[list[float]]
    distance_km: float
    duration_mins: float
    candidate_pois: list[CandidatePOI] = []
    selected_pois: list[SelectedPOI] = []
    solver_status: str = "no_candidates"
    total_estimated_detour_km: float = 0.0