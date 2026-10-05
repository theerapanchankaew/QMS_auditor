# ISO 9001:2026 Atomic Requirement Profiles

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
through 10.2.2 of ISO 9001:2026 (the normative body; Annex A excluded).
`standard_id` reads `"ISO 9001:2026"` (the published International
Standard, Sixth edition, 2026-09) as of 2026-09-17 — see "IS cross-check"
below for what that label change is actually based on.

Each clause file also carries a `related_clauses` block (and a resolved
`related_requirement_ids` list of `AR-<clause>-E0N` IDs) — cross-references
to other clauses in this corpus that have a real relationship to it,
because ISO 9001 clauses are not independent: 6.1.1's risk/opportunity
determination feeds 6.1.2/6.1.3, the whole 8.5.x family shares one control
context, management review (9.3.x) explicitly draws on 6.1.x and 9.1.x,
etc. `related_clauses` is attributed by source, not a single opaque list:

- **`siblings`** — other corpus clauses under the same immediate parent
  clause number (e.g. `8.5.2`..`8.5.6` are siblings of `8.5.1`). Purely
  mechanical, derived from clause numbering only.
- **`from_related_clause_map`** — reuses the **existing**
  `references/data/related_clause_map.yaml` (already loaded elsewhere by
  `retrieval_engine.simple_yaml_map` for RAG expansion) rather than
  inventing a second, competing relationship scheme. That file only
  curates ~15 clause-family groups, so most of the 65 clauses get an empty
  list from this source — that is the map's real, current coverage, not a
  bug here.
- **`explicit_text_references`** — clause numbers the real standard text
  cites inline (e.g. clause 6.1.1 literally says "the issues referred to in
  4.1"), extracted from the raw PDF text via `scripts/extract_clause.py`
  at generation time — not from this corpus's own paraphrased
  object/condition fields, which may have dropped an inline citation
  during paraphrasing. One extractor bug was caught and hand-patched for
  this specifically: `extract_clause.py`'s heading-boundary regex
  mis-triggers on clause 6.1.1's inline "4.1" reference (same bug described
  under Provenance below, hand-patched with a cached correct text so
  `6.1.1`'s cross-references are also correct); `6.1.1` is the only one of
  the 65 clauses affected — checked by re-running the extractor against all
  65 and flagging any clause whose text ended mid-sentence or was
  suspiciously short, so this isn't an assumption.
- **`all`** — deduplicated union of the three sources above.

These relations are **not necessarily symmetric** (A referencing B does
not guarantee a generated file for B lists A back) — each is derived
independently from its own text/mapping, by design; forcing symmetry
would have meant inventing relations no source actually states.

`_index.json` lists every clause with its element count and assigned
`semantic_category`.

### `possible_worlds_dimensions` (added 2026-09-21)

Each clause file also carries a `possible_worlds_dimensions` block (and a
`possible_worlds_dimensions_source` note) — the Hartley-measure input
consumed by `scripts/hartley_uncertainty.py` and, when supplied to a
hypothesis, `scripts/awm_runtime`'s planner (see
`references/68-hartley-uncertainty.md` and
`docs/eei-blueprint-crosswalk.md`, "Update 2026-09-21").

**This is mechanically derived, not hand-authored per clause**: one binary
dimension per `mandatory: true` evidence expectation already attached to
that clause's elements (e.g. `"AR-6.1.3-E02_observation": ["YES", "NO"]`),
using the same PRESENT/ABSENT vs YES/NO vocabulary the textbook's own
worked example uses per evidence type. Given the same evidence
expectations, anyone can regenerate the same dimensions — it carries no
additional AI judgement call beyond what was already made when authoring
`evidence_expectations` above. `_index.json` records each clause's
resulting `possible_worlds_dimension_count` and `raw_hartley_bits` (the
full, unconstrained `H(Xt)` before any evidence narrows it).

**Caveat**: this mechanical rule is a first, traceable approximation of a
clause's possible-worlds structure, not an SME-reviewed decomposition. A
human auditor might identify materially different or additional
distinguishing axes for a given clause (the textbook's own worked example
for 6.1.3 — "Implementation? / Effectiveness evaluated? / Objective
record?" — happens to also cardinality-match this corpus's 3 mechanically
derived dimensions for that clause, but the two are not claimed to be the
same axes, only the same count by coincidence).

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
  first authored from the real clause text of the ISO/FDIS 9001:2026 draft
  (extracted with what is now `scripts/extract_clause_legacy.py` against
  `ISO_FDIS_9001_2026_en.pdf`) — not from any secondhand summary. Since
  2026-10-05 the registered source is the published edition,
  `assets/standards/ISO_9001_2026.pdf`, read through
  `scripts/controlled_retrieval.py` (`scripts/extract_clause.py` is a thin
  wrapper over it); the generator's explicit-reference extraction now uses
  that, and the FDIS-vs-IS differences are recorded under "IS cross-check"
  below. (The legacy extractor's 6.1.1 heading-boundary bug no longer
  matters: the registered extractor reads 6.1.1 correctly, so the
  hand-patched 6.1.1 text override was removed from the generator.)
