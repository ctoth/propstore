# Audit: ASPIC+ / Structured Argumentation Correctness

Date: 2026-03-24

Auditing against: Modgil & Prakken 2018, Pollock 1987, Cayrol 2005.

Files reviewed:
- `propstore/structured_argument.py`
- `propstore/argumentation.py`
- `propstore/preference.py`
- `propstore/stances.py`
- `propstore/propagation.py` (not argumentation-related, included per instructions)
- `propstore/dung.py`
- `tests/test_structured_argument.py`
- `tests/test_bipolar_argumentation.py`
- `tests/test_preference.py`
- `tests/test_propagation.py`

---

## 1. ASPIC+ Argument Structure

**Finding: MAJOR -- No actual ASPIC+ argument construction.**

The module `structured_argument.py` declares itself as "not full ASPIC+ execution" (line 4). This is honest, but the gap is significant:

- **No rules**: ASPIC+ arguments are built by chaining strict rules (Rs) and defeasible rules (Rd) over premises (Kn, Kp). The implementation has no concept of rules at all. Every argument is a flat "base_claim" with `top_rule_kind="claim"` and `premise_claim_ids=()` (always empty tuple, line 85).

- **No recursive argument construction**: Modgil & Prakken 2018 Def 5 (p.9) defines arguments recursively -- base case from premises, inductive case from applying rules to sub-argument conclusions. This implementation maps each claim 1:1 to an argument. There is no composition.

- **`subargument_ids` always empty**: The field exists on `StructuredArgument` (line 42) but is always set to `()` (line 90). Sub-argument closure (rationality postulate, Thm 12 p.18) is vacuously satisfied but only because there is nothing to close over.

- **`attackable_kind` always "base_claim"**: The field exists (line 41) but is never varied. In ASPIC+, different parts of an argument are attackable in different ways (ordinary premises via undermining, defeasible inference conclusions via rebutting, defeasible rules via undercutting). Here everything is undifferentiated.

**Implication**: The "structured_projection" backend is a thin wrapper around Dung's AF with claim-level arguments. It does not implement ASPIC+ argument construction. The name and docstring are accurate about this, but any code that assumes ASPIC+ structural properties (sub-argument closure, last-link/weakest-link over rules) will not get them.

---

## 2. Attack Types

**Finding: MODERATE -- All three attack types exist as labels but lack structural semantics.**

`_ATTACK_TYPES = frozenset({"rebuts", "undercuts", "undermines", "supersedes"})` (argumentation.py:22)

The four stance types are defined, and the code routes them:
- `undercuts` and `supersedes` -> unconditional defeat (preference-independent)
- `rebuts` and `undermines` -> preference-dependent defeat

**Problem**: The distinction between rebut, undermine, and undercut is purely a label on the stance record. In ASPIC+ (Def 8, p.11):
- Undermining attacks an *ordinary premise* of the target argument
- Rebutting attacks the *conclusion* of a defeasible inference step
- Undercutting attacks the *applicability of a defeasible rule*

Since arguments have no internal structure (no premises, no rules, no sub-arguments), the implementation cannot verify that "undermines" actually targets a premise or "rebuts" actually targets a conclusion. The label is trusted from the stance data without structural validation.

**Finding: `supersedes` has no ASPIC+ counterpart.** It is treated as unconditional defeat. This is a domain-specific extension (reasonable for claim supersession) but not grounded in any of the three reference papers.

---

## 3. Defeat from Attack + Preference

**Finding: CORRECT -- Preference filtering matches Modgil & Prakken 2018 Def 9.**

`defeat_holds()` in `preference.py` (lines 37-53):
- `undercuts` and `supersedes` -> always True (preference-independent) -- correct per Def 9
- `rebuts` and `undermines` -> `not strictly_weaker(attacker, target, comparison)` -- correct per Def 9: attack succeeds as defeat iff the attacker is NOT strictly less preferred.

This means equal-strength attacks succeed as defeats, which matches the paper (an attack is blocked only when the attacker is *strictly* weaker).

**Edge case verified**: `defeat_holds("rebuts", [3], [3], "elitist")` returns True. Correct.

---

