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

export default function TicketCard({ ticket, isInProgress, isResolving, onToggleProgress, onResolve }) {
  return (
    <div
      className={[
        'ticket-card',
        `ticket-card--${ticket.urgency}`,
        isInProgress ? 'ticket-card--in-progress' : '',
        isResolving  ? 'ticket-card--resolving'   : '',
      ].filter(Boolean).join(' ')}
    >
      <div className="ticket-card-header">
        <UrgencyBadge urgency={ticket.urgency} />
        <CategoryTag category={ticket.category} />

        <div className="ticket-card-actions">
          {isInProgress && (
            <span className="ticket-progress-dot" aria-label="In Bearbeitung" />
          )}

          {/* Start / Stop toggle */}
          <button
            className={`ticket-action-btn ticket-action-btn--progress ${isInProgress ? 'ticket-action-btn--stop' : ''}`}
            onClick={() => onToggleProgress(ticket.id)}
            aria-label={isInProgress ? 'Fortschritt stoppen' : 'Fortschritt starten'}
            title={isInProgress ? 'Stopp' : 'Start'}
            disabled={isResolving}
          >
            {isInProgress ? '■' : '▶'}
          </button>

          {/* Resolve checkbox */}
          <button
            className={`ticket-resolve-btn ${isResolving ? 'ticket-resolve-btn--checked' : ''}`}
            onClick={() => !isResolving && onResolve(ticket.id)}
            aria-label="Als erledigt markieren"
            title="Als erledigt markieren"
            disabled={isResolving}
          >
            {isResolving ? (
              <svg viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <polyline points="2,7 6,11 12,3" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : (
              <svg viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <polyline points="2,7 6,11 12,3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {isResolving && (
        <div className="ticket-resolved-banner">Erledigt</div>
      )}

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
