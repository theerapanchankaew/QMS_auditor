#!/usr/bin/env python3
"""
conditional_qualifiers.py -- canonical trigger vocabulary and executable
specification of the L7 Conditional Qualifier Gate (L7 v2, 2026-10-06).

Single source of truth for:
  * which phrases trigger L7, and the family each belongs to (A/B/C);
  * the L7 routing table (l7_route) that SKILL.md rule 3 and
    references/26-layered-audit-cognition.md describe in prose;
  * the inventory of clauses 4-10 whose registered text carries a phrase
    (checked against references/standard/iso9001-2026-standard-map.md by
    assets/tests/test_conditional_qualifiers.py, so docs and code cannot
    drift silently).

Families (ISO 9001:2026 Annex A.2 / A.3):
  A  applicability / relevance -- as applicable, where applicable, when
     applicable, if applicable, if they are applicable, when relevant.
     A requirement generally applicable under 4.3 may be determined not
     applicable in some situations, but only if that does not affect
     conformity of products and services, customer satisfaction or
     statutory/regulatory obligations, and the determination was
     considered and justified (A.2(a), A.3, 4.3).
  B  appropriateness -- as appropriate. NOT interchangeable with
     "applicable" (A.2(a)): the requirement still applies; "appropriate"
     means suitable for the organization's context and involves judgement.
  C  extent / necessity -- to the extent necessary, as necessary, if
     necessary, when it is necessary. Annex A does not define these; the
     grouping is this project's. The organization determines the extent.

NOT triggers: adjectival uses ("applicable requirements", "take
appropriate action", "relevant interested parties") and event conditions
("when requirements are changed"). Elements conditional only by scope or
circumstance (8.3 via 4.3; 8.5.3 customer property; 8.5.5 post-delivery;
the 7.1.5.2 traceability lead-in) have no phrase; references/27 marks
them "by scope"/"by circumstance" and L7 treats them as family A.

l7_route() is the executable specification of the gate. It is enforced by
scripts/harness_gate_executor.py (gate "L7": l7_from_trace + the verdict
check below; the OpenWebUI gateway runs that harness on every trace) and
derived for AWM candidates by aias_awm/control/gate_trace_deriver.py (which
uses a parity copy, aias_awm/qualifiers.py, because the AWM package is
installed independently). What stays open (crosswalk gap #2) is *judging*
applicability from evidence: the inputs to l7_route are supplied by the
LLM (gateway) or by explicit evidence metadata (AWM), never inferred.

Usage:
  python scripts/conditional_qualifiers.py --inventory [--json]
  python scripts/conditional_qualifiers.py --text "... as appropriate ..."
"""
from __future__ import annotations

import argparse
import json
import re
import sys

FAMILY_A = "A"
FAMILY_B = "B"
FAMILY_C = "C"
FAMILY_NAMES = {FAMILY_A: "applicability", FAMILY_B: "appropriateness", FAMILY_C: "extent"}

# Canonical phrases, lowercase, single-spaced.
PHRASE_FAMILY = {
    "as applicable": FAMILY_A,
    "where applicable": FAMILY_A,
    "when applicable": FAMILY_A,
    "if applicable": FAMILY_A,
    "if they are applicable": FAMILY_A,
    "when relevant": FAMILY_A,
    "as appropriate": FAMILY_B,
    "to the extent necessary": FAMILY_C,
    "as necessary": FAMILY_C,
    "if necessary": FAMILY_C,
    "when it is necessary": FAMILY_C,
}

# Equivalent constructions are caught by shape, not enumeration; the head
# word decides the family.
_QUAL_RE = re.compile(
    r"\b(?:to\s+the\s+extent\s+necessary"
    r"|(?:as|where|when|if)\s+(?:(?:they|it)\s+(?:are|is)\s+)?(?:applicable|relevant|appropriate|necessary))\b",
    re.IGNORECASE,
)
_HEAD_FAMILY = {"applicable": FAMILY_A, "relevant": FAMILY_A, "appropriate": FAMILY_B, "necessary": FAMILY_C}

# The registered PDF's OCR layer drops this phrase (hyphenated line break
# "provi-sion"); confirmed on the IS page image and in the FDIS text layer.
KNOWN_OCR_EXCEPTIONS = {"8.5.6": ("to the extent necessary",)}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("­", " ")).strip().lower()


def find_qualifiers(text: str) -> list[dict]:
    """Distinct qualifier phrases in `text`, as {phrase, family}, in order."""
    seen, out = set(), []
    for m in _QUAL_RE.finditer(re.sub(r"\s+", " ", text.replace("­", ""))):
        phrase = _norm(m.group(0))
        if phrase in seen:
            continue
        seen.add(phrase)
        out.append({"phrase": phrase, "family": family_of(phrase)})
    return out


def family_of(phrase: str) -> str:
    p = _norm(phrase)
    if p in PHRASE_FAMILY:
        return PHRASE_FAMILY[p]
    if p.startswith("to the extent"):
        return FAMILY_C
    head = p.split()[-1]
    if head in _HEAD_FAMILY:
        return _HEAD_FAMILY[head]
    raise ValueError(f"not a conditional-qualifier phrase: {phrase!r}")


