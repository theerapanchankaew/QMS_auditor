#!/usr/bin/env python3
"""Deterministic retrieval helpers for QMS clause evidence packs.

This module intentionally avoids heavyweight dependencies so it can run in a
local Ollama/Qwen stack. It performs exact clause lookup first, then controlled
expansion using related clause metadata. Optional vector search can be added by
calling your embedding database before or after the deterministic gates here.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

CLAUSE_RE = re.compile(r"\b(?:clause|ข้อ|ข้อกำหนด)?\s*([A]?(?:\d{1,2})(?:\.\d{1,2}){0,3})\b", re.IGNORECASE)


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_clause(text: str) -> Optional[str]:
    """Detect a clause id such as 4.1, 6.1.2, A.4.1 from a user query."""
    matches = CLAUSE_RE.findall(text or "")
    if not matches:
        return None
    # Prefer the most specific clause detected first.
    matches = sorted(matches, key=lambda x: (x.startswith("A"), x.count(".")), reverse=True)
    return matches[0].upper()


def normalize_clause(clause_id: str) -> str:
    return clause_id.strip().upper().replace(" ", "")


def is_parent_or_child(requested: str, retrieved: str) -> bool:
    requested = normalize_clause(requested)
    retrieved = normalize_clause(retrieved)
    return retrieved == requested or retrieved.startswith(requested + ".") or requested.startswith(retrieved + ".")


def simple_yaml_map(path: str | Path) -> Dict[str, Dict[str, List[str]]]:
    """Parse the simple related_clause_map.yaml format without PyYAML.

    Supports this limited structure:
    4.1:
      primary: ["4.1"]
      related_requirements: ["6.1"]
    """
    data: Dict[str, Dict[str, List[str]]] = {}
    current: Optional[str] = None
    line_re = re.compile(r"^\s{2}([A-Za-z_]+):\s*\[(.*)\]\s*$")
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].rstrip()
            if not line:
                continue
            if not line.startswith(" ") and line.endswith(":"):
                current = line[:-1].strip().strip('"')
                data[current] = {}
                continue
            if current:
                m = line_re.match(line)
                if m:
                    key, vals = m.groups()
                    items = [v.strip().strip('"').strip("'") for v in vals.split(",") if v.strip()]
                    data[current][key] = items
    return data


def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9\.]+|[ก-๙]+", (text or "").lower())


@dataclass
class BM25Doc:
    doc_id: str
    text: str
    metadata: Dict[str, Any]


class BM25Lite:
    def __init__(self, docs: Iterable[BM25Doc], k1: float = 1.5, b: float = 0.75):
        self.docs = list(docs)
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(d.text) for d in self.docs]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avg_len = sum(self.doc_len) / max(len(self.doc_len), 1)
        self.df = defaultdict(int)
        for toks in self.doc_tokens:
            for term in set(toks):
                self.df[term] += 1
        self.N = len(self.docs)

    def score(self, query: str, idx: int) -> float:
        q_terms = tokenize(query)
        if not q_terms:
            return 0.0
        tf = Counter(self.doc_tokens[idx])
        score = 0.0
        dl = self.doc_len[idx] or 1
        for term in q_terms:
            if term not in tf:
                continue
            df = self.df.get(term, 0)
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            freq = tf[term]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / max(self.avg_len, 1))
            score += idf * (freq * (self.k1 + 1)) / denom
        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[BM25Doc, float]]:
        scored = [(self.docs[i], self.score(query, i)) for i in range(len(self.docs))]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(d, s) for d, s in scored[:top_k] if s > 0]


def make_metadata_docs(index: Dict[str, Any]) -> List[BM25Doc]:
    docs = []
    for clause_id, meta in index.get("clauses", {}).items():
        text = " ".join([
            clause_id,
            meta.get("title", ""),
            meta.get("section_type", ""),
            " ".join(meta.get("related_clauses", []) or []),
            " ".join(meta.get("related_annex", []) or []),
        ])
        docs.append(BM25Doc(doc_id=clause_id, text=text, metadata=meta))
    return docs


def exact_clause(index: Dict[str, Any], clause_id: str) -> Optional[Dict[str, Any]]:
    clause_id = normalize_clause(clause_id)
    meta = index.get("clauses", {}).get(clause_id)
    if not meta:
        return None
    return {"clause_id": clause_id, **meta}


def build_evidence_pack(
    index: Dict[str, Any],
    related_map: Dict[str, Dict[str, List[str]]],
    requested_clause: str,
    query: str = "",
    include_related: bool = True,
    include_informative: bool = True,
) -> Dict[str, Any]:
    requested_clause = normalize_clause(requested_clause)
    primary_meta = exact_clause(index, requested_clause)
    if not primary_meta:
        return {
            "status": "stop",
            "decision": "stop",
            "reason": f"Exact requested clause not found: {requested_clause}",
            "requested_clause": requested_clause,
            "primary_evidence": [],
            "related_evidence": [],
            "informative_evidence": [],
        }

    if primary_meta.get("section_type") != "requirement":
        return {
            "status": "stop",
            "decision": "stop",
            "reason": f"Requested clause is not a requirement clause: {requested_clause}",
            "requested_clause": requested_clause,
            "primary_evidence": [primary_meta],
            "related_evidence": [],
            "informative_evidence": [],
        }

    rule = related_map.get(requested_clause, {})
    primary_ids = rule.get("primary", [requested_clause])
    related_ids = rule.get("related_requirements", []) if include_related else []
    informative_ids = rule.get("informative", []) if include_informative else []

    def collect(ids: List[str], expected_type: Optional[str] = None) -> List[Dict[str, Any]]:
        out = []
        for cid in ids:
            item = exact_clause(index, cid)
            if not item:
                continue
            if expected_type and item.get("section_type") != expected_type:
                continue
            out.append(item)
        return out

    primary = collect(primary_ids, expected_type="requirement")
    if not primary:
        primary = [primary_meta]

    related = collect(related_ids, expected_type="requirement")
    informative = collect(informative_ids, expected_type="informative")

    # Optional metadata BM25 expansion. Only add matching clauses already allowed by map.
    if query:
        bm25 = BM25Lite(make_metadata_docs(index))
        bm25_hits = bm25.search(query, top_k=10)
        allowed_related = set(related_ids)
        existing_related = {x["clause_id"] for x in related}
        for doc, score in bm25_hits:
            cid = doc.doc_id
            if cid in allowed_related and cid not in existing_related:
                item = exact_clause(index, cid)
                if item and item.get("section_type") == "requirement":
                    item["bm25_score"] = round(score, 4)
                    related.append(item)
                    existing_related.add(cid)

    return {
        "status": "ok",
        "decision": "proceed",
        "requested_clause": requested_clause,
        "query": query,
        "primary_evidence": primary,
        "related_evidence": related,
        "informative_evidence": informative,
        "validation": {
            "primary_evidence_available": bool(primary),
            "annex_used_as_primary": False,
            "clause_matched": all(is_parent_or_child(requested_clause, p["clause_id"]) for p in primary),
        },
    }


def validate_pack(pack: Dict[str, Any]) -> Dict[str, Any]:
    if pack.get("status") != "ok":
        return {"valid": False, "action": "stop", "reason": pack.get("reason", "pack status is not ok")}
    primary = pack.get("primary_evidence", [])
    if not primary:
        return {"valid": False, "action": "stop", "reason": "Primary evidence is missing."}
    requested = pack.get("requested_clause")
    for item in primary:
        if item.get("section_type") != "requirement":
            return {"valid": False, "action": "stop", "reason": "Non-requirement evidence used as primary."}
        if requested and not is_parent_or_child(requested, item.get("clause_id", "")):
            return {"valid": False, "action": "stop", "reason": "Requested clause and primary evidence do not match."}
    return {"valid": True, "action": "proceed", "reason": "Evidence pack passed validation."}
