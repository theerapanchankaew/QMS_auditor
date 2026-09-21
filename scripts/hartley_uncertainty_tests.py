#!/usr/bin/env python3
"""
hartley_uncertainty_tests.py — regression suite for
scripts/hartley_uncertainty.py. Every case's expected outcome is constructed
by design (like scripts/world_constraint_validator_tests.py) -- no external
corpus involved.

The clause-6.1.3 dimension set below is transcribed verbatim from
AIAS_Theory_Technology_Stack_Textbook_v1.0.pdf, Ch.9's worked example (Q1
Implementation? / Q2 Effectiveness evaluated? / Q3 Objective record?) and
Ch.20's end-to-end use case, so the "textbook reproduction" tests double as
a check that this module's numbers (H=3 bits, IG=2 bits) actually match the
textbook's own stated numbers, not just internally-consistent arithmetic.

Usage:
  python scripts/hartley_uncertainty_tests.py --run
"""
import argparse
import json
from hartley_uncertainty import (
    enumerate_worlds,
    resolve_uncertainty,
    expected_information_gain,
    information_gain_from_resolving_dimension,
)

# Textbook Ch.9: "Q1 Implementation? YES/NO, Q2 Effectiveness evaluated?
# YES/NO, Q3 Objective record? PRESENT/ABSENT -> |Xraw| = 2x2x2 = 8 -> H=3 bits"
CLAUSE_613_DIMENSIONS = {
    "implementation": ["YES", "NO"],
    "effectiveness_evaluated": ["YES", "NO"],
    "objective_record": ["PRESENT", "ABSENT"],
}


def case_enumerate_worlds_cardinality():
    worlds = enumerate_worlds(CLAUSE_613_DIMENSIONS)
    assert len(worlds) == 8, worlds
    assert len(set(tuple(sorted(w.items())) for w in worlds)) == 8, "worlds must be distinct"


def case_hartley_matches_textbook_h3_bits():
    """Textbook Ch.9: |X|=8 -> H=log2(8)=3 bits, with no known facts yet."""
    r = resolve_uncertainty(CLAUSE_613_DIMENSIONS)
    assert r["raw_world_count"] == 8, r
    assert r["surviving_world_count"] == 8, r
    assert r["status"] == "MATERIAL_UNCERTAINTY", r
    assert r["hartley_bits"] == 3.0, r


def case_hartley_collapses_to_zero_after_full_evidence():
    """Textbook Ch.9 Step 7: objective evidence eliminates worlds down to one
    material state -> |X|=1 -> H=0. This must NOT be interpreted as
    'conforming' by this module -- it only reports the collapse."""
    known_facts = {"implementation": "NO", "effectiveness_evaluated": "NO", "objective_record": "ABSENT"}
    r = resolve_uncertainty(CLAUSE_613_DIMENSIONS, known_facts)
    assert r["surviving_world_count"] == 1, r
    assert r["status"] == "RESOLVED", r
    assert r["hartley_bits"] == 0.0, r
    assert "does NOT mean conforming" in r["reason"], r


def case_hartley_inconsistent_known_facts_fail_closed():
    """A known_fact value outside the declared dimension's domain (e.g. a
    typo) eliminates every world -- must fail closed as INCONSISTENT, never
    silently report H=0."""
    known_facts = {"objective_record": "MAYBE"}
    r = resolve_uncertainty(CLAUSE_613_DIMENSIONS, known_facts)
    assert r["surviving_world_count"] == 0, r
    assert r["status"] == "INCONSISTENT", r
    assert r["hartley_bits"] is None, r


def case_known_facts_unknown_dimension_key_is_ignored():
    """A known_facts key that isn't one of the declared dimensions must be
    ignored for elimination purposes, never invented as a new axis."""
    r = resolve_uncertainty(CLAUSE_613_DIMENSIONS, {"unrelated_field": "whatever"})
    assert r["surviving_world_count"] == 8, r
    assert r["hartley_bits"] == 3.0, r


def case_information_gain_matches_textbook_example():
    """Textbook Ch.10: 'if before the audit there are 8 feasible worlds (3
    bits) and REQUEST_RECORD is expected to reduce them to an average of 2
    worlds (1 bit): IG(REQUEST_RECORD) = 3 - 1 = 2 bits'. Modeled here as two
    equally likely branches, each pinning 2 of the 3 dimensions and leaving
    2 worlds (1 bit) per branch, so E[H_next] = 1 bit exactly."""
    action_outcomes = [
        {
            "outcome_id": "record_confirms_done",
            "probability": 0.5,
            "known_facts": {"implementation": "YES", "effectiveness_evaluated": "YES"},
        },
        {
            "outcome_id": "record_confirms_not_done",
            "probability": 0.5,
            "known_facts": {"implementation": "NO", "effectiveness_evaluated": "NO"},
        },
    ]
    r = expected_information_gain(CLAUSE_613_DIMENSIONS, {}, action_outcomes)
    assert r["h_current_bits"] == 3.0, r
    assert r["expected_h_next_bits"] == 1.0, r
    assert r["information_gain_bits"] == 2.0, r


