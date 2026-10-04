# IntentWay Agile and DevOps workflow

## Working in small increments

Develop one demonstrable feature at a time. Keep each story small enough to
review, test, and explain in a semester-project viva. Agree on acceptance
criteria before implementation and update the documentation when behavior
changes.

Suggested story progression:

1. **IW-1 — Foundation:** local services, project shell, configuration, and
   baseline checks (this phase).
2. **IW-2 — Intent parser:** deterministic keyword-to-category mapping.
3. **IW-3 — Spatial filtering:** find matching POIs near a simple route
   corridor.
4. **IW-4 — Route solver:** order stops with a simple greedy heuristic.
5. **IW-5 — Frontend wizard:** collect origin, destination, travel mode, and
   intents.
6. **IW-6 — Map and confirmation:** show candidate POIs, then display a route
   after user confirmation.

These are planned stages; only the foundation is currently implemented.

## Development workflow

```text
Jira
  ↓
User Story
  ↓
Git Branch
  ↓
Development
  ↓
Commit
  ↓
Pull Request
  ↓
GitHub
  ↓
Jenkins / CI
  ↓
Docker
  ↓
Testing
  ↓
Monitoring
```

For each story, write a short description and testable acceptance criteria.
Create a feature branch, implement and test locally, then open a pull request.
CI should run backend tests and the frontend build before the change is
accepted. Docker Compose supports local integration checks. Monitoring is a
future demonstration task; no Nagios checks are active yet.

## Branch strategy

- `main`: stable, reviewable project state.
- `develop`: integration branch for completed feature work.
- Feature branches: short-lived branches based on `develop`, merged through a
  pull request.

Example names:

- `feature/intent-parser`
- `feature/spatial-filter`
- `feature/solver`
- `feature/frontend-wizard`
- `feature/docker`
- `feature/monitoring`

Create branches manually for the relevant stories; this project setup does not
create branches automatically.

## Commit convention

Use the Jira/story key followed by a concise, present-tense change summary:

```text
IW-2 implement intent parser
IW-3 implement spatial filtering
IW-4 implement greedy route solver
```

Keep commits focused so reviewers can relate each change to a story or fix.