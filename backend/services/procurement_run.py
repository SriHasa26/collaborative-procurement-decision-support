"""
Phase 6E -- application-level orchestration layer.

ONE public entry point: ProcurementRunService.run(ProcurementRunInput) ->
ProcurementRunResult. This module contains NO validation, demand
estimation, eligibility, geographic, group-formation, decision, or
selection logic of its own -- it only sequences existing, unmodified
Phase 6B/6C/6D services in the fixed order Phase 6E's own spec requires,
and assembles their already-computed outputs into one structured result.

PIPELINE (fixed order, must not change):
    Phase 6B: backend.services.pipeline.evaluate_procurement_context
        -> validation, demand estimation, eligibility (all internal to
           that one call -- Phase 6E does not call validation.py or
           eligibility.py directly, since evaluate_procurement_context
           already sequences them correctly; calling them separately here
           would be a duplicate, competing orchestration of the same
           steps, not a reuse of them)
    Phase 6C: backend.services.group_formation.form_candidate_groups
    Phase 6D: backend.services.batch_decision.run_procurement_decision
        -> which itself sequences decision_evaluation.evaluate_candidate_groups
           (per-candidate evaluation + WAIT/EXPAND resolution) and
           selection.select_final_groups (overlap resolution + final
           lexicographic selection)

STOP-CONDITION / RUN_STATUS PRECEDENCE (Phase 6E Sections 4, 9, 18):
Checked in this fixed order; the first that applies determines the
result's run_status. Each condition is a direct, derived fact about the
pipeline's own actual output -- none is guessed or estimated:

    1. COMPLETED_INVALID_CONTEXT
       -- the procurement context itself was structurally invalid
          (Phase 6B's own context_validation.is_valid is False). No
          per-vendor processing, group formation, evaluation, or
          selection is attempted (Phase 6B already enforces this
          internally; Phase 6E does not attempt to work around it).
    2. COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS
       -- fewer than 2 eligible vendors (Step 5, Cases A/B). No
          compatibility graph, no group formation, no evaluation, no
          selection is attempted -- a single vendor (or zero) cannot form
          a collaborative group by definition (Phase 2B Part 2).
    3. COMPLETED_NO_GROUPS
       -- 2+ eligible vendors, but Phase 6C's compatibility graph produced
          zero candidate groups (Step 7, Case C -- e.g. every vendor ended
          up geographically isolated). No candidate evaluation or
          selection is attempted on an empty candidate list.
    4. COMPLETED_NO_SELECTION
       -- candidate groups existed and were evaluated, but none survived
          to a final BUY_TOGETHER selection (Case D). Selection ran; it
          legitimately produced an empty selected-group set. This is NOT
          an error and NOT the same as "no groups existed at all" --
          hence a distinct status rather than reusing COMPLETED_NO_GROUPS.
    5. COMPLETED_WITH_ABSTENTIONS
       -- the full pipeline reached a non-empty final selection, but at
          least one submitted vendor abstained or had a validation error
          along the way. The run is a genuine success; this status only
          flags that not every submitted vendor participated in it.
    6. COMPLETED
       -- the full pipeline reached a non-empty final selection and every
          submitted vendor was eligible (no abstentions, no validation
          errors).

This precedence means a run that, say, has both zero candidate groups AND
some abstained vendors is reported as COMPLETED_NO_GROUPS, not
COMPLETED_WITH_ABSTENTIONS -- the more specific "how far did the pipeline
get" fact takes priority, since it is strictly more informative. The
abstention/validation-error counts are ALWAYS present on the result
regardless of run_status (via batch_eligibility and the *_count fields),
so no information is ever lost to this precedence choice.

DELIBERATE NON-DECISION: this module does not wrap the Phase 6C/6D calls
in a blanket try/except. Group formation and decision evaluation are pure
computations over already-validated, already-eligible input (Phase 6B's
own boundary); a genuine exception there indicates a real defect and must
propagate visibly, per this project's standing "do not hide failures"
rule -- it is not disguised as a run_status value. (Phase 6B's own
per-vendor defense-in-depth, inside evaluate_procurement_context, is
untouched and still applies to malformed individual vendor submissions.)
"""

from backend.models.run_contracts import ProcurementRunInput, ProcurementRunResult, RunStatus
from backend.services.batch_decision import run_procurement_decision
from backend.services.group_formation import form_candidate_groups
from backend.services.pipeline import evaluate_procurement_context


class ProcurementRunService:
    """The one public entry point for running a full procurement analysis."""

    def run(self, run_input: ProcurementRunInput) -> ProcurementRunResult:
        batch_eligibility = evaluate_procurement_context(
            run_input.context, list(run_input.vendor_submissions)
        )

        if not batch_eligibility.context_validation.is_valid:
            return self._assemble(
                run_input, batch_eligibility,
                group_formation=None, final_selection=None,
                run_status=RunStatus.COMPLETED_INVALID_CONTEXT,
            )

        eligible_vendor_inputs = [r.vendor_input for r in batch_eligibility.eligible_vendors]

        if len(eligible_vendor_inputs) < 2:
            return self._assemble(
                run_input, batch_eligibility,
                group_formation=None, final_selection=None,
                run_status=RunStatus.COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS,
            )

        group_formation = form_candidate_groups(
            eligible_vendors=eligible_vendor_inputs,
            commodity_id=run_input.commodity.commodity_id,
            context_date=run_input.context.date,
            d_max_km=run_input.config.d_max_km,
        )

        if len(group_formation.candidate_groups) == 0:
            return self._assemble(
                run_input, batch_eligibility,
                group_formation=group_formation, final_selection=None,
                run_status=RunStatus.COMPLETED_NO_GROUPS,
            )

        final_selection = run_procurement_decision(
            group_formation, run_input.commodity, run_input.context, run_input.config
        )

        has_mixed_outcomes = bool(batch_eligibility.abstained_vendors) or bool(
            batch_eligibility.validation_error_vendors
        )
        if len(final_selection.selected_group_ids) == 0:
            run_status = RunStatus.COMPLETED_NO_SELECTION
        elif has_mixed_outcomes:
            run_status = RunStatus.COMPLETED_WITH_ABSTENTIONS
        else:
            run_status = RunStatus.COMPLETED

        return self._assemble(
            run_input, batch_eligibility,
            group_formation=group_formation, final_selection=final_selection,
            run_status=run_status,
        )

    @staticmethod
    def _assemble(run_input, batch_eligibility, group_formation, final_selection, run_status) -> ProcurementRunResult:
        return ProcurementRunResult(
            run_status=run_status.value,
            commodity_id=run_input.commodity.commodity_id,
            context_date=run_input.context.date,
            total_vendors_submitted=len(run_input.vendor_submissions),
            eligible_vendor_count=len(batch_eligibility.eligible_vendors),
            abstained_vendor_count=len(batch_eligibility.abstained_vendors),
            validation_error_vendor_count=len(batch_eligibility.validation_error_vendors),
            candidate_group_count=len(group_formation.candidate_groups) if group_formation else 0,
            selected_group_count=len(final_selection.selected_group_ids) if final_selection else 0,
            batch_eligibility=batch_eligibility,
            group_formation=group_formation,
            final_selection=final_selection,
        )
