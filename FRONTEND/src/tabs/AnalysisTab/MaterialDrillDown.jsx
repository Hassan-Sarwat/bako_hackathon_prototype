import { useMemo } from 'react'

function formatAmount(value, unit) {
  if (unit === 'g' && value >= 1000) return `${(value / 1000).toFixed(2)} kg`
  if (unit === 'ml' && value >= 1000) return `${(value / 1000).toFixed(2)} L`
  return `${value.toLocaleString()} ${unit}`
}

export default function MaterialDrillDown({ entries, unit }) {
  const grouped = useMemo(() => {
    const map = {}
    for (const e of entries) {
      if (!map[e.plan_date]) map[e.plan_date] = []
      map[e.plan_date].push(e)
    }
    return Object.entries(map).sort((a, b) => b[0].localeCompare(a[0]))
  }, [entries])

  if (entries.length === 0) {
    return <div className="drilldown-empty">Keine Backpläne für dieses Material im gewählten Zeitraum.</div>
  }

  return (
    <div className="drilldown-content">
      {grouped.map(([date, items]) => {
        const dayTotal = items.reduce((s, e) => s + e.total_usage, 0)
        return (
          <div key={date} className="drilldown-day">
            <div className="drilldown-day-header">
              <span className="drilldown-date">{date}</span>
              <span className="drilldown-day-total">Gesamt: {formatAmount(dayTotal, unit)}</span>
            </div>
            <div className="drilldown-table">
              <div className="drilldown-table-header">
                <span>Produkt</span>
                <span>Anz.</span>
                <span>Pro Stück</span>
                <span>Gesamtverbrauch</span>
              </div>
              {items.map((e, i) => (
                <div key={i} className="drilldown-table-row">
                  <span>{e.product_name}</span>
                  <span>{e.quantity}</span>
                  <span>{e.amount_per_unit}</span>
                  <span>{formatAmount(e.total_usage, unit)}</span>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
