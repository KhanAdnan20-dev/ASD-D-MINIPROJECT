import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import './App.css'
import { API_BASE_URL } from './config'

/* ── Custom marker icons ──────────────────────────────────── */

function makeIcon(color, size = 12) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<span style="
      display:block;width:${size}px;height:${size}px;
      border-radius:50%;background:${color};
      border:2.5px solid #fff;
      box-shadow:0 1px 6px rgba(0,0,0,.3);
    "></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  })
}

const originIcon = makeIcon('#508568', 14)
const destinationIcon = makeIcon('#637f9b', 14)
const poiIcon = makeIcon('#d39b4a', 11)

/* ── Map auto-fit ─────────────────────────────────────────── */

function FitBounds({ bounds }) {
  const map = useMap()
  useEffect(() => {
    if (bounds && bounds.length >= 2) {
      map.fitBounds(bounds, { padding: [45, 45], maxZoom: 15 })
    }
  }, [map, bounds])
  return null
}

/* ── Example prompts (pre-fill structured fields) ─────────── */

const examplePrompts = [
  {
    label: 'Find a pharmacy from Wadala to Bandra',
    origin: 'Wadala',
    destination: 'Bandra',
    intent: 'pharmacy',
  },
  {
    label: 'Find a restaurant from Andheri to Dadar',
    origin: 'Andheri',
    destination: 'Dadar',
    intent: 'restaurant',
  },
  {
    label: 'Find a hospital from Juhu to Kurla',
    origin: 'Juhu',
    destination: 'Kurla',
    intent: 'hospital',
  },
]

/* ── Brand mark SVG ───────────────────────────────────────── */

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

/* ── Map empty state ──────────────────────────────────────── */

/* ── Main application ─────────────────────────────────────── */

