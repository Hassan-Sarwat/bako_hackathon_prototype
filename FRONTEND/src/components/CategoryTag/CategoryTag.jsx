import './CategoryTag.css'

const LABELS = {
  machine_breakdown: 'Machine Breakdown',
  no_show: 'No-Show',
  stock_shortage: 'Stock Shortage',
  safety: 'Safety',
  other: 'Other',
}

export default function CategoryTag({ category }) {
  return (
    <span className={`category-tag category-${category}`}>
      {LABELS[category] ?? category}
    </span>
  )
}
