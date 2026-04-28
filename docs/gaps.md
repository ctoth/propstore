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

### Closed 2026-04-28 (WS-I ATMS / world correctness)
- Cluster E HIGH E.H1a/E.H1b/E.H1c — ATMS future-query APIs no longer silently truncate at an implicit default. `is_stable`, `node_relevance`, and `node_interventions` require explicit keyword-only budgets; unbounded mode is `limit=None`, and exhausted finite budgets raise `BudgetExhausted`. Evidence: commits `29a17918`, `791a2a78`, `c736db78`, `367a94ab`, `5e582e6`; test `tests/test_atms_unbounded_stability_api.py`.
- Cluster E HIGH E.H2 — cyclic support pruned by nogoods is classified as `NOGOOD_PRUNED`, not `MISSING_SUPPORT`, so intervention planning sees the right discriminator. Evidence: commits `82374b85`, `3e582e6e`; test `tests/test_atms_was_pruned_by_nogood_cycle.py`.
- Cluster E HIGH E.H3 — categorical or boolean parameterization providers are surfaced as explicit OUT derived nodes with `PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE`, instead of being silently dropped. Evidence: commits `93fd07d9`, `074de941`; test `tests/test_atms_categorical_provider_visibility.py`.
- Codex #24 — derived-vs-derived parameterization contradictions now produce conflict nogoods instead of first-compatible-candidate collapse. Evidence: commits `0e58f69c`, `8d73f291`, `bff598e9`; test `tests/test_atms_derived_contradictions.py`.
- Codex #25 — serialized ATMS support environments preserve both assumption ids and context ids through core, app, CLI, nogood, and future-report surfaces. Evidence: commits `e2ed0435`, `0342ce3f`, `e9635a0b`, `18c4c9a3`, `db9bf660`, `2228c735`, `6a6cc9d6`; test `tests/test_atms_environment_context_serialisation.py`.
- Codex #26 — ATMS exact antecedent matching uses canonical CEL equality for supported commutative forms instead of raw string spelling. Evidence: commits `ac3c99b0`, `63a77d4d`; test `tests/test_atms_cel_semantic_equality.py`.
- Cluster E MED E.M1/E.M2/E.M3 — ATMS build ceilings return partial state with fixpoint metadata, dead `consequent_ids` production surface is gone, and propagation no longer has the old stale-nogood ordering. Evidence: commits `0c03a8f9`, `e0352cc4`, `66423302`, `bcf54490`; tests `tests/test_atms_max_iterations_anytime.py`, `tests/test_atms_consequent_field_discipline.py`, `tests/test_atms_propagation_nogood_interleave.py`.
- Cluster E MED E.M4 — conflict orchestration now fails loudly on synthetic CEL concept collisions, composes parameterization records by return value, has an explicit lifting decision cache, and keys lifted records with derivation-chain provenance. Evidence: commits `4b0285e6`, `f10c3717`; test `tests/test_conflict_orchestrator_isolation.py`.

### Closed 2026-04-28 (WS-D subjective-logic operator naming)
- T2.7 / gaps F1 — `opinion.wbf()` now implements van der Heijden et al. 2018 Definition 4, including Table I WBF output, confidence-weighted base rate, dogmatic/no-evidence cases, and no `_BASE_RATE_CLAMP` in WBF. Evidence: commits `b1dd9c21`, `e197305d`, `7c4f094d`, `02f79021`, `aecf1057`; tests `tests/test_wbf_vs_van_der_heijden_2018_def_4.py`, `tests/test_subjective_logic_operator_audit.py`, `tests/test_consensus_clamp_consistency.py`.
- T2.8 / gaps F2 — `decision_criterion="pignistic"` now means Smets & Kennes 1994 BetP (`b + u/2` for binomial opinions), while Jøsang 2001 Definition 6 is exposed as `projected_probability` in owner and CLI surfaces. Evidence: commits `a8c73757`, `878df257`, `ed61b5fc`, `a489722f`, `02f79021`, `a00bf3e8`; tests `tests/test_pignistic_vs_smets_kennes_1994.py`, `tests/test_subjective_logic_operator_audit.py`, `tests/test_workstream_d_done.py`.
- Cluster F HIGH F3/F4/F12 and MED F5/F8/F10 — PrAF defeat summaries no longer fabricate calibrated opinions, stance confidence without sample size is vacuous, COH dogmatic/divergent cases fail loudly, dogmatic Opinion construction requires explicit opt-in, and CEL literals now cover exponent doubles plus CEL string escapes. Evidence: commits `b7518c45`, `2e74c597`, `f93340ae`, `19bb1072`, `d32bc649`, `9b1e362e`, `9376ea55`, `c19b6e11`, `636f975b`, `48679bbf`; tests `tests/test_defeat_summary_opinion_no_fabrication.py`, `tests/test_from_probability_n_one_round_trip.py`, `tests/test_enforce_coh_diverges_loudly.py`, `tests/test_opinion_allow_dogmatic_enforced.py`, `tests/test_cel_float_exponent.py`, `tests/test_cel_string_escapes.py`.

