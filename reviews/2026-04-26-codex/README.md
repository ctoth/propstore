# 2026-04-26 Codex deep review

Scope: `propstore`, direct runtime dependencies in `../argumentation`, `../ast-equiv`, `../bridgman`, `../gunray`, and `../quire`, and paper notes/page evidence in `./papers`.

Constraints followed: I did not open old review artifacts under `reviews/**` or root review/summary files. Paper comparison used local notes and, where agents reported it, page images; no `pdftotext`/`full_text` extraction was used as a paper-reading basis. Findings below distinguish direct local inspection, subagent inspection, and command verification.

## Verification snapshot

- `uv run pyright propstore`: passed with `0 errors`.
- `uv run lint-imports`: passed, 4 contracts kept.
- `powershell -File scripts/run_logged_pytest.ps1`: `2970 passed, 1 failed` in `logs/test-runs/pytest-20260426-154852.log`.
- The pytest failure was `tests/test_repository_artifact_boundary_gates.py::test_current_docs_do_not_name_deleted_repo_storage_surface`, caused by `FileNotFoundError` for `CLAUDE.md`. `git status` showed `D CLAUDE.md` before this review edited anything.
- Direct dependency runtime pins match `pyproject.toml`/installed direct URLs. Sibling checkout `../argumentation` is at `45aa1bbe...` while propstore pins installed `formal-argumentation` at `cc903a62...`; the reported drift was plan-file only, not package code. Other sibling dependency checkouts matched their pins.

## Highest priority findings

### Storage, sidecar, identity

1. **High: `materialize` can partially overwrite the worktree before refusing conflicts.**
   Evidence: `propstore/storage/snapshot.py:201-216` accumulates conflicts but writes non-conflicting files inside the same loop before raising `MaterializeConflictError`. Expected behavior from `docs/git-backend.md` is refusal without partial application unless forced. This needs a preflight conflict pass or transactional temp/write phase.

2. **High: duplicate claim handling rests on a false content-identity premise.**
   Evidence: `propstore/sidecar/claims.py:72-82` says `artifact_id` is content-derived and dedupe is safe, but `propstore/families/identity/claims.py:18-24` derives artifact IDs from normalized logical handles while `version_id` is content-derived at `claims.py:69-71`. `propstore/sidecar/claims.py:85-94` dedupes only parent `claim_core` rows and still inserts child concept links against PKs in `propstore/sidecar/schema.py:401-407`. Same logical ID with different content should be a version conflict; identical duplicate child rows should not crash.

3. **High: micropublication IDs are not content-derived, while sidecar dedupe assumes they are.**
   Evidence: `propstore/source/finalize.py:39-40` derives `ps:micropub:*` from `source_id` and `claim_id`, while `version_id` is separate at `:86`. `propstore/sidecar/micropublications.py:17-57` treats duplicate IDs as content-derived and skips/merges later rows. Trusty/nanopub papers require verifiable content identity; changed evidence/context/provenance can collapse under the same micropub ID.

4. **High: read-only sidecar query opens and configures SQLite in write-capable mode first.**
   Evidence: `propstore/sidecar/query.py:21-30` calls `connect_sidecar` before `PRAGMA query_only=ON`; `propstore/sidecar/sqlite.py:20-22` sets `journal_mode = WAL`. A query path can create or mutate WAL/SHM state before read-only mode is enabled.

5. **Medium: sidecar cache invalidation ignores compiler/pass/family semantics.**
   Evidence: `propstore/sidecar/build.py:77-82` hashes only `SCHEMA_VERSION` and source revision; reuse happens at `:317-320`. Compiler, pass, and family contract changes can reuse stale sidecars if the git source revision is unchanged.

