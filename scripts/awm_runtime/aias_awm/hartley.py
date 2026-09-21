"""Minimal, self-contained port of scripts/hartley_uncertainty.py's core
math, for use inside the aias-audit-world-model package.

Why a port instead of an import: scripts/awm_runtime is packaged and
installed independently (its own pyproject.toml, own pinned dependencies --
see ../pyproject.toml) and nothing else in this package imports a
top-level scripts/*.py file; every existing cross-boundary reference in
this package is a doc-comment pointer, never a live import (see
control/world_fsm.py, control/world_gates.py, cognition/evidence_reconciliation.py).
Reaching outside the package for a plain script would break that
self-containment. This file must stay in sync with
scripts/hartley_uncertainty.py's enumerate_worlds()/hartley_measure()/
filter_worlds()/information_gain_from_resolving_dimension() -- the
regression suites for both (scripts/hartley_uncertainty_tests.py and
assets/tests/awm_v07/test_planning_v07.py) reproduce the same textbook
numbers so a drift between them would show up as a test failure, not
silently.

Lives at the top of the package (not inside planning/ or cognition/)
deliberately: cognition/planner.py needs to import this, and
planning/__init__.py imports policy.py which imports cognition/planner.py
-- putting this file inside the planning subpackage would make importing
it also execute planning/__init__.py, recreating the exact
cognition<->planning circular import this file exists to avoid.
"""
from __future__ import annotations

import math
from itertools import product


def _enumerate_worlds(dimensions: dict[str, list[str]]) -> list[dict[str, str]]:
    names = list(dimensions.keys())
    value_lists = [dimensions[n] for n in names]
    return [dict(zip(names, combo)) for combo in product(*value_lists)]


def _filter_worlds(worlds: list[dict[str, str]], known_facts: dict[str, str]) -> list[dict[str, str]]:
    if not known_facts:
        return list(worlds)
    return [w for w in worlds if all(w.get(k) == v for k, v in known_facts.items() if k in w)]


def information_gain_from_resolving_dimension(
    dimensions: dict[str, list[str]],
    known_facts: dict[str, str],
    target_dimension: str,
) -> dict:
    """Exact IG = log2(k) for fully resolving one dimension with k
    still-undetermined values, under Hartley's independent-dimension
    Cartesian-product structure. See
    scripts/hartley_uncertainty.py::information_gain_from_resolving_dimension
    for the full derivation and references/68-hartley-uncertainty.md for
    provenance. Returns status "OK" | "UNKNOWN_DIMENSION" |
    "ALREADY_RESOLVED" | "INCONSISTENT" -- only "OK" carries a nonzero gain.
    """
    if not dimensions:
        return {"status": "UNKNOWN_DIMENSION", "information_gain_bits": 0.0, "normalized_information_gain": 0.0}

    raw_worlds = _enumerate_worlds(dimensions)
    current_worlds = _filter_worlds(raw_worlds, known_facts or {})
    if not current_worlds:
        return {"status": "INCONSISTENT", "information_gain_bits": 0.0, "normalized_information_gain": 0.0}
    h_current = math.log2(len(current_worlds))

    if target_dimension not in dimensions:
        return {"status": "UNKNOWN_DIMENSION", "information_gain_bits": 0.0, "normalized_information_gain": 0.0}

    surviving_values = sorted(set(w[target_dimension] for w in current_worlds))
    k = len(surviving_values)
    if k <= 1:
        return {"status": "ALREADY_RESOLVED", "information_gain_bits": 0.0, "normalized_information_gain": 0.0, "h_current_bits": round(h_current, 6)}

    ig = math.log2(k)
    return {
        "status": "OK",
        "h_current_bits": round(h_current, 6),
        "information_gain_bits": round(ig, 6),
        "normalized_information_gain": round(min(1.0, ig / h_current), 6) if h_current > 0 else 0.0,
    }
