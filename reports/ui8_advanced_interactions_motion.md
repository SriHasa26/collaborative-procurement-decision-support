# UI-8 — Advanced Interactions, Motion & Procurement Network Experience

**Date:** 2026-09-16

## 1. Objective

Make the existing product (Landing → Dashboard → Analyze → Results → History → Insights) feel alive, responsive, and deliberate through purposeful motion and interaction — never decoration for its own sake, never fake data or fake "live" system behavior — while preserving every existing contract, data value, and accessibility guarantee established in UI-1 through UI-7.

## 2. Existing UI Inspected

Before writing any code: `styles/{global.css, variables.css, components.css, dashboard.css, results.css, analysis.css}`, `results/{DecisionHero, SelectedGroupCard, SelectedGroupNetwork, VendorEconomics, CandidateGroupRow, CandidateGroupsPanel}.jsx` (UI-5), `dashboard/{NetworkOverview, SavingsAnalytics}.jsx` (UI-3), `analysis/{AnalysisForm, VendorCard, StepProgress, FormSection}.jsx` (UI-4), `insights/{DecisionDistribution, GroupSizeAnalysis}.jsx` (UI-7), `history/RunHistoryRow.jsx` (UI-6), and `pages/ResultsPage.jsx`.

## 3. Existing Motion System