function App() {
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [intent, setIntent] = useState('')
  const [transportMode, setTransportMode] = useState('driving')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const mapRef = useRef(null)

  /* ── Submit handler ──────────────────────────────────────── */

  async function handleSubmit(event) {
    event.preventDefault()
    if (!origin.trim() || !destination.trim() || !intent.trim()) {
      setError('Please fill in all three fields: origin, destination, and what you need.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

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

  /* ── Example prompt handler ──────────────────────────────── */

  function chooseExample(example) {
    setOrigin(example.origin)
    setDestination(example.destination)
    setIntent(example.intent)
    setError('')
  }

  /* ── Compute Leaflet data from result ────────────────────── */

  const routeLatLngs = result
    ? result.route_geometry.map(([lng, lat]) => [lat, lng])
    : []

  /* ── Format helpers ──────────────────────────────────────── */

  function formatDistance(km) {
    if (km < 1) return `${Math.round(km * 1000)} m`
    return `${km.toFixed(1)} km`
  }

  function formatDuration(mins) {
    if (mins < 1) return '< 1 min'
    if (mins < 60) return `${Math.round(mins)} min`
    const h = Math.floor(mins / 60)
    const m = Math.round(mins % 60)
    return m > 0 ? `${h} h ${m} min` : `${h} h`
  }

  /* ── Render ──────────────────────────────────────────────── */

  return (
    <main className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="IntentWay home">
          <BrandMark />
          <span>intentway</span>
        </a>
        <div className="header-meta">
          <span className="header-subtitle">Intelligent Route Planning</span>
          <span className="preview-badge">
            <span className="preview-badge__dot" />
            LIVE DEMO
          </span>
        </div>
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="eyebrow__line" />
            A MORE INTENTIONAL WAY TO GO
          </p>
          <h1 id="hero-title">
            Your city,
            <br />
            <span>with purpose.</span>
          </h1>
          <p className="hero-description">
            Plan your journey naturally and find useful places along the way.
            Tell IntentWay where you&apos;re headed and what matters on the route.
          </p>
          <div className="journey-flow" aria-label="How IntentWay works">
            <span>Natural language</span>
            <span className="journey-flow__arrow" aria-hidden="true">→</span>
            <span>Useful places</span>
            <span className="journey-flow__arrow" aria-hidden="true">→</span>
            <span>Your route</span>
          </div>
        </div>

        <form className="request-card" onSubmit={handleSubmit}>
          <div className="request-card__heading">
            <div>
              <p className="request-card__step">PLAN A JOURNEY</p>
              <h2>Where can we take you?</h2>
            </div>
            <span className="request-card__number" aria-hidden="true">01</span>
          </div>

          <label className="request-label" htmlFor="journey-origin">
            Starting point
          </label>
          <input
            id="journey-origin"
            className="request-input"
            type="text"
            placeholder="e.g. Wadala, Mumbai"
            value={origin}
            onChange={(e) => { setOrigin(e.target.value); if (error) setError('') }}
            required
          />

          <label className="request-label" htmlFor="journey-destination">
            Destination
          </label>
          <input
            id="journey-destination"
            className="request-input"
            type="text"
            placeholder="e.g. Bandra, Mumbai"
            value={destination}
            onChange={(e) => { setDestination(e.target.value); if (error) setError('') }}
            required
          />

          <label className="request-label" htmlFor="journey-intent">
            What do you need along the way?
          </label>
          <input
            id="journey-intent"
            className="request-input"
            type="text"
            placeholder="e.g. buy medicine, eat food, visit hospital"
            value={intent}
            onChange={(e) => { setIntent(e.target.value); if (error) setError('') }}
            required
          />

          <label className="request-label" htmlFor="journey-mode">
            Travel mode
          </label>
          <select
            id="journey-mode"
            className="request-input request-select"
            value={transportMode}
            onChange={(e) => setTransportMode(e.target.value)}
          >
            <option value="driving">Driving</option>
            <option value="walking">Walking</option>
            <option value="cycling">Cycling</option>
          </select>

          <p className="input-hint">
            Enter real places — they are geocoded via OpenStreetMap.
          </p>

          <div className="examples">
            <p className="examples__label">TRY AN EXAMPLE</p>
            <div className="example-list">
              {examplePrompts.map((ex, i) => (
                <button
                  className="example-chip"
                  key={i}
                  onClick={() => chooseExample(ex)}
                  type="button"
                >
                  {ex.label}
                  <span aria-hidden="true">↗</span>
                </button>
              ))}
            </div>
          </div>

          <button
            className="submit-button"
            disabled={loading || !origin.trim() || !destination.trim() || !intent.trim()}
            type="submit"
          >
            <span>{loading ? 'Planning route…' : 'Find my route'}</span>
            <span className="submit-button__arrow" aria-hidden="true">
              {loading ? '' : '→'}
            </span>
          </button>

          {loading && (
            <div className="loading-bar" role="status" aria-label="Loading">
              <div className="loading-bar__track" />
            </div>
          )}

          {error && (
            <p className="request-notice request-notice--error" role="alert">
              <span aria-hidden="true">✕</span>
              {error}
            </p>
          )}

          {result && !result.parsed_category && (
            <p className="request-notice" role="status">
              <span aria-hidden="true">i</span>
              Could not match your intent to a known category. The route is
              shown without POI stops. Try: &quot;buy medicine&quot;, &quot;eat food&quot;, or
              &quot;visit hospital&quot;.
            </p>
          )}

          {result && result.solver_status === 'not_implemented' && result.candidate_pois.length > 0 && (
            <p className="request-notice request-notice--info" role="status">
              <span aria-hidden="true">i</span>
              {result.candidate_pois.length} candidate{' '}
              {result.candidate_pois.length === 1 ? 'place' : 'places'} found
              along your route. Stop optimization (IW-4) is not yet connected.
            </p>
          )}
        </form>
      </section>

      <section className="workspace" aria-label="Journey preview and summary">
        <div className="map-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">THE BIG PICTURE</p>
              <h2>Journey preview</h2>
            </div>
            <span className={`map-status ${result ? 'map-status--live' : ''}`}>
              <span className="map-status__dot" />
              {result ? 'ROUTE LOADED' : 'AWAITING ROUTE'}
            </span>
          </div>

          <div className="map-container-wrapper">
            <MapContainer
              center={[19.0760, 72.8777]}
              zoom={12}
              scrollWheelZoom
              style={{ height: '100%', width: '100%', borderRadius: '8px' }}
              ref={mapRef}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {result && (
                <FitBounds
                  bounds={
                    routeLatLngs.length > 0
                      ? routeLatLngs
                      : [
                          [result.origin.lat, result.origin.lng],
                          [result.destination.lat, result.destination.lng],
                        ]
                  }
                />
              )}

              {/* Route polyline */}
              {routeLatLngs.length > 0 && (
                <Polyline
                  positions={routeLatLngs}
                  pathOptions={{
                    color: '#287a58',
                    weight: 5,
                    opacity: 0.85,
                    lineCap: 'round',
                    lineJoin: 'round',
                  }}
                />
              )}

              {/* Origin marker */}
              {result && (
                <Marker position={[result.origin.lat, result.origin.lng]} icon={originIcon}>
                  <Popup>
                    <strong>Origin: {result.origin.name}</strong><br />{result.origin.display_name}
                  </Popup>
                </Marker>
              )}

              {/* Destination marker */}
              {result && (
                <Marker position={[result.destination.lat, result.destination.lng]} icon={destinationIcon}>
                  <Popup>
                    <strong>Destination: {result.destination.name}</strong><br />{result.destination.display_name}
                  </Popup>
                </Marker>
              )}

              {/* POI markers */}
              {result && result.candidate_pois.map((poi, i) => (
                <Marker key={i} position={[poi.lat, poi.lng]} icon={poiIcon}>
                  <Popup>
                    <strong>{poi.name}</strong><br />
                    <em>{poi.category}</em>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
            {!result && (
              <div className="map-overlay-hint">
                <p>Interactive Map Active · Enter journey details or click an example above</p>
              </div>
            )}
          </div>

          <div className="map-legend" aria-label="Map legend">
            <span><i className="legend-dot legend-dot--origin" /> Starting point</span>
            <span><i className="legend-dot legend-dot--stop" /> Places along the way</span>
            <span><i className="legend-dot legend-dot--destination" /> Destination</span>
          </div>
        </div>

        <aside className="summary-panel" aria-labelledby="summary-title">
          <div className="panel-heading panel-heading--summary">
            <div>
              <p className="section-kicker">AT A GLANCE</p>
              <h2 id="summary-title">Route summary</h2>
            </div>
            <span className="summary-icon" aria-hidden="true">↗</span>
          </div>

          <div className="route-endpoints">
            <div className="endpoint">
              <span className="endpoint-marker endpoint-marker--start" />
              <div>
                <span className="endpoint__label">ORIGIN</span>
                <span className="endpoint__value">
                  {result ? result.origin.name : 'Not set'}
                </span>
              </div>
            </div>
            <span className="endpoint-connector" />
            <div className="endpoint">
              <span className="endpoint-marker endpoint-marker--end" />
              <div>
                <span className="endpoint__label">DESTINATION</span>
                <span className="endpoint__value">
                  {result ? result.destination.name : 'Not set'}
                </span>
              </div>
            </div>
          </div>

          <div className="summary-metrics">
            <div className="metric">
              <span className="metric__label">DISTANCE</span>
              <span className="metric__value">
                {result ? formatDistance(result.distance_km) : '—'}
              </span>
            </div>
            <div className="metric">
              <span className="metric__label">EST. TIME</span>
              <span className="metric__value">
                {result ? formatDuration(result.duration_mins) : '—'}
              </span>
            </div>
          </div>

          {result && result.candidate_pois.length > 0 ? (
            <div className="stops-list">
              <div className="stops-list__header">
                <span className="stops-list__icon" aria-hidden="true">◆</span>
                <div>
                  <h3>
                    {result.candidate_pois.length} candidate{' '}
                    {result.candidate_pois.length === 1 ? 'place' : 'places'}
                  </h3>
                  <p className="stops-list__note">
                    Along your route · {result.parsed_category}
                  </p>
                </div>
              </div>
              <ul className="poi-list">
                {result.candidate_pois.map((poi, i) => (
                  <li key={i} className="poi-item">
                    <span className="poi-item__dot" />
                    <div>
                      <span className="poi-item__name">{poi.name}</span>
                      <span className="poi-item__category">{poi.category}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="stops-empty">
              <span className="stops-empty__icon" aria-hidden="true">＋</span>
              <div>
                <h3>Stops that make sense</h3>
                <p>
                  {result
                    ? 'No matching places were found along this route.'
                    : 'Relevant places will show here once a route is planned.'}
                </p>
              </div>
            </div>
          )}

          <p className="summary-note">
            {result
              ? 'Candidates shown are not optimized. Stop ordering (IW-4) is pending.'
              : 'Plan a route to see real distance, time, and nearby places.'}
          </p>
        </aside>
      </section>

      <footer className="site-footer">
        <a className="footer-brand" href="/" aria-label="IntentWay home">
          <BrandMark />
          <span>intentway</span>
        </a>
        <span>Intelligent Route Planning</span>
        <span className="footer-location">BUILT FOR THE JOURNEY AHEAD</span>
      </footer>
    </main>
  )
}

export default App
