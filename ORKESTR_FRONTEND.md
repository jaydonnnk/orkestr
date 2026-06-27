# Orkestr — Frontend Build Guide
### Build2026 · Saturday 27 June · 9:00 AM – 9:00 PM

---

## 1. What Orkestr is

Orkestr solves the group chat that never resolves: *"where should we eat Friday?" → "idk anywhere" → "you decide" → [three days of silence].*

Each person sets their constraints once (dietary, budget, travel limit). Orkestr's agents negotiate a plan everyone can live with, book the venue automatically, and settle every share without anyone chasing anyone.

**One-line pitch:** Splitwise tracks the bill after you've decided. Orkestr's agents do the deciding, strike the booking, and clear the debt themselves.

**The demo arc — what the user experiences:**
1. Organiser creates a group and sends an invite link
2. Each member sets their constraints (once, saved to profile)
3. App finds a plan — user gets a push notification
4. User reviews the plan, approves their deposit
5. Booking confirmed — everyone gets the ref
6. At the meal, anyone logs extra expenses
7. After the meal, settlement runs — 3 transfers instead of a tangle
8. Everyone approves their transfer — all balances hit zero
9. "Settled ✓" — nobody's chasing anybody

---

## 2. Tech stack

| Layer | Choice |
|---|---|
| Framework | Next.js + React |
| Styling | CSS modules + design tokens (see `orkestr.mdc`) |
| Map | react-leaflet (seeded pins, no live data) |
| Animations | Framer Motion — settlement graph collapse only |
| API calls | `lib/api.js` wrapper (mock flag in `.env.local`) |
| Fonts | Plus Jakarta Sans (display) · Inter (body) — Google Fonts |

