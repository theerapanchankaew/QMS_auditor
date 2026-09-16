from __future__ import annotations

import hashlib
from .models import DocumentChunk, SourceSpan


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SpanChunker:
    """Deterministic chunker preserving source-span lineage."""
    def __init__(self, max_chars: int = 1800, overlap_spans: int = 1):
        self.max_chars = max_chars
        self.overlap_spans = overlap_spans

    def chunk(self, source_id: str, spans: list[SourceSpan]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        i = 0
        ordinal = 0
        while i < len(spans):
            selected: list[SourceSpan] = []
            total = 0
            j = i
            while j < len(spans):
                add = len(spans[j].text) + (2 if selected else 0)
                if selected and total + add > self.max_chars:
                    break
                selected.append(spans[j]); total += add; j += 1
            if not selected:
                selected = [spans[i]]; j = i + 1
            text = "\n\n".join(s.text for s in selected)
            chunks.append(DocumentChunk(
                chunk_id=f"{source_id}:CH{ordinal:05d}", source_id=source_id,
                span_ids=[s.span_id for s in selected], text=text,
                chunk_hash=_hash(text), ordinal=ordinal,
                token_estimate=max(1, len(text)//4),
            ))
            ordinal += 1
            if j >= len(spans): break
            i = max(i + 1, j - self.overlap_spans)
        return chunks
