import { useState, useEffect, useMemo } from 'react'
import { fetchProductLossAnalysis, fetchProductLossDrilldown } from '../../api'
import ProductLossDrillDown from './ProductLossDrillDown'

function toISO(d) {
  return d.toISOString().slice(0, 10)
}

export default function ProductLossPanel() {
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
    fetchProductLossAnalysis({ start_date: startDate, end_date: endDate })
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

  const totalLoss = data.reduce((sum, p) => sum + p.attributed_loss_value, 0)
  const flaggedCount = data.filter(p => p.flagged).length

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
              <span className="summary-label">Est. Total Product Loss</span>
              <span className="summary-value summary-value--loss">{totalLoss.toFixed(2)} €</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Flagged Products</span>
              <span className={`summary-value ${flaggedCount > 0 ? 'summary-value--loss' : ''}`}>{flaggedCount}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Products Tracked</span>
              <span className="summary-value">{data.length}</span>
            </div>
          </div>

          <div className="analysis-grid">
            <div className="analysis-header">
              <span>Product</span>
              <span>Units Planned</span>
              <span>Materials</span>
              <span>Attributed Loss (€)</span>
              <span>Loss/Unit (€)</span>
              <span>Loss % of Price</span>
            </div>

            {data.map(p => (
              <div key={p.product_id}>
                <div
                  className={`analysis-row ${p.flagged ? 'analysis-row--flagged' : ''} ${expandedId === p.product_id ? 'analysis-row--expanded' : ''}`}
                  onClick={() => handleRowClick(p.product_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && handleRowClick(p.product_id)}
                >
                  <span className="item-name">
                    <span className="expand-icon">{expandedId === p.product_id ? '▾' : '▸'}</span>
                    {p.product_name}
                  </span>
                  <span>{p.total_units_planned}</span>
                  <span>{p.materials_count}</span>
                  <span className={p.attributed_loss_value > 0 ? 'item-loss' : ''}>{p.attributed_loss_value.toFixed(2)}</span>
                  <span>{p.loss_per_unit.toFixed(4)}</span>
                  <span>
                    <span className={`pct-badge ${p.flagged ? 'pct-badge--flagged' : 'pct-badge--ok'}`}>
                      {p.loss_pct_of_price > 0 ? '+' : ''}{p.loss_pct_of_price}%
                    </span>
                  </span>
                </div>

                {expandedId === p.product_id && (
                  <div className="drilldown-panel">
                    {drilldownLoading
                      ? <div className="drilldown-loading">Loading details…</div>
                      : <ProductLossDrillDown entries={drilldownData} />
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
          No product loss data found for the selected date range.
          Make sure cooking plans and product materials are configured.
        </div>
      )}
    </div>
  )
}
