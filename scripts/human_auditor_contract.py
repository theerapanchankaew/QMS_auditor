#!/usr/bin/env python3
"""Human-auditor dialog and output contract for the closed-source QMS skill.

This module is intentionally local-only. It does not retrieve content. It returns
an enforced response contract that callers can include in every material output.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

DIALOG_MODE = "human_auditor_logic"
SOURCE_BOUNDARY = "bundled_qms_skill_sources_and_uploaded_controlled_evidence_only"
ALLOWED_VERDICTS = [
    "Informational",
    "Complied",
    "Noncomplied",
    "OFI",
    "OBS",
    "InsufficientEvidence",
    "ReferenceGap",
    "ReviewRequired",
]
REQUIRED_RESPONSE_SECTIONS = [
    "Human Auditor Frame",
    "Audit Objective",
    "Controlled Sources Used",
    "Source-Based Finding",
    "Thai Meaning / Auditor Explanation",
    "Impact on Certification System",
    "Evidence Gaps / Next Audit Question",
    "Verdict",
]


def build_contract(*, objective: str = "", route: str = "general", status: str = "allowed_controlled_source_only") -> dict[str, Any]:
    return {
        "dialog_mode": DIALOG_MODE,
        "source_boundary": SOURCE_BOUNDARY,
        "external_sources_used": False,
        "connectors_used": False,
        "web_used": False,
        "route": route,
        "status": status,
        "audit_objective": objective,
        "required_response_sections": REQUIRED_RESPONSE_SECTIONS,
        "allowed_verdicts": ALLOWED_VERDICTS,
        "human_auditor_rules": [
            "Use controlled sources before judgement.",
            "Separate source facts, auditee claims, objective evidence, auditor judgement, and evidence gaps.",
            "Ask no more than three focused evidence questions when more evidence is needed.",
            "Return ReferenceGap, InsufficientEvidence, or ReviewRequired rather than guessing.",
            "Never classify Major NC from score or wording alone; require objective evidence of breach, extent, impact, and systemic nature.",
        ],
        "opening_stance_th": (
            "ผมจะใช้เฉพาะ bundled QMS skill sources และหลักฐานที่ผู้ใช้อัปโหลดเป็น controlled evidence เท่านั้น "
            "จะไม่ใช้เว็บ connector หรือแหล่งข้อมูลภายนอก และจะแยกข้อเท็จจริงจากแหล่งอ้างอิง หลักฐานเชิงประจักษ์ "
            "ดุลยพินิจผู้ตรวจประเมิน และช่องว่างของหลักฐานก่อนให้ข้อสรุป"
        ),
        "blocked_or_gap_dialog_th": (
            "หากไม่พบข้อมูลใน bundled references/assets หรือหลักฐานที่อัปโหลด ผมจะคืนค่า ReferenceGap หรือ InsufficientEvidence "
            "และขอให้ผู้ใช้อัปโหลดเอกสารทางการ/มาตรฐาน/คู่มือ/หลักฐานที่ต้องการใช้เป็น controlled source ก่อน"
        ),
    }


def render_markdown_skeleton(contract: dict[str, Any]) -> str:
    objective = contract.get("audit_objective") or "[ระบุวัตถุประสงค์การตรวจ/การตีความ]"
    return f"""## Human Auditor Frame
- Mode: {contract['dialog_mode']}
- Source boundary: bundled QMS skill sources and uploaded controlled evidence only
- External sources: not used

## Audit Objective
{objective}

## Controlled Sources Used
- [ระบุ path/page/line ของ reference, asset, หรือ uploaded controlled evidence]

## Source-Based Finding
[ข้อเท็จจริงจาก controlled source โดยไม่อ้างเกินหลักฐาน]

## Thai Meaning / Auditor Explanation
[คำอธิบายภาษาไทยตามกรอบผู้ตรวจประเมิน]

## Impact on Certification System
[ผลกระทบต่อระบบรับรอง/กระบวนการตรวจ/ความเป็นกลาง/ข้อร้องเรียน/บันทึก/ความเสี่ยง]

## Evidence Gaps / Next Audit Question
[หลักฐานที่ยังขาด หรือคำถาม focused ไม่เกิน 3 ข้อ]

## Verdict
[Informational / Complied / Noncomplied / OFI / OBS / InsufficientEvidence / ReferenceGap / ReviewRequired]
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objective", default="")
    parser.add_argument("--route", default="general")
    parser.add_argument("--status", default="allowed_controlled_source_only")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args(argv[1:])
    contract = build_contract(objective=args.objective, route=args.route, status=args.status)
    if args.markdown:
        print(render_markdown_skeleton(contract))
    else:
        print(json.dumps(contract, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