- Field text is **paraphrased/restructured**, not verbatim reproduction of
  the standard's text, consistent with the extractor's own guidance ("for
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

## IS cross-check (full-text, 2026-10-05; supersedes the 2026-09-17 sample)

ISO 9001:2026 (Sixth edition, 2026-09) was published after this corpus was
first authored from the FDIS draft.

**2026-09-17 (superseded)** — the first IS copy supplied was an image-only
scan (`ISO_9001_2026_IS_en_scanned.pdf`, no text layer), so 21 clauses were
sampled by reading rendered page images, and recorded as "word-for-word
identical" to the FDIS. **That conclusion was wrong for three of the
sampled clauses (7.5.2, 8.5.6, 8.6)** — see below — so the sample, the
`IS_CROSS_CHECKED_CLAUSES` list and the per-profile `is_cross_check` text
it produced have been replaced.

**2026-10-05 (current)** — the user supplied `ISO_9001_2026.pdf` (the same
published edition, with an OCR text layer; sha256 `346ce2e9…`), now the
registered source (`assets/manifests/runtime-source-registry.json`,
`scripts/controlled_retrieval.py`). All 65 clauses were compared
automatically: the legacy FDIS extraction vs. the registered IS text,
normalised for whitespace and list markers. Result: **identical for 58
clauses; normative wording differs in 7** (`IS_WORDING_DIFFS` in
`scripts/build_requirement_profiles.py`, echoed in each profile's
`provenance.is_cross_check`):

| Clause | Published IS vs FDIS | Confirmed by |
|---|---|---|
| 7.3 | "not conforming **to**" (FDIS: "with") | OCR text layer only |
| 7.5.2 | "(e.g. a title, date, author, reference number)" — no "or" | IS page image |
| 8.1 | "actions determined in **clause** 6" | OCR text layer only |
| 8.3.2 | list items carry a leading "the" (e.g. "the required process stages") | OCR text layer only |
| 8.5.6 | "continuing conformity **to** requirements" (FDIS: "with") | IS page image |
| 8.6 | "evidence of conformity **to** the acceptance criteria" (FDIS: "with") | IS page image |
| 9.2.2 | NOTE cites "ISO 19011 [4]" (FDIS cited a different bibliography number) | IS page image |

Two further diffs were extractor/footnote artefacts, not wording changes
(6.1.1 — the legacy extractor truncated it; 5.1.1 — a footnote marker).

Effect on this corpus: three element texts quoted a changed phrase and were
updated to the IS wording (**AR-7.3-E01**, **AR-8.5.6-E01**, **AR-8.6-E03**:
"conformity with" → "conformity to"); no element quotes the other four
differences. Regenerating with the registered extractor also added `6.1.3`
to `9.3.2`'s `explicit_text_references` (the legacy extractor missed the
second cross-reference in "…(see 6.1.2)… (see 6.1.3)"). The OCR text layer
is not an accuracy certification (`text_status` in the retrieval output) —
single-word findings should still be confirmed against a licensed copy.

An earlier first pass had also concluded, from the scanned copy's Table of
Contents alone, that 8 clause pairs (e.g. `4.4.1`+`4.4.2`) had been merged in
the published edition; that was wrong (the TOC omits some sub-clause
headings) and was corrected before it was reported — the full-text
comparison confirms all 65 clauses exist with identical numbering.

`SKILL.md` BLOCK 4, `NOTICE.md`, `README.md`, `references/**` and
`assets/manifests/` were updated on 2026-10-05 to name
`ISO_9001_2026.pdf` as the registered source; the FDIS file and the ISO 9000
sources are retained only as `unavailable_historical_sources`.

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

If the harness's severity lists change, or the published wording of any
clause needs to be re-reflected, edit the `CLAUSES` data (and
`IS_WORDING_DIFFS` where a clause's FDIS-vs-IS difference changes) in that
script and re-run it — do not hand-edit the JSON files directly, since a
manual edit would not be re-validated against the Pydantic schema or
re-checked against the harness lists. The generator reads clause text
through `scripts/extract_clause.py` (registered source
`assets/standards/ISO_9001_2026.pdf`), so that PDF must be present locally.
