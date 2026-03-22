import { useMemo } from 'react'

const SIZE = 260
const CX = SIZE / 2
const CY = SIZE / 2
const R_OUTER = 100
const R_INNER = 60
const COLORS = ['#c0392b', '#e67e22', '#f1c40f', '#27ae60', '#2980b9', '#8e44ad', '#1abc9c', '#d35400']

function polarToXY(cx, cy, r, angleDeg) {
  const rad = (angleDeg - 90) * Math.PI / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

export default function LossDistributionDonut({ data, totalLoss }) {
  const slices = useMemo(() => {
    if (!data || data.length === 0 || totalLoss <= 0) return []

    // Top 6 + Sonstige bucket
    const sorted = [...data]
      .filter(m => m.estimated_loss_value > 0)
      .sort((a, b) => b.estimated_loss_value - a.estimated_loss_value)

    const top = sorted.slice(0, 6)
    const rest = sorted.slice(6)
    const restValue = rest.reduce((s, m) => s + m.estimated_loss_value, 0)

    const items = top.map(m => ({ name: m.material_name, value: m.estimated_loss_value }))
    if (restValue > 0) {
      items.push({ name: 'Sonstige', value: restValue })
    }

    let angle = 0
    return items.map((item, i) => {
      const pct = item.value / totalLoss
      const sweep = pct * 360
      const startAngle = angle
      angle += sweep
      return { ...item, pct, startAngle, sweep, color: COLORS[i % COLORS.length] }
    })
  }, [data, totalLoss])

  if (slices.length === 0) return null

  function donutPath(startAngle, sweep) {
    if (sweep >= 359.99) {
      const ao = polarToXY(CX, CY, R_OUTER, 0)
      const bo = polarToXY(CX, CY, R_OUTER, 180)
      const ai = polarToXY(CX, CY, R_INNER, 0)
      const bi = polarToXY(CX, CY, R_INNER, 180)
      return `M ${ao.x} ${ao.y} A ${R_OUTER} ${R_OUTER} 0 1 1 ${bo.x} ${bo.y} A ${R_OUTER} ${R_OUTER} 0 1 1 ${ao.x} ${ao.y} ` +
        `M ${ai.x} ${ai.y} A ${R_INNER} ${R_INNER} 0 1 0 ${bi.x} ${bi.y} A ${R_INNER} ${R_INNER} 0 1 0 ${ai.x} ${ai.y} Z`
    }
    const os = polarToXY(CX, CY, R_OUTER, startAngle)
    const oe = polarToXY(CX, CY, R_OUTER, startAngle + sweep)
    const is_ = polarToXY(CX, CY, R_INNER, startAngle + sweep)
    const ie = polarToXY(CX, CY, R_INNER, startAngle)
    const large = sweep > 180 ? 1 : 0
    return `M ${os.x} ${os.y} A ${R_OUTER} ${R_OUTER} 0 ${large} 1 ${oe.x} ${oe.y} ` +
      `L ${is_.x} ${is_.y} A ${R_INNER} ${R_INNER} 0 ${large} 0 ${ie.x} ${ie.y} Z`
  }

  return (
    <div className="analysis-chart-container analysis-chart-container--donut">
      <h3 className="analysis-chart-title">Verlustverteilung</h3>
      <div className="pie-chart-layout">
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="pie-chart-svg">
          {slices.map((s, i) => (
            <path key={i} d={donutPath(s.startAngle, s.sweep)} fill={s.color} stroke="var(--bg, #fff)" strokeWidth="2" fillRule="evenodd">
              <title>{s.name}: {s.value.toFixed(2)} € ({(s.pct * 100).toFixed(1)}%)</title>
            </path>
          ))}
          {/* center text */}
          <text x={CX} y={CY - 6} textAnchor="middle" fontSize="10" fontWeight="600" fill="var(--text, #888)">Gesamt</text>
          <text x={CX} y={CY + 14} textAnchor="middle" fontSize="16" fontWeight="700" fill="var(--text-h, #333)">{totalLoss.toFixed(2)} €</text>
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
