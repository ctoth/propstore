# Known Gaps — propstore

This file is the source of truth for gaps between propstore's rhetoric / cited papers / intended behavior and the current implementation. Replaces CLAUDE.md's old "Known Limitations" section, which the 2026-04-16 code review (`reviews/2026-04-16-code-review/axis-6-limitation-honesty.md`) found to be materially inaccurate.

## Discipline

- Every gap has a severity, a citation (axis finding, paper, or observation source), and a plan (workstream, or explicit "not planned").
- Gaps are only added when *observed* (by a reviewer, an agent, or a test failure).
- Gaps are only removed when a test proves closure — the commit that closes a gap also deletes its entry here, and the commit message references the gap entry.
- New workstreams grep this file for relevant gaps; closures happen atomically with implementation.

## Open gaps

### CRIT / structural

### HIGH

- **CLAUDE.md "Pignistic" claim names Denoeux but implements Jøsang.** `propstore/world/types.py:1064-1066` is labeled `"pignistic"` and cites Denoeux p.17-18, but the implemented formula is Jøsang `b + a·u`; Denoeux's binomial BetP is `b + u/2`. Diverges whenever `a ≠ 0.5`. Citation: axis-6 declared-limitation 2 status "materially false"; axis-3b F2. Plan: WS-Z-types (axis-3b docket).

- **`opinion.wbf()` is algebraically aCBF, not WBF.** `propstore/opinion.py` implementation has three structural divergences from the van der Heijden 2018 WBF formula; worked example drifts 0.175 absolute on uncertainty. Commit `c7a9215` self-acknowledges the open bug. Citation: axis-6 declared-limitation 4 "materially false"; axis-3b F1. Plan: WS-Z-types (axis-3b docket).

- **Sidecar claim SI normalization silently writes non-SI values to `_si` columns.** `propstore/sidecar/claim_utils.py:596-606` — on `ValueError`/`TypeError` from `normalize_to_si`, the code writes `value_si = typed_fields.value` (i.e., the unnormalized value). Downstream queries trust the `_si` suffix. Citation: axis-5 Finding 3.1. Plan: not yet scheduled (axis-5 docket).

### MED

- **`dedup_pairs` collapses mirror pairs without provenance.** `propstore/relate.py:67-74` — when `(A,B,0.3)` and `(B,A,0.4)` both exist, keeps the cheaper pair and throws away the other. Silent collapse of two rival evidence records at pair-selection time instead of render time. Citation: axis-1 Finding 1.2. Plan: not yet scheduled.

- **`finalize_source_branch` mutates authored payloads in place.** `propstore/source/finalize.py:96-140` — finalize saves `SOURCE_*_FAMILY` updated documents, overwriting the originals on the source branch. If the user re-runs extract-claims before promote, the finalized layer gets clobbered. The branch preserves one stance (latest finalize), not rival authored-vs-finalized. Citation: axis-1 Finding 1.3. Plan: not yet scheduled.

- **Probabilistic argumentation treewidth bound doesn't deliver.** `propstore/praf/treedecomp.py:13-17` self-documents row count as `O(2^|defeats| * 2^|args|)`, not the Popescu & Wallner 2024 `O(2^tw)` bound the engine dispatch assumes. Queries the engine considers cheap may be exponentially expensive. Citation: axis-6 item 5; axis-3a. Plan: WS-C or independent.

- **Ordinary-premise ordering remains metadata-derived.** Authored rule-file superiority now populates ASPIC+ `rule_order` as a strict partial order, but ordinary-premise ordering still comes from Pareto dominance over `metadata_strength_vector()`, not from an authored premise-priority surface. Citation: narrowed residue of axis-6 item 11; axis-3a. Plan: future premise-priority authoring workstream if premise priorities become a first-class input.

- **Oikarinen strong-equivalence kernels are absent.** No production module implements Oikarinen 2010 `a`/`a*`/`c` kernels or kernel-based strong-equivalence checks for Dung AFs. Phase 5 of the paper-grounded test-suite workstream searched for a production surface and recorded the absence in `reports/paper-grounded-oikarinen-kernel-gap-2026-04-16.md`; no placeholder tests were added. Citation: axis-3a item 5; paper manifest `Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation`; `plans/paper-grounded-test-suite-workstream-2026-04-16.md` Phase 5. Plan: future argumentation strong-equivalence implementation workstream.

