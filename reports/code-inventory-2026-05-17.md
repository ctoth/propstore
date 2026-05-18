# Code Inventory - 2026-05-17

## Scope

In scope: committed Python code files under `propstore/` in `C:\Users\Q\code\propstore`, and committed Python code files under `C:\Users\Q\code\quire`, excluding test files and test directories.

Not in scope: tests, non-Python files, generated caches, untracked files, ignored files, and installed site-packages copies.

Completion standard: every checklist item below must be changed from `unread` to `read` with a human-written inventory entry for what the file owns and any relevant boundaries, storage/query/schema surfaces, or cleanup relevance.

## Checklist

### Propstore

- [x] read `propstore/__init__.py`
- [x] read `propstore/app/__init__.py`
- [x] read `propstore/app/claim_views.py`
- [x] read `propstore/app/claims.py`
- [x] read `propstore/app/compiler.py`
- [x] read `propstore/app/concept_views.py`
- [x] read `propstore/app/concepts/__init__.py`
- [x] read `propstore/app/concepts/alignment.py`
- [x] read `propstore/app/concepts/display.py`
- [x] read `propstore/app/concepts/embedding.py`
- [x] read `propstore/app/concepts/mutation.py`
- [x] read `propstore/app/contexts.py`
- [x] read `propstore/app/forms.py`
- [x] read `propstore/app/grounding.py`
- [x] read `propstore/app/materialize.py`
- [x] read `propstore/app/merge.py`
- [x] read `propstore/app/micropubs.py`
- [x] read `propstore/app/neighborhoods.py`
- [x] read `propstore/app/observatory.py`
- [x] read `propstore/app/predicates.py`
- [x] read `propstore/app/project_init.py`
- [x] read `propstore/app/proposals.py`
- [x] read `propstore/app/rendering.py`
- [x] read `propstore/app/repository_history.py`
- [x] read `propstore/app/repository_import.py`
- [x] read `propstore/app/repository_overview.py`
- [x] read `propstore/app/repository_views.py`
- [x] read `propstore/app/rules.py`
- [x] read `propstore/app/sources.py`
- [x] read `propstore/app/verify.py`
- [x] read `propstore/app/world.py`
- [x] read `propstore/app/world_atms.py`
- [x] read `propstore/app/world_reasoning.py`
- [x] read `propstore/app/world_revision.py`
- [x] read `propstore/app/worldlines.py`
- [x] read `propstore/argumentation.py`
- [x] read `propstore/artifact_codes.py`
- [x] read `propstore/artifact_verification.py`
- [x] read `propstore/aspic_bridge/__init__.py`
- [x] read `propstore/aspic_bridge/build.py`
- [x] read `propstore/aspic_bridge/extract.py`
- [x] read `propstore/aspic_bridge/grounding.py`
- [x] read `propstore/aspic_bridge/lifting_projection.py`
- [x] read `propstore/aspic_bridge/projection.py`
- [x] read `propstore/aspic_bridge/query.py`
- [x] read `propstore/aspic_bridge/translate.py`
- [x] read `propstore/canonical_namespaces.py`
- [x] read `propstore/cel_bindings.py`
- [x] read `propstore/cel_registry.py`
- [x] read `propstore/cel_types.py`
- [x] read `propstore/cel_validation.py`
- [x] read `propstore/claim_graph.py`
- [x] read `propstore/claims.py`
- [x] read `propstore/cli/__init__.py`
- [x] read `propstore/cli/claim/__init__.py`
- [x] read `propstore/cli/claim/analysis.py`
- [x] read `propstore/cli/claim/display.py`
- [x] read `propstore/cli/claim/embedding.py`
- [x] read `propstore/cli/claim/relation.py`
- [x] read `propstore/cli/claim/validation.py`
- [x] read `propstore/cli/compiler_cmds.py`
- [x] read `propstore/cli/concept/__init__.py`
- [x] read `propstore/cli/concept/alignment.py`
- [x] read `propstore/cli/concept/display.py`
- [x] read `propstore/cli/concept/embedding.py`
- [x] read `propstore/cli/concept/mutation.py`
- [x] read `propstore/cli/context.py`
- [x] read `propstore/cli/contracts.py`
- [x] read `propstore/cli/form.py`
- [x] read `propstore/cli/grounding_cmds.py`
- [x] read `propstore/cli/helpers.py`
- [x] read `propstore/cli/history_cmds.py`
- [x] read `propstore/cli/init.py`
- [x] read `propstore/cli/materialize.py`
- [x] read `propstore/cli/merge_cmds.py`
- [x] read `propstore/cli/micropub.py`
- [x] read `propstore/cli/observatory.py`
- [x] read `propstore/cli/output/__init__.py`
- [x] read `propstore/cli/output/console.py`
- [x] read `propstore/cli/output/sections.py`
- [x] read `propstore/cli/output/tables.py`
- [x] read `propstore/cli/output/yaml.py`
- [x] read `propstore/cli/predicate/__init__.py`
- [x] read `propstore/cli/predicate/display.py`
- [x] read `propstore/cli/predicate/mutation.py`
- [x] read `propstore/cli/proposal.py`
- [x] read `propstore/cli/repository_import_cmd.py`
- [x] read `propstore/cli/rule/__init__.py`
- [x] read `propstore/cli/rule/display.py`
- [x] read `propstore/cli/rule/mutation.py`
- [x] read `propstore/cli/source/__init__.py`
- [x] read `propstore/cli/source/authoring.py`
- [x] read `propstore/cli/source/batch.py`
- [x] read `propstore/cli/source/lifecycle.py`
- [x] read `propstore/cli/source/proposal.py`
- [x] read `propstore/cli/verify.py`
- [x] read `propstore/cli/web.py`
- [x] read `propstore/cli/world/__init__.py`
- [x] read `propstore/cli/world/analysis.py`
- [x] read `propstore/cli/world/atms.py`
- [x] read `propstore/cli/world/query.py`
- [x] read `propstore/cli/world/reasoning.py`
- [x] read `propstore/cli/world/revision.py`
- [x] read `propstore/cli/worldline/__init__.py`
- [x] read `propstore/cli/worldline/display.py`
- [x] read `propstore/cli/worldline/journal.py`
- [x] read `propstore/cli/worldline/materialize.py`
- [x] read `propstore/cli/worldline/mutation.py`
- [x] read `propstore/cli/worldline/rendering.py`
- [x] read `propstore/compiler/__init__.py`
- [x] read `propstore/compiler/context.py`
- [x] read `propstore/compiler/errors.py`
- [x] read `propstore/compiler/ir.py`
- [x] read `propstore/compiler/workflows.py`
- [x] read `propstore/concept_ids.py`
- [x] read `propstore/condition_classifier.py`
- [x] read `propstore/conflict_detector/__init__.py`
- [x] read `propstore/conflict_detector/algorithms.py`
- [x] read `propstore/conflict_detector/collectors.py`
- [x] read `propstore/conflict_detector/context.py`
- [x] read `propstore/conflict_detector/equation_inputs.py`
- [x] read `propstore/conflict_detector/equations.py`
- [x] read `propstore/conflict_detector/measurements.py`
- [x] read `propstore/conflict_detector/models.py`
- [x] read `propstore/conflict_detector/orchestrator.py`
- [x] read `propstore/conflict_detector/parameter_claims.py`
- [x] read `propstore/conflict_detector/parameterization_conflicts.py`
- [x] read `propstore/context_lifting.py`
- [x] read `propstore/contracts.py`
- [x] read `propstore/core/__init__.py`
- [x] read `propstore/core/activation.py`
- [x] read `propstore/core/active_claims.py`
- [x] read `propstore/core/algorithm_stage.py`
- [x] read `propstore/core/aliases.py`
- [x] read `propstore/core/analyzers.py`
- [x] read `propstore/core/anytime.py`
- [x] read `propstore/core/assertions/__init__.py`
- [x] read `propstore/core/assertions/codec.py`
- [x] read `propstore/core/assertions/conversion.py`
- [x] read `propstore/core/assertions/refs.py`
- [x] read `propstore/core/assertions/situated.py`
- [x] read `propstore/core/base_rates.py`
- [x] read `propstore/core/claim_types.py`
- [x] read `propstore/core/claim_values.py`
- [x] read `propstore/core/concept_relationship_types.py`
- [x] read `propstore/core/concept_status.py`
- [x] read `propstore/core/conditions/__init__.py`
- [x] read `propstore/core/conditions/cel_frontend.py`
- [x] read `propstore/core/conditions/checked.py`
- [x] read `propstore/core/conditions/codec.py`
- [x] read `propstore/core/conditions/estree_backend.py`
- [x] read `propstore/core/conditions/ir.py`
- [x] read `propstore/core/conditions/python_backend.py`
- [x] read `propstore/core/conditions/registry.py`
- [x] read `propstore/core/conditions/solver.py`
- [x] read `propstore/core/conditions/sql_backend.py`
- [x] read `propstore/core/conditions/z3_backend.py`
- [x] read `propstore/core/embeddings.py`
- [x] read `propstore/core/environment.py`
- [x] read `propstore/core/exactness_types.py`
- [x] read `propstore/core/graph_build.py`
- [x] read `propstore/core/graph_relation_types.py`
- [x] read `propstore/core/graph_types.py`
- [x] read `propstore/core/id_types.py`
- [x] read `propstore/core/justifications.py`
- [x] read `propstore/core/labels.py`
- [x] read `propstore/core/lemon/__init__.py`
- [x] read `propstore/core/lemon/description_kinds.py`
- [x] read `propstore/core/lemon/forms.py`
- [x] read `propstore/core/lemon/proto_roles.py`
- [x] read `propstore/core/lemon/qualia.py`
- [x] read `propstore/core/lemon/references.py`
- [x] read `propstore/core/lemon/temporal.py`
- [x] read `propstore/core/lemon/types.py`
- [x] read `propstore/core/literal_keys.py`
- [x] read `propstore/core/micropublications.py`
- [x] read `propstore/core/reasoning.py`
- [x] read `propstore/core/relation_types.py`
- [x] read `propstore/core/relations.py`
- [x] read `propstore/core/results.py`
- [x] read `propstore/core/source_types.py`
- [x] read `propstore/core/store_results.py`
- [x] read `propstore/defeasibility.py`
- [x] read `propstore/demo/__init__.py`
- [x] read `propstore/demo/reasoning_demo.py`
- [x] read `propstore/derived_build.py`
- [x] read `propstore/derived_build_plan.py`
- [x] read `propstore/description_generator.py`
- [x] read `propstore/dimensional_invariants.py`
- [x] read `propstore/dimensions.py`
- [x] read `propstore/epistemic_process.py`
- [x] read `propstore/families/__init__.py`
- [x] read `propstore/families/addresses.py`
- [x] read `propstore/families/batch_specs.py`
- [x] read `propstore/families/calibration/__init__.py`
- [x] read `propstore/families/calibration/declaration.py`
- [x] read `propstore/families/claims/__init__.py`
- [x] read `propstore/families/claims/declaration.py`
- [x] read `propstore/families/claims/documents.py`
- [x] read `propstore/families/claims/passes/__init__.py`
- [x] read `propstore/families/claims/passes/checks.py`
- [x] read `propstore/families/claims/passes/diagnostics.py`
- [x] read `propstore/families/claims/projection_model.py`
- [x] read `propstore/families/claims/references.py`
- [x] read `propstore/families/claims/sidecar_runtime.py`
- [x] read `propstore/families/claims/stages.py`
- [x] read `propstore/families/claims/storage.py`
- [x] read `propstore/families/concepts/__init__.py`
- [x] read `propstore/families/concepts/declaration.py`
- [x] read `propstore/families/concepts/documents.py`
- [x] read `propstore/families/concepts/passes.py`
- [x] read `propstore/families/concepts/projection_model.py`
- [x] read `propstore/families/concepts/sidecar_runtime.py`
- [x] read `propstore/families/concepts/stages.py`
- [x] read `propstore/families/contexts/__init__.py`
- [x] read `propstore/families/contexts/declaration.py`
- [x] read `propstore/families/contexts/documents.py`
- [x] read `propstore/families/contexts/passes.py`
- [x] read `propstore/families/contexts/stages.py`
- [x] read `propstore/families/diagnostics/__init__.py`
- [x] read `propstore/families/diagnostics/authoring_lints.py`
- [x] read `propstore/families/diagnostics/declaration.py`
- [x] read `propstore/families/documents/__init__.py`
- [x] read `propstore/families/documents/justifications.py`
- [x] read `propstore/families/documents/merge.py`
- [x] read `propstore/families/documents/micropubs.py`
- [x] read `propstore/families/documents/predicates.py`
- [x] read `propstore/families/documents/rules.py`
- [x] read `propstore/families/documents/source_alignment.py`
- [x] read `propstore/families/documents/sources.py`
- [x] read `propstore/families/documents/stances.py`
- [x] read `propstore/families/documents/worldlines.py`
- [x] read `propstore/families/embeddings/__init__.py`
- [x] read `propstore/families/embeddings/declaration.py`
- [x] read `propstore/families/forms/__init__.py`
- [x] read `propstore/families/forms/documents.py`
- [x] read `propstore/families/forms/passes.py`
- [x] read `propstore/families/forms/stages.py`
- [x] read `propstore/families/identity/__init__.py`
- [x] read `propstore/families/identity/claims.py`
- [x] read `propstore/families/identity/concepts.py`
- [x] read `propstore/families/identity/justifications.py`
- [x] read `propstore/families/identity/logical_ids.py`
- [x] read `propstore/families/identity/micropubs.py`
- [x] read `propstore/families/identity/stances.py`
- [x] read `propstore/families/micropublications/__init__.py`
- [x] read `propstore/families/micropublications/declaration.py`
- [x] read `propstore/families/projection_catalog.py`
- [x] read `propstore/families/registry.py`
- [x] read `propstore/families/relations/__init__.py`
- [x] read `propstore/families/relations/declaration.py`
- [x] read `propstore/families/relations/projection_model.py`
- [x] read `propstore/families/rules/__init__.py`
- [x] read `propstore/families/rules/declaration.py`
- [x] read `propstore/families/sameas/__init__.py`
- [x] read `propstore/families/sameas/documents.py`
- [x] read `propstore/families/sources/__init__.py`
- [x] read `propstore/families/sources/declaration.py`
- [x] read `propstore/form_utils.py`
- [x] read `propstore/fragility.py`
- [x] read `propstore/fragility_contributors.py`
- [x] read `propstore/fragility_scoring.py`
- [x] read `propstore/fragility_types.py`
- [x] read `propstore/graph_export.py`
- [x] read `propstore/grounding/__init__.py`
- [x] read `propstore/grounding/bundle.py`
- [x] read `propstore/grounding/complement.py`
- [x] read `propstore/grounding/explanations.py`
- [x] read `propstore/grounding/facts.py`
- [x] read `propstore/grounding/grounder.py`
- [x] read `propstore/grounding/gunray_complement.py`
- [x] read `propstore/grounding/inspection.py`
- [x] read `propstore/grounding/loading.py`
- [x] read `propstore/grounding/predicates.py`
- [x] read `propstore/grounding/translator.py`
- [x] read `propstore/heuristic/__init__.py`
- [x] read `propstore/heuristic/calibrate.py`
- [x] read `propstore/heuristic/classify.py`
- [x] read `propstore/heuristic/embed.py`
- [x] read `propstore/heuristic/embedding_identity.py`
- [x] read `propstore/heuristic/predicate_extraction.py`
- [x] read `propstore/heuristic/relate.py`
- [x] read `propstore/heuristic/rule_corpus.py`
- [x] read `propstore/heuristic/rule_extraction.py`
- [x] read `propstore/heuristic/source_trust.py`
- [x] read `propstore/importing/__init__.py`
- [x] read `propstore/importing/machinery.py`
- [x] read `propstore/importing/passes.py`
- [x] read `propstore/importing/repository_import.py`
- [x] read `propstore/importing/stages.py`
- [x] read `propstore/json_types.py`
- [x] read `propstore/merge/__init__.py`
- [x] read `propstore/merge/description_kinds.py`
- [x] read `propstore/merge/merge_claims.py`
- [x] read `propstore/merge/merge_classifier.py`
- [x] read `propstore/merge/merge_commit.py`
- [x] read `propstore/merge/merge_report.py`
- [x] read `propstore/merge/structured_merge.py`
- [x] read `propstore/merge/witness.py`
- [x] read `propstore/observatory.py`
- [x] read `propstore/opinion.py`
- [x] read `propstore/parameterization_groups.py`
- [x] read `propstore/parameterization_walk.py`
- [x] read `propstore/policies.py`
- [x] read `propstore/praf/__init__.py`
- [x] read `propstore/praf/engine.py`
- [x] read `propstore/praf/projection.py`
- [x] read `propstore/preference.py`
- [x] read `propstore/probabilistic_relations.py`
- [x] read `propstore/propagation.py`
- [x] read `propstore/proposal_promotion.py`
- [x] read `propstore/proposals.py`
- [x] read `propstore/proposals_predicates.py`
- [x] read `propstore/proposals_rules.py`
- [x] read `propstore/provenance/__init__.py`
- [x] read `propstore/provenance/derivative.py`
- [x] read `propstore/provenance/homomorphism.py`
- [x] read `propstore/provenance/nogoods.py`
- [x] read `propstore/provenance/polynomial.py`
- [x] read `propstore/provenance/projections.py`
- [x] read `propstore/provenance/prov_o.py`
- [x] read `propstore/provenance/records.py`
- [x] read `propstore/provenance/support.py`
- [x] read `propstore/provenance/trusty.py`
- [x] read `propstore/provenance/variables.py`
- [x] read `propstore/relation_analysis.py`
- [x] read `propstore/reporting.py`
- [x] read `propstore/repository.py`
- [x] read `propstore/resources.py`
- [x] read `propstore/semantic_passes/__init__.py`
- [x] read `propstore/semantic_passes/diagnostics.py`
- [x] read `propstore/semantic_passes/registry.py`
- [x] read `propstore/semantic_passes/runner.py`
- [x] read `propstore/semantic_passes/types.py`
- [x] read `propstore/sensitivity.py`
- [x] read `propstore/source/__init__.py`
- [x] read `propstore/source/alignment.py`
- [x] read `propstore/source/claim_concepts.py`
- [x] read `propstore/source/claims.py`
- [x] read `propstore/source/common.py`
- [x] read `propstore/source/concepts.py`
- [x] read `propstore/source/finalize.py`
- [x] read `propstore/source/promote.py`
- [x] read `propstore/source/reference_indexes.py`
- [x] read `propstore/source/registry.py`
- [x] read `propstore/source/relations.py`
- [x] read `propstore/source/stages.py`
- [x] read `propstore/source/status.py`
- [x] read `propstore/source_trust_argumentation/__init__.py`
- [x] read `propstore/stances.py`
- [x] read `propstore/storage/__init__.py`
- [x] read `propstore/storage/git_policy.py`
- [x] read `propstore/storage/snapshot.py`
- [x] read `propstore/structured_projection.py`
- [x] read `propstore/support_revision/__init__.py`
- [x] read `propstore/support_revision/af_adapter.py`
- [x] read `propstore/support_revision/belief_set_adapter.py`
- [x] read `propstore/support_revision/dispatch.py`
- [x] read `propstore/support_revision/entrenchment.py`
- [x] read `propstore/support_revision/explain.py`
- [x] read `propstore/support_revision/explanation_types.py`
- [x] read `propstore/support_revision/history.py`
- [x] read `propstore/support_revision/input_normalization.py`
- [x] read `propstore/support_revision/iterated.py`
- [x] read `propstore/support_revision/projection.py`
- [x] read `propstore/support_revision/realization.py`
- [x] read `propstore/support_revision/scope_policy.py`
- [x] read `propstore/support_revision/snapshot_types.py`
- [x] read `propstore/support_revision/state.py`
- [x] read `propstore/support_revision/workflows.py`
- [x] read `propstore/unit_dimensions.py`
- [x] read `propstore/uri.py`
- [x] read `propstore/uri_authority.py`
- [x] read `propstore/value_comparison.py`
- [x] read `propstore/web/__init__.py`
- [x] read `propstore/web/app.py`
- [x] read `propstore/web/html.py`
- [x] read `propstore/web/requests.py`
- [x] read `propstore/web/routing.py`
- [x] read `propstore/web/serialization.py`
- [x] read `propstore/world/__init__.py`
- [x] read `propstore/world/actual_cause.py`
- [x] read `propstore/world/assignment_selection_merge.py`
- [x] read `propstore/world/atms.py`
- [x] read `propstore/world/bound.py`
- [x] read `propstore/world/bridge.py`
- [x] read `propstore/world/consistency.py`
- [x] read `propstore/world/intervention.py`
- [x] read `propstore/world/journal_replay.py`
- [x] read `propstore/world/model.py`
- [x] read `propstore/world/overlay.py`
- [x] read `propstore/world/queries.py`
- [x] read `propstore/world/resolution.py`
- [x] read `propstore/world/scm.py`
- [x] read `propstore/world/types.py`
- [x] read `propstore/world/value_resolver.py`
- [x] read `propstore/worldline/__init__.py`
- [x] read `propstore/worldline/_constants.py`
- [x] read `propstore/worldline/argumentation.py`
- [x] read `propstore/worldline/definition.py`
- [x] read `propstore/worldline/hashing.py`
- [x] read `propstore/worldline/interfaces.py`
- [x] read `propstore/worldline/resolution.py`
- [x] read `propstore/worldline/result_types.py`
- [x] read `propstore/worldline/revision_capture.py`
- [x] read `propstore/worldline/revision_types.py`
- [x] read `propstore/worldline/runner.py`
- [x] read `propstore/worldline/trace.py`

### Quire

- [x] read `../quire/quire/__init__.py`
- [x] read `../quire/quire/artifacts.py`
- [x] read `../quire/quire/canonical.py`
- [x] read `../quire/quire/contracts.py`
- [x] read `../quire/quire/derived_runtime.py`
- [x] read `../quire/quire/derived_store.py`
- [x] read `../quire/quire/documents/__init__.py`
- [x] read `../quire/quire/documents/_paths.py`
- [x] read `../quire/quire/documents/batch.py`
- [x] read `../quire/quire/documents/codecs.py`
- [x] read `../quire/quire/documents/loaded.py`
- [x] read `../quire/quire/documents/schema.py`
- [x] read `../quire/quire/families.py`
- [x] read `../quire/quire/family_store.py`
- [x] read `../quire/quire/git_store.py`
- [x] read `../quire/quire/hashing.py`
- [x] read `../quire/quire/notes.py`
- [x] read `../quire/quire/projection_mapping.py`
- [x] read `../quire/quire/projections.py`
- [x] read `../quire/quire/references.py`
- [x] read `../quire/quire/refs.py`
- [x] read `../quire/quire/sqlite_vec_store.py`
- [x] read `../quire/quire/tree_path.py`
- [x] read `../quire/quire/versions.py`
- [x] read `../quire/scripts/benchmark_packed_repo_reads.py`
- [x] read `../quire/scripts/benchmark_raw_fs_baselines.py`
- [x] read `../quire/scripts/profile_dulwich_runtime.py`
- [x] read `../quire/scripts/profile_gitstore_hotpaths.py`

## Inventory Entries

### `propstore/__init__.py`

Owner/subsystem: package root public API.

This file owns Propstore's lazy package-level exports for core world/query concepts. It does not implement world behavior itself; it maps public names such as `WorldQuery`, `BoundWorld`, `OverlayWorld`, `InterventionWorld`, `StructuralCausalModel`, `ValueResult`, `ResolvedResult`, and `actual_cause` to their owner modules and resolves them through `__getattr__` on first access. The boundary purpose is import laziness: package import does not eagerly import the world stack, while type-checking still sees the exported types under `TYPE_CHECKING`. Cleanup relevance: this is an API surface and should stay shallow; new behavior belongs in the referenced owner modules, not here.

### `propstore/app/__init__.py`

Owner/subsystem: application service package marker.

This file is empty. It marks `propstore.app` as a package but owns no types, functions, storage behavior, query behavior, schema, or cross-layer boundary. Cleanup relevance: no behavior to move or delete here; it is only package structure.

### `propstore/app/claim_views.py`

Owner/subsystem: application-layer claim view reports for durable presenters.

This file owns typed request/report objects for claim detail, claim list, and claim search presentation: `ClaimViewRequest`, `ClaimListRequest`, `ClaimSearchRequest`, `ClaimViewReport`, `ClaimSummaryReport`, and nested concept/value/uncertainty/condition/provenance/status DTOs. Its main entry points are `build_claim_view`, `list_claim_views`, and `search_claim_views`. It opens the app world model, applies render policy, resolves concept filters, reads sidecar-backed `world` claim/concept rows, and formats presenter-safe summaries. Boundary: it is app/presentation logic, not storage ownership; it depends on `open_app_world_model`, render policy builders, repository view labels, and `WorldStore`-like methods such as `get_claim`, `get_concept`, `claims_with_policy`, and `resolve_concept`. Cleanup relevance: this file contains substantial formatting and display heuristics such as focus concept selection, value text, condition text, provenance text, and search matching; those should remain app-layer/report concerns and not drift into CLI modules or core domain objects.

### `propstore/app/claims.py`

Owner/subsystem: application-layer claim workflows.

This file owns typed request/report/failure objects for claim comparison, validation, conflict detection, embedding, similarity search, and relation proposal workflows. Main entry points include `compare_algorithm_claims`, `compare_algorithm_claims_from_repo`, `validate_claim_files`, `validate_claim_file`, `detect_claim_conflicts`, `embed_claim_embeddings`, `find_similar_claims`, and `relate_claims`. It is a coordination layer: it opens `WorldQuery` for algorithm comparison, builds compilation contexts for validation/conflict detection, calls claim family sidecar runtime helpers for embeddings/similarity/relation discovery, and commits stance proposals through the proposal subsystem. Boundary: app layer owns typed workflow reports and maps expected failures to domain-specific exceptions, while compiler, families, sidecar runtime, conflict detector, and proposals own the underlying behavior. Storage/query surfaces: reads claim handles through `repo.families.claims`, materializes/opens the world sidecar, and writes proposal branches through `commit_stance_proposals`. Cleanup relevance: keep CLI out of this logic; any duplicated claim validation or embedding command behavior should call these app APIs instead of reimplementing in `propstore.cli`.

### `propstore/app/compiler.py`

Owner/subsystem: application-layer compiler facade.

This file is a thin app adapter for repository validation, repository build, and concept alias export. It defines `AliasExportRequest` and delegates `validate_repository` and `build_repository` to `propstore.compiler.workflows`, while `export_aliases` delegates to `propstore.core.aliases.export_concept_aliases`. Boundary: it intentionally keeps compiler workflow ownership in `propstore.compiler.workflows` and alias extraction in core; this module only provides a stable app-layer call site. Cleanup relevance: this is already shallow and should not accumulate compiler behavior.

### `propstore/app/concept_views.py`

Owner/subsystem: application-layer concept view reports for durable presenters.

This file owns typed concept detail report DTOs and the `build_concept_view` workflow. It resolves a concept through the app world model, finds the authored concept entry through `propstore.app.concepts.display._find_concept_entry`, applies render policy, collects visible and blocked claims, and builds a durable presentation model containing form status, claim groups, value/uncertainty/provenance summaries, and related claim links. Boundary: this is app/report formatting and summary logic; it reads from sidecar-backed world APIs and authored concept lookup helpers but does not own storage or projection definitions. Cleanup relevance: display decisions such as grouping claims by type, classifying missing/blocked/known states, and producing sentences belong here or in nearby app presentation helpers, not in CLI or core semantic types.

### `propstore/app/concepts/__init__.py`

Owner/subsystem: application-layer concept workflow package API.

This file re-exports concept app workflows and DTOs from `alignment`, `display`, `embedding`, and `mutation`. It owns no behavior beyond package-level API aggregation. Boundary: callers can import concept app functions from one package surface, while implementation stays in sibling modules. Cleanup relevance: keep this shallow; avoid adding workflow logic here because it would obscure ownership and increase import coupling.

### `propstore/app/concepts/alignment.py`

Owner/subsystem: application-layer concept alignment facade.

This file owns the app-level wrappers for concept alignment build/query/decision/promotion: `build_concept_alignment`, `query_concept_alignment`, `decide_concept_alignment`, and `promote_concept_alignment`. It delegates the actual source-alignment behavior to `propstore.source` functions (`align_sources`, `load_alignment_artifact`, `decide_alignment`, `promote_alignment`) and returns concept app report DTOs from `mutation.py`. Boundary: source subsystem owns alignment artifacts and mutations; this module maps those operations into app-layer request/report shapes and expected display errors. Cleanup relevance: this is appropriately thin; CLI should call this rather than import source alignment primitives directly if it needs app-level behavior.

### `propstore/app/concepts/display.py`

Owner/subsystem: application-layer concept display workflows.

This file owns concept search/list/category/show app functions and one app-specific search syntax error. `search_concepts` uses the concept sidecar FTS query helper and maps rows into `ConceptSearchReport`; `list_concepts` and `list_concept_categories` inspect loaded authored concepts; `show_concept` renders either a concept alignment artifact (`align:` handles) or a canonical concept document through the family renderers. Boundary: this module imports private concept mutation helpers for shared loading/rendering primitives, while actual search SQL belongs to `propstore.families.concepts.declaration` and alignment artifact loading belongs to `propstore.source`. Cleanup relevance: display and rendering orchestration belongs here, but the dependency on private helpers from `mutation.py` is a coupling point to watch if concept app modules are reorganized.

### `propstore/app/concepts/embedding.py`

Owner/subsystem: application-layer concept embedding workflows.

This file owns app-level concept embedding and similarity workflows: `embed_concept_embeddings` and `find_similar_concepts`. It validates request shape, requires a materialized sidecar through shared concept app helper `_require_sidecar`, delegates embedding/similarity execution to `propstore.families.concepts.sidecar_runtime`, and maps sidecar result rows into app report DTOs. Boundary: app layer owns request/report/error mapping and progress callback plumbing; sidecar runtime owns SQLite/vector operations. Cleanup relevance: similar shape to claim embedding app workflows; duplication may be intentional family symmetry, but shared embedding workflow abstractions could be considered only if they reduce real repetition without hiding family-specific DTOs.

### `propstore/app/concepts/mutation.py`

Owner/subsystem: application-layer concept mutation and shared concept app DTOs.

This file owns most typed concept app request/report/error classes and the mutation workflows for adding concepts, adding aliases, renaming, deprecating, linking concepts, adding qualia, setting description kinds, adding proto-role entailments, and adding category values. It also contains older display/alignment DTOs and wrappers that are now partly split into sibling modules, plus shared helpers used by those modules: sidecar requirement, concept lookup by handle/name/artifact/logical ID/alias, concept document coercion/normalization, loaded concept construction, validation, CEL identifier rewriting, form registry construction, and mutation serialization through `repo.mutation_guard`. Boundary: concept document identity/normalization belongs to family identity/stages modules, validation belongs to concept/claim pipelines, persistence goes through `repo.families.concepts` and transactions, and this app module coordinates those owner layers into user-facing mutation workflows. Storage/query/schema surfaces: reads and writes canonical concept family artifacts, may rewrite claim condition CEL when renaming concepts, validates claim files after rename, and uses repository snapshots/mutation guards. Cleanup relevance: this file is large and has mixed responsibilities: mutation orchestration, shared private helpers, and duplicate display/alignment functions that also exist in `display.py`/`alignment.py`; it is a likely refactor target, but owner-layer behavior should move carefully rather than into CLI.

### `propstore/app/contexts.py`

Owner/subsystem: application-layer context and context-lifting workflows.

This file owns typed request/report/error objects and workflows for adding, listing, searching, showing, and removing contexts, plus listing/showing/adding/updating/removing context lifting rules. It constructs and validates `ContextDocument` and `LiftingRuleDocument` values, serializes context mutations through `repo.mutation_guard`, validates CEL assumptions and lifting-rule conditions against the compiler CEL registry, and checks references from canonical claims, source-branch claims, and worldlines before context removal. Boundary: authored context schema belongs to `propstore.families.contexts.documents`; parsed context records belong to context stages; repository persistence goes through `repo.families.contexts`; this app module coordinates those into user-facing workflows. Storage/query surfaces: iterates context family handles, source branches, source claim documents, worldline family handles, and canonical claim handles. Cleanup relevance: context reference scanning is business logic for safe deletion and belongs outside CLI; if reused elsewhere, extract to a context owner/helper rather than duplicating.

### `propstore/app/forms.py`

Owner/subsystem: application-layer form workflows.

This file owns typed form request/report/error objects and workflows for showing, listing, searching, adding, removing, and validating forms. It parses dimension filters, formats dimensions with Bridgman when available, renders form YAML through family renderers, optionally enriches `show_form` with form algebra rows from `WorldQuery`, and prevents unsafe form deletion by scanning concept family references. Boundary: form document schema belongs to `propstore.families.forms.documents`, form parsing/stage validation belongs to form stages/passes, concept references are read through concept family handles, and this module coordinates those owner layers into app-level workflows. Storage/query surfaces: reads/writes/deletes `repo.families.forms`, scans `repo.families.concepts`, runs `run_form_pipeline`, and optionally queries world sidecar form algebra. Cleanup relevance: `show_form` catches all exceptions around world algebra enrichment and silently drops those details; that is presentation-tolerant behavior but should not mask owner-layer validation failures elsewhere.

### `propstore/app/grounding.py`

Owner/subsystem: application-layer grounding inspection facade.

This file owns tiny request DTOs for grounding query/explain and re-exports grounding inspection report/error types. Its functions delegate directly to `propstore.grounding.inspection` for status, show, query, arguments, and explain operations. Boundary: grounding inspection ownership is in `propstore.grounding.inspection`; this app module is an adapter for callers that use app-layer request/report shapes. Cleanup relevance: appropriately shallow facade; keep grounding logic out of CLI by routing through this or the grounding owner layer.

### `propstore/app/materialize.py`

Owner/subsystem: application-layer repository materialization workflow.

This file owns `MaterializeRequest`, `MaterializeError`, and `materialize_repository`. It selects either the passed repository or a repository found at a requested directory, then delegates actual materialization to `RepositorySnapshot.materialize`, mapping `MaterializeConflictError` and `ValueError` to app-layer `MaterializeError`. Boundary: snapshot/materialization semantics are owned by `propstore.storage.snapshot`; this module is a thin app adapter. Cleanup relevance: keep it as a facade; materialization policy should not move into CLI.

### `propstore/app/merge.py`

Owner/subsystem: application-layer repository merge workflows.

This file owns typed inspect/commit merge request/report DTOs and app entry points `inspect_merge` and `commit_merge`. Inspect delegates to merge framework construction and summary rendering; commit delegates to `propstore.merge.merge_commit.create_merge_commit`, then reads the merge manifest at the resulting commit and returns a storage-merge payload including changed claim paths, manifest path, commit SHA, and semantic candidate count. Boundary: merge classification/report/commit behavior is owned by `propstore.merge`; this app module coordinates request/report shapes and repository access. Storage surfaces: uses `repo.snapshot`, `repo.require_git`, `repo.families.merge_manifests`, and Git flat tree entries. Cleanup relevance: app layer still returns loose `Mapping[str, object]` payloads here; typed report payloads may be a future cleanup target if merge reports stabilize.