6. **High: schema validation misses columns runtime code requires.**
   Evidence: production schema defines `claim_core.build_status`, `stage`, `promotion_status` and `build_diagnostics` at `propstore/sidecar/schema.py:395` and `:485`. `WorldModel` selects/filters them at `propstore/world/model.py:481` and `:727`, but `_REQUIRED_SCHEMA["claim_core"]` stops before those lifecycle columns at `world/model.py:126`.

7. **High: test fixtures use a hand-written SQLite schema that diverges from production.**
   Evidence: `tests/conftest.py:386` defines `create_world_model_schema`; its source/concept/parameterization shapes differ from `propstore/sidecar/schema.py:79`, `:93`, and production parameterization columns. Tests can pass against a schema production never creates.

### Web/render policy leaks

8. **High: hidden claims are accessible through direct claim URLs.**
   Evidence: `propstore/web/routing.py:144-170` exposes `/claim/{claim_id}` and JSON. `propstore/app/claim_views.py` computes policy visibility but returns the full `ClaimViewReport` even when `visible_under_policy` is false, and `propstore/web/html.py:82-104` renders statement/value/provenance. Default-hidden draft/blocked rows should be 404/403/redacted unless explicitly included.

9. **High: neighborhood routes leak hidden supporter/attacker IDs and edges.**
   Evidence: `propstore/app/neighborhoods.py:126-140` computes visible IDs, then uses unfiltered `world.all_claim_stances()`. `propstore/world/model.py:887-912` returns all claim relations. `neighborhoods.py:141-158` and `:200-214` expose supporters, attackers, rows, nodes, and edges without filtering related claims through the render policy.

10. **Medium: concept pages disclose hidden claim counts and type distribution.**
    Evidence: `propstore/app/concept_views.py:162-184` loads both policy-filtered and unfiltered claims; `_concept_status` reports total/blocked counts at `:242-270`, and `_claim_groups` computes blocked counts by claim type at `:275-309`.

11. **Medium: malformed concept FTS queries can escape as 500s.**
    Evidence: `propstore/web/routing.py:381-406` passes raw `q` to `search_concepts`; `propstore/app/concepts/display.py:40-49` uses `concept_fts MATCH ?`; `_EXPECTED_WEB_ERRORS` in routing does not include `sqlite3.OperationalError`.

### Argumentation, ASPIC, PrAF, belief revision

12. **High: ASPIC grounded can accept attack-conflicting arguments.**
    Evidence: `propstore/structured_projection.py:253` delegates grounded ASPIC results to `argumentation.dung.grounded_extension`, whose dependency implementation ignores `attacks` and uses `defeats` only. `tests/test_structured_projection.py:688` pins a mutually attacking/no-defeat case where both arguments are justified. ASPIC+/Dung grounded extensions should be conflict-free over the relevant attack/defeat semantics.

13. **High: `aspic-incomplete-grounded` and `aspic-direct-grounded` are advertised but not executed.**
    Evidence: `propstore/world/types.py:667-672` marks them supported for ASPIC, while `propstore/structured_projection.py:240-258` handles only grounded/preferred/stable then raises. Dependency incomplete support exists but is not routed.

14. **High: `praf-paper-td-complete` is advertised but wired as a normal acceptance query.**
    Evidence: `propstore/world/types.py:623` defines it and `:682` supports it; runtime calls in `propstore/core/analyzers.py:767-771`, `propstore/world/resolution.py:691`, and `propstore/app/world_reasoning.py:239` pass it as `semantics` with `query_kind="argument_acceptance"`. The dependency paper TD backend is selected by `strategy="paper_td"` and requires `extension_probability` plus a queried set.

15. **High: missing PrAF calibration deletes arguments and relations instead of representing ignorance or failing hard.**
    Evidence: `propstore/core/analyzers.py:665`, `:675`, and `:700` omit uncalibrated arguments/relations; metadata at `:794` does not surface the omissions. Li PrAF existence probabilities and Jøsang/Shafer uncertainty distinguish ignorance from nonexistence.

