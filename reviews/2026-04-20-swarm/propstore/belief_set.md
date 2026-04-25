# belief_set review — 2026-04-20

Scope: `propstore/belief_set/` (627 LOC across 6 source files + README). Tests live at `tests/test_belief_set_postulates.py`, `tests/test_belief_set_iterated_postulates.py`, `tests/test_belief_set_docs.py`, and `tests/test_af_revision_postulates.py`. No dedicated `tests/belief_set/` directory exists.

## Principle Violations

### C1 (CRIT). Fabricated provenance timestamp and status
**File:** `propstore/belief_set/agm.py:125-143`
Every revision trace emits `ProvenanceWitness(asserter="propstore", timestamp="1970-01-01T00:00:00Z", ...)` with `ProvenanceStatus.STATED`. The epoch timestamp is a lie, and `STATED` asserts human-made assertion for what is in fact a derivational operator output. `ProvenanceStatus` already exposes `DEFAULTED` and `VACUOUS` (verified at `propstore/provenance/__init__.py:59-66`). This directly contradicts CLAUDE.md: "every probability-bearing document value that enters the argumentation layer must carry typed provenance... a made-up 0.75 is not" — here a made-up timestamp and a mislabeled status are shipped on every revision. Fix: take a real clock (or explicit `now: datetime` injection) and set `status=DEFAULTED` (or a new `DERIVED` variant) for operator-generated traces.

### C2 (HIGH). Distance fabrication in IC merge for unsatisfiable profile members
**File:** `propstore/belief_set/ic_merge.py:70-78`
When a profile formula has no models, `_distance_to_formula` returns `len(signature) + 1` — a made-up finite rank that lets a contradictory voter still participate in sigma/gmax aggregation on equal footing with satisfiable voters. The honest value is `math.inf` (tuple comparison handles it) or a separate inconsistency signal. Fix: return `math.inf`; or filter inconsistent profile members upstream with an explicit report of exclusion.

### C3 (HIGH). Silent no-op on contradiction input violates non-commitment + AGM success
**File:** `propstore/belief_set/agm.py:77-79`; `propstore/belief_set/iterated.py:21-26`
`revise(state, BOTTOM)` and `lexicographic_revise(state, BOTTOM)` both detect `not satisfying` and return `working_state` unchanged with a trace claiming a revise succeeded. There is no explicit `VACUOUS` opinion emitted, no error, no surface signal. This is exactly the "silent absorb" pattern CLAUDE.md warns against — the caller cannot distinguish "revision completed" from "input was incoherent." Fix: raise, or return `RevisionOutcome` with a flag `inconsistent_input: bool` and vacuous provenance.

### C4 (MED). Workstream code leaks into production provenance
**File:** `propstore/belief_set/agm.py:131`
`source_artifact_code="ws-b-belief-set-layer"` hardcodes the plan/workstream name as the provenance `where` pointer. This conflates deliverable tracking with data lineage and will outlive the workstream. Fix: use a stable module identifier (e.g., `"propstore.belief_set.agm"` plus operator).

## Axiom/Postulate Compliance

### P1 (CRIT). `restrained_revise` is identical to DP bullet revise — postulate claim is false
**File:** `propstore/belief_set/iterated.py:42-52`
Body is `result = revise(state, formula)` followed by a trace rewrap. Docstring claims "Booth-Meyer restrained revision represented by conservative Spohn update." Booth-Meyer 2006 restrained revision has distinctive behavior versus Nayak-Spohn lexicographic and versus DP bullet (it restricts shift to minimally-mu-preferred alpha-worlds among other constraints). The existing test `test_booth_meyer_2006_restrained_revision_preserves_internal_preorders` passes trivially because DP bullet also preserves within-class preorder (formula-worlds get `-min` uniformly; counter-worlds get `+1` uniformly). The admissibility-P test likewise does not separate restrained from bullet revise. The module is shipping a misnamed alias. Fix: implement actual Booth-Meyer, or rename to `spohn_bullet_revise` and delete the docstring claim.

### P2 (HIGH). `full_meet_contract` erases prior entrenchment on output state
**File:** `propstore/belief_set/agm.py:104-110`
After computing `contracted = state.belief_set.intersection_theory(revised_by_negation.belief_set)`, the returned `SpohnEpistemicState.from_belief_set(contracted)` flattens to 0/1 ranks (accepted vs rejected), discarding all ordering from the input `state`. This breaks iterated-contraction analogues of Darwiche-Pearl and any downstream entrenchment queries after a contraction step. Fix: derive the post-contraction ranking from `state`'s ranks restricted to surviving worlds, not a flat 0/1.

