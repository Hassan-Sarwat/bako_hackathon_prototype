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

export default function TicketCard({ ticket, isInProgress, isDeleting, onToggleProgress, onDelete }) {
  return (
    <div
      className={[
        'ticket-card',
        `ticket-card--${ticket.urgency}`,
        isInProgress ? 'ticket-card--in-progress' : '',
        isDeleting   ? 'ticket-card--deleting'    : '',
      ].filter(Boolean).join(' ')}
    >
      <div className="ticket-card-header">
        <UrgencyBadge urgency={ticket.urgency} />
        <CategoryTag category={ticket.category} />

        <div className="ticket-card-actions">
          {/* In-progress indicator dot (shown when active) */}
          {isInProgress && (
            <span className="ticket-progress-dot" aria-label="In progress" />
          )}

          {/* Start / Stop toggle */}
          <button
            className={`ticket-action-btn ticket-action-btn--progress ${isInProgress ? 'ticket-action-btn--stop' : ''}`}
            onClick={() => onToggleProgress(ticket.id)}
            aria-label={isInProgress ? 'Stop progress' : 'Start progress'}
            title={isInProgress ? 'Stop' : 'Start'}
          >
            {isInProgress ? '■' : '▶'}
          </button>

          {/* Delete */}
          <button
            className="ticket-action-btn ticket-action-btn--delete"
            onClick={() => onDelete(ticket.id)}
            aria-label="Delete ticket"
            title="Delete ticket"
            disabled={isDeleting}
          >
            🗑
          </button>
        </div>
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