### Closed 2026-04-28 (WS-E source-promote correctness)
- T3.5 / Cluster A HIGH-1 / Codex 1.14 — source promote now admits justifications only when every conclusion and premise resolves to either the current promotion batch or the captured primary-branch artifact snapshot; dangling source-local-only references are dropped instead of promoted. Evidence: commits `967b819d`, `3f07c56b`; tests `tests/test_source_promote_dangling_refs.py`.
- T3.6 / Cluster A HIGH-3 — source concept alignment now defaults conflicting definitions to attack rather than silently accepting non-attack. Evidence: commits `91bb6601`, `594624a9`; test `tests/test_alignment_default_classification.py`.
- T3.7 / Cluster A HIGH-4 — concept alias collisions now raise `ConceptAliasCollisionError` instead of first-writer-wins alias merging. Evidence: commits `5be268d1`, `5181f1d3`; test `tests/test_alias_collision_rejected.py`.
- T3.8 / Cluster A HIGH-5 — source finalize blocks claims that cannot be represented as micropublications because required context is missing, reports `micropub_coverage_errors`, and bumps the source finalize report contract manifest. Evidence: commits `f93628bf`, `37388421`, `09a3ef6d`, `152818da`; tests `tests/test_finalize_micropub_required.py`, `tests/test_contract_manifest.py`.
- T1.6 / Cluster A HIGH-2 source-promote half — source promotion consumes the WS-C atomicity primitive and WS-Q-cas branch-head CAS path; blocked sidecar mirrors publish only after successful git CAS. Evidence: WS-C commits through `eedfbaa8`, WS-Q-cas commits through `645df92f`; tests `tests/test_promote_atomicity.py`, `tests/test_branch_head_cas_matrix.py`, `tests/test_cas_rejection_no_orphan_rows.py`.
- Cluster A MED M1/M2/M4/M5/M7 — stance targets are guarded before resolution, transaction commit SHAs are captured inside transactions, imported concepts default to `proposed`, ambiguous local-handle import warnings block commit, and promote rebuilds claim payloads without in-place mutation. Evidence: commits `d925fa90` through `6cd6bf63`; tests `tests/test_transaction_commit_sha_lifetime.py`, `tests/test_concept_import_status_proposed.py`, `tests/test_local_handle_collision_blocks_commit.py`, `tests/test_promote_claim_immutability.py`.
- Adjacent datetime/rule validation — source extraction provenance timestamps use timezone-aware UTC and source justification rule kind/strength are validated at commit. Evidence: commits `b5b12940`, `33401d1c`, `7ae17ad8`, `ab73a7b9`; tests `tests/test_extraction_provenance_aware_timestamps.py`, `tests/test_justification_rule_kind_validated.py`.
- WS-E property gates — generated re-promotes preserve canonical claim artifacts, generated source-local fields are stripped before canonical claim payloads, and generated stale-head CAS properties are inherited from WS-Q-cas. Evidence: commit `34d0a459`; tests `tests/test_source_promote_properties.py`, `tests/test_branch_head_cas_properties.py`.

