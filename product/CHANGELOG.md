# Product Changelog

## v3.0 — V3-201 Research Workbench (2026-08-06)

**Milestone:** V3-201  
**Architecture:** [docs/apex/APEX-018_V3-201_Research_Workbench.md](../docs/apex/APEX-018_V3-201_Research_Workbench.md)

### Research Workbench (V3-201)

- Research › Workbench (Single Stock tab) — 7-question research workflow, Investment View Hero
- Reuses `DecisionContextBundle` → `MorningBriefViewModel` + existing presentation contracts
- Projection only: `research_workspace_from_view_model()`
- Shared Understand framework; Proof overlay reuses `DecisionArtifact` evidence
- Investment Decision: session-only (Watch · Hold · Accumulate Later · Avoid)
- Portfolio handoff preserves back navigation context
- Regression gate: **43 / 43 passing**
- V2 frozen pipeline unchanged

## v3.0 — V3-103 Portfolio Review (2026-08-06)

**Milestone:** V3-103  
**Architecture:** [docs/apex/APEX-017_V3-103_Portfolio_Review.md](../docs/apex/APEX-017_V3-103_Portfolio_Review.md)

### Portfolio Review (V3-103)

- Portfolio › Review — theme-first review queue, explanation headline, healthy reassurance
- Reuses `PortfolioOverviewViewModel`; theme grouping via `portfolio_review_from_view_model()` (projection only)
- Shared Understand framework for theme-level disclosure
- Research handoff: navigation only
- Mark reviewed: session state only
- Regression gate: **32 / 32 passing**
- V2 frozen pipeline unchanged

## v3.0 — V3-102 Holdings Experience (2026-08-06)

**Milestone:** V3-102  
**Architecture:** [docs/apex/APEX-016_V3-102_Holdings_Experience.md](../docs/apex/APEX-016_V3-102_Holdings_Experience.md)

### Holdings Experience (V3-102)

- Portfolio › Holdings — inventory ledger (context bar, table, cards, watchlist)
- Extended `PortfolioOverviewViewModel` with holdings rows; health SSOT reused from V3-101
- Presentation projection only: `holdings_experience_from_view_model()`
- Shared Understand framework for row-level disclosure
- Research row action: navigation only
- Regression gate: **25 / 25 passing**
- V2 frozen pipeline unchanged

## v3.0 — V3-101 Portfolio Command Center (2026-08-06)

**Milestone:** V3-101  
**Architecture:** [docs/apex/APEX-015_V3-101_Portfolio_Command_Center.md](../docs/apex/APEX-015_V3-101_Portfolio_Command_Center.md)

### Portfolio Command Center (V3-101)

- Portfolio › Overview — Health Hero, Action Row, Status Strip, below-fold cards
- Use-case assembly: `assemble_portfolio_overview()` — health evaluation upstream
- Presentation projection only: `portfolio_overview_from_view_model()`
- Shared Understand framework: `understand_popover.py` (Home + Portfolio)
- Regression gate: **16 / 16 passing**
- V2 frozen pipeline unchanged

## v2.0.0 — General Availability (2026-08-06)

**Tag:** `v2.0.0`  
**Release notes:** [product/releases/v2.0.0.md](./releases/v2.0.0.md)

### V2.1-T001 — Test Suite Excellence

- Full test suite: **687 / 687 passing** — zero known failures
- Obsolete Phase 1 static tests replaced with V2 wiring assertions
- Tier-A guardrail allowlists `morning_brief_ui.py` (contract projection)
- Engineering MCP tests aligned with platform tool registry
- No product, analyzer, contract, or UI changes

## v2.0.0-rc1 — Release Candidate (2026-08-06)

**Tag:** `v2.0.0-rc1`  
**Release notes:** [product/releases/v2.0.0-rc1.md](./releases/v2.0.0-rc1.md)

### Release Candidate Hardening (RC-001)

- Unified Review Depth — Today popover reuses `render_decision_depth_panel`
- Render integration tests for Home Command Center, Understand popover, Review Workspace
- Engineering documentation: `docs/apex/APEX-014_V2_Architecture_and_Release.md`
- Full suite triaged — no RC regressions

## APEX V2 Complete

- Home Command Center
- Review Workspace
- Visual Polish
- Performance Improvements
- Accessibility Improvements
- Shared Theme System
- CSS Consolidation

### Performance & Accessibility (V2-004)

- Pre-built `APEX_PARTNER_EXPERIENCE_CSS` bundle replaces runtime CSS concatenation
- `content-visibility: auto` on below-fold sections for render performance
- Focus-visible rings, reduced-motion support, and improved contrast (WCAG basics)
- Semantic landmarks and ARIA attributes on Brief and Review surfaces
- Duplicate hero CSS injection removed from `plan_canvas`
- No contract changes
- No business logic changes

## APEX V2

### Visual Polish (V2-003)

- Shared theme system via `APEX_V2_VISUAL_POLISH_CSS`
- CSS consolidation — single source of truth for shared visual rules
- Premium visual hierarchy across Home Command Center and Review Workspace
- No contract changes
- No business logic changes

### Review Workspace (V2-002)

- Single Review Depth container on Investments
- Reduced scrolling on Review page
- Improved navigation hierarchy (Hero → Plan → Review Depth)
- No contract changes
- No business logic changes

### Home Command Center (V2-001)

- Brief page transformed into Home Command Center
- Inline APS-003–006 removed from Brief; gateway via Help me understand
- Shared contract popover reused

## APEX V1 Milestone

### Implemented

- APS-001 Today's Brief
- APS-002 Hero Recommendation
- APS-003 Recommendation Explanation
- APS-004 Investment Thesis
- APS-005 Business Health
- APS-006 Risk Monitor
