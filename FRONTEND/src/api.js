// API helpers — all calls go to /api (proxied to localhost:8000 in dev).
// Write operations pass x-staff-id header; update STAFF_ID to match the active operator.
const STAFF_ID = 'dashboard'

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${options.method ?? 'GET'} ${path} failed (${res.status}): ${body}`)
  }
  return res.json()
}

// ── Tickets ──────────────────────────────────────────────────────────────────

export function fetchTickets() {
  return apiFetch('/api/tickets').then(d => d.tickets)
}

export function closeTicket(id) {
  return apiFetch(`/api/tickets/${id}/close`, {
    method: 'PUT',
    headers: { 'x-staff-id': STAFF_ID },
  })
}

// ── Inventory ─────────────────────────────────────────────────────────────────

export function fetchInventory() {
  return apiFetch('/api/inventory').then(d => d.items)
}

// ── Checklists ────────────────────────────────────────────────────────────────

export function fetchChecklistItems(type) {
  return apiFetch(`/api/checklist/${type}/items`).then(d => d.items)
}

export function markChecklistComplete(id) {
  return apiFetch(`/api/checklist/items/${id}/complete`, {
    method: 'PUT',
    headers: { 'x-staff-id': STAFF_ID },
    body: JSON.stringify({}),
  })
}

export function markChecklistIncomplete(id) {
  return apiFetch(`/api/checklist/items/${id}/incomplete`, {
    method: 'PUT',
    headers: { 'x-staff-id': STAFF_ID },
  })
}

// ── Cleaning tasks ─────────────────────────────────────────────────────────────

export function fetchCleaningTasks() {
  return apiFetch('/api/cleaning/tasks').then(d => d.tasks)
}

export function markCleaningComplete(id) {
  return apiFetch(`/api/cleaning/tasks/${id}/complete`, {
    method: 'PUT',
    headers: { 'x-staff-id': STAFF_ID },
    body: JSON.stringify({}),
  })
}

export function markCleaningIncomplete(id) {
  return apiFetch(`/api/cleaning/tasks/${id}/incomplete`, {
    method: 'PUT',
    headers: { 'x-staff-id': STAFF_ID },
  })
}

// ── Schedules ────────────────────────────────────────────────────────────────

export function fetchSchedules({ date, start_date, end_date } = {}) {
  const q = new URLSearchParams()
  if (date) q.set('date', date)
  if (start_date) q.set('start_date', start_date)
  if (end_date) q.set('end_date', end_date)
  const qs = q.toString()
  return apiFetch(`/api/schedules${qs ? `?${qs}` : ''}`).then(d => d.schedules)
}

export function createSchedule(data) {
  return apiFetch('/api/schedules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateSchedule(id, data) {
  return apiFetch(`/api/schedules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteSchedule(id) {
  return apiFetch(`/api/schedules/${id}`, { method: 'DELETE' })
}

// ── Baked Goods ──────────────────────────────────────────────────────────────

export function fetchBakedGoods() {
  return apiFetch('/api/baked-goods').then(d => d.baked_goods)
}

export function fetchBakedGood(id) {
  return apiFetch(`/api/baked-goods/${id}`)
}

export function createBakedGood(data) {
  return apiFetch('/api/baked-goods', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateBakedGood(id, data) {
  return apiFetch(`/api/baked-goods/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteBakedGood(id) {
  return apiFetch(`/api/baked-goods/${id}`, { method: 'DELETE' })
}

export function fetchProductMaterials(productId) {
  return apiFetch(`/api/baked-goods/${productId}/materials`).then(d => d.materials)
}

export function setProductMaterials(productId, materials) {
  return apiFetch(`/api/baked-goods/${productId}/materials`, {
    method: 'PUT',
    body: JSON.stringify({ materials }),
  })
}

// ── Raw Purchases ────────────────────────────────────────────────────────────

export function fetchPurchases(params = {}) {
  const q = new URLSearchParams()
  if (params.material_id) q.set('material_id', params.material_id)
  if (params.start_date) q.set('start_date', params.start_date)
  if (params.end_date) q.set('end_date', params.end_date)
  const qs = q.toString()
  return apiFetch(`/api/purchases${qs ? `?${qs}` : ''}`).then(d => d.purchases)
}

export function createPurchase(data) {
  return apiFetch('/api/purchases', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updatePurchase(id, data) {
  return apiFetch(`/api/purchases/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deletePurchase(id) {
  return apiFetch(`/api/purchases/${id}`, { method: 'DELETE' })
}

// ── Cooking Plans ────────────────────────────────────────────────────────────

export function fetchCookingPlans(date) {
  const q = date ? `?date=${date}` : ''
  return apiFetch(`/api/cooking-plans${q}`).then(d => d.cooking_plans)
}

export function createCookingPlan(data) {
  return apiFetch('/api/cooking-plans', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateCookingPlan(id, data) {
  return apiFetch(`/api/cooking-plans/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteCookingPlan(id) {
  return apiFetch(`/api/cooking-plans/${id}`, { method: 'DELETE' })
}

// ── Materials (for dropdowns) ────────────────────────────────────────────────

export function fetchMaterials() {
  return apiFetch('/api/materials').then(d => d.materials)
}

// ── Analysis ─────────────────────────────────────────────────────────────────

export function fetchMaterialUsageAnalysis({ start_date, end_date }) {
  const q = new URLSearchParams({ start_date, end_date })
  return apiFetch(`/api/analysis/material-usage?${q}`).then(d => d.materials)
}

export function fetchMaterialDrilldown(materialId, { start_date, end_date }) {
  const q = new URLSearchParams({ start_date, end_date })
  return apiFetch(`/api/analysis/material-drilldown/${materialId}?${q}`).then(d => d.entries)
}

export function fetchProductLossAnalysis({ start_date, end_date }) {
  const q = new URLSearchParams({ start_date, end_date })
  return apiFetch(`/api/analysis/product-loss?${q}`).then(d => d.products)
}

export function fetchProductLossDrilldown(productId, { start_date, end_date }) {
  const q = new URLSearchParams({ start_date, end_date })
  return apiFetch(`/api/analysis/product-loss-drilldown/${productId}?${q}`).then(d => d.entries)
}

// ── Dashboard (all at once) ───────────────────────────────────────────────────

export function fetchDashboard() {
  return apiFetch('/api/dashboard')
}

// ── Sales ────────────────────────────────────────────────────────────────────

export function fetchSales(params = {}) {
  const q = new URLSearchParams()
  if (params.start_date) q.set('start_date', params.start_date)
  if (params.end_date) q.set('end_date', params.end_date)
  if (params.product_id) q.set('product_id', params.product_id)
  const qs = q.toString()
  return apiFetch(`/api/sales${qs ? `?${qs}` : ''}`).then(d => d.sales)
}

// ── Predictions ──────────────────────────────────────────────────────────────

export function fetchDailyPlan(date) {
  return apiFetch(`/api/predictions/daily-plan?date=${date}`).then(d => d.plan)
}

export function fetchProductHistory(productId) {
  return apiFetch(`/api/predictions/product/${productId}/history`)
}
