# Docstring Audit: Core Argumentation Modules

Audited 2026-03-24. Files: argumentation.py, dung.py, dung_z3.py, preference.py, propagation.py, stances.py, maxsat_resolver.py

## Findings

---

### 1. argumentation.py

#### Finding 1.1 -- Module docstring: HALF-TRUTH

- **File/Line:** `propstore/argumentation.py:1-6`
- **Docstring claim:** `"conditions only decide which claims are active before AF construction"`
- **What the code actually does:** This module never evaluates conditions. It receives `active_claim_ids` as a pre-filtered set from the caller. The module itself has zero condition logic. The docstring implies this module does condition evaluation as a step; it does not.
- **Severity:** HALF-TRUTH -- the statement is architecturally true (conditions are evaluated before AF construction) but falsely implies this module is involved in that evaluation.

#### Finding 1.2 -- `build_argumentation_framework` docstring step 5: HALF-TRUTH

- **File/Line:** `propstore/argumentation.py:95`
- **Docstring claim:** `"Return AF with attacks (pre-preference) and defeats (post-preference + derived)"`
- **What the code actually does:** The returned `attacks` set does NOT include support-type stances (lines 122-124 `continue` before they reach the attacks set) and does NOT include stances below confidence threshold (lines 113-114). But the docstring says "attacks (pre-preference)" implying the only filtering is preference. In reality, attacks is post-confidence-threshold and post-support-filtering, just pre-preference.
- **Severity:** HALF-TRUTH -- "pre-preference" is technically correct but hides the other two filters already applied.

#### Finding 1.3 -- `stance_summary` docstring: OMISSION

- **File/Line:** `propstore/argumentation.py:190-193`
- **Docstring claim:** `"Summarize stances used in AF construction for render explanation."`
- **What the code actually does:** The summary logic diverges from `build_argumentation_framework` in two ways: (1) `stance_summary` uses `_NON_ATTACK_TYPES` (which includes `"none"`) to exclude non-attacks, but `build_argumentation_framework` uses `_SUPPORT_TYPES` to catch supports and then `_ATTACK_TYPES` to catch attacks -- meaning a stance with type `"none"` is silently skipped in `build_argumentation_framework` (line 126, fails the `not in _ATTACK_TYPES` check) but explicitly counted as `excluded_non_attack` in `stance_summary`. (2) `build_argumentation_framework` also skips stances referencing claims not in `claims_by_id` (line 118-119), but `stance_summary` does not perform this check. So the summary does not accurately reflect what the AF construction actually included.
- **Severity:** OMISSION -- the docstring says it summarizes "stances used in AF construction" but the filtering logic is materially different from the actual AF construction.

#### Finding 1.4 -- `compute_consistent_beliefs` docstring: HALF-TRUTH

- **File/Line:** `propstore/argumentation.py:233-237`
- **Docstring claim:** `"Find maximally consistent claim subset using MaxSMT."`
- **What the code actually does:** It calls `maxsat_resolver.resolve_conflicts` which uses `z3.Optimize` with soft constraints. z3.Optimize is an optimization solver, not strictly a "MaxSMT" solver. The z3 documentation distinguishes between MaxSMT (maximum satisfiability) and weighted optimization. The module-level docstring of `maxsat_resolver.py` also calls it "MaxSMT" (line 1). However, `z3.Optimize` with soft constraints is the z3 API for weighted MaxSAT/MaxSMT, so this is at worst a terminological imprecision rather than a lie.
- **Severity:** HALF-TRUTH -- z3.Optimize with soft constraints is functionally MaxSAT-like, but calling it "MaxSMT" is imprecise since the encoding uses only Boolean variables (no SMT theories).

#### Finding 1.5 -- `compute_consistent_beliefs` docstring: OMISSION

- **File/Line:** `propstore/argumentation.py:233-237`
- **Docstring claim:** `"Loads claims, detects conflicts via the conflict detector, computes claim strengths, then calls the MaxSMT resolver"`
- **What the code actually does:** The conflict detection at line 275 filters to only `{ConflictClass.CONFLICT, ConflictClass.OVERLAP, ConflictClass.PARAM_CONFLICT}` -- it excludes other conflict classes. The docstring does not mention this filtering.
- **Severity:** OMISSION -- reader would assume all detected conflicts are passed through.

---

### 2. dung.py

#### Finding 2.1 -- `ArgumentationFramework` docstring: ACCURATE

- **File/Line:** `propstore/dung.py:20-33`
- The docstring correctly describes the dual-relation design (attacks vs defeats) and the fallback behavior when attacks is None.

#### Finding 2.2 -- `defends` unused parameter: OMISSION

