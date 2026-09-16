#!/usr/bin/env python3
"""Code-level guardrails for controlled-source QMS audit scripts.

This module fails closed. It is designed so every executable path can detect
attempts to use web search, public internet sources, external connectors, or
out-of-bound files before the task continues.

Important distinction:
- web/network/connector access is always blocked and must return a dialog payload;
  approval does not silently bypass it.
- local files outside the skill bundle may be opened only when a calling script
  receives explicit per-run approval and is designed to handle user evidence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]

# Keys that usually mean the model or caller is trying to leave controlled sources.
EXTERNAL_SOURCE_KEYS = {
    "external_source", "external_sources", "external_access", "external_search",
    "web_search", "web", "internet", "browser", "browse", "url", "urls",
    "connector", "connectors", "google_drive", "slack", "github", "sharepoint",
    "dropbox", "box", "file_search", "api_tool", "open_web", "search_web",
    "online", "website", "webpage", "search_query", "search_engine",
}

# Hard indicators: these are never silently allowed for QMS audit substance.
HARD_EXTERNAL_RE = re.compile(
    r"(https?://|www\.|\bweb\b|\binternet\b|\bbrowse\b|\bbrowser\b|\bonline\b|"
    r"\bwebsite\b|\bwebpage\b|\bsearch(?:ing)?\s+(?:the\s+)?web\b|\bweb\s+search\b|"
    r"\bgoogle\s+search\b|\bgoogle\s+drive\b|\bslack\b|\bgithub\b|\bsharepoint\b|"
    r"\bdropbox\b|\bbox\b|\bfile_search\b|\bapi_tool\b|\bconnector\b|"
    r"\biso\.org\b|\biaf\b|\bcertification\s+body\s+website\b)",
    re.IGNORECASE,
)

# Soft/current-info indicators that often cause the assistant to browse unless blocked.
CURRENT_INFO_RE = re.compile(
    r"(latest|current|update|updates|updated|recent|newest|publication\s+status|"
    r"transition\s+(?:period|rule|deadline|timeline)|official\s+(?:site|website|source)|"
    r"ตรวจสอบล่าสุด|ข้อมูลล่าสุด|อัปเดต|อัพเดต|ค้นเว็บ|ค้นหาเว็บ|เว็บไซต์|ออนไลน์|สถานะประกาศ|กำหนดเปลี่ยนผ่าน)",
    re.IGNORECASE,
)

ISO_9001_2026_RE = re.compile(r"iso\s*9001\s*:?\s*2026|9001\s*:?\s*2026|iso/fdis\s*9001", re.IGNORECASE)


class GuardrailDialogRequired(RuntimeError):
    """Raised when an external-boundary confirmation dialog is required."""

    def __init__(self, blocked_action: str, detected: list[str] | None = None, *, hard_block: bool = True):
        self.blocked_action = blocked_action
        self.detected = detected or []
        self.hard_block = hard_block
        super().__init__(blocked_action)

    def payload(self) -> dict[str, Any]:
        return {
            "guardrail": "controlled_source_boundary",
            "status": "blocked_pending_user_dialog",
            "dialog_required": True,
            "hard_block": self.hard_block,
            "blocked_action": self.blocked_action,
            "detected_external_indicators": self.detected,
            "message_th": (
                "พบความพยายามที่จะออกนอก controlled source boundary ของ QMS skill "
                "จึงต้องหยุดก่อนทุกครั้งและถามผู้ใช้ก่อน ห้ามเริ่มค้นเว็บ ใช้ connector "
                "หรืออ้างอิงข้อมูลภายนอกโดยอัตโนมัติ\n\n"
                "คำถามสำหรับผู้ใช้: ตรวจพบ action ที่จะออกนอกขอบเขต เช่น web/connector/external definition. "
                "ยืนยันให้หยุด action นี้และวิเคราะห์เฉพาะ controlled source ภายใน skill หรือเอกสารที่อัปโหลดเท่านั้นหรือไม่? "
                "ถ้าข้อมูลไม่อยู่ใน skill กรุณาอัปโหลดเอกสารทางการ/หลักฐานล่าสุดเข้ามาเป็น controlled source ก่อน"
            ),
            "message_en": (
                "An attempt to leave the QMS skill controlled-source boundary was detected. "
                "Stop before every such attempt. Do not start web search, connectors, or external-source use automatically. "
                "Ask the user to confirm stopping that action and continuing only with bundled/user-uploaded controlled sources. If the source is missing, request an uploaded official document/evidence instead."
            ),
            "required_dialog": {
                "ask_every_time": True,
                "do_not_reuse_prior_consent": True,
                "external_sources_remain_forbidden": True,
                "allowed_safe_next_step": "search bundled references/assets or request user-uploaded official/current document as a controlled source",
            },
            "human_auditor_contract": {
                "dialog_mode": "human_auditor_logic",
                "source_boundary": "bundled_qms_skill_sources_and_uploaded_controlled_evidence_only",
                "external_sources_used": False,
                "required_response_sections": [
                    "Human Auditor Frame",
                    "Controlled Source Boundary Dialog",
                    "Blocked Action",
                    "Safe Next Step",
                    "Verdict"
                ],
                "verdict": "ReferenceGap_or_blocked_pending_user_dialog"
            },
            "auditor_instruction": (
                "Do not continue, search, browse, use external connectors, or rely on external/current-status knowledge. "
                "For QMS audit substance, proceed only with bundled skill sources and user-provided controlled evidence. "
                "Respond in human auditor logic mode: explain the boundary, identify the blocked action, and ask for uploaded controlled evidence if the bundled sources are insufficient."
            ),
        }


def print_guardrail_and_exit(exc: GuardrailDialogRequired) -> int:
    print(json.dumps(exc.payload(), ensure_ascii=False, indent=2))
    return 3


def approval_present(payload: dict[str, Any] | None) -> bool:
    """Return true only for local out-of-bound file approvals, not web/network approvals."""
    if not isinstance(payload, dict):
        return False
    approval = payload.get("external_access_approval") or payload.get("external_source_approval")
    if not isinstance(approval, dict):
        return False
    return bool(approval.get("allowed") is True and str(approval.get("approval_text") or "").strip())


def detect_external_text(text: str, *, context: str = "text") -> list[str]:
    """Detect external/web/current-info intent in free text."""
    if not isinstance(text, str) or not text.strip():
        return []
    detected: list[str] = []
    if HARD_EXTERNAL_RE.search(text):
        detected.append(f"{context}: hard external/web indicator")
    if CURRENT_INFO_RE.search(text):
        detected.append(f"{context}: current/latest/update indicator")
    if ISO_9001_2026_RE.search(text) and CURRENT_INFO_RE.search(text):
        detected.append(f"{context}: ISO 9001:2026 update/current-status request")
    return detected


def assert_no_external_intent_text(text: str, *, context: str = "user request") -> None:
    detected = detect_external_text(text, context=context)
    if detected:
        raise GuardrailDialogRequired(f"External/current-source intent found in {context}", detected, hard_block=True)


def assert_no_external_payload(payload: Any, *, approval: dict[str, Any] | None = None, context: str = "input payload") -> None:
    """Fail if a JSON-like payload requests or references external sources.

    Web/network/connector/current-status indicators are hard-blocked even when an
    approval object is present. Approval may only be used by path checks for local
    user-provided evidence when the calling script explicitly supports that flow.
    """
    detected: list[str] = []

    def walk(obj: Any, path: str = "$") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = str(k).strip().lower()
                if key in EXTERNAL_SOURCE_KEYS or any(token in key for token in ["external", "web", "internet", "connector", "url", "online", "website"]):
                    if key not in {"external_access_approval", "external_source_approval"}:
                        detected.append(f"{path}.{k}: external key")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            for item in detect_external_text(obj, context=path):
                detected.append(item)

    walk(payload)
    if detected:
        raise GuardrailDialogRequired(f"External-source or current-info indicator found in {context}", detected[:30], hard_block=True)


def assert_path_inside_skill(path: str | Path, *, purpose: str, approval: dict[str, Any] | None = None) -> Path:
    """Allow only files inside the skill bundle unless explicit local-file approval is supplied."""
    candidate = Path(path).expanduser().resolve()
    try:
        candidate.relative_to(SKILL_ROOT)
        return candidate
    except ValueError:
        if approval_present(approval):
            return candidate
        raise GuardrailDialogRequired(
            f"Attempted to access path outside skill-controlled bundle for {purpose}",
            [str(candidate)],
            hard_block=False,
        )
