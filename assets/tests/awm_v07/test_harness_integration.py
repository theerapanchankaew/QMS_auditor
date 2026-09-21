"""Proves the two Audit World Model systems this repo has (the older,
dict-based scripts/harness_gate_executor.py G0-G7 harness, and the newer
Pydantic/SQL-backed aias_awm) are actually wired together, not merely
structurally compatible on paper.

aias_awm/adapters/production_harness.py::ProductionHarnessAdapter and
aias_awm/control/decision_adapter.py::WorldToDecisionAdapter already
existed before this file -- but nothing in this repo ever actually
constructed a ProductionHarnessAdapter pointed at the real harness, or
called AuditWorldRuntime.make_decision() at all (grep confirmed zero
usage). This file closes that: it loads the REAL, unmodified
scripts/harness_gate_executor.py via ProductionHarnessAdapter and drives
real gate_execution_trace candidates through it, both directly and through
the full aias_awm decision path (WG0-WG6 readiness -> real G0-G7 harness).

See docs/eei-blueprint-crosswalk.md ("two separate Audit World Model
systems") and references/70-harness-integration.md for the full writeup,
including what this does NOT do (it does not auto-derive a
gate_execution_trace from a RequirementAssessment -- the caller still
builds that dict; the semantic mapping from aias_awm's evidence model to
the harness's G0-G7 field vocabulary is a separate, judgement-heavy task
not attempted here).
"""
from datetime import datetime, timezone
from pathlib import Path

from aias_awm.adapters.production_harness import ProductionHarnessAdapter
from aias_awm.control.decision_adapter import WorldToDecisionAdapter
from aias_awm.control.world_gates import WorldGateEngine
from aias_awm.domain.models import (
    AtomicRequirement,
    AuditCase,
    EpistemicState,
    EvidenceExpectation,
    EvidenceItem,
    RequirementAssessment,
    WorldSnapshot,
)
from aias_awm.persistence import Database
from aias_awm.runtime import AuditWorldRuntime

NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)
HARNESS_PATH = Path(__file__).resolve().parents[3] / "scripts" / "harness_gate_executor.py"


def real_harness() -> ProductionHarnessAdapter:
    assert HARNESS_PATH.exists(), HARNESS_PATH
    return ProductionHarnessAdapter(str(HARNESS_PATH))


def passing_candidate(clause="6.1.3"):
    """A gate_execution_trace shaped to sail through all six gates
    enforce_gates() runs, using the same minimal-PASS pattern this repo's
    own architecture walkthrough for clause 6.1.3 used earlier this
    session: InsufficientEvidence + nc_class=null skips G2/G3/G4/G6
    entirely, leaving only G0 and G7 to satisfy."""
    return {
        "predicted_clause": clause,
        "verdict": "InsufficientEvidence",
        "nc_class": None,
        "gate_execution_trace": {
            "G0_preflight": {"closed_source_confirmed": True},
            "G1_linguistic": {"evidence_activity": "VERIFIED"},
            "G7_trace": {"decisive_question": "Is objective evidence of the risk review present?"},
        },
    }


# --- direct: ProductionHarnessAdapter against the real harness file -----

def test_production_harness_adapter_loads_and_passes_real_candidate():
    result = real_harness().enforce(passing_candidate(), {"world_snapshot_id": "SNAP-1"})
    assert result["gate_validation"] == "PASS", result


def test_production_harness_adapter_real_rejection_from_g0():
    candidate = passing_candidate()
    candidate["gate_execution_trace"]["G0_preflight"] = {"closed_source_confirmed": False}
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "FAIL", result
    assert result["gate_failed"] == "G0", result
    assert result["rejection_reason"] == "G0_PREFLIGHT_NOT_CONFIRMED", result