## 4. Last-Link vs Weakest-Link

**Finding: MAJOR -- Neither last-link nor weakest-link is implemented.**

Modgil & Prakken 2018 Defs 20-21 (p.21) define two principles for comparing arguments:
- **Last-link**: Compare the last defeasible rules applied in each argument
- **Weakest-link**: Compare both the ordinary premises AND all defeasible rules

The implementation in `preference.py` computes `claim_strength()` from claim-level metadata (sample_size, uncertainty, confidence) and compares these flat vectors. There is no concept of "last defeasible rule" or "all defeasible rules in the argument" because arguments have no rule structure.

The `comparison` parameter (elitist/democratic) correctly implements Def 19's set comparison, but the *sets being compared* are claim metadata dimensions, not sets of rules or premises as Modgil & Prakken specify.

This is internally consistent (elitist vs democratic comparison over claim-strength vectors) but it is NOT last-link or weakest-link in the ASPIC+ sense. The code does not claim otherwise, but anyone expecting ASPIC+ compliance will be surprised.

---

## 5. Rationality Postulates

**Finding: MODERATE -- Postulates are vacuously or trivially satisfied due to flat structure.**

The four postulates from Modgil & Prakken 2018 Thms 12-15 (p.18-19):

1. **Sub-argument closure**: Every sub-argument of an accepted argument must also be accepted. Since `subargument_ids` is always `()`, there are no sub-arguments. Vacuously satisfied.

2. **Closure under strict rules**: If accepted arguments' conclusions entail something via strict rules, that must also be in the extension. No strict rules exist. Vacuously satisfied.

3. **Direct consistency**: The conclusions of accepted arguments must be consistent. The implementation does not check logical consistency of accepted claims. NOT enforced. Two claims with contradictory values for the same concept can both be in the grounded extension if neither attacks the other (i.e., no stance record exists between them).

4. **Non-interference**: Extensions over independent sub-frameworks should not interfere. Not explicitly enforced but unlikely to be violated given the flat AF structure.

**The consistency gap (postulate 3) is the most concerning**: If the stance data is incomplete (missing a "rebuts" stance between two contradictory claims), the AF will accept both. The system relies entirely on stance data completeness for consistency.

---

## 6. Pollock's Rebutting vs Undercutting Defeat

**Finding: CORRECT -- Undercutters are preference-independent.**

Pollock 1987 (Defs 2.4-2.5, p.485) distinguishes:
- Rebutting defeaters: reasons for denying the conclusion
- Undercutting defeaters: reasons for denying the connection between reason and conclusion

Pollock's key insight: undercutting defeaters should NOT be subject to preference-based filtering -- they work regardless of relative strength. This is correctly implemented:

```python
_UNCONDITIONAL_TYPES = frozenset({"undercuts", "supersedes"})  # always succeed
_PREFERENCE_TYPES = frozenset({"rebuts", "undermines"})         # filtered by strength
```

In `defeat_holds()`: `undercuts` always returns True regardless of strengths. Correct.

