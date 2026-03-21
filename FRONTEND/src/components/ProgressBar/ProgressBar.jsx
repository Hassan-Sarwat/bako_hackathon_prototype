import './ProgressBar.css'

export default function ProgressBar({ completed, total, label }) {
  const pct = total === 0 ? 0 : Math.round((completed / total) * 100)
  const done = completed === total && total > 0

  return (
    <div className="progress-bar-wrapper">
      {label && (
        <div className="progress-bar-header">
          <span className="progress-bar-label">{label}</span>
          <span className="progress-bar-count">
            {completed}/{total}
          </span>
        </div>
      )}
      <div className="progress-bar-track">
        <div
          className={`progress-bar-fill ${done ? 'progress-bar-fill--complete' : ''}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="progress-bar-pct">{pct}%</span>
    </div>
  )
}
