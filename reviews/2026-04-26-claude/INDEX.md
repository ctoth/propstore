# Deep review of propstore + dependencies — 2026-04-26

Reviewer: Claude (Opus 4.7, 1M-context). Twenty-one parallel subagent reports.
Method: each cluster scout/analyst/adversary read its scope independently, compared against the listed papers in `papers/<dir>/notes.md`, and wrote a per-cluster report.
Constraint: did not read existing `reviews/` files. Did not run tests. Did not modify code.

## How to read this

If you have ten minutes: read **§ Top 20 findings**.
If you have an hour: also read **§ Cross-cutting themes** and any cluster report whose theme matches today's intent.
If you are deciding what to fix this week: read **§ Action triage** and **§ Consolidated open questions for Q**.

## Coverage map — what each cluster did

| Cluster | Scope | Output | Headline |
|---|---|---|---|
| A | core/, storage/, source/, repository, uri, concept_ids | `cluster-A-core-storage-source.md` | 6 HIGH bugs in source-promote / alignment / micropub paths |
| B | claims, stances, predicates, rules, families/, grounding/ vs DeLP/contexts/micropubs/Trusty | `cluster-B-semantic-layer.md` | Two parallel claim shapes; lifting rules authored but only partially read; gunray boundary drops provenance |
| C | belief_set/ vs AGM/Darwiche/IC/AGM-AF papers | `cluster-C-belief-set-agm.md` | K*2 silently violated for ⊥; iterated contraction collapses entrenchment to 2 levels; many postulates untested |
| D | aspic_bridge/ + propstore consumption of `argumentation` pkg | `cluster-D-aspic-bridge.md` | Transposition closure runs against narrowed contrariness; rebuts always become contradictory; `_contraries_of` boundary leak |
| E | world/ATMS, conflict_detector/, support_revision provenance/nogoods | `cluster-E-atms-conflict.md` | Engine is global rebuild not Forbus incremental; `is_stable`/`node_relevance` claim soundness over "all bounded futures" but check ≤8 subsets |
| F | probabilistic_relations, praf/, opinion (subjective logic), sensitivity, fragility, calibrate | `cluster-F-probabilistic-subjective.md` | WBF clamp wrong; defeat-summary fabricates uncertainty; `from_probability(n=1)` shifts; OAT-only sensitivity; no Brier |
| G | cel_*, dimensions, units, equations, sympy, z3, ast-equiv usage | `cluster-G-cel-units-equations.md` | Ternary type-rule unsound; affine temperature wrong for deltas (~273 K silent error); equation comparison reports DIFFERENT for log/exp/sqrt true equivalences with no UNKNOWN |
| H | heuristic, proposals, classify, relate, semantic_passes (adversary) | `cluster-H-heuristic-proposals-adversary.md` | `derive_source_document_trust` writes heuristic output to source branch with no proposal gate; `dedup_pairs` collapses bidirectional disagreement |
| I | merge/structured_merge vs IC/sameAs/lenses | `cluster-I-merge.md` | Cross-paper assertion-id collapse strips provenance from semantic payload; regime-split disagreement equated as identity; union-find sameAs collapse |
| J | worldline/, support_revision/, context_lifting vs Pearl/Halpern/Spohn/Bonanno | `cluster-J-worldline-causal.md` | Hashing embeds exception reprs; `HypotheticalWorld` is not Pearl do-operator; Spohn/Halpern/circumscription/Reiter — absent |
| K | CLI, web/, app/, demo, observatory, contracts | `cluster-K-cli-web-app.md` | README documents commands that don't exist; `pks web --host 0.0.0.0` exposes no-auth knowledge browser; observatory "evaluator" performs no evaluation |
| L | families/ deep, parameterization*, structured_projection, sidecar/, forms | `cluster-L-families-parameterization.md` | ClaimDocument has two parallel encodings; `normalize_logical_value` does no case-folding; FormDefinition is mutable, module-level cached |
| M | provenance/, sidecar/, source ingestion, importing/, grounding (provenance angle) | `cluster-M-provenance-sources.md` | Trusty URI verification unimplemented; PROV-O coverage zero; grounded facts persist to sidecar without provenance; `WhySupport.subsumes` named opposite of behavior |
| N | compiler/, importing/, sources/ (text ingest), semantic_passes/, repository, epistemic_process | `cluster-N-compiler-importing.md` | `build_repository` swallows sidecar `FileNotFoundError`; `_normalize_concept_batch` silently overwrites on collision; SQLite-before-git ordering leaves orphan rows on git failure |
| P | `../argumentation` package — Dung semantics, ASPIC kernel, ABA, ADF, bipolar, weighted, ranking, gradual | `cluster-P-argumentation-pkg.md` | `ideal_extension` returns union of admissible-maximals (incorrect); `aspic_encoding._literal_id = repr(literal)` produces non-loadable ASP; ABA/ADF/Bench-Capon VAF entirely missing |
| Q | `../bridgman` (units / dim algebra) | `cluster-Q-bridgman.md` | `verify_equation` ignores extra rhs_terms; `dims_of_expr` raises TypeError on transcendentals which propstore swallows — equations involving sin/cos/exp/log silently pass dimensional check |
| R | `../gunray` (defeasible Datalog grounder) | `cluster-R-gunray.md` | `build_arguments` exponential per candidate; gunray→propstore evaluate path discards `DefeasibleTrace` (provenance loss); propstore re-grounds twice |
| S | `../quire` (git-backed artifact store) | `cluster-S-quire.md` | `canonical_json_sha256` and `contracts._normalize_payload` use different normalization rules; `expected_head` is opportunistic not transactional; CAS-failed commits leak orphans |
| T | `../ast-equiv` (canonical AST + sympy bridge) | `cluster-T-ast-equiv.md` | Identity elimination `x+0→x` has no type guard despite knowing `+` is overloaded; repeated-mult-to-power changes call counts; `compare()` swallows all exceptions |
| U | architecture, contracts, import-linter alignment vs project principles (adversary) | `cluster-U-architecture-adversary.md` | All four import-linter forbidden contracts are vacuously satisfied; the linter catches no current violation; six-layer claim is decorative |
| V | paper→code aggregate coverage of 42 high-value papers | `cluster-V-paper-coverage.md` | 134 paper-item rows; conspicuous absences: Pearl SCM, Halpern actual cause, Reiter, McCarthy circumscription, ADF, ABA, semi-stable, generalized specificity, PROV-O serializer, Bozzato CKR `ovr/instd` |

