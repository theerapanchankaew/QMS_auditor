# Deterministic Harness Specification — v1.0
> **Upskill module ID:** `qms-deterministic-harness-v1`
> **Type:** `harness_engineering_module`
> **Version:** 1.0.0
> **Purpose:** Convert probabilistic rule enforcement → deterministic gate execution
> **Addresses:** Skill drift Type 1 (rule-skip), Type 2 (rule-override), Type 3 (oscillation)
> **Benchmark evidence:** IE Recall = 0.000 across all 4 rounds despite refs 37/39/40

---

## Part 1 — Drift Taxonomy and Root Cause

### Three drift types observed in benchmark

```
Type 1 — Rule-skip drift:
  Model does not execute a gate
  Example: skips IE chain entirely when "ครบถ้วน สอดคล้อง" signal is strong
  Fix: structured output forces model to fill every gate field before verdict is allowed

Type 2 — Rule-override drift:
  Model executes gate but overrides the result with holistic judgment
  Example: G2 IE chain step2 fires → but model returns Complied anyway
  Fix: harness script validates gate output against verdict; rejects contradiction

Type 3 — Oscillation drift:
  Adding more prose rules causes over-correction in opposite direction
  Example: v5.1 under-escalation → v5.2 over-correction after ref 36
  Fix: replace prose rules with lookup tables and hard functions; no more "presume"
```

### Why OFI and Clause never drift

```
OFI: pattern is uniquely discriminating — "ไม่พบ requirement breach + โอกาสปรับปรุง"
     No adjacent verdict shares this pattern → no drift possible
     = deterministic by evidence pattern

Clause: lookup task — evidence contains clause number; model maps it
     No judgment involved → no drift possible
     = deterministic by design

Lesson: deterministic metrics share one property — they require LOOKUP or PATTERN MATCH,
        not JUDGMENT. The harness must convert all judgment gates to lookups.
```

---

## Part 2 — Structured Output Schema (the core enforcement mechanism)

Instead of prose rules that model interprets, the model MUST fill this structured JSON
at inference time. The harness script then validates the struct and enforces gate results.

```json
{
  "gate_execution_trace": {
    "G0_preflight": {
      "closed_source_confirmed": true,
      "scope_confirmed": "ISO 9001:2026 QMS audit"
    },
    "G1_linguistic": {
      "signal_detected": "<exact phrase from evidence>",
      "evidence_activity": "PRESENTED | VERIFIED | PARTIAL | ABSENT"
    },
    "G2_ie_chain": {
      "triggered": true,
      "step2_khropthuean_without_verify": true,
      "step3_yuenyankarn_only": null,
      "step4_stage1_presented": null,
      "chain_result": "InsufficientEvidence | PASS"
    },
    "G3_severity_ceiling": {
      "clause_category": "D2_SAFE | M4_MANDATORY | AMBIGUOUS",
      "verdict_ceiling": "Minor | Major | ReviewRequired"
    },
    "G4_m4_conditions": {
      "A_process_entirely_absent": true,
      "B_zero_records_in_sample": true,
      "C_interview_confirms_absence": true,
      "m4_result": "Major M4 | D2 Minor | ReviewRequired"
    },
    "G5_d_anchor": {
      "d1_triggered": false,
      "d2_triggered": false
    },
    "G6_complied_check": {
      "C1_implementation_proven": false,
      "C2_record_proven": false,
      "C3_elements_covered": false,
      "C4_evidence_current": false,
      "complied_result": "Complied | InsufficientEvidence"
    },
    "G7_trace": {
      "decisive_question": "<single question that controlled the verdict>",
      "calibration_trace": {
        "risk_sensitivity": "<from case>",
        "critical_code_status": "<from case>",
        "evidence_pattern": "absent | incomplete | policy_only | presented_ambiguous | verified",
        "severity_path": "<gate sequence taken>"
      }
    }
  },
  "verdict": "Complied | OFI | Noncomplied | InsufficientEvidence | ReviewRequired",
  "nc_class": "Major | Minor | null",
  "trigger_or_anchor": "M1 | M2 | M3 | M4 | M5 | D1 | D2 | evidence_supports_conformity | insufficient_evidence | ofi",
  "rationale_th": "<Thai rationale referencing clause and evidence>"
}
```

