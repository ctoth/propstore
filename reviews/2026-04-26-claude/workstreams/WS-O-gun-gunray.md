# WS-O-gun: gunray fixes — defeasible Datalog grounder (existing bugs + anytime wire-up)

**Status**: CLOSED v0.1.0
**Depends on**: nothing internal — gunray is a sibling repo at `../gunray`.
**Blocks**: nothing strict, but every cluster R finding rolls into propstore via the `gunray` pin in `pyproject.toml`. WS-M's gunray-boundary fix
(propstore consumer side) wants the gunray-side fixes here landed and tagged first; coordinate so that propstore lands the new pin in the same window.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)
**Repo**: this workstream lives in `../gunray`. The propstore-side propagation is in WS-M.
**Sibling sub-stream**: `WS-O-gun-garcia.md` — Garcia 2004 generalized-specificity rewrite of the grounding/defeasibility module (per D-17).
This WS does NOT cover the section-projection rewrite; everything that touches `not_defeasibly` semantics moves there.

---

## Why this workstream

gunray is the defeasible Datalog grounder that propstore calls through `propstore/grounding/grounder.py` and `propstore/grounding/translator.py`. Cluster R
(read every file under `C:\Users\Q\code\gunray\src\gunray\` plus all consumer files in propstore) found a tight cluster of bugs that all bite the
same propstore call site:

- `gpr ground` becomes unusable on theories of more than ~30 grounded defeasible rules because of two compounding exponential blowups (HIGH-1, HIGH-2).
- propstore re-grounds the theory twice on every ground call (HIGH-3), so even small theories pay double.
- A handful of smaller correctness and clarity issues (MED-2/3/5/6/7, all LOW items) accrete into a public surface that is hard to trust.
- The `EnumerationExceeded` sentinel is exported but unreachable today (LOW-2). Per D-18 it gains real wiring: gunray's `evaluate` accepts a
  `max_arguments` budget and raises with partial result on overflow; propstore catches and surfaces `ResultStatus.BUDGET_EXCEEDED`. This becomes
  the principal escape hatch when HIGH-1's exponential rule-set still bites adversarial theories after the perf work in step 2.

The **section-projection paper-fidelity question** (was MED-4 here) has been promoted out of WS-O-gun: per D-17 Q chose a full Garcia 2004
generalized-specificity rewrite rather than the smaller "split sections vs Antoniou" patch. That work lives in WS-O-gun-garcia and runs as a
separate sub-stream. This WS deliberately leaves `defeasible.py`'s section projection alone — touching it would conflict with the rewrite.

Cluster R is the only cluster where every HIGH item is a perf or determinism cliff that ships through to propstore unchanged. Closing it ahead of
WS-M's boundary fix is cheap engineering hygiene; closing it after means re-doing the WS-M boundary contract once gunray gets its own argument
accessor.

---

## Findings covered

Every Cluster R HIGH and the remaining MEDs are closed in this workstream. LOWs are bundled because they're cheap and they live in the same files.
"Done means done" — each row below has a green test in `../gunray/tests/` (path noted), and each row gets its own micro-commit on a `ws-o-gun` branch.

### HIGH

| ID | Title | Source citation | Description |
|---|---|---|---|
| **HIGH-1** | `build_arguments` exponential | `cluster-R-gunray.md` lines 237-256 | `arguments.py:_has_redundant_nonempty_subset` runs `O(\|rule_set\|)` memoization-free strict closures per candidate. The outer loop in `build_arguments:131-159` iterates every product of support sets across the body atoms, so a `k`-rule chained theory pays `2**O(k)` candidate combinations × `O(k)` redundancy checks × an `O(k * \|strict_rules\|)` strict closure. The `pi_closure` is precomputed once but per-candidate closures are not. The dialectical tree's `_concordant_rules` cache (`dialectic.py:309`) is **per-tree** rather than **per-theory**, so during the `_evaluate_via_argument_pipeline` outer loop the same closure is recomputed across every root tree. |
| **HIGH-2** | `disagrees` re-grounds entire theory on every call inside `counter_argues` | `cluster-R-gunray.md` lines 258-271 | `dialectic.counter_argues` (lines 89-113) calls `_theory_strict_rules` and `_theory_pi_facts` on every invocation. Both re-parse the theory via `parse_defeasible_theory` and re-ground via `_positive_closure_for_grounding` and `_ground_rule_instances`. Tree construction calls `counter_argues` / `_disagreeing_subarguments` up to `O(N²)` times per root tree; the `_evaluate_via_argument_pipeline` outer loop multiplies that by `N` again. So the entire grounding pass runs `O(N³)` times per pipeline call on top of HIGH-1. |
| **HIGH-3** | propstore re-grounds twice (`evaluate` + `inspect_grounding`) | `cluster-R-gunray.md` lines 272-282; `propstore/grounding/grounder.py:170-171` | `evaluator.evaluate(theory, policy)` (line 170) internally grounds the theory via `_ground_theory`. The very next line `gunray.inspect_grounding(theory)` reparses and re-grounds via its own `parse_defeasible_theory` / `_positive_closure_for_grounding` pass (`gunray/grounding.py:73-121`). The fact that two parallel grounders exist (`_internal._ground_theory` and `inspect_grounding`'s standalone path) is itself the underlying gunray smell that causes the propstore double-call. The boundary contract should be: gunray exposes one grounder; the trace carries the inspection. |

### MED

| ID | Title | Source citation | Description |
|---|---|---|---|
| **MED-2** | `mark()` not memoized | `cluster-R-gunray.md` lines 320-334; `dialectic.py:411-427` | The public `mark()` recurses on every `DialecticalNode` without memoization. In gunray's tree construction the same sub-argument can be a child of multiple nodes (every defeater of a node can also be a defeater of a sub-argument), so trees can have shared children. The `_mark_table` helper at `dialectic.py:488-504` *does* memoize but is only used by the renderer and `explain()`. The public `mark()` walks the tree naively and can be exponential in the worst case. |
| **MED-3** | Cross-module private-name leak in `grounding.py` | `cluster-R-gunray.md` lines 336-348; `ARCHITECTURE.md:196-200`; `gunray/grounding.py:8-11, 137` | ARCHITECTURE.md's pitfall section forbids cross-module private imports. `_internal.py` is positioned as the shared sink, so `dialectic.py` importing from it is fine. **But** `grounding.py` imports `_ground_rule_instances_with_substitutions` and `_positive_closure_for_grounding` from `_internal` and re-exports their *outputs* through public types (`GroundRuleInstance`, `GroundingInspection`). If `_ground_rule_instances_with_substitutions` ever changes its return shape, `grounding.py:_public_substitution` (line 137) silently breaks the public surface. |
| ~~**MED-4**~~ | ~~`not_defeasibly` semantics has no García 04 backing~~ | **MOVED to WS-O-gun-garcia** per D-17 | This finding originally proposed splitting sections (Option A) vs pinning Antoniou 2007 (Option B). Q rejected both as patches and chose a full Garcia 2004 generalized-specificity rewrite as a separate sub-stream. See `WS-O-gun-garcia.md`. **WS-O-gun does NOT touch `defeasible.py:196-229` section projection or `CITATIONS.md` Antoniou/Garcia entries.** |
| **MED-5** | `build_grounding_text_explanation` falls back silently to complement | `cluster-R-gunray.md` lines 369-378; `propstore/grounding/explanations.py:43-53` | The propstore explainer tries the requested atom's predicate, then if that fails, tries `_complement_predicate(atom.predicate)`. If the complement *is* found, the user is told an explanation for an atom they did not ask about — the only signal is that `explained_atom != requested_atom`. There is no error message or warning. For a propstore caller that asks "explain `flies(opus)`" and gets an explanation for `~flies(opus)`, this is misleading. |
| **MED-6** | `superiority` validation does not detect cycles or self-pairs | `cluster-R-gunray.md` lines 380-393; `schema.py:164-170`; `preference.py:225-253` | `schema.DefeasibleTheory.__post_init__` checks every referenced rule id exists, but does not check that the pair list is acyclic, and does not reject `(r1, r1)` self-pairs. The downstream `SuperiorityPreference.__init__` computes the transitive closure with a Floyd-Warshall-style loop; if `(r1, r2)` and `(r2, r1)` are both supplied, the closure produces both `(r1, r1)` and `(r2, r2)`, so `prefers(arg_with_r1, arg_with_r2)` becomes `True` *and* `prefers(arg_with_r2, arg_with_r1)` becomes `True`, violating the strict-partial-order axiom that `CompositePreference.__doc__` claims is a precondition. `tests/test_superiority.py` cannot catch this because its property fixtures don't generate cyclic input. |
| **MED-7** | Strict-only fast path drops the argument view | `cluster-R-gunray.md` lines 395-404; `defeasible.py:280-301` | `_evaluate_strict_only_theory_with_trace` builds a `DefeasibleModel` with only `definitely` and `defeasibly` sections (mirrored). It does NOT populate the trace's `arguments`, `trees`, or `markings`. So a propstore caller that asked for `return_arguments=True` on a strict-only theory gets an empty argument tuple — no way to enumerate the trivial single-rule strict arguments even though `build_arguments` would have produced `Argument(rules=frozenset(), conclusion=h)` for every strict consequence. Inconsistent with the documented "argument view is opt-in" contract. |

### LOW

Bundled into the same workstream because they live in the same files and are mostly one-liners.

| ID | Title | Source citation | Description |
|---|---|---|---|
| **LOW-1** | `CITATIONS.md` miscategorises Diller 2025 | `cluster-R-gunray.md` lines 408-416; `CITATIONS.md:83-86`; `grounding.py:153-195` | Diller 2025 is in "Contextual (shaped design, not directly implemented)" with the comment "Gunray enumerates arguments directly from DeLP rules rather than compiling through ASPIC+." But `grounding.py:_simplify_strict_fact_grounding` (lines 153-195) *is* a partial Diller Algorithm 2 implementation; its own docstring at lines 163-168 says "the conservative DeLP-compatible fragment" of Diller. The citation should reflect that, and the docstring should pin to specific theorem / page numbers from `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md` (note the trailing hyphen in the directory name). |
| **LOW-2** | `anytime.EnumerationExceeded` wired to nothing | `cluster-R-gunray.md` lines 418-426; `_internal.py:228-287` | **Resolved decision: D-18 — wire it up.** `EnumerationExceeded` is exported in `__init__.py:5`, used as a return type only by `_head_only_bindings(max_candidates: int)` overload. No public caller passes a budget today. Per D-18: `gunray.evaluate` (and `evaluate_with_trace`) gain a `max_arguments: int \| None = None` parameter; `build_arguments` accepts and threads it; on overflow gunray raises `EnumerationExceeded` carrying the partial argument tuple already built. propstore's `propstore/grounding/grounder.py` catches and surfaces `ResultStatus.BUDGET_EXCEEDED` to its caller (instead of letting the exception propagate or returning a misleading "complete" result). This is the anytime escape hatch HIGH-1's exponential rule-set needed; without it the only recourse on adversarial theories is wall-clock timeout. |
| **LOW-4** | Parser rejects `p()` | `cluster-R-gunray.md` lines 438-444; `parser.py:345-354`; `propstore/grounding/translator.py:251-262` | `_find_atom_argument_bounds` demands non-empty inner content between parens. The translator must work around this by emitting `p` rather than `p()` for arity-0 atoms. The output is asymmetric: bareword for arity-0, parens for arity ≥ 1. A better-behaved parser would accept either. |
| **LOW-6** | `_collect_conflicts` ignored everywhere except strict fast path | `cluster-R-gunray.md` lines 454-464; `parser.py:283-303`; callers at `_internal.py:77`, `grounding.py:76`, `dialectic.py:71, 85` | `parser.parse_defeasible_theory` returns `(facts, rules, conflicts)`. Every caller in the codebase destructures with `_conflicts` (underscore-ignored). The conflict set is computed and discarded everywhere except `_raise_if_strict_pi_contradictory` in the strict-only fast path. Either propagate it through `_GroundedTheory` so the dialectical pipeline can use it, or stop computing it. |
| **LOW-7** | `Policy` enum mixes orthogonal concerns | `cluster-R-gunray.md` lines 466-475; `schema.Policy` | `Policy` has `BLOCKING`, `RATIONAL_CLOSURE`, `LEXICOGRAPHIC_CLOSURE`, `RELEVANT_CLOSURE`. The first selects a dialectical-tree marking discipline; the last three dispatch to a totally different evaluator (`closure.ClosureEvaluator`). `defeasible.py:55-59` and `adapter.py:59-64` use set-membership in `_CLOSURE_POLICIES` to route. Two unrelated choices share one type; a consumer that wants to set a marking policy and a closure policy independently has no way to express it. Refactor as two enums. |

### Architecture cluster

These are not numbered HIGH/MED in the cluster but they are the underlying smells that make HIGH-3, MED-3, and LOW-1 possible. They fall in scope here.

| ID | Title | Source citation | Description |
|---|---|---|---|
| **ARCH-1** | Two parallel `Rule` types | `cluster-R-gunray.md` lines 38-46; `schema.py:93-105` (id/head/body strings); `types.py:62-67` (heads/positive_body/negative_body/constraints/source_text) | `schema.Rule` is the user-authored surface; `types.Rule` is the parsed structured form. Translation happens in `parser.py`. Round-trip through strings means provenance ties to the original `RuleDocument` are limited to the `id`. |
| **ARCH-2** | Two parallel grounders | `cluster-R-gunray.md` HIGH-3 root cause; `_internal._ground_theory` vs `grounding.inspect_grounding`'s `_positive_closure_for_grounding` standalone path | These should share one entry point. `inspect_grounding` should ride on the trace from `evaluate_with_trace` rather than re-parsing and re-grounding. |
| **ARCH-3** | `closure.py` propositional-only | `cluster-R-gunray.md` line 105 ("zero arity only"); `closure.py:134-157` (`_ensure_propositional`, `_ensure_zero_arity_literal`) | The closure engine raises `ValueError` on arity ≥ 1 atoms or facts. Any first-order use of KLM closure routes through the DeLP path instead. The KLM machinery (Kraus 1990, Lehmann 1989, Morris 2020) does not in principle restrict to zero arity — this is a gunray scope cap, documented but unaddressed. |
| **ARCH-4** | `ARCHITECTURE.md` drift | `cluster-R-gunray.md` LOW-1 / MED-3 cross-cite | The doc says "no cross-module private imports" but `grounding.py` does this (MED-3); the doc says "Block 1 is correctness-first" in `dialectic.py:34` but Block 2+ has happened (HIGH-1 / HIGH-2 perf gaps documented but unaddressed). Doc should be updated to reflect the current contract or the contract should be updated to match the doc. |

### Boundary

The propstore→gunray translator and the gunray→propstore evaluate path together form the boundary. WS-M owns the propstore side; this WS owns the
gunray side. Keep them in lockstep.

| ID | Title | Source citation | Description |
|---|---|---|---|
| **BND-1** | propstore→gunray translator flattens documents to surface strings | `cluster-R-gunray.md` lines 152-163; `propstore/grounding/translator.py:78-185, 228-262` | `RuleDocument` carries metadata about authoring (file, justification, source quote) that propstore considers load-bearing per the `imports_are_opinions` principle. The translator stringifies head and body atoms via `_stringify_atom`. The `RuleDocument.id` is preserved as `gunray.Rule.id`, so the rule-id-as-handle works, but every other piece of `RuleDocument` provenance is dropped. Atom-level provenance (which `AtomDocument` came from which import row, with what confidence) is rendered to the surface string and erased beyond what `gunray.parser` can recover. |
| **BND-2** | gunray→propstore evaluate path discards `DefeasibleTrace` | `cluster-R-gunray.md` lines 137-146; `defeasible.py:71-77`; `propstore/grounding/grounder.py:170` | The bare `evaluate` path throws the trace away (the wrapper unpacks `model, _ = self.evaluate_with_trace(...)`). Propstore's `ground` calls `evaluator.evaluate(theory, policy)`, the non-trace entry point, so `DefeasibleTrace.arguments`, `.trees`, `.markings` are discarded. Then separately calls `gunray.inspect_grounding(theory)` (HIGH-3), which itself does not carry the trace — only the grounded rule instances. Result: argument-level provenance never reaches the propstore caller unless `return_arguments=True` is explicitly threaded, and even then the path is `build_arguments(theory)` (a third grounding pass). The fix: gunray exposes one grounder, `evaluate_with_trace` carries `GroundingInspection` on the trace, propstore reads it from there. |
| **BND-3** | `gunray.DefeasibleTheory.conflicts` is unused by propstore | `cluster-R-gunray.md` lines 184-191; `propstore/grounding/translator.py:184` | `conflicts=()` is hardcoded in the translator. `gunray.DefeasibleTheory.conflicts` is the slot the strict-only fast path uses to detect predicate-pair contradictions beyond strong-negation `~p` vs `p`; propstore never populates it. This is a missed channel for domain-asserted incompatibilities (e.g. propstore's `incompatible_with` predicates). Fix: WS-M wires it; this WS makes sure the gunray side accepts and honors it on the dialectical pipeline as well as the strict fast path (closing LOW-6 simultaneously). |

---

## Resolved decisions

These were "Open question for Q" in the prior draft. Both are now closed by the 2026-04-27 decisions log.

- **D-17 (was MED-4 not_defeasibly)**: Full Garcia 2004 rewrite as a separate sub-stream `WS-O-gun-garcia`. WS-O-gun does NOT touch section
  projection. WS-O-gun-garcia is the highest-fidelity path and supersedes both Option A (split sections) and Option B (pin Antoniou 2007).
- **D-18 (was LOW-2 anytime)**: Wire `EnumerationExceeded` through `evaluate(..., max_arguments=N)` and have propstore catch it and surface
  `ResultStatus.BUDGET_EXCEEDED`. Step 9 below implements this.

---

## First failing tests (write these first; they MUST fail before any production change)

All paths are relative to `../gunray/tests/` unless noted. Add `@pytest.mark.property` to every Hypothesis-`@given` test per the WS-A property-marker
discipline, which the gunray repo also adopts (it's the same `pytest -m property` selector).

1. **`tests/test_build_arguments_perf_bound.py`** (new — HIGH-1, HIGH-2)
   - Generates a chained theory of `k=20` defeasible rules where each rule's body uses the previous rule's head.
   - Runs `build_arguments(theory)` under a wall-clock budget (`time.perf_counter()`, threshold ~2 seconds on CI hardware).
   - Then re-runs through `_evaluate_via_argument_pipeline` and asserts the per-tree `_concordant_rules` cache is shared across the outer loop's
     trees (assert call count for `strict_closure` is `O(k)` not `O(k²)` via a wrapper).
   - **Must fail today**: a 20-rule chain currently takes seconds because of the per-candidate redundancy closure and the per-tree concordance cache.

2. **`tests/test_inspect_grounding_via_trace.py`** (new — HIGH-3 + ARCH-2)
   - Calls `evaluator.evaluate_with_trace(theory, policy)` and asserts the returned trace has a `grounding_inspection` field of type `GroundingInspection`.
   - Asserts that calling `inspect_grounding(theory)` separately returns the same value (round-trip equality), so the public function still exists
     but is now a thin reader over the trace.
   - **Must fail today**: trace has no `grounding_inspection` slot; the standalone `inspect_grounding` re-runs `parse_defeasible_theory`.

3. **`tests/test_mark_memoized.py`** (new — MED-2)
   - Constructs a `DialecticalNode` whose tree has shared children (the same sub-argument is a child of two parents).
   - Wraps `mark` with a counting decorator and asserts the recursion visits each unique node at most once.
   - **Must fail today**: `mark` recurses without memoization.

4. **`tests/test_grounding_no_private_imports.py`** (new — MED-3)
   - AST-walks `src/gunray/grounding.py` and asserts no `ImportFrom` from `._internal` of names beginning with `_`.
   - **Must fail today**: imports `_ground_rule_instances_with_substitutions` and `_positive_closure_for_grounding`.

5. **`tests/test_explanation_no_silent_complement.py`** (new — MED-5; in propstore-side WS-M but cross-link here)
   - Calls `build_grounding_text_explanation` with an atom for which only the complement has a tree.
   - Asserts the returned `GroundingTextExplanation.message` is a non-`None` warning that names the requested atom AND the complement explicitly.
   - **Must fail today**: silent fallback, `message=None`.

6. **`tests/test_superiority_validates_acyclic.py`** (new — MED-6)
   - Builds a theory with `superiority=(("r1","r2"), ("r2","r1"))` and asserts `DefeasibleTheory.__post_init__` raises `ValueError`.
   - Builds a theory with `superiority=(("r1","r1"),)` and asserts `__post_init__` raises `ValueError`.
   - Hypothesis property: for any acyclic input, `SuperiorityPreference._closure` is irreflexive and antisymmetric.
   - **Must fail today**: schema validation only checks rule-id existence.

7. **`tests/test_strict_only_argument_view.py`** (new — MED-7)
   - Builds a strict-only theory with two strict rules deriving the same fact from disjoint chains.
   - Calls `evaluate_with_trace` and asserts `trace.arguments` contains both `Argument(rules=frozenset(), conclusion=h)` entries (one per chain).
   - **Must fail today**: strict-only fast path leaves trace.arguments as `()`.

8. **`tests/test_anytime_budget_exhausted.py`** (new — LOW-2 / D-18)
   - **Gunray side**: builds an adversarial chained theory designed to make `build_arguments` enumerate >`max_arguments` candidates. Calls
     `evaluator.evaluate(theory, policy, max_arguments=8)` and asserts `EnumerationExceeded` is raised. Asserts the exception's
     `partial_arguments` field is a non-empty tuple of `Argument` and that `len(partial_arguments) <= 8`. Asserts a `reason` string is set.
   - **Gunray side, with-trace**: same theory through `evaluate_with_trace(theory, policy, max_arguments=8)`. Asserts `EnumerationExceeded` raised
     with the same partial result and that, if the trace was partially built, it is attached to the exception (not silently dropped).
   - **Propstore side** (`propstore/tests/test_grounder_budget_exceeded.py`, owned by WS-M but cross-linked from this WS): calls
     `Grounder.ground(theory, max_arguments=8)`, asserts the returned result has `status == ResultStatus.BUDGET_EXCEEDED` and a partial-argument
     view, and that no exception escapes the propstore boundary.
   - **Must fail today**: `evaluate` does not accept `max_arguments`; `EnumerationExceeded` is never raised by any public function;
     `ResultStatus.BUDGET_EXCEEDED` does not exist in propstore.

9. **`tests/test_parser_accepts_p_parens_arity_zero.py`** (new — LOW-4)
   - Asserts `parse_atom_text("p()")` returns the same `Atom` as `parse_atom_text("p")`.
   - **Must fail today**: raises `ParseError`.

10. **`tests/test_conflicts_threaded_to_dialectical_path.py`** (new — LOW-6 + BND-3)
    - Builds a theory with `conflicts=(("ferry", "fly"),)`, two defeasible chains derive `ferry(opus)` and `fly(opus)` respectively, no strong negation
      between them.
    - Asserts `evaluate(theory, BLOCKING)` does NOT put both atoms in `defeasibly` simultaneously — the conflict pair must propagate to the
      dialectical pipeline. Exact section assignment depends on the WS-O-gun-garcia rewrite; this test asserts only the no-double-warrant invariant
      so it is stable across both the current section names and the post-Garcia ones.
    - **Must fail today**: dialectical pipeline ignores `conflicts`; both atoms warrant.

11. **`tests/test_policy_split_enums.py`** (new — LOW-7)
    - Asserts `MarkingPolicy` has only `BLOCKING`.
    - Asserts a separate `ClosurePolicy` enum carries `RATIONAL_CLOSURE`, `LEXICOGRAPHIC_CLOSURE`, `RELEVANT_CLOSURE`.
    - Asserts `evaluator.evaluate(theory, marking_policy=..., closure_policy=...)` accepts both independently.
    - **Must fail today**: one mixed enum.

12. **`tests/test_citations_diller_load_bearing.py`** (new — LOW-1)
    - AST-greps `src/gunray/grounding.py` for the docstring on `_simplify_strict_fact_grounding`; asserts it cites Diller 2025 with page numbers
      from `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md`.
    - Asserts `CITATIONS.md` has Diller 2025 in the load-bearing section, not the contextual section.
    - **Must fail today**: docstring cites "page images 004-007" (raw image filenames, not paper page numbers); `CITATIONS.md` puts Diller in
      contextual.

13. **`tests/test_workstream_o_gun_done.py`** (new — gating sentinel)
    - `xfail` until WS-O-gun closes; flips to `pass` on the final commit.
    - Mirrors WS-A pattern. Independent of `test_workstream_o_gun_garcia_done.py` — WS-O-gun can close without WS-O-gun-garcia closing.

---

## Production change sequence

Each step lands in its own commit on a `ws-o-gun` branch in `../gunray`, with message `WS-O-gun step N — <slug>`. Tag a new gunray version
(`v<next>`) at the end and update propstore's `pyproject.toml` pin in WS-M. The propstore-side production code is **read-only** for this WS; only
WS-M and the propstore-side test in step 9b touch propstore source.

### Step 1 — Single grounder (HIGH-3, ARCH-2)

Refactor `inspect_grounding` so it operates on the same `_GroundedTheory` value the dialectical pipeline already builds. Concretely:

- `_internal._ground_theory(theory)` returns a struct that can be projected into a `GroundingInspection`. Add a `to_inspection()` method.
- `evaluator.evaluate_with_trace` populates `trace.grounding_inspection` from that one ground.
- `grounding.inspect_grounding(theory)` becomes a thin wrapper: `_ground_theory(theory).to_inspection()`. No second `parse_defeasible_theory` call.
- `propstore/grounding/grounder.py:170-171` (in WS-M) drops the second `inspect_grounding` call and reads from the trace instead.

Acceptance: `tests/test_inspect_grounding_via_trace.py` turns green; per-call grounder count drops from 2 to 1.

### Step 2 — Per-theory concordance cache and redundancy memoization (HIGH-1, HIGH-2)

In `dialectic.py`:
- Hoist the `concordance_cache` from `build_tree` (line 309) into a per-theory cache, keyed at the `_evaluate_via_argument_pipeline` entry point and
  threaded through every `build_tree` call. Or, more cleanly: cache by `(theory id, frozenset_of_rules)` on a module-level WeakValueDictionary.
- Hoist `_theory_strict_rules(theory)` and `_theory_pi_facts(theory)` from `counter_argues` into a precomputed value in
  `_evaluate_via_argument_pipeline`. Pass them down. `counter_argues` keeps the legacy signature with `universe=None` defaulting to a fresh
  computation, but the pipeline-internal calls always supply.

In `arguments.py`:
- `_has_redundant_nonempty_subset` memoizes by `(rule_set, conclusion)`. The cache is theory-scoped: pass it in from `build_arguments`.
- `disagreement.strict_closure` adds an optional `cache: dict[frozenset[GroundAtom], frozenset[GroundAtom]]` parameter; the hot loop in
  `build_arguments` and `_concordant_rules` shares one cache.

In `disagreement.py`:
- `disagrees(h1, h2, strict_context, facts, *, cache=None)` — same cache passed in.

Acceptance: `tests/test_build_arguments_perf_bound.py` turns green; the 20-rule chain runs in seconds; per-tree closure call count is `O(k)` not
`O(k²)`.

### Step 3 — Memoize `mark()` (MED-2)

Replace the body of public `mark(node)` with `return _mark_table(node)[node]`. Delete the duplicate recursive variant. Update `__all__` reference.

Acceptance: `tests/test_mark_memoized.py` turns green.

### Step 4 — Move `grounding.py`'s `_internal` consumption to a public seam (MED-3)

Promote `_ground_rule_instances_with_substitutions` and `_positive_closure_for_grounding` to a public submodule (`gunray.grounding_core` or an
extension of `gunray.grounding`). Or: change the dependency direction so `_internal` calls into `grounding_core` for the inspection-shaped output, and
`grounding.py` only consumes the public seam. Update ARCHITECTURE.md to reflect the new contract.

Acceptance: `tests/test_grounding_no_private_imports.py` turns green.

### Step 5 — (REMOVED — moved to WS-O-gun-garcia per D-17)

The prior draft's Step 5 was a section-projection patch (Option A split / Option B Antoniou pin). Q rejected both as too small. The full Garcia 2004
generalized-specificity rewrite of `defeasible.py` section projection plus `arguments.py` proper-vs-blocking-defeater taxonomy lives in
`WS-O-gun-garcia.md`. **Do not touch `defeasible.py:196-229` in this WS.** Step numbers below stay aligned with the prior draft for cross-reference;
gap is intentional.

### Step 6 — Propagate `conflicts` through dialectical pipeline (LOW-6, BND-3)

`_GroundedTheory` (the named tuple returned by `_ground_theory`) gains a `conflicts: tuple[tuple[str, str], ...]` field populated from
`parser.parse_defeasible_theory`. The argument pipeline checks `conflicts` when projecting sections: a pair `(left, right)` declared as conflicting,
where both atoms warrant, prevents the double-warrant. The exact post-conflict section assignment is a Garcia-rewrite concern; here we only enforce
the no-double-warrant invariant so the test stays stable across the WS-O-gun-garcia rewrite.

Update `parser.parse_defeasible_theory` callers in `_internal.py:77`, `dialectic.py:71, 85` to use the conflict set rather than ignoring it.

Acceptance: `tests/test_conflicts_threaded_to_dialectical_path.py` turns green.

### Step 7 — Schema validation: superiority acyclic + irreflexive (MED-6)

`schema.DefeasibleTheory.__post_init__` adds:
- Self-pair check: every `(left, right)` in `superiority` requires `left != right`.
- Cycle check: tarjan SCC over the `superiority` directed graph, raise `ValueError` if any SCC has size > 1.

Add Hypothesis property test in `tests/test_superiority.py` that round-trips arbitrary acyclic graphs and asserts `SuperiorityPreference._closure`
is irreflexive and antisymmetric.

Acceptance: `tests/test_superiority_validates_acyclic.py` turns green.

### Step 8 — Strict-only fast path populates argument view (MED-7)

`_evaluate_strict_only_theory_with_trace` calls `build_arguments(theory)` — which, on a strict-only theory, is cheap (every atom in the strict
closure becomes an `Argument(rules=frozenset(), conclusion=atom)`). Populate `trace.arguments`, `trace.trees`, `trace.markings` accordingly. Each strict
atom gets a leaf `DialecticalNode`, mark `U`.

Acceptance: `tests/test_strict_only_argument_view.py` turns green.

### Step 9 — Wire `EnumerationExceeded` through evaluate (LOW-2 / D-18)

This step has two halves: gunray-side wiring and propstore-side surfacing. Gunray side lands first; propstore side rides along in WS-M after the
new gunray pin.

**9a — Gunray side (this WS):**

- `gunray.anytime.EnumerationExceeded` gains structured fields (or stays a plain exception with attributes — pick one and stick with it):
  `partial_arguments: tuple[Argument, ...]`, `partial_trace: DefeasibleTrace | None`, `reason: str` ("argument enumeration budget exceeded:
  `<n>` candidates produced of `<max>` allowed"). Update `__init__.py:5` export.
- `arguments.build_arguments(theory, *, max_arguments: int | None = None, ...)` — when non-`None`, the outer enumeration loop counts produced
  arguments; on overflow, stops, packages the partial tuple, raises `EnumerationExceeded` with `partial_arguments=<so-far>`. The redundancy /
  closure caches built so far are discarded — they are theory-scoped intermediate values, not user-visible.
- `dialectic._evaluate_via_argument_pipeline(theory, policy, *, max_arguments=None)` — passes through. If `build_arguments` raises, the pipeline
  catches at the outermost layer ONLY to attach whatever partial trace was constructed (root trees built so far), then re-raises with the trace
  attached to `partial_trace`. No swallowing.
- `evaluator.evaluate(theory, policy, *, max_arguments=None)` and `evaluator.evaluate_with_trace(theory, policy, *, max_arguments=None)` both
  accept the parameter and let `EnumerationExceeded` propagate to the caller. The `evaluate_with_trace` variant attaches the partial trace; the
  bare `evaluate` variant attaches `partial_trace=None` (it has no trace to begin with).
- The strict-only fast path is exempt — strict-only enumeration is bounded by the strict closure size, not exponential. Document in a docstring.
- `gunray/ARCHITECTURE.md` boundary section gets a "Budget exhaustion" subsection documenting the new parameter and the `EnumerationExceeded`
  contract: callers MUST be prepared to handle it; partial results are valid but incomplete; re-running with a larger budget is the only recourse.

**9b — Propstore side (WS-M owns; cross-linked here):**

- `propstore/grounding/grounder.py` adds `max_arguments: int | None = None` to `Grounder.ground(...)` (and any pluggable evaluator API around it),
  threading to `evaluate_with_trace`.
- `propstore/grounding/types.py` (or wherever `ResultStatus` lives) adds `BUDGET_EXCEEDED` to the `ResultStatus` enum. If no `ResultStatus` exists
  yet because the current return shape is the bare `DefeasibleModel`, WS-M introduces a `GroundingResult` envelope with `status` +
  `model: DefeasibleModel | None` + `partial_arguments: tuple[...] | None`. WS-M owns the envelope design; this WS only reserves the status name.
- `Grounder.ground` wraps the gunray call in `try/except gunray.EnumerationExceeded as exc:`, returns a result with
  `status=ResultStatus.BUDGET_EXCEEDED`, `partial_arguments=exc.partial_arguments`. No exception escapes propstore's boundary.
- propstore's existing `GroundingTextExplanation` / `inspect_grounding` consumers must tolerate `model is None` (or whatever the partial shape is) —
  WS-M audit. This WS surfaces only the contract; WS-M lands the consumer audit.

Acceptance:
- `tests/test_anytime_budget_exhausted.py` (gunray-side halves) turns green.
- `propstore/tests/test_grounder_budget_exceeded.py` (propstore-side, WS-M) turns green after the new pin lands.
- The propstore-side test is gated separately in WS-M's acceptance, not WS-O-gun's; WS-O-gun closes when 9a is green and the propstore-side test
  is `xfail` pending-pin.

### Step 10 — Parser accepts `p()` (LOW-4)

`_find_atom_argument_bounds` returns `(open_index, close_index)` even when inner content is empty; `parse_atom_text` returns
`Atom(predicate=<id>, terms=())` for `p()` exactly as for `p`. Update `propstore/grounding/translator.py:_stringify_atom` to emit `p()` consistently for
zero-arity atoms, removing the bareword/parens asymmetry (this propagates in WS-M).

Acceptance: `tests/test_parser_accepts_p_parens_arity_zero.py` turns green.

### Step 11 — Diller load-bearing citation (LOW-1)

In `grounding.py:_simplify_strict_fact_grounding` docstring (lines 159-168), replace "page images 004-007" with the actual paper page numbers /
theorem numbers from `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md`. Move the Diller 2025 entry in `CITATIONS.md` from
"Contextual" (line 83-86) to "Load-bearing" with a list of which Algorithm 2 transformations are implemented (and which are deliberately not — i.e.
the "no defeasible or defeater rule is removed" carve-out).

Acceptance: `tests/test_citations_diller_load_bearing.py` turns green.

### Step 12 — Policy enum split (LOW-7)

Rename `Policy` → `MarkingPolicy` with only `BLOCKING`. Introduce `ClosurePolicy` enum with `RATIONAL_CLOSURE`, `LEXICOGRAPHIC_CLOSURE`,
`RELEVANT_CLOSURE`. `evaluator.evaluate(theory, *, marking_policy=MarkingPolicy.BLOCKING, closure_policy=None, max_arguments=None)` — when
`closure_policy` is non-`None`, route to `ClosureEvaluator`; otherwise use the dialectical-tree path. No backwards-compat shim per Q's "no fallbacks"
rule. Update propstore in WS-M.

Acceptance: `tests/test_policy_split_enums.py` turns green.

### Step 13 — Boundary contract documentation

Update `gunray/ARCHITECTURE.md` boundary section to:
- Document that `evaluate_with_trace` is the canonical entry point; `evaluate` is a convenience that returns the trace and discards it.
- Document that `trace.grounding_inspection` carries the single ground.
- Document the new `MarkingPolicy` / `ClosurePolicy` split.
- Document the new `superiority` validation guarantees.
- Document the `max_arguments` budget and `EnumerationExceeded` contract from step 9.
- Note that the section-projection contract is owned by WS-O-gun-garcia and may change; consumers depending on section names should track that WS.

Update `propstore/grounding/grounder.py` (in WS-M) to call `evaluate_with_trace` and read `inspection` and `arguments` from the trace.

### Step 14 — Close gaps and gate

- Update `gunray/notes/` (or `notes/ws-o-gun-2026-04-26.md`) with a per-step datestamp and a one-line summary.
- Tag gunray `v<next>`, push to GitHub.
- Update `propstore/pyproject.toml` `gunray` pin to the new tag (in WS-M).
- Flip `tests/test_workstream_o_gun_done.py` from xfail to pass.
- Update `propstore/reviews/2026-04-26-claude/workstreams/WS-O-gun-gunray.md` STATUS line to `CLOSED <gunray-tag> + <propstore-sha>`.

---

## Acceptance gates

Before declaring WS-O-gun done, ALL must hold:

- [ ] `cd ../gunray && uv run pyright src` — passes with 0 errors.
- [ ] `cd ../gunray && uv run pytest -m property tests/` — all property tests green.
- [ ] `cd ../gunray && uv run pytest tests/` — full suite green; specifically, every `test_*` listed in the "First failing tests" section above
  turns from xfail/red to green (except `test_workstream_o_gun_garcia_done.py` which gates the sibling WS).
- [ ] `cd ../gunray && uv run pytest tests/test_dialectic_perf.py` — perf regression bounds hold, plus the new `test_build_arguments_perf_bound`.
- [ ] `cd ../gunray && uv run pytest tests/test_anytime_budget_exhausted.py` — both gunray-side halves green; propstore-side half stays `xfail`
  pending the WS-M pin bump.
- [ ] gunray `CITATIONS.md` has Diller 2025 in load-bearing.
- [ ] gunray `ARCHITECTURE.md` updated for boundary section + cross-module private import status + budget contract.
- [ ] WS-O-gun property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged gunray test run or a named companion run.
- [ ] propstore pin bump and `tests/test_grounder_budget_exceeded.py` are listed as WS-M follow-up gates, not WS-O-gun closure gates.
- [ ] `propstore/reviews/2026-04-26-claude/workstreams/WS-O-gun-gunray.md` STATUS line is `CLOSED <gunray-tag>`.

NOT in this WS's acceptance gates (owned by WS-O-gun-garcia):
- Section-projection paper-fidelity (formerly MED-4).
- Antoniou 2007 / Garcia 2004 CITATIONS.md classification changes.
- Generalized specificity in `arguments.py` / `preference.py`.

---

## Done means done

This workstream is done when **every finding listed above (excluding the moved MED-4)** is closed:

- HIGH-1, HIGH-2, HIGH-3 — perf cliff is gone; verified by `test_build_arguments_perf_bound.py` and `test_inspect_grounding_via_trace.py`.
- MED-2, MED-3, MED-5, MED-6, MED-7 — each has a green test gating it. (MED-4 is in WS-O-gun-garcia.)
- LOW-1, LOW-2, LOW-4, LOW-6, LOW-7 — each has a green test gating it. LOW-2 specifically means the D-18 wiring is live and propstore's
  `BUDGET_EXCEEDED` status is reserved (even if the consumer audit lands in WS-M). (LOW-3 and LOW-5 from cluster-R are not in scope for this WS —
  LOW-3 is an observability nit and LOW-5 is a naming-only API question; document them in `gunray/notes/ws-o-gun-deferred.md` for a follow-up if
  needed.)
- ARCH-1 — two parallel `Rule` types: documented in ARCHITECTURE.md as deliberate (the string surface IS the user-authored seam) but NOT consolidated;
  surfacing is OK, consolidation is out of scope. If Q wants consolidation, that becomes a successor WS.
- ARCH-2, ARCH-3, ARCH-4 — closed in steps above.
- BND-1, BND-2, BND-3 — gunray-side seam (single grounder, trace-carries-inspection, conflicts threaded, budget plumbed) lands in this WS;
  propstore-side consumption lands in WS-M.

If any one of the above is not true, WS-O-gun stays OPEN. No "we'll get to it later." Either it's in scope and closed, or it's explicitly removed
from this WS (and moved to a successor) before declaring done.

---

## Papers / specs referenced

This WS is paper-backed; every behavioural change cites a paper directory under `propstore/papers/`. Garcia 2004 detailed citations live in
WS-O-gun-garcia; this WS uses the existing references where relevant.

- `Garcia_2004_DefeasibleLogicProgramming` — DeLP pipeline backbone. Used here only for the dialectical-pipeline call surface; the
  generalized-specificity / section-projection rewrite is in WS-O-gun-garcia.
- `Simari_1992_MathematicalTreatmentDefeasibleReasoning` — Lemma 2.4 (generalized specificity), Def 2.2 (argument structures). Cited at
  preference.py only for the existing acyclic-superiority axiom; the generalized-specificity rewrite is in WS-O-gun-garcia.
- `Maher_2021_DefeasibleReasoningDatalog` — read for the alternative compilation path. CITATIONS.md keeps it as "alternative considered, not taken";
  this WS does not consume Maher's metaprogram, but the paper's complexity bounds inform the perf bounds in Step 2.
- `Bozzato_2018_ContextKnowledgeJustifiableExceptions`, `Bozzato_2020_DatalogDefeasibleDLLite` — read for the defeasible-DL landscape; informs the
  ARCH-3 closure-arity scope decision. Gunray is not a DL system, so the Bozzato translation rules do not apply.
- `Diller_2025_GroundingRule-BasedArgumentationDatalog` — Algorithm 2 / Definition 7 / Definition 9. Already partially implemented in
  `grounding.py:_simplify_strict_fact_grounding`; LOW-1 promotes the citation. Note: the directory name has a trailing hyphen
  (`Diller_2025_GroundingRule-BasedArgumentationDatalog`) due to the original paper title's stylized hyphen — preserve in cross-references.
- `Morris_2020_DefeasibleDisjunctiveDatalog` — KLM closure (Algorithms 3-5 pp. 150-153). Already cited in `closure.py`; ARCH-3 documents the
  zero-arity scope cap.
- `Pollock_1987_DefeasibleReasoning` — historical background on undercutting / rebutting defeaters (the underlying notion `kind="defeater"` exists
  to support). Currently uncited in gunray; this WS adds a CITATIONS.md entry under "Contextual."
- `Kraus_1990_NonmonotonicReasoningPreferentialModels` (KLM 1990) — the K, L, M postulates that Morris/Ross/Meyer 2020 lift to Datalog+. Already cited
  in CITATIONS.md (load-bearing); no change.
- `Lehmann_1989_DoesConditionalKnowledgeBase` — rational closure historical paper. This WS adds a CITATIONS.md entry under "Contextual" anchoring
  the rational-closure terminology used in `closure.py`'s `Policy.RATIONAL_CLOSURE`.

The Antoniou 2007 reference, formerly load-bearing for the prior draft's MED-4 Option B, is no longer in this WS's scope. WS-O-gun-garcia decides
whether Antoniou stays out-of-contract or gets cited as a contrast point against Garcia.

---

## Cross-stream notes

- **WS-O-gun-garcia (sibling)** owns the section-projection rewrite. The two sub-streams share the gunray repo and the `ws-o-gun*` branch family.
  Ordering: WS-O-gun lands first (perf, anytime, boundary plumbing); WS-O-gun-garcia rebases on top. Step 6's conflicts test is written to be
  stable across the rewrite; if WS-O-gun-garcia changes section names, only the test's section-name parameter needs updating.
- **WS-M** owns the propstore consumer side of the gunray boundary. WS-O-gun owns the gunray side. The two MUST be coordinated:
  - WS-O-gun lands first, tags a new gunray version.
  - WS-M updates `propstore/pyproject.toml` to the new pin and updates `propstore/grounding/grounder.py` and `propstore/grounding/explanations.py`
    to consume the new boundary contract (single grounder, trace-carries-inspection, MarkingPolicy/ClosurePolicy split, conflicts plumbed,
    explanation no-silent-fallback, **budget plumbing + ResultStatus.BUDGET_EXCEEDED per D-18**).
  - The propstore side has its own first-failing tests under `propstore/tests/test_grounding_*.py` already; WS-M extends them, and
    `propstore/tests/test_grounder_budget_exceeded.py` is added.
- WS-A's property-marker discipline applies to gunray as well: every `@given` test in `gunray/tests/` must also be `@pytest.mark.property`.
  Mechanical pass before declaring done.
- WS-N (architecture / import-linter) does not directly affect gunray (separate repo, separate import-linter contracts), but the spirit applies:
  cross-module private imports (MED-3) violate gunray's own ARCHITECTURE.md pitfall section. Same discipline.
- WS-G (belief revision), WS-I (ATMS), WS-J (worldline) all consume the four-section `DefeasibleSections` from gunray indirectly. They depend on
  WS-O-gun-garcia's section-projection outcome, NOT this WS — flag in their workstream docs that the section contract is in flux until
  WS-O-gun-garcia closes.

---

## What this WS does NOT do

- Does NOT touch `defeasible.py:196-229` section projection or the `not_defeasibly` semantics. Owned by WS-O-gun-garcia per D-17.
- Does NOT touch `arguments.py` / `preference.py` generalized-specificity. Owned by WS-O-gun-garcia per D-17.
- Does NOT change `CITATIONS.md` Antoniou 2007 / Garcia 2004 classifications beyond what step 11 does for Diller 2025. Owned by WS-O-gun-garcia.
- Does NOT consolidate `schema.Rule` and `types.Rule` (ARCH-1 documented but not closed). The string surface is deliberate — it is the round-trip
  seam between propstore documents and the parser. Consolidation would merge the surface and the parsed form, which would couple them. If Q wants
  consolidation, that's a successor WS.
- Does NOT extend `closure.py` to first-order arity (ARCH-3 documented). KLM closure for arity ≥ 1 is a research question (Morris 2020 §5
  acknowledges it as future work). The zero-arity cap is a deliberate scope decision and stays.
- Does NOT add provenance accessors to `DefeasibleModel.sections` beyond what the trace already provides. The cluster-R "Missing features" section
  lists `arguments_for_atom`, per-fact rule-id back-pointer, etc. — those are captured in WS-M's scope (the propstore-side provenance contract);
  gunray's job here is to expose `trace.grounding_inspection` and a clean argument tuple, not to redesign `DefeasibleModel`.
- Does NOT serialize `DefeasibleTrace` (cluster R "Missing features"). Trace serialization is a sidecar persistence question that lives in WS-M
  if anywhere.
- Does NOT add Caminada-Amgoud restricted rebut, ambiguity-propagating policy, or any new defeasible-reasoning regime. Scope-bound.
- Does NOT re-run the gunray conformance suite (`test_conformance.py`) with new fixtures. Conformance baseline stays as-is; only the unit and
  property tests added in step 1 are gating.
- Does NOT modify propstore production source. The propstore `Grounder.ground` budget signature, `ResultStatus.BUDGET_EXCEEDED` enum value, and
  `GroundingResult` envelope are all WS-M's territory; this WS only reserves the names and ships the gunray-side counterpart.

---

## Cross-link to WS-M

WS-M's "First failing test" includes `tests/test_provenance_polynomial_properties.py` and the gunray boundary HIGH-1 finding ("grounded facts persist
without provenance"). The propstore-side WS-M scope:

- `propstore/grounding/grounder.py:170-209` — switch from `evaluate(theory, policy)` + `inspect_grounding(theory)` to `evaluate_with_trace(theory,
  policy, max_arguments=...)` and read `trace.grounding_inspection` and `trace.arguments` from the single trace. Default `return_arguments=True`.
- `propstore/grounding/grounder.py` — wrap gunray call in `try/except gunray.EnumerationExceeded`, surface `ResultStatus.BUDGET_EXCEEDED` per D-18.
  Add `max_arguments: int | None = None` to the public `Grounder.ground` signature.
- `propstore/grounding/translator.py:184` — populate `conflicts` from authored `incompatible_with` rows (whatever propstore's source for predicate
  conflicts is) instead of hardcoding `()`.
- `propstore/grounding/translator.py:_stringify_atom:251-262` — emit `p()` for arity-0 atoms once gunray accepts it (LOW-4).
- `propstore/grounding/explanations.py:43-53` — populate `message` whenever the requested atom's predicate yielded no tree but the complement did
  (MED-5).
- `propstore/grounding/grounder.py:_FOUR_SECTIONS` — deferred to WS-O-gun-garcia coordination (the section contract may change there).
- `propstore/grounding/grounder.py:77` — change `policy: gunray.Policy = gunray.Policy.BLOCKING` to the new split: `marking_policy:
  gunray.MarkingPolicy = gunray.MarkingPolicy.BLOCKING, closure_policy: gunray.ClosurePolicy | None = None`.
- New propstore test `propstore/tests/test_grounder_budget_exceeded.py` — asserts the propstore-side surfacing of `EnumerationExceeded` as
  `ResultStatus.BUDGET_EXCEEDED` per D-18.

WS-M owns these tests; this WS owns the gunray-side counterparts.
