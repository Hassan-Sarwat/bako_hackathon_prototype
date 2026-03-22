import { useState, useEffect } from 'react'
import { fetchPurchases, createPurchase, updatePurchase, deletePurchase, fetchMaterials } from '../../api'
import './PurchasesTab.css'

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

function pricePerUnit(totalPrice, quantity, amountValue, unit) {
  const totalValue = (quantity || 1) * (amountValue || 0)
  if (!totalValue) return '—'
  const ppu = totalPrice / totalValue
  if (unit === 'g') return `${(ppu * 1000).toFixed(2)}/kg`
  if (unit === 'ml') return `${(ppu * 1000).toFixed(2)}/L`
  if (unit === 'Stuck') return `${ppu.toFixed(2)}/Stk`
  return `${ppu.toFixed(2)}/${unit || 'u'}`
}

export default function PurchasesTab() {
  const [items, setItems] = useState([])
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState({ material_id: '', amount: '', quantity: '1', price: '', purchase_date: todayISO() })
  const [filterMaterial, setFilterMaterial] = useState('')

  function load() {
    setLoading(true)
    const params = {}
    if (filterMaterial) params.material_id = filterMaterial
    Promise.all([fetchPurchases(params), fetchMaterials()])
      .then(([purchases, mats]) => { setItems(purchases); setMaterials(mats) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filterMaterial])

  function resetForm() {
    setForm({ material_id: materials[0]?.id || '', amount: '', quantity: '1', price: '', purchase_date: todayISO() })
    setEditId(null)
    setShowForm(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const data = {
      ...form,
      material_id: parseInt(form.material_id),
      quantity: parseInt(form.quantity) || 1,
      price: parseFloat(form.price),
    }
    try {
      if (editId) {
        await updatePurchase(editId, data)
      } else {
        await createPurchase(data)
      }
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  function startEdit(item) {
    setForm({
      material_id: String(item.material_id),
      amount: item.amount,
      quantity: String(item.quantity || 1),
      price: String(item.price),
      purchase_date: item.purchase_date,
    })
    setEditId(item.id)
    setShowForm(true)
  }

  async function handleDelete(id) {
    try {
      await deletePurchase(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <div className="tab-status">Loading purchases...</div>
  if (error) return <div className="tab-status tab-status--error">Error: {error}</div>

  const totalSpent = items.reduce((sum, i) => sum + i.price, 0)

  return (
    <div className="purchases-tab">
      <div className="purchases-toolbar">
        <select
          value={filterMaterial}
          onChange={e => setFilterMaterial(e.target.value)}
          className="filter-select"
        >
          <option value="">All materials</option>
          {materials.map(m => (
            <option key={m.id} value={m.id}>{m.item_name}</option>
          ))}
        </select>
        <span><strong>{items.length}</strong> purchases</span>
        <span>Total: <strong>{totalSpent.toFixed(2)}</strong></span>
        <button className="btn-add" onClick={() => { resetForm(); setShowForm(true) }}>+ Add Purchase</button>
      </div>

      {showForm && (
        <form className="purchase-form" onSubmit={handleSubmit}>
          <select
            value={form.material_id}
            onChange={e => setForm({ ...form, material_id: e.target.value })}
            required
          >
            <option value="">Select material</option>
            {materials.map(m => (
              <option key={m.id} value={m.id}>{m.item_name}</option>
            ))}
          </select>
          <input placeholder="Size (e.g. 25kg)" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} required />
          <input type="number" min="1" placeholder="Qty" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} required />
          <input type="number" step="0.01" placeholder="Total Price" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} required />
          <input type="date" value={form.purchase_date} onChange={e => setForm({ ...form, purchase_date: e.target.value })} required />
          <button type="submit" className="btn-save">{editId ? 'Update' : 'Save'}</button>
          <button type="button" className="btn-cancel" onClick={resetForm}>Cancel</button>
        </form>
      )}

      <div className="purchases-grid">
        <div className="purchases-header">
          <span>Material</span>
          <span>Qty</span>
          <span>Size</span>
          <span>Total Price</span>
          <span>Price/Unit</span>
          <span>Date</span>
          <span>Actions</span>
        </div>
        {items.length === 0 && (
          <div className="purchases-empty">No purchases found</div>
        )}
        {items.map(item => (
          <div key={item.id} className="purchases-row">
            <span className="item-name">{item.material_name}</span>
            <span className="item-qty">{item.quantity || 1}</span>
            <span>{item.amount}</span>
            <span className="item-price">{item.price.toFixed(2)}</span>
            <span className="item-ppu">{pricePerUnit(item.price, item.quantity, item.amount_value, item.amount_unit)}</span>
            <span>{item.purchase_date}</span>
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