def test_production_harness_adapter_real_rejection_from_g3_d2_safe_ceiling():
    """Uses the real D2_SAFE_LIST from the real harness file, not a
    re-typed copy -- clause 4.1 is D2_SAFE, so claiming Major must be
    force-ceilinged to Minor by the ACTUAL harness code."""
    candidate = passing_candidate(clause="4.1")
    candidate["nc_class"] = "Major"
    candidate["verdict"] = "Noncomplied"
    result = real_harness().enforce(candidate, {})
    assert result["gate_validation"] == "FAIL", result
    assert result["gate_failed"] == "G3", result
    assert result["forced_overrides"]["forced_nc_class"] == "Minor", result


# --- through WorldToDecisionAdapter: WG6 readiness gates the real harness -

def snapshot(*, resolved: bool):
    state = "SATISFIED" if resolved else "INSUFFICIENT_EVIDENCE"
    return WorldSnapshot(
        snapshot_id="SNAP-2", organization_id="ORG-HI", as_of=NOW,
        requirement_states=[RequirementAssessment(
            assessment_id="RA-1", audit_case_id="CASE-HI", requirement_id="AR-6.1.3-E02",
            applicability="APPLICABLE", state=state, updated_at=NOW,
        )],
        source_manifest_hash="H1", rule_pack_hash="H2", created_from_event_seq=0,
    )


def test_decision_adapter_delegates_to_real_harness_when_world_ready():
    adapter = WorldToDecisionAdapter(WorldGateEngine(), real_harness())
    result = adapter.decide(snapshot(resolved=True), passing_candidate(), {})
    assert result["gate_validation"] == "PASS", result


def test_decision_adapter_blocks_before_reaching_real_harness_when_world_not_ready():
    adapter = WorldToDecisionAdapter(WorldGateEngine(), real_harness())
    result = adapter.decide(snapshot(resolved=False), passing_candidate(), {})
    assert result["status"] == "WORLD_NOT_DECISION_READY", result
    # proves the real harness was never reached: its output always carries
    # gate_validation, which this early-return branch never sets
    assert "gate_validation" not in result, result


# --- full runtime path: register -> ingest -> reason -> make_decision ---

def requirement():
    return AtomicRequirement(
        requirement_id="AR-6.1.3-E02", standard_id="ISO 9001:2026", clause="6.1.3",
        subject="organization", obligation="plan",
        object="actions to address these opportunities",
        semantic_category="AMBIGUOUS",
        evidence_expectations=[
            EvidenceExpectation(evidence_type="observation", minimum_strength="implemented", mandatory=True),
        ],
        version="0.2.0-ai-draft-unreviewed",
    )


def test_make_decision_through_full_runtime_reaches_real_harness_once_world_resolved():
    """register_requirement -> ingest evidence that fully satisfies the
    mandatory expectation -> reason() resolves it to SATISFIED ->
    make_decision() must now delegate to the REAL harness and get a real
    PASS, using AuditWorldRuntime's own harness (not a hand-built adapter),
    exactly as a real deployment would construct it."""
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    rt = AuditWorldRuntime(db, real_harness(), source_manifest_hash="SRC1", rule_pack_hash="RULE1")
    rt.create_case(AuditCase(
        audit_case_id="CASE-HI", organization_id="ORG-HI", standard_ids=["ISO9001-2026"],
        audit_type="document_review", scope={}, created_at=NOW,
    ))
    rt.register_requirement(requirement())
    rt.ingest_evidence(EvidenceItem(
        evidence_id="EV-1", organization_id="ORG-HI", audit_case_id="CASE-HI",
        process_id="PROC-1", evidence_type="observation",
        assertion="Opportunity actions observed integrated into QMS processes",
        normalized_fact="opportunity actions implemented",
        epistemic_state=EpistemicState.VERIFIED,
        related_requirement_ids=["AR-6.1.3-E02"], metadata={},
    ))
    result = rt.reason("CASE-HI", ["AR-6.1.3-E02"])
    assert result["decision_ready"] is True, result

    decision = rt.make_decision("CASE-HI", passing_candidate())
    assert decision["gate_validation"] == "PASS", decision
