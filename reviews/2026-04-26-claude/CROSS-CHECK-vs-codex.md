# Cross-check: Claude review vs Codex review (2026-04-26)

Two independent deep reviews of propstore + dependencies were performed on the same day:
- **Claude**: 21 parallel cluster reports under `reviews/2026-04-26-claude/`
- **Codex**: 1 README + 7 TDD-style workstream remediation plans under `reviews/2026-04-26-codex/`

This file cross-references the two and synthesizes a combined critical-priority list. Codex numbered its findings 1–40; Claude organized by cluster A–V.

## Summary

- **Both caught (corroboration — high confidence real)**: ~9 findings.
- **Codex-only (Claude blind spots)**: ~22 findings, especially in the sidecar-atomicity and web-render-policy classes that Claude largely missed.
- **Claude-only (Codex blind spots)**: ~30 findings, especially in math/naming corrections (`opinion.wbf`, `pignistic`), the heuristic→source layering leak, dependency-internal bugs (`argumentation` ideal_extension, `ast-equiv` while-to-for), and the `dims_of_expr` TypeError-swallow trap.
- **Disagreements**: none observed. The reviews complement each other; no contradicting verdicts.

The complete picture is the **union** of the two reviews. Neither alone is sufficient.

## Section 1 — Both caught (corroborated findings)

These are validated by independent observation. Treat as definitely-real, fix first.

| # | Finding | Claude location | Codex # |
|---|---|---|---|
| C1 | **Asymmetric stance encoded via symmetric contradiction.** `aspic_bridge/translate.py:139-193` maps `supersedes`/`undermines` into contradictory pairs, losing directionality. | Cluster D HIGH-2 | #22 |
| C2 | **AGM contraction collapses Spohn epistemic state.** `belief_set/agm.py:116-120` rebuilds via `from_belief_set`, flattening the ranking. Iterated contractions degenerate to two levels. | Cluster C HIGH-3 | #23 |
| C3 | **Micropublication IDs are not content-derived.** `source/finalize.py:39-40` uses `(source_id, claim_id)` only; payload changes don't change the ID, breaking Kuhn 2014 immutability. Sidecar dedupe assumes content identity. | Cluster M HIGH-6 | #3 |
| C4 | **CEL ternary type-rule unsound.** `cel_checker.py:586-590` doesn't enforce boolean condition or branch type unification. | Cluster G HIGH | #30 |
| C5 | **Nested `ist`/`proposition` claims schema-only.** `ClaimDocument.proposition` is parsed and serialized but never reaches validation/sidecar/FTS. McCarthy/Guha context logic is centered on `ist(c,p)`. | Cluster B HIGH | #35 |
| C6 | **Live worldline revision does not populate merge-parent evidence.** `support_revision/projection.py:76` builds `RevisionScope` without `merge_parent_commits`. Codex notes the merge guard is unreachable through normal flow; Claude notes the runner converts the refusal to an error revision payload. Same root cause, two consequences. | Cluster J | #19 |
| C7 | **ASPIC routing gaps for advertised semantics.** `aspic-incomplete-grounded` and `aspic-direct-grounded` are advertised but `structured_projection.py:240-258` raises; `praf-paper-td-complete` is wired as ordinary `argument_acceptance` instead of `paper_td` strategy. Codex flagged precisely; Claude's cluster D listed coverage gaps in the bridge but routed through structured_projection only at #12 below. | Cluster D + Cluster F | #13, #14 |
| C8 | **Complete semantics missing from key surfaces.** Dependency has `complete_extensions`; propstore claim-graph dispatch handles only grounded/preferred/stable. | Cluster P | #21 |
| C9 | **Algorithm unbound-name validation misuses ast-equiv `extract_names`.** Returns all `ast.Name` nodes including local temporaries; subtraction-as-free-vars is wrong. Claude flagged the canonicalizer's broad name extraction; Codex traced the consumer error precisely. | Cluster T | #34 |

These nine are the safest items to land first — both reviewers saw them.

## Section 2 — Codex-only (Claude missed)

Codex covered classes of bug Claude largely missed. These are the most important blind-spots in the Claude review.

### Sidecar atomicity / SQLite discipline / production-vs-test schema (5 findings)

