"""L7 Conditional Qualifier Gate v2 -- parity copy for the aias_awm package.

Port of scripts/conditional_qualifiers.py (vocabulary, l7_route,
combine_routes, l7_from_trace), kept here because this package is installed
independently and imports nothing from the repo's scripts/ directory (same
reason as aias_awm/hartley.py). assets/tests/awm_v07/test_l7_awm.py asserts
parity with the script over every input combination, so a drift between the
two is a test failure, not a silent divergence.

Also holds l7_inputs(): the deterministic derivation of l7_route's inputs
from the evidence attached to one requirement. Nothing is *judged* from
evidence content; the organization's determination is read only from an
explicit, opt-in EvidenceItem.metadata contract (same style as the M4
flags in control/gate_trace_deriver.py):

    org_determination   "applicable" | "not_applicable" | "extent_determined"
                        -- this item records the organization's own
                        determination (it is NOT counted as activity evidence)
    na_justification    true  -- the not-applicable / nil-extent claim was
                        considered and reasoned (Annex A.3, 4.3)
    a3_effect           "none" | "affects" | "unknown" -- does the claim
                        affect conformity, customer satisfaction or
                        statutory/regulatory obligations (Annex A.3)?
    condition_applies   false -- opt this item out of "activity evidence"
                        (e.g. an interview saying the activity does not exist)

Every other non-invalid evidence item attached to the requirement counts as
objective evidence that the activity exists. Defaults are fail-safe:
no determination, no justification, a3_effect "unknown".
"""
from __future__ import annotations

import re

FAMILY_A, FAMILY_B, FAMILY_C = "A", "B", "C"

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
_QUAL_RE = re.compile(
    r"\b(?:to\s+the\s+extent\s+necessary"
    r"|(?:as|where|when|if)\s+(?:(?:they|it)\s+(?:are|is)\s+)?(?:applicable|relevant|appropriate|necessary))\b",
    re.IGNORECASE,
)
_HEAD_FAMILY = {"applicable": FAMILY_A, "relevant": FAMILY_A, "appropriate": FAMILY_B, "necessary": FAMILY_C}

ROUTE_L8 = "L8"
ROUTE_OFI = "OFI_STOP"
ROUTE_COMPLIED = "COMPLIED_STOP"
ROUTE_4_3 = "ROUTE_4_3"
ROUTE_REVIEW = "REVIEW_REQUIRED"
ROUTE_PRIORITY = (ROUTE_4_3, ROUTE_REVIEW, ROUTE_L8, ROUTE_OFI, ROUTE_COMPLIED)

DETERMINATIONS = ("none", "applicable", "not_applicable", "extent_determined")
A3_EFFECTS = ("none", "affects", "unknown")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("­", " ")).strip().lower()


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


def phrases_in(text: str | None) -> list[str]:
    """Distinct canonical qualifier phrases found in an element's qualifier
    text (e.g. 'as appropriate; as applicable (d)'), in order."""
    seen: list[str] = []
    for m in _QUAL_RE.finditer(re.sub(r"\s+", " ", (text or "").replace("­", ""))):
        p = _norm(m.group(0))
        if p not in seen:
            seen.append(p)
    return seen


def l7_route(family, *, condition_evidenced, determination="none", justification=False, a3_effect="unknown") -> dict:
    if family not in (FAMILY_A, FAMILY_B, FAMILY_C):
        raise ValueError(f"unknown family {family!r}")
    if determination not in DETERMINATIONS:
        raise ValueError(f"unknown determination {determination!r}")
    if a3_effect not in A3_EFFECTS:
        raise ValueError(f"unknown a3_effect {a3_effect!r}")

    def out(route, reason):
        return {"route": route, "family": family, "reason": reason}

    if family == FAMILY_B:
        return out(ROUTE_L8, "'as appropriate' is not an applicability switch (Annex A.2(a)): the requirement applies")
    if condition_evidenced:
        return out(ROUTE_L8, "objective evidence shows the condition applies")
    if determination == "none":
        return out(ROUTE_OFI, "condition not assessed and no objective evidence it applies -> OFI, not NC")
    if determination in ("applicable", "extent_determined"):
        return out(ROUTE_L8, "the organization determined the condition applies / determined the extent")
    if not justification:
        return out(ROUTE_OFI, "'not applicable' claimed without justification is not a valid determination -> OFI")
    if family == FAMILY_C:
        return out(ROUTE_COMPLIED, "justified nil/limited extent and no evidence of need -> Complied")
    if a3_effect == "none":
        return out(ROUTE_COMPLIED, "justified not-applicable with no effect on conformity/customer satisfaction/statutory obligations (A.3)")
    if a3_effect == "affects":
        return out(ROUTE_4_3, "A.3 not met: judge the scope determination under 4.3")
    return out(ROUTE_REVIEW, "cannot establish the A.3 effect from evidence -> ReviewRequired")


def combine_routes(routes) -> str:
    if not routes:
        raise ValueError("no routes to combine")
    for r in ROUTE_PRIORITY:
        if r in routes:
            return r
    raise ValueError(f"unknown routes {routes!r}")


def l7_from_section(section: dict) -> dict:
    """Same evaluation as scripts/conditional_qualifiers.l7_from_trace for a
    section this package built itself (assumes well-formed input)."""
    families = [family_of(p) for p in section["phrases"]]
    if section.get("determination_conflict"):
        routes = [ROUTE_REVIEW]
    else:
        routes = [
            l7_route(f, condition_evidenced=section["condition_evidenced"],
                     determination=section.get("determination", "none"),
                     justification=section.get("justification", False),
                     a3_effect=section.get("a3_effect", "unknown"))["route"]
            for f in families
        ]
    return {"route": combine_routes(routes), "routes": routes, "families": families}


_INACTIVE = {"INVALID", "SUPERSEDED"}
_VALID_DET = {"applicable", "not_applicable", "extent_determined"}
_A3_RANK = {"none": 0, "unknown": 1, "affects": 2}


def l7_inputs(evidence_items, applicability: str = "APPLICABLE") -> dict:
    """Inputs for l7_route from the evidence items attached to ONE
    requirement (see module docstring for the metadata contract).
    `applicability` is RequirementAssessment.applicability; only
    "NOT_APPLICABLE" is read from it (a caller-supplied claim), and only when
    no evidence item records a determination."""
    active = [e for e in evidence_items if e.epistemic_state.value not in _INACTIVE]
    det_items = [e for e in active if e.metadata.get("org_determination") is not None]
    activity = [e for e in active if e.metadata.get("org_determination") is None and e.metadata.get("condition_applies") is not False]
    dets = {str(e.metadata["org_determination"]) for e in det_items} & _VALID_DET
    conflict = len(dets) > 1
    if len(dets) == 1:
        determination = next(iter(dets))
    elif not det_items and applicability == "NOT_APPLICABLE":
        determination = "not_applicable"
    else:
        determination = "none"
    chosen = [e for e in det_items if str(e.metadata["org_determination"]) == determination]
    justification = any(e.metadata.get("na_justification") is True for e in chosen)
    a3 = [str(e.metadata["a3_effect"]) for e in chosen if str(e.metadata.get("a3_effect")) in _A3_RANK]
    a3_effect = max(a3, key=_A3_RANK.__getitem__) if a3 else "unknown"
    return {
        "condition_evidenced": bool(activity),
        "determination": determination,
        "justification": justification,
        "a3_effect": a3_effect,
        "determination_conflict": conflict,
    }
