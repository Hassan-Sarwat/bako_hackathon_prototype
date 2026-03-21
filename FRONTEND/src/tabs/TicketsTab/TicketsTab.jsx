import { useState, useEffect } from 'react'
import { fetchTickets, closeTicket } from '../../api'
import TicketCard from './TicketCard'
import './TicketsTab.css'

const LS_PREFIX = 'bako_ticket_inprogress_'

function loadInProgress() {
  const ids = new Set()
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(LS_PREFIX)) {
      ids.add(Number(key.slice(LS_PREFIX.length)))
    }
  }
  return ids
}

export default function TicketsTab() {
  const [tickets, setTickets]         = useState([])
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(null)
  const [inProgress, setInProgress]   = useState(loadInProgress)
  const [deleting, setDeleting]       = useState(new Set())

  useEffect(() => {
    fetchTickets()
      .then(data => setTickets(data.filter(t => t.status !== 'close')))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  function toggleProgress(id) {
    setInProgress(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
        localStorage.removeItem(LS_PREFIX + id)
      } else {
        next.add(id)
        localStorage.setItem(LS_PREFIX + id, '1')
      }
      return next
    })
  }

  function handleDelete(id) {
    // Start the deletion animation
    setDeleting(prev => new Set(prev).add(id))

    // After animation (~900ms), close via API and remove from list
    setTimeout(() => {
      closeTicket(id).catch(() => {}) // fire-and-forget; UI already removed it
      localStorage.removeItem(LS_PREFIX + id)
      setInProgress(prev => { const n = new Set(prev); n.delete(id); return n })
      setTickets(prev => prev.filter(t => t.id !== id))
      setDeleting(prev => { const n = new Set(prev); n.delete(id); return n })
    }, 900)
  }

  if (loading) return <div className="tab-status">Loading tickets…</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  const urgentCount = tickets.filter(t => t.urgency === 'urgent').length
  const highCount   = tickets.filter(t => t.urgency === 'high').length

  return (
    <div className="tickets-tab">
      <div className="tickets-summary">
        <span><strong>{tickets.length}</strong> open tickets</span>
        {urgentCount > 0 && (
          <span className="summary-urgent">{urgentCount} urgent</span>
        )}
        {highCount > 0 && (
          <span className="summary-high">{highCount} high</span>
        )}
      </div>
      <div className="tickets-grid">
        {tickets.map(ticket => (
          <TicketCard
            key={ticket.id}
            ticket={ticket}
            isInProgress={inProgress.has(ticket.id)}
            isDeleting={deleting.has(ticket.id)}
            onToggleProgress={toggleProgress}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  )
}
