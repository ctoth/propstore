# WS-O-arg-gradual: gradual / bipolar quantitative semantics in `argumentation`

**Status**: CLOSED fcbc77b1
**Depends on**: WS-O-arg-argumentation-pkg (the existing-bugs sub-stream — same upstream policy applies; we don't fork, we ship as PRs against `../argumentation` and bump the pin); **WS-O-arg-vaf-ranking** (`RankingResult` owner — see Codex 2.22 below).
**Blocks**: nothing downstream — propstore consumers gain the new semantics opportunistically.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).

---

## Why this exists

DECISIONS.md D-16: "All four groups — implement everything." This is the **Group D** sub-stream — the gradual / quantitative bipolar surface where arguments carry numeric strength rather than binary acceptance.

D-15: every fix is a PR in `../argumentation` with its own first-failing test. propstore pin bumps after each PR ships. No wraps, no fork.

Cluster P diagnoses the floor: `gradual.py` ships Potyka quadratic only; DF-QuAD lives only inside the probabilistic stack; Matt-Toni and Gabbay equational are absent. Above that floor, Potyka 2018 itself derives a **continuous dynamical system** whose discretisation gives the iteration in `gradual.py:110-131`. The continuous form is what proves convergence; shipping it makes the guarantee true at the API level.

Scope honesty (per D-16): months of work. Four kernels, paper-faithful tests, Baroni 2019 axiomatic compliance, pin bump and corpus re-run per kernel. Sequence them; don't promise dates.

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **D-16 Group D.1** | `DECISIONS.md:163-176` | n/a | DF-QuAD discontinuity-free outside the probabilistic stack. |
| **D-16 Group D.2** | `DECISIONS.md:163-176` | n/a | Bipolar adaptation of DF-QuAD. |
| **D-16 Group D.3** | `DECISIONS.md:163-176` | n/a | Matt-Toni 2008 game-theoretic argument-strength measure. |
| **D-16 Group D.4** | `DECISIONS.md:163-176` (text says "DF-QuAD + Matt-Toni"; we additionally close the Cluster P-named gap) | `cluster-P:300-307,694-701` | Continuous dynamical systems formulation (Potyka 2018) and equational approach (Gabbay 2012). The Q decision text names two; cluster-P names four. We implement four — splitting from D-16 only widens scope, never narrows it, and the missing two are the same kernel family. |
| **Cluster P #cluster-P:300-307** | `cluster-P-argumentation-pkg.md:300-307` | `gradual.py:86-258` | Gradual module exposes Potyka quadratic only. |
| **Cluster P #cluster-P:694-701** | `cluster-P-argumentation-pkg.md:694-701` | n/a | Game-theoretic and equational kernels absent. |
| **Codex #17 (cluster F upstream)** | `reviews/2026-04-26-codex/...` (per task brief) | `probabilistic_dfquad.py:39-65` | Asymmetric attack/support handling; the upstream version fixes here as part of paper-faithful bipolar DF-QuAD. |
| **Codex 2.21** | `DECISIONS.md:323` | `probabilistic_dfquad.py:87-190` | Old `compute_dfquad_strengths` path must be deleted (not retained alongside the new module); continuous integration is default-on; no `strict=True` compat flag. Deletion-first per `feedback_no_fallbacks.md`. |
| **Codex 2.22** | `DECISIONS.md:324` | n/a | Ranking-convergence ownership conflict with WS-O-arg-vaf-ranking. Resolution: vaf-ranking owns `RankingResult` and `ranking.py`; this WS owns gradual-kernel changes that produce or consume that result shape. |

Adjacent finding closed in the same series (cheaper here than later):

| Finding | Citation | Why included |
|---|---|---|
| Baroni 2019 axiomatic principles as testable predicates | `papers/Baroni_2019_GradualArgumentationPrinciples` | Each gradual semantics must declare which Baroni 2019 principles it satisfies. The principles become test predicates. We add the predicate library as part of this WS so every gradual kernel ships with its principle compliance documented and gated. |

## Code references (verified by direct read)

