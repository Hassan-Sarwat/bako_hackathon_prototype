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
  const [tickets, setTickets]       = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [inProgress, setInProgress] = useState(loadInProgress)
  const [resolving, setResolving]   = useState(new Set())
  const [activeTab, setActiveTab]   = useState('unresolved')

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
        // Move view to in-progress tab when a ticket is started
        setActiveTab('inprogress')
      }
      return next
    })
  }

  function handleResolve(id) {
    setResolving(prev => new Set(prev).add(id))

    // After success animation (~1.1s), close via API and remove from list
    setTimeout(() => {
      closeTicket(id).catch(() => {})
      localStorage.removeItem(LS_PREFIX + id)
      setInProgress(prev => { const n = new Set(prev); n.delete(id); return n })
      setTickets(prev => prev.filter(t => t.id !== id))
      setResolving(prev => { const n = new Set(prev); n.delete(id); return n })
    }, 1100)
  }

  if (loading) return <div className="tab-status">Tickets werden geladen…</div>
  if (error)   return <div className="tab-status tab-status--error">Error: {error}</div>

  const unresolvedTickets  = tickets.filter(t => !inProgress.has(t.id))
  const inProgressTickets  = tickets.filter(t =>  inProgress.has(t.id))
  const visibleTickets     = activeTab === 'unresolved' ? unresolvedTickets : inProgressTickets

  const urgentCount = unresolvedTickets.filter(t => t.urgency === 'urgent').length
  const highCount   = unresolvedTickets.filter(t => t.urgency === 'high').length

  return (
    <div className="tickets-tab">
      {/* Summary row */}
      <div className="tickets-summary">
        <span><strong>{tickets.length}</strong> offene Tickets</span>
        {urgentCount > 0 && <span className="summary-urgent">{urgentCount} dringend</span>}
        {highCount   > 0 && <span className="summary-high">{highCount} hoch</span>}
      </div>

      {/* Sub-tab bar */}
      <div className="tickets-subtabs" role="tablist" aria-label="Ticket view">
        <button
          role="tab"
          aria-selected={activeTab === 'unresolved'}
          className={`tickets-subtab ${activeTab === 'unresolved' ? 'tickets-subtab--active' : ''}`}
          onClick={() => setActiveTab('unresolved')}
        >
          Offen
          {unresolvedTickets.length > 0 && (
            <span className="tickets-subtab-count">{unresolvedTickets.length}</span>
          )}
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'inprogress'}
          className={`tickets-subtab ${activeTab === 'inprogress' ? 'tickets-subtab--active' : ''}`}
          onClick={() => setActiveTab('inprogress')}
        >
          In Bearbeitung
          {inProgressTickets.length > 0 && (
            <span className="tickets-subtab-count tickets-subtab-count--progress">{inProgressTickets.length}</span>
          )}
        </button>
      </div>

      {/* Ticket grid */}
      {visibleTickets.length === 0 ? (
        <div className="tickets-empty">
          {activeTab === 'unresolved' ? 'Keine offenen Tickets.' : 'Keine Tickets in Bearbeitung.'}
        </div>
      ) : (
        <div className="tickets-grid">
          {visibleTickets.map(ticket => (
            <TicketCard
              key={ticket.id}
              ticket={ticket}
              isInProgress={inProgress.has(ticket.id)}
              isResolving={resolving.has(ticket.id)}
              onToggleProgress={toggleProgress}
              onResolve={handleResolve}
            />
          ))}
        </div>
      )}
    </div>
  )
}
