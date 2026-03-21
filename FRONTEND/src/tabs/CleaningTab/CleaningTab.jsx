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
    // Optimistic update
    setSanitation(prev => prev.map(i => i.id === id ? { ...i, is_complete: !i.is_complete } : i))
    apiFn(id).catch(() => {
      // Revert on failure
      setSanitation(prev => prev.map(i => i.id === id ? { ...i, is_complete: item.is_complete } : i))
    })
  }

  function toggleCleaning(id) {
    const task = cleaning.find(t => t.id === id)
    const apiFn = task.is_complete ? markCleaningIncomplete : markCleaningComplete
    // Optimistic update
    setCleaning(prev => prev.map(t => t.id === id ? { ...t, is_complete: !t.is_complete } : t))
    apiFn(id).catch(() => {
      // Revert on failure
      setCleaning(prev => prev.map(t => t.id === id ? { ...t, is_complete: task.is_complete } : t))
    })
  }

  if (loading) return <div className="tab-status">Loading cleaning tasks…</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  const sanitationDone = sanitation.filter(i => i.is_complete).length
  const cleaningDone   = cleaning.filter(i => i.is_complete).length
  const totalDone = sanitationDone + cleaningDone
  const totalAll  = sanitation.length + cleaning.length

  return (
    <div className="cleaning-tab">
      <div className="cleaning-overall">
        <ProgressBar completed={totalDone} total={totalAll} label="Overall Progress" />
      </div>

      <section className="cleaning-section">
        <div className="cleaning-section-header">
          <h2>Sanitation Checklist</h2>
          <ProgressBar completed={sanitationDone} total={sanitation.length} />
        </div>
        <div className="cleaning-list">
          {sanitation.map(item => (
            <ChecklistRow key={item.id} item={item} onToggle={toggleSanitation} />
          ))}
        </div>
      </section>

      <section className="cleaning-section">
        <div className="cleaning-section-header">
          <h2>Daily Cleaning Tasks</h2>
          <ProgressBar completed={cleaningDone} total={cleaning.length} />
        </div>
        <div className="cleaning-list">
          {cleaning.map(task => (
            <ChecklistRow key={task.id} item={{ ...task, item_name: task.action }} onToggle={toggleCleaning} areaLabel />
          ))}
        </div>
      </section>
    </div>
  )
}
