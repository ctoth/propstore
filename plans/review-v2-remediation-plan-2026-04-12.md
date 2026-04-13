# Review V2 Remediation Plan

Date: 2026-04-12
Status: executable

This plan covers the findings in `review-v2.md` after validation against the
current repo state and the editable local `gunray` dependency.

The purpose of this plan is not to relitigate the review. It is to decide what
we accept, what we reject, what is already covered by existing plans, and what
must be sequenced first because it can produce wrong derivations today.

## Writable Repos

The work for this review is allowed to span multiple local repos when the
correct fix surface is not entirely inside `propstore`.

Writable repos for this plan:

- `C:/Users/Q/code/propstore`
- `C:/Users/Q/code/gunray`
- `C:/Users/Q/code/research-papers-plugin`
- `C:/Users/Q/code/datalog-conformance-suite`

Use the narrowest correct write surface:

- fix parser/evaluator defects in `gunray`
- fix bridge/projection/query defects in `propstore`
- land any required import-contract or caller updates in `research-papers-plugin`
- land cross-implementation conformance cases in `datalog-conformance-suite`

Do not leave correctness fixes half-landed across repo boundaries.

## Execution Discipline

For every accepted issue in this plan:

1. prove the issue first with a failing regression test or failing Hypothesis
   property
2. run the failing test/property and keep the failure as evidence
3. fix the implementation
4. rerun the focused proof plus the nearest relevant regression suite
5. commit the kept reduction before moving to the next issue or tightly coupled
   issue pair

Commit discipline:

- commit frequently
- push frequently
- prefer one issue or one tightly coupled slice per commit
- if a fix spans repos, make the repo-local commits as soon as each repo is
  internally green rather than batching unrelated fixes into one long-running
  dirty state

Repo sync discipline:

- run `uv sync` in each touched repo before running its test suite if that repo
  may have drifted
- run `uv sync` again after any dependency or lockfile change
- when switching to a repo after upstream movement, sync that repo before
  trusting test results
- do not assume one repo's environment is current just because another repo's
  environment is current

Plan-reread discipline:

- reread this workstream after every green substantial targeted run
- reread this workstream after every phase-close run
- reread this workstream before deciding the next slice
- do not treat local momentum or a convenient checkpoint as permission to skip
  unchecked issues

The default for this review is test-first, then fix. Diagnostics or reasoning
alone do not count as issue closure.

## Live Status Ledger

Update this ledger as the work proceeds. Each issue should end in exactly one
terminal state: `kept-fixed`, `rejected-after-proof`, or `deferred-by-user`.

### Immediate correctness tranche

