# Code Review: Argumentation and Formal Reasoning Subsystem

Date: 2026-03-23

## Files Reviewed

Core argumentation/reasoning (9 files):
- `propstore/dung.py`
- `propstore/dung_z3.py`
- `propstore/argumentation.py`
- `propstore/preference.py`
- `propstore/maxsat_resolver.py`
- `propstore/z3_conditions.py`
- `propstore/cel_checker.py`
- `propstore/propagation.py`
- `propstore/sensitivity.py`

Conflict detector package (9 files):
- `propstore/conflict_detector/__init__.py`
- `propstore/conflict_detector/models.py`
- `propstore/conflict_detector/algorithms.py`
- `propstore/conflict_detector/collectors.py`
- `propstore/conflict_detector/context.py`
- `propstore/conflict_detector/equations.py`
- `propstore/conflict_detector/measurements.py`
- `propstore/conflict_detector/orchestrator.py`
- `propstore/conflict_detector/parameters.py`

---

## 1. Argumentation Frameworks Implemented

### 1a. Dung Abstract Argumentation Framework (dung.py)

A textbook-correct implementation of Dung 1995. The core data structure is `ArgumentationFramework` (line 18), a frozen dataclass holding `arguments: frozenset[str]`, `defeats: frozenset[tuple[str, str]]`, and an optional `attacks: frozenset[tuple[str, str]]`.

**Extension semantics implemented (all brute-force, O(2^n)):**
- **Grounded extension** (line 106): Iterative least-fixed-point of the characteristic function F. Returns a single frozenset.
- **Complete extensions** (line 122): Enumerates all subsets, filters to those that are admissible and are fixed points of F.
- **Preferred extensions** (line 151): Maximal complete extensions by set inclusion.
- **Stable extensions** (line 173): Conflict-free sets that defeat every outsider. Includes the correct warning that stable extensions may not exist (line 182).

**Key design distinction:** The AF carries both `attacks` (pre-preference) and `defeats` (post-preference). Conflict-free checks use `attacks` when available, defense checks use `defeats`. This correctly implements Modgil & Prakken 2018 Def 14 (see `admissible()` at line 84, `conflict_free()` at line 45).

### 1b. Z3-backed Dung Extensions (dung_z3.py)

SAT-encoded alternatives to brute-force. Each extension function uses Z3's `Solver` with solution enumeration via blocking clauses.

- **Stable extensions** (line 66): Encodes conflict-free + "every outsider is defeated" as SAT constraints. Unattacked arguments are forced in (line 96).
- **Complete extensions** (line 115): Encodes conflict-free + defense (admissibility) + fixed-point (completeness). The fixed-point encoding at line 152-172 ensures that if all attackers of `a` are counter-attacked by the set, then `a` must be in the set.
- **Preferred extensions** (line 191): Not truly CEGAR despite the comment -- it computes all complete extensions then filters to maximal. The docstring says "CEGAR approach" but the implementation is enumerate-and-filter. This is **misleading** (see Observations section).
- **Acceptance queries** (lines 211-252): `credulously_accepted` (in at least one extension) and `skeptically_accepted` (in all extensions), parameterized by semantics.

Each `dung.py` function dispatches to Z3 via `backend="z3"` parameter (e.g., `complete_extensions` at line 131).

### 1c. Bipolar Argumentation with ASPIC+ Preferences (argumentation.py)

This is the bridge layer. `build_argumentation_framework()` (line 83) constructs a bipolar AF from the stance graph:

1. Loads stances between active claims
2. Classifies into attacks (`rebuts`, `undercuts`, `undermines`, `supersedes`) and supports (`supports`, `explains`)
3. Filters attacks through preferences to get defeats (Modgil 2018 Def 9)
4. Computes **Cayrol 2005 derived defeats** from support chains (line 48):
   - **Supported defeat**: A supports B transitively, B defeats C => (A, C)
   - **Indirect defeat**: A defeats B, B supports C transitively => (A, C)
