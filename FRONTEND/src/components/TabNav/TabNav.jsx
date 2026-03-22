import './TabNav.css'

const TABS = [
  { id: 'dashboard',    label: 'Startseite'   },
  { id: 'tickets',      label: 'Tickets'      },
  { id: 'inventory',    label: 'Lager'        },
  { id: 'cleaning',     label: 'Reinigung'    },
  { id: 'haccp',        label: 'HACCP'        },
  { id: 'schedule',     label: 'Dienstplan'   },
  { id: 'products',     label: 'Produkte'     },
  { id: 'purchases',    label: 'Einkauf'      },
  { id: 'cooking-plan',     label: 'Backplan'      },
  { id: 'prediction-plan',  label: 'Prognose'      },
  { id: 'analysis',         label: 'Analyse'       },
]

export default function TabNav({ activeTab, onTabChange }) {
  return (
    <nav className="tab-nav" role="tablist" aria-label="Dashboard sections">
      {TABS.map(tab => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          className={`tab-btn ${activeTab === tab.id ? 'tab-btn--active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
