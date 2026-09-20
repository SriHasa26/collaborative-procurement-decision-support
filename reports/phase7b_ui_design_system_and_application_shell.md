# Phase 7B — UI Design System and Application Shell

**Date:** 2026-09-14
**Scope:** Establish a professional visual design system, a responsive application shell (sidebar + top bar), reusable UI components, decision-state visual language, and redesigned (but still non-functional) placeholder pages. No real analysis form, no API integration beyond Phase 7A's existing connectivity check, no authentication, no backend logic changes.

---

## 1. Purpose

Phase 7A produced a working, but visually bare, frontend skeleton (plain links, unstyled placeholder text). Phase 7B's job is to give the application a real, professional visual identity and a scalable component/styling foundation that Phases 7C–7H (dashboard, analysis workflow, results, history, full API integration) can build on without needing a visual redesign later.

## 2. Scope

Implemented: design tokens, global typography/reset, a responsive `AppLayout` (`Sidebar` + `TopBar`), nine reusable common components, a decision-state visual language for the backend's four `DecisionState` values, and redesigned Home/Analyze/Results/History/NotFound pages. **Not** implemented (unchanged from Phase 7A's placeholders in substance, only in presentation): the real procurement form, any `POST /procurement/analyze` call from a page, any `GET /procurement/runs` or `GET /procurement/runs/{run_id}` call, authentication, Supabase/Firebase, or any backend/database change.

## 3. Design Principles

Following this phase's own design direction: clean spacing and hierarchy over decoration; a restrained, professional palette (no neon, no gradients, no glassmorphism); subtle, functional motion only (hover/nav transitions, one loading spinner); and — specific to this project's domain — visual honesty. The Home page's hero copy and a dedicated "trust note" explicitly state the system is rule-based and evidence-driven, not an AI or autonomous-ordering product, and that savings are never guaranteed; no page anywhere claims or implies otherwise.

## 4. Color/Design Token System

`frontend/src/styles/variables.css` defines every color, spacing, radius, shadow, and typography value used anywhere in the app as a CSS custom property under `:root` — no component hardcodes a raw color or pixel value. Semantic color groups: `--color-primary`/`-hover`/`-light` (brand blue), `--color-secondary` (dark neutral accent), `--color-success`/`-warning`/`-danger`/`-info` each with a `-light`/`-border` pair (used for badges and state panels), a neutral scale (`--color-background`, `--color-surface`, `--color-surface-alt`, `--color-border`, `--color-border-strong`), and text tokens (`--color-text-primary`/`-secondary`/`-muted`/`-on-primary`). Spacing (`--spacing-xs` through `-2xl`), radius (`-sm`/`-md`/`-lg`/`-full`), shadow (`-sm`/`-md`/`-lg`), and layout tokens (`--sidebar-width`, `--topbar-height`, `--content-max-width`) complete the system. Breakpoints are documented as comments in the same file (CSS custom properties cannot be used inside `@media` conditions) and the same four px values (1440/1024/768/375, per Section 10) are used consistently in `layout.css`/`components.css`/`global.css`'s media queries.

## 5. Typography System

Defined in `global.css` as named classes rather than raw heading tags, so the same visual hierarchy applies consistently regardless of the underlying HTML element: `.page-title` (used for the `<h1>` on every real page), `.section-title` (`<h2>`-level), `.card-title`, `.text-body`, `.text-small`, `.text-muted`, and `.text-label` (uppercase, letter-spaced, used for small tags like "Developer diagnostic" and "Planned for a later phase"). Font stack is the existing Phase 7A system-font stack (`system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`) — no external font dependency was added, per this phase's explicit instruction.

## 6. Layout Architecture