**Enforcement rule:** harness_gate_executor.py validates:
- If G1=PRESENTED AND G2.chain_result=InsufficientEvidence → final verdict MUST be InsufficientEvidence
- If G3.clause_category=D2_SAFE → final nc_class MUST be Minor (not Major)
- If G6.C1=false AND G1=VERIFIED → final verdict MUST NOT be Complied
- If any gate field is null/missing when gate was triggered → quarantine and retry

---

## Part 3 — harness_gate_executor.py Specification

```python
"""
harness_gate_executor.py
Deterministic gate enforcer for QMS audit verdicts.
Inputs: model's structured output JSON (gate_execution_trace + verdict fields)
Outputs: validated verdict OR rejection with enforcement reason
"""

# Gate enforcement rules (Python pseudo-code)

def enforce_gates(model_output: dict) -> dict:
    trace = model_output.get("gate_execution_trace", {})
    verdict = model_output.get("verdict")
    nc_class = model_output.get("nc_class")

    # G1 + G2: IE Hard Stop enforcement
    g1 = trace.get("G1_linguistic", {})
    g2 = trace.get("G2_ie_chain", {})
    if g1.get("evidence_activity") == "PRESENTED":
        if g2.get("step2_khropthuean_without_verify") == True:
            if verdict != "InsufficientEvidence":
                return reject(reason="G2_STEP2_VIOLATION",
                              forced_verdict="InsufficientEvidence",
                              message="ครบถ้วน สอดคล้อง without verification → IE mandatory")
        if g2.get("step4_stage1_presented") == True:
            if verdict != "InsufficientEvidence":
                return reject(reason="G2_STEP4_VIOLATION",
                              forced_verdict="InsufficientEvidence",
                              message="stage_1 + presented → IE mandatory")

    # G3: D2-safe ceiling enforcement
    g3 = trace.get("G3_severity_ceiling", {})
    if g3.get("clause_category") == "D2_SAFE":
        if nc_class == "Major":
            return reject(reason="G3_D2_SAFE_CEILING_VIOLATION",
                          forced_nc_class="Minor",
                          message="D2-safe clause cannot be Major regardless of risk")

    # G4: M4 three-condition enforcement
    g4 = trace.get("G4_m4_conditions", {})
    if g4.get("m4_result") == "Major M4":
        all_three = (g4.get("A_process_entirely_absent") and
                     g4.get("B_zero_records_in_sample") and
                     g4.get("C_interview_confirms_absence"))
        if not all_three:
            return reject(reason="G4_M4_INCOMPLETE_CONDITIONS",
                          forced_result="D2_Minor_or_ReviewRequired",
                          message="M4 requires A AND B AND C; missing condition → Minor D2")

    # G6: Complied pre-conditions enforcement
    g6 = trace.get("G6_complied_check", {})
    if verdict == "Complied":
        if not all([g6.get("C1_implementation_proven"),
                    g6.get("C2_record_proven"),
                    g6.get("C3_elements_covered"),
                    g6.get("C4_evidence_current")]):
            return reject(reason="G6_COMPLIED_PRECONDITION_FAIL",
                          forced_verdict="InsufficientEvidence",
                          message="Complied requires C1+C2+C3+C4; incomplete → IE")

    # G7: Trace completeness check
    g7 = trace.get("G7_trace", {})
    if not g7.get("decisive_question"):
        return reject(reason="G7_TRACE_INCOMPLETE",
                      message="decisive_question is required for every material verdict")

    # All gates passed
    model_output["gate_validation"] = "PASS"
    return model_output


def reject(reason: str, message: str, **overrides) -> dict:
    return {
        "gate_validation": "FAIL",
        "rejection_reason": reason,
        "rejection_message": message,
        "forced_overrides": overrides,
        "action": "retry_with_override OR escalate_to_human_review"
    }
```

---

## Part 4 — Drift Regression Suite (50 cases)

### Coverage design: 5 groups × 10 cases each