- `argumentation/src/argumentation/gradual.py:1-329` — current module. `WeightedBipolarGraph`, `quadratic_energy_strengths` discrete fixed-point, `revised_direct_impact` (Al Anaissy Def 12), `shapley_attack_impacts` (Al Anaissy Def 13). No DF-QuAD, no Matt-Toni, no continuous, no equational.
- `gradual.py:86-139` — discrete iteration is the Euler discretisation of Potyka 2018's ODE, not the ODE itself. Shipping the ODE form (adaptive step) gives stable convergence on stiff graphs.
- `gradual.py:133` — returns `converged=False` after `max_iterations`; no raise. (The convergence contract for `gradual.py` itself is set in this WS; the cross-module unification of `ranking.py:65` is owned by WS-O-arg-vaf-ranking — see Codex 2.22.)
- `argumentation/src/argumentation/probabilistic_dfquad.py:21-65` — `dfquad_aggregate` (Rago 2016 Definition 5) and `dfquad_combine`. Lift out of the probabilistic stack, then **delete** the old `compute_dfquad_strengths` entry point.
- `probabilistic_dfquad.py:39-65` — `dfquad_combine` is structurally symmetric in supports vs attacks. Codex #17 (cluster F) reported propstore-consumer asymmetry; the upstream obligation lives here.
- `probabilistic_dfquad.py:87-190` — `compute_dfquad_strengths` takes a `ProbabilisticAF`. **DELETED in Step 1.** The new core-gradual variant takes a `WeightedBipolarGraph`; every propstore caller migrates in the same PR (Codex 2.21 per `feedback_no_fallbacks.md`).
- `probabilistic_dfquad.py:21-36` — aggregation `b + c·(1-b)` if `c≥0` else `b + c·b`. Rago 2016 removes the QuAD discontinuity at `c=0`: both branches evaluate to `b` continuously.

## First failing tests (write these first; they MUST fail in `argumentation/tests/` before any production change)

These are PRs against `../argumentation`. Each test is paper-faithful and references the exact paper definition it gates. propstore consumes the new functions only after the upstream PR ships and the pin bumps.

### DF-QuAD discontinuity-free (Rago 2016)

1. **`argumentation/tests/test_dfquad_continuity_at_zero.py`** (new)
   - Builds a `WeightedBipolarGraph` with one supporter and one attacker of identical strength, sweeping the strength from `0.01` to `0.99` in `0.001` increments.
   - At every point: combined influence = `0`; aggregated strength must equal the base score exactly.
   - **Must fail today** (the function doesn't exist on `gradual.py`'s surface yet — `compute_dfquad_strengths` lives in `probabilistic_dfquad.py` and requires a `ProbabilisticAF`).
   - **Reference**: Rago 2016 §3, "discontinuity-free aggregation"; the paper's whole point is that the function is continuous at `c=0`, which is not true of the older QuAD function.

2. **`argumentation/tests/test_dfquad_baroni_2019_principles.py`** (new)
   - For each of the Baroni 2019 axiomatic principles applicable to a strength function (Anonymity, Independence, Directionality, Equivalence, Stability, Neutrality, Bi-variate Monotonicity, Bi-variate Reinforcement, Franklin, Resilience, Weak Monotonicity, Weak Reinforcement), encode a Hypothesis property test that sweeps random graphs and asserts the principle holds for the new `dfquad_strengths(graph)` function.
   - **Must fail today**: function doesn't exist.
   - **Reference**: Baroni 2019, Tables 1-2 of axiomatic principles. Per Q's Hypothesis preference (`feedback_hypothesis_property_tests.md` in user memory): formal properties → `@given` strategies, not example tests.

3. **`argumentation/tests/test_dfquad_old_path_deleted.py`** (new — Codex 2.21)
   - AST-walks `argumentation/src/argumentation/`; asserts `compute_dfquad_strengths` is no longer defined anywhere.
   - Asserts `from argumentation.probabilistic_dfquad import compute_dfquad_strengths` raises `ImportError`.
   - On the propstore side, a paired sentinel asserts no propstore module imports `compute_dfquad_strengths`.
   - **Must fail today**: function exists at `probabilistic_dfquad.py:87-190` and is importable.
   - **Reference**: `feedback_no_fallbacks.md`; DECISIONS.md Codex 2.21 (deletion-first; no compat retention).

### Bipolar DF-QuAD (Rago 2016 — Adapting DF-QuAD)

4. **`argumentation/tests/test_dfquad_bipolar_attack_support_symmetry.py`** (new)
   - Construct a `WeightedBipolarGraph` `G_a` with one supporter `s` of `t` at strength `0.7` and base scores `s=0.6, t=0.5`.
   - Construct the mirror graph `G_b` with one attacker `s` of `t` at strength `0.7`, same base scores.
   - Compute DF-QuAD strengths in both. Assert `strength_a[t] - 0.5 == 0.5 - strength_b[t]` to floating-point tolerance.
   - **Must fail today**: the function doesn't exist; once added, the symmetry obligation must hold (Rago 2016, Adapting paper, §4: bipolar aggregation is symmetric in attack/support contributions on a neutral base).
   - **Note**: This is the **upstream version** of Codex #17. propstore consumers in cluster F observed asymmetric behaviour; the fix lives in the upstream kernel because that's where the aggregation function lives.

5. **`argumentation/tests/test_dfquad_bipolar_strict_balance.py`** (new)
   - Three arguments: `t` with `n` symmetric `(supporter_i, attacker_i)` pairs of equal strength.
   - Sweep `n ∈ {1, 5, 20, 100}` and base score in `{0.1, 0.5, 0.9}`.
   - Assert final strength of `t` equals its base score for every combination.
   - **Must fail today**: function absent.
   - **Reference**: Rago 2016 Adapting, §4 example 3 — symmetric attack/support is a fixed point.

