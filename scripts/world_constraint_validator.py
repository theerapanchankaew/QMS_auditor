#!/usr/bin/env python3
"""
world_constraint_validator.py — deterministic ambiguity gate for evidence tagging.

Naming note: "world" here means a candidate (epistemic_state, coverage)
tagging hypothesis (possible-worlds semantics), NOT the W0-W9/WG0-WG6
Audit World Model in scripts/awm_runtime/aias_awm/control/ (world_fsm.py,
world_gates.py). Different concept, different directory, no relation --
see docs/eei-blueprint-crosswalk.md for why that distinction matters here.

PORTED from the professional-auditor Claude Skill (v6.7), adapted to this
repo's own severity vocabulary (M1-M5 Major triggers via Q1-Q5 exposure
analysis, D1-D4 Minor anchors — see SKILL.md BLOCK 3, rules 4-13) instead
of professional-auditor's own labels. This is a genuinely portable pattern
because the underlying evidence-activity states — PRESENTED / VERIFIED /
PARTIAL / ABSENT — are already shared vocabulary between the two skills
(SKILL.md BLOCK 3 rule 16's linguistic trigger gate uses the same four
states professional-auditor's ref 24 does). Only the CONSEQUENCE_TABLE's
output labels needed to change; the (epistemic_state, coverage) input
domain did not.

WHAT THIS DOES NOT DO: it does not compute a full audit verdict from
constraints alone, and it does not run the M1-M5/Q1-Q5 exposure test or
the M4 three-condition test (rule 13) itself — those still need the LLM's
semantic judgment plus `harness_gate_executor.py`'s existing gates. This
validator only catches the case where the SAME evidence text supports two
readings that would send the finding down different downstream paths
(e.g. toward an M-trigger test vs. toward InsufficientEvidence) — it
flags that fork mechanically instead of letting the LLM silently pick one
branch.

WHAT THIS DOES: formalizes the (epistemic_state, coverage) -> consequence
mapping implied by BLOCK 3 rules 8, 14, and 16-22 into code, so that when
a Thai evidence description is genuinely double-readable (e.g.
"ไม่พบหลักฐาน" could mean ABSENT — "the process doesn't exist" — or
PRESENTED-unverified — "the auditee's claim, not yet independently
checked"), the disagreement is caught mechanically.

Terminology:
  world (hypothesis)   = one candidate (epistemic_state, coverage) tagging
                          for one ambiguous evidence element, proposed by
                          the LLM — it does NOT invent the tagging itself,
                          the LLM does; this script only validates/compares.
  viable world          = a hypothesis whose fields are in-domain (schema-valid)
  consequence V(w)      = the CONSEQUENCE_TABLE category that tagging
                          implies below — a pure function, no LLM call,
                          no learned weight.
  W                     = the set of viable worlds
  K                     = {V(w) for w in W} — the set of DISTINCT consequences

Resolution rule:
  |W| == 0            -> INCONSISTENT   (every proposed tagging was invalid) -> FAIL_CLOSED
  |W| == 1            -> UNIQUE          -> proceed with that tagging
  |W| > 1, |K| == 1   -> EQUIVALENT      -> multiple readings, same downstream
                                            path -> proceed
  |K| > 1             -> MATERIAL_AMBIGUITY -> BLOCK_AND_CLARIFY, do not guess

Forbidden signal: a world hypothesis must never carry a probability,
confidence, or likelihood field used to pick a "winner" — ambiguity is
resolved by evidence (a human clarifies, or new evidence removes a world),
never by which reading sounds more likely. Any such field found on an
input world is stripped and reported, not used.

Usage:
  python scripts/world_constraint_validator.py --input worlds.json
  python scripts/world_constraint_validator.py --input worlds.json --output result.json
"""
import argparse
import json
import sys

VALID_EPISTEMIC = {"PRESENTED", "VERIFIED", "PARTIAL", "ABSENT"}
VALID_COVERAGE = {"covered", "partial", "not_covered", "absent"}
FORBIDDEN_RANKING_FIELDS = {"confidence", "likelihood", "probability", "score", "rank"}

