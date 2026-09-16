from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aias_awm.domain.models import RequirementAssessment, WorldSnapshot
from aias_awm.world.hashing import sha256_obj


@dataclass(frozen=True)
class WorldGateResult:
    gate_id: str
    result: str
    reason_code: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class WorldGateEngine:
    """WG0-WG6 deterministic pre-decision gates for the Audit World Model.

    Distinct from the G0-G7 verdict gates in scripts/harness_gate_executor.py
    (the assurance-boundary gate catalog). See
    ../../../../docs/eei-blueprint-crosswalk.md before adding another gate
    catalog.
    """

    def evaluate(
        self,
        snapshot: WorldSnapshot,
        *,
        source_manifest_resolved: bool = True,
        temporal_consistent: bool = True,
        entity_identity_consistent: bool = True,
        evidence_world_consistent: bool = True,
        hypothesis_complete: bool = True,
        action_admissible: bool = True,
        critical_contradictions: bool = False,
    ) -> list[WorldGateResult]:
        results: list[WorldGateResult] = []

        results.append(self._bool("WG0", source_manifest_resolved, "WORLD_LOAD_INTEGRITY"))
        results.append(self._bool("WG1", temporal_consistent, "TEMPORAL_CONSISTENCY"))
        results.append(self._bool("WG2", entity_identity_consistent, "ENTITY_IDENTITY_INTEGRITY"))
        results.append(self._bool("WG3", evidence_world_consistent, "EVIDENCE_WORLD_CONSISTENCY"))
        results.append(self._bool("WG4", hypothesis_complete, "HYPOTHESIS_COMPLETENESS"))
        results.append(self._bool("WG5", action_admissible, "ACTION_ADMISSIBILITY"))

        material = [x for x in snapshot.requirement_states if x.applicability == "APPLICABLE"]
        resolved = all(self._assessment_resolved(x) for x in material) if material else False
        ready = resolved and not critical_contradictions and all(r.result == "PASS" for r in results)
        results.append(
            WorldGateResult(
                gate_id="WG6",
                result="PASS" if ready else "BLOCK",
                reason_code=None if ready else "DECISION_NOT_READY",
                details={
                    "material_requirements": len(material),
                    "resolved": resolved,
                    "critical_contradictions": critical_contradictions,
                    "snapshot_hash": sha256_obj(snapshot.model_dump(mode="json")),
                },
            )
        )
        return results

    @staticmethod
    def _bool(gate_id: str, condition: bool, reason: str) -> WorldGateResult:
        return WorldGateResult(
            gate_id=gate_id,
            result="PASS" if condition else "BLOCK",
            reason_code=None if condition else reason,
        )

    @staticmethod
    def _assessment_resolved(a: RequirementAssessment) -> bool:
        return a.state.value in {
            "SATISFIED",
            "BREACH_PROVEN",
            "NOT_APPLICABLE",
        }
