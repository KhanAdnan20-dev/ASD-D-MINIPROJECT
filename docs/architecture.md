# IntentWay architecture

## Purpose

IntentWay is a small, explainable project for planning a journey that can
include useful stops. The intended implementation uses a React interface, a
FastAPI service, and PostgreSQL with PostGIS for points of interest (POIs).

## Current foundation

The foundation currently includes:

- **Frontend:** React + Vite application shell, IntentWay branding, and an
  explicitly labelled placeholder where a future Leaflet map can go.
- **API:** FastAPI application with `GET /` and `GET /health`, local-origin
  CORS settings, and basic coordinate, POI, and route request models.
- **Configuration/database access:** Pydantic Settings reads database
  connection values from environment variables. `database.py` provides a
  small psycopg connection function; no API endpoint queries the database yet.
- **Database:** Compose uses PostgreSQL with PostGIS. Its initialization SQL
  enables the extension, creates a spatially indexed POI table, and inserts
  synthetic demonstration data around Bandra, Mumbai.
- **Development/quality:** Docker Compose, independent API/model tests, a
  GitHub Actions test/build workflow, and simple Jenkins pipeline examples.

The health endpoint checks that the API process responds. It does not check
database availability.

## Planned request flow

```text
React frontend
      |
      | JSON over HTTP
      v
FastAPI API
      |
      +--> Intent processing (planned)
      |
      +--> Spatial candidate filtering (planned)
      |       Shapely and PostGIS
      |
      +--> Route optimization (planned)
      |       deterministic greedy heuristic
      |
      +--> PostgreSQL + PostGIS POI data
      |
      v
Leaflet map display (planned)
```

The diagram describes the target flow, not fully implemented behavior. The
current API exposes no routing endpoint and the UI does not call the backend.

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| React + Vite | Present the user interface. The current shell is a placeholder; a future wizard and map will live here. |
| FastAPI | Validate requests and expose JSON endpoints. Only root and health endpoints are implemented so far. |
| Intent parser | Planned module to map simple task phrases to POI categories. |
| Spatial layer | Planned use of PostGIS and Shapely to find candidate POIs near a route corridor. |
| Solver | Planned deterministic, greedy ordering of candidate stops; no optimizer is implemented yet. |
| PostgreSQL + PostGIS | Store POI attributes and WGS 84 point geometry (SRID 4326). |
| Docker Compose | Run the frontend, backend, and database together for local development. |
| Jenkins / GitHub Actions | Demonstrate automated tests and a frontend build. Deployment is not configured. |
| Nagios | Reserved project directory for a later service-availability monitoring exercise. No checks are configured. |

## Data and configuration

The POI table stores a name, category, latitude, longitude, and PostGIS point.
The geometry index prepares for future spatial searches; no corridor query is
implemented. Database credentials and local ports are configured through
environment variables. `.env.example` contains safe development values and
must not be used to store real credentials.

## Local service boundaries

Compose places the three services on a project network. Only their development
ports are published to the local machine. The PostgreSQL data directory is
stored in a named volume and survives a normal `docker compose down`.