**Environment variables:**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK=true   ← flip to false when backend is ready
```

---

## 3. The 14 screens + 1 system state

### Phase 1 — Before the meal

| Screen | Route | Who sees it | Primary action |
|---|---|---|---|
| S1 · Create event | `/create` | Organiser only | Name group, pick date range |
| S2 · Share invite | `/invite/[id]` | Organiser only | Copy link / share to WhatsApp |
| S3 · Set constraints | `/join/[id]` | Each member (once) | Dietary, budget, max travel |
| — Finding your plan | `/waiting/[id]` | Everyone | No action — push notification when ready |
| S5 · Review the plan | `/plan/[id]` | Everyone | Read venue, date, time, per-person cost |
| S6 · Approve + deposit | `/approve/[id]` | Each member | Tap Approve — deposit deducted |
| S7 · Booking confirmed | `/confirmed/[id]` | Everyone | Add to calendar |

### Phase 2 — At the meal

| Screen | Route | Who sees it | Primary action |
|---|---|---|---|
| S8 · Event view | `/event/[id]` | Everyone | View itinerary and booking ref |
| S9 · Log an expense | `/event/[id]/expense` | Anyone | Who paid, amount, what for |
| S10 · Running tab | `/event/[id]/tab` | Everyone | Read-only live list |

### Phase 3 — After the meal

| Screen | Route | Who sees it | Primary action |
|---|---|---|---|
| S11 · Confirm fronted | `/settle/[id]/confirm` | Everyone | Review auto-filled, confirm |
| S12 · See who owes what | `/settle/[id]` | Everyone | View simplified transfers |
| S13 · Approve transfer | `/settle/[id]/approve` | Payers only | Tap Approve — payment fires |
| S14 · Settled | `/settle/[id]/done` | Everyone | Read-only — all zeros |

---

## 4. Screen-by-screen data + API

### S1 · Create event `/create`

**User inputs:** group name, rough date range (1–2 dates), optional activity hint (freeform text)

**On submit:** `POST /api/session/start`

**Returns:**
```json
{ "session_id": "ORK-001", "invite_url": "https://orkestr.app/join/ORK-001" }
```

**On success:** navigate to S2

---

### S2 · Share invite `/invite/[id]`

**Displays:** invite URL as a copyable link + WhatsApp share button

**No API call** — static screen using `session_id` from params

---

### S3 · Set constraints `/join/[id]`

**User inputs (form):**
- Name (text)
- Dietary requirements (multi-select chips: none / vegetarian / halal / no raw fish / other)
- Budget per person (slider: $20–$150, step $10)
- Max travel time (select: 15 / 30 / 45 / 60 min)
- Freeform note (text, optional, 100 char max)

**On submit:** `POST /api/constraints`

**Request body matches person shape:**
```json
{
  "session_id": "ORK-001",
  "id": "P-002",
  "name": "Bob",
  "constraints": {
    "available_days": ["FRI", "SUN"],
    "budget_max": 40,
    "dietary": ["no_raw_fish"],
    "max_travel_min": 30,
    "origin": "Tampines"
  },
  "freeform": "broke this week, somewhere chill, not raw fish"
}
```

**On success:** navigate to `/waiting/[id]`

**Note:** constraints save to profile. On return visits, form pre-fills from saved profile — user just confirms.

---

### System state · Finding your plan `/waiting/[id]`

**No user action.** Display:
- Status text: "Finding your plan..."
- Subtitle: "We'll notify you when it's ready"
- Pulsing status dot (coral, `--color-accent`)

**Poll** `GET /api/status/[id]` every 1500ms:
```json
{ "phase": "negotiating" | "plan_ready" | "booking" | "confirmed" }
```

When `phase === "plan_ready"` → navigate to S5

---

### S5 · Review the plan `/plan/[id]`

**Fetch:** `GET /api/plan/[id]`

**Displays (from plan shape):**
```json
{
  "plan_id": "PLAN-1",
  "title": "Korean BBQ + arcade",
  "day": "FRI",
  "time": "19:30",
  "venue": { "name": "Seoul Garden", "lat": 1.3010, "lng": 103.8480 },
  "activity": { "name": "Timezone @ VivoCity", "lat": 1.2643, "lng": 103.8222 },
  "total_cost": 400,
  "per_person": 80
}
```

**UI elements:**
- Map with two seeded pins: venue + activity (react-leaflet, static zoom)
- Venue card: name, address, halal/veg tags, time, table size
- Activity card: name, location
- Cost summary: total + per person (Inter tabular-nums)
- Booking ref pill (amber, `--color-amber-light`)
- "Approve plan" CTA button (coral, full-width)

**On CTA tap:** navigate to S6

---

### S6 · Approve + deposit `/approve/[id]`

**Displays:**
- Plan summary (venue, date, time)
- Your share: `$80.00` — large, Inter 600 tabular-nums
- Mandate summary: "Seoul Garden has locked in your price and table. Approving releases your $80 deposit."
- Booking ref: `SG-2026-0627-77`
- "Approve $80.00" primary button (coral)
- "View plan details" tertiary button

**On approve:** `POST /api/approve/[session_id]` with `{ "person_id": "P-002" }`

**Poll** `GET /api/status/[id]` — when all members approved → navigate to S7

---

### S7 · Booking confirmed `/confirmed/[id]`

**Fetch:** `GET /api/handshake/[id]` — use only: `booking_ref`, `status`, `merchant`

**Displays:**
- "Booking confirmed" amber badge
- Booking ref pill: `SG-2026-0627-77`
- Venue name, date, time, table size
- "Add to calendar" button (secondary)
- Group avatar row (5 avatars, all showing approved state)

---

### S8 · Event view `/event/[id]`

**Same data as S7 plan.** Resting state for the day of the event.

**Displays:**
- Itinerary card: venue → time → activity
- Map (same seeded pins as S5)
- Booking ref
- "+ Log expense" floating button (coral)

---

### S9 · Log an expense `/event/[id]/expense`

**User inputs:**
- Who paid (avatar selector — one of the 5 members)
- Amount (number input, `$` prefix)
- Description (text: "arcade credit", "drinks", etc.)
- Split (toggle: evenly / custom)
- If custom: per-person amount inputs

**On submit:** `POST /api/expense/[id]`

**On success:** navigate back to S10

---

### S10 · Running tab `/event/[id]/tab`

**Fetch:** `GET /api/expenses/[id]`

**Displays:** list of logged expenses, each showing:
- Who paid (avatar + name)
- Amount (amber, tabular-nums)
- Description
- Split summary ("split 5 ways · $20/person")

Read-only. Anyone can tap "+ Log expense" to add more.

---

### S11 · Confirm fronted `/settle/[id]/confirm`

**Fetch:** `GET /api/settlement/[id]` — use `fronted` object only

**Displays:** list of what each person fronted (auto-filled from logged expenses)

```json
"fronted": { "P-001": 240, "P-002": 100, "P-003": 60, "P-004": 0, "P-005": 0 }
```

Each row: avatar + name + amount. Editable if something was missed.

**On confirm:** `POST /api/settle/[id]` with confirmed fronted amounts

---

### S12 · See who owes what `/settle/[id]`

**Fetch:** `GET /api/settlement/[id]`

**Full settlement shape:**
```json
{
  "fronted":  { "P-001": 240, "P-002": 100, "P-003": 60, "P-004": 0, "P-005": 0 },
  "shares":   { "P-001": 80, "P-002": 80, "P-003": 80, "P-004": 80, "P-005": 80 },
  "net":      { "P-001": 160, "P-002": 20, "P-003": -20, "P-004": -80, "P-005": -80 },
  "transfers": [
    { "from": "P-004", "to": "P-001", "amount": 80, "rail": "x402", "status": "pending", "tx_hash": null, "latency_ms": 1100 },
    { "from": "P-005", "to": "P-001", "amount": 80, "rail": "x402", "status": "pending", "tx_hash": null, "latency_ms": 1300 },
    { "from": "P-003", "to": "P-002", "amount": 20, "rail": "x402", "status": "pending", "tx_hash": null, "latency_ms": 900 }
  ],
  "net_after": { "P-001": 0, "P-002": 0, "P-003": 0, "P-004": 0, "P-005": 0 }
}
```

**Displays:**
- 3 transfer rows: "Dave owes Alice $80", "Eve owes Alice $80", "Carol owes Bob $20"
- Each row: from-avatar → amount → to-avatar
- Amounts in amber tabular-nums
- "Approve your transfer" CTA (visible to payers only)

---

### S13 · Approve transfer `/settle/[id]/approve`

**Visible to payers only** (Dave, Eve, Carol in the demo scenario)

**Displays:**
- "You owe [name] $[amount]"
- Amount large (Inter 600, 32px, tabular-nums)
- Transfer detail: to whom, via x402
- "Approve $80.00" primary button (coral)

**On approve:** `POST /api/settle/[id]` with `{ "person_id": "P-004" }`

**Poll** `GET /api/status/[id]` — when all transfers `status === "settled"` → navigate to S14

---

### S14 · Settled `/settle/[id]/done`

**Fetch:** `GET /api/settlement/[id]` — use `net_after` (all zeros) and `transfers` (all `status: "settled"`)

**Displays:**
- Near-black card (`--color-settled-bg`)
- Amber seal circle with ✓
- "Everyone's square" (Plus Jakarta Sans, 700, white)
- Tx hash + timestamp (Inter, 10px, muted)
- Audit row: 3 transfers, each with amount + hash

---

## 5. Mock data file

Create `lib/mockData.js` before the hackathon. All screens import from here when `NEXT_PUBLIC_USE_MOCK=true`.

```js
export const mockSession = {
  session_id: "ORK-001",
  invite_url: "https://orkestr.app/join/ORK-001"
}

