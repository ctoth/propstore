# Addendum: remaining Claude workstreams

Date: 2026-04-27

## Read status

After the first `claude-workstream-review.md`, I read the previously-unread workstreams directly where feasible: WS-F, WS-G, WS-H, WS-I, WS-J, and WS-K2. I also used three explorer subagents to inspect the remaining upstream/dependency files:

- WS-O-arg-argumentation-pkg, WS-O-arg-aba-adf, WS-O-arg-dung-extensions, WS-O-arg-gradual, WS-O-arg-vaf-ranking.
- WS-G, WS-H, WS-I, WS-J.
- WS-F, WS-K2, WS-O-gun-garcia, WS-O-bri-bridgman, WS-O-ast-ast-equiv.

I did not reread the cited papers in this addendum. Any paper-fidelity claims here are therefore about contradictions inside Claude's workstream text, not independent paper adjudication.

## Verdict

The remaining workstreams add important coverage, especially around ASPIC, AGM/IC postulates, PrAF, ATMS, worldline determinism, and the upstream `argumentation` package. They also introduce a second class of risk: several workstreams now look like execution plans but still contain unresolved decisions, impossible tests, dual-path compatibility surfaces, and cross-repo sequencing contradictions.

Before using Claude's folder as an execution control surface, these need correction.

## Critical Amendments

### 1. Assign owners before execution

Every upstream or manual-review-heavy stream still says `Owner: TBD`. That is not harmless for:

- WS-O-arg-* streams, which are multi-month upstream package work.
- WS-O-gun-garcia, WS-O-bri, WS-O-ast, which require sibling repo releases and propstore pin bumps.
- WS-K2, which requires human review of extracted rules and acceptance-rate accounting.

Amendment: replace `Owner: TBD` with either a named human owner or `Codex implementation owner + human reviewer required`. WS-K2 especially needs a named human reviewer because the acceptance gate depends on accepted/rejected rule proposals.

### 2. WS-F projection test erases the ASPIC attack/defeat distinction

WS-F correctly says ASPIC attacks and defeats may diverge, and conflict-freeness must be checked over attacks. But its `test_projection_attack_defeat_skew` asserts projected attacks iff projected defeats.

That is the wrong invariant. It collapses the distinction WS-F exists to preserve.

Amendment: the projection test should assert that both relations are projected without silent loss, not that they are equal. A valid projected framework may have an attack with no defeat.

### 3. WS-F has undeclared WS-O-arg dependencies

WS-F header depends only on WS-D. But Step 6 needs the upstream `argumentation` package to expose a public `contraries_of`, and Step 1 contemplates an upstream kernel signature change for transposition closure.

Amendment: split WS-F into propstore-only steps and WS-O-arg-blocked steps, or declare WS-O-arg as a dependency for the relevant steps. Do not write a sequence that cannot land without an upstream release.

### 4. WS-G tests conflate "missing coverage" with "must fail"

Several WS-G first-failing tests are for currently-unasserted postulates such as IC4, Maj, and Arb. The implementation may already satisfy some of them. A new test that passes on the first run is still valuable coverage, but it is not a TDD proof of a bug.

Amendment: label such tests as "coverage gates" unless a concrete counterexample is provided. Reserve "must fail today" for tests with a known failing fixture.

### 5. WS-G has a flaky cache test plan

WS-G proposes forcing Python `id()` recycling in a loop to expose `_distance_to_formula` cache keying. That is nondeterministic and environment-sensitive.

Amendment: inspect the cache keying directly or build a deterministic stale-cache fixture. Do not depend on object-id reuse timing.

### 6. WS-G's OCF contraction formula is under-proven

WS-G proposes a concrete ranking update formula, `min(state.ranks[w], revised_by_negation.state.ranks[w])`, but the proposed test only proves "not flattened." It does not prove that formula is the paper-faithful Spohn/Booth-Meyer contraction.

Amendment: add a paper-derived worked example with expected ranks. If no worked example is in the notes, write the derivation into the test docstring before implementing the formula.

### 7. WS-H pins DF-QuAD behavior before deciding the paper contract

WS-H's DF-QuAD test asserts symmetric attacker/supporter edge weighting. Later text says the implementation should be chosen per the paper's actual definition.

Amendment: decide the DF-QuAD paper contract first, then write the test. The test should pin the cited formula, not a plausible symmetry intuition.

### 8. WS-I/WS-J ordering contradicts itself

WS-I says it is a practical precondition for trusting worldline outputs. WS-J depends only on WS-A and WS-D. If WS-J's determinism tests consume ATMS-derived state, the ordering is wrong.