- **File/Line:** `propstore/dung.py:59-69`
- **Docstring claim:** `"Check if s defends arg: for every attacker of arg, s counter-attacks it."`
- **What the code actually does:** The function signature includes `all_args: frozenset[str]` (line 62) which is completely unused (has a `# noqa: ARG001` suppression). The docstring does not mention this vestigial parameter. The parameter exists only to maintain signature compatibility with `characteristic_fn` dispatch.
- **Severity:** OMISSION -- minor, but the dead parameter is actively suppressing a lint warning.

#### Finding 2.3 -- `complete_extensions` docstring: LIE (minor)

- **File/Line:** `propstore/dung.py:125-129`
- **Docstring claim:** `"A complete extension is a fixed point of F that is admissible. Reference: Dung 1995, Definition 10."`
- **What the code actually does:** The code is correct (checks both `characteristic_fn(s, ...) == s` and `admissible(s, ...)`). But Definition 10 in Dung 1995 defines *complete extensions* -- the actual Definition 10 states a complete extension is an admissible set S such that every argument defended by S is in S (i.e., a fixed point of F that is admissible). The characterization is correct. However, Dung 1995 numbering: Definition 10 is actually the definition of "complete extension" only in some printings. In the canonical version, the relevant definition may be numbered differently. This is a citation accuracy concern, not a code correctness issue.
- **Severity:** Downgrading to ACCURATE -- the mathematical characterization matches even if the definition number may vary across printings.

#### Finding 2.4 -- `grounded_extension` docstring: ACCURATE

- **File/Line:** `propstore/dung.py:106-113`
- Correctly describes least fixed point iteration. Code matches.

#### Finding 2.5 -- `stable_extensions` docstring: ACCURATE

- **File/Line:** `propstore/dung.py:173-182`
- Correctly describes conflict-free + defeats all outsiders. Code matches. Uses `cf_relation` correctly.

---

### 3. dung_z3.py

#### Finding 3.1 -- Module docstring: HALF-TRUTH

- **File/Line:** `propstore/dung_z3.py:1-5`
- **Docstring claim:** `"Provides SAT-encoded alternatives to the brute-force extension computation in dung.py. Results are identical but scale better for large argumentation frameworks."`
- **What the code actually does:** The module uses `z3.Solver` (an SMT solver), not a pure SAT encoding. The variables are `z3.Bool` and constraints use `Implies`, `And`, `Or`, `Not` -- which are propositional, so calling it "SAT-encoded" is defensible. However, the claim "Results are identical" is an unverified assertion. The encoding appears correct but there is no formal proof or test asserting equivalence for all inputs. More importantly, the z3 solver may return extensions in a different order than brute force.
- **Severity:** HALF-TRUTH -- "SAT-encoded" is technically defensible but "Results are identical" is a strong claim that depends on the encoding being provably equivalent, which is asserted but not proven.

#### Finding 3.2 -- `_conflict_free_constraints` docstring: ACCURATE

- **File/Line:** `propstore/dung_z3.py:27-35`
- Correctly describes Modgil & Prakken Def 14 behavior and fallback to defeats.

#### Finding 3.3 -- `z3_stable_extensions` constraint logic: OMISSION

- **File/Line:** `propstore/dung_z3.py:66-109`
- **Docstring claim:** `"A stable extension S is conflict-free and every argument outside S is defeated by some member of S."`
- **What the code actually does:** The encoding at line 91-93 says `Or(v[a], Or(*[v[b] for b in atks]))` which means "either a is in S, or some attacker of a is in S." This is correct for the outsider condition (if a is NOT in S, then some attacker must be in S). But line 95-96: when `atks` is empty (no attackers), it forces `v[a]` to be True. This means unattacked arguments are always included. This is correct for stable semantics but the docstring does not mention this forced-inclusion behavior.
- **Severity:** OMISSION -- minor, the forced inclusion of unattacked args is a logical consequence but worth noting.

#### Finding 3.4 -- `_extensions_for_semantics` missing "grounded": OMISSION

- **File/Line:** `propstore/dung_z3.py:239-252`
- **Docstring claim:** `"Dispatch to the appropriate z3 extension function."`
- **What the code actually does:** Supports "stable", "complete", and "preferred" but NOT "grounded". Calling with `semantics="grounded"` raises ValueError. The docstring does not state which semantics are supported.
- **Severity:** OMISSION -- a caller might reasonably expect "grounded" to work.

---

### 4. preference.py

#### Finding 4.1 -- `strictly_weaker` elitist definition: LIE

