#!/usr/bin/env python3
"""Single mandatory closed-source entrypoint for QMS skill tasks.

The purpose of this entrypoint is to prevent the assistant from bypassing code
checks and free-form searching. It validates the user request and any planned
action, then either blocks with a dialog payload or resolves the query only from
bundled local sources.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from pathlib import Path

from controlled_source_guardrail import (
    GuardrailDialogRequired,
    assert_no_external_intent_text,
    print_guardrail_and_exit,
)
from local_source_resolver import search_local_sources
from human_auditor_contract import build_contract
from source_manifest_validator import validate_manifest, validate_local_rag_policy


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, help="User request")
    parser.add_argument("--planned-action", default="", help="Assistant's next planned action, if any")
    parser.add_argument("--resolve", action="store_true", help="Also search only bundled local sources")
    parser.add_argument("--mode", choices=["bundled_only", "approved_local_rag", "uploaded_controlled_evidence"], default="bundled_only", help="Controlled retrieval mode")
    parser.add_argument("--rag-profile-id", default="bundled-qms-local-index", help="Approved local RAG profile ID")
    parser.add_argument("--validate-sources", action="store_true", help="Validate source manifest and local RAG policy before continuing")
    args = parser.parse_args(argv[1:])

    try:
        assert_no_external_intent_text(args.request, context="user request")
        if args.planned_action:
            assert_no_external_intent_text(args.planned_action, context="planned assistant action")
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)

    if args.validate_sources:
        skill_root = Path(__file__).resolve().parents[1]
        manifest_result = validate_manifest(skill_root / "assets/manifests/bundled-source-manifest.json")
        policy_result = validate_local_rag_policy(skill_root / "assets/manifests/local-rag-connection-policy.json", skill_root / "assets/manifests/bundled-source-manifest.json")
        validation = {"source_manifest": manifest_result, "local_rag_policy": policy_result}
        if manifest_result.get("status") != "valid" or policy_result.get("status") != "valid":
            print(json.dumps({"status": "ReviewRequired", "reason": "controlled_source_validation_failed", "validation": validation, "human_auditor_contract": build_contract(objective=args.request, route="source_validation", status="ReviewRequired")}, ensure_ascii=False, indent=2))
            return 5

    if args.resolve:
        try:
            if args.mode == "approved_local_rag":
                from local_rag_adapter import query_local_rag
                result = query_local_rag(args.request, profile_id=args.rag_profile_id)
            else:
                result: dict[str, Any] = search_local_sources(args.request)
        except GuardrailDialogRequired as exc:
            return print_guardrail_and_exit(exc)
        result["human_auditor_contract"] = build_contract(
            objective=args.request,
            route="approved_local_rag" if args.mode == "approved_local_rag" else "local_source_resolution",
            status=result.get("status", "resolved")
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "found_in_controlled_sources" else 4

    print(json.dumps({
        "guardrail": "closed_source_entrypoint",
        "status": "allowed_controlled_source_only",
        "dialog_required": False,
        "retrieval_mode": args.mode,
        "instruction_th": "ดำเนินการได้เฉพาะกับ references/assets/scripts ภายใน skill, approved local RAG ที่อยู่ใน manifest, และหลักฐานที่ผู้ใช้อัปโหลดเท่านั้น ห้ามค้นเว็บหรือใช้ connector และต้องตอบในกรอบ human auditor logic",
        "instruction_en": "Proceed only with bundled references/assets/scripts, manifest-approved local RAG, and user-uploaded controlled evidence. Do not search web or use connectors. Use the human auditor logic response frame.",
        "human_auditor_contract": build_contract(objective=args.request, route="preflight")
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
