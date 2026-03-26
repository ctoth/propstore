# Feasibility Report: Hypothesis Strategies for ASPIC+ Argumentation Theories

Date: 2026-03-25
Scout: hypothesis-aspic-feasibility

---

## 1. Feasibility Verdict: YES (with bounded size and careful strategy design)

Hypothesis can generate well-formed ASPIC+ argumentation theories suitable for property-testing the rationality postulates (Modgil 2018 Theorems 12-15). The approach is feasible provided:

- The logical language |L| is bounded to <= 8 formulas
- Rule sets are small: |R_s| <= 4, |R_d| <= 4
- Knowledge bases are small: |K| <= 6
- Strategies are designed to guarantee non-trivial examples (rules that actually fire)
- Argument construction runs inside the strategy, not as a separate step

The existing codebase already demonstrates the core patterns needed. The `argumentation_frameworks()` strategy in `tests/test_dung.py` generates random AFs with up to 8 arguments and runs 200 examples with `deadline=None`. The ASPIC+ strategy will be more complex but follows the same `@st.composite` pattern.

---

## 2. Existing Strategy Patterns (What We Have)

### 2.1 `tests/test_dung.py::argumentation_frameworks()` (lines 34-54)

The foundation pattern. A `@st.composite` strategy that:
1. Draws a frozenset of 1-8 arguments (2-char strings from alphabet "abcdefgh")
2. Sorts the arguments into a list for `st.sampled_from()`
3. Draws a frozenset of attack tuples sampled from the argument list
4. Returns an `ArgumentationFramework` dataclass

Key design choices: small alphabet limits combinatorial explosion; `st.sampled_from()` ensures attacks only reference existing arguments; `frozenset` gives hashability for Hypothesis's shrinking.

### 2.2 `tests/test_dung.py::af_with_attacks_superset()` (lines 406-443)

A more complex 2-level strategy that generates AFs where `attacks` is a superset of `defeats`. Demonstrates:
- Chaining dependent draws (defeats drawn from the previously-drawn attacks set)
- Handling empty sets gracefully (`st.nothing()` fallback)
- The pattern of "generate a superset, then draw a subset" — directly applicable to generating K then partitioning into K_n/K_p

### 2.3 `tests/test_opinion.py::valid_opinions()` (lines 362-379)

Demonstrates constraint satisfaction inside a composite strategy:
- Draws u first, then b from remaining budget, computes d = 1 - u - b
- Uses `assume()` to filter floating-point drift
- Shows that algebraic constraints (b + d + u = 1) can be maintained by construction rather than rejection

### 2.4 `tests/test_preference.py` (lines 24-28)

Shows flat strategy composition without `@st.composite`:
- `_strengths`, `_strength_sets`, `_comparisons`, `_attack_types` as module-level strategies
- Combined via `@given()` with multiple strategy arguments
- 200 examples with `deadline=None` is the established baseline

### 2.5 `tests/test_praf.py`

No Hypothesis strategies. All concrete/regression tests. This is a gap — PrAF would also benefit from property testing, but it's orthogonal to the ASPIC+ question.

---

## 3. Proposed Strategy Architecture

The ASPIC+ strategy must compose five levels, each depending on the previous. Here is the proposed decomposition into sub-strategies:

### Level 1: `logical_language()` — Generate L and Contrariness

```
@st.composite
def logical_language(draw, max_formulas=8):
    # Generate atomic formulas: "p", "q", "r", "s", "t", "u", "v", "w"
    atoms = draw(st.frozensets(
        st.sampled_from(["p","q","r","s","t","u","v","w"]),
        min_size=2, max_size=max_formulas // 2,
    ))
    # Negated forms: "~p", "~q", etc.
    L = atoms | {f"~{a}" for a in atoms}

    # Contrariness: (phi, ~phi) are contradictories (symmetric)
    contradictories = {(a, f"~{a}") for a in atoms}
    # Optionally draw some asymmetric contraries between non-negation pairs
    ...
    return L, contradictories, contraries
```

**Key insight**: By constructing L as atoms + their negations, we guarantee every formula has at least one contrary/contradictory. This avoids generating useless formulas that can never participate in attacks.

**Size analysis**: With max 4 atoms, |L| = 8. This is the same scale as the existing Dung AF strategy.

### Level 2: `strict_rules(L)` — Generate R_s with Transposition Closure

