import { useEffect, useMemo, useState } from 'react'
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const TRAVEL_MODES = [
  'driving',
  'public_transport',
  'walking',
  'cycling',
  'flight',
  'best_available',
]

const defaultForm = {
  start: 'Bangalore',
  destination: 'Mysore',
  days: 2,
  budget: 10000,
  travelers: 2,
  travel_style: 'standard',
  travel_mode: 'driving',
  currency: 'INR',
  preferences: 'nature, food, heritage sites, relaxed scenic route',
}

const formatInr = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))

function parseRoutePayload(routeData, mode = 'driving') {
  if (!routeData) {
    return {
      route: null,
      places: [],
      enRoutePlaces: [],
      destinationPlaces: [],
      directions: [],
      routeBudget: null,
      error: 'Route map data is currently unavailable for this trip.',
      startPoint: null,
      destinationPoint: null,
      routeType: 'unavailable',
    }
  }

  const startPoint = routeData.start
    ? {
        name: routeData.start.name,
        coordinates: [Number(routeData.start.latitude), Number(routeData.start.longitude)],
      }
    : null

  const destinationPoint = routeData.destination
    ? {
        name: routeData.destination.name,
        coordinates: [Number(routeData.destination.latitude), Number(routeData.destination.longitude)],
      }
    : null

  const geometry = Array.isArray(routeData.geometry)
    ? routeData.geometry.map(([lat, lon]) => [Number(lat), Number(lon)])
    : []

  const enRoutePlaces = (routeData.en_route_places || []).map((place, index) => ({
    id: place.id || `enroute-${place.name}-${index}`,
    name: place.name,
    category: place.category || 'Scenic Stop',
    description: place.description || 'Famous place to visit along the route.',
    coordinates: Array.isArray(place.coordinates) ? [Number(place.coordinates[0]), Number(place.coordinates[1])] : [0, 0],
    location: place.location || 'Between route',
    isEnRoute: true,
  }))

  const destinationPlaces = (routeData.destination_places || []).map((place, index) => ({
    id: place.id || `dest-${place.name}-${index}`,
    name: place.name,
    category: place.category || 'Destination Highlight',
    description: place.description || 'Must-visit place in destination.',
    coordinates: Array.isArray(place.coordinates) ? [Number(place.coordinates[0]), Number(place.coordinates[1])] : [0, 0],
    location: place.location || 'Destination area',
    isEnRoute: false,
  }))

  const allStops = [...enRoutePlaces, ...destinationPlaces]
  const directions = Array.isArray(routeData.directions) ? routeData.directions : []
  const routeBudget = routeData.route_budget || null

  return {
    route:
      geometry.length > 0
        ? {
            coordinates: geometry,
            distanceKm: routeData.distance_km,
            durationMinutes: routeData.duration_minutes,
            profile: routeData.mode || mode,
            mode: routeData.mode || mode,
          }
        : null,
    places: allStops,
    enRoutePlaces,
    destinationPlaces,
    directions,
    routeBudget,
    error:
      routeData.status === 'success' || (geometry.length > 0 && allStops.length > 0)
        ? ''
        : routeData.summary || 'Route map data is currently unavailable for this trip.',
    startPoint,
    destinationPoint,
    routeType: routeData.status === 'success' ? 'verified' : 'estimated',
  }
}

async function fetchRouteDetails(startQuery, destinationQuery, mode, travelers = 2, travelStyle = 'standard') {
  const queryParams = new URLSearchParams({
    start: String(startQuery || '').trim(),
    destination: String(destinationQuery || '').trim(),
    mode: String(mode || 'driving').trim(),
    travelers: String(travelers || 2),
    travel_style: String(travelStyle || 'standard'),
  })

  try {
    const response = await fetch(`${API_BASE}/api/routes?${queryParams.toString()}`)
    if (!response.ok) {
      return parseRoutePayload(null, mode)
    }
    const routeData = await response.json()
    return parseRoutePayload(routeData, mode)
  } catch {
    return parseRoutePayload(null, mode)
  }
}

