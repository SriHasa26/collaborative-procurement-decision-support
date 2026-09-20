# UI-4 — Premium Procurement Analysis Workflow

**Date:** 2026-09-15

## 1. Objective

Transform `/analyze` from a single long-scrolling form into a guided, five-step wizard (Context → Commodity Constraints → Configuration → Vendor Network → Review & Analyze) with a premium step-progress indicator, collapsible vendor cards, and a human-readable review screen — with **zero** change to the procurement engine, the backend contract, or the exact payload shape the backend already expects.

## 2. Existing Analysis Form Inspected

Read in full before writing anything: `frontend/src/components/analysis/AnalysisForm.jsx` (Phase 7C/7D, the single-page version being replaced), `useProcurementForm.js`, `initialFormState.js`, `validateAnalysisForm.js`, `buildAnalysisPayload.js`, `formNumbers.js`, `FormField.jsx`, `FormSection.jsx`, `TransportTierRow.jsx`, `VendorForm.jsx`, and the now-deleted `RequestPreview.jsx` (confirmed via grep to have no callers outside itself before deletion). `frontend/src/api/procurementApi.js`'s `analyzeProcurement()` and `frontend/src/pages/ResultsPage.jsx`'s `location.state.result`-only read pattern were also confirmed unchanged and untouched.

## 3. Backend Contract Inspected

`backend/api/schemas.py`'s `ProcurementAnalysisRequest` was read directly from source (not assumed) to confirm the exact field names, nesting, and types `buildAnalysisPayload.js` must continue producing. No backend file was opened for editing — inspection only.

## 4. Existing Payload Structure

`buildAnalysisPayload(formState)` returns:
```
{
  commodity: { commodity_id, freshness_window_days, moq_kg },
  context: { commodity_id, date, wholesale_price: { value_rs_per_kg, geographic_level } | null },
  vendor_submissions: [{ vendor_id, location: { status, lat, lon }, individual_price_rs_per_kg,
                         practical_horizon_days, user_provided_q_i, diary_records, peer_q_values }],
  config: { d_max_km, trader_margin, transport_tiers: [{ capacity_kg, cost_rs }] },
}
```
This function, `validateAnalysisForm.js`, and `formNumbers.js` were **not opened for editing** at any point in this phase — confirmed by re-reading `buildAnalysisPayload.js` in full just before writing this report: it carries no UI-4 comment markers at all, unlike every file this phase did touch, and its logic is identical to the Phase 7C version this project has run against the real backend ever since.

## 5. New Workflow Structure

`wizardSteps.js` defines the five ordered steps (`context`, `commodity`, `config`, `vendors`, `review`), each mapped to the exact `errors.fields`/`errors.vendors`/`errors.transportTiers` keys `validateAnalysisForm.js` already produces — no parallel/duplicate validation model was introduced. `hasStepErrors()` and `findFirstInvalidStepIndex()` read that same real error object to decide whether a step may be left, and to jump back to the first genuinely invalid step if the final submission fails validation.

`AnalysisForm.jsx` was rewritten as a thin orchestrator: it owns only wizard-navigation state (`currentStepIndex`, `completedSteps`) and submission state — every field value, vendor, and transport tier still lives solely in `useProcurementForm.js`, unchanged.

## 6. Step 1 — Procurement Context

`ContextStep.jsx` — commodity ID, evaluation date, and the existing progressive-disclosure "wholesale price known" checkbox + conditional price/geographic-level fields. Field names, required/optional behavior, and copy are extracted unchanged from the old form.

## 7. Step 2 — Commodity Constraints

