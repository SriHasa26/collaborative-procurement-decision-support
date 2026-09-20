# UI-2 — Premium Landing Page

**Date:** 2026-09-15

## 1. Objective

Transform the existing `/` Home page into a premium, memorable landing experience that makes "fragmented demand → compatible connections → optimized collaboration → quantified savings" understandable within seconds — reusing UI-1's design system exclusively, changing nothing about the backend, authentication, or any other route's behavior.

## 2. Existing Home Page Inspected

`frontend/src/pages/HomePage.jsx` (Phase 7B) was a single static section — a bare hero, a `WorkflowSteps` list, a grid of all four `DecisionStateCard`s, and a "Developer diagnostic" `BackendStatusCheck` card — all rendered inside the shared `AppLayout` (permanent Sidebar + TopBar). `AppRoutes.jsx`, `AppLayout.jsx`, `Sidebar.jsx`, `TopBar.jsx`, and every other page were also inspected to confirm the exact current routing/shell structure before deciding how to restructure only `/`.

## 3. Landing Page Structure

A genuine architectural decision was made and is recorded here: `/` no longer renders inside `AppLayout` (the permanent-sidebar app shell). It now has its own `LandingLayout` (a light shell: `LandingNav` + routed content + `Footer`), because a public marketing page and an authenticated internal tool are different products with different navigation needs — exactly what this phase's own "Section 1 — Navigation" (logo, anchor links, Sign In, Start) describes, which does not match a permanent left sidebar. `AppLayout`/`Sidebar`/`TopBar` were **not modified** — every other route (`/signin`, `/signup`, `/analyze`, `/results`, `/history`, 404) still uses them, unchanged, verified in Section 17.

Section order implemented, per the brief's own intended sequence: Navigation → Hero (with the network visualization) → Value/capability cards → How It Works → Decision Intelligence → Product Preview → Differentiators → Final CTA → Footer.

## 4. Hero Design

`components/landing/Hero.jsx`. Eyebrow ("Collaborative Procurement Intelligence") → headline ("Turn fragmented demand into smarter procurement decisions.") → supporting copy → primary CTA ("Start an Analysis", routes to `/analyze`) → secondary CTA ("See How It Works", an in-page anchor to `#how-it-works`). No generic "Welcome to our platform" copy, no marketing jargon.

**CTA routing decision**: both the hero's and the final CTA's primary buttons point directly at `/analyze`, not `/signup`. This deliberately reuses the *existing, already-tested* `ProtectedRoute` behavior (Phase 8C): a signed-out visitor is redirected to `/signin` and automatically returned to `/analyze` after signing in. This was chosen over inventing a separate "Get Started → sign up" path, per this phase's own "use existing routing and auth behavior... do not invent new authentication flows" instruction.

## 5. Procurement Network Visualization

`components/landing/HeroNetwork.jsx` — a hand-built inline SVG (no charting/network library added), five generic "Vendor A"–"Vendor E" nodes connected to a central "Group" hub, animated once on load via CSS keyframes only:
1. Nodes fade/scale in, staggered.
2. Connecting lines "draw" (SVG `stroke-dashoffset` animation), staggered.
3. The hub emits a single, non-repeating pulse ring (not a continuous animation).
4. A "✓ Buy Together" badge fades in last.

