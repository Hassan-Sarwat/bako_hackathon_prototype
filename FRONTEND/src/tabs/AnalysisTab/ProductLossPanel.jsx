import { useState } from 'react'
import { fetchProductLossDrilldown } from '../../api'
import ProductLossDrillDown from './ProductLossDrillDown'

function trafficClass(lossPct) {
  if (lossPct >= 15) return 'traffic-light--red'
  if (lossPct >= 5) return 'traffic-light--yellow'
  return 'traffic-light--green'
}

export default function ProductLossPanel({ data, startDate, endDate }) {
  const [expandedId, setExpandedId] = useState(null)
  const [drilldownData, setDrilldownData] = useState([])
  const [drilldownLoading, setDrilldownLoading] = useState(false)

  function handleRowClick(productId) {
    if (expandedId === productId) {
      setExpandedId(null)
      return
    }
    setExpandedId(productId)
    setDrilldownLoading(true)
    fetchProductLossDrilldown(productId, { start_date: startDate, end_date: endDate })
      .then(setDrilldownData)
      .catch(() => setDrilldownData([]))
      .finally(() => setDrilldownLoading(false))
  }

  if (!data || data.length === 0) {
    return (
      <div className="analysis-empty">
        Keine Produktverlustdaten für den gewählten Zeitraum gefunden.
        Stellen Sie sicher, dass Backpläne und Produktmaterialien konfiguriert sind.
      </div>
    )
  }

  return (
    <div className="analysis-grid">
      <div className="analysis-header analysis-header--product">
        <span></span>
        <span>Produkt</span>
        <span>Zugeordneter Verlust (€)</span>
        <span>Verlust/Stück (€)</span>
      </div>

      {data.map(p => (
        <div key={p.product_id}>
          <div
            className={`analysis-row analysis-row--product ${p.flagged ? 'analysis-row--flagged' : ''} ${expandedId === p.product_id ? 'analysis-row--expanded' : ''}`}
            onClick={() => handleRowClick(p.product_id)}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && handleRowClick(p.product_id)}
          >
            <span><span className={`traffic-light ${trafficClass(p.loss_pct_of_price)}`} /></span>
            <span className="item-name">
              <span className="expand-icon">{expandedId === p.product_id ? '▾' : '▸'}</span>
              {p.product_name}
            </span>
            <span className={p.attributed_loss_value > 0 ? 'item-loss' : ''}>
              {p.attributed_loss_value.toFixed(2)}
            </span>
            <span>{p.loss_per_unit.toFixed(4)}</span>
          </div>

          {expandedId === p.product_id && (
            <div className="drilldown-panel">
              <div className="expanded-detail-cards">
                <div className="detail-card">
                  <span className="detail-card-label">Geplante Stück</span>
                  <span className="detail-card-value">{p.total_units_planned}</span>
                </div>
                <div className="detail-card">
                  <span className="detail-card-label">Zutaten</span>
                  <span className="detail-card-value">{p.materials_count}</span>
                </div>
                <div className="detail-card">
                  <span className="detail-card-label">Verlust % vom Preis</span>
                  <span className="detail-card-value">
                    <span className={`pct-badge ${p.flagged ? 'pct-badge--flagged' : 'pct-badge--ok'}`}>
                      {p.loss_pct_of_price > 0 ? '+' : ''}{p.loss_pct_of_price}%
                    </span>
                  </span>
                </div>
              </div>

              {drilldownLoading
                ? <div className="drilldown-loading">Details werden geladen…</div>
                : <ProductLossDrillDown entries={drilldownData} />
              }
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
