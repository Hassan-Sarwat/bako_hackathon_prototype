import { useState, useEffect, useMemo } from 'react'
import { fetchSchedules, createSchedule, updateSchedule, deleteSchedule } from '../../api'
import './ScheduleTab.css'

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
const HOUR_START = 4   // 04:00
const HOUR_END = 22    // 22:00

function toISO(d) {
  return d.toISOString().slice(0, 10)
}

function getMonday(d) {
  const date = new Date(d)
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  return date
}

function getWeekDays(monday) {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    return d
  })
}

function timeToMinutes(t) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function formatDate(d) {
  return d.toLocaleDateString([], { day: 'numeric', month: 'short' })
}

function formatWeekRange(days) {
  const start = days[0].toLocaleDateString([], { day: 'numeric', month: 'short' })
  const end = days[6].toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })
  return `${start} — ${end}`
}

// Assign a consistent color per employee name
const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
]

function getColor(name, colorMap) {
  if (!colorMap.current[name]) {
    const idx = Object.keys(colorMap.current).length % COLORS.length
    colorMap.current[name] = COLORS[idx]
  }
  return colorMap.current[name]
}

/**
 * Compute side-by-side layout for overlapping events.
 * Returns a Map of item.id → { col, totalCols }.
 */
function layoutEvents(dayItems) {
  if (dayItems.length === 0) return new Map()

  const sorted = [...dayItems].sort(
    (a, b) => timeToMinutes(a.start_time) - timeToMinutes(b.start_time)
  )

  // columns tracks end-time per column (in minutes)
  const columns = []
  const placement = new Map()

  for (const item of sorted) {
    const start = timeToMinutes(item.start_time)
    const end = timeToMinutes(item.end_time)

    // find first column where the item doesn't overlap
    let placed = false
    for (let c = 0; c < columns.length; c++) {
      if (columns[c] <= start) {
        columns[c] = end
        placement.set(item.id, { col: c })
        placed = true
        break
      }
    }
    if (!placed) {
      placement.set(item.id, { col: columns.length })
      columns.push(end)
    }
  }

  // For each event, find how many events are concurrent with it
  for (const item of sorted) {
    const start = timeToMinutes(item.start_time)
    const end = timeToMinutes(item.end_time)
    // Count how many events overlap with this one
    let maxConcurrent = 0
    for (const other of sorted) {
      const oStart = timeToMinutes(other.start_time)
      const oEnd = timeToMinutes(other.end_time)
      if (oStart < end && oEnd > start) maxConcurrent++
    }
    const p = placement.get(item.id)
    p.totalCols = Math.max(maxConcurrent, p.col + 1)
  }

  return placement
}

