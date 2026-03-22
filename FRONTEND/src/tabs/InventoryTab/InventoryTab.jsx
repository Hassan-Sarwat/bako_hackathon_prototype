import { useState, useEffect } from 'react'
import { fetchInventory, fetchMaterialNeeds } from '../../api'
import './InventoryTab.css'

function formatAmount(count, unit) {
  if (!unit) return String(count)
  if (unit === 'g' && count >= 1000) return `${(count / 1000).toFixed(2)} kg`
  if (unit === 'ml' && count >= 1000) return `${(count / 1000).toFixed(2)} L`
  if (unit === 'Stuck') return `${count} Stk`
  return `${count.toLocaleString()} ${unit}`
}

function stockClass(count, unit) {
  // Thresholds depend on unit — base units are g, ml, Stuck
  if (unit === 'g' || unit === 'ml') {
    if (count <= 500) return 'stock-critical'
    if (count <= 2000) return 'stock-low'
    return 'stock-ok'
  }
  // Stuck or unknown
  if (count <= 10) return 'stock-critical'
  if (count <= 50) return 'stock-low'
  return 'stock-ok'
}

function stockLabel(count, unit) {
  const cls = stockClass(count, unit)
  if (cls === 'stock-critical') return 'Critical'
  if (cls === 'stock-low') return 'Low'
  return 'OK'
}

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString([], { day: '2-digit', month: '2-digit', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function InventoryTab() {
  const [items, setItems] = useState([])
  const [needs, setNeeds] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      fetchInventory(),
      fetchMaterialNeeds(3).catch(() => ({ needs: [] })),
    ])
      .then(([inv, needsResp]) => {
        setItems(inv)
        setNeeds(needsResp.needs || [])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="tab-status">Loading inventory...</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  const criticalCount = items.filter(i => stockClass(i.count, i.unit) === 'stock-critical').length
  const lowCount = items.filter(i => stockClass(i.count, i.unit) === 'stock-low').length
  const shortages = needs.filter(n => n.has_shortage)

  return (
    <div className="inventory-tab">
      <div className="inventory-summary">
        <span><strong>{items.length}</strong> ingredients tracked</span>
        {criticalCount > 0 && (
          <span className="summary-critical">{criticalCount} critical</span>
        )}
        {lowCount > 0 && (
          <span className="summary-low">{lowCount} low</span>
        )}
        {shortages.length > 0 && (
          <span className="summary-shortage">{shortages.length} shortage{shortages.length > 1 ? 's' : ''} (3-day forecast)</span>
        )}
      </div>

      {/* Material needs section */}
      {needs.length > 0 && (
        <div className="needs-section">
          <h3 className="needs-title">Material Needs — Next 3 Days (based on forecast)</h3>
          <div className="needs-grid">
            <div className="needs-header">
              <span>Material</span>
              <span>Needed</span>
              <span>In Stock</span>
              <span>Shortage</span>
              <span>Status</span>
            </div>
            {needs.map(n => (
              <div key={n.material_id} className={`needs-row ${n.has_shortage ? 'needs-row--shortage' : ''}`}>
                <span className="item-name">{n.material_name}</span>
                <span>{formatAmount(n.needed, n.unit)}</span>
                <span>{formatAmount(n.current_stock, n.unit)}</span>
                <span className={n.has_shortage ? 'val-shortage' : ''}>
                  {n.has_shortage ? formatAmount(n.shortage, n.unit) : '—'}
                </span>
                <span>
                  {n.has_shortage
                    ? <span className="needs-badge needs-badge--shortage">Order needed</span>
                    : <span className="needs-badge needs-badge--ok">Sufficient</span>
                  }
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current inventory */}
      <div className="inventory-grid">
        <div className="inventory-header">
          <span>Ingredient</span>
          <span>Stock</span>
          <span>Status</span>
          <span>Logged by</span>
          <span className="col-time">Date / Time</span>
        </div>
        {items.map(item => (
          <div key={item.id} className="inventory-row">
            <span className="item-name">{item.item_name}</span>
            <span className={`item-count ${stockClass(item.count, item.unit)}`}>
              {formatAmount(item.count, item.unit)}
            </span>
            <span className={`item-status ${stockClass(item.count, item.unit)}`}>
              {stockLabel(item.count, item.unit)}
            </span>
            <span className="item-staff">{item.logged_by ?? '—'}</span>
            <span className="item-time col-time">{formatDateTime(item.logged_at)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
