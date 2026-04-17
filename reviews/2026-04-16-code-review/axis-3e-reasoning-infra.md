# Axis 3e — Reasoning Infrastructure Fidelity

## Summary

Reasoning-infrastructure fidelity is **mixed**.

The ATMS (`propstore/world/atms.py` + `propstore/core/labels.py`) is a
high-fidelity implementation of de Kleer 1986 — all four label invariants
(consistency, soundness, completeness, minimality) are both defined in the
label algebra and **runtime-verified** by `verify_labels()`. Confirmed
visually against `papers/deKleer_1986_AssumptionBasedTMS/pngs/page-017.png`
(Section 4.3 "Labels").

Against that solid core, the Z3 interface is a **crit correctness hazard**:
`propstore/z3_conditions.py` collapses Z3's three-valued
`sat | unsat | unknown` result to `bool` at its public API boundary
(`:444,463,481,489`), and `propstore/dung_z3.py` enumeration loops
silently terminate on `unknown` (`:151,197`). No Z3 call anywhere in
`propstore/` sets a timeout. `propstore/condition_classifier.py:32-36`
then maps the hidden `unknown` signal to `ConflictClass.OVERLAP` (already
flagged by axis 5). There is no `SolverResult` sum type. There is no
test for the `unknown` path; the single "unknown" test in
`tests/test_z3_conditions.py:437` is about an undefined concept name.

The treedecomp-DP in `propstore/praf/treedecomp.py` is framework-correct but
its module docstring (`:12-17`) honestly admits the DP body gives *"zero
asymptotic improvement over brute-force enumeration."* Dvořák 2012 / Fichte
2021 are not cited — the cited authority is Popescu & Wallner 2024.

`propstore/sensitivity.py` is local gradient-and-elasticity, not Coupé
2002 (Bayesian posterior sensitivity) or Ballester-Ripoll 2024
(variance-based global sensitivity). `propstore/equation_comparison.py`
uses `sympy.expand(lhs-rhs) / cancel` for canonicalization — polynomial
normal form, not Knuth-Bendix. The compiler (`propstore/compiler/`) is a
linear normalize → bind → validate pipeline — not abstract interpretation
(Cousot 1977) and not Sarkar nanopass. None of the citations for those
papers appear in the codebase.

CLAUDE.md line 33 claims `KindType.TIMEPOINT` is *"not valid for
parameterization or dimensional algebra"* — unenforced in code.

## Findings

### crit — Z3 3-valued result collapsed to bool at API boundary

Files:
- `propstore/z3_conditions.py:444` — `is_condition_satisfied` returns
  `solver.check() == z3.sat`. `z3.unknown` → `False`.
- `propstore/z3_conditions.py:463` — `are_disjoint` returns
  `solver.check() == z3.unsat`. `z3.unknown` → `False`.
- `propstore/z3_conditions.py:481` — `are_equivalent` step 1: `if
  s1.check() != z3.unsat: return False`. `z3.unknown` → `False`.
- `propstore/z3_conditions.py:489` — `are_equivalent` step 2: `return
  s2.check() == z3.unsat`. `z3.unknown` → `False`.
- `propstore/condition_classifier.py:32-36` — the caller: if
  `are_equivalent` is False and `are_disjoint` is False, return
  `ConflictClass.OVERLAP`. Both underlying False values include any
  `unknown` result.

Paper evidence:
- Moura_2008_Z3EfficientSMTSolver — SMT solvers legitimately return
  `unknown` whenever theory combinations cannot decide a query; linear
  real arithmetic alone is decidable but combining with strings /
  quantifiers is not.
- Bjorner_2014_MaximalSatisfactionZ3 — optimization queries surface
  unknown explicitly.

Consequence: "I don't know whether these claims overlap" is silently
reported as "they overlap." This is exactly what propstore's CLAUDE.md
"Honest ignorance over fabricated confidence" principle forbids. A
vacuous Jøsang opinion would be the architecturally correct response;
instead, a confident `OVERLAP` is fabricated.

No `SolverResult` sum type exists; no caller can distinguish known-overlap
from unknown-overlap.

### crit — No Z3 timeout anywhere

Files:
- `propstore/z3_conditions.py:439, 459, 477, 485` — every
  `z3.Solver(ctx=self._ctx)` construction runs with unbounded wall time.