## Cross-cutting themes

These emerged from independent clusters reaching the same conclusion. Each is a class of failure, not a single bug.

### Theme 1 — Non-commitment principle has unscheduled, structural violations

The project's stated rule: never collapse disagreement in storage unless the user explicitly migrates. The reviews found this collapse in many places, all live:

- `relate.dedup_pairs` collapses bidirectional embedding distance to the minimum (H, U, gaps.md)
- `source/finalize.py` rewrites authored payloads in place (H, M, U, gaps.md)
- `merge/_semantic_payload` strips provenance/conditions/stances/context from the assertion-id hash, so two papers asserting the same statement collide; `_deduplicate_arguments` then folds them (I)
- `merge/_canonical_claim_groups` is union-find transitive sameAs closure with no quality filter — same algorithm as Beek 2018's pathological 177K-member conflation (I)
- `classify.py:389` silently treats whole LLM response as forward when the bidirectional shape isn't there (H, U)
- `world/types.py:1275` `CONFIDENCE_FALLBACK` enum forks render-time decisions on missing-opinion branch with no provenance (U)
- `support_revision/iterated.py` freezes entrenchment from the prior state instead of recomputing — chains diverge from one-shot revisions (J)
- `aspic_bridge` rules with inactive premise/conclusion claims are silently dropped (D, U, gaps.md)
- `worldline/argumentation.py:107-111` uses `len(extensions) == 1` only — multi-extension semantics silently discarded (J)

Most of these are MED in `gaps.md` and "not yet scheduled." The principle should not have unscheduled violations.

### Theme 2 — "Imports are opinions" enforced asymmetrically

Memory says: every imported KB row carries provenance, no source is privileged. Reviews found:

