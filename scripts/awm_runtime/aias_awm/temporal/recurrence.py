from __future__ import annotations

from aias_awm.domain.models import EvidenceItem
from .models import CorrectiveActionLink, RecurrenceAssessment


class RecurrenceEngine:
    """Deterministic recurrence assessment.

    M5 eligibility is deliberately stricter than simple recurrence: the prior
    corrective action must have been effectiveness-verified and the current
    failure must be the same/equivalent failure. The final Major decision is
    still owned by the existing AIAS G8/M1-M5 severity gate and human auditor.
    """

    def assess(
        self,
        *,
        recurrence_id: str,
        organization_id: str,
        requirement_id: str,
        prior_finding_id: str,
        current_finding_id: str | None,
        current_observed_at,
        prior_ca: CorrectiveActionLink | None,
        same_or_equivalent_failure: bool,
        representative_scope_confirmed: bool,
        evidence_ids: list[str],
    ) -> RecurrenceAssessment:
        prior_effectiveness_verified = bool(
            prior_ca
            and prior_ca.effectiveness_verified_at is not None
            and prior_ca.effectiveness_result == "EFFECTIVE"
        )
        recurrence_proven = bool(
            same_or_equivalent_failure
            and prior_effectiveness_verified
            and evidence_ids
        )
        m5_eligible = bool(recurrence_proven and representative_scope_confirmed)

        if not same_or_equivalent_failure:
            rationale = "Current failure is not demonstrated to be the same or equivalent failure."
        elif not prior_effectiveness_verified:
            rationale = "Prior corrective action lacks verified-effective closure; M5 cannot be asserted."
        elif not evidence_ids:
            rationale = "Recurrence assertion lacks supporting current evidence."
        elif not representative_scope_confirmed:
            rationale = "Recurrence is evidenced but representative/system scope is not yet confirmed; escalate for review."
        else:
            rationale = "Same/equivalent failure recurred after verified-effective corrective action; M5 eligibility signal is present."

        return RecurrenceAssessment(
            recurrence_id=recurrence_id,
            organization_id=organization_id,
            requirement_id=requirement_id,
            prior_finding_id=prior_finding_id,
            current_finding_id=current_finding_id,
            prior_ca_id=prior_ca.ca_id if prior_ca else None,
            current_observed_at=current_observed_at,
            same_or_equivalent_failure=same_or_equivalent_failure,
            prior_effectiveness_verified=prior_effectiveness_verified,
            representative_scope_confirmed=representative_scope_confirmed,
            recurrence_proven=recurrence_proven,
            m5_eligible=m5_eligible,
            rationale=rationale,
            evidence_ids=evidence_ids,
        )