Confirmed already in place, not reinvented:
- `variables.css` already defines exactly three durations (`--transition-fast` 120ms, `--transition-base` 200ms, `--transition-slow` 320ms) plus two easing curves (`--ease-standard`, `--ease-emphasized`) — already consistently applied: buttons/inputs use `--transition-fast`, interactive cards use `--transition-base`, the one existing page-entrance (`global.css`'s `.animate-in`, `@keyframes fade-in-up`) uses `--transition-slow`.
- `PageHeader.jsx` already applies `.animate-in` on **every** page (confirmed via grep — Dashboard, Analyze, Results, History, Insights, and the landing Hero all already get a page entrance for free through this one shared component). Section B's "if route transitions are already implemented, reuse them" is therefore already satisfied — no second/competing transition system was created.
- A single, blanket `@media (prefers-reduced-motion: reduce)` rule in `global.css` neutralizes every animation/transition duration site-wide already — every new animation this phase adds inherits this automatically, with zero additional code (verified in Section 15).
- `.animate-in-delay-1`/`-2` existed but were **never actually used** in any JSX before this phase (confirmed via grep — comment-only).

## 4. Motion Architecture Introduced

No new duration/easing tokens were added — the three existing tiers already covered every case (documented explicitly, for the first time, in `global.css`: micro/standard/emphasis mapped onto the existing `--transition-fast/base/slow`). Two new, small, reusable additions:
- `.animate-in-delay-3`/`-4` (global.css) — extends the existing, previously-unused stagger utility.
- `.bar-grow-horizontal` / `.bar-grow-vertical` (global.css) — a proportional bar's fill growing from 0 to its real, final value **once**, via `transform: scaleX`/`scaleY` (never a stepped sequence of fake intermediate numbers, and the underlying `width`/`height` is still set correctly on the very first frame — only the visual fill is animated). Applied to all four existing bar-chart implementations: `results/VendorEconomics.jsx`, `insights/DecisionDistribution.jsx`, `insights/GroupSizeAnalysis.jsx`, `dashboard/SavingsAnalytics.jsx` — one shared mechanism, not four separate ones.

## 5. Components Created

`components/common/Tooltip.jsx` — click/tap-toggled (never hover-only, keyboard-focusable, closes on Escape/blur), used only where it carries genuine value (Section L): the real run ID shown on a reopened Results page. It was **not** applied to History's own row-level run ID, because that text already sits inside History's own whole-row `<button>` (UI-6's "make the entire item tappable" design) — nesting a second interactive `<button>` inside it would be invalid HTML and would break the row's own click behavior; the existing native `title` attribute was left as the honest, structurally-safe choice there instead of forcing an inconsistent interaction pattern.

## 6. Components Modified

`results/{DecisionHero.jsx, SelectedGroupCard.jsx, SelectedGroupNetwork.jsx, VendorEconomics.jsx, CandidateGroupRow.jsx}`, `insights/{DecisionDistribution.jsx, GroupSizeAnalysis.jsx}`, `dashboard/SavingsAnalytics.jsx`, `analysis/{AnalysisForm.jsx, VendorCard.jsx, FormSection.jsx, steps/ReviewStep.jsx}`, `pages/ResultsPage.jsx`, `styles/{global.css, dashboard.css, results.css, components.css}`.

## 7. Network Visualization Changes (Section D)

The existing `results/SelectedGroupNetwork.jsx` (UI-5) already correctly labeled itself "Selected procurement relationship — not a geographic map" and already supported click-to-select. This phase upgraded it into a genuinely interactive **Procurement Network**:
- **Hover/focus** now softly highlights the active node and its own edge (`.is-active`) while dimming the rest of the network (`opacity: 0.35`/`0.15` on non-active nodes/edges) — a real relationship cue, driven by real `hoveredVendorId`/`selectedVendorId` React state, not decoration.
- **Click (or Enter/Space)** opens an accessible detail panel showing **only real fields the response actually carries** for that vendor: its real cost share and individual savings and consumption time (`entry.decision.per_vendor_allocation`, already available) and, newly threaded through from `ResultsPage.jsx` → `SelectedGroupCard.jsx` → here, its real submitted price and demand (`result.batch_eligibility.eligible_vendors[].vendor_input`) — no field is ever shown that the response doesn't actually contain (verified: if a fact is absent, it is simply omitted from the panel, never replaced with a placeholder).
- **Escape** closes the panel (a real `keydown` listener scoped to the widget).
- No geography, no coordinates, no distances are drawn or implied anywhere — the existing "not a geographic map" label is preserved verbatim, and a new "Procurement Network" label was added above it for clarity.
- This required one small, additive prop-threading change (`batchEligibility` passed down two levels) — no business logic, no new backend field, no new computation.

## 8. Decision Reveal Changes (Section C)

`DecisionHero.jsx`'s own internal elements (eyebrow → decision badge/state → supporting sentence → expected savings → supporting chips) now reveal with a short staggered sequence (`.animate-in-delay-0` through `-4`, 0–240ms offsets, each a 320ms fade), reusing the exact same `@keyframes fade-in-up` every other page entrance already uses. Total sequence completes in well under 600ms — the page is fully interactive immediately; the animation is purely a presentation of the already-returned, real result (no "AI is thinking"/"Optimizing…"/confidence-score theater of any kind was added, per the explicit prohibition).

## 9. Candidate Interaction Changes (Section E)

`CandidateGroupRow.jsx`'s expand/collapse detail panel now uses the `grid-template-rows: 0fr → 1fr` technique for a smooth height transition (previously an instant conditional mount/unmount) — the panel is now always present in the DOM but `inert` (and `aria-hidden`) while collapsed, exactly preserving the prior accessibility guarantee (collapsed content was never keyboard/screen-reader reachable before, and still isn't) while adding the requested smooth motion. The selected candidate already said "✓ Selected" (never "Best") — confirmed unchanged and re-verified (Section 19).

## 10. Savings Visualization Changes (Section F)

All four existing bar-chart components (Section 4) now grow from 0 to their real final proportion on mount, via the shared `.bar-grow-horizontal`/`-vertical` utility. No numeric value was ever changed, rounded differently, or shown as a fake intermediate step — only the visual fill animates; the text label next to each bar always shows the real, final, correctly-formatted number from the very first frame.

## 11. History Interactions (Section G)

Audited, not rewritten: `RunHistoryRow.jsx` already uses the same `.card-interactive` hover/focus treatment (`--transition-base`) every other interactive card in the product uses, already has a real full-row `<button>` (works without hover, comfortably tappable), and filtering already re-renders instantly with no artificial delay. No changes were made here — Section T's own "do not rewrite working components merely for cosmetic uniformity" was followed; the one genuine gap found (the run ID's native-`title`-only tooltip) was investigated for a `Tooltip` upgrade and correctly **not** applied, for the structural reason in Section 6.

