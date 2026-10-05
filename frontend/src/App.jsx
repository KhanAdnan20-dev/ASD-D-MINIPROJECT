import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import './App.css'
import { API_BASE_URL } from './config'

/* ── Geometry & Math Helpers ─────────────────────────────── */

function haversineMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function calculateBearing(lat1, lon1, lat2, lon2) {
  const y = Math.sin(((lon2 - lon1) * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180)
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.cos(((lon2 - lon1) * Math.PI) / 180)
  const brng = (Math.atan2(y, x) * 180) / Math.PI
  return (brng + 360) % 360
}

/* ── Custom marker icons ──────────────────────────────────── */

function makeDotIcon(color, size = 11, borderColor = '#ffffff') {
  return L.divIcon({
    className: 'custom-marker',
    html: `<span style="
      display:block;width:${size}px;height:${size}px;
      border-radius:50%;background:${color};
      border:2px solid ${borderColor};
      box-shadow:0 2px 8px rgba(0,0,0,0.5);
    "></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  })
}

const originIcon = L.divIcon({
  className: 'custom-marker',
  html: `<div class="endpoint-pin endpoint-pin--origin">
    <span class="endpoint-pin__pulse"></span>
    <span class="endpoint-pin__core">A</span>
  </div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -14],
})

const destinationIcon = L.divIcon({
  className: 'custom-marker',
  html: `<div class="endpoint-pin endpoint-pin--dest">
    <span class="endpoint-pin__core">B</span>
  </div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -14],
})

const candidatePoiIcon = makeDotIcon('#94a3b8', 11, '#ffffff')

function makeRecommendedStopIcon(num, isApproaching = false, isArrived = false) {
  const activeClass = isArrived
    ? 'recommended-pin--arrived'
    : isApproaching
    ? 'recommended-pin--approaching'
    : ''

  return L.divIcon({
    className: 'custom-marker',
    html: `<div class="recommended-pin ${activeClass}">
      <span class="recommended-pin__badge">${num}</span>
      ${isApproaching || isArrived ? '<span class="recommended-pin__ring"></span>' : ''}
    </div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  })
}

