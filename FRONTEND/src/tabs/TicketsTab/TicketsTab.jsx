import { useState, useEffect } from 'react'
import { fetchTickets } from '../../api'
import TicketCard from './TicketCard'
import './TicketsTab.css'

export default function TicketsTab() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchTickets()
      .then(setTickets)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

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
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
      </div>
    </div>
  )
}
