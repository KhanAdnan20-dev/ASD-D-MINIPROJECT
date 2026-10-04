# IntentWay

IntentWay is a BTech semester project exploring context-aware, multi-stop
journeys. A future version will turn natural-language tasks such as "buy
medicine" into points of interest near a journey and order those stops with a
simple, explainable routing heuristic.

## Current foundation

This repository currently provides:

- A FastAPI service with `GET /` and `GET /health`.
- Environment-based settings and basic routing request/POI models.
- A PostgreSQL/PostGIS schema with a small, synthetic Mumbai POI dataset.
- A React + Vite application shell and a placeholder for a future map.
- Docker Compose services for the frontend, backend, and database.
- Backend tests, a frontend build, and starter GitHub Actions/Jenkins pipelines.

Intent parsing, spatial filtering, route optimization, the interactive map,
monitoring checks, and deployment are planned work; they are not implemented
in this foundation.

## Requirements

- Python 3.11
- Node.js 22 or newer
- npm
- Docker Desktop or Docker Engine with the Compose plugin (for the full stack)

## Run the backend locally

From the repository root, create a local environment file and install the
backend dependencies:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Start the API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Open `http://localhost:8000/` or `http://localhost:8000/health`. The API health
check reports process availability; it deliberately does not require a
database connection.

## Run the frontend locally

In a second terminal, from the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite reads the root `.env` through its configuration. `VITE_API_BASE_URL` is
the single frontend convention for the future API base URL; the current shell
does not call the API yet.

## Run the full stack with Docker Compose

From the repository root:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

The app is available at `http://localhost:5173`, the API at
`http://localhost:8000`, and PostgreSQL is published on `localhost:5432`.
Compose initializes PostGIS and the sample POIs when it creates the database
volume for the first time. The database data persists in a named volume.

Stop the services with `docker compose down`. This preserves the database
volume. Removing that volume is destructive to locally stored database data.

## Run tests and build checks

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
Set-Location frontend
npm ci
npm run build
npm run lint
```

The backend tests do not require a running database. The database schema and
seed data are exercised by starting the Compose stack.

## Project guide

- [Architecture](docs/architecture.md) describes implemented components and
  planned routing responsibilities.
- [API contract](docs/api.md) documents the available foundation endpoints and
  the future optimization request/response shape.
- [Agile workflow](docs/agile-workflow.md) describes the proposed student
  development and CI workflow.