- **File/Line:** `propstore/preference.py:23-25`
- **Docstring claim:** `"Elitist: set_a < set_b iff EXISTS x in set_a s.t. FORALL y in set_b, x < y"`
- **What Modgil & Prakken 2018 Def 19 actually says (elitist ordering):** The elitist ordering compares the MAXIMUM elements: set_a < set_b iff max(set_a) < max(set_b). The docstring's formulation "EXISTS x in set_a such that FORALL y in set_b, x < y" means "some element of A is less than ALL elements of B" -- which is equivalent to `min(set_a) < min(set_b)` when sets are singletons, but diverges for multi-element sets. For the singleton case used in this codebase (claim_strength returns a single float, wrapped in a list at argumentation.py:138-139), the distinction is moot. But the docstring's mathematical claim about Def 19 is wrong for the general case.
- **What the code actually does:** `any(all(x < y for y in set_b) for x in set_a)` -- this checks if ANY element of set_a is strictly less than ALL elements of set_b. This is equivalent to `min(set_a) < min(set_b)` only when... no, it checks if there exists an x in A that is less than every y in B, meaning x < min(B). So the test is: does A contain any element less than min(B)? This is NOT the standard elitist comparison from ASPIC+.
- **Severity:** LIE -- the docstring claims to implement Def 19 elitist ordering but the formula and code implement a different comparison. Mitigated by the fact that the codebase only ever passes singleton lists (line argumentation.py:138-139), making the distinction academic in practice.

#### Finding 4.2 -- `strictly_weaker` democratic definition: HALF-TRUTH

- **File/Line:** `propstore/preference.py:25`
- **Docstring claim:** `"Democratic: set_a < set_b iff FORALL x in set_a EXISTS y in set_b, x < y"`
- **What the code actually does:** Lines 30-32 match this formula. The empty-set guard (line 30-31 returns False) is not mentioned in the docstring but is a reasonable edge case handling.
- **Severity:** HALF-TRUTH -- the formula as stated is correct for the democratic case, but the empty-set behavior is undocumented.

#### Finding 4.3 -- `claim_strength` docstring: HALF-TRUTH