### `propstore/app/micropubs.py`

Owner/subsystem: application-layer micropublication inspection workflows.

This file owns micropublication lookup/list DTOs and lift-inspection reports. `find_micropub` loads a canonical micropublication by `MicropublicationRef`; `list_micropubs` summarizes all canonical micropubs; `inspect_micropub_lift` builds a lifting system from authored contexts and reports lifting decisions for each claim in a micropub from source context to a requested target context. Boundary: micropublication schema belongs to family documents, lifting logic belongs to `propstore.context_lifting` via context stages, and this app module adapts those into inspection reports. Storage/query surfaces: reads `repo.families.micropubs` and `repo.families.contexts`. Cleanup relevance: this is a focused inspection adapter; no persistence mutation here.

### `propstore/app/neighborhoods.py`

Owner/subsystem: application-layer semantic neighborhood reports.

This file owns DTOs and `build_semantic_neighborhood` for a claim-centered semantic neighborhood view. It currently supports only `focus_kind="claim"` and reports focus status, navigation moves, graph nodes/edges, table rows, and prose summary from visible stance relations, shared value-concept claims, condition status, and provenance status. Boundary: it is a presenter/report projection over the app world model and render policy; stance semantics come from `StanceType`, world data comes from `open_app_world_model`, and unsupported focus kinds are explicitly rejected. Cleanup relevance: the module has hard-coded unavailable moves for assumptions and policy alternatives, and concept/source/worldline focus kinds are declared in the type alias but not implemented; those are honest extension gaps, not completed surfaces.

### `propstore/app/observatory.py`

Owner/subsystem: application-layer epistemic observatory adapter.

This file owns `AppObservatoryRunRequest`, conversion from/to dictionaries, and `run_observatory`. It validates that request scenarios are mappings, converts them into `EvaluationScenario`, and delegates evaluation to `propstore.observatory.evaluate_scenarios`; the `Repository` argument is currently unused. Boundary: observatory scenario semantics and report computation belong to `propstore.observatory`; this app module only adapts request shape. Cleanup relevance: if repository-dependent observatory behavior is not planned, the unused repo parameter is an API consistency choice rather than active behavior.

### `propstore/app/predicates.py`

Owner/subsystem: application-layer predicate authoring workflows.

This file owns typed predicate request/report/error classes and workflows for declaring, listing, showing, and removing canonical predicate documents. `add_predicate` validates predicate id, arity, and argument type count, converts the request into a `PredicateDocument`, rejects duplicate/conflicting declarations, and writes through the predicate family inside a git-backed head transaction. `remove_predicate` uses a mutation guard and deletes the canonical predicate artifact by `PredicateRef`; `show_predicate` renders the document with `encode_document`; `list_predicates` summarizes family handles. Boundary: predicate schema and storage addressing belong to `propstore.families.documents.predicates` and the Quire-backed family registry; this module owns app-level mutation workflow and conflict policy. Cleanup relevance: the file is appropriately focused, but it still carries CLI wording in docstrings and request names even though the behavior is app-layer authoring rather than CLI-owned logic.

### `propstore/app/project_init.py`

Owner/subsystem: application-layer repository initialization and packaged seed import.

This file owns `initialize_project`, `ProjectInitReport`, and the helpers that load packaged default forms/concepts and render them into a newly initialized repository. It detects already initialized repositories, calls `Repository.init`, loads packaged YAML resources through `_get_resource`, converts seed form/concept payloads into typed `FormDocument` and `ConceptDocument` values, writes all seed artifacts in one git commit, and records the bootstrap manifest. Boundary: resource discovery is in `propstore.resources`, document conversion is in Quire document helpers, and family storage preparation belongs to repository family APIs; this module coordinates those pieces for the init workflow. Cleanup relevance: seed concept payload construction is hand-authored and detailed here, including provenance, ontology references, description-kind slots, qualia, and proto-role bundles; changes to seed schema should update these helpers rather than bypassing typed document conversion.

### `propstore/app/proposals.py`

Owner/subsystem: application-layer proposal promotion adapter.

This file owns the app DTOs for stance proposal promotion planning and execution. `plan_proposal_promotion` delegates to `propstore.proposals.plan_stance_proposal_promotion` and maps the plan items into stable report objects while preserving the underlying plan for execution; `promote_proposals` delegates to `promote_stance_proposals` and maps promoted items back into app reports. Boundary: proposal discovery and mutation semantics are owned by `propstore.proposals`; this module is a thin app-facing adapter. Cleanup relevance: because execution takes the returned plan object, callers must treat `ProposalPromotionPlanReport` as more than display data; any future serialization boundary would need a typed re-load or validation path.

### `propstore/app/rendering.py`

Owner/subsystem: application-layer render policy normalization.

This file owns the app request/summary DTOs for render-policy options and the `build_render_policy`/`summarize_render_policy` functions. It converts string options for reasoning backend, argumentation semantics, and optional resolution strategy into the domain `RenderPolicy`, carries display filters such as drafts/blocked/quarantined, and maps normalization errors into `RenderPolicyValidationError`. Boundary: policy semantics and enum normalization belong to `propstore.world` and `propstore.world.types`; this app module owns input normalization and API-safe summaries. Cleanup relevance: this is the right shared adapter for CLI/API surfaces that need render policy construction without importing or duplicating world-layer parsing logic.

### `propstore/app/repository_history.py`

Owner/subsystem: application-layer repository history and checkout reports.

This file owns typed report DTOs for commit logs, file changes, merge summaries, commit-show output, and historical checkout. It classifies commit messages into stable operation labels, builds branch log reports from git history, optionally attaches changed-file lists, loads merge manifest summaries for merge commits, builds diff/commit-show reports, and materializes the world sidecar for a requested historical commit after verifying concepts exist there. Boundary: low-level git operations are through `repo.require_git`, merge manifest storage is through `repo.families.merge_manifests`, and sidecar rebuild belongs to `propstore.derived_build`; this module owns app-facing history semantics. Cleanup relevance: operation classification is message-pattern based, so commit message changes affect history labels; durable operation metadata would be a stronger long-term interface if history classification becomes semantic rather than presentational.

### `propstore/app/repository_import.py`

Owner/subsystem: application-layer repository import facade.

This file owns `import_repository` and a small `RepositoryImportError`. It verifies that the target repository is git-backed, delegates planning and commit execution to `propstore.importing.repository_import`, and returns the dataclass result as a mapping. Boundary: import planning, path comparison, artifact copying, and commit semantics are owned by the importing subsystem; this module only exposes an app-layer workflow. Cleanup relevance: the function currently returns a loose mapping through `asdict`; if import results become part of a stable API, a typed report DTO would better match the rest of the app layer.

### `propstore/app/repository_overview.py`

Owner/subsystem: application-layer repository overview/index report.

This file owns the typed overview report model used for the repository index page, including inventory rows, source pointers, provenance summary, recent activity, notable conflicts, and prose summary. It builds a render-policy summary, repository view label, claim/concept inventory counts through registered `KindContributor` objects, source pointers through `list_sources`, and recent activity through repository history reports; unsupported aggregate sections explicitly return `state="not_implemented"` rather than fabricated data. Boundary: underlying claim/concept/source/history data comes from other app modules and world/sidecar behavior; this file composes those reports into a top-level overview. Cleanup relevance: the honest-vacuous state discipline is intentional; future additions should extend `KIND_REGISTRY` or implemented sections directly instead of hard-coding kind lists in renderers.

### `propstore/app/repository_views.py`

Owner/subsystem: shared application-layer repository view contract.

This file owns `AppRepositoryViewRequest`, expected repository-view errors, and validation/label helpers for read surfaces. It currently supports only the current worktree view and rejects branch-qualified or revision-qualified views as not implemented. Boundary: consumers such as repository overview call this to keep unsupported historical/branch read modes explicit instead of silently ignoring request fields. Cleanup relevance: when branch or revision views become real, this is the small shared contract that should change before individual app read surfaces start accepting those modes.

### `propstore/app/rules.py`

Owner/subsystem: application-layer rule and rule-superiority authoring workflows.

This file owns typed request/report/error classes plus parsing and mutation workflows for canonical rule artifacts and superiority artifacts. It parses atom/body literal strings into rule document terms, validates rule kind/source paper, verifies referenced predicates exist with matching arity at the expected head commit, writes rule documents through head-bound family transactions, renders and lists rules, deletes rules, and manages superiority pairs while preventing strict-rule participation, duplicates, self-superiority, and cycles. Boundary: rule/predicate document schemas belong to family document modules and grounding predicate registry; this app module owns user-facing rule authoring workflow and conflict policy. Cleanup relevance: like predicates, the docstrings still say CLI even though the implementation is app-layer owner logic; the string parser is intentionally narrow and should not be treated as a full DeLP parser without extension.

### `propstore/app/sources.py`

Owner/subsystem: application-layer source authoring, proposal, sync, and lifecycle workflows.

This file owns source app request/report DTOs and wrappers for source branch creation, finalization, promotion, inspection, synchronization, provenance stamping, batch authoring, listing, and per-item proposal commands for concepts, claims, justifications, and stances. It delegates source branch mutations to `propstore.source`, validates app-specific inputs such as category value closure and claim/stance type coercion, auto-finalizes after batch writes, promotes source branches and forces a repository build afterward, exports source trees for sync, and lists source branches from the repository snapshot. Boundary: source-local storage and promotion semantics are in the source subsystem; compiler build verification is in compiler workflows; provenance stamping belongs to `propstore.provenance`; this module coordinates those as app workflows. Cleanup relevance: this is a broad facade over many source operations, but most heavy behavior is delegated; any CLI code should stay thin and call these typed workflows rather than reaching into source internals.

### `propstore/app/verify.py`

Owner/subsystem: application-layer artifact verification facade.

This file owns a single `verify_claim_tree` wrapper that delegates to `propstore.artifact_verification.verify_claim_tree`, passing through the repository, claim reference, and optional commit. Boundary: verification semantics are owned by the artifact verification module; this app file is only a stable adapter surface. Cleanup relevance: keep it shallow unless app-specific request/report types are needed for verification workflows.

### `propstore/app/world.py`

Owner/subsystem: application-layer world query and analysis workflows.

This file owns repository-bound app request DTOs and entry points for world status, concept query, binding, explanation, algorithm listing, derivation, resolution, hypothetical diffs, chains, graph export, sensitivity, fragility, and consistency. It opens/closes `WorldQuery`, maps missing sidecar files to `WorldSidecarMissingError`, constructs `Environment` and `RenderPolicy` values, augments world status with authored family counts, and delegates model algorithms to `propstore.world.queries` or specialized owner modules. Boundary: world algorithms, query reports, graph export, sensitivity, fragility, and consistency implementations live in their respective owner modules; this app module binds repository lifecycle and input normalization around them. Cleanup relevance: this is the central app facade for read-only world behavior; presentation adapters should not bypass it unless they are intentionally using lower-level world APIs.

### `propstore/app/world_atms.py`

Owner/subsystem: application-layer ATMS world inspection workflows.

This file owns ATMS-specific app request/report DTOs and functions for status, context, label verification, futures, why-out explanations, stability, relevance, interventions, and next-query suggestions. It binds the world with an ATMS `RenderPolicy`, resolves concept targets, serializes ATMS statuses/support/future witness structures into app-safe report objects, validates queryable assumptions and target statuses, and chooses claim-vs-concept paths based on whether the target resolves to an existing claim. Boundary: ATMS algorithms and engines live under `propstore.world`/`BoundWorld`; this module adapts those lower-level reports for app consumers and manages world model lifecycle. Cleanup relevance: `_bind_atms` manually enters/exits the context manager to return manager/world/bound together, so future refactors should preserve correct close behavior; several reports use `object` fields where stronger typed DTOs may eventually be useful.

### `propstore/app/world_reasoning.py`

Owner/subsystem: application-layer argumentation extension reports for bound worlds.

This file owns app DTOs and `world_extensions` for computing Dung-style extension reports over active claims under claim-graph, ASPIC, or probabilistic RAF backends. It binds the world for a requested environment, coerces active claims, summarizes stance inclusion, builds active claim lines, routes claim-graph and ASPIC backends through their respective framework/projection builders, rejects ATMS for extension-style queries, and returns grounded accepted/defeated claims, non-grounded extension sets, or probabilistic acceptance summaries. Boundary: framework construction, structured justification, PRAF calculation, stance analysis, and support metadata come from owner modules; this app module selects the backend and serializes the report. Cleanup relevance: backend-specific result coercion is concentrated here, which is useful, but several casts reflect loose cross-backend result types that could be tightened if the reasoning API is unified.

### `propstore/app/world_revision.py`

Owner/subsystem: application-layer support-revision workflows.

This file owns app request DTOs for revision world selection, expand/contract/revise/explain/iterated revise operations, plus display helpers for belief atoms and revision event inspection payloads. It lowers app world requests into support-revision workflow requests, opens the app world model, delegates revision operations to `propstore.support_revision.workflows`, validates operation-specific explain requirements, and serializes decision/realization/policy/diagnostic fields from revision events. Boundary: AGM/support-revision semantics, atom construction, entrenchment, realization, and iterated operators live in the support-revision subsystem; this module adapts those for repository-bound app calls. Cleanup relevance: many functions return owner-layer objects directly; if these are exposed through stable external APIs, stronger app-level report DTOs may be needed.

### `propstore/app/worldlines.py`

Owner/subsystem: application-layer worldline definition, materialization, diff, journal, and deletion workflows.

This file owns worldline app errors, request/report DTOs, policy/revision option coercion, JSON-safe value validation, and workflows for create, show, list, diff, materialize, build journal, inspect at a journal step, stale checking, and delete. It loads worldline family documents into `WorldlineDefinition`, validates reasoning backend/semantics combinations and revision operation requirements, converts app requests into worldline definitions, runs materialization through `propstore.worldline.run_worldline`, persists results/journals to the worldline family, and compares materialized inputs/values/dependencies between two worldlines. Boundary: worldline execution, staleness, journal capture, and policy profile semantics are owned by worldline/policy modules; this app module owns repository persistence and app-level validation. Cleanup relevance: worldline journals are correctly kept as semantic artifacts here rather than process-local state; some error messages still reference CLI commands but the workflow ownership is app-layer.

### `propstore/argumentation.py`

Owner/subsystem: argumentation-layer package marker.

This file contains only an architecture marker docstring. It owns no runtime behavior, imports, types, or functions. Boundary: actual argumentation logic lives in other modules such as claim graph, ASPIC bridge, PRAF, and structured projection. Cleanup relevance: this file is likely present to make an architectural boundary explicit; do not infer behavior from it.

### `propstore/artifact_codes.py`

Owner/subsystem: semantic artifact-code computation and stamping.

This file owns canonical hash computation for source, claim, justification, and stance artifacts plus helpers to stamp those codes back into typed documents. It hashes canonical document payloads using Quire canonical JSON SHA-256, removes existing `artifact_code` fields before hashing, canonicalizes claim payloads through claim identity version logic, sorts justification premises and related justification/stance code lists, and rewrites source-local or canonical documents through typed document conversion. Boundary: document schemas and claim canonicalization live in family modules; this module owns artifact-code composition and stamping for semantic identity. Cleanup relevance: `stamp_canonical_artifact_codes` builds justification/stance code maps but currently returns claims unchanged, unlike `stamp_source_artifact_codes`, so canonical claim artifact-code stamping may be intentionally deferred or incomplete and should be checked before relying on it.

### `propstore/artifact_verification.py`

Owner/subsystem: semantic artifact-code verification workflows.

This file owns `verify_claim_tree`, which verifies a claim and its recursive justification/stance/source neighborhood against semantic artifact codes. It loads canonical claims, sources, justifications, and stances from repository families; resolves unknown claim references through `WorldQuery` when available; recursively visits premise and stance-target claims; recomputes source, claim, justification, and stance artifact codes; reports mismatches; checks source origin content references against local paper files via `ni_uri_for_file`; and includes an ATMS label when a sidecar can be opened. Boundary: code computation is delegated to `artifact_codes`, claim file traversal comes from `propstore.claims`, and ATMS labels come from world APIs; this module composes verification output as dictionaries. Cleanup relevance: the output is loose `dict[str, Any]`; typed verification reports would reduce ambiguity if this becomes a stable API.

### `propstore/aspic_bridge/__init__.py`

Owner/subsystem: public ASPIC bridge package facade.

This file re-exports the ASPIC bridge API from build, grounding, lifting projection, projection, query, and translation modules. It also wraps `project_grounded_rules` to provide the default GUNRAY complement encoder while preserving an override hook. Boundary: implementation is in sibling modules and grounding complement modules; this file defines the import surface. Cleanup relevance: keep this facade shallow so importing the package does not become a hidden owner of bridge behavior.

### `propstore/aspic_bridge/build.py`

Owner/subsystem: ASPIC bridge compilation pipeline and CSAF assembly.

This file owns the shared pipeline that turns active claims, canonical justifications, stances, grounded rule bundles, and lifting decisions into ASPIC+/CSAF structures. It normalizes active claims, builds literals, projects lifting and grounded rules, creates contrariness and knowledge base entries, adds grounded facts as axioms, closes strict rules under transposition, builds preference configuration, computes arguments/attacks/defeats, filters preference-sensitive stance attacks/defeats, and assigns stable argument ids for a Dung framework inside the returned `CSAF`. Boundary: argumentation primitives come from the external `argumentation` package, while claim/lifting/grounding translation helpers live in sibling bridge modules; this module orchestrates compilation. Cleanup relevance: this is central bridge logic and intentionally more than a facade; changing stance preference filtering or complement encoding here changes ASPIC semantics.

### `propstore/aspic_bridge/extract.py`

Owner/subsystem: ASPIC bridge input harvesting helpers.

This file owns private helpers for extracting stance rows and canonical justifications for the active claim scope. It can harvest relation rows from an `ActiveWorldGraph` or from a stance store, filters relations to attack/support types, converts relation rows through the stance row projection model, prefers authored justifications when available, synthesizes reported-claim justifications, and falls back to active-graph or stance-derived support/explanation justifications. Boundary: active-claim graph, authored justification store, and stance store interfaces live in core modules; this file prepares bridge inputs. Cleanup relevance: the authored-justification path intentionally adds reported-claim justifications alongside authored ones, so bridge consumers get premises for claim reports even when authored rules exist.

### `propstore/aspic_bridge/grounding.py`

Owner/subsystem: ASPIC bridge grounded-rule projection.

This file owns `GroundedAspicProjection` and the helpers that project a `GroundedRulesBundle` into ASPIC strict/defeasible rules, axioms, origins, and rule-order preferences. It converts Gunray grounding inspection to an `argumentation.datalog_grounding` theory, handles empty bundles, extends the shared literal-key dictionary with grounded rules/facts, and injects grounded facts into the ASPIC knowledge base. Boundary: actual datalog-to-ASPIC translation is delegated to the `argumentation` package; propstore supplies its bundle envelope and source superiority metadata. Cleanup relevance: complement encoder parameters are accepted but currently deleted because the underlying grounding projection owns encoding; callers should not assume this function is doing local complement decoding.

### `propstore/aspic_bridge/lifting_projection.py`

Owner/subsystem: ASPIC projection of context-lifting decisions.

This file owns `LiftingProjectionRecord`, `LiftingProjection`, and `project_lifting_decisions`. It maps typed context-lifting decisions into `ist(context, proposition)` ASPIC literals, records source/target/status/mode metadata, and emits strict bridge rules or defeasible lifting rules only for decisions whose status is `LIFTED`. Boundary: context-lifting decision semantics come from `propstore.context_lifting`, while ASPIC `Literal` and `Rule` values come from the argumentation package; this module translates between them. Cleanup relevance: non-lifted decisions are preserved in records but do not affect rules, which is important for inspection versus reasoning behavior.

### `propstore/aspic_bridge/projection.py`

Owner/subsystem: caller-facing ASPIC structured projection.

This file owns the public conversion from compiled ASPIC CSAF objects into propstore `StructuredProjection` reports and the `build_aspic_projection` entry point. It derives projection atom ids/provenance/loss witnesses, maps ASPIC arguments to structured arguments with claim ids, premise/dependency claim ids, support metadata, strength, top rule kind, attackable kind, justification id, subargument ids, and projected attack/defeat frameworks. It also extracts stance rows and justifications from the provided store or active graph before building the CSAF. Boundary: ASPIC compilation is in `build.py`; active graph/store extraction is in `extract.py`; structured report types live in `propstore.structured_projection`; this module bridges them. Cleanup relevance: projection provenance depends on source assertion ids in active-claim attributes; missing source assertions are explicitly represented as projection loss rather than hidden.

### `propstore/aspic_bridge/query.py`

Owner/subsystem: goal-directed ASPIC bridge querying.

This file owns `ClaimQueryResult` and `query_claim`, a focused ASPIC query path for one claim/ground atom/literal key. It compiles the bridge context, resolves string claim references to context-aware `IstLiteralKey` values where possible, builds only arguments for the goal and attackers up to a depth limit, applies the same preference-sensitive stance attack/defeat filtering as full CSAF assembly, and separates arguments for and against the goal using contrary conclusions and attacks on goal subarguments. Boundary: bridge compilation is in `build.py` and argument construction/attack/defeat semantics come from the argumentation package. Cleanup relevance: ambiguous same-claim references across contexts are rejected rather than guessed, which preserves context precision for `ist` literals.

### `propstore/aspic_bridge/translate.py`

Owner/subsystem: claim-graph to ASPIC+ translation stages.

This file owns the lower-level translation functions that map active claims, justifications, stances, and metadata strength into ASPIC literals, rules, contrariness, knowledge bases, preference-sensitive pairs, and preference configuration. Claims become `ist(context, claim)` literals; non-reported justifications become strict or defeasible ASPIC rules; attack stances become contradictories, contraries, or rule-name undercuts with ambiguity checks; reported claims become axioms or premises; and preference order is built from explicit rule order plus metadata-strength premise comparisons under elitist or democratic behavior. Boundary: typed active claims and justifications are core objects, stance rows are coerced through family projection models, and ASPIC data structures come from the argumentation package. Cleanup relevance: ambiguity across contexts and ambiguous undercuts raise errors here, making this a key precision boundary for the bridge.

### `propstore/canonical_namespaces.py`

Owner/subsystem: reserved canonical namespace validation.

This file owns the reserved canonical namespace set (`ps`, `propstore`), the `ReservedNamespaceViolation` error, and small assertion helpers for rejecting source-local minting or aliases that target reserved namespaces. Boundary: this is an IO-boundary guard used by callers that accept source-local identifiers or aliases; it does not own concept identity itself. Cleanup relevance: keep reserved namespace policy centralized here so source-local and alias validators do not drift.

### `propstore/cel_bindings.py`

Owner/subsystem: standard synthetic CEL binding names.

This file owns the runtime contract list for synthetic CEL binding dimensions such as source, domain, source kind, origin type, name, framework, mode, and variant. It exposes both descriptions and an ordered tuple of names. Boundary: CEL parsing/type checking live elsewhere; this file only declares environment binding names used by authored/generated conditions. Cleanup relevance: add new standard synthetic bindings here rather than scattering string allowlists across validators.

### `propstore/cel_registry.py`

Owner/subsystem: typed CEL concept registry projection.

This file owns conversion from canonical concept records or sidecar concept rows into `ConceptInfo` entries used by CEL condition validation. It infers kind type from explicit row kind or form name, parses category form parameters and extensibility, validates non-empty ids/names, rejects duplicate canonical names or concept ids, and builds registries keyed by canonical name. Boundary: concept records/rows and form-to-kind inference come from family modules, while `ConceptInfo`/`KindType` belong to core condition registry. Cleanup relevance: this is the boundary that turns persisted concept data into CEL-visible type information; keep duplicate detection here so validators can assume registry uniqueness.

### `propstore/cel_types.py`

Owner/subsystem: typed carriers for authored CEL source.

This file owns `NewType` wrappers for CEL expression text and CEL registry fingerprints plus helpers to brand one or many raw values as `CelExpr`. It validates that authored CEL source is a string before branding. Boundary: parsing, validation, and registry construction are elsewhere; this module provides lightweight type distinctions. Cleanup relevance: use these carriers where APIs need to distinguish authored CEL source from arbitrary strings.

### `propstore/cel_validation.py`

Owner/subsystem: ingest-time CEL expression validation.

This file owns `CelIngestValidationError`, `CelExpressionLocation`, reusable single/batch CEL validation functions, and iterators that attach locations to claim conditions, context assumptions, and lifting-rule conditions. It delegates actual CEL type checking to `propstore.core.conditions.check_condition_ir`, wraps failures with artifact/field/index context, skips empty or non-string expressions in batch iteration, and fails fast before callers perform write-side operations. Boundary: CEL checker semantics and concept registry data live in core condition modules; this module is the authoring-boundary validator. Cleanup relevance: validation imports the condition frontend lazily to keep CLI import paths light, matching the root CLI laziness discipline.

### `propstore/claim_graph.py`

Owner/subsystem: store-based claim-graph reasoning entrypoints.

This file owns the public claim-graph backend entrypoints for building an argumentation framework and computing justified claims from a `WorldStore`. It delegates shared input construction and analysis to `propstore.core.analyzers`, resolves input claim ids to canonical ids while preserving display ids in results, validates backend/semantics combinations, and returns a single grounded extension or multiple preferred/stable extensions as appropriate. Boundary: graph construction/analyzer semantics live in core analyzers and the `argumentation.dung` framework type; this module exposes store-based claim-graph access. Cleanup relevance: the docstring warns this is a hybrid attack/defeat framework when attacks and defeats diverge, so downstream grounded evaluation must use the analyzer rather than ad hoc defeat pruning.

### `propstore/claims.py`

Owner/subsystem: typed claim artifact loading helpers.

This file owns helpers for loading single claim artifacts, decoding claim batch payloads into one-claim `LoadedDocument` entries, adapting old-style `claims:` batch payloads into canonical `ClaimDocument` values, and extracting filename, source paper, stage, claims tuple, and payload from either loaded documents or Quire artifact handles. Boundary: claim document schemas and batch specs live in family modules and Quire handles document decoding/loading; this module is a compatibility/loading helper around typed claim artifacts. Cleanup relevance: `claim_file_claims` now always returns a single document, while batch decoding creates synthetic filenames with `#index`; callers should not assume a loaded claim file contains multiple claim documents.

### `propstore/cli/__init__.py`

Owner/subsystem: root `pks` Click entry point and lazy command registry.

This file owns the top-level CLI group, command registry, quickstart/advanced command lists, command aliases, lazy repository lookup, lazy command import behavior, expected-error rendering, `--traceback` handling, and the `-C/--directory` option. It keeps root command discovery shallow by importing command modules only when a command is requested, exposes `status` as an alias to `world status`, wraps expected `ValueError`/`RuntimeError` failures into Click exceptions unless tracebacks are requested, and passes a lazy repository object through `ctx.obj` except for `init`. Boundary: command families live in sibling CLI modules/packages and app/domain logic should live outside CLI; this module is presentation and dispatch infrastructure. Cleanup relevance: it correctly follows the project rule that root CLI registration be lazy.

### `propstore/cli/claim/__init__.py`

Owner/subsystem: `pks claim` Click group and shared claim CLI helpers.

This file owns the claim command group, shared render-policy option decorator, and conversion from claim CLI flags into `AppRenderPolicyRequest`. It then imports split command modules after group/helper definitions so they can register subcommands. Boundary: claim app workflows and render policy semantics live in app modules; this package initializer is CLI presentation/registration only. Cleanup relevance: shared claim render flags are centralized here so display/analysis commands do not each recreate policy flag mapping.

### `propstore/cli/claim/analysis.py`

Owner/subsystem: claim analysis CLI adapter.

This file registers `pks claim compare`, parses two claim ids plus optional numeric `key=value` bindings, warns and skips non-numeric bindings, delegates comparison to `compare_algorithm_claims_from_repo`, maps expected app errors to CLI failures, and renders tier/equivalence/similarity/details lines. Boundary: algorithm claim comparison lives in `propstore.app.claims`; this module owns only Click parsing and text output. Cleanup relevance: CLI correctly avoids owning comparison semantics, but binding parsing is flag-shaped CLI code and belongs here.

### `propstore/cli/claim/display.py`

Owner/subsystem: claim display/search/neighborhood CLI adapter.

This file registers `pks claim show`, `list`, `search`, and `neighborhood`. It parses format/filter/render-policy options, delegates claim view/list/search and semantic neighborhood construction to app modules, maps missing sidecar and unknown claim errors to CLI failures, renders JSON through report `to_json`, and formats text/table output for claim details, visible claim lists, search results, and neighborhood moves/rows. Boundary: claim view and neighborhood semantics live in app modules; this file owns Click flags and terminal rendering. Cleanup relevance: `_render_claim_view` is presentation logic only and should not become semantic claim formatting used by non-CLI consumers.

### `propstore/cli/claim/embedding.py`

Owner/subsystem: claim embedding CLI adapter.

This file registers `pks claim embed` and `pks claim similar`. It parses claim/model/batch and similarity flags, builds progress callbacks for embedding runs, delegates embedding generation and similarity search to `propstore.app.claims`, maps expected sidecar/model/workflow errors to CLI failures, and renders simple progress/result lines. Boundary: embedding model registry, sidecar writes, and similarity search live in the app/sidecar layers; this module owns terminal command parsing and output. Cleanup relevance: model `"all"` has distinct progress and report rendering behavior here, which is CLI presentation rather than embedding semantics.

### `propstore/cli/claim/relation.py`

Owner/subsystem: claim relationship classification CLI adapter.

This file registers `pks claim relate`, validates mutually exclusive claim-id/`--all` usage, parses LLM/embedding/top-k/concurrency options, delegates relationship classification to `propstore.app.claims.relate_claims`, emits progress every ten processed claims or at completion, maps expected sidecar/workflow errors to CLI failures, and renders proposal commit summaries or stance lines. Boundary: embedding candidate selection, LLM classification, proposal writing, and branch semantics live in the app workflow; this module owns CLI flags and text output. Cleanup relevance: the command docstring explicitly says main branch is not mutated and proposals must be promoted separately, which is CLI-facing workflow explanation.

### `propstore/cli/claim/validation.py`

Owner/subsystem: claim validation/conflict CLI adapter.

This file registers `pks claim validate`, `validate-file`, and `conflicts`. It parses path/filter options, delegates claim validation and conflict detection to app workflows, maps path/document validation errors to CLI failures or validation exit codes, emits warnings/errors/success messages, and formats conflict rows with class, concept, claim ids, values, and derivation chain. Boundary: validation, loading, and conflict detection semantics live in `propstore.app.claims`; this module owns command parsing and terminal reporting. Cleanup relevance: validation exit-code handling is presentation behavior and should remain in CLI rather than app workflows.

### `propstore/cli/compiler_cmds.py`

Owner/subsystem: top-level compiler/build/alias CLI adapter.

This file registers `pks validate`, `pks build`, and `pks export-aliases`. It delegates validation/build/alias export to `propstore.app.compiler`, renders workflow messages, maps compiler workflow errors to validation exit codes, prints build conflict/phi/embedding snapshot diagnostics, and supports text or JSON alias output. Boundary: compiler workflows and derived-store creation live outside CLI; this module owns flags and terminal rendering. Cleanup relevance: phi-node glosses and build summaries are presentation details; build policy should stay in compiler workflows.

### `propstore/cli/concept/__init__.py`

Owner/subsystem: `pks concept` Click group registration.

This file owns the concept command group and imports split alignment, display, embedding, and mutation command modules after the group is defined so they can attach subcommands. Boundary: concept workflows live in app modules and sibling CLI modules render them. Cleanup relevance: keep this package initializer shallow; it is command registration infrastructure only.

### `propstore/cli/concept/alignment.py`

Owner/subsystem: concept alignment CLI adapter.

This file registers `pks concept align`, `query`, `decide`, and `promote`. It parses source lists, cluster ids, query modes/operators, and accept/reject decisions; delegates alignment build/query/decision/promotion to `propstore.app.concepts`; maps display/value errors to Click exceptions; and renders alignment ids, accepted arguments, or operator scores. Boundary: alignment artifact semantics and promotion logic live in app/source subsystems; this module owns command parsing and output. Cleanup relevance: `--sources` takes the first source as an option and remaining sources as positional arguments, which is a CLI shape only.

### `propstore/cli/concept/display.py`

Owner/subsystem: concept display/search/list CLI adapter.

This file registers `pks concept search`, `list`, `categories`, and `show`. It delegates FTS search, list/filter, category listing, and rendered concept/alignment display to app concept workflows; supports text/JSON output; maps missing sidecar and unknown concept/alignment errors to CLI messages; and renders simple tables or category value lists. Boundary: concept lookup/rendering/category semantics live in app/family modules; this file owns command flags and terminal output. Cleanup relevance: the `--json` alias and `--format json` both exist for categories, which is presentation compatibility only.

### `propstore/cli/concept/embedding.py`

Owner/subsystem: concept embedding CLI adapter.

This file registers `pks concept embed` and `pks concept similar`. It imports app embedding workflows lazily inside command functions, parses concept/model/batch/similarity flags, supplies a progress callback, delegates embedding and similarity operations to app concept workflows, maps expected sidecar/model/workflow/unknown-concept errors to CLI failures, and renders summary or hit lines. Boundary: embedding storage/search semantics live in app/sidecar layers; this file owns command presentation. Cleanup relevance: the lazy app imports keep concept CLI registration lighter and consistent with command-family laziness.

### `propstore/cli/concept/mutation.py`

Owner/subsystem: concept mutation CLI adapter.

This file registers concept mutation commands for add, alias, rename, deprecate, link, qualia-add, description-kind, proto-role, and add-value. It parses Click arguments/options, prompts for missing add-definition/form fields, lists available forms for prompting, parses comma-separated values, delegates all mutations to `propstore.app.concepts`, maps validation errors to validation exit output, maps mutation errors to general CLI failures, and renders warnings/lines from mutation reports. Boundary: concept document mutation, validation, CEL rewriting, and persistence live in the app concept workflows; this module owns CLI-specific prompting, flags, and text rendering. Cleanup relevance: command docstrings describe mutation behavior, but implementation should remain thin and not duplicate app-layer mutation logic.

### `propstore/cli/context.py`

Owner/subsystem: context and context-lifting CLI adapter.

This file registers `pks context` commands for add/list/show/remove/search and a nested `pks context lifting` group for list/show/add/update/remove. It parses context metadata, assumptions, parameters, perspective, dry-run/force flags, lifting rule source/conditions/mode/justification options, delegates all behavior to `propstore.app.contexts`, maps expected not-found/reference/workflow errors to CLI failures, encodes dry-run context documents, and renders success/warning/reference messages. Boundary: context document mutation, reference scanning, CEL validation, and lifting-rule semantics live in the app/context-lifting layers; this module owns Click presentation. Cleanup relevance: the update command enforces mutually exclusive clear/set flags at the CLI layer before building the app request.

