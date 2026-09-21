#!/usr/bin/env python3
"""
hartley_uncertainty.py — deterministic Hartley-measure / expected-information-
gain calculator over an explicitly enumerated finite possible-worlds set.

Source: AIAS_Theory_Technology_Stack_Textbook_v1.0.pdf (MASCI internal
technical reference, Ch.9 "Possible Worlds and Hartley Measure", Ch.10
"Expected Information Gain and Planning Utility", Ch.20 worked use case for
clause 6.1.3). This module was written because a repo-wide search for
`hartley`, `log2`, `entropy`, `cardinality`, `possible_worlds`, `bits` found
zero hits before this file existed — the textbook's own worked numbers for
clause 6.1.3 (|X|=8 -> H=3 bits; IG(REQUEST_RECORD)=2 bits) could not be
reproduced by anything in this repo. See references/68-hartley-uncertainty.md
for the full provenance and gap writeup, and docs/eei-blueprint-crosswalk.md
("Update 2026-09-21") for why this is a new, additive file rather than a
change to an existing one.

Formulas (Textbook Appendix A):
  Xt      = finite set of materially distinguishable feasible states at time t
  H(X)    = log2|X|                                   (Hartley measure, bits)
  IG(a)   = H(Xt) - E[H(Xt+1) | a]                     (expected information gain)
  a*      = argmax U(a), a in A_permitted              (NOT computed here — see
            scripts/awm_runtime/aias_awm/planning/scoring.py for the existing
            utility scorer; this module only supplies one candidate input to
            that decision, it does not rank or authorize actions itself)

WHAT THIS DOES NOT DO:
  - It does not compute a verdict, severity, or breach determination. H=0
    means the enumerated uncertainty has collapsed to one state — it does
    NOT mean "conforming" (Textbook Ch.9 Step 8: "H=0 does NOT mean
    conforming").
  - It does not replace `expected_information_gain` as used today in
    scripts/awm_runtime/aias_awm/planning/scoring.py, cognition/planner.py,
    or scripts/next_best_audit_action.py — those remain unchanged, bounded
    [0,1] heuristics. Wiring this module's bit-valued output into those
    scorers is a deliberate follow-up decision, not done here, because it
    would require per-clause possible-worlds dimensions to be authored for
    all 65 clauses first (only the clause 6.1.3 worked example exists today
    — see hartley_uncertainty_tests.py).
  - It does not resolve *which* facts are known — that is still evidence
    work done by the LLM extraction layer and, where the reading is
    genuinely ambiguous, scripts/world_constraint_validator.py. This module
    only quantifies uncertainty MAGNITUDE (a bit count) over a dimension set
    someone else has already enumerated; world_constraint_validator.py
    instead CLASSIFIES whether a set of candidate evidence-tags is safe to
    proceed on. Different questions, same "world" vocabulary — do not
    conflate the two, and do not let one import the other's decision.

Forbidden signal (same house rule as world_constraint_validator.py): a
`known_facts` value must be a hard, already-confirmed fact (e.g. objective
evidence obtained), never a probability/confidence/likelihood estimate about
what MIGHT be true. `action_outcomes` probabilities are a different,
permitted use of probability: the planner's own admissible forecast of what
an action might reveal (e.g. "70% chance a requested record comes back
ABSENT"), used only to rank un-taken candidate actions — never to resolve an
ambiguous evidence reading already in hand.

Usage:
  python scripts/hartley_uncertainty.py --input case.json --mode measure
  python scripts/hartley_uncertainty.py --input case.json --mode gain
"""
import argparse
import json
import math
import sys
from itertools import product


def enumerate_worlds(dimensions: dict) -> list:
    """Cartesian product of named dimensions -> list of world dicts.

    dimensions: {"implementation": ["YES", "NO"], ...} — every dimension must
    map to a non-empty list of distinct values. This is Xt's raw definition
    before any known fact narrows it.
    """
    if not dimensions:
        raise ValueError("dimensions must be a non-empty mapping of name -> list of possible values")
    names = list(dimensions.keys())
    value_lists = []
    for name in names:
        values = dimensions[name]
        if not isinstance(values, list) or not values:
            raise ValueError(f"dimension {name!r} must map to a non-empty list of possible values")
        if len(set(values)) != len(values):
            raise ValueError(f"dimension {name!r} has duplicate values: {values}")
        value_lists.append(values)
    return [dict(zip(names, combo)) for combo in product(*value_lists)]


