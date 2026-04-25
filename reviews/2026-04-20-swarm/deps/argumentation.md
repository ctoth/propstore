# Argumentation dependency review — 2026-04-20

Scope: `C:/Users/Q/code/argumentation/src/argumentation/` as a dep of propstore.
Consumers: `propstore.aspic_bridge.*`, `propstore.core.analyzers`, `propstore.defeasibility`,
`propstore.praf.engine`, `propstore.fragility_scoring`, `propstore.merge.*`,
`propstore.worldline.argumentation`, `propstore.source.alignment`,
`propstore.structured_projection`, `propstore.grounding.*`.

Method: read source and tests; cross-check with Dung 1995, Modgil & Prakken 2018,
Cayrol & Lagasquie-Schiex 2005, Baumann 2015, Li 2012, Freedman 2025. Did not
re-run tests.

## API Contract Issues

### `af_revision.AFChangeKind.RESTRICTIVE` / `QUESTIONING` are dead enum members
- File: `C:/Users/Q/code/argumentation/src/argumentation/af_revision.py:21-28` and `186-198`.
- Summary: `AFChangeKind` declares seven cases (`DECISIVE`, `RESTRICTIVE`, `QUESTIONING`, `DESTRUCTIVE`, `EXPANSIVE`, `CONSERVATIVE`, `ALTERING`). `_classify_extension_change` can only ever return five of them — `RESTRICTIVE` and `QUESTIONING` are never produced. The README advertises the full seven-way enum to consumers.
- Severity: medium. Consumers that `match`-dispatch on the enum will have dead branches they falsely believe are reachable (`cayrol_2014_classify_grounded_argument_addition` is used nowhere in propstore today, but the surface promises are wrong).
- Fix: either add the missing classification branches per Cayrol, de Saint-Cyr, Lagasquie-Schiex 2014 (their paper defines all seven and gives exact decision criteria), or drop the unreachable enum cases so the typed surface matches reality.

### `preference.strictly_weaker` vs `aspic._strictly_weaker` are two different APIs
- Files: `preference.py:47-64` (public, float vectors) and `aspic.py:1155-1230` (module-private, Argument objects).
- Summary: Two name-clashing strictness comparators with incompatible signatures. The public one takes `list[float]` strength vectors; the private one takes `Argument` pairs and a `PreferenceConfig`. Consumer propstore (`core/analyzers.py`) uses `defeat_holds` from `preference.py` (float API) while `aspic_bridge/build.py` uses the full `compute_defeats` path (Argument API). Works, but the two drifts are easy to conflate.
- Severity: low. Documentation hazard.
- Fix: rename one of them, or document clearly that two tiers exist (float shortcut vs structural ASPIC+).

## Consumer Drift (propstore → argumentation)

No symbol-level drift detected. Every propstore import resolves to an exported name:

| propstore file | symbols | argumentation module | resolves? |
|---|---|---|---|
| `aspic_bridge/build.py` | `Argument, ArgumentationSystem, CSAF, ContrarinessFn, GroundAtom, KnowledgeBase, Literal, PreferenceConfig, Rule, build_arguments, compute_attacks, compute_defeats, transposition_closure` | `argumentation.aspic` | yes |
| `aspic_bridge/translate.py` | `ContrarinessFn, GroundAtom, KnowledgeBase, Literal, PreferenceConfig, Rule`, `strict_partial_order_closure` | aspic + preference | yes |
| `aspic_bridge/query.py` | `Argument, Attack, ContrarinessFn, GroundAtom, Literal, build_arguments_for, conc, compute_attacks, compute_defeats` | aspic | yes |
| `aspic_bridge/grounding.py` | `GroundAtom, KnowledgeBase, Literal, Rule, Scalar` | aspic | yes (`Scalar` is a `TypeAlias` on aspic.py line 22) |
| `core/analyzers.py` | `BipolarArgumentationFramework, cayrol_derived_defeats`, `ArgumentationFramework`, `defeat_holds`, `extensions` | bipolar + dung + preference + semantics | yes |
| `defeasibility.py` | `Argument, CSAF, conc`, `ArgumentationFramework` | aspic + dung | yes |
| `fragility_scoring.py` | `ArgumentationFramework, grounded_extension`, `ProbabilisticAF`, `compute_dfquad_strengths` | dung + probabilistic + probabilistic_dfquad | yes |
| `praf/engine.py`, `worldline/argumentation.py` | `compute_probabilistic_acceptance`, `ProbabilisticAF`, etc. | probabilistic | yes (needs manual verification of exact symbols — only grepped module-level imports) |
| `merge/*`, `source/alignment.py`, `structured_projection.py` | `PartialArgumentationFramework`, `enumerate_completions`, `credulously_accepted_arguments`, `skeptically_accepted_arguments` | partial_af | yes |

