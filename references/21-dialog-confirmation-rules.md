# Dialog Confirmation Rules

## Purpose
Require explicit user confirmation before the skill takes any action that is:
- Hard to reverse (NC Major classification, CAR closure, formal report generation)
- High-stakes (affects certification status or significant audit findings)
- Potentially consequential if wrong (evidence gap that might mask a systemic failure)

Confirmation is never skipped. Prior consent in the same conversation does not carry forward to a new action instance.

## Trigger matrix

| Action | Confirmation level |
|---|---|
| Classify a finding as **NC Major** | REQUIRED — always |
| Close a corrective action (declare effective) | REQUIRED — always |
| Generate a formal audit report or NC register | REQUIRED — first instance per session |
| Classify a finding as NC Minor | RECOMMENDED — show draft, ask to proceed |
| AHP full evaluation with weighted verdict | RECOMMENDED |
| Clause advisor or checklist generation | NOT REQUIRED |
| Informational / definitional lookup | NOT REQUIRED |

## Confirmation dialog pattern (Thai)

**Pre-action confirmation (REQUIRED tier):**
```
[CONFIRMATION_GATE] action_type: <action>
ผมกำลังจะดำเนินการต่อไปนี้:
  → <description of action and its consequence in one sentence>

ก่อนดำเนินการ ขอให้ยืนยัน:
  ✓ หลักฐานที่ใช้: <brief evidence summary>
  ✓ ข้อกำหนดที่ทดสอบ: <clause reference>
  ✓ ผลที่จะออกมา: <verdict / output type>

พิมพ์ "ยืนยัน" หรือ "confirm" เพื่อดำเนินการ หรือ "แก้ไข" เพื่อปรับก่อน
```

**Pre-action confirmation (RECOMMENDED tier — softer):**
```
[CONFIRMATION_GATE] action_type: <action>
ผมจะ draft <output> โดยอิงจากหลักฐานที่มีอยู่
ถ้าต้องการดำเนินการต่อ พิมพ์ "ดำเนินการ" หรือบอกให้ผมปรับก่อนได้เลยครับ
```

## Post-confirmation behavior

If the user confirms:
- Record `confirmation_given: true` in the output trace.
- Proceed with the action.
- Include confirmation reference in the output's `human_auditor_contract`.

If the user declines or provides corrections:
- Acknowledge the correction.
- Re-run the route with the updated evidence or revised scope.
- Do not treat the declined action as a fault or error — it is a normal part of the audit dialogue.

If no response is received (conversation ends):
- Do not proceed. Treat as `InsufficientEvidence` — the user did not confirm the action.

## Integration with SKILL.md

The confirmation gate is called from `scripts/dialog_confirmation_gate.py`. The gate is invoked after the preflight guard passes and before any high-risk route execution.

```bash
python scripts/dialog_confirmation_gate.py \
  --action "nc_major_classification" \
  --clause "8.4.1" \
  --evidence-summary "Supplier evaluation procedure exists but no evaluation records for 6 of 8 critical suppliers" \
  --verdict-draft "NC Major"
```

The script returns one of:
- `{ "status": "confirmation_required", "dialog": "..." }` — show dialog and stop
- `{ "status": "confirmation_not_required" }` — proceed directly

## Out-of-scope confirmation

The confirmation gate does NOT apply to scope gate rejections or preflight boundary blocks. Those use their own dialog patterns (see `references/20-scope-detection-rules.md` and `references/17-knowledge-boundary-enforcement.md`).
