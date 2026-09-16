# Full AHP Input Model for QMS Document and Evidence Evaluation

## Purpose
Use this reference when the user asks for full AHP input, an AHP scoring model, pairwise criteria, weighted ISO 9001 evaluation, or an audit scoring worksheet for QMS evidence. AHP is a decision-support method for weighting and transparency. It never replaces ISO 9001 requirements, objective evidence, auditor competence, or final certification judgement.

## Required Input Blocks
A full AHP/QMS input should contain these blocks:

1. `objective`: the audit-support decision objective.
2. `evaluation_scale`: the scoring range and score meanings.
3. `criteria`: 4-8 practical criteria with clause focus and scoring meaning.
4. `matrix`: reciprocal pairwise comparison matrix for criteria.
5. `alternatives`: documents, sites, processes, findings, suppliers, risks, or evidence packages to score.
6. `scores`: score per alternative per criterion.
7. `evidence`: traceable evidence rationale per criterion.
8. `required_output_controls`: audit-safe rules for verdict and escalation.

Use `assets/templates/full-ahp-qms-input-template.json` as the default full input skeleton.

## Default ISO 9001 Criteria Set
Use this default criteria set when the user evaluates a quality manual, QMS document package, or evidence package against ISO 9001 and does not provide custom criteria.

| ID | Criterion | Clause focus | Default weight intent |
|---|---|---|---:|
| C1 | Context of organization and QMS scope | 4.1-4.4 | 0.10 |
| C2 | Leadership, policy and roles | 5.1-5.3 | 0.15 |
| C3 | Planning, risk, opportunity and objectives | 6.1-6.3 | 0.15 |
| C4 | Support, resources and documented information | 7.1-7.5 | 0.15 |
| C5 | Operation and service delivery control | 8.1-8.7 | 0.20 |
| C6 | Performance evaluation | 9.1-9.3 | 0.15 |
| C7 | Improvement and corrective action | 10.1-10.3 | 0.10 |

The default weights intentionally give the highest importance to operation controls while keeping leadership, planning, support, and performance evaluation balanced. Replace these with auditor pairwise judgements if the audit objective differs.

## Default Reciprocal Pairwise Matrix
The default matrix below is derived from the default weights and should have near-zero inconsistency. Use it as a stable starter matrix, not as a universal truth.

```json
[
  [1, 0.666667, 0.666667, 0.666667, 0.5, 0.666667, 1],
  [1.5, 1, 1, 1, 0.75, 1, 1.5],
  [1.5, 1, 1, 1, 0.75, 1, 1.5],
  [1.5, 1, 1, 1, 0.75, 1, 1.5],
  [2, 1.333333, 1.333333, 1.333333, 1, 1.333333, 2],
  [1.5, 1, 1, 1, 0.75, 1, 1.5],
  [1, 0.666667, 0.666667, 0.666667, 0.5, 0.666667, 1]
]
```

## Scoring Scale
Use a 0-5 score unless the user supplies another scale.

| Score | Meaning |
|---:|---|
| 0 | no evidence or not addressed |
| 1 | very weak evidence or severe gap |
| 2 | partial evidence with important gaps |
| 3 | adequate evidence with limitations |
| 4 | strong evidence with minor uncertainty |
| 5 | clear, complete, and traceable evidence |

## Weighted Score Bands
These bands support prioritization and readiness discussion only. They do not create automatic conformity verdicts.

| Percent | Decision support |
|---:|---|
| 85-100 | strongly supported conclusion |
| 70-84 | generally supported; check gaps |
| 50-69 | weak or partial support; review required |
| below 50 | not supported or likely gap |

## Consistency Rules
- `CR <= 0.10`: acceptable for decision support.
- `0.10 < CR <= 0.20`: preliminary only; request review for high-risk conclusions.
- `CR > 0.20`: return `ReviewRequired due to inconsistent pairwise judgements` and do not finalize ranking.

## Script Workflow
Use scripts when the user gives a matrix or requests a reproducible calculation.

Run a weights-only AHP calculation:

```bash
python scripts/ahp_calculator.py assets/templates/full-ahp-qms-input-template.json
```

Run full AHP plus weighted scoring:

```bash
python scripts/full_ahp_qms_evaluator.py assets/templates/full-ahp-qms-input-template.json
```

## Output Requirements
For full AHP/QMS evaluation, include:

1. objective and scope;
2. criteria and weights;
3. matrix consistency check: lambda max, CI, RI, CR, status;
4. evidence scoring table;
5. weighted result;
6. audit verdict separated from score;
7. clause and evidence trace;
8. missing evidence and review/escalation note.

## Guardrails
- Do not use an AHP score as proof of conformity or nonconformity.
- Do not classify Major NC or Minor NC from the weighted score alone.
- Do not hide weak evidence behind a high weighted score.
- Treat missing objective evidence as `InsufficientEvidence` or `ReviewRequired` even when the weighted score appears acceptable.
- For high structural-AHP clauses from `references/09-structural-ahp-model.md`, increase evidence strictness and sampling depth.
