# Hypothesis ASPIC+ Feasibility Scout Notes

Date: 2026-03-25

## GOAL
Determine whether Hypothesis can generate well-formed ASPIC+ theories for property-testing the rationality postulates (Modgil 2018 Thms 12-15).

## OBSERVATIONS

### Existing Hypothesis strategies in the codebase

1. **`tests/test_dung.py::argumentation_frameworks()`** — `@st.composite`, generates random AFs with max 8 args (2-char strings from "abcdefgh"), attacks as frozenset of tuples sampled from args. Simple, flat, fast. ~200 examples, deadline=None.

2. **`tests/test_dung.py::af_with_attacks_superset()`** — generates AFs where attacks is a superset of defeats (some attacks filtered by preference). Uses `st.sampled_from(sorted(all_attacks))` to draw defeats as subset.

3. **`tests/test_preference.py`** — uses `_strengths` (floats 0-10), `_strength_sets` (lists of 1-5 floats), `_comparisons` (sampled from ["elitist","democratic"]), `_preference_attack_types`, `_unconditional_attack_types`. All flat — no composite strategies needed.

4. **`tests/test_opinion.py::valid_opinions()`** — `@st.composite`, draws u, b, d summing to 1, plus base rate a. Uses `assume()` for validity. ~100 examples.

5. **`tests/test_praf.py`** — NO Hypothesis strategies at all. All concrete/regression tests.

### Key architectural observations

- All existing strategies are 1-2 levels deep. The deepest is `af_with_attacks_superset` which chains: generate args → generate attacks → generate defeats as subset.
- ASPIC+ needs 5+ levels of composition: L → contrariness → R_s (with transposition closure) → R_d (with naming) → K_n/K_p (consistent) → argument construction → attack determination → defeat filtering.
- Argument construction is a fixpoint computation (potentially exponential). This runs INSIDE the strategy.
- Current strategies use max_args=8, max_size=5 etc. — small bounds are already the pattern.

### What aspic-literature-requirements.md tells us about data structures needed

- ArgumentationSystem = (L, contrariness, R_s, R_d, n)
- KnowledgeBase = (K_n, K_p)
- Rule = antecedents + consequent + kind + name
- Argument = recursive tree (conclusion, top_rule, direct_sub_arguments)
- Argument construction algorithm is bottom-up fixpoint (Section 9.1)
- Transposition closure is fixpoint (Section 9.5)
- Attack determination is O(|Args|^2 * max|Sub|)

### Feasibility assessment forming

- **Composability**: Hypothesis `@st.composite` can absolutely chain 5+ levels. The `draw()` function is just a call — you can do as much Python as you want inside a composite strategy.
- **Performance**: The key risk. With |L|=8, |R_s|=3, |R_d|=3, |K|=4, argument construction could produce dozens of arguments. With |L|=12+ it explodes. Need tight bounds.
- **Non-triviality**: Major risk. Random formulas + random rules = likely no rule fires. Need careful strategy design to ensure rules have matching antecedents in K.
- **Transposition closure**: Generate-then-close is simpler and more natural for Hypothesis.

## STUCK
Nothing blocked — ready to write the report.

## NEXT
Write the report to reports/hypothesis-aspic-feasibility.md.
