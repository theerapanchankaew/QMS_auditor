from __future__ import annotations

from datetime import datetime, timezone

from aias_awm.domain.models import AtomicRequirement, RequirementAssessment, RequirementState
from .evidence_reconciliation import EvidenceBundle


_STRENGTH_RANK = {
    "claim": 0,
    "documented": 1,
    "implemented": 2,
    "recorded": 3,
    "verified": 4,
    "effectiveness": 5,
}


class RequirementStateEngine:
    """Computes requirement state from controlled evidence bundles and atomic profiles.

    Evidence may explicitly encode `proves_breach=true` or `proves_effectiveness=true/false`
    in metadata. Missing evidence never proves a breach by itself.

    This is the canonical requirement-atomization + sufficiency + breach
    engine (see AtomicRequirement in domain/models.py for the AR schema).
    `applicability` is currently a caller-supplied input — no evaluator yet
    resolves `AtomicRequirement.applicability_rule_id` (the L7 conditional-
    qualifier / "as applicable" exception test). That is a confirmed real
    gap; see ../../../../docs/eei-blueprint-crosswalk.md before building it
    as a standalone module instead of extending this engine.
    """

    def assess(
        self,
        *,
        audit_case_id: str,
        requirement: AtomicRequirement,
        bundle: EvidenceBundle | None,
        applicability: str = "APPLICABLE",
        now: datetime | None = None,
    ) -> RequirementAssessment:
        now = now or datetime.now(timezone.utc)
        if applicability == "NOT_APPLICABLE":
            return RequirementAssessment(
                assessment_id=f"RA-{audit_case_id}-{requirement.requirement_id}",
                audit_case_id=audit_case_id,
                requirement_id=requirement.requirement_id,
                applicability="NOT_APPLICABLE",
                state=RequirementState.NOT_APPLICABLE,
                updated_at=now,
            )
        if applicability == "UNRESOLVED":
            return RequirementAssessment(
                assessment_id=f"RA-{audit_case_id}-{requirement.requirement_id}",
                audit_case_id=audit_case_id,
                requirement_id=requirement.requirement_id,
                applicability="UNRESOLVED",
                state=RequirementState.REVIEW_REQUIRED,
                missing_evidence=["applicability determination"],
                updated_at=now,
            )

        if bundle is None or not bundle.evidence:
            return self._insufficient(audit_case_id, requirement, [x.evidence_type for x in requirement.evidence_expectations if x.mandatory], now)

        if bundle.has_contradiction:
            return RequirementAssessment(
                assessment_id=f"RA-{audit_case_id}-{requirement.requirement_id}",
                audit_case_id=audit_case_id,
                requirement_id=requirement.requirement_id,
                applicability="APPLICABLE",
                state=RequirementState.CONTRADICTORY,
                positive_evidence_ids=list(bundle.positive_ids),
                negative_evidence_ids=list(bundle.negative_ids),
                contradictory_evidence_ids=list(bundle.contradictory_ids),
                breach_proven=False,
                updated_at=now,
            )

        active = [x for x in bundle.evidence if x.evidence_id not in bundle.invalid_ids]
        breach_evidence = [x for x in active if bool(x.metadata.get("proves_breach", False))]
        if breach_evidence:
            return RequirementAssessment(
                assessment_id=f"RA-{audit_case_id}-{requirement.requirement_id}",
                audit_case_id=audit_case_id,
                requirement_id=requirement.requirement_id,
                applicability="APPLICABLE",
                state=RequirementState.BREACH_PROVEN,
                positive_evidence_ids=list(bundle.positive_ids),
                negative_evidence_ids=[x.evidence_id for x in breach_evidence],
                breach_proven=True,
                effectiveness_proven=self._effectiveness(active),
                coverage_ratio=self._coverage(requirement, active),
                reasoning_candidate="Explicit verified evidence proves non-fulfilment; breach is not inferred from mere absence.",
                updated_at=now,
            )

        missing = self._missing_expectations(requirement, active)
        coverage = self._coverage(requirement, active)
        if missing:
            state = RequirementState.PARTIALLY_SUPPORTED if active else RequirementState.INSUFFICIENT_EVIDENCE
            return RequirementAssessment(
                assessment_id=f"RA-{audit_case_id}-{requirement.requirement_id}",
                audit_case_id=audit_case_id,
                requirement_id=requirement.requirement_id,
                applicability="APPLICABLE",
                state=state,
                positive_evidence_ids=list(bundle.positive_ids),
                negative_evidence_ids=list(bundle.negative_ids),
                missing_evidence=missing,
                coverage_ratio=coverage,
                breach_proven=False,
                effectiveness_proven=self._effectiveness(active),
                reasoning_candidate="Evidence exists but mandatory evidence expectations are not fully satisfied.",
                updated_at=now,
            )

        return RequirementAssessment(
            assessment_id=f"RA-{audit_case_id}-{requirement.requirement_id}",
            audit_case_id=audit_case_id,
            requirement_id=requirement.requirement_id,
            applicability="APPLICABLE",
            state=RequirementState.SATISFIED,
            positive_evidence_ids=list(bundle.positive_ids),
            negative_evidence_ids=list(bundle.negative_ids),
            coverage_ratio=coverage,
            breach_proven=False,
            effectiveness_proven=self._effectiveness(active),
            reasoning_candidate="Mandatory evidence expectations are satisfied and no breach evidence is present.",
            updated_at=now,
        )

    def _missing_expectations(self, req: AtomicRequirement, items) -> list[str]:
        missing: list[str] = []
        max_strength = max((self._item_strength(x) for x in items), default=-1)
        evidence_types = {str(x.metadata.get("evidence_role", x.evidence_type)) for x in items}
        for exp in req.evidence_expectations:
            if not exp.mandatory:
                continue
            type_present = exp.evidence_type in evidence_types or exp.evidence_type == "any"
            strength_ok = max_strength >= _STRENGTH_RANK[exp.minimum_strength]
            if not (type_present and strength_ok):
                missing.append(f"{exp.evidence_type}:{exp.minimum_strength}")
        return missing

    def _coverage(self, req: AtomicRequirement, items) -> float:
        mandatory = [x for x in req.evidence_expectations if x.mandatory]
        if not mandatory:
            return 1.0
        missing = self._missing_expectations(req, items)
        return (len(mandatory) - len(missing)) / len(mandatory)

    @staticmethod
    def _item_strength(item) -> int:
        explicit = item.metadata.get("strength")
        if explicit in _STRENGTH_RANK:
            return _STRENGTH_RANK[explicit]
        if item.epistemic_state.value in {"VERIFIED", "CORROBORATED"}:
            return _STRENGTH_RANK["verified"]
        if item.evidence_type in {"record", "measurement", "system_log"}:
            return _STRENGTH_RANK["recorded"]
        if item.evidence_type == "observation":
            return _STRENGTH_RANK["implemented"]
        if item.evidence_type == "document":
            return _STRENGTH_RANK["documented"]
        return _STRENGTH_RANK["claim"]

    @staticmethod
    def _effectiveness(items) -> bool | None:
        vals = [x.metadata.get("proves_effectiveness") for x in items if "proves_effectiveness" in x.metadata]
        if not vals:
            return None
        if any(v is False for v in vals):
            return False
        if all(v is True for v in vals):
            return True
        return None

    def _insufficient(self, case_id, req, missing, now):
        return RequirementAssessment(
            assessment_id=f"RA-{case_id}-{req.requirement_id}",
            audit_case_id=case_id,
            requirement_id=req.requirement_id,
            applicability="APPLICABLE",
            state=RequirementState.INSUFFICIENT_EVIDENCE,
            missing_evidence=missing,
            coverage_ratio=0.0,
            breach_proven=False,
            updated_at=now,
        )
