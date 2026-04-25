# Gunray Dependency Review

Date: 2026-04-20
Reviewer: analyst subagent
Scope: `C:\Users\Q\code\gunray\src\`, `C:\Users\Q\code\gunray\tests\` (read), docs, papers; cross-referenced against `C:\Users\Q\code\propstore\propstore\grounding\` consumer.

## Purpose & Public Surface

Gunray is a pure-Python defeasible-logic engine. Verified by reading source (not guessed):

- `DefeasibleEvaluator` (`src/gunray/defeasible.py`): García & Simari 2004 DeLP pipeline — `build_arguments` → `build_tree` (Def 5.1 + Def 4.7 acceptable lines) → `mark` (Procedure 5.1) → four-valued projection into `definitely` / `defeasibly` / `not_defeasibly` / `undecided`.
- `SemiNaiveEvaluator` (`src/gunray/evaluator.py`): stratified semi-naive Datalog with Apt-Blair-Walker safety and Nemo existential semantics as alternative.
- `ClosureEvaluator` (`src/gunray/closure.py`): zero-arity KLM rational / lexicographic / relevant closure via Morris-Ross-Meyer 2020 Algorithms 3-5.
- `GunrayEvaluator` (`src/gunray/adapter.py`): dispatcher over `Program | DefeasibleTheory` that routes closure policies to `ClosureEvaluator`, blocking to `DefeasibleEvaluator`, and `Program` to `SemiNaiveEvaluator`. A fallback path into `GunrayConformanceEvaluator` is reached for arbitrary non-schema input.

The public `__init__.py` exports: `GunrayEvaluator`, `DefeasibleEvaluator`, `SemiNaiveEvaluator`, `Answer`, `Argument`, `DialecticalNode`, `DefeasibleModel`, `DefeasibleTheory`, `Model`, `NegationSemantics`, `Policy`, `Program`, `Rule`, `TraceConfig`, `DatalogTrace`, `DefeasibleTrace`, preference criteria, plus the free functions `answer`, `build_arguments`, `build_tree`, `counter_argues`, `proper_defeater`, `blocking_defeater`, `disagrees`, `complement`, `strict_closure`, `explain`, `is_subargument`, `mark`, `render_tree`, `render_tree_mermaid`.

`DefeasibleSections` (used by propstore) is present in `schema.py` but not in `__all__`; propstore reaches it via `from gunray.schema import DefeasibleSections`, which works but is not part of the declared public surface.

## API Contract Issues

### `GunrayEvaluator.evaluate` return type is `object` — all type information lost
**`src/gunray/adapter.py:30-52, 54-82`**

`evaluate` and `evaluate_with_trace` are typed `-> object` / `-> tuple[object, object]`. Consumers have no static way to know that a `Program` input yields `Model`, a `DefeasibleTheory` under `BLOCKING` yields `DefeasibleModel`, etc. Propstore's `grounder.py:177` already has to `cast(DefeasibleModel, evaluator.evaluate(theory, policy))` — runtime-unchecked and invisible to pyright. Severity: MEDIUM. Fix: overloads on `evaluate` keyed by input type and policy, or a union return type `Model | DefeasibleModel`.

### `DefeasibleEvaluator.evaluate` silently accepts and discards `policy`
**`src/gunray/defeasible.py:84`** — `del policy`

Any `policy` value (including closure policies that should have gone to `ClosureEvaluator`, and the deprecated `PROPAGATING`) is silently dropped inside `evaluate_with_trace`. The adapter intercepts closure policies before they reach here, but callers who construct `DefeasibleEvaluator()` directly (which the README advertises at line 103-104: "`DefeasibleEvaluator`, `SemiNaiveEvaluator`, and `ClosureEvaluator` are exported directly if you'd rather skip the dispatcher.") will get wrong-engine behavior with no warning. Severity: MEDIUM. Fix: validate `policy in {Policy.BLOCKING}` and raise `ValueError` for anything else.

### `Rule` / `DefeasibleTheory` are "frozen" but mutable via their list fields
**`src/gunray/schema.py:91-97, 105-145`**

`Rule.body: list[str]` — direct test confirms `Rule(...).body.append("evil")` succeeds on a supposedly frozen+slots dataclass, and `hash(Rule(...))` raises `TypeError: unhashable type: 'list'`. Same for `DefeasibleTheory.strict_rules/defeasible_rules/defeaters/presumptions/superiority/conflicts/facts`. The "frozen" is cosmetic — it blocks attribute *replacement* but not list mutation. Consequences:

1. Rules cannot be put into sets/frozensets (they're unhashable), yet many internal paths assume hashability is cheap.
2. A consumer who mutates `rule.body` post-construction creates an in-flight state drift that `__post_init__`'s validations (presumption-body-empty check, superiority-id check) cannot see.

Severity: HIGH for the immutability claim, MEDIUM for practical impact (no internal code hashes `schema.Rule`). Fix: store as `tuple[str, ...]`, and document the immutability contract.

### `DefeasibleTheory.__post_init__` does not detect duplicate rule IDs
**`src/gunray/schema.py:126-145`**

Directly verified: `DefeasibleTheory(strict_rules=[Rule(id='x',...)], defeasible_rules=[Rule(id='x',...)])` constructs without error. Also `defeasible_rules=[Rule(id='r1',...), Rule(id='r1',...)]` — two different rules, same id, both kept. Downstream, `SuperiorityPreference._closure` is keyed by `rule_id`, `_grounded.*_rules` carries them by id, and argument rule-id display in `_format_rule_ids` sorts by id. Any id collision silently yields wrong preference matching, wrong display, and ambiguous superiority pairs.

Severity: MEDIUM. Fix: in `__post_init__`, assert unique ids across all rule collections.

### `GroundDefeasibleRule` uniqueness of ground keys is lossy
**`src/gunray/_internal.py:181-198`**

`seen: dict[GroundRuleKey, GroundDefeasibleRule]` keys by `(rule_id, head.arguments)`. Two distinct bindings that instantiate the same schema rule to the same head but different bodies (possible when multiple body atoms share arity/vars differently) would clobber each other. The likelihood is low in the current argument pipeline, but the key choice is not obviously correct per the grounding literature — Diller et al. 2025 §3 defines ground instances over the full substitution, not just the head.

Severity: LOW-MEDIUM. Fix: key by `(rule_id, head.arguments, body_arguments_tuple)`.

### `_head_only_bindings` enumerates a full Cartesian product over the constant universe
**`src/gunray/_internal.py:201-219`**

For head-only rules (e.g. presumptions with variables) with N variables and |C| constants the helper returns `|C|^N` bindings with no safety bound. Unsafe by Datalog standards: a presumption with 3 variables over 1000 constants builds a billion bindings. Propstore rule sets are small today, but nothing in the public API warns consumers about this.

Severity: MEDIUM (correctness-safe, but a DoS vector on adversarial theories). Fix: reject head-only rules with un-range-restricted variables, consistent with the `_validate_head` safety check applied to schema-level Datalog rules.

### `KeyError` silently swallowed during grounding
**`src/gunray/_internal.py:183-190`**

```python
try:
    head = ground_atom(rule.head, binding)
