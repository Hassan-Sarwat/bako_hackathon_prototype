import { useState, useEffect } from 'react'
import { fetchInventory } from '../../api'
import './InventoryTab.css'

function stockClass(count) {
  if (count <= 3) return 'stock-critical'
  if (count <= 8) return 'stock-low'
  return 'stock-ok'
}

function stockLabel(count) {
  if (count <= 3) return 'Critical'
  if (count <= 8) return 'Low'
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchInventory()
      .then(setItems)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="tab-status">Loading inventory…</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  const criticalCount = items.filter(i => i.count <= 3).length
  const lowCount = items.filter(i => i.count > 3 && i.count <= 8).length
  const lastUpdated = items.reduce((latest, item) =>
    item.logged_at && item.logged_at > latest ? item.logged_at : latest,
    items[0]?.logged_at ?? null
  )

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
        {lastUpdated && (
          <span className="summary-updated">Last logged {formatDateTime(lastUpdated)}</span>
        )}
      </div>

      <div className="inventory-grid">
        <div className="inventory-header">
          <span>Ingredient</span>
          <span>Count</span>
          <span>Status</span>
          <span>Logged by</span>
          <span className="col-time">Date / Time</span>
        </div>
        {items.map(item => (
          <div key={item.id} className="inventory-row">
            <span className="item-name">{item.item_name}</span>
            <span className={`item-count ${stockClass(item.count)}`}>
              {item.count}
            </span>
            <span className={`item-status ${stockClass(item.count)}`}>
              {stockLabel(item.count)}
            </span>
            <span className="item-staff">{item.logged_by ?? '—'}</span>
            <span className="item-time col-time">{formatDateTime(item.logged_at)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
