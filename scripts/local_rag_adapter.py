#!/usr/bin/env python3
"""Approved local RAG adapter for the closed QMS skill.

This is not a web connector. It reads only local index files declared in
`assets/manifests/local-rag-connection-policy.json`. If the profile or index is
not approved, it fails closed. If the local index is absent, it can optionally
fall back to bundled local source resolution, not web.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from controlled_source_guardrail import GuardrailDialogRequired, assert_no_external_intent_text, print_guardrail_and_exit
from human_auditor_contract import build_contract
from local_source_resolver import search_local_sources

SKILL_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = SKILL_ROOT / "assets/manifests/local-rag-connection-policy.json"
MANIFEST_PATH = SKILL_ROOT / "assets/manifests/bundled-source-manifest.json"


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _inside_skill(rel: str) -> Path:
    p = (SKILL_ROOT / rel).resolve()
    if not str(p).startswith(str(SKILL_ROOT.resolve())):
        raise ValueError("local rag path escapes skill root")
    return p


STOPWORDS = {"definition", "define", "meaning", "term", "terms", "คือ", "นิยาม", "คำจำกัดความ", "ความหมาย"}

def _tokens(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9_:/.-]*|[\u0E00-\u0E7F]+", text or "") if len(t) > 1 and t.lower() not in STOPWORDS}


def _get_profile(profile_id: str) -> dict[str, Any] | None:
    policy = _load(POLICY_PATH)
    if policy.get("network_allowed") is not False or policy.get("web_fallback_allowed") is not False:
        return None
    for p in policy.get("approved_profiles", []):
        if p.get("rag_profile_id") == profile_id and p.get("status") == "approved":
            if p.get("allow_network") is False and p.get("allow_web_fallback") is False:
                return p
    return None


def query_local_rag(query: str, *, profile_id: str = "bundled-qms-local-index", max_results: int = 8) -> dict[str, Any]:
    assert_no_external_intent_text(query, context="approved local rag query")
    profile = _get_profile(profile_id)
    if not profile:
        return {"status":"ReviewRequired", "reason":"rag_profile_not_approved", "profile_id":profile_id, "human_auditor_contract": build_contract(objective=query, route="approved_local_rag", status="ReviewRequired")}
    index_path = _inside_skill(profile["index_path"])
    qtokens = _tokens(query)
    results: list[dict[str, Any]] = []
    if index_path.exists():
        with index_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if row.get("source_id") not in profile.get("allowed_source_ids", []):
                    continue
                text = row.get("text", "")
                overlap = qtokens & _tokens(text)
                required_overlap = 1 if len(qtokens) <= 2 else max(2, min(3, len(qtokens)))
                if query.lower() in text.lower() or len(overlap) >= required_overlap:
                    item = dict(row)
                    loc = item.get("controlled_location", "")
                    bonus = 0
                    if "references/standard/" in loc:
                        bonus += 8
                    if "assets/standards/" in loc:
                        bonus += 6
                    if "definition-index" in loc or "vocabulary" in loc.lower():
                        bonus += 5
                    if "guardrail" in loc.lower() or "knowledge-boundary" in loc.lower():
                        bonus -= 4
                    item["score"] = len(overlap) + (10 if query.lower() in text.lower() else 0) + bonus
                    item["retrieval_mode"] = "approved_local_rag"
                    results.append(item)
        results.sort(key=lambda r: -r.get("score", 0))
        results = results[:max_results]
    if not results:
        # Controlled fallback: bundled source resolver only, never web.
        fallback = search_local_sources(query, max_results=max_results)
        fallback["retrieval_mode"] = "bundled_only_fallback_from_approved_local_rag"
        fallback["rag_profile_id"] = profile_id
        return fallback
    return {
        "guardrail":"approved_local_rag_adapter",
        "status":"found_in_controlled_sources",
        "retrieval_mode":"approved_local_rag",
        "rag_profile_id":profile_id,
        "allow_web_fallback":False,
        "external_sources_used":False,
        "human_auditor_contract": build_contract(objective=query, route="approved_local_rag", status="found_in_controlled_sources"),
        "results": results,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", required=True)
    p.add_argument("--profile-id", default="bundled-qms-local-index")
    p.add_argument("--max-results", type=int, default=8)
    args = p.parse_args(argv[1:])
    try:
        result = query_local_rag(args.query, profile_id=args.profile_id, max_results=args.max_results)
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "found_in_controlled_sources" else 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