except KeyError:
    continue
try:
    body = tuple(ground_atom(atom, binding) for atom in rule.body)
except KeyError:
    continue
```

A `KeyError` from `ground_atom` means a variable in the head/body was not in the binding — which should not happen once variables are collected via `_rule_variable_names` and bindings are fully materialized. Swallowing here silently drops potentially valid ground instances when the grounding pipeline has a bug. No log, no counter, no warning.

Severity: LOW-MEDIUM. Fix: convert to `assert`, or raise `GunrayError` with context.

## Consumer Drift (propstore -> gunray)

### `grounder.py` uses `cast(DefeasibleModel, ...)` because adapter returns `object`
**`propstore/grounding/grounder.py:177`** — calls `evaluator.evaluate(theory, policy)` where `theory: DefeasibleTheory`. Correct at runtime per the adapter's `isinstance` dispatch, but untyped. If adapter behavior changes to return `Model` for any DefeasibleTheory input (e.g. a new closure path silently routed to `Model`), the cast goes unnoticed. Severity: LOW. The hazard is a gunray change, not a propstore bug.

### `grounder.py` imports `from gunray.schema import DefeasibleSections`
**`propstore/grounding/grounder.py:53`**. `DefeasibleSections` is a type alias in `gunray.schema`, not in `gunray.__all__`. The import is legal but depends on a non-declared surface. If gunray reorganizes or moves the alias, propstore breaks. Severity: LOW. Fix: gunray adds `DefeasibleSections` to `__all__`, or propstore reconstructs the alias locally.

### `inspection.py` imports `from gunray.types import GroundDefeasibleRule`
**`propstore/grounding/inspection.py:18`**. `gunray.types` is not exported via the package `__init__.py`. Reading `gunray/types.py` module docstring: `"""Internal immutable syntax and rule-model types for Gunray."""` — marked *internal*. Propstore's `inspection.py` uses this internal type in `_grounded_rules()` (line 135) and `format_ground_rule()` (line 168) as its canonical ground-rule shape. This is consumer-internal coupling: if gunray renames `rule_id` → `id`, restructures `GroundDefeasibleRule`, or moves it, propstore breaks.

Severity: MEDIUM. Fix: either gunray promotes `GroundDefeasibleRule` (and `GroundAtom`, used the same way) to public API, or propstore wraps the returned `bundle.arguments` rules in its own type adapter before use.

### `grounder.py` sorts `gunray.Argument.conclusion.arguments` by `str(arg)`
**`propstore/grounding/grounder.py:238`**. `GroundAtom.arguments: tuple[Scalar, ...]` where `Scalar = str | int | float | bool`. `str(1)` == `str("1")`, so mixing int and string constants between rule-files could collide sort keys. Not a gunray bug, but the propstore workaround is brittle — exposed because gunray's `Scalar` mixing is not prevented anywhere.

### `grounder.py` calls `gunray.build_arguments(theory)` twice when `return_arguments=True`
**`propstore/grounding/grounder.py:176-198`** — first implicitly via `evaluator.evaluate`, then explicitly via `gunray.build_arguments(theory)`. `build_arguments` is not memoized and involves the subset-enumeration-with-pruning loop from `arguments.py:120-160`. Severity: LOW. Fix: propstore-side cache, or gunray exposes the arguments computed by the pipeline in the trace (it already does — `DefeasibleTrace.arguments`).

### Propstore's `translator.py` assumes gunray parser accepts empty body lists
No bug observed — `Rule.__post_init__` permits empty body and `parse_defeasible_rule` loops zero times. Verified against `parser.py:92-100`.

## Correctness vs cited literature

### `DefeasibleEvaluator` section projection deviates from García 04 Def 5.3
**`src/gunray/defeasible.py:184-217`**

The README claims the four sections correspond to Def 5.3 `YES`/`NO`/`UNDECIDED`/`UNKNOWN`. Code maps `yes → defeasibly`, `no or defeater_touches → not_defeasibly`, `strict → definitely`. The `defeater_touches` clause adds a non-paper rule: an atom with a defeater-rule argument lands in `not_defeasibly` even if a warranted argument for its complement does not exist. Nute/Antoniou's defeater reading is cited in `notes/b2_defeater_participation.md`, which is not checked in alongside the tree. This is a conscious deviation per the CLAUDE.md discipline ("defeater-kind reading"), but the four-section mapping diverges from Def 5.3's verbatim wording.

Severity: LOW (documented in CLAUDE.md). Verdict: acceptable, but consumers should know the projection is not the paper's four-valued `Answer` verbatim — propstore's `grounder.py` treats sections as the four-valued answer without surfacing this nuance.

### Defeater arguments exist in the argument universe but are filtered at warrant time
**`src/gunray/defeasible.py:147-168`, `src/gunray/dialectic.py:762-772`**

Two filter points both exclude defeater-kind arguments from warrant. Correct per the documented reading, but if a future agent adds a third entry point (e.g. a public `is_warranted` helper), it must also filter. There is no single choke point. Severity: LOW. Fix: a single predicate on `Argument` like `Argument.can_warrant` (or `is_pure_attacker`).

### `disagrees` closes `Π ∪ {h1, h2}` with facts included — correct per Def 3.3
**`src/gunray/disagreement.py:69-91`**. Matches García 04 Def 3.3 facts-plus-rules. Corresponds to `CLAUDE.md` pitfall "disagrees must see Π facts".

### `GeneralizedSpecificity` empty-rules guard is on both sides symmetrically
**`src/gunray/preference.py:129-130`**. `if not left.rules or not right.rules: return False`. This correctly refuses vacuous domination of strict-only arguments — the pitfall P1-T2 fix.

### `CompositePreference` — first-criterion-to-fire is defensible but not from the paper
**`src/gunray/preference.py:294-389`**. The composition is not taken verbatim from García 04 §4.1 — that paper discusses rule priority and specificity as modular alternatives without specifying how to compose them. Gunray's first-fire semantics is a reasonable design choice (asymmetry preserved) but readers should know this is an *engineering decision*, not a paper-sourced algorithm.

Severity: LOW. Documentation already states this on `CompositePreference.__doc__`.

### `CompositePreference.prefers` evaluates child criteria twice per pair
Lines 368-373: for each child it calls `prefers(left, right)` and `prefers(right, left)`. `explain_preference` (lines 383-389) calls `explain_preference` *and* `prefers(right, left)` per child — that is three calls in the worst case. `GeneralizedSpecificity.prefers` is not cheap (`_covers` does a `strict_closure` fixpoint). No memoization. Severity: LOW-MEDIUM (performance, not correctness). Fix: memoize per `(left, right, criterion)` at the composite.

### `build_arguments` contradiction guard is pre-check on Π, not per-argument
**`src/gunray/arguments.py:87-89`**. Raises `ContradictoryStrictTheoryError` if Pi itself is inconsistent. Per-subset non-contradiction check happens inside the loop (line 149). Matches Def 3.1 cond (2).

### `build_tree` acceptable-line conditions implemented correctly, but O(|universe|^depth)
**`src/gunray/dialectic.py:278-408`**. Def 4.7 conds 2 (concordance), 3 (sub-argument exclusion), 4 (blocking-on-blocking ban) enforced during construction. Cond 1 (finiteness) relies on cond 3 + finite `build_arguments`. Severity: correctness OK, performance fragile — for each candidate defeater at each depth the algorithm re-runs `_defeat_kind` which itself iterates `_disagreeing_subarguments` over the whole universe. No memoization at the tree level.

### `strict_closure` is O(R^2) per call with no memoization
**`src/gunray/disagreement.py:41-66`**. Runs a while-changed loop over every strict rule per call. Called by `_concordant_rules` on every tree-expansion step. The `_concordant_rules` cache keys are `frozenset[GroundDefeasibleRule]`, and the cache *is* threaded through `build_tree`, but each call to `GeneralizedSpecificity._covers` creates a fresh `strict_closure` invocation — no cache there. Severity: LOW-MEDIUM.

### `stratify` does not gate on positive-cycle detection through negative edges
**`src/gunray/stratify.py:46-49`**. Negative-cycle detection only checks direct same-SCC membership. Chained negation that crosses a positive edge to come back negatively is caught by Tarjan's SCC treating negative edges as graph edges (lines 102-107), so it's fine, but combining positive and negative adjacency into one `neighbors` set for Tarjan means the SCC groups over *both* — which is the correct reading of stratifiability (no negation in a cycle) but is not spelled out in a comment.

Severity: LOW / documentation.

### `closure.py` `_ranked_defaults` implements Algorithm 3 but the loop exit condition is "no rank added"
**`src/gunray/closure.py:173-183`**. Ivy-style exceptional-rank partitioning. Exits when `current_rank` is empty, after which `remaining` becomes `infinite_rank`. Matches Morris-Ross-Meyer 2020 p.150 Algorithm 3 if `_branch_satisfiable` is correctly a classical-satisfiability check; not audited further.

## Silent Failures

1. **`src/gunray/defeasible.py:84`** — `del policy` in `DefeasibleEvaluator.evaluate_with_trace`. Any non-BLOCKING policy passed directly is silently ignored. See API Contract Issues.
2. **`src/gunray/_internal.py:183-190`** — `KeyError` from `ground_atom` silently swallowed; ground instance dropped with no counter/log.
3. **`src/gunray/_internal.py:557, 575, 579, 626`** — `SemanticError` caught and translated to "no value" / "constraint fails". Four separate sites. Correct per arithmetic semantics (type errors collapse to "constraint doesn't hold") but the behavior is indistinguishable from legitimate non-matches; a buggy expression silently never fires.
4. **`src/gunray/schema.py`** — duplicate rule IDs silently accepted across/within rule collections.
5. **`src/gunray/schema.py`** — `Rule.body.append()` mutates "frozen" dataclass silently.
6. **`src/gunray/adapter.py:15-28`** — `GunrayEvaluator._bridge` lazy construction mutates the bridge's private `_core` attribute. If the conformance_adapter refactors `_core` away, construction silently succeeds but `self._bridge.evaluate(...)` has unexpected engine-sharing behavior.

## Bugs

### BUG 1 — `Rule` "frozen" semantics is broken
**`src/gunray/schema.py:91-97`** (severity HIGH for the immutability contract; MEDIUM for downstream impact)

Direct reproduction:
```
Rule(id='x', head='p', body=['q']).body.append('evil')  # succeeds
hash(Rule(id='x', head='p', body=['q']))  # TypeError: unhashable type: 'list'
```

`DefeasibleTheory` has the same shape on all six list fields. The `frozen=True, slots=True` decoration blocks attribute replacement but does not make the list fields immutable. Fix: use `tuple[str, ...]` for `body` and all list fields, adjust construction call sites.

### BUG 2 — Duplicate rule IDs silently accepted
**`src/gunray/schema.py:126-145`** (severity MEDIUM)

Repro above. `SuperiorityPreference._closure` is keyed by `rule_id`; two rules sharing an id cause preference ambiguity. Fix: `__post_init__` should aggregate all rule IDs and raise `ValueError` on collisions.

### BUG 3 — `_head_only_bindings` is unbounded on the constant universe
**`src/gunray/_internal.py:201-219`** (severity MEDIUM — DoS surface)

No safety gate for head variables in bodyless rules. `|C|^N` Cartesian product. Fix: require head variables in non-presumption rules to be range-restricted, or raise `UnboundVariableError` at grounding time rather than enumerating.

### BUG 4 — `GunrayEvaluator._suite_bridge` accesses conformance bridge private `_core`
**`src/gunray/adapter.py:21-28`** (severity LOW)

```python
bridge._core = self  # reuse this evaluator's engines
```

Writes `self._bridge._core = self` with `# type: ignore[attr-defined]` elsewhere. If `GunrayConformanceEvaluator` renames `_core`, this silently succeeds (attribute set on the new object) but the bridge uses its original `_core` and no engine sharing occurs. Fix: expose a public `set_core(evaluator)` method on the conformance adapter.

