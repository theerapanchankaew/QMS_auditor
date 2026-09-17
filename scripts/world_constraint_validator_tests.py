#!/usr/bin/env python3
"""
world_constraint_validator_tests.py — regression suite for
scripts/world_constraint_validator.py. Every case's expected outcome is
constructed by design (like scripts/gate_boundary_test_generator.py and
scripts/world_model_coherence_test.py) — no external corpus involved.

Includes two adversarial cases modeled directly on the uploaded AWM
handbook's C-01/A-01 test pattern: proving the validator ignores a
smuggled-in ranking signal rather than using it to silently pick a winner.

Usage:
  python scripts/world_constraint_validator_tests.py --run
"""
import argparse
import json
import sys
from world_constraint_validator import resolve


def case_material_ambiguity():
    """Two structurally valid readings of the same 'ไม่พบหลักฐาน'-style evidence
    lead to different consequences -> must block, never guess."""
    worlds = [
        {"world_id": "H1_absent", "epistemic_state": "ABSENT", "coverage": "not_covered"},
        {"world_id": "H2_presented", "epistemic_state": "PRESENTED", "coverage": "not_covered"},
    ]
    r = resolve(worlds)
    assert r["status"] == "MATERIAL_AMBIGUITY", r
    assert r["action"] == "BLOCK_AND_CLARIFY", r
    assert len(r["consequence_set"]) == 2, r


def case_equivalent_worlds():
    """Two different-looking tags that both land on the same ref-24 consequence
    (PRESENTED stays InsufficientEvidence whether coverage is claimed full or not,
    per rule 17) -> safe to proceed despite multiple worlds."""
    worlds = [
        {"world_id": "H1", "epistemic_state": "PRESENTED", "coverage": "not_covered"},
        {"world_id": "H2", "epistemic_state": "PRESENTED", "coverage": "covered"},
    ]
    r = resolve(worlds)
    assert r["status"] == "EQUIVALENT", r
    assert r["action"] == "PROCEED", r
    assert r["consequence_set"] == ["InsufficientEvidence"], r


def case_unique_world():
    worlds = [{"world_id": "H1", "epistemic_state": "VERIFIED", "coverage": "covered"}]
    r = resolve(worlds)
    assert r["status"] == "UNIQUE", r
    assert r["action"] == "PROCEED", r


def case_inconsistent_all_invalid():
    """Every proposed world is schema-invalid -> INCONSISTENT, fail closed.
    (ABSENT evidence cannot simultaneously be 'covered' per ref 24 — that
    combination does not describe a real possible reading.)"""
    worlds = [{"world_id": "H1", "epistemic_state": "ABSENT", "coverage": "covered"}]
    r = resolve(worlds)
    assert r["status"] == "INCONSISTENT", r
    assert r["action"] == "FAIL_CLOSED", r
    assert r["viable_world_count"] == 0, r


def case_out_of_domain_value_rejected():
    """A value outside the controlled vocabulary (e.g. a typo or an invented
    state) must be rejected as not viable, never silently coerced to the
    nearest valid value."""
    worlds = [{"world_id": "H1", "epistemic_state": "LIKELY_ABSENT", "coverage": "not_covered"}]
    r = resolve(worlds)
    assert r["viable_world_count"] == 0, r
    assert r["status"] == "INCONSISTENT", r


def case_adversarial_confidence_field_ignored():
    """Modeled on the handbook's A-01 test: a world hypothesis carries a fake
    'confidence' score trying to make one reading look more likely. The
    validator must strip it and still report ambiguity, not silently pick
    the higher-confidence world."""
    worlds = [
        {"world_id": "H1_absent", "epistemic_state": "ABSENT", "coverage": "not_covered", "confidence": 0.95},
        {"world_id": "H2_presented", "epistemic_state": "PRESENTED", "coverage": "not_covered", "confidence": 0.05},
    ]
    r = resolve(worlds)
    assert r["status"] == "MATERIAL_AMBIGUITY", "adversarial confidence field must not resolve ambiguity: " + str(r)
    assert r["forbidden_ranking_fields_stripped"] is True, r
    for w in r["worlds"]:
        assert "confidence" not in w, "confidence field leaked into a validated world: " + str(w)


def case_adversarial_probability_field_ignored_single_world():
    """Even with only one world proposed, a smuggled probability field must not
    appear in the validated output — the field is stripped regardless of
    whether ambiguity was present, per the handbook's 'never rank by
    probability' rule applying unconditionally, not just when >1 world exists."""
    worlds = [{"world_id": "H1", "epistemic_state": "VERIFIED", "coverage": "covered", "probability": 0.99}]
    r = resolve(worlds)
    assert r["status"] == "UNIQUE", r
    assert r["forbidden_ranking_fields_stripped"] is True, r
    assert "probability" not in r["worlds"][0], r


TESTS = [
    ("material_ambiguity_blocks", case_material_ambiguity),
    ("equivalent_worlds_proceed", case_equivalent_worlds),
    ("unique_world_proceeds", case_unique_world),
    ("inconsistent_all_invalid_fails_closed", case_inconsistent_all_invalid),
    ("out_of_domain_value_rejected", case_out_of_domain_value_rejected),
    ("adversarial_confidence_field_ignored", case_adversarial_confidence_field_ignored),
    ("adversarial_probability_field_stripped_even_when_unique", case_adversarial_probability_field_ignored_single_world),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if not args.run:
        print("Usage: world_constraint_validator_tests.py --run")
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