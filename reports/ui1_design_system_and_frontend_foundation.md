# UI-1 — Design System and Frontend Architecture Foundation

**Date:** 2026-09-15

## 1. Objective

Establish a premium, cohesive design system and component foundation for the Collaborative Procurement Decision-Support frontend, so later UI phases (landing page, dashboard, analysis wizard, results/history redesigns) can build consistently on shared tokens and primitives — without redesigning any actual page, without touching the backend, and without changing the existing stack (React 19, Vite 8, JavaScript, plain CSS, react-router-dom).

## 2. Existing Frontend Architecture Inspected

Before changing anything: `git status`, `package.json`, `frontend/src/routes/AppRoutes.jsx`, `frontend/src/auth/*`, `frontend/src/api/{client,procurementApi}.js`, and every existing stylesheet and component (`variables.css`, `global.css`, `layout.css`, `components.css`, `analysis.css`, `results.css`, `auth.css`, all of `components/common/`, `components/layout/`, `components/results/`, `components/analysis/`, `components/history/`). Confirmed: the existing architecture already separates `components/{common,layout,analysis,results,history}/`, `pages/`, `api/`, `auth/`, `styles/`, and already uses CSS custom properties exclusively (no scattered magic values) — this is a solid foundation, not a rebuild target. A `components/results/MetricCard.jsx` already existed as a reusable KPI-card primitive; it was extended in place rather than duplicated.

## 3. Design Direction

Deep midnight-navy sidebar + a refined blue primary + cool neutral light surfaces for content + a restrained violet accent used only for small emphasis (eyebrow text, an active-nav indicator, a focus glow) — never covering a large surface, per the brief's "premium, not flashy" principle. This is the common, professional "dark sidebar / light content" pattern used by real analytics SaaS products, applied to this project's own existing shell rather than copied from any specific reference site.

## 4. Design Tokens

All tokens live in `frontend/src/styles/variables.css`. Every existing token **name** was preserved exactly (dozens of rules across five stylesheets reference them) — only values were refined, and new tokens were added alongside:

- **Colors**: refined `--color-primary` (#2f54eb) and `--color-primary-hover`; new `--color-midnight`/`--color-midnight-elevated`/`--color-midnight-border` (the sidebar surface family); new `--color-accent`/`--color-accent-light` (restrained violet); cooler-toned neutrals (`--color-background`, `--color-surface-alt`, `--color-border`, `--color-border-strong`, `--color-text-*`); new `--color-surface-elevated`, `--color-text-on-dark`, `--color-text-muted-on-dark`. Decision-state colors (success/warning/danger/info) kept their exact meaning and near-exact values — these are load-bearing for `DecisionStateBadge`/`ErrorState` and were not reinterpreted.
- **Typography**: added `--font-size-4xl` (future display heading).
- **Spacing**: added `--spacing-3xl` (future hero section).
- **Radius**: added `--radius-xl` (future large feature card).
- **Shadows**: refined `--shadow-sm/md/lg` to a cooler tint; added `--shadow-focus` (colored focus ring) and `--shadow-primary` (a restrained glow under the primary CTA).
- **Layout widths**: added `--content-max-width-wide` (future wide dashboard layout).
- **Z-index layers**: new `--z-topbar`/`--z-backdrop`/`--z-sidebar` (replacing three previously bare numbers in `layout.css`) plus reserved-but-unused `--z-modal`/`--z-tooltip`/`--z-toast` for when those components are actually built.
- **Motion**: new `--ease-standard`/`--ease-emphasized` easing curves, applied to the existing `--transition-fast`/`--transition-base`, plus a new `--transition-slow`.

## 5. Typography

Existing hierarchy (`.page-title`, `.section-title`, `.card-title`, `.text-body`, `.text-small`, `.text-muted`, `.text-label`) preserved exactly. Three additions in `global.css`, not yet applied to any page (for UI-2+): `.eyebrow` (a small, accent-colored kicker label), `.text-display` (a large hero heading), `.text-metric` (a bold, tabular-numeral KPI value style — the concrete expression of the brief's "₹3,732.60 expected savings should visually dominate" principle). The existing system-font stack (`system-ui, -apple-system, "Segoe UI", Roboto...`) was kept rather than adding a webfont: it already renders as a clean, modern, professional sans-serif on every OS, and adding a Google Fonts dependency would be exactly the kind of unnecessary dependency/network cost this phase's own "keep UI-1 lightweight" rule warns against.

## 6. Color System

See Section 4. Decision-state semantics are unchanged and were re-confirmed intact (BUY_TOGETHER → success green, WAIT_OR_EXPAND_GROUP → warning amber, ABSTAIN → info, kept distinct from danger red, DO_NOT_BUY_TOGETHER → danger red) — `decisionStateMeta.js` was not modified.

## 7. Spacing / Layout System

Existing `--spacing-*` scale, `AppLayout`/`Sidebar`/`TopBar` structure, and the `.page-section`/`.app-content-inner` layout primitives are unchanged in structure. `layout.css` was recolored (dark sidebar) and its three z-index numbers were tokenized; the Phase 7G off-canvas/overflow-fix logic (the exact CSS that prevents horizontal scroll on `/history`) was left byte-for-byte untouched, since it is working, tested logic, not a styling concern.

## 8. Component System

| Component | Change |
|---|---|
| `Button.jsx` | Added `isLoading` prop (inline spinner + forced disabled + `aria-busy`); `ghost`/`danger` variants now stylable via existing className construction |
| `Card.jsx` | Added optional `variant` prop (`standard` default = pixel-identical to before, `elevated`, `interactive`, `highlighted`) |
| `MetricCard.jsx` (results/) | Added optional `tone="emphasis"` prop (default unchanged); no existing call site passes it |
| `PageHeader.jsx` | Added `.animate-in` (the one deliberate, sparing entrance animation this phase applies) |
| `Divider.jsx` (new, `components/common/`) | Plain visual separator; not wired into any page yet |
| `Input`/`Select`/`Textarea`/`Label`/`HelperText`/`ErrorText` (new, `components/ui/`) | Styled form primitives for UI-4; **not wired into the existing analysis or auth forms** |

`Badge`/`StatusBadge`/`DecisionStateBadge`/`EmptyState`/`LoadingState`/`ErrorState`/`WorkflowSteps`/`DecisionStateCard` were **not modified** — they already reference design tokens exclusively, so they inherit every color/shadow/spacing refinement automatically, with zero code change needed. Modal and Tooltip were deliberately **not created**: nothing in the current application has a concrete use for either, and building them now would be exactly the "dozens of meaningless one-line abstractions" this phase's own brief warns against. They are reserved z-index layers (`--z-modal`, `--z-tooltip`) away from being built when a real need exists.

## 9. Button System

Variants: `primary` (now carries a restrained `--shadow-primary` glow), `secondary`, `outline` (all three unchanged in behavior), plus new `ghost` (minimal, borderless, for a lower-emphasis action beside a primary one) and `danger` (for a future destructive action — none exists in the app today). States: hover (existing), **new** `:active` (a 1px press-down), **new** explicit `:disabled` (50% opacity, `cursor: not-allowed`, `pointer-events: none` — previously relied on inconsistent browser default styling), focus (existing global `:focus-visible` ring, unchanged), and a new optional loading state (`isLoading` prop) with an inline spinner.

## 10. Card System

`standard` (default, pixel-identical to Phase 7B), `elevated` (stronger shadow, for a future featured panel), `interactive` (hover lift + colored focus ring, for a future clickable card — e.g. a dashboard tile), `highlighted` (primary-tinted border/background, for a future "this is the recommended option" callout). **Note for whoever wires up `card-interactive` next**: since it is currently just a styling variant on a `<div>`, a real clickable card should also add `role="button"`, `tabIndex={0}`, and `Enter`/`Space` key handling (or simply wrap the content in a real `<button>`/`<Link>`) — flagged here so it isn't missed later, not implemented now since nothing uses this variant yet.

## 11. Form System

New primitives in `components/ui/`: `Input`, `Select`, `Textarea` (visually identical to the existing `.form-field input`/`select` styling in `analysis.css`, under standalone classes so they work outside a `.form-field` wrapper too), `Label` and `HelperText`/`ErrorText` (matching `FormField.jsx`'s existing inline label/hint/error styling as reusable components). **The existing analysis form (`AnalysisForm.jsx`, `FormField.jsx`, `FormSection.jsx`) and both auth forms (`SignInPage.jsx`, `SignUpPage.jsx`) were not touched** — they continue to render their own native `<input>`/`<select>` elements exactly as before; these new primitives exist for a future phase (UI-4) to adopt.

## 12. Status System

`Badge`/`StatusBadge`/`DecisionStateBadge` and the four decision-state mappings in `decisionStateMeta.js` are entirely unchanged — already correct, already token-driven, already accessible (icon is `aria-hidden`, label text always carries the meaning).

## 13. Motion System

New `@keyframes fade-in-up` and `.animate-in`/`.animate-in-delay-1`/`.animate-in-delay-2` utility classes in `global.css`, using the new `--ease-standard` curve and `--transition-slow` (320ms) duration. Applied to exactly one place this phase — `PageHeader`, used at the top of every page — deliberately not to every card, per the brief's "avoid animation on every element" instruction. The existing global reduced-motion block (`@media (prefers-reduced-motion: reduce)`, unchanged) already neutralizes every animation/transition site-wide, so this new animation automatically respects the preference with no additional code.

## 14. Responsive Strategy

Unchanged breakpoints (`1024px`, `768px`, `480px`, documented in `variables.css`'s comment). The sidebar's existing off-canvas/backdrop behavior below `1024px` is structurally unchanged, only recolored. Verified fresh via real Playwright at 1440×900 / 820×1180 / 375×812 (Section 20) — zero horizontal overflow anywhere, zero console errors, mobile menu opens/closes correctly.

## 15. Accessibility

No regression: the global `:focus-visible` ring is unchanged and still applies to every interactive element, including the new `Input`/`Select`/`Textarea` primitives and `.card-interactive` (via a colored `--shadow-focus` ring, layered alongside the existing outline). `Button`'s new `isLoading` state sets `aria-busy`. No color-only state indicator was introduced — every new variant (ghost/danger buttons, card variants) still pairs a visual change with real text content, matching the project's existing convention (e.g. `DecisionStateBadge`'s icon is `aria-hidden`, the label text always carries meaning).

## 16. Authentication / Routing Preservation

**Not modified**: `frontend/src/auth/{AuthContext.jsx, useAuth.js, ProtectedRoute.jsx, authContextObject.js, authErrors.js, validateAuthForm.js}`, `frontend/src/lib/supabase.js`, `frontend/src/api/{client.js, procurementApi.js}`, `frontend/src/routes/AppRoutes.jsx`. All existing routes (`/`, `/analyze`, `/results`, `/history`, `/signin`, `/signup`, `*`) are unchanged. Route protection was verified still working fresh via Playwright (Section 20): unauthenticated visits to `/analyze` still redirect to `/signin` at every viewport.

## 17. API / Backend Preservation

**Zero backend files touched** — confirmed via `git status backend/ supabase/`, identical to every prior phase's baseline. No API request/response schema, no authentication behavior, no database migration, and no RLS policy was changed. No fake data, mock endpoint, or hardcoded metric was introduced anywhere.

## 18. Files Changed

**Modified** (all pre-existing, already-uncommitted stylesheets/components — token values and CSS rules changed, no structural/behavioral change):
- `frontend/src/styles/variables.css`
- `frontend/src/styles/global.css`
- `frontend/src/styles/layout.css`
- `frontend/src/styles/components.css`
- `frontend/src/styles/results.css`
- `frontend/src/components/common/Button.jsx`
- `frontend/src/components/common/Card.jsx`
- `frontend/src/components/common/PageHeader.jsx`
- `frontend/src/components/results/MetricCard.jsx`

**Created**:
- `frontend/src/components/common/Divider.jsx`
- `frontend/src/components/ui/Input.jsx`
- `frontend/src/components/ui/Select.jsx`
- `frontend/src/components/ui/Textarea.jsx`
- `frontend/src/components/ui/Label.jsx`
- `frontend/src/components/ui/HelperText.jsx`
- `frontend/src/components/ui/ErrorText.jsx`
- `reports/ui1_design_system_and_frontend_foundation.md` (this file)

**Not touched**: everything under `backend/`, `supabase/`, `frontend/src/auth/`, `frontend/src/api/`, `frontend/src/lib/`, `frontend/src/routes/AppRoutes.jsx`, every page component (`HomePage.jsx`, `AnalysisPage.jsx`, `ResultsPage.jsx`, `HistoryPage.jsx`, `SignInPage.jsx`, `SignUpPage.jsx`, `NotFoundPage.jsx`), `AnalysisForm.jsx`/`FormField.jsx`/`FormSection.jsx`, `Sidebar.jsx`/`TopBar.jsx`/`AppLayout.jsx` (JS unchanged — only their CSS), `analysis.css`/`auth.css` (unchanged files — they already inherit every token refinement automatically).

## 19. Verification

```
python -m pytest -q     →  178 passed, 0 failed, 0 skipped   (unchanged baseline)
npm run build            →  succeeds (129 modules; one pre-existing, unrelated bundle-size notice)
npm run lint              →  clean, 0 warnings, 0 errors (including the new components/ui/ files, explicitly re-linted)
```

## 20. Browser Verification

Real Playwright (Chromium), reusing the isolated scratchpad install from Phase 8H, against the live Vite dev server — **16 checks across desktop (1440×900), tablet (820×1180), and mobile (375×812), all PASS**:
- No horizontal overflow on Home at any viewport.
- Zero console/page errors on Home or after navigating to `/analyze`, at every viewport.
- Sidebar renders (desktop/tablet) or the mobile menu button opens the off-canvas drawer correctly (mobile), confirmed via `is-open` class state, not just a screenshot.
- Unauthenticated `/analyze` still redirects to `/signin` at every viewport — route protection unaffected.

Screenshots were captured and visually inspected (desktop Home, mobile Home, mobile sidebar-open, desktop Sign In): the new midnight sidebar, refined blue primary actions, cool neutral background, and the violet active-nav accent render cohesively and consistently across the shell, the Home page's existing content, and the Sign In page — confirming the design system actually looks and behaves as intended, not just that the CSS parses.

## 21. Known Limitations

This phase intentionally did **not** touch: the landing page's actual content/hero section (UI-2), the dashboard (not yet built), the analysis form's own visual redesign (UI-4), the Results Dashboard's visual redesign, the History table's visual redesign, any chart or network-visualization implementation, and any icon library (none was introduced; the existing plain-glyph/emoji approach in `Badge`/`DecisionStateBadge` was left as-is, since it already works and adding an icon framework was explicitly out of scope). The new `components/ui/` form primitives and `Divider` are unused by any current page — they exist only as a foundation for later phases, exactly as instructed. `Card`'s `interactive` variant needs keyboard/ARIA wiring added at its first real call site (Section 10).

## 22. Final Verdict

**PASS**
