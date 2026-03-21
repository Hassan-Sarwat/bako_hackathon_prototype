import { useMemo } from 'react'

const SIZE = 260
const CX = SIZE / 2
const CY = SIZE / 2
const R = 100
const COLORS = ['#c0392b', '#e67e22', '#f1c40f', '#27ae60', '#2980b9', '#8e44ad', '#1abc9c', '#d35400']

function polarToXY(cx, cy, r, angleDeg) {
  const rad = (angleDeg - 90) * Math.PI / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

export default function ProductLossPieChart({ data }) {
  const slices = useMemo(() => {
    const totalLoss = data.reduce((s, p) => s + p.attributed_loss_value, 0)
    if (totalLoss <= 0) return []

    let angle = 0
    return data
      .filter(p => p.attributed_loss_value > 0)
      .sort((a, b) => b.attributed_loss_value - a.attributed_loss_value)
      .map((p, i) => {
        const pct = p.attributed_loss_value / totalLoss
        const sweep = pct * 360
        const startAngle = angle
        angle += sweep
        return {
          name: p.product_name,
          value: p.attributed_loss_value,
          pct,
          startAngle,
          sweep,
          color: COLORS[i % COLORS.length],
        }
      })
  }, [data])

  if (slices.length === 0) return null

  function slicePath(startAngle, sweep) {
    if (sweep >= 359.99) {
      // full circle
      const a = polarToXY(CX, CY, R, 0)
      const b = polarToXY(CX, CY, R, 180)
      return `M ${a.x} ${a.y} A ${R} ${R} 0 1 1 ${b.x} ${b.y} A ${R} ${R} 0 1 1 ${a.x} ${a.y} Z`
    }
    const start = polarToXY(CX, CY, R, startAngle)
    const end = polarToXY(CX, CY, R, startAngle + sweep)
    const large = sweep > 180 ? 1 : 0
    return `M ${CX} ${CY} L ${start.x} ${start.y} A ${R} ${R} 0 ${large} 1 ${end.x} ${end.y} Z`
  }

  return (
    <div className="analysis-chart-container">
      <h3 className="analysis-chart-title">Product Loss Distribution</h3>
      <div className="pie-chart-layout">
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="pie-chart-svg">
          {slices.map((s, i) => (
            <path key={i} d={slicePath(s.startAngle, s.sweep)} fill={s.color} stroke="var(--bg, #fff)" strokeWidth="2">
              <title>{s.name}: {s.value.toFixed(2)} € ({(s.pct * 100).toFixed(1)}%)</title>
            </path>
          ))}
        </svg>
        <div className="pie-chart-legend">
          {slices.map((s, i) => (
            <div key={i} className="pie-legend-item">
              <span className="pie-legend-swatch" style={{ background: s.color }} />
              <span className="pie-legend-label">{s.name}</span>
              <span className="pie-legend-value">{s.value.toFixed(2)} € ({(s.pct * 100).toFixed(1)}%)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
