"""Bounded Imagination -- counterfactual, prediction-only trajectories for
candidate audit actions, with a Simulation Firewall that mirrors Textbook
Ch.11 ("Bounded Imagination"): simulated state must never be promoted to
verified evidence, must never set breach_proven/effectiveness_proven, must
never classify severity, and must never release a verdict.

Provenance: this package (aias_awm) had NO bounded-imagination mechanism at
all until this file -- confirmed by grepping the whole package for
simulat|imagin|counterfactual|trajectory|bounded before writing this (zero
hits). A working Simulation Firewall already existed, but only in a
completely separate, disconnected system: scripts/audit_world_model.py's
step() + scripts/imagination_engine.py (dict/JSON-based, no Pydantic, no
SQL, no cross-import with this package either direction -- see
docs/eei-blueprint-crosswalk.md, "two separate Audit World Model systems").
This file is a fresh implementation of the same firewall PATTERN
(FORBIDDEN_FIELDS stripping + simulation/epistemic_class/evidence_status/
release_authority tagging), adapted to this package's real
RequirementAssessment/AuditAction Pydantic types and WorldSnapshot -- not a
port or an import of the older system, since RequirementAssessment is a
StrictModel (extra="forbid") that cannot carry the older system's loose
dict-shaped simulation markers directly; those markers live on the
ImaginedNode/ImaginedTrajectory WRAPPER instead (plain dataclasses, not
persisted, not accepted by any repository's upsert()).

WHAT THIS DOES: given a WorldSnapshot and a list of candidate AuditActions
(as scripts/awm_runtime's own planner already proposes), produces one
ImaginedTrajectory per action -- a predicted RequirementAssessment for the
action's target requirement, optionally adjusted by a caller-supplied
`predicted_delta` for non-authoritative fields only (coverage_ratio,
missing_evidence, positive/negative/contradictory_evidence_ids,
reasoning_candidate). This is a deliberately thin scaffold, matching the
real capability level of the older system it parallels -- it does not
forecast what evidence an action would actually surface; it only lets a
caller explore "if this action came back looking like X, what would the
resulting assessment shape be" without ever touching real state.

WHAT THIS DOES NOT DO:
- It cannot set breach_proven, effectiveness_proven, or state via
  predicted_delta -- attempting to do so raises ValueError immediately
  (fail-closed, same posture as the rest of this repo's gates). Only
  RequirementStateEngine.assess() (real evidence) may set those fields.
- It never calls any repository's upsert() and is never called by
  AuditWorldRuntime.reason() or ingest_evidence() -- imagining a
  trajectory has zero effect on persisted case state. See
  reject_if_simulated() below, which any future persistence boundary
  should call as an explicit guard.
- It does not compute Hartley uncertainty or information gain itself --
  see aias_awm/hartley.py and cognition/planner.py for that, a separate
  concern this module does not duplicate.
- It does not evaluate whether the underlying WorldSnapshot is fresh or
  stale, and it does not run the W0-W9/WG0-WG6 world gates
  (control/world_gates.py) -- those govern REAL decision readiness, not
  imagined exploration.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from aias_awm.domain.models import AuditAction, RequirementAssessment, WorldSnapshot

# Fields on a RequirementAssessment that authoritatively express a
# conformity/severity/verdict-adjacent decision. Bounded Imagination must
# never set these via predicted_delta -- only real evidence promotion
# (RequirementStateEngine.assess()) may.
FIREWALLED_FIELDS = frozenset({"breach_proven", "effectiveness_proven", "state"})

_ALLOWED_DELTA_FIELDS = frozenset({
    "coverage_ratio", "missing_evidence", "reasoning_candidate",
    "positive_evidence_ids", "negative_evidence_ids", "contradictory_evidence_ids",
})


def _stable_hash(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class ImaginedNode:
    """One step of a trajectory: the action considered, and the resulting
    predicted (never persisted, never authoritative) RequirementAssessment."""
    action: AuditAction
    predicted_assessment: RequirementAssessment

    def to_dict(self) -> dict:
        return {
            "action": self.action.model_dump(mode="json"),
            "predicted_assessment": self.predicted_assessment.model_dump(mode="json"),
        }


@dataclass(frozen=True)
class ImaginedTrajectory:
    """A single candidate action's imagined outcome, firewalled per
    Textbook Ch.11. simulation/epistemic_class/evidence_status/
    release_authority are fixed, non-overridable markers -- exactly the
    four fields scripts/audit_world_model.py's step() also sets, so a
    human or downstream tool sees the same vocabulary regardless of which
    of this repo's two world-model systems produced it."""
    trajectory_id: str
    start_snapshot_id: str
    nodes: tuple[ImaginedNode, ...]
    simulation: bool = field(default=True, init=False)
    epistemic_class: str = field(default="prediction_only", init=False)
    evidence_status: str = field(default="not_audit_evidence", init=False)
    release_authority: str = field(default="none", init=False)

    def to_dict(self) -> dict:
        return {
            "trajectory_id": self.trajectory_id,
            "start_snapshot_id": self.start_snapshot_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "simulation": self.simulation,
            "epistemic_class": self.epistemic_class,
            "evidence_status": self.evidence_status,
            "release_authority": self.release_authority,
        }


