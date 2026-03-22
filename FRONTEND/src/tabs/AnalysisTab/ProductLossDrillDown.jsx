function formatAmount(value, unit) {
  if (unit === 'g' && value >= 1000) return `${(value / 1000).toFixed(2)} kg`
  if (unit === 'ml' && value >= 1000) return `${(value / 1000).toFixed(2)} L`
  return `${value.toLocaleString()} ${unit}`
}

export default function ProductLossDrillDown({ entries }) {
  if (entries.length === 0) {
    return <div className="drilldown-empty">Keine Verlustdaten für dieses Produkt im gewählten Zeitraum.</div>
  }

  return (
    <div className="drilldown-content">
      <div className="drilldown-table">
        <div className="drilldown-table-header">
          <span>Material</span>
          <span>Erwarteter Verbrauch</span>
          <span>Anteil (%)</span>
          <span>Zugeordneter Verlust (Menge)</span>
          <span>Zugeordneter Verlust (€)</span>
        </div>
        {entries.map(e => (
          <div key={e.material_id} className="drilldown-table-row">
            <span>{e.material_name}</span>
            <span>{formatAmount(e.expected_usage, e.unit)}</span>
            <span>{e.product_share_pct}%</span>
            <span>{formatAmount(e.attributed_loss_qty, e.unit)}</span>
            <span className={e.attributed_loss_value > 0 ? 'item-loss' : ''}>{e.attributed_loss_value.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
