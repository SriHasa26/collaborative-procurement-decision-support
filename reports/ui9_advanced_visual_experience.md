# UI-9 — Advanced Visual Experience & Spatial Procurement Intelligence

**Date:** 2026-09-16

## 1. Objective

Determine whether the product genuinely benefits from a richer spatial/visual layer for its procurement network and decision economics, and implement the strongest visualization the *actual available data* supports — technology chosen to serve product value, not the reverse.

## 2. Existing Visualization Architecture Inspected

Read in full before writing anything: `results/SelectedGroupNetwork.jsx` (UI-5/UI-8's interactive hub-and-spoke network), `results/{DecisionHero, CandidateGroupRow, CandidateGroupsPanel, VendorEconomics, SelectedGroupCard}.jsx`, `pages/ResultsPage.jsx`'s full section order, `dashboard/NetworkOverview.jsx` (UI-3), `styles/dashboard.css`'s `.network-overview-*` rules (UI-3/UI-8), `common/decisionStateMeta.js` (the exhaustive `DecisionState` → variant mapping), `landing/HeroNetwork.jsx`'s existing "illustrative, not live" label, and UI-8's own motion primitives (`.animate-in*`, `.bar-grow-horizontal/-vertical`, the shared reduced-motion override).

## 3. Available Real Data

Re-confirmed, not re-derived (already established in UI-5/8's own reports): the response contains **group membership** (`vendor_ids`), **per-vendor economics** (`per_vendor_allocation[].{share_rs, individual_savings_rs, consumption_time_days}`), and, via `batch_eligibility.eligible_vendors[].vendor_input`, each vendor's **real submitted price and demand**. It contains **no geographic coordinates, no real-world distances, and no time-series/positional data of any kind** — `centroid_distance_km` is an abstract compatibility-check number, never a real-world position.

## 4. Visualization Approach Chosen

**Advanced 2D SVG — not 3D.** The network was upgraded (not replaced) with curved edges, a decision-tied depth glow on the hub, per-node shadow depth, and a brief staggered entrance; a new compact "Evaluated → Selected" flow visual and a paired cost-share/savings dual-bar were added elsewhere on the Results page using the same technique family.

## 5. Why 2D Was Selected Over 3D

Answered honestly against this phase's own six justification questions (Section 3 above establishes what data actually exists):

1. **What does 3D communicate that 2D cannot?** Nothing structural. The only real relationships in this data are *membership* (which vendors belong to the selected group) and *magnitude* (how much each vendor's cost share/savings is) — both are naturally hierarchy/proportion concepts, not volumetric ones. A "layered/depth" *feel* was achievable with CSS shadows and glow alone (Section J's own suggested techniques), without a third spatial axis carrying any real information.
2. **Does the data support spatial interpretation?** No — there are no coordinates. Introducing 3D would require inventing an arbitrary 3D layout with no data behind it, which Rule 2 explicitly forbids ("a visual element must never imply data that does not exist").
3. **Would 3D improve understanding or merely decorate?** For 4–11 simple nodes with a bipartite membership relationship, a well-composed 2D diagram communicates the same story in the same or less time — the product's own stated goal ("help a judge understand in seconds") favors immediacy over a WebGL scene that needs orientation/loading first.
4. **Is the performance cost justified?** No. Three.js/React Three Fiber would be a genuinely new, non-trivial dependency (bundle weight, WebGL context management) for a scene this simple — disproportionate engineering weight relative to the actual visual gain.
5. **Can it remain accessible?** A 3D/WebGL canvas still requires a full text/2D fallback to be accessible at all (Section M) — meaning the accessible path would end up being *exactly* what was already built directly, making the 3D layer additive complexity with no accessibility upside.
6. **Would reduced-motion users still understand it?** A static (non-orbiting) 3D scene under reduced motion is, at best, an expensively-rendered 2D-equivalent view — strictly worse than a real, lightweight 2D SVG for that user.

All six answers point the same direction. **3D was not introduced.** This is the explicit, permitted, arguably-preferred outcome this phase's own brief describes ("If 2D SVG provides a better result, USE 2D SVG").

## 6. If 3D: N/A

Not applicable — 3D was not used. No `three`/`@react-three/fiber` (or any 3D/WebGL) dependency was added; `frontend/package.json` is unchanged this phase (confirmed via `git diff --stat`, which shows the file's only tracked change predates this session).

## 7. Components Created

`results/DecisionFlowVisual.jsx` — Section F's real-data "Evaluated → Selected" bridge.

## 8. Components Modified

`results/SelectedGroupNetwork.jsx` (the advanced-SVG upgrade), `results/VendorEconomics.jsx` (the paired cost-share/savings dual-bar), `pages/ResultsPage.jsx` (wires `DecisionFlowVisual` above Candidate Groups Evaluated), `styles/{dashboard.css, results.css}`.

## 9. Interaction Design

Every UI-8 interaction on the network was preserved and re-verified unchanged: hover/focus highlight-and-dim, click/Enter/Space opens the real per-vendor detail panel, Escape closes it, mobile tap works without hover. Nothing about the *interaction model* changed this phase — only the *rendering* of edges/nodes/hub (curves, glow, entrance) and two new, purely-informational, non-interactive visuals (`DecisionFlowVisual`, the second economics bar) were added.

## 10. Motion Design

No new animation system — UI-8's existing primitives and the single site-wide reduced-motion override were reused throughout. New, narrowly-scoped additions: `network-edge-draw` (a `stroke-dasharray`/`dashoffset` "draw-in," `--transition-slow` + `--ease-emphasized`) and `network-node-enter` (fade + scale, `--transition-base` + `--ease-emphasized`), both staggered by real vendor index order — never implying this sequence is the backend's own execution order (it is a one-time presentation reveal of an already-complete result, per Section S's explicit distinction). Both bar additions reuse the existing `.bar-grow-horizontal` utility (UI-8) as-is. No continuous or looping animation, no camera movement (there is no camera — this is not 3D).

## 11. Accessibility

- The network's `role="img"`/`aria-label` already stated vendor membership in words (UI-5/8, unchanged) — re-verified intact.
- `network-node-enter` uses `transform-box: fill-box` so the SVG scale-entrance animates from each node's own center, not the SVG viewport origin — verified visually (nodes fade in place, never slide in from a corner).
- The hub's decision-tied color is explicitly **supplementary**: `DecisionStateBadge` remains the actual semantic source of the decision everywhere on the page (Section E's explicit instruction) — the network's color alone never carries meaning nothing else on the page already states in text.
- `DecisionFlowVisual` is `role="img"` with a complete real-data `aria-label` ("11 candidate groups evaluated; 1 selected."); its visual child elements are `aria-hidden` to avoid double-announcement.
- The dual economics bars keep every value as permanent visible text (never hover-only) — same accessibility stance as UI-7/8's other bar charts.

## 12. Reduced-Motion Behavior

Explicitly tested via `page.emulateMedia({ reducedMotion: "reduce" })` against the real, unmodified `ResultsPage`: the computed `animation-duration` on both `.network-edge-draw` and `.network-node-enter` was measured and confirmed neutralized (`1e-06s` = the existing global override's `0.001ms`); clicking a network node still opens the real detail panel instantly; `DecisionFlowVisual` still shows its real counts. No new code was needed for this — inherited automatically from the existing global rule (Section 19).

## 13. Responsive Behavior

Tested at 1440px/1024px/390px (Section 19): no horizontal overflow at any viewport, in any scenario. The network SVG, `DecisionFlowVisual`, and the dual bars all reuse the exact responsive rules already established in `dashboard.css`/`results.css`; `DecisionFlowVisual` gets one small new mobile rule (centers and narrows its two stage boxes below 480px).

## 14. Performance

No new dependency (Section 6). Production bundle: 593.77 kB JS (up from UI-8's own reported 591.78 kB — a ~2 KB increase from one new component and two rewritten ones, not a new library) and 48.85 kB CSS. No `requestAnimationFrame` loop, no canvas, no WebGL context, no continuous rendering of any kind — every addition is a CSS `transition`/`animation` that runs once on mount and then stops.

## 15. Real-Data Verification

The real, previously-persisted `POTATO_HYD_2026_09` run was rendered by the actual, unmodified `ResultsPage.jsx` and its full component tree (Section 19). Confirmed, exactly matching this phase's own reference values, none hardcoded anywhere in the changed code: the network hub correctly renders in the **success** (green) color because this run's real `final_decision_state` is `BUY_TOGETHER`; clicking `BOWENPALLY_POTATO_01` still surfaces its real ₹106.89 cost share and ₹718.11 individual savings; `DecisionFlowVisual` shows the real `11 → 1` (candidate_group_count → selected_group_count); `VendorEconomics`'s new savings bar renders the real ₹718.11/₹1,093.11/₹1,046.90/₹874.49 figures for all four vendors, each proportional to the real group maximum.

## 16. Browser Verification

No real Supabase session was available, and none was fabricated. The same, already-established harness technique from UI-5/6/7/8 was used: a temporary `harness.html`/`_harness_main.jsx`, never imported by the real app, deleted before this report was written (confirmed via `git status`), rendering the real, unmodified `ResultsPage.jsx` inside a `MemoryRouter` with the real `POTATO_HYD_2026_09` result injected as router state.

At 1440px/1024px/390px: network edges render as curved `<path>` elements carrying the entrance class (4/4); the hub carries the real decision-tied color class; nodes carry the entrance class (4/4); clicking a node still shows the real detail panel and Escape still closes it (UI-8 regression, re-verified); `DecisionFlowVisual` shows the real `11`/`1`/"Evaluated"/"Selected"; `VendorEconomics` shows both the real cost-share and real savings figures with a savings bar rendered per vendor (4/4); the Decision Hero and all 11 real candidate groups still render (UI-5/8 regressions, re-verified). A dedicated reduced-motion pass confirmed all of the above still functions, instantly. **42/42 checks passed.**

A separate unauthenticated-regression pass against the real production `vite preview` build confirmed `/insights`, `/history`, `/results`, `/analyze`, `/dashboard` still correctly redirect to `/signin`, and `/`/`/signin` still load. **7/7 checks passed.**

**Not verified:** an actual authenticated click-through in the live deployed app (Section 20).

## 17. Build

`npm run build` — **188 modules transformed, 0 errors** (up from 187 after UI-8, reflecting the one new `DecisionFlowVisual.jsx`).

## 18. Lint

`npm run lint` (oxlint) — **0 warnings**.

## 19. Backend Tests

`python -m pytest -q` — **178 passed, 0 failed, 0 skipped** (unchanged — confirms the backend was genuinely never touched).

## 20. Authentication Verification

Not possible in this environment — no real Supabase session was available, and none was fabricated. `ProtectedRoute`/`AuthContext`/`api/client.js` were not touched this phase; the unauthenticated-redirect checks in Section 16 confirm every route is still gated exactly as before.

## 21. Limitations

- No live, credentialed browser session was available, so an actual sign-in → Dashboard → Analyze → Results → History → Insights click-through was not performed. The harness-based verification (Section 16) exercises the real, unmodified component tree against real data instead — the same mitigating technique every prior UI phase's report has documented.
- Dashboard's own `NetworkOverview.jsx` (UI-3) automatically inherits the new hub/node depth-shadow CSS (a shared class), but deliberately does **not** get the curved-edge/entrance-animation upgrade (that requires markup changes only made in `SelectedGroupNetwork.jsx`) — a conscious choice to avoid touching a Dashboard component file beyond what Section H's "do not redesign the Dashboard" allows.
- The Landing page's illustrative network (UI-2) was inspected and confirmed to still carry its "Illustrative network — not live vendor data" label, but was not otherwise modified this phase (a legitimate, low-risk scope choice — it already correctly avoids implying real data).
- Insights (UI-7) was inspected and intentionally received no spatial/network visualization — the underlying historical data supports only counts/sums, never a genuine "map" of any kind, and inventing one would violate Rule 2 and Section U directly; UI-7's limited-data states remain completely untouched.

## 22. Backend Confirmation

**Backend NOT modified. Procurement engine NOT modified. Database NOT modified. Authentication/RLS/JWT NOT modified. No 3D/WebGL introduced. No new dependency added.** Confirmed by `git status`: zero changes under `backend/` or `supabase/` beyond what was already present from prior phases before this session began, and `frontend/package.json`/`package-lock.json` carry no new dependency from this phase. `python -m pytest -q` remains 178 passed / 0 failed / 0 skipped.

---

## UI-9 IMPLEMENTATION SUMMARY

**Visualization approach:** Advanced 2D SVG — curved edges, a decision-tied depth glow on the network hub, per-node shadow depth, and a brief staggered entrance on the existing Procurement Network; a new real-data "Evaluated → Selected" flow visual; a paired cost-share/savings dual-bar in Vendor Economics.

**Why this approach was chosen:** The real data behind this page supports exactly two relationships — group membership and economic magnitude — both naturally 2D (hierarchy/proportion) concepts with no coordinates or positional data to justify a third spatial axis. Answering this phase's own six 3D-justification questions honestly (Section 5) pointed the same direction every time: 3D would add engineering weight, WebGL risk, and reduced accessibility without adding real information a well-composed 2D diagram couldn't already convey — and a 3D scene still needs a full 2D/text fallback to be accessible, making the 3D layer pure additive complexity.

**3D introduced:** NO

**What changed:** The Procurement Network (`SelectedGroupNetwork.jsx`) now uses curved bezier edges instead of straight lines, a hub whose color reflects the group's real decision state (supplementary to the unchanged `DecisionStateBadge`), soft depth shadows on hub and nodes, and a brief one-time staggered entrance — all interaction (hover-dim, click-to-inspect, Escape-to-close) unchanged and re-verified. A new `DecisionFlowVisual` shows the real evaluated-vs-selected candidate counts as a compact flow. `VendorEconomics` now pairs each vendor's real cost share with its real individual savings as two proportional bars instead of one.

**Components created:** `results/DecisionFlowVisual.jsx`.

**Components modified:** `results/SelectedGroupNetwork.jsx`, `results/VendorEconomics.jsx`, `pages/ResultsPage.jsx`, `styles/dashboard.css`, `styles/results.css`.

**Components deleted:** none.

**Backend changed:** NO
**Procurement engine changed:** NO
**Authentication/security changed:** NO

**Backend tests:** 178 passed, 0 failed, 0 skipped.
**Build:** clean, 188 modules, 0 errors.
**Lint:** clean, 0 warnings.
**Browser verification:** 42/42 (Results page: curved network edges/entrance/hub color, click-to-detail and Escape regressions, DecisionFlowVisual, dual economics bars, decision hero and candidate groups regressions — across 1440/1024/390px plus a dedicated reduced-motion pass) + 7/7 (unauthenticated route regression).
**Reduced-motion verification:** explicitly tested and confirmed neutralized (network edge-draw and node-enter animation durations both measured at ~0); every interaction still fully functional, instantly.
**Accessibility verification:** network `aria-label`/detail panel unchanged and re-verified; `DecisionFlowVisual` is a labeled `role="img"` with real counts; SVG scale-entrance correctly uses `transform-box: fill-box` to animate in place; decision color on the hub is supplementary only, never the sole carrier of meaning.
**Real-data verification:** the real `POTATO_HYD_2026_09` run rendered correctly through every new visual — the network hub is green because the real decision is `BUY_TOGETHER`, the real per-vendor cost-share and savings figures appear correctly in both the new dual bars and the click-to-inspect panel, and `DecisionFlowVisual` shows the real `11 → 1`.
**Authenticated verification:** not possible — no real Supabase session available; documented rather than fabricated.
**Performance:** no new dependency; bundle grew by ~2 KB (one new component, two rewritten); no continuous rendering, no WebGL, no `requestAnimationFrame` loop anywhere.
**Limitations:** no live authenticated click-through possible; Dashboard's own network only inherits the shared depth-shadow CSS, not the curved-edge markup change (a deliberate scope boundary); Landing's illustrative network and Insights were inspected and intentionally left unchanged, for the reasons in Section 21.

**Report:** `reports/ui9_advanced_visual_experience.md`

**Git operations:** NONE
