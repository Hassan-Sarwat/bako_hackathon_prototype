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
  if (cls === 'stock-critical') return 'Kritisch'
  if (cls === 'stock-low') return 'Niedrig'
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

  if (loading) return <div className="tab-status">Lager wird geladen...</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  const criticalCount = items.filter(i => stockClass(i.count, i.unit) === 'stock-critical').length
  const lowCount = items.filter(i => stockClass(i.count, i.unit) === 'stock-low').length
  const shortages = needs.filter(n => n.has_shortage)

  // Build a lookup from material name to needs data
  const needsByName = {}
  for (const n of needs) {
    needsByName[n.material_name] = n
  }

  // Sort by urgency: critical > low > ok, then by % stock remaining after needs
  const statusPriority = { 'stock-critical': 0, 'stock-low': 1, 'stock-ok': 2 }

  const sortedItems = [...items].sort((a, b) => {
    const aCls = stockClass(a.count, a.unit)
    const bCls = stockClass(b.count, b.unit)

    // 1) Status urgency first
    if (statusPriority[aCls] !== statusPriority[bCls]) {
      return statusPriority[aCls] - statusPriority[bCls]
    }

    // 2) % of stock remaining after forecast needs (lower remaining = higher urgency)
    const aNeed = needsByName[a.item_name]
    const bNeed = needsByName[b.item_name]
    const aRemainPct = aNeed && aNeed.needed > 0
      ? (a.count - aNeed.needed) / a.count
      : 1 // no forecast data = assume safe
    const bRemainPct = bNeed && bNeed.needed > 0
      ? (b.count - bNeed.needed) / b.count
      : 1
    return aRemainPct - bRemainPct
  })

  // Items where stock covers the 3-day need but leaves <=20% remaining
  function isRunningLow(item) {
    const need = needsByName[item.item_name]
    if (!need || need.needed <= 0 || need.has_shortage) return false
    const remainPct = (item.count - need.needed) / item.count
    return remainPct <= 0.2
  }

  return (
    <div className="inventory-tab">
      <div className="inventory-summary">
        <span><strong>{items.length}</strong> Zutaten erfasst</span>
        {criticalCount > 0 && (
          <span className="summary-critical">{criticalCount} kritisch</span>
        )}
        {lowCount > 0 && (
          <span className="summary-low">{lowCount} niedrig</span>
        )}
        {shortages.length > 0 && (
          <span className="summary-shortage">{shortages.length} {shortages.length > 1 ? 'Engpässe' : 'Engpass'} (3-Tage-Prognose)</span>
        )}
      </div>

      <div className="inventory-grid">
        <div className="inventory-header">
          <span>Zutat</span>
          <span>Bestand</span>
          <span>Status</span>
          <span>Bedarf</span>
          <span>Engpass</span>
          <span className="col-price">Letzter Preis</span>
          <span>Erfasst von</span>
          <span className="col-time">Datum / Uhrzeit</span>
        </div>
        {sortedItems.map(item => {
          const need = needsByName[item.item_name]
          const runningLow = isRunningLow(item)
          const remainPct = need && need.needed > 0
            ? Math.round(((item.count - need.needed) / item.count) * 100)
            : null
          return (
            <div key={item.id} className={`inventory-row ${need?.has_shortage ? 'inventory-row--shortage' : ''} ${runningLow ? 'inventory-row--running-low' : ''}`}>
              <span className="item-name">{item.item_name}</span>
              <span className={`item-count ${stockClass(item.count, item.unit)}`}>
                {formatAmount(item.count, item.unit)}
              </span>
              <span className={`item-status ${stockClass(item.count, item.unit)}`}>
                {stockLabel(item.count, item.unit)}
              </span>
              <span className="item-needed">
                {need ? formatAmount(need.needed, need.unit) : '—'}
              </span>
              <span className={`item-shortage ${need?.has_shortage ? 'val-shortage' : ''}`}>
                {need?.has_shortage
                  ? formatAmount(need.shortage, need.unit)
                  : runningLow
                    ? <span className="val-running-low">{remainPct}% übrig nach</span>
                    : '—'}
              </span>
              <span className="item-last-price col-price">
                {item.last_purchase_price != null
                  ? <>{item.last_purchase_price.toFixed(2)} <span className="price-amount">({item.last_purchase_amount})</span></>
                  : '—'}
              </span>
              <span className="item-staff">{item.logged_by ?? '—'}</span>
              <span className="item-time col-time">{formatDateTime(item.logged_at)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
