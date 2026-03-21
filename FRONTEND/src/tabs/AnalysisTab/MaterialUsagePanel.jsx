import { useState, useEffect, useMemo } from 'react'
import { fetchMaterialUsageAnalysis, fetchMaterialDrilldown } from '../../api'
import MaterialDrillDown from './MaterialDrillDown'
import MaterialWasteChart from './MaterialWasteChart'

function toISO(d) {
  return d.toISOString().slice(0, 10)
}

function formatAmount(value, unit) {
  if (unit === 'g' && Math.abs(value) >= 1000) return `${(value / 1000).toFixed(2)} kg`
  if (unit === 'ml' && Math.abs(value) >= 1000) return `${(value / 1000).toFixed(2)} L`
  return `${value.toLocaleString()} ${unit}`
}

export default function MaterialUsagePanel() {
  const today = useMemo(() => new Date(), [])
  const weekAgo = useMemo(() => {
    const d = new Date(today)
    d.setDate(d.getDate() - 7)
    return d
  }, [today])

  const [startDate, setStartDate] = useState(toISO(weekAgo))
  const [endDate, setEndDate] = useState(toISO(today))
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [expandedId, setExpandedId] = useState(null)
  const [drilldownData, setDrilldownData] = useState([])
  const [drilldownLoading, setDrilldownLoading] = useState(false)

  function load() {
    setLoading(true)
    setError(null)
    setExpandedId(null)
    fetchMaterialUsageAnalysis({ start_date: startDate, end_date: endDate })
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

  const totalLoss = data.reduce((sum, m) => sum + m.estimated_loss_value, 0)
  const flaggedCount = data.filter(m => m.flagged).length

  return (
    <div className="material-usage-panel">
      <div className="analysis-toolbar">
        <label>
          From
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
        </label>
        <button className="btn-analyze" onClick={load}>Analyze</button>
      </div>

      {loading && <div className="tab-status">Loading analysis…</div>}
      {error && <div className="tab-status tab-status--error">Error: {error}</div>}

      {!loading && !error && data.length > 0 && (
        <>
          <div className="analysis-summary">
            <div className="summary-card">
              <span className="summary-label">Est. Total Loss</span>
              <span className="summary-value summary-value--loss">{totalLoss.toFixed(2)} €</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Flagged Materials</span>
              <span className={`summary-value ${flaggedCount > 0 ? 'summary-value--loss' : ''}`}>{flaggedCount}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Materials Tracked</span>
              <span className="summary-value">{data.length}</span>
            </div>
          </div>

          <MaterialWasteChart data={data} />

          <div className="analysis-grid">
            <div className="analysis-header">
              <span>Material</span>
              <span>Purchased</span>
              <span>Expected Usage</span>
              <span>Inventory</span>
              <span>Unaccounted</span>
              <span>Loss %</span>
              <span>Est. Loss (€)</span>
            </div>

            {data.map(m => (
              <div key={m.material_id}>
                <div
                  className={`analysis-row ${m.flagged ? 'analysis-row--flagged' : ''} ${expandedId === m.material_id ? 'analysis-row--expanded' : ''}`}
                  onClick={() => handleRowClick(m.material_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && handleRowClick(m.material_id)}
                >
                  <span className="item-name">
                    <span className="expand-icon">{expandedId === m.material_id ? '▾' : '▸'}</span>
                    {m.material_name}
                  </span>
                  <span>{formatAmount(m.total_purchased, m.unit)}</span>
                  <span>{formatAmount(m.expected_usage, m.unit)}</span>
                  <span>{formatAmount(m.current_stock, m.unit)}</span>
                  <span className={m.unaccounted_loss > 0 ? 'val-negative' : 'val-positive'}>
                    {formatAmount(m.unaccounted_loss, m.unit)}
                  </span>
                  <span>
                    <span className={`pct-badge ${m.flagged ? 'pct-badge--flagged' : 'pct-badge--ok'}`}>
                      {m.loss_pct > 0 ? '+' : ''}{m.loss_pct}%
                    </span>
                  </span>
                  <span className={m.estimated_loss_value > 0 ? 'item-loss' : ''}>{m.estimated_loss_value.toFixed(2)}</span>
                </div>

                {expandedId === m.material_id && (
                  <div className="drilldown-panel">
                    {drilldownLoading
                      ? <div className="drilldown-loading">Loading details…</div>
                      : <MaterialDrillDown entries={drilldownData} unit={m.unit} />
                    }
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="analysis-empty">
          No material usage data found for the selected date range.
          Make sure cooking plans and product materials are configured.
        </div>
      )}
    </div>
  )
}