function FitMapBounds({ route, places, startPoint, destinationPoint }) {
  const map = useMap()

  useEffect(() => {
    const boundPoints = []
    if (startPoint?.coordinates) boundPoints.push(startPoint.coordinates)
    if (destinationPoint?.coordinates) boundPoints.push(destinationPoint.coordinates)
    for (const place of places || []) {
      if (place.coordinates && place.coordinates[0] !== 0) boundPoints.push(place.coordinates)
    }
    if (route?.coordinates?.length) {
      boundPoints.push(...route.coordinates)
    }

    if (boundPoints.length > 1) {
      map.fitBounds(boundPoints, { padding: [35, 35] })
    } else if (boundPoints.length === 1) {
      map.setView(boundPoints[0], 10)
    }
  }, [route, places, startPoint, destinationPoint, map])

  return null
}

function RouteMap({ routeData, selectedStopId, onSelectStop }) {
  if (!routeData) {
    return <div className="map-empty">Map data is loading...</div>
  }

  const route = routeData.route
  const places = routeData.places || []

  return (
    <div className="map-wrapper">
      <div className="map-legend" aria-label="Map legend">
        <span><i className="legend-dot start-dot" /> Starting point</span>
        <span><i className="legend-dot destination-dot" /> Destination</span>
        <span><i className="legend-line route-dot" /> Verified Route</span>
        <span><i className="legend-dot enroute-dot" /> Famous Places Between Route</span>
        <span><i className="legend-dot attraction-dot" /> Destination Highlights</span>
      </div>

      <MapContainer center={[12.6, 77.1]} zoom={9} scrollWheelZoom className="map-container">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitMapBounds
          route={route}
          places={places}
          startPoint={routeData.startPoint}
          destinationPoint={routeData.destinationPoint}
        />

        {route?.coordinates?.length > 0 && (
          <Polyline positions={route.coordinates} pathOptions={{ color: '#6366f1', weight: 5, opacity: 0.9 }} />
        )}

        {routeData.startPoint && (
          <CircleMarker
            center={routeData.startPoint.coordinates}
            radius={11}
            pathOptions={{ color: '#059669', fillColor: '#10b981', fillOpacity: 1, weight: 3 }}
          >
            <Popup>
              <strong>Starting Point</strong>
              <br />
              {routeData.startPoint.name}
            </Popup>
          </CircleMarker>
        )}

        {routeData.destinationPoint && (
          <CircleMarker
            center={routeData.destinationPoint.coordinates}
            radius={12}
            pathOptions={{ color: '#c2410c', fillColor: '#f97316', fillOpacity: 1, weight: 3 }}
          >
            <Popup>
              <strong>Destination</strong>
              <br />
              {routeData.destinationPoint.name}
            </Popup>
          </CircleMarker>
        )}

        {places.map((place) => {
          const isEnRoute = place.isEnRoute
          const isSelected = selectedStopId === place.id
          const markerBorder = isSelected ? '#38bdf8' : (isEnRoute ? '#d97706' : '#7c3aed')
          const markerFill = isSelected ? '#38bdf8' : (isEnRoute ? '#f59e0b' : '#a855f7')

          return (
            <CircleMarker
              key={place.id}
              center={place.coordinates}
              radius={isSelected ? 10 : (isEnRoute ? 8 : 7)}
              pathOptions={{
                color: markerBorder,
                fillColor: markerFill,
                fillOpacity: 0.95,
                weight: isSelected ? 3 : 2,
              }}
              eventHandlers={{ click: () => onSelectStop(place.id) }}
            >
              <Popup>
                <div style={{ maxWidth: '240px' }}>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      color: isEnRoute ? '#d97706' : '#7c3aed',
                      display: 'block',
                      marginBottom: '4px',
                    }}
                  >
                    {isEnRoute ? '📍 Famous En Route Stop (Between Route)' : '⭐ Destination Highlight'}
                  </span>
                  <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{place.name}</strong>
                  <div style={{ fontSize: '0.78rem', color: '#475569', margin: '4px 0' }}>
                    <em>{place.category} · {place.location}</em>
                  </div>
                  <p style={{ fontSize: '0.82rem', color: '#334155', margin: '6px 0 0', lineHeight: 1.4 }}>
                    {place.description}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}

function App() {
  const [formData, setFormData] = useState(defaultForm)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [health, setHealth] = useState({ status: 'checking', service: 'API' })
  const [generatedPlan, setGeneratedPlan] = useState('')
  const [tripSummary, setTripSummary] = useState(null)
  const [markdownReport, setMarkdownReport] = useState('')
  const [reportLoading, setReportLoading] = useState(false)
  const [pdfUrl, setPdfUrl] = useState('')
  const [aiSource, setAiSource] = useState('')
  const [routeData, setRouteData] = useState(null)
  const [routeLoading, setRouteLoading] = useState(false)
  const [mapError, setMapError] = useState('')
  const [selectedStopId, setSelectedStopId] = useState('')
  const [popularStops, setPopularStops] = useState([])
  const [enRouteStops, setEnRouteStops] = useState([])
  const [destinationStops, setDestinationStops] = useState([])
  const [itineraryStops, setItineraryStops] = useState([])
  const [directionsExpanded, setDirectionsExpanded] = useState(true)

  const formattedBudget = useMemo(
    () => formatInr(formData.budget),
    [formData.budget],
  )

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`)
      if (!response.ok) {
        throw new Error('Health check failed')
      }

      const payload = await response.json()
      setHealth({
        status: payload.status === 'healthy' ? 'healthy' : 'degraded',
        service: payload.service || 'AI Travel Planner API',
      })
    } catch {
      setHealth({ status: 'offline', service: 'Backend unavailable' })
    }
  }

  const updateRouteMap = async (request) => {
    setRouteLoading(true)
    setMapError('')

    try {
      const routeInfo = await fetchRouteDetails(
        request.start || request.destination,
        request.destination,
        request.travel_mode || 'driving',
        request.travelers || 2,
        request.travel_style || 'standard',
      )

      setRouteData(routeInfo)
      setEnRouteStops(routeInfo.enRoutePlaces || [])
      setDestinationStops(routeInfo.destinationPlaces || [])
      setPopularStops(routeInfo.places || [])
      setMapError(routeInfo.error || '')
      if (routeInfo.places?.[0]) {
        setSelectedStopId(routeInfo.places[0].id)
      }
    } catch {
      setMapError('Route map data is currently unavailable for this trip.')
      setRouteData(null)
      setPopularStops([])
      setEnRouteStops([])
      setDestinationStops([])
    } finally {
      setRouteLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    updateRouteMap(defaultForm)
  }, [])

  const handleInputChange = (event) => {
    const { name, value } = event.target

    if (name === 'budget') {
      if (value === '') {
        setFormData((current) => ({ ...current, budget: '' }))
        return
      }

      const parsed = Number(value)
      setFormData((current) => ({
        ...current,
        budget: Number.isFinite(parsed) ? parsed : current.budget,
      }))
      return
    }

    setFormData((current) => ({
      ...current,
      [name]:
        name === 'days' || name === 'travelers'
          ? Number(value)
          : value,
    }))
  }

  const fetchMarkdownReport = async () => {
    setReportLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/reports/markdown`)
      if (!response.ok) {
        setMarkdownReport('')
        return
      }

      const payload = await response.json()
      setMarkdownReport(payload.content || 'No markdown content returned.')
    } catch {
      setMarkdownReport('')
    } finally {
      setReportLoading(false)
    }
  }

  const handleGenerateTrip = async (event) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)

    const budgetValue = Number(formData.budget)
    if (!Number.isFinite(budgetValue) || budgetValue <= 0 || budgetValue > 10_000_000) {
      setError('Budget must be a valid positive amount up to ₹ 1,00,00,000.')
      setIsLoading(false)
      return
    }

    try {
      const payload = {
        ...formData,
        budget: budgetValue,
        days: Number(formData.days),
        travelers: Number(formData.travelers),
        currency: 'INR',
      }

      const response = await fetch(`${API_BASE}/api/trips/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Trip generation failed.')
      }

      setTripSummary({
        start: data.trip?.start || formData.start,
        destination: data.destination || formData.destination,
        days: data.trip?.days || formData.days,
        budget: data.trip?.budget || budgetValue,
        travelers: data.trip?.travelers || formData.travelers,
        travel_style: data.trip?.travel_style || formData.travel_style,
        travel_mode: data.trip?.travel_mode || formData.travel_mode,
        preferences: data.trip?.preferences || formData.preferences,
        currency: data.trip?.currency || 'INR',
      })
      setGeneratedPlan(data.result || 'No itinerary returned from the backend.')
      setAiSource(
        data.ai_source === 'gemini_live'
          ? 'Live Gemini response (Fast AI Itinerary)'
          : data.warnings && data.warnings.length
            ? `Offline fallback response — ${data.warnings[0]}`
            : 'Offline fallback response — AI provider is offline, but itinerary and route details are generated safely.',
      )
      setPdfUrl(`${API_BASE}/api/reports/pdf`)

      if (data.markdown_content) {
        setMarkdownReport(data.markdown_content)
      } else {
        await fetchMarkdownReport()
      }

      if (data.route_data) {
        const routeInfo = parseRoutePayload(data.route_data, formData.travel_mode || 'driving')
        setRouteData(routeInfo)
        setEnRouteStops(routeInfo.enRoutePlaces || [])
        setDestinationStops(routeInfo.destinationPlaces || [])
        setPopularStops(routeInfo.places || [])
        setMapError(routeInfo.error || '')
        if (routeInfo.places?.[0]) {
          setSelectedStopId(routeInfo.places[0].id)
        }
      } else {
        await updateRouteMap({
          start: formData.start || formData.destination,
          destination: formData.destination,
          travel_mode: formData.travel_mode || 'driving',
          travelers: formData.travelers,
          travel_style: formData.travel_style,
        })
      }
    } catch (submitError) {
      setError(submitError.message || 'Unable to generate a trip right now.')
      setAiSource('')
      setGeneratedPlan('')
      setTripSummary(null)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleStop = (place) => {
    setItineraryStops((current) => {
      const exists = current.some((entry) => entry.id === place.id)
      if (exists) {
        return current.filter((entry) => entry.id !== place.id)
      }
      return [...current, place]
    })
    setSelectedStopId(place.id)
  }

  const budgetBreakdown = useMemo(() => {
    const base = Number(formData.budget || 0)
    const travelers = Number(formData.travelers || 1)
    return [
      { label: 'Transport / Route', amount: base * 0.15 },
      { label: 'Accommodation', amount: base * 0.40 },
      { label: 'Food & Dining', amount: base * 0.25 },
      { label: 'Sightseeing & Activities', amount: base * 0.15 },
      { label: 'Contingency buffer', amount: base * 0.05 },
    ].map((item) => ({
      ...item,
      perPerson: item.amount / travelers,
    }))
  }, [formData.budget, formData.travelers])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Travel Planner</p>
          <h1>Build your next unforgettable trip</h1>
        </div>

        <div className={`health-indicator ${health.status}`} aria-live="polite">
          <span className="status-dot" aria-hidden="true" />
          <div>
            <strong>{health.service}</strong>
            <small>
              {health.status === 'healthy'
                ? 'Healthy'
                : health.status === 'offline'
                  ? 'Offline'
                  : 'Checking'}
            </small>
          </div>
        </div>
      </header>

      <main className="planner-layout">
        <section className="card form-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Trip setup</p>
              <h2>Travel details</h2>
            </div>
          </div>

          <form onSubmit={handleGenerateTrip} className="travel-form">
            <div className="field-grid">
              <label className="field">
                <span>Starting city</span>
                <input
                  type="text"
                  name="start"
                  value={formData.start}
                  onChange={handleInputChange}
                  placeholder="e.g. Bangalore"
                />
              </label>

              <label className="field">
                <span>Destination</span>
                <input
                  type="text"
                  name="destination"
                  value={formData.destination}
                  onChange={handleInputChange}
                  placeholder="e.g. Mysore"
                  required
                />
              </label>

              <label className="field">
                <span>Days</span>
                <input
                  type="number"
                  name="days"
                  min="1"
                  max="30"
                  value={formData.days}
                  onChange={handleInputChange}
                />
              </label>

              <label className="field">
                <span>Total Budget (₹ INR)</span>
                <div className="currency-input-wrap">
                  <span className="currency-prefix">₹</span>
                  <input
                    type="number"
                    name="budget"
                    min="0.01"
                    max="10000000"
                    step="any"
                    inputMode="decimal"
                    required
                    value={Number.isFinite(formData.budget) ? formData.budget : ''}
                    onChange={handleInputChange}
                    aria-label="Budget in Indian Rupees"
                  />
                </div>
              </label>

              <label className="field">
                <span>Travelers</span>
                <input
                  type="number"
                  name="travelers"
                  min="1"
                  max="50"
                  value={formData.travelers}
                  onChange={handleInputChange}
                />
              </label>

              <div className="field">
                <span>Travel style</span>
                <div className="style-switcher" role="tablist" aria-label="Travel style selector">
                  {['budget', 'standard', 'luxury'].map((style) => (
                    <button
                      key={style}
                      type="button"
                      className={formData.travel_style === style ? 'active' : ''}
                      onClick={() =>
                        setFormData((current) => ({ ...current, travel_style: style }))
                      }
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>

              <div className="field full-width">
                <span>Travel mode</span>
                <div className="style-switcher travel-mode-switcher" role="tablist" aria-label="Travel mode selector">
                  {TRAVEL_MODES.map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      className={formData.travel_mode === mode ? 'active' : ''}
                      onClick={() =>
                        setFormData((current) => ({ ...current, travel_mode: mode }))
                      }
                    >
                      {mode.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              <label className="field full-width">
                <span>Travel preferences</span>
                <textarea
                  name="preferences"
                  rows="4"
                  value={formData.preferences}
                  onChange={handleInputChange}
                  placeholder="Heritage sites, local food, nature, scenic viewpoints, relaxed driving route..."
                />
              </label>
            </div>

            <div className="form-meta-row">
              <span className="budget-preview">{formattedBudget}</span>
              <span className="meta-caption">Estimated total group budget in INR</span>
            </div>

            <div className="form-actions">
              <button type="submit" className="primary-button" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <span className="spinner" aria-hidden="true" />
                    Generating complete trip plan...
                  </>
                ) : (
                  'Generate Trip Plan'
                )}
              </button>
            </div>
          </form>
        </section>

        <aside className="card preview-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Overview</p>
              <h2>Trip snapshot</h2>
            </div>
          </div>

          {tripSummary ? (
            <div className="summary-grid">
              <div className="summary-item">
                <span>From</span>
                <strong>{tripSummary.start || 'Bangalore'}</strong>
              </div>
              <div className="summary-item">
                <span>To</span>
                <strong>{tripSummary.destination}</strong>
              </div>
              <div className="summary-item">
                <span>Days</span>
                <strong>{tripSummary.days} days</strong>
              </div>
              <div className="summary-item">
                <span>Total Budget</span>
                <strong>{formatInr(tripSummary.budget)}</strong>
              </div>
              <div className="summary-item">
                <span>Travelers</span>
                <strong>{tripSummary.travelers} person(s)</strong>
              </div>
              <div className="summary-item">
                <span>Style</span>
                <strong>{tripSummary.travel_style} ({tripSummary.travel_mode})</strong>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              Fill out the trip details and generate a plan to view the comprehensive itinerary here.
            </div>
          )}

          <div className="itinerary-wrapper">
            <h3>Generated Itinerary Details</h3>
            {generatedPlan ? (
              <div className="itinerary-body">{generatedPlan}</div>
            ) : (
              <div className="empty-state small">No itinerary generated yet. Click Generate Trip to begin.</div>
            )}
          </div>
        </aside>
      </main>

      {(error || aiSource) && (
        <div className={`banner ${error ? 'error-banner' : 'info-banner'}`}>
          {error || aiSource}
        </div>
      )}

      {/* Interactive Route Map Section */}
      <section className="card map-panel">
        <div className="panel-header report-header">
          <div>
            <p className="eyebrow">Interactive Route Map</p>
            <h2>{formData.start || 'Origin'} to {formData.destination || 'Destination'} Navigation</h2>
          </div>
          <div className="route-summary">
            {routeData?.route ? (
              <>
                <span className="route-mode-badge">{routeData.route.mode || 'Driving'}</span>
                <span><strong>{routeData.route.distanceKm} km</strong></span>
                <span><strong>~{routeData.route.durationMinutes} mins</strong></span>
              </>
            ) : (
              <span>Calculating route data...</span>
            )}
          </div>
        </div>

        {routeLoading ? (
          <div className="empty-state small">Loading route map, navigation directions, and attractions...</div>
        ) : routeData ? (
          <RouteMap
            routeData={routeData}
            selectedStopId={selectedStopId}
            onSelectStop={setSelectedStopId}
          />
        ) : (
          <div className="empty-state small">Route map is preparing...</div>
        )}

        {mapError && <div className="map-error-banner">{mapError}</div>}

        {/* Route Travel Budget Strip */}
        {routeData?.routeBudget && (
          <div className="route-budget-container">
            <div className="route-budget-header">
              <h3>
                <span>⛽ Route Travel Budget</span>
                <span className="route-mode-badge">{routeData.routeBudget.mode_label || 'Driving'}</span>
              </h3>
              <small style={{ color: '#cbd5e1' }}>
                Distance: {routeData.routeBudget.distance_km} km ({formData.travelers} travelers)
              </small>
            </div>

            <div className="route-budget-grid">
              <div className="route-budget-item">
                <span>Fuel Cost</span>
                <strong>{formatInr(routeData.routeBudget.fuel_cost)}</strong>
              </div>
              <div className="route-budget-item">
                <span>Highway Tolls</span>
                <strong>{formatInr(routeData.routeBudget.toll_cost)}</strong>
              </div>
              <div className="route-budget-item">
                <span>Highway Food & Snacks</span>
                <strong>{formatInr(routeData.routeBudget.highway_refreshments)}</strong>
              </div>
              <div className="route-budget-item highlight">
                <span>One-Way Total</span>
                <strong>{formatInr(routeData.routeBudget.total_one_way)}</strong>
              </div>
              <div className="route-budget-item highlight">
                <span>Round-Trip Total</span>
                <strong>{formatInr(routeData.routeBudget.total_round_trip)}</strong>
              </div>
              <div className="route-budget-item">
                <span>Per Traveler</span>
                <strong>{formatInr(routeData.routeBudget.cost_per_traveler)}</strong>
              </div>
            </div>
            {routeData.routeBudget.notes && (
              <p className="route-budget-note">{routeData.routeBudget.notes}</p>
            )}
          </div>
        )}

        {/* Accurate Turn-by-Turn Route Directions */}
        {routeData?.directions?.length > 0 && (
          <div className="directions-wrapper">
            <div
              className="directions-header"
              onClick={() => setDirectionsExpanded(!directionsExpanded)}
              role="button"
              tabIndex={0}
            >
              <h3>
                <span>🧭 Accurate Turn-by-Turn Route Directions</span>
                <span className="step-count-pill">{routeData.directions.length} steps</span>
              </h3>
              <span className="toggle-arrow">{directionsExpanded ? '▲ Hide steps' : '▼ Show directions'}</span>
            </div>

            {directionsExpanded && (
              <div className="directions-list">
                {routeData.directions.map((step) => (
                  <div key={step.step} className="direction-step-card">
                    <div className="step-number">{step.step}</div>
                    <div className="step-content">
                      <p>{step.instruction}</p>
                      <div className="step-meta">
                        <span className="step-road">{step.road}</span>
                        {step.distance_km > 0 && <span>• {step.distance_km} km</span>}
                        {step.duration_minutes > 0 && <span>• ~{step.duration_minutes} min</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Famous Places Between The Route (En Route Stops) */}
      <section className="card route-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Route Highlights</p>
            <h2>Famous Places That Can Be Visited Between The Route</h2>
            <small style={{ color: '#94a3b8', display: 'block', marginTop: '4px' }}>
              Iconic scenic viewpoints, heritage fortresses, craft villages, and highway food stops along your road trip.
            </small>
          </div>
        </div>

        <div className="route-list">
          {enRouteStops.length ? (
            enRouteStops.map((place) => {
              const active = itineraryStops.some((entry) => entry.id === place.id)
              return (
                <button
                  key={place.id}
                  type="button"
                  className={`stop-item ${selectedStopId === place.id ? 'selected' : ''}`}
                  onClick={() => toggleStop(place)}
                >
                  <div>
                    <span className="enroute-badge">📍 Between Route</span>
                    <strong>{place.name}</strong>
                    <small>{place.category}</small>
                    <span className="milestone-text">{place.location}</span>
                    <p>{place.description}</p>
                  </div>
                  <span className={`tag ${active ? 'tag enroute-active' : ''}`}>
                    {active ? 'Added to trip' : '+ Add stop'}
                  </span>
                </button>
              )
            })
          ) : (
            <div className="empty-state small">No midway stops available for this corridor.</div>
          )}
        </div>
      </section>

      {/* Destination Must-Visit Highlights */}
      <section className="card route-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Destination Landmarks</p>
            <h2>Must-Visit Places in {formData.destination}</h2>
            <small style={{ color: '#94a3b8', display: 'block', marginTop: '4px' }}>
              Top cultural attractions, royal palaces, markets, and scenic spots in {formData.destination}.
            </small>
          </div>
        </div>

        <div className="route-list">
          {destinationStops.length ? (
            destinationStops.map((place) => {
              const active = itineraryStops.some((entry) => entry.id === place.id)
              return (
                <button
                  key={place.id}
                  type="button"
                  className={`stop-item ${selectedStopId === place.id ? 'selected' : ''}`}
                  onClick={() => toggleStop(place)}
                >
                  <div>
                    <span className="tag" style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', marginBottom: '6px' }}>
                      ⭐ Destination
                    </span>
                    <strong>{place.name}</strong>
                    <small>{place.category} · {place.location || formData.destination}</small>
                    <p>{place.description}</p>
                  </div>
                  <span className={`tag ${active ? 'active' : ''}`}>
                    {active ? 'Added to trip' : '+ Add stop'}
                  </span>
                </button>
              )
            })
          ) : (
            <div className="empty-state small">No destination highlights available yet.</div>
          )}
        </div>
      </section>

      {/* Estimated Overall Budget Breakdown */}
      <section className="card budget-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Trip Budget</p>
            <h2>Overall Estimated Budget Breakdown ({formData.currency || 'INR'})</h2>
          </div>
        </div>

        <div className="budget-grid">
          {budgetBreakdown.map((item) => (
            <div key={item.label} className="budget-card">
              <span>{item.label}</span>
              <strong>{formatInr(item.amount)}</strong>
              <small>Per traveler: {formatInr(item.perPerson)}</small>
            </div>
          ))}
        </div>
      </section>

      {/* Reports Section */}
      <section className="card report-panel">
        <div className="panel-header report-header">
          <div>
            <p className="eyebrow">Export Plan</p>
            <h2>Comprehensive Travel Plan Report</h2>
          </div>

          <div className="report-actions">
            <a
              className={`report-button ${pdfUrl ? '' : 'disabled'}`}
              href={pdfUrl || '#'}
              target={pdfUrl ? '_blank' : undefined}
              rel={pdfUrl ? 'noreferrer' : undefined}
            >
              📄 Download PDF Report
            </a>
            <button
              type="button"
              className="secondary-button"
              onClick={fetchMarkdownReport}
              disabled={reportLoading}
            >
              {reportLoading ? 'Refreshing...' : 'Refresh Markdown'}
            </button>
          </div>
        </div>

        <div className="report-viewer">
          {reportLoading ? (
            <div className="empty-state small">Loading travel report...</div>
          ) : markdownReport ? (
            <pre>{markdownReport}</pre>
          ) : (
            <div className="empty-state small">
              Generate a trip to view the complete formatted Markdown travel report with day-wise itinerary, directions, and budget.
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export default App