### Matt-Toni 2008 game-theoretic strength

6. **`argumentation/tests/test_matt_toni_two_player_strength.py`** (new)
   - On a small AF (≤6 args), the Matt-Toni 2008 strength of an argument `a` is the value of a 2-player zero-sum game where the proponent picks an admissible set containing `a` and the opponent picks an attacker, with payoff `1` if the proponent wins.
   - Compute the LP value via the package's existing solver layer (`solver.py:108`) or a minimax LP, compare against a hand-computed paper example (Matt-Toni 2008 Example 1 — five-argument framework with values pre-computed in the paper).
   - **Must fail today**: function absent.
   - **Reference**: Matt-Toni 2008 §3, "the value of the game".

7. **`argumentation/tests/test_matt_toni_baroni_2019_compliance.py`** (new)
   - Apply the Baroni 2019 principle predicate library (added in test 2 above) to Matt-Toni's strength function. Document which principles hold; gate the documented set.
   - **Must fail today**: function absent. Once added, only the principles **Matt-Toni 2008 actually proves** should pass — others should be **explicitly recorded as not satisfied** in the principle compliance table the implementation ships.

8. **`argumentation/tests/test_matt_toni_extension_consistency.py`** (new)
   - For arguments in the grounded extension, Matt-Toni strength must be `1`. For arguments in no admissible set (rejected), strength must be `0`. For undecided arguments, strength must be in `(0, 1)`.
   - **Must fail today**: function absent.
   - **Reference**: Matt-Toni 2008 Theorem 4.

### Potyka 2018 continuous dynamical system

9. **`argumentation/tests/test_potyka_continuous_ode.py`** (new)
   - The continuous form: `dσ_a/dt = w_a + (1-w_a)·h(E_a) - w_a·h(-E_a) - σ_a`, with `h` as in `gradual.py:142-144`.
   - Build a small graph; integrate with adaptive RK4 to a tolerance of `1e-12`. Compare against the discrete fixed-point of `quadratic_energy_strengths` to a less strict tolerance of `1e-6`. They must agree.
   - **Must fail today**: there is no continuous integrator in the package. The discrete fixed-point alone is not the paper's contribution — the convergence theorem is about the ODE.
   - **Reference**: Potyka 2018 §4 (continuous dynamical system) and §5 (convergence theorem). The discrete iteration is one Euler step.

10. **`argumentation/tests/test_potyka_convergence_on_stiff_graphs.py`** (new)
    - Construct a graph where the discrete iteration in `gradual.py:110-131` oscillates without converging within `max_iterations`. The continuous integrator must converge.
    - **Must fail today**: no continuous integrator exists, so the test cannot demonstrate the difference.
    - This test pins the **reason** for shipping the continuous form. The continuous integrator is the **default** path once Step 4 lands (Codex 2.21: default-on, no opt-in flag).

### Gabbay 2012 equational approach

11. **`argumentation/tests/test_gabbay_equational_fixpoint.py`** (new)
    - Gabbay 2012 represents an AF (or weighted bipolar graph) as a system of equations `E(a) = f(parents(a))` and computes a fixed point.
    - For the Eq-min and Eq-max equation schemes from the paper, on small graphs, compute the fixed-point and compare against the paper's Examples 4 and 7.
    - **Must fail today**: equational module absent.

12. **`argumentation/tests/test_gabbay_equational_relation_to_dung.py`** (new)
    - Gabbay 2012 Theorem 7: the Eq-min fixed-point of the equational system, restricted to crisp `{0, 1}` inputs, recovers the complete extensions of the underlying Dung AF.
    - On a small AF, enumerate complete extensions via `dung.py:239`, then compare against fixed-points of `equational_fixpoint(graph, scheme="min")` with all initial weights in `{0, 1}`.
    - **Must fail today**: function absent.

### Cross-cutting principle library

13. **`argumentation/tests/test_baroni_2019_principle_library.py`** (new)
    - Existence of a `principles.py` module exposing each Baroni 2019 principle as a callable `principle_X(strength_fn, graph) -> bool` predicate.
    - Each principle must accept any callable matching the gradual-strength signature: `(graph: WeightedBipolarGraph) -> dict[str, float]`.
    - Each existing semantics (Potyka quadratic, DF-QuAD, DF-QuAD bipolar, Matt-Toni, Gabbay-min, Gabbay-max) ships a **declared compliance table** mapping principle → `holds | violates | conditional` and the test gate enforces that the table matches the actual evaluation.
    - **Must fail today**: module absent.

### Paired sentinels — upstream + propstore (per Codex 2.18)

Per Codex 2.18 (already applied to WS-O-arg-argumentation-pkg), every upstream WS needs **two** sentinels with explicit closure conditions. A propstore commit cannot flip an upstream test; an upstream commit cannot prove the propstore pin contains the fix. Both directions are required.

**14a. Upstream sentinel — `argumentation/tests/test_workstream_o_arg_gradual_done.py`** (new; lives in the **argumentation** repo)