- `storage/repository_import.py` — zero `provenance` references in the cross-repo import path (U)
- `source/promote.py:745-758` mutates a provenance dict in-place; never constructs `Provenance`, never calls `compose_provenance`, never writes a git note (M)
- Grounded facts persist to sidecar without provenance — `GroundedRulesBundle` docstring claims "full provenance chain stays intact"; rehydration returns empty `source_rules`/`source_facts` (M)
- `derive_source_document_trust` writes a `prior_base_rate: float` into source storage with no operation tag, no agent, no model version, no commit-of-knowledge — and the rest of the codebase carries Jøsang opinions everywhere else (H)
- Embeddings stored in sidecar are not provenanced as model-opinions — typo'd model name silently registers a new "model" (H, U)
- gunray→propstore evaluate path discards `DefeasibleTrace`; rule-id back-pointers do not survive (R, M)
- propstore→gunray translator flattens `RuleDocument`/`AtomDocument` to surface strings; only `Rule.id` survives (R)

Two clusters confirmed cluster B's original "claim provenance dropped at the gunray boundary" suspicion (D, R, M).

### Theme 3 — Architecture is decorative; the linter watches none of it

`U` produced the strongest finding here, but it was independently corroborated:

- All four `forbidden` contracts in `.importlinter` are vacuously satisfied — they catch zero current imports (U)
- The README's six layers are not encoded as a `layered` contract (U)
- The "test" of import-linter only asserts return-code zero on the current state — no negative test injects a known violation (U)
- Heuristic logic lives at the *top level* of `propstore/`: `embed.py`, `classify.py`, `relate.py`, `calibrate.py`. The package `propstore/heuristic/` contains exactly two files (U, H)
- `sidecar/build.py` (storage compiler) imports `propstore.embed` (heuristic). `world/model.py` (render) imports `propstore.embed`. The architecture diagram in README is materially false on this layout (U)
- `derive_source_document_trust` (heuristic) returns a mutated SourceDocument that is then committed to the source branch in the same transaction as `attach_source_artifact_codes` — Layer 3 mutates Layer 1 in production (H, U)
- `pyproject.toml:65` lists `propstore/aspic_bridge.py` in pyright `strict` — file does not exist; entry silently does nothing; suggests strict list is not exercised in CI (U)

### Theme 4 — Math is wrong in subjective-logic / decision-criterion / dimensions

Several clusters independently flagged math that is provably divergent from the cited paper:

- `opinion.wbf()` named WBF but computes aCBF; worked example drifts 0.175 absolute on uncertainty (F, U, gaps.md HIGH)
- `decision_criterion="pignistic"` cited Denoeux but formula is Jøsang's `b + a·u` (F, U, gaps.md HIGH)
- `from_probability(n=1)` shifts in F's reading (F)
- `enforce_coh` divergence from Jøsang (F)
- `dims_of_expr` raises `TypeError` on transcendentals; propstore swallows the TypeError so any equation with sin/cos/exp/log silently passes dimensional check (Q, G)
- Affine temperature units treated as linear for deltas — silent ~273 K errors (G)
- CEL ternary type-rule unsound (no two-branch type equality check) (G)
- Equation comparison reports DIFFERENT for log/exp/sqrt true equivalences with no UNKNOWN state (G)
- `ideal_extension` returns union of admissible-maximal candidates; admissibility isn't closed under union (P)
- `ic_merge` distance cache keyed on `id(formula)` — eviction releases the strong ref, inviting `id` recycling (C)

### Theme 5 — Silent failure paths everywhere

- `build_repository` swallows `FileNotFoundError` from sidecar build; reports success indistinguishable from "empty repo" (N)
- `_normalize_concept_batch` silently overwrites on key collision; sibling `_normalize_claim_batch` warns — inconsistent (N)
- Promote pipeline commits SQLite *before* the git `transact` block — git failure leaves orphan sidecar rows (N, A)
- Source-promote: justification filter admits dangling refs (A)
- Sidecar-before-git PK collision risk (A, S)
- Alignment classifier defaults to `non_attack` rendering the AF inert (A)
- Alias collisions silently merge (A, L)
- Micropubs silently dropped for context-less claims (A)
- ATMS engine `_was_pruned_by_nogood` returns False on cycles, mis-classifying OUT_KIND and silently breaking intervention planning (E)
- ATMS `is_stable` / `node_relevance` claim soundness over "all bounded futures" but check ≤8 subsets — unsound under-approximations presented as facts (E)
- `worldline.runner` flips content hash on transient subsystem errors and embeds exception reprs into the hash (J)
- `compare()` in ast-equiv swallows all exceptions in three tiers via bare `except Exception` (T)
- `ASPICQueryResult.arguments_against` only collects conclusion-level contraries; misses undercut and undermine attackers entirely (D)

