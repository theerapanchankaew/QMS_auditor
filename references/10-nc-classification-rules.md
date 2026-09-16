# NC Classification Rules

## Labels
Use only: `Major`, `Minor`, `OBS`, `OFI`, `Not NC`.

## Major NC Indicators
Classify as Major when evidence shows systemic failure, absence of a required system element, repeated or widespread failure, failure creating significant risk to intended results, ineffective corrective action for repeated issue, or breakdown affecting product/service conformity.

## Minor NC Indicators
Classify as Minor when there is an isolated lapse, partial implementation failure, limited evidence gap, or localized nonfulfillment that does not indicate systemic breakdown.

## OBS
Use OBS for noteworthy conditions that may become a problem but do not currently demonstrate requirement failure.

## OFI
Use OFI for improvement opportunities where requirements are met but effectiveness, clarity, or efficiency could improve.

## Not NC
Use Not NC when there is no requirement failure, the issue is outside scope, or evidence does not support a nonconformity.

## NC Wording
A strong NC statement includes:
1. Requirement reference.
2. Objective evidence.
3. Clear failure statement.
4. Scope/location/process affected.
5. Avoid blame and unsupported interpretation.

Do not classify as Major solely because a clause is important. Use AHP as a severity sensitivity modifier only.

## v2 Requirement-Breach Test
Before classifying a finding, apply this test:

1. **Requirement** - Identify the ISO clause, organization procedure, contract, legal/regulatory requirement, or audit criterion.
2. **Objective evidence** - Identify records, samples, observations, or traceable interview evidence showing failure or concern.
3. **Nature of issue** - Decide whether it is a requirement breach, potential risk signal, improvement opportunity, or auditor preference.
4. **Extent and impact** - Determine isolated vs systemic, repeated vs one-off, and effect on intended results.
5. **Classification** - Only then classify as Major, Minor, OBS, OFI, or Not NC.

If no requirement breach is established, do not classify as Major or Minor.

## NC vs OBS vs OFI vs Not NC
| Label | Requirement breach? | Objective failure evidence? | Typical use |
|---|---|---|---|
| Major | Yes | Strong/systemic/repeated/high impact | Absence or breakdown of required system element |
| Minor | Yes | Clear but isolated/limited | Local lapse with system mostly functioning |
| OBS | Not yet proven | Risk signal or weak/potential evidence | Follow-up concern that may become NC |
| OFI | No | Requirement met | Improvement to effectiveness, clarity, or efficiency |
| Not NC | No | No relevant failure | Preference, outside scope, or unsupported allegation |

## Auditor Preference Regression Rule
Auditor preference is not a requirement. For example, manual approval is not an NC if the procedure allows manual approval and sampled records show complete signatures and dates. A more modern electronic workflow may be an OFI only if useful, not a nonconformity.

## v2 NC Wording Formula
Use this formula:

```text
Requirement + objective evidence + extent/sample + failure statement + risk/impact where relevant.
```

Pattern:

```text
The organization did not [required action/control], as required by [clause/procedure]. Evidence reviewed showed [sample/record facts]. This indicates [failure statement] and may affect [risk/impact where relevant].
```

Avoid blame language such as “forgot,” “careless,” or “negligent” unless it is a direct quote from evidence and professionally relevant.

---

## v3.0 — Layered Cognition Gate Sequence

NC classification now operates as part of the **Layered QMS Audit Cognition Engine** (`references/26-layered-audit-cognition.md`). Execute gates in order before any classification:

| Gate | Cognition Layer | Rule |
|---|---|---|
| **Gate 1 — Conditional qualifier** | **L7** | OFI if qualifier present and applicability not assessed; proceed if applies |
| **Gate 2 — Requirement breach** | **L8** | All 4 elements required: element + evidence + extent + effect |
| **Gate 3 — Major triggers** | **L9 Q1–Q5** | Name M-trigger from Q1–Q5 or confirm Q6 (none) |
| **Gate 4 — Minor anchors** | **L10 D1–D4** | Assign D-anchor if no M-trigger |
| **Gate 5 — Clause override** | **L10** + ref 25 | Cross-check against `references/25-nc-severity-calibration-guide.md` |
| **Gate 6 — Counterfactual** | **L11** | Challenge before finalizing Major or Minor |
| **Gate 7 — Output** | **L13** | `trigger_or_anchor` + `decisive_question_answered` mandatory |

### QMS Major Triggers (M1–M5) — explicit

| Code | When | Example clause |
|---|---|---|
| **M1** | Product/service conformity exposure — uncontrolled or at risk | 8.4, 8.5, 7.1.5 |
| **M2** | Customer / statutory / regulatory / contract breach | 8.5.5, 7.4, 8.7 |
| **M3** | Release or delivery without required verification; NC output uncontrolled | 8.6, 8.7 |
| **M4** | Entire required system element completely absent | 6.1, 8.3, 9.2, 10.2 |
| **M5** | Same NC recurred after verified CA closure; widespread failure | 10.2, 9.2 |

### QMS Minor Anchors (D1–D4) — explicit

| Code | When |
|---|---|
| **D1** | Documentation/record gap, no conformity exposure |
| **D2** | Process exists but weak or incomplete (not absent) |
| **D3** | Leadership/awareness/competence weakness, no demonstrated system failure |
| **D4** | Isolated single lapse, no pattern or recurrence |

### Decision trace output — mandatory for every NC

```json
{
  "nc_class": "Major | Minor",
  "trigger_or_anchor": "M1–M5 | D1–D4",
  "decisive_question_answered": "<single question controlling severity>"
}
```

### OFI vs Noncomplied enforcement

```
Q: Does the clause contain a conditional qualifier (as applicable / as appropriate / etc.)?
    YES → Run L7.
        IF applicability_not_assessed AND no exposure evidence:
            → OFI. STOP. Do NOT proceed to NC.
        IF applies: → Gate 2.
    NO → Gate 2 directly.
```

**Allowed verdicts (updated — includes OUT_OF_SCOPE):**
`Complied` | `Noncomplied` | `OFI` | `OBS` | `InsufficientEvidence` | `ReviewRequired` | `ReferenceGap` | `OUT_OF_SCOPE` | `Informational`
