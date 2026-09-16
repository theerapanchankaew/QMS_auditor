# Deontic Term Precision — Anti-Hallucination Rules

## CRITICAL: shall ≠ ควร

| Term | Thai | Audit Impact |
|------|------|-------------|
| **shall** | **ต้อง** | NC if absent |
| **shall not** | **ห้าม** | NC if present |
| **should** | **ควร** | OFI only |
| **may / can** | **อาจ** | Not auditable |

## Rules
1. NEVER translate "shall" as "ควร" — changes NC to OFI (wrong verdict)
2. Every clause explanation must label: (shall=บังคับ) or (should=แนะนำ)
3. When uncertain → state "ต้องตรวจสอบกับ PDF มาตรฐาน"

## Examples
- Clause 6.3: "shall be carried out" = "ต้องดำเนินการ" (บังคับ) → NC if no evidence
- Clause 6.3 items a-g: "shall consider" = "ต้องพิจารณา" (บังคับ)