16. **High: raw confidence can become fabricated dogmatic evidence.**
    Evidence: `propstore/praf/engine.py:291-304` maps raw `confidence` to opinions and turns `1.0` into dogmatic true; `:164` falls claim confidence into claim probability. Sensoy/Jøsang treat evidence as non-negative counts/Dirichlet strength; an uncalibrated score of `1.0` is not infinite evidence.

17. **High: DF-QuAD treats probabilistic support and attack asymmetrically.**
    Evidence: `../argumentation/src/argumentation/probabilistic.py:1363` feeds `p_supports` into supports weights; `probabilistic_dfquad.py:163-164` uses attacker strengths at full value while multiplying supporters by support probability. A defeat with probability 0 can still attack at full strength if structurally present.

18. **High: IC merge drops infinite distances.**
    Evidence: `propstore/belief_set/ic_merge.py:80-86` filters `math.inf` out before SIGMA or GMAX scoring. A profile formula with no model should not silently contribute nothing; this can let impossible or unsatisfied inputs stop affecting the merge score.

19. **High: live worldline revision does not populate merge-parent evidence.**
    Evidence: `propstore/support_revision/projection.py:76` builds `RevisionScope` with only bindings/context; `merge_parent_commits` stays default in `state.py:96`, so the merge guard in `iterated.py:66` is unreachable through normal `BoundWorld -> project_belief_base -> make_epistemic_state`. Bonanno's temporal revision frame requires backward-unique histories and flags DAG merge points as violations.

20. **High: AF revision conflates no stable extension with the empty extension.**
    Evidence: `../argumentation/src/argumentation/af_revision.py:274` uses `tuple(stable_extensions(framework)) or (frozenset(),)`, mirrored in `tests/test_af_revision_postulates.py:111`. "No stable extensions" is not the same as "the empty set is a stable extension."

21. **Medium: complete semantics is available in the dependency but missing from key propstore surfaces.**
    Evidence: dependency has `complete_extensions`; `complete` is normalized in `propstore/world/types.py:637`, but claim-graph dispatch in `propstore/core/analyzers.py:568` handles grounded/preferred/stable only, and ASPIC support omits complete.

22. **Medium: asymmetric stance intent is encoded through symmetric contradiction.**
    Evidence: `propstore/aspic_bridge/translate.py:139-193` maps `supersedes`/`undermines` into contradictory pairs and patches direction later through preference-sensitive filtering. Modgil/Prakken distinguish symmetric contradictories from asymmetric contraries.

23. **Medium: AGM contraction collapses Spohn epistemic state.**
    Evidence: `propstore/belief_set/agm.py:116-120` computes contraction then returns `SpohnEpistemicState.from_belief_set`, which flattens models/non-models at `:55`. Iterated revision should preserve epistemic-state ranking structure, not only the resulting belief set.

### ATMS, provenance, context

24. **High: derived-vs-derived contradictions are hidden instead of becoming nogoods.**
    Evidence: `propstore/world/value_resolver.py:166-178` returns the first compatible derived candidate. ATMS builds derived nodes at `propstore/world/atms.py:1422`, but nogoods consume only runtime claim-pair conflicts at `:1481`; `BoundWorld.conflicts()` is direct-claim based at `propstore/world/bound.py:920`. de Kleer ATMS contradictions in propagated dependency space should become nogoods.

25. **High: context-bearing ATMS environments are serialized as assumption-only.**
    Evidence: `EnvironmentKey` carries assumptions and contexts, but `_serialize_environment_key` returns only `environment.assumption_ids` at `propstore/world/atms.py:2369`; labels/nogoods build on that at `:2375` and `:2383`; app `_support_ids` repeats the loss at `propstore/app/world_atms.py:195`.

26. **Medium: exact ATMS support depends on raw CEL string equality.**
    Evidence: `propstore/world/atms.py:1562` matches `assumption.cel == condition`; runtime activation uses typed/solver compatibility in `propstore/world/bound.py:299`. Semantically equivalent CEL can be active in the world but missing from ATMS support.

