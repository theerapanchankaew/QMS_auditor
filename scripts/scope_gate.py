#!/usr/bin/env python3
"""Scope gate for QMS skill.

Detects whether a user request is within the ISO 9001 / QMS audit scope
before any audit resources are consumed.

Usage:
  python scripts/scope_gate.py --text "help me with ISO 27001"
  python scripts/scope_gate.py --text "clause 4.1 context of the organization"
"""
from __future__ import annotations

import argparse
import json
import sys
import re

# ---------------------------------------------------------------------------
# Scope signal tables
# ---------------------------------------------------------------------------

IN_SCOPE_SIGNALS = [
    r"\biso\s*9001\b",
    r"\biso\s*9000\b",
    r"\bqms\b",
    r"\bquality management\b",
    r"\bclause\s+[4-9]\b",
    r"\bcorrective action\b",
    r"\bnonconformit",
    r"\baudit plan\b",
    r"\baudit checklist\b",
    r"\baudit report\b",
    r"\bcertification\b",
    r"\bmanagement review\b",
    r"\broot cause\b",
    r"\bcaar\b",
    r"\bahp\b",
    r"\bconformity\b",
    r"\bsurveillance audit\b",
    r"\bstage 1\b",
    r"\bstage 2\b",
    r"\brecertification\b",
    r"\bexternal provider\b",
    r"\bsupplier evaluation\b",
    r"\bplanning of change\b",
    r"\brisk and opportunit",
    r"\bquality culture\b",
    r"\bquality objectiv",
    r"\bdocumented information\b",
    r"\bmonitoring and measurement\b",
    r"\bคุณภาพ\b",
    r"\bการตรวจ\b",
    r"\bข้อกำหนด\b",
    r"\bผู้ส่งมอบ\b",
    r"\bข้อบกพร่อง\b",
    r"\bสอดคล้อง\b",
]

OUT_OF_SCOPE_SIGNALS = {
    "WRONG_STANDARD": [
        r"\biso\s*27001\b",
        r"\biso\s*27017\b",
        r"\biso\s*27018\b",
        r"\biso\s*45001\b",
        r"\biso\s*14001\b",
        r"\biso\s*56001\b",
        r"\biso\s*13485\b",
        r"\biatf\s*16949\b",
        r"\bgmp\b(?!.*iso\s*9001)",
        r"\bfda\b(?!.*iso\s*9001)",
        r"\bce\s+marking\b(?!.*iso\s*9001)",
        r"\bpdpa\b",
        r"\bgdpr\b",
        r"\bสอบ\s*ก\.ม\.ช\.",
    ],
    "PERSONAL_ADVICE": [
        r"\bstock\b|\bหุ้น\b",
        r"\binvest\b|\bลงทุน\b",
        r"\blaw firm\b|\bทนายความ\b",
        r"\bmedical advice\b|\bคำแนะนำทางการแพทย์\b",
        r"\bวิเคราะห์หุ้น\b",
    ],
    "CB_DECISION": [
        r"\bgrant\s+certification\b",
        r"\bissue\s+certificate\b",
        r"\bdecide\s+(on\s+)?certification\b",
        r"\bออกใบรับรอง\b",
        r"\bตัดสิน.*certification\b",
    ],
}

AMBIGUOUS_SIGNALS = [
    r"\bquality system\b",
    r"\bระบบคุณภาพ\b",
    r"\boutsourcing\b(?!.*clause)",
    r"\bsupplier\b(?!.*9001)",
    r"\binternal audit\b(?!.*9001)",
    r"\bตรวจสอบภายใน\b(?!.*9001)",
]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _match_any(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def evaluate_scope(text: str) -> dict:
    text_lower = text.lower()

    # Check explicit out-of-scope
    for category, patterns in OUT_OF_SCOPE_SIGNALS.items():
        if _match_any(text_lower, patterns):
            # Still in scope if ISO 9001 is also referenced (comparison question)
            if _match_any(text_lower, IN_SCOPE_SIGNALS):
                return {
                    "status": "in_scope",
                    "reason": "Cross-standard comparison referencing ISO 9001 — proceed with ISO 9001 framing",
                    "dialog_required": False,
                }
            return {
                "status": "out_of_scope",
                "category": category,
                "reason_th": _oos_reason_th(category),
                "suggestion_th": _oos_suggestion_th(category),
                "verdict": "OUT_OF_SCOPE",
                "dialog_required": True,
            }

    # Check in-scope signals
    if _match_any(text_lower, IN_SCOPE_SIGNALS):
        return {
            "status": "in_scope",
            "dialog_required": False,
        }

    # Check ambiguous
    if _match_any(text_lower, AMBIGUOUS_SIGNALS):
        return {
            "status": "ambiguous",
            "dialog_required": True,
            "question_th": (
                "ขอให้ระบุมาตรฐานที่ใช้เป็น audit criterion ก่อนครับ "
                "— งานนี้อยู่ภายใต้ ISO 9001 หรือมาตรฐานอื่น?"
            ),
        }

    # Very short / greeting / unclear — default to in_scope with note
    if len(text.split()) <= 4:
        return {
            "status": "in_scope",
            "note": "Short request — proceeding; scope gate will re-evaluate if audit substance emerges",
            "dialog_required": False,
        }

    return {
        "status": "ambiguous",
        "dialog_required": True,
        "question_th": (
            "ขอให้ระบุมาตรฐานและงานที่ต้องการให้ชัดเจนก่อนครับ "
            "— skill นี้รองรับ ISO 9001 / QMS audit เท่านั้น"
        ),
    }


def _oos_reason_th(category: str) -> str:
    reasons = {
        "WRONG_STANDARD": "คำขอนี้อ้างถึงมาตรฐานที่อยู่นอกขอบเขตของ skill นี้ (รองรับเฉพาะ ISO 9001 / QMS)",
        "PERSONAL_ADVICE": "คำขอนี้เป็นการขอคำแนะนำส่วนบุคคลด้านกฎหมาย การเงิน หรือการแพทย์ ซึ่งอยู่นอก scope",
        "CB_DECISION": "การตัดสินใจออกใบรับรองเป็นอำนาจของ CB ที่ได้รับการ accredit เท่านั้น skill นี้รองรับการให้เหตุผลและการเตรียมการตรวจ",
    }
    return reasons.get(category, "คำขอนี้อยู่นอกขอบเขตของ skill นี้")


def _oos_suggestion_th(category: str) -> str:
    suggestions = {
        "WRONG_STANDARD": "กรุณาใช้ skill ที่รองรับมาตรฐานดังกล่าวโดยตรง หรืออัปโหลดเอกสารอ้างอิงอย่างเป็นทางการเข้ามาเพื่อเปรียบเทียบกับ ISO 9001",
        "PERSONAL_ADVICE": "กรุณาปรึกษาผู้เชี่ยวชาญที่เกี่ยวข้องโดยตรง",
        "CB_DECISION": "ติดต่อ CB ที่ได้รับการ accredit โดยตรงสำหรับการตัดสินใจด้านการรับรอง",
    }
    return suggestions.get(category, "กรุณาระบุงานที่เกี่ยวข้องกับ ISO 9001 / QMS")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="QMS skill scope gate")
    parser.add_argument("--text", required=True, help="User request text to evaluate")
    args = parser.parse_args(argv[1:])

    result = evaluate_scope(args.text)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["status"] == "out_of_scope":
        return 3
    if result["status"] == "ambiguous":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