| Issue | Summary | Proof added | Fixed | Repo(s) | Commit(s) | Status | Notes |
|---|---|---|---|---|---|---|---|
| 1 | quoted string scalar collapse | yes | yes | gunray/dcs | gunray:`00844b0`; dcs:`9d4c7a9` | kept-fixed | red: `gunray/logs/test-runs/issue1-proof-red-pypath-20260412-220526.log`; green: `gunray/logs/test-runs/issues1-2-green-20260412-220723.log` |
| 2 | arithmetic associativity | yes | yes | gunray/dcs | gunray:`00844b0`; dcs:`9d4c7a9` | kept-fixed | red: `gunray/logs/test-runs/issue2-proof-red-20260412-220649.log`; green: `gunray/logs/test-runs/issues1-2-green-20260412-220723.log` |
| 3 | unsafe negation acceptance | yes | yes | gunray/dcs | gunray:`8de56a7`; dcs:`78e0b0b` | kept-fixed | red: `gunray/logs/test-runs/issue3-proof-red-20260412-221109.log`; green: `gunray/logs/test-runs/issue3-green-20260412-221126.log` |
| 4 | strong negation dropped at boundary | no | no | propstore |  | pending | existing strong-negation plan overlap |
| 5 | grounded literal aliasing by repr | yes | yes | propstore | propstore:`103b613` | kept-fixed | red: `logs/test-runs/issues5-6-24-proof-red-20260412-221526.log`; green: `logs/test-runs/issues5-6-24-green-rerun-20260412-221759.log` |
| 6 | `_parse_ground_atom_key()` not invertible | yes | yes | propstore | propstore:`103b613` | kept-fixed | red: `logs/test-runs/issues5-6-24-proof-red-20260412-221526.log`; green: `logs/test-runs/issues5-6-24-green-rerun-20260412-221759.log` |
| 7 | goal-directed attacker incompleteness | no | no | propstore |  | pending |  |
| 8 | `arguments_against` misclassification | yes | no | propstore | pending | pending | focused chain proof did not reproduce; needs stronger reproducer before resolution |
| 9 | CSAF framework drops `attacks` | yes | yes | propstore | propstore:`5e3eedb` | kept-fixed | red: `logs/test-runs/issues8-11-proof-red-20260412-222016.log`; green: `logs/test-runs/issues9-11-green-20260412-222049.log` |
| 10 | preferred backend threading | yes | yes | propstore | propstore:`5e3eedb` | kept-fixed | red: `logs/test-runs/issues8-11-proof-red-20260412-222016.log`; green: `logs/test-runs/issues9-11-green-20260412-222049.log` |
| 11 | empty-premise rules dropped | yes | yes | propstore | propstore:`5e3eedb` | kept-fixed | red: `logs/test-runs/issues8-11-proof-red-20260412-222016.log`; green: `logs/test-runs/issues9-11-green-20260412-222049.log` |
| 12 | fact extraction ignores arity | yes | yes | propstore | pending | kept-fixed | red: `logs/test-runs/issues12-13-proof-red-20260412-222447.log`; green: `logs/test-runs/issues12-13-green-20260412-222511.log` |
| 13 | incomplete string escaping | yes | yes | propstore | pending | kept-fixed | red: `logs/test-runs/issues12-13-proof-red-20260412-222447.log`; green: `logs/test-runs/issues12-13-green-20260412-222511.log` |
| 14 | grounded-rule naming collision risk | no | no | propstore |  | pending |  |
| 15 | authored undercut ids mismatch grounded ids | no | no | propstore |  | pending |  |
| 24 | mixed claim-id and ground-atom namespace | yes | yes | propstore | propstore:`103b613` | kept-fixed | red: `logs/test-runs/issues5-6-24-proof-red-20260412-221526.log`; green: `logs/test-runs/issues5-6-24-green-rerun-20260412-221759.log` |
| 25 | query API contract mismatch | no | no | propstore |  | pending |  |
| 26 | inconsistent deferred-feature handling | no | no | propstore/gunray |  | pending |  |

### Semantic audit tranche

| Issue | Summary | Proof added | Fixed/Resolved | Repo(s) | Commit(s) | Status | Notes |
|---|---|---|---|---|---|---|---|
| 16 | transposition prunes whole strict theory | no | no | propstore |  | pending |  |
| 17 | transposition ignores contrariness parameter | no | no | propstore |  | pending |  |
| 18 | exponential closure policies public | no | no | gunray |  | pending | may resolve by contract narrowing |
| 19 | vacuous antecedent policy disagreement | no | no | gunray |  | pending |  |
| 20 | closure faithfulness unproven | no | no | gunray/dcs |  | pending |  |
| 21 | simplified specificity/defeat semantics | no | no | gunray |  | pending |  |
| 22 | incomplete negative-status coverage | no | no | gunray |  | pending |  |
| 23 | ASPIC edge-case deviations | no | no | propstore |  | pending |  |

## Validation Basis

I validated the plan inputs by reading the cited implementations directly.

Propstore files read:

- `propstore/aspic.py`
- `propstore/aspic_bridge.py`
- `propstore/dung.py`
- `propstore/grounding/facts.py`
- `propstore/grounding/translator.py`
- `propstore/structured_projection.py`

Gunray files read:

