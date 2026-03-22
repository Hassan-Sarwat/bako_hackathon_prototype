import { useMemo } from 'react'

const CHART_W = 640
const CHART_H = 280
const PAD = { top: 30, right: 20, bottom: 50, left: 55 }
const PLOT_W = CHART_W - PAD.left - PAD.right
const PLOT_H = CHART_H - PAD.top - PAD.bottom

const COLORS = {
  actual: '#3b82f6',
  predicted: '#22c55e',
  confidenceFill: 'rgba(34,197,94,0.12)',
  grid: 'var(--border, #e0e0e0)',
  text: 'var(--text, #888)',
  textH: 'var(--text-h, #333)',
}

function formatDateLabel(iso) {
  const d = new Date(iso + 'T00:00:00')
  return `${d.getDate()}.${d.getMonth() + 1}`
}

export default function SalesChart({ history, predictions }) {
  const { allDates, maxY, actualPoints, predictedPoints, confLower, confUpper } = useMemo(() => {
    const hDates = (history || []).map(h => h.date)
    const pDates = (predictions || []).map(p => p.date)
    const allDates = [...new Set([...hDates, ...pDates])].sort()

    if (allDates.length === 0) return { allDates: [], maxY: 1, actualPoints: [], predictedPoints: [], confLower: [], confUpper: [] }

    const hMap = {}
    for (const h of (history || [])) hMap[h.date] = h.quantity
    const pMap = {}
    for (const p of (predictions || [])) pMap[p.date] = p

    const allValues = [
      ...(history || []).map(h => h.quantity),
      ...(predictions || []).map(p => p.confidence_upper || p.quantity),
    ]
    const maxY = Math.max(...allValues, 10) * 1.1

    const xScale = (i) => PAD.left + (i / Math.max(1, allDates.length - 1)) * PLOT_W
    const yScale = (v) => PAD.top + PLOT_H - (v / maxY) * PLOT_H

    const actualPoints = []
    const predictedPoints = []
    const confLower = []
    const confUpper = []

    allDates.forEach((d, i) => {
      const x = xScale(i)
      if (hMap[d] !== undefined) {
        actualPoints.push({ x, y: yScale(hMap[d]), val: hMap[d], date: d })
      }
      if (pMap[d]) {
        predictedPoints.push({ x, y: yScale(pMap[d].quantity), val: pMap[d].quantity, date: d })
        confLower.push({ x, y: yScale(pMap[d].confidence_lower || pMap[d].quantity) })
        confUpper.push({ x, y: yScale(pMap[d].confidence_upper || pMap[d].quantity) })
      }
    })

    // Connect: add last actual point as first predicted point
    if (actualPoints.length > 0 && predictedPoints.length > 0) {
      const last = actualPoints[actualPoints.length - 1]
      predictedPoints.unshift({ ...last })
      confLower.unshift({ x: last.x, y: last.y })
      confUpper.unshift({ x: last.x, y: last.y })
    }

    return { allDates, maxY, actualPoints, predictedPoints, confLower, confUpper }
  }, [history, predictions])

  if (allDates.length === 0) {
    return <div className="chart-empty">Keine Daten verfügbar</div>
  }

  // Y-axis ticks
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => ({
    val: Math.round(f * maxY),
    y: PAD.top + PLOT_H - f * PLOT_H,
  }))

  // X-axis labels (show every Nth to avoid overlap)
  const step = Math.max(1, Math.ceil(allDates.length / 10))
  const xLabels = allDates.filter((_, i) => i % step === 0 || i === allDates.length - 1)

  function polylineStr(points) {
    return points.map(p => `${p.x},${p.y}`).join(' ')
  }

  // Confidence band polygon
  const confPolygon = confLower.length > 0
    ? [...confUpper, ...confLower.slice().reverse()].map(p => `${p.x},${p.y}`).join(' ')
    : null

  return (
    <div className="sales-chart-container">
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="sales-chart-svg">
        {/* Grid lines */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={PAD.left} y1={t.y} x2={CHART_W - PAD.right} y2={t.y}
              stroke={COLORS.grid} strokeWidth="1" />
            <text x={PAD.left - 8} y={t.y + 4} textAnchor="end"
              fontSize="10" fill={COLORS.text}>
              {t.val}
            </text>
          </g>
        ))}

        {/* Confidence band */}
        {confPolygon && (
          <polygon points={confPolygon} fill={COLORS.confidenceFill} />
        )}

        {/* Actual sales line (blue) */}
        {actualPoints.length > 1 && (
          <polyline
            points={polylineStr(actualPoints)}
            fill="none"
            stroke={COLORS.actual}
            strokeWidth="2.5"
            strokeLinejoin="round"
          />
        )}

        {/* Predicted line (green) */}
        {predictedPoints.length > 1 && (
          <polyline
            points={polylineStr(predictedPoints)}
            fill="none"
            stroke={COLORS.predicted}
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeDasharray="6,3"
          />
        )}

        {/* Actual data points */}
        {actualPoints.map((p, i) => (
          <g key={`a${i}`}>
            <circle cx={p.x} cy={p.y} r="4" fill={COLORS.actual} />
            <title>{p.date}: {p.val} sold</title>
          </g>
        ))}

        {/* Predicted data points (skip first if it's the connecting point) */}
        {predictedPoints.slice(actualPoints.length > 0 ? 1 : 0).map((p, i) => (
          <g key={`p${i}`}>
            <circle cx={p.x} cy={p.y} r="4" fill={COLORS.predicted} />
            <title>{p.date}: {p.val} predicted</title>
          </g>
        ))}

        {/* X-axis labels */}
        {xLabels.map((d, i) => {
          const idx = allDates.indexOf(d)
          const x = PAD.left + (idx / Math.max(1, allDates.length - 1)) * PLOT_W
          return (
            <text key={i} x={x} y={CHART_H - 8}
              textAnchor="middle" fontSize="10" fill={COLORS.text}
              transform={`rotate(-35, ${x}, ${CHART_H - 8})`}>
              {formatDateLabel(d)}
            </text>
          )
        })}

        {/* Legend */}
        <rect x={PAD.left + 4} y={6} width={10} height={10} rx={2} fill={COLORS.actual} />
        <text x={PAD.left + 18} y={15} fontSize="11" fill={COLORS.textH}>Tatsächliche Verkäufe</text>
        <rect x={PAD.left + 150} y={6} width={10} height={10} rx={2} fill={COLORS.predicted} />
        <text x={PAD.left + 164} y={15} fontSize="11" fill={COLORS.textH}>Prognose</text>
      </svg>
    </div>
  )
}
