#!/usr/bin/env python3
"""
requirement_profile_loader.py -- loads possible_worlds_dimensions out of
assets/requirement_profiles/<clause>.json for a given list of
requirement_ids, filtered down to each requirement's OWN dimensions (not
its whole clause's), and shaped exactly as
scripts/awm_runtime.reason(dimensions_by_requirement=...) expects.

Why this lives outside scripts/awm_runtime: that package is packaged and
installed independently (see scripts/awm_runtime/pyproject.toml) and does
not read assets/requirement_profiles/ itself -- see
AuditCognitionPipeline.run()'s docstring. This script is the caller-side
glue that closes that gap; the package only accepts the dict, it never
fetches it.

Why per-requirement filtering, not the whole clause: each clause's JSON
file carries possible_worlds_dimensions for ALL its elements combined
(e.g. 6.1.3 has three: AR-6.1.3-E01_observation, E02_observation,
E03_observation). But a RequirementAssessment/AuditHypothesis in this
runtime is scoped to exactly ONE requirement_id (one element). Attaching
the whole clause's dimension set to every one of its elements' hypotheses
would inflate H(Xt) to reflect the entire clause's uncertainty for a
question about only one element of it -- so this loader keeps only the
dimensions whose key starts with "<requirement_id>_", matching how
scripts/awm_runtime/aias_awm/cognition/planner.py derives its target
dimension name (f"{requirement_id}_{evidence_type}").

Usage:
  python scripts/requirement_profile_loader.py --requirement-ids AR-6.1.3-E02 AR-6.1.3-E01
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = REPO_ROOT / "assets" / "requirement_profiles"


def _clause_of(requirement_id: str) -> str:
    """'AR-6.1.3-E02' -> '6.1.3'. Requirement IDs never contain a '-' inside
    the clause number itself, so splitting off the last '-Exx' segment and
    stripping the 'AR-' prefix is exact, not a heuristic guess."""
    prefix, _, _suffix = requirement_id.rpartition("-")
    if not prefix.startswith("AR-"):
        raise ValueError(f"not a recognized requirement_id shape: {requirement_id!r}")
    return prefix[len("AR-"):]


def load_possible_worlds_dimensions(
    requirement_ids: list[str],
    profiles_dir: Path = PROFILES_DIR,
) -> dict[str, dict[str, list[str]]]:
    """Returns {requirement_id: {dimension_name: [values]}} for every
    requirement_id whose clause file exists and whose own dimensions are
    non-empty. Requirement IDs with no match are silently omitted (not an
    error) -- the caller (cognition/hypothesis_engine.py) already treats a
    missing entry the same as "no dimensions for this one", per its own
    dict.get() default-None lookup."""
    clause_cache: dict[str, dict] = {}
    out: dict[str, dict[str, list[str]]] = {}
    for req_id in requirement_ids:
        clause = _clause_of(req_id)
        if clause not in clause_cache:
            path = profiles_dir / f"{clause}.json"
            if not path.exists():
                clause_cache[clause] = {}
                continue
            clause_cache[clause] = json.loads(path.read_text(encoding="utf-8")).get("possible_worlds_dimensions", {})
        clause_dims = clause_cache[clause]
        own = {k: v for k, v in clause_dims.items() if k.startswith(f"{req_id}_")}
        if own:
            out[req_id] = own
    return out


def load_requirement_records(
    requirement_ids: list[str],
    profiles_dir: Path = PROFILES_DIR,
) -> list[dict]:
    """The corpus records (dicts in the AtomicRequirement schema, including
    `qualifier`) for the given requirement_ids, ready for
    AtomicRequirement(**record) / AuditWorldRuntime.register_requirement().
    Raises KeyError for an unknown id: registering a requirement must not be
    silently skipped (its qualifier drives the L7 gate in aias_awm)."""
    cache: dict[str, dict] = {}
    out: list[dict] = []
    for req_id in requirement_ids:
        clause = _clause_of(req_id)
        if clause not in cache:
            path = profiles_dir / f"{clause}.json"
            if not path.exists():
                raise KeyError(f"no profile file for clause {clause!r} (requirement {req_id})")
            cache[clause] = {r["requirement_id"]: r for r in json.loads(path.read_text(encoding="utf-8"))["requirements"]}
        if req_id not in cache[clause]:
            raise KeyError(f"unknown requirement_id {req_id!r} in {clause}.json")
        out.append(dict(cache[clause][req_id]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--requirement-ids", nargs="+", required=True)
    ap.add_argument("--profiles-dir", default=str(PROFILES_DIR))
    ap.add_argument("--output", help="where to write the result JSON (default: stdout)")
    args = ap.parse_args()

    result = load_possible_worlds_dimensions(args.requirement_ids, Path(args.profiles_dir))
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
