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


class PlanResponse(BaseModel):
    origin: GeocodedLocation
    destination: GeocodedLocation
    parsed_category: str | None
    route_geometry: list[list[float]]
    distance_km: float
    duration_mins: float
    candidate_pois: list[CandidatePOI]
    solver_status: str = "not_implemented"