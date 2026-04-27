# Claude cross-check synthesis

Compared against `reviews/2026-04-26-claude/INDEX.md` and cluster reports A-V. I read the Claude index in full and checked the cluster reports for concrete overlap/delta evidence by cluster and literal finding searches. This synthesis answers two questions:

1. What did Claude catch that Codex missed or underweighted?
2. What did Codex catch that Claude missed or contradicted?

## Bottom line

Claude caught a larger architecture/provenance/source-ingestion failure class than Codex did. Codex caught several concrete web/render-policy, sidecar-readonly, schema-validation, and materialize-atomicity bugs that Claude either did not flag or explicitly marked as acceptable.

The existing Codex workstream order is still mostly right, but it needs two amendments:

- Add a new early source/import/provenance stream between current WS-03 and WS-05, or expand WS-03 substantially.
- Expand WS-06 and WS-07 with Claude's dependency-kernel and architecture-linter findings before starting semantic repairs.

## Major Claude findings Codex missed

### Source promotion, import, and provenance

Claude's strongest additions are in source/import paths. Codex covered branch-head CAS and some sidecar identity issues, but missed several direct corruption paths:

- `propstore/source/promote.py:711-727`: justification filtering can promote justifications whose conclusion/premises exist only in the source-branch index, leaving dangling master refs.
- `propstore/source/promote.py:840-851` plus `:518-548`: sidecar mirror writes happen before the git transaction; a git failure can leave orphaned sidecar rows that poison retry. Codex had branch-head CAS but did not catch SQLite-before-git ordering.
- `propstore/source/alignment.py:96-98`: concept alignment defaults to `non_attack`, making the alignment AF accept alternatives by default and hide conflict.
- `propstore/source/registry.py:42-47`: alias collisions keep the first artifact ID through `setdefault`, silently rewriting later concepts to the first one.
- `propstore/source/finalize.py:213-217`: micropubs are silently skipped for claims without context instead of failing finalize.
- `propstore/storage/repository_import.py`: Claude reports no provenance annotation surface for cross-repo imports. Codex did not catch this "imports are opinions" violation.

Workstream impact: add these to WS-03 or create a new WS-03b `source-import-provenance.md`. These should be fixed before context/publication work because they affect what reaches master and sidecar.

### Heuristic/proposal non-commitment violations

Claude found a class Codex mostly missed:

- `derive_source_document_trust` writes heuristic trust output to source storage with no proposal gate.
- `relate.dedup_pairs` collapses bidirectional embedding distances by `frozenset({a,b})` and keeps the minimum.
- `classify.py` falls back to treating the whole LLM response as forward when bidirectional shape is missing.
- Embedding/model outputs are stored as sidecar facts without opinion/provenance discipline.

Codex caught an embedding model-key collision, but not the broader heuristic-as-storage and non-commitment issue. These belong in WS-07 architecture plus WS-03 identity/provenance.

### Subjective logic and decision math

Codex caught raw confidence becoming dogmatic evidence, PrAF calibration deletion, DF-QuAD asymmetry, and cyclic/non-routed semantics. Claude caught additional math problems:

- `opinion.wbf()` is named WBF but implements aCBF-like behavior.
- `decision_criterion="pignistic"` is user-facing Denoeux-labeled terminology but computes Jøsang expectation `b + a*u`.
- `from_probability(p, n=1, a)` shifts expectation toward the base rate; the hard-coded `n=1` makes confidence semantics misleading.
- `enforce_coh()` non-convergence should be an error/result, not silently returned partial enforcement.
- No Brier/calibration scoring and no Hunter/Thimm postulate verifier.

Workstream impact: WS-06 should explicitly include the WBF/pignistic audit and a subjective-logic operator-name-to-formula test matrix.

### Dimensions, equations, and ast-equiv internals

Codex caught raw unit comparison, global Z3 guards, ternary typing, equation orientation, RHS-only SymPy generation, and `ast-equiv` SymPy equivalence treated as conflict. Claude caught more:

- Bridgman `dims_of_expr` raises `TypeError` on transcendentals; propstore can swallow this, letting sin/cos/exp/log equations pass dimensional checks.
- Affine temperature units are treated as linear for deltas, creating silent ~273 K errors.
- Equation comparison reports `DIFFERENT` for true log/exp/sqrt equivalences instead of `UNKNOWN`.
- `ast-equiv` identity elimination such as `x + 0 -> x` lacks type guards despite overloaded `+`.
- `ast-equiv` repeated-multiplication-to-power can change call counts/side effects.
- `ast-equiv.compare()` swallows broad exceptions across tiers.