### BUG 5 — `DefeasibleEvaluator.evaluate` discards `policy` parameter
**`src/gunray/defeasible.py:84`** (severity MEDIUM — wrong-engine risk)

`del policy` silently accepts any input including closure policies that should raise or route elsewhere. See API Contract Issues.

### BUG 6 — `evaluator.py` cast from `set[tuple[object, ...]]` to `set[FactTuple]`
**`src/gunray/evaluator.py:73-76`**: `cast(set[FactTuple], relation.as_set())`. `FactTuple = tuple[Scalar, ...]` where `Scalar = str | int | float | bool`, but `IndexedRelation` stores `tuple[object, ...]`. The cast is a type-system lie: relations actually carry whatever `object` the parser produced. Arithmetic results (`semantics.add_values`) can produce values outside the declared `Scalar` set.

Severity: LOW. Fix: define a normalized output type or narrow the relation element type at the storage boundary.

### BUG 7 — `DefeasibleEvaluator._evaluate_strict_only_theory_with_trace` runs full Datalog before consistency check
**`src/gunray/defeasible.py:268-289`**

`_raise_if_strict_pi_contradictory` runs *after* `SemiNaiveEvaluator().evaluate_with_trace` completes. An adversarial strict theory with an explosive rule set still pays the full fixpoint cost before being rejected.

