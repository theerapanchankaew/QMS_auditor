# Verification and Verdict Rules

## Requirement Decomposition
Break each clause into testable requirement elements before deciding. Ask:
1. What must the organization establish, implement, maintain, retain, determine, monitor, evaluate, or improve?
2. What evidence would demonstrate this?
3. Does supplied evidence cover all material elements?

## Canonical Verdicts
- `Complied`: evidence sufficiently demonstrates conformity.
- `Noncomplied`: evidence demonstrates failure to meet a requirement.
- `InsufficientEvidence`: evidence is missing, incomplete, stale, ambiguous, or not objective enough.
- `ReviewRequired`: competent human review is needed due to risk, ambiguity, conflict, sensitivity, or low confidence.

## Confidence Guidance
- 0.90-1.00: strong, direct, current evidence covers all material requirements.
- 0.80-0.89: adequate evidence with minor limitations.
- 0.60-0.79: partial evidence or interpretation needed; consider ReviewRequired.
- below 0.60: do not issue material conformity conclusion; use InsufficientEvidence or ReviewRequired.

## Decision Discipline
Do not use `Complied` when evidence only shows intention, policy, or plan but no implementation where implementation is required. Do not use `Noncomplied` unless a requirement and objective failure are both clear.

## Missing Evidence
Always state the minimum additional evidence needed when verdict is `InsufficientEvidence` or `ReviewRequired`.

## v2 Procedure-Only Decision Rule
If the requirement requires implementation or operation, do not return `Complied` from a procedure alone. Use `InsufficientEvidence` and state the implementation records, samples, logs, observations, or interviews-with-records needed.

## Product Release / Clause 8.6 Decision Rule
For product or service release, missing acceptance results, missing release authorization, unsigned inspection records, shipment before verification, or conflicting release evidence are material issues. Apply enhanced COV. Use `Noncomplied` when objective evidence clearly shows release before required verification. Use `ReviewRequired` when the conflict needs competent technical review.

## Corrective Action Closure Decision Rule
For closure acceptability, test correction, root cause, corrective action, and effectiveness separately. A reminder, retraining statement, or completed correction is not enough unless supported by evidence that the cause was addressed and effectiveness was verified.

## ReviewRequired Examples
Use `ReviewRequired` when:
- product was released or shipped with incomplete release evidence;
- corrective action effectiveness is unclear for a recurring or sensitive issue;
- high-AHP clause evidence is partial and the conclusion materially affects audit outcome;
- evidence conflicts and cannot be resolved from the supplied records;
- the user asks for certification decision rather than audit assistance.


## ISO 9001:2026 Verification Rules

For ISO 9001:2026 conformity evaluation:

1. Identify the exact clause and requirement element.
2. Decide whether the evidence proves intended arrangement, implementation, results, or effectiveness.
3. ISO 9001:2026 (Sixth edition, 2026-09) is published. Exact wording comes from the registered source `assets/standards/ISO_9001_2026.pdf` via `scripts/extract_clause.py` (OCR text layer, hash-bound); cite it as ISO 9001:2026 without a draft caveat. Curated guides and the requirement profiles were first written from FDIS-stage text and re-compared in full against this PDF on 2026-10-05: identical for 58 of 65 clauses, wording differs in 7 (7.3, 7.5.2, 8.1, 8.3.2, 8.5.6, 8.6, 9.2.2 — see `assets/requirement_profiles/README.md`); for those prefer the retrieved PDF text. If a finding depends on a single word of OCR text, return `ReviewRequired` unless the user confirms the wording against their own copy.
4. Verify new/strengthened themes when relevant: climate change relevance, quality culture/ethical behaviour, separated risks and opportunities, strengthened management of change, organizational knowledge, opportunity effectiveness, and evidence protection.
5. Use Annex A only to clarify intent; do not turn Annex A explanatory text into a new requirement.
6. If evidence only shows a procedure, return `InsufficientEvidence` for implementation-heavy clauses unless the user has also provided records, observations, or sample results.
7. For clause 8.6 release issues, missing acceptance evidence or missing release authorization traceability is escalation-sensitive.