### Theme 6 — Boundary leaks across repos

- `propstore/aspic_bridge/query.py:13` imports `_contraries_of` (private kernel symbol from `argumentation`) — boundary violation per `docs/argumentation-package-boundary.md` (D)
- propstore reaches past quire's `__init__.__all__` into `quire.artifacts.*`, `quire.contracts.*`, `quire.refs.*` (S)
- propstore keeps three duplicate `_canonical_json` implementations (`observatory.py:34`, `policies.py:42`, `epistemic_process.py:50`) that do not import from `quire.hashing` (S)
- gunray's `closure.py` is propositional-only (zero arity); ARCHITECTURE.md drift (R)
- bridgman: `dims_of_expr` likely dead-imported at `families/concepts/passes.py:19` — only `verify_expr` is invoked (Q)

## Top 20 findings

Ranked by *risk × cheapness to fix*. Numbered for triage discussion.

1. **`derive_source_document_trust` writes Layer-3 output to Layer-1 storage with no proposal gate** — `app/sources.py:191-200,505-516` → `source/finalize.py:178-185`. Direct architecture violation. (Cluster H, U)
2. **`relate.dedup_pairs` collapses mirror-pair embedding distance to minimum** — `relate.py:67-74`. Non-commitment violation. Also `classify.py:389` whole-response-as-forward fallback. (H, U)
3. **`opinion.wbf()` is algebraically aCBF, not WBF** — gaps.md HIGH, scheduled WS-Z-types but still open. (F, U)
4. **`decision_criterion="pignistic"` cites Denoeux but formula is Jøsang's `b + a·u`** — same workstream. User-visible flag name is wrong. (F, U)
5. **`dims_of_expr` raises TypeError on transcendentals; propstore swallows** — sin/cos/exp/log equations silently pass dimensional check. (Q, G)
6. **Affine temperature units treated as linear for deltas** — ~273 K silent errors. (G)
7. **`equation_comparison` reports DIFFERENT for log/exp/sqrt true equivalences with no UNKNOWN state** — confidence-killer for any equation surface. (G)
8. **CEL ternary type-rule unsound (no two-branch type equality check)** — type system is unsound. (G)
9. **Promote commits SQLite before git `transact`; git failure leaves orphan sidecar rows** — `source/promote.py:573` vs `:849`. (N, A)
10. **`build_repository` swallows sidecar `FileNotFoundError` and returns success** — `compiler/workflows.py:609-616`. (N)
11. **`ASPICQueryResult.arguments_against` misses undercut and undermine attackers entirely** — `aspic_bridge/query.py:99-107`. Only conclusion-level contraries. (D)
12. **`aspic_bridge` transposition closure runs against narrowed contrariness; system.contrariness keeps the full relation** — strict-rule set no longer closed under transposition w.r.t. attack contrariness; Modgil 2014 §4.2 consistency theorem no longer guaranteed. (D)
13. **`ASP encoding` `_literal_id = repr(literal)` produces strings like `~p` and `p(1, 2)` that aren't valid ASP** — Lehtonen-2024 fact encoding can't actually be loaded into clingo. (P)
14. **`ideal_extension` returns union of admissible-maximal candidates; admissibility isn't closed under union** — wrong-result bug in the kernel. (P)
15. **AGM `revise(state, ⊥)` returns the original state unchanged, silently violating K*2** — postulate test escapes via `assume(_belief(a).is_consistent)`. (C)
16. **AGM `full_meet_contract` rebuilds Spohn state via `from_belief_set`, destroying entrenchment** — iterated contractions degenerate to a 2-level ranking. (C)
17. **ATMS `is_stable`/`node_relevance` claim soundness over "all bounded futures" but check ≤8 subsets** — unsound under-approximations presented as facts. (E)
18. **`HypotheticalWorld` is NOT a Pearl do-operator** — override claims compete via conflict resolution; parent edges to overridden concepts are never severed. (J)
19. **Trusty URI verification unimplemented despite Kuhn 2014 citation** — `_sha_text` constructs `ni:///sha-1;...` URIs without computing or verifying any hash. (M)
20. **All four import-linter `forbidden` contracts are vacuously satisfied** — replace with `layered`; add a negative test injecting a known violation. (U)

