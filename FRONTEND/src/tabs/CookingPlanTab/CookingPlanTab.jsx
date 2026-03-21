import { useState, useEffect } from 'react'
import { fetchCookingPlans, createCookingPlan, updateCookingPlan, deleteCookingPlan, fetchBakedGoods } from '../../api'
import './CookingPlanTab.css'

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export default function CookingPlanTab() {
  const [items, setItems] = useState([])
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [date, setDate] = useState(todayISO())
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState({ product_id: '', quantity: '' })

  function load() {
    setLoading(true)
    Promise.all([fetchCookingPlans(date), fetchBakedGoods()])
      .then(([plans, prods]) => { setItems(plans); setProducts(prods) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [date])

  function resetForm() {
    setForm({ product_id: products[0]?.id || '', quantity: '' })
    setEditId(null)
    setShowForm(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const data = { plan_date: date, product_id: parseInt(form.product_id), quantity: parseInt(form.quantity) }
    try {
      if (editId) {
        await updateCookingPlan(editId, data)
      } else {
        await createCookingPlan(data)
      }
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  function startEdit(item) {
    setForm({ product_id: String(item.product_id), quantity: String(item.quantity) })
    setEditId(item.id)
    setShowForm(true)
  }

  async function handleDelete(id) {
    try {
      await deleteCookingPlan(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <div className="tab-status">Loading cooking plan...</div>
  if (error) return <div className="tab-status tab-status--error">Error: {error}</div>

  const totalBaked = items.reduce((sum, i) => sum + i.quantity, 0)

  return (
    <div className="cooking-plan-tab">
      <div className="cooking-toolbar">
        <input type="date" value={date} onChange={e => setDate(e.target.value)} className="cooking-date-input" />
        <span><strong>{items.length}</strong> products planned</span>
        <span>Total items: <strong>{totalBaked}</strong></span>
        <button className="btn-add" onClick={() => { resetForm(); setShowForm(true) }}>+ Add Entry</button>
      </div>

      {showForm && (
        <form className="cooking-form" onSubmit={handleSubmit}>
          <select
            value={form.product_id}
            onChange={e => setForm({ ...form, product_id: e.target.value })}
            required
          >
            <option value="">Select product</option>
            {products.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Quantity"
            value={form.quantity}
            onChange={e => setForm({ ...form, quantity: e.target.value })}
            required
            min="1"
          />
          <button type="submit" className="btn-save">{editId ? 'Update' : 'Save'}</button>
          <button type="button" className="btn-cancel" onClick={resetForm}>Cancel</button>
        </form>
      )}

      <div className="cooking-grid">
        <div className="cooking-header">
          <span>Product</span>
          <span>Quantity</span>
          <span>Actions</span>
        </div>
        {items.length === 0 && (
          <div className="cooking-empty">No cooking plan for this date</div>
        )}
        {items.map(item => (
          <div key={item.id} className="cooking-row">
            <span className="item-name">{item.product_name}</span>
            <span className="item-quantity">{item.quantity}</span>
            <span className="row-actions">
              <button className="btn-edit" onClick={() => startEdit(item)}>Edit</button>
              <button className="btn-delete" onClick={() => handleDelete(item.id)}>Delete</button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
