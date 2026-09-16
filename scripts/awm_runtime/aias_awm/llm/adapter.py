from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from aias_awm.domain.models import ReasoningProposal


class StructuredReasoningAdapter:
    """Boundary between probabilistic model output and the controlled runtime.

    The adapter only parses and validates. It never converts confidence into authority,
    changes world state, or releases a verdict.
    """

    def parse(self, payload: str | bytes | dict[str, Any]) -> ReasoningProposal:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            payload = json.loads(payload)
        return ReasoningProposal.model_validate(payload)

    def safe_parse(self, payload: str | bytes | dict[str, Any]) -> dict[str, Any]:
        try:
            proposal = self.parse(payload)
            return {"valid": True, "proposal": proposal, "errors": []}
        except (ValidationError, json.JSONDecodeError) as exc:
            return {"valid": False, "proposal": None, "errors": [str(exc)]}