```
@st.composite
def strict_rules(draw, L, max_rules=3):
    # Draw raw strict rules: 1-2 antecedents -> consequent, all from L
    raw_rules = draw(st.lists(
        st.tuples(
            st.frozensets(st.sampled_from(sorted(L)), min_size=1, max_size=2),
            st.sampled_from(sorted(L)),
        ),
        max_size=max_rules,
    ))
    # Filter: consequent must not be in antecedents
    raw_rules = [(antes, cons) for antes, cons in raw_rules if cons not in antes]
    # Compute transposition closure (fixpoint)
    R_s = set(raw_rules)
    changed = True
    while changed:
        changed = False
        for antes, cons in list(R_s):
            for a in antes:
                transposed_antes = (antes - {a}) | {negate(cons)}
                transposed_cons = negate(a)
                t = (transposed_antes, transposed_cons)
                if t not in R_s:
                    R_s.add(t)
                    changed = True
    return frozenset(R_s)
```

**Transposition closure approach**: Generate-then-close. This is more natural for Hypothesis than trying to generate closed sets directly, because:
1. Direct generation of closed sets requires solving a constraint problem inside the strategy
2. Generate-then-close is a simple fixpoint that always terminates
3. The closure may expand the rule set, but with |L|=8 and max 3 seed rules, the closure is bounded

**Size blowup risk**: One strict rule with n antecedents generates n transpositions. With max 2 antecedents, each rule generates at most 2 transpositions. Starting from 3 raw rules, the closure is at most ~9 rules. With 3 antecedents per rule (if we allow it), the closure could reach ~12 rules from 3 seeds. This is manageable.

### Level 3: `defeasible_rules(L)` — Generate R_d with Naming

```
@st.composite
def defeasible_rules(draw, L, max_rules=4):
    rules = draw(st.lists(
        st.tuples(
            st.frozensets(st.sampled_from(sorted(L)), min_size=1, max_size=2),
            st.sampled_from(sorted(L)),
        ),
        max_size=max_rules,
    ))
    # Assign names: n(r_i) = "d_i" — add these to L
    named_rules = []
    for i, (antes, cons) in enumerate(rules):
        if cons not in antes:
            name = f"d{i}"
            named_rules.append((antes, cons, name))
    return named_rules  # also return the names to extend L
```

**Naming**: Each defeasible rule gets a synthetic name formula (e.g., "d0", "d1"). These names are added to L and get negation forms ("~d0", "~d1") so undercutting attacks can target them. This is exactly how Modgil 2018 Def 2 works.

### Level 4: `knowledge_base(L, R_s, R_d)` — Generate K_n and K_p

```
@st.composite
def knowledge_base(draw, L, R_s, R_d):
    # K_n: axiom premises, must be consistent
    K_n = draw(st.frozensets(st.sampled_from(sorted(L)), max_size=2))
    # Filter: no formula and its contrary both in K_n
    assume(is_consistent(K_n, contrariness))

    # K_p: ordinary premises, may be inconsistent
    K_p = draw(st.frozensets(st.sampled_from(sorted(L)), min_size=1, max_size=4))

    # NON-TRIVIALITY: ensure at least one rule's antecedents are covered by K
    assume(any(
        antes <= (K_n | K_p)
        for antes, cons, *_ in (list(R_s) + list(R_d))
    ))

    return K_n, K_p
```

**Non-triviality guarantee**: The `assume()` call rejects knowledge bases where no rule can fire. This is critical — without it, most generated theories would have zero non-premise arguments. The rejection rate depends on how well-aligned the formulas in K are with rule antecedents.

**Optimization**: Instead of `assume()` (which causes Hypothesis to discard and retry), we could construct K_p to *include* at least one rule's antecedents:

```
# Pick a rule and force its antecedents into K_p
if R_s or R_d:
    target_rule = draw(st.sampled_from(list(R_s) + list(R_d)))
    forced = target_rule.antecedents
    K_p = forced | draw(st.frozensets(...))
```

This construction-based approach eliminates rejection entirely.

### Level 5: `aspic_theory()` — The Top-Level Composite

