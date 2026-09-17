# -*- coding: utf-8 -*-
"""Generate AtomicRequirement JSON records for all ISO 9001:2026 clauses
covered by the repo's existing 65-clause / 155-element checklist (derived
structurally from the zip inventory; NOT its AI-generated scenario/label
content, which is excluded per the earlier no-SME-attestation finding).

Field values (subject/obligation/object/condition/qualifier) were originally
authored from the ISO/FDIS 9001:2026 draft PDF text extracted via
scripts/extract_clause.py, then cross-checked against the published IS
(assets/standards/ISO_9001_2026_IS_en_scanned.pdf -- a scanned, no-text-
layer copy of the actual ISO 9001:2026 Sixth edition, 2026-09) by visually
reading its page images. Every clause sampled in that check (4.1, 4.3, 4.4,
5.2, 5.3, 6.1.1-6.1.3, 6.2.1, 7.1.3-7.1.6, 7.5.1-7.5.3.2, 8.5.6-8.7.2) came
back word-for-word identical, with identical clause numbering -- so
extract_clause.py's original FDIS extraction remains the functional source
of truth (the IS scan has no text layer and cannot be parsed by that
script), and STANDARD_ID below was updated to drop "FDIS" now that the
standard is published. This was a SAMPLE, not an exhaustive page-by-page
re-verification of all 65 clauses against the IS scan -- flag it for a
fuller check if any specific clause's wording is ever in doubt.

semantic_category is assigned programmatically from the exact D2_SAFE_LIST
/ M4_MANDATORY_LIST / AMBIGUOUS_LIST parsed directly out of
scripts/harness_gate_executor.py -- never hand-copied -- to avoid the exact
classification error caught earlier in this session (the dismissed
proposal misclassified 8.5.1).

Status: AI-drafted. NOT SME/human-auditor reviewed. Do not treat as
certified interpretation; do not present as final until a qualified
auditor signs off, exactly per this repo's own governance stance.

Cross-references: each clause file also carries a `related_clauses` block
built from three sources, all attributed so the basis for each relation is
visible rather than opaque:
  - "siblings"            -- other corpus clauses sharing the same
                             immediate parent clause number (e.g. 8.5.2 is
                             a sibling of 8.5.1); purely mechanical.
  - "from_related_clause_map" -- reuses the EXISTING, already-curated
                             references/data/related_clause_map.yaml (the
                             file the retrieval engine already loads via
                             retrieval_engine.simple_yaml_map) rather than
                             inventing a second relationship scheme.
  - "explicit_text_references" -- clause numbers the real standard text
                             cites inline (e.g. clause 6.1.1 explicitly
                             says "the issues referred to in 4.1"),
                             re-extracted from the raw PDF text via
                             scripts/extract_clause.py at generation time
                             (not from this script's own paraphrased
                             object/condition text, which may have dropped
                             an inline citation during paraphrasing).
This lives OUTSIDE each AtomicRequirement record (sibling to the
"requirements" list in each clause file), not as a new field on
AtomicRequirement itself -- extending that Pydantic model would also
require updating scripts/awm_runtime/schemas/AtomicRequirement.schema.json
(additionalProperties: false) and the atomic_requirements SQL table/
SQLAlchemy Table in persistence/tables.py, none of which anything in this
repo currently populates from this corpus. Keeping cross-references at the
file level avoids that migration for a field nothing yet consumes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PY = REPO_ROOT / "scripts" / "harness_gate_executor.py"
RELATED_CLAUSE_MAP_YAML = REPO_ROOT / "references" / "data" / "related_clause_map.yaml"
OUT_DIR = REPO_ROOT / "assets" / "requirement_profiles"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from retrieval_engine import simple_yaml_map  # noqa: E402  (reuse existing parser)

STANDARD_ID = "ISO 9001:2026"
VERSION = "0.2.0-ai-draft-unreviewed"

# Clauses whose IS body text was directly visually compared (page images of
# assets/standards/ISO_9001_2026_IS_en_scanned.pdf, which has no text layer
# for automated re-extraction) against this script's FDIS-sourced text, and
# found word-for-word identical with identical numbering. A SAMPLE across
# clauses 4-8, not all 65 -- see the module docstring and
# assets/requirement_profiles/README.md.
IS_CROSS_CHECKED_CLAUSES = {
    "4.1", "4.3", "4.4.1", "4.4.2", "5.2.1", "5.2.2", "5.3",
    "6.1.1", "6.1.2", "6.1.3", "6.2.1",
    "7.1.3", "7.1.4", "7.1.5.1", "7.1.5.2",
    "7.5.1", "7.5.2", "7.5.3.1", "7.5.3.2",
    "8.5.6", "8.6", "8.7.1", "8.7.2",
}

# ---------------------------------------------------------------------------
# Parse the canonical severity-ceiling lists directly out of the harness file
# ---------------------------------------------------------------------------

def parse_clause_set(py_text: str, var_name: str) -> set[str]:
    m = re.search(rf"{var_name}\s*=\s*\{{(.*?)\}}", py_text, re.S)
    if not m:
        raise SystemExit(f"Could not find {var_name} in harness_gate_executor.py")
    body = m.group(1)
    return set(re.findall(r"'([\d.]+)'", body))


harness_text = HARNESS_PY.read_text(encoding="utf-8")
D2_SAFE_LIST = parse_clause_set(harness_text, "D2_SAFE_LIST")
M4_MANDATORY_LIST = parse_clause_set(harness_text, "M4_MANDATORY_LIST")
AMBIGUOUS_LIST = parse_clause_set(harness_text, "AMBIGUOUS_LIST")

assert "8.5.1" in M4_MANDATORY_LIST and "8.5.1" not in D2_SAFE_LIST
assert "4.1" in D2_SAFE_LIST


def semantic_category_for(clause: str) -> str:
    if clause in D2_SAFE_LIST:
        return "D2_SAFE"
    if clause in M4_MANDATORY_LIST:
        return "M4_MANDATORY"
    # AMBIGUOUS_LIST is explicit for {'9.1.3','10.2.2'}; every other clause
    # not in the two lists above also defaults to AMBIGUOUS (safe fallback:
    # never invents a Minor-ceiling or Major-candidate presumption for a
    # clause the tested harness has not classified).
    return "AMBIGUOUS"


# ---------------------------------------------------------------------------
# Evidence expectation presets (reused across elements, not per-element bespoke)
# ---------------------------------------------------------------------------

def doc_info(mandatory: bool = True):
    return [{"evidence_type": "document", "minimum_strength": "documented", "mandatory": mandatory}]


def record(mandatory: bool = True):
    return [{"evidence_type": "record", "minimum_strength": "recorded", "mandatory": mandatory}]


def implementation(mandatory: bool = True):
    return [{"evidence_type": "observation", "minimum_strength": "implemented", "mandatory": mandatory}]


def default_mixed():
    return [
        {"evidence_type": "document", "minimum_strength": "documented", "mandatory": False},
        {"evidence_type": "observation", "minimum_strength": "implemented", "mandatory": True},
    ]


def record_and_doc():
    return [
        {"evidence_type": "record", "minimum_strength": "recorded", "mandatory": True},
        {"evidence_type": "document", "minimum_strength": "documented", "mandatory": True},
    ]


def elem(suffix, subject, obligation, obj, condition=None, qualifier=None,
         evidence=None, failure=None, neg=None):
    return {
        "suffix": suffix,
        "subject": subject,
        "obligation": obligation,
        "object": obj,
        "condition": condition,
        "qualifier": qualifier,
        "evidence": evidence if evidence is not None else default_mixed(),
        "failure": failure or [],
        "neg": neg or [],
    }


ORG = "organization"
TOPMGMT = "top management"

# ---------------------------------------------------------------------------
# Clause data -- element decomposition authored from the real FDIS text
# extracted in this session (scripts/extract_clause.py output), respecting
# the exact per-clause element counts from the zip's structural checklist.
# ---------------------------------------------------------------------------

CLAUSES = [
    ("4.1", "Understanding the organization and its context", [
        elem("E01", ORG, "determine", "external and internal issues that are relevant to the organization's purpose and strategic direction and that affect its ability to achieve the intended result(s) of its quality management system",
             failure=["no evidence of any documented context analysis"], neg=["context analysis mentioned only verbally with no record"]),
        elem("E02", ORG, "determine", "whether climate change is a relevant issue"),
        elem("E03", ORG, "monitor and review", "information about the external and internal issues determined under this clause",
             evidence=record(), failure=["context issues determined once and never revisited"]),
    ]),
    ("4.2", "Understanding the needs and expectations of interested parties", [
        elem("E01", ORG, "determine", "the interested parties that are relevant to the quality management system"),
        elem("E02", ORG, "determine", "the relevant requirements of these interested parties"),
        elem("E03", ORG, "determine", "which of these requirements will be addressed through the quality management system"),
        elem("E04", ORG, "monitor and review", "information about these interested parties", evidence=record()),
        elem("E05", ORG, "monitor and review", "the relevant requirements of these interested parties", evidence=record()),
    ]),
    ("4.3", "Determining the scope of the quality management system", [
        elem("E01", ORG, "determine", "the boundaries and applicability of the quality management system to establish its scope"),
        elem("E02", ORG, "consider", "the external and internal issues referred to in 4.1", condition="when determining the scope"),
        elem("E03", ORG, "consider", "the requirements referred to in 4.2", condition="when determining the scope"),
        elem("E04", ORG, "consider", "the products and services of the organization", condition="when determining the scope"),
        elem("E05", ORG, "apply", "all the requirements of this document", condition="if applicable within the determined scope of the quality management system"),
        elem("E06", ORG, "ensure the scope states", "the types of products and services covered", evidence=doc_info()),
        elem("E07", ORG, "ensure the scope includes", "justification for any requirement of this document that the organization determines is not applicable to its quality management system", evidence=doc_info(),
             neg=["exclusion claimed without any stated justification"]),
        elem("E08", ORG, "ensure the scope is available", "as documented information", evidence=doc_info(mandatory=True)),
        elem("E09", ORG, "ensure", "that requirements determined as not applicable do not affect the organization's ability or responsibility to ensure conformity of products and services and the enhancement of customer satisfaction",
             qualifier="precondition for claiming conformity to this document",
             failure=["scope excludes a requirement that materially affects conformity or customer satisfaction"]),
    ]),
    ("4.4.1", "Quality management system and its processes", [
        elem("E01", ORG, "establish and implement", "a quality management system, including the processes needed and their interactions, in accordance with the requirements of this document"),
        elem("E02", ORG, "maintain and continually improve", "the quality management system, including the processes needed and their interactions"),
        elem("E03", ORG, "determine", "the processes needed for the quality management system and their application throughout the organization"),
        elem("E04", ORG, "determine", "the inputs required and the outputs expected from these processes"),
        elem("E05", ORG, "determine", "the sequence and interaction of these processes"),
        elem("E06", ORG, "determine and apply", "the criteria and methods needed (including monitoring, measurements and related performance indicators) to ensure the effective operation and control of these processes"),
        elem("E07", ORG, "determine", "the resources needed for these processes and ensure their availability"),
        elem("E08", ORG, "assign", "the responsibilities and authorities for these processes"),
        elem("E09", ORG, "address", "the risks and opportunities as determined in accordance with the requirements of 6.1"),
        elem("E10", ORG, "evaluate and implement changes to", "these processes to ensure that they achieve their intended results"),
        elem("E11", ORG, "improve", "the processes and the quality management system"),
    ]),
    ("4.4.2", "Documented information supporting QMS processes", [
        elem("E01", ORG, "ensure", "documented information is available to the extent necessary", evidence=doc_info()),
        elem("E02", ORG, "ensure documented information supports", "the operation of the organization's processes", evidence=doc_info()),
        elem("E03", ORG, "ensure documented information provides evidence", "that the processes are being carried out as planned", evidence=record()),
    ]),
    ("5.1.1", "General (leadership and commitment)", [
        elem("E01", TOPMGMT, "demonstrate", "leadership and commitment with respect to the quality management system"),
        elem("E02", TOPMGMT, "ensure", "the quality policy and quality objectives are established and are compatible with the strategic direction of the organization"),
        elem("E03", TOPMGMT, "ensure", "the integration of the quality management system requirements into the organization's business processes"),
        elem("E04", TOPMGMT, "ensure", "the resources needed for the quality management system are available"),
        elem("E05", TOPMGMT, "communicate", "the importance of effective quality management and of conforming to the quality management system requirements"),
        elem("E06", TOPMGMT, "ensure", "the quality management system achieves its intended result(s)"),
        elem("E07", TOPMGMT, "direct and support", "persons to contribute to the effectiveness of the quality management system"),
        elem("E08", TOPMGMT, "promote", "continual improvement"),
        elem("E09", TOPMGMT, "support", "other relevant roles to demonstrate their leadership, as it applies to their areas of responsibility"),
        elem("E10", TOPMGMT, "promote", "quality culture and ethical behaviour"),
        elem("E11", TOPMGMT, "promote", "the use of the process approach"),
        elem("E12", TOPMGMT, "promote", "risk-based thinking and opportunity-based thinking"),
        elem("E13", TOPMGMT, "take accountability for", "the effectiveness of the quality management system"),
    ]),
    ("5.1.2", "Customer focus", [
        elem("E01", TOPMGMT, "demonstrate", "leadership and commitment with respect to customer focus"),
        elem("E02", TOPMGMT, "ensure", "customer and applicable statutory and regulatory requirements are determined, understood and consistently met"),
        elem("E03", TOPMGMT, "ensure", "the risks and opportunities that can affect conformity of products and services and the ability to enhance customer satisfaction are determined and addressed"),
        elem("E04", TOPMGMT, "ensure", "the focus on enhancing customer satisfaction is maintained"),
    ]),
    ("5.2.1", "Establishing the quality policy", [
        elem("E01", TOPMGMT, "establish", "a quality policy"),
        elem("E02", TOPMGMT, "ensure the quality policy is", "appropriate to the purpose of the organization"),
        elem("E03", TOPMGMT, "ensure the quality policy provides", "a framework for setting quality objectives"),
        elem("E04", TOPMGMT, "ensure the quality policy includes", "a commitment to meet applicable requirements"),
        elem("E05", TOPMGMT, "ensure the quality policy includes", "a commitment to continual improvement of the quality management system"),
        elem("E06", TOPMGMT, "ensure the quality policy takes into account", "the context of the organization and supports its strategic direction"),
    ]),
    ("5.2.2", "Communicating the quality policy", [
        elem("E01", ORG, "ensure the quality policy is available", "as documented information", evidence=doc_info()),
        elem("E02", ORG, "ensure the quality policy is communicated", "within the organization"),
        elem("E03", ORG, "ensure the quality policy is available", "to interested parties", qualifier="as appropriate"),
        elem("E04", ORG, "ensure the quality policy is implemented and applied", "within the organization", evidence=implementation()),
        elem("E05", ORG, "ensure the quality policy is understood", "within the organization", evidence=implementation()),
    ]),
    ("5.3", "Roles, responsibilities and authorities", [
        elem("E01", TOPMGMT, "ensure", "the responsibilities and authorities for relevant roles are assigned within the organization"),
        elem("E02", TOPMGMT, "ensure", "the responsibilities and authorities for relevant roles are communicated within the organization"),
        elem("E03", TOPMGMT, "assign responsibility and authority for", "ensuring that the quality management system conforms to the requirements of this document"),
        elem("E04", TOPMGMT, "assign responsibility and authority for", "reporting on the performance of the quality management system to top management"),
        elem("E05", TOPMGMT, "assign responsibility and authority for", "ensuring that the processes are delivering their intended results"),
        elem("E06", TOPMGMT, "assign responsibility and authority for", "ensuring the promotion of customer focus throughout the organization"),
        elem("E07", TOPMGMT, "assign responsibility and authority for", "reporting on opportunities for improvement to top management"),
        elem("E08", TOPMGMT, "assign responsibility and authority for", "ensuring that the integrity of the quality management system is maintained including when changes to it are planned and implemented"),
    ]),
    ("6.1.1", "Determining risks and opportunities", [
        elem("E01", ORG, "consider", "the issues referred to in 4.1", condition="when planning for the quality management system"),
        elem("E02", ORG, "consider", "the requirements referred to in 4.2", condition="when planning for the quality management system"),
        elem("E03", ORG, "determine risks and opportunities to", "give assurance that the quality management system can achieve its intended result(s)"),
        elem("E04", ORG, "determine risks and opportunities to", "prevent or reduce undesired effects and to achieve continual improvement"),
        elem("E05", ORG, "determine risks and opportunities to", "enhance desired effects"),
    ]),
    ("6.1.2", "Actions to address risks", [
        elem("E01", ORG, "determine, analyse and evaluate", "risks that can have an undesired effect on its ability to continually and consistently provide conforming products and services and enhance customer satisfaction"),
        elem("E02", ORG, "plan", "actions to address these risks"),
        elem("E03", ORG, "plan how to integrate and implement", "the actions into its quality management system processes"),
        elem("E04", ORG, "plan how to evaluate", "the effectiveness of these actions"),
        elem("E05", ORG, "ensure actions taken are proportionate to", "the potential impact of the risks on the intended results of the quality management system",
             neg=["disproportionately heavy action taken for a low-impact risk, or none taken for a high-impact one"]),
    ]),
    ("6.1.3", "Actions to address opportunities", [
        elem("E01", ORG, "determine, analyse and evaluate", "opportunities that can have a desired effect on its ability to continually and consistently provide conforming products and services and enhance customer satisfaction"),
        elem("E02", ORG, "plan", "actions to address these opportunities, including how to integrate and implement them into its quality management system processes and how to evaluate their effectiveness"),
        elem("E03", ORG, "ensure actions taken are appropriate to", "the organization's context and support the achievement of desired results"),
    ]),
    ("6.2.1", "Quality objectives", [
        elem("E01", ORG, "establish", "quality objectives at relevant functions, levels and processes"),
        elem("E02", ORG, "ensure quality objectives are", "consistent with the quality policy, measurable, take into account applicable requirements, monitored, communicated, updated as appropriate, available as documented information, and relevant to conformity of products and services and the ability to enhance customer satisfaction",
             evidence=doc_info()),
    ]),
    ("6.2.2", "Planning to achieve quality objectives", [
        elem("E01", ORG, "determine", "what will be done, what resources will be required, who will be responsible, when it will be completed, and how the results will be evaluated",
             condition="when planning how to achieve its quality objectives"),
    ]),
    ("6.3", "Planning of changes", [
        elem("E01", ORG, "carry out", "changes to the quality management system in a planned manner", condition="when the organization determines the need for changes to the quality management system"),
        elem("E02", ORG, "consider", "the purpose of the changes and their potential consequences, the potential impact on QMS integrity, resource and information availability, allocation or reallocation of responsibilities and authorities, communication of the changes, how effectiveness will be monitored and evaluated, and how results will be reviewed",
             condition="to ensure changes are implemented effectively to achieve intended results"),
    ]),
    ("7.1.1", "Resources - General", [
        elem("E01", ORG, "determine and provide", "the resources needed for the establishment, implementation, maintenance and continual improvement of the quality management system"),
        elem("E02", ORG, "consider", "the capabilities of, and constraints on, existing internal resources, and what needs to be obtained from external providers"),
    ]),
    ("7.1.2", "People", [
        elem("E01", ORG, "determine and provide", "the persons necessary for the effective implementation of its quality management system and for the operation and control of its processes"),
    ]),
    ("7.1.3", "Infrastructure", [
        elem("E01", ORG, "determine, provide and maintain", "the infrastructure necessary for the operation of its processes and to achieve conformity of products and services",
             failure=["infrastructure gap causes a nonconforming output but is never addressed"]),
    ]),
    ("7.1.4", "Environment for the operation of processes", [
        elem("E01", ORG, "determine, provide and maintain", "the environment necessary for the operation of its processes and to achieve conformity of products and services"),
    ]),
    ("7.1.5.1", "Monitoring and measuring resources - General", [
        elem("E01", ORG, "determine and provide", "the resources needed to ensure valid and reliable results", condition="when monitoring or measuring is used to verify the conformity of products and services to requirements"),
        elem("E02", ORG, "ensure resources provided are", "suitable for the specific type of monitoring and measurement activities being undertaken and maintained to ensure their continuing fitness for purpose"),
        elem("E03", ORG, "ensure documented information is available", "as evidence of fitness for purpose of the monitoring and measurement resources", evidence=doc_info()),
    ]),
    ("7.1.5.2", "Traceability of measurement results", [
        elem("E01", ORG, "ensure measuring equipment is", "calibrated or verified at specified intervals or prior to use against traceable measurement standards, identified to determine calibration/verification status, and safeguarded from adjustments, damage or deterioration",
             condition="when traceability of measurement results is a requirement or is considered essential for confidence in measurement validity",
             evidence=record()),
        elem("E02", ORG, "determine whether validity of previous measurement results has been adversely affected and take appropriate action", "as necessary", condition="when measuring equipment is found to be unfit for its intended purpose"),
    ]),
    ("7.1.6", "Organizational knowledge", [
        elem("E01", ORG, "determine", "the knowledge necessary for the operation of its processes and to achieve the intended results of its quality management system"),
        elem("E02", ORG, "retain, apply and share", "this knowledge to the extent necessary"),
        elem("E03", ORG, "consider its current knowledge and determine how to acquire or access", "any necessary additional knowledge and required updates", condition="when addressing changing needs and trends"),
    ]),
    ("7.2", "Competence", [
        elem("E01", ORG, "determine the necessary competence of, and ensure the competence of,", "person(s) doing work under its control that affects its quality management system performance, on the basis of appropriate education, training, or experience"),
        elem("E02", ORG, "take actions to acquire the necessary competence and evaluate their effectiveness, and ensure documented information is available", "as evidence of competence", qualifier="where applicable", evidence=doc_info()),
    ]),
    ("7.3", "Awareness", [
        elem("E01", ORG, "ensure", "persons doing work under the organization's control are aware of the quality policy, their contribution to QMS effectiveness, the implications of not conforming with QMS requirements, relevant quality objectives, and the organizational quality culture and ethical behaviour"),
    ]),
    ("7.4", "Communication", [
        elem("E01", ORG, "determine", "the internal and external communications relevant to the quality management system, including what, when, with whom, how and who communicates"),
    ]),
    ("7.5.1", "Documented information - General", [
        elem("E01", ORG, "ensure the quality management system includes", "documented information required by this document and documented information determined by the organization as necessary for the effectiveness of the quality management system", evidence=doc_info()),
    ]),
    ("7.5.2", "Creating and updating documented information", [
        elem("E01", ORG, "ensure appropriate", "identification and description, format and media, and review and approval for suitability and adequacy", condition="when creating and updating documented information"),
    ]),
    ("7.5.3.1", "Control of documented information - General", [
        elem("E01", ORG, "control documented information required by the quality management system and by this document to ensure", "it is available and suitable for use, where and when needed, and adequately protected"),
    ]),
    ("7.5.3.2", "Control of documented information - activities", [
        elem("E01", ORG, "address", "distribution/access/retrieval/use, storage and preservation, control of changes, and retention and disposition, as applicable, for the control of documented information", qualifier="as applicable"),
        elem("E02", ORG, "identify and control", "documented information of external origin determined by the organization to be necessary for the planning and operation of the quality management system", qualifier="as appropriate"),
        elem("E03", ORG, "protect", "documented information available as evidence of conformity from unintended alterations"),
    ]),
    ("8.1", "Operational planning and control", [
        elem("E01", ORG, "plan, implement and control", "the processes needed to meet requirements for the provision of products and services and to implement the actions determined in clause 6, by determining product/service requirements, establishing acceptance and process criteria, implementing process control, and determining needed resources"),
        elem("E02", ORG, "ensure documented information is available", "to the extent necessary to have confidence that the processes have been carried out as planned", evidence=doc_info()),
        elem("E03", ORG, "control planned changes and review the consequences of unintended changes, taking action to mitigate any adverse effects", "as necessary"),
        elem("E04", ORG, "ensure", "externally provided processes, products or services that are relevant to the quality management system are controlled"),
        elem("E05", ORG, "ensure documented information is available", "to the extent necessary as evidence of the conformity of products and services", evidence=record()),
    ]),
    ("8.2.1", "Customer communication", [
        elem("E01", ORG, "ensure communication with customers includes", "providing product/service information, handling enquiries/contracts/orders including changes, obtaining customer feedback including complaints, handling or controlling customer property, and providing contingency-related information when relevant"),
    ]),
    ("8.2.2", "Determining requirements for products and services", [
        elem("E01", ORG, "ensure", "the requirements for the products and services are defined, including applicable statutory and regulatory requirements and those considered necessary by the organization, and that it can meet the claims it makes for them",
             condition="when determining the requirements for the products and services to be offered to customers"),
    ]),
    ("8.2.3.1", "Review of requirements for products and services", [
        elem("E01", ORG, "ensure it has the ability to meet requirements and conduct a review covering customer-defined requirements, requirements not defined by the customer but necessary for intended use, organization-specified requirements, statutory and regulatory requirements, and differing contract or order requirements; resolve any differing requirements; and confirm customer requirements when not documented by the customer", "before committing to supply products and services to a customer",
             condition="before committing to supply products and services to a customer"),
    ]),
    ("8.2.3.2", "Documented information on review of requirements", [
        elem("E01", ORG, "ensure documented information is available", "as evidence of the results of the review and of any new or changed requirements for the products and services", qualifier="as applicable", evidence=doc_info()),
    ]),
    ("8.2.4", "Changes to requirements for products and services", [
        elem("E01", ORG, "ensure", "relevant documented information is updated and communicated to relevant interested parties", condition="when requirements for products and services are changed", evidence=doc_info()),
    ]),
    ("8.3.1", "Design and development - General", [
        elem("E01", ORG, "establish, implement and maintain", "a design and development process that is appropriate to ensure the subsequent provision of products and services"),
    ]),
    ("8.3.2", "Design and development planning", [
        elem("E01", ORG, "consider", "nature/duration/complexity, required process stages and reviews, verification and validation activities, responsibilities and authorities, resource needs, interface control, involvement of customers and interested parties, requirements for subsequent provision, expected level of control, and documented information needed as evidence",
             condition="when determining the stages and controls for design and development"),
    ]),
    ("8.3.3", "Design and development inputs", [
        elem("E01", ORG, "determine requirements essential for the products and services to be designed and developed, considering functional/performance requirements, information from previous similar activities, statutory and regulatory requirements, and applicable standards or codes; ensure inputs are complete, unambiguous and adequate; resolve conflicting inputs; and ensure documented information is available", "as evidence of design and development inputs",
             evidence=doc_info()),
    ]),
    ("8.3.4", "Design and development controls", [
        elem("E01", ORG, "apply controls to the design and development process to ensure that", "results to be achieved are defined, reviews are conducted, verification and validation activities are conducted, necessary actions are taken on problems found, and documented information is available as evidence of these activities",
             evidence=doc_info()),
    ]),
    ("8.3.5", "Design and development outputs", [
        elem("E01", ORG, "ensure design and development outputs meet input requirements, are adequate for subsequent processes, include or reference monitoring/measuring requirements and acceptance criteria, and specify essential product/service characteristics; ensure documented information is available", "as evidence of design and development outputs",
             evidence=doc_info()),
    ]),
    ("8.3.6", "Design and development changes", [
        elem("E01", ORG, "determine, review and control", "changes made during or subsequent to the design and development of products and services, to the extent necessary to ensure no adverse impact on conformity to requirements; ensure documented information is available as evidence of the changes, review results, authorization, and preventive actions taken",
             evidence=doc_info()),
    ]),
    ("8.4.1", "Control of externally provided processes, products and services - General", [
        elem("E01", ORG, "ensure externally provided processes, products and services conform to requirements; determine the controls to apply when incorporation, direct provision, or process outsourcing applies; determine and apply criteria for evaluation, selection, monitoring and re-evaluation of external providers; and ensure documented information is available", "as evidence of these activities and any necessary actions arising from the evaluations",
             evidence=doc_info()),
    ]),
    ("8.4.2", "Type and extent of control", [
        elem("E01", ORG, "ensure externally provided processes, products and services do not adversely affect its ability to consistently deliver conforming products and services, by ensuring externally provided processes are within QMS control, defining controls applied to the provider and to the resulting output, taking into account potential impact and control effectiveness, and determining necessary verification activities", "as necessary"),
    ]),
    ("8.4.3", "Information for external providers", [
        elem("E01", ORG, "ensure the adequacy of requirements before communicating them to the external provider, and communicate its requirements for processes/products/services, approvals, competence, interactions, control/monitoring, and verification or validation activities", "as appropriate",
             qualifier="as appropriate"),
    ]),
    ("8.5.1", "Control of production and service provision", [
        elem("E01", ORG, "implement production and service provision under controlled conditions, including availability/use of documented information defining characteristics/activities/results, availability/use of suitable monitoring and measuring resources, implementation of monitoring/measurement at appropriate stages, suitable infrastructure and environment, competent persons, validation and periodic revalidation where output cannot be verified by subsequent monitoring, actions to prevent human error, and release/delivery/post-delivery activities", "as applicable",
             qualifier="as applicable", evidence=record_and_doc()),
    ]),
    ("8.5.2", "Identification and traceability", [
        elem("E01", ORG, "use suitable means to identify outputs when necessary for conformity, identify output status with respect to monitoring/measurement requirements, control unique identification when traceability is required, and ensure documented information necessary to enable traceability is available", "as evidence", evidence=record()),
    ]),
    ("8.5.3", "Property belonging to customers or external providers", [
        elem("E01", ORG, "exercise care with, identify, verify, protect and safeguard property belonging to customers or external providers that is under the organization's control or provided for use or incorporation into products and services; report to the owner and ensure documented information is available as evidence of what occurred", "when such property is lost, damaged, or otherwise found unsuitable for use",
             condition="applies throughout custody of the property; reporting/evidence obligation triggers when it is lost, damaged, or found unsuitable for use", evidence=record()),
    ]),
    ("8.5.4", "Preservation", [
        elem("E01", ORG, "preserve", "the outputs during production and service provision, to the extent necessary to ensure conformity to requirements"),
    ]),
    ("8.5.5", "Post-delivery activities", [
        elem("E01", ORG, "meet the requirements for post-delivery activities associated with the products and services, considering statutory and regulatory requirements, potential undesired consequences, nature/use/intended lifetime, customer requirements, and customer feedback", "in determining the extent of post-delivery activities required"),
    ]),
    ("8.5.6", "Control of changes", [
        elem("E01", ORG, "review and control", "changes for production or service provision, to the extent necessary to ensure continuing conformity with requirements, and ensure documented information is available as evidence of review results, the person(s) authorizing the change, and any necessary actions arising from the review",
             evidence=doc_info()),
    ]),
    ("8.6", "Release of products and services", [
        elem("E01", ORG, "implement", "planned arrangements, at appropriate stages, to verify that the product and service requirements have been met"),
        elem("E02", ORG, "ensure release does not proceed", "until the planned arrangements have been satisfactorily completed, unless otherwise approved by a relevant authority and, as applicable, by the customer",
             neg=["output released with an open/failed verification step and no documented authority approval"]),
        elem("E03", ORG, "ensure documented information is available", "as evidence of the release of products and services, including evidence of conformity with acceptance criteria and traceability to the person(s) authorizing release", evidence=record()),
    ]),
    ("8.7.1", "Control of nonconforming outputs", [
        elem("E01", ORG, "ensure outputs that do not conform to requirements are identified and controlled", "to prevent their unintended use or delivery, taking appropriate action based on the nature of the nonconformity and its effect, including nonconformities detected after delivery or during/after service provision"),
        elem("E02", ORG, "deal with nonconforming outputs by correction, segregation/containment/return/suspension, informing the customer, or obtaining concession authorization, and verify conformity", "when nonconforming outputs are corrected", condition="when nonconforming outputs are corrected"),
    ]),
    ("8.7.2", "Documented information on nonconforming outputs", [
        elem("E01", ORG, "ensure documented information is available", "as evidence of the nature of the nonconformity, the actions taken, any concessions obtained, and the authority deciding the action", evidence=doc_info()),
    ]),
    ("9.1.1", "Monitoring, measurement, analysis and evaluation - General", [
        elem("E01", ORG, "determine", "what needs to be monitored and measured, the methods for monitoring/measurement/analysis/evaluation, when monitoring and measuring shall be performed, and when results shall be analysed and evaluated"),
        elem("E02", ORG, "evaluate the performance and effectiveness of the quality management system and ensure documented information is available", "as evidence of the results", evidence=record()),
    ]),
    ("9.1.2", "Customer satisfaction", [
        elem("E01", ORG, "monitor customer satisfaction and determine", "the methods for obtaining, monitoring and reviewing customer satisfaction information"),
    ]),
    ("9.1.3", "Analysis and evaluation", [
        elem("E01", ORG, "analyse and evaluate relevant data and information arising from monitoring and measurement, using the results to evaluate", "conformity of products and services, customer satisfaction, QMS performance and effectiveness, effectiveness of planning implementation, effectiveness of risk and opportunity actions, performance of external providers, and the need for QMS improvements"),
    ]),
    ("9.2.1", "Internal audit - General", [
        elem("E01", ORG, "conduct internal audits at planned intervals to provide information on whether the quality management system", "conforms to the organization's own QMS requirements and to the requirements of this document, and is effectively implemented and maintained"),
    ]),
    ("9.2.2", "Internal audit programme", [
        elem("E01", ORG, "plan, establish, implement and maintain", "an audit programme(s) including frequency, methods, responsibilities, planning requirements and reporting, considering the importance of the processes concerned, results of previous audits, and organizational changes"),
        elem("E02", ORG, "define audit objectives/criteria/scope for each audit, select auditors ensuring objectivity and impartiality, ensure audit results are reported to relevant managers, take correction and corrective action without undue delay, and ensure documented information is available", "as evidence of audit programme implementation and audit results", evidence=doc_info()),
    ]),
    ("9.3.1", "Management review - General", [
        elem("E01", TOPMGMT, "review", "the organization's quality management system, at planned intervals, to ensure its continuing suitability, adequacy, effectiveness, and alignment with the strategic direction of the organization"),
    ]),
    ("9.3.2", "Management review inputs", [
        elem("E01", ORG, "ensure the management review includes", "status of actions from previous reviews, changes in external/internal issues, changes in interested-party needs/expectations, QMS performance information and trends (nonconformities/corrective actions, monitoring and measurement results, audit results, customer satisfaction and feedback, achievement of quality objectives, process performance and product/service conformity, external-provider performance), opportunities for improvement, adequacy of resources, and the effectiveness of actions taken to address risks and opportunities"),
    ]),
    ("9.3.3", "Management review results", [
        elem("E01", TOPMGMT, "ensure the results of the management review include", "decisions related to continual improvement opportunities and any need for changes to the quality management system and resource needs, and ensure documented information is available as evidence of the results", evidence=doc_info()),
    ]),
    ("10.1", "Continual improvement", [
        elem("E01", ORG, "continually improve", "the suitability, adequacy and effectiveness of the quality management system"),
        elem("E02", ORG, "consider the results of monitoring/measurement/analysis/evaluation and of management review to determine opportunities, and address these opportunities", "as part of continual improvement"),
        elem("E03", ORG, "ensure improvement actions include", "improving processes, products and services; addressing future needs and expectations; and correcting, preventing or reducing undesired effects"),
    ]),
    ("10.2.1", "Nonconformity and corrective action", [
        elem("E01", ORG, "react to the nonconformity by taking action to control and correct it and dealing with the consequences, as applicable, and evaluate the need for action to eliminate its cause(s) by reviewing the nonconformity, determining its causes, and determining if similar nonconformities exist or could occur", "when a nonconformity occurs", condition="when a nonconformity occurs", qualifier="as applicable"),
        elem("E02", ORG, "implement needed action, review the effectiveness of any corrective action taken, update risks and opportunities if necessary, and make QMS changes if necessary, ensuring corrective actions are appropriate to the effects of the nonconformities encountered", "as necessary",
             neg=["corrective action disproportionate to (or absent for) the actual effect of the nonconformity"]),
    ]),
    ("10.2.2", "Documented information on nonconformity and corrective action", [
        elem("E01", ORG, "ensure documented information is available", "as evidence of the nature of the nonconformities and any subsequent actions taken, and of the results of any corrective action", evidence=doc_info()),
    ]),
]


CORPUS_CLAUSES = {c for c, _, _ in CLAUSES}
YAML_MAP = simple_yaml_map(RELATED_CLAUSE_MAP_YAML) if RELATED_CLAUSE_MAP_YAML.exists() else {}
CLAUSE_NUM_RE = re.compile(r"\b\d{1,2}(?:\.\d+){1,3}\b")


def parent_of(clause: str) -> str | None:
    if "." not in clause:
        return None
    return clause.rsplit(".", 1)[0]


def expand_clause_ref(ref: str, corpus: set[str]) -> set[str]:
    """A related-clause reference like '6.1' or '8.7' may denote a whole
    sub-clause family in the standard even though only 6.1.1/6.1.2/6.1.3 or
    8.7.1/8.7.2 exist as individual clauses in this corpus. Expand to every
    corpus clause that IS ref or is nested under it."""
    if ref in corpus:
        return {ref}
    return {c for c in corpus if c == ref or c.startswith(ref + ".")}


def compute_siblings(clause: str, corpus: set[str]) -> list[str]:
    parent = parent_of(clause)
    if parent is None:
        return []
    return sorted(c for c in corpus if c != clause and parent_of(c) == parent)


def compute_yaml_related(clause: str, corpus: set[str]) -> list[str]:
    related: set[str] = set()
    for group in YAML_MAP.values():
        if clause in group.get("primary", []):
            for ref in group.get("related_requirements", []):
                related |= expand_clause_ref(ref, corpus)
    related.discard(clause)
    return sorted(related)


# scripts/extract_clause.py's heading-boundary regex mis-triggers on the bare
# cross-reference "4.1" inline in clause 6.1.1's running text (confirmed the
# ONLY clause of the 65 affected by re-running this check against all of
# them), truncating the extracted text before it reaches "4.1"/"4.2". Seed
# the cache with the verified-correct text (read directly off PDF page 20 in
# this session) instead of trusting the live extractor for this one clause.
_TEXT_CACHE: dict[str, str] = {
    "6.1.1": (
        "6.1.1 Determining risks and opportunities\n"
        "When planning for the quality management system, the organization shall consider the issues referred to in "
        "4.1 and the requirements referred to in 4.2 and determine the risks and opportunities that need to be "
        "addressed to:\n"
        "a) give assurance that the quality management system can achieve its intended result(s);\n"
        "b) prevent, or reduce, undesired effects;\n"
        "c) achieve continual improvement;\n"
        "d) enhance desired effects."
    ),
}


def _raw_clause_text(clause: str) -> str:
    if clause in _TEXT_CACHE:
        return _TEXT_CACHE[clause]
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "extract_clause.py"), clause, "--json", "--max-chars", "6000"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    text = ""
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            text = json.loads(proc.stdout)["text"]
        except (json.JSONDecodeError, KeyError):
            text = ""
    _TEXT_CACHE[clause] = text
    return text


def compute_explicit_text_refs(clause: str, corpus: set[str]) -> list[str]:
    text = _raw_clause_text(clause)
    related: set[str] = set()
    for m in CLAUSE_NUM_RE.finditer(text):
        related |= expand_clause_ref(m.group(0), corpus)
    related.discard(clause)
    return sorted(related)


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    total_elements = 0
    # First pass: element IDs per clause, needed to resolve related_requirement_ids.
    element_ids_by_clause = {
        clause: [f"AR-{clause}-{e['suffix']}" for e in elements] for clause, _, elements in CLAUSES
    }
    for clause, title, elements in CLAUSES:
        category = semantic_category_for(clause)
        records = []
        for e in elements:
            req_id = f"AR-{clause}-{e['suffix']}"
            records.append({
                "requirement_id": req_id,
                "standard_id": STANDARD_ID,
                "clause": clause,
                "subject": e["subject"],
                "obligation": e["obligation"],
                "object": e["object"],
                "condition": e["condition"],
                "qualifier": e["qualifier"],
                "applicability_rule_id": None,
                "semantic_category": category,
                "evidence_expectations": e["evidence"],
                "failure_patterns": e["failure"],
                "negative_inference_rules": e["neg"],
                "version": VERSION,
            })
        total_elements += len(records)

        siblings = compute_siblings(clause, CORPUS_CLAUSES)
        yaml_related = compute_yaml_related(clause, CORPUS_CLAUSES)
        explicit_refs = compute_explicit_text_refs(clause, CORPUS_CLAUSES)
        all_related_clauses = sorted(set(siblings) | set(yaml_related) | set(explicit_refs))
        related_requirement_ids = sorted(
            rid for c in all_related_clauses for rid in element_ids_by_clause.get(c, [])
        )

        out_path = OUT_DIR / f"{clause}.json"
        payload = {
            "clause": clause,
            "clause_title": title,
            "standard_id": STANDARD_ID,
            "semantic_category": category,
            "semantic_category_source": (
                "harness_gate_executor.py:D2_SAFE_LIST" if category == "D2_SAFE" else
                "harness_gate_executor.py:M4_MANDATORY_LIST" if category == "M4_MANDATORY" else
                "harness_gate_executor.py:AMBIGUOUS_LIST" if clause in AMBIGUOUS_LIST else
                "default (clause not present in any severity-ceiling list; see docs/eei-blueprint-crosswalk.md gap #4)"
            ),
            "provenance": {
                "extracted_via": "scripts/extract_clause.py",
                "source_pdf": "assets/standards/ISO_FDIS_9001_2026_en.pdf",
                "is_cross_check": (
                    "Cross-checked 2026-09-17 against assets/standards/ISO_9001_2026_IS_en_scanned.pdf "
                    "(published ISO 9001:2026, Sixth edition, 2026-09) by direct visual page comparison "
                    "-- word-for-word identical, same clause numbering."
                    if clause in IS_CROSS_CHECKED_CLAUSES else
                    "Not individually cross-checked against the published IS scan yet (sourced from the "
                    "FDIS draft only) -- see IS_CROSS_CHECKED_CLAUSES in this script and "
                    "assets/requirement_profiles/README.md."
                ),
                "note": "AI-drafted decomposition, NOT SME/human-auditor reviewed.",
            },
            "related_clauses": {
                "siblings": siblings,
                "from_related_clause_map": yaml_related,
                "explicit_text_references": explicit_refs,
                "all": all_related_clauses,
            },
            "related_requirement_ids": related_requirement_ids,
            "requirements": records,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append({
            "clause": clause,
            "title": title,
            "semantic_category": category,
            "element_count": len(records),
            "related_clauses": all_related_clauses,
        })

    index_payload = {
        "standard_id": STANDARD_ID,
        "clause_count": len(CLAUSES),
        "element_count": total_elements,
        "status": "AI-drafted, unreviewed",
        "requires_sme_approval": True,
        "clauses": index,
    }
    (OUT_DIR / "_index.json").write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(CLAUSES)} clause files, {total_elements} elements total, to {OUT_DIR}")
    return index_payload


if __name__ == "__main__":
    result = build()
    print(json.dumps({k: v for k, v in result.items() if k != "clauses"}, indent=2))
