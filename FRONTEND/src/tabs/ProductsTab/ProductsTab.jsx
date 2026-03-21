import { useState, useEffect } from 'react'
import {
  fetchBakedGoods,
  fetchBakedGood,
  createBakedGood,
  updateBakedGood,
  deleteBakedGood,
  setProductMaterials,
  fetchMaterials,
} from '../../api'
import './ProductsTab.css'

export default function ProductsTab() {
  const [products, setProducts] = useState([])
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedId, setExpandedId] = useState(null)
  const [expandedData, setExpandedData] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState({ name: '', price: '', recipe: '' })
  const [recipeMats, setRecipeMats] = useState([])

  function load() {
    setLoading(true)
    Promise.all([fetchBakedGoods(), fetchMaterials()])
      .then(([prods, mats]) => { setProducts(prods); setMaterials(mats) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function toggleExpand(id) {
    if (expandedId === id) {
      setExpandedId(null)
      setExpandedData(null)
      return
    }
    try {
      const data = await fetchBakedGood(id)
      setExpandedId(id)
      setExpandedData(data)
    } catch (err) {
      setError(err.message)
    }
  }

  function resetForm() {
    setForm({ name: '', price: '', recipe: '' })
    setRecipeMats([])
    setEditId(null)
    setShowForm(false)
  }

  async function startEdit(product) {
    const data = await fetchBakedGood(product.id)
    setForm({ name: data.name, price: String(data.price), recipe: data.recipe || '' })
    setRecipeMats(data.materials.map(m => ({ material_id: m.material_id, amount: m.amount })))
    setEditId(product.id)
    setShowForm(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editId) {
        await updateBakedGood(editId, { name: form.name, price: parseFloat(form.price), recipe: form.recipe || null })
        await setProductMaterials(editId, recipeMats)
      } else {
        const res = await createBakedGood({ name: form.name, price: parseFloat(form.price), recipe: form.recipe || null })
        if (recipeMats.length > 0) {
          await setProductMaterials(res.id, recipeMats)
        }
      }
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteBakedGood(id)
      if (expandedId === id) { setExpandedId(null); setExpandedData(null) }
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  function addMatRow() {
    setRecipeMats([...recipeMats, { material_id: materials[0]?.id || 0, amount: '' }])
  }

  function updateMatRow(idx, field, value) {
    setRecipeMats(recipeMats.map((m, i) => i === idx ? { ...m, [field]: field === 'material_id' ? parseInt(value) : value } : m))
  }

  function removeMatRow(idx) {
    setRecipeMats(recipeMats.filter((_, i) => i !== idx))
  }

  if (loading) return <div className="tab-status">Loading products...</div>
  if (error) return <div className="tab-status tab-status--error">Error: {error}</div>

  return (
    <div className="products-tab">
      <div className="products-toolbar">
        <span><strong>{products.length}</strong> products</span>
        <button className="btn-add" onClick={() => { resetForm(); setShowForm(true) }}>+ Add Product</button>
      </div>

      {showForm && (
        <form className="product-form" onSubmit={handleSubmit}>
          <div className="product-form-row">
            <input placeholder="Product name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
            <input type="number" step="0.01" placeholder="Price" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} required />
          </div>
          <textarea placeholder="Recipe / steps (optional)" value={form.recipe} onChange={e => setForm({ ...form, recipe: e.target.value })} rows={3} />

          <div className="mat-section">
            <div className="mat-section-header">
              <strong>Materials</strong>
              <button type="button" className="btn-add-sm" onClick={addMatRow}>+ Material</button>
            </div>
            {recipeMats.map((m, idx) => (
              <div key={idx} className="mat-row">
                <select value={m.material_id} onChange={e => updateMatRow(idx, 'material_id', e.target.value)}>
                  {materials.map(mat => (
                    <option key={mat.id} value={mat.id}>{mat.item_name}</option>
                  ))}
                </select>
                <input placeholder="Amount (e.g. 20kg)" value={m.amount} onChange={e => updateMatRow(idx, 'amount', e.target.value)} required />
                <button type="button" className="btn-delete-sm" onClick={() => removeMatRow(idx)}>x</button>
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-save">{editId ? 'Update' : 'Save'}</button>
            <button type="button" className="btn-cancel" onClick={resetForm}>Cancel</button>
          </div>
        </form>
      )}

      <div className="products-grid">
        <div className="products-header">
          <span>Product</span>
          <span>Price</span>
          <span>Actions</span>
        </div>
        {products.length === 0 && (
          <div className="products-empty">No products yet</div>
        )}
        {products.map(p => (
          <div key={p.id}>
            <div className="products-row" onClick={() => toggleExpand(p.id)}>
              <span className="item-name">{p.name}</span>
              <span className="item-price">{p.price.toFixed(2)}</span>
              <span className="row-actions" onClick={e => e.stopPropagation()}>
                <button className="btn-edit" onClick={() => startEdit(p)}>Edit</button>
                <button className="btn-delete" onClick={() => handleDelete(p.id)}>Delete</button>
              </span>
            </div>
            {expandedId === p.id && expandedData && (
              <div className="product-details">
                {expandedData.recipe && (
                  <div className="detail-section">
                    <strong>Recipe:</strong>
                    <p>{expandedData.recipe}</p>
                  </div>
                )}
                <div className="detail-section">
                  <strong>Materials:</strong>
                  {expandedData.materials.length === 0
                    ? <p className="no-materials">No materials assigned</p>
                    : (
                      <ul className="material-list">
                        {expandedData.materials.map(m => (
                          <li key={m.id}>{m.material_name} — {m.amount}</li>
                        ))}
                      </ul>
                    )
                  }
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
