import { useMemo } from 'react'

const CHART_H = 260
const BAR_AREA_Y = 30
const BAR_AREA_H = 190
const LABEL_Y = BAR_AREA_Y + BAR_AREA_H + 16
const BAR_GAP = 3
const GROUP_GAP = 14
const COLORS = { expected: '#5b8def', actual: '#c0392b' }

const WEEKDAYS = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']

function formatDayLabel(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const wd = WEEKDAYS[d.getDay()]
  return `${wd} ${d.getDate()}.`
}

export default function DailyLossTrendChart({ data }) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return null

    const maxVal = Math.max(
      ...data.flatMap(d => [d.expected_cost, d.actual_cost]),
      1
    )
    const barW = Math.max(10, Math.min(32, 500 / (data.length * 2.5)))
    const groupW = barW * 2 + BAR_GAP
    const totalW = data.length * groupW + (data.length - 1) * GROUP_GAP
    const chartW = Math.max(totalW + 100, 400)
    const offsetX = (chartW - totalW) / 2

    return { maxVal, barW, groupW, totalW, chartW, offsetX }
  }, [data])

  if (!chartData || !data || data.length === 0) return null

  const { maxVal, barW, groupW, chartW, offsetX } = chartData

  function barH(val) {
    return (val / maxVal) * BAR_AREA_H
  }

  const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => ({
    val: f * maxVal,
    y: BAR_AREA_Y + BAR_AREA_H - f * BAR_AREA_H,
  }))

  return (
    <div className="analysis-chart-container analysis-chart-container--trend">
      <h3 className="analysis-chart-title">Tagesverlauf</h3>
      <svg viewBox={`0 0 ${chartW} ${CHART_H + 30}`} className="analysis-chart-svg">
        {/* grid lines */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={50} y1={t.y} x2={chartW - 10} y2={t.y} stroke="var(--border, #e0e0e0)" strokeWidth="1" />
            <text x={46} y={t.y + 4} textAnchor="end" fontSize="10" fill="var(--text, #888)">
              {t.val >= 1000 ? `${(t.val / 1000).toFixed(1)}k` : t.val.toFixed(0)} €
            </text>
          </g>
        ))}

        {/* bars */}
        {data.map((d, i) => {
          const gx = offsetX + i * (groupW + GROUP_GAP)
          const eh = barH(d.expected_cost)
          const ah = barH(d.actual_cost)
          return (
            <g key={i}>
              <rect
                x={gx} y={BAR_AREA_Y + BAR_AREA_H - eh}
                width={barW} height={eh}
                rx={3} fill={COLORS.expected}
              >
                <title>Erwartet: {d.expected_cost.toFixed(2)} €</title>
              </rect>
              <rect
                x={gx + barW + BAR_GAP} y={BAR_AREA_Y + BAR_AREA_H - ah}
                width={barW} height={ah}
                rx={3} fill={COLORS.actual}
              >
                <title>Tatsächlich: {d.actual_cost.toFixed(2)} €</title>
              </rect>
              <text
                x={gx + groupW / 2} y={LABEL_Y}
                textAnchor="middle" fontSize="10" fontWeight="500" fill="var(--text-h, #333)"
              >
                {formatDayLabel(d.date)}
              </text>
            </g>
          )
        })}

        {/* legend */}
        <rect x={chartW - 220} y={4} width={10} height={10} rx={2} fill={COLORS.expected} />
        <text x={chartW - 206} y={13} fontSize="11" fill="var(--text, #888)">Erwartet</text>
        <rect x={chartW - 130} y={4} width={10} height={10} rx={2} fill={COLORS.actual} />
        <text x={chartW - 116} y={13} fontSize="11" fill="var(--text, #888)">Tatsächlich</text>
      </svg>
    </div>
  )
}