Severity: LOW (availability, not correctness).

### BUG 8 — `GroundDefeasibleRule` ground-key uniqueness is head-only
**`src/gunray/_internal.py:191`**: `key = (rule.rule_id, head.arguments)`. Two bindings that ground to the same head but different bodies overwrite. See API Contract Issues.

## Dead Code

- **`src/gunray/adapter.py:52`, `src/gunray/adapter.py:82`, `src/gunray/adapter.py:92`** — `_suite_bridge().evaluate(item, policy)` fallback is only reachable when `item` is neither `Program` nor `DefeasibleTheory`. The conformance adapter will raise for unexpected types (`TypeError Unsupported input type: dict`), but the fallback existing at all suggests legacy compatibility.
- **`src/gunray/preference.py:58-60`** — `TrivialPreference.explain_preference` always returns `None`. Present for protocol conformance; no real consumer. OK to keep, but note it's only used in tests.
- **`src/gunray/_internal.py:640-657`** — `_apply_rule_with_overrides` wrapper that imports `apply_rule_with_overrides` from `evaluator` and forwards — an artefact of the module-extraction refactor. Not dead but adds an extra function-call hop.

## Positive Observations

- **Documentation discipline is excellent.** Every non-trivial function cites the paper definition and page number. `notes/` and `reviews/2026-04-16-full-review/` capture prior audit findings; `CLAUDE.md` lists the specific pitfalls that previously broke (strict-only fast path Π consistency, GS empty-rules, `disagrees` needing facts) and each is addressed in code with a comment at the relevant site.
- **Literature grounding is load-bearing and verifiable.** `CITATIONS.md` names which paper definition each module implements; spot checks (`disagreement.py` vs Def 3.3, `preference.py` vs Simari-Loui Lemma 2.4, `arguments.py` vs Def 3.1) track correctly.
- **Non-destructive layering.** `_internal.py` is the shared helpers point; peer modules don't import each other's private names (pitfall documented in `CLAUDE.md`).
- **`ContradictoryStrictTheoryError` is a typed failure** with a stable `code = "contradictory_strict_theory"`, consumable by conformance harnesses.
- **Def 4.7 acceptable-line conditions are enforced during tree construction**, not post-hoc. This prevents the class of bugs where the marking walks a malformed tree.
- **Presumptions are first-class** (`h -< true`) with an empty-body invariant enforced in `DefeasibleTheory.__post_init__`.
- **Propstore's consumer layer is well-written.** `grounder.py:242-292` re-normalizes gunray's dropped-empty sections back to the four-section non-commitment shape, aligning with propstore's CLAUDE.md design principle. The provenance chain (rule_files, facts, sections, arguments) is preserved in the `GroundedRulesBundle`.

## Summary of severities

- HIGH: `Rule`/`DefeasibleTheory` mutable-list frozen contract (BUG 1).
- MEDIUM: duplicate rule IDs silently accepted (BUG 2); `DefeasibleEvaluator` silently discards policy (BUG 5); `_head_only_bindings` unbounded (BUG 3); `GunrayEvaluator.evaluate` return type `object` loses types; propstore uses non-public `gunray.types.GroundDefeasibleRule`.
- LOW-MEDIUM: `GroundDefeasibleRule` head-only ground key (BUG 8); `strict_closure` re-computation cost; KeyError silently swallowed in `_ground_rule_instances`.
- LOW: conformance bridge private `_core` access (BUG 4); strict-only contradictory check after full Datalog (BUG 7); `Set[FactTuple]` cast lies (BUG 6); `DefeasibleSections` not in `__all__`; propstore double-calls `build_arguments`.

No show-stoppers for the propstore consumer; the most user-visible fragility is (1) the "frozen" dataclass mutability misrepresentation and (2) propstore's dependence on a module (`gunray.types`) that gunray internally marks as not public.