This entire class was a Claude blind spot. Cluster A was data-layer-focused but didn't drill into SQLite-mode/PRAGMA discipline; cluster N was pipeline-focused.

- **#1 — `materialize` partial-overwrite.** `storage/snapshot.py:201-216` writes non-conflicting files inside the same loop before raising `MaterializeConflictError`. Worktree is partially mutated on conflict.
- **#4 — Read-only sidecar query opens write-capable mode first.** `sidecar/query.py:21-30` calls `connect_sidecar` (which sets `journal_mode=WAL`) before `PRAGMA query_only=ON`. WAL/SHM state can be created by a "read-only" path.
- **#5 — Sidecar cache invalidation ignores compiler/pass/family semantics.** `sidecar/build.py:77-82` hashes only `SCHEMA_VERSION` and source revision; compiler/pass/family contract changes can reuse stale sidecars when git revision is unchanged.
- **#6 — Schema validation misses runtime columns.** `_REQUIRED_SCHEMA["claim_core"]` in `world/model.py:126` doesn't include `build_status`, `stage`, `promotion_status`, `build_diagnostics` even though `WorldModel` selects/filters on them.
- **#7 — Test fixtures use a hand-written schema diverging from production.** `tests/conftest.py:386 create_world_model_schema` doesn't match `propstore/sidecar/schema.py`. **Tests can pass against a schema production never creates.** This single finding undermines confidence in the entire test suite for `WorldModel`.

### Web render-policy leaks (4 findings — privacy/security class)

Claude's cluster K caught `--host 0.0.0.0` no-auth exposure but missed every render-policy bypass. This is a serious class.

- **#8 — Hidden claims accessible via direct URLs.** `/claim/{claim_id}` returns full `ClaimViewReport` (statement/value/provenance) even when `visible_under_policy` is false. Default-hidden draft/blocked rows should be 404/403/redacted.
- **#9 — Neighborhood routes leak hidden supporter/attacker IDs and edges.** `app/neighborhoods.py:126-140` filters visible IDs but then uses unfiltered `world.all_claim_stances()`.
- **#10 — Concept pages disclose hidden claim counts and type distribution.** `app/concept_views.py:162-184` loads both filtered and unfiltered claims; reports total/blocked counts and per-type blocked counts.
- **#11 — Malformed concept FTS queries escape as 500s.** `_EXPECTED_WEB_ERRORS` in `web/routing.py` doesn't include `sqlite3.OperationalError`.

### ATMS-specific (3 findings)

Claude's cluster E covered the algorithm shape and ≤8-subset under-approximation, but missed the structural finds Codex caught.

- **#24 — Derived-vs-derived contradictions hidden, not nogoods.** `value_resolver.py:166-178` returns first compatible derived candidate; ATMS builds derived nodes but `nogoods` consume only direct-claim conflicts. de Kleer ATMS contradictions in propagated dependency space should become nogoods.
- **#25 — Context-bearing ATMS environments serialized as assumption-only.** `_serialize_environment_key` returns only `assumption_ids`; labels/nogoods build on that. The context part of `EnvironmentKey` is structurally lost.
- **#26 — Exact ATMS support depends on raw CEL string equality.** `atms.py:1562 assumption.cel == condition`; runtime activation uses typed/solver compatibility. Semantically equivalent CEL active in the world is missing from ATMS support.

### Other Codex-only