### P3 (MED). DP1 not enforced when input is inconsistent
**File:** `propstore/belief_set/agm.py:77-79`
DP1/AGM K*2 (success) requires `K*phi |= phi`. When `phi` is unsatisfiable, the current code returns `state` unchanged, which does not entail phi. The postulate test guards with `assume(_belief(a).is_consistent)` so the axiom gap never fires. Either enforce success (return the inconsistent belief set) or document the intentional guardrail and surface an explicit inconsistency report.

### P4 (MED). IC merge empty-profile case is unspecified and untested
**File:** `propstore/belief_set/ic_merge.py:32-53`
Profile `()` takes the GMAX path to a `()` score and the SIGMA path to `0.0`; all mu-models tie as winners, yielding `Cn = mu`. Konieczny-Pino Pérez IC0 only constrains nonempty profiles, but the behavior is silent and untested. The `st_profile` strategy has `min_size=1`, so the test suite never exercises it. Decide: raise on empty profile, or document the "mu-only" contract and add a test.

### P5 (MED). `lexicographic_revise` does not enforce DP1 on inconsistent input
**File:** `propstore/belief_set/iterated.py:21-26`
Same class as P3 — silent return of unchanged state when formula has no models. DP1/success violated.

### P6 (LOW). Entrenchment EE-5 (tautology is top) is implicit on `float("inf")`
**File:** `propstore/belief_set/entrenchment.py:34-36`
Tautology yields `inf` via the "no countermodels" branch, which makes `leq(a, TOP)` true for any `a`. Correct, but relies on IEEE semantics; no equality-with-inf edge case is tested explicitly.

## Bugs & Correctness Issues

### B1 (HIGH). SIGMA score comparison uses raw float equality, not `_score_key`
**File:** `propstore/belief_set/ic_merge.py:48-49`
`sorted` uses `_score_key(item[1])` but the winners filter uses `score == best_score` against raw `score`. For SIGMA that is `float == float` on sums of ints — usually fine since all distances are ints. But the dual-mode value `float | tuple[int,...]` means the equality semantics are operator-dependent and undocumented. Fix: compare via `_score_key` in both places, or keep scores homogeneous.

### B2 (MED). `_distance_to_formula` rebuilds the world enumeration per (world, formula) pair
**File:** `propstore/belief_set/ic_merge.py:70-78`
For every `(world, formula)` pair we re-enumerate `BeliefSet.all_worlds(signature)` and re-evaluate the formula on each. With profile size p and `|alphabet|=n`, cost is O(p · 2^n · 2^n) instead of O(p · 2^n) after one precompute of models per formula. Not wrong, but O(4^n) in n and silent; tests use n=3 so the explosion is invisible.

### B3 (MED). Duplicate `extend_state` implementations can drift
**File:** `propstore/belief_set/iterated.py:63-71` vs `propstore/belief_set/agm.py:113-121`
Identical logic. `iterated.py` already imports from `agm.py`; no reason to duplicate. Two copies means a future fix to one will silently leave the other broken.

### B4 (LOW). `SpohnEpistemicState` re-bases ranks on every construction, silently
**File:** `propstore/belief_set/agm.py:36-41`
`__post_init__` subtracts `min_rank`. So `from_ranks(alpha, {w1: 5, w2: 10})` yields `{w1: 0, w2: 5}`. Fine as canonical form but undocumented — callers passing "absolute" ranks will not see them preserved. Add a docstring note or drop the re-base.

### B5 (LOW). `fingerprint` uses SHA-1
**File:** `propstore/belief_set/core.py:94-100`
SHA-1 is fine for non-adversarial fingerprints but will trip modern security linters. Consider BLAKE2b or SHA-256.

## Silent Failures

### S1 (HIGH). Inconsistent-input branches return success-shaped outcomes
**Files:** `propstore/belief_set/agm.py:77-79`; `propstore/belief_set/iterated.py:21-26`
Both `revise` and `lexicographic_revise` return `RevisionOutcome` with a normal-looking trace on unsatisfiable input. Caller cannot tell anything went sideways. Already called out as C3/P3/P5; flagging again as the operational symptom.

### S2 (MED). `merge_belief_profile` with impossible integrity constraint returns contradiction silently
**File:** `propstore/belief_set/ic_merge.py:37-41`
If `mu` has no models, returns `BeliefSet.contradiction(signature)` with empty `scored_worlds`. That is a valid IC merge result (IC1: `Delta(E, mu) |= mu`), but it indistinguishable from "merge succeeded on a vacuous mu." No trace, no provenance (unlike `revise` which at least emits a trace). Fix: at minimum, emit a status or raise on `mu` unsat.

