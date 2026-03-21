import './UrgencyBadge.css'

const LABELS = {
  urgent: 'Urgent',
  high: 'High',
  normal: 'Normal',
  low: 'Low',
}

export default function UrgencyBadge({ urgency }) {
  return (
    <span className={`urgency-badge urgency-${urgency}`}>
      {LABELS[urgency] ?? urgency}
    </span>
  )
}