### `propstore/cli/contracts.py`

Owner/subsystem: contract manifest CLI adapter.

This file registers `pks contract-manifest`, parses `--write` and optional output path, delegates manifest construction/writing to `propstore.contracts`, writes bytes to a requested output path when not using the canonical write helper, and emits success or manifest YAML to stdout. Boundary: contract manifest content and canonical path are owned by `propstore.contracts`; this module owns CLI file-output behavior. Cleanup relevance: direct `output.write_bytes` is command-specific export behavior, not source mutation.

### `propstore/cli/form.py`

Owner/subsystem: form definition CLI adapter.

This file registers `pks form` commands for list, search, show, add, remove, and validate. It parses dimensions JSON, dimensionless booleans, and common-alternative JSON into typed form request fields, delegates form workflows to `propstore.app.forms`, renders form YAML plus unit conversions and derived algebra, handles dry-run create/remove output, maps referenced/not-found/workflow errors to CLI failures, and prints validation results. Boundary: form document schema, algebra enrichment, reference scanning, and persistence live in app/family modules; this file owns Click parsing and terminal presentation. Cleanup relevance: unit conversion formatting and JSON option parsing are CLI-specific surfaces and should not become the canonical form API.

### `propstore/cli/grounding_cmds.py`

Owner/subsystem: grounding inspection CLI adapter.

This file registers the `pks grounding` group with status, show, query, arguments, and explain commands. It delegates grounding inspection to `propstore.app.grounding`, maps inspection errors to Click exceptions, and renders counts, facts, grounded rules, sections, matched atom status, arguments, explanations, and dialectical trees. Boundary: grounding surface construction and explanation logic live in the grounding owner layer; this module owns terminal presentation. Cleanup relevance: no grounding semantics are computed here, which keeps CLI aligned with the presentation-adapter rule.

### `propstore/cli/helpers.py`

Owner/subsystem: shared CLI parsing and exit helpers.

This file owns `parse_kv_pairs`, basic scalar coercion for CLI values, standard exit-code constants, `PropstoreClickError`, `fail`, and `exit_with_code`. It converts `key=value` arguments into dictionaries with optional bool/int/float coercion while returning non-key/value arguments separately, and provides a Click exception subclass with explicit exit code. Boundary: this is CLI infrastructure only; domain request parsing should still happen in app/domain layers where typed semantics exist. Cleanup relevance: use these helpers for repeated CLI failure/exit behavior rather than open-coding Click exits.

### `propstore/cli/history_cmds.py`

Owner/subsystem: repository history CLI adapter.

This file registers top-level `pks log`, `diff`, `show`, and `checkout`. It delegates log/diff/show/checkout report construction to `propstore.app.repository_history`, renders text or YAML logs, formats merge and per-file change details, maps branch/commit/concepts errors to Click failures, and implements checkout as sidecar rebuild only without changing git state. Boundary: history classification, git access, and sidecar rebuild semantics live in the app layer; this module owns command options and terminal output. Cleanup relevance: the checkout command docstring clearly constrains behavior to derived store rebuild, not repository branch switching.

### `propstore/cli/init.py`

Owner/subsystem: project initialization CLI adapter.

This file registers `pks init`, resolves the target directory relative to the root CLI `-C/--directory` start path when present, delegates repository initialization and seed import to `propstore.app.project_init.initialize_project`, maps init errors to Click exceptions, and renders already-initialized or initialized messages. Boundary: initialization, git store creation, and packaged seed commits live in the app/repository layers; this module owns CLI path resolution and text output. Cleanup relevance: it intentionally bypasses normal repository lookup through root CLI `ctx.obj["start"]`.

### `propstore/cli/materialize.py`

Owner/subsystem: repository materialization CLI adapter.

This file registers `pks materialize`, validates mutually exclusive `--commit`/`--branch`, builds a `MaterializeRequest` from directory/commit/branch/clean/force options, delegates projection to `propstore.app.materialize.materialize_repository`, maps materialize errors to Click exceptions, and renders source commit plus written/deleted/skipped/flag counts. Boundary: snapshot projection and conflict policy live in app/storage layers; this module owns CLI argument shape and reporting. Cleanup relevance: this command projects committed state to loose files; it should not grow repository mutation semantics beyond materialization flags.

### `propstore/cli/merge_cmds.py`

Owner/subsystem: formal repository merge CLI adapter.

This file registers the `pks merge` group with `inspect` and `commit` subcommands. It parses branch names, semantics, commit message, and optional target branch; delegates merge inspection/commit to `propstore.app.merge`; and emits the returned payload as YAML. Boundary: formal merge framework construction and storage merge commit semantics live in app/merge modules; this file owns CLI dispatch and rendering. Cleanup relevance: payloads are passed through as YAML, so typed formatting improvements should start in the app merge report model.

### `propstore/cli/micropub.py`

Owner/subsystem: micropublication inspection CLI adapter.

This file registers `pks micropub list`, `show`, and `lift`. It delegates listing, lookup, and lifting inspection to `propstore.app.micropubs`, renders micropublication tables or YAML payloads, maps not-found errors to CLI failures, and exits with error when a lift inspection finds no lifted decision. Boundary: micropublication documents and context lifting decisions live in app/family/context-lifting modules; this file owns command output and exit behavior. Cleanup relevance: the lift command's non-lifted exit code is CLI policy, not lifting semantics.

### `propstore/cli/observatory.py`

Owner/subsystem: epistemic observatory CLI adapter.

This file registers `pks observatory run`, loads one or more JSON fixture files into `EvaluationScenario` values, delegates evaluation to `propstore.app.observatory.run_observatory`, supports text or JSON report output, and renders scenario pass/fail lines with operator family and policy id. Boundary: observatory scenario semantics and evaluation live in app/observatory modules; this file owns fixture file parsing and CLI output. Cleanup relevance: fixture JSON validation errors are converted to Click exceptions at the file boundary.

### `propstore/cli/output/__init__.py`

Owner/subsystem: shared CLI output helper facade.

This file re-exports console, section, table, and YAML output helpers under one CLI output import surface. It owns no rendering behavior beyond the package API. Boundary: implementation is in sibling output modules. Cleanup relevance: keep this shallow so output helper imports remain predictable.

### `propstore/cli/output/console.py`

Owner/subsystem: Rich-backed CLI console emission.

This file owns the base `emit`, `emit_error`, `emit_warning`, and `emit_success` helpers. It constructs a Rich `Console` for stdout or stderr with markup/highlighting disabled, stable width, and soft wrapping, then prints stringified messages with optional newline control. Boundary: higher-level section/table/YAML helpers build on this; this file owns raw terminal emission only. Cleanup relevance: disabled markup preserves literal CLI output under tests and capture.

### `propstore/cli/output/sections.py`

Owner/subsystem: reusable CLI section and key/value rendering helpers.

This file owns `emit_section` and `emit_key_values`, which render optional section titles, indented line iterables, and non-None key/value rows through the base console emitter. Boundary: it is presentation infrastructure only. Cleanup relevance: keep repeated simple section formatting here instead of duplicating indentation loops in command modules.

### `propstore/cli/output/tables.py`

Owner/subsystem: stable plain-text CLI table rendering.

This file owns `emit_table`, a small renderer that calculates column widths from headers and rows, emits headers/separators, handles empty rows with optional header and empty message, and supports indentation. Boundary: it is CLI presentation infrastructure only. Cleanup relevance: this avoids bringing table semantics into command modules and keeps output deterministic.

### `propstore/cli/output/yaml.py`

Owner/subsystem: structured YAML CLI output helper.

This file owns `emit_yaml`, which renders arbitrary values through Quire's YAML renderer and emits the result with optional stripping and newline preservation. Boundary: YAML serialization is delegated to Quire; this module provides the CLI output wrapper. Cleanup relevance: command modules that need structured YAML should use this helper rather than direct serializer calls.

### `propstore/cli/predicate/__init__.py`

Owner/subsystem: `pks predicate` Click group registration.

This file owns the predicate command group and imports display/mutation command modules after the group is defined so they can register subcommands. Boundary: predicate authoring workflows live in app modules; this package initializer is CLI registration only. Cleanup relevance: keep this shallow like other command-family initializers.

### `propstore/cli/predicate/display.py`

Owner/subsystem: predicate display CLI adapter.

This file registers `pks predicate list` and `show`. It delegates predicate listing/rendering to `propstore.app.predicates`, maps not-found errors to CLI failures, and renders a table or raw predicate document text. Boundary: predicate storage and rendering are app/family responsibilities; this module owns terminal presentation. Cleanup relevance: command behavior is intentionally thin.

### `propstore/cli/predicate/mutation.py`

Owner/subsystem: predicate mutation CLI adapter.

This file registers `pks predicate add` and `remove`. It parses authoring group, predicate id, arity, argument types, derived-from, and description options into app predicate requests, delegates add/remove to `propstore.app.predicates`, maps workflow errors to CLI failures, and renders created/removed summaries. Boundary: predicate validation, conflict detection, and persistence live in the app predicate workflow; this module owns command flags and output. Cleanup relevance: the optional `--file` flag is authoring metadata, not storage identity.

### `propstore/cli/proposal.py`

Owner/subsystem: proposal promotion and heuristic proposal CLI adapter.

This file registers `pks proposal promote`, predicate proposal declare/promote commands, and rule proposal propose/promote commands. It delegates stance proposal planning/promotion to `propstore.app.proposals`, loads optional mock LLM fixtures, invokes heuristic predicate/rule extraction lazily, delegates predicate/rule proposal promotion to proposal owner modules, prompts before stance proposal promotion unless `--yes`, and renders proposal plans, declarations, rejections, and promotion summaries. Boundary: proposal branch discovery, promotion, LLM extraction, and family persistence live outside CLI; this module owns command shape, confirmation, fixture reading, and text output. Cleanup relevance: this file mixes multiple proposal families in one CLI module, but core behavior is still delegated.

### `propstore/cli/repository_import_cmd.py`

Owner/subsystem: repository import CLI adapter.

This file registers `pks import-repository`, parses a source repository path plus optional target branch and message, delegates import execution to `propstore.app.repository_import.import_repository`, maps import errors to Click exceptions, and emits the result as YAML. Boundary: import planning and commit semantics live in the app/importing layer; this module owns CLI argument parsing and structured output. Cleanup relevance: source path validation is Click-level file-system input handling.

### `propstore/cli/rule/__init__.py`

Owner/subsystem: `pks rule` Click group registration.

This file owns the rule command group and imports display/mutation command modules after the group is defined so they can register subcommands. Boundary: rule authoring workflows live in app modules; this initializer is CLI registration infrastructure. Cleanup relevance: keep it shallow.

### `propstore/cli/rule/display.py`

Owner/subsystem: rule display CLI adapter.

This file registers `pks rule list` and `show`. It delegates rule listing/rendering to `propstore.app.rules`, maps not-found errors to CLI failures, and renders a table or raw rule document. Boundary: rule storage/rendering is app/family behavior; this module owns terminal presentation. Cleanup relevance: intentionally thin display adapter.

### `propstore/cli/rule/mutation.py`

Owner/subsystem: rule and rule-superiority mutation CLI adapter.

This file registers `pks rule add/remove` and nested `pks rule superiority add/list/remove`. It parses rule metadata, paper, id, kind, head/body atom DSL strings, superiority pairs, and optional authoring group metadata; delegates rule and superiority mutations/listing to `propstore.app.rules`; maps workflow errors to CLI failures; and renders success/table summaries. Boundary: rule parsing, predicate validation, acyclicity checks, and persistence live in app rule workflows; this module owns command flags and text output. Cleanup relevance: `--file` on superiority remove is explicitly ignored for command symmetry, confirming it is not storage identity.

### `propstore/cli/source/__init__.py`

Owner/subsystem: `pks source` Click group registration.

This file owns the source command group and imports source authoring, batch, lifecycle, and proposal command modules after the group is defined so they can register subcommands. Boundary: source lifecycle and mutation workflows live in app/source modules; this initializer is CLI registration infrastructure. Cleanup relevance: keep it shallow.

### `propstore/cli/source/authoring.py`

Owner/subsystem: source notes/metadata authoring CLI adapter.

This file registers `pks source write-notes` and `write-metadata`. It parses source name and an existing file path, delegates notes/metadata commits to `propstore.app.sources`, and renders the target source branch. Boundary: source-local authoring and commit behavior live in source/app workflows; this module owns CLI path parsing and success output. Cleanup relevance: intentionally narrow adapter.

### `propstore/cli/source/batch.py`

Owner/subsystem: source batch ingestion CLI adapter.

This file registers source batch commands for add-concepts, add-claim, add-justification, and add-stance. It parses source name, batch file, reader/method metadata, and optional default claim context, delegates batch commits to `propstore.app.sources`, maps `ValueError` to Click exceptions, and renders branch plus auto-finalization messages. Boundary: batch parsing, source-local writes, provenance/default-context handling, and finalization live in source/app workflows; this module owns command flags and output. Cleanup relevance: the singular command names (`add-claim`, etc.) wrap batch files, so CLI text should stay clear about batch semantics.

### `propstore/cli/source/lifecycle.py`

Owner/subsystem: source branch lifecycle CLI adapter.

This file registers source lifecycle commands for init, finalize, promote, status, list, sync, and deprecated stamp-provenance. It parses source metadata/origin/content paths, strict promotion, sync destination, and provenance flags; delegates all operations to `propstore.app.sources`; maps compiler workflow messages and value errors to CLI failures; renders promotion summaries, sidecar promotion-status diagnostics tables, source branch lists, sync results, and deprecation warnings. Boundary: source branch creation/finalization/promotion/status/sync/provenance behavior lives in app/source/compiler layers; this module owns command parsing and terminal output. Cleanup relevance: source status text documents partial-promotion diagnostics, but the underlying sidecar semantics remain outside CLI.

### `propstore/cli/source/proposal.py`

Owner/subsystem: source-local concept/claim/justification/stance proposal CLI adapter.

This file registers source proposal commands for concepts, claims, justifications, and stances. It parses source names, concept definitions/form/category values, claim fields/conditions/evidence pointers, justification premises/rule/attack target fields, and stance source/target/type/strength/note; delegates proposal writes to `propstore.app.sources`; maps app/value errors to Click exceptions; and renders success summaries including linked concept status and resolved justification premises. Boundary: source-local proposal document construction and persistence live in source/app workflows; this module owns CLI argument shape and output. Cleanup relevance: comma-separated concept values and premises are CLI input conveniences, not domain representation.

### `propstore/cli/verify.py`

Owner/subsystem: semantic verification CLI adapter.

This file registers `pks verify tree`, parses a claim reference and optional commit, delegates verification to `propstore.app.verify.verify_claim_tree`, maps unknown/invalid references to Click exceptions, and emits the report as YAML. Boundary: artifact tree verification lives in artifact verification/app modules; this module owns CLI dispatch and YAML output. Cleanup relevance: intentionally thin adapter.

### `propstore/cli/web.py`

Owner/subsystem: web server CLI adapter.

This file registers `pks web`, parses host/port/open/insecure options, refuses public network binds unless `--insecure` is supplied, creates the web app for the repository root, optionally opens a browser, prints URLs, and runs Uvicorn. Boundary: web app construction lives in `propstore.web.app`; this module owns server invocation and CLI safety checks. Cleanup relevance: public-bind guard is CLI safety policy for a no-auth read-only server.

### `propstore/cli/world/__init__.py`

Owner/subsystem: `pks world` Click group and shared world CLI helpers.

This file owns the world command group, a helper for formatting assumption ids, and `parse_world_binding_args`, which splits raw CLI tokens into `key=value` bindings and an optional positional target. It imports split analysis, ATMS, query, reasoning, and revision modules after group/helper definitions. Boundary: world workflows live in app modules; this package initializer is CLI registration plus small input formatting/parsing utilities. Cleanup relevance: binding parsing is CLI-specific and intentionally separate from typed app requests.

### `propstore/cli/world/analysis.py`

Owner/subsystem: analysis-oriented world CLI adapter.

This file registers world commands for hypothetical diffs, derivation chains, graph export, sensitivity, fragility, and consistency checks. It parses world binding tokens, lifecycle render-policy flags, hypothetical synthetic-claim JSON, output formats, graph output paths, fragility ranking/skip flags, and consistency transitive mode; delegates all analysis to `propstore.app.world`; writes export files with exclusive create; and renders JSON, tables, summaries, transitions, chains, sensitivity rows, fragility interactions, and conflict reports. Boundary: world analysis algorithms live in app/world/graph/sensitivity/fragility/consistency layers; this module owns CLI parsing and presentation. Cleanup relevance: `_write_new_text_file` prevents accidental overwrite for graph export, a CLI file-safety policy.

### `propstore/cli/world/atms.py`

Owner/subsystem: ATMS-oriented world CLI adapter.

This file registers nested `pks world atms` commands for status, context, verify, futures, why-out, stability, relevance, interventions, and next-query. It parses bindings/context/queryable/target-status/limit inputs, delegates ATMS inspection and planning to `propstore.app.world_atms`, formats support ids, future witnesses, why-out reports, relevance pairs, intervention plans, and next-query suggestions, and maps validation failures or ATMS verification errors to Click/validation exits. Boundary: ATMS algorithms and report construction live in app/world layers; this module owns CLI presentation and input shape. Cleanup relevance: intervention commands explicitly label their output as bounded additive plans, not revision/contraction.

### `propstore/cli/world/query.py`

Owner/subsystem: basic world query CLI adapter.

This file registers world status, query, bind, explain, and algorithms commands. It parses lifecycle render-policy flags, concept/claim ids, binding tokens, stage/concept filters, and output format; delegates to `propstore.app.world`; maps ambiguous/unknown concept or claim errors to CLI failures; and renders counts, concept claim lists, active/bound claims, stance chains, and algorithm claim tables or JSON reports. Boundary: world model querying, lifecycle visibility, and report construction live in app/world layers; this file owns CLI presentation. Cleanup relevance: render-policy flags are translated to `AppRenderPolicyRequest` here and should stay synchronized with claim display policy flags.

### `propstore/cli/world/reasoning.py`

Owner/subsystem: reasoning-oriented world CLI adapter.

This file registers `pks world derive`, `resolve`, and `extensions`. It parses bindings, lifecycle visibility flags, resolution strategy/backend/semantics/PRAF/opinion options, extension backend/context/options, and output formats; delegates derivation/resolution to `propstore.app.world` and extensions to `propstore.app.world_reasoning`; maps unsupported extension backends and resolve errors to CLI failures; and renders values, formulas, winners, probabilities, stance summaries, grounded accepted/defeated sets, and non-grounded extension groups. Boundary: derivation/resolution/reasoning semantics live in app/world/argumentation layers; this module owns CLI input shape and text labels. Cleanup relevance: `_claim_label` and grouping helpers are presentation-only summaries of claim extension reports.

### `propstore/cli/world/revision.py`

Owner/subsystem: revision-oriented world CLI adapter.

This file registers nested `pks world revision` commands for base, entrenchment, expand, contract, revise, explain, iterated-state, and iterated-revise. It parses binding/context tokens, revision atom JSON, targets/conflicts, and iterated operator choices; delegates all revision operations to `propstore.app.world_revision`; formats belief atoms, assumptions, formal decisions, support realization, explanations, epistemic state, ranking deltas, and history; and maps invalid atom JSON or revision validation errors to Click exceptions. Boundary: support-revision semantics, entrenchment, realization, and iterated operators live in support-revision/app layers; this module owns CLI parsing and display. Cleanup relevance: `format_revision_event_inspection` provides reusable text lines for persisted revision-event inspection payloads.

### `propstore/cli/worldline/__init__.py`

Owner/subsystem: `pks worldline` Click group and shared worldline CLI helpers.

This file owns the worldline command group, JSON-safe CLI value coercion, key=value parsing for bindings/overrides, revision atom JSON parsing, shared reasoning option decorators, and shared revision option decorators. It imports display, journal, materialize, and mutation modules after defining the group/decorators. Boundary: worldline validation/execution lives in app worldline modules; this package initializer owns CLI input coercion and option reuse. Cleanup relevance: typed JSON value guards prevent arbitrary Python objects from leaking into worldline definitions from CLI parsing.

### `propstore/cli/worldline/display.py`

Owner/subsystem: worldline display/list/diff CLI adapter.

This file registers `pks worldline show`, `list`, and `diff`. It delegates show/list/diff to `propstore.app.worldlines`, maps not-found/validation errors to CLI failures, renders worldline inputs, targets, revision queries, materialized results, staleness, target values, derivation trace, sensitivity, defeated claims, revision results, dependencies, list entries, and side-by-side input/value/dependency differences. Boundary: worldline definition/result/diff semantics live in app/worldline modules; rendering helpers for values/traces live in `worldline.rendering`; this module owns terminal composition. Cleanup relevance: display includes a prompt-like hint to run materialization when results are absent, but does not perform it.

### `propstore/cli/worldline/journal.py`

Owner/subsystem: worldline journal CLI adapter.

This file registers `pks worldline build-journal` and `at-step`. It delegates journal capture and step projection to `propstore.app.worldlines`, maps validation errors to CLI failures, renders build success with step count, and prints accepted claim ids at a requested journal step. Boundary: journal capture/projection semantics live in app/worldline/world modules; this module owns command parsing and output. Cleanup relevance: `at-step` uses raw `click.echo` for claim ids, a simple stream output choice.

### `propstore/cli/worldline/materialize.py`

Owner/subsystem: worldline create/run/refresh CLI adapter.

This file registers `pks worldline create`, `run`, and `refresh`. It parses bindings, overrides, targets, strategy, context, shared reasoning options, and shared revision options; coerces override values to floats or strings; builds `WorldlineCreateRequest` or `WorldlineRunRequest`; delegates creation/materialization to `propstore.app.worldlines`; renders creation/materialization summaries and target values; and implements refresh by invoking run with extracted default option values. Boundary: worldline definition construction, validation, and execution live in app/worldline modules; this file owns CLI parsing and invocation mechanics. Cleanup relevance: `run` intentionally ignores CLI options when a saved worldline exists, as documented in the command docstring.

### `propstore/cli/worldline/mutation.py`

Owner/subsystem: worldline deletion CLI adapter.

This file registers `pks worldline delete`, delegates deletion to `propstore.app.worldlines.delete_worldline`, maps not-found errors to CLI failure, and renders a success message. Boundary: worldline persistence/deletion semantics live in the app worldline workflow; this module owns command output. Cleanup relevance: intentionally narrow mutation adapter.

### `propstore/cli/worldline/rendering.py`

Owner/subsystem: CLI-local worldline rendering helpers.

This file owns formatting helpers for worldline target values, result target-value lines, derivation trace lines, and sensitivity lines. It turns worldline result objects into concise terminal strings with optional formulas, winning claims, derivation claim ids, and sensitivity errors/partials/elasticities. Boundary: worldline result data structures live in `propstore.worldline`; this module owns CLI-only string formatting. Cleanup relevance: keep these helpers presentation-only and separate from worldline result semantics.

### `propstore/compiler/__init__.py`

Owner/subsystem: compiler package public facade.

This file re-exports compilation context builders and core compiler IR types such as compilation bundles, semantic claims, semantic claim files, semantic stances, and resolved references. It owns no behavior beyond package API aggregation. Boundary: implementation lives in `context.py` and `ir.py`. Cleanup relevance: keep this shallow to avoid import coupling in compiler consumers.

### `propstore/compiler/context.py`

Owner/subsystem: shared canonical compilation context and registries.

This file owns `CompilationContext` and builders for immutable compiler symbol tables from loaded concept/form/claim data or from a repository commit. It builds form registries, context id sets, concept records keyed by artifact id, Quire family reference indexes for concepts and claims, CEL registries with standard synthetic bindings, concept/claim match-kind helpers, concept form lookup, authored concept registry payloads, and enriched concept lookup maps used by validators/builders. Boundary: concept/form/claim parsing and reference-index primitives live in family/Quire modules; this compiler module assembles them into compilation context. Cleanup relevance: it freezes most registry maps to protect compiler consumers from accidental mutation; `build_authored_concept_registry` still returns mutable payload dictionaries for validator compatibility.

### `propstore/compiler/errors.py`

Owner/subsystem: compiler workflow error carrier.

This file owns `CompilerWorkflowError`, an exception that carries a human summary and the associated workflow messages. Boundary: workflow diagnostics are built elsewhere; this type packages them for app/CLI callers. Cleanup relevance: simple error container.

### `propstore/compiler/ir.py`

Owner/subsystem: semantic compiler intermediate representation.

This file owns dataclasses for semantic stances, semantic claims, semantic claim files, and claim compilation bundles. The IR carries loaded/normalized claim entries, resolved claim documents, concept/variable/parameter references, bound stance targets, checked conditions, diagnostics, and an `ok` property that checks for error diagnostics. Boundary: reference resolution comes from Quire, claim documents from family schemas, conditions from core checking, and diagnostics from semantic passes; this module defines the compiler data shape. Cleanup relevance: `SemanticStance.data` and `SemanticClaim.authored_claim` are still loose dictionaries, likely reflecting IO-boundary/authored-payload compatibility.

### `propstore/compiler/workflows.py`

Owner/subsystem: repository-level compiler validation and build orchestration.

This file owns validation/build report dataclasses and the `validate_repository`/`build_repository` workflows. It loads concept/form/claim/context family artifacts, catches schema errors as diagnostics, runs form/concept/claim/context pipelines, builds compilation contexts and CEL registries, enforces CEL structural-concept invariants for claims and contexts before build, collects authoring lints, optionally promotes lints to errors, materializes the world sidecar with checked bundles and diagnostics, records embedding snapshot information, queries the sidecar for conflict/phi counts, and returns build summaries with derived-store handles. Boundary: individual semantic passes, family schemas, sidecar materialization, conflict detection, and world querying live in their owner modules; this module decides orchestration order and report composition. Cleanup relevance: this is the right owner for compiler workflow policy; CLI modules should only render these reports.

### `propstore/concept_ids.py`

Owner/subsystem: numeric concept id allocation and counter storage.

This file owns discovery, reservation, and recording of numeric `conceptN` ids. It extracts numeric ids from concept logical ids or artifact ids, detects namespace ambiguity, falls back to scanning concept documents, stores a monotonic counter under a dedicated git ref, reserves ids with compare-and-set retry logic, and uses a process lock plus Dulwich ref operations to handle concurrent writers. Boundary: concept documents/family iteration provide existing ids, while GitStore/Dulwich own ref/blob storage; this module owns allocation policy. Cleanup relevance: namespace ambiguity is explicitly raised when multiple namespaces disagree, preventing silent reuse of an unclear numeric id.

### `propstore/condition_classifier.py`

Owner/subsystem: CEL condition classification for conflict detection.

This file owns `classify_conditions`, which classifies two differing-value claim condition sets as conflict, phi-node, overlap, or unknown. It treats identical sorted condition lists as direct conflicts, otherwise requires a CEL registry, type-checks CEL into checked condition sets, asks the Z3-backed condition solver for equivalence and disjointness, maps solver unknown/unsat/sat results to conflict classes, and fails on unexpected solver result types. Boundary: CEL parsing/checking and solver behavior live in core condition modules; this module owns conflict-detector classification policy. Cleanup relevance: Z3 absence or missing registry is a hard error rather than heuristic fallback, which preserves semantic precision.

### `propstore/conflict_detector/__init__.py`

Owner/subsystem: conflict detector package facade.

This file re-exports conflict model types and lazy wrapper entrypoints for direct and transitive conflict detection. It routes direct conflict detection to `orchestrator.detect_conflicts` and transitive conflict detection to `parameterization_conflicts.detect_transitive_conflicts`, passing through concept/CEL registries, lifting system, and optional forms. Boundary: implementation lives in sibling conflict detector modules. Cleanup relevance: lazy imports avoid pulling the full detector graph when only types or facade functions are needed.

### `propstore/conflict_detector/algorithms.py`

Owner/subsystem: algorithm-claim conflict detection.

This file owns pairwise conflict detection for algorithm claims grouped by concept. It extracts algorithm claims, compares algorithm bodies with `ast_equiv` using variable-to-concept bindings, skips parse/equivalence failures, records non-equivalence with similarity/tier derivation details, first attempts context/lifting-aware classification, and otherwise classifies condition overlap with the CEL condition classifier. Boundary: algorithm AST equivalence is external, collection/context helpers live in sibling modules, and conflict records/models live in `models.py`; this module owns algorithm-specific detector logic. Cleanup relevance: parse/comparison failures are logged and skipped, so detector output is conservative rather than blocking on unparseable algorithm bodies.

### `propstore/conflict_detector/collectors.py`

Owner/subsystem: conflict-detector claim conversion and grouping helpers.

This file owns conversion from claim payloads/files to `ConflictClaim` values and grouping helpers for measurement, parameter, equation, and algorithm claims. It adds source-paper metadata when missing, injects source conditions, groups measurements by target concept and measure, parameters by output concept, equations by normalized equation signature, and algorithms by output concept or first variable concept. Boundary: claim file traversal lives in `propstore.claims`, equation signature logic is external/neighboring, and conflict claim schema lives in `models.py`. Cleanup relevance: these private grouping helpers define which claims enter each detector family.

### `propstore/conflict_detector/context.py`

Owner/subsystem: context-aware conflict classification helpers.

This file owns private helpers that decide whether two otherwise conflicting claims should be classified as `CONTEXT_PHI_NODE` because they live in different contexts without a lifted bridge. It filters lifting decisions to lifted ones, checks opposite-direction lift decisions for each claim, extracts claim context ids, and appends context-classified `ConflictRecord` rows. Boundary: lifting semantics come from `propstore.context_lifting`; detector-specific record shape comes from conflict models. Cleanup relevance: this is the shared place that prevents detector families from duplicating context/lifting checks.

### `propstore/conflict_detector/equation_inputs.py`

Owner/subsystem: equation-equivalence input adapter.

This file owns `bound_equation_from_conflict_claim`, converting a `ConflictClaim` equation expression and variables into the external `eq_equiv.BoundEquation` shape with `EquationSymbolBinding` entries. Boundary: conflict claim schema is local, equation equivalence data structures are external. Cleanup relevance: small adapter keeps external equation API coupling out of collectors/detectors.

### `propstore/conflict_detector/equations.py`

Owner/subsystem: equation-claim conflict detection.

This file owns pairwise conflict detection for equation claims grouped by equation signature. It compares bound equations with `eq_equiv`, skips failures/equivalent/incomparable results, records unknown comparison status as `UNKNOWN`, determines the dependent concept from reported dependent variables when possible, applies context/lifting-aware classification before CEL condition classification, and logs equation comparison failures. Boundary: equation equivalence is external, grouping/input conversion/context helpers are sibling modules, and conflict records live in models. Cleanup relevance: incomparable equations are intentionally skipped rather than reported as conflicts.

### `propstore/conflict_detector/measurements.py`

Owner/subsystem: measurement-claim conflict detection.

This file owns pairwise conflict detection for measurement claims grouped by target concept and measure. It skips value-compatible pairs, applies context/lifting-aware classification first, treats differing listener populations as phi nodes, otherwise classifies condition overlap with the CEL condition classifier, and records value strings for incompatible measurements. Boundary: measurement grouping is in collectors, value compatibility/rendering is in `value_comparison`, and conflict records are in models. Cleanup relevance: listener-population mismatch is handled as contextual branching rather than a direct hard conflict.

### `propstore/conflict_detector/models.py`

Owner/subsystem: shared conflict detector data models.

This file owns `ConflictClaimVariable`, `ConflictClaim`, `ConflictClass`, conflict-class coercion, and `ConflictRecord`. It parses authored claim payloads into detector-friendly typed objects, extracts context ids from flat or mapping payloads, brands conditions as `CelExpr`, parses variables, appends a source-paper CEL condition when available, defines detector warning classes, and stores final conflict records. Boundary: this is detector-local representation, not canonical claim schema; canonical claim documents are adapted into it by collectors. Cleanup relevance: `ConflictRecord` is mutable while most input models are frozen, so downstream consumers should avoid mutating emitted records casually.

### `propstore/conflict_detector/orchestrator.py`

Owner/subsystem: top-level conflict detection orchestration.

This file owns the main `detect_conflicts` pipeline and supporting helpers for synthetic CEL concepts, lifted-claim expansion, concept-form extraction, and concept registry validation. It validates the concept registry, injects synthetic CEL categories for source and standard bindings, rejects synthetic-name collisions, builds one condition solver, expands claims through applicable context-lifting rules, runs parameter/measurement/equation/algorithm detectors, adds parameterization conflicts, and shares forms/concept-form maps with parameter detection. Boundary: individual detector families live in sibling modules, CEL solver/checking is in core conditions, and lifting semantics come from context lifting. Cleanup relevance: this is the central place where source-paper conditions and synthetic bindings become solver-visible, so changes here affect all detector families.

### `propstore/conflict_detector/parameter_claims.py`

Owner/subsystem: direct parameter-claim conflict detection.

This file owns detection of incompatible parameter claims grouped by output concept. It builds/uses a condition solver, prepares checked condition sets, partitions more-than-two claims into equivalent condition classes, compares values with unit/form-aware compatibility, applies context/lifting-aware classification before recording conflicts, uses direct pairwise classification for small groups, marks equivalent-condition incompatible values as hard conflicts, and classifies cross-class overlaps via solver disjointness. Boundary: value compatibility is in `value_comparison`, condition solving is in core conditions, and grouping/context/model helpers are sibling modules. Cleanup relevance: Z3 partition/disjointness translation failures are promoted to runtime errors rather than downgraded, preserving detector correctness.

### `propstore/conflict_detector/parameterization_conflicts.py`

Owner/subsystem: parameterization-derived and transitive conflict detection.

This file owns derived-value conflict detection from concept parameterization relationships. It defines `DerivedConflictValue`, normalizes direct parameter claim values with form/unit conversion, evaluates sympy parameterizations with concept alias rewriting, merges contexts through lifting rules, merges conditions, derives exact relationship outputs from direct input states, compares derived values against direct claims, records `PARAM_CONFLICT` or context phi nodes, and computes transitive multi-hop derived conflicts across parameterization groups. Boundary: value comparison, dimensions normalization, propagation evaluation, parameterization groups/walks, and context lifting are owner modules outside this detector. Cleanup relevance: only exact relationships are used for direct parameterization conflicts, while transitive detection walks exact and approximate edges but only reports states with at least two hops.

### `propstore/context_lifting.py`

Owner/subsystem: first-class context references and explicit lifting rules.

This file owns the McCarthy/Guha-style context lifting model: `IstProposition`, lifting modes/statuses, lifting rules, lifting exceptions, decision provenance, lifting decisions, lifted assertions, and `LiftingSystem`. It validates contexts/rules/exceptions/assumptions, computes effective assumptions, evaluates rule conditions through an exception-pattern/condition solver, materializes lifted assertions only for lifted decisions, reports blocked/unknown decisions with provenance and nogood witnesses, applies explicit exception defeats, and supports querying decisions between source/target contexts for a proposition. Boundary: condition solving, defeasibility exception construction, provenance polynomials, and context id types live in core/defeasibility/provenance modules; this module owns context-lifting semantics. Cleanup relevance: there is no ancestry-based default visibility; cross-context visibility exists only through authored rules and successful condition/exception evaluation.

