# IntentWay API contract

Base URL for local development: `http://localhost:8000`

The API uses JSON. The current foundation endpoints are implemented; the
multi-stop route endpoint below is a future contract only.

## Implemented endpoints

### `GET /`

Returns basic project/service information.

```json
{
  "project": "IntentWay",
  "status": "foundation-ready",
  "service": "intentway-backend"
}
```

### `GET /health`

Reports that the API process is responding. This endpoint intentionally does
not depend on PostgreSQL or the future routing features.

```json
{
  "status": "ok",
  "service": "intentway-backend"
}
```

### `POST /api/route/plan`

Orchestrates full multi-stop route planning:
1. Intent Parsing (IW-2)
2. Nominatim Geocoding
3. OSRM Road Routing
4. Overpass + IW-3 Spatial Corridor POI Discovery
5. IW-4 Deterministic Greedy Solver

Request payload:
```json
{
  "origin": "Wadala",
  "destination": "Bandra",
  "intent": "Find a pharmacy from Wadala to Bandra",
  "transport_mode": "driving"
}
```

Response payload:
```json
{
  "origin": {
    "name": "Wadala",
    "display_name": "Wadala, Mumbai...",
    "lat": 19.0269,
    "lng": 72.8759
  },
  "destination": {
    "name": "Bandra",
    "display_name": "Bandra, Mumbai...",
    "lat": 19.0549,
    "lng": 72.8402
  },
  "parsed_category": "pharmacy",
  "distance_km": 8.96,
  "duration_mins": 10.6,
  "route_geometry": [[72.8759, 19.0269], "..."],
  "candidate_pois": [
    {"name": "Noble Plus", "category": "pharmacy", "lat": 19.0401, "lng": 72.8581}
  ],
  "selected_pois": [
    {
      "id": 1,
      "name": "Utility Chemists",
      "category": "pharmacy",
      "lat": 19.0350,
      "lng": 72.8594,
      "route_fraction": 0.3837,
      "distance_from_route_km": 0.02,
      "estimated_detour_km": 0.04
    }
  ],
  "solver_status": "success",
  "total_estimated_detour_km": 1.77
}
```

## Frontend API base URL

The frontend convention is `VITE_API_BASE_URL`, centralized in
`frontend/src/config.js`. The default local value is `http://localhost:8000`.
The current UI does not make API requests.