Positive note: `__init__.py` only re-exports submodules, not symbols — propstore always imports through qualified paths. This keeps the contract surface stable. No star imports.

### Type-level surface that callers depend on
- `argumentation.aspic.Scalar` is a `TypeAlias = str | int | float | bool` and is re-imported in propstore (`propstore/sidecar/rules.py:66`, `grounding/bundle.py:45`, `grounding/grounder.py:55`, `core/literal_keys.py:17`). Any future narrowing (e.g. dropping `bool`) would break all grounding sidecars. File it as load-bearing contract.

### `ArgumentationFramework.attacks` is `None`-able
- Consumer `aspic_bridge/build.py:191-195` always supplies an explicit `attacks` frozenset when building the CSAF framework. Consumer `claim_graph.py:14`, `defeasibility.py:21` may construct frameworks without it. Mixed usage is legal per docstrings but the implicit fallback semantics (CF falls back to defeats) affects answer sets silently — see "Silent Failures" below.

## Dung/ASPIC+ Correctness

### Attack-vs-defeat split is not uniformly applied in stable extensions
- File: `dung.py:293-322` (brute) and `dung_z3.py:138-181` (Z3).
- Summary: Stable extension is defined as "conflict-free and defeats every outsider". The code uses `framework.attacks` for conflict-freeness when present (M&P 2018 Def 14), but `framework.defeats` for outsider coverage. Mixing pre-preference attacks for CF with post-preference defeats for coverage can yield extensions where two members attack each other pre-preference yet don't defeat each other — structurally illegal under pure Dung semantics. The Modgil–Prakken split is intentional for admissibility/completeness but Dung Def 12 stable uses a single relation for both checks. The current implementation follows the split uniformly, which is plausible but not a canonical Dung formulation.
- Severity: medium. Produces extensions that differ from classical Dung stable when `attacks ⊋ defeats`, which is exactly propstore's case (preference-filtered defeats).
- Fix: document the intended behaviour precisely. Either (a) use `defeats` for both in stable semantics, matching Dung 1995 Def 12 verbatim; or (b) add a test pinning the M&P-Def-14-style hybrid behaviour with a citation that justifies it. Leaving this undocumented is the bug.

### ASPIC+ argument construction uses `id()` keys for dedup
- File: `aspic.py:743` — `combo_signature = (id(rule), tuple(id(sub_arg) for sub_arg in combo))`.
- Summary: `id()` is memory-address based. It is only safe here because `all_args` keeps references alive for the duration of `build_arguments`. If anyone extracts this helper into a context where references are released mid-build, dedup could silently fail and produce duplicate Argument instances under value-equality.
- Severity: low/latent. Works today; brittle to refactor.
- Fix: use value-based keys (`(rule, combo)` with tuples of Arguments is hashable via the cached `__hash__`).

### `build_arguments_for` cycle handling is non-idempotent
- File: `aspic.py:852-932`.
- Summary: When a rule cycle is detected (`target in in_progress`), every literal currently resolving is added to `cycle_tainted`; memoization is suppressed for tainted literals (`if target not in cycle_tainted: memo[target] = result`). This means later calls to `_build_backward(tainted_lit, ...)` will re-execute the search with a now-empty `in_progress` stack and return a non-empty result. So the same literal yields different results depending on whether the caller happened to traverse it during cycle detection or later. The attacker-fixpoint loop at lines 944-974 invokes `_build_backward(contrary_lit, 0)` for contraries — if a contrary was tainted, it gets re-evaluated. Not an incorrectness (the fixpoint eventually settles) but depth-order-dependent and wasteful.
- Severity: low. Produces correct final argument set under typical KBs, but is a footgun: changing traversal order changes intermediate cache state.
- Fix: memoize tainted literals with a cycle sentinel, not suppressed; or do two-pass: first detect SCCs on the rule graph, then resolve acyclically.