27. **Medium: semiring provenance collapses to ATMS why-labels too early.**
    Evidence: `propstore/core/labels.py:265` multiplies polynomials then projects to environments and rebuilds; `_polynomial_to_environments` at `:350` and `:375` ignores coefficients/exponents and treats non-prefixed variables as assumptions. This is an ATMS projection, not Green universal `N[X]` provenance.

### CEL, units, equations, algorithms

28. **High: parameter conflict detection compares raw values, not canonical units.**
    Evidence: `propstore/conflict_detector/models.py:43` and `:106` carry raw value/unit but no canonical `value_si`; orchestrator calls without form metadata at `orchestrator.py:74`; `parameter_claims.py:112` calls `_values_compatible` without forms. Unit normalization only happens when forms are supplied in `propstore/value_comparison.py:97`. Main conflict detection can treat `200 Hz` and `0.2 kHz` as conflicting.

29. **High: Z3 division guards are conjoined globally, changing boolean semantics.**
    Evidence: `propstore/core/conditions/z3_backend.py:121` emits denominator guards; `condition_ir_to_z3` conjoins all guards with the whole formula at `:31`. Similar logic exists in `propstore/z3_conditions.py:252` and `:410`. `enabled || (1 / x > 0)` should not require `x != 0` when `enabled` is true.

30. **Medium: CEL ternary checking does not enforce boolean condition or branch type agreement.**
    Evidence: `propstore/cel_checker.py:586-590` checks children and returns the true-branch type; it does not validate test type or branch unification before lowering to `ConditionChoice` and Z3 `If`.

31. **Medium: equation equivalence is orientation-sensitive.**
    Evidence: `propstore/equation_comparison.py:176-184` stores `str(sympy.cancel(sympy.expand(lhs - rhs)))`; comparison uses exact string equality at `:108`; conflict detection records conflicts when strings differ. `x = y` and `y = x` can normalize to different strings.

32. **Medium: SymPy generation drops the equation left-hand side.**
    Evidence: `propstore/sympy_generator.py:54-91` returns a SymPy-parseable string of the RHS. `y = f(x)` and `z = f(x)` can share generated text if callers use it as an equation identity.

33. **Medium: algorithm conflict detection treats `ast-equiv` SymPy equivalence as conflict.**
    Evidence: `../ast-equiv/ast_equiv/comparison.py:273` can return `equivalent=True, tier=Tier.SYMPY`; propstore suppresses conflicts only for canonical/bytecode tiers at `propstore/conflict_detector/algorithms.py:55`. Current tests pin that behavior at `tests/test_conflict_detector.py:901` and `:911`.

34. **Medium: algorithm unbound-name validation misuses `extract_names` as free-variable analysis.**
    Evidence: `propstore/families/claims/passes/checks.py:819-827` subtracts declared variables from `ast_equiv.extract_names(tree)`, but `../ast-equiv/ast_equiv/canonicalizer.py:47-54` returns all `ast.Name` nodes plus function args, including local temporaries.

### Contexts, concepts, forms, publication surface

35. **High: nested `ist`/`proposition` claims are schema-only and do not reach the semantic pipeline.**
    Evidence: `propstore/families/claims/documents.py:562` accepts `proposition` and serializes it at `:630`, and `docs/contexts-and-micropubs.md:32` says nested `ist` propositions are expressible. Validation reads top-level `claim.get("type")` at `propstore/families/claims/passes/checks.py:429`; sidecar reads top-level type/fields at `propstore/sidecar/claim_utils.py:672-675`; FTS uses top-level `claim.statement` at `propstore/sidecar/passes.py:821`. McCarthy/Guha context logic centers `ist(c,p)`, including nested assertions.