def reject_if_simulated(candidate) -> None:
    """Guard for any real persistence or verdict boundary that might
    accidentally receive imagined output. Raises ValueError if `candidate`
    is an ImaginedTrajectory/ImaginedNode, or any object/dict explicitly
    carrying simulation=True -- mirrors scripts/audit_world_model.py's
    FORBIDDEN_FIELDS stripping, but as an explicit raise instead of a
    silent pop(), since this package's repositories have no field to
    silently strip from in the first place (RequirementAssessment has no
    'simulation' field at all -- see this module's own docstring for why)."""
    if isinstance(candidate, (ImaginedTrajectory, ImaginedNode)):
        raise ValueError(
            "Simulated/imagined data must never be persisted as real case "
            "state or used to set a verdict (Ch.11 Simulation Firewall)."
        )
    if isinstance(candidate, dict) and candidate.get("simulation") is True:
        raise ValueError(
            "Simulated/imagined data must never be persisted as real case "
            "state or used to set a verdict (Ch.11 Simulation Firewall)."
        )


class BoundedImaginationEngine:
    """Produces ImaginedTrajectory objects for candidate actions against a
    WorldSnapshot, without mutating any real state. See module docstring."""

    def imagine(
        self,
        snapshot: WorldSnapshot,
        candidate_actions: list[AuditAction],
        predicted_deltas: dict[str, dict] | None = None,
    ) -> list[ImaginedTrajectory]:
        """predicted_deltas is optional, keyed by action_id -> delta dict
        (see imagine_one()). Actions with no target_requirement_ids, or
        whose target isn't in the snapshot, still produce a trajectory
        against a synthetic UNRESOLVED starting point -- imagining an
        action for a requirement not yet assessed is a legitimate use case
        (e.g. "what if we requested this record before assessing at all")."""
        predicted_deltas = predicted_deltas or {}
        by_requirement = {a.requirement_id: a for a in snapshot.requirement_states}
        trajectories = []
        for action in candidate_actions:
            current = None
            if action.target_requirement_ids:
                current = by_requirement.get(action.target_requirement_ids[0])
            node = self.imagine_one(action, current, predicted_deltas.get(action.action_id))
            trajectories.append(ImaginedTrajectory(
                trajectory_id=_stable_hash({"snapshot": snapshot.snapshot_id, "action": action.action_id}),
                start_snapshot_id=snapshot.snapshot_id,
                nodes=(node,),
            ))
        return trajectories

    def imagine_one(
        self,
        action: AuditAction,
        current_assessment: RequirementAssessment | None,
        predicted_delta: dict | None = None,
    ) -> ImaginedNode:
        if predicted_delta:
            forbidden = set(predicted_delta) & FIREWALLED_FIELDS
            if forbidden:
                raise ValueError(
                    f"Bounded Imagination cannot set {sorted(forbidden)} via predicted_delta -- "
                    "these are firewalled per Ch.11's Simulation Firewall; only real evidence "
                    "promotion (RequirementStateEngine.assess()) may set them."
                )
            unknown = set(predicted_delta) - _ALLOWED_DELTA_FIELDS
            if unknown:
                raise ValueError(f"predicted_delta has unrecognized field(s) {sorted(unknown)}")

        requirement_id = action.target_requirement_ids[0] if action.target_requirement_ids else "UNKNOWN"
        if current_assessment is not None:
            base = current_assessment.model_dump(mode="python")
        else:
            # No real assessment exists yet for this requirement -- start
            # from the same starting point RequirementStateEngine.assess()
            # itself uses when no evidence has been ingested at all
            # (see cognition/requirement_engine.py::_insufficient()).
            base = {
                "assessment_id": f"SIM-{action.action_id}",
                "audit_case_id": action.audit_case_id,
                "requirement_id": requirement_id,
                "applicability": "APPLICABLE",
                "state": "INSUFFICIENT_EVIDENCE",
                "updated_at": datetime.now(timezone.utc),
            }
        base.update(predicted_delta or {})
        predicted = RequirementAssessment.model_validate(base)
        return ImaginedNode(action=action, predicted_assessment=predicted)
