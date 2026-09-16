# Structural AHP Model

## Purpose
Use structural AHP weighting to adjust audit priority, evidence strictness, sampling depth, escalation sensitivity, and confidence penalties. Do not use AHP score alone to decide conformity.

## Data File
Use `references/data/iso9001_structural_ahp_model_scored.csv` for clause/node lookup when needed.

The data columns are:
- Node
- Node Title
- ID
- Role
- Description
- Downstream (Structural)
- Score (0-4)

## Treatment Bands
| Score | Treatment |
|---:|---|
| 3.00-4.00 | high structural importance: require stronger evidence, deeper sampling, lower tolerance for evidence gaps |
| 2.00-2.99 | medium-high importance: require clear evidence linkage and explicit risk consideration |
| 1.00-1.99 | standard importance: normal verification and evidence sufficiency rules |
| below 1.00 | supporting/local importance: avoid over-escalation unless other risk triggers exist |

## How to Apply
- Raise sampling depth for higher-scored clauses.
- Penalize confidence more strongly when evidence gaps affect high-scored clauses.
- Trigger COV carefully for high-score clauses.
- Escalate when high structural score combines with conflict, missing evidence, high risk, or sensitive clauses.

## Known High-Impact Examples
- 8.1 Operational planning and control: highest structural control point.
- 4.4.1 QMS establishment, maintenance, and improvement: QMS backbone.
- 6.1.2 Actions to address risks: risk-based thinking anchor.
- 7.2 Competence: process effectiveness enabler.
- 7.4 Communication: requirement transfer and control linkage.

## v2 Explicit AHP Use Pattern
When applying AHP, write the impact explicitly:

```text
Structural AHP consideration: Clause [x] is treated as [band]. This increases evidence strictness and sampling depth. It does not itself determine the verdict.
```

For high-score clauses such as 8.1 and 4.4.1:
- Require implementation records, not only procedures.
- Recommend deeper sampling across relevant processes or records.
- Reduce confidence more strongly when evidence is partial.
- Consider `ReviewRequired` when high structural importance combines with missing evidence, conflict, or high-risk context.

## Boundary Examples
Correct: “Because 8.1 has high structural importance, procedure-only evidence is insufficient and additional production control records are needed.”

Incorrect: “Because 8.1 has a high AHP score, the process is nonconforming.”
