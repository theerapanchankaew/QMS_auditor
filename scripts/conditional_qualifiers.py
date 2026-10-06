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

l7_route() is an executable specification of the prompt-level gate. It is
not wired into the gateway or the AWM runtime (crosswalk gap #2 stays open
for the *evaluation* of applicability from evidence).

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