- **`pks world chain` accepts lifecycle flags but does not behaviorally filter.** Phase-4 flagged: `chain` accepts `--include-drafts` / `--include-blocked` / `--show-quarantined` for CLI symmetry but `chain_query` reads parameterizations and relationship state rather than a filtered claim set — the constructed `_lifecycle_policy` sits unused. Citation: phase-4 coder report (`reports/ws-z-gates-04-renderpolicy-cli.md` deviation 2; flag 2). Plan: future workstream when chain-query materially consumes claim sets.

- **CLAUDE.md references `aspic_bridge.py` as a file, but it is now a package.** CLAUDE.md lines 35, 45; README.md; `docs/argumentation.md:30`; `docs/data-model.md:332`; `agent-papers.md`; `EXPLORATION_NOTES.txt` all still reference `aspic_bridge.py`. The file does not exist; `aspic_bridge/` does. Citation: axis-9 Findings A.3, E.2, E.3, E.4. Plan: CLAUDE.md rewrite (phase beyond WS-Z-gates).

- **`aspic.py` cites "Modgil & Prakken 2018 Def 1 (p.8)" for contrariness — wrong number, wrong page, wrong content.** `argumentation/src/argumentation/aspic.py:55, 74, 91-93` — Def 1 is on page 4 (Dung acceptability); contrariness is Def 2, page 8. Same phantom citation repeated three times. Citation: axis-9 Findings B.1, C.1 (most-damaging single drift). Plan: citation-discipline cleanup (not yet scheduled).

- **`artifacts/documents/rules.py:120` cites Def 13 for last-link.** Modgil & Prakken 2018 Def 13 is defeat-based conflict-free (which the paper argues *against*). Last-link is Def 20 (p.21). Citation: axis-9 Findings B.2, C.2. Plan: citation-discipline cleanup.

### LOW / NOTE

- **10 pyright errors remain in `propstore/source/common.py` after the phase-4 fix.** Commit `5a47bfa` addressed `cli/source.py:33`; the broader `propstore.artifacts` `__getattr__` lazy-dispatch pattern still produces "Object of type 'object' is not callable" errors across other `SOURCE_*_FAMILY` constants and identity helpers. Citation: phase-4 coder report (flag 1). Plan: follow-up typing workstream.

- **Seven production modules with zero test references.** 1506 LOC in `diagnostics.py`, `fragility_contributors.py`, `fragility_scoring.py`, `fragility_types.py`, `parameterization_walk.py`, `probabilistic_relations.py`, `source_calibration.py`; plus `conflict_detector/orchestrator.py`. Citation: axis-6 item 14; axis-4. Plan: test-coverage workstream.

- **`papers/index.md` is 21% incomplete.** 44 paper directories have no index entry (Pearl 2000, Pierce 2002, Cousot 1977, Clark 2014, Guha 1991, Halpern 2000 among them); 25 directories have no `notes.md` at all (Toni 2014, Clark 2014, Guha 1991, etc. — cited in code but unverifiable). Citation: axis-9 Category D. Plan: papers-index backfill workstream.

- **CLAUDE.md "Defs 1-22" shorthand for Modgil & Prakken 2018.** Paper extends through Def 23+; Def 1 is plain Dung AFs, not ASPIC+. Citation: axis-9 Finding A.4. Plan: CLAUDE.md rewrite.

- **CLAUDE.md TIMEPOINT claim points at wrong file.** Line 16 semantic claim is correct but the implicit pointer (prompt says check `cel_types.py`) is wrong — `KindType` lives in `propstore/cel_checker.py:38`. Citation: axis-9 Finding A.1. Plan: CLAUDE.md rewrite.

- **Citation-pattern drift across codebase.** `aspic.py`, `world/types.py` (Denoeux→Jøsang), and `wbf()` (WBF name, aCBF computation) cite papers for authority while implementing something different. Citation: axis-6 item 15; axis-9 cross-cutting. Plan: citation-as-claim CI lint (per disciplines.md rule 1) + workstream-specific closures.

## Closed gaps (reference only — kept for traceability)

