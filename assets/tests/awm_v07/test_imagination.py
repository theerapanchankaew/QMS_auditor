from datetime import datetime, timezone

import pytest

from aias_awm.adapters.legacy_harness import LegacyAIASHarnessStub
from aias_awm.cognition.imagination import (
    BoundedImaginationEngine,
    ImaginedNode,
    ImaginedTrajectory,
    reject_if_simulated,
)
from aias_awm.domain.models import (
    AtomicRequirement,
    AuditAction,
    AuditCase,
    EvidenceExpectation,
    RequirementAssessment,
)
from aias_awm.persistence import Database
from aias_awm.runtime import AuditWorldRuntime

NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)


def build_runtime():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    return AuditWorldRuntime(db, LegacyAIASHarnessStub(), source_manifest_hash="SRC1", rule_pack_hash="RULE1")


def action(action_id="A1", target="AR-6.1.3-E02"):
    return AuditAction(
        action_id=action_id, audit_case_id="CASE-IMG", action_type="REQUEST_RECORD",
        target_requirement_ids=[target], rationale="test", status="PROPOSED",
    )


def assessment(state="INSUFFICIENT_EVIDENCE", **overrides):
    base = dict(
        assessment_id="RA-CASE-IMG-AR-6.1.3-E02", audit_case_id="CASE-IMG",
        requirement_id="AR-6.1.3-E02", applicability="APPLICABLE", state=state,
        updated_at=NOW,
    )
    base.update(overrides)
    return RequirementAssessment(**base)


# --- unit tests: BoundedImaginationEngine.imagine_one() -----------------

def test_imagine_one_against_no_current_assessment_uses_synthetic_starting_point():
    node = BoundedImaginationEngine().imagine_one(action(), current_assessment=None)
    assert isinstance(node, ImaginedNode)
    assert node.predicted_assessment.requirement_id == "AR-6.1.3-E02"
    assert node.predicted_assessment.state.value == "INSUFFICIENT_EVIDENCE"
    assert node.predicted_assessment.breach_proven is False


def test_imagine_one_carries_forward_real_current_assessment_unchanged_by_default():
    real = assessment(coverage_ratio=0.5)
    node = BoundedImaginationEngine().imagine_one(action(), current_assessment=real)
    assert node.predicted_assessment.coverage_ratio == 0.5
    assert node.predicted_assessment.assessment_id == real.assessment_id


def test_imagine_one_rejects_firewalled_field_breach_proven():
    with pytest.raises(ValueError, match="firewalled"):
        BoundedImaginationEngine().imagine_one(
            action(), assessment(), predicted_delta={"breach_proven": True},
        )


def test_imagine_one_rejects_firewalled_field_state():
    with pytest.raises(ValueError, match="firewalled"):
        BoundedImaginationEngine().imagine_one(
            action(), assessment(), predicted_delta={"state": "BREACH_PROVEN"},
        )


def test_imagine_one_rejects_unrecognized_delta_field():
    with pytest.raises(ValueError, match="unrecognized"):
        BoundedImaginationEngine().imagine_one(
            action(), assessment(), predicted_delta={"not_a_real_field": 1},
        )


def test_imagine_one_allows_non_firewalled_delta_field():
    node = BoundedImaginationEngine().imagine_one(
        action(), assessment(), predicted_delta={"coverage_ratio": 0.9, "missing_evidence": []},
    )
    assert node.predicted_assessment.coverage_ratio == 0.9
    assert node.predicted_assessment.missing_evidence == []
    # the real assessment's state/breach_proven must survive untouched
    assert node.predicted_assessment.state.value == "INSUFFICIENT_EVIDENCE"
    assert node.predicted_assessment.breach_proven is False


def test_imagine_trajectory_is_tagged_with_firewall_markers():
    snapshot_like_requirement_states = []
    from aias_awm.domain.models import WorldSnapshot
    snap = WorldSnapshot(
        snapshot_id="SNAP-1", organization_id="ORG-IMG", as_of=NOW,
        requirement_states=snapshot_like_requirement_states,
        source_manifest_hash="H1", rule_pack_hash="H2", created_from_event_seq=0,
    )
    trajectories = BoundedImaginationEngine().imagine(snap, [action()])
    assert len(trajectories) == 1
    t = trajectories[0]
    assert isinstance(t, ImaginedTrajectory)
    assert t.simulation is True
    assert t.epistemic_class == "prediction_only"
    assert t.evidence_status == "not_audit_evidence"
    assert t.release_authority == "none"
    d = t.to_dict()
    assert d["simulation"] is True and d["release_authority"] == "none"