Workstream impact: WS-04 should add a "dependency semantics" subsection for bridgman and ast-equiv soundness, not just propstore call-site fixes.

### ASPIC and argumentation package kernel

Codex caught advertised/unrouted ASPIC semantics, attack-conflicting grounded ASPIC, missing complete surfaces, and asymmetric stances through contradiction. Claude caught additional ASPIC/kernel bugs:

- `ASPICQueryResult.arguments_against` only collects conclusion-level contraries; it misses undercut and undermine attackers.
- Transposition closure runs against narrowed contrariness while `system.contrariness` keeps the full relation, undermining Modgil consistency theorem assumptions.
- `aspic_bridge` rebuts always become contradictory; directionality can be lost when mixed with undermines.
- `argumentation` package `ideal_extension` returns a union of admissible-maximal candidates even though admissibility is not closed under union.
- ASP encoding `_literal_id = repr(literal)` produces strings that are not valid ASP for clingo.
- ABA, ADF, Bench-Capon VAF, and several semantics are absent despite nearby paper coverage.

Workstream impact: WS-06 should split propstore-bridge fixes from dependency-kernel fixes. Some tests must land in `../argumentation` first.

### AGM, ATMS, worldline, and causal surfaces

Codex caught IC infinite-distance dropping, no-stable-extension vs empty stable extension, Spohn-state collapse, worldline merge-parent detection, derived nogoods, context-bearing ATMS serialization, and raw-CEL ATMS support. Claude caught additional gaps:

- AGM `revise(state, bottom)` silently violates K*2 by returning original state; tests escape via `assume`.
- `ic_merge` distance cache keyed on `id(formula)` risks id recycling after cache eviction.
- ATMS `is_stable` and `node_relevance` claim "all bounded futures" but check at most 8 subsets.
- `_materialize_parameterization_justifications` silently drops non-numeric provider values.
- `HypotheticalWorld` is not a Pearl do-operator; overrides compete through conflict resolution and parent edges are not severed.
- `worldline.runner` content hash changes on transient subsystem errors and embeds exception reprs.

Workstream impact: WS-06 should include K*2, cache-key soundness, bounded-future claims, and the Pearl naming/implementation decision.

### Trusty URI, PROV-O, gunray, quire

Codex caught micropub content identity and semiring projection too early. Claude added important dependency/provenance issues:

- Trusty URI verification is effectively unimplemented despite Kuhn citations.
- PROV-O export coverage is zero despite provenance records having enough data.
- Grounded facts persist to sidecar without provenance; gunray traces are discarded at propstore boundaries.
- `gunray.build_arguments` is exponential per candidate and propstore can re-ground twice.
- quire `canonical_json_sha256` and contract normalization rules differ.
- quire expected-head handling and object writes can leak orphan objects on CAS/commit failures.

Workstream impact: WS-05 should add provenance interoperability/trusty verification; WS-03 should add quire/sidecar transaction-orphan tests.

### CLI/web/docs additions

Codex caught hidden-claim/render-policy leaks. Claude caught different web/CLI issues:

- `pks web --host 0.0.0.0` exposes a no-auth knowledge browser to the LAN with no warning/opt-in/security headers.
- `web/requests.py` accepts NaN/inf/out-of-range floats.
- README/CLI docs list commands or workflows that do not exist or are stale.
- `pks materialize` CLI does not validate target containment before `--clean`.

Workstream impact: WS-01 should add host exposure warning/opt-in and float-boundary tests; WS-07 should include doc/CLI command existence gates.

## Codex findings Claude missed or contradicted

### Render-policy data leaks

Codex found:

- direct hidden claim access via `/claim/{id}` and `/claim/{id}.json`
- hidden supporter/attacker leakage through neighborhood routes
- concept hidden-count/type-distribution leakage
- malformed concept FTS 500 boundary

Claude's web cluster focused on no-auth LAN exposure, docs, request parsing, and XSS. I did not find the direct hidden-claim/neighborhood/concept-count leaks in Claude's reports.

### Materialize conflict atomicity

Codex found `propstore/storage/snapshot.py:201-216` writes non-conflicting files before raising a conflict for later files. Claude found related materialize/path-clean issues, but not this refused-conflict partial-write bug.

### Read-only sidecar query mutates before query-only

Codex found that `query_sidecar` opens through shared setup that sets WAL before `PRAGMA query_only=ON`. Claude explicitly called `pks sidecar query` acceptable/read-only because it saw `query_only=ON`, so this is a direct Codex catch over a Claude false negative.

