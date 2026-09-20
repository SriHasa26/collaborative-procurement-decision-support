// UI-5 -- Section 9: "Diagnostics, Warnings & Limitations". Every item
// below is derived from a REAL field already present in the response --
// context_validation.reasons, abstained/validation-error vendor counts,
// group_formation.singleton_vendor_ids, group_formation.diagnostics'
// large_pool_warning flag, and final_selection's own
// non_selected_buy_together_results/wait_or_expand_results/
// do_not_buy_results/abstained_results counts (each already partitioned
// by the backend's own selection.py by final_decision_state -- never
// re-derived here). No generic "AI warning" is ever generated; when none
// of these real conditions apply, this section says so plainly rather
// than inventing something to fill the space.

import { getContextValidationReasonLabel } from "./resultHelpers";

function DiagnosticItem({ variant, children }) {
  return <li className={`diagnostic-item diagnostic-item-${variant}`}>{children}</li>;
}

function DecisionDiagnostics({ result }) {
  const batchEligibility = result.batch_eligibility;
  const groupFormation = result.group_formation;
  const finalSelection = result.final_selection;
  const items = [];

  const contextValidation = batchEligibility?.context_validation;
  if (contextValidation && !contextValidation.is_valid) {
    for (const reason of contextValidation.reasons ?? []) {
      items.push(
        <DiagnosticItem key={`context-${reason}`} variant="warning">
          {getContextValidationReasonLabel(reason)}
        </DiagnosticItem>
      );
    }
  }

  if (result.abstained_vendor_count > 0) {
    items.push(
      <DiagnosticItem key="abstained" variant="info">
        {result.abstained_vendor_count} vendor(s) abstained due to insufficient evidence — see Vendor Submission
        Detail below.
      </DiagnosticItem>
    );
  }

  if (result.validation_error_vendor_count > 0) {
    items.push(
      <DiagnosticItem key="validation-errors" variant="danger">
        {result.validation_error_vendor_count} vendor submission(s) had validation errors — see Vendor Submission
        Detail below.
      </DiagnosticItem>
    );
  }

  const singletonVendorIds = groupFormation?.singleton_vendor_ids ?? [];
  if (singletonVendorIds.length > 0) {
    items.push(
      <DiagnosticItem key="singletons" variant="info">
        {singletonVendorIds.length} eligible vendor(s) had no geographically compatible pool-mate:{" "}
        {singletonVendorIds.join(", ")}.
      </DiagnosticItem>
    );
  }

  for (const diagnostic of groupFormation?.diagnostics ?? []) {
    if (diagnostic.large_pool_warning) {
      items.push(
        <DiagnosticItem key={`pool-${diagnostic.pool_id}`} variant="warning">
          Compatibility pool {diagnostic.pool_id} has {diagnostic.vendor_count} vendors, producing{" "}
          {diagnostic.nominal_candidate_count} candidate groups — evaluation may be computationally heavy for
          very large pools.
        </DiagnosticItem>
      );
    }
  }

  const nonSelectedBuyTogether = finalSelection?.non_selected_buy_together_results ?? [];
  if (nonSelectedBuyTogether.length > 0) {
    items.push(
      <DiagnosticItem key="non-selected" variant="info">
        {nonSelectedBuyTogether.length} other feasible group(s) were eligible but not selected, because their
        vendors overlap with an already-selected group.
      </DiagnosticItem>
    );
  }

  const waitOrExpand = finalSelection?.wait_or_expand_results ?? [];
  if (waitOrExpand.length > 0) {
    items.push(
      <DiagnosticItem key="wait-or-expand" variant="warning">
        {waitOrExpand.length} group(s) remain in a Wait/Expand state — see Candidate Groups Evaluated for details.
      </DiagnosticItem>
    );
  }

  return (
    <section className="page-section" id="diagnostics" aria-labelledby="diagnostics-heading">
      <h2 id="diagnostics-heading" className="section-title">
        Diagnostics, Warnings &amp; Limitations
      </h2>

      {items.length === 0 ? (
        <p className="text-small text-muted">No decision warnings were reported for this run.</p>
      ) : (
        <ul className="diagnostics-list">{items}</ul>
      )}
    </section>
  );
}

export default DecisionDiagnostics;
