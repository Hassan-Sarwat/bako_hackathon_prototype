import { useState } from 'react'
import { MOCK_SANITATION_ITEMS, MOCK_CLEANING_TASKS } from '../../data/mockData'
import ProgressBar from '../../components/ProgressBar/ProgressBar'
import ChecklistRow from '../../components/ChecklistRow/ChecklistRow'
import './CleaningTab.css'

export default function CleaningTab() {
  const [sanitation, setSanitation] = useState(MOCK_SANITATION_ITEMS)
  const [cleaning, setCleaning] = useState(MOCK_CLEANING_TASKS)

  function toggleSanitation(id) {
    // TODO: POST /api/checklists/items/{id}/complete or /incomplete
    setSanitation(prev =>
      prev.map(item =>
        item.id === id ? { ...item, is_complete: !item.is_complete } : item
      )
    )
  }

  function toggleCleaning(id) {
    // TODO: POST /api/cleaning/tasks/{id}/complete or /incomplete
    setCleaning(prev =>
      prev.map(task =>
        task.id === id ? { ...task, is_complete: !task.is_complete } : task
      )
    )
  }

  const sanitationDone = sanitation.filter(i => i.is_complete).length
  const cleaningDone = cleaning.filter(i => i.is_complete).length
  const totalDone = sanitationDone + cleaningDone
  const totalAll = sanitation.length + cleaning.length

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
