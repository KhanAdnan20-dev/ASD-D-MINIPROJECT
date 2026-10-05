# IntentWay IW-4 — Deterministic Greedy Multi-Stop Route Solver

## 1. Objective and Problem Definition

The IntentWay solver (IW-4) solves the problem of selecting and ordering intermediate stops (Points of Interest) along a journey from an origin to a destination while minimizing user detour.

Given:
- **Origin & Destination** GPS coordinates $(lat, lng)$
- **OSRM Road Route Geometry** represented as a sequence of coordinates $[(lng_1, lat_1), (lng_2, lat_2), \dots]$
- **Candidate POIs** discovered along the spatial route corridor
- **Solver Constraints**:
  - `max_stops` (default: 3)
  - `max_detour_km` (default: 2.0 km)
  - `min_spacing_km` (default: 1.0 km)

The solver selects up to `max_stops` feasible candidates that minimize the round-trip detour cost and orders them in ascending along-route travel sequence.

---

## 2. Algorithmic Design

The solver employs a **computational geometry + greedy discrete optimization heuristic**:

```text
OSRM Route Geometry (GeoJSON [lng, lat])
               │
               ▼
  Shapely LineString Construction
               │
               ▼
   Linear Route Projection (route.project)
   ├── Along-route position & fraction (0.0 = origin, 1.0 = destination)
   └── Nearest point on route (route.interpolate)
               │
               ▼
   Haversine Distance & Detour Estimation
   ├── Lateral Distance (distance_from_route_km)
   └── Estimated Detour (estimated_detour_km = 2 * distance_from_route_km)
               │
               ▼
   Candidate Feasibility Filtering
   ├── Reject coordinates exceeding max_detour_km (> 2.0 km)
   ├── Reject malformed / NaN / out-of-range coordinates
   ├── Deduplicate identical POIs
   └── Exclude points at origin/destination (< 50m)
               │
               ▼
   Deterministic Greedy Selection
   ├── Enforce min_spacing_km constraint (>= 1.0 km between selected stops)
   ├── Pick candidate minimizing detour cost
   └── Stable tie-breaking: detour → off-route dist → route fraction → POI ID
               │
               ▼
   Along-Route Ordering
   └── Sort selected stops by route_fraction ASCENDING
```

---

## 3. Detour Estimation Rationale

- **Estimated Detour Formula**:
  $$\text{estimated\_detour\_km} = 2 \times \text{distance\_from\_route\_km}$$
- **Rationale**: A user deviating from their main road route to visit a point of interest and then returning to the route travels approximately twice the perpendicular off-route distance.
- **Note**: This is an explainable heuristic estimate rather than an exact graph traversal detour, keeping execution fast, deterministic, and lightweight without issuing redundant routing API requests.

---

## 4. Deterministic Tie-Breaking

To guarantee that identical inputs always yield identical outputs, candidates with equal estimated detour are evaluated using a strict lexicographical tie-break tuple:
1. `estimated_detour_km` (ascending)
2. `distance_from_route_km` (ascending)
3. `route_fraction` (ascending)
4. `_poi_sort_id(poi.id)` (numeric ascending, then string ascending)
5. `poi.name` (alphabetical ascending)

---

## 5. Computational Complexity

- **Route Projection**: $O(m)$ per candidate, where $m$ is the number of route polyline vertices. For $n$ candidates, initial projection and filtering takes $O(n \cdot m)$.
- **Greedy Selection**: At each iteration, $O(n)$ unselected candidates are evaluated against up to $k$ selected stops ($k \le \text{max\_stops}$). For $k$ selections, this takes $O(k \cdot n)$.
- **Sorting**: Sorting the $k$ selected stops takes $O(k \log k)$.
- **Overall Time Complexity**: $O(n \cdot m + k \cdot n)$ where $n$ is candidate count, $m$ is route vertex count, and $k$ is maximum stops.

---

## 6. Viva / Academic Explanation

> *"In IW-4, the actual road route from OSRM is converted into a linear geometric polyline. Each candidate POI discovered in the spatial corridor is projected onto the route using linear referencing to obtain its normalized journey position and perpendicular off-route distance. We approximate detour cost as twice the off-route distance. Candidates exceeding the maximum detour threshold are filtered out. A deterministic greedy heuristic repeatedly selects the lowest-detour candidate that satisfies minimum spacing constraints. Finally, selected stops are sorted in ascending route order from origin to destination."*