- `xfail` until tests 1-13 above are all green in the argumentation repo and Steps 1-6 have shipped upstream.
- Asserts the upstream behaviour shipped: `from argumentation import dfquad, matt_toni, equational, gradual_principles` all succeed; `compute_dfquad_strengths` is no longer importable from anywhere in `argumentation`; `gradual.quadratic_energy_strengths_continuous` exists; `GradualStrengthResult.integration_method` field exists; `dfquad_bipolar_strengths` exists.
- **Closure condition**: turns green when the final upstream PR (Step 6 — Baroni 2019 principle library) merges to argumentation's default branch. Closes in the **argumentation repo**. Independent of any propstore-side change.

**14b. Propstore sentinel — `propstore/tests/architecture/test_argumentation_pin_gradual.py`** (new; lives in **propstore**)

- Imports the public API surface from the pinned `argumentation` package: `from argumentation import dfquad, matt_toni, equational, gradual_principles`; `from argumentation.gradual import quadratic_energy_strengths_continuous, GradualStrengthResult`.
- Exercises one paper-faithful behavioural assertion per major addition, observable from propstore (no reaching into argumentation internals):
  - DF-QuAD: build a small `WeightedBipolarGraph` via the public constructor; call `dfquad_strengths(graph, base_scores=...)` on a fixture where one supporter and one attacker of identical strength leave aggregated strength equal to base score; assert continuity at `c=0`.
  - Bipolar symmetry: assert the Codex #17 symmetry obligation on a public-API fixture.
  - Matt-Toni: call `matt_toni_strength(af, "a")` on a small AF where the answer is hand-computable; assert pinned value.
  - Continuous Potyka: call `quadratic_energy_strengths_continuous(graph, ...)` and assert it is the default Potyka entry point (no opt-in flag exists; introspect signature to confirm).
  - Equational: call `equational_fixpoint(graph, scheme="min", ...)` on a small fixture; assert paper-pinned value.
  - Deletion: `from argumentation.probabilistic_dfquad import compute_dfquad_strengths` raises `ImportError`.
  - RankingResult consumption: assert `gradual` kernels populate `GradualStrengthResult.converged` and do not raise on non-convergence (the contract owned by WS-O-arg-vaf-ranking but consumed here).
- Asserts `propstore/pyproject.toml`'s argumentation pin string equals or post-dates the recorded post-Step-6 argumentation commit (resolved via a recorded commit string in this WS or via git metadata).
- Also performs the propstore-side `compute_dfquad_strengths` no-importer check from test 3 (no propstore module imports the deleted function).
- **Closure condition**: turns green when `propstore/pyproject.toml`'s argumentation pin advances to a commit that contains all Step 1-6 fixes AND every behavioural assertion above passes against that pinned dependency. Closes in **propstore** when the pin bumps and the propstore suite re-runs clean.

The two-sentinel discipline ensures that a fix is genuinely reflected in propstore behavior, not merely in upstream source. A propstore PR cannot mark this WS closed by editing only the upstream sentinel (which lives in a different repo); the propstore-side pin bump and 14b turning green is the closure event for propstore.

## Production change sequence

The PRs land **in `../argumentation` upstream**. Each is its own PR with its own first-failing test, followed by a propstore pin bump and corpus re-run. Per D-15: no wraps, no fork. Per Codex 2.21: deletion-first; no compat shims; no `strict=True` flag; no opt-in continuous-integration flag.

### Step 1 — Extract pure DF-QuAD module; DELETE the old function; migrate propstore callers in one pass

In `argumentation`:

- Create new `dfquad.py` (formalism-named module, matching package convention) exposing pure DF-QuAD aggregation:
  - `dfquad_aggregate(...)` and `dfquad_combine(...)` (lifted, paper-faithful per Rago 2016 Definition 5).
  - `dfquad_strengths(graph: WeightedBipolarGraph, *, base_scores: dict[str, float]) -> GradualStrengthResult`.
- **Delete** `compute_dfquad_strengths` from `probabilistic_dfquad.py:87-190`. No re-export. No wrapper. No alias.
- **Delete** any thin `ProbabilisticAF`-typed entry point that previously routed to the old function.
- Update `argumentation/__init__.py` re-exports: add `dfquad`, remove `compute_dfquad_strengths`.
- **In the same PR (or a paired propstore PR pinned to the same `argumentation` version):** update **every propstore caller** of `compute_dfquad_strengths` to call `dfquad_strengths(graph, base_scores=...)` instead. Build the `WeightedBipolarGraph` from whatever propstore-side structure the caller currently passes as a `ProbabilisticAF`. No shim left in propstore.
- Pin propstore `pyproject.toml` to the new `argumentation` version that ships the deletion. The pin bump is part of the same one-pass migration; old pin and new pin do not coexist.