- `propstore/dung_z3.py:148, 194` — same.

`grep 'timeout|set_param|set_option'` across `propstore/` returns zero
matches. A decidable-fragment hang stalls the caller indefinitely; once a
timeout is added later, it will silently poison all `z3.unknown` paths
above. This is an operational crit orthogonal to the bool-collapse issue.

### high — dung_z3 enumeration loops silently truncate on unknown

Files:
- `propstore/dung_z3.py:151` — `while solver.check() == sat:` in
  `z3_stable_extensions`.
- `propstore/dung_z3.py:197` — `while solver.check() == sat:` in
  `z3_complete_extensions`.

`z3.unknown` terminates the loop. Callers receive a partial extension
list they cannot distinguish from an exhaustive enumeration. For a Dung
AF encoding over Booleans this is unlikely to trigger today, but the
same pattern will bite once the encoding incorporates arithmetic or
string theories (e.g., for conditional attacks).

### high — CLAUDE.md TIMEPOINT claim is unenforced

CLAUDE.md line 33: *"KindType.TIMEPOINT maps to z3.Real (same as
QUANTITY) but is semantically distinct — not valid for parameterization
or dimensional algebra."*

Reality:
- `propstore/z3_conditions.py:134` (`_translate_name`) and `:362`
  (`_binding_to_z3`) both use `if info.kind in (KindType.QUANTITY,
  KindType.TIMEPOINT)` — identical handling.
- `propstore/cel_checker.py:521` (`_resolve_type`), `:640`
  (`_check_in`), `:745` (`_check_concept_literal_type_mismatch`) — all
  bundle TIMEPOINT with QUANTITY in the "numeric" class; all accept
  identical operations.
- `propstore/propagation.py`, `propstore/sensitivity.py`,
  `propstore/parameterization_walk.py`, `propstore/unit_dimensions.py`
  contain no TIMEPOINT-reject rule (searched).

The claimed "semantic distinction" exists only in CLAUDE.md prose. Either
enforce at the checker (preferred) or soften the CLAUDE.md claim.

### high — Treedecomp DP is tree-shaped brute force, not FPT

File: `propstore/praf/treedecomp.py:12-17` (module docstring,
self-admitted): *"tree decomposition DP currently tracks full edge sets
and forgotten arguments in table keys, giving row count
O(2^|defeats| * 2^|args|). This provides zero asymptotic improvement over
brute-force enumeration. Effective for AFs with treewidth <= ~15. A
principled redesign would track only local state per bag, achieving the
theoretical O(2^tw) bound."*

The *framework* (primal graph, min-degree elimination, running-intersection
validation, nice TD conversion) is clean and cited to Popescu & Wallner
2024. The *DP body* at `:585-800+` uses `_RowKey = tuple[bag_state,
frozenset[active_edges], frozenset[present_forgotten]]` — the edge and
present-forgotten components are global, not local to the bag.

Paper evidence: Dvořák 2012 and Fichte 2021 both publish FPT algorithms
parameterized by treewidth with `O(f(tw) · n)` bounds. Neither paper is
cited in the code. CLAUDE.md "Known Limitations" does NOT mention this
gap — it is declared only in the module docstring.

### high — equation_comparison uses polynomial normal form, not Knuth-Bendix

File: `propstore/equation_comparison.py:169-188`
(`_normalize_parsed_equation`). Uses `diff = sympy.cancel(sympy.expand(
lhs - rhs))`, stringifies, and compares at `:108-113`.

- Not a confluent + terminating term rewriting system.
- No critical-pair analysis, no E-matching, no completion.
- `_expr_to_sympy` (`:191-222`) supports `log/ln/exp/sqrt` as
  uninterpreted SymPy function applications. `expand+cancel` does NOT
  simplify `log(xy) = log x + log y`, `sin²+cos² = 1`,
  `e^(a+b) = e^a · e^b`, or most other non-polynomial identities.
- No reference to Knuth 1970 or TRS literature.

Consequence: semantically-equivalent equations that differ across these
identity classes are reported `DIFFERENT`. Silent false-negatives in the
`EquationComparisonStatus.EQUIVALENT` path.

### high — sensitivity.py is local gradient, not Bayesian/global

File: `propstore/sensitivity.py:47-272`.