**However**: Pollock's warrant computation (levels of defeat and reinstatement, Def 4.2 p.492) is not implemented. The system uses Dung's grounded/preferred/stable semantics instead. This is a deliberate design choice (using Dung rather than Pollock's bespoke procedure) and is standard in the literature, but it means Pollock's collective defeat (4.4) and self-defeating argument handling (4.5) are not captured.

---

## 7. Bipolar Argumentation (Cayrol 2005)

**Finding: MOSTLY CORRECT with one semantic gap.**

`_cayrol_derived_defeats()` in `argumentation.py` (lines 46-98) implements Cayrol 2005 Definition 3:
- Supported defeat: A supports* B, B defeats C -> (A, C)
- Indirect defeat: A defeats B, B supports* C -> (A, C)
- Fixpoint iteration for chaining derived defeats (lines 73-97)

**Correct behaviors verified by tests**:
- Basic supported defeat (test_supported_defeat)
- Basic indirect defeat (test_indirect_defeat)
- Transitive support chains (test_chain_supported_defeat)
- Fixpoint chaining (test_cayrol_derived_defeats_chain_transitively) -- the A->B sup, B->C def, C->D sup case correctly produces (A,D) via fixpoint iteration
- Self-support loop terminates (test_self_support_loop_terminates)

**Semantic gap: Deductive support vs necessary support not distinguished.** Cayrol 2005 treats support as a single abstract relation. The implementation has two support types (`supports` and `explains` in `_SUPPORT_TYPES`), but both are treated identically for derived defeat computation. There is no distinction between "deductive support" (if A is accepted then B must be accepted) and "necessary support" (B is acceptable only if A is acceptable). This is fine for Cayrol 2005 itself (which is abstract) but may matter for later work that distinguishes support types.

**Cayrol's safety/coherence semantics NOT implemented**: Cayrol defines safe sets (Def 7), s-admissible (Def 10), and c-admissible (Def 11) extensions. The implementation only computes Dung-style extensions over the expanded defeat relation (with derived defeats added). This means the implementation uses d-admissible semantics only. Whether a set simultaneously set-supports and set-defeats an argument (external incoherence) is NOT checked.

---

## 8. Stance Computation / Premature Commitment

**Finding: GOOD -- No premature commitment in AF construction.**

The system correctly avoids premature commitment:
- All attacks are stored in `attacks` (pre-preference), all defeats in `defeats` (post-preference). Both are exposed on the `ArgumentationFramework` object.
- Conflict-free checking uses `attacks` (Modgil 2018 Def 14), defense uses `defeats` (Dung 1995). This is correct.
- The soft epsilon prune (opinion_uncertainty > 0.99) only removes vacuous opinions, per Josang 2001. This is a minimal gate.
- Support metadata tracking (Label, SupportQuality) preserves provenance without collapsing.

---

## 9. Elitist Set Comparison Edge Case

**Finding: MINOR -- Empty set_b behavior is counterintuitive under elitist.**

`strictly_weaker([], [3, 4], "elitist")` returns False (line 70 test). Correct per Def 19: empty set is not strictly weaker.

But `strictly_weaker([1, 2], [], "elitist")` returns True (line 79 test). This follows from the quantifier structure: EXISTS x in [1,2] s.t. FORALL y in [] (x < y) -- the universal is vacuously true. While logically correct, this means any non-empty set is "strictly weaker" than the empty set under elitist comparison. This is noted in the test and matches the paper's Def 19 formulation: Gamma' = empty, Gamma != empty -> Gamma <_s Gamma'. But it could produce surprising defeat behaviors if claim_strength ever returns an empty list.

`claim_strength()` always returns at least `[1.0]` (line 87), so this edge case cannot actually occur in practice. The guard is adequate.

---

## 10. Grounded Extension with Attacks: Post-hoc Filtering

**Finding: MODERATE -- The grounded extension attack-CF enforcement is a post-hoc filter, not built into the fixpoint.**

In `dung.py` lines 106-151, the grounded extension is computed by:
1. Iterating the characteristic function F to a fixpoint (using defeats for defense)
2. Then filtering for attack-based conflict-freeness by removing attacked-in-extension arguments
3. Re-computing the fixpoint on the reduced set

This is functionally correct for the cases tested, but it is a non-standard construction. Modgil & Prakken 2018 define complete extensions as fixpoints of F that are admissible (where admissible uses attacks for CF). The standard approach is to enumerate complete extensions and take the least one. The post-hoc removal approach could theoretically produce different results than the standard definition in edge cases where the fixpoint of F is not conflict-free w.r.t. attacks and multiple valid reductions exist.

The tests in `test_bipolar_argumentation.py` verify specific cases but do not systematically test that this post-hoc approach yields the same result as the standard definition.

---

## 11. Test Coverage Gaps

**Finding: Several failure modes untested.**

Tested well:
- Cayrol derived defeats (unit and integration)
- Preference ordering (property-based with Hypothesis)
- Attack-based conflict-free (multiple scenarios)
- Structured projection labels and qualities

Not tested:
- **Cyclic support chains**: `_transitive_support_targets` uses visited-set tracking but no test exercises A->B->A support cycles combined with defeats
- **Inconsistent stance data**: No test where two contradictory claims lack a stance record, verifying that both survive into the grounded extension (the consistency gap from finding 5)
- **claim_strength with all-zero or negative metadata**: `claim_strength({"sample_size": 0})` -- sample_size check is `> 0` so this is skipped, but `uncertainty=0` would cause division by zero at line 80. The guard is `uncertainty > 0` which excludes zero, but no test verifies this edge case
- **Mixed-dimensionality comparison**: Two claims with different numbers of strength dimensions (e.g., one has sample_size only, other has sample_size + confidence). The elitist/democratic comparison operates on different-length lists. No test for this
- **PrAF construction**: `build_praf()` in argumentation.py (lines 181-235) has zero test coverage in the files reviewed
- **Structured projection with actual stances**: `test_structured_projection_support_induces_additional_defeat_path` tests one support case. No test for preference-filtered rebuts or undermines through the structured projection path
- **Grounded extension post-hoc attack filtering with complex topology**: Only simple 2-argument cases tested

---

## 12. `claim_strength` Dimension Mismatch

**Finding: MINOR -- Different-dimensionality comparisons may produce arbitrary results.**

If claim A has `{"sample_size": 100}` -> strength `[log1p(100)]` (1 dimension) and claim B has `{"sample_size": 100, "confidence": 0.9}` -> strength `[log1p(100), 0.9]` (2 dimensions), then `strictly_weaker(A_strength, B_strength, "elitist")` compares a 1-element list against a 2-element list. The quantifier semantics handle this (EXISTS x in [4.6] FORALL y in [4.6, 0.9]: x < y -- False because 4.6 is not < 4.6). But the result depends on which signals happen to be present, not on principled argument comparison.

This is not a bug but a semantic concern: two claims with the same data but different metadata availability will compare differently.

---

## 13. Architecture Assessment

**Finding: GOOD -- Clean separation, appropriate abstraction level.**

- `preference.py`: Clean, focused, well-documented with paper references
- `argumentation.py`: Clear separation of AF construction from extension computation
- `dung.py`: Standard Dung semantics, properly extended with attacks
- `structured_argument.py`: Honest about its limitations in docstring
- `stances.py`: Minimal, appropriate

The layering is correct: `stances.py` (vocabulary) -> `preference.py` (ordering) -> `argumentation.py` (AF construction) -> `dung.py` (extension computation) -> `structured_argument.py` (structured projection wrapper).

No spaghetti. Abstractions are appropriate for what is actually implemented.

---

## Summary of Findings

| # | Severity | Finding |
|---|----------|---------|
| 1 | MAJOR | No actual ASPIC+ argument construction (no rules, no premises, no sub-arguments) |
| 2 | MODERATE | Attack type labels lack structural validation against argument internals |
| 3 | CORRECT | Preference filtering matches Def 9 |
| 4 | MAJOR | Neither last-link nor weakest-link principle implemented |
| 5 | MODERATE | Direct consistency postulate not enforced; relies on stance data completeness |
| 6 | CORRECT | Undercutters are preference-independent per Pollock |
| 7a | CORRECT | Cayrol derived defeats with fixpoint chaining |
| 7b | MODERATE | Cayrol safety/coherence semantics not implemented (d-admissible only) |
| 8 | GOOD | No premature commitment in AF/stance handling |
| 9 | MINOR | Empty-set elitist comparison edge case (guarded in practice) |
| 10 | MODERATE | Grounded extension attack-CF via post-hoc filtering, not standard construction |
| 11 | MODERATE | Several untested failure modes (mixed dims, cyclic support, missing stances) |
| 12 | MINOR | Different-dimensionality claim_strength comparisons are semantically fragile |
| 13 | GOOD | Clean architecture and abstraction |

The two MAJOR findings (1, 4) are acknowledged in the code: the docstring says "not full ASPIC+ execution." The system is a claim-graph backend inspired by ASPIC+ ideas, not an ASPIC+ implementation. If full ASPIC+ compliance is a goal, substantial work is needed on argument construction, rule systems, and last-link/weakest-link ordering over argument structure. If the current claim-graph approach is the intended design, the docstrings are honest and the implementation is sound within its scope.
