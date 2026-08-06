# V3 Holdings Experience — Product & UX Design

**Document ID:** V3-HE-001  
**Version:** 0.1  
**Status:** DRAFT — Phase 1 Design  
**Date:** 2026-08-06  
**Owner:** Product · UX · Architecture  
**Baseline:** V3-101 Portfolio Command Center @ `2df8da1` · v2.0.0 GA (frozen architecture)  
**Parent:** [V3_PORTFOLIO_COMMAND_CENTER.md](./V3_PORTFOLIO_COMMAND_CENTER.md) · [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md)  
**Screen ID:** SCR-P-002 (Portfolio › Holdings)

---

## Design Questions — Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What should the investor see first? | **Inventory summary line** — count, total value, last sync. Not a health hero. Not P&L leaderboard. |
| 2 | What deserves the largest visual emphasis? | The **holdings table** (desktop) or **holding cards** (mobile). Each row answers: symbol, quantity, value, weight. |
| 3 | What actions should be immediately available? | **Search / filter** · **Sort** · **Row → Research** · **Sync** (if stale). No trade execution. No "Analyze" gate. |
| 4 | What belongs above the fold? | Context bar · filter/sort controls · table header + first 6–8 rows (typical portfolio). |
| 5 | What belongs below the fold? | Remaining rows · broker truth footer · optional watchlist section (collapsed). |
| 6 | What should never appear? | Health hero duplicate · allocation dashboard · buy/sell signal columns · manual CRUD inline · CSV paste · gamification · intraday ticker strip. |

**10-second test:** User scans table → can name top 3 holdings by weight → knows quantity and current value for any row they care about.

---

## 1. Objectives

### Primary question (frozen)

> **What exactly do I own?**

### Relationship to Portfolio Command Center (V3-101)

| Surface | Question | Role |
|---------|----------|------|
| **Overview** (SCR-P-001) | Is it healthy? | Verdict + attention + allocation snapshot |
| **Holdings** (SCR-P-002) | What exactly do I own? | Authoritative inventory — quantities, cost, value, weight |

Holdings is the **inventory ledger**. Overview is the **health briefing**. They complement; they do not duplicate.

### Success criteria

| Objective | Measure |
|-----------|---------|
| Inventory clarity | User identifies any holding's qty, avg cost, current value, portfolio weight within 5 seconds |
| Findability | User locates a symbol via search or sort in ≤ 2 interactions |
| Trust | Broker-sourced numbers labeled; stale sync visible; no fabricated fields |
| Calm | No verdict anxiety; no signal spam; muted P&L presentation |
| Continuity | Same sub-nav, theme, and row handoff patterns as Overview |

### Non-objectives (this screen)

- Portfolio health verdict (Overview owns this)
- Daily buy/sell recommendations (Home owns this)
- Full allocation policy editor (You › Policy — future)
- Trade execution or order placement
- Portfolio Doctor monthly report (Doctor sub-tab)
- Inline research depth (Research Workbench handoff)

### Personas served

| Persona | Need met |
|---------|----------|
| Busy professional | Quick lookup: "How many shares of X do I hold?" |
| Disciplined allocator | Weight % and sector tags per row; sort by weight |
| Learning investor | Row-level health chip + Understand without leaving inventory |
| Post-trade validator | Confirm new quantity and weight after a trade |

---

## 2. User Problems

| Problem | Today (legacy Holdings tab) | V3 Holdings Experience |
|---------|----------------------------|------------------------|
| **"What do I own?" buried under CRUD** | Manual entry, CSV upload, paste symbols dominate | Broker-connected inventory is default; CRUD moved to Settings fallback |
| **Analyze gate blocks answer** | User must click "Analyze my portfolio" before useful view | Table renders from sync immediately — no gate |
| **Dashboard fatigue** | Signals table, buy/sell counts, risk metrics compete with inventory | Single-purpose inventory; signals live in Research / Home |
| **Can't find a holding** | Basic dataframe; no search/filter/sort UX | Search, filter chips, column sort |
| **Trust unclear** | Mixed manual + broker sources; LTP refresh in expander | Broker truth footer; sync chip; source badge per row when mixed |
| **Mobile unusable** | Wide dataframe horizontal scroll | Card list with primary fields stacked |
| **Health vs inventory conflated** | Analysis scores in same table as qty | Health chip is secondary column; full health story in Overview or row Understand |
| **Watchlist mixed with holdings** | Same table, confusing qty=0 rows | Holdings table qty > 0 only; watchlist collapsed section or separate filter |

