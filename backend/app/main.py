import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.geocoding import geocode
from app.intent_parser import parse_intent
from app.models import (
    CandidatePOI,
    Coordinate,
    GeocodedLocation,
    PlanRequest,
    PlanResponse,
)
from app.poi_discovery import discover_pois_along_route
from app.routing import get_multi_stop_route, get_road_route
from app.solver import solve_route_stops

settings = get_settings()

app = FastAPI(
    title="IntentWay API",
    description="Foundation API for the IntentWay multi-stop routing project.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def extract_origin_destination_from_text(text: str) -> tuple[str | None, str | None]:
    """Extract origin and destination from text like 'from Wadala to Bandra'."""
    pattern = r"(?:from|starting from|start at)\s+([A-Za-z0-9\s,.-]+?)\s+(?:to|heading to|headed to)\s+([A-Za-z0-9\s,.-]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        orig = match.group(1).strip()
        dest = match.group(2).strip()
        dest = re.split(r"\s+(?:for|to get|to find|to buy)\s+", dest, flags=re.IGNORECASE)[0].strip()
        return orig, dest
    return None, None


def extract_intent_category(intent_text: str | None) -> str | None:
    """Resolve POI category using IW-2 parse_intent with graceful category keyword fallback."""
    if not intent_text:
        return None
    category = parse_intent(intent_text)
    if category:
        return category

    lower = intent_text.casefold()
    if any(k in lower for k in ("pharmacy", "chemist", "drugstore", "medical store", "medicine", "tablets", "tablet")):
        return "pharmacy"
    if any(k in lower for k in ("restaurant", "food", "cafe", "dinner", "lunch", "eat", "dining", "coffee")):
        return "restaurant"
    if any(k in lower for k in ("hospital", "clinic", "doctor", "health", "physician", "checkup", "medical")):
        return "hospital"
    if any(k in lower for k in ("grocery", "supermarket", "store", "market", "convenience")):
        return "supermarket"
    if any(k in lower for k in ("fuel", "petrol", "gas", "diesel", "gas station")):
        return "fuel"
    if any(k in lower for k in ("bank", "atm", "cash")):
        return "bank"
    return None


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "project": "IntentWay",
        "status": "foundation-ready",
        "service": "intentway-backend",
    }


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok", "service": "intentway-backend"}


@app.post("/api/route/plan")
def plan_route(request: PlanRequest) -> PlanResponse:
    """Orchestrate a full route plan.

    1. Parse intent using IW-2 intent parser (with fallback for explicit category keywords)
    2. Geocode origin and destination via Nominatim
    3. Fetch base road route via OSRM
    4. Discover real POIs via Overpass, filtered through IW-3 corridor
    5. Solve minimum-detour stops via IW-4 greedy solver
    6. Fetch FINAL multi-waypoint road route via OSRM through origin -> selected stops -> destination
    7. Return full presentation-ready response
    """
    origin_query = request.origin.strip()
    dest_query = request.destination.strip()
    intent_query = request.intent.strip()

    if " from " in intent_query.lower() and " to " in intent_query.lower():
        extracted_orig, extracted_dest = extract_origin_destination_from_text(intent_query)
        if extracted_orig and extracted_dest:
            if not origin_query or origin_query == dest_query:
                origin_query = extracted_orig
                dest_query = extracted_dest

    # ── Step 1: IW-2 intent parsing + category resolution ─────────
    category = extract_intent_category(intent_query)

    # ── Step 2: Nominatim geocoding ──────────────────────────────
    origin_geo = geocode(origin_query)
    if not origin_geo:
        raise HTTPException(
            status_code=422,
            detail=f"Could not geocode origin: '{origin_query}'",
        )

    dest_geo = geocode(dest_query)
    if not dest_geo:
        raise HTTPException(
            status_code=422,
            detail=f"Could not geocode destination: '{dest_query}'",
        )

    # ── Step 3: Base OSRM road routing ───────────────────────────
    base_road_route = get_road_route(
        origin_geo["lat"],
        origin_geo["lng"],
        dest_geo["lat"],
        dest_geo["lng"],
        request.transport_mode,
    )
    if not base_road_route:
        raise HTTPException(
            status_code=502,
            detail="Could not compute a road route via OSRM.",
        )

    # ── Step 4: Overpass + IW-3 corridor POI discovery ───────────
    candidate_pois: list[CandidatePOI] = []
    if category:
        origin_coord = Coordinate(lat=origin_geo["lat"], lng=origin_geo["lng"])
        dest_coord = Coordinate(lat=dest_geo["lat"], lng=dest_geo["lng"])
        try:
            raw_pois = discover_pois_along_route(
                origin_coord,
                dest_coord,
                category,
            )
            candidate_pois = [CandidatePOI(**poi) for poi in raw_pois]
        except Exception:
            pass  # Overpass may timeout; degrade gracefully

    # ── Step 5: IW-4 Multi-stop Route Optimization ──────────────
    solver_result = solve_route_stops(
        origin=(origin_geo["lat"], origin_geo["lng"]),
        destination=(dest_geo["lat"], dest_geo["lng"]),
        route_geometry=base_road_route["coordinates"],
        candidate_pois=candidate_pois,
    )

    # ── Step 6: Final OSRM Multi-Waypoint Road Route ─────────────
    # If the solver selected stops, route through origin -> stop1 -> stop2 -> ... -> dest
    final_road_route = base_road_route
    if solver_result.selected_stops:
        waypoints: list[tuple[float, float]] = [(origin_geo["lat"], origin_geo["lng"])]
        for stop in solver_result.selected_stops:
            waypoints.append((stop.lat, stop.lng))
        waypoints.append((dest_geo["lat"], dest_geo["lng"]))

        multi_route = get_multi_stop_route(waypoints, request.transport_mode)
        if multi_route:
            final_road_route = multi_route

    # ── Step 7: Return Response ──────────────────────────────────
    return PlanResponse(
        origin=GeocodedLocation(
            name=request.origin,
            display_name=origin_geo["display_name"],
            lat=origin_geo["lat"],
            lng=origin_geo["lng"],
        ),
        destination=GeocodedLocation(
            name=request.destination,
            display_name=dest_geo["display_name"],
            lat=dest_geo["lat"],
            lng=dest_geo["lng"],
        ),
        parsed_category=category,
        route_geometry=final_road_route["coordinates"],
        distance_km=final_road_route["distance_km"],
        duration_mins=final_road_route["duration_mins"],
        candidate_pois=candidate_pois,
        selected_pois=solver_result.selected_stops,
        solver_status=solver_result.solver_status,
        total_estimated_detour_km=solver_result.total_estimated_detour_km,
    )