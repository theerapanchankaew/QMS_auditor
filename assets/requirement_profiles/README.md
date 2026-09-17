# ISO/FDIS 9001:2026 Atomic Requirement Profiles

**Status: AI-drafted, NOT SME/human-auditor reviewed.** `requires_sme_approval: true`
in every file. Do not treat as certified interpretation of the standard, and
do not feed into a production verdict pipeline as ground truth until a
qualified auditor has reviewed it — the same standard this repo requires of
any other data source (see `docs/eei-blueprint-crosswalk.md` and the
project's own governance stance that human auditor judgment is final).

## What this is

One JSON file per clause (`<clause>.json`, e.g. `6.1.3.json`), each holding
the clause's `AtomicRequirement` records exactly in the schema defined by
`scripts/awm_runtime/aias_awm/domain/models.py::AtomicRequirement` — every
record in every file has been validated against that real Pydantic model
(`extra="forbid"`, strict types), not just hand-checked JSON.

Coverage: **65 clauses, 155 atomic requirement elements** — clauses 4.1
through 10.2.2 of ISO/FDIS 9001:2026 (the normative body; Annex A excluded).
`_index.json` lists every clause with its element count and assigned
`semantic_category`.

## Provenance

- **Clause boundaries and element counts** come from the 65-clause /
  155-element `clause` + `requirement_element_id` inventory found inside
  `ISO9001_2026_HDF5_Training_Pipeline_v3_1_AUTO_PRODUCTION_APPROVED.zip`
  (`01_master/ISO9001_Master_v3.h5`, `records/clause` and
  `records/requirement_element_id` datasets). **Only the structural
  inventory (IDs and clause boundaries) was reused** — none of that zip's
  AI-generated `question_scenario`/`answer_text`/`nc_severity` content was
  used, because the zip's own embedded metadata says
  `requires_sme_approval: True` / `production_ready: False` and its
  `RELEASE_GATES.csv` states human SME attestation was **not performed**
  (see the `project_openwebui_deployment` session memory for the full
  finding).
- **Requirement text (subject/obligation/object/condition/qualifier)** was
  authored from the real clause text extracted via
  `scripts/extract_clause.py` against
  `assets/standards/ISO_FDIS_9001_2026_en.pdf` — not from any secondhand
  summary. One extraction bug was caught and fixed by hand during
  authoring: `extract_clause.py`'s heading-boundary regex mis-triggered on
  the bare cross-reference "4.1" inside clause 6.1.1's running text,
  truncating it; the correct text was recovered by reading the raw PDF
  page directly.
- Field text is **paraphrased/restructured**, not verbatim reproduction of
  the FDIS draft, consistent with `extract_clause.py`'s own guidance ("for
  verification and short audit criteria... avoid long verbatim
  reproduction") and this repo's copyright constraints on the ISO source
  (`NOTICE.md`).
- **`semantic_category`** (`D2_SAFE` / `M4_MANDATORY` / `AMBIGUOUS`) is
  assigned **programmatically** by `scripts/build_requirement_profiles.py`,
  parsed at generation time directly out of
  `scripts/harness_gate_executor.py`'s `D2_SAFE_LIST` /
  `M4_MANDATORY_LIST` / `AMBIGUOUS_LIST` — never hand-copied. This
  specifically guards against the classification error caught earlier in
  this project's history, where a pasted proposal misclassified clause
  8.5.1 as `D2_SAFE`/Minor-ceiling when the tested harness actually places
  it in `M4_MANDATORY` (Major-candidate). Independently re-verified after
  generation with a second, separate parse of the three lists: **zero
  mismatches**.
- Distribution: 18 clauses `D2_SAFE`, 22 `M4_MANDATORY`, **25 `AMBIGUOUS`**.
  The 25 `AMBIGUOUS` clauses (verified against `_index.json`, the
  authoritative list — do not hand-retype it elsewhere without
  re-checking): 4.3, 4.4.1, 5.1.1, 5.3, 6.1.3, 6.2.1, 6.2.2, 7.1.2, 7.1.4,
  7.1.5.1, 7.1.5.2, 7.5.3.1, 7.5.3.2, 8.1, 8.2.1, 8.2.3.1, 8.3.1, 8.4.1,
  8.4.2, 8.5.2, 8.6, 9.1.3, 9.3.2, 9.3.3, 10.2.2. Only 2 of these (9.1.3,
  10.2.2) are in the harness's explicit `AMBIGUOUS_LIST`; the other 23
  default to `AMBIGUOUS` simply because they appear in neither
  `D2_SAFE_LIST` nor `M4_MANDATORY_LIST`. `AMBIGUOUS` was used as the safe
  default here — it never presumes a Minor ceiling or a Major candidacy
  for a clause the harness hasn't classified — but this is
  `docs/eei-blueprint-crosswalk.md` gap #4 made concrete with real numbers.
  Whether these 25 clauses genuinely belong in "needs deeper check", or
  whether `D2_SAFE_LIST`/`M4_MANDATORY_LIST` in `harness_gate_executor.py`
  should be extended to cover more of them, is an open question for human
  auditor review — not resolved by this dataset.

## Regenerating

`scripts/build_requirement_profiles.py` builds this entire directory from
scratch: it parses `D2_SAFE_LIST`/`M4_MANDATORY_LIST`/`AMBIGUOUS_LIST`
directly out of `harness_gate_executor.py`, holds the per-clause element
decomposition as data, and validates every record against
`scripts/awm_runtime/aias_awm/domain/models.py::AtomicRequirement` before
writing. Re-run it with:

```bash
python scripts/build_requirement_profiles.py
```

If the harness's severity lists change, or the clause text needs revising
once the FDIS draft is superseded by the published IS text, edit the
`CLAUSES` data in that script and re-run it — do not hand-edit the JSON
files directly, since a manual edit would not be re-validated against the
Pydantic schema or re-checked against the harness lists.
