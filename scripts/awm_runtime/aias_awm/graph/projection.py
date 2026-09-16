from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aias_awm.domain.models import AtomicRequirement, AuditAction, AuditHypothesis, EvidenceItem, RequirementAssessment


@dataclass
class GraphProjection:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[tuple[str, str, str, dict[str, Any]]] = field(default_factory=list)

    def add_node(self, node_id: str, node_type: str, **attrs: Any) -> None:
        self.nodes[node_id] = {"type": node_type, **attrs}

    def add_edge(self, source: str, relation: str, target: str, **attrs: Any) -> None:
        self.edges.append((source, relation, target, attrs))


class AuditGraphProjector:
    """Creates a graph-neutral projection. It can later be loaded into NetworkX/Neo4j."""

    def project(
        self,
        requirements: list[AtomicRequirement],
        evidence: list[EvidenceItem],
        assessments: list[RequirementAssessment],
        hypotheses: list[AuditHypothesis],
        actions: list[AuditAction],
    ) -> GraphProjection:
        g = GraphProjection()
        for r in requirements:
            g.add_node(r.requirement_id, "AtomicRequirement", clause=r.clause, obligation=r.obligation)
        for e in evidence:
            g.add_node(e.evidence_id, "Evidence", epistemic_state=e.epistemic_state.value, assertion=e.assertion)
            for rid in e.related_requirement_ids:
                g.add_edge(e.evidence_id, "RELATES_TO", rid)
        for a in assessments:
            g.add_node(a.assessment_id, "RequirementAssessment", state=a.state.value, breach_proven=a.breach_proven)
            g.add_edge(a.assessment_id, "ASSESSES", a.requirement_id)
            for eid in a.positive_evidence_ids:
                g.add_edge(eid, "SUPPORTS", a.assessment_id)
            for eid in a.negative_evidence_ids:
                g.add_edge(eid, "SUPPORTS_BREACH", a.assessment_id)
            for eid in a.contradictory_evidence_ids:
                g.add_edge(eid, "CONTRADICTS", a.assessment_id)
        for h in hypotheses:
            g.add_node(h.hypothesis_id, "Hypothesis", status=h.status, statement=h.statement)
            for rid in h.requirement_ids:
                g.add_edge(h.hypothesis_id, "CONCERNS", rid)
            for eid in h.supporting_evidence_ids:
                g.add_edge(eid, "SUPPORTS_HYPOTHESIS", h.hypothesis_id)
        for action in actions:
            g.add_node(action.action_id, "AuditAction", action_type=action.action_type, priority=action.priority_score)
            for rid in action.target_requirement_ids:
                g.add_edge(action.action_id, "SEEKS_EVIDENCE_FOR", rid)
        return g
