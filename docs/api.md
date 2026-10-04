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

## Planned endpoint (not implemented)

### `POST /api/route/optimize`

The eventual route endpoint will receive an origin, destination, task intents,
and transport mode. Request models are present for this shape, but there is
currently no route handler, intent parsing, POI selection, or optimization.

Example request:

```json
{
  "origin": {
    "lat": 19.0556,
    "lng": 72.8295
  },
  "destination": {
    "lat": 19.0689,
    "lng": 72.8223
  },
  "intents": ["buy medicine", "eat"],
  "transport_mode": "walking"
}
```

Coordinates use latitude in `[-90, 90]` and longitude in `[-180, 180]`.
Supported transport-mode values in the request model are `walking`, `driving`,
and `cycling`. At least one non-empty intent is required.

Planned response shape:

```json
{
  "total_distance_km": 3.4,
  "estimated_duration_mins": 48,
  "optimized_sequence": [
    {"name": "Bandra Wellness Pharmacy", "category": "pharmacy"}
  ],
  "polyline_geometry": {
    "type": "LineString",
    "coordinates": [[72.8295, 19.0556], [72.8223, 19.0689]]
  }
}
```

The response values are illustrative only. Distance/time calculation, POI
selection, stop ordering, and route geometry are not implemented. A future
implementation should document its error responses and exact output fields
when that behavior is defined.

## Frontend API base URL

The frontend convention is `VITE_API_BASE_URL`, centralized in
`frontend/src/config.js`. The default local value is `http://localhost:8000`.
The current UI does not make API requests.