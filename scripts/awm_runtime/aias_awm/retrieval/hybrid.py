from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import math
import re

from aias_awm.perception.models import DocumentChunk


@dataclass(frozen=True)
class RetrievalHit:
    chunk_id: str
    source_id: str
    score: float
    lexical_score: float
    semantic_score: float
    graph_bonus: float
    metadata_bonus: float
    text: str
    span_ids: tuple[str, ...]


class HybridRetriever:
    """Small deterministic hybrid retriever.

    Semantic channel uses TF-IDF cosine if scikit-learn is available. Graph/metadata
    constraints are explicit inputs so retrieval remains inspectable.
    """
    def __init__(self, chunks: Iterable[DocumentChunk]):
        self.chunks = list(chunks)
        self._vectors = None
        self._vectorizer = None
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
            self._vectors = self._vectorizer.fit_transform([c.text for c in self.chunks]) if self.chunks else None
        except Exception:
            pass

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[\w\.\-]+", text.lower(), flags=re.UNICODE))

    def search(self, query: str, *, top_k: int = 5,
               allowed_source_ids: set[str] | None = None,
               requirement_ids: set[str] | None = None,
               metadata_filters: dict[str, str] | None = None) -> list[RetrievalHit]:
        qtok = self._tokens(query)
        semantic = [0.0] * len(self.chunks)
        if self._vectorizer is not None and self._vectors is not None:
            qv = self._vectorizer.transform([query])
            sims = (self._vectors @ qv.T).toarray().ravel()
            semantic = [float(x) for x in sims]
        hits: list[RetrievalHit] = []
        for i, chunk in enumerate(self.chunks):
            if allowed_source_ids is not None and chunk.source_id not in allowed_source_ids:
                continue
            ctok = self._tokens(chunk.text)
            lexical = len(qtok & ctok) / max(1, len(qtok))
            reqs = set(chunk.metadata.get("requirement_ids", []))
            graph_bonus = 0.15 if requirement_ids and reqs & requirement_ids else 0.0
            metadata_bonus = 0.0
            if metadata_filters:
                matched = sum(str(chunk.metadata.get(k, "")) == str(v) for k, v in metadata_filters.items())
                metadata_bonus = 0.05 * matched
            score = 0.45 * lexical + 0.40 * semantic[i] + graph_bonus + metadata_bonus
            if score > 0:
                hits.append(RetrievalHit(
                    chunk_id=chunk.chunk_id, source_id=chunk.source_id, score=score,
                    lexical_score=lexical, semantic_score=semantic[i], graph_bonus=graph_bonus,
                    metadata_bonus=metadata_bonus, text=chunk.text, span_ids=tuple(chunk.span_ids)
                ))
        return sorted(hits, key=lambda h: (-h.score, h.chunk_id))[:top_k]
