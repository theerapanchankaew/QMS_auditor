# ISO 9001:2026 Standard Map

Use this file as the first navigation layer before opening or searching the full PDF. It maps likely audit topics to clauses in ISO 9001:2026 and tells the auditor when to verify exact wording from `assets/standards/ISO_9001_2026.pdf` (published Sixth edition, OCR text layer; this map was first written from FDIS-stage text — wording differs in 7.3, 7.5.2, 8.1, 8.3.2, 8.5.6, 8.6, 9.2.2, see `assets/requirement_profiles/README.md`).

## Source hierarchy
1. **Audit workflow and judgement logic**: use `SKILL.md` and references `01` to `16`.
2. **Clause navigation**: use this standard map plus `iso9001-2026-clause-guide.md` and `iso9001-2026-definition-index.md`.
3. **Authoritative full source for exact requirement wording**: use the registered `assets/standards/ISO_9001_2026.pdf` through `scripts/search_standard.py` or `scripts/extract_clause.py`.

## Exact-wording rule
Use the full PDF when the task needs any of the following:
- exact clause wording, subclause wording, note wording, or definition lookup;
- challenge/review of a nonconformity statement;
- disputed interpretation;
- audit criteria quoted in a report;
- clause extraction for checklist, audit criteria, or training material;
- 2015-to-2026 transition comparison involving changed text.

Do not rely only on summary references for certification-critical judgement.

## Clause map

| Clause | Topic | Typical audit intent | Verify exact wording when |
|---|---|---|---|
| 1 | Scope | Applicability, products/services, generic requirements | determining applicability or certification boundary |
| 2 | Normative references | ISO/DIS 9000 terminology dependency | definitions or vocabulary are disputed |
| 3 | Terms and definitions | organization, interested party, QMS, risk, audit, NC, etc. | term meaning affects finding classification |
| 4.1 | Context | internal/external issues; strategic direction; climate change relevance | climate change relevance or context evidence is disputed |
| 4.2 | Interested parties | relevant interested parties, their relevant requirements, addressed through QMS | interested-party requirements affect QMS controls |
| 4.3 | QMS scope | boundaries, applicability, exclusions/not applicable justification | scope claim, exclusions, or certification claim is assessed |
| 4.4 | QMS processes | process inputs/outputs, sequence, criteria, resources, responsibilities, risks/opportunities, evaluation, improvement | evaluating process approach or QMS process map |
| 5.1 | Leadership | accountability, integration, resources, customer focus, quality culture, ethical behaviour, risk/opportunity thinking | leadership failure or culture/ethics evidence is central |
| 5.2 | Quality policy | policy suitability, commitments, communication, implementation | checking policy adequacy or awareness |
| 5.3 | Roles/responsibilities | assigned authorities, QMS conformity, process results, customer focus, change integrity | responsibility gaps or change ownership are cited |
| 6.1 | Risks and opportunities | determine, analyse, evaluate, plan actions for risks and opportunities separately | risk/opportunity planning or proportionality is disputed |
| 6.2 | Quality objectives | measurable, monitored, communicated, documented, planned | objective evidence is weak or contested |
| 6.3 | Planning of changes | planned changes, consequences, QMS integrity, resources, responsibilities, communication, monitoring/review | change management is a finding candidate |
| 7.1 | Resources | people, infrastructure, environment, monitoring/measuring resources, organizational knowledge | resource/control adequacy affects product/service conformity |
| 7.2 | Competence | competence needs, competence basis, actions, effectiveness, evidence | competence evidence is insufficient |
| 7.3 | Awareness | policy, contribution, nonconformity implications, objectives, quality culture/ethical behaviour | interview evidence is used |
| 7.4 | Communication | what/when/with whom/how/who communicates | communication control is a finding candidate |
| 7.5 | Documented information | required and necessary documentation; creation/update; control; external origin; evidence protection | document control or record evidence is central |
| 8.1 | Operational planning and control | process controls, criteria, resources, planned/unplanned changes, external controls | operations evidence or change control is examined |
| 8.2 | Requirements for products/services | customer communication, requirement determination/review/change | contract review/customer requirement issue exists |
| 8.3 | Design and development | planning, inputs, controls, outputs, changes | design evidence is sampled or not applicable is claimed |
| 8.4 | External providers | controls, evaluation, selection, monitoring, communication | supplier/outsourcing finding is considered |
| 8.5 | Production/service provision | controlled conditions, traceability, customer property, preservation, post-delivery, production/service changes | process implementation evidence is sampled |
| 8.6 | Release | planned arrangements, release authorization, acceptance evidence, traceability to releaser | release/shipment/service delivery issue exists |
| 8.7 | Nonconforming outputs | identification, control, correction, containment, concession, evidence | nonconforming output or customer impact exists |
| 9.1 | Monitoring, measurement, analysis, evaluation | what/method/when/analysis/evaluation, customer satisfaction, data analysis | KPIs, customer satisfaction, data analysis are assessed |
| 9.2 | Internal audit | audit programme, criteria, scope, impartiality, reporting, correction/CAPA | audit programme or internal-audit effectiveness is assessed |
| 9.3 | Management review | inputs, trends, resources, risks/opportunities, outputs | management review evidence is sampled |
| 10.1 | Continual improvement | use of monitoring/analysis/review results to determine and address opportunities | improvement evidence is weak |
| 10.2 | Nonconformity and corrective action | reaction, cause, recurrence, implementation, effectiveness, R/O update, QMS changes | CAPA closure or NC classification is assessed |
| Annex A | Clarification | informative clarification of structure, terminology, clauses | interpreting terms like appropriate/applicable/ensure/documented information |

## Search examples
Use scripts from the skill root.

```bash
python scripts/search_standard.py "quality culture ethical behaviour" --max 5
python scripts/extract_clause.py 5.1
python scripts/extract_clause.py 6.1.3   # normative clauses 4-10 only; Annex A is not indexed
```

## Auditor safeguards
- Always distinguish requirement text from explanatory Annex A text.
- Treat Annex A as informative clarification, not additional requirements.
- When citing a clause in audit output, cite the clause number and summarize; avoid long verbatim quotations.
- If the PDF search/extraction and the curated guide conflict, verify against the PDF and flag `ReviewRequired`.
