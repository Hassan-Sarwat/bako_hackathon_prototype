import UrgencyBadge from '../../components/UrgencyBadge/UrgencyBadge'
import CategoryTag from '../../components/CategoryTag/CategoryTag'

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function TicketCard({ ticket }) {
  return (
    <div className={`ticket-card ticket-card--${ticket.urgency}`}>
      <div className="ticket-card-header">
        <UrgencyBadge urgency={ticket.urgency} />
        <CategoryTag category={ticket.category} />
      </div>
      <h3 className="ticket-title">{ticket.title}</h3>
      <p className="ticket-description">{ticket.description}</p>
      <div className="ticket-meta">
        <span className="ticket-assignee">
          <span className="ticket-assignee-icon" aria-hidden="true">👤</span>
          {ticket.raised_by}
        </span>
        <span className="ticket-date">{formatDate(ticket.created_at)}</span>
      </div>
    </div>
  )
}