```
@st.composite
def aspic_theory(draw):
    L, contradictories, contraries = draw(logical_language())
    R_s = draw(strict_rules(L))
    R_d, rule_names = draw(defeasible_rules(L))
    L_extended = L | set(rule_names) | {f"~{n}" for n in rule_names}
    K_n, K_p = draw(knowledge_base(L_extended, R_s, R_d))

    # ARGUMENT CONSTRUCTION (computed, not drawn)
    arguments = build_arguments(K_n, K_p, R_s, R_d)

    # ATTACK DETERMINATION (computed)
    attacks = determine_attacks(arguments, contradictories, contraries)

    # PREFERENCE ORDERING (drawn)
    ordering_type = draw(st.sampled_from(["last_link", "weakest_link"]))
    comparison = draw(st.sampled_from(["elitist", "democratic"]))
    base_ordering = draw(generate_base_ordering(R_d, K_p))

    # DEFEAT FILTERING (computed)
    defeats = filter_defeats(attacks, ordering_type, comparison, base_ordering)

    return WellFormedCSAF(
        L=L_extended,
        contrariness=(contradictories, contraries),
        R_s=R_s, R_d=R_d,
        K_n=K_n, K_p=K_p,
        arguments=arguments,
        attacks=attacks,
        defeats=defeats,
        ordering_type=ordering_type,
        comparison=comparison,
    )
```

**Argument construction inside the strategy**: This is the key question from the prompt. Yes, Hypothesis absolutely supports running arbitrary computation inside `@st.composite`. The `draw()` function is just a Python call; everything else is normal Python code. The `build_arguments()` fixpoint runs as pure computation — Hypothesis doesn't care how long it takes, only whether it exceeds the deadline (which we set to `None`).

---

## 4. Size Bounds for Tractable Generation

### 4.1 Argument Construction Complexity

Argument construction is worst-case exponential: with n premises and m rules, the number of possible arguments can be O(n^m) if rules chain deeply. But with bounded inputs:

| Parameter | Bound | Rationale |
|-----------|-------|-----------|
| |L| (atoms) | 4 | 8 formulas total (with negations) |
| |R_s| (seed, pre-closure) | 3 | Closure adds ~6 more = ~9 total |
| |R_d| | 4 | Each becomes one argument step |
| |K_n| | 2 | Axiom premises |
| |K_p| | 4 | Ordinary premises |
| Max antecedents per rule | 2 | Limits combinatorial branching |
| Max argument depth | 3 | Natural from small rule sets |

### 4.2 Estimated Argument Counts

With these bounds:
- **Premise arguments**: |K_n| + |K_p| = up to 6
- **One-step rule applications**: each rule with matching antecedents produces 1 argument per combination. With 2-antecedent rules and 6 premises, worst case ~15 combinations per rule, ~60 for 4 rules. But most combinations won't match.
- **Two-step chaining**: arguments from step 1 become available antecedents. Adds another layer but quickly exhausts novel conclusions (only 8 formulas in L).
- **Realistic estimate**: 10-30 arguments per theory.

### 4.3 Timing Estimate

- Argument construction (fixpoint): ~1ms for 20 arguments
- Attack determination (O(|Args|^2 * max|Sub|)): ~0.5ms for 20 arguments with depth 3
- Extension computation (reuse existing `dung.py`): ~5ms for 20 arguments (dominated by preferred/stable brute-force)
- **Total per example**: ~10ms
- **200 examples**: ~2 seconds

This is well within Hypothesis's tolerance, especially with `deadline=None`.

### 4.4 Comparison to Existing Strategies

The `argumentation_frameworks()` strategy generates up to 8 arguments with up to 64 attacks. The ASPIC+ strategy would generate ~20 arguments with ~50 attacks (derived). The extension computation is the bottleneck in both cases, and it's the same code (`dung.py`). The overhead of argument construction is small relative to extension computation.

---

## 5. Key Risks and Mitigations

### Risk 1: Non-Trivial Examples (HIGH)

**Problem**: Random rules over random formulas will rarely fire. Most generated theories will have only premise arguments and no attacks.

**Mitigation**: Construction-based non-triviality. Instead of `assume()` rejection:
1. Draw rules first
2. Force at least one rule's antecedents into K_p
3. Ensure contrariness pairs exist among conclusions reachable from K

**Evidence**: The existing `af_with_attacks_superset()` strategy uses a similar pattern — it draws attacks first, then draws defeats as a subset. The "draw the interesting structure first, then fill in the rest" pattern is well-established in the codebase.

### Risk 2: Transposition Closure Blowup (MEDIUM)

**Problem**: Transposition closure can expand rule sets significantly. With 3-antecedent rules, each rule generates 3 transpositions, each of which generates 3 more, etc.