- `:240` — `partial = sym_diff(expr, input_sym)`.
- `:254` — `elasticity = partial_val * x_val / output_value`.
- Inputs are point floats (`input_values[iid] = float(val)` at `:208`).

No Bayesian posterior-to-parameter sensitivity (Coupé 2002), no
variance-based / Sobol / global sensitivity (Ballester-Ripoll 2024), no
uncertainty propagation. Neither priority paper is cited.

Classification: paper-list drift, not project-spec drift — CLAUDE.md does
not claim Coupé/Ballester-Ripoll fidelity. Documented here so the
synthesis step knows the gap.

### med — No test exercises the z3.unknown path

File: `tests/test_z3_conditions.py:437` — the only test named
`test_unknown_concept_name_is_hard_error` is about an undefined concept
name in the registry, not about Z3 returning `unknown`.

`grep 'unknown|timeout'` over `tests/test_z3_conditions.py` returns only
that one match. The bool-collapse crit is live because it has never been
tested.

### med — Temporal ordering matches by string suffix, not metadata

File: `propstore/z3_conditions.py:380-430` — `_temporal_ordering_constraints`
pairs TIMEPOINT concepts by name suffix (`*_from` / `*_until`). A
TIMEPOINT concept named `heart_rate_from` would accidentally get an
ordering constraint with a hypothetical `heart_rate_until`. Low risk in
practice but a principled fix would read interval metadata from the form
definition, not the concept name.

### low — dung_z3 blocking-clause constructed unconditionally

File: `propstore/dung_z3.py:55-67` — `_block_solution` always builds
`Or(*clause_parts)` over all argument vars. If the problem were
unsatisfiable from the start (empty AF with no initial solution), the
`while solver.check() == sat` loop at `:151/:197` would simply not enter,
so the block function is defensive. No bug — just a minor clean-up note.

### note — ATMS is a high-fidelity de Kleer 1986 implementation (positive)

Confirmed against `papers/deKleer_1986_AssumptionBasedTMS/pngs/
page-017.png` (Section 4.3, Labels):

- `propstore/core/labels.py:69-86` — `normalize_environments` dedups,
  prunes supersets, drops nogood-subsumed environments. Matches
  de Kleer p.151 label-update formula *"removing inconsistent and
  subsumed environments."*
- `propstore/core/labels.py:89-99` — `Label` is stored as the minimal
  antichain of environments. Invariant enforced in `__post_init__` via
  `normalize_environments`.
- `propstore/core/labels.py:211-230` — `combine_labels` cross-product-
  unions antecedent labels. Matches de Kleer p.151 `∪_k { x | x = ∪_i x_i
  where x_i ∈ j_{ik} }`.
- `propstore/core/labels.py:48-49` — `EnvironmentKey.subsumes` is proper
  subset check on assumption IDs.
