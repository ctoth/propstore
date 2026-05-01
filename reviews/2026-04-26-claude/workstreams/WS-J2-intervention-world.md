# WS-J2: InterventionWorld — Pearl `do()` and Halpern HP-modified actual cause

**Status**: CLOSED e4207ff5 — FEATURE/RESEARCH STREAM — not on critical bug-fix path.
**Depends on**:
- **WS-J** (rename `HypotheticalWorld` → `OverlayWorld` must land first so `InterventionWorld` can be added as a sibling type without a name collision and without inheriting the overlay's "synthetic claim competes via conflict resolution" semantics).
- **WS-A** (schema fidelity — added per Codex re-review #18). The SCM constructor `from_world(world)` walks parameterization claims under `propstore/families/concepts/`; without WS-A's schema parity those reads yield wrong shapes. WS-J transitively depends on WS-A, so this is also a transitive consequence of the WS-J dependency above; the explicit listing here matches the cross-stream notes section and prevents drift if WS-J's own dependency set ever changes.
**Blocks**: nothing on the critical bug-fix path (A/B/C/D/E/K/L/M/N).
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).

Decision authority: `reviews/2026-04-26-claude/DECISIONS.md` D-11 — "Both — rename to OverlayWorld AND add separate InterventionWorld that does Pearl `do()`" — and D-22 — "Feature now, remediation later. Open as feature; if any user/test discovers reliance on Pearl semantics, escalate to remediation blocker." This file is the workstream that delivers the second half of D-11 under the framing fixed by D-22.

---

## Why this workstream exists

**Framing (per D-22): this is a feature/research workstream, not a remediation blocker.** The critical bug-fix path is WS-A / WS-B / WS-C / WS-D / WS-E / WS-K / WS-L / WS-M / WS-N (plus their dependency-package streams). WS-J2 is not on it. WS-J's rename of `HypotheticalWorld` → `OverlayWorld` is sufficient to make the *current* code honest about what it does (overlay semantics, not Pearl `do()`); WS-J2 then adds `InterventionWorld` as a **new capability**, layered on top of an already-truthful naming. WS-J2 ships when it ships. None of A/B/C/D/E/K/L/M/N waits on it. The original technical case (Pearl 2000 `do()`, Halpern 2015 HP-modified actual cause) is preserved in full as the technical scope of this WS — only the priority framing changes.

`OverlayWorld` (the renamed `HypotheticalWorld`, after WS-J Path A) does exactly one thing: it adds a synthetic claim asserting `X = x` and lets the existing parameterization graph and conflict-resolution policy adjudicate between the synthetic claim and pre-existing claims for the same concept. That semantics is correct for "what if someone *also* asserted X = x" — the linguist-style overlay query the propstore review surface was actually designed for.

It is **not** correct for counterfactual reasoning in the Pearl 2000 / Halpern 2005 / Halpern 2015 sense. Per Pearl 2000 Def 3.2.1 and Halpern 2015 §2: `do(X = x)` replaces the structural equation for `X` with the constant `X = x` and **deletes every arrow into X**; the post-intervention values are computed on the surgically-modified model. `OverlayWorld` does not delete arrows — the parameterization edges feeding the intervened concept survive, and the synthetic claim merely competes with whatever the parameterizations propagate. For overdetermined or pre-empted scenarios (Halpern 2005 forest-fire Fig 1, Suzy/Billy in Halpern 2015 §4, voting in §5), overlay semantics give the wrong answer.

Per the `imports_are_opinions` memory note: every imported KB row is a defeasible claim, so we cannot "trust the parameterization" as a god's-eye mechanism either. `InterventionWorld` treats the parameterization graph as the *current best causal model* — a defeasible artifact — and applies do-operator surgery on top of it. The SCM (Pearl 2000 §1.4) is the formal object on which interventions act; per D-11, it is built **separately from the claim graph**, so do() on the SCM does not corrupt the claim layer.

This WS also implements **Halpern 2015 HP-modified actual cause** (AC1/AC2/AC3) on top of the SCM. HP-modified is the target because (a) it is the latest formal statement, (b) it eliminates HP-2005's AC2(b) "extended witness" clause, and (c) Halpern 2015 §4 walks the canonical Suzy/Billy example end-to-end, giving a paper-faithful pinning test.

What this WS does **not** do (kept tight): no Spohn OCF migration, no Bonanno merge, no probabilistic counterfactuals (Pearl 2000 Ch 7), no responsibility/blame degree (Chockler & Halpern 2004). Those are real follow-ups; they are out of scope here. See "What this WS does NOT do" at the bottom.

## Escalation trigger

WS-J2 is a feature stream today. **It promotes to a remediation blocker if any user or test discovers reliance on Pearl semantics in current code (post-WS-J rename to `OverlayWorld`).** Specifically:

- Any code site that asserts or assumes the current `OverlayWorld` (or any pre-WS-J caller of `HypotheticalWorld`) performs Pearl-style intervention — i.e., severs parameterization edges into the intervened concept — is a bug. The current implementation does not do that, by construction.
- Any documentation, docstring, comment, test, or example that claims overlay semantics yield `do()`-style counterfactuals is a bug.
- Any downstream consumer (a caller in `propstore/`, an external user of the public API, a paper-process pipeline step, etc.) whose *behavior* depends on edge severance during overlay queries is a bug.

Finding such a code site **escalates WS-J2 from feature/research to remediation blocker** — the misled caller is a correctness defect that cannot be left in place. The escalation procedure: open a finding against this WS, link the offending code/doc, raise the STATUS line in this file from "FEATURE/RESEARCH STREAM" to "REMEDIATION BLOCKER (escalated <date>, trigger: <link>)", notify the critical-path WS owners, and re-prioritize against A/B/C/D/E/K/L/M/N. Until that trigger fires, WS-J2 stays a feature stream and is sequenced after the critical path.

Note: WS-J's rename alone does not fix code that already asserts Pearl semantics on overlay — it just renames the symbol. If such code exists, WS-J's rename surfaces it (the new name `OverlayWorld` makes the overlay-vs-intervention distinction obvious), and the discovery is the trigger above. Audit during WS-J's grep pass; if zero such sites are found, WS-J2 stays feature-priority.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed has a green test and is removed from `docs/gaps.md` or its WS-J successor.

| Finding | Source | Citation | Description |
|---|---|---|---|
| **J2-F1** | Cluster J | `propstore/world/hypothetical.py:481-490` | Pearl `do(X=x)` requires deleting every parameterization edge whose target is `X` before re-evaluating downstream concepts. The current overlay applies a `GraphDelta(add_claims, remove_claim_ids)` only — no edge severance. `InterventionWorld` will provide the severance path. |
| **J2-F2** | Cluster J | `propstore/world/hypothetical.py:610-619` | Overlay `derived_value` evaluates parameterizations from parents whose edges were not cut, producing the wrong value for an intervened concept whose causal parents disagree with the intervention. `InterventionWorld` evaluates only the constant equation. |
| **J2-F3** | Cluster J | `propstore/world/hypothetical.py:636-654` | Overlay `diff()` walks only concepts whose claims were directly added/removed; downstream concepts derived through parameterizations from intervened parents are invisible. `InterventionWorld.diff()` walks the **post-surgery** descendant set under the SCM. |
| **J2-F4** | Cluster J | "Halpern actual cause (AC1/AC2/AC3): ABSENT." | No partition `(Z, W)` search, no freeze-and-test, no AC2/AC3 evaluator anywhere in `propstore/`. This WS adds an `actual_cause(world, effect, candidate_cause)` API that returns an AC1/AC2/AC3 verdict with explicit witnesses. |
| **J2-F5** | DECISIONS.md D-11 | n/a | The DECISIONS log mandates a separate `InterventionWorld` type (not a flag on `OverlayWorld`). This WS creates the type and its public surface. |
| **J2-F6** (narrowed per Codex re-review #19) | Cluster J | "Distinguish do() (intervention by edge severance) from observation (not-intervention)." | The current `OverlayWorld` collapses do() with overlay assertion. `InterventionWorld` offers `do(concept_id, value)` as the edge-severance operator. **`observe(concept_id, value)` is implemented as deterministic-only "not-intervention": it preserves parameterization edges, raises if the observed value is inconsistent with the deterministic SCM under exogenous assignment, and otherwise returns a typed observation world distinguishable in trace from `__intervention_*`.** Full Bayesian observation (probabilistic conditioning over `P(U)`, posterior updates over endogenous values, soft evidence) is **explicitly OUT OF SCOPE for WS-J2** and tracked as a future workstream **WS-J7** (Bayesian observation semantics). The honest scope of J2-F6 is "observation = not-intervention; deterministic-only; fail-closed outside deterministic constraints." |

Adjacent feature included in scope (cheaper to ship together):

| Feature | Rationale |
|---|---|
| Public `actual_cause` API takes a witness budget and a partition-search ceiling | Halpern 2015 acknowledges actual-cause search is exponential in `|W|`; without a configurable ceiling and an `EnumerationExceeded` signal (analogous to the `_choose_incision_set` bound discussed in WS-J H-5), the API is a DoS. Adding the ceiling at construction time is one extra parameter; doing it in a follow-up means refactoring the search later. |

## Code references (verified by direct read; production READ-ONLY in this WS for review)

### Sibling type to follow
- `propstore/world/hypothetical.py:438-593` — current `HypotheticalWorld` (post WS-J: `OverlayWorld`). New `InterventionWorld` is a sibling of this, not a subclass. Both implement the same `BoundWorld`-projection contract; their `.diff()` and `.derived_value()` differ.
- `propstore/world/hypothetical.py:413-416` — `_GraphOverlayStore.compiled_graph` already raises when no compiled graph is available. `InterventionWorld` will require a compiled graph (severance is a graph-edit; no compiled graph → no intervention) and validate this at construction.

### Where parameterization edges live
- `propstore/families/concepts/` — parameterization claims (the equations that, in SCM terms, give us `F_X` for each concept `X`). The severance step walks the compiled graph's parameterization index and drops every parameterization with `target_concept_id == intervened`.
- `propstore/world/model.py` — `WorldModel` (post-WS-N: `WorldQuery`) is the consumer surface. `InterventionWorld` is constructed by `world.intervene({concept_id: value, ...})` analogously to `world.overlay({...})`.

### Where the bound surface joins
- `propstore/world/bound.py` — `BoundWorld` is what `derived_value()` queries are issued against. `InterventionWorld._bound` overrides the parameterization-evaluation path so that for any intervened concept, only the constant equation fires; for descendants of an intervened concept, the surgically-modified parent set is used.

### Existing `__override_` plumbing (do NOT reuse for `do()`)
- `propstore/worldline/trace.py:46-48` — overlay synthetic claims use the `__override_` prefix (post-WS-J: `OVERRIDE_CLAIM_PREFIX`). `InterventionWorld` deliberately does **not** reuse it; intervened concepts get `__intervention_<concept_id>` entries evaluated via the SCM. The two prefixes must be distinguishable in trace output so consumers cannot confuse "asserted X" with "fixed X by surgery."

## Required new module: `propstore/world/scm.py`

The structural causal model is the home for do(): it has explicit equations and explicit exogenous variables, and edge surgery is well-defined on it. Building it as a separate data structure is a hard requirement from the brief and from D-11's "build SCM data structure separate from the claim graph."

```python
@dataclass(frozen=True)
class StructuralEquation:
    """F_X: an equation that determines X's value from its parents."""
    target: ConceptId
    parents: tuple[ConceptId, ...]
    # Compiled callable closing over parameterization rows; pure.
    evaluate: Callable[[Mapping[ConceptId, Value]], Value]
    provenance: ParameterizationProvenance  # which claim row(s) authored F_X

@dataclass(frozen=True)
class StructuralCausalModel:
    """Pearl 2000 §1.4 SCM: <U, V, F, P(U)>. P(U) is omitted in this
    deterministic-first cut; treated as point-mass at observed exogenous
    values for AC1/AC2/AC3 evaluation."""
    exogenous: frozenset[ConceptId]            # U
    endogenous: frozenset[ConceptId]           # V
    equations: Mapping[ConceptId, StructuralEquation]   # F
    exogenous_assignment: Mapping[ConceptId, Value]     # u (the actual world)

    def intervene(self, assignment: Mapping[ConceptId, Value]) -> "StructuralCausalModel":
        """Pearl do(): replace F_X with F_X = constant for each X in
        assignment.keys(); drop every parent edge into X. Return new SCM."""
        ...

    def evaluate(self) -> Mapping[ConceptId, Value]:
        """Solve F under exogenous_assignment. Acyclic by construction."""
        ...
```

The `from_world(world: WorldQuery) -> StructuralCausalModel` constructor walks the compiled parameterization graph, applies the existing conflict-resolution policy at SCM-build time (with provenance), and returns a static snapshot. KB updates do not mutate; a new SCM is built. The SCM is a defeasible artifact with provenance.

## Halpern HP-modified actual cause: the algorithm

From `papers/Halpern_2015_ModificationHalpern-PearlDefinitionCausality/notes.md` §3 (HP-modified definition):

A conjunctive primitive event `X = x` is an **actual cause** of `phi` in `(M, u)` iff:

- **AC1** (sufficiency on the actual world): `(M, u) ⊨ X = x ∧ phi`.
- **AC2** (counterfactual dependence under a witness): there exists a partition of the endogenous variables `V \ X` into `Z` and `W`, an alternative assignment `x'` to `X`, and an assignment `w` to `W` such that
  - `(M, u) ⊨ W = w` (the witness `w` matches the actual world on `W`), AND
  - `(M, u) ⊨ [X ← x', W ← w] ¬phi` (under the do-intervention setting `X = x'` and freezing `W = w` to actual values, `phi` no longer holds).
- **AC3** (minimality): no proper subset of `X = x` satisfies AC1 and AC2.

HP-modified differs from HP-2005 in dropping the "extended witness" AC2(b) clause; the resulting search is over `(W, x', w)` only.

Pseudocode for the evaluator (target file `propstore/world/actual_cause.py`):

```python
def actual_cause(
    world: InterventionWorld,
    effect: Predicate,                # phi
    candidate_cause: Mapping[ConceptId, Value],   # X = x
    *,
    max_witnesses: int = 2 ** 14,
) -> ActualCauseVerdict:
    scm = world.scm
    u = scm.exogenous_assignment

    # AC1
    actual_values = scm.evaluate()
    if not _matches(actual_values, candidate_cause) or not effect(actual_values):
        return ActualCauseVerdict.fail(criterion="AC1", actual=actual_values)

    # AC2: enumerate partitions (Z, W) of V \ X; for each, search x' assignments.
    rest = scm.endogenous - candidate_cause.keys()
    examined = 0
    for w_set in _subsets(rest):                     # W candidates
        z_set = rest - w_set                          # Z = complement
        w_assignment = {v: actual_values[v] for v in w_set}
        for x_prime in _alternative_assignments(scm, candidate_cause):
            examined += 1
            if examined > max_witnesses:
                raise EnumerationExceeded(...)
            intervened = scm.intervene({**x_prime, **w_assignment})
            post = intervened.evaluate()
            if not effect(post):
                # AC2 satisfied with witness (W=w_set, x'=x_prime).
                # Now AC3: check that no proper subset of X also satisfies AC1+AC2.
                if _is_minimal(scm, candidate_cause, effect, w_set, x_prime, ...):
                    return ActualCauseVerdict.holds(
                        criterion="AC1+AC2+AC3",
                        witness_W=w_set, witness_x_prime=x_prime,
                        witness_w_values=w_assignment,
                    )
    return ActualCauseVerdict.fail(criterion="AC2", actual=actual_values)
```

`ActualCauseVerdict` is a frozen dataclass with `holds: bool`, `criterion: Literal["AC1","AC2","AC3","AC1+AC2+AC3"]` (named which clause failed if it failed), and witness fields. Frozen so it can be hashed into worldline content hashes if anyone ever wants to materialize "actual-cause result for `phi` in W".

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_intervention_world_severs_edges.py`** (new)
   - Build an SCM with a parent → child parameterization (`X → Y`, equation `Y = X + 1`).
   - Set the actual world such that `X = 0`, so `Y = 1`.
   - Construct `InterventionWorld` with `do(Y=99)`.
   - Assert that querying `Y` returns `99`, AND that no parameterization with `target=Y` survives in `world.scm.intervene(...).equations`.
   - Verify by inspecting the post-do SCM's `equations[Y].parents == ()` and `equations[Y].evaluate(...) == 99` regardless of input.
   - **Must fail today**: there is no `InterventionWorld`. Even after WS-J's rename, `OverlayWorld.do()` does not exist; `OverlayWorld.overlay({Y: 99})` keeps the `X → Y` edge.

2. **`tests/test_intervention_world_distinct_from_observation.py`** (new)
   - Same SCM as test 1.
   - Construct two worlds: `world.intervene({Y: 99})` and `world.observe({Y: 99})` (the observation operator preserves `X → Y`).
   - Per Codex re-review #19, scope of `observe` here is **deterministic-only "not-intervention"**: edges are preserved, the observed value must be consistent with the deterministic SCM under exogenous assignment. If the observation matches the SCM's computed value for the concept, return an `ObservationWorld` whose `derived_value(Y)` returns the observed value and whose trace marks `Y` as observed. If the observation is inconsistent (e.g. `Y=99` but SCM yields `Y=1`), the call **fails closed** by raising `ObservationInconsistent`.
   - Assert the deterministic-consistent case returns an `ObservationWorld` distinct in type from `InterventionWorld`.
   - Assert the deterministic-inconsistent case raises `ObservationInconsistent` (NOT a silent fall-through to overlay or a Bayesian update — full Bayesian observation is out of scope for WS-J2 per Codex re-review #19; tracked as future WS-J7).
   - Assert that the **provenance trace** marks them with disjoint sentinels: `__intervention_*` vs `__observation_*`. Must NOT be `__override_`.
   - **Must fail today**: only one operator exists; both collapse to overlay.

3. **`tests/test_actual_cause_suzy_billy.py`** (new — the Halpern 2015 §4 worked example, verbatim)
   - Construct the SCM from Halpern 2015 §4: exogenous `U_S, U_B` (Suzy and Billy decide to throw), endogenous `ST, BT, BS, SH, BH` (Suzy throws, Billy throws, bottle shatters, Suzy hits, Billy hits) with the equations from the paper.
   - Actual world: both decide to throw, Suzy's rock arrives first.
   - Query `actual_cause(world, effect="bottle shatters", candidate_cause={"ST": True})`.
   - Assert verdict is `holds=True`, criterion `AC1+AC2+AC3`, with witness `W = {BH}` set to `False` (the actual value: Billy's rock did not hit because the bottle was already shattered) and `x' = {"ST": False}`.
   - Assert that `actual_cause(world, effect="bottle shatters", candidate_cause={"BT": True})` returns `holds=False`, criterion `AC2` (Billy's throw is *not* an actual cause of the shatter under HP-modified, even though Billy threw — because the witness needed for AC2 doesn't exist in HP-modified the way it did in HP-2000).
   - **Must fail today**: no `actual_cause` API exists.

4. **`tests/test_actual_cause_forest_fire.py`** (new — Halpern 2015 disjunctive model)
   - SCM: exogenous `L, MD` (lightning, match-dropper), endogenous `FF` (forest fire) with disjunctive equation `FF = L ∨ MD`.
   - Actual world: both `L=1` and `MD=1`, so `FF=1`.
   - Query `actual_cause(world, effect="FF=1", candidate_cause={"L": 1})`. Under HP-modified, the answer for the *disjunctive* model is **no** for singleton `L=1`; `L=1` is part of the joint cause, not an individual cause, because `MD` may only be held at its actual value `1`.
   - Symmetric negative assertion for singleton `MD=1`.
   - Query `actual_cause(world, effect="FF=1", candidate_cause={"L": 1, "MD": 1})`; the joint cause satisfies AC1/AC2/AC3 with `x' = {"L": 0, "MD": 0}`.
   - Citation: Halpern 2015 notes lines 101-108 and 199 state that disjunctive forest-fire singletons are parts of a joint cause under modified HP, not individual causes.
   - **Must fail today**: no implementation.

5. **`tests/test_actual_cause_voting.py`** (new — Halpern 2015 §5.2 voting example)
   - SCM: 11 voters, majority outcome. Actual world: `7-4` for candidate `A`. Query whether voter 1's vote is an actual cause of A's win.
   - Under HP-modified: **no**, because there is no witness `W` such that flipping voter 1's vote alone reverses the outcome (you need at least three flips). Halpern 2015 §5.2 confirms.
   - Query for a `6-5` actual world: each majority voter's vote IS an actual cause.
   - **Must fail today**: no implementation.

6. **`tests/test_intervention_diff_walks_descendants.py`** (new)
   - SCM: `X → Y → Z`. Actual world such that `X=0, Y=1, Z=2`.
   - `world.intervene({X: 5})` should produce a `diff` that includes `X`, `Y`, AND `Z` (all post-surgery descendants), each with old vs new values.
   - **Must fail today**: `OverlayWorld.diff()` walks only *directly added/removed claims*, not graph descendants under the post-surgery model.

7. **`tests/test_actual_cause_minimality.py`** (new)
   - Build a model where conjunction `X = a ∧ Y = b` satisfies AC1+AC2 but `X = a` alone also satisfies AC1+AC2.
   - Query the conjunctive cause; assert verdict is `holds=False`, criterion `AC3` (failed minimality), with the smaller witness reported.
   - **Must fail today**: no implementation, hence no AC3 check.

8. **`tests/test_actual_cause_witness_budget.py`** (new — property test, `@pytest.mark.property`)
   - Hypothesis strategy: SCMs with `n` endogenous variables, `1 ≤ n ≤ 6`, deterministic Boolean equations.
   - Call `actual_cause(...)` with `max_witnesses=2**(n-1)` (deliberately too small for some inputs).
   - Assert that **either** the call returns a verdict, **or** raises `EnumerationExceeded` — never silently returns a "no" because the search ran out.
   - **Must fail today**: no API, no exception class.

9. **`tests/test_intervention_world_construction_requires_compiled_graph.py`** (new)
   - Construct an `InterventionWorld` against a `WorldQuery` whose compiled graph is missing.
   - Assert it raises a structured error pointing to the missing-compiled-graph cause; do not let it raise mid-do() with a confusing `TypeError`.
   - **Must fail today**: no construction path.

10. **`tests/test_workstream_j2_done.py`** (new — gating sentinel) — `xfail` until WS-J2 closes; flips to `pass` on the final commit.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-J2 step N — <slug>`. WS-J must merge first (specifically, the `OverlayWorld` rename and the `OVERRIDE_CLAIM_PREFIX` constant from WS-J Step 7).

### Step 1 — `propstore/world/scm.py` data structure

Create the SCM module per the definitions above. `StructuralCausalModel.intervene(assignment)` returns a new SCM with:
- `equations[X]` replaced by a constant equation for each `X` in `assignment`.
- All entries in other `equations[Y].parents` that referred to a now-constant `X` are kept (the equation `F_Y` still mentions `X` as a parent; it just now reads a fixed value). Note: this is the cleaner formulation than physically deleting the edge in the parents tuple, and it is equivalent to Pearl §3.2.1 because `X`'s value under the new SCM is unconditionally `x`, regardless of `X`'s former parents — those former parents `Pa(X)` are what get their *outgoing* edge to `X` cut.
- `from_world(world)` constructor walks `propstore/families/concepts/` parameterizations.
- Unit tests: equation severance is correct, evaluation is acyclic, exogenous values pass through unchanged.

Acceptance: SCM unit tests green; `tests/test_intervention_world_severs_edges.py` Step-1 portion (the SCM-level severance check) turns green.

### Step 2 — `InterventionWorld` type

Add `propstore/world/intervention.py` defining `InterventionWorld`. Sibling to `OverlayWorld`. Construction: `WorldQuery.intervene(assignment) -> InterventionWorld`. Implements:
- `_scm: StructuralCausalModel` built lazily from the world's compiled graph.
- `_bound: BoundWorld` that, on `derived_value(concept_id)`:
  - if `concept_id ∈ assignment`: return `assignment[concept_id]`.
  - else: walk `_scm.intervene(assignment).evaluate()[concept_id]`.
- `diff()`: returns post-surgery descendants of intervened concepts under the modified SCM.
- Provenance tagging: synthetic claim records use `__intervention_<concept_id>` (NOT `__override_`).

Acceptance: tests 1 and 6 turn green.

### Step 3 — `observe()` operator on `WorldQuery`

Add `WorldQuery.observe(assignment) -> ObservationWorld`. Distinct type from `InterventionWorld`. **Scope per Codex re-review #19**: deterministic-only "not-intervention." Edges into the observed concept are preserved (no severance — that's the do() semantics). Behavior:

- If the observed value is consistent with the SCM's deterministic value for that concept under the actual exogenous assignment, return an `ObservationWorld` whose `derived_value(observed_concept)` returns the observed value and whose provenance trace marks the concept as `__observation_<concept_id>`.
- If the observed value is inconsistent with the deterministic SCM, raise `ObservationInconsistent` with structured fields naming the concept, the observed value, and the SCM's computed value. Fail closed; do NOT silently update.

Provenance prefix: `__observation_<concept_id>` (disjoint from `__intervention_<concept_id>` and from `__override_*`).

**Out of scope for WS-J2 (tracked for future WS-J7)**: full Bayesian observation, including probabilistic conditioning over `P(U)`, posterior updates over endogenous values, soft evidence, and any observation that does not reduce to a deterministic-consistency check. Once `Opinion`-typed `prior_base_rate` lands (D-8) and probabilistic SCM extension (Pearl 2000 Ch 7) is in place, WS-J7 will replace this deterministic-only cut with full Bayesian observation. WS-J2 does NOT promise that capability and does NOT block on it.

Acceptance: test 2 turns green for the type-distinctness, deterministic-consistent return, deterministic-inconsistent fail-closed, and provenance-prefix cases.

### Step 4 — `actual_cause` API

Create `propstore/world/actual_cause.py` per the pseudocode above. `ActualCauseVerdict` dataclass. `EnumerationExceeded` exception class. Public surface: `from propstore import actual_cause` (re-exported from `propstore/__init__.py`). The function is a pure query over an `InterventionWorld` plus a `Predicate` plus a candidate cause; no I/O, no mutation.

Witness search:
- Enumerate `W ⊆ V \ X` in increasing-size order (smallest witness first).
- For each `W`, enumerate `x'` from a paper-faithful "alternative assignments" set: for Boolean variables, the negation; for finite-domain, the other domain values; for continuous, this is out of scope (raise `NotImplementedError` with a pointer to a follow-up WS).
- Memoize SCM evaluation by `frozenset(intervention.items())` to avoid re-solving identical sub-models.
- Honor `max_witnesses` and raise `EnumerationExceeded` with partial state.

AC3 minimality is checked only after AC1+AC2 succeed: enumerate proper subsets of `X` (small, since `X` is usually a singleton or a pair); if any subset also satisfies AC1+AC2 with a witness, fail AC3 and report the smaller cause.

Acceptance: tests 3, 4, 5, 7, 8 turn green.

### Step 5 — Compiled-graph requirement

Validate at `InterventionWorld` construction: if the world's compiled graph is `None`, raise `InterventionWorldUnavailable("intervention requires a compiled parameterization graph; got None")`. Do not let the error fire mid-do(), where the diagnostic is confusing.

Acceptance: test 9 turns green.

### Step 6 — Documentation pass

- `docs/worldlines.md` — add a new section "Counterfactual primitives" explaining the three world types: `OverlayWorld` (synthetic claim, conflict-resolution adjudication), `ObservationWorld` (deterministic-only observation / not-intervention; no edge severance; Bayesian conditioning deferred to WS-J7), `InterventionWorld` (Pearl do(), edge severance, SCM-level surgery). Include the canonical Suzy/Billy worked example as a Halpern 2015 §4 reference.
- `papers/Halpern_2015_ModificationHalpern-PearlDefinitionCausality/notes.md` — verify the AC1/AC2/AC3 statements in the test file match the paper's notation; add a back-reference comment in the test linking to the notes.md line numbers.

Acceptance: notes review by a paper-reader subagent confirms paper-faithfulness; cross-link is in place.

### Step 7 — Close gaps and gate

- Update `docs/gaps.md`: add closing entries for J2-F1..J2-F6.
- Flip `tests/test_workstream_j2_done.py` from `xfail` to `pass`.
- Update STATUS line in this file to `CLOSED <sha>`.
- Open follow-up WS stubs for the deferred items listed below.

## Acceptance gates

Before declaring WS-J2 done, ALL must hold:

- [x] `uv run pyright propstore` — passed with 0 errors.
- [x] `uv run lint-imports` — passed; the new `propstore/world/scm.py` and `propstore/world/intervention.py` modules respect the existing layer contracts.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-J2 tests/test_intervention_world_severs_edges.py tests/test_intervention_world_distinct_from_observation.py tests/test_actual_cause_suzy_billy.py tests/test_actual_cause_forest_fire.py tests/test_actual_cause_voting.py tests/test_intervention_diff_walks_descendants.py tests/test_actual_cause_minimality.py tests/test_actual_cause_witness_budget.py tests/test_intervention_world_construction_requires_compiled_graph.py tests/test_intervention_world_public_surface.py tests/test_workstream_j2_done.py` — passed: 16 passed. Log: `logs/test-runs/WS-J2-20260430-193708.log`.
- [x] Full suite — passed: 3563 passed, 2 skipped. Log: `logs/test-runs/WS-J2-full-final-20260430-194443.log`.
- [x] No call site of `OverlayWorld` was changed to use `InterventionWorld` blindly. WS-J2 added sibling APIs and left overlay callers on overlay semantics.
- [x] WS-J2 property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-J2 test run or moved to named successor workstreams. `tests/test_actual_cause_witness_budget.py` covers witness-budget behavior; broader probabilistic, continuous-domain, staleness, and search-equivalence property gates are tracked in WS-J7, WS-J9, WS-J10, and WS-J11.
- [x] `tests/test_workstream_j2_done.py` passes.
- [x] STATUS line is `CLOSED e4207ff5`.

## Done means done

This workstream is done when every finding in the table at the top is closed, not "most." Specifically: J2-F1..J2-F6 each have a green test in CI; the three Halpern 2015 worked examples (§4 Suzy/Billy, §5.1 forest-fire disjunction, §5.2 voting) are pinned verbatim; `actual_cause` returns AC1/AC2/AC3 verdicts with explicit witnesses (`W`, `x'`, `w`); `do()` and `observe()` are distinct named operators with disjoint provenance sentinels; the SCM data structure exists in `propstore/world/scm.py` with Pearl 2000 §3.2.1 semantics; `gaps.md` is updated; the gating sentinel test flips from `xfail` to `pass`. Halpern 2015 §4 Suzy/Billy is the single most important gate — if it is not verbatim-faithful and green, WS-J2 is not done.

## Papers / specs referenced

- **Pearl 2000** *Causality: Models, Reasoning, and Inference*, §1.4 (SCM definition `<U, V, F, P(U)>`), §3.2.1 (do(X=x) as model surgery). `papers/Pearl_2000_CausalityModelsReasoningInference/notes.md`. Authority for the SCM data structure and the do() semantics.
- **Halpern & Pearl 2000** *Causes and Explanations: A Structural-Model Approach*. `papers/Halpern_2000_CausesExplanationsStructural-ModelApproach/notes.md`. Original HP definition; included for historical grounding and to show why HP-modified is preferred.
- **Halpern & Pearl 2005** *Causes and Explanations: A Structural-Model Approach (refined)*. `papers/Halpern_2005_CausesExplanationsStructuralModel/notes.md`. The "HP-2005" variant of AC2 with extended witnesses. WS-J2 implements the HP-modified definition instead, but cites this paper's Figure 1 (forest fire) and the formal partition machinery.
- **Halpern 2015** *A Modification of the Halpern-Pearl Definition of Causality*. `papers/Halpern_2015_ModificationHalpern-PearlDefinitionCausality/notes.md`. **Target definition for AC1/AC2/AC3.** §4 Suzy/Billy is the verbatim pinning test. §5.1 forest-fire-disjunction and §5.2 voting are the second and third pinning tests. This paper's preference for HP-modified over HP-2005 (no extended-witness clause) is the reason this WS targets it.
- **Ginsberg 1985** *Counterfactuals*. `papers/Ginsberg_1985_Counterfactuals/notes.md`. Counterfactual semantics from the AI / non-monotonic reasoning tradition. Provides background and informs the documentation pass; not directly implemented (Ginsberg 1985 predates the SCM formalism).

## Cross-stream notes

**Independence from the critical bug-fix path (D-22).** WS-J2 does not block, and is not blocked by, the critical bug-fix path A/B/C/D/E/K/L/M/N. The rename in WS-J is what makes current code honest (overlay is called overlay, not "hypothetical"); WS-J2 adds `InterventionWorld` as a *new capability* on top of that honest naming. Critical-path WSs can ship and close without WS-J2; WS-J2 can ship and close after them. The only firm sequencing constraint is on WS-J2's *upstream* dependencies (WS-J, WS-A), not on critical-path *downstream* consumers — none of those exist.

- **WS-J** must merge first. `InterventionWorld` is a sibling type to `OverlayWorld`; the rename and the `OVERRIDE_CLAIM_PREFIX` constant from WS-J Step 7 are prerequisites. If WS-J is still open, do not start WS-J2 implementation; the rename will conflict. WS-J's rename is sufficient on its own to make the current code honest — WS-J2 is *additive*, not corrective, in the absence of the D-22 escalation trigger.
- **WS-A** schema parity is a transitive prerequisite. Do not start WS-J2 implementation before WS-A merges, because the SCM constructor walks parameterization claims and relies on schema fidelity.
- **WS-B / WS-C / WS-D / WS-E / WS-K / WS-L / WS-M / WS-N** (the rest of the critical bug-fix path) are independent of WS-J2. They neither require nor enable any part of this WS. WS-J2 is sequenced after them by priority (D-22), not by technical dependency.
- **WS-N** rename of `WorldModel → WorldQuery` (D-4) interacts mechanically: if WS-N1 has merged by the time WS-J2 starts, all references in this file should already have been updated. If not, expect a small mechanical rename pass during WS-J2. This is bookkeeping, not a blocker.
- **D-8** (argumentation pipeline replaces `derive_source_document_trust`) is independent but conceptually related: SCM equations are themselves opinion-typed when the parameterization claims they're built from carry `Opinion` confidences. WS-J2 keeps the deterministic-first cut; the probabilistic SCM extension (Pearl 2000 Ch 7) is a follow-up.
- **`imports_are_opinions` memory note**: every parameterization equation `F_X` used to build the SCM is a defeasible claim with provenance. The SCM is a snapshot; recomputing it after KB updates may yield a different SCM and therefore different actual-cause verdicts. This is correct and expected. The actual-cause verdict should record which SCM (by content hash) it was computed against.

## What this WS does NOT do

Out of scope; each gets a follow-up WS slot on close:

- **Probabilistic counterfactuals** (Pearl 2000 Ch 7) — depends on the `Opinion`-typed `prior_base_rate` lift from D-8.
- **Responsibility and blame** (Chockler & Halpern 2004) — layers on top of AC1/AC2/AC3; separate stream depending on this one.
- **Continuous-domain interventions** — `_alternative_assignments` is restricted to Boolean / finite-domain; continuous needs a different witness formulation (Pearl 2009 §3.4).
- **Spohn OCF kappa**, **Bonanno 2012 ternary merge**, **lifting-rule transitive closure** — all out of scope here as in WS-J.
- **Cheap `is_stale` fingerprint for actual-cause results** — verdict is content-addressable in principle; materialized cache is a separate ticket.
- **Multi-cause partition search optimizations** — naive AC2 enumeration is `O(2^|V \ X|)`; greedy / SAT-based optimizations (Ibrahim et al. 2019) are a separate ticket. `max_witnesses` is the safety valve.

If any are pulled into WS-J2 during implementation, they must be added to the findings table in the same commit. No silent scope creep.
