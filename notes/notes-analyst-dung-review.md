# Analyst Review: Dung AF Implementation

## GOAL
Review propstore's Dung argumentation framework against Dung 1995, Modgil & Prakken 2018, Cayrol 2005.

## FILES READ
- propstore/dung.py — core AF, grounded/preferred/stable/complete
- propstore/dung_z3.py — z3 SAT-backed extensions
- propstore/argumentation.py — claim-graph backend, Cayrol bipolar
- propstore/structured_argument.py — structured projection backend
- propstore/preference.py — ASPIC+ preference ordering
- tests/test_dung.py — property + concrete tests
- tests/test_dung_z3.py — z3 vs brute-force equivalence
- tests/test_preference.py — preference ordering tests
- tests/test_bipolar_argumentation.py — Cayrol + Modgil tests
- tests/test_structured_argument.py — structured projection tests
- tests/test_argumentation_integration.py — end-to-end integration

## FINDINGS (in progress)

### FINDING 1: Grounded extension — CORRECT
dung.py:106-119 — Iterates F from empty set until fixed point. This is Dung 1995 Def 20 / Thm 25. Correct.
BUT: grounded_extension does NOT check conflict-free or admissibility of its result. It doesn't need to (the least fixed point is guaranteed admissible by theorem), but the iteration could diverge for a buggy characteristic_fn. Low risk.

### FINDING 2: Grounded ignores attacks relation — SEMANTIC ISSUE
dung.py:116 — `characteristic_fn(s, framework.arguments, framework.defeats)` only uses defeats.
The grounded extension is computed purely from defeats, ignoring the attacks relation entirely.
test_bipolar_argumentation.py:354-367 confirms this: grounded({A,B}, defeats={}, attacks={(A,B)}) = {A,B}.
This means the grounded extension can contain arguments that attack each other (pre-preference).
Per Modgil & Prakken 2018, the grounded extension should still be conflict-free w.r.t. attacks.
The test at line 354 explicitly documents this as expected behavior, but it violates Def 14.
The grounded is then NOT attack-conflict-free, which breaks the ASPIC+ rationality postulates.

### FINDING 3: Elitist comparison with empty set_b — EDGE CASE BUG
preference.py:27-28 — `strictly_weaker` elitist: `any(all(x < y for y in set_b) for x in set_a)`.
When set_b is empty, `all(x < y for y in [])` is vacuously True, so `any(True for x in set_a)` = True.
test_preference.py:79 confirms: `strictly_weaker([1, 2], [], "elitist") is True`.
This means any argument is "strictly weaker" than an argument with no strength signals under elitist.
This is mathematically correct (vacuous truth) but semantically questionable — it means a claim with known sample_size is considered weaker than a claim with no metadata at all under the elitist comparison. In defeat_holds, this means rebuts/undermines by a claim with strengths against a claim with NO strengths would be BLOCKED. That seems backwards.
However: claim_strength returns 1.0 for empty claims, so in practice the list never becomes empty at the preference.py call sites. The edge case is tested but may not be reachable from real code paths.

### FINDING 4: Cayrol derived defeats are single-pass — POTENTIAL UNDER-APPROXIMATION
argumentation.py:46-78 and structured_argument.py:193-213 — Cayrol derived defeats computed in one pass.
The comment at test_bipolar_argumentation.py:119-128 acknowledges this: "(A, D) requires A defeats C (a derived defeat) plus C supports D. But derived defeats don't chain further in a single pass."
This means transitive derived defeats through multiple support-defeat-support chains are missed.
Cayrol 2005 does define derived defeats transitively. A proper implementation would iterate to fixed point.

### FINDING 5: DRY violation — duplicated Cayrol code
argumentation.py:29-78 duplicates _transitive_support_targets and _cayrol_derived_defeats.
structured_argument.py:193-229 has its own copy of the same functions.
Both are identical in logic. If one gets a bug fix, the other won't.

### FINDING 6: DRY violation — duplicated attack type constants
argumentation.py:22-26 defines _ATTACK_TYPES, _UNCONDITIONAL_TYPES, etc.
structured_argument.py:23-27 defines the exact same constants.
These should live in one place.

### FINDING 7: Stable extension — missing admissibility check
dung.py:173-201 — stable_extensions checks conflict-free + defeats all outsiders.
Dung 1995 Def 12 says stable = conflict-free + attacks every non-member.
The implementation is correct per Dung's definition (stable implies admissible by theorem, no need to check separately).

### FINDING 8: Complete extensions — correct
dung.py:122-148 — checks both F(S)=S (fixed point) AND admissible. Correct per Dung Def 23.

### FINDING 9: Preferred extensions — correct
dung.py:151-170 — maximal complete extensions. Uses strict subset operator `<`. Correct.

### FINDING 10: z3 encoding — potential soundness issue with model extraction
dung_z3.py:44-45 — `_extract_extension`: `model[var]` can return None for don't-care variables.
If z3 doesn't assign a value to a variable (don't-care), `model[var]` returns None, which is falsy.
This means don't-care args are excluded from extensions. For complete/stable this is likely fine since constraints force assignment, but worth noting.

### FINDING 11: Test coverage gap — no test for grounded extension NOT being attack-CF
The test at test_bipolar_argumentation.py:354-367 documents the behavior but doesn't flag it as a known limitation. There's no test asserting the grounded IS attack-conflict-free (because it isn't).

### FINDING 12: Test coverage gap — no failure mode tests for claim_strength
No test for negative sample_size, negative uncertainty, confidence > 1.0, or NaN values.
claim_strength does not validate inputs.

### FINDING 13: Exponential brute-force — no guard
dung.py:140-148, 191-201 — brute-force iterates 2^n subsets. No size guard.
For n=30 args, that's ~1 billion iterations. No warning, no timeout, no fallback to z3.

## STATUS
All files read. Writing up findings.
