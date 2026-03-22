import { useState } from 'react'
import { MOCK_HACCP_GROUPS } from '../../data/mockData'
import ProgressBar from '../../components/ProgressBar/ProgressBar'
import HaccpGroup from './HaccpGroup'
import './HaccpTab.css'

export default function HaccpTab() {
  const [groups, setGroups] = useState(MOCK_HACCP_GROUPS)
  const [activeFilter, setActiveFilter] = useState('all')

  function toggleItem(groupId, itemId) {
    // TODO: POST /api/checklists/items/{id}/complete or /incomplete (when HACCP backend added)
    setGroups(prev =>
      prev.map(g =>
        g.id === groupId
          ? {
              ...g,
              items: g.items.map(item =>
                item.id === itemId
                  ? { ...item, is_complete: !item.is_complete }
                  : item
              ),
            }
          : g
      )
    )
  }

  const totalItems = groups.reduce((sum, g) => sum + g.items.length, 0)
  const totalDone  = groups.reduce(
    (sum, g) => sum + g.items.filter(i => i.is_complete).length, 0
  )
  const pct = Math.round((totalDone / totalItems) * 100)

  // Derive categories dynamically from groups
  const categories = groups.map(g => ({ id: g.id, label: g.category }))

  const visibleGroups = activeFilter === 'all'
    ? groups
    : groups.filter(g => g.id === activeFilter)

  return (
    <div className="haccp-tab">
      <div className="haccp-overview">
        <div className="haccp-overview-text">
          <h2 className="haccp-overview-title">HACCP-Kontrolle</h2>
          <p className="haccp-overview-sub">
            Hazard Analysis &amp; Critical Control Points — {totalDone}/{totalItems} Prüfungen abgeschlossen
          </p>
        </div>
        <span className={`haccp-pct-badge ${pct === 100 ? 'haccp-pct-badge--complete' : ''}`}>
          {pct}%
        </span>
      </div>

      <ProgressBar completed={totalDone} total={totalItems} />

      <div className="section-filter-bar" role="tablist" aria-label="Filter HACCP categories">
        <button
          role="tab"
          aria-selected={activeFilter === 'all'}
          className={`section-filter-btn ${activeFilter === 'all' ? 'section-filter-btn--active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          Alle
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            role="tab"
            aria-selected={activeFilter === cat.id}
            className={`section-filter-btn ${activeFilter === cat.id ? 'section-filter-btn--active' : ''}`}
            onClick={() => setActiveFilter(cat.id)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <div className="haccp-groups">
        {visibleGroups.map(group => (
          <HaccpGroup key={group.id} group={group} onToggle={toggleItem} />
        ))}
      </div>
    </div>
  )
}
