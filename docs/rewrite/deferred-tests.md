# Cross-phase deferred PORT tests

Tests whose behavioral contract is owned by a slice, but whose *infrastructure*
(WorldStore, source Documents, sidecar projection schemas, praf engine, render
policy) lands in a later phase. These are NOT dropped — they must be PORTed when
their owning phase is built. The Phase-9/10 completion gate is not satisfied
until every row here is green.

Recording convention: `reference test -> owning phase (infra it needs)`.

## Deferred during Phase 5a (commit 1bc1ace3)

5a built the value/honesty layer self-contained over quire; these need substrate
that 5a deliberately did not stub (stubbing phantom infra would violate
build-fresh + no-Document-mirror):

- test_relate_opinions.py -> 5b (relation_analysis over the AF / praf surface)
- test_relation_concept_identity.py -> 5b/6 (relation+concept alignment graph)
- test_defeat_summary_opinion_honest.py -> 5b (praf defeat-summary)
- test_defeat_summary_opinion_no_fabrication.py -> 5b (praf defeat-summary)
- test_source_relations.py -> 8 (source subsystem)
- test_trust_calibration_runs_at_promote.py -> 8 (source promote lifecycle)
- test_sidecar_relation_edge_projection.py -> 9 (projection_catalog relation_edge schema)
- test_sidecar_calibration_counts_projection.py -> 9/10 (families.calibration sidecar; calibration extract)
- test_opinion_schema.py -> 9/10 (opinion sidecar/schema projection)
- test_render_policy_opinions.py -> 10 (render policy)
- test_prior_base_rate_is_opinion.py -> 5b/7 (base-rate resolution against a store)
- test_claim_and_stance_document_enums.py -> 5b (needs the stance Document surface alongside claim enums)
