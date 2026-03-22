import { useState, useEffect, useMemo } from 'react'
import {
  fetchMaterialUsageAnalysis,
  fetchProductLossAnalysis,
  fetchDailyLossTrend,
  fetchLossComparison,
} from '../../api'
import KpiStrip from './KpiStrip'
import DailyLossTrendChart from './DailyLossTrendChart'
import LossDistributionDonut from './LossDistributionDonut'
import MaterialUsagePanel from './MaterialUsagePanel'
import ProductLossPanel from './ProductLossPanel'
import './AnalysisTab.css'

function toISO(d) {
  return d.toISOString().slice(0, 10)
}

export default function AnalysisTab() {
  const today = useMemo(() => new Date(), [])
  const weekAgo = useMemo(() => {
    const d = new Date(today)
    d.setDate(d.getDate() - 7)
    return d
  }, [today])

  const [startDate, setStartDate] = useState(toISO(weekAgo))
  const [endDate, setEndDate] = useState(toISO(today))

  const [materialData, setMaterialData] = useState([])
  const [productData, setProductData] = useState([])
  const [trendData, setTrendData] = useState([])
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [activeView, setActiveView] = useState('material')

  function load() {
    setLoading(true)
    setError(null)

    const params = { start_date: startDate, end_date: endDate }

    Promise.all([
      fetchMaterialUsageAnalysis(params),
      fetchProductLossAnalysis(params),
      fetchDailyLossTrend(params),
      fetchLossComparison(params),
    ])
      .then(([materials, products, trend, comp]) => {
        setMaterialData(materials)
        setProductData(products)
        setTrendData(trend)
        setComparison(comp)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const totalLoss = materialData.reduce((sum, m) => sum + m.estimated_loss_value, 0)
  const flaggedCount = materialData.filter(m => m.flagged).length

  return (
    <div className="analysis-tab">
      {/* Toolbar */}
      <div className="analysis-toolbar">
        <label>
          Von
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
        </label>
        <label>
          Bis
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
        </label>
        <button className="btn-analyze" onClick={load}>Analysieren</button>
      </div>

      {loading && <div className="tab-status">Analyse wird geladen…</div>}
      {error && <div className="tab-status tab-status--error">Fehler: {error}</div>}

      {!loading && !error && materialData.length > 0 && (
        <>
          {/* KPI Strip */}
          <KpiStrip
            totalLoss={totalLoss}
            previousLoss={comparison?.previous_total_loss}
            flaggedCount={flaggedCount}
            trackedCount={materialData.length}
          />

          {/* Charts row */}
          <div className="analysis-charts-row">
            <DailyLossTrendChart data={trendData} />
            <LossDistributionDonut data={materialData} totalLoss={totalLoss} />
          </div>

          {/* Table view toggle */}
          <div className="table-section">
            <nav className="table-view-toggle" role="tablist">
              <button
                role="tab"
                aria-selected={activeView === 'material'}
                className={`analysis-panel-btn ${activeView === 'material' ? 'analysis-panel-btn--active' : ''}`}
                onClick={() => setActiveView('material')}
              >
                Nach Material
              </button>
              <button
                role="tab"
                aria-selected={activeView === 'product'}
                className={`analysis-panel-btn ${activeView === 'product' ? 'analysis-panel-btn--active' : ''}`}
                onClick={() => setActiveView('product')}
              >
                Nach Produkt
              </button>
            </nav>

            {activeView === 'material' && (
              <MaterialUsagePanel data={materialData} startDate={startDate} endDate={endDate} />
            )}
            {activeView === 'product' && (
              <ProductLossPanel data={productData} startDate={startDate} endDate={endDate} />
            )}
          </div>
        </>
      )}

      {!loading && !error && materialData.length === 0 && (
        <div className="analysis-empty">
          Keine Analysedaten für den gewählten Zeitraum gefunden.
          Stellen Sie sicher, dass Backpläne und Produktmaterialien konfiguriert sind.
        </div>
      )}
    </div>
  )
}
