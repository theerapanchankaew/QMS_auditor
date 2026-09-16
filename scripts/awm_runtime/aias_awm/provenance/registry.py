from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from aias_awm.perception.models import SourceDocument, SourceSpan


@dataclass(frozen=True)
class SourceValidation:
    ok: bool
    reason: str


class ControlledSourceRegistry:
    def __init__(self):
        self._docs: dict[str, SourceDocument] = {}
        self._spans: dict[str, SourceSpan] = {}

    def register(self, document: SourceDocument, spans: list[SourceSpan]) -> None:
        if document.source_id in self._docs and self._docs[document.source_id].sha256 != document.sha256:
            raise ValueError("source_id collision with different content hash")
        self._docs[document.source_id] = document
        for span in spans:
            if span.source_id != document.source_id:
                raise ValueError("span/source mismatch")
            self._spans[span.span_id] = span

    def get_document(self, source_id: str) -> SourceDocument | None:
        return self._docs.get(source_id)

    def get_span(self, span_id: str) -> SourceSpan | None:
        return self._spans.get(span_id)

    def validate_span(self, span_id: str) -> SourceValidation:
        span = self._spans.get(span_id)
        if span is None: return SourceValidation(False, "SPAN_NOT_REGISTERED")
        doc = self._docs.get(span.source_id)
        if doc is None: return SourceValidation(False, "SOURCE_NOT_REGISTERED")
        if not doc.controlled: return SourceValidation(False, "SOURCE_NOT_CONTROLLED")
        actual = hashlib.sha256(span.text.encode("utf-8")).hexdigest()
        if actual != span.span_hash: return SourceValidation(False, "SPAN_HASH_MISMATCH")
        return SourceValidation(True, "OK")

    def manifest_hash(self) -> str:
        rows = [{"source_id": d.source_id, "sha256": d.sha256, "version": d.version,
                 "controlled": d.controlled} for d in sorted(self._docs.values(), key=lambda x: x.source_id)]
        return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