### S3 (LOW). `ICMergeOperator` unknown branch is dynamically-raised
**File:** `propstore/belief_set/ic_merge.py:67`
`raise ValueError(f"Unsupported IC merge operator: {operator}")`. StrEnum is closed, so this is unreachable under strict typing — but it also silently skips any exhaustiveness check pyright could enforce. Replace with `assert_never` from `typing`.

## Type Holes

### T1 (MED). `ICMergeOutcome.scored_worlds` uses union type that leaks into callers
**File:** `propstore/belief_set/ic_merge.py:18`
`tuple[tuple[World, float | tuple[int, ...]], ...]` — callers cannot pattern-match without a runtime `isinstance` check. Better: two separate outcome types, or a `Score` NewType with operator-indexed payload.

### T2 (LOW). `_score_world` return type mirrors the same union
**File:** `propstore/belief_set/ic_merge.py:56-67`
Same union leak. Generic over operator would make this typesafe.

### T3 (LOW). `extend_state` parameter name shadows `SpohnEpistemicState.alphabet`
**File:** `propstore/belief_set/agm.py:113`
`def extend_state(state, alphabet: frozenset[str])` — local `alphabet` identifier shadows the state attribute inside the function. Not a bug, but mildly confusing.

### T4 (LOW). Untyped `draw` parameter in hypothesis strategies
**Files:** `tests/test_belief_set_postulates.py:57,66,73`; `tests/test_belief_set_iterated_postulates.py:31`
Strict-mode config may tolerate tests, but `def st_state(draw)` has no type annotation. If the package is in strict mode, these would be holes.

## Dead Code / Drift

### D1 (LOW). `_extend_state` in `iterated.py` is a verbatim copy of `extend_state` in `agm.py`
See B3.

### D2 (LOW). `BeliefSet.cn()` is identity
**File:** `propstore/belief_set/core.py:58-59`
`def cn(self) -> BeliefSet: return self`. Present only to satisfy test `test_agm_1985_cn_is_inclusive_monotonic_and_idempotent` at `tests/test_belief_set_postulates.py:92-93`. Either inline at call site or document that closure is extensional (models representation makes `Cn(K) = K`).

### D3 (LOW). README claims `argumentation` extraction boundary but `tests/test_af_revision_postulates.py` imports from `argumentation.af_revision`
The package appears to already have an argumentation sibling package. README's "this package is formal-adjacent, but it is not part of the initial argumentation extraction" may be stale relative to current layout.

## Positive Observations

- Model-theoretic extensional representation is a clean kernel: every operator is a set operation on `frozenset[World]`. No hidden SAT calls.
- `SpohnEpistemicState.__post_init__` canonicalizes by re-basing to zero minimum rank, which keeps `fingerprint`-like comparisons clean.
- `conjunction`/`disjunction` short-circuit to `BOTTOM`/`TOP` and normalize singletons, which keeps the Formula algebra well-behaved.
- `negate` collapses `Not(Not(x)) → x` preventing boolean-wrapper blowup in iterated revise.
- Postulate tests are Hypothesis-driven with explicit paper citations in function names, matching the CLAUDE.md citation discipline.
- IC merge test covers IC5/IC6 profile decomposition and syntactic-variant invariance (IC2 in spirit).
- Harper identity is implemented and tested against `full_meet_contract` directly (`tests/test_belief_set_postulates.py:146-147`).

## Cross-cutting recommendations (not findings, for your discretion)

1. Unify the inconsistent-input story across `revise`, `lexicographic_revise`, `restrained_revise`, and `merge_belief_profile` — emit a typed inconsistency report, never silently succeed.
2. Replace the fabricated provenance witness with an injected clock and a `DERIVED`/`DEFAULTED` status. If no real witness exists, use `VACUOUS`.
3. Either implement genuine Booth-Meyer restrained revision or rename the function and delete the false postulate claim.
4. Add pyright strict-mode runs scoped specifically to `propstore.belief_set` and test modules; several union types and untyped `draw` parameters will need cleanup.

## Files referenced (absolute paths)

- `C:\Users\Q\code\propstore\propstore\belief_set\__init__.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\agm.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\core.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\entrenchment.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\ic_merge.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\iterated.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\language.py`
- `C:\Users\Q\code\propstore\propstore\belief_set\README.md`
- `C:\Users\Q\code\propstore\propstore\provenance\__init__.py` (for ProvenanceStatus enum verification)
- `C:\Users\Q\code\propstore\tests\test_belief_set_postulates.py`
- `C:\Users\Q\code\propstore\tests\test_belief_set_iterated_postulates.py`
- `C:\Users\Q\code\propstore\tests\test_af_revision_postulates.py`
