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