Acceptance:
- `tests/test_dfquad_continuity_at_zero.py` and `tests/test_dfquad_baroni_2019_principles.py` turn green.
- `tests/test_dfquad_old_path_deleted.py` turns green (function absent; import errors; no propstore caller imports it).
- propstore full-suite re-run: no NEW failures; every former `compute_dfquad_strengths` caller now exercises `dfquad_strengths`.

PR title: `gradual: extract DF-QuAD module from probabilistic stack and DELETE compute_dfquad_strengths (Rago 2016)`.

Rationale: Codex 2.21 + `feedback_no_fallbacks.md` + project deletion-first rule. The "extract then keep importing the old name" pattern is exactly the fallback shape the project rejects. Target behaviour is the only behaviour.

### Step 2 — Bipolar DF-QuAD adaptation

In `argumentation`:

- Add `dfquad_bipolar_strengths(graph, *, base_scores)` honouring Rago 2016 Adapting paper §4. The aggregation differs from base DF-QuAD only in symmetry guarantees — but those guarantees become **first-class** axioms instead of incidental.
- Document the bipolar adaptation's relation to base DF-QuAD: same aggregation, additional symmetry property, additional acyclicity contract clarification.

Acceptance: `tests/test_dfquad_bipolar_attack_support_symmetry.py` and `tests/test_dfquad_bipolar_strict_balance.py` turn green.

PR title: `gradual: bipolar DF-QuAD adaptation with symmetry guarantee (Rago 2016)`.

propstore: pin bump; **fix Codex #17 in cluster F by routing propstore consumers through the new `dfquad_bipolar_strengths`** instead of the asymmetric in-propstore code path. Cluster F's WS records the consumer-side cutover. No fallback to the old asymmetric path.

### Step 3 — Matt-Toni 2008 game-theoretic strength

In `argumentation`:

- New module `matt_toni.py` (matches package naming convention; `value_based.py` and `accrual.py` use formalism names).
- `matt_toni_strength(af: ArgumentationFramework, argument: str) -> float` and `matt_toni_strengths(af) -> dict[str, float]`.
- Implementation: 2-player zero-sum game with proponent picking admissible sets and opponent picking attackers; LP solution. Use the existing `dung.py:175-196` admissibility primitives.
- Document complexity: NP-hard in general; ship an exact LP for small AFs and **explicitly fail loudly** with `MattToniIntractable` for AFs above a configurable size threshold (default 12 — same as `_AUTO_BACKEND_MAX_ARGS` in `dung.py:53`). Do not silently degrade.

Acceptance: `tests/test_matt_toni_two_player_strength.py`, `tests/test_matt_toni_baroni_2019_compliance.py`, `tests/test_matt_toni_extension_consistency.py` turn green.

PR title: `matt_toni: Matt-Toni 2008 strength measure`.

propstore: pin bump; expose via the existing `propstore.argumentation_bridge` surface as a new strength type (no schema change — strengths flow through the same Opinion-projection path as Potyka strengths).

### Step 4 — Potyka 2018 continuous dynamical system (default-on)

In `argumentation`:

- Extend `gradual.py` with `quadratic_energy_strengths_continuous(graph, *, integrator: str = "rk4_adaptive", abs_tol: float, rel_tol: float)`.
- Add an `Integrator` protocol so callers can plug alternatives (Euler, RK4, RK45-adaptive). Default to RK45-adaptive.
- The discrete `quadratic_energy_strengths` stays as an explicit fast path for graphs known to be non-stiff. Callers select it by name; it is **not** the default. The docstring marks it as the Euler discretisation of the continuous form.
- The `GradualStrengthResult` dataclass at `gradual.py:51-60` gets a new `integration_method: str` field. This is a backward-incompatible change; per Q's no-backwards-compat rule (`feedback_no_fallbacks.md`), update all callers in the same PR.
- **Default behaviour change** (Codex 2.21): the public Potyka entry point now invokes the continuous integrator. There is no opt-in flag. propstore bridge code in `propstore/grounding/...` that consumes Potyka strengths gets the continuous result by default; the bridge code is updated in the same pin-bump PR.

Acceptance: `tests/test_potyka_continuous_ode.py` and `tests/test_potyka_convergence_on_stiff_graphs.py` turn green. Existing `tests/test_quadratic_energy.py` (or whatever the current test name is) is updated to call the discrete path explicitly where it intends to test the discretisation, or migrated to the continuous path where it intends to test the semantics.

PR title: `gradual: continuous dynamical system as default (Potyka 2018)`.

propstore: pin bump; bridge code in `propstore/grounding/...` consumes the continuous form by default. No `enable_continuous_integration` flag is introduced. Corpus regression check runs on the new default; if the corpus shifts, the corpus is the thing that updates, not the kernel default.

### Step 5 — Gabbay 2012 equational approach

In `argumentation`:

- New module `equational.py`.
- Two equation schemes: `Eq-min` (Gabbay 2012 §3) and `Eq-max` (§4).
- `equational_fixpoint(graph: WeightedBipolarGraph, *, scheme: Literal["min", "max"], tolerance: float, max_iterations: int) -> GradualStrengthResult`.
- Document the relation to Dung complete semantics (Gabbay 2012 Theorem 7) — and ship that relation as the test below.

