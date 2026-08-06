# Product Changelog

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
