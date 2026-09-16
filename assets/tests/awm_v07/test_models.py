from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from aias_awm.domain.models import EvidenceItem, EpistemicState, SourcePointer


def test_evidence_item_valid():
    item = EvidenceItem(
        evidence_id="EV-1",
        organization_id="ORG-1",
        evidence_type="record",
        assertion="Approved effectiveness review exists.",
        epistemic_state=EpistemicState.VERIFIED,
        provenance=[SourcePointer(source_id="SRC-1", page=1)],
        confidence=0.95,
        observed_at=datetime.now(timezone.utc),
    )
    assert item.evidence_id == "EV-1"


def test_confidence_range_enforced():
    with pytest.raises(ValidationError):
        EvidenceItem(
            evidence_id="EV-2",
            organization_id="ORG-1",
            evidence_type="record",
            assertion="x",
            epistemic_state=EpistemicState.PRESENTED,
            provenance=[],
            confidence=1.5,
        )