# --- reject_if_simulated() guard ----------------------------------------

def test_reject_if_simulated_raises_for_imagined_trajectory():
    from aias_awm.domain.models import WorldSnapshot
    snap = WorldSnapshot(
        snapshot_id="SNAP-2", organization_id="ORG-IMG", as_of=NOW,
        requirement_states=[], source_manifest_hash="H1", rule_pack_hash="H2", created_from_event_seq=0,
    )
    t = BoundedImaginationEngine().imagine(snap, [action()])[0]
    with pytest.raises(ValueError, match="Simulation Firewall"):
        reject_if_simulated(t)
    with pytest.raises(ValueError, match="Simulation Firewall"):
        reject_if_simulated(t.nodes[0])


def test_reject_if_simulated_passes_for_real_assessment():
    reject_if_simulated(assessment())  # must not raise
    reject_if_simulated({"simulation": False})  # must not raise
    with pytest.raises(ValueError):
        reject_if_simulated({"simulation": True})


# --- live, through AuditWorldRuntime -------------------------------------

def requirement():
    return AtomicRequirement(
        requirement_id="AR-6.1.3-E02", standard_id="ISO 9001:2026", clause="6.1.3",
        subject="organization", obligation="plan",
        object="actions to address these opportunities",
        semantic_category="AMBIGUOUS",
        evidence_expectations=[
            EvidenceExpectation(evidence_type="document", minimum_strength="documented", mandatory=False),
            EvidenceExpectation(evidence_type="observation", minimum_strength="implemented", mandatory=True),
        ],
        version="0.2.0-ai-draft-unreviewed",
    )


def test_imagine_actions_through_runtime_has_no_side_effects_on_real_state():
    """Bounded Imagination through the real runtime must not persist
    anything -- assessments/hypotheses/actions counts must be identical
    before and after calling imagine_actions()."""
    rt = build_runtime()
    rt.create_case(AuditCase(
        audit_case_id="CASE-IMG", organization_id="ORG-IMG", standard_ids=["ISO9001-2026"],
        audit_type="document_review", scope={}, created_at=NOW,
    ))
    rt.register_requirement(requirement())
    rt.reason("CASE-IMG", ["AR-6.1.3-E02"])  # produces one real pending action, no evidence ingested

    before_assessments = len(rt.assessments.list_for_case("CASE-IMG"))
    before_hypotheses = len(rt.hypotheses.list_for_case("CASE-IMG"))
    before_actions = len(rt.actions.list_for_case("CASE-IMG"))

    result = rt.imagine_actions("CASE-IMG")

    assert len(rt.assessments.list_for_case("CASE-IMG")) == before_assessments
    assert len(rt.hypotheses.list_for_case("CASE-IMG")) == before_hypotheses
    assert len(rt.actions.list_for_case("CASE-IMG")) == before_actions

    assert len(result["trajectories"]) == before_actions
    t = result["trajectories"][0]
    assert t["simulation"] is True
    assert t["release_authority"] == "none"
    assert t["nodes"][0]["predicted_assessment"]["requirement_id"] == "AR-6.1.3-E02"


def test_imagine_actions_through_runtime_rejects_firewalled_predicted_delta():
    rt = build_runtime()
    rt.create_case(AuditCase(
        audit_case_id="CASE-IMG2", organization_id="ORG-IMG2", standard_ids=["ISO9001-2026"],
        audit_type="document_review", scope={}, created_at=NOW,
    ))
    rt.register_requirement(requirement())
    rt.reason("CASE-IMG2", ["AR-6.1.3-E02"])
    real_action = rt.actions.list_for_case("CASE-IMG2")[0]

    with pytest.raises(ValueError, match="firewalled"):
        rt.imagine_actions(
            "CASE-IMG2",
            actions=[real_action],
            predicted_deltas={real_action.action_id: {"breach_proven": True}},
        )