# Pure decision table, values adapted to this repo's own severity vocabulary
# (SKILL.md BLOCK 3 rules 8, 14, 16-22 — M1-M5/D1-D4/InsufficientEvidence).
# No LLM call, no learned weight, no corpus. Any change to this table is a
# change to those documented rules and must be made in both places together.
CONSEQUENCE_TABLE = {
    ("ABSENT", "not_covered"): "NC_CANDIDATE_PENDING_M1_M5_TEST",
    ("ABSENT", "absent"): "NC_CANDIDATE_PENDING_M1_M5_TEST",
    ("ABSENT", "partial"): "NC_CANDIDATE_PENDING_M1_M5_TEST",
    ("ABSENT", "covered"): "SCHEMA_INCONSISTENT_TAGGING",   # ABSENT evidence cannot be "covered"
    ("PRESENTED", "not_covered"): "InsufficientEvidence",
    ("PRESENTED", "partial"): "InsufficientEvidence",
    ("PRESENTED", "covered"): "InsufficientEvidence",       # BLOCK 3 rule 17: "presented" claims of full coverage still stay IE
    ("PRESENTED", "absent"): "SCHEMA_INCONSISTENT_TAGGING",
    ("VERIFIED", "covered"): "COMPLIED_CANDIDATE",
    ("VERIFIED", "partial"): "D1_MINOR_ANCHOR_CANDIDATE",
    ("VERIFIED", "not_covered"): "NC_CANDIDATE_PENDING_M1_M5_TEST",
    ("VERIFIED", "absent"): "NC_CANDIDATE_PENDING_M1_M5_TEST",
    ("PARTIAL", "partial"): "D1_MINOR_ANCHOR_CANDIDATE",
    ("PARTIAL", "not_covered"): "D1_MINOR_ANCHOR_CANDIDATE",
    ("PARTIAL", "covered"): "SCHEMA_INCONSISTENT_TAGGING",   # "partial" evidence claiming full coverage is an inconsistent tagging
    ("PARTIAL", "absent"): "SCHEMA_INCONSISTENT_TAGGING",
}



def strip_forbidden_fields(world: dict) -> tuple:
    """Remove any probability/confidence-style ranking field from a world hypothesis.
    Returns (cleaned_world, list_of_stripped_field_names)."""
    stripped = [k for k in world if k in FORBIDDEN_RANKING_FIELDS]
    cleaned = {k: v for k, v in world.items() if k not in FORBIDDEN_RANKING_FIELDS}
    return cleaned, stripped


def validate_world(world: dict) -> dict:
    """Check one world hypothesis for schema validity and compute its consequence.
    Returns a result dict; does not raise on invalid input — invalid worlds are
    reported as not viable, never silently dropped."""
    cleaned, stripped_fields = strip_forbidden_fields(world)
    world_id = cleaned.get("world_id", "unnamed")
    epistemic_state = cleaned.get("epistemic_state")
    coverage = cleaned.get("coverage")

    if epistemic_state not in VALID_EPISTEMIC or coverage not in VALID_COVERAGE:
        return {
            "world_id": world_id,
            "viable": False,
            "reason": f"out-of-domain assignment: epistemic_state={epistemic_state!r}, coverage={coverage!r}",
            "stripped_forbidden_fields": stripped_fields,
        }

    consequence = CONSEQUENCE_TABLE.get((epistemic_state, coverage))
    if consequence is None:
        return {
            "world_id": world_id,
            "viable": False,
            "reason": f"no rule for combination ({epistemic_state}, {coverage}) — update CONSEQUENCE_TABLE and SKILL.md BLOCK 3 rules 8/14/16-22 together",
            "stripped_forbidden_fields": stripped_fields,
        }
    if consequence == "SCHEMA_INCONSISTENT_TAGGING":
        return {
            "world_id": world_id,
            "viable": False,
            "reason": f"({epistemic_state}, {coverage}) is an internally inconsistent tagging per SKILL.md BLOCK 3 — not a real-world possibility",
            "stripped_forbidden_fields": stripped_fields,
        }

    return {
        "world_id": world_id,
        "viable": True,
        "epistemic_state": epistemic_state,
        "coverage": coverage,
        "consequence": consequence,
        "stripped_forbidden_fields": stripped_fields,
    }


def resolve(worlds: list) -> dict:
    results = [validate_world(w) for w in worlds]
    viable = [r for r in results if r["viable"]]
    consequences = sorted(set(r["consequence"] for r in viable))
    any_stripped = any(r["stripped_forbidden_fields"] for r in results)

    if len(viable) == 0:
        status = "INCONSISTENT"
        action = "FAIL_CLOSED"
    elif len(consequences) == 1:
        status = "UNIQUE" if len(viable) == 1 else "EQUIVALENT"
        action = "PROCEED"
    else:
        status = "MATERIAL_AMBIGUITY"
        action = "BLOCK_AND_CLARIFY"

    return {
        "note": "Deterministic table lookup only (SKILL.md BLOCK 3 rules 8/14/16-22) — no LLM call, no probability, no learned weight involved in this resolution.",
        "world_count": len(worlds),
        "viable_world_count": len(viable),
        "consequence_set": consequences,
        "status": status,
        "action": action,
        "forbidden_ranking_fields_stripped": any_stripped,
        "worlds": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON file with a list of world hypotheses, or '-' for stdin")
    ap.add_argument("--output", help="where to write the result JSON (default: stdout)")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    worlds = json.loads(raw)
    if not isinstance(worlds, list):
        print("Input must be a JSON list of world hypotheses.", file=sys.stderr)
        return 2

    result = resolve(worlds)
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(out)
    print(out)
    return 0 if result["status"] != "MATERIAL_AMBIGUITY" else 1


if __name__ == "__main__":
    raise SystemExit(main())