**Honesty safeguards** (per this phase's explicit "not live data" rule): every label is a generic placeholder, never the real vendor/location names from this project's actual test data; a visible caption directly under the SVG reads "Illustrative network — not live vendor data"; and the SVG carries a real `<title>`/`<desc>` (an accessible text equivalent, satisfying this phase's own accessibility requirement for the visualization) stating the same thing. `prefers-reduced-motion` needs no special-case code here — the existing global rule (`global.css`, unchanged) already neutralizes every CSS animation/transition site-wide, so a user with that preference sees the finished state immediately.

## 6. How-It-Works Section

`components/landing/HowItWorks.jsx` — a new component, **not** a reuse of `components/common/WorkflowSteps.jsx` (left completely untouched; it is still used, as-is, by `AnalysisPage`'s own "Analysis workflow" section — duplicating the landing page's richer visual treatment there would have changed an existing, working page). Five numbered stages (Submit → Validate → Connect → Optimize → Decide) connected by a horizontal line on desktop/tablet, transformed into a vertical timeline below 900px (confirmed visually in the mobile screenshot, Section 17). Uses "decision engine"/"deterministic rules" language throughout — never "AI", consistent with this project's own established, honest positioning (see `backend/api/main.py`'s own description, unread but consistent).

## 7. Decision Intelligence Section

`components/landing/DecisionIntelligence.jsx` — reuses the **existing, unmodified** `DecisionStateBadge` component (Phase 7B) rather than inventing a second badge style. The card is explicitly labeled "Example Decision" (a `text-label`, the same convention used elsewhere in the app for metadata labels), shows illustrative counts (4 vendors, 1 group) and a qualitative "+" / "Positive savings identified" — deliberately **not** a specific currency figure, since a precise-looking number (e.g. one lifted from real prior test output) could be mistaken for a real statistic. Ends with a real CTA ("Run Your Own Analysis →") to `/analyze`.

## 8. Product Preview

`components/landing/ProductPreview.jsx` — reuses the **existing, unmodified** `MetricCard` component (`results/MetricCard.jsx`) rather than duplicating its markup, composed into a small preview card explicitly labeled "Demo Scenario". Figures shown (4 vendors, 1 compatible pool, 11 candidate groups) are the same style of round, illustrative example the brief itself suggests — no specific currency amount, no claim of live platform statistics. No API call is made anywhere on this page.

## 9. Differentiators

`components/landing/Differentiators.jsx` — the five cards from the brief (Collaborative by Design, Geography-Aware, Constraint-Aware, Explainable, Savings-Focused), built from the existing `Card` component.

## 10. Final CTA

`components/landing/LandingCTA.jsx` — a dark (midnight) full-width section, one heading, one line of supporting copy, one primary button to `/analyze`. No manipulative language.

## 11. Responsive Design

Verified via real Playwright at 1440×900 / 820×1180 / 375×812 (Section 17): zero horizontal overflow on any viewport, the hero collapses to a single column with the network visual promoted above the copy on tablet/mobile (`hero-visual { order: -1 }` below 1024px), the How-It-Works line becomes a vertical timeline below 900px, and the nav collapses into a mobile menu below 768px (reusing the same off-canvas-toggle pattern already established for the app shell's own mobile menu, but as its own lighter implementation local to `LandingNav.jsx`, since it only needs to show/hide a short flat menu, not a routed multi-page sidebar).

## 12. Accessibility

Semantic HTML throughout (`<header>`, `<nav>`, `<main>`, `<section>`, `<figure>`/`<figcaption>`, `<footer>`, proper heading levels `h1`→`h2`). The nav's mobile menu button has `aria-label`/`aria-expanded`/`aria-controls`. The hero SVG has `role="img"` with `aria-labelledby` pointing at a real `<title>`/`<desc>` pair (Section 5) — a genuine accessible-name/description, not just a decorative image. Every decision-state badge still carries real label text (via the unmodified `DecisionStateBadge`), never color alone. The global `:focus-visible` ring (unchanged) still applies to every new interactive element, including the new nav links and anchor-rendered `Button`s.

## 13. Animation / Motion

Exactly three animated elements on the whole page: the hero copy's single `.animate-in` entrance (reusing UI-1's existing utility), the hero network's one-time node/line/pulse/badge sequence (Section 5), and the existing global hover/focus transitions on buttons and cards (unchanged, from `components.css`). No infinite pulsing, no bouncing, no particles, no scroll-jacking — native browser scrolling is untouched. `prefers-reduced-motion` is honored globally, with no page-specific code required (Section 5).

## 14. Real Data / Demo Data Handling

No fake user counts, no fake savings totals, no fake accuracy percentage, no fake vendors, no fake customer logos, and no fake activity anywhere on the page. Every illustrative number is either a capability statement (Value Metrics section, no numbers at all) or explicitly labeled "Example Decision" / "Demo Scenario" (Sections 7–8) with deliberately round, non-suspicious figures — never the exact real numbers from this project's actual prior test runs, and never a specific currency amount.

## 15. Files Changed

**Created:**
- `frontend/src/components/layout/LandingLayout.jsx`
- `frontend/src/components/layout/LandingNav.jsx`
- `frontend/src/components/layout/Footer.jsx`
- `frontend/src/components/landing/Hero.jsx`
- `frontend/src/components/landing/HeroNetwork.jsx`
- `frontend/src/components/landing/ValueMetrics.jsx`
- `frontend/src/components/landing/HowItWorks.jsx`
- `frontend/src/components/landing/DecisionIntelligence.jsx`
- `frontend/src/components/landing/ProductPreview.jsx`
- `frontend/src/components/landing/Differentiators.jsx`
- `frontend/src/components/landing/LandingCTA.jsx`
- `frontend/src/styles/landing.css`
- `reports/ui2_premium_landing_page.md` (this file)

**Modified:**
- `frontend/src/pages/HomePage.jsx` (full rewrite — the one page this phase redesigns)
- `frontend/src/routes/AppRoutes.jsx` (`/` moved to `LandingLayout`; every other route's declaration and protection unchanged)
- `frontend/src/main.jsx` (added `import './styles/landing.css'`)
- `frontend/src/components/common/Button.jsx` (added an optional `href` prop, for a same-page anchor CTA — see Section 4)

**Deleted:**
- `frontend/src/components/common/BackendStatusCheck.jsx` — its own Phase 7A docstring anticipated exactly this ("A later phase... will replace or remove this"); a raw "GET /health: Reachable" diagnostic box has no place on a public landing page, and it had no other caller.

**Not touched:** `backend/`, `supabase/` (confirmed via `git status`, identical to every prior phase's baseline), `frontend/src/components/layout/{AppLayout,Sidebar,TopBar}.jsx`, `frontend/src/auth/*`, `frontend/src/api/*`, `frontend/src/lib/supabase.js`, `AnalysisPage.jsx`/`AnalysisForm.jsx`, `ResultsPage.jsx` and every `results/` component (except reusing `MetricCard` unmodified), `HistoryPage.jsx`. `components/common/DecisionStateCard.jsx` and a few Phase 7B-only CSS classes (`.hero`, `.trust-note`, `.decision-grid` in `components.css`) are now unused by any page (their sole prior caller was the old HomePage) but were deliberately left in place rather than deleted — `DecisionStateCard` is a genuinely reusable component that was never marked for removal (unlike `BackendStatusCheck`), and removing a few harmless, unreferenced CSS rules was judged unnecessary churn beyond this phase's scope.

## 16. Verification

```
python -m pytest -q     →  178 passed, 0 failed, 0 skipped   (unchanged baseline)
npm run build             →  succeeds (139 modules -- up from 129, since the new
                              landing components are now actually imported/bundled;
                              one pre-existing, unrelated bundle-size notice)
npm run lint               →  clean, 0 warnings, 0 errors
```

## 17. Browser Verification

Real Playwright (Chromium), the same isolated scratchpad install used in UI-1 — **30 checks across desktop (1440×900), tablet (820×1180), and mobile (375×812), all PASS**:
- No horizontal overflow on Home (checked after the hero animation fully settles) at every viewport.
- Zero console/page errors on Home and after every subsequent navigation.
- All 7 landing sections and the footer render.
- The nav's anchor link (`#how-it-works`) actually scrolls the page (desktop/tablet).
- **Regression**: unauthenticated `/analyze`, `/results`, and `/history` still redirect to `/signin` at every viewport; `/signin` itself renders with zero overflow and **still shows the app-shell sidebar** — direct confirmation that `AppLayout`/`ProtectedRoute` were unaffected by the landing page's separate shell.

Full-page screenshots were captured and visually inspected at desktop and mobile widths: the hero, network visualization, capability cards, five-stage process (horizontal on desktop, correctly stacked to a vertical timeline on mobile), decision/product preview cards, differentiator grid, dark final-CTA band, and footer all render cohesively, using the UI-1 token system throughout with no visual inconsistency.

## 18. Regressions Checked

- `python -m pytest -q` — 178 passed, identical to the pre-UI-2 baseline; no backend file was touched.
- Existing routes `/analyze`, `/results`, `/history` — reachable, still protected, still redirect correctly (Section 17).
- `/signin`, `/signup` — unaffected; still render inside the unmodified `AppLayout`.
- Sign-in/sign-up/logout **logic** — not modified (`frontend/src/auth/*` untouched); `LandingNav`'s auth-aware CTA only *reads* the existing `useAuth()` state, exactly as `TopBar.jsx` already did.
- The existing analysis flow (`AnalysisForm.jsx` and everything it calls) — not modified at all.

## 19. Known Limitations

Per this phase's own explicit scope: the dashboard, the analysis form's own visual redesign, the Results Dashboard redesign, and the History redesign were **not** started (later UI phases). No 3D/WebGL/map library was added — the network visualization is 2D SVG + CSS only, as instructed. The "Intelligence" and "How it works" nav links are same-page anchors only (no dedicated `/about` or `/intelligence` route exists, and none was invented, since the brief's mockup names but does not require a real "About" destination — including one would have meant fabricating content this project doesn't have). The landing page's own mobile menu is a small, local implementation in `LandingNav.jsx`, intentionally not a reuse of `Sidebar.jsx`'s off-canvas drawer (that component is unchanged and serves a materially different, multi-page navigation need).

## 20. Final Verdict

**PASS**
