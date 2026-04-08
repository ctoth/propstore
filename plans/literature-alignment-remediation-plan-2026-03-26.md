# Literature Alignment Remediation Plan

Date: 2026-03-26

## Objective

Bring the argumentation stack onto a more principled footing by:

1. Fixing verified implementation bugs.
2. Replacing heuristic or ambiguous behavior with explicit literature-grounded semantics.
3. Expanding the test suite with TDD-first repro tests and Hypothesis properties.
4. Making semantic choices explicit where multiple papers define different, incompatible notions.

This plan assumes strict TDD:

1. Write the failing test or property first.
2. Confirm it fails on current `main`.
3. Implement the smallest change that makes it pass.
4. Refactor only after the regression/property is green.

## Non-Goals

- No silent semantic rewrites without tests and an explicit migration note.
- No replacing one paper with another by accident when the papers define different objects.
- No burying literature divergences behind overloaded names like "grounded" or "preference" without qualifiers.

## Guiding Decisions

1. Separate bug-fix work from semantic redesign work.
2. Preserve current behavior only when it is both intentional and defensible.
3. Where the literature offers multiple semantics, expose them as named options instead of forcing one hybrid default.
4. Prefer additive refactors first, then deprecate old ambiguous APIs after equivalence or migration tests exist.

## Workstreams

### W1. Verified Bug Fixes

Scope:

- Fix the public DF-QuAD dispatcher dropping support edges.
- Fix MC stopping so `mc_confidence` actually changes convergence.
- Fix or remove the near-deterministic shortcut that rounds probabilistic worlds into certainty.
- Investigate and resolve the `exact_dp` silent wrong-answer risk.
- Make DF-QuAD reject or explicitly document ignored Dung `semantics`.

TDD plan:

1. Add failing regression tests to:
   - `tests/test_dfquad.py`
   - `tests/test_praf.py`
   - `tests/test_treedecomp.py`
2. Confirm each new test fails in isolation.
3. Fix one bug at a time.
4. Keep differential tests against `exact_enum` for every exact backend change.

Required RED tests:

- `test_dfquad_dispatch_uses_praf_support_edges`
- `test_dfquad_dispatch_respects_support_weight_changes`
- `test_mc_confidence_99_requires_more_or_equal_samples_than_95`
- `test_mc_reported_ci_respects_requested_confidence`
- `test_auto_does_not_round_near_certain_probabilities_to_deterministic`
- `test_dfquad_rejects_irrelevant_dung_semantics_argument` or `test_dfquad_semantics_argument_is_explicitly_fixed_to_none`
- `test_exact_dp_matches_exact_enum_under_repeated_randomized_differential_runs`
- `test_exact_dp_history_independence`

Implementation targets:

- `propstore/praf.py`
- `propstore/praf_dfquad.py`
- `propstore/praf_treedecomp.py`

Acceptance criteria:

- New regression tests fail before changes and pass after changes.
- `exact_dp` either proves out against strong differential tests or is demoted/removed from public exact dispatch until sound.
- No public API silently ignores support edges or confidence levels.

### W2. Dung and Bipolar Semantics Cleanup

Problem:

The current code mixes Dung semantics, attack-based conflict-freeness, Cayrol-style derived defeats, and a bespoke fallback for "grounded" when `attacks != defeats`.

Goal:

Replace ambiguous hybrid behavior with explicit semantic families.

Sub-work:

1. Define explicit AF kinds:
   - `DungAF`
   - `HybridAttackDefeatAF`
   - `BipolarAF`
2. Make grounded semantics explicit:
   - Dung grounded on pure AFs.
   - A named hybrid fallback only if retained.
   - Bipolar semantics exposed under bipolar names, not plain Dung names.
3. Stop presenting a bespoke least-complete/empty fallback as plain "grounded" without qualification.

TDD plan:

Add failing tests to `tests/test_dung.py` and `tests/test_bipolar_argumentation.py`:

- `test_grounded_name_not_used_for_hybrid_attack_defeat_fallback_without_opt_in`
- `test_hybrid_grounded_mode_is_explicitly_named`
- `test_bipolar_d_admissible_differs_from_s_admissible_when_safety_fails`
- `test_bipolar_c_admissible_requires_support_closure`
- `test_cayrol_example_2_set_classifications`

Implementation targets:

- `propstore/dung.py`
- `propstore/argumentation.py`
- possible new module: `propstore/bipolar.py`

Acceptance criteria:

- Plain `grounded` means Dung grounded only.
- Bipolar semantics are exposed as bipolar semantics.
- Cayrol Example 2 style cases are executable tests, not comments in notes.

### W3. Cayrol 2005 Proper Bipolar Semantics

Problem:

Current code computes supported/indirect defeats but stops short of safety, support-closure, and the d/s/c admissibility hierarchy.

