import { useState, useEffect } from 'react'
import {
  fetchChecklistItems,
  fetchCleaningTasks,
  markChecklistComplete,
  markChecklistIncomplete,
  markCleaningComplete,
  markCleaningIncomplete,
} from '../../api'
import ProgressBar from '../../components/ProgressBar/ProgressBar'
import ChecklistRow from '../../components/ChecklistRow/ChecklistRow'
import './CleaningTab.css'

export default function CleaningTab() {
  const [sanitation, setSanitation] = useState([])
  const [cleaning, setCleaning] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeFilter, setActiveFilter] = useState('all')

  useEffect(() => {
    Promise.all([fetchChecklistItems('sanitation'), fetchCleaningTasks()])
      .then(([sanitationItems, cleaningTasks]) => {
        setSanitation(sanitationItems)
        setCleaning(cleaningTasks)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  function toggleSanitation(id) {
    const item = sanitation.find(i => i.id === id)
    const apiFn = item.is_complete ? markChecklistIncomplete : markChecklistComplete
    setSanitation(prev => prev.map(i => i.id === id ? { ...i, is_complete: !i.is_complete } : i))
    apiFn(id).catch(() => {
      setSanitation(prev => prev.map(i => i.id === id ? { ...i, is_complete: item.is_complete } : i))
    })
  }

  function toggleCleaning(id) {
    const task = cleaning.find(t => t.id === id)
    const apiFn = task.is_complete ? markCleaningIncomplete : markCleaningComplete
    setCleaning(prev => prev.map(t => t.id === id ? { ...t, is_complete: !t.is_complete } : t))
    apiFn(id).catch(() => {
      setCleaning(prev => prev.map(t => t.id === id ? { ...t, is_complete: task.is_complete } : t))
    })
  }

  if (loading) return <div className="tab-status">Loading cleaning tasks…</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  // Derive sections dynamically from available data
  const sections = [
    { id: 'sanitation', label: 'Sanitation Checklist', items: sanitation, toggleFn: toggleSanitation, areaLabel: false },
    { id: 'cleaning',   label: 'Daily Cleaning Tasks',  items: cleaning,   toggleFn: toggleCleaning,  areaLabel: true  },
  ].filter(s => s.items.length > 0)

  const sanitationDone = sanitation.filter(i => i.is_complete).length
  const cleaningDone   = cleaning.filter(i => i.is_complete).length
  const totalDone = sanitationDone + cleaningDone
  const totalAll  = sanitation.length + cleaning.length

  const visibleSections = activeFilter === 'all'
    ? sections
    : sections.filter(s => s.id === activeFilter)

  return (
    <div className="cleaning-tab">
      <div className="cleaning-overall">
        <ProgressBar completed={totalDone} total={totalAll} label="Overall Progress" />
      </div>

      <div className="section-filter-bar" role="tablist" aria-label="Filter sections">
        <button
          role="tab"
          aria-selected={activeFilter === 'all'}
          className={`section-filter-btn ${activeFilter === 'all' ? 'section-filter-btn--active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All
        </button>
        {sections.map(s => (
          <button
            key={s.id}
            role="tab"
            aria-selected={activeFilter === s.id}
            className={`section-filter-btn ${activeFilter === s.id ? 'section-filter-btn--active' : ''}`}
            onClick={() => setActiveFilter(s.id)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {visibleSections.map(section => {
        const done = section.items.filter(i => i.is_complete).length
        return (
          <section key={section.id} className="cleaning-section">
            <div className="cleaning-section-header">
              <h2>{section.label}</h2>
              <ProgressBar completed={done} total={section.items.length} />
            </div>
            <div className="cleaning-list">
              {section.items.map(item => (
                <ChecklistRow
                  key={item.id}
                  item={section.areaLabel ? { ...item, item_name: item.action } : item}
                  onToggle={section.toggleFn}
                  areaLabel={section.areaLabel}
                />
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