### `propstore/contracts.py`

Owner/subsystem: propstore semantic contract manifest generation.

This file owns contract-version constants, document-schema version overrides, the canonical checked-in manifest path, iterators for artifact families, semantic foreign keys, claim-type contracts, semantic pass classes, semantic stage contracts, document schema types, and functions to build/write a Quire `ContractManifest`. It introspects msgspec document structs, family registry entries, foreign key specs, claim type contracts, pipeline stage/pass definitions, and callback identities into structured contract entries. Boundary: family registries, document schemas, semantic passes, and Quire contract types own their data; this module assembles the manifest. Cleanup relevance: schema version overrides are centralized here and must be updated when document contracts intentionally change.

### `propstore/core/__init__.py`

Owner/subsystem: core package import boundary.

This file intentionally exports nothing and documents that callers should import concrete core modules directly. Boundary: core submodules own their own APIs; this package initializer avoids eager re-exports and broad runtime coupling. Cleanup relevance: keep it empty to preserve shallow imports.

### `propstore/core/activation.py`

Owner/subsystem: graph-native claim activation over compiled semantic graphs.

This file owns activation checks for claim nodes and active claims under a bound environment. It converts environment bindings/assumptions into CEL conditions, checks context projection through explicit lifting rules, materializes possible lifted assertions, augments condition solver registries with standard/binding synthetic concepts, detects unknown CEL concepts with source-artifact context, tests condition disjointness through the solver, retries after Z3 translation errors with standard bindings, and builds `ActiveWorldGraph` active/inactive claim id sets. Boundary: condition parsing/solving, environment labels, context lifting, and graph types live in core/context modules; this module owns activation policy. Cleanup relevance: no binding conditions means conditional claims are treated active, while nonempty environment conditions require a solver.

### `propstore/core/active_claims.py`

Owner/subsystem: typed runtime active-claim model.

This file owns the immutable `ActiveClaim` and `ActiveClaimVariable` records used by active-world reasoning. It parses serialized condition CEL, checked-condition IR, and variable JSON from projection rows; coerces claim ids, concept ids, claim types, algorithm stages, provenance/source fields, and concept-link roles; exposes convenience accessors for logical ids, provenance, role-specific concept links, display ids, condition JSON, variable bindings, and source-claim payload conversion. Boundary: row coercion is delegated to the claims projection model, condition IR is delegated to the conditions package, and semantic enum/id coercion is delegated to the core type modules. Cleanup relevance: this is the runtime normalization point for projected claim rows, so canonical/source leakage and condition sidecar assumptions surface here.

### `propstore/core/algorithm_stage.py`

Owner/subsystem: typed algorithm-stage scalar.

This file defines `AlgorithmStage` as a branded string `NewType` plus constructors/coercers for optional runtime values. Boundary: it does not enumerate allowed stages or own algorithm semantics; it only prevents loose object values from entering stage-typed paths. Cleanup relevance: callers using free-form strings for algorithm stage should cross this explicit coercion boundary.

### `propstore/core/aliases.py`

Owner/subsystem: concept alias export.

This file owns `AliasExportEntry` and `export_concept_aliases`, which scan committed concept family handles, parse concept documents, choose a logical id from primary logical identity or canonical name, and map each alias name to the concept's logical id/name pair. Boundary: concept document parsing and logical-id selection are delegated to family helpers; this module only packages alias export rows. Cleanup relevance: alias export is payload-shaped at the edge after parsing, so deeper concept code should not depend on these dictionaries as domain objects.

### `propstore/core/analyzers.py`

Owner/subsystem: shared reasoning analyzers over active world graphs.

This file owns conversion from active graph/store data into analyzer inputs for claim-graph, ASPIC, and probabilistic argumentation backends. It builds claim mappings, stance rows, conflict rows, minimal compiled graphs, active graph views, derived conflict rebuttals, Cayrol support-derived defeats, Dung/bipolar frameworks, extension projections, PrAF query-parameter normalization, PrAF calibration/vacuous fallback packaging, and backend-specific `AnalyzerResult` values. Boundary: graph/domain rows are coerced by family projection models, argumentation algorithms come from the `argumentation` package, claim strength/preference and probabilistic calibration live in their own propstore modules, and world backend/semantics validation lives in world types. Cleanup relevance: this is a major integration point where row-shaped data is converted into typed graph semantics, and where missing probability calibration is intentionally represented rather than hidden.

### `propstore/core/anytime.py`

Owner/subsystem: bounded exact-enumeration sentinel.

This file defines `EnumerationExceeded`, a frozen runtime-error dataclass carrying partial count, candidate ceiling, and the provenance status assigned to unvisited remainder results. Boundary: it does not run enumeration; exact enumerators raise or return this value to report bounded interruption without pretending the remainder was inferred. Cleanup relevance: callers should preserve the vacuous remainder semantics rather than converting this into a generic failure.

### `propstore/core/assertions/__init__.py`

Owner/subsystem: core assertion package export surface.

This file re-exports the assertion record, conversion, reference, and situated assertion types: canonical/source records, condition/context/provenance refs, unconditional condition sentinel, `SituatedAssertion`, and assertion-id derivation. Boundary: implementation remains in sibling modules; this package initializer is a convenience import surface. Cleanup relevance: because it is shallow and explicit, new assertion APIs should be deliberately added here only when they are intended as package-level surface.

### `propstore/core/assertions/codec.py`

Owner/subsystem: canonical situated-assertion serialization boundary.

This file owns `AssertionCanonicalRecord`, the closed canonical payload form for situated assertions. It validates that the supplied assertion id matches the derived situated assertion id, rejects old claim-shaped payloads, parses relation refs, role binding sets, context refs, condition refs, and provenance graph refs from mappings, and serializes back to canonical IO payload dictionaries. Boundary: `SituatedAssertion`, reference types, and role-binding domain types are owned by sibling/core relation modules; this module owns strict canonical wire-shape validation. Cleanup relevance: this is the hard boundary that prevents old claim payload shape from being accepted as canonical assertion data.

### `propstore/core/assertions/conversion.py`

Owner/subsystem: source structural-assertion conversion boundary.

This file owns `AssertionSourceRecord` and `assertion_source_record_from_payload`, converting decoded source mappings into closed assertion domain objects. It rejects old claim-like source shapes, parses relation concept references with optional lexical/description ids, parses role bindings, context id strings, condition refs, and provenance graph refs, and can validate role bindings against a `RoleSignature` before producing a `SituatedAssertion`. Boundary: source dictionaries are accepted only here; downstream code receives assertion/reference/relation domain types. Cleanup relevance: this is the source-side hard failure point for old semantic claim payload shapes.

### `propstore/core/assertions/refs.py`

Owner/subsystem: situated assertion reference identities.

This file defines validated references for assertion context, checked condition artifact, and provenance named graph, plus the unconditional condition singleton. It enforces nonempty context ids, `ps:condition:` condition ids with nonempty registry fingerprints, URI-shaped provenance graph names, and provides identity payload tuples for stable assertion identity derivation. Boundary: id branding comes from core id types; this module owns assertion-reference validity rules. Cleanup relevance: authored CEL is intentionally absent here; condition identity is a checked artifact reference with a registry fingerprint.

### `propstore/core/assertions/situated.py`

Owner/subsystem: situated assertion identity.

This file defines `SituatedAssertion` as a relation instance with role bindings, context, checked condition, and audit provenance graph reference. It derives assertion identity from relation, role bindings, context, and condition only, excluding provenance from equality/identity, and hashes the canonical JSON identity payload into a `ps:assertion:` id. Boundary: relation/reference validation is owned by their domain types; this module owns identity composition. Cleanup relevance: provenance remains audit metadata, not canonical assertion identity.

### `propstore/core/base_rates.py`

Owner/subsystem: assertion-scoped base-rate resolution for subjective opinions.

This file defines base-rate profile records, source parameter-claim records, resolution success/failure records, assertion opinions, a resolver that enforces one profile per target plus acyclic/stratified dependencies, and `construct_assertion_opinion`. It validates `ps:assertion:` ids, open-interval base-rate values, proportion units for source base-rate claims, and returns unresolved sentinel objects for missing or recursive base rates. Boundary: authored parameter claim payloads are only decoded at `BaseRateAssertionRecord.from_parameter_claim`, while opinion construction delegates to `Opinion` and provenance types. Cleanup relevance: no opinion should be constructed for an assertion without an explicit resolved base-rate profile.

### `propstore/core/claim_types.py`

Owner/subsystem: canonical claim-type vocabulary.

This file defines the `ClaimType` string enum for authored/runtime claim semantics, the `VALID_CLAIM_TYPES` set excluding `unknown`, and a simple optional coercer. Boundary: it is vocabulary only, not claim validation or storage. Cleanup relevance: code paths accepting arbitrary claim type strings should coerce through this enum so unsupported values fail immediately.

### `propstore/core/claim_values.py`

Owner/subsystem: typed nested claim value objects.

This file owns parsing and serialization for nested claim-side source/provenance payloads: `SourceOrigin`, `SourceTrust`, `ClaimSource`, and `ClaimProvenance`. It parses optional JSON mappings/lists, subjective-opinion dictionaries, source origin/trust fields, source kind/origin enums, paper/page provenance, and stable JSON output for provenance. Boundary: source kind vocabularies come from `source_types`, opinion math comes from `Opinion`, and decoded mappings are consumed only at these constructors. Cleanup relevance: this file is the boundary that keeps nested source/trust/provenance dictionaries from flowing untyped through active claims.

### `propstore/core/concept_relationship_types.py`

Owner/subsystem: canonical concept relationship vocabulary.

This file defines the `ConceptRelationshipType` enum, the complete valid relationship-type set, and an optional coercer. Boundary: it owns concept-to-concept relationship labels only, not relation persistence or graph behavior. Cleanup relevance: concept relationship inputs should pass through this enum so unsupported relationship labels fail at the boundary.

### `propstore/core/concept_status.py`

Owner/subsystem: canonical concept status vocabulary.

This file defines `ConceptStatus` with accepted, deprecated, and proposed states, the valid status set, and a strict coercer with explicit error messages for invalid strings or non-string values. Boundary: it is vocabulary/coercion only, not lifecycle policy. Cleanup relevance: concept status validation should use this coercer rather than accepting loose strings.

### `propstore/core/conditions/__init__.py`

Owner/subsystem: condition IR package export surface.

This file re-exports checked condition sets, JSON codecs, ESTree/Python/SQL/Z3 backends, solver types, and IR node/value types. It lazily exposes CEL frontend parsing/checking through `__getattr__` to avoid eager imports. Boundary: implementation stays in sibling modules; this initializer coordinates the public condition package surface. Cleanup relevance: lazy CEL frontend exports are intentional and should be preserved if import cycles or startup cost matter.

### `propstore/core/conditions/cel_frontend.py`

Owner/subsystem: CEL frontend validation and lowering into `ConditionIR`.

This file owns CEL parsing/type checking against the condition concept registry and lowering cel-parser AST nodes into propstore condition IR. It validates undefined concepts, structural concepts in conditions, boolean/logical operand types, arithmetic/ordering constraints, category value membership warnings/errors, ternary branch consistency, `in` list literals, and supported CEL operators, then returns either checked conditions with registry fingerprints or lowered IR. Boundary: CEL parsing comes from `cel_parser`, registry metadata comes from `conditions.registry`, and downstream execution/serialization is owned by condition backend modules. Cleanup relevance: unsupported CEL forms fail here instead of being carried into runtime solvers.

### `propstore/core/conditions/checked.py`

Owner/subsystem: checked condition carriers and condition-set JSON.

This file defines `CheckedCondition` and `CheckedConditionSet`, normalizes condition sources, enforces nonempty sources/fingerprints, requires all set members to share one registry fingerprint, de-duplicates by source, and serializes/deserializes versioned checked-condition-set JSON containing source, warnings, and condition IR. Boundary: actual IR encoding/decoding is delegated to `conditions.codec`; this module owns checked runtime carrier invariants. Cleanup relevance: condition sets preserve registry fingerprints with the IR, which is the guard against evaluating CEL under the wrong concept registry.

### `propstore/core/conditions/codec.py`

Owner/subsystem: versioned JSON codec for condition IR.

This file owns `CONDITION_IR_JSON_VERSION`, recursive encoding of every supported `ConditionIR` node to JSON dictionaries, and strict decoding back into literal, reference, unary, binary, membership, and choice nodes. It validates node tags, version, scalar literal values, spans, nested mappings, sequences, string sequences, value kinds, and operators. Boundary: the IR dataclasses/enums are owned by `conditions.ir`; this module owns only their external JSON representation. Cleanup relevance: every persisted condition IR payload must pass through this versioned codec so shape changes are explicit.

### `propstore/core/conditions/estree_backend.py`

Owner/subsystem: ESTree backend for condition IR.

This file defines small ESTree expression dataclasses, converts condition IR into ESTree-like expressions, and evaluates those expressions against name bindings. It maps condition references to identifiers, literals to ESTree literals, unary/binary/logical operators to JavaScript-style operators, membership to `Array.includes`, and choices to conditional expressions, while validating unsupported operators, missing bindings, computed members, non-member calls, and nonnumeric arithmetic operands. Boundary: condition node definitions are owned by `conditions.ir`; this backend owns a JavaScript-facing representation and local evaluator. Cleanup relevance: membership and logical short-circuit semantics are encoded here, so web/runtime adapters should not reimplement them ad hoc.

### `propstore/core/conditions/ir.py`

Owner/subsystem: closed semantic condition IR.

This file defines the condition source-span, value-kind, unary-op, binary-op, literal, reference, unary, binary, membership, and choice dataclasses/enums plus the `ConditionIR` union. It validates source spans, literal value types against value kinds, nonempty concept ids/source names, enum coercions, category metadata normalization, and tuple normalization for membership options. Boundary: it is pure domain structure; parsing, serialization, solver translation, and execution are separate backends. Cleanup relevance: this is the closed set of condition nodes all frontend/backend adapters must target.

### `propstore/core/conditions/python_backend.py`

Owner/subsystem: Python AST backend for condition IR.

This file converts condition IR into Python `ast.Expression` objects and evaluates them with an empty builtins environment plus caller-provided bindings. It maps references to names, literals to constants, unary/logical/comparison/arithmetic/membership/choice nodes to their Python AST equivalents, precomputes referenced names to reject missing bindings, and validates unsupported operators. Boundary: it relies on the IR module for node definitions and uses Python AST only as an execution backend. Cleanup relevance: runtime Python evaluation goes through compiled AST with explicit bindings, not string eval of authored CEL.

### `propstore/core/conditions/registry.py`

Owner/subsystem: typed condition registry projection and synthetic bindings.

This file defines condition concept kinds, `ConceptInfo`, registry scoping by concept id, registry augmentation with synthetic concepts, synthetic category concept construction, standard synthetic binding injection, and deterministic registry fingerprinting over condition-relevant concept semantics. Boundary: standard synthetic binding names come from `cel_bindings`; this module owns the minimal registry shape needed by condition checking. Cleanup relevance: checked condition fingerprints depend on the exact canonical-name/id/kind/category semantics produced here.

### `propstore/core/conditions/solver.py`

Owner/subsystem: public semantic condition solver over checked condition IR.

This file wraps Z3 queries for checked conditions, exposing satisfiability with bindings, disjointness, equivalence, implication, and equivalence-class partitioning. It owns solver result dataclasses, unknown-reason classification, Z3 translation/unknown exceptions, registry fingerprint enforcement, expression/set caching, timeout setup, temporal ordering constraints, and conversion of Z3 `sat`/`unsat`/`unknown` results. Boundary: Z3 expression construction is delegated to `conditions.z3_backend`; this module owns public query semantics and fingerprint-safe solver use. Cleanup relevance: two-valued helpers raise on unknown results instead of silently treating timeout/incomplete as false.

### `propstore/core/conditions/sql_backend.py`

Owner/subsystem: parameterized SQL fragment backend for condition IR.

This file converts condition IR into `SqlConditionFragment` values with SQL text and parameter tuples. It quotes references as identifiers, emits literals as parameters, maps unary/binary/logical/arithmetic/comparison operators to SQL, lowers membership to `IN`, handles empty membership as `(0 = 1)`, and rejects condition-choice nodes for SQL projection. Boundary: it does not execute SQL or own database schema; it only produces fragments. Cleanup relevance: callers should use these parameterized fragments instead of interpolating condition literals into SQL.

### `propstore/core/conditions/z3_backend.py`

Owner/subsystem: Z3 projection backend for condition IR.

This file defines `ConditionZ3Encoder`, `Z3Projection`, Z3 translation errors, simple helper entrypoints, and reference-kind collection. It projects condition IR into Z3 terms with explicit definedness conditions, supports numeric/timepoint/string/boolean references, extensible and closed category concepts, equality and membership over category literals, arithmetic including defined division, short-circuit-style definedness for boolean operators, conditional choice expressions, binding constraints, and temporal `_from`/`_until` ordering constraints. Boundary: registry concept metadata comes from `conditions.registry`; query orchestration and fingerprint checks are owned by `conditions.solver`. Cleanup relevance: category enum handling and definedness semantics live here, so solver callers should not bypass this encoder.

### `propstore/core/embeddings.py`

Owner/subsystem: embedding input domain objects.

This file defines `EmbeddingEntity` and text construction helpers for claim and concept embeddings. Claim text prefers auto summary, then statement, expression, name, and finally claim id; concept text combines canonical name, optional aliases, and definition. Boundary: it does not compute embeddings or touch sidecar storage; it only prepares stable text inputs from active claims and concept rows. Cleanup relevance: embedding behavior depends on this precedence order, especially whether generated summaries outrank authored statements.

### `propstore/core/environment.py`

Owner/subsystem: core environment value object and store protocols.

This file defines the runtime `Environment` dataclass plus protocol interfaces for world stores, claim/concept catalogs, stance/conflict/justification access, condition solving, compiled graphs, search/similarity, parameterizations, and micropublications. `Environment` normalizes bindings, context id, effective CEL assumptions, and assumption refs to/from dictionaries. Boundary: it intentionally lives in core to avoid core importing world-layer types, while protocol implementations live elsewhere. Cleanup relevance: this is the architectural contract between analyzers/world operations and storage-backed repositories.

### `propstore/core/exactness_types.py`

Owner/subsystem: parameterization exactness vocabulary.

This file defines the `Exactness` enum with exact, approximate, and conditional values plus an optional coercer. Boundary: it is vocabulary only, not parameterization validation or scoring. Cleanup relevance: parameterization rows should use this enum rather than loose exactness strings.

### `propstore/core/graph_build.py`

Owner/subsystem: canonical compiled-world graph construction from store protocols.

This file builds `CompiledWorldGraph` objects from sidecar-backed stores. It coerces concept, claim, relationship, parameterization, stance, and conflict rows through family projection models; constructs graph nodes/edges/witnesses; preserves provenance records; maps claim ids to primary logical ids when requested; carries checked conditions from claims and parameterizations; rejects stale `conditions_cel` without `conditions_ir`; and derives concept relationships, claim stances, parameterization edges, and conflict witnesses. Boundary: storage access is via core store protocols and family row models; this module owns graph assembly, not storage mutation. Cleanup relevance: this is the central transition from row projections to canonical graph semantics, including the hard sidecar rebuild checks for missing checked condition IR.

### `propstore/core/graph_relation_types.py`

Owner/subsystem: compiled graph relation vocabulary.

This file defines `GraphRelationType`, combining concept relationships and claim stance/argumentation relations, plus the valid relation-type set and strict coercer with explicit errors. Boundary: it is vocabulary only; relation storage and graph edge construction are elsewhere. Cleanup relevance: compiled graph edges should use this enum so unsupported relation labels fail before analysis.

### `propstore/core/graph_types.py`

Owner/subsystem: canonical runtime graph dataclasses.

This file defines the core graph object model: concept nodes, provenance records, claim nodes, relation edges, parameterization edges, conflict witnesses, compiled world graphs, graph deltas, and active world graphs. It normalizes/freeze-sorts attributes, serializes/deserializes graph payloads, round-trips checked condition IR from encoded JSON, handles labels and environments, coerces ids/enums/exactness, sorts canonical graph collections, applies claim add/remove deltas while pruning affected claim relations/conflicts, and records active/inactive claim id sets. Boundary: it is the in-memory canonical graph representation; graph construction, activation, storage, and analysis live in other modules. Cleanup relevance: this file defines what is canonical at runtime, including whether checked conditions, provenance, labels, and parameterization conditions survive graph serialization.

### `propstore/core/id_types.py`

Owner/subsystem: semantic id branding and coercion.

This file defines `NewType` wrappers for concept, claim, assertion, context, condition, provenance graph, justification, assumption, and queryable ids, plus `LogicalId` and scalar/iterable coercion helpers. Boundary: it performs string branding only, not prefix validation except where other modules add it. Cleanup relevance: use these helpers at boundaries to make id intent visible without scattering raw strings.

### `propstore/core/justifications.py`

Owner/subsystem: canonical justification records.

This file defines `CanonicalJustification`, its dict round-trip, attribute normalization, and derivation of active-graph justifications. It creates reported-claim justifications for active claims and support/explain justifications from active relation edges, carrying provenance and relation attributes. Boundary: active graph structure and provenance records come from graph types; this module owns justification record shape and active-graph extraction. Cleanup relevance: this is the bridge from compiled/active graph relations to structured argument construction inputs.

### `propstore/core/labels.py`

Owner/subsystem: ATMS-style belief-space labels and assumption environments.

This file defines assumption refs, environment keys, nogood sets, labels, justification records, binding/CEL conversion helpers, environment assumption compilation, label combination/merging, and conversions between labels/environments and provenance polynomials/nogoods. It normalizes antichain environments, prunes known nogoods, builds stable assumption ids from bindings/context assumptions, represents contexts as separate support variables, and combines antecedent support by polynomial multiplication/sum with optional live filtering. Boundary: provenance algebra, nogood filtering, and support quality types live in the provenance package; this module owns the core ATMS projection layer. Cleanup relevance: belief-space support semantics now flow through provenance polynomials, so old bespoke label math should not be duplicated elsewhere.

### `propstore/core/lemon/__init__.py`

Owner/subsystem: OntoLex-Lemon package export surface.

This file re-exports lexical forms/entries/senses, ontology references, description kinds, causal and merge helpers, proto-role utilities, qualia structures, temporal anchors/relations, and identity-key helpers from the Lemon subpackage. Boundary: implementation is in sibling modules; this initializer is the curated package-level surface. Cleanup relevance: adding Lemon concepts should update this explicit export list only when they are intended as public core vocabulary.

### `propstore/core/lemon/description_kinds.py`

Owner/subsystem: Lemon description kinds, slot bindings, merge arguments, and causal assertions.

This file defines document-structured participant slots, description kinds, slot bindings, description claims, merge arguments, merge protocols, causal account vocabulary, and causal connection assertions. It validates unique slot names, binding slot existence/type constraints, merge-attack references to known arguments, and account-sensitive causal transitivity. Boundary: ontology references, proto-role bundles, and provenance are imported domain objects; this module owns description-kind structure and validation. Cleanup relevance: causal closure is intentionally account-sensitive and limited to counterfactual/mechanistic accounts.

### `propstore/core/lemon/forms.py`

Owner/subsystem: Lemon lexical surface forms.

This file defines text cleanup helpers and the immutable `LexicalForm` record. It requires nonempty written representation and language, optionally validates phonetic representation, and provides casefolded whitespace-normalized text folding. Boundary: this is linguistic form only, not ontology/world measurement data. Cleanup relevance: lexical form identity and validation should use these normalized text helpers rather than duplicating surface-form cleanup.

### `propstore/core/lemon/proto_roles.py`

Owner/subsystem: Dowty-style proto-role entailment model.

This file defines proto-agent and proto-patient property vocabularies, graded entailments, proto-role bundles, aggregate proto-agent/patient weights, and predicted subject role selection. It validates entailment properties and probability-like values, ensures bundle entailments use the proper property enum, and returns no predicted subject on ties. Boundary: provenance is attached to entailments, while syntactic/description slot structures live in other Lemon modules. Cleanup relevance: role prediction is intentionally graded and tie-sensitive rather than a fixed role label.

### `propstore/core/lemon/qualia.py`

Owner/subsystem: Pustejovsky-style qualia references and coercion.

This file defines qualia role vocabulary, type constraints, qualia references/structures, coerced reference results, role-specific reference access, qualia-mediated coercion, and TELIC purposive chain traversal. It checks target type compatibility by URI, composes provenance for coercion operations, follows first TELIC links with cycle/depth protection, and returns explicit coercion records rather than rewriting references implicitly. Boundary: ontology references and provenance are imported domain objects; this module owns qualia role traversal/coercion semantics. Cleanup relevance: type coercion through qualia is explicit and provenance-bearing.

### `propstore/core/lemon/references.py`

Owner/subsystem: Lemon ontology references.

This file defines the immutable `OntologyReference` record with required nonempty URI and optional nonempty label. Boundary: text validation is delegated to Lemon form helpers; this module owns the ontology-side reference object. Cleanup relevance: Lemon structures should use this object instead of raw URI/label pairs.

### `propstore/core/lemon/temporal.py`

Owner/subsystem: Allen temporal relations for Lemon description anchors.

This file defines Allen interval relation vocabulary, temporal anchor documents, CEL expressions for each relation, a synthetic timepoint registry, and `description_temporal_relation` evaluation through the condition solver. It validates `valid_from <= valid_until` and binds left/right interval endpoints to checked CEL conditions. Boundary: condition parsing/solving is delegated to the condition subsystem; this module owns the Allen relation mapping for description claims. Cleanup relevance: temporal relation logic is centralized as checked CEL over timepoint concepts rather than duplicated interval comparisons.

### `propstore/core/lemon/types.py`

Owner/subsystem: Lemon lexical entries and senses.

This file defines `LexicalSense`, `LexicalEntry`, and identity-key helpers. It validates optional sense usage text and role-bundle keys, requires lexical entries to have nonempty identifiers and at least one sense, exposes canonical plus other forms and sense references, and computes folded form/entry identity keys without collapsing homographs because entry id remains part of the key. Boundary: forms, ontology references, qualia, description kinds, proto-role bundles, and provenance are imported domain objects. Cleanup relevance: lexical identity explicitly includes language, written form, optional physical-dimension form, and entry id.

### `propstore/core/literal_keys.py`

Owner/subsystem: typed ASPIC literal identity keys.

This file defines claim-backed, context-scoped `ist`, and grounded predicate literal key types, plus the repository root context id and helpers to build claim and ground literal keys. It coerces context/proposition ids for situated literals and includes predicate, ground arguments, and explicit negation in grounded literal identity. Boundary: ASPIC ground atom/scalar types come from the argumentation package; this module owns propstore's bridge key identity. Cleanup relevance: literal identity is structural, not serialized UI text, and claim literals are now context-scoped by default.

### `propstore/core/micropublications.py`

Owner/subsystem: runtime micropublication objects for ATMS bundle reasoning.

This file defines `ActiveMicropublication`, mapping coercion, input union type, and string-tuple parsing for claim/assumption references. It accepts JSON-encoded or collection-shaped claim ids, extracts ids from small mapping entries, supports context from `context_id` or nested `context.id`, validates required artifact/context/nonempty claims, and normalizes context ids and assumption strings. Boundary: it is a runtime carrier only; family storage and micropublication analysis live elsewhere. Cleanup relevance: micropublication claim and assumption references are normalized here before label/reasoning code consumes them.

### `propstore/core/reasoning.py`

Owner/subsystem: shared reasoning backend and argumentation-semantics selectors.

This file defines reasoning backend and argumentation semantics enums, CLI-visible semantics ordering, backend-to-supported-semantics mappings, normalization helpers, and backend/semantics validation. It supports aliases such as `bipolar_stable`, rejects unknown backends/semantics, and reports supported semantics when a backend cannot run a requested semantics. Boundary: it is selector vocabulary and validation only; actual analyzers are elsewhere. Cleanup relevance: all CLI/app reasoning surfaces should use this matrix instead of hand-maintaining backend capability checks.

### `propstore/core/relation_types.py`

Owner/subsystem: backend-agnostic stance relation categories.

This file groups graph relation types into attack, unconditional attack, preference-sensitive attack, support, non-attack, and graph-relation categories used by analyzers. Boundary: relation labels come from `GraphRelationType`; this module owns semantic classification sets, not edge storage. Cleanup relevance: argumentation backends should share these categories so defeat/support semantics do not drift.

### `propstore/core/relations.py`

Owner/subsystem: bootstrap relation concept and role-binding kernel.

This file defines bootstrap relation ids, claim-concept link roles, relation concept references, role bindings/sets, role definitions/signatures, relation property kinds/assertions/sets, and small relation-property algorithms. It validates nonempty relation/role/domain/range ids, duplicate-free role bindings and signatures, complete binding sets, inverse property target rules, symmetric binary canonicalization, and transitive closure for declared transitive relations. Boundary: higher relation definitions are intended to be ordinary propstore content; this kernel owns only the minimal typed relation/role/property substrate. Cleanup relevance: relation assertion identity is based on relation concept plus sorted role bindings, not lexical labels.

### `propstore/core/results.py`

Owner/subsystem: canonical analyzer result dataclasses.

This file defines `ExtensionResult`, `ClaimProjection`, and `AnalyzerResult` plus metadata/string normalization and dict round-tripping. It sorts and de-duplicates claim id tuples, normalizes metadata pairs, serializes/deserializes extension sets, target/survivor/witness projections, optional support labels, and analyzer metadata. Boundary: label serialization is delegated to graph label helpers; this module owns backend-neutral result shape. Cleanup relevance: analyzer backends should return these typed results instead of backend-specific dictionaries.

### `propstore/core/source_types.py`

Owner/subsystem: source kind and origin vocabularies.

This file defines `SourceKind`, `SourceOriginType`, their valid value sets, and strict coercers with explicit error messages. Current source kind vocabulary contains academic papers; origin types include DOI, file, and manual. Boundary: vocabulary only; source record parsing is in claim value objects. Cleanup relevance: source metadata should use these enums to avoid silently accepting unsupported origin/kind strings.

### `propstore/core/store_results.py`

Owner/subsystem: typed results for world-store query surfaces.

This file defines `ConceptSearchHit`, `ClaimSimilarityHit`, `ConceptSimilarityHit`, and `WorldStoreStats`, including mapping constructors and id coercion. It carries similarity distances plus selected display/source metadata for claims and concepts. Boundary: it does not perform search or similarity; store implementations populate these result types. Cleanup relevance: world store protocols should return these dataclasses instead of loose sidecar row dictionaries.

### `propstore/defeasibility.py`

Owner/subsystem: CKR-style exception and defeasibility support contracts.

This file defines contextual claim use, CEL bindings, justifiable exceptions, lifting-rule support, exception defeats, policy issues, contextual claim results, decidability/applicability vocabularies, and utilities to evaluate exceptions and add exception defeats to ASPIC CSAFs. It filters exception support through provenance nogoods, lifts exceptions across contexts only via explicit lifting rules, treats solver unknown/translation/unbound authoring as non-positive incomplete/authoring statuses, detects multiple applicable exceptions as a policy issue, and injects defeat edges from justification-claim arguments to excepted target arguments. Boundary: CEL checking/solver behavior comes from the condition subsystem, provenance support/nogoods from provenance, and CSAF/Dung structures from argumentation. Cleanup relevance: exception patterns must not be treated as applied when solver status is unknown or required bindings are absent.

### `propstore/demo/__init__.py`

Owner/subsystem: demo repository helper export surface.

This file re-exports `materialize_reasoning_demo` from the demo package. Boundary: implementation is in `reasoning_demo.py`; this initializer is only the public package surface for demo materialization. Cleanup relevance: keep demo exports explicit so importing `propstore.demo` has a small, predictable surface.

### `propstore/demo/reasoning_demo.py`

Owner/subsystem: materialized reasoning demo repository builder.

This file creates a small git-backed demo repository that exercises grounding and ASPIC/reasoning flows. It initializes a repository, seeds default forms, authors demo concepts, claims, context, stances, predicates, and a defeasible rule inside family transactions, normalizes concept/claim payloads through family identity helpers, stamps stance ids, saves through family refs, syncs the git worktree, and returns the repository. Boundary: it is demo data materialization, not reusable reasoning logic; repository/family APIs own persistence. Cleanup relevance: this is a source of fixture-like demo content that depends on private project-init form seeding and current family payload shapes.

### `propstore/derived_build.py`

Owner/subsystem: world and grounding sidecar build orchestration.

This file owns content-hash inputs for derived world sidecars, semantic pass and family contract version collection, source-branch tip inclusion, materialized world sidecar cache lookup/build, sidecar export, and grounding-only sidecar materialization. The build path loads family handles, runs form/claim pipelines, builds compilation and concept registries, compiles a repository sidecar build plan, collects promotion-blocked facts, snapshots/restores embeddings, creates projection schema, populates source/concept/context/claim/conflict/stance/justification/micropublication/grounded-fact tables, records diagnostics and build exceptions, commits/checkpoints SQLite, and publishes failures when appropriate. Boundary: Quire derived-store APIs own materialization/caching, family declarations own table population, and semantic pipelines own validation; this module coordinates them. Cleanup relevance: build cache identity depends on source revision, source branch tips, schema versions, pass versions, family contract versions, generated schema hash, dependency pins, and cache-bust config.

### `propstore/derived_build_plan.py`

Owner/subsystem: sidecar row compilation planning.

This file defines the checked repository bundle and sidecar build plan dataclasses, then compiles source, concept, context, claim, raw-id quarantine, conflict, micropublication, stance, justification, and quarantine-diagnostic rows. It builds the claim reference index when normalized claims exist, requires a checked claim bundle before claim population, compiles conflicts with optional context lifting, collects stance/justification/micropublication quarantine diagnostics, and still compiles source/concept/context/micropublication rows when claims are absent. Boundary: family declaration modules own individual row compilation; this module orders and aggregates those row sets for the sidecar builder. Cleanup relevance: the plan preserves claim-absent builds while keeping quarantine diagnostics available for render policy.

### `propstore/description_generator.py`

Owner/subsystem: legacy-style human-readable claim description generation.

This file generates one-line descriptions from loose claim dictionaries for parameter, equation, observation, measurement, model, and algorithm claims, preserving explicit statements when present. It resolves concept names from a concept registry, formats numeric values/ranges/uncertainty/unit text, renders algorithm stage/output text, and summarizes simple CEL equality conditions into readable phrases while passing complex conditions through. Boundary: this module accepts raw dicts and does not use the newer typed claim/domain models. Cleanup relevance: it is a loose-payload presentation helper and should be treated carefully if core semantic paths are being tightened away from dictionaries.

### `propstore/dimensional_invariants.py`