Goal:

Implement the actual bipolar notions as named semantics.

Plan:

1. Introduce primitives:
   - set-defeat
   - set-support
   - safety
   - support-closure
   - defense by a set
2. Implement:
   - d-admissible
   - s-admissible
   - c-admissible
   - corresponding preferred/stable variants where intended
3. Keep current claim-graph behavior behind a legacy or "derived-defeat-only" mode until migrated.

TDD/property plan:

- Example-based tests from Cayrol Definition 3/4/5 examples.
- Hypothesis properties:
  - safe implies conflict-free
  - conflict-free + support-closed implies safe
  - derived defeats are a fixpoint
  - set-defeat is monotone in the attacking set

Implementation targets:

- new `tests/test_bipolar_semantics.py`
- `propstore/argumentation.py` or new `propstore/bipolar.py`

Acceptance criteria:

- d/s/c behaviors are distinguishable in tests.
- The current reduced encoding is no longer the only bipolar option.

### W4. Preference Semantics Refactor

Problem:

`preference.py` is explicitly heuristic and does not implement either:

- ASPIC+ last-link / weakest-link induced orderings, or
- Amgoud 2011 semantics-level preference handling.

Goal:

Split the current heuristic from the literature-backed implementations.

Plan:

1. Rename current logic to a clearly heuristic name.
   - Example: `metadata_strength_ordering`
2. Implement ASPIC+ argument-ordering machinery as a first-class path.
   - set comparison
   - last-link
   - weakest-link
   - premise/rule order separation
3. Add an explicit Amgoud-2011-inspired semantics-level track for asymmetric attack cases, if adopted.
4. Ensure the public API cannot imply that the metadata heuristic is "the" preference semantics from the papers.

TDD plan:

Add failing tests to:

- `tests/test_preference.py`
- `tests/test_aspic.py`
- a new `tests/test_preference_semantics.py`

Required tests:

- last-link and weakest-link diverge on a constructed counterexample
- empty ordering implies all attacks succeed as defeats in ASPIC+
- asymmetric attack case where attack-removal and semantics-level preference handling diverge
- heuristic ordering is labeled and tested as heuristic, not literature-equivalent

Acceptance criteria:

- Users can pick explicit preference semantics.
- Heuristic metadata ordering remains available only under an honest name.

### W5. ASPIC+ Alignment

Problem:

Current ASPIC+ support is partial:

- asymmetric contraries are collapsed into contradiction
- there is custom pruning in transposition closure that may be stronger than the paper
- attack computation is written assuming the current symmetric shortcut

Goal:

Move ASPIC+ support from "subset with caveats" toward a faithful implementation.

Plan:

1. Implement genuine contraries vs contradictories in `ContrarinessFn`.
2. Audit all attack sites for directional contrary use.
3. Re-check defeat conditions once asymmetric contraries exist.
4. Audit transposition closure against the paper and keep any extra safety pruning behind explicit justification and tests.
5. Re-run rationality postulate tests at larger generated sizes.

TDD/property plan:

Add or expand tests in `tests/test_aspic.py`:

- asymmetric contrary attack one-way but not the other
- contrary-based attacks always defeat, if that path is adopted from the generalized account
- larger generated c-SAF rationality postulates
- transposition closure monotonicity and idempotence
- closure under strict rules for generated complete/preferred extensions

Acceptance criteria:

- `is_contrary` is no longer a synonym for contradiction.
- Directionality matters and is covered by tests.

### W6. Probabilistic Semantics Separation

Problem:

The current PrAF code mixes several different ideas:

- Li 2011 constellation probabilities
- Dung extension acceptance
- a credulous union-of-extensions reduction for multi-extension semantics
- DF-QuAD gradual strengths
- Hunter-style rationality constraints that are defined but not integrated

Goal:

Separate incompatible probabilistic notions instead of overloading one API.

Plan:

1. Split result types or query modes:
   - extension probability
   - argument acceptability probability
   - credulous acceptance probability
   - skeptical acceptance probability
   - gradual strength
2. Make DF-QuAD live under a QBAF/gradual interface, not a Dung-semantics-shaped slot.
3. Separate `P_A` from intrinsic strength `tau`.
4. Decide whether COH enforcement is:
   - explicit validation,
   - optional normalization,
   - or a required precondition for certain modes.
5. Clarify exact semantics in naming and return types.

TDD/property plan:

Add failing tests to:

- `tests/test_praf.py`
- `tests/test_dfquad.py`
- `tests/test_praf_integration.py`

Required tests:

- world probability normalization to 1
- exact vs MC agreement on small AFs
- credulous vs skeptical divergence on multi-extension worlds
- DF-QuAD output invariant only to QBAF inputs, not Dung semantics labels
- `tau` variation can differ from `P_A` variation
- COH validator catches violations
- `enforce_coh` postcondition holds on all attacks and self-attacks