export const mockPersonas = [
  { id: "P-001", name: "Alice", avatar: "A", color: "#FBF0EC", textColor: "#B03A1A",
    constraints: { available_days: ["FRI","SAT"], budget_max: 120, dietary: [], max_travel_min: 45, origin: "Bugis" },
    freeform: "down for anything fun, happy to book" },
  { id: "P-002", name: "Bob", avatar: "B", color: "#FDF4E3", textColor: "#7A5500",
    constraints: { available_days: ["FRI","SUN"], budget_max: 40, dietary: ["no_raw_fish"], max_travel_min: 30, origin: "Tampines" },
    freeform: "broke this week, somewhere chill, not raw fish" },
  { id: "P-003", name: "Carol", avatar: "C", color: "#F7F6F3", textColor: "#3D3A35",
    constraints: { available_days: ["FRI"], budget_max: 90, dietary: ["vegetarian"], max_travel_min: 40, origin: "Clementi" },
    freeform: "needs veg options, loves a good arcade" },
  { id: "P-004", name: "Dave", avatar: "D", color: "#FBF0EF", textColor: "#8B2020",
    constraints: { available_days: ["FRI","SAT"], budget_max: 100, dietary: [], max_travel_min: 60, origin: "Jurong" },
    freeform: "anywhere with good meat" },
  { id: "P-005", name: "Eve", avatar: "E", color: "#F0EEE9", textColor: "#4A4740",
    constraints: { available_days: ["FRI","SAT"], budget_max: 80, dietary: ["halal"], max_travel_min: 30, origin: "HarbourFront" },
    freeform: "halal please, walkable area" }
]