Owner/subsystem: Bridgman-backed dimensionless invariant diagnostics.

This file wraps Bridgman dimensional-analysis functions in propstore `PiDiagnostic` results. It converts propstore dimension mappings to Bridgman dimensions, counts Buckingham Pi groups, checks authored dimensionless products, and returns structured ok/value/error diagnostics instead of propagating Bridgman/type/value exceptions. Boundary: actual dimension analysis lives in the `bridgman` package; this module adapts it to propstore diagnostics. Cleanup relevance: callers can distinguish failed diagnostics from false dimensionless-product results.

### `propstore/dimensions.py`

Owner/subsystem: physical dimension and unit conversion helpers.

This file owns Pint integration, SI normalization/reverse conversion, form-declared conversion specs, extra unit registration, dimensional-form protocols, dimension filtering/requirements, form algebra dimensional verification through Bridgman/Sympy, and canonical dimension signatures. It handles multiplicative, affine, logarithmic, and delta conversions; maps propstore unit aliases to Pint names; rejects dimensionless conversions and incompatible Pint units; and can define additional Pint units from dimension vectors. Boundary: semantic form loading is elsewhere and Bridgman/Pint perform the underlying algebra/conversion. Cleanup relevance: unit conversion and dimensional algebra are centralized here rather than in form or claim pipelines.

### `propstore/epistemic_process.py`

Owner/subsystem: owner-layer process records for executable epistemic workflows.

This file defines content-addressed investigation plans, intervention plans, process jobs, queued jobs, completion records, replay reports, and the immutable process manager. It builds plans from fragility reports and ATMS intervention plans, creates jobs from plans or transition operations with policy/snapshot/journal hashes, verifies recorded ids/content hashes on load, queues idempotently, records completions only for queued jobs, replays manager consistency, and serializes all records through canonical JSON hashing. Boundary: fragility querying, policy profiles, support-revision snapshots/journals, and ATMS plan structures are imported owner-layer inputs; this module owns process identity and queue/completion state. Cleanup relevance: workflow artifacts are content-addressed and versioned, so mutating a process payload must produce a new id/hash rather than updating in place.

### `propstore/families/__init__.py`

Owner/subsystem: family declarations package marker.

This file contains only the package docstring for propstore family declarations. Boundary: all family registration and implementation is in sibling modules. Cleanup relevance: keep this initializer shallow to avoid import coupling across family modules.

### `propstore/families/addresses.py`

Owner/subsystem: semantic family address branding.

This file defines `SemanticFamilyAddress` as a `NewType` string. Boundary: address resolution and family registry behavior live elsewhere; this module only provides a named type for family addresses. Cleanup relevance: use the type to make family address intent explicit instead of raw strings.

### `propstore/families/batch_specs.py`

Owner/subsystem: Quire document batch specifications for propstore families.

This file declares batch specs for claim files and source concept/claim/justification/stance/micropublication batches, including item document types, items field names, batch names, and inherited item fields such as source and produced_by. Boundary: document classes live in family document modules and Quire owns `DocumentBatchSpec`; this module centralizes batch-shape declarations. Cleanup relevance: batch import/export behavior depends on these inherited field lists.

### `propstore/families/calibration/__init__.py`

Owner/subsystem: calibration family package marker.

This file contains only the calibration family package docstring. Boundary: calibration declaration details live in sibling modules. Cleanup relevance: keep this initializer shallow.

### `propstore/families/calibration/declaration.py`

Owner/subsystem: calibration counts derived-store projection.

This file declares the `calibration_counts` projection table, a row dataclass, and a loader that returns pass/category correct/total counts from SQLite or `None` when the table is missing/empty. Boundary: Quire projection fields generate table SQL; this module owns calibration count query shape. Cleanup relevance: callers can treat absent calibration tables as unavailable data rather than a hard failure.

### `propstore/families/claims/__init__.py`

Owner/subsystem: claim family package marker.

This file contains the claim family package docstring and future annotations import only. Boundary: claim family declaration, documents, passes, projection models, storage, and runtime helpers live in sibling modules. Cleanup relevance: keep the package initializer shallow.

### `propstore/families/claims/declaration.py`

Owner/subsystem: claim family sidecar declarations, queries, and population.

This file owns claim-side SQLite query helpers, FTS/vector/embedding projections, row selection with concept/visibility filters, logical-id resolution/indexing, claim text/embedding-row queries, and row compilation/population for normalized claims, deferred stances, raw-id quarantine rows, and promotion-blocked claims. It compiles claim core/numeric/text/algorithm/link/stance rows from checked semantic files, threads file stage into claim core rows, records deferred stance quarantine diagnostics, creates blocked synthetic claim rows for raw ids and promotion blockers, deduplicates claim versions/links, emits version-conflict diagnostics, and handles deletion of stale child rows before inserting promotion-blocked replacements. Boundary: projection table definitions come from the claim projection model, storage row preparation from `claims.storage`, diagnostics from diagnostics declarations, and relation tables from relations declarations. Cleanup relevance: build-time policy is filter-at-render, so blocked/quarantined claims are still materialized with diagnostics instead of aborting the sidecar build.

### `propstore/families/claims/documents.py`

Owner/subsystem: typed document models and contracts for canonical claim YAML.

This file defines claim type contracts, semantic check declarations, logical ids, source/provenance/fit/variable/parameter/opinion/resolution/stance documents, atomic and `ist` proposition documents, and the top-level `ClaimDocument`. It describes required/nonempty fields, concept-link declarations, value groups, unit policies, semantic checks by claim type, and `to_payload` methods for each document shape. Boundary: Quire `DocumentStruct` owns document parsing, core claim/relation/source vocabularies provide enums, and later passes enforce the contract semantics. Cleanup relevance: this is the canonical authored claim YAML schema surface, including nested proposition support and source-local stance declarations.

### `propstore/families/claims/passes/__init__.py`

Owner/subsystem: claim compile pipeline pass.

This file owns claim binding/validation pipeline execution from authored claim files to checked bundles. It resolves output/target/about/variable/parameter concept references and stance target claim references through compiler indexes, preserves draft files as normal claims with diagnostics, validates canonical artifact/version/logical ids, provenance, context existence, CEL conditions against the registry, semantic claim contracts, and stance targets, synthesizes quarantine records for raw `id` inputs without canonical identity, and registers/runs `ClaimCompilePass` through the semantic pass runner. Boundary: detailed semantic checks live in `passes.checks`, diagnostics in `passes.diagnostics`, identity regex/version hashing in family identity modules, and pipeline orchestration in semantic pass infrastructure. Cleanup relevance: draft and raw-id handling intentionally produce diagnostics/quarantine rather than dropping files from the semantic bundle.

### `propstore/families/claims/passes/checks.py`

Owner/subsystem: claim validation checks driven by claim-type contracts.

This file owns validation helpers for logical ids, embedded stance declarations, claim value/bound/uncertainty groups, required/nonempty fields, declared concept links, form range bounds, unit policy, unit/form compatibility, equation Sympy generation, dimensional consistency, algorithm parsing, and algorithm unbound-name warnings. It resolves concept/form references through the compilation context, validates stance resolution payloads and target ids, auto-fills dimensionless default units where contract policy allows, uses Bridgman/Sympy for equation dimensional checks, uses `ast_equiv` for algorithm parsing/free variables, and reports structured claim diagnostics. Boundary: claim-type contracts are declared in claim documents, unit conversion/dimension helpers live elsewhere, and this module reports diagnostics rather than mutating storage. Cleanup relevance: semantic validation behavior is contract-driven, so adding/changing claim types should update contracts instead of scattering new checks.

### `propstore/families/claims/passes/diagnostics.py`

Owner/subsystem: claim-family pass diagnostic construction.

This file defines `claim_diagnostic`, a small helper that creates `PassDiagnostic` instances for the claim family/check stage with filename, artifact id, code, and pass name metadata. It maps informational claim messages to warning-level pass diagnostics while retaining a `claim.info` code by default. Boundary: diagnostic record structure is owned by semantic pass types; this module supplies claim-specific defaults. Cleanup relevance: claim validation should use this helper for consistent family/stage/pass metadata.

### `propstore/families/claims/projection_model.py`

Owner/subsystem: Quire projection models for claim storage and row views.

This file defines codecs, path bindings, attached concept-link rows, storage projection models/tables for claim core, concept links, numeric payload, text payload, and algorithm payload, plus the joined `CLAIM_ROW_MODEL` that materializes `ActiveClaim` records. It handles logical id JSON/primary id conversion, source/provenance component column mapping, typed id/claim type/stage/link-role coercion, projection indexes, claim row query-plan joins to payload and source tables, render views for logical ids/source payloads, and metadata/attribute fields. Boundary: Quire projection mapping owns generic mapping mechanics; this module owns claim-family table layout and active-claim read/write projection shape. Cleanup relevance: canonical claim runtime rows are assembled here from split storage tables, so schema or source/provenance shape changes must update this model.

### `propstore/families/claims/references.py`

Owner/subsystem: claim family reference indexes.

This file defines claim reference records, imported-claim references, reference key generation, record extraction from claim files, claim-file/imported-claim `FamilyReferenceIndex` construction, and first-match resolution across indexes. It derives artifact ids from canonical artifact ids or source-paper/raw-id combinations, indexes raw ids, normalized source-paper logical ids, logical id formatted strings, and logical id values. Boundary: Quire `FamilyReferenceIndex` owns lookup mechanics, while identity normalization/derivation lives in family identity modules. Cleanup relevance: authored stance/reference resolution depends on these key choices, including raw id fallback for source-local files.

### `propstore/families/claims/sidecar_runtime.py`

Owner/subsystem: claim derived-store runtime operations.

This file provides runtime helpers for embedding claims, finding similar/agreeing/disagreeing claim rows, and running heuristic relation generation from a sidecar SQLite store. It opens derived stores, loads sqlite-vec extensions, chooses registered embedding models, wraps progress callbacks by model, commits embedding writes, exposes a `SidecarClaimRelationStore` adapter for claim text/model/similarity access, and delegates relation discovery to heuristic relate functions. Boundary: embedding implementation and vector queries live in the embeddings family; this module is a runtime sidecar adapter. Cleanup relevance: sidecar runtime operations should go through this adapter so model registration and sqlite-vec loading stay centralized.

### `propstore/families/claims/stages.py`

Owner/subsystem: claim semantic stage and sidecar row carrier objects.

This file defines claim pipeline stages, authored-files input, checked bundle output, sidecar row aggregate dataclasses, raw-id quarantine sidecar rows/records, and promotion-blocked fact/reason/row carriers. It preserves context ids as an optional frozen set, carries raw-id quarantine records alongside checked bundles, and emits deterministic JSON detail for quarantine synthetic-id basis. Boundary: actual compilation, validation, and row population live in sibling modules; this module owns typed carriers. Cleanup relevance: blocked/quarantine flows have explicit data structures instead of ad hoc tuples.

### `propstore/families/claims/storage.py`

Owner/subsystem: shared claim-side sidecar row preparation.

This file prepares normalized claim storage rows, claim concept-link rows, and deferred stance rows from loose or semantic claims. It canonicalizes raw ids into artifact/logical/version ids where needed, resolves concept references, extracts typed numeric/text/algorithm fields, generates descriptions, checks/serializes checked conditions, generates Sympy and algorithm canonical AST storage, normalizes units to SI when form definitions are available, converts embedded stance resolutions/opinions into relation columns, and emits quarantine diagnostics for invalid/dead stance references. Boundary: validation happens mostly in claim passes, projection insertion in declarations, concept identity and form/unit logic in separate modules; this module turns validated semantic payloads into storage-shaped dictionaries/tuples. Cleanup relevance: this is a major loose-dict-to-storage boundary and still contains raw-id canonicalization fallback behavior.

### `propstore/families/concepts/__init__.py`

Owner/subsystem: concept family package export surface.

This file re-exports the concept document, loaded concept carrier, and concept-loading helper. Boundary: concept implementation lives in sibling declaration/document/pass/stage modules. Cleanup relevance: keep exports explicit to avoid eager coupling.

### `propstore/families/concepts/declaration.py`

Owner/subsystem: concept family projection, row compilation, and derived queries.

This file declares concept/form/alias/relationship/parameterization/group/form-algebra/FTS/vector projections, concept and parameterization row dataclasses, sidecar row aggregates, row compilation from loaded concepts, SQLite population, concept search, id/alias/logical-id resolution, embedding source selection, registry row selection, parameterization/group queries, and form algebra queries. It compiles forms from form registry, concept rows from concept records, aliases, concept relationship rows plus relation-edge rows, parameterization rows with checked condition IR, parameterization groups, and form algebra rows with symbol rewriting and dimensional verification. Boundary: concept parsing/staging lives in sibling modules, relation edges in relation declarations, form definitions in forms stages, and Quire projections own SQL table mechanics. Cleanup relevance: this is the main concept sidecar boundary and also centralizes FTS/search and concept id resolution precedence.

### `propstore/families/concepts/documents.py`

Owner/subsystem: typed document models for canonical concept YAML.

This file defines concept logical ids, aliases, relationships, form parameters, parameterization relationships, ontology references, lexical forms/senses/entries, the top-level concept document, and a lightweight concept-id scan document. It uses Lemon/provenance/core enum types, enforces at least one lexical sense per lexical entry, and carries artifact/version/logical identity plus aliases, dates, domain, form parameters, range, relationships, parameterization relationships, replacement, and notes. Boundary: detailed normalization and sidecar compilation happen in stages/declaration modules; this module owns authored concept document shape. Cleanup relevance: concept canonical identity now flows through artifact/logical ids plus ontology/lexical entry structures rather than flat name-only documents.

### `propstore/families/concepts/passes.py`

Owner/subsystem: concept normalization, identity, and semantic check pipeline.

This file validates loaded concept registries and registers/runs the concept semantic pipeline. It checks Lemon document consistency, qualia and description-kind references/type constraints, required concept fields, logical/artifact/version ids, form existence and form parameters, category values, range shape, duplicate ids, deprecated replacement chains, relationship targets/types/conditions, parameterization input existence/kinds, dimensional compatibility via Bridgman/Sympy/brute-force heuristics, conditional exactness conditions, canonical-claim references, and missing Sympy warnings. Boundary: loaded concept records/stages handle parsing/normalization, form definitions come from forms stages, claim references from claim indexes, CEL registry from canonical concept registry, and semantic pass infrastructure owns pass execution. Cleanup relevance: concept validation is intentionally code-driven rather than JSON-schema-driven, and it depends on repository-wide concept/form/claim context.

### `propstore/families/concepts/projection_model.py`

Owner/subsystem: Quire projection models for concept row views.

This file defines projection codecs and row models for `ConceptRow` and `ParameterizationRow`. It coerces concept ids, concept statuses, exactness values, integer/real/text fields, exposes render views for primary/logical ids, decodes logical id JSON payloads for rendering, and maps concept metadata such as version/content hash, seq, range, dimensionless flag, unit symbol, and dates into attributes. Boundary: projection tables are declared in concept declarations; this module owns row-object mapping. Cleanup relevance: derived-store concept reads should use these models so enum/id coercion and render views stay consistent.

### `propstore/families/concepts/sidecar_runtime.py`

Owner/subsystem: concept derived-store runtime operations.

This file provides sidecar runtime helpers for embedding concepts and finding similar/agreeing/disagreeing concept rows. It opens SQLite sidecars, loads sqlite-vec, resolves concept handles to sidecar ids, supports one or all registered embedding models, wraps progress callbacks by model, commits embedding writes, and delegates vector similarity queries to the embeddings family. Boundary: embeddings and vector search are implemented in the embeddings declaration module; this module is the concept-specific runtime adapter. Cleanup relevance: concept handle resolution and vec extension loading should go through this path for CLI/app operations.

### `propstore/families/concepts/stages.py`

Owner/subsystem: canonical concept dataclasses, normalization, and document boundary conversions.

This file defines concept pipeline stages, alias/relationship/parameterization specs, canonical `ConceptRecord`, loaded concept carriers, pipeline set/registry carriers, document-to-payload/render/write normalization helpers, concept document-to-record conversion, concept reference key generation, concept reference rewriting, loaded concept normalization, registry construction, and concept loading. It derives artifact/logical/version ids when absent, maps Lemon ontology/lexical entry data into canonical name/definition/form, prunes semantic defaults, rewrites source-local concept references to artifact ids, updates version ids after rewrites, parses relationships/parameterizations/ranges/form parameters into typed objects, and preserves source-local ids for validation/reference indexing. Boundary: document classes define authored shape, identity helpers compute canonical ids, and passes/declarations validate and compile records. Cleanup relevance: this is the canonical boundary from authored concept documents into `ConceptRecord` domain objects.

### `propstore/families/contexts/__init__.py`

Owner/subsystem: context family package export and loader.

This file exports `ContextDocument` and defines `load_contexts`, which loads context documents from a directory using Quire and wraps loaded documents as `LoadedContext` lazily. Boundary: document shape and stage conversion live in sibling modules; this initializer provides the package-level loading helper. Cleanup relevance: lazy `LoadedContext` import keeps the package surface shallow.

### `propstore/families/contexts/declaration.py`

Owner/subsystem: context family projections, row compilation, and lifting-system read model.

This file defines projection codecs/models/tables/schema for contexts, context assumptions, context lifting rules, and lifting materializations; creates/populates context tables; filters invalid lifting rules when context diagnostics exist; compiles loaded contexts and authored `ist` assertions into projection rows; compiles lifting decision/materialization rows; and loads a `LiftingSystem` from SQLite. Boundary: context records/stages and context-lifting domain objects own semantic meaning, while Quire projections own table mechanics. Cleanup relevance: context lifting rules are persisted as semantic sidecar data, and invalid source/target context references can be filtered before population.

### `propstore/families/contexts/documents.py`

Owner/subsystem: typed document models for authored context YAML.

This file defines context references, context structure, lifting rule documents, and top-level context documents with payload serialization. It carries assumptions, parameters, perspective, descriptions, lifting source/target/mode/conditions/justification, and uses `LiftingMode` for rule mode. Boundary: document parsing is Quire/msgspec, and semantic coercion into context records happens in stages. Cleanup relevance: context authoring shape separates structure assumptions/parameters from lifting rule declarations.

### `propstore/families/contexts/passes.py`

Owner/subsystem: semantic passes for context artifacts.

This file defines and registers the context pipeline: normalization, identity validation, lifting-rule binding, and checked graph pass. It validates context ids/names/duplicates, checks lifting rule source/target context existence, builds a `LiftingSystem` with context references, bound rules, and context assumptions, and emits context-family pass diagnostics. Boundary: context records/stage carriers are in `contexts.stages`, lifting semantics are in `context_lifting`, and pass execution is generic semantic-pass infrastructure. Cleanup relevance: invalid lifting references are reported during binding, while checked output carries only valid bound rules.

### `propstore/families/contexts/stages.py`

Owner/subsystem: context semantic stage objects and boundary coercion.

This file defines context pipeline stages, `ContextRecord`, loaded context carriers, authored/normalized/bound/checked stage carriers, parsers from payloads and `ContextDocument`, loaded-document wrappers, lifting-rule parsing, and conversion from loaded contexts to a `LiftingSystem`. It accepts assumptions either top-level or under `structure`, coerces context ids, parameters, perspective, lifting rules, CEL conditions, and context references, and preserves source paths/knowledge roots. Boundary: authored document shape lives in `contexts.documents`; lifting semantics are in `context_lifting`. Cleanup relevance: this is the context-family boundary from YAML/document payloads into typed context/lifting records.

### `propstore/families/diagnostics/__init__.py`

Owner/subsystem: diagnostics family package marker.

This file contains only the diagnostics family package docstring. Boundary: diagnostics declarations and authoring lints live in sibling modules. Cleanup relevance: keep this initializer shallow.

### `propstore/families/diagnostics/authoring_lints.py`

Owner/subsystem: authoring-quality diagnostics surfaced during builds.

This file collects non-blocking authoring lints for sources, stance files, and claim files. It warns on `Unknown_*` source slugs, sources missing descriptive metadata, claim provenance that looks like placeholder page 1 without quote/section/table/figure, stances missing strength, and undercut stances missing target justification ids. Boundary: it reads typed source/stance/claim documents and emits semantic pass diagnostics; it does not block compilation. Cleanup relevance: these warnings are build-surfaced quality signals separate from semantic validation errors.

### `propstore/families/diagnostics/declaration.py`

Owner/subsystem: build diagnostics projection and query contract.

This file declares the `build_diagnostics` projection table, quarantine/write result carriers, source-status diagnostic rows, `QuarantinableWriter`, diagnostic recording helpers, promotion-blocked diagnostic row compilation, build-diagnostics selection, source-status diagnostic selection, and promotion-blocked diagnostic deletion. It can create the diagnostics table, quarantine failed payload writes as blocking errors, record build exceptions and embedding-restore warnings, record pass diagnostics and authoring diagnostics, and query diagnostics ordered by insertion id. Boundary: Quire projections own table mechanics and semantic pass diagnostics provide upstream errors/warnings; this module owns build diagnostic persistence. Cleanup relevance: diagnostics are durable sidecar rows and are used to represent quarantines/blockers without aborting all builds.

### `propstore/families/documents/__init__.py`

Owner/subsystem: artifact document schema package marker.

This file contains only the artifact document schema package docstring. Boundary: individual document schemas live in sibling modules. Cleanup relevance: keep this initializer shallow.

### `propstore/families/documents/justifications.py`

Owner/subsystem: typed document model for canonical justification artifacts.

This file defines `JustificationDocument` with optional id, conclusion, premises, rule kind/strength, provenance, attack target, artifact code, and payload serialization. Boundary: provenance and attack-target document shapes are shared from source documents; compilation/storage are in relation/claim declarations. Cleanup relevance: canonical justification artifacts retain source-provenance and attack-target metadata without embedding compiler behavior here.

### `propstore/families/documents/merge.py`

Owner/subsystem: typed merge manifest document models.

This file defines merge manifest witness, argument, semantic candidate argument/detail, payload, and top-level document structs. It records branch pairs, assertion/logical/artifact/canonical claim ids, branch origins, witness basis, materialization status, semantic candidate tuples, and candidate details. Boundary: this is schema-only; merge logic and manifest generation live elsewhere. Cleanup relevance: merge artifacts have a typed schema for both materialized arguments and candidate semantic equivalence groups.

### `propstore/families/documents/micropubs.py`

Owner/subsystem: typed Clark-style micropublication document models.

This file defines micropublication evidence entries and top-level micropublication documents. It requires at least one claim reference, carries artifact/version id, context, claim refs, evidence refs, assumptions, optional stance, provenance, and source, and serializes to payload dictionaries. Boundary: context/provenance/stance document types come from other family modules; runtime coercion and sidecar population live elsewhere. Cleanup relevance: micropublications explicitly bundle claims in context with optional assumptions/evidence/stance.

### `propstore/families/documents/predicates.py`

Owner/subsystem: typed document models for DeLP/Datalog predicate declarations.

This file defines predicate argument type validation, canonical predicate documents, proposal-side predicate declarations, extraction provenance, and proposal payloads. It validates declaration arity, arg type count, base scalar/paper id sorts, and enum-style argument sorts. Boundary: the document schema records predicate vocabulary and provenance; grounding semantics and derived-from parsing live in `propstore.grounding.predicates`. Cleanup relevance: predicate artifacts carry canonical id/arity/types plus source-authoring metadata without putting canonical identity in the CLI.

### `propstore/families/documents/rules.py`

Owner/subsystem: typed document models for DeLP-style rule artifacts.

This file defines term, atom, body literal, source, rule, superiority, extraction provenance, and proposal document structs for strict rules, defeasible rules, proper defeaters, and blocking defeaters. It separates strong negation on atoms from default-negated body literals and records rule authoring/proposal metadata. Boundary: the schema round-trips authored safe rules but does not enforce DeLP safety or perform grounding; those checks live in authoring and grounding layers. Cleanup relevance: rule artifacts keep DeLP rule shape and priority assertions first-class instead of encoding them in CLI command payloads.

### `propstore/families/documents/source_alignment.py`

Owner/subsystem: typed document models for concept-alignment artifacts.

This file defines alignment arguments, argumentation framework relation sets, acceptance queries/operator scores, decisions, and a top-level concept alignment artifact document. Each struct exposes `to_payload` conversion, including list conversion for tuple fields and score dictionaries. Boundary: it is a serialization schema for alignment artifacts; scoring, argument construction, and promotion decisions are owned by alignment application logic. Cleanup relevance: source alignment records accepted/rejected local concept mappings and promoted concept ids as explicit artifacts.

### `propstore/families/documents/sources.py`

Owner/subsystem: typed source-local document models.

This file defines the source-local schema for sources, source trust/origin/metadata, source concept entries and aliases, parameterization relationships, extraction provenance, source claims, provenance snippets, justifications, stances, parameterization group merges, and finalize reports. Most structs provide `to_payload` methods that omit absent fields and lower enum/domain objects to serialized values. Boundary: this is the source authoring/document boundary; canonical claim, concept, stance, and justification promotion logic lives outside this schema. Cleanup relevance: it keeps source-local fields such as local ids, artifact codes, produced-by metadata, alignment candidates, and finalize diagnostics explicitly confined to source documents.

### `propstore/families/documents/stances.py`

Owner/subsystem: typed document model for canonical stance YAML files.

This file defines `StanceDocument`, including source claim, perspective source claim id, target claim, stance type, strength, note, condition-difference text, optional resolution, target justification id, artifact code, classifier metadata, and promoted-from commit metadata. Its payload conversion omits absent fields and lowers `StanceType` and nested resolution documents. Boundary: this schema models canonical stance files only; stance extraction, classification, and reference validation are elsewhere. Cleanup relevance: canonical stance artifacts can carry classification/promoted metadata without reusing source-local document shapes.

### `propstore/families/documents/worldlines.py`

Owner/subsystem: typed document models for worldline definitions, results, policies, and revision journals.

This file defines worldline assumption/input/policy documents, variable and input-source references, target value results, computation steps, dependency lists, revision atoms/queries/results/states, journals, top-level result payloads, and worldline definitions. It uses `msgspec.field(default_factory=dict)` for mutable defaults and carries CEL assumptions plus policy knobs for reasoning, probabilistic argumentation, merge/revision, future queries, and concept strategies. Boundary: these are persisted semantic artifact schemas; execution, reasoning, journal capture, and revision semantics live in owner layers outside the document definitions. Cleanup relevance: worldline journals and revision state are represented as propstore semantic artifacts rather than process-local CLI state.

### `propstore/families/embeddings/__init__.py`

Owner/subsystem: embeddings family package marker.

This file only contains the package docstring for embedding derived-store declaration exports. Boundary: it exports no runtime API or registration objects directly. Cleanup relevance: no behavior to migrate here; the declaration module owns the embedding family definition.

### `propstore/families/embeddings/declaration.py`

Owner/subsystem: embedding derived-store declarations and sidecar entity APIs.

This file defines claim and concept vector store specs, sqlite-vec extension loading, embedding snapshot/report dataclasses, table initialization, model registry access, entity embedding stores for claims and concepts, snapshot extraction/restoration, and public functions to embed or query similar claims/concepts. It delegates SQLite vector mechanics to Quire and text/entity selection to the claim/concept family declarations while using heuristic embedding helpers for actual embedding/query workflows. Boundary: it owns propstore-specific claim/concept embedding entity resolution and snapshot shape, not generic sqlite vector storage. Cleanup relevance: embedding state is a derived sidecar surface with explicit preservation across sidecar rebuilds.

### `propstore/families/forms/__init__.py`

Owner/subsystem: form family package API and document loading.

This file exports `FormDocument`, `LoadedForm`, and `load_form_documents`. The loader coerces a path-like forms directory to a Quire tree path, returns an empty list when absent, decodes each `.yaml` file as a `FormDocument`, and wraps it with its filename stem. Boundary: it is a shallow package surface plus file loading helper; validation and stage/pass behavior live in sibling modules. Cleanup relevance: form family loading is path/coercion based and already avoids CLI-specific behavior.

### `propstore/families/forms/documents.py`

Owner/subsystem: typed form family document schemas.

This file defines form unit alternatives, extra unit documents, and top-level form documents. The schema captures base/unit metadata, QUDT id, parameters, common and delta unit conversions, dimensions, extra units, min/max bounds, and notes using `msgspec` factories for mutable dictionaries. Boundary: it does not validate dimensional consistency or compile derived data; passes and stages consume these documents. Cleanup relevance: physical/semantic form metadata has a compact typed source schema separate from runtime dimension logic.

### `propstore/families/forms/passes.py`

Owner/subsystem: semantic pipeline passes for form artifacts.

This file defines normalize, dimension-policy, and registry passes for the forms family, plus pipeline registration and execution helpers. The policy pass validates dimension key syntax, dimensionless/dimensions/unit consistency, and filename/name matches, emitting typed `PassDiagnostic` errors. Boundary: it orchestrates form-family semantic pass stages through the generic pass runner but does not own form decoding or dimension runtime behavior. Cleanup relevance: form validation is centralized as family passes instead of being embedded in CLI or repository loading code.

### `propstore/families/forms/stages.py`

Owner/subsystem: form semantic stage objects and parsing/loading helpers.

This file defines form pipeline stages, loaded/authored/normalized/checked containers, runtime `FormDefinition`, form cache management, kind mapping, form parsing, single/all form loading, kind derivation helpers, and allowed-unit extraction. It converts authored form documents into dimension API conversion objects and normalized registries while caching lookups by directory and form name. Boundary: it owns normalized form definitions and loading/parsing, while semantic diagnostics live in passes and dimensional math lives in `propstore.dimensions`. Cleanup relevance: this is the central owner for converting form YAML into runtime form definitions.

### `propstore/families/identity/__init__.py`

Owner/subsystem: family identity primitives package marker.

This file only contains the package docstring for propstore family identity primitives. Boundary: it exports no identities directly; individual identity modules own each artifact family. Cleanup relevance: no behavior to migrate here.

### `propstore/families/identity/claims.py`

Owner/subsystem: claim artifact and version identity derivation.

This file derives deterministic claim artifact ids from normalized logical namespace/value pairs, canonicalizes claim payloads for version hashing, computes claim version ids, normalizes source claim-file payloads, rewrites local stance targets to artifact ids, and optionally strips source-local fields from canonical claim payloads. It sorts logical ids, conditions, and stance payloads before hashing and preserves invalid raw ids as data rather than local handles. Boundary: it still operates on dict payloads at the identity/document boundary; semantic claim domain objects and storage live elsewhere. Cleanup relevance: claim identity excludes source-local fields from immutable version content and lowers local handles before canonical use.

### `propstore/families/identity/concepts.py`

Owner/subsystem: concept artifact/version identity and reference normalization.

This file derives deterministic concept artifact ids, canonicalizes concept payloads for version hashing, normalizes canonical concept payloads, ensures logical ids, ontology references, lexical entries, numeric ranges, and resolves concept references through registry keys. It sorts logical ids and selected dict-list fields before hashing and adds a propstore logical id alongside the effective domain/canonical-name id. Boundary: it works at the payload/identity boundary and still accepts dictionaries; concept domain behavior, storage, and semantic validation live in the family declarations and passes. Cleanup relevance: concept canonicalization creates explicit ontology/lexical surfaces while keeping artifact identity stable and reference lookup centralized.

### `propstore/families/identity/justifications.py`

Owner/subsystem: justification artifact identity stamping.

This file canonicalizes justification payloads for identity by removing `artifact_code` and sorting premises, derives a justification artifact id through typed `JustificationDocument` conversion and `justification_artifact_code`, and stamps a copied payload with that artifact code. Boundary: it operates on JSON payloads and document conversion at the identity edge; justification semantics and storage are owned elsewhere. Cleanup relevance: justification identity is deterministic and excludes its own stored artifact code from the identity calculation.

### `propstore/families/identity/logical_ids.py`

Owner/subsystem: logical id regexes and normalization utilities.

This file defines regular expressions for claim/concept artifact ids, version ids, logical namespaces, and logical values. It parses `namespace:value` claim ids, normalizes namespace/value tokens into allowed character sets, formats logical-id dict entries, and returns a claim's primary logical id. Boundary: it is a small identity utility layer and does not derive artifact hashes itself. Cleanup relevance: shared logical id rules are centralized for claim/concept identity modules.

### `propstore/families/identity/micropubs.py`

Owner/subsystem: content identity for micropublication documents.

This file canonicalizes `MicropublicationDocument` payloads for artifact/version identity, excluding recursive `artifact_id` and `version_id`, sorting claim/assumption string lists and evidence dict lists, and then deriving ni-URI artifact ids and sha256 version ids. Boundary: it adapts Kuhn/Dumontier-style content hashing to propstore typed YAML/JSON documents rather than claiming RDF module compatibility. Cleanup relevance: micropublication identity is deterministic and self-reference aware.

### `propstore/families/identity/stances.py`

Owner/subsystem: stance artifact identity stamping.

This file canonicalizes stance payloads by removing artifact code, classifier metadata, and promoted commit metadata, derives stance artifact ids through typed `StanceDocument` conversion and `stance_artifact_code`, and stamps copied payloads with the derived artifact code. Boundary: it owns deterministic identity for stance payload dictionaries, not stance extraction/classification logic. Cleanup relevance: volatile classifier/provenance fields do not participate in stance artifact identity.

### `propstore/families/micropublications/__init__.py`

Owner/subsystem: micropublication family declaration package marker.

This file only contains the package docstring for the micropublication family declaration package. Boundary: it exports no runtime API directly; declaration logic lives in the sibling `declaration.py`. Cleanup relevance: no behavior to migrate here.

### `propstore/families/micropublications/declaration.py`

Owner/subsystem: micropublication derived-store declarations and query helpers.

This file declares the micropublication and micropublication-claim projection tables, projection models/query plans for active micropublications, sidecar row dataclasses, compilation from `MicropublicationDocument` entries, table creation, population, and selection of all active micropublications. Compilation resolves claim references through a Quire family reference index and emits quarantine diagnostics for missing claim references. Boundary: it owns micropublication sidecar projection and query surfaces; identity generation and document schemas are in identity/document modules. Cleanup relevance: micropublications use explicit family reference columns and quarantine diagnostics instead of silently accepting broken claim links.

### `propstore/families/projection_catalog.py`

Owner/subsystem: family-owned derived projection catalog.

This file imports projection tables from source, concept, context, claim, relation, rule, micropublication, calibration, embedding, and diagnostic family declarations, then assembles `PROPSTORE_WORLD_PROJECTION_SCHEMA` with metadata and sidecar schema version/key constants. Boundary: it aggregates family-owned projection declarations but does not define their table details. Cleanup relevance: sidecar world schema composition is centralized while table ownership stays with each semantic family.

### `propstore/families/registry.py`

Owner/subsystem: propstore semantic family registry and artifact-family contracts.

