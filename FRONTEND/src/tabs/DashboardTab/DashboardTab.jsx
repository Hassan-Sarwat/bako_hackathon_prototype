import { useState, useEffect } from 'react'
import { fetchDashboard } from '../../api'
import { MOCK_HACCP_GROUPS } from '../../data/mockData'
import './DashboardTab.css'

const HACCP_TOTAL = MOCK_HACCP_GROUPS.reduce((s, g) => s + g.items.length, 0)
const HACCP_DONE  = MOCK_HACCP_GROUPS.reduce(
  (s, g) => s + g.items.filter(i => i.is_complete).length, 0
)

const CARDS = [
  { id: 'tickets',   label: 'Tickets',   desc: 'Offene Meldungen vom Personal',      accent: 'urgent' },
  { id: 'inventory', label: 'Lager',     desc: 'Zutatenbestand',                     accent: 'high'   },
  { id: 'cleaning',  label: 'Reinigung', desc: 'Hygiene & tägliche Reinigung',       accent: 'normal' },
  { id: 'haccp',     label: 'HACCP',     desc: 'Lebensmittelsicherheit',             accent: 'low'    },
]

function getStat(id, summary) {
  if (!summary) return null
  if (id === 'tickets') {
    const tickets = summary.tickets ?? []
    const urgent = tickets.filter(t => t.urgency === 'urgent').length
    const high   = tickets.filter(t => t.urgency === 'high').length
    const alert  = urgent > 0 ? `${urgent} dringend` : high > 0 ? `${high} hoch` : null
    return { main: `${tickets.length} open`, alert, alertLevel: urgent > 0 ? 'urgent' : 'high' }
  }
  if (id === 'inventory') {
    const items    = summary.inventory?.items ?? []
    const critical = items.filter(i => i.count <= 3).length
    const low      = items.filter(i => i.count > 3 && i.count <= 8).length
    const alert    = critical > 0 ? `${critical} kritisch` : low > 0 ? `${low} niedrig` : null
    return { main: `${items.length} items`, alert, alertLevel: 'urgent' }
  }
  if (id === 'cleaning') {
    const san   = summary.sanitation ?? { completed: 0, total: 0 }
    const cln   = summary.cleaning   ?? { completed: 0, total: 0 }
    const done  = san.completed + cln.completed
    const total = san.total + cln.total
    const pct   = total > 0 ? Math.round((done / total) * 100) : 0
    return { main: `${pct}% erledigt`, sub: `${done} / ${total} Aufgaben` }
  }
  if (id === 'haccp') {
    const pct = HACCP_TOTAL > 0 ? Math.round((HACCP_DONE / HACCP_TOTAL) * 100) : 0
    return { main: `${pct}% compliant`, sub: `${HACCP_DONE} / ${HACCP_TOTAL} Prüfungen` }
  }
  return null
}

export default function DashboardTab({ onNavigate }) {
  const [summary, setSummary] = useState(null)

  useEffect(() => {
    fetchDashboard()
      .then(setSummary)
      .catch(() => {})
  }, [])

  return (
    <div className="dashboard-tab">
      <div className="dashboard-welcome">
        <h2 className="dashboard-welcome-title">Betriebsübersicht</h2>
        <p className="dashboard-welcome-sub">Bereich auswählen für Details</p>
      </div>

      <div className="dashboard-cards">
        {CARDS.map(card => {
          const stat = getStat(card.id, summary)
          return (
            <button
              key={card.id}
              className={`dashboard-card dashboard-card--${card.accent}`}
              onClick={() => onNavigate(card.id)}
            >
              <div className="dashboard-card-body">
                <h3 className="dashboard-card-label">{card.label}</h3>
                <p className="dashboard-card-desc">{card.desc}</p>
                {stat && (
                  <div className="dashboard-card-stats">
                    <span className="dashboard-card-main">{stat.main}</span>
                    {stat.sub && (
                      <span className="dashboard-card-sub">{stat.sub}</span>
                    )}
                    {stat.alert && (
                      <span className={`dashboard-card-alert dashboard-card-alert--${stat.alertLevel}`}>
                        {stat.alert}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <span className="dashboard-card-arrow" aria-hidden="true">→</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
