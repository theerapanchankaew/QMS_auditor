from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from aias_awm.adapters.legacy_harness import LegacyAIASHarnessStub
from aias_awm.api import create_app
from aias_awm.domain.models import AuditCase, AtomicRequirement, EvidenceExpectation, EvidenceItem, EpistemicState
from aias_awm.persistence import Database
from aias_awm.runtime import AuditWorldRuntime


def main():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    runtime = AuditWorldRuntime(db, LegacyAIASHarnessStub(), source_manifest_hash="TII-SOURCE-v1", rule_pack_hash="AIAS-GATES-v4")
    client = TestClient(create_app(runtime))

    case = AuditCase(
        audit_case_id="CASE-TII-613", organization_id="ORG-TII",
        standard_ids=["STD-ISO9001-2026"], audit_type="scenario_assessment",
        scope={"process_ids": ["PROC-CUSTOMER-SERVICE"]}, created_at=datetime.now(timezone.utc)
    )
    req = AtomicRequirement(
        requirement_id="AR-6.1.3-E06", standard_id="STD-ISO9001-2026", clause="6.1.3",
        subject="organization", obligation="evaluate", object="effectiveness_of_actions_to_address_opportunities",
        semantic_category="D2_SAFE",
        evidence_expectations=[EvidenceExpectation(evidence_type="effectiveness_evaluation", minimum_strength="effectiveness")],
        failure_patterns=["no_acceptance_criteria", "results_available_but_no_evaluation"],
        negative_inference_rules=["monitoring_data_alone_does_not_prove_effectiveness"], version="1.0"
    )
    client.post("/api/v1/audits/cases", json={"case": case.model_dump(mode="json")}).raise_for_status()
    client.post("/api/v1/requirements", json={"requirement": req.model_dump(mode="json")}).raise_for_status()

    monitor = EvidenceItem(
        evidence_id="EV-TII-MONITOR", organization_id="ORG-TII", audit_case_id="CASE-TII-613",
        evidence_type="record", assertion="Pilot metrics are monitored", epistemic_state=EpistemicState.VERIFIED,
        related_requirement_ids=["AR-6.1.3-E06"],
        metadata={"evidence_role": "monitoring", "strength": "recorded", "polarity": "support"}
    )
    client.post("/api/v1/audits/CASE-TII-613/evidence", json={"evidence": monitor.model_dump(mode="json")}).raise_for_status()
    print("STEP 1:", client.post("/api/v1/audits/CASE-TII-613/reason", json={"requirement_ids": ["AR-6.1.3-E06"]}).json())

    breach = EvidenceItem(
        evidence_id="EV-TII-NO-CRITERIA", organization_id="ORG-TII", audit_case_id="CASE-TII-613",
        evidence_type="record", assertion="No formal numerical acceptance criteria were established",
        epistemic_state=EpistemicState.VERIFIED, related_requirement_ids=["AR-6.1.3-E06"],
        metadata={"evidence_role": "effectiveness_evaluation", "strength": "effectiveness", "polarity": "negative", "proves_breach": True, "proves_effectiveness": False}
    )
    client.post("/api/v1/audits/CASE-TII-613/evidence", json={"evidence": breach.model_dump(mode="json")}).raise_for_status()
    print("STEP 2:", client.post("/api/v1/audits/CASE-TII-613/reason", json={"requirement_ids": ["AR-6.1.3-E06"]}).json())
    print("GRAPH:", client.get("/api/v1/audits/CASE-TII-613/graph").json())


if __name__ == "__main__":
    main()