- **#2 — Duplicate claim handling rests on a false content-identity premise.** `sidecar/claims.py` says `artifact_id` is content-derived; `families/identity/claims.py` derives from normalized logical handles while `version_id` is content-derived. Same logical ID with different content should be a version conflict; identical duplicate child rows shouldn't crash.
- **#12 — ASPIC grounded delegates to `argumentation.dung.grounded_extension` which ignores attacks.** `structured_projection.py:253` route accepts attack-conflicting arguments. Claude's cluster D flagged transposition+contrariness mismatches and `arguments_against` gaps but missed this specific delegation bug at the structured_projection layer. Test pins it.
- **#15 — Missing PrAF calibration deletes arguments and relations.** Claude's cluster F flagged "defeat-summary fabricates uncertainty" — Codex's complementary finding is that uncalibrated inputs are *silently dropped* rather than represented as ignorance.
- **#16 — Raw confidence becomes fabricated dogmatic evidence.** `praf/engine.py:291-304` maps raw confidence 1.0 to dogmatic-true. Sensoy/Jøsang treat evidence as non-negative counts/Dirichlet strength; 1.0 isn't infinite evidence.
- **#17 — DF-QuAD asymmetric support/attack in argumentation pkg probabilistic.** `probabilistic_dfquad.py:163-164` uses attacker strengths at full value while multiplying supporters by support probability. Claude's cluster P went broad; missed this specific asymmetry.
- **#18 — IC merge drops infinite distances.** `belief_set/ic_merge.py:80-86` filters `math.inf` before SIGMA/GMAX. A profile formula with no model contributes nothing instead of infinite cost.
- **#20 — AF revision conflates no stable extension with empty extension.** `argumentation/src/argumentation/af_revision.py:274 tuple(stable_extensions(framework)) or (frozenset(),)`. "No stable" ≠ "the empty set is stable."
- **#27 — Semiring provenance collapses to ATMS why-labels too early.** `core/labels.py:265` projects polynomials to environments and rebuilds; this is ATMS projection, not Green universal `N[X]` provenance. Claude's cluster M said the polynomial algebra is "faithful to Green for positive-RA" but missed this premature collapse.
- **#28 — Parameter conflict compares raw values not canonical units.** `conflict_detector/models.py:43,106` carry raw value/unit but no canonical `value_si`. `200 Hz` and `0.2 kHz` can be flagged conflicting. Claude's cluster G caught the affine-temperature-delta bug in the same module family but missed this orchestrator-level oversight.
- **#29 — Z3 division guards conjoined globally.** `core/conditions/z3_backend.py:121` emits denominator guards; `condition_ir_to_z3` conjoins all guards with the whole formula. Boolean semantics are wrong: `enabled || (1 / x > 0)` shouldn't require `x != 0` when `enabled` is true.
- **#31 — Equation equivalence orientation-sensitive.** `equation_comparison.py:176-184` stores `str(cancel(expand(lhs - rhs)))`; comparison uses exact string equality. `x = y` and `y = x` can normalize to different strings. Claude's cluster G flagged the log/exp/sqrt failure mode; Codex flagged this orientation issue separately.
- **#32 — SymPy generation drops equation LHS.** `sympy_generator.py:54-91` returns RHS only; `y = f(x)` and `z = f(x)` share generated text.
- **#33 — Algorithm conflict treats SymPy-tier equivalence as conflict.** `conflict_detector/algorithms.py:55` suppresses only canonical/bytecode tiers; tests pin this. SymPy-tier equivalence under `ast-equiv` should not be a conflict signal.
- **#36 — Duplicate concept canonical_name downgraded to warning while lookup is first-wins.** `cel_registry.py:112` raises duplicates; `families/concepts/passes.py:506-507` only warns. Inconsistency is the bug.
- **#37 — Invalid form `kind` silently becomes `quantity`.** `_KIND_MAP.get(raw_kind, KindType.QUANTITY)`. `docs/units-and-forms.md` documents a closed enum.
- **#38, #39 — App-layer request objects accept CLI-shaped payloads.** `app/forms.py`, `app/concepts/mutation.py`, `app/worldlines.py`, `app/world_revision.py` parse JSON/comma-strings and report `--flag-name` errors from owner-style code. CLI should parse strings into typed request values before owner/app logic.
- **#40 — Owner modules write to process streams or own command parsing.** `sidecar/build.py:467-480`, `provenance/__init__.py:428` print to stderr; `contracts.py:287-301` parses argv, prints, and raises `SystemExit`. Architecture-ownership leak.

## Section 3 — Claude-only (Codex missed)

Codex's review was strong on sidecar/web/test-infrastructure and weaker on:
- Math/operator-name correctness (`opinion.wbf`, `pignistic`, `from_probability(n=1)`)
- Cross-repo and inter-package boundary leaks
- Dependency-internal bugs (`argumentation` and `ast-equiv` and `gunray` internals)
- Architecture-decorative findings (import-linter contracts being vacuous)
- Some specific data-pipeline silent-failure bugs

### Math / naming