function makeVehicleIcon(bearing = 0) {
  return L.divIcon({
    className: 'custom-marker vehicle-marker-wrapper',
    html: `<div class="vehicle-marker">
      <span class="vehicle-marker__radar"></span>
      <div class="vehicle-marker__arrow" style="transform: rotate(${Math.round(bearing)}deg)">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none">
          <path d="M12 2L20 21L12 16.5L4 21L12 2Z" fill="#10b981" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  })
}

/* ── Map Controller ───────────────────────────────────────── */

function MapViewController({ bounds, vehicleCoord, followVehicle, fitTrigger, theme }) {
  const map = useMap()

  // Invalidate size on mount, theme change, and window resize
  useEffect(() => {
    const handleResize = () => {
      map.invalidateSize()
    }
    handleResize()
    const timer = setTimeout(handleResize, 150)
    window.addEventListener('resize', handleResize)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('resize', handleResize)
    }
  }, [map, theme])

  // Fit bounds when new route arrives or user explicitly resets view
  useEffect(() => {
    if (bounds && bounds.length >= 2) {
      map.invalidateSize()
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15, animate: true })
    }
  }, [map, bounds, fitTrigger])

  // Gentle camera follow during simulation
  useEffect(() => {
    if (followVehicle && vehicleCoord) {
      map.panTo(vehicleCoord, { animate: true, duration: 0.3 })
    }
  }, [map, vehicleCoord, followVehicle])

  return null
}

/* ── Example Prompts ──────────────────────────────────────── */

const examplePrompts = [
  {
    label: 'Pharmacy: Wadala → Bandra',
    origin: 'Wadala',
    destination: 'Bandra',
    intent: 'pharmacy',
  },
  {
    label: 'Restaurant: Andheri → Dadar',
    origin: 'Andheri',
    destination: 'Dadar',
    intent: 'restaurant',
  },
  {
    label: 'Hospital: Juhu → Kurla',
    origin: 'Juhu',
    destination: 'Kurla',
    intent: 'hospital',
  },
]

/* ── Brand Mark SVG ───────────────────────────────────────── */

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none">
        <path
          d="M8 23.5 15.8 8l8.2 15.5"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="8" cy="23.5" r="3" fill="currentColor" />
        <circle cx="16" cy="8" r="3" fill="currentColor" />
        <circle cx="24" cy="23.5" r="3" fill="currentColor" />
      </svg>
    </span>
  )
}

/* ── Main Application Component ───────────────────────────── */

function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('intentway_theme')
    return saved || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('intentway_theme', theme)
  }, [theme])

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [intent, setIntent] = useState('')
  const [transportMode, setTransportMode] = useState('driving')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [fitTrigger, setFitTrigger] = useState(0)

  // Simulation state
  const [simState, setSimState] = useState('idle') // 'idle' | 'running' | 'paused' | 'completed'
  const [simProgress, setSimProgress] = useState(0) // 0.0 to 1.0
  const [simSpeed, setSimSpeed] = useState(1) // 1x, 2x, 4x
  const [followVehicle, setFollowVehicle] = useState(false)

  const mapRef = useRef(null)
  const animFrameRef = useRef(null)
  const lastTimeRef = useRef(null)

  // Parse Leaflet route coordinates: OSRM is [lng, lat] -> Leaflet [lat, lng]
  const routeLatLngs = useMemo(() => {
    if (!result || !result.route_geometry) return []
    return result.route_geometry.map(([lng, lat]) => [lat, lng])
  }, [result])

  // Precalculate cumulative distances along route
  const { cumulativeDistances, totalRouteMeters } = useMemo(() => {
    if (routeLatLngs.length < 2) {
      return { cumulativeDistances: [0], totalRouteMeters: 0 }
    }
    const cum = [0]
    let total = 0
    for (let i = 0; i < routeLatLngs.length - 1; i++) {
      const d = haversineMeters(
        routeLatLngs[i][0],
        routeLatLngs[i][1],
        routeLatLngs[i + 1][0],
        routeLatLngs[i + 1][1]
      )
      total += d
      cum.push(total)
    }
    return { cumulativeDistances: cum, totalRouteMeters: total }
  }, [routeLatLngs])

  // Project selected stops onto route to get along-route distance for arrival alerts
  const stopsWithPosition = useMemo(() => {
    if (!result || !result.selected_pois || routeLatLngs.length < 2) return []

    return result.selected_pois.map((poi, idx) => {
      let bestDist = Infinity
      let bestIdx = 0
      for (let i = 0; i < routeLatLngs.length; i++) {
        const d = haversineMeters(poi.lat, poi.lng, routeLatLngs[i][0], routeLatLngs[i][1])
        if (d < bestDist) {
          bestDist = d
          bestIdx = i
        }
      }
      const distanceAlongMeters = cumulativeDistances[bestIdx] || 0
      const fraction = totalRouteMeters > 0 ? distanceAlongMeters / totalRouteMeters : 0

      return {
        ...poi,
        stopIndex: idx,
        stopNumber: idx + 1,
        distanceAlongMeters,
        fraction,
      }
    })
  }, [result, routeLatLngs, cumulativeDistances, totalRouteMeters])

  // Compute interpolated vehicle state (position, bearing, travelled polyline)
  const vehicleState = useMemo(() => {
    if (routeLatLngs.length < 2 || simProgress <= 0) {
      if (routeLatLngs.length > 0) {
        return {
          coord: routeLatLngs[0],
          bearing:
            routeLatLngs.length > 1
              ? calculateBearing(
                  routeLatLngs[0][0],
                  routeLatLngs[0][1],
                  routeLatLngs[1][0],
                  routeLatLngs[1][1]
                )
              : 0,
          travelledLatLngs: [routeLatLngs[0]],
          segmentIndex: 0,
          distanceTravelledMeters: 0,
        }
      }
      return null
    }

    if (simProgress >= 1.0) {
      const last = routeLatLngs[routeLatLngs.length - 1]
      const prev = routeLatLngs[routeLatLngs.length - 2]
      return {
        coord: last,
        bearing: calculateBearing(prev[0], prev[1], last[0], last[1]),
        travelledLatLngs: [...routeLatLngs],
        segmentIndex: routeLatLngs.length - 2,
        distanceTravelledMeters: totalRouteMeters,
      }
    }

    const targetDist = simProgress * totalRouteMeters

    let segIdx = 0
    for (let i = 0; i < cumulativeDistances.length - 1; i++) {
      if (
        targetDist >= cumulativeDistances[i] &&
        targetDist <= cumulativeDistances[i + 1]
      ) {
        segIdx = i
        break
      }
    }

    const segStartDist = cumulativeDistances[segIdx]
    const segEndDist = cumulativeDistances[segIdx + 1]
    const segLen = segEndDist - segStartDist
    const segFraction = segLen > 0 ? (targetDist - segStartDist) / segLen : 0

    const p1 = routeLatLngs[segIdx]
    const p2 = routeLatLngs[segIdx + 1]

    const lat = p1[0] + segFraction * (p2[0] - p1[0])
    const lng = p1[1] + segFraction * (p2[1] - p1[1])
    const coord = [lat, lng]
    const bearing = calculateBearing(p1[0], p1[1], p2[0], p2[1])

    const travelled = routeLatLngs.slice(0, segIdx + 1)
    travelled.push(coord)

    return {
      coord,
      bearing,
      travelledLatLngs: travelled,
      segmentIndex: segIdx,
      distanceTravelledMeters: targetDist,
    }
  }, [routeLatLngs, simProgress, totalRouteMeters, cumulativeDistances])

  // Stop arrival and next stop status
  const { approachingStop, arrivedStop, nextStop } = useMemo(() => {
    if (!vehicleState || stopsWithPosition.length === 0) {
      return { approachingStop: null, arrivedStop: null, nextStop: null }
    }

    const currentDist = vehicleState.distanceTravelledMeters
    let approaching = null
    let arrived = null
    let next = null

    for (const stop of stopsWithPosition) {
      const delta = stop.distanceAlongMeters - currentDist

      if (delta > 50 && !next) {
        next = stop
      }

      if (Math.abs(delta) <= 85) {
        arrived = stop
      } else if (delta > 85 && delta <= 400) {
        approaching = stop
      }
    }

    return { approachingStop: approaching, arrivedStop: arrived, nextStop: next }
  }, [vehicleState, stopsWithPosition])

  // Cleanup animation on unmount
  useEffect(() => {
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
  }, [])

  // Animation frame loop for simulation
  const animate = useCallback(
    (timestamp) => {
      if (lastTimeRef.current == null) {
        lastTimeRef.current = timestamp
      }
      const deltaSec = (timestamp - lastTimeRef.current) / 1000
      lastTimeRef.current = timestamp

      const BASE_JOURNEY_SECONDS = 22
      const step = (deltaSec / BASE_JOURNEY_SECONDS) * simSpeed

      setSimProgress((prev) => {
        const nextVal = prev + step
        if (nextVal >= 1.0) {
          setSimState('completed')
          return 1.0
        }
        return nextVal
      })
    },
    [simSpeed]
  )

  useEffect(() => {
    if (simState === 'running') {
      lastTimeRef.current = null
      const loop = (timestamp) => {
        animate(timestamp)
        animFrameRef.current = requestAnimationFrame(loop)
      }
      animFrameRef.current = requestAnimationFrame(loop)
    } else {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
        animFrameRef.current = null
      }
      lastTimeRef.current = null
    }

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
  }, [simState, animate])

  /* ── Simulation Control Handlers ─────────────────────────── */

  function handleStartSimulation() {
    if (simState === 'completed' || simProgress >= 1.0) {
      setSimProgress(0)
    }
    setSimState('running')
  }

  function handlePauseSimulation() {
    setSimState('paused')
  }

  function handleResumeSimulation() {
    setSimState('running')
  }

  function handleRestartSimulation() {
    setSimProgress(0)
    setSimState('running')
  }

  function handleResetSimulation() {
    setSimProgress(0)
    setSimState('idle')
  }

  function handleResetView() {
    setFitTrigger((c) => c + 1)
  }

  /* ── Submit Handler ──────────────────────────────────────── */

  async function handleSubmit(event) {
    event.preventDefault()
    if (!origin.trim() || !destination.trim() || !intent.trim()) {
      setError('Please fill in all three fields: origin, destination, and intent.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    setSimState('idle')
    setSimProgress(0)

    try {
      const response = await fetch(`${API_BASE_URL}/api/route/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: origin.trim(),
          destination: destination.trim(),
          intent: intent.trim(),
          transport_mode: transportMode,
        }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Server error (${response.status})`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function chooseExample(example) {
    setOrigin(example.origin)
    setDestination(example.destination)
    setIntent(example.intent)
    setError('')
  }

  function formatDistance(km) {
    if (km == null) return '—'
    if (km < 1) return `${Math.round(km * 1000)} m`
    return `${km.toFixed(1)} km`
  }

  function formatDuration(mins) {
    if (mins == null) return '—'
    if (mins < 1) return '< 1 min'
    if (mins < 60) return `${Math.round(mins)} min`
    const h = Math.floor(mins / 60)
    const m = Math.round(mins % 60)
    return m > 0 ? `${h}h ${m}m` : `${h}h`
  }

  const remainingKm = result
    ? Math.max(0, result.distance_km * (1 - simProgress))
    : 0

  return (
    <div className="app-shell" data-theme={theme}>
      {/* ── Top Header ────────────────────────────────────────── */}
      <header className="site-header">
        <div className="brand-group">
          <a className="brand" href="/" aria-label="IntentWay Home">
            <BrandMark />
            <span className="brand-text">intentway</span>
          </a>
          <span className="header-tagline">Intelligent Route Planning & Multi-Stop Solver</span>
        </div>

        <div className="header-controls">
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            <span className="theme-toggle-icon">
              {theme === 'dark' ? '☀️' : '🌙'}
            </span>
            <span className="theme-toggle-label">
              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </span>
          </button>

          <span className="live-status-chip">
            <span className="live-status-chip__dot" />
            LIVE PIPELINE
          </span>
        </div>
      </header>

      {/* ── Structured Dashboard Cockpit ──────────────────────── */}
      <div className="dashboard-layout">
        {/* ── Left Column: Journey Planner & Stop Intelligence ── */}
        <aside className="planner-column">
          {/* Card 1: Route Planning Input */}
          <section className="dashboard-card planner-card">
            <div className="card-header">
              <div>
                <span className="card-kicker">STEP 01 · INTENT DISCOVERY</span>
                <h2 className="card-title">Plan Your Journey</h2>
              </div>
              <span className="card-step-badge">IW-4</span>
            </div>

            <form className="planner-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="journey-origin">
                  Starting Point (Origin)
                </label>
                <div className="input-with-icon">
                  <span className="input-dot input-dot--origin">A</span>
                  <input
                    id="journey-origin"
                    className="form-input"
                    type="text"
                    placeholder="e.g. Wadala, Mumbai"
                    value={origin}
                    onChange={(e) => {
                      setOrigin(e.target.value)
                      if (error) setError('')
                    }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="journey-destination">
                  Destination
                </label>
                <div className="input-with-icon">
                  <span className="input-dot input-dot--dest">B</span>
                  <input
                    id="journey-destination"
                    className="form-input"
                    type="text"
                    placeholder="e.g. Bandra, Mumbai"
                    value={destination}
                    onChange={(e) => {
                      setDestination(e.target.value)
                      if (error) setError('')
                    }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="journey-intent">
                  What do you need along the way?
                </label>
                <input
                  id="journey-intent"
                  className="form-input"
                  type="text"
                  placeholder="e.g. pharmacy, restaurant, hospital"
                  value={intent}
                  onChange={(e) => {
                    setIntent(e.target.value)
                    if (error) setError('')
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="journey-mode">
                  Travel Mode
                </label>
                <select
                  id="journey-mode"
                  className="form-input form-select"
                  value={transportMode}
                  onChange={(e) => setTransportMode(e.target.value)}
                >
                  <option value="driving">🚗 Driving (OSRM Road Routing)</option>
                  <option value="walking">🚶 Walking</option>
                  <option value="cycling">🚴 Cycling</option>
                </select>
              </div>

              <div className="quick-examples">
                <span className="examples-kicker">QUICK PRESETS:</span>
                <div className="example-chips-wrap">
                  {examplePrompts.map((ex, i) => (
                    <button
                      key={i}
                      type="button"
                      className="preset-chip"
                      onClick={() => chooseExample(ex)}
                    >
                      {ex.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                id="find-route-btn"
                className="btn-primary-action"
                disabled={loading || !origin.trim() || !destination.trim() || !intent.trim()}
              >
                <span>{loading ? 'Solving Route & Stops…' : 'Calculate Intent Route'}</span>
                <span className="btn-arrow" aria-hidden="true">
                  {loading ? '⟳' : '→'}
                </span>
              </button>

              {loading && (
                <div className="active-loading-bar" role="status" aria-label="Loading">
                  <div className="active-loading-bar__fill" />
                </div>
              )}

              {error && (
                <div className="alert-message alert-message--error" role="alert">
                  <span className="alert-icon">✕</span>
                  <p>{error}</p>
                </div>
              )}

              {result && result.solver_status === 'success' && result.selected_pois.length > 0 && (
                <div className="alert-message alert-message--success" role="status">
                  <span className="alert-icon">✓</span>
                  <p>
                    Greedy solver found {result.selected_pois.length} optimal stops with +
                    {result.total_estimated_detour_km} km estimated detour.
                  </p>
                </div>
              )}

              {result && result.solver_status === 'no_candidates' && (
                <div className="alert-message alert-message--info" role="status">
                  <span className="alert-icon">ℹ</span>
                  <p>Direct road route calculated. No candidate POIs were found along this corridor.</p>
                </div>
              )}
            </form>
          </section>

          {/* Card 2: Route Metrics & Summary */}
          {result && (
            <section className="dashboard-card summary-card">
              <div className="card-header">
                <div>
                  <span className="card-kicker">STEP 02 · ROUTE METRICS</span>
                  <h3 className="card-title">Journey Overview</h3>
                </div>
                <span className="category-tag">
                  {result.parsed_category || 'Direct Route'}
                </span>
              </div>

              {/* Endpoints overview */}
              <div className="endpoints-overview">
                <div className="endpoint-node">
                  <span className="node-marker node-marker--start">A</span>
                  <div className="node-details">
                    <span className="node-label">ORIGIN</span>
                    <strong className="node-name">{result.origin.name}</strong>
                  </div>
                </div>
                <div className="endpoint-divider" />
                <div className="endpoint-node">
                  <span className="node-marker node-marker--end">B</span>
                  <div className="node-details">
                    <span className="node-label">DESTINATION</span>
                    <strong className="node-name">{result.destination.name}</strong>
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="metrics-grid">
                <div className="metric-cell">
                  <span className="metric-cell__label">DISTANCE</span>
                  <span className="metric-cell__value">{formatDistance(result.distance_km)}</span>
                </div>
                <div className="metric-cell">
                  <span className="metric-cell__label">EST. TIME</span>
                  <span className="metric-cell__value">{formatDuration(result.duration_mins)}</span>
                </div>
                <div className="metric-cell">
                  <span className="metric-cell__label">CANDIDATES</span>
                  <span className="metric-cell__value">{result.candidate_pois.length}</span>
                </div>
                <div className="metric-cell">
                  <span className="metric-cell__label">DETOUR ADDED</span>
                  <span className="metric-cell__value metric-cell__value--detour">
                    +{result.total_estimated_detour_km || 0} km
                  </span>
                </div>
              </div>
            </section>
          )}

          {/* Card 3: Recommended Solver Stops */}
          {result && result.selected_pois && result.selected_pois.length > 0 && (
            <section className="dashboard-card stops-card">
              <div className="card-header">
                <div>
                  <span className="card-kicker">STEP 03 · OPTIMIZED STOPS</span>
                  <h3 className="card-title">Recommended Stops</h3>
                </div>
                <span className="stop-count-badge">{result.selected_pois.length} STOPS</span>
              </div>

              <div className="stops-sequence-list">
                {result.selected_pois.map((stop, idx) => {
                  const isApp = approachingStop && approachingStop.stopNumber === idx + 1
                  const isArr = arrivedStop && arrivedStop.stopNumber === idx + 1
                  const activeClass = isArr
                    ? 'stop-card--arrived'
                    : isApp
                    ? 'stop-card--approaching'
                    : ''

                  return (
                    <div key={idx} className={`stop-card ${activeClass}`}>
                      <div className="stop-card__index">{String(idx + 1).padStart(2, '0')}</div>
                      <div className="stop-card__content">
                        <h4 className="stop-card__name">{stop.name}</h4>
                        <div className="stop-card__meta">
                          <span className="stop-cat">{stop.category}</span>
                          <span className="stop-route-dist">
                            {Math.round(stop.distance_from_route_km * 1000)}m off-route
                          </span>
                        </div>
                      </div>
                      <div className="stop-card__detour">
                        +{stop.estimated_detour_km} km
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>
          )}
        </aside>

        {/* ── Right Column: Interactive Map & Journey Simulation Cockpit ── */}
        <main className="map-column">
          <section className="dashboard-card map-card">
            <div className="map-card-header">
              <div className="map-header-left">
                <span className="card-kicker">VISUALIZATION & SIMULATION</span>
                <h2 className="card-title">Interactive Route Map</h2>
              </div>

              <div className="map-header-right">
                {simState !== 'idle' && (
                  <span className="sim-status-pill">
                    <span className="sim-status-pill__dot" />
                    {simState === 'running'
                      ? 'SIMULATION IN PROGRESS'
                      : simState === 'paused'
                      ? 'SIMULATION PAUSED'
                      : 'JOURNEY COMPLETED'}
                  </span>
                )}
                <span className={`route-status-pill ${result ? 'route-status-pill--active' : ''}`}>
                  <span className="route-status-pill__dot" />
                  {result ? 'ROUTE READY' : 'AWAITING INPUT'}
                </span>
              </div>
            </div>

            {/* Simulation Command Toolbar */}
            {result && (
              <div className="sim-command-bar" aria-label="Journey simulation controls">
                <div className="sim-primary-controls">
                  {simState === 'idle' && (
                    <button
                      type="button"
                      id="simulate-journey-btn"
                      className="sim-cmd-btn sim-cmd-btn--play"
                      onClick={handleStartSimulation}
                    >
                      <span>▶</span>
                      <strong>Simulate Journey</strong>
                    </button>
                  )}

                  {simState === 'running' && (
                    <button
                      type="button"
                      id="pause-simulation-btn"
                      className="sim-cmd-btn sim-cmd-btn--pause"
                      onClick={handlePauseSimulation}
                    >
                      <span>⏸</span>
                      <strong>Pause</strong>
                    </button>
                  )}

                  {simState === 'paused' && (
                    <button
                      type="button"
                      id="resume-simulation-btn"
                      className="sim-cmd-btn sim-cmd-btn--play"
                      onClick={handleResumeSimulation}
                    >
                      <span>▶</span>
                      <strong>Resume</strong>
                    </button>
                  )}

                  {(simState === 'running' || simState === 'paused') && (
                    <button
                      type="button"
                      id="restart-simulation-btn"
                      className="sim-cmd-btn sim-cmd-btn--restart"
                      onClick={handleRestartSimulation}
                    >
                      <span>↻</span>
                      <span>Restart</span>
                    </button>
                  )}

                  {simState === 'completed' && (
                    <button
                      type="button"
                      id="replay-simulation-btn"
                      className="sim-cmd-btn sim-cmd-btn--play"
                      onClick={handleRestartSimulation}
                    >
                      <span>↻</span>
                      <strong>Replay Journey</strong>
                    </button>
                  )}

                  {simState !== 'idle' && (
                    <button
                      type="button"
                      className="sim-cmd-btn sim-cmd-btn--stop"
                      onClick={handleResetSimulation}
                      title="Stop simulation"
                    >
                      <span>■</span>
                      <span>Stop</span>
                    </button>
                  )}

                  <button
                    type="button"
                    id="reset-view-btn"
                    className="sim-cmd-btn sim-cmd-btn--ghost"
                    onClick={handleResetView}
                    title="Fit route bounds"
                  >
                    <span>🎯</span>
                    <span>Reset View</span>
                  </button>
                </div>

                <div className="sim-secondary-controls">
                  <label className="follow-toggle-label">
                    <input
                      type="checkbox"
                      checked={followVehicle}
                      onChange={(e) => setFollowVehicle(e.target.checked)}
                    />
                    <span>Follow Vehicle</span>
                  </label>

                  <div className="speed-pills-cluster" role="group" aria-label="Simulation Speed">
                    <span className="speed-cluster-label">Speed:</span>
                    {[1, 2, 4].map((spd) => (
                      <button
                        key={spd}
                        type="button"
                        className={`speed-select-btn ${simSpeed === spd ? 'speed-select-btn--active' : ''}`}
                        onClick={() => setSimSpeed(spd)}
                      >
                        {spd}×
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Live Progress & Stop Alert Banner */}
            {result && simState !== 'idle' && (
              <div className="sim-hud-banner">
                <div className="hud-progress-track">
                  <div
                    className="hud-progress-bar"
                    style={{ width: `${Math.round(simProgress * 100)}%` }}
                  />
                </div>

                <div className="hud-telemetry-row">
                  <div className="telemetry-item">
                    <span className="telemetry-label">PROGRESS</span>
                    <strong className="telemetry-val">{Math.round(simProgress * 100)}%</strong>
                  </div>
                  <div className="telemetry-item">
                    <span className="telemetry-label">DISTANCE REMAINING</span>
                    <strong className="telemetry-val">{formatDistance(remainingKm)}</strong>
                  </div>
                  <div className="telemetry-item telemetry-item--dest">
                    <span className="telemetry-label">TARGET POINT</span>
                    <strong className="telemetry-val telemetry-val--highlight">
                      {arrivedStop
                        ? `⭐ Arrived: ${arrivedStop.name}`
                        : approachingStop
                        ? `⚡ Approaching: ${approachingStop.name}`
                        : nextStop
                        ? `Stop ${nextStop.stopNumber}: ${nextStop.name}`
                        : `${result.destination.name}`}
                    </strong>
                  </div>
                </div>

                {/* Animated Stop Alert Toast */}
                {arrivedStop && (
                  <div className="hud-alert-toast hud-alert-toast--arrived" role="status">
                    <span className="toast-icon">📍</span>
                    <div className="toast-body">
                      <strong>Arrived at Stop #{arrivedStop.stopNumber}: {arrivedStop.name}</strong>
                      <p>{arrivedStop.category} · +{arrivedStop.estimated_detour_km} km detour added</p>
                    </div>
                  </div>
                )}

                {approachingStop && !arrivedStop && (
                  <div className="hud-alert-toast hud-alert-toast--approaching" role="status">
                    <span className="toast-icon">⚡</span>
                    <div className="toast-body">
                      <strong>Approaching Stop #{approachingStop.stopNumber}: {approachingStop.name}</strong>
                      <p>{approachingStop.category} ahead along route</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Map Canvas */}
            <div className="map-viewport-frame">
              <MapContainer
                center={[19.0760, 72.8777]}
                zoom={12}
                scrollWheelZoom
                style={{ height: '100%', width: '100%' }}
                ref={mapRef}
              >
                <TileLayer
                  key={theme}
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url={
                    theme === 'dark'
                      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
                      : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
                  }
                />

                <MapViewController
                  bounds={
                    result && routeLatLngs.length > 0
                      ? routeLatLngs
                      : result
                      ? [
                          [result.origin.lat, result.origin.lng],
                          [result.destination.lat, result.destination.lng],
                        ]
                      : null
                  }
                  vehicleCoord={vehicleState ? vehicleState.coord : null}
                  followVehicle={followVehicle && simState === 'running'}
                  fitTrigger={fitTrigger}
                  theme={theme}
                />

                {/* Full Route Polyline - High Contrast */}
                {routeLatLngs.length > 0 && (
                  <Polyline
                    positions={routeLatLngs}
                    pathOptions={{
                      color: theme === 'dark' ? '#38bdf8' : '#2563eb',
                      weight: 6,
                      opacity: 0.8,
                      lineCap: 'round',
                      lineJoin: 'round',
                    }}
                  />
                )}

                {/* Travelled Route Polyline - Neon Emerald */}
                {vehicleState && vehicleState.travelledLatLngs.length > 1 && (
                  <Polyline
                    positions={vehicleState.travelledLatLngs}
                    pathOptions={{
                      color: '#10b981',
                      weight: 6,
                      opacity: 0.95,
                      lineCap: 'round',
                      lineJoin: 'round',
                    }}
                  />
                )}

                {/* Origin Marker */}
                {result && (
                  <Marker position={[result.origin.lat, result.origin.lng]} icon={originIcon}>
                    <Popup>
                      <div className="popup-bubble">
                        <span className="popup-badge popup-badge--origin">Origin</span>
                        <h4 className="popup-title">{result.origin.name}</h4>
                        <p className="popup-sub">{result.origin.display_name}</p>
                      </div>
                    </Popup>
                  </Marker>
                )}

                {/* Destination Marker */}
                {result && (
                  <Marker position={[result.destination.lat, result.destination.lng]} icon={destinationIcon}>
                    <Popup>
                      <div className="popup-bubble">
                        <span className="popup-badge popup-badge--dest">Destination</span>
                        <h4 className="popup-title">{result.destination.name}</h4>
                        <p className="popup-sub">{result.destination.display_name}</p>
                      </div>
                    </Popup>
                  </Marker>
                )}

                {/* Candidate POIs */}
                {result &&
                  result.candidate_pois
                    .filter(
                      (poi) =>
                        !result.selected_pois.some(
                          (sel) =>
                            Math.abs(sel.lat - poi.lat) < 0.0001 &&
                            Math.abs(sel.lng - poi.lng) < 0.0001
                        )
                    )
                    .map((poi, i) => (
                      <Marker key={`cand-${i}`} position={[poi.lat, poi.lng]} icon={candidatePoiIcon}>
                        <Popup>
                          <div className="popup-bubble">
                            <span className="popup-badge popup-badge--cand">Candidate POI</span>
                            <h4 className="popup-title">{poi.name}</h4>
                            <p className="popup-sub">Category: {poi.category}</p>
                          </div>
                        </Popup>
                      </Marker>
                    ))}

                {/* Recommended Solver Stops */}
                {stopsWithPosition.map((stop) => {
                  const isApp = approachingStop && approachingStop.stopNumber === stop.stopNumber
                  const isArr = arrivedStop && arrivedStop.stopNumber === stop.stopNumber
                  const icon = makeRecommendedStopIcon(stop.stopNumber, isApp, isArr)

                  return (
                    <Marker
                      key={`sel-${stop.stopNumber}`}
                      position={[stop.lat, stop.lng]}
                      icon={icon}
                    >
                      <Popup>
                        <div className="popup-bubble">
                          <span className="popup-badge popup-badge--rec">
                            Recommended Stop #{stop.stopNumber}
                          </span>
                          <h4 className="popup-title">{stop.name}</h4>
                          <p className="popup-sub">
                            <strong>Category:</strong> {stop.category}<br />
                            <strong>Estimated Detour:</strong> +{stop.estimated_detour_km} km<br />
                            <strong>Off-Route Distance:</strong> {Math.round(stop.distance_from_route_km * 1000)} m
                          </p>
                        </div>
                      </Popup>
                    </Marker>
                  )
                })}

                {/* Simulated Vehicle */}
                {vehicleState && simState !== 'idle' && (
                  <Marker
                    position={vehicleState.coord}
                    icon={makeVehicleIcon(vehicleState.bearing)}
                    zIndexOffset={1000}
                  >
                    <Popup>
                      <div className="popup-bubble">
                        <span className="popup-badge popup-badge--vehicle">Journey Vehicle</span>
                        <h4 className="popup-title">Simulated Position</h4>
                        <p className="popup-sub">
                          Progress: {Math.round(simProgress * 100)}%<br />
                          Remaining: {formatDistance(remainingKm)}
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                )}
              </MapContainer>

              {!result && (
                <div className="map-idle-floating-chip">
                  <span>🗺️</span>
                  <span>Enter a journey on the left to plan route & simulate stops</span>
                </div>
              )}
            </div>

            {/* Map Legend */}
            <div className="map-legend-dock" aria-label="Map legend">
              <span className="legend-item">
                <i className="legend-sym legend-sym--origin" /> Origin (A)
              </span>
              <span className="legend-item">
                <i className="legend-sym legend-sym--dest" /> Destination (B)
              </span>
              <span className="legend-item">
                <i className="legend-sym legend-sym--rec" /> Recommended Stop
              </span>
              <span className="legend-item">
                <i className="legend-sym legend-sym--cand" /> Candidate POI
              </span>
              <span className="legend-item">
                <i className="legend-sym legend-sym--veh" /> Vehicle
              </span>
            </div>
          </section>
        </main>
      </div>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer className="site-footer">
        <div className="footer-left">
          <BrandMark />
          <span>intentway · Intelligent Multi-Stop Routing Engine</span>
        </div>
        <div className="footer-right">
          <span>OSRM + Nominatim + Overpass + Greedy Solver IW-4</span>
        </div>
      </footer>
    </div>
  )
}

export default App
