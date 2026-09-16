from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Protocol

from aias_awm.domain.models import WorldEvent


class EventStore(Protocol):
    def append(self, event: WorldEvent) -> None: ...
    def list(self, organization_id: str, after_seq: int = -1) -> list[WorldEvent]: ...
    def last_sequence(self, organization_id: str) -> int: ...


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: dict[str, list[WorldEvent]] = defaultdict(list)

    def append(self, event: WorldEvent) -> None:
        events = self._events[event.organization_id]
        expected = 0 if not events else events[-1].sequence_no + 1
        if event.sequence_no != expected:
            raise ValueError(f"sequence mismatch: expected {expected}, got {event.sequence_no}")
        events.append(event)

    def extend(self, events: Iterable[WorldEvent]) -> None:
        for event in events:
            self.append(event)

    def list(self, organization_id: str, after_seq: int = -1) -> list[WorldEvent]:
        return [e for e in self._events.get(organization_id, []) if e.sequence_no > after_seq]

    def last_sequence(self, organization_id: str) -> int:
        events = self._events.get(organization_id, [])
        return -1 if not events else events[-1].sequence_no
