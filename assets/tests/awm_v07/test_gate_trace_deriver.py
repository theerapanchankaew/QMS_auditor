"""Proves GateTraceDeriver derives a candidate gate_execution_trace from
real aias_awm state (RequirementAssessment/AtomicRequirement/EvidenceItem/
WorldSnapshot), and that the derived candidate actually survives real
enforcement by the unmodified scripts/harness_gate_executor.py -- both the
conservative-default (fail-closed) paths and the paths where real evidence
justifies a stronger candidate.

See references/71-gate-trace-derivation.md for the full field mapping and
docs/eei-blueprint-crosswalk.md ("Update ... auto-derivation") for why this
was built after references/70-harness-integration.md deliberately did not.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aias_awm.adapters.production_harness import ProductionHarnessAdapter
from aias_awm.control.gate_trace_deriver import GateTraceDeriver
from aias_awm.domain.models import (
    AtomicRequirement,
    AuditCase,
    EpistemicState,
    EvidenceExpectation,
    EvidenceItem,
    RequirementAssessment,
    RequirementState,
    WorldSnapshot,
)
from aias_awm.persistence import Database
from aias_awm.runtime import AuditWorldRuntime

NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)
HARNESS_PATH = Path(__file__).resolve().parents[3] / "scripts" / "harness_gate_executor.py"


def real_harness() -> ProductionHarnessAdapter:
    assert HARNESS_PATH.exists(), HARNESS_PATH
    return ProductionHarnessAdapter(str(HARNESS_PATH))


def requirement(clause="6.1.3", category="AMBIGUOUS"):
    return AtomicRequirement(
        requirement_id="AR-X-E01", standard_id="ISO 9001:2026", clause=clause,
        subject="organization", obligation="plan", object="actions",
        semantic_category=category,
        evidence_expectations=[EvidenceExpectation(evidence_type="observation", minimum_strength="implemented", mandatory=True)],
        version="0.2.0-ai-draft-unreviewed",
    )


def snapshot(source_manifest_hash="REAL-SHA256-ABC"):
    return WorldSnapshot(
        snapshot_id="SNAP-1", organization_id="ORG-1", as_of=NOW,
        requirement_states=[], source_manifest_hash=source_manifest_hash,
        rule_pack_hash="RULE1", created_from_event_seq=0,
    )


def evidence(evidence_id, evidence_type, epistemic_state, metadata=None, valid_to=None):
    return EvidenceItem(
        evidence_id=evidence_id, organization_id="ORG-1", audit_case_id="CASE-1",
        process_id="PROC-1", evidence_type=evidence_type, assertion="x",
        epistemic_state=epistemic_state, related_requirement_ids=["AR-X-E01"],
        metadata=metadata or {}, valid_to=valid_to,
    )


def assessment(state, **overrides):
    base = dict(
        assessment_id="RA-1", audit_case_id="CASE-1", requirement_id="AR-X-E01",
        applicability="APPLICABLE", state=state, updated_at=NOW,
    )
    base.update(overrides)
    return RequirementAssessment(**base)


# --- unit: field-by-field derivation correctness -------------------------

def test_verdict_mapping_is_conservative_for_every_state():
    deriver = GateTraceDeriver()
    expected = {
        "SATISFIED": "Complied",
        "BREACH_PROVEN": "Noncomplied",
        "INSUFFICIENT_EVIDENCE": "InsufficientEvidence",
        "PARTIALLY_SUPPORTED": "InsufficientEvidence",
        "CONTRADICTORY": "ReviewRequired",
        "NOT_APPLICABLE": "OUT_OF_SCOPE",
        "REVIEW_REQUIRED": "ReviewRequired",
        "UNKNOWN": "InsufficientEvidence",
    }
    for state, verdict in expected.items():
        a = assessment(state, applicability="NOT_APPLICABLE" if state == "NOT_APPLICABLE" else "APPLICABLE")
        candidate = deriver.derive(assessment=a, requirement=requirement(), evidence_items=[], snapshot=snapshot())
        assert candidate["verdict"] == verdict, (state, candidate["verdict"])


def test_g0_closed_source_rejects_dev_placeholder_hash():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(),
        evidence_items=[], snapshot=snapshot(source_manifest_hash="DEV-SOURCE"),
    )
    assert candidate["gate_execution_trace"]["G0_preflight"]["closed_source_confirmed"] is False


def test_g0_closed_source_confirmed_for_real_hash():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(),
        evidence_items=[], snapshot=snapshot(source_manifest_hash="REAL-SHA256-ABC"),
    )
    assert candidate["gate_execution_trace"]["G0_preflight"]["closed_source_confirmed"] is True


def test_g1_evidence_activity_absent_with_no_evidence():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(), evidence_items=[], snapshot=snapshot())
    assert candidate["gate_execution_trace"]["G1_linguistic"]["evidence_activity"] == "ABSENT"


def test_g1_evidence_activity_verified_beats_presented():
    deriver = GateTraceDeriver()
    ev = [
        evidence("E1", "document", EpistemicState.PRESENTED),
        evidence("E2", "observation", EpistemicState.VERIFIED),
    ]
    candidate = deriver.derive(assessment=assessment("SATISFIED"), requirement=requirement(), evidence_items=ev, snapshot=snapshot())
    assert candidate["gate_execution_trace"]["G1_linguistic"]["evidence_activity"] == "VERIFIED"


def test_g1_evidence_activity_ignores_contradictory_and_stale():
    deriver = GateTraceDeriver()
    ev = [evidence("E1", "document", EpistemicState.CONTRADICTORY), evidence("E2", "record", EpistemicState.STALE)]
    candidate = deriver.derive(assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(), evidence_items=ev, snapshot=snapshot())
    assert candidate["gate_execution_trace"]["G1_linguistic"]["evidence_activity"] == "ABSENT"


def test_nc_class_defaults_minor_for_d2_safe_even_when_breach_proven():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("BREACH_PROVEN", breach_proven=True),
        requirement=requirement(clause="4.1", category="D2_SAFE"),
        evidence_items=[], snapshot=snapshot(),
    )
    assert candidate["nc_class"] == "Minor"
    assert candidate["gate_execution_trace"]["G4_m4_conditions"] == {}


def test_nc_class_defaults_minor_for_m4_mandatory_without_opt_in_flags():
    """Fail-closed: BREACH_PROVEN + M4_MANDATORY alone is NOT enough to
    propose Major -- the opt-in A/B/C metadata must be explicitly present."""
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("BREACH_PROVEN", breach_proven=True),
        requirement=requirement(clause="6.1.1", category="M4_MANDATORY"),
        evidence_items=[evidence("E1", "record", EpistemicState.VERIFIED, metadata={"proves_breach": True})],
        snapshot=snapshot(),
    )
    assert candidate["nc_class"] == "Minor"


def test_nc_class_proposes_major_only_when_all_three_opt_in_flags_present():
    deriver = GateTraceDeriver()
    ev = [evidence("E1", "record", EpistemicState.VERIFIED, metadata={
        "proves_breach": True,
        "process_entirely_absent": True,
        "zero_records_in_sample": True,
        "interview_confirms_absence": True,
    })]
    candidate = deriver.derive(
        assessment=assessment("BREACH_PROVEN", breach_proven=True),
        requirement=requirement(clause="6.1.1", category="M4_MANDATORY"),
        evidence_items=ev, snapshot=snapshot(),
    )
    assert candidate["nc_class"] == "Major"
    g4 = candidate["gate_execution_trace"]["G4_m4_conditions"]
    assert g4["m4_result"] == "Major M4"
    assert g4["A_process_entirely_absent"] and g4["B_zero_records_in_sample"] and g4["C_interview_confirms_absence"]


def test_nc_class_minor_when_only_partial_opt_in_flags_present():
    deriver = GateTraceDeriver()
    ev = [evidence("E1", "record", EpistemicState.VERIFIED, metadata={
        "proves_breach": True, "process_entirely_absent": True,
        # B and C missing
    })]
    candidate = deriver.derive(
        assessment=assessment("BREACH_PROVEN", breach_proven=True),
        requirement=requirement(clause="6.1.1", category="M4_MANDATORY"),
        evidence_items=ev, snapshot=snapshot(),
    )
    assert candidate["nc_class"] == "Minor"
    assert candidate["gate_execution_trace"]["G4_m4_conditions"] == {}


def test_g6_c3_maps_exactly_from_coverage_ratio():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("SATISFIED", coverage_ratio=1.0, positive_evidence_ids=["E1", "E2"]),
        requirement=requirement(), evidence_items=[
            evidence("E1", "observation", EpistemicState.VERIFIED),
            evidence("E2", "record", EpistemicState.VERIFIED),
        ], snapshot=snapshot(),
    )
    g6 = candidate["gate_execution_trace"]["G6_complied_check"]
    assert g6["C1_implementation_proven"] is True
    assert g6["C2_record_proven"] is True
    assert g6["C3_elements_covered"] is True
    assert g6["C4_evidence_current"] is True


def test_g6_c3_false_when_coverage_incomplete():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("SATISFIED", coverage_ratio=0.5, positive_evidence_ids=["E1"]),
        requirement=requirement(), evidence_items=[evidence("E1", "observation", EpistemicState.VERIFIED)],
        snapshot=snapshot(),
    )
    assert candidate["gate_execution_trace"]["G6_complied_check"]["C3_elements_covered"] is False


def test_g6_c4_false_when_only_positive_evidence_is_stale():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("SATISFIED", coverage_ratio=1.0, positive_evidence_ids=["E1"]),
        requirement=requirement(), evidence_items=[evidence("E1", "observation", EpistemicState.STALE)],
        snapshot=snapshot(),
    )
    assert candidate["gate_execution_trace"]["G6_complied_check"]["C4_evidence_current"] is False


def test_g7_decisive_question_always_present():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(), evidence_items=[], snapshot=snapshot())
    assert candidate["gate_execution_trace"]["G7_trace"]["decisive_question"]


# --- integration: derived candidate through the REAL harness -------------

def test_derived_insufficient_evidence_candidate_passes_real_harness():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(),
        evidence_items=[], snapshot=snapshot(),
    )
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "PASS", result


def test_derived_dev_placeholder_source_hash_is_rejected_by_real_g0():
    """The one deliberately conservative default (DEV-SOURCE) must cause a
    REAL rejection from the actual harness, not a silent pass."""
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("INSUFFICIENT_EVIDENCE"), requirement=requirement(),
        evidence_items=[], snapshot=snapshot(source_manifest_hash="DEV-SOURCE"),
    )
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "FAIL", result
    assert result["gate_failed"] == "G0", result


def test_derived_major_with_full_m4_evidence_passes_real_g4():
    deriver = GateTraceDeriver()
    ev = [evidence("E1", "record", EpistemicState.VERIFIED, metadata={
        "proves_breach": True, "process_entirely_absent": True,
        "zero_records_in_sample": True, "interview_confirms_absence": True,
    })]
    candidate = deriver.derive(
        assessment=assessment("BREACH_PROVEN", breach_proven=True),
        requirement=requirement(clause="6.1.1", category="M4_MANDATORY"),
        evidence_items=ev, snapshot=snapshot(),
    )
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "PASS", result
    assert result["nc_class"] == "Major", result


def test_derived_complied_with_full_coverage_passes_real_g6():
    deriver = GateTraceDeriver()
    ev = [
        evidence("E1", "observation", EpistemicState.VERIFIED),
        evidence("E2", "record", EpistemicState.VERIFIED, valid_to=NOW + timedelta(days=30)),
    ]
    candidate = deriver.derive(
        assessment=assessment("SATISFIED", coverage_ratio=1.0, positive_evidence_ids=["E1", "E2"]),
        requirement=requirement(), evidence_items=ev, snapshot=snapshot(),
    )
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "PASS", result


def test_derived_complied_with_incomplete_coverage_is_rejected_by_real_g6():
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("SATISFIED", coverage_ratio=0.5, positive_evidence_ids=["E1"]),
        requirement=requirement(), evidence_items=[evidence("E1", "observation", EpistemicState.VERIFIED)],
        snapshot=snapshot(),
    )
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "FAIL", result
    assert result["gate_failed"] == "G6", result
    assert result["forced_overrides"]["forced_verdict"] == "InsufficientEvidence", result


def test_derived_noncomplied_for_d2_safe_passes_real_g3_ceiling():
    """The deriver already proposes Minor for D2_SAFE; the real G3 ceiling
    check must have nothing to object to."""
    deriver = GateTraceDeriver()
    candidate = deriver.derive(
        assessment=assessment("BREACH_PROVEN", breach_proven=True),
        requirement=requirement(clause="4.1", category="D2_SAFE"),
        evidence_items=[], snapshot=snapshot(),
    )
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "PASS", result
    assert result["nc_class"] == "Minor", result


# --- full live path: reason() -> make_decision_for_requirement() --------

def real_requirement_6_1_1():
    return AtomicRequirement(
        requirement_id="AR-6.1.1-E03", standard_id="ISO 9001:2026", clause="6.1.1",
        subject="organization", obligation="determine risks and opportunities to",
        object="give assurance that the quality management system can achieve its intended result(s)",
        semantic_category="M4_MANDATORY",
        evidence_expectations=[EvidenceExpectation(evidence_type="observation", minimum_strength="implemented", mandatory=True)],
        version="0.2.0-ai-draft-unreviewed",
    )


def test_make_decision_for_requirement_full_live_path_with_real_breach_evidence():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    rt = AuditWorldRuntime(db, real_harness(), source_manifest_hash="REAL-SHA256-XYZ", rule_pack_hash="RULE1")
    rt.create_case(AuditCase(
        audit_case_id="CASE-DERIVE", organization_id="ORG-DERIVE", standard_ids=["ISO9001-2026"],
        audit_type="document_review", scope={}, created_at=NOW,
    ))
    rt.register_requirement(real_requirement_6_1_1())
    rt.ingest_evidence(EvidenceItem(
        evidence_id="EV-BREACH-1", organization_id="ORG-DERIVE", audit_case_id="CASE-DERIVE",
        process_id="PROC-1", evidence_type="record",
        assertion="No risk/opportunity determination process exists at all; no records, no interviews confirm any activity",
        epistemic_state=EpistemicState.VERIFIED, related_requirement_ids=["AR-6.1.1-E03"],
        metadata={
            "proves_breach": True,
            "process_entirely_absent": True,
            "zero_records_in_sample": True,
            "interview_confirms_absence": True,
        },
    ))
    rt.reason("CASE-DERIVE", ["AR-6.1.1-E03"])

    decision = rt.make_decision_for_requirement("CASE-DERIVE", "AR-6.1.1-E03")
    assert decision["gate_validation"] == "PASS", decision
    assert decision["nc_class"] == "Major", decision
    assert decision["derived_candidate"]["derivation_provenance"]["requirement_id"] == "AR-6.1.1-E03"