### `_contradictories_of` raises when literal has no contradictory partner
- File: `aspic.py:345-372`.
- Summary: `transposition_closure` calls `_contradictories_of` on every strict-rule literal. If any literal lacks an explicit contradictory entry, `ValueError` is raised mid-closure. propstore's `aspic_bridge.build._build_language` and `stances_to_contrariness` explicitly add `literal.contrary` and seed `(literal, literal.contrary)` contradictories for every literal, so this is safe in practice — but the contract is an implicit pre-condition callers must know.
- Severity: low (contract documented in docstring), but a caller that forgets the universal `(lit, lit.contrary)` seeding will see cryptic errors.
- Fix: the docstring already names the precondition. Consider surfacing this as a named `Contract`-style check with a clearer error, or expose a helper `ensure_structural_contradictories(language, cfn)`.

### `baumann_2015_kernel_union_expand` does not compute kernels
- File: `af_revision.py:121-130`.
- Summary: The function name and citation advertise "kernel union expansion" per Baumann 2015 (stable-kernel or similar). The implementation is a naive union of arguments and defeats with no kernel computation. The test (`tests/test_af_revision.py:125-137`) only checks monotonicity and idempotence — properties satisfied by naive union too — so the drift is untested. Baumann 2015 defines specific kernels (e.g. the stable-kernel) under which two AFs have equivalent extension behaviour precisely when they share the kernel; "kernel union" is a technical operation that deletes redundant edges before unioning.
- Severity: medium. If no consumer relies on kernel-level equivalence, it's cosmetic. If any consumer does, the cited paper's guarantees do not hold.
- Fix: verify propstore consumers. If nobody needs the kernel property, rename to `naive_union_expand`. Otherwise, implement kernel computation.

## Extension Algorithm Compliance

### Grounded extension — correct
- File: `dung.py:187-210`.
- Least fixed point of the characteristic function. Matches Dung 1995 Def 20 + Thm 25. Uses a precomputed `_attackers_index` so each characteristic iteration is linear in |A| + |D|. Terminates because F is monotonic and the universe is finite.

### Complete extensions — correct, with one redundant check
- File: `dung.py:230-267` (brute), `dung_z3.py:187-226` (Z3).
- Complete = fixed point of F and admissible. The brute-force version checks both `characteristic_fn(S) == S` AND `admissible(S)`. Because admissibility also validates CF (against `attacks`), this is not fully redundant when the attack relation is supplied — the fixpoint check uses defeats only, while admissibility also enforces CF on attacks. Correct per M&P Def 14. Z3 version encodes `v[a] ↔ defended(a)` directly — cleaner.

### Preferred extensions — correct
- File: `dung.py:270-290`.
- Filters complete extensions to those that are maximal (`not any(ext < other for other in completes)`). Matches Dung 1995 Def 8. Z3 version does the same filter over `z3_complete_extensions`.

### Stable extensions — see "Attack-vs-defeat split" above
- File: `dung.py:293-322`, `dung_z3.py:138-181`.
- Coverage-of-outsiders check is correct. CF check has the documented hybrid behaviour. Pinning test absent.

### Semantics dispatch for partial AFs collapses grounded across completions
- File: `semantics.py:72-85`.
- Calling `extensions(partial_af, semantics="grounded")` returns the deduped union of grounded extensions across ALL completions — i.e. a tuple of extensions, not a single extension. This is mathematically "grounded over all completions" but naming-wise confusing: grounded is unique per Dung AF, not per partial AF. Callers expecting `(single_extension,)` will misinterpret.
- Severity: low/documentation. Works as enumerated.
- Fix: rename the dispatcher return to make plurality obvious, or document in the README.

### `accepted_arguments` with empty extension family returns empty
- File: `semantics.py:103-126`.
- Summary: When stable has no extension, both credulous and skeptical modes return `frozenset()`. Some formal-argumentation conventions define skeptical acceptance over an empty extension family as vacuously universal (every argument is in every extension, because there are no extensions). The code's choice is defensible but silent — propstore callers using `accepted_arguments(af, semantics="stable", mode="skeptical")` to drive world queries may treat "no acceptance" and "stable undefined" identically, which would be wrong.
- Severity: medium in the context of propstore's stable-based render paths.
- Fix: either return `frozenset(framework.arguments)` for skeptical-over-empty (vacuous truth) or raise a typed `NoExtensionsError` so callers see the undefined case explicitly.

## Silent Failures

### `ArgumentationFramework` attacks-defeat mixing is silent
- File: `dung.py:99-110`, `admissible` at `156-184`, `stable_extensions` at `293-322`.
- When `framework.attacks is None`, CF falls back to `defeats`. When `attacks` is supplied, CF uses it. No warning or typed signal distinguishes "I meant pure Dung" from "I meant preference-filtered M&P". A bug where a caller forgets to pass `attacks=` silently changes stable-extension results.
- Severity: medium.
- Fix: require explicit `attacks` (or explicitly-null attacks meaning "same as defeats") at construction time. Or add a render-time comparison tool surfacing the difference.

