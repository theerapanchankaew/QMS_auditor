#!/usr/bin/env python3
"""Preflight guard for QMS controlled-source skill runs.

Run this before any retrieval, clause extraction, AHP evaluation, or audit answer.
It blocks user requests that would push the skill toward web search/current updates
or external connectors, and prints a dialog payload for the assistant to show.

Usage:
  python scripts/preflight_request_guard.py --text "Searching the web for ISO 9001:2026 updates"
  echo '{"user_request":"latest ISO 9001:2026 updates"}' | python scripts/preflight_request_guard.py --json-stdin
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from controlled_source_guardrail import (
    GuardrailDialogRequired,
    assert_no_external_intent_text,
    assert_no_external_payload,
    print_guardrail_and_exit,
)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="", help="Raw user request or planned assistant action to check")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON payload from stdin and scan it")
    args = parser.parse_args(argv[1:])

    try:
        if args.json_stdin:
            data: Any = json.load(sys.stdin)
            assert_no_external_payload(data, context="preflight JSON payload")
        else:
            assert_no_external_intent_text(args.text, context="preflight request/action")
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)

    print(json.dumps({
        "guardrail": "controlled_source_boundary",
        "status": "allowed_controlled_source_only",
        "dialog_required": False,
        "instruction": "Proceed only with bundled skill sources and user-provided controlled evidence. Do not use web search or external connectors."
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