Acceptance criteria:

- No public API pretends gradual strength is the same object as probabilistic acceptability.
- Multi-extension semantics are explicit about credulous vs skeptical aggregation.

### W7. Tree-Decomposition Exact Backend

Problem:

The current DP backend is marked exact but has known structural limitations and at least one observed silent-mismatch risk in randomized differential runs.

Goal:

Either make it demonstrably sound or remove it from public exact dispatch.

Plan:

1. Add a heavy differential test module that repeatedly compares:
   - `exact_dp`
   - `exact_enum`
2. Add history-independence tests:
   - repeated runs on the same PrAF
   - runs after prior unrelated PrAF evaluations
3. If unsound:
   - reduce a minimal counterexample
   - fix the state-combination logic
   - or gate `exact_dp` behind an experimental flag
4. Only claim Popescu alignment after the DP state matches the paper's local-state discipline, not the current edge-set accumulation.

TDD plan:

New module:

- `tests/test_treedecomp_differential.py`

Required tests:

- seeded randomized differential agreement
- repeated-call agreement
- disconnected-component agreement
- self-attack and cycle-heavy agreement
- agreement on every AF up to a chosen small size budget if computationally feasible

Acceptance criteria:

- `exact_dp` survives strong differential testing.
- If not, `auto` and public exact APIs stop routing through it.

### W8. Property-Suite Expansion

Goal:

Codify the paper-derived invariants as Hypothesis tests instead of relying on a few curated examples.

Property inventory:

1. Dung:
   - empty set admissible
   - every stable extension is preferred
   - every preferred extension is complete
   - grounded subset of every preferred extension
2. Bipolar:
   - safe implies conflict-free
   - conflict-free + closed for support implies safe
   - derived defeat closure is idempotent
3. ASPIC+:
   - subargument closure
   - strict closure
   - direct consistency
   - indirect consistency
4. Probabilistic:
   - total world mass equals 1
   - acceptability probabilities stay in [0,1]
   - exact and approximate agreement within tolerance on bounded instances
   - larger confidence never weakens required sample count
5. DF-QuAD/QBAF:
   - boundedness in [0,1]
   - base-score monotonicity
   - relation contestability
   - support/attack influence monotonicity

Execution:

- Expand existing test modules where local.
- Add `tests/test_argumentation_properties.py` for cross-module invariants.

Acceptance criteria:

- Every planned semantics family has at least one Hypothesis-backed invariant suite.

## Recommended Execution Order

### Phase 1. Red-Bar the Verified Bugs

1. DF-QuAD support dispatch
2. MC confidence stopping
3. near-deterministic auto shortcut
4. DF-QuAD semantics argument handling
5. `exact_dp` differential harness

### Phase 2. Make Public Semantics Honest

1. Rename heuristic preference path
2. Split gradual-strength vs probabilistic-acceptance interfaces
3. clarify hybrid grounded behavior

### Phase 3. Add Missing Literature Semantics

1. Cayrol d/s/c
2. ASPIC+ asymmetric contraries
3. explicit preference semantics options

### Phase 4. Differential and Property Hardening

1. randomized cross-backend checks
2. larger Hypothesis state spaces
3. component and history-independence checks

### Phase 5. Migration and Cleanup

1. deprecate ambiguous APIs
2. tighten docs and type names
3. remove or quarantine experimental semantics that remain unsound

## Concrete Test Writing Checklist

For each item:

1. Create the test name and a one-paragraph docstring citing the relevant paper claim.
2. Write the smallest reproducible fixture.
3. Run the single test and save the failing output.
4. Implement the minimal change.
5. Run the local target module.
6. Run the wider affected suite.
7. If the change alters semantics, add a regression fixture that demonstrates the old behavior is intentionally gone.

## Deliverables

1. New regression tests for every verified bug.
2. New Hypothesis properties for Dung, bipolar, ASPIC+, PrAF, and DF-QuAD/QBAF layers.
3. Refactored public APIs that separate:
   - Dung
   - bipolar
   - ASPIC+
   - probabilistic acceptance
   - gradual strength
4. A sound exact backend policy:
   - proven differential agreement, or
   - disabled experimental routing.

## Definition of Done

This remediation is done when:

1. All verified bugs are covered by failing-then-passing tests.
2. Literature-backed semantics are named and implemented explicitly rather than implied through hybrids.
3. Heuristic behavior is labeled as heuristic.
4. The probabilistic APIs distinguish existence probability, acceptance probability, and gradual strength.
5. The exact backend is either trustworthy under differential testing or no longer presented as exact.
6. The property suite exercises the main paper-derived invariants continuously.
