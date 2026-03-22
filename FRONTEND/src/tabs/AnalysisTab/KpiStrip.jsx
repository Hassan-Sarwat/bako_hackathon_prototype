export default function KpiStrip({ totalLoss, previousLoss, flaggedCount, trackedCount }) {
  let trendText = null
  if (previousLoss != null && previousLoss > 0) {
    const pct = ((totalLoss - previousLoss) / previousLoss * 100).toFixed(1)
    const up = totalLoss > previousLoss
    trendText = (
      <span className={`kpi-trend ${up ? 'kpi-trend--up' : 'kpi-trend--down'}`}>
        {up ? '▲' : '▼'} {Math.abs(pct)}% ggü. Vorwoche
      </span>
    )
  }

  return (
    <div className="kpi-strip">
      <div className="kpi-card kpi-card--hero">
        <span className="kpi-label">Gesamtverlust</span>
        <span className="kpi-value kpi-value--loss">{totalLoss.toFixed(2)} €</span>
        {trendText}
      </div>
      <div className="kpi-card">
        <span className="kpi-label">Auffällige Materialien</span>
        <span className={`kpi-value ${flaggedCount > 0 ? 'kpi-value--loss' : ''}`}>{flaggedCount}</span>
      </div>
      <div className="kpi-card">
        <span className="kpi-label">Erfasste Materialien</span>
        <span className="kpi-value">{trackedCount}</span>
      </div>
    </div>
  )
}
