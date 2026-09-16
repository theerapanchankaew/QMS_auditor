from __future__ import annotations

import networkx as nx

from aias_awm.domain.models import AuditAction, AuditHypothesis, EvidenceItem, RequirementAssessment


class AuditWorldGraph:
    """Derived, queryable graph view. PostgreSQL/event store remains the system of record."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def rebuild(
        self,
        evidence: list[EvidenceItem],
        assessments: list[RequirementAssessment],
        hypotheses: list[AuditHypothesis],
        actions: list[AuditAction],
    ) -> None:
        self.graph.clear()
        for ev in evidence:
            self.graph.add_node(ev.evidence_id, kind="Evidence", epistemic_state=ev.epistemic_state.value)
            for req in ev.related_requirement_ids:
                self.graph.add_node(req, kind="AtomicRequirement")
                self.graph.add_edge(ev.evidence_id, req, relation="RELATES_TO")
        for a in assessments:
            self.graph.add_node(a.assessment_id, kind="RequirementAssessment", state=a.state.value)
            self.graph.add_node(a.requirement_id, kind="AtomicRequirement")
            self.graph.add_edge(a.assessment_id, a.requirement_id, relation="ASSESSES")
            for ev_id in a.positive_evidence_ids:
                self.graph.add_edge(ev_id, a.assessment_id, relation="SUPPORTS")
            for ev_id in a.negative_evidence_ids:
                self.graph.add_edge(ev_id, a.assessment_id, relation="SUPPORTS_BREACH")
            for ev_id in a.contradictory_evidence_ids:
                self.graph.add_edge(ev_id, a.assessment_id, relation="CONTRADICTS")
        for h in hypotheses:
            self.graph.add_node(h.hypothesis_id, kind="Hypothesis", status=h.status, unresolved_questions=list(h.unresolved_questions))
            for req in h.requirement_ids:
                self.graph.add_edge(h.hypothesis_id, req, relation="CONCERNS")
        for act in actions:
            self.graph.add_node(act.action_id, kind="AuditAction", action_type=act.action_type, status=act.status)
            for req in act.target_requirement_ids:
                self.graph.add_edge(act.action_id, req, relation="SEEKS_EVIDENCE_FOR")

    def evidence_for_requirement(self, requirement_id: str) -> list[str]:
        return sorted({u for u, v, d in self.graph.edges(data=True) if v == requirement_id and d.get("relation") == "RELATES_TO"})

    def unresolved_hypotheses(self) -> list[str]:
        return sorted([n for n, d in self.graph.nodes(data=True) if d.get("kind") == "Hypothesis" and bool(d.get("unresolved_questions"))])

    def pending_actions(self) -> list[str]:
        return sorted([n for n, d in self.graph.nodes(data=True) if d.get("kind") == "AuditAction" and d.get("status") == "PROPOSED"])