def hartley_measure(world_count: int) -> float:
    """H(X) = log2|X|. |X|=0 is undefined -- an empty set is an inconsistent
    world, not a zero-uncertainty one; callers must not conflate the two."""
    if world_count < 0:
        raise ValueError("world_count cannot be negative")
    if world_count == 0:
        raise ValueError("H(X) is undefined for an empty (inconsistent) world set -- this is not the same as H=0")
    return math.log2(world_count)


def filter_worlds(worlds: list, known_facts: dict) -> list:
    """Eliminate worlds inconsistent with confirmed facts (objective evidence).

    A known_facts key that does not appear on a world's dimensions is ignored
    for that world (schema mismatch is the caller's responsibility, not this
    function's -- it never silently invents a dimension)."""
    if not known_facts:
        return list(worlds)
    return [w for w in worlds if all(w.get(k) == v for k, v in known_facts.items() if k in w)]


def resolve_uncertainty(dimensions: dict, known_facts: dict = None) -> dict:
    """Full single-state pipeline: build Xt, apply known facts, report H(Xt)."""
    raw_worlds = enumerate_worlds(dimensions)
    surviving = filter_worlds(raw_worlds, known_facts or {})
    result = {
        "note": (
            "Deterministic combinatorial measure only (log2 of a finite, "
            "materially distinguishable state count) -- no LLM call, no "
            "learned weight, no probability estimation. Hartley measure is "
            "valid only when states are finite, canonicalizable, and treated "
            "as equipossible for planning purposes (Textbook Ch.9)."
        ),
        "dimensions": dimensions,
        "raw_world_count": len(raw_worlds),
        "known_facts": known_facts or {},
        "surviving_world_count": len(surviving),
        "surviving_worlds": surviving,
    }
    if len(surviving) == 0:
        result["status"] = "INCONSISTENT"
        result["hartley_bits"] = None
        result["reason"] = "known_facts eliminate every enumerated world -- check for a typo or an out-of-domain value; this is not zero uncertainty"
    else:
        result["status"] = "RESOLVED" if len(surviving) == 1 else "MATERIAL_UNCERTAINTY"
        result["hartley_bits"] = round(hartley_measure(len(surviving)), 6)
        if len(surviving) == 1:
            result["reason"] = "H=0: uncertainty within this dimension set has collapsed to one state. This does NOT mean conforming -- it means one material state remains; severity/verdict is a separate, unrelated determination (Textbook Ch.9 Step 8)."
    return result


def expected_information_gain(dimensions: dict, known_facts: dict, action_outcomes: list) -> dict:
    """IG(a) = H(Xt) - E[H(Xt+1) | a].

    action_outcomes: list of {"outcome_id": str, "probability": float,
    "known_facts": dict} -- the planner's own admissible forecast of what an
    action might reveal. Probabilities must sum to 1.0. This ranks a
    CANDIDATE, un-taken action; it authorizes nothing and proves nothing by
    itself (Textbook Ch.10: "Utility != conformity probability; IG != model
    confidence; low entropy != conforming").
    """
    raw_worlds = enumerate_worlds(dimensions)
    current_worlds = filter_worlds(raw_worlds, known_facts or {})
    if not current_worlds:
        raise ValueError("known_facts already eliminate every world -- H(Xt) is undefined, there is nothing left to gain information about")
    h_current = hartley_measure(len(current_worlds))

    if not action_outcomes:
        raise ValueError("action_outcomes must be a non-empty list")
    total_p = sum(float(o["probability"]) for o in action_outcomes)
    if abs(total_p - 1.0) > 1e-6:
        raise ValueError(f"action_outcomes probabilities must sum to 1.0, got {total_p}")

    outcome_details = []
    expected_h_next = 0.0
    for o in action_outcomes:
        combined_facts = dict(known_facts or {})
        combined_facts.update(o.get("known_facts", {}))
        next_worlds = filter_worlds(current_worlds, combined_facts)
        if not next_worlds:
            raise ValueError(f"outcome {o.get('outcome_id')!r} eliminates every remaining world -- H is undefined for that branch, not zero")
        h_next = hartley_measure(len(next_worlds))
        expected_h_next += float(o["probability"]) * h_next
        outcome_details.append({
            "outcome_id": o.get("outcome_id", "unnamed"),
            "probability": o["probability"],
            "resulting_world_count": len(next_worlds),
            "hartley_bits": round(h_next, 6),
        })

    ig = h_current - expected_h_next
    return {
        "note": (
            "IG(a) = H(Xt) - E[H(Xt+1)|a]. Ranks a candidate INVESTIGATION "
            "action before it is taken -- a planning utility input, not a "
            "conformity probability, not a verdict, and it does not itself "
            "authorize or execute anything."
        ),
        "h_current_bits": round(h_current, 6),
        "current_world_count": len(current_worlds),
        "expected_h_next_bits": round(expected_h_next, 6),
        "information_gain_bits": round(ig, 6),
        "outcomes": outcome_details,
    }