- `C:/Users/Q/code/gunray/src/gunray/parser.py`
- `C:/Users/Q/code/gunray/src/gunray/evaluator.py`
- `C:/Users/Q/code/gunray/src/gunray/closure.py`
- `C:/Users/Q/code/gunray/src/gunray/defeasible.py`

Test run executed:

- `uv run pytest -vv tests/test_backward_chaining.py tests/test_dung.py tests/test_review_regressions.py`
- log: `logs/test-runs/review-v2-assessment-20260412-215241.log`

The targeted tests pass. That does not refute the review. It means the review
is largely exposing correctness gaps that current tests do not cover.

## Decision Summary

### Accept as immediate correctness work

These are either directly wrong by inspection or structurally unsound enough
that they should not remain in production:

1. Gunray scalar identity collapse for quoted strings.
2. Gunray arithmetic associativity for `+` / `-` chains.
3. Gunray unsafe-negation acceptance.
4. Strong negation dropped at the propstore -> gunray boundary.
5. Grounded literal interning keyed only by `repr(GroundAtom)`.
6. `_parse_ground_atom_key()` not being a real inverse.
7. `build_arguments_for(..., include_attackers=True)` not computing an attack-relevance fixed point.
8. `query_claim()` misclassifying `arguments_against`.
9. `build_bridge_csaf()` omitting `framework.attacks`.
10. `preferred_extensions(..., backend="brute")` not threading backend through.
11. `justifications_to_rules()` silently dropping empty-premise rules.
12. `extract_facts()` ignoring predicate arity discipline.
13. Gunray translator string escaping being incomplete.
14. Grounded-rule naming not being collision-safe.
15. Ground-rule undercut targeting being mismatched with authored IDs.
24. Claim ids and ground-atom surface strings sharing one literal namespace.
25. Query API doc/behavior mismatch.
26. Inconsistent phase-boundary discipline for deferred semantics.

### Accept as semantic-risk work, but not tranche 1

These are real concerns, but they belong after the immediate derivation and
identity bugs:

16. `transposition_closure()` pruning the entire strict theory on singleton inconsistency.
17. `transposition_closure()` ignoring explicit contrariness input.
18. Closure policies exposing exponential world enumeration under public options.
19. Closure policies disagreeing on vacuous antecedents.
20. Rational / lexicographic / relevant closure faithfulness not established.
21. Specificity / defeat behavior being a narrowed interpretation, not a neutral one.
22. Negative-status sections not necessarily classifying all interesting ground instances.
23. Intentional ASPIC preference/deafeat deviations in edge cases.

### Already covered by an existing plan

These are already recognized and should not get a competing second plan:

- strong negation end-to-end and grounding/projection cutover:
  `plans/defeasible-logic-integration-remediation-plan-2026-04-12.md`
- broader evaluator-faithfulness and benchmark discipline:
  `plans/datalog-conformance-suite-2026-04-10.md`

This plan extends those efforts with the newly validated review-v2 defects.

## Full Issue Ledger

Every numbered review item is assigned here. Nothing from `review-v2.md` is
outside this workstream.

### Immediate correctness tranche

- Issue 1: `gunray` parser scalar identity
  proof surface: `gunray` regression test + portable conformance case
  fix surface: `C:/Users/Q/code/gunray/src/gunray/parser.py`
- Issue 2: `gunray` arithmetic associativity
  proof surface: `gunray` regression/property + portable conformance case
  fix surface: `C:/Users/Q/code/gunray/src/gunray/parser.py`
- Issue 3: `gunray` unsafe negation
  proof surface: `gunray` regression + rejection-focused conformance case
  fix surface: `C:/Users/Q/code/gunray/src/gunray/evaluator.py`
- Issue 4: strong negation dropped at boundary
  proof surface: `propstore` grounding/bridge regressions
  fix surface: `propstore`, with caller updates in `research-papers-plugin` if needed
