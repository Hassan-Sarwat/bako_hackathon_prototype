import { useState, useEffect, useMemo } from 'react'
import { fetchDailyPlan, fetchProductHistory } from '../../api'
import SalesChart from './SalesChart'
import './PredictionPlanTab.css'

function toISO(d) {
  return d.toISOString().slice(0, 10)
}

export default function PredictionPlanTab() {
  const today = useMemo(() => toISO(new Date()), [])
  const [date, setDate] = useState(today)
  const [plan, setPlan] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [expandedId, setExpandedId] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [chartLoading, setChartLoading] = useState(false)

  function load(d) {
    setLoading(true)
    setError(null)
    setExpandedId(null)
    setChartData(null)
    fetchDailyPlan(d)
      .then(setPlan)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(date) }, [date])

  function handleRowClick(productId) {
    if (expandedId === productId) {
      setExpandedId(null)
      return
    }
    setExpandedId(productId)
    setChartLoading(true)
    fetchProductHistory(productId)
      .then(setChartData)
      .catch(() => setChartData(null))
      .finally(() => setChartLoading(false))
  }

  const totalRevenue = plan.reduce((sum, p) => sum + (p.estimated_revenue || 0), 0)
  const totalProduction = plan.reduce((sum, p) => sum + p.recommended_production, 0)

  return (
    <div className="prediction-plan-tab">
      <div className="prediction-toolbar">
        <label>
          Datum
          <input type="date" value={date} onChange={e => setDate(e.target.value)} />
        </label>
        <button className="btn-refresh" onClick={() => load(date)}>Aktualisieren</button>
      </div>

      {loading && <div className="tab-status">Prognosen werden geladen...</div>}
      {error && <div className="tab-status tab-status--error">Error: {error}</div>}

      {!loading && !error && plan.length > 0 && (
        <>
          <div className="prediction-summary">
            <div className="summary-card">
              <span className="summary-label">Produkte</span>
              <span className="summary-value">{plan.length}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Gesamtproduktion</span>
              <span className="summary-value">{totalProduction}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Gesch. Umsatz</span>
              <span className="summary-value summary-value--positive">{totalRevenue.toFixed(2)} &euro;</span>
            </div>
          </div>

          <div className="prediction-grid">
            <div className="prediction-header">
              <span>Produkt</span>
              <span>Progn. Verkauf</span>
              <span>Empfohlen</span>
              <span>Preis</span>
              <span>Gesch. Umsatz</span>
            </div>

            {plan.map(p => (
              <div key={p.product_id}>
                <div
                  className={`prediction-row ${expandedId === p.product_id ? 'prediction-row--expanded' : ''}`}
                  onClick={() => handleRowClick(p.product_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && handleRowClick(p.product_id)}
                >
                  <span className="item-name">
                    <span className="expand-icon">{expandedId === p.product_id ? '\u25BE' : '\u25B8'}</span>
                    {p.product_name}
                  </span>
                  <span>
                    {p.predicted_sales}
                    {p.confidence_lower != null && (
                      <span className="confidence-range"> ({p.confidence_lower}–{p.confidence_upper})</span>
                    )}
                  </span>
                  <span className="recommended-qty">{p.recommended_production}</span>
                  <span>{p.price.toFixed(2)} &euro;</span>
                  <span className="est-revenue">{(p.estimated_revenue || 0).toFixed(2)} &euro;</span>
                </div>

                {expandedId === p.product_id && (
                  <div className="chart-panel">
                    {chartLoading ? (
                      <div className="chart-loading">Diagramm wird geladen...</div>
                    ) : chartData ? (
                      <div className="chart-wrapper">
                        <h4 className="chart-title">{chartData.product?.name} — Verkaufsverlauf &amp; Prognose</h4>
                        <SalesChart
                          history={chartData.history}
                          predictions={chartData.predictions}
                        />
                      </div>
                    ) : (
                      <div className="chart-empty">Keine Daten verfügbar</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && !error && plan.length === 0 && (
        <div className="prediction-empty">
          Keine Prognosen verfügbar für {date}. Führen Sie das Prognosemodell aus, um Prognosen zu erstellen.
        </div>
      )}
    </div>
  )
}
