import './UrgencyBadge.css'

const LABELS = {
  urgent: 'Dringend',
  high: 'Hoch',
  normal: 'Normal',
  low: 'Niedrig',
}

export default function UrgencyBadge({ urgency }) {
  return (
    <span className={`urgency-badge urgency-${urgency}`}>
      {LABELS[urgency] ?? urgency}
    </span>
  )
}