---

## 3. Wireframes (ASCII)

### 3.1 Desktop — connected, 12 holdings

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  [ Home ] [ Portfolio ● ] [ Research ] [ Journal ] [ You ]     🟢 Synced 2m  │
├──────────────────────────────────────────────────────────────────────────────┤
│  Overview │ Holdings ● │ Positions │ Wealth │ Doctor                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ CONTEXT BAR (not a hero) ──────────────────────────────────────────────┐ │
│  │  12 holdings · ₹42.8L invested · Last synced 2m ago                     │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  [ 🔍 Search symbol or name… ]     [ Filter ▾ ]  [ Sort: Weight ↓ ▾ ]  Sync  │
│                                                                              │
│  ┌─ HOLDINGS TABLE ──────────────────────────────────────────────────────────┐ │
│  │ Symbol    Name          Qty    Avg      LTP      Value     Weight  Health│ │
│  │ ─────────────────────────────────────────────────────────────────────── │ │
│  │ RELIANCE  Reliance Ind  120    ₹2,410   ₹2,890   ₹3.47L    14.2%   ● OK │ │
│  │ TCS       Tata Consult  85     ₹3,820   ₹4,105   ₹3.49L    14.3%   ● OK │ │
│  │ HDFCBANK  HDFC Bank     200    ₹1,520   ₹1,680   ₹3.36L    13.8%   ⚠ Att│ │
│  │ INFY      Infosys       150    ₹1,450   ₹1,520   ₹2.28L     9.4%   ● OK │ │
│  │ …         (8 more rows)                                                  │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Row actions (on focus / hover):  [ Research → ]  [ Understand ▾ ]           │
│                                                                              │
│  ▾ Watchlist (3 symbols — not held)                                        │
│                                                                              │
│  Zerodha Console is source of truth for quantities, cost basis, and P&L.     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Desktop — filtered (Needs attention)

```text
[ Filter: Needs attention ● ]  [ All ]  [ Sector: Financials ]  [ Clear ]

│ Symbol    …   Weight  Health │
│ HDFCBANK  …   13.8%   ⚠ Att  │
│ WIPRO     …    4.1%   ⚠ Att  │
│                                                              2 of 12 shown │
```

### 3.3 Desktop — broker disconnected

```text
┌─ CONTEXT BAR ───────────────────────────────────────────────────────────────┐
│  Connect broker to see live holdings · or view last saved snapshot (Aug 5)   │
└───────────────────────────────────────────────────────────────────────────────┘

[ Connect Zerodha ]                              [ Open saved snapshot ]

(empty table illustration OR read-only snapshot rows with stale badge)
```

### 3.4 Desktop — row Understand popover (L3)

```text
┌─ RELIANCE — Understand ────────────────────────────────────────┐
│  You hold 120 shares · 14.2% of portfolio                      │
│  ▾ Why this weight matters                                     │
│  ▾ Cost basis vs current value                               │
│  ▾ Health indicator (links to Overview attention if flagged)   │
│  [ Open Research → ]                                           │
└────────────────────────────────────────────────────────────────┘
```

### 3.5 Mobile — card list

```text
┌─────────────────────────┐
│ Portfolio          Sync │
├─────────────────────────┤
│ Overview │ Holdings ●   │
├─────────────────────────┤
│ 12 holdings · ₹42.8L    │
│ Synced 2m ago           │
├─────────────────────────┤
│ [ 🔍 Search…      ]     │
│ [ Filter ] [ Sort ▾ ]   │
├─────────────────────────┤
│ ┌─ RELIANCE ──────────┐ │
│ │ 120 qty · 14.2%     │ │
│ │ ₹3.47L · +₹57.6K    │ │
│ │ ● Healthy      [ → ]│ │
│ └─────────────────────┘ │
│ ┌─ TCS ───────────────┐ │
│ │ …                   │ │
│ └─────────────────────┘ │
│                         │
│ ▾ Watchlist (3)         │
│                         │
│ Broker truth footer     │
└─────────────────────────┘
     [ Home ][ Port ][ … ]
```

