#!/usr/bin/env python3
"""Validate controlled QMS source manifests.

Fail-closed rules:
- source locations must be inside the skill root unless explicitly provided as
  current-task uploaded controlled evidence by a calling workflow;
- web URLs, connector paths, and network indexes are forbidden;
- local RAG profiles must disable network and web fallback;
- every source needs a stable source_id and controlled_location.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "drive://", "sharepoint://", "slack://")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _inside_skill(rel: str) -> Path:
    if rel.lower().startswith(FORBIDDEN_PREFIXES):
        raise ValueError(f"forbidden external location: {rel}")
    p = (SKILL_ROOT / rel).resolve()
    if not str(p).startswith(str(SKILL_ROOT.resolve())):
        raise ValueError(f"location escapes skill root: {rel}")
    return p


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    data = _load_json(manifest_path)
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()

    if data.get("allow_web_fallback") is not False:
        errors.append("manifest.allow_web_fallback must be false")
    if data.get("allow_external_connectors") is not False:
        errors.append("manifest.allow_external_connectors must be false")

    for i, src in enumerate(data.get("sources", [])):
        sid = src.get("source_id")
        loc = src.get("controlled_location")
        if not sid:
            errors.append(f"sources[{i}] missing source_id")
            continue
        if sid in seen:
            errors.append(f"duplicate source_id: {sid}")
        seen.add(sid)
        if not loc:
            errors.append(f"{sid}: missing controlled_location")
            continue
        try:
            p = _inside_skill(loc)
        except ValueError as exc:
            errors.append(f"{sid}: {exc}")
            continue
        if not p.exists():
            errors.append(f"{sid}: controlled_location does not exist: {loc}")
            continue
        expected = src.get("checksum_sha256")
        if expected and p.is_file():
            actual = _sha256(p)
            if actual != expected:
                errors.append(f"{sid}: checksum mismatch for {loc}")
        if src.get("external_access_allowed") is not False:
            errors.append(f"{sid}: external_access_allowed must be false")
        if src.get("requires_human_auditor_contract") is not True:
            warnings.append(f"{sid}: requires_human_auditor_contract is not true")

    return {
        "validator": "source_manifest_validator",
        "manifest": str(manifest_path.relative_to(SKILL_ROOT)) if str(manifest_path).startswith(str(SKILL_ROOT)) else str(manifest_path),
        "status": "valid" if not errors else "invalid",
        "errors": errors,
        "warnings": warnings,
        "source_count": len(data.get("sources", [])),
        "source_boundary": data.get("source_boundary", "controlled_sources_only"),
    }


def validate_local_rag_policy(policy_path: Path, manifest_path: Path) -> dict[str, Any]:
    data = _load_json(policy_path)
    manifest = _load_json(manifest_path)
    allowed_source_ids = {s.get("source_id") for s in manifest.get("sources", [])}
    errors: list[str] = []
    if data.get("network_allowed") is not False:
        errors.append("network_allowed must be false")
    if data.get("web_fallback_allowed") is not False:
        errors.append("web_fallback_allowed must be false")
    if data.get("external_connector_allowed") is not False:
        errors.append("external_connector_allowed must be false")
    for profile in data.get("approved_profiles", []):
        pid = profile.get("rag_profile_id", "<missing>")
        if profile.get("status") != "approved":
            errors.append(f"{pid}: profile status must be approved")
        if profile.get("allow_network") is not False:
            errors.append(f"{pid}: allow_network must be false")
        if profile.get("allow_web_fallback") is not False:
            errors.append(f"{pid}: allow_web_fallback must be false")
        index_path = profile.get("index_path")
        if index_path:
            try:
                _inside_skill(index_path)
            except ValueError as exc:
                errors.append(f"{pid}: {exc}")
        for sid in profile.get("allowed_source_ids", []):
            if sid not in allowed_source_ids:
                errors.append(f"{pid}: unknown allowed_source_id {sid}")
    return {"validator":"local_rag_policy_validator","status":"valid" if not errors else "invalid","errors":errors,"profile_count":len(data.get("approved_profiles", []))}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="assets/manifests/bundled-source-manifest.json")
    parser.add_argument("--rag-policy", default="assets/manifests/local-rag-connection-policy.json")
    args = parser.parse_args(argv[1:])
    manifest_path = _inside_skill(args.manifest)
    policy_path = _inside_skill(args.rag_policy)
    manifest_result = validate_manifest(manifest_path)
    policy_result = validate_local_rag_policy(policy_path, manifest_path) if policy_path.exists() else {"status":"missing","errors":["local rag policy missing"]}
    result = {"status":"valid" if manifest_result["status"] == "valid" and policy_result["status"] == "valid" else "invalid", "manifest": manifest_result, "local_rag_policy": policy_result}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