## ISO 9001:2026 transition verdicts

For transition assessment, use:
- `Ready for transition evidence review` - criteria are identified but evidence still needs sampling.
- `Transition gap identified` - new or strengthened 2026 theme is not addressed.
- `InsufficientEvidence for transition` - evidence is too limited to judge.
- `ReviewRequired` - certification or accredited transition decision requires authorized review.

Do not state that an organization is certified or fully compliant with ISO 9001:2026 unless the user provides the authorized certification decision basis.

## Full Closed-Loop Verdict Guard

Use `ReferenceGap` when a clause, topic, interpretation, evidence rule, or classification basis is not covered by controlled sources. Do not substitute base training knowledge, web results, or assumptions.

Before issuing a material verdict, confirm the criterion is traceable to a controlled source, the evidence is controlled or user-provided, reasoning does not rely on external knowledge, and the output includes the required knowledge source trace. If not, use `ReferenceGap`, `InsufficientEvidence`, or `ReviewRequired`.

---

## v3.0 — Cognition Engine Integration

The verdict decision tree now operates within the **Layered QMS Audit Cognition Engine** (`references/26-layered-audit-cognition.md`). Updates:

### Requirement element decomposition (MANDATORY at L6)

Before any verdict on a material clause, load the clause profile from `references/27-clause-requirement-profiles.md` and check each requirement element. Document coverage in Clause Element Coverage Map (`references/28-evidence-schema.md` §2).

```
Complied requires:
  ✓ All material requirement elements have objective evidence
  ✓ implementation_proven = true (for 8.3, 8.4, 8.5, 8.6, 8.7, 9.2, 10.2)
  ✓ record_proven = true (for documentation-heavy clauses)
  ✓ Evidence is current (not stale since last significant change)

Cannot return Complied if:
  ✗ Policy/procedure only, for an implementation-heavy clause
  ✗ Auditee verbal claim only
  ✗ Any material element lacks objective evidence
```

### Evidence object construction (L4 — mandatory)

Populate the Evidence Object Schema (`references/28-evidence-schema.md` §1) before reading any evidence for a verdict:
- Separate `auditee_claim` from `objective_evidence`
- Set `implementation_proven` — policy ≠ implementation
- Set `evidence_age` — stale evidence ≠ current conformance
- Set `evidence_covers_all_material_elements` after L6

### Conditional qualifier enforcement (L7 — mandatory)

For clauses with `as applicable` / `as appropriate` / `where applicable` / `to the extent necessary`:
1. Was applicability assessed by the organization?
2. NO assessment AND no objective evidence condition applies → **OFI, STOP.**
3. Assessed not applicable with justification → **Complied, STOP.**
4. Applies → proceed to L8 breach test.

**Common error (failure layer L7):** OFI vs NC confusion arises when this gate is skipped for clauses 8.3, 8.5.5, 8.5.4, 8.5.3, 7.1.5 — keep running L7 for all of them. Note what the text actually contains: only 8.5.4 (`to the extent necessary`), 7.1.5.2 (`as necessary`, under a “when traceability … is a requirement or is considered essential” lead-in) and 8.3.5 / 8.3.6 (`as appropriate` / `to the extent necessary`) carry a qualifier phrase; 8.3 as a whole is conditional through the 4.3 scope determination, and 8.5.3 / 8.5.5 are conditional by circumstance (no customer property / no post-delivery activity). The complete list of qualifier phrases is `references/standard/iso9001-2026-standard-map.md` → “Conditional qualifiers in clauses 4–10”.

### OUT_OF_SCOPE verdict (new — v3.0)

`OUT_OF_SCOPE` is a valid verdict for requests that are outside ISO 9001 / QMS boundary. Do NOT convert wrong-standard requests to `ReviewRequired` — return `OUT_OF_SCOPE` per L2 scope gate.