- Issue 5: grounded literal aliasing by `repr(GroundAtom)`
  proof surface: `propstore` bridge regressions
  fix surface: `propstore/aspic_bridge.py`
- Issue 6: `_parse_ground_atom_key()` not invertible
  proof surface: `propstore` query regressions
  fix surface: `propstore/aspic_bridge.py`
- Issue 7: goal-directed attacker expansion not closed
  proof surface: `propstore` reinstatement-depth regression/property
  fix surface: `propstore/aspic.py`
- Issue 8: `arguments_against` misclassification
  proof surface: `propstore` query regression
  fix surface: `propstore/aspic_bridge.py`
- Issue 9: CSAF framework drops `attacks`
  proof surface: `propstore` bridge/projection regression
  fix surface: `propstore/aspic_bridge.py`
- Issue 10: preferred backend threading bug
  proof surface: `propstore` Dung regression
  fix surface: `propstore/dung.py`
- Issue 11: empty-premise rules silently dropped
  proof surface: `propstore` bridge regression + conformance case
  fix surface: `propstore/aspic_bridge.py`
- Issue 12: fact extraction ignores arity discipline
  proof surface: `propstore` grounding regression
  fix surface: `propstore/grounding/facts.py`
- Issue 13: incomplete string escaping
  proof surface: `propstore` translator regression
  fix surface: `propstore/grounding/translator.py`
- Issue 14: grounded-rule naming collisions
  proof surface: `propstore` bridge regression/property
  fix surface: `propstore/aspic_bridge.py`
- Issue 15: authored undercut ids not matching grounded instance ids
  proof surface: `propstore` bridge regression
  fix surface: `propstore/aspic_bridge.py`
- Issue 24: mixed claim-id and ground-atom key namespace
  proof surface: `propstore` bridge/query regression
  fix surface: `propstore/aspic_bridge.py`
- Issue 25: query API doc/behavior mismatch
  proof surface: `propstore` API regression
  fix surface: `propstore/aspic_bridge.py`
- Issue 26: inconsistent deferred-feature handling
  proof surface: targeted regressions for each deferred semantic edge
  fix surface: `propstore` and `gunray` boundary code

### Semantic audit tranche

- Issue 16: global strict-theory pruning semantics
  proof surface: `propstore` strict-closure regression
  fix surface: `propstore/aspic.py`
- Issue 17: dead contrariness parameter in transposition closure
  proof surface: `propstore` regression proving parameter irrelevance
  fix surface: `propstore/aspic.py`
- Issue 18: exponential public closure policies
  proof surface: `gunray` benchmark/regression and public-surface audit
  fix surface: `gunray/closure.py` and possibly API exposure points
- Issue 19: vacuous-antecedent policy disagreement
  proof surface: `gunray` closure regressions + conformance case
  fix surface: `gunray/closure.py`
- Issue 20: closure faithfulness not established
  proof surface: `datalog-conformance-suite` plus canonical paper examples
  fix surface: `gunray/closure.py` or public contract narrowing
- Issue 21: simplified specificity/defeat semantics
  proof surface: `gunray` / `propstore` targeted examples from intended semantics
  fix surface: `gunray/defeasible.py` and any exposed product contract
- Issue 22: incomplete negative-status sections
  proof surface: `gunray` negative-status coverage regression
  fix surface: `gunray/defeasible.py`
- Issue 23: intentional ASPIC edge-case deviations
  proof surface: `propstore` preference/defeat regressions
  fix surface: `propstore/aspic.py`

## Sequencing Principle

Do the identity and soundness repairs before literature-faithfulness work.

Reason:

- Right now some literals, constants, and grounded rule names do not have stable
  semantics.
- If we try to benchmark closure semantics or ASPIC preference semantics before
  fixing identity, the results are contaminated.

## Tranche 1: Identity And Soundness

This tranche fixes the defects that can directly change derivations or make
behavior depend on encounter order or lossy stringification.

### Workstream A: Constant And Literal Identity

Scope:

