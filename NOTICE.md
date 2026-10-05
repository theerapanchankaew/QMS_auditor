# Third-Party Notices

## ISO / IEC standards

This project references and (locally, outside of git) consumes the following
copyrighted works. They are **not** distributed with this repository:

- ISO 9001:2026 (Quality management systems — Requirements), published Sixth
  edition (2026-09) — `ISO_9001_2026.pdf` (OCR text layer, sha256
  `346ce2e96c9d22caacd747c4ad15030d0931b1b363c68b79f178d385c2ca2565`), the
  single registered source, read through `scripts/controlled_retrieval.py`
  (used by `scripts/extract_clause.py` and `scripts/search_standard.py`; see
  `assets/manifests/runtime-source-registry.json`). Earlier copies this repo
  no longer reads — `ISO_FDIS_9001_2026_en.pdf` (FDIS draft, used only by
  `scripts/extract_clause_legacy.py` for historical comparison) and
  `ISO_9001_2026_IS_en_scanned.pdf` (image-only scan of the same published
  edition) — may still sit locally. All are copyrighted ISO works
  regardless of draft/published status.
- ISO/FDIS 9000:2026 (Fundamentals and vocabulary; **not confirmed
  published**) and the ISO 9000 glossary (`ISO9000GlossaryENv5FA2025.pdf`) —
  historical sources (`unavailable_historical_sources` in
  `assets/manifests/bundled-source-manifest.json`), outside the active
  retrieval boundary.

ISO and IEC hold copyright in these standards. Obtain your own licensed copy
from ISO, your national standards body, or an authorized reseller. Place the
file locally at the path listed in `SKILL.md` BLOCK 4 and `README.md`;
`.gitignore` keeps them out of version control. Do not upload their full text
to a public or shared OpenWebUI Knowledge base — treat any Knowledge
collection built from them as private to this deployment.

## Certification body branding (MASCI)

`references/43-org-template-contract.md` and the `assets/templates/masci-*`
files encode a formal audit report format (section order, footer code
`FP-016-16`, fixed layout) associated with a specific certification body
(MASCI). This format is that organization's intellectual property. Use it
only for its intended internal purpose; do not redistribute or repurpose the
branded template outside that context.