export default function ScheduleTab() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [weekMonday, setWeekMonday] = useState(() => getMonday(new Date()))
  const [showForm, setShowForm] = useState(false)
  const [formDate, setFormDate] = useState('')
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState({ employee_name: '', start_time: '06:00', end_time: '14:00', cleaning: 0 })

  const colorMap = useMemo(() => ({ current: {} }), [])
  const weekDays = useMemo(() => getWeekDays(weekMonday), [weekMonday])
  const todayStr = toISO(new Date())

  function load() {
    setLoading(true)
    const start_date = toISO(weekDays[0])
    const end_date = toISO(weekDays[6])
    fetchSchedules({ start_date, end_date })
      .then(setItems)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [weekMonday])

  function prevWeek() {
    const d = new Date(weekMonday)
    d.setDate(d.getDate() - 7)
    setWeekMonday(d)
  }

  function nextWeek() {
    const d = new Date(weekMonday)
    d.setDate(d.getDate() + 7)
    setWeekMonday(d)
  }

  function goToday() {
    setWeekMonday(getMonday(new Date()))
  }

  function resetForm() {
    setForm({ employee_name: '', start_time: '06:00', end_time: '14:00', cleaning: 0 })
    setFormDate('')
    setEditId(null)
    setShowForm(false)
  }

  function openFormForDate(dateStr) {
    resetForm()
    setFormDate(dateStr)
    setShowForm(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const data = { ...form, schedule_date: formDate }
    try {
      if (editId) {
        await updateSchedule(editId, data)
      } else {
        await createSchedule(data)
      }
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  function startEdit(item) {
    setForm({
      employee_name: item.employee_name,
      start_time: item.start_time,
      end_time: item.end_time,
      cleaning: item.cleaning ? 1 : 0,
    })
    setFormDate(item.schedule_date)
    setEditId(item.id)
    setShowForm(true)
  }

  async function handleDelete(id) {
    try {
      await deleteSchedule(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  // Group items by date
  const byDate = useMemo(() => {
    const map = {}
    for (const item of items) {
      if (!map[item.schedule_date]) map[item.schedule_date] = []
      map[item.schedule_date].push(item)
    }
    return map
  }, [items])

  const totalMinutes = (HOUR_END - HOUR_START) * 60
  const hours = Array.from({ length: HOUR_END - HOUR_START + 1 }, (_, i) => HOUR_START + i)

  if (error) return <div className="tab-status tab-status--error">Error: {error}</div>

  return (
    <div className="schedule-tab">
      {/* Toolbar */}
      <div className="cal-toolbar">
        <button className="cal-nav-btn" onClick={prevWeek}>&larr;</button>
        <button className="cal-today-btn" onClick={goToday}>Heute</button>
        <button className="cal-nav-btn" onClick={nextWeek}>&rarr;</button>
        <span className="cal-week-label">{formatWeekRange(weekDays)}</span>
        <button className="btn-add" onClick={() => openFormForDate(todayStr)}>+ Schicht hinzufügen</button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <form className="schedule-form" onSubmit={handleSubmit}>
          <input type="date" value={formDate} onChange={e => setFormDate(e.target.value)} required />
          <input
            placeholder="Mitarbeitername"
            value={form.employee_name}
            onChange={e => setForm({ ...form, employee_name: e.target.value })}
            required
          />
          <input type="time" value={form.start_time} onChange={e => setForm({ ...form, start_time: e.target.value })} required />
          <input type="time" value={form.end_time} onChange={e => setForm({ ...form, end_time: e.target.value })} required />
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={form.cleaning === 1}
              onChange={e => setForm({ ...form, cleaning: e.target.checked ? 1 : 0 })}
            />
            Reinigung
          </label>
          <button type="submit" className="btn-save">{editId ? 'Aktualisieren' : 'Speichern'}</button>
          <button type="button" className="btn-cancel" onClick={resetForm}>Abbrechen</button>
        </form>
      )}

      {/* Calendar grid */}
      <div className="cal-container">
        {loading && <div className="cal-loading">Laden...</div>}
        <div className="cal-grid" style={{ gridTemplateColumns: '50px repeat(7, 1fr)' }}>
          {/* Header row */}
          <div className="cal-corner" />
          {weekDays.map((day, i) => {
            const dateStr = toISO(day)
            const isToday = dateStr === todayStr
            return (
              <div
                key={i}
                className={`cal-day-header ${isToday ? 'cal-day-header--today' : ''}`}
                onClick={() => openFormForDate(dateStr)}
              >
                <span className="cal-day-label">{DAY_LABELS[i]}</span>
                <span className={`cal-day-num ${isToday ? 'cal-day-num--today' : ''}`}>
                  {day.getDate()}
                </span>
              </div>
            )
          })}

          {/* Time gutter + day columns */}
          <div className="cal-gutter">
            {hours.map(h => (
              <div key={h} className="cal-hour-label" style={{ top: `${((h - HOUR_START) / (HOUR_END - HOUR_START)) * 100}%` }}>
                {String(h).padStart(2, '0')}:00
              </div>
            ))}
          </div>

          {weekDays.map((day, colIdx) => {
            const dateStr = toISO(day)
            const dayItems = byDate[dateStr] || []
            const isToday = dateStr === todayStr
            const layout = layoutEvents(dayItems)
            return (
              <div
                key={colIdx}
                className={`cal-day-col ${isToday ? 'cal-day-col--today' : ''}`}
                onClick={() => openFormForDate(dateStr)}
              >
                {/* Hour grid lines */}
                {hours.map(h => (
                  <div
                    key={h}
                    className="cal-hour-line"
                    style={{ top: `${((h - HOUR_START) / (HOUR_END - HOUR_START)) * 100}%` }}
                  />
                ))}

                {/* Shift blocks */}
                {dayItems.map(item => {
                  const startMin = Math.max(timeToMinutes(item.start_time) - HOUR_START * 60, 0)
                  const endMin = Math.min(timeToMinutes(item.end_time) - HOUR_START * 60, totalMinutes)
                  const top = (startMin / totalMinutes) * 100
                  const height = ((endMin - startMin) / totalMinutes) * 100
                  const bg = getColor(item.employee_name, colorMap)
                  const { col, totalCols } = layout.get(item.id)
                  const widthPct = 100 / totalCols
                  const leftPct = col * widthPct

                  return (
                    <div
                      key={item.id}
                      className={`cal-event ${item.cleaning ? 'cal-event--cleaning' : ''}`}
                      style={{
                        top: `${top}%`,
                        height: `${Math.max(height, 2)}%`,
                        left: `${leftPct}%`,
                        width: `calc(${widthPct}% - 2px)`,
                        backgroundColor: bg,
                      }}
                      onClick={e => { e.stopPropagation(); startEdit(item) }}
                      title={`${item.employee_name}\n${item.start_time} – ${item.end_time}${item.cleaning ? '\nReinigungsdienst' : ''}`}
                    >
                      <span className="cal-event-name">{item.employee_name}</span>
                      <span className="cal-event-time">{item.start_time}–{item.end_time}</span>
                      {item.cleaning && <span className="cal-event-badge">C</span>}
                      <button
                        className="cal-event-delete"
                        onClick={e => { e.stopPropagation(); handleDelete(item.id) }}
                        title="Löschen"
                      >&times;</button>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