### Closed 2026-04-28 (WS-O-qui quire substrate release)
- S-H1/S-H2 — quire canonical JSON hashing now uses the shared contract payload normalizer, supports domain payloads consistently, and rejects NaN/Infinity. Evidence: quire commits `e4abe17`, `989db98`, `ab982d2`; tests `tests/test_hashing.py`.
- S-H3 — quire transaction head prechecks are explicitly advisory; durable protection remains the write-time CAS. Evidence: quire commits `5e090df`, `ddc32c5`; tests `tests/test_families.py`.
- S-H4 — stale-head write races no longer write failed blobs before the final pre-write branch-head assertion, and `GitStore.gc(dry_run=True)` reports unreachable objects. Evidence: quire commits `e2260e6`, `10cb88f`, `7f0804a`, `5c1523a`; tests `tests/test_git_store.py`.
- S-H5 — filesystem-backed quire repositories serialize mutations with a cross-process lock. Evidence: quire commits `6fe2e0c`, `2c4f5b7`; test `tests/test_git_store.py::test_multiprocess_writers_are_serialized_by_filesystem_lock`.
- S-M1 — family and registry contract-version slots reject placeholder `VersionId` values and require strict calendar contract versions. Evidence: quire commits `8e7fa8f`, `23dcfe2`; tests `tests/test_families.py`.
- S-M2 — ambiguous reference IDs now raise `AmbiguousReferenceError`, while `exists()` remains false for non-unique references. Evidence: quire commits `06956d2`, `8817cf0`; tests `tests/test_references.py`.
- S-M3 — `ForeignKeySpec.required` and `many` are executable through quire's `validate_foreign_key(...)` helper against caller-provided target indexes. Evidence: quire commits `8e047c3`, `1fe47f0`; tests `tests/test_references.py`.
- S-M4 — `materialize_worktree()` refreshes the on-disk index for filesystem repositories. Evidence: quire commits `bd87d88`, `829b5e6`; tests `tests/test_git_store.py`.
- S-M5/S-M6 — opaque hash-scattered iteration and unscannable placements now fail through explicit typed errors instead of unrelated generic `TypeError`s. Evidence: quire commits `b463267`, `f21dd48`, `8df3628`; tests `tests/test_artifacts.py`.
- S-M7 — quire `merge_base()` delegates to Dulwich's native merge-base implementation instead of repeatedly walking ancestor-distance maps. Evidence: quire commits `029846f`, `2f838f9`; tests `tests/test_git_store.py`.
- S-Boundary — propstore's quire imports are covered by quire's public package surface, and propstore pins the pushed quire `0.2.0` release commit. Evidence: quire commits `bac6266`, `f469665`, `23bbac2`; propstore commit `a27b3cbc`; test `tests/test_quire_boundary.py`.

### Closed 2026-04-27 (WS-CM micropub canonical payload and Trusty URI identity)
- D-7 / D-29 — source-finalized micropublication artifact ids are now `ni:///sha-256;...` URIs computed over canonical authored micropub payload bytes, excluding recursive identity fields. Evidence: `tests/test_micropub_identity_trusty_uri.py`.
- D-7 / D-29 — micropublication ids are no longer derived from only `(source_id, claim_id)`; changing authored micropub content changes the id even when the source and claim handle are unchanged. Evidence: `tests/test_micropub_identity_not_logical_handle.py`.
- D-7 / D-29 — generated micropub Trusty URIs verify against exact canonical bytes and fail against mutated bytes. Evidence: `tests/test_micropub_trusty_verification.py`.

### Closed 2026-04-27 (WS-B render policy and web data leak)
- T1.1 / Codex #8 — direct blocked claim reads no longer construct `ClaimViewReport`; they raise `ClaimViewBlockedError` and render a generic 404 with no claim payload. Evidence: `tests/test_render_policy_direct_claim.py`.
- T1.2 / Codex #9 — claim neighborhoods now use policy-filtered stance endpoints and hard-error when the focus claim is hidden. Evidence: `tests/test_render_policy_neighborhood.py`.
- T1.3 / Codex #10 — concept reports are policy-relative and default counts/prose exclude hidden claims. Evidence: `tests/test_render_policy_concept.py`.
- T1.5 / Codex #4 — read-only sidecar queries and `WorldModel` open SQLite in `mode=ro` without switching to WAL. Evidence: `tests/test_sidecar_query_read_only.py`.
- T1.8 — web render-policy float parameters reject non-finite and out-of-range values at the request boundary. Evidence: `tests/test_web_request_float_boundary.py`.
- T1.9 — `pks web --host 0.0.0.0` requires `--insecure` and the insecure path warns. Evidence: `tests/test_pks_web_insecure_flag.py`.
- Codex #11 — malformed concept FTS queries raise `ConceptSearchSyntaxError` and return `400 Invalid Search Query`. Evidence: `tests/test_concept_fts_malformed_query.py`.