## 12. Insights Interactions (Section H)

`DecisionDistribution.jsx`/`GroupSizeAnalysis.jsx`'s proportional bars now use the same `.bar-grow-horizontal` reveal (Section 4/10). Every bar's exact value was already shown as permanent, always-visible text (never hidden behind hover) — a stronger accessibility guarantee than a hover-reveal tooltip would have provided, so none was added. UI-7's limited-data states (`LimitedDataState.jsx`) were not touched and remain exactly as they were — confirmed no chart/bar-grow animation exists on any path that would visually imply a trend where UI-7 correctly determined there wasn't enough data.

## 13. Analysis Wizard Interactions (Section I)

`AnalysisForm.jsx`: each step's content wrapper now carries `key={currentStep.key}` (forcing a real remount rather than an in-place patch, which would never have replayed the CSS animation) plus `.animate-in`, so moving between steps — forward or Back — crossfades in the new step's fields. This required one small, additive change to `FormSection.jsx` (an optional `className` prop, merged the same way `Card.jsx` already merges its own — previously `FormSection` accepted no `className` at all). `VendorCard.jsx`'s summary ↔ full-form toggle now crossfades the same way (also needed an explicit differing `key` per branch, for the same reason). No payload builder, validation semantics, form field, or backend contract was touched — confirmed unchanged by re-reading `buildAnalysisPayload.js`/`validateAnalysisForm.js` (neither was opened for editing this phase) and by the unchanged 178/178 backend test count.

## 14. Accessibility