- gunray quoted-string parsing
- propstore grounded-literal keying
- query-side goal parsing
- ground-rule naming
- mixed claim-id / ground-atom namespace

Required changes:

1. Stop normalizing quoted strings into numeric/bool scalars in gunray.
2. Replace `repr(GroundAtom)` as the canonical grounded literal key.
3. Introduce a typed structural literal key that includes:
   - predicate
   - argument tuple with preserved scalar types
   - polarity
   - claim-vs-grounded namespace separation
4. Replace `_parse_ground_atom_key()` with a real parser or delete the string
   fallback and require structural query keys at the boundary.
5. Replace `_canonical_substitution_key()` string concatenation with a robust
   escaped or structured encoding.
6. Make grounded undercut targets resolve against stable rule-instance identity,
   not `rule_id#human_rendered_sigma` string coincidence.
7. Add failing regression tests or Hypothesis properties for each accepted
   identity bug before changing implementation.

Files:

- `C:/Users/Q/code/gunray/src/gunray/parser.py`
- `propstore/aspic.py`
- `propstore/aspic_bridge.py`
- `C:/Users/Q/code/datalog-conformance-suite` for any reusable conformance cases

Review items addressed:

- 1, 5, 6, 14, 15, 24, 25

### Workstream B: Parser And Evaluator Soundness

Scope:

- arithmetic associativity
- negation safety
- string literal encoding
- fact arity validation

Required changes:

1. Replace the current recursive split parsing for arithmetic with an actual
   precedence/associativity-aware parse.
2. Reject unsafe negation in gunray validation instead of assigning existential
   wildcard-like runtime meaning.
3. Use a real string-literal encoder in the translator.
4. Make `extract_facts()` validate emitted atoms against the predicate registry.
5. Add failing parser/evaluator tests first, including property coverage where a
   compact algebraic invariant is stronger than one example.

Files:

- `C:/Users/Q/code/gunray/src/gunray/parser.py`
- `C:/Users/Q/code/gunray/src/gunray/evaluator.py`
- `propstore/grounding/translator.py`
- `propstore/grounding/facts.py`
- `C:/Users/Q/code/datalog-conformance-suite` for durable evaluator-facing cases

Review items addressed:

- 2, 3, 12, 13

### Workstream C: Bridge Correctness

Scope:

- strong negation behavior
- query result partitioning
- Dung framework construction
- backend threading
- empty-premise rule handling
- consistent hard-failure discipline for unsupported semantics

Required changes:

1. Keep the existing strong-negation workstream active and treat it as tranche-1
   blocking work, not a later enhancement.
2. Fix `query_claim()` so `arguments_against` means arguments whose conclusion is
   contrary or contradictory to the goal, not merely `!= goal`.
3. Pass `attacks=` into the CSAF framework.
4. Pass the resolved backend through `preferred_extensions(..., backend="brute")`.
5. Do not silently drop empty-premise justifications. Either translate them as
   zero-antecedent rules or reject them loudly at the boundary.
6. Make unsupported phase-crossing semantics fail loudly instead of being partly
   threaded and partly erased.
7. Add failing bridge/query regressions for each accepted defect before fixing
   code.

Files:

- `propstore/aspic_bridge.py`
- `propstore/dung.py`
- `propstore/grounding/translator.py`
- `C:/Users/Q/code/research-papers-plugin` if any caller/import contract must be
  updated to match the corrected boundary

Review items addressed:

- 4, 8, 9, 10, 11, 26

### Workstream D: Goal-Directed Completeness

Scope:

- attacker inclusion logic in `build_arguments_for()`

Required changes:

1. Replace the current two-pass attacker expansion with a fixed-point over attack
   relevance.
2. Add a regression that proves reinstatement chains of depth > 2 are preserved.
3. Keep the subset-of-exhaustive property tests, but add depth-sensitive focused
   correctness cases because the current property tests are too weak to catch
   premature truncation.

Files:

- `propstore/aspic.py`
- `tests/test_backward_chaining.py`
- any focused bridge/query regression tests needed