Amendment: either make WS-J depend on WS-I, or constrain WS-J tests to worldline surfaces that do not consume ATMS outputs. The dependency graph should not say "practically required" in one file and omit it in the other.

### 9. WS-I rename plan keeps the old API while saying no shim

WS-I says rename `is_stable` to `is_stable_within_limit`, then keep a thin `is_stable(...)` as the unbounded call, while also saying "No shim."

Amendment: write this as an interface replacement, not a rename. The old bounded meaning of `is_stable` is deleted; the new `is_stable(limit=None)` is a new unbounded API with different semantics. Tests should assert callers handle the new return type.

### 10. WS-J hash tests have wrong premises

`test_worldline_hash_excludes_transient_errors` compares a failed run with a successful run and expects equal hashes. Those are different materialized results. Stable error categorization should make equivalent failures hash the same, not make failures equal successes.

`test_worldline_hash_repr_stability` feeds a custom non-JSON object and expects stable hashing, while Step 1 requires a strict encoder that raises on unknown types.

Amendment:

- Compare two equivalent failures with different exception reprs.
- For unknown objects, assert typed failure or require normalization before hashing.

### 11. WS-J public budget API is contradictory

WS-J says `max_candidates` should be required positional and also have a default configured constant.

Amendment: pick one. Given the project discipline, I recommend a required keyword argument on owner-layer APIs and explicit values at every caller. If a default is truly desired, make it configuration, not a hidden compatibility path.

### 12. WS-J real replay lacks a storage contract

WS-J says `check_replay_determinism` should become actual replay, but the plan does not add or validate journal metadata sufficient to dispatch `revise`, `contract`, or `iterated_revise`.

Amendment: add a step before replay implementation: journal entries must store typed operator name, operator input, version/policy, and enough normalized state to rerun. Then replay tests can be meaningful.

### 13. WS-K2 first step references a missing skill

WS-K2 Step 1 says to run `research-papers:register-predicates`. That skill is not in the available skill list in this session.

Amendment: either add the missing skill, change the step to use an existing skill/workflow, or write the predicate-registration implementation explicitly. As written, the first production step is not executable.

### 14. WS-K2 CLI is not tested

WS-K2 adds `pks proposal propose-rules` and `pks proposal promote-rules`, but acceptance relies on hand-run output. The acceptance gate lists no CLI tests.

Amendment: add logged CLI tests for help, dry-run/review mode, propose with mocked LLM, selective promote, unknown rule id, and no-commit review mode.

### 15. WS-O-arg top-level stream falsely says it blocks nothing

WS-O-arg-argumentation-pkg says it blocks "nothing hard" and can run in parallel, but sibling WS-O-arg streams declare it as a prerequisite.

Amendment: make WS-O-arg-argumentation-pkg the explicit first upstream argumentation stream, or split truly-independent bug fixes from foundation work.

### 16. WS-O-arg ideal-extension proof claim is unsafe

The workstream claims the intersection of maximal admissible candidates is always admissible because subsets of admissible sets preserve defense. Defense is not generally downward-closed: removing a defender can make a subset undefended.

Amendment: replace the proposed proof with the actual ideal-semantics construction from the cited source, and add a counterexample test for the unsafe subset-defense assumption.

### 17. WS-O-arg Dung stream keeps a second backend after saying delete old paths

WS-O-arg-dung says labelling-backed semantics replace old paths and "Do NOT keep" old code, then keeps a Z3 path as a second backend.

Amendment: choose one target architecture. If Z3 remains, justify it as a distinct solver backend with identical contract and explicit selection, not as an undeleted legacy path. Otherwise delete it and update every caller.

### 18. WS-O-arg sentinels have repo-location confusion

Several upstream streams place sentinel tests in `argumentation/tests/` but describe propstore-side pin-bump steps as flipping those sentinels. A propstore commit cannot flip an upstream test.

Amendment: separate upstream sentinels from propstore pin sentinels:

- upstream sentinel closes in the dependency repo;
- propstore sentinel asserts the pinned dependency version contains the fix and the public behavior is observable from propstore.

### 19. WS-O-arg ABA/ADF representation is unresolved while tests require serialization

WS-O-arg-aba-adf leaves ADF acceptance-condition representation open, but also requires ICCMA I/O and done-means-done serialization. If callable acceptance conditions are chosen, serialization is descoped.

Amendment: resolve the representation before tests are declared final. If serialization is required, callable-only conditions cannot be the primary representation.

### 20. WS-O-arg ABA scope overclaims non-flat support

