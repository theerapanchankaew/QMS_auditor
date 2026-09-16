# MASCI Org Template Contract — v1.0
> **Upskill module ID:** `qms-org-template-contract-v1`
> **Type:** `output_template_module`
> **Version:** 1.0.0
> **Purpose:** Ensure every MASCI audit report output matches the org-branded format deterministically
> **Applies to route:** `audit_workflow` — all report outputs

---

## Part 1 — MASCI Org Identity Block

Every MASCI audit report output must include the following identity block:

```
Organization:  MASCI (Management System Certification Institute)
Form reference: FP-016-16  Iss.0, Rev.4  6/6/68 SCD
Classification: CONFIDENTIAL
Footer format:  FP-016-16  Iss.0, Rev.4  <date>  |  Page N  |  CONFIDENTIAL
```

---

## Part 2 — Mandatory Report Structure (section order is fixed)

Every MASCI Audit Report output MUST follow this section order exactly.
Model may NOT reorder, rename, or omit sections:

```
Cover:         [Client Name TH] / [Client Name EN]
               Audit Report
               [Audit Date]

Contents:      Section A: Client Information .............. 1
               Section B: Audit summary .................. 2
               Section C: Summary of finding ............. 3
               Section D: Auditor recommendation ......... 5
               Section E: Audit programme ................ 5

               Attachment:
                 - Audit Result
                 - Previous nonconformity report
                 - Nonconformity report
                 - Audit schedule
                 - Certificate confirmation

Section A:     Client Information
               - Client name (TH + EN)
               - Address (TH + EN) | audit mode | site type
               - Audit date
               - Client representatives (name + position)
               - Audit team (name + role)
               - No. of employees in scope
               - Management system applied (table: app no / cert no / expiry / standard / program / application)
               - Certified scope (table: MS / site / scope TH+EN / ISIC/IAF code)
               - Scope appropriateness
               - Audit Objectives (bulleted)
               - Audit criteria and reference documents (bulleted)

Section B:     Audit Summary
               - Nonconformities found (none / count major / count minor)
               - OFI found
               - Deviation from plan
               - Significant changes
               - CA effectiveness from previous audit
               - Certification mark use
               - Unresolved diverging opinions
               - Significant issues for audit programme

Section C:     Summary of Finding
               - Per-category table: category | description | verdict (Effective / Minor NC / Major NC)
               Standard categories: Documentation | Risks and opportunities | Internal audit |
               Management review | Customer complaints | Continual improvement

Section D:     Auditor Recommendation
               - Maintain certification OR follow-up required
               - Per-MS recommendation

Section E:     Audit Programme
               - Audit programme timeline table
               - Clause coverage tables (per standard: QMS / EMS / OHSMS)
               - Signatory block
               - Remark
```

---

## Part 3 — Output Struct (model MUST fill before rendering)

Before generating any audit report output, model fills this struct completely.
Renderer `scripts/org_report_renderer.js` converts struct → branded DOCX.

Required fields: see `assets/schemas/org/masci-audit-report-schema.json`

Mandatory fields at minimum:
- `meta`: form_ref, issue, revision, issue_date
- `section_a`: client_name_th, client_name_en, audit_date, audit_team, management_systems, certified_scope, audit_objectives
- `section_b`: nonconformities_found, num_major_nc, num_minor_nc
- `section_c`: audit_type, findings (min 1)
- `section_d`: recommendation_type, recommendations_by_ms
- `section_e`: audit_programme_rows, signatories

---

## Part 4 — Renderer Command

After model fills struct, run:
```bash
node scripts/org_report_renderer.js <input.json> <output.docx>
```

Or when model produces markdown output for review:
```bash
python scripts/apply_org_template.py --struct <input.json> --format md
```

---

## Part 5 — Format Invariants (deterministic — never change per run)

The following elements are FIXED in every output:
1. Section order: A → B → C → D → E (never reorder)
2. Section heading labels: exact English as specified in Part 2
3. Footer: `FP-016-16  Iss.0, Rev.4  <date>  Page N  CONFIDENTIAL`
4. Signatory block: two-column table with auditor name, role, date
5. Remark: "The audit conclusion is based on a sampling process of the available data during the audit."
6. NC severity colors in Section C: Effective=gray, Minor NC=yellow, Major NC=red
7. MASCI header on every page with client name

---

## Part 6 — SKILL.md Integration

When `audit_workflow` route is selected AND user requests a formal audit report:
1. Load this ref (42) first — before generating any output
2. Fill the struct per Part 3
3. Validate struct against `assets/schemas/org/masci-audit-report-schema.json`
4. Run renderer: `node scripts/org_report_renderer.js struct.json output.docx`
5. Do NOT return raw markdown that bypasses the renderer
6. If struct validation fails (missing required field) → ask user for missing information before generating

Cognition engine rule 25 (added by this module):
"Org-branded output contract — when audit_workflow route produces a formal MASCI audit report,
fill the org_report_struct (ref 42 Part 3), validate against schema, then run the renderer.
Do NOT return free-form markdown as the final report output."