### Closed 2026-04-28 (WS-C sidecar atomicity and SQLite discipline)
- T1.4 / Codex #1 — `materialize(force=False)` now preflights all snapshot conflicts before writing any worktree files, so a refusal does not partially overwrite local edits. Evidence: commits `3b2ec607`, `4fc57df6`; tests `tests/test_T1_4_materialize_atomicity.py`.
- T1.6 / Claude A H2 — source promotion now commits git state before mirroring blocked diagnostics into the sidecar, and returns `PromotionResult` with in-memory blocked-claim diagnostics plus sidecar mirror status. Evidence: commits `d01663c4`, `fea35828`; test `tests/test_promote_atomicity.py`.
- Codex #3 — micropublication sidecar dedupe now consumes WS-CM payload-derived micropub ids: identical authored payloads dedupe, changed authored payloads produce distinct rows. Evidence: commits `9de09633`, `6275a32b`; test `tests/test_micropub_identity_dedupe_shape.py`.
- Codex #2 — claim sidecar dedupe now treats `artifact_id` as the logical handle and `version_id` as the content version; same id plus different version emits `claim_version_conflict`, while duplicate concept links dedupe by the full link primary key. Evidence: commits `6fb2a473`, `03c75dd9`, `3c5daafd`; test `tests/test_codex2_claim_dedupe_diverges_on_version.py`.
- T1.7 / Claude N HIGH-1 — repository builds no longer silently collapse missing sidecars into zero-count success; `RepositoryBuildReport.sidecar_missing` and CLI validation surface the failure. Evidence: commits `912aba09`, `6090cc07`; test `tests/test_T1_7_build_repository_propagates_sidecar_errors.py`.
- Codex #5 — sidecar cache invalidation now derives from source revision, sidecar schema version, generated schema fingerprint, registered semantic pass versions, family contract versions, relevant `uv.lock` dependency pins, and registered build-time config, with `PROPSTORE_SIDECAR_CACHE_BUST` only as an explicit manual override. Evidence: commits `b063f365`, `7dbfd08e`, `6deb1bbc`, `0e7edaa2`, `77177d0f`, `e5b5946f`, `4c05ed04`, `35c118d6`, `eedfbaa8`; test `tests/test_codex5_sidecar_cache_derived_invalidation.py`.
- Adjacent materialize cleanup — semantic-file cleanup now builds the delete plan before unlinking files, avoiding mutation during the `rglob()` traversal. Evidence: commits `b0909d60`, `0bac2c19`; test `tests/test_materialize_clean_unlink_plan.py`.

### Closed 2026-04-28 (WS-Q-cas branch-head CAS discipline)
- D-23 / race-window — propstore mutation paths now capture the branch head before mutation and thread that value into quire's `expected_head` CAS for source finalize, source promote, repository import, and materialize. Evidence: commits `77d67c3e`, `ab20cff6`, `1ece09e4`, `38b19aa1`, `ee6bb945`, `b1d804b7`; tests `tests/test_head_bound_transaction_primitive.py`, `tests/test_branch_head_cas_matrix.py`.
- D-23 / no silent retry — CAS rejection is mapped to typed `StaleHeadError` and propagates without retrying finalize, promote, repository_import, or materialize. Evidence: commit `13402d57`; test `tests/test_cas_no_silent_retry.py`.
- D-23 / no orphan sidecar rows — sidecar writes queued inside the head-bound transaction flush only after kernel CAS success; stale promotion attempts do not leave blocked mirror rows or diagnostics, while promotion-blocked rows are staged in a temporary sidecar and published only after CAS success. Evidence: commits `77d67c3e`, `38b19aa1`, `9e3491b6`, `645df92f`; test `tests/test_cas_rejection_no_orphan_rows.py`.
- D-23 / property gates — generated stale expected heads fail before mutation, and generated concurrent operations have exactly one winner with the loser observing typed stale-head failure. Evidence: commit `93312b07`; test `tests/test_branch_head_cas_properties.py`.
- D-23 / regression gate — scoped mutation paths cannot bypass `head_bound_transaction` with direct family/git commit calls. Evidence: commit `f35d05ab`; test `tests/test_no_unbounded_quire_commit.py`.

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