This file defines the `PropstoreFamily` enum, runtime/reference dataclasses, contract version constants, branch/placement policies, identity policies for claims and concepts, canonical artifact families, semantic foreign-key specs, reference-key specs, source batch encode/decode/render helpers, and the full `PROPSTORE_FAMILY_REGISTRY`. It registers canonical families, source-branch side files/batches, proposal families, concept alignments, and merge manifests with Quire artifact/family APIs. Boundary: propstore owns family names, semantic metadata, family-specific document types, placements, identity policies, and FK specs, while Quire owns the generic registry, placement, reference, and document machinery. Cleanup relevance: semantic family discovery/import roots/FK lookup/addressing are centralized here rather than reading placement contract dictionaries throughout propstore.

### `propstore/families/relations/__init__.py`

Owner/subsystem: relation family package marker.

This file only contains the package docstring for relation family declarations. Boundary: it exports no runtime API directly; relation projection declarations live in the sibling declaration module. Cleanup relevance: no behavior to migrate here.

### `propstore/families/relations/declaration.py`

Owner/subsystem: relation-edge projection rows, authored stance compilation, and read-model queries.

This file defines dataclasses for concept relationship rows, claim stance rows, and conflict rows, including coercion of relation/stance/conflict enum values and attribute mappings. It imports the projection model/table declarations, compiles authored stance documents into relation-edge sidecar rows with claim-reference validation/quarantine diagnostics, and provides selectors for stances, conflicts, relationships, policy-filtered stances, explanation stances, and conflict counts. Boundary: it owns relation-family sidecar compilation/query API while table layouts live in `projection_model.py` and claim resolution helpers live in claim family storage/reference code. Cleanup relevance: stance edges are canonical relation rows with explicit family reference validation rather than CLI-owned stance projection behavior.

### `propstore/families/relations/projection_model.py`

Owner/subsystem: Quire projection models for relation row views.

This file defines codecs for text/raw/integer/real/claim/concept/justification ids and relation/stance/conflict classes, the shared `relation_edge` table, discriminators for claim-stance and concept-relationship edges, projection models for relationship and stance rows, storage models for claim stances and concept relationships, query plans for stance/relationship views, a policy-aware stance query plan, and the conflict witness projection model/table. Boundary: it owns declarative projection/table/query mapping, while row dataclasses and compile/select APIs live in `declaration.py`. Cleanup relevance: relation edges use one typed projection surface with discriminators instead of separate ad hoc claim/concept relation tables.

### `propstore/families/rules/__init__.py`

Owner/subsystem: rules family declaration package marker.

This file only contains the package docstring for rules family declaration exports. Boundary: it exports no runtime API directly; rule projection declarations live in the sibling declaration module. Cleanup relevance: no behavior to migrate here.

### `propstore/families/rules/declaration.py`

Owner/subsystem: grounded-rule projection and query contract.

This file declares grounded fact, empty-predicate, and grounded-bundle-input projection tables; row dataclasses; table creation; deterministic population from `GroundedRulesBundle`; JSON/msgspec/gunray/ASPIC encoding and decoding of persisted bundle inputs; read-back of four-status grounded facts; runtime bundle rehydration with divergence checks; and repository snapshot bundle construction. It preserves all four gunray answer sections and separately records empty predicate classifications. Boundary: it owns durable sidecar persistence for grounded rule read models, while authored rule schemas, predicate registry loading, and the grounder live elsewhere. Cleanup relevance: grounded-rule storage is explicit, deterministic, and non-pickle sidecar state rather than an in-process cache or collapsed status table.

### `propstore/families/sameas/__init__.py`

Owner/subsystem: sameAs assertion family package marker.

This file only contains the package docstring for the sameAs assertion family. Boundary: it exports no runtime API directly; sameAs document schema lives in `documents.py`. Cleanup relevance: no behavior to migrate here.

### `propstore/families/sameas/documents.py`

Owner/subsystem: sameAs assertion document schema.

This file defines the `SameAsRelation` enum for same individual, identical claims, and almost-same-as relations, plus `SameAsAssertionDocument` with left/right artifact ids, relation, evidence source, optional artifact id, provenance, and confidence. Its payload conversion lowers the enum and omits empty optional fields. Boundary: this is only the authored document schema; sameAs reasoning, identity derivation, and storage/query behavior are not implemented here. Cleanup relevance: sameAs equivalence assertions have a typed artifact surface that can distinguish strict identity from weaker similarity.

### `propstore/families/sources/__init__.py`

Owner/subsystem: source family declaration package marker.

This file only contains the package docstring for the source family declaration package. Boundary: it exports no runtime API directly; source projection declarations live in the sibling declaration module. Cleanup relevance: no behavior to migrate here.

### `propstore/families/sources/declaration.py`

Owner/subsystem: source derived-store projection helpers.

This file declares the `source` projection table, source projection row dataclass, opinion JSON serialization, compilation from canonical `SourceDocument` entries to projection rows, and insertion into the sidecar. It stores origin fields, trust prior/quality/derived-from JSON, kind, source id, slug, and artifact code. Boundary: it owns source sidecar projection/population only; source document schemas and lifecycle workflows live elsewhere. Cleanup relevance: canonical source metadata has a simple sidecar table keyed by slug with trust/origin details serialized explicitly.

### `propstore/form_utils.py`

Owner/subsystem: form parsing/loading utility facade.

This file provides helpers to parse `FormDocument` into `FormDefinition`, load one or all form YAML files from filesystem or Quire tree paths with shared cache use, convert date/datetime values to JSON-safe strings, map form names to CEL kind values, load typed form documents, and collect allowed unit symbols. It substantially mirrors form-family stage parsing/loading behavior while importing `FormDefinition`, `_form_cache`, and `clear_form_cache` from the form stages module. Boundary: it is a utility facade around the forms family and dimension API, not a semantic pass owner. Cleanup relevance: this is a likely duplicate/compatibility surface with `propstore.families.forms.stages` for future consolidation.

### `propstore/fragility.py`

Owner/subsystem: intervention-ranked fragility orchestration.

This file defines `FragilityRequest`, binds world queries to environments, collects fragility interventions from ATMS assumptions, missing measurements, conflicts, grounded facts/rules, and bridge undercuts, applies ranking policies, computes world fragility, detects interactions, and returns `FragilityReport`. It re-exports the fragility target/report/scoring/contributor API surface through `__all__`. Boundary: this is orchestration over contributor/scoring modules and world/query stores; individual intervention construction and scoring formulas live in sibling fragility modules. Cleanup relevance: fragility query execution is owner-layer logic rather than CLI presentation code.

### `propstore/fragility_contributors.py`

Owner/subsystem: typed fragility intervention contributors by family.

This file discovers and builds ranked interventions for assumptions/ATMS, missing measurements, conflicts, grounded facts, grounded rules, and ASPIC bridge undercuts. It derives scored concepts from parameterizations and active claims, builds provenance polynomials for assumption witnesses, scores conflicts via argumentation frameworks, projects grounded rules/facts, encodes typed row/substitution keys, attaches provenance notes for heuristic coefficients, and extracts bridge inputs from a bound world. Boundary: it constructs family-specific intervention targets and local scores while ranking policy application and report assembly live in `fragility.py`, and core scoring formulas live in `fragility_scoring.py`. Cleanup relevance: fragility intervention generation is separated from CLI/world presentation and carries explicit provenance for heuristic parts.

### `propstore/fragility_scoring.py`

Owner/subsystem: fragility scoring and interaction helpers.

This file defines recoverable fragility warnings, score-combination policies, grounded-extension conflict impact scoring, weighted epistemic scores, support-derivative fragility over provenance polynomials, assumption-interaction detection through ATMS witnesses, subjective-opinion sensitivity, and `imps_rev` attack impact over DF-QuAD/weighted bipolar graphs with provenance-bearing opinion requirements. Boundary: it provides mathematical/scoring helpers and does not collect interventions or run world queries. Cleanup relevance: fragility scoring keeps heuristic/provenance-sensitive formulas in one module separate from intervention discovery.

### `propstore/fragility_types.py`

Owner/subsystem: typed intervention surfaces for fragility.

This file defines intervention kind/family/ranking/interaction enums, provenance, typed target payloads for assumptions, missing measurements, conflicts, grounded facts/rules, and bridge undercuts, `InterventionTarget`, `RankedIntervention`, `FragilityInteraction`, `FragilityReport`, and protocols for ATMS engines and fragility-capable worlds. Post-init validation enforces kind-to-family/payload consistency, positive cost tiers, normalized CEL expressions, score ranges, and provenance family matching. Boundary: it contains data contracts and protocols only; collection, scoring, ranking, and querying live in sibling modules. Cleanup relevance: fragility outputs have a typed report surface suitable for owner-layer and CLI adapters.

### `propstore/graph_export.py`

Owner/subsystem: knowledge graph export from sidecar relational structure.

This file defines graph node/edge/data containers, DOT and JSON rendering, graph export request/report objects, world-binding export entrypoint, and `build_knowledge_graph`. It builds concept and claim nodes plus parameterization, concept relationship, stance, and claim-of edges, with optional belief-space active-claim filtering and parameterization-group scoping. Boundary: it reads through world/store APIs and projection models but does not own sidecar table definitions or CLI formatting. Cleanup relevance: graph export has an owner-layer request/report surface and keeps display ids separate from artifact ids when rendering claim nodes.

### `propstore/grounding/__init__.py`

Owner/subsystem: grounding pipeline package marker.

This file only contains the package docstring for the rule-based argumentation Datalog grounding backend. Boundary: it exports no runtime API directly; bundle, fact loading, grounder, translation, and inspection live in sibling modules. Cleanup relevance: no behavior to migrate here.

### `propstore/grounding/bundle.py`

Owner/subsystem: immutable grounding pipeline output bundle.

This file defines the four-section empty grounding map, `GroundingProjectionFrame`, and `GroundedRulesBundle`. The bundle carries source rule documents, source superiority, source facts, gunray sections, optional gunray arguments, inspection data, projection frames, and status/budget metadata, with an `empty()` identity bundle that still exposes yes/no/undecided/unknown sections. Boundary: it is the frozen handoff object from the grounder to rendering, sidecar persistence, ASPIC projection, and fragility; it does not perform grounding itself. Cleanup relevance: grounded rule state keeps provenance inputs and four-valued classifications together instead of dropping empty sections or passing optional ad hoc maps.

### `propstore/grounding/complement.py`

Owner/subsystem: grounding complement encoder protocol.

This file defines the `ComplementEncoder` protocol with a single `complement(predicate)` method. Boundary: it declares the interface only; concrete gunray encoding lives in `gunray_complement.py`. Cleanup relevance: complement naming is explicit and injectable for grounding/projection code.

### `propstore/grounding/explanations.py`

Owner/subsystem: textual explanation helpers for the Gunray grounding backend.

This file defines `GroundingTextExplanation` and builds textual dialectical explanations by translating rules/facts/registry to a Gunray theory, evaluating with trace, locating the requested atom or its strong-negation complement, and rendering Gunray prose/tree output with a composite preference criterion. Boundary: Gunray owns dialectical tree construction and explanation rendering; propstore owns typed inputs and report envelope. Cleanup relevance: grounding explanation is an owner-layer helper independent of CLI formatting.

### `propstore/grounding/facts.py`

Owner/subsystem: fact extractor for the propstore-to-Datalog grounding pipeline.

This file defines `GroundingFactInputs` and extracts deterministic duplicate-free `GroundAtom` facts from loaded concept and claim data based on predicate registry `derived_from` declarations. It supports concept-relation facts plus claim attribute, condition, role, context, and provenance facts, validates each emitted atom against predicate declarations, derives claim fact ids, and sorts output by predicate/arguments. Boundary: it is the sole bridge from propstore source data to the grounding fact base; rule translation and gunray evaluation live elsewhere. Cleanup relevance: fact extraction is typed and registry-driven rather than ad hoc predicate invention.

### `propstore/grounding/grounder.py`

Owner/subsystem: thin Gunray grounder wrapper and bundle construction.

This file exposes `ground`, translating propstore rules/facts/registry/superiority into a Gunray theory, evaluating it with marking/closure/budget options, normalizing the raw model into immutable four-section output, sorting Gunray arguments deterministically, handling enumeration-budget failures, and packaging everything into `GroundedRulesBundle`. It also builds projection frames from source facts and Gunray grounding inspection instances with stable backend atom ids. Boundary: Gunray owns substitution enumeration and dialectical evaluation; propstore owns input translation, output normalization, provenance envelope, and deterministic bundle shape. Cleanup relevance: grounding has a single public entrypoint and preserves all four DeLP answer sections for downstream storage/rendering.

### `propstore/grounding/gunray_complement.py`

Owner/subsystem: concrete Gunray complement encoder.

This file defines `GunrayComplementEncoder`, which delegates complement naming to Gunray by complementing an empty-argument `GroundAtom`, and exposes a singleton `GUNRAY_COMPLEMENT_ENCODER`. Boundary: it adapts the generic complement encoder protocol to Gunray’s concrete complement implementation. Cleanup relevance: strong-negation/complement spelling is centralized for grounding projection code.

### `propstore/grounding/inspection.py`

Owner/subsystem: typed inspection reports for grounded rule surfaces.

This file defines grounding inspection error/report dataclasses, surface detection, bundle requirement checks, atom/rule/argument formatting, query-atom parsing, and inspection entrypoints for status, show, query, arguments, and explain. It reads predicate/rule authoring from the repository, builds bundles as needed, counts sections, formats grounded rules from Gunray arguments, and delegates explanation text to the explanation helper. Boundary: the grounding package owns surface classification and report data; CLI should only render these reports. Cleanup relevance: grounding inspection is owner-layer logic and keeps presentation adapters out of bundle loading and atom parsing.

### `propstore/grounding/loading.py`

Owner/subsystem: repository-family loading helpers for the grounding pipeline.

This file defines `GroundingInputs`, loads predicate/rule/superiority documents from repository family handles, builds a predicate registry, loads concept handles into `LoadedConcept` records, feeds claim handles into fact extraction, and builds a `GroundedRulesBundle` for a repository snapshot. It returns an empty bundle when no predicates/rules exist and fails when rules exist without predicates. Boundary: it bridges repository family APIs to grounding inputs; actual fact extraction and Gunray evaluation live in `facts.py` and `grounder.py`. Cleanup relevance: grounding input loading is family-registry based instead of direct directory walking.

### `propstore/grounding/predicates.py`

Owner/subsystem: predicate registry and `derived_from` DSL for the Datalog grounder.

This file defines predicate registry errors, `DerivedFromSpec`, `PredicateAtom`, strict parsing for supported `derived_from` forms, and `PredicateRegistry`. The registry rejects duplicate predicate ids, looks up predicate documents, validates atom arity and per-position argument types, and exposes all declarations in order. The DSL covers concept relations and claim attributes, conditions, roles, context, and provenance. Boundary: this is schema/registry validation for grounding; fact extraction consumes parsed specs and grounder translation consumes the registry. Cleanup relevance: predicate signatures and data-derivation routes are explicit authoring schema rather than hidden extractor conventions.

### `propstore/grounding/translator.py`

Owner/subsystem: translator from propstore rule/fact documents to Gunray theories.

This file exposes `translate_to_theory`, converting `RuleDocument` inputs and `GroundAtom` facts into a `gunray.DefeasibleTheory`. It stringifies atoms/body literals/terms for Gunray parsing, groups facts by predicate, routes strict/defeasible/defeater rules to the correct theory slots, validates and transitively closes authored superiority pairs, and quotes string constants to preserve variable/constant distinction. Boundary: it does not ground rules; Gunray performs substitution/evaluation, while propstore owns the structured-to-Gunray schema projection. Cleanup relevance: rule translation is a single owner-layer boundary between typed propstore artifacts and the Gunray backend.

### `propstore/heuristic/__init__.py`

Owner/subsystem: heuristic-layer package marker.

This file only contains the package docstring for heuristic-layer APIs. Boundary: it exports no runtime API directly; individual heuristic workflows live in sibling modules. Cleanup relevance: no behavior to migrate here.

### `propstore/heuristic/calibrate.py`

Owner/subsystem: calibration bridge from raw model outputs to opinion algebra.

This file implements temperature scaling, corpus-distance CDF calibration, categorical prior registries, categorical-to-opinion conversion, probability-to-opinion conversion, and binary calibration metrics (`brier_score`, `log_loss`, ECE). It uses explicit provenance for calibrated priors/corpus calibration, returns `BaseRateUnresolved` when categorical base rates are missing, and avoids fabricating certainty from corpus size by using local effective sample size. Boundary: depends only on opinion/provenance/base-rate domain code and stdlib; it does not run embedding or LLM models itself. Cleanup relevance: heuristic confidence calibration has provenance-bearing opinion outputs rather than hardcoded confidence lookup tables.

### `propstore/heuristic/classify.py`

Owner/subsystem: LLM stance classifier for directional epistemic relationships.

This file defines classifier prompt construction, enrichment context for close embedding pairs, `ClassifiedStance`, LLM response parsing, error/abstain stance construction, opinion payload serialization, category/corpus calibration integration, async two-direction stance classification through litellm, call-id hashing, and a synchronous wrapper. It treats each direction as an independent LLM call and represents missing confidence, malformed output, missing base rates, and model errors as abstain/error payloads rather than inferred relationships. Boundary: it classifies claim-pair relationships and produces stance dictionaries; candidate-pair discovery and persistence live in relate/source workflows. Cleanup relevance: stance classification is separated from pair selection and carries prompts/raw responses/opinion provenance in resolution metadata.

### `propstore/heuristic/embed.py`

Owner/subsystem: embedding generation and similarity search helpers.

This file defines embedding/similarity store protocols, litellm dependency loading, float32 vector serialization, generic entity embedding generation with content-hash skipping and progress callbacks, top-k similarity lookup by embedding model identity, and cross-model agreement/disagreement helpers. Boundary: it is store-agnostic heuristic logic; sidecar-specific stores live in family declarations and entity text construction lives in core/family modules. Cleanup relevance: embedding workflows are centralized around explicit store protocols and model identities rather than direct SQLite or claim-only code.

### `propstore/heuristic/embedding_identity.py`

Owner/subsystem: stable embedding model identity for heuristic caches.

This file defines `EmbeddingModelIdentity` with provider, model name, version, cache-relevant content digest, constructors from model name/config or registry row, and an identity hash over the full identity tuple. Boundary: it supplies model identity values for embedding stores and does not perform embedding or persistence. Cleanup relevance: embedding cache keys include provider/config/version details instead of relying on model-name strings alone.

### `propstore/heuristic/predicate_extraction.py`

Owner/subsystem: predicate proposal extraction for papers.

This file loads the predicate extraction prompt resource, hashes the prompt and paper notes, parses LLM/test-fixture JSON into typed `PredicateDeclaration` values, builds `PredicateProposalDocument` provenance, locates proposal predicate family paths/branches, and records proposal documents through repository family transactions unless dry-run. The live LLM call is a placeholder that raises without an injected response/client. Boundary: it owns predicate proposal document creation and persistence, not canonical predicate promotion or grounding registry behavior. Cleanup relevance: predicate extraction writes typed proposal-branch artifacts with prompt/notes provenance instead of directly mutating canonical predicates.

### `propstore/heuristic/relate.py`

Owner/subsystem: pair discovery and batch orchestration for epistemic relationship classification.

This file defines the claim relation store protocol, async runner helper, directed-distance pair deduplication, shared-concept extraction, single-claim relation workflow, all-claim relation workflow, and synchronous wrappers. It loads embedding extension/models, retrieves claim text, finds similar claims, deduplicates unordered pairs while preserving forward/reverse distances, gathers reference distances for calibration, invokes directional stance classification concurrently, and aggregates stances by source claim. Boundary: pair selection/batching lives here; LLM stance classification and calibration live in `classify.py` and `calibrate.py`, and persistence is handled by callers. Cleanup relevance: embedding-neighbor discovery is separated from stance inference and preserves directed-distance metadata for calibration.

### `propstore/heuristic/rule_corpus.py`

Owner/subsystem: lint and synthetic metadata helpers for extracted rule corpora.

This file defines `RuleCorpusLintReport`, predicate-reference validation, variable-safety validation, YAML loading helpers, rule-body/head term extraction, corpus linting over per-paper predicate/rule proposal files, and a synthetic metadata lookup for selected papers. Boundary: it is a heuristic/test/lint helper for WS-K2 extracted rule corpora, not canonical rule promotion or grounding execution. Cleanup relevance: extracted rule quality checks are isolated from the main grounding pipeline.

### `propstore/heuristic/rule_extraction.py`

Owner/subsystem: rule proposal extraction for papers.

This file loads the rule extraction prompt resource, hashes prompts/notes/predicate declarations, parses simple atom/body literal strings into typed rule documents, validates extracted predicate references against registered predicates for a source paper, builds `RuleProposalDocument` provenance, records accepted proposal files through repository family transactions, and reports rejected candidates with missing predicates. The live LLM call is a placeholder unless a fixture response is supplied. Boundary: it owns proposal-branch rule document creation, not canonical rule promotion, grounding, or deep safety checks. Cleanup relevance: rule extraction remains a proposal workflow with typed rejections instead of direct canonical mutation.

### `propstore/heuristic/source_trust.py`

Owner/subsystem: source-level trust opinion utility.

This file defines `derive_source_trust`, combining a caller prior and source-chain trust opinion using Jøsang consensus. Boundary: it is a tiny opinion-algebra helper and does not compute priors or chain opinions itself. Cleanup relevance: source trust composition is explicit rather than selecting one trust signal and discarding the other.

### `propstore/importing/__init__.py`

Owner/subsystem: import contract package exports.

This file re-exports repository import plan/result types and plan/commit functions from `repository_import.py` through `__all__`. Boundary: it is a shallow import package API and does not implement import behavior. Cleanup relevance: package import surface is narrow.

### `propstore/importing/machinery.py`

Owner/subsystem: typed import contract machinery and authored-surface compiler.

This file defines non-NL authored import surfaces, external inference/source/license/import-run/mapping/context metadata types, an import lens between surfaces and structural forms, import metadata payload/identity, compilation to `SituatedAssertion` with provenance graph references, and an explicit equivalence-witness store that records asserted/derived unresolved candidate equivalences without identity closure. It validates URI/content-hash/nonempty fields, canonicalizes candidate pairs and URI tuples, and derives stable witness/provenance ids by JSON hashes. Boundary: this module compiles one authored import form and metadata envelope; bulk import workflows and semantic guessing live elsewhere. Cleanup relevance: import behavior is typed and provenance-rich, with equivalence witnesses kept separate from sameAs identity closure.

### `propstore/importing/passes.py`

Owner/subsystem: semantic import normalization pipeline pass.

This file builds a semantic import registry, plans family writes, normalizes concept/claim/stance import batches, rewrites concept references and imported claim handles, records ambiguous imported claim handle warnings, and registers/runs a source import normalization pass through the semantic pass runner. Concept imports get default canonical/status/definition/form values and canonical identity normalization; claim imports require one claim per file and are normalized through source claim-concept logic; stance imports rewrite source/target claim refs through the imported claim index. Boundary: it owns normalization of committed repository import writes, not source discovery or transaction commit. Cleanup relevance: import normalization is a semantic pass with family-aware rewriting rather than ad hoc repository file copying.

### `propstore/importing/repository_import.py`

Owner/subsystem: committed-snapshot repository import planning and commit helpers.

This file defines repository import plan/result dataclasses, semantic path collection, repository-name inference, import-run provenance construction, import planning from a source git-backed repository snapshot through the source import pipeline, delete/touched-path calculation against an existing import branch, and commit execution into a destination branch with provenance note writing. It refuses imports with normalization warnings and requires git-backed repositories. Boundary: it owns repository import planning/commit orchestration; family-specific normalization lives in `passes.py` and Quire owns low-level git/family transaction mechanics. Cleanup relevance: repository imports use semantic family registries and explicit provenance rather than broad file copies.

### `propstore/importing/stages.py`

Owner/subsystem: repository import stage objects.

This file defines source import stage enum values, planned semantic write records, authored and normalized write containers, and mutable normalization state carrying repository name, concept reference map, imported claim handles, and warnings. Boundary: it contains pipeline data structures only; normalization and commit logic live in `passes.py` and `repository_import.py`. Cleanup relevance: import pipeline state is explicit and typed for semantic pass execution.

### `propstore/json_types.py`

Owner/subsystem: shared JSON-native type aliases.

This file defines recursive aliases for JSON scalar, value, and object types. Boundary: it is typing-only and has no runtime behavior. Cleanup relevance: JSON payload boundaries can use one shared alias vocabulary.

### `propstore/merge/__init__.py`

Owner/subsystem: semantic repository merge package marker.

This file only contains the package docstring for semantic repository merge services. Boundary: it exports no runtime API directly; merge behavior lives in sibling modules. Cleanup relevance: no behavior to migrate here.

### `propstore/merge/description_kinds.py`

Owner/subsystem: argumentation-backed description-kind coreference merge query.

This file defines `CoreferenceQuery` around a description-kind merge protocol and Dung argumentation framework. It exposes merge arguments and computes coreference clusters under grounded/preferred/stable semantics, plus a `coreference_query` constructor from merge arguments and attacks. Boundary: it adapts lemon description-kind merge arguments to argumentation semantics; it does not write merge manifests or repository changes. Cleanup relevance: description-kind merge decisions are represented through explicit argumentation semantics.

### `propstore/merge/merge_claims.py`

Owner/subsystem: typed claim surface for repository merge semantics.

This file defines `MergeClaim`, wrapping canonical `ClaimDocument` values with branch-origin metadata, artifact/logical/value accessors, a merge-time `SituatedAssertion` projection, assertion id derivation, provenance payload construction, and payload/dict-like access helpers. It derives stable condition and provenance references from claim conditions and provenance JSON while excluding identity/context/stance fields from semantic content. Boundary: it adapts claim documents to merge assertion semantics; classification, witness construction, and commits live in other merge modules. Cleanup relevance: merge logic can compare claims as situated assertions with explicit provenance instead of loose claim dictionaries.

### `propstore/merge/merge_classifier.py`

Owner/subsystem: formal repository merge framework construction.

This file builds a provenance-bearing partial argumentation framework over claim alternatives from two or more branches. It indexes claim artifacts, groups canonical claims by logical ids, compares branch/base claim payloads, classifies pair differences through conflict detection with provenance requirements, emits merge arguments with witness bases, applies optional integrity constraints, deduplicates assertion ids, computes attack/ignorance/non-attack pairs, and identifies semantic candidate groups. Boundary: it constructs the merge object and formal relations; manifest rendering and repository writes live elsewhere. Cleanup relevance: repository merge output is a formal partial AF with provenance rather than an informal claim-bucket classification.

### `propstore/merge/merge_commit.py`

Owner/subsystem: merge commit creation for propstore knowledge repositories.

This file defines non-claim merge conflict errors and `create_merge_commit`, which builds the formal merge framework, verifies branch heads, carries through identical/non-conflicting non-claim tree entries, materializes merge arguments as claim payloads, rewrites artifact ids for rival alternatives, stamps claim versions, prepares a merge manifest with semantic candidate details, stores blobs, and commits a two-parent flat tree to the target branch with expected-head checking. Boundary: it owns repository write materialization from the merge framework; framework construction lives in `merge_classifier.py` and Quire/git owns low-level tree commits. Cleanup relevance: merge commits reject non-claim content conflicts instead of silently choosing one side.

### `propstore/merge/merge_report.py`

Owner/subsystem: repository-facing summaries for merge frameworks.

This file produces semantic candidate detail payloads and formal merge summaries from `RepositoryMergeFramework`. It computes skeptical and credulous acceptance under a chosen semantics, reports attacks/ignorance/non-attacks, relation counts, completion count, canonical groups, argument details, semantic candidates, and per-argument statuses. Boundary: it is reporting over an already-built merge framework; it does not classify merge pairs or write commits. Cleanup relevance: merge framework reporting is structured and independent of CLI rendering.

### `propstore/merge/structured_merge.py`

Owner/subsystem: branch-local structured projection and exact merge candidates.

This file defines branch argumentation evidence and structured summary records, builds argumentation evidence from structured projections, extracts inline/file stance rows, loads branch claims, canonicalizes stance rows, computes branch content signatures/provenance summaries/lossiness metadata, builds branch ASPIC projections with branch-local grounding bundles, and computes exact structured merge candidates using sum/max/leximax partial-AF merge operators. Boundary: it summarizes and merges branch argumentation structures; it does not create repository commits or classify claim-pair conflicts. Cleanup relevance: structured merge candidates are generated from formal argumentation projections with explicit lossiness declarations.

### `propstore/merge/witness.py`

Owner/subsystem: merge provenance witness records.

This file defines `ProvenanceWitness`, with construction from a `MergeClaim` provenance payload and serialization to payload form. It captures source artifact id, source paper/page, branch origin, and optional rule chain. Boundary: it is a small data adapter for merge provenance; merge framework construction consumes it. Cleanup relevance: merge arguments carry explicit source/branch witness metadata.

### `propstore/observatory.py`

Owner/subsystem: deterministic observatory reports for epistemic workflow behavior.

This file defines versioned, content-hashed dataclasses for semantic trace records, evaluation scenarios, scenario evaluations, operator-family summaries, and observatory reports. It provides dict serialization/deserialization with content-hash validation, deterministic sorting/canonical JSON hashing, pass/falsification status, scenario evaluation, and operator summary aggregation. Boundary: it is report/data-contract logic only; workflow replay, falsification generation, and CLI rendering live elsewhere. Cleanup relevance: observatory outputs are deterministic and self-verifying through schema versions and content hashes.

### `propstore/opinion.py`

Owner/subsystem: subjective logic opinion algebra.

This file defines the `Opinion` and `BetaEvidence` dataclasses, evidence/probability constructors, expectation/uncertainty interval, beta evidence conversion, negation, conjunction/disjunction, ordering, uncertainty maximization, consensus, discounting, weighted belief fusion, consensus and compromise fusion, and fusion dispatch. It enforces opinion component/base-rate constraints, blocks truthiness, quantizes equality/hash consistently, handles dogmatic/vacuous cases, and composes provenance for opinion operators. Boundary: it is a core opinion algebra module with no higher-level workflow logic, though it imports provenance records for operator provenance. Cleanup relevance: uncertainty/trust math is centralized and provenance-aware rather than spread through heuristic code.

### `propstore/parameterization_groups.py`

Owner/subsystem: connected-component analysis for concept parameterization graphs.

This file accepts concept records, loaded concepts, or concept-like mappings; extracts artifact/reference keys and parameterization inputs; resolves aliases/logical ids; and builds connected components using union-find. Boundary: it computes group membership only and does not write sidecar group rows or mutate concepts. Cleanup relevance: parameterization grouping supports both typed and payload inputs while centralizing alias resolution for graph connectivity.

### `propstore/parameterization_walk.py`

Owner/subsystem: shared utilities for walking parameterization graphs.

This file provides breadth-first reachable concept traversal over parameterization rows and a helper to build output-to-parameterization edge maps from concept registry dictionaries with optional exactness filtering. It coerces row-like inputs through the parameterization projection model when needed. Boundary: it supplies shared traversal utilities for worldline resolution and conflict detection, not graph persistence or evaluation. Cleanup relevance: transitive parameterization walking is centralized across consumers.

### `propstore/policies.py`

Owner/subsystem: inspectable policy profiles for epistemic workflows.

This file defines versioned policy dataclasses for revision, merge, admissibility, source trust, escalation, and top-level `PolicyProfile`, with dict parsing/serialization, canonical content hashing, derived profile ids, render-policy conversion, and projection of policy profile fields into situated assertions. It normalizes enum-like backend/semantics/merge values and validates recorded profile/content hashes on load. Boundary: it models policy data and assertions; policy execution is owned by world/support-revision/merge layers. Cleanup relevance: workflow policy choices are inspectable, hash-addressed, and assertable as semantic facts rather than implicit runtime flags.

### `propstore/praf/__init__.py`

Owner/subsystem: probabilistic argumentation adapter package exports.

This file re-exports PrAF engine errors/results/functions, `PropstorePrAF`, stance/claim conversion helpers, relation summary helpers, and `build_praf` from projection. Boundary: it is a package API surface only; engine/projection modules own behavior. Cleanup relevance: PrAF public surface is explicitly enumerated through `__all__`.

### `propstore/praf/engine.py`

Owner/subsystem: propstore adapters for probabilistic argumentation.

This file defines calibration-missing sentinels, PrAF preference-layer errors, `PropstorePrAF`, COH enforcement results, claim/stance-to-opinion conversion helpers, PrAF kernel extraction, COH rationality enforcement over argument opinions, and defeat-relation marginal summarization as provenance-bearing probabilistic relations. It keeps omitted arguments/relations immutable, handles source-prior/quality discounting, refuses uncalibrated confidence-only inputs without evidence counts/base rates, and reconstructs kernel probabilities from opinion expectations. Boundary: formal PrAF algorithms live in `argumentation.probabilistic`; this module owns propstore opinion/provenance/diagnostic adaptation. Cleanup relevance: probabilistic argumentation inputs require explicit calibration rather than raw confidence shortcuts.

### `propstore/praf/projection.py`

Owner/subsystem: store-based probabilistic argumentation projection construction.

This file defines `build_praf`, which builds shared analyzer input from a world store and active claim ids, then delegates to `build_praf_from_shared_input`. Boundary: it is a thin store adapter; PrAF engine details and shared analyzer construction live elsewhere. Cleanup relevance: store-to-PrAF conversion has a narrow owner-layer entrypoint.

### `propstore/preference.py`

Owner/subsystem: propstore metadata preference heuristics.

This file defines `MetadataStrengthVector`, provenance construction for metadata-derived strength, `metadata_strength_vector`, and `claim_strength`. It converts claim metadata into a three-dimensional vector (sample-size log, inverse uncertainty, confidence) paired with a subjective opinion, deriving uncertainty from evidence when possible and using vacuous opinion when metadata is insufficient. Boundary: it supplies heuristic strength vectors for preference consumers; ASPIC/claim graph comparison logic lives elsewhere. Cleanup relevance: missing metadata is represented as uncertainty rather than fabricated finite preference strength.

### `propstore/probabilistic_relations.py`

Owner/subsystem: primitive probabilistic relation records for argumentation.

This file defines relation kind aliases, relation provenance, probabilistic relation records, claim graph relation bundles, and helpers to derive stable provenance from stance-like rows, create relation records, and map relations to edge-opinion dictionaries. Boundary: it represents primitive/derived relation uncertainty and provenance; PrAF construction and stance extraction live elsewhere. Cleanup relevance: derived semantic relations can be reported with uncertainty without becoming canonical primitive inputs.

### `propstore/propagation.py`

Owner/subsystem: shared SymPy evaluation for parameterization relationships.

This file defines typed parameterization evaluation statuses/results, cached SymPy parsing, symbol rewriting from authored aliases to safe runtime symbols, and parameterization evaluation for bare expressions and `Eq(output, expr)` equations. It distinguishes missing SymPy, parse errors, missing inputs, no solution, and non-numeric results instead of returning overloaded `None`. Boundary: it evaluates one expression from provided numeric inputs; graph traversal and worldline conflict handling live elsewhere. Cleanup relevance: parameterization evaluation is a reusable typed service for propagation and conflict detection.