def case_information_gain_rejects_probabilities_not_summing_to_one():
    action_outcomes = [
        {"outcome_id": "a", "probability": 0.5, "known_facts": {"implementation": "YES"}},
        {"outcome_id": "b", "probability": 0.2, "known_facts": {"implementation": "NO"}},
    ]
    try:
        expected_information_gain(CLAUSE_613_DIMENSIONS, {}, action_outcomes)
        raise AssertionError("expected ValueError for probabilities not summing to 1.0")
    except ValueError as e:
        assert "sum to 1.0" in str(e), e


def case_resolve_dimension_exact_ig_matches_log2_k():
    """Resolving 'objective_record' (k=2 surviving values: PRESENT/ABSENT)
    out of the full 8-world set must yield exactly log2(2)=1 bit, and
    normalized_information_gain = 1/3 of the current 3 bits -- this is an
    exact identity (Hartley's independent-dimension property), not a
    forecast approximation."""
    r = information_gain_from_resolving_dimension(CLAUSE_613_DIMENSIONS, {}, "objective_record")
    assert r["status"] == "OK", r
    assert r["information_gain_bits"] == 1.0, r
    assert r["h_current_bits"] == 3.0, r
    assert abs(r["normalized_information_gain"] - (1.0 / 3.0)) < 1e-6, r


def case_resolve_dimension_already_resolved_yields_zero_gain():
    known_facts = {"objective_record": "ABSENT"}
    r = information_gain_from_resolving_dimension(CLAUSE_613_DIMENSIONS, known_facts, "objective_record")
    assert r["status"] == "ALREADY_RESOLVED", r
    assert r["information_gain_bits"] == 0.0, r


def case_resolve_dimension_unknown_name_rejected():
    r = information_gain_from_resolving_dimension(CLAUSE_613_DIMENSIONS, {}, "not_a_real_dimension")
    assert r["status"] == "UNKNOWN_DIMENSION", r
    assert r["information_gain_bits"] == 0.0, r


def case_dimension_with_duplicate_values_rejected():
    try:
        enumerate_worlds({"objective_record": ["PRESENT", "PRESENT"]})
        raise AssertionError("expected ValueError for duplicate dimension values")
    except ValueError as e:
        assert "duplicate" in str(e), e


def case_empty_dimensions_rejected():
    try:
        enumerate_worlds({})
        raise AssertionError("expected ValueError for empty dimensions")
    except ValueError as e:
        assert "non-empty" in str(e), e


TESTS = [
    ("enumerate_worlds_cardinality_is_8", case_enumerate_worlds_cardinality),
    ("hartley_matches_textbook_h3_bits", case_hartley_matches_textbook_h3_bits),
    ("hartley_collapses_to_zero_after_full_evidence", case_hartley_collapses_to_zero_after_full_evidence),
    ("hartley_inconsistent_known_facts_fail_closed", case_hartley_inconsistent_known_facts_fail_closed),
    ("known_facts_unknown_dimension_key_ignored", case_known_facts_unknown_dimension_key_is_ignored),
    ("information_gain_matches_textbook_example", case_information_gain_matches_textbook_example),
    ("information_gain_rejects_bad_probabilities", case_information_gain_rejects_probabilities_not_summing_to_one),
    ("resolve_dimension_exact_ig_matches_log2_k", case_resolve_dimension_exact_ig_matches_log2_k),
    ("resolve_dimension_already_resolved_yields_zero_gain", case_resolve_dimension_already_resolved_yields_zero_gain),
    ("resolve_dimension_unknown_name_rejected", case_resolve_dimension_unknown_name_rejected),
    ("dimension_with_duplicate_values_rejected", case_dimension_with_duplicate_values_rejected),
    ("empty_dimensions_rejected", case_empty_dimensions_rejected),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if not args.run:
        print("Usage: hartley_uncertainty_tests.py --run")
        return 2

    results = []
    all_pass = True
    for name, fn in TESTS:
        try:
            fn()
            results.append({"test": name, "result": "PASS"})
        except AssertionError as e:
            all_pass = False
            results.append({"test": name, "result": "FAIL", "reason": str(e)})
    print(json.dumps({"results": results, "all_pass": all_pass}, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
