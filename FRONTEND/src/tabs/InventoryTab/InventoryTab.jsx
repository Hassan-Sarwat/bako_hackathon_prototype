import { MOCK_INVENTORY } from '../../data/mockData'
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

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function InventoryTab() {
  const lastUpdated = MOCK_INVENTORY.reduce((latest, item) =>
    item.logged_at > latest ? item.logged_at : latest,
    MOCK_INVENTORY[0].logged_at
  )

  const criticalCount = MOCK_INVENTORY.filter(i => i.count <= 3).length
  const lowCount = MOCK_INVENTORY.filter(i => i.count > 3 && i.count <= 8).length

  return (
    <div className="inventory-tab">
      <div className="inventory-summary">
        <span><strong>{MOCK_INVENTORY.length}</strong> ingredients tracked</span>
        {criticalCount > 0 && (
          <span className="summary-critical">{criticalCount} critical</span>
        )}
        {lowCount > 0 && (
          <span className="summary-low">{lowCount} low</span>
        )}
        <span className="summary-updated">Last logged {formatTime(lastUpdated)}</span>
      </div>

      <div className="inventory-grid">
        <div className="inventory-header">
          <span>Ingredient</span>
          <span>Count</span>
          <span>Status</span>
          <span>Logged by</span>
          <span className="col-time">Time</span>
        </div>
        {MOCK_INVENTORY.map(item => (
          <div key={item.id} className="inventory-row">
            <span className="item-name">{item.item_name}</span>
            <span className={`item-count ${stockClass(item.count)}`}>
              {item.count}
            </span>
            <span className={`item-status ${stockClass(item.count)}`}>
              {stockLabel(item.count)}
            </span>
            <span className="item-staff">{item.logged_by}</span>
            <span className="item-time col-time">{formatTime(item.logged_at)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
