#!/usr/bin/env python3
"""Upskill module registry for QMS skill.

Manages the lifecycle of knowledge modules: registration, validation,
activation, retirement, and F1-driven priority queue.

Usage:
  python scripts/upskill_module_registry.py --list
  python scripts/upskill_module_registry.py --validate clause_guide_8_4_v1
  python scripts/upskill_module_registry.py --activate clause_guide_8_4_v1
  python scripts/upskill_module_registry.py --priority-queue
  python scripts/upskill_module_registry.py --register --id my_module_v1 \
    --type clause_guide_module --files "references/modules/my-guide.md" \
    --triggers "clause 8.4,supplier"
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = SKILL_ROOT / "assets" / "manifests" / "upskill-module-registry.json"
F1_STATS_PATH = SKILL_ROOT / "assets" / "stats" / "f1_stats.json"

# Files that no module may override
IMMUTABLE_FILES = {
    "references/governance/closed-source-policy.md",
    "references/governance/auditor-code-of-conduct.md",
    "references/governance/evidence-integrity-rules.md",
    "references/governance/refusal-and-escalation-rules.md",
    "references/governance/controlled-output-rules.md",
    "references/12-ethics-cov-escalation-rules.md",
    "references/17-knowledge-boundary-enforcement.md",
}

# External-reference indicators that fail validation
EXTERNAL_INDICATORS = ("http://", "https://", "www.", "ftp://", ".com/", ".org/")


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"modules": [], "schema_version": "1.0"}
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def find_module(registry: dict, module_id: str) -> dict | None:
    for m in registry.get("modules", []):
        if m.get("module_id") == module_id:
            return m
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_module(module: dict) -> dict:
    errors = []
    warnings = []

    # Required fields
    for field in ("module_id", "type", "version", "files"):
        if not module.get(field):
            errors.append(f"Missing required field: {field}")

    # Files must be within skill bundle
    for fp in module.get("files", []):
        full_path = SKILL_ROOT / fp
        if not full_path.exists():
            warnings.append(f"File not found (may be created later): {fp}")
        # Check no external references
        for indicator in EXTERNAL_INDICATORS:
            if indicator in fp:
                errors.append(f"External reference in file path: {fp}")
        # Check no immutable file override
        if fp in IMMUTABLE_FILES:
            errors.append(f"File is immutable and cannot be overridden by a module: {fp}")

    # Check file contents for external references (if files exist)
    for fp in module.get("files", []):
        full_path = SKILL_ROOT / fp
        if full_path.exists() and full_path.is_file():
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            for indicator in EXTERNAL_INDICATORS:
                if indicator in content:
                    warnings.append(f"External indicator '{indicator}' found in {fp} — review required")

    status = "valid" if not errors else "invalid"
    return {
        "module_id": module.get("module_id"),
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# F1-driven priority queue
# ---------------------------------------------------------------------------

def load_f1_stats() -> dict:
    if not F1_STATS_PATH.exists():
        return {}
    with F1_STATS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_priority_queue() -> list[dict]:
    """Return upskill priorities sorted by F1 gap (1 - f1)."""
    stats = load_f1_stats()
    queue = []

    by_route = stats.get("by_route", {})
    by_clause = stats.get("by_clause_group", {})

    for route, data in by_route.items():
        f1 = data.get("f1")
        status = data.get("f1_status", "insufficient_data")
        n = data.get("n", 0)
        if status in ("low", "unreliable", "moderate"):
            gap = round(1 - f1, 4) if f1 is not None else 0.5
            queue.append({
                "dimension": f"route:{route}",
                "f1": f1,
                "f1_status": status,
                "n": n,
                "priority_score": gap,
                "suggestion": f"Consider adding dialog_module or clause_guide_module for route '{route}'",
            })
        elif status == "insufficient_data" and n > 0:
            queue.append({
                "dimension": f"route:{route}",
                "f1": None,
                "f1_status": status,
                "n": n,
                "priority_score": 0.3,
                "suggestion": f"Collect more feedback for route '{route}' (current n={n})",
            })

    for cg, data in by_clause.items():
        f1 = data.get("f1")
        status = data.get("f1_status", "insufficient_data")
        n = data.get("n", 0)
        if status in ("low", "unreliable"):
            gap = round(1 - f1, 4) if f1 is not None else 0.5
            queue.append({
                "dimension": f"clause_group:{cg}",
                "f1": f1,
                "f1_status": status,
                "n": n,
                "priority_score": gap,
                "suggestion": f"Consider adding clause_guide_module for clause group {cg}",
            })

    queue.sort(key=lambda x: x["priority_score"], reverse=True)
    return queue


# ---------------------------------------------------------------------------
# CLI actions
# ---------------------------------------------------------------------------

def cmd_list(registry: dict) -> int:
    modules = registry.get("modules", [])
    if not modules:
        print(json.dumps({"status": "empty", "message": "No modules registered yet."}, ensure_ascii=False, indent=2))
        return 0
    summary = [
        {
            "module_id": m.get("module_id"),
            "type": m.get("type"),
            "version": m.get("version"),
            "status": m.get("status"),
            "added_date": m.get("added_date"),
        }
        for m in modules
    ]
    print(json.dumps({"modules": summary, "count": len(summary)}, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(registry: dict, module_id: str) -> int:
    module = find_module(registry, module_id)
    if not module:
        print(json.dumps({"error": f"Module '{module_id}' not found in registry"}, ensure_ascii=False))
        return 2
    result = validate_module(module)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


def cmd_activate(registry: dict, module_id: str) -> int:
    module = find_module(registry, module_id)
    if not module:
        print(json.dumps({"error": f"Module '{module_id}' not found"}, ensure_ascii=False))
        return 2
    validation = validate_module(module)
    if validation["status"] != "valid":
        print(json.dumps({"error": "Validation failed — cannot activate", "validation": validation},
                         ensure_ascii=False, indent=2))
        return 1
    module["status"] = "active"
    module["activated_date"] = datetime.now(timezone.utc).isoformat()
    save_registry(registry)
    print(json.dumps({"status": "activated", "module_id": module_id}, ensure_ascii=False, indent=2))
    return 0


def cmd_register(registry: dict, module_id: str, module_type: str,
                 files: list[str], triggers: list[str], notes: str) -> int:
    if find_module(registry, module_id):
        print(json.dumps({"error": f"Module '{module_id}' already exists. Use a new ID or retire the old one."},
                         ensure_ascii=False))
        return 2
    module = {
        "module_id": module_id,
        "type": module_type,
        "version": "1.0.0",
        "status": "pending",
        "added_date": datetime.now(timezone.utc).date().isoformat(),
        "files": files,
        "triggers": triggers,
        "f1_priority_score": 0.0,
        "replaces": None,
        "notes": notes,
    }
    validation = validate_module(module)
    registry.setdefault("modules", []).append(module)
    save_registry(registry)
    print(json.dumps({
        "status": "registered_pending",
        "module_id": module_id,
        "validation": validation,
        "next_step": f"Run: python scripts/upskill_module_registry.py --activate {module_id}",
    }, ensure_ascii=False, indent=2))
    return 0 if validation["status"] == "valid" else 1


def cmd_priority_queue() -> int:
    queue = build_priority_queue()
    if not queue:
        print(json.dumps({
            "status": "no_priorities",
            "message": "No F1 data available yet or all routes performing well. Collect more feedback.",
        }, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({"priority_upskill_queue": queue}, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="QMS upskill module registry")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--validate", metavar="MODULE_ID")
    parser.add_argument("--activate", metavar="MODULE_ID")
    parser.add_argument("--priority-queue", action="store_true", dest="priority_queue")
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--id", default="", dest="module_id")
    parser.add_argument("--type", default="clause_guide_module", dest="module_type")
    parser.add_argument("--files", default="", help="Comma-separated file paths")
    parser.add_argument("--triggers", default="", help="Comma-separated trigger keywords")
    parser.add_argument("--notes", default="")
    args = parser.parse_args(argv[1:])

    registry = load_registry()

    if args.list:
        return cmd_list(registry)
    if args.validate:
        return cmd_validate(registry, args.validate)
    if args.activate:
        return cmd_activate(registry, args.activate)
    if args.priority_queue:
        return cmd_priority_queue()
    if args.register:
        if not args.module_id:
            print(json.dumps({"error": "--id is required for --register"}, ensure_ascii=False))
            return 2
        files = [f.strip() for f in args.files.split(",") if f.strip()]
        triggers = [t.strip() for t in args.triggers.split(",") if t.strip()]
        return cmd_register(registry, args.module_id, args.module_type, files, triggers, args.notes)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