Review items addressed:

- 7

### Tranche 1 phase gates

Tranche 1 is complete only when all of the following are true:

1. issues `1-15` and `24-26` each have a proving test or property
2. each proving test/property was observed failing before its fix
3. each fix has a green focused rerun
4. each kept slice has been committed and pushed
5. touched repos have been `uv sync`ed before their final verification runs
6. cross-repo boundary suites are green together, not only repo-locally

## Tranche 2: Semantic Policy Audit

This tranche starts only after Tranche 1 is green.

### Workstream E: Strict-Theory And Contrariness Semantics

Required changes:

1. Re-evaluate the `transposition_closure()` choice that drops the full strict
   theory when any singleton closure is inconsistent.
2. Either use the explicit contrariness relation or remove the dead parameter and
   narrow the supported language honestly.

Review items addressed:

- 16, 17

### Workstream F: Closure Policies

Required changes:

1. Decide whether rational / lexicographic / relevant closure remain public
   production policies before a conformance suite exists.
2. Unify vacuous-antecedent semantics across policy implementations.
3. Benchmark and validate the implementations against canonical examples.
4. If the current implementations are only reduced-fragment heuristics, expose
   them as such rather than presenting them as literature-faithful closures.

Review items addressed:

- 18, 19, 20

### Workstream G: Defeasible Status And Preference Semantics

Required changes:

1. Audit negative-status completeness over possible ground instances.
2. Audit specificity and defeat behavior against the intended formal target.
3. Decide whether the current ASPIC edge-case deviations are deliberate product
   semantics or bugs; then either document and rename them, or remove them.

Review items addressed:

- 21, 22, 23

### Tranche 2 phase gates

Tranche 2 is complete only when all of the following are true:

1. issues `16-23` each have a proving regression, property, benchmark, or
   conformance example
2. every public semantic choice is either:
   - implemented and validated against the chosen target semantics, or
   - explicitly narrowed in code/docs as a non-faithful reduced policy
3. any closure/preference policy that remains public has a durable case in
   `datalog-conformance-suite`
4. all resulting repo-local changes are committed and pushed

## Phase-by-Phase Workstream

This is the full execution order for the whole review, not only tranche 1.

### Phase 0: Harness, Sync, And Baseline

1. `uv sync` each repo before work begins:
   - `propstore`
   - `gunray`
   - `research-papers-plugin`
   - `datalog-conformance-suite`
2. capture the current focused baseline in each touched repo
3. create the proving-test backlog issue-by-issue before implementation work

Exit criteria:

- all touched repos are synced
- the proving-test backlog exists for all accepted issues

### Phase 1: Identity proofs and fixes

Issues:

- `1, 5, 6, 14, 15, 24, 25`

Repos:

- `gunray`
- `propstore`
- `datalog-conformance-suite`

Exit criteria:

- all seven issues have red-to-green proofs
- literal identity is structural and namespace-safe
- commits and pushes are complete for this phase

### Phase 2: Parser/evaluator proofs and fixes

Issues:

- `2, 3, 12, 13`

Repos:

- `gunray`
- `propstore`
- `datalog-conformance-suite`

Exit criteria:

- arithmetic, negation safety, escaping, and fact-arity proofs are green
- commits and pushes are complete for this phase

### Phase 3: Bridge and query correctness

Issues:

- `4, 8, 9, 10, 11, 26`

Repos:

- `propstore`
- `research-papers-plugin` if caller or artifact-contract changes are required

Exit criteria:

- strong negation is not silently erased
- query semantics and CSAF/Dung surfaces are coherent
- unsupported semantics fail loudly
- commits and pushes are complete for this phase

### Phase 4: Goal-directed completeness

Issues:

- `7`

Repos:

- `propstore`

Exit criteria:

- attacker inclusion is fixed-point complete for the intended focused query surface
- reinstatement-depth proofs are green
- commit and push are complete

### Phase 5: Strict-theory and contrariness audit

