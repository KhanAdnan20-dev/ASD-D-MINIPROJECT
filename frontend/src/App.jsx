import { useState } from 'react'
import './App.css'

const examplePrompts = [
  'Find a pharmacy from Wadala to Bandra',
  'Find a restaurant along my route',
  'Find a hospital near my destination',
]

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

function MapEmptyState() {
  return (
    <div className="map-empty-state">
      <span className="map-empty-state__icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" fill="none">
          <path
            d="m5 12 12-5 14 5 12-5v29l-12 5-14-5-12 5V12Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="M17 7v29m14-24v29"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="M24 15a5 5 0 0 0-5 5c0 3.4 5 8 5 8s5-4.6 5-8a5 5 0 0 0-5-5Z"
            fill="currentColor"
          />
          <circle cx="24" cy="20" r="1.6" fill="white" />
        </svg>
      </span>
      <p className="map-empty-state__eyebrow">YOUR JOURNEY, VISUALIZED</p>
      <h3>Your route will appear here</h3>
      <p>
        The interactive map will connect here when route planning is available.
      </p>
    </div>
  )
}

function App() {
  const [request, setRequest] = useState('')
  const [notice, setNotice] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    if (!request.trim()) {
      setNotice('Add a starting point, destination, and what you need along the way.')
      return
    }

    setNotice(
      'Your request is ready, but route planning is not connected yet. It has not been sent or calculated.',
    )
  }

  function chooseExample(prompt) {
    setRequest(prompt)
    setNotice('')
  }

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
            PRODUCT PREVIEW
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
            Tell IntentWay where you’re headed and what matters on the route.
          </p>
          <div className="journey-flow" aria-label="How IntentWay will work">
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

          <label className="request-label" htmlFor="journey-request">
            Describe your journey
          </label>
          <textarea
            id="journey-request"
            name="journey-request"
            rows="3"
            maxLength="300"
            placeholder="e.g. Find a pharmacy while travelling from Wadala to Bandra"
            value={request}
            onChange={(event) => {
              setRequest(event.target.value)
              if (notice) setNotice('')
            }}
            required
          />
          <p className="input-hint">
            Include where you’re starting, where you’re going, and what you need.
          </p>

          <div className="examples">
            <p className="examples__label">TRY AN EXAMPLE</p>
            <div className="example-list">
              {examplePrompts.map((prompt) => (
                <button
                  className="example-chip"
                  key={prompt}
                  onClick={() => chooseExample(prompt)}
                  type="button"
                >
                  {prompt}
                  <span aria-hidden="true">↗</span>
                </button>
              ))}
            </div>
          </div>

          <button className="submit-button" disabled={!request.trim()} type="submit">
            <span>Find my route</span>
            <span className="submit-button__arrow" aria-hidden="true">→</span>
          </button>
          {notice && (
            <p className="request-notice" role="status">
              <span aria-hidden="true">i</span>
              {notice}
            </p>
          )}
          <p className="request-footnote">
            Route planning is in development. Your request stays on this page.
          </p>
        </form>
      </section>

      <section className="workspace" aria-label="Journey preview and summary">
        <div className="map-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">THE BIG PICTURE</p>
              <h2>Journey preview</h2>
            </div>
            <span className="map-status">
              <span className="map-status__dot" />
              AWAITING ROUTE
            </span>
          </div>
          <MapEmptyState />
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
                <span className="endpoint__value">Not set</span>
              </div>
            </div>
            <span className="endpoint-connector" />
            <div className="endpoint">
              <span className="endpoint-marker endpoint-marker--end" />
              <div>
                <span className="endpoint__label">DESTINATION</span>
                <span className="endpoint__value">Not set</span>
              </div>
            </div>
          </div>

          <div className="summary-metrics">
            <div className="metric">
              <span className="metric__label">DISTANCE</span>
              <span className="metric__value">—</span>
            </div>
            <div className="metric">
              <span className="metric__label">EST. TIME</span>
              <span className="metric__value">—</span>
            </div>
          </div>

          <div className="stops-empty">
            <span className="stops-empty__icon" aria-hidden="true">＋</span>
            <div>
              <h3>Stops that make sense</h3>
              <p>Relevant places will show here once a route can be calculated.</p>
            </div>
          </div>

          <p className="summary-note">
            No route or stop results are generated in this preview.
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
