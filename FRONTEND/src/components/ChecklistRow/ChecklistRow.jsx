import './ChecklistRow.css'

function formatTime(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChecklistRow({ item, onToggle, areaLabel }) {
  return (
    <div className={`checklist-row ${item.is_complete ? 'checklist-row--done' : ''}`}>
      <input
        type="checkbox"
        className="checklist-checkbox"
        checked={item.is_complete}
        onChange={() => onToggle(item.id)}
        aria-label={item.item_name ?? item.action}
      />
      <div className="checklist-row-body">
        {areaLabel && <span className="checklist-area">{item.area}</span>}
        <span className="checklist-name">
          {item.item_name ?? item.action}
        </span>
        {item.is_complete && item.completed_by && (
          <span className="checklist-meta">
            {item.completed_by} · {formatTime(item.completed_at)}
          </span>
        )}
      </div>
    </div>
  )
}
