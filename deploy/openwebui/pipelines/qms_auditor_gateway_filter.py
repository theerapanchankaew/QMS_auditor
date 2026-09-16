"""
title: QMS Auditor ISO 9001:2026 Gateway
author: qms-auditor-iso-9001-2026
version: 0.1.0
description: >
  OpenWebUI Pipelines FILTER that enforces the QMS Auditor ISO 9001:2026
  deterministic gates (scope gate, closed-source preflight guard, and the
  harness gate executor) around an Ollama model, instead of relying on the
  LLM to remember and self-apply SKILL.md's governance rules from a prompt.

  inlet()  runs BEFORE the model call:
    - scope_gate.py           -> blocks/asks for clarification on out-of-scope
                                  or ambiguous requests (wrong standard,
                                  personal advice, CB certification decisions)
    - preflight_request_guard.py -> blocks requests/actions that would push the
                                  model toward web search / external connectors
    - injects a condensed governance header (system_prompt.md) so the model
      knows the route taxonomy, verdict taxonomy, and output-format contract

  outlet() runs AFTER the model call:
    - if the model's reply contains a `gate_execution_trace` JSON block (the
      structured verdict format SKILL.md BLOCK 3 rule 23 requires), it is
      validated with harness_gate_executor.py. A gate rejection is surfaced
      to the user as a visible warning banner instead of being silently
      accepted, mirroring SKILL.md rule 24 ("harness enforces gates; on
      rejection, retry with corrected values — never override the harness").

  This filter does NOT replace Ollama for text generation — it wraps it.
  Attach it to a model in OpenWebUI Admin > Settings > Pipelines.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        # Which OpenWebUI model IDs this filter attaches to ("*" = all)
        pipelines: List[str] = ["*"]
        priority: int = 0

        # Path to the qms-auditor-iso-9001-2026 skill root INSIDE the
        # pipelines container (see docker-compose.yml volume mount).
        SKILL_ROOT: str = "/app/qms-skill"
        PYTHON_BIN: str = "python3"

        # Behavior toggles
        BLOCK_ON_OUT_OF_SCOPE: bool = True
        BLOCK_ON_AMBIGUOUS: bool = True
        BLOCK_ON_GUARDRAIL: bool = True
        INJECT_GOVERNANCE_HEADER: bool = True
        VALIDATE_GATE_TRACE_ON_OUTLET: bool = True
        GATE_SUBPROCESS_TIMEOUT_SECONDS: int = 15

    def __init__(self) -> None:
        self.type = "filter"
        self.name = "QMS Auditor ISO 9001:2026 Gateway"
        self.valves = self.Valves(
            **{
                "SKILL_ROOT": os.getenv("QMS_SKILL_ROOT", "/app/qms-skill"),
                "PYTHON_BIN": os.getenv("QMS_PYTHON_BIN", "python3"),
            }
        )
        self._governance_header: Optional[str] = None

    async def on_startup(self) -> None:
        self._governance_header = self._load_governance_header()

    async def on_shutdown(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Gate subprocess helpers
    # ------------------------------------------------------------------

    def _run_script(self, script_name: str, args: List[str]) -> tuple[int, dict]:
        script_path = Path(self.valves.SKILL_ROOT) / "scripts" / script_name
        cmd = [self.valves.PYTHON_BIN, str(script_path), *args]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.valves.GATE_SUBPROCESS_TIMEOUT_SECONDS,
                cwd=self.valves.SKILL_ROOT,
            )
        except subprocess.TimeoutExpired:
            return 124, {"status": "gate_timeout", "script": script_name}
        except FileNotFoundError as exc:
            return 127, {"status": "gate_missing", "script": script_name, "error": str(exc)}

        stdout = (proc.stdout or "").strip()
        try:
            payload = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            payload = {
                "status": "gate_output_unparseable",
                "script": script_name,
                "raw_stdout": stdout[-2000:],
                "raw_stderr": (proc.stderr or "")[-2000:],
            }
        return proc.returncode, payload

    def _load_governance_header(self) -> str:
        header_path = Path(__file__).with_name("system_prompt.md")
        if header_path.exists():
            return header_path.read_text(encoding="utf-8")
        return (
            "You are the QMS Auditor ISO 9001:2026 assistant. Answer only "
            "from bundled skill sources and user-provided evidence. Never "
            "browse the web. Answer in Thai unless asked otherwise."
        )

    # ------------------------------------------------------------------
    # inlet: run BEFORE the LLM call
    # ------------------------------------------------------------------

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages") or []
        if not messages:
            return body

        last_user_text = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_text = str(msg.get("content") or "")
                break
        if not last_user_text.strip():
            return body

        # 1) Scope gate
        _, scope = self._run_script("scope_gate.py", ["--text", last_user_text])
        status = scope.get("status")
        if status == "out_of_scope" and self.valves.BLOCK_ON_OUT_OF_SCOPE:
            raise Exception(
                scope.get("reason_th", "คำขอนี้อยู่นอกขอบเขตของ skill นี้")
                + "\n\n"
                + scope.get("suggestion_th", "")
            )
        if status == "ambiguous" and self.valves.BLOCK_ON_AMBIGUOUS:
            raise Exception(scope.get("question_th", "กรุณาระบุขอบเขตของงานให้ชัดเจนก่อน"))

        # 2) Closed-source / no-external-search preflight guard
        _, preflight = self._run_script("preflight_request_guard.py", ["--text", last_user_text])
        if preflight.get("status") == "blocked_pending_user_dialog" and self.valves.BLOCK_ON_GUARDRAIL:
            raise Exception(preflight.get("message_th") or json.dumps(preflight, ensure_ascii=False))

        # 3) Inject condensed governance header as a system message
        if self.valves.INJECT_GOVERNANCE_HEADER and self._governance_header:
            body["messages"] = [
                {"role": "system", "content": self._governance_header},
                *messages,
            ]

        return body

    # ------------------------------------------------------------------
    # outlet: run AFTER the LLM call
    # ------------------------------------------------------------------

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if not self.valves.VALIDATE_GATE_TRACE_ON_OUTLET:
            return body

        messages = body.get("messages") or []
        if not messages:
            return body

        last_assistant_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                last_assistant_idx = i
                break
        if last_assistant_idx is None:
            return body

        content = str(messages[last_assistant_idx].get("content") or "")
        trace_obj = self._extract_gate_trace(content)
        if trace_obj is None:
            return body

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(trace_obj, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            _, result = self._run_script("harness_gate_executor.py", ["--input", tmp_path])
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        if result.get("gate_validation") == "FAIL":
            banner = (
                "\n\n---\n"
                "**⚠️ Deterministic harness rejected this verdict "
                f"({result.get('gate_failed', 'unknown gate')} — "
                f"{result.get('rejection_reason', 'unknown reason')}).**\n\n"
                f"{result.get('rejection_message', '')}\n\n"
                "Per SKILL.md rule 24, do not treat the verdict above as final; "
                "retry with corrected gate values or escalate to human auditor "
                "review — never override the harness.\n"
            )
            messages[last_assistant_idx]["content"] = content + banner
            body["messages"] = messages

        return body

    @staticmethod
    def _extract_gate_trace(text: str) -> Optional[dict]:
        if "gate_execution_trace" not in text:
            return None

        # Prefer a fenced ```json ... ``` block if present.
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        candidates = fenced or [text]

        for candidate in candidates:
            start = candidate.find("{")
            if start == -1:
                continue
            depth = 0
            for i in range(start, len(candidate)):
                if candidate[i] == "{":
                    depth += 1
                elif candidate[i] == "}":
                    depth -= 1
                    if depth == 0:
                        chunk = candidate[start : i + 1]
                        try:
                            obj = json.loads(chunk)
                        except json.JSONDecodeError:
                            break
                        if "gate_execution_trace" in obj:
                            return obj
                        break
        return None