### Closed 2026-04-27 (WS-A schema fidelity, fixture parity, identity boundaries)
- T0.1 / Codex #7 — test fixtures no longer own a hand-written world-model schema. Closed by deleting `tests/conftest.py:create_world_model_schema` and routing tests through production-owned `build_minimal_world_model_schema`. Evidence: `tests/test_fixture_schema_parity.py` and the WS-A targeted gate.
- T0.2 / Codex #6 — `_REQUIRED_SCHEMA["claim_core"]` now requires the runtime lifecycle columns consumed by `WorldModel`, including `build_diagnostics`. Evidence: `tests/test_required_schema_completeness.py`.
- Generated schema freshness — generated schema resources are committed and generation is byte-preserving. Evidence: `tests/test_generated_schema_freshness.py`.
- axis-6 item 13 / axis-4 — Hypothesis property markers no longer lie about coverage. Closed by recursive marker maintenance plus collection-time warning for unmarked `@given` tests. Evidence: `tests/test_property_marker_discipline.py` and `scripts/mark_hypothesis_property_tests.py`.
- D-24 T0.3 — URI tagging authorities are parsed and validated before interpolation or repository-config use. Evidence: `tests/test_uri_authority_validation.py`.
- D-24 T0.4 — concept numeric IDs no longer privilege the `propstore` namespace; ambiguous numeric aliases fail unless a namespace is specified. Evidence: `tests/test_no_privileged_namespace.py`.
- D-24 T0.5/T0.6 — source-local claim namespaces and concept aliases cannot mint or shadow reserved canonical namespaces. Evidence: `tests/test_source_cannot_mint_canonical_ids.py`.

### Closed 2026-04-17 (WS-C Defeasibility)
- axis-6 item 6 / axis-7 / axis-9 — defeasibility priority information was unconditionally dropped by `superiority=[]` in the grounding translator and `rule_order=frozenset()` in the ASPIC bridge. Closed by `RulesFileDocument.superiority`, translator strict-partial-order validation and emission, and ASPIC bridge projection of authored schematic superiority onto grounded `PreferenceConfig.rule_order` pairs. Evidence: `tests/test_rule_documents.py`, `tests/test_grounding_translator.py`, `tests/test_defeasible_conformance_tranche.py`, `tests/test_preference.py`, `tests/test_aspic_bridge.py`.
- WS-C C-3/C-4 — CKR-style justifiable exceptions and exception-derived ASPIC+ boundary defeats were absent. Closed by `propstore.defeasibility` support-bearing exception contracts, contextual satisfaction, explicit lifting, unknown-aware decidability status, and `apply_exception_defeats_to_csaf(...)`. Evidence: `tests/test_defeasibility_support_contract.py`, `tests/test_defeasibility_satisfaction.py`, `tests/test_defeasibility_aspic_integration.py`.

### Closed 2026-04-17 (WS-Z-types)
- axis-1 Finding 2.1 / axis-6 item 9 — hardcoded `_DEFAULT_BASE_RATES` fabricated category priors. Closed by replacing the constant with explicit `CategoryPrior` / `CategoryPriorRegistry` inputs and vacuous provenanced opinions when no prior is supplied. Evidence: `tests/test_calibrate.py`, `tests/test_relate_opinions.py`, grep gate for `_DEFAULT_BASE_RATES`.
- axis-1 Finding 2.2 / axis-5 Findings 1.1, 1.2, 1.5 — PrAF claim and stance hooks fabricated dogmatic opinions when calibration was absent. Closed by adding `NoCalibration`, returning `Opinion | NoCalibration`, omitting uncalibrated PrAF arguments/relations with omission records, and removing dogmatic fallbacks. Evidence: `tests/test_praf.py`, `tests/test_source_trust.py`, `tests/test_core_analyzers.py`, `tests/test_praf_integration.py`.
- axis-1 Finding 2.3 / axis-5 Category 1 — `fragility_scoring.imps_rev` fabricated dogmatic PrAF opinions. Closed by requiring caller-supplied provenance-bearing `p_args` and `p_defeats` and rejecting missing/unprovenanced values. Evidence: `tests/test_fragility.py`.
- axis-1 Findings 2.4 and 2.5 / structural S2 — source trust and source quality probability fields lacked status on the stored payload. Closed by mandatory `status` fields on `SourceTrustDocument` and `SourceTrustQualityDocument`, with source initialization/finalization writing `defaulted`, `calibrated`, or `vacuous` status. Evidence: `tests/test_provenance_foundations.py`, `tests/test_source_trust.py`.
- axis-1 Finding 2.6 / structural S3 / axis-5 Finding 1.3 — resolution opinion data used independent scalar fields and `classify.py` wrote invalid no-stance opinions. Closed by `ResolutionDocument.opinion: OpinionDocument | None`, mandatory `OpinionDocument.provenance`, and `classify.py` writing `opinion=None` for no stance. Evidence: `tests/test_provenance_foundations.py`, `tests/test_relate_opinions.py`.
- axis-5 Category 2 / axis-3e CRIT — Z3 `sat | unsat | unknown` collapsed to `bool`, condition classification mapped unknown to overlap, and Dung Z3 enumeration silently truncated. Closed by `SolverSat | SolverUnsat | SolverUnknown`, configured Z3 timeouts, `ConflictClass.UNKNOWN`, explicit unknown propagation, and timeout/unknown tests. Evidence: `tests/test_z3_conditions.py`, `tests/test_condition_classifier.py`, `tests/test_conflict_detector.py`, `tests/test_dung_z3.py`.
- axis-5 Categories 5 and 6 — remaining bool/None collapses lost uncertainty in parameterization and value-resolution paths. Closed by `ParameterizationEvaluation` / `ParameterizationEvaluationStatus`, strict `ast_compare.equivalent` handling, invalid override errors, and fail-closed value-status membership. Evidence: `tests/test_propagation.py`, `tests/test_value_resolver_failure_reasons.py`, `tests/test_fragility.py`, `tests/test_atms_engine.py`, `tests/test_conflict_detector.py`.

