import './CategoryTag.css'

const LABELS = {
  machine_breakdown: 'Maschinenausfall',
  no_show: 'Nicht erschienen',
  stock_shortage: 'Materialmangel',
  safety: 'Sicherheit',
  other: 'Sonstiges',
}

export default function CategoryTag({ category }) {
  return (
    <span className={`category-tag category-${category}`}>
      {LABELS[category] ?? category}
    </span>
  )
}