### `propstore/proposal_promotion.py`

Owner/subsystem: shared transaction helper for planned proposal promotions.

This file defines `PlannedCanonicalArtifact` and a helper to commit already-planned canonical artifacts through a supplied transaction context and family writer callback. It returns zero for empty plans and otherwise saves each planned artifact in one transaction. Boundary: planning/validation of promotion artifacts happens elsewhere; this only commits a prepared set. Cleanup relevance: promotion commit mechanics are shared without coupling to one proposal family.

### `propstore/proposals.py`

Owner/subsystem: committed stance proposal artifacts.

This file provides stance proposal branch/path helpers, promotion plan/result dataclasses, unknown/already-promoted errors, stance proposal promotion planning from the proposal branch, promotion to canonical stance artifacts with promoted-from sha, proposal document construction/stamping from classification results, YAML encoding, and committing stance proposal snapshots to a proposal branch. Boundary: this module owns stance proposal persistence/promotion mechanics; claim-pair classification and relation discovery live in heuristic modules. Cleanup relevance: proposal artifacts are durable family-managed git state on proposal branches, not ambient working-tree files.

### `propstore/proposals_predicates.py`

Owner/subsystem: predicate proposal planning and promotion.

This file defines predicate proposal promotion item/plan/result dataclasses, finds predicate proposal documents by source paper on the fixed proposal branch, skips already-promoted proposals, builds planned canonical `PredicateDocument` artifacts, checks predicate document conflicts under the mutation lock, and commits promoted predicates through a head-bound family transaction. Boundary: it promotes already-authored predicate proposal artifacts; extraction lives in heuristic predicate extraction and canonical mutation conflict rules live in app predicate logic. Cleanup relevance: predicate promotion is planned and conflict-checked before canonical writes.

### `propstore/proposals_rules.py`

Owner/subsystem: rule proposal planning and selective promotion.

This file defines rule proposal promotion item/plan/result dataclasses, selects proposal rule refs by source paper and optional rule ids, reports unknown requested rules, skips already-promoted rules, builds planned canonical `RuleDocument` artifacts with source/authoring/promoted metadata, checks canonical rule conflicts under the rule mutation lock, and commits promoted rules through a head-bound family transaction. Boundary: it promotes proposal artifacts only; extraction and canonical rule mutation policy live in other modules. Cleanup relevance: rule promotion is selective, planned, conflict-checked, and provenance-stamped.

### `propstore/provenance/__init__.py`

Owner/subsystem: provenance package model, git-note named graphs, and stamping API.

This file defines provenance status/witness/record types, deterministic JSON-LD named graph encoding/decoding, git-note read/write helpers on `refs/notes/provenance`, composition semantics for derived provenance, and YAML/Markdown `produced_by` stamping. It also re-exports the polynomial, homomorphism, nogood, projection, record, support, and variable provenance APIs. Boundary: named-graph/provenance metadata mechanics live here; specific provenance algebra and record families live in sibling modules. Cleanup relevance: provenance status and graph names are explicit and validated rather than implicit side metadata.

### `propstore/provenance/derivative.py`

Owner/subsystem: provenance polynomial sensitivity operation.

This file defines `partial_derivative`, normalizing a source variable id and differentiating each provenance polynomial term with respect to that variable. Boundary: it depends on the polynomial and source-variable value types only; polynomial normalization and evaluation are owned elsewhere. Cleanup relevance: source sensitivity is expressed as a typed provenance-algebra operation instead of ad hoc coefficient rewriting.

### `propstore/provenance/homomorphism.py`

Owner/subsystem: generic provenance polynomial homomorphic evaluation.

This file defines the `Homomorphism` protocol (`zero`, `one`, `add`, `mul`, and variable interpretation) plus `evaluate`, which folds a provenance polynomial into any target semiring-like domain. Boundary: it is algebraic plumbing only; concrete homomorphisms and provenance meaning are supplied by callers. Cleanup relevance: provenance projections can share one evaluator instead of duplicating polynomial traversal.

### `propstore/provenance/nogoods.py`

Owner/subsystem: provenance nogood representation and polynomial filtering.

This file defines nogood witness and provenance-bearing nogood records, normalizes nogood variables to `SourceVariableId`, and implements `live` to remove polynomial terms whose squarefree support contains a nogood set. Boundary: it filters provenance polynomial supports; discovery/justification of nogoods comes from callers. Cleanup relevance: inconsistent support combinations are explicit provenance objects instead of hidden filtering rules.

### `propstore/provenance/polynomial.py`

Owner/subsystem: canonical provenance polynomial value types.

This file defines `VariablePower`, `PolynomialTerm`, and `ProvenancePolynomial`, enforcing positive exponents/coefficients, normalizing source variable ids, combining duplicate powers and like terms, and implementing zero/one/variable constructors plus addition, multiplication, support extraction, and zero checks. Boundary: it owns immutable polynomial normalization and algebra; semantic projections and derivatives live in sibling modules. Cleanup relevance: provenance support algebra has a deterministic typed representation rather than loose term dictionaries.

### `propstore/provenance/projections.py`

Owner/subsystem: semantic projections from provenance polynomials.

This file defines `WhySupport`, boolean presence over trusted variables, derivation counting, why-provenance support extraction with assumption/context variable mapping, support normalization by minimality, and tropical min-plus cost evaluation through the generic homomorphism evaluator. Boundary: it interprets already-built provenance polynomials; source variable derivation and polynomial construction live elsewhere. Cleanup relevance: different provenance views are explicit projections rather than separate bespoke provenance stores.

### `propstore/provenance/prov_o.py`

Owner/subsystem: PROV-O JSON-LD export boundary.

This file maps typed provenance records and generic provenance payloads into one-way PROV-O JSON-LD documents with entities, activities, agents, derivation links, source/license/import/projection/external statement/external inference nodes, and the shared propstore/prov context. Boundary: it is export-only and does not drive internal mutation semantics. Cleanup relevance: external provenance interchange is isolated from the internal typed provenance model.

### `propstore/provenance/records.py`

Owner/subsystem: typed provenance record carriers.

This file defines validated dataclass records for source versions, licenses, import runs, projection frames, external statements, and external inferences, plus `ExternalStatementAttitude` and shared URI/non-empty/content-hash canonicalization helpers. Each record exposes deterministic identity and payload forms. Boundary: it models provenance facts for import/export carriers; PROV-O rendering and named-graph note storage live elsewhere. Cleanup relevance: provenance carrier identity is explicit and validated instead of being assembled from loose dictionaries.

### `propstore/provenance/support.py`

Owner/subsystem: support evidence wrapper for semiring provenance.

This file defines support quality categories and `SupportEvidence`, pairing a provenance polynomial with a normalized quality enum. Boundary: it is a small value object used by higher-level semantic support logic; polynomial algebra lives in `polynomial.py`. Cleanup relevance: support quality is typed separately from the polynomial itself.

### `propstore/provenance/trusty.py`

Owner/subsystem: provenance-facing trusty/NI URI byte helpers.

This file wraps `propstore.uri` NI URI compute and verify functions as provenance primitives, currently defaulting to SHA-256 artifact-code identifiers. Boundary: actual NI URI implementation lives in `propstore.uri`; this module is a provenance namespace adapter. Cleanup relevance: provenance identity hashing is routed through one URI primitive instead of reimplementing hashing locally.

### `propstore/provenance/variables.py`

Owner/subsystem: stable source-variable identities for provenance polynomials.

This file defines `SourceVariableId`, source roles, `SourceVariable`, and deterministic id derivation from role, artifact id, and canonical body hash. `SourceVariable` validates that its id is exactly the derived hash-based value and carries provenance for the source variable itself. Boundary: it owns variable identity; polynomial structure and projections consume these ids. Cleanup relevance: provenance support variables are content-addressed and role-scoped instead of arbitrary strings.

### `propstore/relation_analysis.py`

Owner/subsystem: stance/relation summary for argumentation render explanations.

This file defines `stance_summary`, which reads stance rows from a world store, coerces them through the relation projection model, counts total/included/non-attack/vacuous stances, collects resolution model names, and reports mean uncertainty when available. Boundary: it summarizes stance surfaces for explanation; AF construction, rendering, and resolution policy live elsewhere. Cleanup relevance: uncertainty and non-attack exclusions are reported rather than silently used as pre-render filters.

### `propstore/reporting.py`

Owner/subsystem: shared JSON report serialization.

This file defines `JsonReportMixin` and `json_ready`, recursively converting dataclasses, enums, paths, mappings, and sequences into JSON-compatible values using the project `JsonValue` alias. Boundary: it prepares report payloads only; report construction and rendering live in caller modules. Cleanup relevance: report serialization uses one typed conversion path instead of per-report ad hoc encoders.

### `propstore/repository.py`

Owner/subsystem: propstore repository root, bootstrap, and path/family access.

This file defines repository constants, `RepositoryNotFound`, repository config decoding, the `Repository` object with root/git/tree/families/snapshot/derived-store access, repository discovery/init/bootstrap manifest handling, live branch update retry around stale heads, and safe branch tree export with path escape checks. Boundary: it locates and binds propstore stores; individual family behavior, git storage internals, and semantic operations live in owner modules. Cleanup relevance: store bootstrap state and family registry binding are centralized behind the repository object.

### `propstore/resources.py`

Owner/subsystem: packaged and development resource loading.

This file detects development mode, resolves resources from `propstore/_resources` directly in source checkouts or through `importlib.resources` when installed, and provides text, package-local text, JSON, and existence helpers. Boundary: it only loads static resources; callers own interpretation of the loaded payloads. Cleanup relevance: installed/package resource access is centralized instead of callers hard-coding source-tree paths.

### `propstore/semantic_passes/__init__.py`

Owner/subsystem: semantic pass pipeline package marker.

This file contains only the package docstring for the explicit semantic pass pipeline substrate. Boundary: behavior is in sibling modules. Cleanup relevance: it marks the package without re-exporting deeper pass machinery.

### `propstore/semantic_passes/diagnostics.py`

Owner/subsystem: semantic pass diagnostic rendering helper.

This file defines `render_diagnostics`, converting pass diagnostic objects to their rendered strings. Boundary: diagnostic structure lives in `types.py`; this is a presentation helper for pass results. Cleanup relevance: diagnostic rendering is kept as a tiny shared adapter instead of duplicated loops.

### `propstore/semantic_passes/registry.py`

Owner/subsystem: lazy semantic pipeline registration and ordering.

This file defines `PipelineRegistryError` and `PipelineRegistry`, registering pass classes per `PropstoreFamily`, rejecting family/name mismatches, listing registered passes, and selecting a linear pipeline from start stage to target stage by checking each pass input/output stage. Boundary: it owns pass declaration validation and pipeline selection; pass execution and pass result types live in runner/types. Cleanup relevance: semantic stage ordering is validated centrally instead of relying on implicit import order.

### `propstore/semantic_passes/runner.py`

Owner/subsystem: linear semantic pipeline execution.

This file defines `PipelineExecutionError` and `run_pipeline`, which asks a registry for the family/stage pipeline, instantiates passes in order, enforces family and stage contracts, accumulates diagnostics, handles pass errors with no output, and returns a typed `PipelineResult`. Boundary: it executes already-registered pass classes; registry selection and pass type declarations are separate. Cleanup relevance: stage contract violations fail explicitly during execution.

### `propstore/semantic_passes/types.py`

Owner/subsystem: shared semantic pass pipeline data contracts.

This file defines stage and diagnostic types, `PassDiagnostic`, generic `PassResult` and `PipelineResult` containers with error/warning helpers, the `SemanticPass` protocol, and `FamilyPipeline`. Boundary: it declares contracts only; registry and runner enforce/use them. Cleanup relevance: pass outputs and diagnostics are typed objects instead of unstructured status dictionaries.

### `propstore/sensitivity.py`

Owner/subsystem: local and global sensitivity analysis for parameterized concepts.

This file defines sensitivity result/request/report dataclasses, `query_sensitivity`, local derivative-based `analyze_sensitivity`, and Saltelli-style sampled global sensitivity estimates. It resolves concept ids, selects compatible parameterizations, rewrites symbols safely, resolves input values from bound worlds or overrides, computes partial derivatives/elasticities with SymPy, and estimates first-order/total indices from bounded samples. Boundary: it analyzes existing world parameterizations; parameterization storage, compatibility, and numeric propagation live elsewhere. Cleanup relevance: sensitivity reports are typed and separate local derivative analysis from global variance analysis.

### `propstore/source/__init__.py`

Owner/subsystem: public API aggregator for source-branch workflows.

This file re-exports source alignment, claim/concept/relation proposal commit helpers, source metadata/notes/init helpers, finalize/promote/status functions, and source registry projection/matching helpers through an explicit `__all__`. Boundary: it is an API surface only; behavior lives in sibling modules. Cleanup relevance: source subsystem entrypoints are enumerated rather than relying on broad package imports.

### `propstore/source/alignment.py`

Owner/subsystem: source concept alignment framework and promotion workflow.

This file builds concept-alignment artifacts from source-branch proposals, classifies proposal relations using lexical identity/definition/opinion uncertainty, computes partial argumentation framework acceptance queries, stores alignment artifacts in the concept-alignment family, records alignment decisions, and promotes accepted alternatives into canonical concept documents. Mutating operations are serialized through the repository mutation guard. Boundary: it owns source concept alignment artifacts; source proposal authoring, canonical concept identity normalization, and family storage are delegated to their owners. Cleanup relevance: alignment decisions and promotions are durable family artifacts instead of transient CLI choices.

### `propstore/source/claim_concepts.py`

Owner/subsystem: source/local concept reference rewriting during claim import and promotion.

This file defines normalized imported/promoted claim artifact containers, detects source-local concept refs, rewrites claim concept fields through a concept map while collecting unresolved refs, normalizes imported standalone claim artifacts, and normalizes source-branch claim artifacts for canonical promotion with source/provenance/context adjustments. Boundary: it owns concept-reference lowering for claims; claim family document schemas and canonical identity normalization live in family modules. Cleanup relevance: source-local concept handles are explicitly lowered before canonical claim writes.

### `propstore/source/claims.py`

Owner/subsystem: source-branch claim authoring, validation, and normalization.

This file derives stable source claim logical ids and artifact/version ids, gathers and validates source-local concept references, validates CEL conditions against master plus source-proposed concepts, checks numeric claim values against form bounds, normalizes source claim batches, and commits batch or single claim proposals to the source claims family with live-branch retry. It also stamps extraction provenance and default contexts when requested. Boundary: it owns source-side claim persistence and preflight validation; canonical promotion rewriting and claim family identity primitives live elsewhere. Cleanup relevance: source-local claim ids are converted into deterministic source-namespace logical ids before storage.

### `propstore/source/common.py`

Owner/subsystem: shared source-branch naming, initialization, commit, and load helpers.

This file normalizes source slugs and paper slugs, stamps UTC time, mints source tag URIs, constructs initial source documents with origin/trust/metadata, initializes source branches, commits source notes/metadata, and loads all source-branch document families through repository family APIs. Boundary: it supplies common source infrastructure; claim/concept/relation/finalize behavior lives in sibling modules. Cleanup relevance: source branch stems and master paper artifact stems are kept consistent through a single helper.

### `propstore/source/concepts.py`

Owner/subsystem: source-branch concept proposal normalization and commit.

This file validates proposed concept form names against the form family, normalizes source concept entries by requiring local/proposed names, definitions, and forms, links entries to primary-branch concept matches when present, commits concept batches, and updates single concept proposals with live-branch retry. Boundary: it owns source concept proposal documents; primary-branch matching and form definitions are delegated. Cleanup relevance: source concept proposals are either explicitly linked to canonical concepts or marked proposed before later promotion.

### `propstore/source/finalize.py`

Owner/subsystem: source-branch readiness validation, artifact-code stamping, and finalize report generation.

This file validates source claim artifact ids, micropub context coverage, justification references, and stance references against source and primary claim indexes; composes source micropublications from finalized claims; previews concept-alignment and parameterization-group merge candidates; stamps source artifact codes in a head-bound family transaction; and writes a source finalize report with readiness, artifact-code, micropub, and calibration status. Boundary: it finalizes source-branch artifacts before promotion; actual canonical promotion lives in `promote.py`. Cleanup relevance: source branches must produce explicit readiness reports and micropub coverage before becoming promotable.

### `propstore/source/promote.py`

Owner/subsystem: source-branch partial promotion to canonical families.

This file resolves source concept promotions, maps or creates canonical concept documents, filters blocked claims by artifact/reference/concept-mapping diagnostics, validates the would-be canonical claim view before commit, assembles a `SourcePromotionPlan`, commits promoted source/claim/micropub/concept/justification/stance documents in a head-bound primary-branch transaction, writes provenance notes for the promotion commit, and recalibrates source trust after promotion. It also exposes blocked promotion facts for derived-store diagnostics. Boundary: it promotes finalized source artifacts; source authoring/finalize validation and canonical family identity helpers live elsewhere. Cleanup relevance: source-local handles are lowered explicitly and invalid items are quarantined as blocked promotion facts instead of promoted into canonical state.

### `propstore/source/reference_indexes.py`

Owner/subsystem: source and primary claim reference indexes.

This file declares source-claim reference keys (`source_local_id`, formatted logical ids, and namespace/value pairs), builds a `FamilyReferenceIndex` from source claim documents, loads the source-claim index for a source branch, and exposes the primary canonical claim reference index. Boundary: it only builds lookup indexes; reference resolution policy is used by finalize/promote callers. Cleanup relevance: claim references resolve through family reference APIs instead of bespoke string matching.

### `propstore/source/registry.py`

Owner/subsystem: primary/source concept lookup and projected parameterization previews.

This file loads primary-branch concept records/docs, matches handles through the concept reference index, projects source concept entries into canonical-like concept payloads with derived artifact ids, resolves source-local parameterization inputs against source and primary indexes, and previews parameterization group merges by comparing current and projected concept groups. Boundary: it provides source promotion/finalize registry views; actual concept commits and parameterization group logic are delegated. Cleanup relevance: source-local concept references are resolved through reference indexes before promotion planning.

### `propstore/source/relations.py`

Owner/subsystem: source-branch justification and stance authoring/normalization.

This file validates justification rule kinds/strengths, normalizes source justifications and stances by resolving source or primary claim references, stamps extraction provenance for batch imports, commits justification/stance batches, and appends single justification or stance proposals with live-branch retry. Boundary: it owns source-side relation documents; reference indexes and canonical promotion are separate. Cleanup relevance: source relation references are resolved to artifact ids before storage where possible.

### `propstore/source/stages.py`

Owner/subsystem: source promotion stage data container.

This file defines `SourcePromotionPlan`, carrying the source identity, source branch, canonical source ref, promoted source/claim/micropub/concept/justification/stance document maps, and blocked claim diagnostics. Boundary: it is a planning data object consumed by promotion code; promotion assembly and commit mechanics live in `promote.py`. Cleanup relevance: promotion state is explicit and typed before canonical writes.

### `propstore/source/status.py`

Owner/subsystem: typed source-branch promotion status reporting.

This file defines status states, diagnostic/row/report dataclasses, SQL LIKE escaping, and `inspect_source_status`, which reads derived-store claim promotion rows plus build diagnostics for a source branch and returns a typed report. Boundary: it owns source status correlation from sidecar tables; CLI rendering and sidecar table declarations live elsewhere. Cleanup relevance: promotion blocking diagnostics are reported through typed source status rows rather than CLI-owned SQL.

### `propstore/source_trust_argumentation/__init__.py`

Owner/subsystem: argumentation-backed source trust calibration.

This file loads source-trust rules from repository or packaged rule YAML, converts rule documents into support/attack rules, matches rules against source metadata, builds a Dung framework where attacks defeat support rules, evaluates the grounded extension, converts active firings into subjective-logic opinions, and returns `SourceTrustResult` with kernel/version/provenance status. Boundary: it calibrates source trust from metadata/rules; source document mutation is handled by promotion code. Cleanup relevance: default/vacuous/calibrated trust states are explicit and provenance-status-bearing.

### `propstore/stances.py`

Owner/subsystem: shared stance type vocabulary.

This file defines the `StanceType` enum, the frozen set of valid stance strings, `UnknownStanceType`, and `coerce_stance_type`. Boundary: it supplies vocabulary and coercion only; stance documents, relation semantics, and promotion logic live elsewhere. Cleanup relevance: stance typing is centralized instead of scattered string validation.

### `propstore/storage/__init__.py`

Owner/subsystem: propstore storage package export.

This file declares the storage package docstring and re-exports `PROPSTORE_GIT_POLICY` through `__all__`. Boundary: it is an API surface only; git policy details live in `git_policy.py`. Cleanup relevance: storage package imports expose the policy without importing unrelated storage code.

### `propstore/storage/git_policy.py`

Owner/subsystem: propstore GitStore policy declaration.

This file defines the default git author, primary branch name, initial `.gitignore` content, and `PROPSTORE_GIT_POLICY` with ignored sidecar/cache path prefixes and suffixes. Boundary: it configures Quire `GitStore`; repository behavior and family storage live elsewhere. Cleanup relevance: repository initialization and ignored diagnostic/storage artifacts are governed by one policy object.

### `propstore/storage/snapshot.py`

Owner/subsystem: repository snapshot reads and materialization.

This file defines branch/materialization report types, classifies branch names, exposes `RepositorySnapshot` for branch iteration, tree access, typed document reads from branch/commit, and materializing git-backed semantic artifacts to disk with conflict wrapping and ignored clean-path reporting. Boundary: it adapts Quire git materialization for propstore roots and policies; repository and family logic live elsewhere. Cleanup relevance: materialization has typed reports and explicit ignored diagnostic paths instead of opaque git-store side effects.

### `propstore/structured_projection.py`

Owner/subsystem: structured argumentation projection records and lifting helpers.

This file defines projection loss/atom/lifted result/structured argument/projection dataclasses, lifts projected structured arguments and analyzer claim projections back to situated assertion ids, derives claim assertion id maps from active world graphs, and computes justified structured arguments via Dung semantics after backend/semantics validation. Boundary: ASPIC construction happens elsewhere; this module owns propstore-facing projection records and result lifting. Cleanup relevance: backend projection loss and missing source assertions fail explicitly instead of silently dropping provenance.

### `propstore/support_revision/__init__.py`

Owner/subsystem: support-revision package API surface.

This file documents that support revision is scoped worldline capture rather than formal AGM/AF revision, then re-exports argumentation adapters, entrenchment, explanation, iterated revision, input normalization, projection, realization, and state types through `__all__`. Boundary: it is an API aggregator; behavior lives in sibling modules and external revision packages. Cleanup relevance: package exports distinguish propstore support-incision helpers from formal revision kernels.

### `propstore/support_revision/af_adapter.py`

Owner/subsystem: support-revision projection into argumentation store/view surfaces.

This file defines `RevisionArgumentationView`, a read-only `RevisionArgumentationStore` overlay limited to active revision claims, stance/conflict filtering against the active set, and `project_epistemic_state_argumentation_view`, which maps accepted assertion atoms to active claims and support metadata while tracking unmapped and accepted assumption atoms. Boundary: it adapts epistemic state to argumentation inputs; revision state changes and formal argumentation analysis live elsewhere. Cleanup relevance: revision-specific active claims are exposed through a scoped overlay rather than mutating the backing world store.

### `propstore/support_revision/belief_set_adapter.py`

Owner/subsystem: adapter from propstore belief atoms to the external `belief_set` formal revision kernel.

This file projects `BeliefBase` atoms into formal belief sets and Spohn states with alphabet budget checks, implements expand/contract/revise/iterated revise/IC merge decision helpers, constructs revision formulas with explicit conflict negations, reports accepted/rejected atom ids and selected merge worlds, and records deterministic hashes/traces for formal decisions. Boundary: formal AGM/iterated/IC algorithms live in the `belief_set` package; this module maps propstore atoms and reports into that kernel. Cleanup relevance: formal revision decisions are traceable typed reports instead of hidden support-incision heuristics.

### `propstore/support_revision/dispatch.py`

Owner/subsystem: replay dispatcher for support-revision journal operators.

This file maps normalized journal inputs and policy snapshots into support-revision operations for expand, revise, contract, iterated revise, and IC merge. It reconstructs epistemic state snapshots, builds formal decisions through the belief-set adapter, realizes decisions, advances epistemic state with replay status, and wraps realization or merge-required failures with revision events. Boundary: it dispatches one replayed operator; journal capture, formal kernels, realization, and state snapshots are delegated. Cleanup relevance: replay requires explicit policy versions and normalized operator inputs instead of ambient mutable state.

### `propstore/support_revision/entrenchment.py`

Owner/subsystem: support-revision entrenchment ranking and reasons.

This file defines `EntrenchmentReport` and `compute_entrenchment`, projecting the belief base into the formal belief-set bundle, combining formal entrenchment order with support counts, essential support, and override priorities keyed by atom/source/context/kind, then producing ranked atom ids and explanation reasons. Boundary: it computes ranking metadata; formal projection and revision realization are separate. Cleanup relevance: entrenchment has explicit override/reason provenance rather than unexplained deletion order.

### `propstore/support_revision/explain.py`

Owner/subsystem: support-revision explanation assembly.

This file defines `build_revision_explanation`, collecting accepted/rejected atom ids and per-atom explanation details from a `RevisionResult`, optionally attaching entrenchment reasons, incision sets, and support sets into a stable `RevisionExplanation`. Boundary: it formats explanation data only; revision decisions and entrenchment computation live elsewhere. Cleanup relevance: accepted/rejected explanations are explicit typed payloads rather than ad hoc text.

### `propstore/support_revision/explanation_types.py`

Owner/subsystem: typed support-revision explanation payloads.

This file defines revision atom detail, entrenchment reason, atom explanation, and full explanation dataclasses, plus mapping coercion and dictionary serialization helpers. It normalizes assumption ids, incision sets, support sets, override priorities, rankings, and accepted/rejected atom lists. Boundary: it owns explanation data shapes; explanation assembly and entrenchment computation are separate. Cleanup relevance: revision explanations are round-trippable structured objects instead of loosely shaped mappings.

### `propstore/support_revision/history.py`

Owner/subsystem: epistemic snapshots, transition journals, replay integrity, and semantic diffs.

This file defines journal operators, canonical hashing/serialization helpers, `EpistemicSnapshot`, transition operations and journal entries with policy snapshots and normalized in/out states, journal chain integrity and replay reports, replay divergence records, semantic snapshot diffs, and diff application across assertion acceptance, warrant, ranking, provenance, and dependency surfaces. Boundary: it records and verifies revision history; dispatch executes individual operators and snapshot types convert state payloads. Cleanup relevance: worldline support-revision history is durable, hash-checked, replayable, and policy-versioned.

### `propstore/support_revision/input_normalization.py`

Owner/subsystem: user-facing revision input normalization.

This file defines `normalize_revision_input`, accepting existing belief atoms, string ids, or mapping payloads and resolving them to assertion or assumption atoms against a belief base, plus helpers for matching assertion/assumption candidates. Boundary: it only normalizes caller inputs; revision decisions and realization live elsewhere. Cleanup relevance: unknown revision targets fail at the input boundary instead of becoming synthetic assertions.

### `propstore/support_revision/iterated.py`

Owner/subsystem: epistemic state construction and iterated revision advancement.

This file creates initial epistemic states from stabilized belief bases and entrenchment reports, advances state with revision episodes/events, runs selected iterated revision operators through the belief-set adapter and realization layer, rejects multi-parent merge scopes, wraps realization failures with replayable events, recomputes entrenchment after realization, and exposes snapshot payload serialization. Boundary: it coordinates state transitions; formal decision logic, realization, and history hashing live in sibling modules. Cleanup relevance: revision state evolution is explicit, event-backed, and replay-status-aware.

### `propstore/support_revision/projection.py`

Owner/subsystem: projection from bound worlds to revision belief bases and situated assertions.

This file converts active claims with exact ATMS support into situated assertion atoms, derives support/essential-support sets, includes supporting assumptions, captures revision scope from bound environment/git state, builds stable relation/role/context/condition/provenance references, and projects epistemic snapshots back to accepted claim ids. Boundary: it builds revision-facing belief bases from bound world surfaces; revision decisions and realization are separate. Cleanup relevance: only exact reconstructible support enters support revision, with provenance and condition ids content-hashed.

### `propstore/support_revision/realization.py`

Owner/subsystem: realization of formal revision decisions back into support belief bases.

This file realizes formal accepted/rejected atom sets by rebuilding belief bases, computing minimal support incision cuts with entrenchment-aware scoring and enumeration limits, forcing unsupported rejections, stabilizing acceptance until support closure is reached, realizing IC merge selected worlds, and producing `RevisionResult` plus `SupportRevisionRealization` metadata. Boundary: formal decisions come from the belief-set adapter; this module applies them to propstore support structures. Cleanup relevance: formal revision output is reconciled with support dependencies instead of blindly accepting formal atom sets.

### `propstore/support_revision/scope_policy.py`

Owner/subsystem: declarative scope completeness policy decorator.

This file defines `scope_policy`, a decorator that extracts snapshot scope from arguments or journal step outputs, enforces required scope fields for selected kwargs, and degrades selected kwargs with warnings when fallback behavior remains meaningful. Boundary: it is a method-decorator utility for snapshot consumers; scope data and journal structures live elsewhere. Cleanup relevance: incomplete historical/synthetic snapshot scopes are handled by explicit require/degrade policy instead of silent partial behavior.

### `propstore/support_revision/snapshot_types.py`

Owner/subsystem: canonical serialization/deserialization for support-revision snapshots.

This file converts labels, assumptions, revision scopes, assertion/assumption belief atoms, belief bases, revision episodes, and epistemic states to and from canonical mapping payloads. It validates required mapping fields, reconstructs situated assertions and active claims, preserves revision events, ranking, entrenchment reasons, support sets, and essential support, and exposes belief-atom canonical dict helpers. Boundary: it owns snapshot payload shapes; history hashing/replay and live revision state operations are separate. Cleanup relevance: persisted epistemic state has a strict round-trippable schema instead of pickled runtime objects.

### `propstore/support_revision/state.py`

Owner/subsystem: core support-revision runtime state types.

This file defines assertion and assumption belief atoms, revision scopes, belief bases, formal decision reports, support realization records, revision results, revision events with canonical content hashes, realization and merge-required failures, revision episodes, and epistemic states. It normalizes ids, assumption refs, ranking/reason maps, and serialization helpers. Boundary: these are the runtime data contracts; projection, formal decisions, realization, snapshots, and journal history use them. Cleanup relevance: support-revision state is explicit, hashable, and typed across decision, realization, and history layers.

### `propstore/support_revision/workflows.py`

Owner/subsystem: world-bound support-revision workflow façade.

This file defines `RevisionWorldRequest`, `IteratedRevisionReport`, a helper to bind worlds with environment/context, and workflow functions for revision base, entrenchment, expand, contract, revise, explanation, epistemic state, and iterated revise operations. Boundary: it delegates to `BoundWorld` revision methods; it does not implement formal revision mechanics itself. Cleanup relevance: reusable owner-layer workflow functions keep support revision behavior out of CLI adapters.

### `propstore/unit_dimensions.py`

Owner/subsystem: unit symbol to physical dimension lookup.

This file lazily loads shipped `physgen_units.json`, supports clearing and registering form-declared extra units, forwards extra units to Pint registration, resolves unit strings to canonical dimensions, and checks dimensional compatibility with Bridgman. Boundary: it owns unit dimension lookup; form loading and claim validation call into it. Cleanup relevance: unit compatibility uses a shared dimension table rather than per-validator string checks.

### `propstore/uri.py`

Owner/subsystem: propstore tag URI and NI URI helpers.

This file defines default tagging authority, token normalization, tag URI constructors for sources/concepts/claims, SHA-256 RFC 6920 `ni` URI computation and verification, and byte/file helpers. Boundary: it owns URI construction and byte hashing; authority parsing lives in `uri_authority.py`. Cleanup relevance: entity and byte identifiers are minted through shared standards-based helpers.

### `propstore/uri_authority.py`

Owner/subsystem: RFC 4151 tag authority validation.

This file defines the tagging-authority regex, `MalformedTaggingAuthority`, immutable `TaggingAuthority`, and `parse_tagging_authority` with length and syntax validation. Boundary: it validates authority components; concrete entity tag URI construction lives in `uri.py`. Cleanup relevance: tag authority strings are validated once instead of being accepted as arbitrary text.

### `propstore/value_comparison.py`

Owner/subsystem: pure claim value and interval comparison logic.

This file extracts numeric intervals from claim-like objects, checks interval compatibility with tolerance, optionally normalizes intervals to SI using form/unit metadata, compares scalar/list/other values, formats values for display, and reads fields from mappings or objects. Boundary: it owns numeric compatibility primitives; claim loading, form definitions, and unit normalization are external. Cleanup relevance: value compatibility is centralized and unit-aware instead of repeated in validators.

### `propstore/web/__init__.py`

Owner/subsystem: web presentation adapter package marker.

This file contains the package docstring and an empty `__all__`. Boundary: web app behavior lives in sibling modules. Cleanup relevance: the web package does not re-export deeper presentation code.

### `propstore/web/app.py`

Owner/subsystem: FastAPI web application construction.

This file defines `create_app`, creating the FastAPI app, storing an optional repository root on app state, mounting the package `static` directory, and registering routes lazily. Boundary: it builds the web adapter shell; route behavior lives in `routing.py`. Cleanup relevance: app construction remains a presentation adapter with repository location passed as state.

### `propstore/web/html.py`

Owner/subsystem: Jinja-backed HTML presenters for web reports.

This file creates the template environment, defines table/link row helpers, renders repository overview, claim index/detail, concept index/detail, neighborhood, and error pages, and supplies shared HTML fragments for filters, render policy, machine ids, source/provenance/conflict/activity sections, tables, links, status text, and escaped markup. Boundary: it presents already-built app reports; report construction and route handling live elsewhere. Cleanup relevance: HTML rendering is centralized in presentation helpers rather than embedded in routes or domain objects.

### `propstore/web/requests.py`

Owner/subsystem: HTTP query parsing for web app requests.

This file defines `WebQueryParseError`, parses render policy query parameters into `AppRenderPolicyRequest`, parses branch/revision parameters into `AppRepositoryViewRequest`, and validates optional text, booleans, finite bounded floats, and integers. Boundary: it adapts HTTP strings to app-layer request objects; route functions and app rendering are separate. Cleanup relevance: web query validation is centralized instead of duplicated across handlers.

### `propstore/web/routing.py`

Owner/subsystem: FastAPI route registration and web error mapping.

This file registers health, repository overview, claims, concepts, claim/concept detail, semantic neighborhood, and world revision JSON/HTML routes; parses query parameters into app requests; finds the repository from app state; dispatches to app-layer report builders; serializes JSON responses; renders HTML responses; and maps expected app/web errors to status-coded JSON or HTML error responses. Boundary: it is a web presentation adapter; app report builders own domain behavior. Cleanup relevance: route handlers stay thin and expected failures are mapped through one table.