- `propstore/core/labels.py:65-66` — `NogoodSet.excludes(env)` is True
  iff some known nogood *subsumes* env (consistent with "nogoods are
  minimal and their supersets are inconsistent").
- `propstore/world/atms.py:1016-1072` — `verify_labels()` is a live
  correctness monitor checking all four invariants: `consistency_errors`,
  `minimality_errors`, `soundness_errors`, `completeness_errors`. The
  soundness and completeness checks recompute the expected label from the
  justification graph and compare sets — not a docstring claim, an actual
  runtime-checkable property.
- `propstore/world/atms.py:1177-1187` — `_build` fixpoint iterates:
  propagate labels → materialize parameterization justifications → update
  nogoods → re-run until nothing changes; then a final propagation.
- `propstore/world/atms.py:1318-1349` — nogood update per conflict pair:
  union one env from each claim's label and add to the nogood set;
  re-normalize.

Minor drift from paper:
- Engine is **eager** (whole-world label recomputation each cycle), not
  lazy as de Kleer §6 recommends for `n ~ 1000` assumptions.
- No bit-vector environment representation (uses tuples of string IDs).
- Docstring (`world/atms.py:6-12`) explicitly admits both: *"bounded
  ATMS-native analysis over rebuilt future bound worlds rather than AGM-
  style revision, entrenchment maintenance, or a full de Kleer runtime
  manager."* The claim is consistent with the implementation.

### note — Z3 division-by-zero is guarded correctly (positive)

File: `propstore/z3_conditions.py:170-178` — translating `x / y` pushes
`y != 0` into `_current_guards`. `:331-334` conjuncts those guards into
the final translated expression. Z3's default uninterpreted-division
semantics (where `x / 0` is an arbitrary value, making counter-models
spurious) is principled-ly worked around. Good.

### note — Compiler is a linear pipeline, not abstract interpretation

File: `propstore/compiler/passes.py:257-440+` — `compile_claim_files` is
a straight-line sequence:
1. `jsonschema.validate` (`:310-313`)
2. `_bind_claim` — concept resolution, logical-id checks, version-id
   hashing (`:341-348`)
3. Semantic validators: `_validate_algorithm`, `_validate_equation`,
   `_validate_model`, `_validate_measurement`, `_validate_observation`,
   `_validate_parameter`, `_validate_stances` (imported `:26-34`)

No Cousot-style abstract domain, Galois connection, widening/narrowing,
or fixed-point iteration:
- `grep 'fixpoint|widen|narrow|galois|lattice|join|meet|bottom|top'`
  over `propstore/compiler/` → zero matches.
- `grep 'Cousot|abstract interpretation|nanopass|Sarkar'` over
  `propstore/` → zero matches.

Priority papers Cousot 1977 and Sarkar 2004 are structurally not
applicable to this design; their absence in the code is consistent with
the compiler's actual shape. No finding — just answering the audit
question.

## Biggest drift

**Z3 three-valued result collapsed to bool at the API boundary
(`z3_conditions.py:444,463,481,489`), with no timeout anywhere in
`propstore/`.** The downstream `condition_classifier.py:32-36` then
fabricates `ConflictClass.OVERLAP` from hidden `unknown` signals. This is
the axis's single most important finding: the semantic layer silently
manufactures confidence in exactly the place CLAUDE.md forbids it. The fix
is a `SolverResult = SAT(model) | UNSAT | UNKNOWN(reason)` sum type
carried end-to-end to `condition_classifier`, which can then route
`unknown` to an explicit `ConflictClass.UNDETERMINED` variant (or a
Jøsang vacuous opinion).

## Open questions

- **Does Z3 actually return unknown today on any live propstore query?**
  Not verified by runtime evidence. The bool-collapse is a latent hazard
  until a query hits it — non-linear reals and string solvers are the
  usual triggers, both reachable via `_translate_binary` (arithmetic) and
  string enums (`_try_category_comparison`). I did not run the test suite
  against adversarial CEL expressions to produce a known-unknown.
- **Do any callers of `Z3ConditionSolver` already paper over unknown?**
  Grep showed `condition_classifier.py` as the obvious caller; I did not
  enumerate all callers. Axis 2 has the cross-module import graph and
  would answer faster.
- **Is the treedecomp DP reachable in any current `pks build` run?** The
  engine is in `praf/`, used by `praf/engine.py`. I did not trace which
  CLI paths exercise it. The "zero asymptotic improvement" claim is a
  paper-fidelity finding regardless.
- **Does `equation_comparison.compare_equation_claims` get invoked from
  any path that treats `DIFFERENT` as authoritative?** Potential silent
  false-conflict source; I did not trace the callers. Axis 5 or axis 9
  may have more context.
- **Does `opinion_sensitivity` (`fragility_scoring.py:306-350`) satisfy
  any formal property from the Jøsang 2001 / DFQUAD literature, or is it
  a bespoke finite-difference heuristic?** I read the code but did not
  cross-check against Jøsang's opinion-perturbation framework.
- **Does the compiler need a Sarkar-nanopass or Cousot-abstract-
  interpretation layer given its actual workload (claim file → bound IR
  → validate)?** I did not evaluate whether those techniques would add
  value — the current design is adequate for the workload I observed.
- **Does the ATMS `verify_labels` method get called in production paths
  or only in tests?** I did not trace its callers. If it runs only in
  tests, the live-correctness-monitor framing is aspirational.
- **What happens in `z3_conditions.py` when two condition sets reference
  disjoint concept sets?** The Z3 translation would build two independent
  SAT problems glued with `solver.add(expr_a); solver.add(expr_b)`; I did
  not verify whether the `_condition_expr_cache` keyed by
  `(registry_fingerprint, source)` correctly handles this case when the
  registry is shared across both sets but variable allocation is
  per-set. Likely correct (variables are registry-keyed, not set-keyed)
  but unverified.