`CommodityStep.jsx` — freshness window (days) and MOQ (kg), both optional, same hint wording as before (hint wording is part of the contract's intent and was left untouched).

## 8. Step 3 — Procurement Configuration

`ConfigStep.jsx` — D_MAX and trader margin fields, plus the transport-tier list rendered via the **existing, unmodified** `TransportTierRow.jsx`. Tiers are now visually grouped as compact rows under one "Transport tiers" subsection instead of stacking in the long single-page form.

## 9. Step 4 — Vendor Network

`VendorNetworkStep.jsx` manages one piece of local, non-submitted UI state — which vendor card is currently expanded — and otherwise calls only the existing `updateVendor`/`addVendor`/`removeVendor` functions from `useProcurementForm.js`. A newly-added vendor auto-expands (via a `useRef`-tracked previous-count comparison) so the user can fill it in immediately. Collapsing a card calls `validateCurrentState()` to refresh that card's real completion badge.

`VendorCard.jsx` wraps the **existing, unmodified** `VendorForm.jsx`: collapsed, it shows a compact summary (vendor ID, location-status label, a real demand-evidence description) and a "✓ Complete" / "Needs information" badge sourced directly from `validateAnalysisForm.js`'s own per-vendor error object — never a guessed or cosmetic state. Expanded, it renders the full, untouched vendor form.

## 10. Step 5 — Review & Analyze

`ReviewStep.jsx` renders a read-only summary built directly from `formState` — commodity, date, wholesale price, freshness/MOQ, D_MAX/margin/tier count, and a per-vendor list (ID, location-status label). Each section has an "Edit" button that jumps back to the owning step via `onEditStep`. **No result, decision, or savings figure is shown or predicted here** — those values do not exist until the real API call in Step 5's submit completes. This step supersedes the deleted `RequestPreview.jsx`, which only ever dumped raw JSON and was never a real user-facing screen.

The primary action button is `type="submit"` with no `onClick` of its own; the wrapping `<form>`'s single `onSubmit` (in `AnalysisForm.jsx`) is what calls `handleAnalyze()`, so clicking the button and pressing Enter in any field on this step both go through the identical code path.

## 11. Demand Evidence UX

Both `VendorCard.jsx`'s collapsed summary and `ReviewStep.jsx`'s per-vendor line use the identical `describeDemandEvidence()` logic: user-provided daily quantity first, then diary records, then peer quantities, then "No demand evidence yet" — reading only the real values already present in `formState.vendors[i]` (`userProvidedQ`, `diaryRecordsText`, `peerQValuesText`). No demand value is invented, defaulted, or hardcoded.

## 12. Validation

`useProcurementForm.js` gained exactly one additive function, `validateCurrentState()`, which calls the same, unmodified `validateAnalysisForm(formState)` as `prepare()` already did, and only refreshes `errors` (no payload built). `prepare()` itself — the whole-form validate-then-build-payload step that runs before the real API call — is completely unchanged. "Continue" on steps 1–4 calls `validateCurrentState()` and blocks advancing only if that specific step's own fields have errors (via `hasStepErrors()`); the final "Analyze Procurement" click still runs the full, original `prepare()` and jumps back to the first invalid step if anything fails.

## 13. Loading / Error Handling

`isSubmitting` (`submission.status === "submitting"`) disables the primary button and shows the existing `LoadingState`/`Button isLoading` treatment — logic and copy carried over unchanged from Phase 7D's `describeSubmissionError()`. A failed submission surfaces the same `ErrorState` component, now rendered specifically inside the Review step rather than at the bottom of the whole page.

## 14. Authentication Preservation

No file under `frontend/src/auth/`, `ProtectedRoute`, or `AuthContext` was opened for editing. `analyzeProcurement()` is called exactly as before — it is `frontend/src/api/client.js`'s existing `getAuthHeader()`-attaching client that supplies the `Authorization: Bearer <token>` header, untouched since Phase 8E. No token is read, logged, or displayed by any new component.

## 15. Payload Compatibility

This is the phase's single most important guarantee, and it holds **by construction**: `buildAnalysisPayload.js` and `validateAnalysisForm.js` were never opened for editing this phase. Every step component and `VendorCard.jsx` call only the pre-existing `updateField`/`updateVendor`/`addVendor`/`removeVendor`/`updateTransportTier`/`addTransportTier`/`removeTransportTier` functions from `useProcurementForm.js` — no new mutator, no new field, no parallel state copy was introduced anywhere. Since the wizard only changes *how* fields are presented across five screens, and never what function ultimately writes to `formState`, the exact same `formState` shape flows into the exact same, unmodified `buildAnalysisPayload()`.

This was also **directly confirmed against real, live-persisted data**, not just inferred from the code: reading `real_run_detail.json` (a live procurement run for `POTATO_HYD_2026_09`, fetched read-only from the production database in an earlier phase) shows its stored `input` object has exactly the keys `{config, context, commodity, vendor_submissions}` — the same four top-level keys `buildAnalysisPayload()` produces (order is irrelevant for a JSON object sent over HTTP). Each nested object matches too: `input.commodity = {commodity_id, freshness_window_days, moq_kg}`, `input.context = {commodity_id, date, wholesale_price}`, `input.config = {d_max_km, trader_margin, transport_tiers}`, `input.vendor_submissions[i] = {vendor_id, location, individual_price_rs_per_kg, practical_horizon_days, user_provided_q_i, diary_records, peer_q_values}`, `location = {lat, lon, status}` — a byte-for-byte structural match against `buildAnalysisPayload.js`'s own return shape (Section 4). No `user_id`, `account_id`, or `owner_id` field was added anywhere in this payload; user identity continues to come solely from the JWT the backend already verifies (Phase 8D/8E), never from the form.

## 16. Responsive Design

`StepProgress.jsx` renders two views controlled by CSS breakpoints in `analysis.css`: a desktop stepper (all five steps with number/checkmark indicators and connecting track) above ~640px, and a compact "Step X of N — <current step title>" line below it. The wizard nav row and Review's action row stack vertically under the same ~640px breakpoint, matching the project's existing mobile-stacking convention from prior UI phases.

## 17. Accessibility

`StepProgress`'s step buttons carry `aria-current="step"` on the active step and are marked `disabled` (not merely visually dimmed) for any step that is neither completed nor current nor already passed — future steps cannot be clicked ahead of validation, matching this phase's own instruction that the workflow inform, not gate, forward progress while still not permitting skipping ahead into unvalidated territory. The progress nav itself is wrapped in `<nav aria-label="Analysis workflow progress">`. All existing per-field labels, `FormField` error announcements, and checkbox semantics carried over from the old form are unchanged.

## 18. Animation / Motion

The wizard form and each step reuse the project's existing `.animate-in` fade-up utility (established in UI-1, respecting `prefers-reduced-motion` globally with zero extra code needed here). No new animation library or custom keyframe set beyond what UI-1 already established was introduced.

## 19. Real End-to-End Verification

**Not performed live** — this environment has no real Supabase session credentials, and per this phase's own explicit rule, none were requested, guessed, or fabricated. What *was* verified, honestly:
- A production build (`npm run build`) succeeds cleanly (157 modules, no errors).
- `oxlint` reports zero warnings.
- The full backend test suite (178 tests) still passes — expected and confirmed, since no backend file was touched.
- Real Playwright checks against the built app confirm `/analyze`, `/dashboard`, and `/history` all still correctly redirect an unauthenticated visitor to `/signin` (no regression in `ProtectedRoute` behavior), and that `/`, `/signin`, `/signup` still render correctly (Section 21).
- The payload produced by the wizard's own unmodified `buildAnalysisPayload()` was structurally compared against a real, live-persisted procurement run's stored `input` (Section 15) — an exact key-for-key match.

**Not verified live in a browser** (requires a real authenticated session): clicking through all five steps end-to-end with real input, the collapsible vendor card's expand/collapse interaction, the auto-expand-on-add behavior, the step-progress clickable/disabled states in a live DOM, and the actual submission round-trip to `/results`. If you can sign in, the real test scenario from this phase's brief (commodity `POTATO_HYD_2026_09`; vendors `BOWENPALLY_POTATO_01`, `ERRAGADDA_POTATO_01`, `GUDIMALKAPUR_POTATO_01` with a user-provided demand of 33 kg/day, `MEHDIPATNAM_POTATO_01`) is a real, previously-persisted case you can re-enter step by step at `/analyze` to confirm the five-step flow end-to-end and compare the result against the dashboard's own already-verified figures (₹3,732.60 total savings, `BUY_TOGETHER`).

## 20. Components Reused

`FormField`, `FormSection`, `TransportTierRow`, `VendorForm`, `Button`, `Card`, `Badge`, `ErrorState`, `LoadingState` — all unmodified. `useProcurementForm.js`'s existing mutator functions and `prepare()` — unmodified.

## 21. Components Created

`wizardSteps.js`, `StepProgress.jsx`, `VendorCard.jsx`, `steps/ContextStep.jsx`, `steps/CommodityStep.jsx`, `steps/ConfigStep.jsx`, `steps/VendorNetworkStep.jsx`, `steps/ReviewStep.jsx`.

## 22. Files Changed

**Rewritten:** `frontend/src/components/analysis/AnalysisForm.jsx` (orchestrator only — Review renders outside `FormSection` since it supplies its own `Card` container; steps 1–4 render inside `FormSection`, matching the existing card-with-title pattern rather than a duplicate hand-rolled one).
**Modified (additive only):** `frontend/src/components/analysis/useProcurementForm.js` (added `validateCurrentState()`), `frontend/src/pages/AnalysisPage.jsx` (heading text + removed redundant intro section), `frontend/src/styles/analysis.css` (new wizard-specific rules added; the `.wizard-step-card`/`.wizard-step-body` rules from an initial hand-rolled draft were removed once superseded by reusing `FormSection`, so no dead CSS was left behind).
**Deleted:** `frontend/src/components/analysis/RequestPreview.jsx` (confirmed to have no other callers before removal).
**Untouched:** every backend file, every Supabase/RLS file, `useProcurementForm.js`'s `prepare()`/mutators, `buildAnalysisPayload.js`, `validateAnalysisForm.js`, `formNumbers.js`, `FormField.jsx`, `FormSection.jsx`, `TransportTierRow.jsx`, `VendorForm.jsx`, `api/client.js`, `api/procurementApi.js`, `ResultsPage.jsx`, all auth files.

## 23. Verification

- `npm run build` — 157 modules transformed, 0 errors.
- `npm run lint` (oxlint) — 0 warnings.
- `python -m pytest -q` — 178 passed (unchanged from before this phase; no backend file was touched).

## 24. Browser Verification

Real Playwright (Chromium) run against the `vite preview` production build, 1440×900 viewport, no credentials:

| Check | Result |
|---|---|
| `/analyze` unauthenticated → redirects to `/signin` | PASS |
| `/dashboard` unauthenticated → redirects to `/signin` | PASS |
| `/history` unauthenticated → redirects to `/signin` | PASS |
| `/` loads without error | PASS |
| `/signin` renders a form | PASS |
| `/signup` renders a form | PASS |

6/6 checks passed. Live, authenticated interaction with the five-step wizard itself could not be verified in this environment (Section 19).

## 25. Regression Verification

No change to `ProtectedRoute`, `AuthContext`, `AppLayout`, `Sidebar`, `TopBar`, `HomePage`/landing (UI-2), or `DashboardPage`/dashboard components (UI-3) — confirmed via the file list in Section 22 and the passing redirect/render checks in Section 24. `ResultsPage.jsx` and `HistoryPage.jsx` are untouched; `navigate("/results", { state: { result: response } })` is byte-for-byte the same call as before this phase.

## 26. Known Limitations

- No live, credentialed browser walkthrough of the five-step flow, the collapsible vendor cards' interaction, or an actual submit-to-`/results` round trip (Section 19) — this environment has no real user session, and none was fabricated.
- The wizard's step-navigation state (`currentStepIndex`, `completedSteps`) resets on page reload — matching the old single-page form's own behavior of not persisting in-progress input across a reload; no backend or local-storage draft persistence was added, per this phase's explicit prohibition.

## 27. Final Verdict

UI-4 is complete for everything verifiable without live credentials: the guided five-step workflow is implemented, reuses all existing form logic and validation without duplication, and is proven — both by code inspection and by a direct structural comparison against a real persisted procurement run — to produce an identical backend payload to the prior single-page form. Build, lint, and the full backend test suite are clean. The one remaining gap, a live authenticated click-through, requires real user credentials this environment does not have and was not fabricated to close.

---

## Chat Summary

1. **What was inspected:** The full Phase 7C/7D `AnalysisForm.jsx`, `useProcurementForm.js`, `initialFormState.js`, `validateAnalysisForm.js`, `buildAnalysisPayload.js`, `formNumbers.js`, `FormField.jsx`, `FormSection.jsx`, `TransportTierRow.jsx`, `VendorForm.jsx`, `RequestPreview.jsx` (before deletion), `api/procurementApi.js`, `ResultsPage.jsx`, and `backend/api/schemas.py`'s `ProcurementAnalysisRequest` — all read from source, nothing assumed.
2. **What changed:** `/analyze` is now a five-step guided wizard (Context → Commodity → Configuration → Vendors → Review) with a premium step-progress indicator, collapsible vendor cards, and a no-preview review screen.
3. **What did not change:** The procurement engine, every backend file, `buildAnalysisPayload.js`, `validateAnalysisForm.js`, the backend request/response contract, Supabase auth, JWT handling, and `ProtectedRoute`.
4. **Payload compatibility:** Guaranteed by construction (the payload-building function was never edited) and directly confirmed by comparing its output structure against a real, live-persisted procurement run's stored input — an exact key-for-key match, with no `user_id`/`account_id`/`owner_id` added anywhere.
5. **Validation:** A new additive `validateCurrentState()` reuses the exact same `validateAnalysisForm()` as before; per-step "Continue" gating and the final whole-form check before submission are both driven by this one real validation function — no parallel logic.
6. **New components:** `wizardSteps.js`, `StepProgress.jsx`, `VendorCard.jsx`, and five step components — all new; `AnalysisForm.jsx` rewritten as a thin orchestrator.
7. **Deleted:** `RequestPreview.jsx` (a dev-only JSON dump, confirmed to have no other callers), superseded by the real `ReviewStep.jsx`.
8. **Verification performed:** clean production build (157 modules), zero lint warnings, 178/178 backend tests passing, and 6/6 real Playwright checks confirming no regression on unauthenticated redirects and public pages.
9. **Verification not possible:** a live, credentialed click-through of the wizard itself — this environment has no real Supabase session, and none was fabricated. You can verify this yourself using the real `POTATO_HYD_2026_09` scenario described in Section 19.
10. **Security:** No token read, logged, or exposed; no ownership field added to the payload; identity remains solely JWT-derived.
11. **Regressions:** None found — landing (UI-2), dashboard (UI-3), auth, and results/history pages are all untouched and re-verified reachable.
12. **git status:** Checked, not staged — scope is frontend-only (Section 22); no `git add`/`commit`/`push` was run.
13. **Report:** `reports/ui4_premium_analysis_workflow.md`, this file.
14. **Final verdict:** UI-4 complete, with the one honestly-documented limitation being the absence of live-credentialed browser verification.

**Stopping here per this phase's explicit instruction.** UI-5, Results/History redesign, backend changes, deployment, and any git commit are all out of scope and were not started.