def information_gain_from_resolving_dimension(dimensions: dict, known_facts: dict, target_dimension: str) -> dict:
    """Exact IG for the case where an action is expected to fully resolve one
    named dimension to a single confirmed value -- NOT an expectation over a
    forecast distribution (that is expected_information_gain() above), and
    not an approximation. Under Hartley's independent-dimension Cartesian-
    product structure, resolving one dimension with k still-undetermined
    values always yields exactly log2(k) bits, regardless of which value it
    turns out to be:

        H(Xt) = H(Xt with target_dimension pinned) + log2(k)
        =>  IG = H(Xt) - H(Xt pinned) = log2(k)

    This is the wiring point used by scripts/awm_runtime's planner to
    replace a hand-picked info_gain constant with a real, derived bit value
    WHEN a clause's possible_worlds_dimensions are available -- see
    aias_awm/cognition/planner.py and references/68-hartley-uncertainty.md.

    Returns a dict with status "OK" | "UNKNOWN_DIMENSION" | "ALREADY_RESOLVED";
    only "OK" carries a nonzero information_gain_bits. Also returns
    normalized_information_gain = IG / H(Xt) in [0, 1] for callers whose
    schema bounds expected_information_gain to that range.
    """
    raw_worlds = enumerate_worlds(dimensions)
    current_worlds = filter_worlds(raw_worlds, known_facts or {})
    if not current_worlds:
        raise ValueError("known_facts already eliminate every world -- nothing left to gain information about")
    h_current = hartley_measure(len(current_worlds))

    if target_dimension not in dimensions:
        return {
            "status": "UNKNOWN_DIMENSION",
            "information_gain_bits": 0.0,
            "normalized_information_gain": 0.0,
            "reason": f"{target_dimension!r} is not one of this clause's declared possible-worlds dimensions",
        }

    surviving_values = sorted(set(w[target_dimension] for w in current_worlds))
    k = len(surviving_values)
    if k <= 1:
        return {
            "status": "ALREADY_RESOLVED",
            "information_gain_bits": 0.0,
            "normalized_information_gain": 0.0,
            "h_current_bits": round(h_current, 6),
            "reason": f"{target_dimension!r} already has only one surviving value among current known_facts -- no further gain possible from resolving it",
        }

    ig = math.log2(k)
    return {
        "status": "OK",
        "target_dimension": target_dimension,
        "surviving_values": surviving_values,
        "h_current_bits": round(h_current, 6),
        "information_gain_bits": round(ig, 6),
        "normalized_information_gain": round(min(1.0, ig / h_current), 6) if h_current > 0 else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON file with dimensions/known_facts[/action_outcomes], or '-' for stdin")
    ap.add_argument("--mode", choices=["measure", "gain", "resolve-dimension"], default="measure",
                     help="measure: H(Xt) for the current state; gain: IG(a) across action_outcomes; "
                          "resolve-dimension: exact IG for fully resolving one named dimension")
    ap.add_argument("--output", help="where to write the result JSON (default: stdout)")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    payload = json.loads(raw)
    dimensions = payload.get("dimensions")
    known_facts = payload.get("known_facts", {})

    try:
        if args.mode == "measure":
            result = resolve_uncertainty(dimensions, known_facts)
            exit_code = 1 if result["status"] == "INCONSISTENT" else 0
        elif args.mode == "gain":
            action_outcomes = payload.get("action_outcomes")
            result = expected_information_gain(dimensions, known_facts, action_outcomes)
            exit_code = 0
        else:
            target_dimension = payload.get("target_dimension")
            result = information_gain_from_resolving_dimension(dimensions, known_facts, target_dimension)
            exit_code = 0 if result["status"] == "OK" else 1
    except ValueError as e:
        result = {"status": "ERROR", "reason": str(e)}
        exit_code = 2

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(out)
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