def inventory(store=None) -> dict[str, list[dict]]:
    """{clause: [{phrase, family}, ...]} over the registered clauses 4-10.
    Needs the registered PDF (scripts/controlled_retrieval.ClauseStore)."""
    if store is None:
        from controlled_retrieval import ClauseStore
        store = ClauseStore()
    inv: dict[str, list[dict]] = {}
    for clause in sorted(store.profiles, key=lambda c: tuple(map(int, c.split(".")))):
        found = find_qualifiers(store.get(clause)["text"])
        have = {f["phrase"] for f in found}
        for phrase in KNOWN_OCR_EXCEPTIONS.get(clause, ()):
            if phrase not in have:
                found.append({"phrase": phrase, "family": family_of(phrase)})
        if found:
            inv[clause] = found
    return inv


# --------------------------------------------------------------------------
# L7 routing table (executable specification)
# --------------------------------------------------------------------------

ROUTE_L8 = "L8"                      # proceed to the breach test
ROUTE_OFI = "OFI_STOP"               # OFI, not NC; stop
ROUTE_COMPLIED = "COMPLIED_STOP"     # justified not applicable / nil extent; stop
ROUTE_4_3 = "ROUTE_4_3"              # judge the scope determination under 4.3, not the qualifier clause
ROUTE_REVIEW = "REVIEW_REQUIRED"     # human auditor must decide

DETERMINATIONS = ("none", "applicable", "not_applicable", "extent_determined")
A3_EFFECTS = ("none", "affects", "unknown")


def l7_route(
    family: str,
    *,
    condition_evidenced: bool,
    determination: str = "none",
    justification: bool = False,
    a3_effect: str = "unknown",
) -> dict:
    """Route one conditional element through L7.

    condition_evidenced -- objective evidence that the circumstance/activity
        exists, or that the requirement is clearly needed (evidence beats
        paperwork: it overrides the organization's own claim).
    determination -- the organization's own determination: "none" (not
        assessed), "applicable", "not_applicable", or "extent_determined"
        (family C: it determined the necessary extent).
    justification -- a not-applicable / nil-extent claim was considered and
        reasoned (A.3: "determined, with justification"; see 4.3).
    a3_effect -- family A, not-applicable claims only: does the claim affect
        the ability to ensure conformity of products and services, enhance
        customer satisfaction or fulfil statutory/regulatory obligations
        (Annex A.3)? "none" | "affects" | "unknown".
    """
    if family not in FAMILY_NAMES:
        raise ValueError(f"unknown family {family!r}")
    if determination not in DETERMINATIONS:
        raise ValueError(f"unknown determination {determination!r}")
    if a3_effect not in A3_EFFECTS:
        raise ValueError(f"unknown a3_effect {a3_effect!r}")

    def out(route: str, reason: str) -> dict:
        return {"route": route, "family": family, "reason": reason}

    if family == FAMILY_B:
        why = "'as appropriate' is not an applicability switch (Annex A.2(a)): the requirement applies"
        if determination == "not_applicable":
            why += "; a not-applicable claim cannot short-circuit it"
        return out(ROUTE_L8, why + ". Judge the organization's own suitable approach in L8; do not substitute your own. "
                   "No evidence -> InsufficientEvidence per L8, not NC and not OFI-by-N/A.")

    if condition_evidenced:
        return out(ROUTE_L8, "objective evidence shows the condition applies; it overrides any 'not applicable' claim or missing determination")

    if determination == "none":
        return out(ROUTE_OFI, "condition not assessed and no objective evidence it applies -> OFI, not NC")
    if determination in ("applicable", "extent_determined"):
        return out(ROUTE_L8, "the organization determined the condition applies / determined the extent; test it in L8")

    # determination == "not_applicable" (family A) or nil extent (family C)
    if not justification:
        return out(ROUTE_OFI, "'not applicable' claimed without justification is not a valid determination (A.3: considered and justified) -> OFI")
    if family == FAMILY_C:
        return out(ROUTE_COMPLIED, "justified nil/limited extent and no evidence of need -> Complied")
    if a3_effect == "none":
        return out(ROUTE_COMPLIED, "justified not-applicable that does not affect conformity, customer satisfaction or statutory obligations (A.3) -> Complied")
    if a3_effect == "affects":
        return out(ROUTE_4_3, "the exclusion affects conformity/customer satisfaction/statutory obligations, so A.3 is not met: judge the scope determination under 4.3 (AR-4.3-E07 / E09), not this clause")
    return out(ROUTE_REVIEW, "cannot establish from evidence whether the exclusion affects conformity, customer satisfaction or statutory obligations (A.3) -> ReviewRequired")


ROUTE_PRIORITY = (ROUTE_4_3, ROUTE_REVIEW, ROUTE_L8, ROUTE_OFI, ROUTE_COMPLIED)


