from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from aias_awm.domain.models import WorldSnapshot
from aias_awm.control.world_gates import WorldGateEngine


class ExistingAIASHarness(Protocol):
    def enforce(self, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class WorldToDecisionAdapter:
    world_gates: WorldGateEngine
    harness: ExistingAIASHarness

    def decide(self, snapshot: WorldSnapshot, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        gate_results = self.world_gates.evaluate(snapshot)
        wg6 = next(x for x in gate_results if x.gate_id == "WG6")
        if wg6.result != "PASS":
            return {
                "status": "WORLD_NOT_DECISION_READY",
                "world_gate_results": [x.__dict__ for x in gate_results],
                "candidate": candidate,
            }
        enriched = dict(context)
        enriched["world_snapshot_id"] = snapshot.snapshot_id
        enriched["world_gate_results"] = [x.__dict__ for x in gate_results]
        return self.harness.enforce(candidate, enriched)