### Closed 2026-04-17 (WS-B Phase 4)
- axis-3c / axis-6 item 3 — `propstore/world/ic_merge.py` claimed IC-merge lineage while enumerating only `product(observed_values)` assignments. Closed by renaming that production surface to `propstore/world/assignment_selection_merge.py`, migrating callers/tests/docs to `ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE`, and implementing true Konieczny-Pino Perez model-theoretic IC merge over all `mu`-models in `propstore/belief_set/ic_merge.py`. Evidence: `tests/test_assignment_selection_merge.py`, `tests/test_resolution_helpers.py`, `tests/test_render_contracts.py`, and `tests/test_belief_set_postulates.py`.
- axis-3c / axis-6 item 1 — the old `propstore/revision/` package used AGM-facing names without AGM semantics or postulate tests. Closed by deleting that import path, moving the surviving operational support-incision adapter to `propstore/support_revision/`, and implementing formal AGM/DP/Gardenfors operators with postulate properties under `propstore/belief_set/`. Evidence: `tests/test_revision_retirement.py`, `tests/test_belief_set_postulates.py`, and `tests/test_belief_set_iterated_postulates.py`.
- axis-3c / axis-6 item 2 — AF revision was absent from the old revision package. Closed by implementing Baumann/Diller/Cayrol-facing operators in `argumentation.af_revision` with property tests, while the old active-claim projection adapter moved under the honest support-incision package. Evidence: `tests/test_af_revision_postulates.py` and `tests/test_revision_retirement.py`.

### Closed 2026-04-17 (WS-A Phase 4)
- axis-3d / axis-6 item 3 — semantic substrate remained incomplete at contexts and micropublications. Closed by WS-A Phase 4: `context_hierarchy.py` was replaced by `context_lifting.py`; `ClaimDocument.context` is required; nested `ist(c, p)` proposition documents exist; source finalize/promote emits canonical `micropubs/{source}.yaml`; sidecar `micropublication` and `micropublication_claim` tables materialize bundles; `WorldModel.all_micropublications()` returns typed `ActiveMicropublication` records; `EnvironmentKey` includes `context_ids`; ATMS seeds context nodes and micropublication nodes. Evidence: `docs/contexts-and-micropubs.md`, `tests/test_context_lifting_phase4.py`, `tests/test_micropublications_phase4.py`, `tests/test_labels_properties.py`, and `tests/test_atms_engine.py`.

### Closed 2026-04-16 (this commit)
- axis-1 Finding 3.1 — raw-id claim quarantine. Closed by commit `67fccc1` (WS-Z-gates phase 3).
- axis-1 Finding 3.2 — compiler draft filter. Closed by commit `5bb948d` (WS-Z-gates phase 3).
- axis-1 Finding 3.3 — source promote all-or-nothing. Closed by commits `8923b9f` + `c263db6` (WS-Z-gates phases 3 + 4).
