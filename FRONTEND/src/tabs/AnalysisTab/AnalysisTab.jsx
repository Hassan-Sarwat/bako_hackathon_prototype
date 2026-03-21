import { useState } from 'react'
import MaterialUsagePanel from './MaterialUsagePanel'
import ProductLossPanel from './ProductLossPanel'
import './AnalysisTab.css'

const PANELS = [
  { id: 'material-usage', label: 'Material Usage' },
  { id: 'product-loss', label: 'Product Loss' },
]

export default function AnalysisTab() {
  const [activePanel, setActivePanel] = useState('material-usage')

  return (
    <div className="analysis-tab">
      <nav className="analysis-panels" role="tablist">
        {PANELS.map(p => (
          <button
            key={p.id}
            role="tab"
            aria-selected={activePanel === p.id}
            className={`analysis-panel-btn ${activePanel === p.id ? 'analysis-panel-btn--active' : ''}`}
            onClick={() => setActivePanel(p.id)}
          >
            {p.label}
          </button>
        ))}
      </nav>

      {activePanel === 'material-usage' && <MaterialUsagePanel />}
      {activePanel === 'product-loss' && <ProductLossPanel />}
    </div>
  )
}