- **opinion.wbf() is algebraically aCBF, not WBF.** Worked example drifts 0.175 absolute on uncertainty. Cluster F + gaps.md HIGH.
- **`decision_criterion="pignistic"` cited Denoeux but formula is Jøsang's projected probability `b + a·u`.** Cluster F + gaps.md HIGH.
- **`from_probability(n=1)` shifts.** Cluster F.
- **`enforce_coh` divergence from Jøsang.** Cluster F.

### Architecture leaks Codex didn't flag

- **All four import-linter `forbidden` contracts are vacuously satisfied.** No current code attempts the forbidden imports; the linter catches nothing. Cluster U.
- **Heuristic logic lives outside `propstore/heuristic/`.** `embed.py`, `classify.py`, `relate.py`, `calibrate.py` are top-level. README says Layer 3 = `propstore/heuristic/`; package contains 2 files. Cluster U.
- **`derive_source_document_trust` (Layer 3) writes to source storage (Layer 1) with no proposal gate.** `app/sources.py:191-200,505-516` → `source/finalize.py:178-185`. Cluster H + Cluster U.
- **`storage/repository_import.py` has zero provenance annotation surface.** Imported rows look identical to authored rows. Direct violation of "imports are opinions". Cluster U.

### Source-promote and finalize

- **`source/promote.py:711-727` justification filter admits dangling refs** on master. Inconsistent with stance loop's conservative test. Cluster A HIGH.
- **Sidecar-before-git PK collision risk.** Failed promote can poison subsequent successful ones. Cluster A HIGH + Cluster N HIGH.
- **`source/alignment.py:96-98` defaults to `non_attack`.** The alignment AF defaults to credulous-accept; the only paths producing `attack` are narrow same-identity-different-definition cases. Defeats the layer's purpose. Cluster A HIGH.
- **`source/registry.py:42-47` alias collisions silently merge via `setdefault`.** Cluster A HIGH.
- **Micropubs silently skipped for context-less claims.** Cluster A HIGH.
- **`uri.py:19-22` authority unsanitized.** User-supplied authority strings reach identity comparisons unvalidated. Cluster A HIGH.
- **`build_repository` swallows sidecar `FileNotFoundError`** and reports success indistinguishable from "empty repo". Cluster N.
- **`_normalize_concept_batch` silently overwrites on collision** while sibling claim batch warns. Inconsistent. Cluster N.

### Argumentation-pkg internal bugs

- **`ideal_extension` returns union of admissible-maximals.** Admissibility isn't closed under union. Wrong-result bug. Cluster P.
- **`aspic_encoding._literal_id = repr(literal)` produces non-loadable ASP.** `~p` and `p(1, 2)` aren't valid ASP identifiers. The Lehtonen-2024 fact encoding cannot actually be loaded into clingo. Cluster P.
- **Silent rule-name collision in `defeasible_rule_ids` dict.** Cluster P.
- **`aspic.py` `strictly_weaker` vs `preference.py` `strictly_weaker` disagree on `(non-empty, empty)` boundary.** Cluster P.
- **Probabilistic confidence dict uses exact 0.90/0.95/0.99 string keys.** Cluster P.

### gunray, quire, ast-equiv, bridgman internals

- **gunray `build_arguments` exponential per candidate.** `_has_redundant_nonempty_subset` runs O(k) memo-free strict closures. Cluster R.
- **gunray `disagrees` re-grounds entire theory on every call** inside `counter_argues`. Cluster R.
- **propstore re-grounds twice via `evaluate` + `inspect_grounding`.** Cluster R.
- **gunray→propstore evaluate path discards `DefeasibleTrace`.** Bare `DefeasibleModel.sections` carries no per-fact rule-id back-pointer. Provenance loss at the boundary. Clusters B, D, M, R all corroborated.
- **propstore→gunray `translator.py` flattens `RuleDocument`/`AtomDocument` to surface strings.** Cluster R.
- **quire `canonical_json_sha256` and `contracts._normalize_payload` use different normalization rules in the same package.** Silent hash divergence. Cluster S.
- **quire CAS-failed commits leak orphan blobs/trees** with no GC. Cluster S.
- **propstore keeps three duplicate `_canonical_json` implementations** that don't import quire's. Cluster S.
- **ast-equiv identity-elimination `x+0→x` has no type guard** despite the canonicalizer commenting that `+` is overloaded. Cluster T.
- **ast-equiv `WhileToForNormalizer` ignores `break`/`continue`** and accepts non-int init values. Cluster T.
- **ast-equiv `compare()` swallows all exceptions in three tiers** via bare `except Exception`. Cluster T.
- **bridgman `dims_of_expr` raises TypeError on transcendentals; propstore swallows.** Equations with sin/cos/exp/log silently pass dim check. Cluster Q + Cluster G.
- **bridgman `verify_equation` ignores extra `rhs_terms`** when ops/terms lengths disagree. Cluster Q.
- **Affine temperature units treated as linear for deltas (~273 K silent error).** Cluster G.