---

## 4. Component Hierarchy

```text
PortfolioPageShell (shared with Overview)
├── PrimaryNav (global — 5 items)
├── PortfolioSubNav (Overview | Holdings ● | Positions | Wealth | Doctor)
└── HoldingsExperience (Holdings tab only)
    ├── HoldingsContextBar
    │   ├── SummaryLine (count · invested · sync freshness)
    │   └── DisconnectedBanner (conditional — connect CTA inline)
    ├── HoldingsToolbar
    │   ├── SearchField
    │   ├── FilterChipGroup
    │   ├── SortControl
    │   └── SyncButton (conditional — when stale or explicit refresh)
    ├── HoldingsTableRegion (desktop ≥768px)
    │   ├── HoldingsTableHeader (sortable columns)
    │   └── HoldingsTableBody
    │       └── HoldingsRow (repeat)
    │           ├── SymbolCell
    │           ├── NameCell (truncated)
    │           ├── QuantityCell
    │           ├── AvgCostCell
    │           ├── LTPCell
    │           ├── ValueCell
    │           ├── WeightCell
    │           ├── HealthChip
    │           └── RowActionMenu (Research · Understand)
    ├── HoldingsCardList (mobile <768px)
    │   └── HoldingsCard (repeat — same data, stacked layout)
    ├── WatchlistCollapsible (optional — qty=0 symbols)
    │   └── WatchlistRow (lighter weight — no value/weight)
    ├── HoldingsEmptyState (no holdings · disconnected · filtered empty)
    ├── HoldingsRowUnderstandPopover (shared Understand framework — per row)
    └── BrokerTruthFooter (same copy pattern as Overview)
```

**Render rule (future implementation):** Projection-only contracts assembled in use-case layer. No health scoring or weight math in UI. Reuse shared `UnderstandPopover` pattern from V3-101.

---

## 5. Information Hierarchy

### 5.1 Page-level priority (top → bottom)

| Rank | Element | User need |
|------|---------|-----------|
| 1 | Context bar | Orientation — how many, how much, how fresh |
| 2 | Search / filter / sort | Find a specific holding fast |
| 3 | Symbol + quantity | Core inventory fact |
| 4 | Current value + weight | Economic significance |
| 5 | Avg cost + LTP | Cost basis context (secondary) |
| 6 | Health chip | Interpretive — links to Overview attention |
| 7 | Row actions | Depth on demand |
| 8 | Watchlist | Peripheral — not held |
| 9 | Broker footer | Trust anchor |

### 5.2 Row-level priority (left → right desktop)

```text
Symbol → Name → Qty → Value → Weight → Health → (actions)
         └── Avg / LTP grouped as secondary numeric cluster
```

**Rule:** Weight and value outrank P&L. Unrealized P&L appears in row secondary line or expandable detail — never as the primary sort default.

### 5.3 Cognitive load budget

| Above fold | Below fold |
|------------|------------|
| Context bar | Rows 9+ |
| Toolbar | Watchlist section |
| First 6–8 table rows | Broker footer |
| | Row Understand popover (on demand) |

### 5.4 What Overview already answered — do not repeat

- Portfolio health badge (Healthy / Needs attention)
- Allocation snapshot (Core / Tactical / Cash)
- Attention list narrative
- Standouts (strongest / weakest one-liners)
- Primary CTA ("Review N items")

Holdings may **reference** these via health chips and Understand popover links — never re-render them as page-level cards.

---

## 6. Table Design

### 6.1 Columns (desktop default)

| Column | Source | Format | Sortable | Notes |
|--------|--------|--------|----------|-------|
| **Symbol** | Broker | `RELIANCE` | ✅ | Primary identifier; links to Research |
| **Name** | Instrument master | Truncated 24 chars | ✅ | Tooltip full name |
| **Qty** | Broker | Integer | ✅ | Right-aligned tabular nums |
| **Avg cost** | Broker | `₹2,410` | ✅ | Cost basis per share |
| **LTP** | Broker / live stream | `₹2,890` | ✅ | Muted if market closed |
| **Value** | Computed (qty × LTP) | `₹3.47L` | ✅ default sort | Broker truth inputs |
| **Weight** | Use-case assembly | `14.2%` | ✅ | % of total portfolio value |
| **Health** | Use-case assembly | Chip | ✅ filter | OK · Attention · Unknown |

