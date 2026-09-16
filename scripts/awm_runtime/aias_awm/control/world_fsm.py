from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorldState(str, Enum):
    W0_UNINITIALIZED = "W0_UNINITIALIZED"
    W1_WORLD_LOADED = "W1_WORLD_LOADED"
    W2_OBSERVATION_INGESTED = "W2_OBSERVATION_INGESTED"
    W3_WORLD_UPDATED = "W3_WORLD_UPDATED"
    W4_UNCERTAINTY_ANALYZED = "W4_UNCERTAINTY_ANALYZED"
    W5_HYPOTHESES_UPDATED = "W5_HYPOTHESES_UPDATED"
    W6_ACTION_PLANNED = "W6_ACTION_PLANNED"
    W7_EVIDENCE_ACQUISITION = "W7_EVIDENCE_ACQUISITION"
    W8_WORLD_RECONCILED = "W8_WORLD_RECONCILED"
    W9_AUDIT_READY = "W9_AUDIT_READY"


ALLOWED_TRANSITIONS = {
    WorldState.W0_UNINITIALIZED: {WorldState.W1_WORLD_LOADED},
    WorldState.W1_WORLD_LOADED: {WorldState.W2_OBSERVATION_INGESTED},
    WorldState.W2_OBSERVATION_INGESTED: {WorldState.W3_WORLD_UPDATED},
    WorldState.W3_WORLD_UPDATED: {WorldState.W4_UNCERTAINTY_ANALYZED},
    WorldState.W4_UNCERTAINTY_ANALYZED: {WorldState.W5_HYPOTHESES_UPDATED},
    WorldState.W5_HYPOTHESES_UPDATED: {WorldState.W6_ACTION_PLANNED, WorldState.W8_WORLD_RECONCILED},
    WorldState.W6_ACTION_PLANNED: {WorldState.W7_EVIDENCE_ACQUISITION},
    WorldState.W7_EVIDENCE_ACQUISITION: {WorldState.W2_OBSERVATION_INGESTED},
    WorldState.W8_WORLD_RECONCILED: {WorldState.W4_UNCERTAINTY_ANALYZED, WorldState.W9_AUDIT_READY},
    WorldState.W9_AUDIT_READY: set(),
}


@dataclass
class WorldFSM:
    state: WorldState = WorldState.W0_UNINITIALIZED

    def transition(self, next_state: WorldState) -> WorldState:
        if next_state not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"forbidden world-state transition: {self.state} -> {next_state}")
        self.state = next_state
        return self.state