### `PartialArgumentationFramework` partition requires full A × A
- File: `partial_af.py:42-72`.
- Construction raises if `attacks ∪ ignorance ∪ non_attacks` does not equal `arguments × arguments`. Consumers MUST explicitly supply non-attacks for every un-listed pair. `consensual_expand` handles it; ad-hoc construction does not. propstore's `source/alignment.py` and `merge/merge_classifier.py` call the constructor — need to verify they always pass complete partitions.
- Severity: low — raises cleanly. But "missing pairs" is the default mode of getting this wrong and the error message is long.
- Fix: provide a `from_attacks_and_ignorance(arguments, attacks, ignorance)` classmethod that auto-fills non-attacks.

### `_extend_state` in `af_revision.py` silently defaults unknown ranks to 0
- File: `af_revision.py:201-211`, line 207: `candidate: state.ranking.get(frozenset(...), 0)`.
- Summary: When extending the argument universe, each new candidate extension projects down to its intersection with the old universe; if the projected set is not in the old ranking, its rank defaults to 0. This silently equates new candidates with the minimum rank — equivalently, treats novel extensions as indistinguishable from originally-preferred ones.
- Severity: medium. Changes Diller 2015 revision outcomes in edge cases.
- Fix: either use `max_rank + 1` as the default, or raise on missing projection. The paper gives a specific lifting rule that should be codified.

### `minimal_extensions` uses a fallback sentinel `len(self.ranking) + 1`
- File: `af_revision.py:91-101`, line 97 and 99.
- Candidates not in `self.ranking` receive rank `len(self.ranking) + 1` — larger than any real rank. Harmless for well-formed states (ranking covers all extensions), but if ever called on a stale state after universe expansion without rebuild, it silently returns non-minimal candidates.
- Severity: low. Depends on the `ranking is None` hot-path in `from_extensions` always rebuilding.

## Bugs

### `af_revision._classify_extension_change` has non-exhaustive branches
- File: `af_revision.py:186-198`.
- The classification is hand-coded without any RESTRICTIVE or QUESTIONING case. The `len(before) > 2` guard in the DECISIVE branch is also suspicious: Cayrol 2014 does not condition decisiveness on source cardinality. This reads like an under-specified heuristic, not the paper's case analysis.
- Severity: medium.
- Fix: reimplement against Cayrol et al. 2014's seven-case decision tree, or explicitly document the reduction.

### `compute_dfquad_strengths` has O(n²) Kahn's sort
- File: `probabilistic_dfquad.py:136-153`.
- Loop: `while queue: node = queue.pop(0); ... for a in args: if node in predecessors[a]: ...`. Both `queue.pop(0)` and the scan-every-arg inner loop are O(n), total O(n²·degree). Not wrong, just slow — and lack of `collections.deque` and `successors` index is avoidable.
- Severity: low. Performance issue on wide QBAFs.
- Fix: use `deque.popleft()` and a successors adjacency.

### `compute_dfquad_strengths` cycle fallback: no divergence detection
- File: `probabilistic_dfquad.py:171-188`.
- Fixpoint loop runs 100 iterations with `1e-9` convergence. If the DF-QuAD update is non-contractive on a given graph, this silently returns the last iterate after 100 passes with no warning. Freedman 2025 assumes acyclic QBAFs — so cyclic inputs are outside the paper's guarantees — but the code accepts them.
- Severity: low (documented in comments).
- Fix: raise on non-convergence or at least record in a returned diagnostic.

### `bipolar.cayrol_derived_defeats` — inner loops always re-scan `working_defeats`
- File: `bipolar.py:126-149`.
- The fixpoint loop iterates `working_defeats` (which grows every iteration) and for each edge checks against `support_reach`. Correct, but quadratic-in-edges each iteration. For dense frameworks this is slow; no incremental frontier tracking.
- Severity: low (performance).