Honourable mentions (any one of these would be top-20 in a smaller review):

- `merge/_semantic_payload` strips provenance from assertion-id, collapsing cross-paper corroboration (I)
- `quire`'s `canonical_json_sha256` vs `contracts._normalize_payload` use different normalization rules in the same package (S)
- `worldline.runner` content hash flips on transient subsystem errors and embeds exception reprs (J)
- `gunray.build_arguments` exponential per candidate (R)
- `_normalize_concept_batch` silently overwrites on key collision (N)
- ast-equiv `WhileToForNormalizer` ignores `break`/`continue` and accepts non-int init values; canonicalized `for` would behave differently from original `while` (T)
- `aspic_bridge` rebuts always become contradictory; if `rebuts(a,b)` and `undermines(b,a)` both authored, the `undermines` directionality is silently lost (D)
- `web` accepts NaN/inf/out-of-range floats at the request boundary (`web/requests.py:58-69`) (K)
- `pks web --host 0.0.0.0` exposes no-auth, no-CSRF knowledge browser to LAN (K)

## Action triage

**Bugs that should be fixed this week** (HIGH severity, small blast radius, no design churn):
- 9 (promote SQLite-before-git ordering): wrap in correct order
- 10 (build_repository swallow): re-raise or aggregate to diagnostic
- 4 + 3 + 6 (math/naming): pick the operator name to match the math, or fix the math; rename `pignistic` flag if Jøsang
- 11 (arguments_against): broaden to undercut + undermine attackers
- 15 + 16 (AGM): K*2 escape; full_meet entrenchment loss

**Architectural items that need a Q decision before fixing**:
- 1 (heuristic→source via trust calibration): Q1 in cluster H — proposal-gate trust calibration, or exempt it explicitly?
- 20 (vacuous import-linter): convert to `layered` contract over six README layers — needs Q sign-off on layer ordering
- Theme 1 globally: rule the unscheduled non-commitment violations in or out

**Items that need a research/spec spike**:
- 5, 7, 8 (CEL/dimensions soundness): Pierce-style operational semantics + Kennedy units before patching
- 17 (ATMS bounded-replay soundness): decide whether to replace or rename
- 18 (Pearl do-operator): commit to actual SCM intervention or rename the type

**Items to add to `gaps.md`** (newly discovered, not currently tracked):
- All four backwards-compat shims surfaced by U (grounder.py:141-144, classify.py:389, world/types.py:1275 CONFIDENCE_FALLBACK, core/concept_status.py:13-15 _CONCEPT_STATUS_ALIASES)
- `pyproject.toml:65 aspic_bridge.py` strict-list dead entry
- `storage/repository_import.py` zero-provenance surface
- Negative-test gap for `lint-imports`
- Theme 2 imports-are-opinions structural blind spot at cross-repo import surface

## Consolidated open questions for Q

I won't reproduce every cluster's open Q — read each report's "Open questions for Q" section. The questions I rank as *most worth answering first* (they unblock multiple clusters):

