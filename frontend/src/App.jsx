import './App.css'

function MapPlaceholder() {
  return (
    <section className="map-placeholder" aria-label="Map preview">
      <div className="map-placeholder__content">
        <span className="map-placeholder__label">MAP PREVIEW</span>
        <p>The interactive map will appear here in a future feature.</p>
      </div>
    </section>
  )
}

function App() {
  return (
    <main className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="IntentWay home">
          IntentWay
        </a>
        <span className="header-note">A journey with purpose</span>
      </header>

      <section className="intro">
        <p className="eyebrow">CONTEXT-AWARE MULTI-STOP ROUTING</p>
        <h1>Make every stop count.</h1>
        <p className="intro__description">
          IntentWay is being built to help plan journeys around the places and
          tasks that matter to you.
        </p>
      </section>

      <MapPlaceholder />

      <footer className="site-footer">
        <span>IntentWay foundation</span>
        <span>Routing features are coming soon</span>
      </footer>
    </main>
  )
}

export default App