Acceptance: `tests/test_gabbay_equational_fixpoint.py` and `tests/test_gabbay_equational_relation_to_dung.py` turn green.

PR title: `equational: Gabbay 2012 equational approach`.

propstore: pin bump; equational strengths are wired into the same Opinion-projection path as Potyka and DF-QuAD.

### Step 6 — Baroni 2019 principle library

In `argumentation`:

- New module `gradual_principles.py`.
- Each Baroni 2019 principle as a callable predicate.
- A registry `PRINCIPLE_COMPLIANCE: dict[str, dict[str, ComplianceLabel]]` mapping `(semantics_name, principle_name) → holds | violates | conditional`.
- Tests: per principle, a Hypothesis sweep over random `WeightedBipolarGraph` instances asserts the registry's claim.
- The tests **fail loudly** if a registry entry says `holds` but a counterexample is found.

Acceptance: `tests/test_baroni_2019_principle_library.py` and per-principle Hypothesis tests all green.

PR title: `gradual_principles: Baroni 2019 axiomatic compliance library`.

propstore: pin bump; the principle compliance table is what propstore documentation references when discussing trust-calibration provenance (per D-8: argumentation-pipeline-replaces-heuristic — the chosen gradual semantics' principle compliance is part of the pipeline's documented behaviour).

### Step 7 — Convergence-failure contract: deferred to WS-O-arg-vaf-ranking

Per Codex 2.22, **WS-O-arg-vaf-ranking owns `RankingResult` and `ranking.py` non-convergence**. This WS does not redefine that type. This WS owns the gradual kernels and updates their return surfaces to produce or consume the `RankingResult`-shaped contract once VAF/ranking has shipped it.

This WS:
- Does **not** define a convergence contract for `ranking.py`.
- Does **not** introduce a `strict=True` flag (Codex 2.21 rejects compat flags; the chosen contract is the only contract).
- Each gradual kernel shipped in Steps 1–6 returns a `GradualStrengthResult` whose `converged` field is populated honestly; the contract specifying what callers do on `converged=False` (raise vs return) is set in WS-O-arg-vaf-ranking and consumed here.
- Cross-link: see WS-O-arg-vaf-ranking, "Convergence contract" section. The propstore-side migration of `RankingResult`-typed results lives there too.

