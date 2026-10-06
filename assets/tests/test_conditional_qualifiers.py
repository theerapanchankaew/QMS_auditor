"""Tests for the L7 Conditional Qualifier Gate v2: trigger vocabulary, the
executable routing table (scripts/conditional_qualifiers.py), and the
consistency of the docs / requirement profiles with them.

The inventory tests need the licensed registered PDF and are skipped when
assets/standards/ISO_9001_2026.pdf is absent (gitignored).

Run:  python -m pytest assets/tests/test_conditional_qualifiers.py -q
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import conditional_qualifiers as cq  # noqa: E402

PDF = ROOT / "assets/standards/ISO_9001_2026.pdf"
needs_pdf = pytest.mark.skipif(not PDF.exists(), reason="licensed ISO_9001_2026.pdf not present (gitignored)")

STANDARD_MAP = (ROOT / "references/standard/iso9001-2026-standard-map.md").read_text(encoding="utf-8")
REF26 = (ROOT / "references/26-layered-audit-cognition.md").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")


def documented_inventory():
    """{clause: {phrase, ...}} parsed from the standard-map table."""
    sec = STANDARD_MAP.split("## Conditional qualifiers in clauses 4–10", 1)[1].split("\n## ", 1)[0]
    inv = {}
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"\d+(\.\d+)*", cells[0]):
            phrases = {re.sub(r"\s*\([^)]*\)", "", p).strip(" ,").lower() for p in cells[1].split(";")}
            inv[cells[0]] = {p for p in phrases if p}
    return inv


# --- vocabulary ----------------------------------------------------------

@pytest.mark.parametrize("phrase,family", [
    ("as applicable", "A"), ("where applicable", "A"), ("when applicable", "A"), ("if applicable", "A"),
    ("if they are applicable", "A"), ("when relevant", "A"),
    ("as appropriate", "B"),
    ("to the extent necessary", "C"), ("as necessary", "C"), ("if necessary", "C"), ("when it is necessary", "C"),
])
def test_canonical_phrase_family(phrase, family):
    assert cq.PHRASE_FAMILY[phrase] == family
    assert cq.family_of(phrase) == family
    assert cq.find_qualifiers(f"The organization shall do X {phrase} for Y.") == [{"phrase": phrase, "family": family}]


def test_adjectival_uses_are_not_triggers():
    text = ("the applicable statutory requirements; take appropriate action; appropriate documented information; "
            "relevant interested parties; identified as being necessary for the effectiveness")
    assert cq.find_qualifiers(text) == []


def test_line_breaks_and_case_do_not_hide_a_phrase():
    assert cq.find_qualifiers("shall be retained\nto  the extent\nnecessary.") == [{"phrase": "to the extent necessary", "family": "C"}]
    assert cq.find_qualifiers("As Appropriate") == [{"phrase": "as appropriate", "family": "B"}]


def test_equivalent_construction_is_caught_by_head_word():
    assert cq.find_qualifiers("where relevant") == [{"phrase": "where relevant", "family": "A"}]
    assert cq.family_of("where appropriate") == "B"
    with pytest.raises(ValueError):
        cq.family_of("shall ensure")


# --- L7 routing table (executable specification) -------------------------

def route(family, **kw):
    return cq.l7_route(family, **{"condition_evidenced": False, **kw})["route"]


def test_family_a_undetermined_is_ofi_not_nc():
    assert route("A", determination="none") == cq.ROUTE_OFI


def test_family_a_applicable_goes_to_l8():
    assert route("A", determination="applicable") == cq.ROUTE_L8


def test_family_a_not_applicable_without_justification_is_ofi():
    assert route("A", determination="not_applicable", justification=False, a3_effect="none") == cq.ROUTE_OFI


def test_family_a_justified_not_applicable_needs_the_a3_test():
    assert route("A", determination="not_applicable", justification=True, a3_effect="none") == cq.ROUTE_COMPLIED
    assert route("A", determination="not_applicable", justification=True, a3_effect="affects") == cq.ROUTE_4_3
    assert route("A", determination="not_applicable", justification=True, a3_effect="unknown") == cq.ROUTE_REVIEW


def test_a3_defaults_fail_safe():
    """Omitting the A.3 effect must never produce Complied."""
    r = cq.l7_route("A", condition_evidenced=False, determination="not_applicable", justification=True)
    assert r["route"] == cq.ROUTE_REVIEW


def test_evidence_overrides_every_family_a_and_c_path():
    for fam in ("A", "C"):
        for det in cq.DETERMINATIONS:
            assert route(fam, determination=det, justification=True, a3_effect="none", condition_evidenced=True) == cq.ROUTE_L8


def test_family_b_is_never_a_not_applicable_switch():
    for det in cq.DETERMINATIONS:
        for just in (True, False):
            for ev in (True, False):
                r = cq.l7_route("B", condition_evidenced=ev, determination=det, justification=just, a3_effect="none")
                assert r["route"] == cq.ROUTE_L8, (det, just, ev)
    r = cq.l7_route("B", condition_evidenced=False, determination="not_applicable", justification=True, a3_effect="none")
    assert "cannot short-circuit" in r["reason"]


def test_family_c_paths():
    assert route("C", determination="none") == cq.ROUTE_OFI
    assert route("C", determination="extent_determined") == cq.ROUTE_L8
    assert route("C", determination="not_applicable", justification=True) == cq.ROUTE_COMPLIED
    assert route("C", determination="not_applicable", justification=False) == cq.ROUTE_OFI


def test_invalid_inputs_are_rejected():
    for kw in ({"family": "D"}, {"family": "A", "determination": "maybe"}, {"family": "A", "a3_effect": "some"}):
        with pytest.raises(ValueError):
            cq.l7_route(kw.pop("family"), condition_evidenced=False, **kw)


# --- docs / profiles stay consistent with the code -----------------------

def test_ref26_lists_every_canonical_phrase_and_the_spec():
    l7 = REF26.split("## L7 — Conditional Qualifier Gate", 1)[1].split("\n---\n\n## L8", 1)[0]
    for phrase in cq.PHRASE_FAMILY:
        assert f"`{phrase}`" in l7, phrase
    assert "l7_route" in l7 and "conditional_qualifiers.py" in l7


def test_skill_rule_3_names_the_three_families_and_annex_a():
    rule = next(l for l in SKILL.splitlines() if l.startswith("**3. L7 Conditional Qualifier Gate"))
    for token in ("Family A", "Family B", "Family C", "Annex A.2(a)", "Annex A.3", "OFI", "ReviewRequired"):
        assert token in rule, token


def test_documented_inventory_has_22_clauses_with_canonical_phrases_only():
    inv = documented_inventory()
    assert len(inv) == 22
    for clause, phrases in inv.items():
        assert phrases <= set(cq.PHRASE_FAMILY), (clause, phrases - set(cq.PHRASE_FAMILY))


def test_every_documented_phrase_is_recorded_on_a_profile_element():
    for clause, phrases in documented_inventory().items():
        d = json.loads((ROOT / f"assets/requirement_profiles/{clause}.json").read_text(encoding="utf-8"))
        blob = " ".join(f"{r.get('qualifier') or ''} {r.get('condition') or ''}".lower() for r in d["requirements"])
        for phrase in phrases:
            assert phrase in blob, f"{clause}: {phrase}"


@needs_pdf
def test_docs_inventory_equals_registered_text_inventory():
    scanned = {c: {i["phrase"] for i in items} for c, items in cq.inventory().items()}
    assert scanned == documented_inventory()


@needs_pdf
def test_8_5_6_ocr_exception_is_the_only_one_needed():
    from controlled_retrieval import ClauseStore
    store = ClauseStore()
    raw = {c for c in cq.KNOWN_OCR_EXCEPTIONS if not cq.find_qualifiers(store.get(c)["text"])}
    assert raw == {"8.5.6"}
