# Features 5-7 Implementation Notes

Session: 2026-03-16

## Plan
- Feature 5: graph_export.py (KnowledgeGraph, build_knowledge_graph, to_dot, to_json)
- Feature 6: sensitivity.py (analyze_sensitivity, SensitivityResult)
- Feature 7: transitive conflicts + HypotheticalWorld.recompute_conflicts()

## Key observations from codebase read
- WorldModel queries sidecar SQLite via self._conn
- Tables: concept, alias, relationship, parameterization, parameterization_group, claim, claim_stance, conflicts
- BoundWorld._is_active checks conditions via Z3
- propagation.py has evaluate_parameterization() and _parse_cached()
- build_sidecar calls _populate_conflicts which calls detect_conflicts from conflict_detector
- Parameterization: output_concept_id, concept_ids (JSON list of input IDs), formula, sympy, exactness, conditions_cel
- Existing claim IDs in fixture: claim1-claim10
- Test fixture has 7 concepts (concept1-concept7)

## Progress
- [ ] Feature 5: graph_export.py
- [ ] Feature 5: tests
- [ ] Feature 5: CLI
- [ ] Feature 6: sensitivity.py
- [ ] Feature 6: tests
- [ ] Feature 6: CLI
- [ ] Feature 7: detect_transitive_conflicts
- [ ] Feature 7: HypotheticalWorld.recompute_conflicts
- [ ] Feature 7: tests
- [ ] Feature 7: CLI
- [ ] Feature 7: build_sidecar integration