**Boundary (locked per Codex re-review #11):** WS-O-arg-vaf-ranking owns `RankingResult` and `ranking.py`; it does **NOT** modify `gradual.py`. WS-O-arg-gradual owns all changes to gradual kernels that return or consume `RankingResult`, including the `gradual.py:133` non-convergence site. WS-O-arg-vaf-ranking ships `RankingResult` first; this WS then performs the `gradual.py` updates that produce or consume `RankingResult`-shaped values, working entirely within the gradual module surface.

Ordering: WS-O-arg-vaf-ranking's `RankingResult` PR lands first (or at the same pin); this WS then updates `gradual.py` (and the new kernels in Steps 1-6) to populate `RankingResult` from day one. The `gradual.py:133` cleanup is a WS-O-arg-gradual deliverable, not a WS-O-arg-vaf-ranking deliverable.

PR title: n/a in this WS. The `RankingResult` type-shipping PR comes from WS-O-arg-vaf-ranking; the `gradual.py:133` site update plus all kernel updates that consume or produce `RankingResult` values ship from this WS.

### Step 8 — Close gaps and gate (both repos, paired sentinels)

- Update `docs/gaps.md` (propstore-side mirror): remove the "gradual coverage" / "missing DF-QuAD outside probabilistic" / "no Matt-Toni" / "no equational" entries; add a `# WS-O-arg-gradual closed <sha>` line in the "Closed gaps" section.

Upstream side (argumentation):
- Flip `argumentation/tests/test_workstream_o_arg_gradual_done.py` (14a) from `xfail` to `pass`. This test lives in the **argumentation** repo and closes upstream behaviour.

Propstore side:
- Confirm `propstore/pyproject.toml`'s argumentation pin is on the post-Step-6 argumentation commit.
- Flip `propstore/tests/architecture/test_argumentation_pin_gradual.py` (14b) from `xfail` to `pass`. This test lives in **propstore** and closes the pin / observable-behaviour gate.
- Update this WS file's STATUS line to `CLOSED <propstore-sha>`.

Acceptance: both sentinels green in their respective repos; gaps.md has new closed entries; WS-O-arg-vaf-ranking's convergence contract has shipped and this WS's kernels consume it. Per Codex 2.18, the propstore commit cannot flip the upstream test (different repo); the upstream commit cannot prove the propstore pin contains the fix. Both directions are required.

## Acceptance gates

Before declaring WS-O-arg-gradual done, ALL must hold:

- [x] Upstream Steps 1-6 shipped in `../argumentation` and were pushed to `main` through `dbb036b9968b370856c22cb2ebf6157a72587956`. No GitHub PR objects were created in this local execution.
- [x] WS-O-arg-vaf-ranking's convergence contract is in the pinned dependency; this WS consumes the shared result shape and did not redefine it.
- [x] `compute_dfquad_strengths` deleted from `argumentation`; grep finds only deletion sentinel tests.
- [x] Zero propstore modules import `compute_dfquad_strengths`; grep finds only the propstore deletion sentinel.
- [x] No `strict` compat parameter exists on gradual or convergence entry points; the only remaining `strict=True` matches in those files are unrelated `zip(..., strict=True)` calls.
- [x] No opt-in `enable_continuous_integration` flag exists; the only grep hit is the propstore sentinel asserting absence, and Potyka continuous integration is the default entry point upstream.
- [x] propstore `pyproject.toml` pin reaches `dbb036b9968b370856c22cb2ebf6157a72587956`, which exposes all four kernels, the principle library, the deleted old DF-QuAD path, and the WS-O-arg-vaf-ranking convergence contract.
- [x] `uv run pyright propstore` passed with 0 errors.
- [x] `uv run lint-imports` passed with 4 contracts kept and 0 broken.
- [x] Upstream sentinel `argumentation/tests/test_workstream_o_arg_gradual_done.py` (14a) green in the focused upstream gate.
- [x] Propstore sentinel `propstore/tests/architecture/test_argumentation_pin_gradual.py` (14b) green in propstore against the bumped pin.
- [x] Full propstore suite passed: `3214 passed in 555.88s`, log `logs/test-runs/arg-gradual-property-full-final-n0-20260428-214915.log`.
- [x] Upstream `argumentation` workstream gate passed for all new named tests and sentinel: `31 passed in 1.09s`. The full upstream suite was not completed; an existing ASPIC Hypothesis run hit a memory blowup before this closure.
- [x] WS-O-arg-gradual property-based gates from `PROPERTY-BASED-TDD.md` are included in upstream tests: `test_dfquad_baroni_2019_principles.py`, `test_matt_toni_baroni_2019_compliance.py`, `test_potyka_convergence_on_stiff_graphs.py`, and `test_gabbay_equational_relation_to_dung.py`.
- [x] `propstore/grounding/...` has no Opinion-producing gradual-strength consumers. Applicable propstore consumers route through the kernel directly (`fragility_scoring.py`) or probability conversion layers, so there is no gradual-kernel Opinion provenance to attach in this WS.
- [x] `docs/gaps.md` has no open rows for the findings table at the top of this file; WS-O-arg-gradual closure is recorded under closed gaps.
- [x] `reviews/2026-04-26-claude/workstreams/WS-O-arg-gradual.md` STATUS line is `CLOSED fcbc77b1`.

## Done means done

This workstream is done when **every finding in the table at the top is closed** AND every step in the production-change sequence has shipped (Steps 1–6 in this WS, Step 7 from WS-O-arg-vaf-ranking) AND propstore's pin reflects them. Specifically:

- Rago 2016 DF-QuAD lives in its own module, callable on a `WeightedBipolarGraph`; the old `compute_dfquad_strengths` is deleted upstream and no propstore caller references it.
- Rago 2016 Adapting bipolar DF-QuAD ships with a symmetry test that gates regressions.
- Matt-Toni 2008 strength is implemented and gates the three Matt-Toni tests.
- Potyka 2018 ships in continuous form **as the default**; the discrete form is callable explicitly and documented as one Euler step. No opt-in flag.
- Gabbay 2012 equational ships in two schemes (min, max) with the Dung-recovery theorem gated.
- Baroni 2019 principle library ships, every kernel declares compliance, the registry is gated by Hypothesis tests.
- Convergence-failure contract: the contract this WS's kernels populate is owned by WS-O-arg-vaf-ranking and consumed here. There is no `strict=True` compat flag anywhere.
- Cluster F Codex #17 is closed via the upstream symmetry fix in Step 2.

If any one of those is not true, WS-O-arg-gradual stays OPEN. No "we'll skip Gabbay because nobody uses it" — D-16 said "all four groups." Either every kernel ships, or this WS file is amended (in this file, before declaring done) to remove a kernel and document the reason.

## Papers / specs referenced

Read these from `papers/<dir>/notes.md` before implementing the corresponding step:

- **Rago 2016 DF-QuAD** (`papers/Rago_2016_DiscontinuityFreeQuAD/notes.md`) — Step 1. Definition 5 is the aggregation function; §3 motivates the discontinuity removal.
- **Rago 2016 Adapting** (`papers/Rago_2016_AdaptingDFQuADBipolarArgumentation/notes.md`) — Step 2. §4 gives the bipolar adaptation and the symmetry obligation.
- **Matt-Toni 2008** (`papers/Matt_2008_Game-TheoreticMeasureArgumentStrength/notes.md`) — Step 3. §3 defines the game; §4 gives the boundary theorems.
- **Potyka 2018** (`papers/Potyka_2018_ContinuousDynamicalSystemsWeighted/notes.md`) — Step 4. §4 derives the ODE; §5 proves convergence.
- **Gabbay 2012** (`papers/Gabbay_2012_EquationalApproachArgumentationNetworks/notes.md`) — Step 5. §3 (Eq-min), §4 (Eq-max), Theorem 7 (Dung recovery).
- **Baroni 2019** (`papers/Baroni_2019_GradualArgumentationPrinciples/notes.md`) — Step 6. The principle catalogue.
- **Amgoud 2017** (`papers/Amgoud_2017_AcceptabilitySemanticsWeightedArgumentation/notes.md`) — supporting reference for principle interpretation; helpful for resolving disagreements between Baroni 2019's terminology and earlier formulations.

Per Q's coder-citation discipline (`feedback_citations_and_tdd.md`): every implementation function carries a docstring citing the paper, definition number, and page. Inline comments at the aggregation core also cite the paper. No unsourced math.

## Paper contract resolved

- Rago 2016 DF-QuAD, pp. 65-66: support and attack sequences aggregate by noisy-or, `1 - product(1 - v_i)`. Combined influence is support aggregate minus attack aggregate. Final aggregation is `b + c(1-b)` for positive `c` and `b + cb` for negative `c`; equal support and attack therefore gives `c = 0` and leaves the base score `b` unchanged.
- Rago/Cyras/Toni 2016 bipolar DF-QuAD, p. 35: a BAF uses neutral base `0.5`. With support product `Sprod = product(1 - s_i)` and attack product `Aprod = product(1 - a_j)`, neutral target strength is `0.5 + 0.5 * (Aprod - Sprod)`.
- The implemented weighted-graph contract in `argumentation.dfquad` uses `source_strength * support_weight` for support contributions, bounded to `[0, 1]`; attack contributions use attacker strength. Missing QuAD tau is a hard `ValueError` at the probabilistic boundary.
- Page citations above are actual paper page numbers, not image artifact indices.

## Cross-stream notes

- **Hard dependency on WS-O-arg-vaf-ranking** — owns `RankingResult` and `ranking.py` non-convergence handling (Codex 2.22). This WS's kernels populate or consume that contract inside gradual modules; they do not redefine the type. Step 7 here is a deferral, not an implementation.
- **Sequential with WS-O-arg-argumentation-pkg (existing-bugs)** — Step 1 in this WS touches `gradual.py` indirectly (via the `dfquad.py` extraction path) and `probabilistic_dfquad.py` directly; the bugs WS may also touch them. Do bugs WS first; rebase this WS on top.
- **Parallel with WS-O-arg-aba-adf, WS-O-arg-dung-extensions** — independent kernels per D-16. No coordination needed.
- **Cluster F Codex #17** — closed by Step 2 of this WS. Cluster F's WS records the propstore-side migration.
- **Cluster D propstore bridge** — once Step 3 (Matt-Toni) and Step 5 (Gabbay) ship, propstore's grounding layer gains optional new strength sources. Cluster D decides which to expose to Opinion projection.
- **D-8 trust calibration** — the argumentation pipeline that replaces `derive_source_document_trust` benefits from richer gradual semantics. WS-K updates can reference whichever kernel survives review against the meta-paper rule corpus. No hard dependency in either direction.

## What this WS does NOT do

- Does NOT fork the argumentation package (D-15: no fork).
- Does NOT keep `compute_dfquad_strengths` alongside the new module (Codex 2.21 + `feedback_no_fallbacks.md`: deletion-first).
- Does NOT introduce a `strict=True` compat flag on any convergence or kernel API (Codex 2.21).
- Does NOT make the continuous integrator opt-in via flag (Codex 2.21: default-on).
- Does NOT own the `ranking.py` convergence contract or `RankingResult` — that is **WS-O-arg-vaf-ranking** (Codex 2.22).
- Does NOT add Bench-Capon 2003 VAFs — that's WS-O-arg-vaf-ranking.
- Does NOT add ABA or ADF — that's WS-O-arg-aba-adf.
- Does NOT add eager / stage2 / prudent / semi-stable extensions — that's WS-O-arg-dung-extensions.
- Does NOT change the propstore-side trust calibration design — that's WS-K (per D-8).
- Does NOT touch the propstore-side asymmetric DF-QuAD code path beyond the routing change in Step 2 — the actual cleanup is cluster F's responsibility.
- Does NOT add new ICCMA solver protocol support — that's a separate WS within the argumentation-pkg series if Q decides to pursue it (cluster P open question 3).
- Does NOT add sampled / approximate Shapley computation for `shapley_attack_impacts` — that's a performance follow-up, not a correctness gap.
- Does NOT touch `accrual.py`, `value_based.py`, or `weighted.py` — different kernels, different sub-streams.