**Mitigation**:
1. Limit antecedents to 2 per strict rule (yields at most 2 transpositions per rule)
2. Set a hard cap on |R_s| after closure (e.g., 15). If exceeded, `assume(False)` and retry
3. The closure is guaranteed to terminate because L is finite — there are at most |L|^(k+1) possible rules with k antecedents

### Risk 3: Hypothesis Shrinking Breaks Invariants (MEDIUM)

**Problem**: Hypothesis shrinks failing examples by removing elements. But removing a formula from L could invalidate rules that reference it; removing a rule could break transposition closure.

**Mitigation**:
1. Shrinking operates on the *drawn* values (the random choices), not on the derived values. So Hypothesis shrinks the *seed* rules and re-runs the closure, producing a valid smaller theory.
2. The `@st.composite` pattern naturally handles this — all derived values are recomputed from the drawn values on each shrink attempt.
3. This is a strength of the generate-then-derive approach over a generate-everything approach.

### Risk 4: Floating-Point in Preference Ordering (LOW)

**Problem**: Preference ordering uses float comparisons. Hypothesis is good at finding float edge cases.

**Mitigation**: Already handled by the existing `tests/test_preference.py` strategies. The ASPIC+ strategy reuses the same `_strengths` and `_comparisons` strategies.

### Risk 5: Empty Extensions (LOW)

**Problem**: Generated theories might always have empty grounded extensions (e.g., all arguments attack each other).

**Mitigation**: This is actually fine for property testing. The rationality postulates (sub-argument closure, strict closure, consistency) all hold vacuously for the empty extension. The interesting cases are non-empty preferred/stable extensions, which the strategy will produce when there are unattacked arguments (guaranteed when K_n produces firm+strict arguments that cannot be attacked per Modgil 2018 Def 18).

---

## 6. Specific Feasibility Answers

### Q1: Can Hypothesis strategies compose to this depth?

**YES.** `@st.composite` strategies can nest arbitrarily. Each level calls `draw()` on sub-strategies, and arbitrary Python computation runs between draws. The existing `af_with_attacks_superset()` strategy demonstrates 2-level composition; the ASPIC+ strategy needs 5 levels, but there is no architectural limit.

The key constraint is that *drawn* values must be the source of randomness, and *derived* values (arguments, attacks, defeats) must be deterministically computed from the drawn values. This ensures Hypothesis's shrinking and replay work correctly. The proposed architecture satisfies this: L, rules, and K are drawn; arguments, attacks, and defeats are derived.

### Q2: Will it be fast enough?

**YES, with the proposed bounds.** Estimated ~10ms per example, ~2s for 200 examples. The existing `argumentation_frameworks()` strategy runs 200 examples and the bottleneck is extension computation in `dung.py`, which is the same code reused here.

The argument construction fixpoint is the new cost center, but with |L|=8 and bounded rules it terminates quickly. The transposition closure fixpoint is even cheaper (purely syntactic, no search).

### Q3: Can we ensure non-trivial examples?

**YES, via construction.** Force at least one rule's antecedents into K_p. Force at least one contrariness pair among reachable conclusions. This guarantees at least one non-premise argument and at least one attack in every generated theory.

`assume()` is the fallback for additional constraints (e.g., K_n consistency), but the primary non-triviality mechanism should be construction-based to minimize rejection rate.

### Q4: How do we handle transposition closure?

**Generate-then-close** is the recommended approach. Reasons:
1. Generating closed rule sets directly requires solving a constraint — impractical for Hypothesis
2. Generate-then-close is a deterministic fixpoint applied after drawing seed rules
3. Shrinking works correctly: Hypothesis shrinks the seed rules, then re-runs the closure
4. The closure is bounded by |L|^(k+1) where k is max antecedents per rule

### Q5: Existing precedent?

**In this codebase**: `argumentation_frameworks()` and `af_with_attacks_superset()` demonstrate the pattern. `valid_opinions()` demonstrates constraint-aware generation.

**In the literature**: No published examples of ASPIC+ property testing with Hypothesis were found. The closest is Niskanen et al. 2020 (Toxisia) which generates random AFs for solver testing, but uses C++ and custom generators, not Hypothesis. Mahmood et al. 2025 (Structure-Aware Encodings) use random graph generation for AF benchmarking but again not Hypothesis.

This would be novel — which is both a risk (no prior art to learn from) and an opportunity (publishable contribution if it works).

### Q6: Alternative: table-driven?