**Hidden by default (toggle via column picker — Phase 2):** Day P&L · Total P&L · Sector · Exchange

### 6.2 Row states

| State | Visual |
|-------|--------|
| Default | Standard row |
| Hover / focus | Subtle background; row actions visible |
| Attention flagged | Amber health chip; optional left border accent (icon + text, not color alone) |
| Stale data | Muted cells + tooltip "As of {snapshot date}" |
| Selected (keyboard) | Focus ring per V2-004 |

### 6.3 Density

- **Comfortable** (default): 48px row height desktop; 72px card mobile
- **Compact** (user preference — future): 40px rows; persist in You › Display

### 6.4 Empty states

| Condition | Message | CTA |
|-----------|---------|-----|
| Connected · zero holdings | "No equity holdings in your broker account." | Positions tab · Research |
| Disconnected · no snapshot | "Connect Zerodha to see holdings." | Connect |
| Disconnected · snapshot | "Showing saved snapshot from {date}." | Connect · Sync |
| Filter · no matches | "No holdings match these filters." | Clear filters |

---

## 7. Filtering

### 7.1 Filter chips (horizontal toolbar)

| Filter | Behavior |
|--------|----------|
| **All** | Default; clears other filters |
| **Needs attention** | Rows where `health_key = attention` |
| **Healthy** | Rows where `health_key = ok` |
| **Sector** | Dropdown multi-select (from assembly layer sector map) |
| **Core / Tactical** | Policy bucket tag (when policy data available) |

### 7.2 Filter UX rules

- Filters combine with AND logic
- Active filter count badge on Filter button when collapsed
- URL/session persistence optional (Phase 2); default resets on tab leave
- Filter state survives sort changes
- Screen reader announces: "Showing 2 of 12 holdings. Filter: Needs attention."

### 7.3 Search interaction with filters

Search narrows within active filter set. Clearing search does not clear filters.

---

## 8. Sorting

### 8.1 Sort control

- Default: **Weight ↓** (largest position first — answers "what matters most")
- Dropdown options: Symbol A–Z · Value ↓↑ · Weight ↓↑ · Qty ↓↑ · P&L ↓↑ · Health
- Column header click toggles sort on desktop (aria-sort)
- Sort indicator visible on active column

### 8.2 Sort rules

- Stable sort (secondary key: symbol A–Z)
- Missing LTP: sort to bottom with "—" display
- Watchlist excluded from holdings sort (separate section)

---

## 9. Search

### 9.1 Search field

- Placeholder: "Search symbol or name…"
- Debounce 150ms
- Matches: symbol prefix, trading name substring (case insensitive)
- Clear button (×) when non-empty
- Keyboard: `/` focuses search (desktop)

### 9.2 Search results

- Instant filter of table/card list
- No separate results page
- Zero results → filtered empty state
- Highlight matched substring in name column (accessible: aria-label includes match context)

### 9.3 Deep link (future)

`Portfolio › Holdings?symbol=RELIANCE` — scrolls to row, brief highlight (from Overview preview tap)

---

## 10. Health Indicators

### 10.1 Row health chip

| Chip | Meaning | Source |
|------|---------|--------|
| **OK** | No flags from portfolio health assembly | Reuse V3-101 health evaluation per symbol |
| **Attention** | Symbol appears in Overview attention set | Same assembly; not re-computed in UI |
| **Unknown** | Insufficient data (new listing, sync gap) | Neutral chip |

### 10.2 Display rules

- Chip is **secondary** — never the first column
- Tooltip / Understand: one-line reason ("Sector concentration" · "Business health declined")
- Tap chip → Understand popover OR scroll Overview attention (prefer popover on Holdings)
- Do not show numeric "health score" in table (Research owns scores)

### 10.3 Sync with Overview

Health chips must derive from the **same assembly output** as Overview attention list. Single source of truth — no divergent flags between tabs.

---

## 11. Allocation Indicators