export const mockPlan = {
  plan_id: "PLAN-1",
  title: "Korean BBQ + arcade",
  day: "FRI",
  time: "19:30",
  venue: { name: "Seoul Garden", address: "VivoCity #03-01", lat: 1.3010, lng: 103.8480, tags: ["halal","vegetarian"] },
  activity: { name: "Timezone @ VivoCity", lat: 1.2643, lng: 103.8222 },
  total_cost: 400,
  per_person: 80,
  booking_ref: "SG-2026-0627-77",
  mandate_status: "co-signed"
}

export const mockExpenses = [
  { id: "EXP-1", paid_by: "P-001", amount: 240, description: "Dinner — KBBQ set", split: "even" },
  { id: "EXP-2", paid_by: "P-002", amount: 100, description: "Arcade credit", split: "even" },
  { id: "EXP-3", paid_by: "P-003", amount: 60, description: "Drinks", split: "even" }
]

export const mockSettlement = {
  fronted:  { "P-001": 240, "P-002": 100, "P-003": 60, "P-004": 0, "P-005": 0 },
  shares:   { "P-001": 80, "P-002": 80, "P-003": 80, "P-004": 80, "P-005": 80 },
  net:      { "P-001": 160, "P-002": 20, "P-003": -20, "P-004": -80, "P-005": -80 },
  transfers: [
    { from: "P-004", to: "P-001", amount: 80, rail: "x402", status: "pending", tx_hash: null, latency_ms: 1100 },
    { from: "P-005", to: "P-001", amount: 80, rail: "x402", status: "pending", tx_hash: null, latency_ms: 1300 },
    { from: "P-003", to: "P-002", amount: 20, rail: "x402", status: "pending", tx_hash: null, latency_ms: 900 }
  ],
  net_after: { "P-001": 0, "P-002": 0, "P-003": 0, "P-004": 0, "P-005": 0 }
}

export const mockSettled = {
  ...mockSettlement,
  transfers: [
    { from: "P-004", to: "P-001", amount: 80, rail: "x402", status: "settled", tx_hash: "0x4a2f9c", latency_ms: 1100 },
    { from: "P-005", to: "P-001", amount: 80, rail: "x402", status: "settled", tx_hash: "0x7b3e1d", latency_ms: 1300 },
    { from: "P-003", to: "P-002", amount: 20, rail: "x402", status: "settled", tx_hash: "0x2c8f4a", latency_ms: 900 }
  ]
}
```

---

## 6. API wrapper — `lib/api.js`

```js
import * as mock from './mockData'

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true'
const BASE = process.env.NEXT_PUBLIC_API_URL

export async function startSession(data) {
  if (USE_MOCK) return mock.mockSession
  const res = await fetch(`${BASE}/api/session/start`, { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } })
  return res.json()
}

export async function submitConstraints(data) {
  if (USE_MOCK) return { ok: true }
  const res = await fetch(`${BASE}/api/constraints`, { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } })
  return res.json()
}