5. Returns AF with both attacks and defeats

**Attack type handling** (lines 24-28):
- Unconditional (always become defeats): `undercuts`, `supersedes`
- Preference-dependent (filtered by strength): `rebuts`, `undermines`
- Non-attack: `supports`, `explains`, `none`

`compute_justified_claims()` (line 152) is the end-to-end pipeline: build AF, compute extensions, return justified claim IDs.

### 1d. Preference Ordering (preference.py)

Implements ASPIC+ preference orderings from Modgil & Prakken 2018 Def 19:

- **Elitist** (line 28): set_a < set_b iff EXISTS x in set_a s.t. FORALL y in set_b, x < y
- **Democratic** (line 30): set_a < set_b iff FORALL x in set_a EXISTS y in set_b, x < y

`defeat_holds()` (line 37): Undercuts/supersedes always succeed. Rebuts/undermines succeed iff attacker is NOT strictly weaker.

`claim_strength()` (line 56): Computes ordinal strength from `sample_size` (log-scaled), `uncertainty` (inverse), `confidence` (direct). Missing metadata is neutral (returns 1.0 default at line 85).

### 1e. MaxSMT Conflict Resolution (maxsat_resolver.py)

Uses `z3.Optimize` with soft constraints to find the maximally consistent claim subset weighted by claim strength. Hard constraints: conflicting claims cannot both be kept (line 35). Soft constraints: prefer keeping each claim, weighted by strength (line 38). Returns the frozenset of kept claim IDs.

This is invoked by `compute_consistent_beliefs()` in `argumentation.py` (line 225) as an alternative to extension-based argumentation -- a weighted MaxSAT approach rather than Dung semantics.

---

## 2. How Conflicts Are Detected and Resolved

### 2a. Conflict Detection (conflict_detector package)

The orchestrator (`orchestrator.py` line 21) runs four specialized detectors in sequence:

1. **Parameter conflicts** (`parameters.py`): Groups claims by concept, compares values. Uses `_values_compatible()` to check if values agree. When >2 claims exist for a concept, uses Z3 equivalence-class partitioning to reduce O(n^2) pairwise comparisons.
2. **Measurement conflicts** (`measurements.py`): Groups by (target_concept, measure). Checks value compatibility. Special phi-node handling for different listener populations (line 66).
3. **Equation conflicts** (`equations.py`): Groups by equation signature (dependent concept + independent concepts). Compares canonicalized equations.
4. **Algorithm conflicts** (`algorithms.py`): Groups by concept. Uses `ast_equiv.compare()` (external library) to compare algorithm bodies with variable bindings. Non-equivalent algorithms at tier >2 are flagged.

### 2b. Conflict Classification

The `ConflictClass` enum (`models.py` line 9) defines six classes:
- `COMPATIBLE`: No conflict
- `PHI_NODE`: Different conditions, disjoint -- legitimate disagreement across contexts
- `CONFLICT`: Same conditions, different values -- true conflict
- `OVERLAP`: Overlapping but not identical conditions -- partial conflict
- `PARAM_CONFLICT`: Conflict through parameterization chain
- `CONTEXT_PHI_NODE`: Different named contexts that are hierarchically excluded

### 2c. Context-Aware Classification (context.py)

`_classify_pair_context()` (line 13) checks if two claims' contexts make them non-conflicting via a `ContextHierarchy`. If contexts are excluded or invisible to each other, the pair is classified as `CONTEXT_PHI_NODE` rather than a true conflict.

### 2d. Condition-Aware Classification

The `condition_classifier` module (imported but not in reviewed files) classifies condition pairs. When Z3 is available, `Z3ConditionSolver.are_disjoint()` determines if conditions can never hold simultaneously. The parameter detector (`parameters.py` line 49) uses `partition_equivalence_classes()` for efficient grouping when >2 claims share a concept.

### 2e. Resolution Strategies