- **File/Line:** `propstore/preference.py:57-64`
- **Docstring claim:** `"Missing metadata is neutral (contributes 0), not penalizing."`
- **What the code actually does:** When ALL metadata is missing, the function returns `1.0` (line 85), not `0.0`. When some metadata is missing and some present, the missing fields don't add to the score but also don't increase the `components` divisor -- so they ARE neutral (don't affect the average). The "contributes 0" phrasing is misleading because the averaging denominator only counts present components. A missing field contributes nothing to numerator AND nothing to denominator, which is neutral for averaging -- but "contributes 0" could be read as "adds 0 to the sum" which would be penalizing if the denominator included it.
- **Severity:** HALF-TRUTH -- the behavior is neutral as claimed, but the explanation "contributes 0" is misleading about the mechanism (it's excluded from averaging, not contributing zero).

#### Finding 4.4 -- `defeat_holds` docstring: ACCURATE

- **File/Line:** `propstore/preference.py:43-48`
- Correctly describes the preference-independent vs preference-dependent distinction. Code matches.

---

### 5. propagation.py

#### Finding 5.1 -- Module docstring: STALE

- **File/Line:** `propstore/propagation.py:1`
- **Docstring claim:** `"Shared SymPy evaluation for parameterization relationships."`
- **What the code actually does:** The module is not "shared" in any observable way -- it exports two functions (`parse_cached` and `evaluate_parameterization`). The word "shared" implies it was factored out from multiple callers, but without evidence of that history, it reads as vestigial naming.
- **Severity:** STALE -- "shared" was likely accurate when the module was extracted but is now just a meaningless adjective.

#### Finding 5.2 -- `evaluate_parameterization` docstring: OMISSION

- **File/Line:** `propstore/propagation.py:28-32`
- **Docstring claim:** `"Returns the computed float value, or None if evaluation fails (missing inputs, unsolvable expression, etc.)."`
- **What the code actually does:** Also returns None if sympy is not installed (line 35-36, `except ImportError: return None`). This is a silent failure mode -- the function will return None with no warning if sympy is missing. The docstring does not mention this.
- **Severity:** OMISSION -- silent dependency failure is important to document.

#### Finding 5.3 -- Module docstring claim about "Self-referencing inputs": ACCURATE

- **File/Line:** `propstore/propagation.py:6`
- **Docstring claim:** `"Self-referencing inputs (output concept in inputs) -- exclude and solve"`
- **What the code actually does:** Line 43 filters out `output_concept_id` from inputs: `effective_inputs = {k: v for k, v in input_values.items() if k != output_concept_id}`. This is accurate.

#### Finding 5.4 -- `parse_cached` has no docstring: OMISSION

- **File/Line:** `propstore/propagation.py:14-20`
- The function has no docstring at all. It is a public function (no underscore prefix) that caches parsed SymPy expressions keyed by expression string and symbol names.
- **Severity:** OMISSION -- missing docstring entirely.

---

### 6. stances.py

#### Finding 6.1 -- Module docstring: ACCURATE but minimal

- **File/Line:** `propstore/stances.py:1`
- **Docstring claim:** `"Shared stance-type vocabulary and helpers."`
- **What the code actually does:** Defines `VALID_STANCE_TYPES` as a frozenset. There are no "helpers" -- only a single constant.
- **Severity:** HALF-TRUTH -- "and helpers" implies there are helper functions. There are none. The module contains exactly one constant.

---

### 7. maxsat_resolver.py

#### Finding 7.1 -- Module docstring: HALF-TRUTH

- **File/Line:** `propstore/maxsat_resolver.py:1-4`
- **Docstring claim:** `"MaxSMT-based conflict resolution. Uses z3.Optimize with soft constraints to find the maximally consistent subset of claims, weighted by claim_strength."`
- **What the code actually does:** Uses `z3.Optimize` with Boolean variables and soft constraints. This is weighted partial MaxSAT, not MaxSMT. SMT (Satisfiability Modulo Theories) implies theories beyond propositional logic (integers, reals, arrays, etc.). The encoding here is purely propositional -- Boolean variables with propositional constraints. "MaxSAT" would be accurate; "MaxSMT" is technically wrong.
- **Severity:** HALF-TRUTH -- z3.Optimize CAN do MaxSMT, but this particular encoding only uses MaxSAT features. The "SMT" label implies more sophistication than is present.

#### Finding 7.2 -- `resolve_conflicts` return on unsat: HALF-TRUTH

- **File/Line:** `propstore/maxsat_resolver.py:48`
- **Docstring claim (comment):** `"# Should never happen with soft constraints"`
- **What the code actually does:** Returns `frozenset()` (empty set) if the solver returns non-sat. The comment claims this path is unreachable. This is correct IF there are no hard constraints that are inherently unsatisfiable -- but the hard constraints (line 34-35) only say conflicting claims can't both be kept, which is always satisfiable (set all to False). So the comment is technically correct: with Boolean variables and "not both True" hard constraints, there is always a satisfying assignment (all False). However, the edge case of a claim conflicting with itself (a == b in a conflict pair) would create `Not(And(x, x))` = `Not(x)`, which is still satisfiable. So the comment is indeed correct.
- **Severity:** ACCURATE -- the comment is correct, the empty-set return is unreachable given the constraint structure.

---

## Summary Table

| # | File | Line | Severity | Short description |
|---|------|------|----------|-------------------|
| 1.1 | argumentation.py | 1-6 | HALF-TRUTH | Module docstring implies it evaluates conditions; it does not |
| 1.2 | argumentation.py | 95 | HALF-TRUTH | "pre-preference" hides confidence and support filtering |
| 1.3 | argumentation.py | 190-193 | OMISSION | stance_summary filtering diverges from actual AF construction |
| 1.4 | argumentation.py | 233-237 | HALF-TRUTH | "MaxSMT" is really weighted MaxSAT |
| 1.5 | argumentation.py | 233-237 | OMISSION | Conflict class filtering not documented |
| 2.2 | dung.py | 59-69 | OMISSION | Unused `all_args` parameter with lint suppression |
| 3.1 | dung_z3.py | 1-5 | HALF-TRUTH | "Results are identical" is asserted not proven |
| 3.4 | dung_z3.py | 239-252 | OMISSION | "grounded" semantics not supported, not documented |
| 4.1 | preference.py | 23-25 | LIE | Elitist ordering formula does not match Modgil & Prakken Def 19 |
| 4.2 | preference.py | 25 | HALF-TRUTH | Empty-set edge case undocumented |
| 4.3 | preference.py | 57-64 | HALF-TRUTH | "contributes 0" misleads about averaging mechanism |
| 5.1 | propagation.py | 1 | STALE | "Shared" is vestigial |
| 5.2 | propagation.py | 28-32 | OMISSION | Silent None return on missing sympy not documented |
| 5.4 | propagation.py | 14-20 | OMISSION | Public function has no docstring |
| 6.1 | stances.py | 1 | HALF-TRUTH | "and helpers" -- there are no helpers |
| 7.1 | maxsat_resolver.py | 1-4 | HALF-TRUTH | "MaxSMT" is really MaxSAT (purely propositional) |

## Highest Priority Issues

1. **Finding 4.1 (LIE):** The elitist ordering in `preference.py` claims to implement Modgil & Prakken 2018 Def 19 but the formula is wrong for multi-element sets. Currently harmless because the codebase only passes singletons, but the docstring's academic citation is incorrect.

2. **Finding 1.3 (OMISSION):** `stance_summary` claims to summarize AF construction but uses different filtering logic. This means the render layer's explanation of what was included may not match what was actually included.

3. **Finding 3.4 (OMISSION):** `_extensions_for_semantics` in dung_z3.py silently excludes "grounded" semantics with no documentation.
