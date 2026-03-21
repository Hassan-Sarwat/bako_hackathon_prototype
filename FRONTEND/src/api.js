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

export function closeTicket(id) {
  return apiFetch(`/api/tickets/${id}/close`, {
    method: 'PUT',
    headers: { 'x-staff-id': STAFF_ID },
  })
}

// ── Dashboard (all at once) ───────────────────────────────────────────────────

export function fetchDashboard() {
  return apiFetch('/api/dashboard')
}