### Embedding model-key collision

Codex found `_sanitize_model_key` collapses distinct model names (`a/b`, `a-b`, `a_b`, `a b`) into the same SQL table/status key. Claude discussed embedding provenance and typo registration, but not this SQL identity collision.

### Sidecar semantic cache invalidation

Codex found `_sidecar_content_hash` includes only schema version and source revision, not compiler/pass/family semantic versions. I did not find this in Claude's reports.

### Required schema validation and duplicate test schema

Codex found:

- `WorldModel` required-schema validation misses lifecycle/quarantine columns it later selects.
- tests use a duplicate hand-written schema that diverges from production.

Claude's architecture cluster mentions reading `tests/conftest.py`, but I did not find these concrete schema-validation/test-schema findings in Claude's report set.

### Unit-normalized conflict detector path

Codex found the main conflict detector path compares raw values because canonical units/forms are not threaded through `ConflictClaim`. Claude found broader unit/dimension issues, but I did not find this exact `200 Hz` vs `0.2 kHz` main-path conflict bug.

### Z3 division guard scoping

Codex found division guards are globally conjoined, changing `||` and ternary semantics. Claude found CEL ternary and temporal/Z3 issues, but I did not find this exact global-guard bug.

### Nested `ist` semantic pipeline, duplicate canonical names, invalid form kind

Codex found nested `ist` is document-schema-only, duplicate `canonical_name` is warning/first-wins, and invalid form kind defaults to quantity. Claude caught parallel claim encodings and related family issues, but the Codex specifics remain useful and should stay in WS-05.

## Overlap: both reviews independently support these fixes

These should be considered high-confidence:

- Micropub identity/context problems.
- Sidecar/git transaction ordering problems around source promotion.
- ASPIC bridge semantics are materially incomplete/unsound.
- PrAF/subjective-logic semantics need a full audit, not local patching.
- IC merge infinite-distance behavior is wrong or at least undocumented.
- AGM/Spohn revision surfaces lose required epistemic structure.
- ATMS support/nogood reporting is not faithful to the claimed structures.
- Architecture gates are too weak; import-linter currently gives false confidence.
- Dependency boundaries are leaky; propstore depends on private or unstable symbols in sibling packages.

## Revised workstream amendments

### Add WS-03b: source/import/provenance non-commitment

Place after WS-03 and before WS-05.

First failing tests:

- source promotion with stale/source-only justification refs must fail before master commit
- git transaction failure after sidecar mirror write must not leave poison sidecar rows
- alias collision in source registry must hard-fail, not first-wins
- alignment of two conflicting concepts with different names must produce an attack/review-required state, not default `non_attack`
- `derive_source_document_trust` must produce a proposal object, not mutate source branch storage
- repository import must write provenance/opinion metadata for imported rows

### Amend WS-04

Add tests for:

- sin/cos/exp/log dimensional validation failures are not swallowed
- affine temperature delta conversion is not treated as linear absolute conversion
- log/exp/sqrt equivalences return equivalent or unknown, not false different
- ast-equiv canonical rewrites are type/effect safe or rejected
- broad exceptions in ast-equiv compare are surfaced as unknown/error, not swallowed

### Amend WS-06

Add tests for:

- WBF/aCBF formula-name conformance
- pignistic vs Jøsang expectation naming
- AGM K*2 on bottom
- `ideal_extension` admissibility in `../argumentation`
- ASPIC query `arguments_against` includes undercut/undermine
- transposition closure uses the same contrariness relation as the argumentation system
- `HypotheticalWorld` either implements Pearl do-intervention or is renamed/re-scoped
- ATMS bounded-future APIs stop claiming exhaustive stability when capped

### Amend WS-07

Add gates for:

- import-linter contracts must be non-vacuous; include at least one negative fixture/test
- README/docs command references must map to real commands/modules
- no compatibility shims/fallback aliases unless an explicit old-data support decision exists
- `pyproject.toml` strict-file entries must point to existing files

## Priority changes

The most important ordering correction from Claude is this:

1. Keep WS-01 first for data leaks and read-only mutation.
2. Keep WS-02 second for test/schema truth.
3. Run WS-03 storage identity, then new WS-03b source/import/provenance.
4. Only then proceed to WS-05 contexts/publications and WS-06 semantics.

Rationale: source/import/provenance bugs determine what knowledge enters the store. If those paths silently collapse, accept, or orphan claims, paper-semantic repairs downstream will be tested against corrupted inputs.
