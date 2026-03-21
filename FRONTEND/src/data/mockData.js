// Mock data matching API_SCHEMA.yaml schemas exactly.
// Swap fetch calls here when the real API is ready.

export const MOCK_TICKETS = [
  {
    id: 1,
    title: "Oven #2 Not Reaching Temperature",
    description:
      "Oven 2 won't exceed 180°C. Noticed at 6am during pre-heat. May affect the morning bread batch.",
    category: "machine_breakdown",
    urgency: "urgent",
    raised_by: "alice",
    created_at: "2026-03-21T06:15:00",
  },
  {
    id: 2,
    title: "Morning Shift No-Show",
    description:
      "Carlos did not arrive for the 5am shift and has not called in. Down one staff member for the rush.",
    category: "no_show",
    urgency: "high",
    raised_by: "alice",
    created_at: "2026-03-21T05:20:00",
  },
  {
    id: 3,
    title: "Chocolate Chips Stock Critical",
    description:
      "Chocolate chips almost out — estimated 1 day of supply remaining. Emergency order needed.",
    category: "stock_shortage",
    urgency: "high",
    raised_by: "bob",
    created_at: "2026-03-21T07:30:00",
  },
  {
    id: 4,
    title: "Wet Floor Near Sinks — Slip Risk",
    description:
      "Slow drain at sink area causing standing water. Wet floor sign placed but needs maintenance.",
    category: "safety",
    urgency: "normal",
    raised_by: "diana",
    created_at: "2026-03-20T15:45:00",
  },
  {
    id: 5,
    title: "Display Case Bulb Out",
    description:
      "Left display case has a blown bulb. Pastries not visible from the entrance.",
    category: "other",
    urgency: "low",
    raised_by: "bob",
    created_at: "2026-03-20T13:10:00",
  },
];

// Stock thresholds: <=3 critical, <=8 low, >8 ok
export const MOCK_INVENTORY = [
  { id: 1, item_name: "All-purpose flour",  count: 24,  logged_by: "alice", logged_at: "2026-03-21T06:00:00" },
  { id: 2, item_name: "Sugar",              count: 18,  logged_by: "alice", logged_at: "2026-03-21T06:00:00" },
  { id: 3, item_name: "Butter",             count: 6,   logged_by: "bob",   logged_at: "2026-03-21T06:05:00" },
  { id: 4, item_name: "Eggs",               count: 120, logged_by: "bob",   logged_at: "2026-03-21T06:05:00" },
  { id: 5, item_name: "Yeast",              count: 3,   logged_by: "alice", logged_at: "2026-03-21T06:10:00" },
  { id: 6, item_name: "Vanilla extract",    count: 8,   logged_by: "diana", logged_at: "2026-03-21T06:15:00" },
  { id: 7, item_name: "Chocolate chips",    count: 2,   logged_by: "diana", logged_at: "2026-03-21T06:15:00" },
  { id: 8, item_name: "Baking powder",      count: 12,  logged_by: "alice", logged_at: "2026-03-21T06:00:00" },
];

