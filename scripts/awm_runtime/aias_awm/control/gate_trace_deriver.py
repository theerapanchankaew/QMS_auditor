"""GateTraceDeriver -- deterministically derives a candidate
gate_execution_trace dict (the shape scripts/harness_gate_executor.py's
enforce_gates() expects) from real aias_awm state: RequirementAssessment +
AtomicRequirement + EvidenceItem + WorldSnapshot.

Provenance / rationale: references/70-harness-integration.md deliberately
did NOT build this, on the grounds that inventing the semantic mapping
"what aias_awm evidence corresponds to G6_complied_check.C3_elements_covered"
risked encoding an unreviewed judgement into a deterministic gate. Asked
directly to build it anyway, with the reasoning that Textbook Ch.14's
human authorities (H1 Action Authorization, H2 Escalation Review, H3 Final
Release) remain the final word regardless of what any candidate proposes --
gate_validation is an input to human review, not a replacement for it.
That does not make an overclaiming derivation harmless (a misleading
candidate can still waste a reviewer's time or bias their read), so this
module stays FAIL-CLOSED throughout: every field defaults to the most
conservative value (ABSENT / False / InsufficientEvidence / Minor) unless
a precise, already-real, mechanical signal justifies otherwise. See
references/71-gate-trace-derivation.md for the full field-by-field
mapping and worked examples, and its "What this does NOT do" section for
what still requires human/LLM judgement upstream (Thai-linguistic G2
triggers; the M4 test's A/B/C conditions, which are read from an explicit
OPT-IN evidence metadata convention rather than inferred from aggregate
counts -- see _derive_nc_class_and_g4 below).
"""
from __future__ import annotations

from aias_awm.domain.models import AtomicRequirement, EvidenceItem, RequirementAssessment, WorldSnapshot

_VERDICT_BY_STATE = {
    "SATISFIED": "Complied",
    "BREACH_PROVEN": "Noncomplied",
    "INSUFFICIENT_EVIDENCE": "InsufficientEvidence",
    "PARTIALLY_SUPPORTED": "InsufficientEvidence",
    "CONTRADICTORY": "ReviewRequired",
    "NOT_APPLICABLE": "OUT_OF_SCOPE",
    "REVIEW_REQUIRED": "ReviewRequired",
    "UNKNOWN": "InsufficientEvidence",
}

_EPISTEMIC_RANK = {
    "VERIFIED": 3, "CORROBORATED": 3,
    "PRESENTED": 2, "CLAIMED": 2, "PARSED": 2,
    "PARTIAL": 1,
    # CONTRADICTORY, INVALID, STALE, SUPERSEDED, UNKNOWN all rank 0 (treated
    # as not counting toward "activity" -- fail-closed, not silently upgraded)
}

_RECORD_LIKE_TYPES = {"record", "measurement", "system_log"}


def _closed_source_confirmed(snapshot: WorldSnapshot) -> bool:
    """G0. Maps to WorldSnapshot.source_manifest_hash being a real
    (non-placeholder) value -- the same closed-source-provenance concept
    this repo already tracks via source_manifest_validator.py /
    bundled-source-manifest.json, just read from aias_awm's own field for
    it instead of re-deriving it from scratch. The dev-mode default
    ("DEV-SOURCE", set by AuditWorldRuntime.__init__ when no real hash is
    supplied) deliberately does NOT count as confirmed."""
    h = snapshot.source_manifest_hash
    return bool(h) and h not in {"DEV-SOURCE", ""}


def _evidence_activity(evidence_items: list[EvidenceItem]) -> str:
    """G1. Same ABSENT/PRESENTED/VERIFIED/PARTIAL vocabulary
    world_constraint_validator.py already uses -- deliberately reused, not
    reinvented. Ranks the STRONGEST epistemic state among this
    requirement's evidence; CONTRADICTORY/INVALID/STALE/SUPERSEDED/UNKNOWN
    all rank as if absent (fail-closed: a pile of invalid or contradicted
    evidence does not count as "presented")."""
    if not evidence_items:
        return "ABSENT"
    best = max((_EPISTEMIC_RANK.get(e.epistemic_state.value, 0) for e in evidence_items), default=0)
    return {3: "VERIFIED", 2: "PRESENTED", 1: "PARTIAL"}.get(best, "ABSENT")


