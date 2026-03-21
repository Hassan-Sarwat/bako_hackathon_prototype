import './TabNav.css'

const TABS = [
  { id: 'dashboard', label: 'Home'      },
  { id: 'tickets',   label: 'Tickets'   },
  { id: 'inventory', label: 'Inventory' },
  { id: 'cleaning',  label: 'Cleaning'  },
  { id: 'haccp',     label: 'HACCP'     },
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
