import { MOCK_TICKETS } from '../../data/mockData'
import TicketCard from './TicketCard'
import './TicketsTab.css'

export default function TicketsTab() {
  const urgentCount = MOCK_TICKETS.filter(t => t.urgency === 'urgent').length
  const highCount = MOCK_TICKETS.filter(t => t.urgency === 'high').length

  return (
    <div className="tickets-tab">
      <div className="tickets-summary">
        <span><strong>{MOCK_TICKETS.length}</strong> open tickets</span>
        {urgentCount > 0 && (
          <span className="summary-urgent">{urgentCount} urgent</span>
        )}
        {highCount > 0 && (
          <span className="summary-high">{highCount} high</span>
        )}
      </div>
      <div className="tickets-grid">
        {MOCK_TICKETS.map(ticket => (
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
      </div>
    </div>
  )
}