```
Group A (10): IE Hard Stop — must return InsufficientEvidence
  - All 21 IE benchmark cases + 10 new variants
  - Coverage: all audit_types, multiple clause risk levels
  - Gate tested: G1=PRESENTED → G2 chain → IE

Group B (10): D2-safe ceiling — must return Minor NOT Major
  - All 18 D2-safe clause variants with high risk + mismatch
  - Gate tested: G3.clause_category=D2_SAFE → ceiling enforced

Group C (10): M4-mandatory stays Major
  - 22 M4_MANDATORY_LIST clauses with all 3 conditions present
  - Gate tested: G4 three-condition → Major confirmed

Group D (10): Complied gate — verified evidence must return Complied
  - Must NOT drift to IE; evidence is genuinely verified
  - Gate tested: G6 C1-C4 all pass → Complied

Group E (10): Boundary confusion cases
  - D1 vs Complied boundary (procedure exists + records weak)
  - OFI vs Minor boundary (no breach + opportunity)
  - ReviewRequired vs Major boundary (ambiguous M-trigger)
```

---

## Part 5 — SKILL.md Prompt Engineering Changes

### Replace "execute these rules" with "fill this struct"

**Current (probabilistic — causes Type 2 drift):**
```markdown
Before returning Complied, confirm C1 implementation_proven...
```

**Replace with (deterministic — forces structured execution):**
```markdown
Before returning any verdict, fill the complete `gate_execution_trace`
struct (ref 41 Part 2). The harness will validate your struct against
the verdict. Contradictions will be rejected and retried.

DO NOT return a verdict without first completing the gate struct.
The struct is not optional — it is the audit reasoning record.
```

### New mandatory output format instruction

Add to "## Output Format Requirements" section:

```markdown
Every material audit verdict (Complied, OFI, Noncomplied, InsufficientEvidence,
ReviewRequired) MUST be returned as the full structured JSON from ref 41 Part 2.
Plain text verdicts without gate_execution_trace will be rejected by
harness_gate_executor.py.

The model's job is to fill the struct truthfully.
The harness's job is to enforce the gates.
These are separate responsibilities that cannot be merged.
```

---

## Part 6 — Implementation Roadmap

```
Phase 1 — Foundation (immediate):
  ├── Write harness_gate_executor.py (ref 41 Part 3)
  ├── Update SKILL.md: add structured output requirement
  ├── Update model_task field in blind testcases to require struct output
  └── Run 10-case smoke test on IE cases (Group A)

Phase 2 — Validation (before v5.5 benchmark):
  ├── Build 50-case drift regression suite (ref 41 Part 4)
  ├── Run full 203-case benchmark with struct output
  ├── Validate harness catches: IE violations, D2-safe violations, M4 violations
  └── Record baseline: gate_validation PASS rate per gate

Phase 3 — Production gate:
  ├── IE recall ≥ 0.80 → gate G2 working
  ├── Major precision ≥ 0.90 → gates G3+G4 working
  ├── Composite F1 ≥ 0.85 → all gates working
  └── Drift detection: compare gate_validation PASS rate across 3 runs → stable = no drift
```

---

## Part 7 — SKILL.md Integration Points

### Add after rule 22 in cognition engine:

```markdown
23. **Structured gate execution required** *(ref 41 Part 2)* — Every material verdict MUST
    be accompanied by a complete `gate_execution_trace` struct. Fill G1–G7 truthfully
    before assigning the final verdict. The harness enforcer (ref 41 Part 3) will validate
    the struct and reject contradictions. This is the primary mechanism against skill drift.

24. **Harness validation contract** *(ref 41 Part 3)* — The model fills the struct;
    harness_gate_executor.py enforces the gates. These are separate responsibilities.
    If the harness rejects an output, the model must retry with corrected gate values,
    not override the harness enforcement.
```

### Add to activation commands (v5.5-DH):

```bash
python scripts/harness_gate_executor.py --validate-schema
python scripts/run_regression_suite.py --cases assets/tests/drift-regression-suite.jsonl
python scripts/run_regression_suite.py --enforce-struct-output --cases assets/tests/qms_synth_v3_blind_testcases.jsonl
```

---

## Part 8 — Release Gate: v5.5-DH (Deterministic Harness)

| Gate | Target | Mechanism |
|---|---|---|
| IE Recall | ≥ 0.80 | G2 Hard Stop cannot be overridden |
| Major Precision | ≥ 0.90 | G3 D2-safe ceiling + G4 three-condition |
| Major Recall | ≥ 0.88 | G4 M4-mandatory still triggers |
| Composite F1 | ≥ 0.85 | All gates working together |
| Gate trace present | 100% | Harness rejects any output without trace |
| Drift regression pass | 50/50 | All drift patterns covered |
| Oscillation check | F1 delta < 0.05 vs v5.4 | No over-correction |