**Viable as a complement, not a replacement.** A curated set of 20-50 hand-crafted theories covering known edge cases (from Modgil 2018 examples, Prakken 2010 examples, pathological cases) provides guaranteed coverage of specific scenarios. But it cannot find the unexpected edge cases that Hypothesis excels at discovering.

**Recommended approach**: Both.
1. Hand-crafted theories as concrete regression tests (like the existing `TestGroundedConcrete` pattern)
2. Hypothesis strategies for property tests (like the existing `TestGroundedProperties` pattern)

The hand-crafted theories also serve as validation for the strategy — if the strategy generates a theory equivalent to a hand-crafted one, both the strategy and the implementation are confirmed correct.

### Q7: ATMS composition properties?

**Same approach applies.** The ATMS + AF composite system has these generated components:
- ATMS: assumptions, justifications, nogoods
- AF: arguments (from ATMS assumptions), defeats (from justification conflicts)
- Composition: ATMS label propagation must agree with AF extension membership

A `@st.composite` strategy can generate a small ATMS (3-5 assumptions, 2-4 justifications, 1-2 nogoods), derive the corresponding AF, compute both ATMS labels and AF extensions, and assert consistency. Size bounds are even tighter than ASPIC+ because ATMS label propagation is polynomial.

---

## 7. Pseudocode: Top-Level Strategy

```python
@st.composite
def well_formed_csaf(draw, max_atoms=4, max_strict=3, max_defeasible=4, max_premises=4):
    """Generate a well-formed c-SAF per Modgil 2018 Def 12.

    Guarantees:
    - Axiom consistency (K_n contains no formula and its contrary)
    - Well-formed contrariness (contradictories symmetric, contraries asymmetric)
    - Transposition closure (R_s = Cl(R_s))
    - At least one non-premise argument (non-triviality)
    """
    # --- Level 1: Language ---
    atoms = draw(st.lists(
        st.sampled_from(ATOM_POOL),
        min_size=2, max_size=max_atoms, unique=True,
    ))
    L = set(atoms) | {neg(a) for a in atoms}
    contradictories = frozenset((a, neg(a)) for a in atoms)
    # Optional asymmetric contraries between select atom pairs
    contrary_pairs = draw(st.frozensets(
        st.tuples(st.sampled_from(atoms), st.sampled_from(atoms)).filter(lambda t: t[0] != t[1]),
        max_size=2,
    ))

    # --- Level 2: Strict rules (with transposition closure) ---
    seed_strict = draw(st.lists(
        rule_from(L, max_antecedents=2),
        max_size=max_strict,
    ))
    R_s = transposition_closure(seed_strict, L)  # deterministic fixpoint

    # --- Level 3: Defeasible rules (with naming) ---
    raw_defeasible = draw(st.lists(
        rule_from(L, max_antecedents=2),
        max_size=max_defeasible,
    ))
    R_d = []
    for i, (antes, cons) in enumerate(raw_defeasible):
        name = f"d{i}"
        L.add(name)
        L.add(neg(name))
        R_d.append(DefeasibleRule(antes, cons, name))

    # --- Level 4: Knowledge base ---
    # Force at least one rule's antecedents into K_p for non-triviality
    all_rules = list(R_s) + list(R_d)
    if all_rules:
        target = draw(st.sampled_from(all_rules))
        forced_premises = target.antecedents
    else:
        forced_premises = set()

    K_p = forced_premises | draw(st.frozensets(
        st.sampled_from(sorted(L)),
        max_size=max_premises,
    ))
    K_n = draw(st.frozensets(st.sampled_from(sorted(L)), max_size=2))
    assume(is_consistent(K_n, contradictories))
    assume(K_n & K_p == set())  # disjoint partitions (optional strictness)

    # --- Level 5: Derived structure ---
    arguments = construct_arguments(K_n, K_p, R_s, R_d)  # fixpoint
    assume(len(arguments) > len(K_n) + len(K_p))  # at least one rule fired

    attacks = determine_attacks(arguments, contradictories, contrary_pairs)
    ordering = draw(st.sampled_from(["last_link", "weakest_link"]))
    comparison = draw(st.sampled_from(["elitist", "democratic"]))
    base_ord = draw(generate_base_ordering(R_d, K_p))
    defeats = compute_defeats(attacks, arguments, ordering, comparison, base_ord)

    # --- Build AF for Dung layer ---
    arg_ids = frozenset(a.id for a in arguments)
    af = ArgumentationFramework(
        arguments=arg_ids,
        defeats=frozenset(defeats),
        attacks=frozenset((a, b) for a, b, _ in attacks),
    )

    return CSAF(
        language=L, contrariness=(contradictories, contrary_pairs),
        R_s=R_s, R_d=R_d, K_n=K_n, K_p=K_p,
        arguments=arguments, framework=af,
        ordering=ordering, comparison=comparison,
    )
```