### `sum_merge_frameworks` / `max_merge_frameworks` / `leximax_merge_frameworks` enumerate `2^(|A|^2)` candidate AFs
- File: `partial_af.py:231-338`.
- `_candidate_frameworks` iterates all subsets of `arguments × arguments`. For |A|=5 that's `2^25 ≈ 33M`; |A|=6 is `68B`. No size guard, no timeout. A propstore caller that merges on a universe of even 5-6 arguments will hang the process.
- Severity: high for consumer usage (propstore's `merge` subsystem calls these).
- Fix: add a tunable threshold and raise a typed `MergeTooLargeError` above it; or replace exact search with an ILP / local-search approximation above the threshold.

### `_or_vars(v, ())` returns `BoolVal(False)` but is never reached defensively
- File: `dung_z3.py:95-101` and call sites.
- `_or_vars` is called from `_defended_expressions`, which already early-returns `BoolVal(True)` for un-attacked arguments before calling `_or_vars`. The empty-tuple branch in `_or_vars` is thus dead. Defensive but confusing.
- Severity: trivial.

## Dead Code

- `AFChangeKind.RESTRICTIVE` and `AFChangeKind.QUESTIONING` (see API issue above).
- `_or_vars` empty-tuple branch in `dung_z3.py:97-98` is unreachable from the only caller.
- `transposition_closure` `if transposed_consequent in transposed_antes: continue` guard at `aspic.py:447` is redundant with `_is_degenerate_rule` checking for contradictory antecedent pairs; not strictly dead (different semantics) but both guards exist for the "well-formedness" requirement.
- `argumentation.probabilistic_treedecomp` was not reviewed in detail — unclear if all exports are consumed.

## Positive Observations

### Citation discipline is excellent
- Every public function cites its paper, definition, and often the page number. This is rare in formal-argumentation libraries and makes review tractable. `aspic.py` especially: Def 5, Def 8, Def 9, Def 12, Def 14, Def 19, Def 20, Def 21, Def 22 are all cited at their implementation sites.

### Immutable frozen dataclasses with structural equality
- `ArgumentationFramework`, `PartialArgumentationFramework`, `BipolarArgumentationFramework`, `Rule`, `Literal`, `GroundAtom`, `PremiseArg`, `StrictArg`, `DefeasibleArg`, `CSAF` — all `@dataclass(frozen=True)`. This is the correct foundation for deterministic build/compare/merge over large argument sets. Hash caches on argument variants (`_hash` field with compare=False) preserve value-equality while avoiding recomputation.

### `__init__.py` imports submodules only
- No symbol-level re-export at package root. Propstore imports via `from argumentation.<module> import …`, which is stable across internal refactors. Good boundary discipline.

### The Z3 backend and brute-force backend share helpers
- `_attackers_index` is reused by both `dung.py` and `dung_z3.py`. The attack-relation split (`cf_relation = framework.attacks if framework.attacks is not None else framework.defeats`) is implemented identically in both backends — this is what makes the differential tests meaningful.

### Contrariness function distinguishes contrary from contradictory
- `ContrarinessFn` (aspic.py:84-134) explicitly separates symmetric `contradictories` from directional `contraries` per M&P Def 2. `is_contrary` excludes contradictory pairs (line 124). This is correctly refined compared to libraries that conflate the two.

### Preference comparison edge cases documented in code
- `_set_strictly_less` at `aspic.py:1128-1131` explicitly handles "empty Γ vs empty Γ′" with a citation-driven choice, per M&P 2018 Defs 19-21. This is exactly the kind of edge case most implementations get wrong.

### Probabilistic module routes to the right backend
- `_compute_probabilistic_acceptance` (probabilistic.py:593-776) explicitly orders: deterministic → exact_enum for ≤13 args → MC for relation-rich worlds → DP for low-treewidth grounded → MC fallback. Each branch cites its source (Li 2012 p.2/p.8, Hunter & Thimm Prop 18, Popescu-Wallner 2024). Healthy guard against silent strategy drift.

### Acyclicity check in ASPIC+ argument construction is correct
- `aspic.py:757` — `if rule.consequent in combo_concs: continue` where `combo_concs = union(all_concs(sub_arg))`. Because `all_concs` is transitive, this catches both direct (p→p) and multi-hop (p→q→p) rule cycles. Combined with c-consistency filtering, this is a sound termination condition for a finite language.

---

**Summary:** no symbol-level consumer drift. Classical Dung/ASPIC+ algorithms are
correct against their cited definitions, with one notable gap: stable-extension
CF/defeat hybrid semantics is not pinned by a test, and in preference-filtered
regimes (propstore's actual use case) it yields subtly non-classical behaviour.
One naming/citation mismatch in `af_revision.baumann_2015_kernel_union_expand`
(naive union, not kernel). One actionable DoS risk in `partial_af` merge
operators (2^(|A|²) enumeration with no guard). Multiple medium-severity
silent-failure patterns (skeptical-on-empty, rank defaulting in `_extend_state`,
attacks/defeats confusion).
