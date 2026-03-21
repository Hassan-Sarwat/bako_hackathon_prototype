import ChecklistRow from '../../components/ChecklistRow/ChecklistRow'
import ProgressBar from '../../components/ProgressBar/ProgressBar'

export default function HaccpGroup({ group, onToggle }) {
  const done = group.items.filter(i => i.is_complete).length
  const total = group.items.length

  return (
    <div className="haccp-group">
      <div className="haccp-group-header">
        <div className="haccp-group-title">
          <h3 className="haccp-group-name">{group.category}</h3>
          <span className="haccp-group-count">{done}/{total}</span>
        </div>
        <ProgressBar completed={done} total={total} />
      </div>
      <div className="haccp-group-items">
        {group.items.map(item => (
          <ChecklistRow key={item.id} item={item} onToggle={id => onToggle(group.id, id)} />
        ))}
      </div>
    </div>
  )
}
