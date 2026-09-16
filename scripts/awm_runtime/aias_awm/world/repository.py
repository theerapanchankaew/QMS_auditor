from __future__ import annotations

from aias_awm.domain.models import WorldEvent, WorldSnapshot
from aias_awm.world.event_store import EventStore
from aias_awm.world.reducer import WorldReducer


class WorldRepository:
    def __init__(self, event_store: EventStore, reducer: WorldReducer) -> None:
        self.event_store = event_store
        self.reducer = reducer

    def load(self, organization_id: str) -> WorldSnapshot:
        return self.reducer.replay(organization_id, self.event_store.list(organization_id))

    def append_and_load(self, event: WorldEvent) -> WorldSnapshot:
        self.event_store.append(event)
        return self.load(event.organization_id)