### Belief revision (Cluster C, complementary to Codex's #18, #20, #23)

- **AGM `revise(state, ⊥)` returns the original state, silently violating K*2.** Postulate test escapes via `assume(_belief(a).is_consistent)`. Cluster C HIGH-1.
- **K*6, K*7, K*8 (contraction supplementaries) not tested.** Cluster C.
- **IC4 (fairness), Maj, Arb not tested.** Cluster C.
- **CR1-CR4 (DP semantic counterparts) not tested for `revise`.** Cluster C.
- **C1-C4 not tested for `lexicographic_revise` or `restrained_revise`.** Cluster C.
- **`ic_merge` distance cache keyed on `id(formula)`.** Eviction releases the strong ref, inviting `id` recycling. Cluster C.
- **`BeliefSet.all_worlds(alphabet)` is O(2^|alphabet|) on every revise call.** Cluster C.

### ATMS / world (complementary to Codex #24, #25, #26)

- **`is_stable`/`node_relevance`/`node_interventions` claim soundness over "all bounded futures" but check ≤8 subsets.** Unsound under-approximations presented as facts. Cluster E HIGH.
- **`_was_pruned_by_nogood` returns False on cycles.** Mis-classifies OUT_KIND, silently breaks intervention planning. Cluster E HIGH.
- **`_materialize_parameterization_justifications` silently drops non-numeric inputs.** Categorical claims invisible to derivation. Cluster E HIGH.
- **`max_iterations=10_000` raises instead of returning anytime result.** Cluster E.
- **Multi-consequent `consequent_ids` is dead generalization.** Cluster E.

### Worldline / hashing / Pearl

- **Hashing embeds exception reprs into the content hash.** Transient subsystem errors flip the hash. Cluster J HIGH.
- **`HypotheticalWorld` is NOT a Pearl do-operator.** Override claims compete via conflict resolution; parent edges to overridden concepts are never severed. Cluster J HIGH.
- **`json.dumps(..., default=str)` everywhere as canonical-hash basis.** Object reprs may embed memory addresses. Cluster J.
- **`worldline/argumentation.py:107-111` uses `len(extensions) == 1` only.** Multi-extension semantics silently discarded. Cluster J.

### Heuristic / classify / relate (Cluster H)

- **`relate.dedup_pairs` collapses bidirectional embedding distance to minimum.** Two embedding models' rankings of `(a,b)` and `(b,a)` collapse before LLM ever runs. Cluster H HIGH.
- **`classify.py:389` whole-response-as-forward fallback.** When LLM doesn't return bidirectional shape, fabricates a `{"type":"none","strength":"weak","note":"not classified"}` reverse. Cluster H HIGH.
- **`commit_stance_proposals` reads `commit_sha` after `with` block exits.** Cluster H + Cluster A.

### Merge

- **Cross-paper assertion-id collapse: `_semantic_payload` strips provenance** from the assertion-id hash. Two papers asserting the same statement collide; `_deduplicate_arguments` folds them. Cluster I HIGH.
- **Union-find sameAs collapse.** `_canonical_claim_groups` is transitive sameAs closure with no quality filter — Beek 2018 pathological algorithm. Cluster I HIGH.
- **`branch_a` wins on non-claim files** in merge. Asymmetric, untested. Cluster I.

### Provenance / source ingestion

- **Trusty URI verification unimplemented despite Kuhn 2014 citation.** `_sha_text` constructs `ni:///sha-1;...` URIs without computing or verifying any hash. Cluster M HIGH.
- **PROV-O coverage zero.** `prov:` namespace declared in JSON-LD context; no `prov:Activity`/`prov:Entity`/`prov:Agent` instances emitted. Cluster M HIGH.
- **`compose_provenance` alphabetically sorts `operations`** destroying causal ordering for PROV-O `wasInformedBy` chains. Cluster M.
- **`WhySupport.subsumes` named opposite of behavior.** Cluster M.

