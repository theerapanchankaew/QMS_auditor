"""Tests for the registered-source retrieval stack (scripts/controlled_retrieval.py,
extract_clause.py, search_standard.py) and the manifests/index/profiles that
must stay consistent with it.

The standard PDF is licensed material and gitignored, so every test that needs
it is skipped when assets/standards/ISO_9001_2026.pdf is absent.

Run:  python -m pytest assets/tests/test_controlled_retrieval.py -q
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

REGISTRY = json.loads((ROOT / "assets/manifests/runtime-source-registry.json").read_text(encoding="utf-8"))
PRIMARY = REGISTRY["primary_standard"]
PDF = ROOT / PRIMARY["path"]

needs_pdf = pytest.mark.skipif(not PDF.exists(), reason="licensed ISO_9001_2026.pdf not present (gitignored)")


def run(script, *args):
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout


def clause_numbers():
    idx = json.loads((ROOT / "assets/requirement_profiles/_index.json").read_text(encoding="utf-8"))
    return [c["clause"] for c in idx["clauses"]]


# --- registry / manifest / profile consistency (no PDF needed except hash) ---

def test_registry_points_at_published_edition_not_fdis():
    assert PRIMARY["path"] == "assets/standards/ISO_9001_2026.pdf"
    assert "FDIS" not in PRIMARY["path"]


def test_active_manifest_source_matches_registry():
    manifest = json.loads((ROOT / "assets/manifests/bundled-source-manifest.json").read_text(encoding="utf-8"))
    active = {s["source_id"]: s for s in manifest["sources"]}
    src = active[PRIMARY["source_id"]]
    assert src["controlled_location"] == PRIMARY["path"]
    assert src["checksum_sha256"] == PRIMARY["sha256"]
    assert not any("fdis" in sid for sid in active), "FDIS must not be an active source"
    assert any(s["source_id"] == "iso9001-fdis-2026-en" for s in manifest["unavailable_historical_sources"])


def test_rag_policy_allows_only_active_sources():
    manifest = json.loads((ROOT / "assets/manifests/bundled-source-manifest.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "assets/manifests/local-rag-connection-policy.json").read_text(encoding="utf-8"))
    active = {s["source_id"] for s in manifest["sources"]}
    for profile in policy["approved_profiles"]:
        assert set(profile["allowed_source_ids"]) <= active


def test_manifest_and_policy_validator_pass():
    code, out = run("source_manifest_validator.py")
    assert code == 0, out
    assert json.loads(out)["status"] == "valid"


def test_every_profile_names_the_registered_pdf():
    for clause in clause_numbers():
        d = json.loads((ROOT / f"assets/requirement_profiles/{clause}.json").read_text(encoding="utf-8"))
        assert d["provenance"]["source_pdf"] == PRIMARY["path"], clause
        assert "FDIS" not in d["provenance"]["source_pdf"], clause


def test_rag_index_uses_registered_source_with_portable_paths():
    seen = set()
    for line in (ROOT / "assets/rag_indexes/bundled-qms-local-index.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        seen.add(row["source_id"])
        assert "\\" not in row["chunk_id"] and "\\" not in row["controlled_location"]
        if row["source_id"] == PRIMARY["source_id"]:
            assert row["controlled_location"] == PRIMARY["path"]
    assert PRIMARY["source_id"] in seen
    assert not any("fdis" in s for s in seen)


# --- registered-source retrieval ---------------------------------------

@needs_pdf
def test_registered_pdf_hash_matches_registry():
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == PRIMARY["sha256"]


@needs_pdf
def test_all_65_profile_clauses_have_credible_bodies_inside_registered_pages():
    from controlled_retrieval import ClauseStore
    store = ClauseStore()
    for clause in clause_numbers():
        c = store.get(clause)
        assert c["source"] == PRIMARY["path"] and c["source_sha256"] == PRIMARY["sha256"]
        assert PRIMARY["body_start_page"] <= c["start_page"] <= c["end_page"] <= PRIMARY["body_end_page"], clause
        assert len(c["text"]) >= 60 and "shall" in c["text"].lower(), clause


@needs_pdf
def test_6_1_3_text_and_page():
    from controlled_retrieval import ClauseStore
    c = ClauseStore().get("6.1.3")
    assert "Actions to address opportunities" in c["text"]
    assert "opportunities" in c["text"] and c["start_page"] == 19


@needs_pdf
def test_heading_correction_recovers_7_5_3():
    from controlled_retrieval import ClauseStore
    store = ClauseStore()
    assert "7.5.3" in store.clauses
    assert "7.8.3" not in store.clauses


@needs_pdf
def test_hash_mismatch_is_refused(monkeypatch):
    import controlled_retrieval as cr
    monkeypatch.setattr(cr, "sha256", lambda path: "0" * 64)
    with pytest.raises(cr.ReferenceGap, match="hash changed"):
        cr.ClauseStore()


@needs_pdf
def test_unknown_and_annex_clauses_are_reference_gaps():
    from controlled_retrieval import ClauseStore, ReferenceGap
    store = ClauseStore()
    for clause in ("99.9", "A.6.1.2", "1"):
        with pytest.raises(ReferenceGap):
            store.get(clause)


@needs_pdf
def test_extract_clause_cli_returns_registered_source_json():
    code, out = run("extract_clause.py", "6.1.3", "--json")
    assert code == 0, out
    d = json.loads(out)
    assert d["clause"] == "6.1.3" and d["source"] == PRIMARY["path"] and d["source_sha256"] == PRIMARY["sha256"]
    assert d["evidence_bucket"] == "primary" and "not a full OCR accuracy certification" in d["text_status"]


@needs_pdf
def test_extract_clause_cli_refuses_annex_and_unregistered_pdf():
    code, out = run("extract_clause.py", "6.1.3", "--include-annex")
    assert code == 2 and json.loads(out)["status"] == "ReferenceGap"
    code, out = run("extract_clause.py", "6.1.3", "--pdf", str(ROOT / "assets/standards/ISO_FDIS_9001_2026_en.pdf"))
    assert code == 2 and json.loads(out)["status"] == "ReferenceGap"


@needs_pdf
def test_search_standard_cli_finds_clause_and_validates_bounds():
    code, out = run("search_standard.py", "opportunities", "--json")
    assert code == 0, out
    d = json.loads(out)
    assert d["status"] == "ok" and any(r["clause"] == "6.1.3" for r in d["results"])
    assert all(r["source"] == PRIMARY["path"] for r in d["results"])
    code, out = run("search_standard.py", "opportunities", "--max", "99")
    assert code == 2 and json.loads(out)["status"] == "ReferenceGap"


@needs_pdf
def test_extractor_text_matches_known_published_wording_changes():
    """The published edition says 'conformity to', where the FDIS (and the
    profiles before 2026-10-05) said 'conformity with' -- see
    assets/requirement_profiles/README.md."""
    from controlled_retrieval import ClauseStore
    store = ClauseStore()
    assert "conformity to the acceptance criteria" in store.get("8.6")["text"].replace("\n", " ")
    prof = json.loads((ROOT / "assets/requirement_profiles/8.6.json").read_text(encoding="utf-8"))
    objs = " ".join(r["object"] for r in prof["requirements"])
    assert "conformity to the acceptance criteria" in objs and "conformity with" not in objs