Issues:

- `16, 17`

Repos:

- `propstore`

Exit criteria:

- the strict-theory behavior is either corrected or explicitly narrowed and
  documented with tests
- commit and push are complete

### Phase 6: Closure-policy audit

Issues:

- `18, 19, 20`

Repos:

- `gunray`
- `datalog-conformance-suite`

Exit criteria:

- public closure policies have validated semantics or narrowed contracts
- portable conformance cases exist for the retained public surface
- commits and pushes are complete

### Phase 7: Defeasible-status and preference audit

Issues:

- `21, 22, 23`

Repos:

- `gunray`
- `propstore`
- `datalog-conformance-suite` where the behavior is evaluator-contract level

Exit criteria:

- negative-status and preference behavior is either corrected or deliberately
  specified
- commits and pushes are complete

## Test Plan

### Propstore regression additions

Add focused tests for:

1. grounded literal identity preserving string vs bool/int/float constants
2. opposite literal polarities not aliasing
3. robust ground-atom query parsing or structural query input
4. query `arguments_against` excluding neutral supporters
5. CSAF framework carrying `attacks`
6. preferred backend threading
7. empty-premise rules being either supported or rejected loudly
8. deep reinstatement chain closure for `build_arguments_for()`
9. undercut targeting by authored justification id vs grounded instance id
10. predicate-registry arity enforcement in fact extraction

Each of these should be added before the corresponding implementation change.

### Gunray regression additions

Add focused tests for:

1. quoted strings remaining strings
2. `1-2-3` and mixed arithmetic associativity
3. unsafe negation rejection
4. newline/control-character string round-tripping
5. vacuous-antecedent closure behavior
6. coverage for unsupported-ground-instance classification

Each of these should be added before the corresponding implementation change.

### Conformance-suite additions

Where a bug is evaluator-contract level rather than a purely internal helper
mistake, also add a portable case to `C:/Users/Q/code/datalog-conformance-suite`
once the local repo-specific regression exists.

Priority candidates:

1. quoted constant identity
2. arithmetic associativity
3. unsafe negation rejection
4. empty-premise rule handling
5. vacuous-antecedent closure behavior

### Cross-repo validation

When tranche 1 changes land, re-run the grounding corridor and bridge suites in
propstore plus the affected gunray suites together. The key point is to verify
the shared boundary, not only each repo in isolation.

At the end of each phase, also:

1. `uv sync` each repo touched in that phase
2. rerun the phase-local focused suites
3. push the green commits

## Execution Order

Run the work in this order:

1. Phase 0: harness, sync, and baseline
2. Phase 1: identity proofs and fixes
3. Phase 2: parser/evaluator proofs and fixes
4. Phase 3: bridge and query correctness
5. Phase 4: goal-directed completeness
6. Re-run the grounding/projection plan with the new identity model
7. Phase 5: strict-theory and contrariness audit
8. Phase 6: closure-policy audit
9. Phase 7: defeasible-status and preference audit

Do not start Tranche 2 before Tranche 1 is complete.

Within each workstream, the micro-order is fixed:

1. add the failing proof
2. run it and capture the red result
3. implement the fix
4. rerun focused and nearby regression coverage
5. commit the kept reduction
6. push the kept reduction

## Completion Criteria

This review is not considered handled until all of the following are true:

1. Literal identity is structural and polarity-aware.
2. Quoted constants preserve syntactic identity across the gunray -> propstore
   path.
3. Unsupported semantics fail loudly instead of silently changing meaning.
4. Goal-directed query results are closed under attack relevance.
5. Bridge/query outputs use attack-based conflict metadata consistently.
6. Closure and preference semantics that remain public are either validated
   against a conformance target or explicitly narrowed as non-faithful reduced
   implementations.
7. Every review item `1-26` has a kept proving artifact and a recorded resolution
   in code/tests/docs.
8. All touched repos have been synced, tested, committed, and pushed on their
   final green state.
