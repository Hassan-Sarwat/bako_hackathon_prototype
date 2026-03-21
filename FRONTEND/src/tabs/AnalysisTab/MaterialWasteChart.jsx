import { useMemo } from 'react'

const CHART_W = 600
const CHART_H = 260
const BAR_AREA_Y = 30
const BAR_AREA_H = 190
const LABEL_Y = BAR_AREA_Y + BAR_AREA_H + 16
const GROUP_GAP = 24
const BAR_GAP = 4
const BAR_W = 32
const GROUP_W = BAR_W * 2 + BAR_GAP
const COLORS = { expected: '#5b8def', actual: '#c0392b' }

export default function MaterialWasteChart({ data }) {
  const top5 = useMemo(() => {
    return [...data]
      .sort((a, b) => b.estimated_loss_value - a.estimated_loss_value)
      .slice(0, 5)
      .map(m => {
        const expectedRemainingValue = m.expected_remaining * m.unit_price
        const actualRemainingValue = m.current_stock * m.unit_price
        return {
          name: m.material_name,
          expectedValue: Math.max(0, expectedRemainingValue),
          actualValue: Math.max(0, actualRemainingValue),
        }
      })
  }, [data])

  if (top5.length === 0) return null

  const maxVal = Math.max(...top5.flatMap(d => [d.expectedValue, d.actualValue]), 1)
  const totalW = top5.length * GROUP_W + (top5.length - 1) * GROUP_GAP
  const offsetX = (CHART_W - totalW) / 2

  function barH(val) {
    return (val / maxVal) * BAR_AREA_H
  }

  // Y-axis ticks
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => ({
    val: f * maxVal,
    y: BAR_AREA_Y + BAR_AREA_H - f * BAR_AREA_H,
  }))

  return (
    <div className="analysis-chart-container">
      <h3 className="analysis-chart-title">Top 5 Materials — Expected vs Actual Remaining Value</h3>
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H + 30}`} className="analysis-chart-svg">
        {/* grid lines */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={50} y1={t.y} x2={CHART_W - 10} y2={t.y} stroke="var(--border, #e0e0e0)" strokeWidth="1" />
            <text x={46} y={t.y + 4} textAnchor="end" fontSize="10" fill="var(--text, #888)">
              {t.val >= 1000 ? `${(t.val / 1000).toFixed(1)}k` : t.val.toFixed(0)} €
            </text>
          </g>
        ))}

        {/* bars */}
        {top5.map((d, i) => {
          const gx = offsetX + i * (GROUP_W + GROUP_GAP)
          const eh = barH(d.expectedValue)
          const ah = barH(d.actualValue)
          return (
            <g key={i}>
              {/* expected remaining */}
              <rect
                x={gx} y={BAR_AREA_Y + BAR_AREA_H - eh}
                width={BAR_W} height={eh}
                rx={3} fill={COLORS.expected}
              />
              {eh > 14 && (
                <text
                  x={gx + BAR_W / 2} y={BAR_AREA_Y + BAR_AREA_H - eh + 13}
                  textAnchor="middle" fontSize="9" fontWeight="600" fill="#fff"
                >
                  {d.expectedValue.toFixed(0)}€
                </text>
              )}

              {/* actual remaining */}
              <rect
                x={gx + BAR_W + BAR_GAP} y={BAR_AREA_Y + BAR_AREA_H - ah}
                width={BAR_W} height={ah}
                rx={3} fill={COLORS.actual}
              />
              {ah > 14 && (
                <text
                  x={gx + BAR_W + BAR_GAP + BAR_W / 2} y={BAR_AREA_Y + BAR_AREA_H - ah + 13}
                  textAnchor="middle" fontSize="9" fontWeight="600" fill="#fff"
                >
                  {d.actualValue.toFixed(0)}€
                </text>
              )}

              {/* label */}
              <text
                x={gx + GROUP_W / 2} y={LABEL_Y}
                textAnchor="middle" fontSize="11" fontWeight="500" fill="var(--text-h, #333)"
              >
                {d.name.length > 12 ? d.name.slice(0, 11) + '…' : d.name}
              </text>
            </g>
          )
        })}

        {/* legend */}
        <rect x={CHART_W - 200} y={4} width={10} height={10} rx={2} fill={COLORS.expected} />
        <text x={CHART_W - 186} y={13} fontSize="11" fill="var(--text, #888)">Expected Remaining</text>
        <rect x={CHART_W - 80} y={4} width={10} height={10} rx={2} fill={COLORS.actual} />
        <text x={CHART_W - 66} y={13} fontSize="11" fill="var(--text, #888)">Actual</text>
      </svg>
    </div>
  )
}