Two resolution paths exist:
1. **Argumentation-based** (`compute_justified_claims`): Build AF from stances, compute grounded/preferred/stable extensions, return justified claims.
2. **MaxSMT-based** (`compute_consistent_beliefs`): Detect conflicts, find maximally consistent weighted subset via Z3 Optimize.

---

## 3. How Z3/SAT Solvers Are Used

### 3a. Extension Computation (dung_z3.py)

Z3 `Solver` used for SAT-based enumeration of Dung extensions. Solution enumeration via blocking clauses (`_block_solution()` at line 48). One Boolean variable per argument. Scales better than brute-force for large AFs.

### 3b. Condition Disjointness/Equivalence (z3_conditions.py)

`Z3ConditionSolver` translates CEL condition expressions to Z3:
- `z3.Real` for quantity concepts
- `z3.EnumSort` for category concepts (finite domain)
- `z3.Bool` for boolean concepts
- `z3.String` for unknown concepts in equality comparisons

Key operations:
- `are_disjoint()` (line 287): Conjunction of two condition sets is UNSAT
- `are_equivalent()` (line 300): Both A^~B and B^~A are UNSAT
- `partition_equivalence_classes()` (line 324): O(n*k) partitioning vs O(n^2) pairwise

Aggressive caching: AST cache, expression cache, condition-set cache (lines 45-47).

### 3c. MaxSMT Resolution (maxsat_resolver.py)

`z3.Optimize` with weighted soft constraints. Each claim gets a soft constraint to be kept, weighted by `claim_strength`. Hard constraints forbid keeping both members of a conflict pair.

### 3d. CEL-to-Z3 Translation Pipeline

```
CEL string -> tokenize (cel_checker.py) -> parse (cel_checker.py) -> AST
    -> Z3ConditionSolver._translate (z3_conditions.py) -> Z3 expression
    -> Solver.check() -> sat/unsat
```

The CEL parser (cel_checker.py) is a hand-rolled recursive descent parser supporting: comparisons, arithmetic, `&&`, `||`, `!`, `in [list]`, ternary `?:`. It is NOT a full CEL implementation -- it covers the subset needed for condition expressions.

### 3e. SymPy for Equation Reasoning (propagation.py, sensitivity.py)

SymPy (not Z3) is used for:
- Evaluating parameterization expressions (`propagation.py`)
- Computing partial derivatives and elasticities (`sensitivity.py`)
- Solving `Eq(y, expr)` forms for output variables

`_parse_cached()` in propagation.py (line 14) uses `functools.lru_cache` for parsed expressions.

---

## 4. Code Quality Observations

### 4a. Positive Observations

- **Literature grounding is excellent.** Every module cites specific papers and definition numbers. The Dung implementation references Dung 1995 Definitions 6, 8, 10, 12, 17, 20, 25. The preference module references Modgil & Prakken 2018 Definitions 9, 19. Cayrol 2005 Definition 3 is cited for derived defeats. This is rare and valuable.

- **Clean separation of concerns.** The AF construction (argumentation.py) is cleanly separated from AF computation (dung.py), Z3 encoding (dung_z3.py), and preference ordering (preference.py). Each file has a single responsibility.

- **Conservative defaults in Z3 translation.** `are_disjoint()` returns `False` on translation errors (line 293 of z3_conditions.py) -- assumes not disjoint. `are_equivalent()` returns `False` on errors (line 309). This is the correct conservative behavior: when the solver can't determine, assume potential conflict.

- **The conflict detector is well-factored.** Four specialized detectors (parameters, measurements, equations, algorithms) share common infrastructure (collectors, context classification) through a clean orchestrator pattern.

- **Frozen dataclasses for immutability.** `ArgumentationFramework` is frozen (line 18 of dung.py), preventing accidental mutation.

- **The CEL parser is competent.** Correct operator precedence (ternary < or < and < comparison < additive < multiplicative < unary < primary). Handles both single and double-quoted strings. Proper escape handling in regex patterns.

### 4b. Issues and Concerns