### CLI surface (complementary to Codex #38-40)

- **README documents commands that don't exist** (`pks promote`, `pks world atms-status`, etc.). Cluster K HIGH.
- **`docs/application-layer-and-undo.md` describes a fully-specified `propstore.application` package.** Package directory does not exist. Cluster K.
- **`pks web --host 0.0.0.0` exposes no-auth, no-CSRF, no-security-headers read-only knowledge browser to LAN.** Cluster K.
- **Web render-policy floats accept any float including NaN/inf.** `web/requests.py:58-69`. Cluster K.

### "Shim" inventory worth keeping

Per Q's "no old repos, iterating to perfection" rule these are now just `git rm` work:
- `_CONCEPT_STATUS_ALIASES = {"active": ACCEPTED}` (`core/concept_status.py:13-15`)
- `DecisionValueSource.CONFIDENCE_FALLBACK` (`world/types.py:1206`)
- `world/types.py:1275 # Fall back to raw confidence ... (old data)`
- `classify.py:389 # fallback: treat whole response as forward`
- `grounding/grounder.py:141-144 # backwards compatibility` block 3 of gunray refactor
- `pyproject.toml:65 propstore/aspic_bridge.py` (file doesn't exist; strict list dead)

## Section 4 — Combined critical priority list (top 30)

Ordered by *risk × cheapness × corroboration*. Items appearing in both reviews bubble to the top.

### Tier 1 — privacy/security/correctness (do first)

1. **Web render-policy bypass via direct claim URL.** Codex #8. Tests: integration tests asserting hidden claims return 404/403.
2. **Web render-policy bypass via neighborhoods/concept pages.** Codex #9, #10. Same fix shape.
3. **Hidden claim counts disclosed in concept aggregates.** Codex #10.
4. **`materialize` partial-overwrite on conflict.** Codex #1. Preflight conflict pass.
5. **Read-only sidecar opens write-capable mode first.** Codex #4. Connect with `query_only=ON` from the start.
6. **Test fixtures use a hand-written schema diverging from production.** Codex #7. Tests can pass against a schema production never creates — undermines the whole suite.

### Tier 2 — math/semantics correctness (corroborated or HIGH)

7. **C1 — Asymmetric stance via symmetric contradiction** (D-H2 / Codex #22). Both caught.
8. **C2 — AGM contraction collapses Spohn** (Cluster C HIGH-3 / Codex #23). Both caught.
9. **C3 — Micropub IDs not content-derived** (Cluster M HIGH-6 / Codex #3). Both caught.
10. **C4 — CEL ternary unsound** (Cluster G HIGH / Codex #30). Both caught.
11. **C5 — Nested `ist`/`proposition` schema-only** (Cluster B HIGH / Codex #35). Both caught.
12. **AGM `K*2` violated for ⊥** (Cluster C HIGH-1). Claude-only.
13. **`opinion.wbf` is aCBF, not WBF** (Cluster F + gaps.md HIGH). Claude-only.
14. **`decision_criterion="pignistic"` cites wrong author** (Cluster F + gaps.md HIGH). Claude-only.
15. **ASPIC grounded delegates to dung which ignores attacks** (Codex #12). Codex-only.
16. **`ideal_extension` returns union of admissible-maximals** (Cluster P). Claude-only — file upstream.
17. **`aspic_encoding._literal_id = repr(literal)` produces non-loadable ASP** (Cluster P). Claude-only.

### Tier 3 — silent collapse / non-commitment violations

18. **`relate.dedup_pairs` collapses bidirectional pairs** (Cluster H + gaps.md MED). Claude-only.
19. **`source/finalize.py` rewrites authored payloads in place** (Cluster A + gaps.md MED). Claude-only.
20. **`merge/_semantic_payload` strips provenance from assertion-id hash** (Cluster I HIGH). Claude-only.
21. **Union-find sameAs collapse with no quality filter** (Cluster I HIGH). Claude-only.
22. **Source/promote justification filter admits dangling refs** (Cluster A HIGH). Claude-only.
23. **Source/alignment defaults to `non_attack`** (Cluster A HIGH). Claude-only.

### Tier 4 — provenance gaps

24. **gunray boundary drops `DefeasibleTrace`/rule provenance** (Clusters B, D, M, R quadruple-corroborated; Codex didn't catch). Claude-only.
25. **Trusty URI verification unimplemented** (Cluster M HIGH / Codex #3 implies). Claude-emphasized.
26. **PROV-O coverage zero** (Cluster M HIGH). Claude-only.
27. **`storage/repository_import.py` no provenance annotation** (Cluster U). Claude-only.

### Tier 5 — pipeline determinism / atomicity

28. **SQLite-before-git in promote** (Cluster A HIGH + Cluster N HIGH). Claude-only.
29. **`build_repository` swallows `FileNotFoundError`** (Cluster N HIGH). Claude-only.
30. **`worldline/runner` hash flips on transient errors** (Cluster J HIGH). Claude-only.

## Section 5 — How to read Codex's workstreams alongside Claude's clusters

Codex's workstreams group findings by remediation order, not by code area. The mapping:

| Codex WS | Codex findings | Closest Claude clusters |
|---|---|---|
| ws-01 render-policy / read-only | #4, #8, #9, #10, #11 | K, N (sidecar query side) |
| ws-02 schema and test infra | #6, #7 | A, N |
| ws-03 storage/sidecar/identity | #1, #2, #3, #5 | A, M |
| ws-04 formal expressions / units / equations | #28, #29, #30, #31, #32, #33, #34 | G, Q, T |
| ws-05 contexts / publications / atms | #24, #25, #26, #27, #35, #36, #37 | B, E, M |
| ws-06 argumentation / belief / probability | #12–#23 | C, D, F, P |
| ws-07 cli / architecture / gates | #38, #39, #40 | K, U |

If an engineer wants TDD-shaped fix sequences, Codex's workstreams are the better starting document. If they want the precise file:line citations and paper-faithful gap analysis, Claude's clusters are the better starting document. Use both.

## Section 6 — What this cross-check revealed about the methodologies

**Codex's strength**: ran the test suite, ran pyright, ran lint-imports — verification on top of inspection. Reported a real test failure (`test_repository_artifact_boundary_gates`). Caught the test-vs-production schema divergence (#7) which is a methodology-finding-as-much-as-bug — a single-reviewer test of test infrastructure. Surfaced runtime-shape issues (SQLite mode, request-payload shape) that static inspection alone misses.

**Claude's strength**: 21 parallel cluster reports gave depth per code area; paper-faithful comparison flagged math-against-citation mismatches Codex didn't catch (`opinion.wbf`, `pignistic`, ideal-extension union, ASPIC narrowed-contrariness transposition); cross-package boundary analysis caught the `ast-equiv`/`gunray`/`quire`/`bridgman`/`argumentation` internal bugs Codex's propstore-centered review didn't drill into.

**Both blind to**: the stance-of-trust-calibration architecture leak (Layer 3 → Layer 1) was *Claude-only*. The `WorldModel`-naming-implies-commitment finding was *Claude-only*. The web direct-claim-URL leak was *Codex-only*. There is no single review methodology that catches everything; multi-reviewer is load-bearing.

**Disagreement count**: zero. The two reviews are entirely complementary — no place where one says "X is wrong" and the other says "X is fine." Where they overlap they agree; where they don't overlap they extend each other.

## Section 7 — Recommended action

1. Treat the Tier 1 (privacy + atomicity + schema) items as immediate; they are the cheap, high-confidence wins where Codex's inspection found things Claude's didn't.
2. Treat the Tier 2 corroborated items (C1–C5 above) as the next batch; both reviewers saw them.
3. For any tier-3+ item, cross-reference Codex's workstream that owns it (table above) and Claude's cluster file for the file:line citation.
4. Update `docs/gaps.md` to absorb the new findings from both reviews; many are not yet tracked there.
5. The "imports-are-opinions" structural blind spot at `storage/repository_import.py` (Claude-only) and the `WorldModel` test-fixture-vs-production-schema divergence (Codex-only) should both be added as workstreams of their own — they are class-of-bug findings, not point fixes.

The combined list is ~70 distinct findings. About a third are corroborated; the rest are unique to one reviewer. Use both.
