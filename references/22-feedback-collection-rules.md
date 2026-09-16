# Feedback Collection Rules

## Purpose
Collect structured feedback after every material audit response. Feedback drives F1 score computation and identifies which routes, verdicts, and clause groups need improvement.

## What counts as a material response
Any response that includes a verdict (`Complied`, `Noncomplied`, `Major`, `Minor`, `OBS`, `OFI`, `InsufficientEvidence`, `ReferenceGap`, `ReviewRequired`) or that generates an output (checklist, report draft, NC form, AHP scoring result).

Informational, definitional, or out-of-scope responses do not require feedback collection unless the user explicitly rates them.

## Feedback request (post-response dialog)

Append this block at the end of every material response:

```
---
[FEEDBACK] ผลลัพธ์นี้เป็นอย่างไรครับ?
  👍  ถูกต้อง  (พิมพ์ "ถูก" หรือ "correct")
  👎  ไม่ถูกต้อง  (พิมพ์ "ผิด" หรือ "wrong" แล้วระบุว่าควรเป็นอะไร)
  ⚠️  บางส่วนถูก  (พิมพ์ "บางส่วน" หรือ "partial" แล้วอธิบาย)
  ⏭  ข้ามการให้คะแนน  (พิมพ์ "ข้าม" หรือ "skip")
```

## Feedback data model

Each feedback event is stored as one JSON line in `assets/stats/feedback_log.jsonl`:

```json
{
  "session_id": "<hash of conversation start>",
  "timestamp": "<ISO 8601>",
  "route": "<route name>",
  "clause_group": "<top-level clause, e.g. '4', '7', '8.4'>",
  "verdict_given": "<verdict from the AI>",
  "feedback_type": "<correct|wrong|partial|skip>",
  "correction": "<user-supplied correction if wrong/partial, else null>",
  "confidence_given": "<high|medium|low>",
  "evidence_count": "<integer — number of evidence items used>",
  "f1_label": "<TP|FP|FN|TN|skip>",
  "notes": "<free text from user, optional>"
}
```

## F1 label mapping

| Feedback type | AI verdict was positive | AI verdict was negative |
|---|---|---|
| `correct` | TP | TN |
| `wrong` | FP | FN |
| `partial` | Partial (counted as 0.5 TP + 0.5 FP) | n/a |
| `skip` | excluded from F1 computation | excluded |

"Positive verdict" = any of `Noncomplied`, `Major`, `Minor`, `OBS`, `OFI`.
"Negative verdict" = `Complied`, `InsufficientEvidence` (treated as inconclusive, not negative for F1 purposes).

## Correction handling

When the user marks feedback as `wrong` or `partial`, the skill must:

1. Acknowledge the correction: "ขอบคุณครับ — บันทึกการแก้ไขแล้ว"
2. Ask: "ต้องการให้ผมทบทวนและให้คำตอบใหม่โดยอิงจากการแก้ไขนี้ไหมครับ?"
3. If yes: re-run the route with the correction as additional context (treat as user-provided controlled evidence).
4. Do not silently accept the correction and re-issue a verdict as if the first one did not happen. The audit trail must show both verdicts.

## Feedback storage script

```bash
python scripts/feedback_collector.py \
  --session-id "<id>" \
  --route "nc_classification" \
  --clause-group "8.4" \
  --verdict "Major" \
  --feedback-type "wrong" \
  --correction "Should be Minor — only one instance, no systemic failure" \
  --confidence "high" \
  --evidence-count 3
```

The script appends the record to `assets/stats/feedback_log.jsonl` and returns the new cumulative F1 stats for the affected route/clause group.

## Privacy and data governance

Feedback logs are stored locally in `assets/stats/`. They do not leave the controlled skill bundle unless the user explicitly exports them. No personal or client-identifying data should be placed in the `notes` field unless the user is the data controller and has reviewed the content.