### `propstore/web/serialization.py`

Owner/subsystem: strict JSON serialization for web responses.

This file defines `WebSerializationError` and `to_json_compatible`, converting primitives, enums, paths, sequences, string-key dictionaries, and dataclasses into `JsonValue`, while rejecting unsupported values and non-string object keys. Boundary: it serializes app reports for JSON responses; report construction and HTML rendering are elsewhere. Cleanup relevance: web JSON output fails fast on unsupported shapes instead of stringifying arbitrary objects.

### `propstore/world/__init__.py`

Owner/subsystem: public world query/render interface exports.

This file re-exports bound/query world classes, intervention/observation/overlay worlds, SCM types, resolution/actual-cause helpers, and the world type vocabulary through `__all__`. Boundary: it is an API aggregation surface; behavior lives in sibling modules. Cleanup relevance: world package imports are explicit instead of broad transitive exposure.

### `propstore/world/actual_cause.py`

Owner/subsystem: modified Halpern-Pearl actual-cause evaluation.

This file defines actual-cause criteria, witness/verdict dataclasses, enumeration budget failure, and `actual_cause`, checking AC1, searching AC2 witnesses over interventions/contingencies, and enforcing AC3 minimality over smaller causes. Boundary: it evaluates finite recursive SCMs exposed by intervention worlds; SCM evaluation/intervention primitives live elsewhere. Cleanup relevance: actual-cause answers include explicit failed criterion, witness, actual values, and smaller-cause counterexamples.

### `propstore/world/assignment_selection_merge.py`

Owner/subsystem: assignment-level integrity-constrained merge solving.

This file defines distance metrics, candidate assignment enumeration with anytime budget support, integrity constraint compilation for range/category/CEL/custom constraints, CEL binding through scoped registries and condition solvers, assignment admissibility, merge scoring for sigma/max/gmax operators, deterministic tie-breaking, and `solve_assignment_selection_merge`. Boundary: it solves observed concept-value merge problems; world resolution prepares problems and consumes results. Cleanup relevance: merge selection is an explicit solver over typed assignments and constraints rather than scattered arbitration logic.

### `propstore/world/atms.py`

Owner/subsystem: ATMS exact-support propagation, inspection, future replay, stability, relevance, and intervention planning.

This file defines ATMS node/justification/runtime/future replay types, builds an `ATMSEngine` from bound worlds or runtime adapters, activates compiled world graphs, creates assumption/context/claim/micropub/derived nodes, propagates exact labels through justifications, materializes compatible parameterization-derived nodes, derives nogoods from conflicts and incompatible derived values with provenance, verifies label soundness/minimality/completeness, explains nodes and nogoods, reports argumentation state, and performs bounded future replay over queryable assumptions for why-out, could-in/out, stability, relevance, minimal additive intervention plans, and next-query suggestions. Boundary: it owns exact ATMS support reasoning; world binding, sidecar graph construction, condition solving, and formal AGM-style revision live elsewhere. Cleanup relevance: support status is explicit about exact labels, semantic-only activation, nogood pruning, parameterization type rejection, and bounded future uncertainty.

### `propstore/world/bound.py`

Owner/subsystem: condition/context-bound world query view.

This file defines `BoundWorld`, conflict recomputation helpers, and revision target normalization. A bound world filters active/inactive claims by environment, context, preactivated graph, and lifting/condition solver state; resolves values, derived values, resolved values, conflicts, explanations, labels, and ATMS-backed support metadata; exposes ATMS future/status/stability/relevance/intervention APIs; and delegates support-revision expand/contract/revise/iterated state workflows to the support revision package. Boundary: it is the world-facing query adapter over a `WorldStore`; stores, resolution algorithms, ATMS engine internals, and formal revision kernels remain separate. Cleanup relevance: rendering and revision use a scoped typed world view instead of raw sidecar rows and ambient bindings.

### `propstore/world/bridge.py`

Owner/subsystem: projection bridge from transition journals to claim views.

This file defines the `BeliefSpaceQuery` protocol and `at_journal_step`, which reads a transition journal entry's `state_out`, projects accepted assertion atoms to source claim ids, fetches claims from a belief space, optionally rebinds to snapshot scope under scope-policy rules, and optionally dispatches heavy replay. Boundary: it bridges persisted epistemic snapshots to world claim views; journal replay and support-revision dispatch live elsewhere. Cleanup relevance: journal-step views are derived from recorded snapshots with explicit scope policy, not reconstructed by guesswork.

### `propstore/world/consistency.py`

Owner/subsystem: world consistency report APIs.

This file defines consistency request/report dataclasses and `check_world_consistency`, either binding a world and reporting active conflicts or running transitive conflict detection from canonical claim files and concept parameterization relationships. Boundary: it builds typed reports around conflict detector outputs; conflict detection internals and world binding are separate. Cleanup relevance: consistency checks are owner-layer report functions rather than CLI-owned scans.

### `propstore/world/intervention.py`

Owner/subsystem: Pearl-style intervention and deterministic observation worlds.

This file defines intervention/observation trace prefixes, compiled-graph world protocol, intervention/observation errors and result/diff dataclasses, `InterventionWorld` for SCM do-surgery, and `ObservationWorld` for validating observations against deterministic SCM values. Boundary: it adapts compiled SCMs for causal interventions/observations; SCM construction/evaluation lives in `scm.py`. Cleanup relevance: interventions alter equations through SCM surgery, while observations preserve equations and fail on disagreement.

### `propstore/world/journal_replay.py`

Owner/subsystem: heavy journal-step replay for claim views.

This file defines fixture registration, cache state/statistics, replay protocols, and `replay_at_step`, which projects accepted claim ids from a journal snapshot, requires snapshot commit scope, caches by commit and claim set, optionally uses registered fixture commits or repository historical query surfaces, and re-derives stances/conflicts visible within the accepted claim set. Boundary: it is the heavy path behind `at_journal_step`; snapshot projection and scope policy live elsewhere. Cleanup relevance: heavy replay is commit-keyed and explicit instead of silently using current working state.

### `propstore/world/model.py`

Owner/subsystem: `WorldQuery` read-only sidecar-backed world model.

This file opens and validates derived world sidecars, manages SQLite read-only access, condition solver/lifting/compiled graph caches, repository-backed historical queries, claim/concept resolution indexes, concept/claim/stance/conflict/relationship/micropublication/form/parameterization queries, render-policy visibility predicates, diagnostics, similarity search, graph activation, binding to `BoundWorld`, intervention/observation construction, journal-step bridging, and chain queries across parameterization groups. Boundary: it is the primary read/query facade over materialized sidecars; mutation, build, app presentation, bound-world reasoning, and SCM internals are separate. Cleanup relevance: world reads go through typed family query APIs and cached indexes instead of direct ad hoc SQL in callers.

### `propstore/world/overlay.py`

Owner/subsystem: graph-delta overlay worlds over bound worlds.

This file builds synthetic claim rows and compiled graph deltas, creates `_GraphOverlayStore` adapters over a base world store, recomputes overlay stances/conflicts, activates overlay compiled graphs, and exposes `OverlayWorld` methods for active claims, values, derived/resolved values, conflicts, explanations, claim lookup, and diffs. Boundary: overlays add/remove claims while preserving parameterization graph semantics; Pearl interventions live in `intervention.py`. Cleanup relevance: hypothetical claim overlays are explicit graph/store adapters rather than mutating the base world.

### `propstore/world/queries.py`

Owner/subsystem: typed owner-layer world query request/report APIs.

This file defines expected world query errors and report/request dataclasses for status, concept queries, binding, explanations, algorithms, derivation, hypotheticals, resolution, and chain queries. It resolves display ids, formats values with SI units, handles ambiguous/unknown concepts, builds visible claim/diagnostic reports, binds worlds, explains stance chains, lists algorithms, derives values, diffs hypothetical overlays including grounded-extension transitions, resolves values through policy, and renders chain-query reports. Boundary: it is an app/CLI reusable world query layer; `WorldQuery`, `BoundWorld`, overlay, and resolver internals do the underlying reasoning. Cleanup relevance: presentation-facing world operations are typed owner APIs rather than direct CLI/web access to world internals.

### `propstore/world/resolution.py`

Owner/subsystem: conflicted-concept resolution strategies.

This file defines resolution helpers and the main `resolve` entry point for applying override, recency, sample-size, assignment-selection merge, claim-graph argumentation, ASPIC, PrAF, and ATMS strategies to a conflicted bound-world concept. It normalizes active claims into internal views, extracts provenance/sample/opinion metadata, builds integrity constraints from concept ranges/categories and render policies, constructs global assignment-selection problems, delegates to graph/ASPIC/PrAF analyzers, handles backend semantics validation, and returns typed `ResolvedResult` values with winning claim ids, reasons, and optional acceptance probabilities. Boundary: it orchestrates strategy selection and result shaping; analyzers, ASPIC projection, ATMS engines, assignment-selection solving, and bound-world value computation live in their own modules. Cleanup relevance: conflict resolution is centralized behind typed policy/back-end abstractions instead of presentation code choosing winners directly.

### `propstore/world/scm.py`

Owner/subsystem: deterministic structural causal model primitives.

This file defines `StructuralEquation` and `StructuralCausalModel`, including constant equations, SCM construction from compiled parameterization graphs, intervention surgery, recursive deterministic evaluation with cycle/missing-equation failures, descendant traversal, and finite domain lookup. It turns parameterization edges with SymPy expressions into structural equations that call the propagation evaluator. Boundary: this is the low-level SCM model used by interventions and actual-cause queries; UI/reporting and world binding live elsewhere. Cleanup relevance: causal semantics are modeled explicitly from compiled graph edges rather than inferred through ad hoc value propagation in callers.

### `propstore/world/types.py`

Owner/subsystem: shared world-layer data contracts, enums, and protocols.

This file defines value/derived/resolved result models, ATMS inspection/future/stability/relevance/intervention/explanation reports, resolution and merge enums, integrity constraints, assignment-selection merge problem/result types, synthetic claim and journal claim-view structures, chain results, render policy serialization, decision-criterion evaluation, and runtime protocols for claim-support views, ATMS engines, active graphs, grounding bundle stores, and belief spaces. It also normalizes statuses, queryable CEL assumptions, merge operators, concept ids, claim types, exactness, and render-policy dictionaries. Boundary: it is a contract module for world, resolution, ATMS, render, and query layers; algorithms and storage access live in implementation modules. Cleanup relevance: world behavior is carried through typed dataclasses/protocols instead of loose dicts or CLI-shaped payloads.

### `propstore/world/value_resolver.py`

Owner/subsystem: shared active-claim and parameterization value resolution.

This file defines `collect_known_values` and `ActiveClaimResolver`, which determine concept values from active direct/algorithm claims, compare algorithms with `ast_equiv`, classify parse-failed algorithms separately from benign inconclusive cases, derive parameterized values recursively, apply override inputs, rewrite parameterization symbols through safe aliases, and normalize numeric values. Boundary: it is reusable belief-space resolution logic used by bound/overlay worlds; storage, graph activation, rendering, and conflict-strategy resolution live elsewhere. Cleanup relevance: value and derivation semantics are centralized in typed resolver code rather than duplicated across world views.

### `propstore/worldline/__init__.py`

Owner/subsystem: worldline package public exports.

This file re-exports the worldline definition dataclasses, content-hash helper, and `run_worldline` materialization entry point. Boundary: it is package-surface wiring only; query definitions, hashing, and execution live in sibling modules. Cleanup relevance: the worldline public API is shallow and does not own behavior.

### `propstore/worldline/_constants.py`

Owner/subsystem: shared worldline constants.

This file defines `OVERRIDE_CLAIM_PREFIX`, the synthetic claim id prefix used for worldline overrides. Boundary: constant-only support module. Cleanup relevance: override identity has a single shared spelling instead of ad hoc literals.

### `propstore/worldline/argumentation.py`

Owner/subsystem: worldline argumentation state capture and stance dependencies.

This file defines `capture_argumentation_state` plus backend-specific capture helpers for claim-graph, ASPIC, ATMS, and PrAF worldline snapshots. It gathers active claim ids, normalizes semantics, uses active compiled graphs when available, records justified/defeated claims or probabilistic acceptance metadata, and computes canonical RFC8785 stance dependency keys from either active graph relations or world stance rows. Boundary: it captures argumentation state for worldline materialization; analyzers, ASPIC projection, PrAF construction, ATMS engines, and result dataclasses live elsewhere. Cleanup relevance: worldline reproducibility includes explicit argumentation and stance dependencies rather than implicit current-world state.

### `propstore/worldline/definition.py`

Owner/subsystem: worldline definition, input, revision query, and result document models.

This file defines `WorldlineInputs`, `WorldlineRevisionQuery`, `WorldlineResult`, and `WorldlineDefinition` with conversions from/to document schemas and plain dictionaries. It validates revision targets, profile atom ids, required targets/id fields, converts render policies and transition journals, coerces nested result/sensitivity/argumentation/revision structures, emits document values through Quire conversion, and checks staleness by rerunning a worldline and comparing content hashes. Boundary: it owns the persisted worldline document contract; execution, hashing, argumentation capture, and revision state internals live elsewhere. Cleanup relevance: worldlines use typed document conversion and validation rather than loose YAML/JSON payloads through runtime code.

### `propstore/worldline/hashing.py`

Owner/subsystem: deterministic worldline content hashing.

This file defines `compute_worldline_content_hash`, which canonicalizes policy, values, steps, dependencies, sensitivity, argumentation, and revision state through RFC8785 JSON and returns a SHA-256 digest. Boundary: hash computation only; result construction and persistence live elsewhere. Cleanup relevance: worldline staleness/content identity is deterministic over typed result payloads.

### `propstore/worldline/interfaces.py`

Owner/subsystem: worldline runtime protocols.

This file defines protocol surfaces for worldline-bound belief spaces, optional binding/environment/lifting/active-graph attributes, and `WorldlineStore.bind`. Boundary: it is type-only interface plumbing between worldline runner/capture code and world stores. Cleanup relevance: worldline execution depends on explicit protocols rather than concrete world implementation imports.

### `propstore/worldline/resolution.py`

Owner/subsystem: worldline target/input resolution and trace recording.

This file defines `ResolutionContext`, concept/claim display helpers, pre-resolution of reachable conflicts, target resolution, and recursive input-source tracing for worldline materialization. It resolves overrides, pre-resolved conflicts, determined claims, conflict strategies, derived values, and chain queries; records claim dependencies and step traces; lowers claim rows into `WorldlineTargetValue`; and builds nested `WorldlineInputSource` trees for derivations. Boundary: it adapts bound-world value/derivation/conflict results into worldline outputs; core world resolution, parameterization walking, chain queries, and trace dataclasses live elsewhere. Cleanup relevance: worldline value provenance is explicit through trace/dependency records rather than hidden in rendered final values.

### `propstore/worldline/result_types.py`

Owner/subsystem: worldline materialized-result value objects.

This file defines worldline capture error tags, variable references, input-source trees, target values, step records, dependency records, sensitivity entries/outcomes/reports, and rich argumentation-state payloads including claim-graph/PrAF/ATMS fields. It validates mapping/list shapes, coerces numeric optional fields and capture errors, serializes nested dataclasses/enums to JSON-native structures, and provides `from_mapping`/`to_dict`/coercion helpers for each result family. Boundary: it owns result payload structures only; runner, resolution, hashing, and argumentation capture fill these structures. Cleanup relevance: worldline outputs have explicit typed nested provenance and diagnostics instead of unvalidated dict blobs.

### `propstore/worldline/revision_capture.py`

Owner/subsystem: worldline support-revision state and journal capture.

This file defines capture of single revision operations and transition journals for expand, contract, revise, iterated revise, and IC merge. It invokes bound revision methods or dispatches journal operators from an epistemic state, normalizes revision atoms, builds operator inputs, records accepted/rejected/incision/explanation result payloads, captures revision events with policy snapshots and pre-state hashes, validates assertion/assumption atom targets, and supports iterated state snapshots. Boundary: it adapts support-revision owner APIs into worldline revision artifacts; revision algorithms, dispatch, state models, and journal dataclasses live in support-revision modules. Cleanup relevance: worldline revision provenance is captured as durable journal/event state instead of process-local decisions.

### `propstore/worldline/revision_types.py`

Owner/subsystem: worldline revision payload dataclasses.

This file defines `RevisionAtomRef`, `RevisionConflictSelection`, `WorldlineRevisionResult`, and `WorldlineRevisionState`, including mapping coercion, revision input conversion, resolved atom id derivation, conflict target maps, accepted/rejected/incision payloads, optional state/event/error fields, and recursive plain-data serialization. Boundary: it owns persisted worldline revision result shapes; capture and support-revision execution live elsewhere. Cleanup relevance: revision artifacts are typed and validate mapping boundaries instead of passing arbitrary dicts through worldline documents.

### `propstore/worldline/runner.py`

Owner/subsystem: worldline materialization engine.

This file defines `run_worldline`, which binds a world with inputs/policy, resolves override and target concept names, records binding/override traces, pre-resolves conflicts when a strategy is configured, materializes target values, captures sensitivity, optional argumentation state, optional revision state, lifting/context/stance/claim dependencies, computes a policy-aware content hash, and returns a `WorldlineResult`. It also contains helpers for sensitivity capture, context dependency extraction, and lifting-rule/blocked-exception dependency discovery. Boundary: it orchestrates worldline execution; target resolution, argumentation capture, revision capture, hashing, and trace objects are delegated. Cleanup relevance: worldline materialization has a single owner-layer execution path with explicit dependencies and capture errors.

### `propstore/worldline/trace.py`

Owner/subsystem: worldline resolution provenance accumulator.

This file defines `ResolutionTrace`, which records worldline steps for bindings, overrides, claim/derived/resolved/error sources, tracks claim dependencies while excluding synthetic override claims, bulk-records active claim dependencies, and reports seen concepts. Boundary: it is an in-memory trace helper used by worldline resolution/runner. Cleanup relevance: provenance and dependency collection are explicit trace operations rather than scattered side effects.

### `../quire/quire/__init__.py`

Owner/subsystem: Quire package public API surface.

This file imports and re-exports Quire document, artifact placement, contract manifest, derived-store, SQLite runtime, family-store, Git-store, notes, projections, projection-mapping, references, tree-path, version, family-registry, hashing, and sqlite-vec symbols through `__all__`. Boundary: package-surface wiring only; behavior is owned by the referenced modules. Cleanup relevance: Propstore consumers can depend on explicit Quire APIs instead of reaching into private module internals.

### `../quire/quire/artifacts.py`

Owner/subsystem: artifact family placement and addressing primitives.

This file defines artifact locators/addresses/scanned artifacts, branch placement policies, ref codecs, path-backed placement strategies (`FlatYamlPlacement`, hash-scattered YAML, fixed file, subdir fixed file, nested flat YAML, template file, singleton file), document-store backend protocols, artifact contexts/handles/prepared artifacts, and `ArtifactFamily` metadata/contract rendering. It handles branch-name derivation from owners, reversible/nonreversible ref encoding, storage-root scanning, loaded-document ref recovery, unscannable/index-required failures, and placement contract bodies. Boundary: it describes where artifacts live and how refs map to paths/branches; reading/writing stores, document conversion, and family registries live elsewhere. Cleanup relevance: storage placement rules are declarative typed policies instead of hard-coded path conventions in higher layers.

### `../quire/quire/canonical.py`

Owner/subsystem: canonical JSON normalization.

This file defines `normalize_payload`, `canonical_json_text`, and `canonical_json_bytes` for turning VersionIds, msgspec structs, dataclasses, sets, mappings, tuples, lists, and JSON scalars into sorted stable JSON-compatible payloads. It rejects unsupported non-string dict keys and non-JSON values, uses compact deterministic `json.dumps`, and emits UTF-8 bytes. Boundary: canonical serialization helper only; hashing and artifact storage call into it. Cleanup relevance: content identity can rely on one canonical payload normalizer instead of bespoke JSON formatting.

### `../quire/quire/contracts.py`

Owner/subsystem: contract manifest serialization and compatibility checks.

This file defines contract manifest entries, compatibility markers, manifests, check reports, YAML conversion, and `check_contract_manifest`. It normalizes contract bodies through canonical payload rules, sorts entries/markers deterministically, validates duplicate contracts and registry contract consistency, compares previous/current contract bodies and versions, honors explicit compatibility markers, reports added/removed/unchanged/bumped entries, and raises on unbumped incompatible body changes. Boundary: it governs Quire contract manifest metadata; individual artifact/family contract bodies are supplied by other modules. Cleanup relevance: schema/API drift is checked through versioned manifests rather than informal file comparisons.

### `../quire/quire/derived_runtime.py`

Owner/subsystem: SQLite derived-store runtime configuration and schema validation.

This file defines SQLite connection policies, read/write defaults, the derived-store `meta` projection, connection helpers for writable and readonly stores, PRAGMA setup, schema metadata table creation/writes, table existence checks, schema-version reads, and `validate_derived_store_schema`. Boundary: it owns SQLite runtime setup and validation; derived-store materialization and projection schemas live elsewhere. Cleanup relevance: all derived-store SQLite access uses one policy/schema gate instead of ad hoc connections.

### `../quire/quire/derived_store.py`

Owner/subsystem: derived SQLite store cache/materialization management.

This file defines derived-store build diagnostics/errors, projection build steps, handles, GC reports, materialization reports, `DerivedStoreManager`, content hashing helpers, directory/dependency-pin digests, SQLite checkpoint/close, one-off SQLite file materialization, projection-step topological ordering, cross-platform file locking, temp-file handling, and path segment sanitization. It builds cache-keyed stores atomically under locks, skips existing matching stores, cleans temp/WAL/SHM families, and garbage-collects stale cache files. Boundary: it owns materialization/cache mechanics; SQLite connection policy and projection schemas live in other modules. Cleanup relevance: derived sidecars have deterministic cache keys and atomic publication instead of scattered build artifacts.

### `../quire/quire/documents/__init__.py`

Owner/subsystem: Quire documents package public API surface.

This file re-exports document schema loading/conversion helpers, batch document APIs, codec functions, and `LoadedDocument` through `__all__`. Boundary: package-surface wiring only; schema, batch, codecs, and loaded-document behavior live in sibling modules. Cleanup relevance: document APIs are gathered under a shallow namespace for callers.

### `../quire/quire/documents/_paths.py`

Owner/subsystem: document source-label helper.

This file defines `_source_label`, which renders filesystem `Path` values directly and `TreePath` values via `as_posix()` with a cache-key fallback for empty roots. Boundary: small private helper for document diagnostics/loading labels. Cleanup relevance: source labeling is centralized for document loaders.

### `../quire/quire/documents/batch.py`

Owner/subsystem: YAML batch document decoding, loading, and rendering.

This file defines `DocumentBatchSpec`, `LoadedBatchItem`, batch envelope validation, inherited item-field handling, batch byte decoding, file/directory batch loading via `TreePath`, and batch rendering back to YAML. It validates envelope/item shapes and fields, converts each item through document schema conversion with item-specific source labels, strips inherited values from rendered items, and returns loaded item metadata. Boundary: it owns batched document envelopes; single-document codecs/schema conversion live in sibling modules. Cleanup relevance: multi-document YAML files have one typed batch path instead of caller-specific parsing loops.

### `../quire/quire/documents/codecs.py`

Owner/subsystem: document encoding/decoding codec functions.

This file defines payload pruning, document-to-payload conversion, YAML/text/JSON encode/decode/render helpers, schema conversion wrappers, `DocumentCodec`, and `DEFAULT_DOCUMENT_CODEC`. It serializes `to_payload` objects or msgspec structs, prunes `None` values, validates text and JSON/YAML mapping shapes, and packages conversion/decode/encode/render/payload functions behind a codec object. Boundary: it owns byte/text codec behavior; document schema validation and batch envelopes live elsewhere. Cleanup relevance: document IO formats are pluggable through a small codec contract instead of per-call format code.

### `../quire/quire/documents/loaded.py`

Owner/subsystem: loaded document metadata wrapper.

This file defines `LoadedDocument`, a generic container for filename, artifact path, store root, and typed document, coercing path inputs to `TreePath`. Boundary: simple transport object for document loaders. Cleanup relevance: loaded document metadata has one shared wrapper shape.

### `../quire/quire/documents/schema.py`

Owner/subsystem: strict document schema conversion and loading.

This file defines `DocumentStruct`, `DocumentSchemaError`, builtins conversion, msgspec YAML byte decoding, strict value conversion, single document path loading, and directory loading with an optional wrapper. It converts paths to `TreePath`, labels schema errors with source paths, loads only YAML files in sorted order, and wraps loaded documents with metadata. Boundary: it owns strict document schema IO; low-level codecs and batch envelopes are separate. Cleanup relevance: authored YAML/JSON documents enter through strict msgspec schema boundaries instead of loose mappings.

### `../quire/quire/families.py`

Owner/subsystem: artifact family registry, binding, and transaction APIs.

This file defines family identity policies, family declarations/definitions, registries, bound registries/families, pinned families, bound transactions, transactional bound families, contract-manifest generation, storage-root/metadata/accessor lookup, reference-index construction, and registry post-state foreign-key validation. It turns declarations into artifact families, validates explicit versions, duplicate keys/names/accessors and FK targets, exposes family load/save/delete/move/iter/handle operations through a `DocumentFamilyStore`, supports transaction-local save/delete tracking, and validates affected FK families before commit. Boundary: it owns high-level family registry and binding semantics; artifact placement, document store IO, and reference validation primitives live in other modules. Cleanup relevance: typed family registries and FK post-state checks replace ad hoc per-family storage access.

### `../quire/quire/family_store.py`

Owner/subsystem: document family store and transaction wrapper over a backend.

This file defines the document-store backend protocol, branch-head resolution, path normalization, `DocumentFamilyStore`, and `DocumentFamilyTransaction`. It maps artifact families/refs to addresses, coerces/renders/payloads documents through family-specific hooks or codecs, prepares normalized/validated encoded artifacts, loads/exists/handles/iterates documents from a backend, saves/deletes/moves through commits, pins branches to commits, and batches transaction adds/deletes with advisory expected-head checks and branch-consistency enforcement. Boundary: it owns generic document-family IO mechanics; Git backend implementation, family registry FK checks, and artifact placement policies live elsewhere. Cleanup relevance: family reads/writes are routed through a typed store and transaction abstraction instead of direct path/backend mutation.

### `../quire/quire/git_store.py`

Owner/subsystem: Dulwich-backed Git object/document store.

This file defines Git store policy, branch metadata, GC/materialization reports, head mismatch/materialize conflict errors, `HeadBoundTransaction`, and `GitStore`. It initializes/open repos, resolves branches, reads/walks trees, iterates files/dirs, commits adds/deletes/flat trees atomically with expected-head checks and mutation locks, stores blobs, reports reachable/orphan objects, manages branches and branch metadata refs, reverts single-parent commits, computes ancestor distances and merge bases, reads/writes/deletes refs, blobs, and notes, logs/shows/diffs commits, materializes commits to a worktree with conflict detection/cleaning, refreshes the on-disk index, edits trees, caches objects, and prunes stale materialized files while honoring ignored runtime paths. Boundary: it owns low-level Git storage semantics; document-family and artifact registries build on top. Cleanup relevance: repository mutation and materialization have explicit CAS/locking/tree-edit semantics instead of shelling out or mutating the worktree directly.

### `../quire/quire/hashing.py`

Owner/subsystem: canonical JSON hash helper.

This file wraps canonical JSON byte encoding and exposes `canonical_json_sha256`, returning `sha256:<hex>` digests. Boundary: small hash utility over `quire.canonical`. Cleanup relevance: content hashes share a single canonical JSON hash spelling.

### `../quire/quire/notes.py`

Owner/subsystem: Git notes reference and note operations.

This file defines `NotesRef` validation for `refs/notes/*` refs and wrappers to write, read, and remove Dulwich Git notes for an object SHA. Boundary: thin notes adapter used by `GitStore`; repository mutation/locking is handled by callers. Cleanup relevance: note refs and object SHA coercion are centralized instead of duplicated around Dulwich calls.

### `../quire/quire/projection_mapping.py`

Owner/subsystem: object-to-SQL projection mapping models.

This file defines projection codecs, scalar/JSON/enum/reference paths, projection bindings, render-only fields, input keys, components, metadata, attached child rows, selected columns, joins, discriminators, query plans, and `ProjectionModel`. It encodes domain objects into row mappings and child rows, decodes rows back into dataclasses/objects, validates unknown row keys, attaches child rows by parent keys, emits child-row SELECT SQL, executes parent plus attached-row queries, builds `ProjectionTable` definitions with indexes/FKs/checks, and produces stable schema-hash material. Boundary: it maps structured documents/domain objects to projection schemas and rows; actual SQL DDL/runtime and row insertion live in projection/derived-store modules. Cleanup relevance: projection shape is declarative and typed rather than hand-written row dict assembly per family.

### `../quire/quire/projections.py`

Owner/subsystem: SQLite projection schema primitives.

This file defines projection columns/fields, JSON codecs, identifier quoting/validation, reference fields/FKs, indexes, rows, runtime catalog entries, projection tables, FTS5 projections, sqlite-vec projections, projection schemas, dynamic name rendering, schema validation, DDL/insert/select/search SQL generation, row encoding/decoding, and shared semantic field constants. It validates table/column/index/FK declarations, creates DDL statements, inserts rows with optional conflict policies, populates FTS from source queries, builds vector search SQL, produces runtime catalogs and schema-hash material, and checks live SQLite connections for required tables/columns. Boundary: it owns projection schema/SQL primitives; object mapping and derived-store materialization live elsewhere. Cleanup relevance: derived store schemas are declarative typed projection objects rather than raw SQL scattered through callers.

### `../quire/quire/references.py`

Owner/subsystem: reference indexes and foreign-key validation.

This file defines reference resolution/missing/ambiguous errors, `ForeignKeySpec`, FK validation, field-path traversal including `[]` many segments, reference lookup builders, `ReferenceKey`, `FamilyReferenceIndex`, `ReferenceIndex`, and `CrossFamilyReferenceIndex`. It extracts ids and alternate keys from mappings/objects, builds immutable lookup maps, rejects ambiguous family indexes, resolves raw references to ids/details, validates required/single/many foreign keys against target indexes, and supports formatted reference keys. Boundary: it owns in-memory reference resolution and FK checks; family registries and stores supply records. Cleanup relevance: cross-family identity and FK integrity are centralized rather than resolved ad hoc in each artifact family.

### `../quire/quire/refs.py`

Owner/subsystem: Git ref and artifact ref helper types.

This file defines strict `RefName` validation/byte conversion plus factories for immutable single-field and singleton ref dataclasses. Boundary: small identity helper module used by Git notes/store and artifact families. Cleanup relevance: refs have explicit validation and generated typed ref shapes instead of bare strings everywhere.

### `../quire/quire/sqlite_vec_store.py`

Owner/subsystem: sqlite-vec embedding table registry, entity store, and snapshot restore.

This file defines embedding model identity protocol, vector entity store specs, vector snapshots, restore reports, embedding model/status projections, vector projection factory, table setup, `SqliteVecRegistry`, `SqliteVecEntityStore`, and `SqliteVecSnapshotStore`. It registers embedding models, creates per-model vec0 tables, tracks existing content hashes, saves/replaces embeddings by rowid, fetches vectors, runs similarity joins, extracts model/status/vector snapshots, restores snapshots against current source rows while counting restored/stale/orphaned vectors, and tolerates missing tables where appropriate. Boundary: it owns sqlite-vec persistence mechanics; embedding generation and source projection construction live elsewhere. Cleanup relevance: vector cache state is restorable and keyed by model/content/source rows rather than opaque side effects.

### `../quire/quire/tree_path.py`

Owner/subsystem: filesystem/Git tree path abstraction.

This file defines the `TreePath` protocol, shared `_BaseTreePath`, `FilesystemTreePath`, `GitTreePath`, and `coerce_tree_path`. It provides pathlib-like name/stem/suffix/parent/join/read/open/as_posix/cache-key operations over either real filesystem roots or Git store trees at a commit, with sorted iteration and read-only text/binary opens. Boundary: it abstracts read-only tree navigation for document loaders and artifact helpers; Git and filesystem storage implementations stay behind concrete adapters. Cleanup relevance: loaders can consume a single path protocol instead of branching on local files versus Git trees.

### `../quire/quire/versions.py`

Owner/subsystem: calendar contract version identifiers.

This file defines `VersionId`, including whitespace normalization, optional rejection of placeholder values, calendar-version parsing, ordering, and string rendering. Boundary: small value object for contract/family versions. Cleanup relevance: contract versions are validated calendar ids rather than arbitrary strings where strict versions are required.

### `../quire/scripts/benchmark_packed_repo_reads.py`

Owner/subsystem: benchmark script for packed versus loose Git read performance.

This file builds temporary Quire Git repositories with demo YAML artifact families, seeds documents, counts loose/pack objects, packs loose objects, measures repeated point loads, unique point loads, `iter_handles` scans, and pinned iter+require scans over multiple rounds, verifies expected loaded values/totals, and prints median/mean/ms-per-op plus speedups. Boundary: diagnostic benchmark script only; Quire store APIs under test live in package modules. Cleanup relevance: it measures GitStore/DocumentFamilyStore read behavior for packed-object performance investigations.

### `../quire/scripts/benchmark_raw_fs_baselines.py`

Owner/subsystem: raw filesystem/YAML decode baseline benchmark script.

This file seeds temporary YAML documents, measures repeated/unique raw `Path.read_bytes`, repeated/unique read-and-decode, and repeated/unique in-memory msgspec YAML decode workloads, validates expected bytes/decoded documents, and prints median/mean/ms-per-op samples. Boundary: diagnostic benchmark script only; Quire package code is not exercised except for comparison context. Cleanup relevance: it provides filesystem and decoder baselines for interpreting Quire Git read benchmarks.

### `../quire/scripts/profile_dulwich_runtime.py`

Owner/subsystem: Dulwich runtime profiling script for Quire loads.

This file builds a temporary filesystem-backed GitStore, seeds demo artifact-family documents, instruments selected Quire/Dulwich/builtin calls, profiles 5000 unique `DocumentFamilyStore.load` operations with cProfile, verifies the final loaded document, prints runtime binding provenance, instrumented call timing breakdowns, and top cumulative profile rows. Boundary: diagnostic profiling script only; production GitStore/family-store code is observed, not modified. Cleanup relevance: it identifies read-path hotspots in Dulwich/Quire interactions for performance work.

### `../quire/scripts/profile_gitstore_hotpaths.py`

Owner/subsystem: GitStore hot-path instrumentation script.

This file builds temporary GitStore repositories, seeds demo artifact families, instruments selected GitStore and `_repo_object` calls, optionally monkey-patches an object cache, profiles repeated loads, unique loads, and small commit loops, verifies loaded/commit outputs, and prints total timings plus call/cache breakdowns. Boundary: diagnostic profiling script only; production GitStore/family-store behavior is measured externally. Cleanup relevance: it compares hot-path behavior with and without object caching for targeted performance decisions.
