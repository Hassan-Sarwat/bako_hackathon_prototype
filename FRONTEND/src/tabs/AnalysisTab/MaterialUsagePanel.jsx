import { useState } from 'react'
import { fetchMaterialDrilldown } from '../../api'
import MaterialDrillDown from './MaterialDrillDown'

function formatAmount(value, unit) {
  if (unit === 'g' && Math.abs(value) >= 1000) return `${(value / 1000).toFixed(2)} kg`
  if (unit === 'ml' && Math.abs(value) >= 1000) return `${(value / 1000).toFixed(2)} L`
  return `${value.toLocaleString()} ${unit}`
}

function trafficClass(lossPct) {
  if (lossPct >= 15) return 'traffic-light--red'
  if (lossPct >= 5) return 'traffic-light--yellow'
  return 'traffic-light--green'
}

export default function MaterialUsagePanel({ data, startDate, endDate }) {
  const [expandedId, setExpandedId] = useState(null)
  const [drilldownData, setDrilldownData] = useState([])
  const [drilldownLoading, setDrilldownLoading] = useState(false)

  function handleRowClick(materialId) {
    if (expandedId === materialId) {
      setExpandedId(null)
      return
    }
    setExpandedId(materialId)
    setDrilldownLoading(true)
    fetchMaterialDrilldown(materialId, { start_date: startDate, end_date: endDate })
      .then(setDrilldownData)
      .catch(() => setDrilldownData([]))
      .finally(() => setDrilldownLoading(false))
  }

  if (!data || data.length === 0) {
    return (
      <div className="analysis-empty">
        Keine Materialverbrauchsdaten für den gewählten Zeitraum gefunden.
        Stellen Sie sicher, dass Backpläne und Produktmaterialien konfiguriert sind.
      </div>
    )
  }

  return (
    <div className="analysis-grid">
      <div className="analysis-header analysis-header--simple">
        <span></span>
        <span>Material</span>
        <span>Schwund</span>
        <span>Verlust (€)</span>
        <span>Verlust %</span>
      </div>

      {data.map(m => (
        <div key={m.material_id}>
          <div
            className={`analysis-row analysis-row--simple ${m.flagged ? 'analysis-row--flagged' : ''} ${expandedId === m.material_id ? 'analysis-row--expanded' : ''}`}
            onClick={() => handleRowClick(m.material_id)}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && handleRowClick(m.material_id)}
          >
            <span><span className={`traffic-light ${trafficClass(m.loss_pct)}`} /></span>
            <span className="item-name">
              <span className="expand-icon">{expandedId === m.material_id ? '▾' : '▸'}</span>
              {m.material_name}
            </span>
            <span className={m.unaccounted_loss > 0 ? 'val-negative' : 'val-positive'}>
              {formatAmount(m.unaccounted_loss, m.unit)}
            </span>
            <span className={m.estimated_loss_value > 0 ? 'item-loss' : ''}>
              {m.estimated_loss_value.toFixed(2)}
            </span>
            <span>
              <span className={`pct-badge ${m.loss_pct >= 15 ? 'pct-badge--flagged' : 'pct-badge--ok'}`}>
                {m.loss_pct > 0 ? '+' : ''}{m.loss_pct}%
              </span>
            </span>
          </div>

          {expandedId === m.material_id && (
            <div className="drilldown-panel">
              {/* Detail cards for hidden columns */}
              <div className="expanded-detail-cards">
                <div className="detail-card">
                  <span className="detail-card-label">Anfangsbestand</span>
                  <span className="detail-card-value">{formatAmount(m.start_inventory, m.unit)}</span>
                </div>
                <div className="detail-card">
                  <span className="detail-card-label">Eingekauft</span>
                  <span className="detail-card-value">{formatAmount(m.total_purchased, m.unit)}</span>
                </div>
                <div className="detail-card">
                  <span className="detail-card-label">Erw. Verbrauch</span>
                  <span className="detail-card-value">{formatAmount(m.expected_usage, m.unit)}</span>
                </div>
                <div className="detail-card">
                  <span className="detail-card-label">Erw. Restbestand</span>
                  <span className="detail-card-value">{formatAmount(m.expected_remaining, m.unit)}</span>
                </div>
                <div className="detail-card">
                  <span className="detail-card-label">Ist-Bestand</span>
                  <span className="detail-card-value">{formatAmount(m.current_stock, m.unit)}</span>
                </div>
              </div>

              {drilldownLoading
                ? <div className="drilldown-loading">Details werden geladen…</div>
                : <MaterialDrillDown entries={drilldownData} unit={m.unit} />
              }
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