- Network: nodes remain real, `tabIndex={0}`, `role="button"` elements with `aria-label`; the detail panel is a labeled `role="region"`; Escape closes it; dimming is a pure visual `opacity` effect that never removes a node from the tab order.
- Candidate rows: the always-mounted detail panel uses `inert` (removing it from both keyboard and screen-reader traversal while collapsed) plus `aria-hidden` as a belt-and-braces fallback for assistive tech that doesn't yet honor `inert`; `aria-expanded` on the toggle button is unchanged and still accurate.
- Tooltip: a real focusable `<button>` trigger, `aria-describedby` linking to a `role="tooltip"` bubble, closes on Escape/blur — never a hover-only native `title`.
- Wizard step crossfade: purely visual (opacity/transform); focus order and tab sequence are unaffected by the `key`-based remount (the newly-mounted step's own first focusable field remains reachable via normal Tab order, unchanged from before this phase).
- No meaning is ever conveyed by motion alone — every animated element still carries the same real text/badge/label it did before.

## 15. Reduced-Motion Verification

Explicitly tested via Playwright's `page.emulateMedia({ reducedMotion: "reduce" })` against the real, unmodified `ResultsPage` and `AnalysisForm` (Section 19): the Decision Hero still shows its real, correct final values (not a mid-stagger state); clicking a network node still opens the real detail panel; expanding a candidate row still works, instantly; the wizard step transition still works, instantly. The computed `animation-duration` on a `.bar-grow-horizontal` element was measured directly and confirmed neutralized to `0.001ms` (Chromium serializes this as `1e-06s`) by the existing global rule — zero new code was needed for this; the pre-existing blanket reduced-motion override in `global.css` covers every new animation automatically.

## 16. Responsive Verification

Tested at 1440px/1024px/390px (Section 19): no horizontal overflow, no console errors, at any viewport, in any scenario. The network SVG, candidate rows, and bar charts all reflow using the exact same responsive rules already established in `dashboard.css`/`results.css` — no new breakpoints were required.

## 17. Performance Considerations

No new dependency was added (confirmed: `frontend/package.json` was not modified this phase). Every animation is a CSS `transition`/`animation` (`transform`/`opacity`/`grid-template-rows`) — no `requestAnimationFrame` loop, no canvas, no continuous/looping animation of any kind was introduced. No 3D library, no WebGL, no particle system — Section Q's prohibition was never approached.

## 18. Real-Data Verification

The real, previously-persisted `POTATO_HYD_2026_09` run (fetched read-only from the live database in an earlier phase) was rendered by the actual, unmodified `ResultsPage.jsx` and its full component tree via the harness in Section 19. Confirmed, exactly matching this phase's own reference values, none hardcoded anywhere in the changed code: 4 vendors, 11 candidate groups, 1 selected group, `Buy Together`, ₹3,732.60 expected savings. Clicking the `BOWENPALLY_POTATO_01` network node surfaced its real, correct per-vendor figures — submitted price ₹11.00/kg, demand 25 kg/day, cost share ₹106.89, individual savings ₹718.11, consumption time 3 day(s) — matching this phase's own stated verification reference exactly.

## 19. Browser Verification

No real Supabase session was available, and none was fabricated. Three real-Chromium harnesses were used, all following the same, already-established technique from UI-5/6/7 (a temporary `harness.html`/`_harness_main.jsx`, never imported by the real app, deleted before this report was written — confirmed via `git status`):

- **Results page** (the highest-risk surface this phase touched): the real, unmodified `ResultsPage.jsx` rendered via `MemoryRouter` with the real `POTATO_HYD_2026_09` result injected as router state. At 1440px/1024px/390px: decision hero settles on real values; clicking a network node opens a real detail panel; Escape closes it; Enter on a focused node also opens it; all 11 real candidate groups render; expanding a row applies the smooth-expand class and reports `aria-expanded="true"`; the page says "Selected", never "Best"; the bar-grow class is present on the real economics bars. **42/42 checks passed**, including a dedicated reduced-motion pass (hero/network/candidates all still fully functional, instantly, with the animation duration numerically confirmed neutralized).
- **Analysis wizard**: the real, unmodified `AnalysisForm.jsx` rendered standalone. Filled step 1, clicked Continue, confirmed step 2 rendered with the step-content wrapper carrying the `animate-in` crossfade class and the step-progress indicator correctly showing step 2 of 5; clicked Back, confirmed step 1 returned; repeated the transition under emulated reduced motion, confirmed it still worked instantly. **8/8 checks passed.**
- **Unauthenticated regression**: `/insights`, `/history`, `/results`, `/analyze`, `/dashboard` all still correctly redirect to `/signin`; `/` and `/signin` still load. **7/7 checks passed.**

**Not verified:** an actual authenticated click-through in the live deployed app (Section 23).

## 20. Build

`npm run build` — **187 modules transformed, 0 errors** (up from 186 after UI-7, reflecting the one new `Tooltip.jsx` component).

## 21. Lint

`npm run lint` (oxlint) — **0 warnings**.

## 22. Backend Tests

`python -m pytest -q` — **178 passed, 0 failed, 0 skipped** (unchanged — confirms the backend was genuinely never touched).

## 23. Authentication Verification

Not possible in this environment — no real Supabase session was available, and none was fabricated. `ProtectedRoute`/`AuthContext`/`api/client.js`'s auth-header logic were not modified in any way this phase; Section 19's unauthenticated-redirect checks confirm every route is still gated exactly as before.

## 24. Limitations

- No live, credentialed browser session was available, so an actual sign-in → Dashboard → Analyze → Results → History → Insights click-through was not performed. The harness-based verification in Section 19 exercises the real, unmodified component trees against real and realistic data instead, which is the same mitigating technique every prior UI phase's report has used and documented.
- `RunHistoryRow.jsx`'s run ID still relies on the native `title` attribute rather than the new `Tooltip` component, for the structural reason in Section 6 (avoiding an invalid nested-button) — documented honestly rather than silently worked around.
- Per this phase's own explicit scope (Sections Q/R), no 3D/WebGL/live-telemetry experience was attempted — that remains reserved for a later phase to evaluate on its own merits.

## 25. Backend Confirmation

**Backend NOT modified. Procurement engine NOT modified. Database NOT modified. Authentication/RLS/JWT NOT modified. No 3D/WebGL introduced. No new dependency added.** Confirmed by `git status`: zero changes under `backend/` or `supabase/` beyond what was already present from prior phases before this session began, and `frontend/package.json`/`package-lock.json` show no new dependency entries from this phase. `python -m pytest -q` remains 178 passed / 0 failed / 0 skipped.

---

## UI-8 IMPLEMENTATION SUMMARY

**What changed:** The product's existing motion language (already established in UI-1) was extended, never replaced, with a small set of purposeful additions: a staggered Decision Hero reveal, a genuinely interactive Procurement Network (hover-dim, click-to-inspect real per-vendor detail, Escape-to-close), smooth candidate-group expand/collapse, a shared bar-grow reveal applied to all four existing bar charts across Results/Insights/Dashboard, a crossfading Analysis wizard step transition, and a small accessible Tooltip component used once, where it genuinely helps.

**Motion system:** No new duration/easing tokens — the existing micro/standard/emphasis tiers (`--transition-fast/base/slow`) already covered every case; formally documented for the first time. New reusable primitives: `.animate-in-delay-3/-4`, `.bar-grow-horizontal`, `.bar-grow-vertical` — all in `global.css`, all inheriting the existing site-wide reduced-motion override automatically.

**Network experience:** `SelectedGroupNetwork.jsx` upgraded from a plain click-to-select-ID toggle into a real interactive network: hover/focus highlight + dim, click/Enter/Space opens an accessible detail panel with real per-vendor price/demand/cost-share/savings (only fields the response actually carries), Escape closes it. Never implies geography; the existing "not a geographic map" label is preserved.

**Components created:** `components/common/Tooltip.jsx`.

**Components modified:** `results/{DecisionHero, SelectedGroupCard, SelectedGroupNetwork, VendorEconomics, CandidateGroupRow}.jsx`, `insights/{DecisionDistribution, GroupSizeAnalysis}.jsx`, `dashboard/SavingsAnalytics.jsx`, `analysis/{AnalysisForm, VendorCard, FormSection, steps/ReviewStep}.jsx`, `pages/ResultsPage.jsx`, `styles/{global.css, dashboard.css, results.css, components.css}`.

**Components deleted:** none.

**Backend changed:** NO
**Procurement engine changed:** NO
**Authentication/security changed:** NO
**3D/WebGL introduced:** NO

**Backend tests:** 178 passed, 0 failed, 0 skipped.
**Build:** clean, 187 modules, 0 errors.
**Lint:** clean, 0 warnings.
**Browser verification:** 42/42 (Results page: decision reveal, network interaction, candidate expand, bar-grow, reduced motion) + 8/8 (Analysis wizard step crossfade, including reduced motion) + 7/7 (unauthenticated route regression) — all via real Chromium against real and realistic data at 1440px/1024px/390px.
**Reduced-motion verification:** explicitly tested and confirmed neutralized (network, candidates, wizard, bar-grow all still fully functional, instantly) — inherited automatically from the existing global rule, zero new code required.
**Real-data verification:** the real `POTATO_HYD_2026_09` run rendered correctly through every new interaction — decision hero, network detail panel (verified real per-vendor figures for BOWENPALLY_POTATO_01), candidate groups, bar charts — matching this phase's own reference values exactly.
**Authenticated verification:** not possible — no real Supabase session available; documented rather than fabricated.
**Limitations:** no live authenticated click-through possible; History's row-level run ID intentionally keeps its native `title` tooltip rather than the new `Tooltip` component, to avoid an invalid nested-button structure.

**Report:** `reports/ui8_advanced_interactions_motion.md`

**Git operations:** NONE
