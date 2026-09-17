# Third-Party Notices

## ISO / IEC standards

This project references and (locally, outside of git) consumes the following
copyrighted works. They are **not** distributed with this repository:

- ISO 9001:2026 (Quality management systems — Requirements) — bundled as
  `ISO_FDIS_9001_2026_en.pdf`, an FDIS-stage text file (still the only
  text-extractable copy, used by `scripts/extract_clause.py`), plus
  `ISO_9001_2026_IS_en_scanned.pdf`, a scanned copy of the actual published
  standard (Sixth edition, 2026-09), added 2026-09-17 to spot-check the
  bundled text against it. Both are copyrighted ISO works regardless of
  draft/published status.
- ISO/FDIS 9000:2026 (Quality management systems — Fundamentals and
  vocabulary) — **not confirmed published**; still treat as draft-stage.
- ISO 9000 glossary (`ISO9000GlossaryENv5FA2025.pdf`)

ISO and IEC hold copyright in these standards. Obtain your own licensed copy
from ISO, your national standards body, or an authorized reseller. Place the
files locally at the paths listed in `SKILL.md` BLOCK 4 and `README.md`;
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