**MISLEADING DOCSTRING (dung_z3.py line 188):** The comment says "CEGAR approach" for preferred extensions, but the implementation at line 200-205 simply computes all complete extensions and filters to maximal. True CEGAR (Counter-Example Guided Abstraction Refinement) would use incremental SAT solving with counterexample-driven constraint addition. This is enumerate-and-filter, not CEGAR.

**BRUTE-FORCE COMPLEXITY (dung.py lines 140-148):** `complete_extensions()` enumerates all 2^n subsets. For n arguments, this is exponential. The Z3 backend mitigates this but is opt-in. There is no warning or automatic fallback for large AFs in the brute-force path.

**CLAIM STRENGTH COMPOSITION (preference.py lines 56-87):** The `claim_strength()` function sums heterogeneous signals: `log1p(sample_size)` + `1/uncertainty` + `confidence`. These have wildly different scales. A claim with sample_size=1000 gets log1p(1000)=6.91, while confidence=0.9 contributes 0.9. The sum is not normalized. A claim with only uncertainty=0.01 gets strength 100.0, which dominates everything. The `components` counter is computed but never used for averaging -- this looks like an abandoned normalization attempt.

**DUPLICATE Z3 SOLVER CONSTRUCTION (parameters.py line 24 vs orchestrator.py line 69):** `parameters.py` has `_build_z3_solver()` at line 24, and `orchestrator.py` has `_build_condition_solver()` at line 69. Both do the same thing. The orchestrator passes its solver to `detect_parameter_conflicts()` via the `solver` kwarg, but `parameters.py` falls back to building its own if `solver is None` (line 41). This redundancy is harmless but suggests evolution without cleanup.

**BROAD EXCEPTION CATCHING (conflict_detector/algorithms.py line 47, parameters.py line 52, z3_conditions.py line 351):** Multiple places catch bare `Exception`. In `algorithms.py` line 47, `ast_compare` failures are silently swallowed. In `parameters.py` line 52, `partition_equivalence_classes` failure silently falls back to pairwise. In `z3_conditions.py` line 351, equivalence check failure silently skips a match. These should at minimum log warnings.

**SENSITIVITY ANALYSIS ACCESSES PRIVATE METHODS (sensitivity.py lines 60, 67):** `analyze_sensitivity()` calls `world._parameterizations_for()` and `bound._is_param_compatible()` -- both private. This creates a fragile coupling to implementation details of WorldModel and BoundWorld.

**PROPAGATION IMPORTS FROM SENSITIVITY (sensitivity.py line 14):** `from propstore.propagation import _parse_cached` -- importing a private function across modules. If propagation changes its caching strategy, sensitivity breaks silently.

**NO INPUT VALIDATION ON CLAIM IDS (argumentation.py):** `build_argumentation_framework()` passes `active_claim_ids` directly through. If an ID is in the set but not in the store, `claims_by_id.get(source_id, {})` returns an empty dict and `claim_strength({})` returns 1.0 (neutral). This means missing claims silently get neutral strength rather than raising an error.

**EMPTY EXTENSION EDGE CASE (dung_z3.py lines 74, 123):** Both `z3_stable_extensions` and `z3_complete_extensions` special-case empty frameworks, returning `[frozenset()]`. The brute-force versions in dung.py do not have this special case -- they fall through to the loop which happens to produce the correct result but via a different code path. Behavior is equivalent but the asymmetry could confuse readers.

### 4c. Type Annotation Quality

Generally good. The codebase uses `from __future__ import annotations` consistently. `frozenset[str]` and `frozenset[tuple[str, str]]` are used throughout. The `TYPE_CHECKING` guard pattern is used correctly in the conflict detector to avoid circular imports.

One inconsistency: `z3_conditions.py` uses `Any` return type on `_translate()` and related methods (line 88). This is understandable since Z3 expression types are hard to annotate, but it means the type checker provides no help inside the translation layer.

---

## 5. Novel or Surprising Aspects