36. **High: duplicate concept `canonical_name` is downgraded to warning while lookup is first-wins.**
    Evidence: `propstore/cel_registry.py:112` raises duplicate canonical names, but `propstore/families/concepts/passes.py:506-507` records only a warning. Canonical name is a reference key at `propstore/families/concepts/stages.py:270`, and registry construction uses `setdefault` at `:832`.

37. **Medium: invalid form `kind` silently becomes `quantity`.**
    Evidence: `propstore/families/forms/documents.py:33` leaves `kind` unconstrained; `propstore/families/forms/stages.py:84` and `propstore/form_utils.py:38` use `_KIND_MAP.get(raw_kind, KindType.QUANTITY)`. `docs/units-and-forms.md:33` documents a closed enum.

### CLI/application ownership

38. **High: app-layer request objects still accept CLI-shaped payloads.**
    Evidence: `propstore/app/forms.py:49-57` has `dimensions_json`, `dimensionless`, `common_alternatives_json`; parsing/errors at `:234-273` name CLI flags. `propstore/app/concepts/mutation.py:253-260` accepts comma-string `values` and flag `closed`; errors at `:1084-1097` name CLI options. CLI should parse strings into typed request values before owner/app logic.

39. **High: worldline/revision app code parses CLI option payloads.**
    Evidence: `propstore/app/worldlines.py:82-89` parses raw `--revision-atom` JSON and reports missing `--revision-*` options at `:367-377`; `propstore/app/world_revision.py:138-146` reports `--atom`, `--target`, `--operation` from owner-style code.

40. **Medium: owner modules write directly to process streams or own command parsing.**
    Evidence: `propstore/sidecar/build.py:467-480` prints embedding snapshot status to `stderr`; `propstore/provenance/__init__.py:428` prints unsupported file type to `stderr`; `propstore/contracts.py:287-301` parses argv, prints/writes, and raises `SystemExit`.

## Test and gate gaps

- Missing IC4 fairness property against `propstore.belief_set.ic_merge.merge_belief_profile`; current formal IC tests cover other postulates, while scalar assignment-selection tests explicitly are not the full paper postulate.
- ASPIC rationality tests cover only part of Modgil/Prakken; strict closure, indirect consistency, and one admissibility variant are not gated.
- AGM recovery is not tested; iterated belief-revision tests do not sweep full Darwiche-Pearl C1-C4 behavior.
- Generated schema freshness/package-resource coverage is not enforced. `schema/generate.py` writes `propstore/_resources/schemas`, but that tree is absent and tests tolerate conditional copying.
- Architecture gates are mostly selected-file/string checks; import-linter currently has only four contracts. Package-wide CLI/owner constraints would catch the app-layer CLI payload leaks above.
- The `property` marker is declared, but many Hypothesis tests are unmarked, so `-m property` would underselect property tests.

## Checked-clean notes

- Root CLI command registration is lazy: `propstore/cli/__init__.py` stores module specs and imports only requested command modules.
- I did not find Click imports in checked owner-layer package surfaces.
- Web HTML escaping appears centralized through `propstore/web/html.py:_text`; route `limit` is bounded; `branch`/`rev` parameters are rejected rather than used as filesystem paths; static assets use a fixed package directory.
- Canonical claim raw `id`/`artifact_code` are rejected by validation; claim/concept logical IDs require non-empty validated lists; context lifting rejects unknown source/target contexts.

## Suggested repair order

1. Fix data-leak and atomicity bugs first: direct claim/neighborhood policy leaks, materialize preflight, read-only sidecar connections.
2. Fix identity collision/dedupe premises: claim/micropub/content identity, concept canonical-name duplicates, sidecar schema-required columns.
3. Repair semantic unsoundness in core reasoning: ASPIC grounded conflict-free behavior, advertised-but-unrouted semantics, IC infinite distances, PrAF calibration omissions, unit-normalized conflict detection, Z3 guard scoping.
4. Replace duplicate test schemas with production schema construction, then add property/gate coverage for the findings above.