### 11.1 Weight column (primary allocation indicator)

- **Weight %** = holding value ÷ total portfolio value
- Bar micro-indicator optional in Weight cell (thin 4px bar, max 20% scale cap for visual)
- Sort by weight default reinforces allocation mental model

### 11.2 Sector tag (secondary — column or chip)

- Small muted tag: `Financials` · `IT` · `Energy`
- Enables sector filter without opening Overview allocation card
- Not a full allocation dashboard — no pie chart on this screen

### 11.3 Policy bucket tag (when available)

- `Core` · `Tactical` · `Cash proxy` from investor policy
- Filter chip only; no drift math inline (Overview Understand owns drift narrative)

### 11.4 What not to show

- Full allocation donut (Overview below fold)
- Rebalance suggestions
- Target vs actual bars per row (Doctor / Policy surfaces)

---

## 12. Actions

### 12.1 Page-level actions

| Action | Trigger | Result |
|--------|---------|--------|
| **Sync** | Toolbar button or global sync chip | Background sync; rows update in place |
| **Connect** | Disconnected banner | Navigate You › Settings › Zerodha |
| **Clear filters** | Empty filter state | Reset chip group |

### 12.2 Row-level actions

| Action | Trigger | Result |
|--------|---------|--------|
| **Open Research** | Row tap (primary) or explicit button | Research › Workbench · symbol context |
| **Understand** | Row secondary button | Row-scoped Understand popover |
| **Copy symbol** | Row menu (optional) | Clipboard; toast confirmation |

### 12.3 Explicitly excluded actions

- Buy / Sell / Place order
- Edit quantity / manual CRUD (Settings fallback only for offline mode)
- "Analyze portfolio" gate
- Remove from portfolio inline
- Share / social

### 12.4 Legacy CRUD migration

| Legacy (current zerodha.py Holdings) | V3 destination |
|--------------------------------------|----------------|
| Manual entry | You › Settings › Portfolio fallback |
| CSV upload | You › Settings › Import |
| Paste Kite symbols | You › Settings › Import |
| Re-save / Clear portfolio | You › Settings › Data |
| Analyze my portfolio button | Removed — table is immediate |
| Signals / risk subsections | Research · Home · Doctor |

---

## 13. Progressive Disclosure

| Layer | Content | Access |
|-------|---------|--------|
| **L0 — Context bar** | Count · total · sync | Always visible |
| **L1 — Table rows** | Symbol · qty · value · weight · health | Always visible |
| **L2 — Secondary numerics** | Avg · LTP · P&L | Row columns or card second line |
| **L3 — Row Understand** | Weight rationale · cost basis · health reason | Explicit tap |
| **L4 — Research Workbench** | Full APS depth | Row handoff |
| **L5 — Overview / Doctor** | Portfolio-level health narrative | Sub-nav |

**Rule:** L0 + L1 answer "what do I own" without any tap. L3 explains; never gates L1.

### 13.1 Watchlist disclosure

- Collapsed by default: "Watchlist (N symbols — not held)"
- Expand reveals lighter rows: symbol · name · last price · Research link
- No weight or health chips for watchlist

---

## 14. Mobile Adaptation

| Aspect | Behavior |
|--------|----------|
| Layout | Card list replaces table |
| Toolbar | Search full width; Filter + Sort on second row |
| Card content | Line 1: Symbol + weight · Line 2: qty + value · Line 3: health chip + chevron |
| Row tap | Whole card → Research |
| Understand | Swipe or overflow menu |
| Sync | In page header next to title |
| Watchlist | Same collapsible |
| Bottom nav | Unchanged 5-item dock |
| Thumb zone | Search and first card in comfortable reach |

**Breakpoint:** `<768px` → cards; `≥768px` → table; `≥1024px` → full column set

---