export async function getStatus(sessionId) {
  if (USE_MOCK) return { phase: 'plan_ready' }
  const res = await fetch(`${BASE}/api/status/${sessionId}`)
  return res.json()
}

export async function getPlan(sessionId) {
  if (USE_MOCK) return mock.mockPlan
  const res = await fetch(`${BASE}/api/plan/${sessionId}`)
  return res.json()
}

export async function approvePlan(sessionId, personId) {
  if (USE_MOCK) return { ok: true }
  const res = await fetch(`${BASE}/api/approve/${sessionId}`, { method: 'POST', body: JSON.stringify({ person_id: personId }), headers: { 'Content-Type': 'application/json' } })
  return res.json()
}

export async function getExpenses(sessionId) {
  if (USE_MOCK) return mock.mockExpenses
  const res = await fetch(`${BASE}/api/expenses/${sessionId}`)
  return res.json()
}

export async function logExpense(sessionId, data) {
  if (USE_MOCK) return { ok: true }
  const res = await fetch(`${BASE}/api/expense/${sessionId}`, { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } })
  return res.json()
}

export async function getSettlement(sessionId) {
  if (USE_MOCK) return mock.mockSettlement
  const res = await fetch(`${BASE}/api/settlement/${sessionId}`)
  return res.json()
}

export async function approveTransfer(sessionId, personId) {
  if (USE_MOCK) return { ok: true }
  const res = await fetch(`${BASE}/api/settle/${sessionId}`, { method: 'POST', body: JSON.stringify({ person_id: personId }), headers: { 'Content-Type': 'application/json' } })
  return res.json()
}
```

---

## 7. Key components

### `PlanCanvas`
Renders S5 (Review the plan). Props: `plan` object. Shows map with two pins, venue card, activity card, cost summary. Map uses react-leaflet with seeded lat/lng — no live geocoding.

### `SettlementGraph`
Renders S12 (See who owes what). Props: `transfers` array, `personas` array. Shows 3 transfer rows with from/to avatars and amounts. On settle, animate amounts ticking to zero — Framer Motion, 300ms stagger per row.

### `ApproveButton`
Shared between S6 and S13. Props: `amount`, `label`, `onApprove`, `loading`. Full-width coral button, 48px min-height. Shows spinner while `loading`. Disabled after tap to prevent double-submit.

### `SettledPassport`
Renders S14. Props: `transfers` (all settled), `timestamp`. Near-black card, amber seal, tx hashes in Inter 10px muted.

---

## 8. Design system

All colour tokens, typography, spacing, border radius, and button states are defined in:

```
.cursor/rules/orkestr.mdc
```

**Typefaces** (add to `_app.js` or `layout.tsx`):
```html
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet" />
```

**Key rules to remember while building:**
- `font-variant-numeric: tabular-nums` on every financial amount
- `min-height: 48px` on every tappable element
- `font-size: 16px` on all text inputs (prevents iOS zoom)
- Coral (`--color-accent`) on one element per screen only
- Amber (`--color-amber`) for financial amounts and booking confirmed states only
- No box-shadows — elevation is surface contrast only

---

## 9. Folder structure (frontend only)

```
frontend/
  app/
    create/page.tsx
    invite/[id]/page.tsx
    join/[id]/page.tsx
    waiting/[id]/page.tsx
    plan/[id]/page.tsx
    approve/[id]/page.tsx
    confirmed/[id]/page.tsx
    event/[id]/
      page.tsx
      expense/page.tsx
      tab/page.tsx
    settle/[id]/
      confirm/page.tsx
      page.tsx
      approve/page.tsx
      done/page.tsx
  components/
    PlanCanvas.tsx
    SettlementGraph.tsx
    ApproveButton.tsx
    SettledPassport.tsx
    Avatar.tsx
    ExpenseRow.tsx
    TransferRow.tsx
    StatusDot.tsx
  lib/
    api.js
    mockData.js
  .cursor/
    rules/
      orkestr.mdc
  .env.local
```
