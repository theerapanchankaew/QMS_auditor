from __future__ import annotations

from typing import Any


class LegacyAIASHarnessStub:
    """Development adapter only.

    It demonstrates the integration boundary expected by WorldToDecisionAdapter.
    Replace with the production AIAS G0-G13 deterministic harness.
    """

    def enforce(self, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        if not candidate.get("gate_execution_trace"):
            return {
                "status": "REJECTED",
                "reason": "MISSING_GATE_EXECUTION_TRACE",
                "forced_verdict": "ReviewRequired",
                "context": context,
            }
        return {
            "status": "HUMAN_REVIEW_REQUIRED",
            "validated_candidate": candidate,
            "context": context,
        }