The workstream initially promises every Dung-style ABA semantics, but later raises `NotImplementedError` for non-flat ABA and narrows done to flat ABA.

Amendment: make the public API and tests flat-ABA-only until non-flat semantics are implemented. Do not advertise broader semantics.

### 21. WS-O-arg gradual stream keeps old paths and compatibility flags

WS-O-arg-gradual moves DF-QuAD out of `probabilistic_dfquad.py`, then keeps the old `compute_dfquad_strengths` path and lets propstore keep importing it. It also adds default-off continuous integration and `strict=True` compatibility behavior.

Amendment: apply the project's deletion-first rule. Delete the old production path, update every caller, and make the target behavior the only behavior unless an external constraint is stated.

### 22. WS-O-arg gradual and VAF both own ranking convergence

WS-O-arg-gradual and WS-O-arg-vaf-ranking both claim ownership of `ranking.py` non-convergence / `RankingResult`, while one says there is no coordination needed.

Amendment: assign ranking convergence to exactly one stream. The other stream consumes the resulting `RankingResult`.

### 23. WS-O-arg VAF overclaims Atkinson coverage

WS-O-arg-vaf-ranking calls AATS first-class while implementing only AS1 plus a few critical questions and deferring the rest.

Amendment: call it an Atkinson slice, not first-class AATS. Done means the implemented subset is honest and the missing CQs remain open.

### 24. WS-O-gun-garcia contradicts TDD execution

It defines first failing tests and per-step acceptance, then later says tests are not run during the rewrite and only at acceptance time.

Amendment: remove the "do not run tests during rewrite" language. TDD means each step starts with a failing test and ends with that targeted test passing.

### 25. WS-O-gun-garcia has a type-shape contradiction

It replaces sections with `GarciaSections(yes, no, undecided, definitely)`, then says strict-only fast path has `yes == defeasibly == definitely`. `defeasibly` no longer exists.

Amendment: update the strict-only invariant to the new field names, or keep a `defeasibly` field if that is actually part of the target type.

### 26. WS-O-gun-garcia claims schema closure while excluding schema work

The table says schema widening is required to close a finding, but the out-of-scope section says schema-side widening lives elsewhere and this stream does not touch `RuleDocument`.

Amendment: either move that finding out of WS-O-gun-garcia or add the schema change as an explicit propstore-side coordinated step. Do not mark it closed from gunray-only work.

### 27. WS-O-bri keeps `verify_equation` as a deprecated path

WS-O-bri says canonical path is `verify_expr` and `verify_equation` is demoted, but closes before deleting `verify_equation`, leaving deletion to a later release. No external constraint is stated.

Amendment: delete `verify_equation` in the target release and update all callers, or state the external constraint that requires a deprecation period.

### 28. WS-O-bri tooling violates local rules

The acceptance gate uses bare `python -c`. The project requires `uv run ...` and forbids inline `python -c` for substantive checks.

Amendment: replace with scripts or proper `uv run` entrypoints.

### 29. WS-O-ast leaves decisions open while scheduling implementation

WS-O-ast chooses real-domain assumptions, an `extract_names` API, and git-hash pinning in production steps, but lists those as open questions later.

Amendment: resolve those decisions first. The workstream should not simultaneously choose and not choose the same architecture.

### 30. WS-O-ast error handling is contradictory

Step 4 says `AstToSympyError` is caught inside `compare()`. Step 12 says propstore may keep external catches if `compare()` raises it. Under Step 4, external catches are dead code.

Amendment: decide the boundary. If `compare()` catches and returns typed `UNKNOWN`, delete external `AstToSympyError` catches and add tests proving they are gone.

## Additional Ordering Changes

1. Add a preflight "workstream consistency lint" before implementation: no `Owner: TBD`, no "must fail" without a known failing fixture, no upstream sentinel flipped by propstore, no unresolved open question referenced by a production step.
2. Run upstream `argumentation` foundation work before WS-F/WS-G/WS-H steps that depend on public API changes.
3. Treat WS-J as either dependent on WS-I or explicitly isolated from ATMS-derived state.
4. Do WS-K2 only after the predicate-registration path exists and a human reviewer is assigned.
5. Do not let any dependency stream close while leaving deprecated APIs or compatibility flags behind unless a real external constraint is documented.

## Bottom Line

Claude's remaining workstreams are valuable, but several are not yet TDD-executable. The biggest problems are not missing bug ideas; they are control-surface failures: impossible tests, contradicted dependencies, ownership gaps, and transition paths that violate the repo's deletion-first discipline. Fix those before starting implementation, or the workstreams will look complete while still allowing the old ambiguity to survive.