## 15. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| **Landmarks** | `main` for holdings region; `nav` for toolbar; table `role="grid"` |
| **Table semantics** | `<th scope="col">` · sort aria-sort · row headers on symbol |
| **Search** | `role="search"` · label "Search holdings" |
| **Filters** | Chip group `role="group"` · aria-pressed on toggles |
| **Health chips** | Text label always ("Attention" not color dot alone) |
| **Focus** | Visible `:focus-visible` on rows, chips, sort headers (V2-004) |
| **Keyboard** | Tab through toolbar → table; Enter opens Research; Escape closes popover |
| **Screen reader** | Context bar: "12 holdings, 42 lakh 80 thousand invested, synced 2 minutes ago" |
| **Motion** | `prefers-reduced-motion` — no row highlight animation |
| **Contrast** | WCAG AA; muted P&L ≥ 4.5:1 |
| **Touch targets** | ≥44×44px on cards, chips, sort control |

---

## 16. Performance

| Technique | Application |
|-----------|-------------|
| **Virtualization** | Render window for >50 rows (desktop table) |
| **Debounced search** | 150ms; no full re-assembly on keystroke |
| **Cached snapshot** | Show last sync rows immediately; patch LTP in place |
| **content-visibility** | Watchlist section deferred |
| **No blocking analyze** | Removed legacy analyze path |
| **Sort / filter client-side** | On assembled row contract (typical <100 holdings) |
| **Popover lazy** | Row Understand rendered on first open |
| **Targets** | LCP ≤2.5s cached · search response <100ms · sort <50ms |

### 16.1 Scale assumptions

| Holdings count | Strategy |
|----------------|----------|
| ≤50 | Full render |
| 51–200 | Virtualized table |
| >200 | Virtualized + "showing N" indicator; search encouraged |

---

## 17. Future Extensibility

| Extension | Hook | Phase |
|-----------|------|-------|
| Column picker | Table header menu | V3-103+ |
| Export CSV | Toolbar overflow · audit trail | V3-3 |
| Group by sector | Sort/group toggle | V3-103 |
| Policy bucket column | When Capital Allocation ships | V3-4 |
| Holdings detail drawer | Row expand without leaving tab | V3-103 |
| Multi-broker | Source column + filter | V4 |
| Cost basis lots | Expand row · FIFO detail | V4 |
| Tax unrealized | Column · hidden default | V4 |

**Contract stability:** Row DTO should expose extensible optional fields (`tags`, `sector`, `policy_bucket`, `pnl_day`) without breaking default columns.

**Architecture alignment (future implementation):**

```text
ZerodhaImportResult + health assembly (reuse V3-101)
    → assemble_holdings_experience()  [new use case — NOT in this milestone]
    → holdings_experience_from_view_model()  [projection]
    → HoldingsExperience components  [render-only]
```

---

## Appendix A — State Matrix

| Broker | Holdings | Hero | Table | Primary action |
|--------|----------|------|-------|----------------|
| Connected · synced | >0 | Context bar | Full rows | Search / Research |
| Connected · stale | >0 | Context bar + stale | Rows + stale tooltips | Sync |
| Connected · empty | 0 | Empty state | Hidden | Positions / Research |
| Disconnected · snapshot | >0 | Snapshot banner | Read-only rows | Connect |
| Disconnected · none | 0 | Connect empty | Hidden | Connect |

---

## Appendix B — Acceptance Criteria (Product Review)

- [ ] Primary question answered in 10 seconds without scrolling (typical 12-holding portfolio)
- [ ] No health hero duplicate of Overview
- [ ] No analyze gate before inventory visible
- [ ] Search + sort + filter specified with AND behavior
- [ ] Health chips aligned with Overview attention SSOT
- [ ] Legacy CRUD relocation documented
- [ ] Mobile card layout specified
- [ ] Broker truth footer present
- [ ] Accessibility checklist complete
- [ ] Performance strategy for 50+ rows
- [ ] Future implementation path respects frozen architecture

---

## Appendix C — Related Documents

| Document | Relationship |
|----------|--------------|
| [V3_PORTFOLIO_COMMAND_CENTER.md](./V3_PORTFOLIO_COMMAND_CENTER.md) | Sibling screen · handoff from preview |
| [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md) | SCR-P-002 registration |
| [docs/apex/APEX-015_V3-101_Portfolio_Command_Center.md](../apex/APEX-015_V3-101_Portfolio_Command_Center.md) | Architecture pattern to mirror |
| [APEX_V3_ROADMAP.md](./APEX_V3_ROADMAP.md) | V3-102 milestone tracking |

---

*End of document — awaiting Product Review.*