def _derive_nc_class_and_g4(requirement: AtomicRequirement, evidence_items: list[EvidenceItem]) -> tuple[str, dict]:
    """Only called when verdict == 'Noncomplied' (assessment.state ==
    BREACH_PROVEN). Returns (nc_class, G4_m4_conditions).

    D2_SAFE and AMBIGUOUS clauses always get the conservative 'Minor'
    ceiling here (matching G3's own real D2_SAFE_LIST ceiling, which will
    independently re-check this regardless).

    M4_MANDATORY clauses: 'Major' is proposed ONLY when every one of the
    M4 test's three conditions (A/B/C) is explicitly True via an OPT-IN
    evidence metadata convention -- 'process_entirely_absent',
    'zero_records_in_sample', 'interview_confirms_absence' -- because none
    of the three has a clean mechanical equivalent in aias_awm's existing
    structured fields (they describe systemic absence, not "evidence
    exists proving a violation", which is a different, more common case).
    Reading an explicit opt-in flag (that some upstream LLM/human step must
    have set) is safer than inferring "the process is entirely absent"
    from an aggregate count, which would risk a false Major. Missing any
    one of the three silently and safely falls back to 'Minor'."""
    if requirement.semantic_category != "M4_MANDATORY":
        return "Minor", {}
    a = any(bool(e.metadata.get("process_entirely_absent")) for e in evidence_items)
    b = any(bool(e.metadata.get("zero_records_in_sample")) for e in evidence_items)
    c = any(bool(e.metadata.get("interview_confirms_absence")) for e in evidence_items)
    if a and b and c:
        return "Major", {
            "m4_result": "Major M4",
            "A_process_entirely_absent": True,
            "B_zero_records_in_sample": True,
            "C_interview_confirms_absence": True,
        }
    return "Minor", {}


def _g6_complied_check(assessment: RequirementAssessment, evidence_items: list[EvidenceItem]) -> dict:
    """Only called when verdict == 'Complied' (assessment.state ==
    SATISFIED). C3 maps exactly and precisely to real data
    (coverage_ratio); C1/C2/C4 check the real evidence backing this
    assessment's own positive_evidence_ids for the right evidence_type /
    freshness -- no invented judgement, only structural facts already on
    these real objects."""
    positive_ids = set(assessment.positive_evidence_ids)
    positive_items = [e for e in evidence_items if e.evidence_id in positive_ids]
    return {
        "C1_implementation_proven": any(e.evidence_type == "observation" for e in positive_items),
        "C2_record_proven": any(e.evidence_type in _RECORD_LIKE_TYPES for e in positive_items),
        "C3_elements_covered": assessment.coverage_ratio == 1.0,
        "C4_evidence_current": bool(positive_items) and all(
            e.epistemic_state.value != "STALE" for e in positive_items
        ),
    }


def _decisive_question(requirement: AtomicRequirement) -> str:
    return (
        f"Does verified evidence establish that {requirement.subject} "
        f"{requirement.obligation} {requirement.object} ({requirement.clause})?"
    )


class GateTraceDeriver:
    """See module docstring. derive() never mutates its inputs and never
    persists anything -- it only builds a plain dict ready to submit to
    AuditWorldRuntime.make_decision() / harness_gate_executor.enforce_gates()."""

    def derive(
        self,
        *,
        assessment: RequirementAssessment,
        requirement: AtomicRequirement,
        evidence_items: list[EvidenceItem],
        snapshot: WorldSnapshot,
    ) -> dict:
        relevant = [e for e in evidence_items if assessment.requirement_id in e.related_requirement_ids]
        verdict = _VERDICT_BY_STATE.get(assessment.state.value, "InsufficientEvidence")

        nc_class = None
        g4 = {}
        if verdict == "Noncomplied":
            nc_class, g4 = _derive_nc_class_and_g4(requirement, relevant)

        g6 = _g6_complied_check(assessment, relevant) if verdict == "Complied" else {}

        trace = {
            "G0_preflight": {"closed_source_confirmed": _closed_source_confirmed(snapshot)},
            "G1_linguistic": {"evidence_activity": _evidence_activity(relevant)},
            "G2_ie_chain": {},  # not derivable -- see module docstring
            "G3_severity_ceiling": {},  # left to the harness's own real auto-detection
            "G4_m4_conditions": g4,
            "G6_complied_check": g6,
            "G7_trace": {"decisive_question": _decisive_question(requirement)},
        }
        return {
            "predicted_clause": requirement.clause,
            "clause": requirement.clause,
            "verdict": verdict,
            "nc_class": nc_class,
            "gate_execution_trace": trace,
            "derivation_provenance": {
                "assessment_id": assessment.assessment_id,
                "requirement_id": assessment.requirement_id,
                "derived_from_state": assessment.state.value,
                "note": (
                    "Mechanically derived candidate, conservative by construction -- "
                    "not an SME-authored verdict. See references/71-gate-trace-derivation.md. "
                    "Human H1/H2/H3 review is still required regardless of gate_validation."
                ),
            },
        }