```
AppLayout (frontend/src/components/layout/AppLayout.jsx)
├── Sidebar (brand + primary navigation, NavLink-based active state)
├── app-main
│   ├── TopBar (mobile menu toggle + current section title)
│   └── page content (React Router's <Outlet/>, max-width constrained, centered)
```
`AppLayout` supersedes Phase 7A's bare `Layout.jsx` (deleted this phase — see Section 13). It owns exactly one piece of component-local state, `isMobileNavOpen` (plain `useState`, not a state-management library), toggled by `TopBar`'s hamburger button and closed by `Sidebar`'s own nav-link `onClick` handlers (not a route-watching `useEffect` — an early version did this via effect and `oxlint` correctly flagged the `setState`-in-effect pattern as unnecessary; the fix ties the state change directly to the user interaction that causes it). `frontend/src/routes/AppRoutes.jsx` was updated to render `AppLayout` instead of `Layout` — the route table itself (paths and page components) is byte-for-byte unchanged from Phase 7A.

## 7. Reusable Components

`frontend/src/components/common/`:

| Component | Purpose |
|---|---|
| `Button` | Renders a real `<button>` for in-page actions, or a router `<Link>` (still styled as a button) when a `to` prop is given — navigation never uses a manual `onClick(navigate)`. |
| `Card` | Generic bordered/shadowed surface container. |
| `Badge` | Generic small status pill (5 variants: neutral/success/warning/danger/info); icon glyphs are `aria-hidden` since the label text always carries the meaning. |
| `StatusBadge` | Thin wrapper over `Badge` for future generic named statuses (e.g. a run's `run_status`) — kept separate from the decision-state-specific component below. |
| `DecisionStateBadge` / `DecisionStateCard` / `decisionStateMeta.js` | The decision-state visual language — see Section 8. |
| `PageHeader` | Title + description + optional action(s), used at the top of every real page. |
| `EmptyState` | "Nothing here yet" presentation, used by Results/History/NotFound. |
| `LoadingState` | Small spinner + label; used today only by `BackendStatusCheck`. |
| `ErrorState` | Application/network error presentation — deliberately distinct from `DecisionStateCard`'s ABSTAIN styling (Section 8). |
| `WorkflowSteps` | Reusable numbered step-flow, used by Home ("how it works") and Analyze ("analysis workflow") with different step data. |

`frontend/src/components/layout/`: `AppLayout`, `Sidebar`, `TopBar` (Section 6). No component was created without a genuine, immediate use in this phase's own pages — e.g. a `src/utils/` folder was still not created (as in Phase 7A), since nothing in this phase needs a shared non-UI helper.

## 8. Decision-State Visualization

`decisionStateMeta.js` is the single source of truth mapping all four backend `DecisionState` values (`backend/models/enums.py`) to a label, color variant, glyph, one-line summary, and explanatory sentence:

| State | Variant | Summary |
|---|---|---|
| `BUY_TOGETHER` | success (green) | Recommended |
| `WAIT_OR_EXPAND_GROUP` | warning (amber) | Conditional |
| `DO_NOT_BUY_TOGETHER` | danger (muted red) | Not recommended |
| `ABSTAIN` | **info (indigo)** | Insufficient evidence |

**ABSTAIN deliberately uses the neutral "info" palette, never "danger."** This is the phase's own explicit, critical requirement: ABSTAIN means the system lacks sufficient evidence, which must never look like an application error. `ErrorState` (Section 7) uses the danger/red palette instead, and is visually and semantically distinct — it is reserved for genuine application/network failures (used today only inside `BackendStatusCheck` when the health check itself fails), never for a legitimate ABSTAIN decision. Meaning is never carried by color alone: every badge pairs an `aria-hidden` glyph with a real text label, and `DecisionStateCard` additionally shows a full explanatory sentence.

## 9. Page-by-Page Implementation

- **HomePage**: hero (title, honest capability description, dual CTA to `/analyze` and `/history`, a "trust note" callout explicitly disclaiming AI/autonomous-ordering/guaranteed-savings framing) → "How the system works" (`WorkflowSteps`, 5 steps) → "Decision transparency" (a `DecisionStateCard` grid for all four states) → a restyled (not re-logic'd) `BackendStatusCheck`, now placed inside a clearly labeled "Developer diagnostic" card at the bottom rather than at the top of the page.
- **AnalysisPage**: `PageHeader`, an "Analysis workflow" `WorkflowSteps` (Validation → Eligibility → Compatibility → Group Evaluation → Final Selection), and five `Card`-based placeholder sections (Procurement Context, Vendor Information, Demand Information, Geographic Information, Constraints) — each names what it will collect and shows a dashed-border `.placeholder-panel` with descriptive text only. No `<input>`, `<select>`, or `<form>` element exists anywhere on this page.
- **ResultsPage**: `PageHeader`, `EmptyState` ("No analysis results yet" + CTA back to `/analyze`), and a plain bulleted list (inside a `Card`) describing what a future results view will include — no numbers, no chart, no mock decision badge.
- **HistoryPage**: `PageHeader`, `EmptyState` + CTA, and a real `<table>` with real column headers (Run ID / Created At / Commodity / Status) and a single "No runs recorded yet." row — an honest empty table, not fabricated rows.
- **NotFoundPage**: a large "404" numeral, a clear message, and a `Button` back to Home.

## 10. Responsive Strategy

Verified conceptually and via the dev server at the four required widths:

| Breakpoint | Behavior |
|---|---|
| ~1440px / desktop | Sidebar fixed at `--sidebar-width` (248px), content centered under `--content-max-width` (1200px) with margin either side. |
| ~1024px (`layout.css`'s `max-width: 1024px` query) | Sidebar becomes an off-canvas drawer (`transform: translateX(-100%)`, slides in via `.is-open`), a backdrop appears behind it, `TopBar`'s hamburger button becomes visible. |
| ~768px | Content padding reduces (`--spacing-lg`→`--spacing-md`), `.page-header` and its actions stack vertically, workflow steps stack vertically, decision-card grid collapses via `auto-fit`/`minmax`. |
| ~375px | Sidebar drawer width caps at `min(248px, 82vw)` so it never exceeds the viewport. |

No fixed-width element forces horizontal scrolling at any of the four widths (verified by inspection of every `width`/`min-width` declaration — none exceeds a responsive/percentage bound at small screens).

## 11. Accessibility Considerations

Semantic HTML throughout: `<nav aria-label="Main navigation">` for the sidebar, real `<button>` elements for the mobile menu toggle (`aria-expanded`, `aria-controls="primary-sidebar"`, `aria-label`) and every in-page action, `<table>`/`<th scope="col">` for the history placeholder, `role="status"`/`aria-live="polite"` on `LoadingState`, `role="alert"` on `ErrorState`, `role="status"` on `EmptyState`. A global `:focus-visible` rule gives every interactive element a visible focus ring. All decorative glyphs (badge icons, the "ⓘ" trust-note icon, workflow step numbers) are `aria-hidden="true"` and always paired with real text — no icon carries meaning alone. `@media (prefers-reduced-motion: reduce)` collapses all transition/animation durations to near-zero globally. No `<input>` placeholder pretends to be a functional form control (Section 9).

## 12. Files Created

**Styles:** `frontend/src/styles/variables.css`, `layout.css`, `components.css` (in addition to the existing, now-updated `global.css`).
**Components:** `frontend/src/components/common/Button.jsx`, `Card.jsx`, `Badge.jsx`, `StatusBadge.jsx`, `decisionStateMeta.js`, `DecisionStateBadge.jsx`, `DecisionStateCard.jsx`, `PageHeader.jsx`, `EmptyState.jsx`, `LoadingState.jsx`, `ErrorState.jsx`, `WorkflowSteps.jsx`; `frontend/src/components/layout/AppLayout.jsx`, `Sidebar.jsx`, `TopBar.jsx`.
**Report:** this file.

## 13. Files Modified

`frontend/src/main.jsx` (import the 3 new stylesheets in order, alongside the existing `global.css`), `frontend/src/routes/AppRoutes.jsx` (render `AppLayout` instead of the deleted `Layout`), `frontend/src/styles/global.css` (replaced with a real reset/typography system), `frontend/src/pages/{HomePage,AnalysisPage,ResultsPage,HistoryPage,NotFoundPage}.jsx` (full content rewrite, still non-functional), `frontend/src/components/common/BackendStatusCheck.jsx` (presentation-only restyle — its `healthCheck()` call, state machine, and dependency on `frontend/src/api/procurementApi.js` are byte-for-byte unchanged).

**Deleted:** `frontend/src/components/layout/Layout.jsx` (superseded by `AppLayout.jsx`, which does everything it did plus the required sidebar/top-bar shell).

**Not modified, confirmed by inspection and `git status`:** `frontend/src/api/client.js`, `frontend/src/api/procurementApi.js`, `frontend/src/config/env.js`, `frontend/.env`/`.env.example`, and every file under `backend/` (`git status --short backend/` returned no output this phase).

## 14. Dependencies Added

**None.** No package was installed this phase — `frontend/package.json` is unchanged from Phase 7A (`react`, `react-dom`, `react-router-dom`, plus Vite/oxlint tooling only). No Tailwind, Material UI, Bootstrap, CSS-in-JS/styled-components, icon library, or state-management library was added; all icons are plain text/Unicode glyphs, not an icon-font/SVG-library dependency.

## 15. Verification Performed

1. `npm run build` — succeeded, 51 modules transformed, zero errors (both before and after a lint-driven fix, see Section 6).
2. `npm run lint` (`oxlint`) — zero warnings/errors on the final code.
3. Started the real Vite dev server and requested all 5 routes (`/`, `/analyze`, `/results`, `/history`, `/some-invalid-route`) — each returned `200` with the correct page shell (SPA routing intact).
4. Requested the transformed source of 5 key modules (`main.jsx`, `App.jsx`, `AppRoutes.jsx`, `AppLayout.jsx`, `HomePage.jsx`) directly from the dev server and confirmed `200` responses with no `SyntaxError`/`Failed to resolve import`/"Internal server error" markers in the output — no console-breaking import error.
5. Re-ran the full backend test suite: **122 passed, 0 failed, 0 skipped** — unchanged.
6. `git status --short backend/` — no output, confirming zero backend files were touched this phase.
7. Dev server processes were stopped after verification; no server left running.

## 16. Known Limitations

No automated visual/screenshot regression testing was added (not requested, and this phase explicitly avoids new testing frameworks). Responsive behavior was verified via the CSS rules themselves and the dev-server checks above, not a literal browser resize/screenshot at each of the four widths (no headless-browser tool was installed, consistent with Phase 7A's same documented limitation). No dark-mode theme was implemented — a single, restrained light theme was judged sufficient for this phase's scope and not explicitly requested. Color-contrast ratios were chosen from a well-tested palette family (dark text on light tints) but were not run through an automated contrast-checking tool.

## 17. Explicit Scope Boundary

Confirmed **not** implemented this phase: the real procurement analysis form, any call to `analyzeProcurement()`/`getProcurementRuns()`/`getProcurementRun()` from a page (both remain defined-but-uncalled from pages, exactly as Phase 7A left them, aside from the pre-existing `healthCheck()` call inside `BackendStatusCheck`), results/history API integration, authentication, login/signup, Supabase, Firebase, any database or backend business-logic change, ML, real charts backed by data, and any state-management library. No route was added or removed. No `git add`/`commit`/`push` command was run.

---

**Files read for this phase:** `frontend/src/App.jsx`, `frontend/src/routes/AppRoutes.jsx`, `frontend/src/main.jsx`, `frontend/src/components/layout/Layout.jsx`, `frontend/src/components/common/BackendStatusCheck.jsx`, `reports/phase7a_frontend_architecture_and_setup.md`.
**Files created/modified/deleted:** see Sections 12–13.