def combine_routes(routes: list[str]) -> str:
    """One element can carry phrases of different families (e.g. 8.4.3:
    `as appropriate` + `as applicable`). Most cautious route wins:
    4.3 route > ReviewRequired > L8 > OFI > Complied. Family B always yields
    L8, so a mixed element is never closed by its applicability phrase alone."""
    if not routes:
        raise ValueError("no routes to combine")
    for r in ROUTE_PRIORITY:
        if r in routes:
            return r
    raise ValueError(f"unknown routes {routes!r}")


# Verdicts a trace may carry for each route. ReviewRequired (human
# escalation) is never a violation. L8 imposes no L7 constraint.
ROUTE_ALLOWED_VERDICTS = {
    ROUTE_OFI: frozenset({"OFI", "ReviewRequired"}),
    ROUTE_COMPLIED: frozenset({"Complied", "InsufficientEvidence", "ReviewRequired"}),
    ROUTE_4_3: frozenset({"ReviewRequired", "InsufficientEvidence"}),
    ROUTE_REVIEW: frozenset({"ReviewRequired", "InsufficientEvidence"}),
    ROUTE_L8: None,
}
ROUTE_FORCED_VERDICT = {
    ROUTE_OFI: "OFI",
    ROUTE_COMPLIED: "Complied",
    ROUTE_4_3: "ReviewRequired",
    ROUTE_REVIEW: "ReviewRequired",
}

# The 22 clauses whose registered text carries a qualifier phrase (see the
# standard-map table; a test keeps this equal to it and to the PDF scan).
QUALIFIER_CLAUSES = frozenset({
    "4.3", "4.4.2", "5.2.2", "6.2.1", "7.1.5.2", "7.1.6", "7.2", "7.5.3.2", "8.1", "8.2.1", "8.2.3.1",
    "8.2.3.2", "8.3.5", "8.3.6", "8.4.3", "8.5.1", "8.5.2", "8.5.4", "8.5.6", "8.6", "9.1.1", "10.2.1",
})
# Conditional by scope (8.3 via 4.3) or by circumstance (no phrase in the
# text): references/27 marks them; L7 treats them as family A.
SCOPE_CONDITIONAL_CLAUSES = frozenset({"8.5.3", "8.5.5"})


def is_conditional_clause(clause) -> bool:
    c = (clause or "").strip()
    return c in QUALIFIER_CLAUSES or c in SCOPE_CONDITIONAL_CLAUSES or c == "8.3" or c.startswith("8.3.")


def l7_from_trace(section) -> dict:
    """Validate and evaluate a gate_execution_trace["L7_conditional_qualifier"]
    section. Returns {"ok": True, "route", "routes", "families"} or
    {"ok": False, "error"}. Section: phrases (non-empty list of qualifier
    phrases), condition_evidenced (bool, required), determination, justification,
    a3_effect (see l7_route), determination_conflict (bool; the evidence
    carries conflicting organization determinations -> ReviewRequired)."""
    if not isinstance(section, dict):
        return {"ok": False, "error": "L7_conditional_qualifier must be an object"}
    phrases = section.get("phrases")
    if not isinstance(phrases, list) or not phrases or not all(isinstance(p, str) for p in phrases):
        return {"ok": False, "error": "L7_conditional_qualifier.phrases must be a non-empty list of strings"}
    try:
        families = [family_of(p) for p in phrases]
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    evidenced = section.get("condition_evidenced")
    if not isinstance(evidenced, bool):
        return {"ok": False, "error": "L7_conditional_qualifier.condition_evidenced must be true or false"}
    determination = section.get("determination", "none")
    if determination not in DETERMINATIONS:
        return {"ok": False, "error": f"L7_conditional_qualifier.determination must be one of {list(DETERMINATIONS)}"}
    justification = section.get("justification", False)
    conflict = section.get("determination_conflict", False)
    if not isinstance(justification, bool) or not isinstance(conflict, bool):
        return {"ok": False, "error": "L7_conditional_qualifier.justification / determination_conflict must be booleans"}
    a3_effect = section.get("a3_effect", "unknown")
    if a3_effect not in A3_EFFECTS:
        return {"ok": False, "error": f"L7_conditional_qualifier.a3_effect must be one of {list(A3_EFFECTS)}"}
    if conflict:
        routes = [ROUTE_REVIEW]
    else:
        routes = [
            l7_route(f, condition_evidenced=evidenced, determination=determination,
                     justification=justification, a3_effect=a3_effect)["route"]
            for f in families
        ]
    return {"ok": True, "route": combine_routes(routes), "routes": routes, "families": families}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--inventory", action="store_true", help="scan the registered PDF (clauses 4-10)")
    ap.add_argument("--text", help="list qualifier phrases found in this text")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.text is not None:
        print(json.dumps(find_qualifiers(a.text), ensure_ascii=False, indent=2))
        return 0
    if a.inventory:
        inv = inventory()
        if a.json:
            print(json.dumps(inv, ensure_ascii=False, indent=2))
        else:
            for c, items in inv.items():
                print(c, "; ".join(f"{i['phrase']} [{i['family']}]" for i in items))
            print(f"{len(inv)} clauses")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