1. **Is heuristic→source mutation via `derive_source_document_trust` an architectural commitment or an oversight?** (H, U) — answer drives a refactor or a documented carve-out.
2. **Is "old data" support a project commitment?** Multiple shims (`CONFIDENCE_FALLBACK`, `_CONCEPT_STATUS_ALIASES`, `world/types.py:1275`) are carrying it implicitly; `AGENTS.md:21-22` forbids this without explicit declaration. (U) — once decided, either delete in one pass or document the exception.
3. **What ASPIC+ flavor is propstore committing to?** Restricted vs unrestricted rebut, last-link vs weakest-link, Pareto vs lex preference — the bridge currently picks none. (D)
4. **What probabilistic-AF semantics is `praf/` committing to?** Constellation, epistemic, monotonic — paper-faithful needs to commit. (F, P)
5. **Pearl do-operator?** `HypotheticalWorld` is named/used as if it were one; the implementation isn't. Either rename or implement. (J)
6. **Does `WorldModel` need to become `WorldQuery` / `WorldSurface`?** The singular noun forecloses the multi-extension reality. (U, J)
7. **Cross-repo import provenance — exempt or required?** `storage/repository_import.py` carries no provenance today. (U, M)
8. **Should the import-linter contracts move from `forbidden` (4 narrow) to `layered` (six README layers)?** With a negative test gating CI. (U)
9. **What `gaps.md` discipline?** Line numbers are stale (`world/types.py:1064-1066` cited; actual `:958-959` and `:1257-1259`). Regenerate per release, or accept drift? (U)
10. **Trusty URI: implement (Kuhn 2014) or stop citing?** (M, B, V)
11. **PROV-O serializer: build (Moreau 2013) or drop the prefix?** (M, V)
12. **DeLP generalized specificity / proper-vs-blocking defeater split: keep aspirational or implement (Garcia 2004)?** (B, V, R)
13. **Bozzato CKR `ovr/instd` predicates: keep aspirational or implement?** (B, V)
14. **Subjective-logic operator-name ↔ formula audit:** if `wbf()` and `pignistic` are wrong, what else is? (F, gaps.md)
15. **Should `ideal_extension` (argumentation pkg) be filed upstream as a bug, or wrapped in propstore?** (P)

## Reading order recommendation

For each role, the report set to read first:

- **Architect / refactor planner**: U → H → I → V (top-10 leverage list).
- **Bug-fixer this week**: A → N → D → C → F.
- **Math / soundness**: G → F → P → C → T.
- **Provenance / ingestion**: M → B → R → S.
- **CLI / web / app surface**: K → L → S.
- **Dependency owner (argumentation pkg)**: P, then D as the consumer view.
- **Dependency owner (gunray, quire, bridgman, ast-equiv)**: R, S, Q, T respectively.

## Methodology notes

- Foreman discipline: parent dispatched, did not edit code; parent's tool calls were reviews-dir creation, enumeration, and writing two adversary reports whose subagents lacked Write.
- Each subagent received: explicit file scope, explicit paper list to read, output path, length cap, no-tests/no-edit/no-other-reviews constraint.
- Worktree isolation NOT used (per memory `feedback_worktrees_research`).
- Subagents were dispatched in three waves (8 + 6 + 7 = 21) with one continuation message after a hook misinterpretation paused cluster H.
- Two adversary subagents (H, U) lack Write tool — their reports were captured from message bodies and written by the parent.
- Coverage gap: papers that lack a `notes.md` (some Pierce/Kennedy/Knuth/Sensoy entries) were flagged as workflow gap (V); cluster G found this for its slice and worked from PDFs/abstracts. The `paper-reader` workflow needs to backfill those notes for future paper-faithful reviews to function.

## Files in this review

```
reviews/2026-04-26-claude/
├── INDEX.md                                    (this file)
├── cluster-A-core-storage-source.md
├── cluster-B-semantic-layer.md
├── cluster-C-belief-set-agm.md
├── cluster-D-aspic-bridge.md
├── cluster-E-atms-conflict.md
├── cluster-F-probabilistic-subjective.md
├── cluster-G-cel-units-equations.md
├── cluster-H-heuristic-proposals-adversary.md
├── cluster-I-merge.md
├── cluster-J-worldline-causal.md
├── cluster-K-cli-web-app.md
├── cluster-L-families-parameterization.md
├── cluster-M-provenance-sources.md
├── cluster-N-compiler-importing.md
├── cluster-P-argumentation-pkg.md
├── cluster-Q-bridgman.md
├── cluster-R-gunray.md
├── cluster-S-quire.md
├── cluster-T-ast-equiv.md
├── cluster-U-architecture-adversary.md
└── cluster-V-paper-coverage.md
```

Total: ~580 KB of review across 21 reports.
