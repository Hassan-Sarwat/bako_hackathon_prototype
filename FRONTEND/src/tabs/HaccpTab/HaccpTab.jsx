import { useState } from 'react'
import { MOCK_HACCP_GROUPS } from '../../data/mockData'
import ProgressBar from '../../components/ProgressBar/ProgressBar'
import HaccpGroup from './HaccpGroup'
import './HaccpTab.css'

export default function HaccpTab() {
  const [groups, setGroups] = useState(MOCK_HACCP_GROUPS)

  function toggleItem(groupId, itemId) {
    // TODO: POST /api/checklists/items/{id}/complete or /incomplete (when HACCP backed added)
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
  const totalDone = groups.reduce(
    (sum, g) => sum + g.items.filter(i => i.is_complete).length,
    0
  )
  const pct = Math.round((totalDone / totalItems) * 100)

  return (
    <div className="haccp-tab">
      <div className="haccp-overview">
        <div className="haccp-overview-text">
          <h2 className="haccp-overview-title">HACCP Compliance</h2>
          <p className="haccp-overview-sub">
            Hazard Analysis &amp; Critical Control Points — {totalDone}/{totalItems} checks complete
          </p>
        </div>
        <span className={`haccp-pct-badge ${pct === 100 ? 'haccp-pct-badge--complete' : ''}`}>
          {pct}%
        </span>
      </div>

      <ProgressBar completed={totalDone} total={totalItems} />

      <div className="haccp-groups">
        {groups.map(group => (
          <HaccpGroup key={group.id} group={group} onToggle={toggleItem} />
        ))}
      </div>
    </div>
  )
}