---

## 8. Property Tests Enabled by This Strategy

With `well_formed_csaf()`, we can assert the four rationality postulates as Hypothesis property tests:

```python
@given(well_formed_csaf())
@settings(max_examples=100, deadline=None)
def test_sub_argument_closure(csaf):
    """Thm 12: If A in E and A' in Sub(A), then A' in E."""
    for ext in complete_extensions(csaf.framework):
        for arg_id in ext:
            arg = csaf.arguments_by_id[arg_id]
            for sub in arg.sub_arguments:
                assert sub.id in ext

@given(well_formed_csaf())
@settings(max_examples=100, deadline=None)
def test_strict_closure(csaf):
    """Thm 13: Conc(E) is closed under R_s."""
    for ext in complete_extensions(csaf.framework):
        conclusions = {csaf.arguments_by_id[a].conclusion for a in ext}
        closed = strict_closure(conclusions, csaf.R_s)
        assert closed == conclusions

@given(well_formed_csaf())
@settings(max_examples=100, deadline=None)
def test_direct_consistency(csaf):
    """Thm 14: No two conclusions in E are contraries/contradictories."""
    for ext in complete_extensions(csaf.framework):
        conclusions = {csaf.arguments_by_id[a].conclusion for a in ext}
        for c1 in conclusions:
            for c2 in conclusions:
                assert (c1, c2) not in csaf.contradictories
                assert (c1, c2) not in csaf.contraries

@given(well_formed_csaf())
@settings(max_examples=100, deadline=None)
def test_indirect_consistency(csaf):
    """Thm 15: Cl_Rs(Conc(E)) is consistent."""
    for ext in complete_extensions(csaf.framework):
        conclusions = {csaf.arguments_by_id[a].conclusion for a in ext}
        closed = strict_closure(conclusions, csaf.R_s)
        for c1 in closed:
            for c2 in closed:
                assert (c1, c2) not in csaf.contradictories
                assert (c1, c2) not in csaf.contraries
```

These four tests are the ultimate validation: if they pass on 100+ random well-formed theories, the implementation is correct. If any fails, Hypothesis provides a minimal counterexample showing exactly which theory structure breaks which postulate.

---

## 9. Implementation Roadmap

### Phase A: Infrastructure (before Hypothesis)
1. Implement `Rule`, `Argument` (recursive), `CSAF` dataclasses
2. Implement `construct_arguments()` fixpoint
3. Implement `determine_attacks()` (three types on sub-arguments)
4. Implement `compute_defeats()` (preference-filtered)
5. Implement `transposition_closure()`
6. Implement `strict_closure()`

### Phase B: Hypothesis Strategies
7. Implement `logical_language()` strategy
8. Implement `strict_rules()` strategy (with closure)
9. Implement `defeasible_rules()` strategy (with naming)
10. Implement `knowledge_base()` strategy (with forced non-triviality)
11. Implement `well_formed_csaf()` composite strategy

### Phase C: Property Tests
12. Write the four rationality postulate tests (Thms 12-15)
13. Write structural invariant tests (firm+strict in every complete extension, undercutting always succeeds, axiom premises never attacked)
14. Write regression tests from Modgil 2018 examples (hand-crafted)

### Phase D: Integration
15. Wire `well_formed_csaf()` into the existing test suite alongside `argumentation_frameworks()`
16. Verify that the Dung-level property tests (from `test_dung.py`) still pass when the AF is derived from an ASPIC+ theory

---

## 10. Summary

| Question | Answer |
|----------|--------|
| Can Hypothesis compose to this depth? | Yes — `@st.composite` supports arbitrary nesting and computation |
| Will it be fast enough? | Yes — ~10ms/example with proposed bounds |
| Can we ensure non-triviality? | Yes — construction-based (force rule antecedents into K) |
| How to handle transposition closure? | Generate seed rules, then close deterministically |
| Existing precedent? | In-codebase patterns exist; no published ASPIC+ property testing |
| Table-driven alternative? | Complement, not replacement — use both |
| ATMS composition? | Same approach, even simpler (polynomial label propagation) |
| **Overall verdict** | **Feasible. Proceed with implementation.** |