### 5a. Bipolar AF with Cayrol Derived Defeats

The `_cayrol_derived_defeats()` function in `argumentation.py` (line 48) implements Cayrol 2005's bipolar argumentation theory. This is uncommon in practice. Most AF implementations only handle attacks. The transitive support propagation (`_transitive_support_targets` at line 31) and the two derived defeat types (supported defeat, indirect defeat) are correctly implemented per Definition 3.

### 5b. Dual Resolution Strategy

The system offers two fundamentally different resolution approaches:
1. **Argumentation semantics** (Dung extensions via `compute_justified_claims`) -- produces extensions, respects defeat structure
2. **Weighted MaxSAT** (via `compute_consistent_beliefs`) -- finds maximum-weight conflict-free subset

These serve different purposes. The argumentation approach preserves the semantics of attack/defense relationships. The MaxSAT approach is purely optimization-based. Having both available at render time is architecturally principled -- different resolution policies for different use cases.

### 5c. Z3 for Condition Equivalence Partitioning

Using Z3 to partition condition sets into equivalence classes (`z3_conditions.py` line 324) is clever. Rather than O(n^2) pairwise checking, it achieves O(n*k) by comparing each new condition set only against class representatives. This optimization is triggered for parameter claims with >2 entries per concept (`parameters.py` line 49).

### 5d. The attacks/defeats Distinction in the AF Dataclass

The `ArgumentationFramework` dataclass carries both `attacks` (pre-preference) and `defeats` (post-preference). This is a direct implementation of Modgil & Prakken 2018's distinction between attacks and defeats. Most Dung AF implementations only carry one relation. Having both allows conflict-free checking against attacks while defense checking uses defeats -- which is the theoretically correct behavior per ASPIC+.

### 5e. CEL as Condition Language with Z3 Backend

Using a CEL (Common Expression Language) subset as the condition language, with a hand-rolled parser that feeds into Z3 for satisfiability checking, is an unusual but effective architecture. The CEL parser in `cel_checker.py` doubles as both a type-checker (against the concept registry's kind system) and a frontend for Z3 translation. The type system distinguishes QUANTITY (z3.Real), CATEGORY (z3.EnumSort), BOOLEAN (z3.Bool), and STRUCTURAL (rejected) kinds.

### 5f. Phi-Node Classification

The conflict detector's `PHI_NODE` class (models.py line 11) and `CONTEXT_PHI_NODE` (line 15) borrow terminology from SSA (Static Single Assignment) form in compilers. A phi-node in SSA merges values from different control flow paths. Here, a PHI_NODE represents claims that disagree but under provably disjoint conditions -- they are the propstore equivalent of different branches of a phi node. This is a meaningful metaphor: the system holds both values without committing, and the render layer selects based on which condition holds.

### 5g. Algorithm Conflict Detection via AST Equivalence

The algorithm conflict detector (`algorithms.py`) uses an external `ast_equiv` library to compare algorithm bodies with variable-to-concept bindings. This is comparing algorithms structurally (modulo variable renaming via concept bindings) rather than textually. The tiered equivalence system (`result.tier <= 2` at line 49) suggests multiple levels of structural similarity.

---

## Summary

The argumentation subsystem is a serious, literature-grounded implementation of formal argumentation theory. It correctly implements Dung 1995 (AF, four extension semantics), Modgil & Prakken 2018 (ASPIC+ preferences, attacks/defeats distinction), and Cayrol 2005 (bipolar derived defeats). Z3 is used in three distinct roles: SAT-based extension computation, condition satisfiability/equivalence checking, and weighted MaxSAT conflict resolution. SymPy handles symbolic equation reasoning separately.

The main risks are: the brute-force paths are exponential with no guard rails, the claim strength composition mixes incompatible scales, the "CEGAR" label is misleading, and several places silently swallow exceptions. The main strengths are: thorough literature grounding, clean separation of concerns, conservative defaults on solver failures, and the novel phi-node metaphor for holding disagreement without commitment.