export const MOCK_SANITATION_ITEMS = [
  { id: 1, checklist_type: "sanitation", item_name: "Sanitize prep surfaces",          is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T06:20:00", notes: null },
  { id: 2, checklist_type: "sanitation", item_name: "Clean oven interiors",            is_complete: true,  completed_by: "bob",   completed_at: "2026-03-21T06:35:00", notes: null },
  { id: 3, checklist_type: "sanitation", item_name: "Wash mixing bowls and utensils", is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 4, checklist_type: "sanitation", item_name: "Mop bakery floor",               is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 5, checklist_type: "sanitation", item_name: "Clean display cases",            is_complete: true,  completed_by: "diana", completed_at: "2026-03-21T07:00:00", notes: null },
  { id: 6, checklist_type: "sanitation", item_name: "Sanitize sink and drain",        is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 7, checklist_type: "sanitation", item_name: "Empty trash bins",               is_complete: true,  completed_by: "bob",   completed_at: "2026-03-21T06:50:00", notes: null },
  { id: 8, checklist_type: "sanitation", item_name: "Wipe down equipment handles",    is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
];

export const MOCK_CLEANING_TASKS = [
  { id: 1,  area: "Prep surfaces",       action: "Sanitize all prep surfaces and countertops",  is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T06:25:00", notes: null },
  { id: 2,  area: "Ovens",               action: "Clean oven interiors and racks",              is_complete: true,  completed_by: "bob",   completed_at: "2026-03-21T06:40:00", notes: null },
  { id: 3,  area: "Mixing equipment",    action: "Wash mixing bowls, utensils and attachments", is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 4,  area: "Floor",               action: "Sweep and mop bakery floor",                  is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 5,  area: "Display cases",       action: "Clean and sanitize display cases",            is_complete: true,  completed_by: "diana", completed_at: "2026-03-21T07:05:00", notes: null },
  { id: 6,  area: "Sinks and drains",    action: "Sanitize sinks and clear drains",             is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 7,  area: "Trash and recycling", action: "Empty all trash and recycling bins",          is_complete: true,  completed_by: "bob",   completed_at: "2026-03-21T06:55:00", notes: null },
  { id: 8,  area: "Equipment handles",   action: "Wipe down all equipment handles and knobs",   is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 9,  area: "Storage areas",       action: "Tidy and clean storage shelves",              is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
  { id: 10, area: "Restrooms",           action: "Clean and restock restrooms",                 is_complete: false, completed_by: null,    completed_at: null,                  notes: null },
];

// HACCP = Hazard Analysis and Critical Control Points (food-safety compliance).
// Frontend-only structure — no backend endpoint yet.
// Items use string ids; swap to integer ids from DB when backend endpoint is added.
export const MOCK_HACCP_GROUPS = [
  {
    id: "temperature",
    category: "Temperature Monitoring",
    items: [
      { id: "h1", item_name: "Oven temp verified ≥ 200°C before use",     is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T06:00:00" },
      { id: "h2", item_name: "Walk-in fridge temp logged (≤ 4°C)",        is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T06:05:00" },
      { id: "h3", item_name: "Freezer temp logged (≤ -18°C)",             is_complete: false, completed_by: null,    completed_at: null },
      { id: "h4", item_name: "Delivery temperature checked on receipt",    is_complete: false, completed_by: null,    completed_at: null },
    ],
  },
  {
    id: "allergens",
    category: "Allergen Controls",
    items: [
      { id: "h5", item_name: "Allergen matrix posted and visible",             is_complete: true,  completed_by: "diana", completed_at: "2026-03-21T07:00:00" },
      { id: "h6", item_name: "Allergen-free utensils stored separately",       is_complete: true,  completed_by: "diana", completed_at: "2026-03-21T07:00:00" },
      { id: "h7", item_name: "Product labels checked for allergen accuracy",   is_complete: false, completed_by: null,    completed_at: null },
    ],
  },
  {
    id: "hygiene",
    category: "Personal Hygiene",
    items: [
      { id: "h8",  item_name: "All staff hair nets / hats in place",    is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T05:55:00" },
      { id: "h9",  item_name: "Gloves available at all prep stations",  is_complete: true,  completed_by: "bob",   completed_at: "2026-03-21T06:00:00" },
      { id: "h10", item_name: "Hand washing compliance checked",        is_complete: false, completed_by: null,    completed_at: null },
    ],
  },
  {
    id: "cross_contamination",
    category: "Cross-Contamination Prevention",
    items: [
      { id: "h11", item_name: "Colour-coded chopping boards in correct stations", is_complete: true,  completed_by: "bob", completed_at: "2026-03-21T06:10:00" },
      { id: "h12", item_name: "Raw and ready-to-eat items stored separately",     is_complete: false, completed_by: null,  completed_at: null },
      { id: "h13", item_name: "Surface sanitizer concentration verified",          is_complete: false, completed_by: null,  completed_at: null },
    ],
  },
  {
    id: "date_labeling",
    category: "Date Labeling & FIFO",
    items: [
      { id: "h14", item_name: "All fridge products labeled with prep date", is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T06:30:00" },
      { id: "h15", item_name: "FIFO rotation applied in storage",           is_complete: true,  completed_by: "alice", completed_at: "2026-03-21T06:30:00" },
      { id: "h16", item_name: "Expired items removed and disposed",         is_complete: false, completed_by: null,    completed_at: null },
    ],
  },
  {
    id: "pest_control",
    category: "Pest Control",
    items: [
      { id: "h17", item_name: "Pest entry points checked and sealed", is_complete: false, completed_by: null, completed_at: null },
      { id: "h18", item_name: "Bait stations checked and logged",     is_complete: false, completed_by: null, completed_at: null },
    ],
  },
  {
    id: "equipment",
    category: "Equipment Calibration",
    items: [
      { id: "h19", item_name: "Oven thermometer calibrated this week",       is_complete: true,  completed_by: "diana", completed_at: "2026-03-17T09:00:00" },
      { id: "h20", item_name: "Scales zeroed and verified before use",       is_complete: true,  completed_by: "bob",   completed_at: "2026-03-21T06:00:00" },
      { id: "h21", item_name: "Probe thermometer sanitized after each use",  is_complete: false, completed_by: null,    completed_at: null },
    ],
  },
];
