# Argumentation & Render Layer Deep Dive -- Scout Report

**Date:** 2026-03-23
**Role:** Scout (Gauntlet protocol -- explore and report, do not implement)

---

## Executive Summary

The argumentation and render layers of propstore constitute a remarkably complete implementation of formal argumentation theory applied to scientific claim resolution. The system implements Dung's abstract argumentation framework with all four standard extension semantics, ASPIC+ preference ordering with Modgil & Prakken's attack/defeat distinction, Cayrol's bipolar argumentation with derived defeats from support chains, Z3-backed SAT solving for scalable extension computation, a custom CEL parser and type-checker with Z3 translation for condition reasoning, and a layered render architecture that separates storage truth from rendered belief spaces.

This is not a toy or partial implementation. Every major component has been built, tested with both concrete examples and Hypothesis property tests grounded in the formal literature, and integrated into a coherent end-to-end pipeline.

---

## 1. Argumentation Frameworks -- Dung AF Construction and Extensions

### What Is Implemented

**File:** `propstore/dung.py` (lines 1-202)

A complete implementation of Dung 1995's abstract argumentation framework. The core data structure is:

```python
@dataclass(frozen=True)
class ArgumentationFramework:
    arguments: frozenset[str]
    defeats: frozenset[tuple[str, str]]
    attacks: frozenset[tuple[str, str]] | None = None
```

The `attacks` field (line 37) is a notable extension beyond standard Dung: it stores the pre-preference attack relation, separate from the post-preference defeat relation. This is required by Modgil & Prakken 2018 Def 14 -- conflict-free is checked against attacks, while defense is checked against defeats.

**All four standard extension semantics are implemented:**

- **Grounded extension** (lines 106-119): Iterates the characteristic function F(S) = {A | A is defended by S} from the empty set to a fixed point. This is the unique, skeptical, polynomial-time extension.
- **Complete extensions** (lines 122-148): Enumerates all fixed points of F that are admissible. Brute-force over all subsets.
- **Preferred extensions** (lines 151-170): Maximal complete extensions (by set inclusion).
- **Stable extensions** (lines 173-201): Conflict-free sets that defeat every outsider. WARNING comment at line 182 correctly notes these may not exist.

**Key design detail at lines 45-56:** The `conflict_free()` function takes a generic relation parameter rather than being hardcoded to defeats. This allows the caller to pass either `attacks` or `defeats`, implementing the Modgil & Prakken distinction where conflict-free uses attacks (pre-preference) but defense uses defeats (post-preference). The `admissible()` function at lines 84-103 correctly dispatches: CF against attacks (when available), defense against defeats.

**Backend dispatch:** Each extension function accepts `backend="z3"` (e.g., line 131) to route to the Z3-backed solver in `dung_z3.py`.

### What Is Tested

**File:** `tests/test_dung.py` (388 lines)

Comprehensive test suite with:
- Concrete regression tests from Dung 1995: empty framework, unattacked wins, Nixon diamond, reinstatement, odd cycle, self-attacker, floating defeat, chain of four, no attacks (lines 68-116)
- Concrete preferred extension tests: Nixon diamond (two extensions), reinstatement, self-attacker (lines 118-148)
- Concrete stable extension tests: Nixon diamond, odd cycle (no stable), self-attacker (no stable) (lines 151-181)
- Concrete complete extension tests: Nixon diamond (three complete) (lines 184-199)
- Helper function unit tests: attackers_of, conflict_free, defends, characteristic_fn, admissible (lines 201-243)

**Property tests (Hypothesis) verifying formal theorems from Dung 1995:**
- P1: Grounded extension is conflict-free (line 257)
- P2: Grounded extension is admissible (line 263)
- P3: Grounded is subset of every preferred extension (Thm 25, line 278)
- P4: Every preferred extension is admissible (line 298)
- P5/P9: Every preferred is complete (line 324)
- P5: Every stable is preferred (Thm 13, line 337)
- P6: Stable = CF + defeats all outsiders (Def 12, line 347)
- P7: Grounded is fixed point of F (Thm 25, line 270)
- P8: Complete extensions are fixed points of F (line 360)
- P10: Empty defeat set means grounded = all args (line 286)
- P11: F is monotone (Fundamental Lemma, line 380)
- P12: Preferred extensions are maximal admissible (line 304)

This is an unusually rigorous test suite -- it directly encodes formal theorems as executable property tests.

---

## 2. Z3-Backed Dung Solver

### What Is Implemented

**File:** `propstore/dung_z3.py` (lines 1-253)

A SAT-encoded alternative to brute-force extension computation. Creates one Boolean variable per argument and encodes:

- **Conflict-free constraints** (lines 27-37): `Not(And(v[a], v[b]))` for each attack pair. Uses attacks (pre-preference) when available, per Modgil & Prakken 2018 Def 14.
- **Stable extensions** (lines 66-109): CF constraints plus "every outsider must be attacked by some member" -- encoded as `Or(v[a], Or(*[v[b] for b in attackers]))`.
- **Complete extensions** (lines 115-185): CF + defense (admissibility) + fixed-point (completeness). The fixed-point encoding at lines 148-172 is notable: "if a is defended by S, then a must be in S" prevents extensions from being too small.
- **Preferred extensions** (lines 191-205): Computed by filtering maximal complete extensions (enumerate-and-filter approach).
- **Acceptance queries** (lines 210-252): `credulously_accepted()` (in at least one extension) and `skeptically_accepted()` (in all extensions), dispatching to the appropriate extension function.

Solution enumeration uses blocking clauses (lines 48-60): after finding an extension, add a clause excluding that exact assignment, then re-solve.

### What Is Tested

**File:** `tests/test_dung_z3.py`

Property tests verify that Z3 results are identical to brute-force for all extension semantics. Concrete tests mirror the brute-force suite.

---

## 3. ASPIC+ Preference Ordering

### What Is Implemented

**File:** `propstore/preference.py` (lines 1-88)

Implements Modgil & Prakken 2018 Def 9 (defeat) and Def 19 (set comparisons).

**Set comparison** (lines 16-34 -- `strictly_weaker()`):
- **Elitist** (line 28): `set_a < set_b iff EXISTS x in set_a s.t. FORALL y in set_b, x < y` -- "one bad apple spoils the barrel"
- **Democratic** (line 30): `set_a < set_b iff FORALL x in set_a EXISTS y in set_b, x < y` -- "every element must be beaten"

**Defeat determination** (lines 37-53 -- `defeat_holds()`):
- Undercuts/supersedes: always succeed (preference-independent)
- Rebuts/undermines: succeed iff attacker is NOT strictly weaker

**Claim strength computation** (lines 56-87 -- `claim_strength()`):
- Composites three signals: `sample_size` (log-scaled via `math.log1p`), `uncertainty` (inverse), `confidence` (direct)
- Missing metadata contributes 0 (neutral), not a penalty (line 84)
- Default for claims with no metadata: 1.0 (line 85)

### What Is Not Yet Implemented

The `aspic.md` design document (the original implementation spec) describes both **last-link** and **weakest-link** preference principles (Def 20 and 21 from Modgil & Prakken 2018). The current `preference.py` implements a unified `claim_strength()` that effectively does last-link (comparing by the immediate claim metadata). Weakest-link (comparing by the weakest component in a derivation chain) is not yet implemented. The design doc explicitly notes at line 976: "The preference ordering is the hard part."

---

## 4. Bipolar Argumentation -- Cayrol 2005

### What Is Implemented

**File:** `propstore/argumentation.py` (lines 31-80)

Cayrol's bipolar argumentation framework extends Dung AF with support relations. The implementation computes two types of derived defeats per Cayrol 2005 Definition 3:

- **Supported defeat** (lines 69-72): If A supports* B (transitively) and B defeats C, then (A, C) is a derived defeat. "I support the argument that defeats you, so I'm also against you."
- **Indirect defeat** (lines 74-79): If A defeats B and B supports* C (transitively), then (A, C) is a derived defeat. "I defeated your supporter, so you lose your backing."

Transitive support chains are computed via `_transitive_support_targets()` (lines 31-45) with cycle detection (`visited` set).

The `build_argumentation_framework()` function (lines 83-149) integrates this:
1. Loads stances between active claims
2. Classifies into attacks (rebuts/undercuts/undermines/supersedes) and supports (supports/explains)
3. Filters attacks through preferences to get defeats
4. Computes Cayrol derived defeats from support chains
5. Returns AF with both attacks (pre-preference) and defeats (post-preference + derived)

**Support types** (line 27): Both `supports` and `explains` are treated as support relations for Cayrol purposes. This is a design choice -- `explains` is treated as a form of evidential support.

### What Is Tested

**File:** `tests/test_bipolar_argumentation.py` (444 lines)

Three test classes covering:

1. **TestCayrolDerivedDefeats** (lines 68-148): Direct unit tests of the derived defeat algorithm. Tests supported defeat, indirect defeat, chain variants, both directions, no-spurious-derivation, and self-support-loop termination.

2. **TestBipolarAFConstruction** (lines 154-253): Integration tests with SQLite backing. Tests supported defeat via DB, indirect defeat via DB, direct defeats unchanged, supports not in attacks, attacks set is pre-preference (blocked attacks still appear), mixed chains, and `explains` treated as support.

3. **TestAttackBasedConflictFree** (lines 259-368): Tests the Modgil & Prakken 2018 Def 14 distinction where CF uses attacks (not defeats). Demonstrates that attack-based CF is stricter than defeat-based CF. Tests `admissible()` with attacks parameter, complete/stable extensions respecting attack-based CF, and that grounded extension (which uses characteristic function on defeats) is unchanged by the attacks field.

4. **TestBipolarExtensions** (lines 373-443): Extension-level tests showing how support-derived defeats change the grounded extension outcome.

---

## 5. The Render/Resolution Layer

### Architecture

The render layer implements a clean separation: `Repository artifacts + Environment + RenderPolicy => BeliefSpace`.

**Key types** defined in `propstore/world/types.py`:

- `ResolutionStrategy` (line 31): Enum with `RECENCY`, `SAMPLE_SIZE`, `ARGUMENTATION`, `OVERRIDE`
- `RenderPolicy` (lines 80-87): Frozen dataclass holding strategy, semantics, comparison, confidence_threshold, overrides, and per-concept strategies
- `Environment` (lines 49-53): Frozen dataclass with bindings, context_id, effective_assumptions
- `ValueResult` (lines 15-18): Status is `determined | conflicted | underdetermined | no_claims`
- `ResolvedResult` (lines 39-46): Adds `winning_claim_id`, `strategy`, `reason` for explainability
- `ArtifactStore` (lines 90-128): Protocol defining the storage boundary -- 20+ methods for claims, concepts, stances, parameterizations, embeddings, condition solving
- `BeliefSpace` (lines 131-146): Protocol defining the rendered view -- active/inactive claims, value_of, derived_value, resolved_value, is_determined, conflicts, explain

### Resolution Strategies

**File:** `propstore/world/resolution.py` (lines 1-203)

Four resolution strategies for conflicted concepts:

1. **RECENCY** (lines 16-34): Picks the claim with the most recent date in provenance_json.
2. **SAMPLE_SIZE** (lines 37-48): Picks the claim with the largest sample_size.
3. **ARGUMENTATION** (lines 51-93): The formal path. Builds a Dung AF from the stance graph filtered through preferences, computes extensions under chosen semantics, and picks the sole survivor (if any). For preferred/stable, takes the intersection across all extensions (skeptical acceptance).
4. **OVERRIDE** (lines 156-169): Explicit user-specified winner, with validation that the override claim is actually active.

The `resolve()` function (lines 96-203) is the main dispatch. It:
- Returns early for `no_claims` or `determined` status
- Reads strategy from `RenderPolicy`, including per-concept strategy overrides (line 128)
- Provides full `ResolvedResult` with winning claim, strategy used, and human-readable reason

### BoundWorld -- The Belief Space

**File:** `propstore/world/bound.py` (lines 1-312)

`BoundWorld` implements `BeliefSpace`. It represents the world under specific condition bindings and optional context scoping.

**Claim activation** (lines 159-180 -- `is_active()`):
1. Context membership check -- if a context is bound, only claims in that context or its ancestors are visible. Claims with no context (NULL) are always visible.
2. CEL condition check -- uses Z3 disjointness testing. A claim is active unless its conditions are provably disjoint from the current bindings. Conservative: if Z3 can't determine, the claim stays active.

**Value resolution chain** in `value_of()` (line 256): Delegates to `ActiveClaimResolver.value_of_from_active()`, which handles three cases:
- Value claims only: determined if all agree, conflicted if they disagree
- Algorithm claims only: determined if one, or if all are semantically equivalent (checked via `ast_compare`)
- Mixed: considers value claims only

**Derived values** (line 260): Via parameterization relationships -- finds compatible parameterization, resolves inputs from other concepts, evaluates SymPy expressions.

**Conflict recomputation** (lines 280-301): Does NOT just use stored conflicts. Re-runs conflict detection against currently active claims, merging with stored conflicts.

### HypotheticalWorld -- Counterfactual Reasoning

**File:** `propstore/world/hypothetical.py` (lines 1-167)

An in-memory overlay on BoundWorld that removes/adds claims without mutation. Key capabilities:
- Remove claims by ID (line 25)
- Add synthetic claims (line 26)
- `diff()` (lines 145-161): Compare base vs hypothetical for all affected concepts
- `recompute_conflicts()` (lines 111-143): Check for value disagreements among active claims

This enables "what if" reasoning -- what would the world look like if we removed claim X and added claim Y?

### Chain Queries

**File:** `propstore/world/model.py` (lines 450-533 -- `chain_query()`)

Traverses the parameter space to derive a target concept. Iteratively resolves values for all concepts in a parameterization group, using bindings, claim values, resolution (for conflicted), and derivation until no more progress can be made.

---

## 6. Z3 Condition Reasoning

### What Is Implemented

**File:** `propstore/z3_conditions.py` (lines 1-359)

`Z3ConditionSolver` translates CEL condition ASTs into Z3 expressions. The type mapping is:
- Quantity concepts -> `z3.Real`
- Boolean concepts -> `z3.Bool`
- Category concepts -> `z3.EnumSort` with known values
- Unknown concepts -> `z3.Real` (most permissive fallback, line 122)

Three key operations:
1. **`are_disjoint()`** (lines 288-299): Checks if the conjunction of two condition sets is UNSAT. Used by BoundWorld to determine if a claim's conditions are incompatible with current bindings.
2. **`are_equivalent()`** (lines 301-323): Checks if A=>B and B=>A. Both `A AND NOT B` and `B AND NOT A` must be UNSAT.
3. **`partition_equivalence_classes()`** (lines 325-359): Groups condition sets by logical equivalence. O(n*k) where k is the number of distinct classes.

Extensive caching at three levels: AST cache, expression cache, condition-set cache (lines 46-48).

Conservative fallback: if Z3 translation fails, returns `False` for disjointness and `False` for equivalence (never makes wrong claims about semantic relationships).

---

## 7. CEL Parser and Type Checker

### What Is Implemented

**File:** `propstore/cel_checker.py` (lines 1-605)

A complete hand-rolled implementation:

**Tokenizer** (lines 102-187): Regex-based, handles: names, int/float/string/bool literals, operators (arithmetic, comparison, logical), brackets, `in`, ternary `?:`.

**Parser** (lines 190-360): Recursive descent with correct precedence: ternary > or > and > comparison/in > additive > multiplicative > unary > primary. Produces an AST with node types: `NameNode`, `LiteralNode`, `BinaryOpNode`, `UnaryOpNode`, `InNode`, `TernaryNode`.

**Type Checker** (lines 362-605): Resolves types of AST nodes against a concept registry:
- `QUANTITY` concepts resolve to `NUMERIC`
- `CATEGORY` concepts resolve to `STRING`
- `BOOLEAN` concepts resolve to `BOOLEAN`
- `STRUCTURAL` concepts are forbidden in CEL expressions (line 421)
- Category value set validation with extensible flag (warnings vs errors)
- Type mismatch detection: quantity compared to string, category in arithmetic, etc.

### What Is Innovative

The CEL subset is deliberately minimal -- "sufficient for the condition expressions used in concept relationships and parameterization relationships" (line 6). This is a pragmatic engineering choice: a full CEL implementation would be massive, but the actual condition language used in propstore is simple comparisons, arithmetic, and membership tests. The parser handles exactly what's needed.

---

## 8. MaxSAT Conflict Resolution

### What Is Implemented

**File:** `propstore/maxsat_resolver.py` (lines 1-48)

An alternative to Dung AF resolution using Z3's Optimize (MaxSMT). Creates one Boolean variable per claim, adds hard constraints (conflicting claims can't coexist), and soft constraints weighted by `claim_strength()`. Finds the maximally consistent subset.

This is invoked via `argumentation.py`'s `compute_consistent_beliefs()` (lines 225-278), which:
1. Loads claims and computes strengths
2. Detects conflicts via the conflict detector
3. Extracts conflict pairs (CONFLICT, OVERLAP, PARAM_CONFLICT types)
4. Calls `resolve_conflicts()` to find the optimal subset

### Relationship to Argumentation

MaxSAT resolution and Dung AF resolution are complementary approaches:
- **Dung AF** works from explicit attack/defeat relations (stances) and computes semantically grounded extensions
- **MaxSAT** works from detected value conflicts and finds the maximum-weight consistent subset

The system offers both. Dung AF is the more principled path (grounded in argumentation theory), while MaxSAT is a practical fallback when stance information is sparse.

---

## 9. Conflict Detection Subsystem

### What Is Implemented

**Directory:** `propstore/conflict_detector/` (8 files)

**`models.py`** defines `ConflictClass`: COMPATIBLE, PHI_NODE, CONFLICT, OVERLAP, PARAM_CONFLICT, CONTEXT_PHI_NODE.

**`orchestrator.py`** runs four parallel conflict detection paths:
1. Parameter conflicts (claims with same concept, different values)
2. Measurement conflicts
3. Equation conflicts
4. Algorithm conflicts

Plus transitive conflicts via parameterization chains.

**`propstore/condition_classifier.py`** (333 lines) classifies condition pairs using two paths:
1. **Z3 primary path** (lines 66-91): Uses `are_equivalent()` for CONFLICT, `are_disjoint()` for PHI_NODE, else OVERLAP.
2. **Interval arithmetic fallback** (lines 127-141): When Z3 is unavailable. Parses conditions into numeric/discrete constraints and checks intersection.

The fallback is conservative: when conditions can't be parsed, returns OVERLAP (line 141).

---

## 10. Sensitivity Analysis

### What Is Implemented

**File:** `propstore/sensitivity.py` (lines 1-165)

Computes "which input most influences this output?" for derived quantities:
- Symbolic partial derivatives via SymPy
- Numerical evaluation at current input values
- **Elasticity** (normalized sensitivity): `(df/dx * x/f)` -- a dimensionless measure of proportional influence
- Results sorted by |elasticity| descending

Integrates with the world model: resolves inputs from BoundWorld, finds compatible parameterizations via condition matching.

---

## 11. Belief Revision and ATMS

### Current Status

Full ATMS (Assumption-based Truth Maintenance System) is **not yet implemented** but is explicitly planned as the next major architectural direction.

**What exists now** (as documented in `plans/semantic-foundations-and-atms-plan.md` and `plans/semantic-contract.md`):

1. **Environment model** with context_id, effective_assumptions, and bindings (`propstore/world/types.py` lines 49-53). The `effective_assumptions` field (a tuple of CEL strings) is explicitly designed as a stepping stone toward ATMS assumption sets.

2. **Context hierarchy** with inheritance, assumptions, and exclusions (`propstore/world/model.py` lines 108-165). Contexts are loaded from sidecar tables and compiled into effective assumption sets.

3. **Context-aware conflict classification** -- claims in unrelated contexts are classified as CONTEXT_PHI_NODE rather than CONFLICT (`propstore/condition_classifier.py` and `propstore/conflict_detector/context.py`).

4. **Non-destructive reasoning** -- HypotheticalWorld creates overlay views without mutating source data, consistent with ATMS's non-destructive belief revision principle.

### What Is Planned

From the semantic foundations plan (`plans/semantic-foundations-and-atms-plan.md` lines 807-850), an R6 ATMS Readiness Pass was completed. The plan envisions:
- Assumption atoms
- Justification representation
- Labels (minimal assumption sets per datum)
- Nogoods
- Minimality maintenance
- Revision policy

The plan explicitly warns against "Fake ATMS terminology" (line 1014): "Do not rename context filters to 'environments' and declare victory."

Current decision (binding decision B4 in semantic-contract.md, line 530): "this phase implements environment-correct semantics only. It does not implement first-class label storage or nogood maintenance."

---

## 12. Architectural Innovation

### The Render-Time Non-Commitment Discipline

The most innovative aspect of this system is not any single algorithm but the architectural principle that **resolution is always deferred to render time**. From `plans/render-layer-architecture-plan.md` line 97: "A rendered answer is always 'under policy P and environment E', never 'the repository now believes X'."

This means:
- The same repository can produce different answers under different RenderPolicies
- Different semantics (grounded vs preferred) can be compared without re-computing the base data
- Argumentation, recency, sample_size, and override strategies are interchangeable
- Per-concept strategy overrides allow mixed resolution approaches
- Confidence thresholds for stance inclusion are render-time parameters, not build-time decisions
- The `stance_summary()` function provides explainability metadata alongside every resolution

### The Attack/Defeat Separation

The system correctly implements the subtle but critical distinction from Modgil & Prakken 2018: attacks are pre-preference, defeats are post-preference, and conflict-free is checked against attacks (not defeats). This is an easy detail to get wrong, and the codebase handles it correctly throughout, including in the Z3 encoding.

### The Dual Resolver Architecture

Having both Dung AF (argumentation-theoretic) and MaxSAT (optimization-theoretic) resolution paths is unusual. It means the system can function with or without explicit stance information:
- When stances exist: use formal argumentation
- When only value conflicts exist: use MaxSAT weighted optimization
- Users can choose which path best fits their use case

### Literature Fidelity

Every module cites specific definitions and theorems. The property tests encode formal theorems as executable specifications. This level of literature grounding in a practical system is rare.

---

## 13. Gaps and Observations

### Implemented but Possibly Unused

- `compute_consistent_beliefs()` in `argumentation.py` (lines 225-278): This MaxSAT path is wired up but there is no resolution strategy in `ResolutionStrategy` that invokes it. It exists as an alternative to the Dung AF path but has no direct entry point through `resolve()`. It may be accessible only through direct API calls.

### Not Yet Implemented from Design Doc

- **Last-link vs weakest-link preference principles**: The `aspic.md` design doc specifies both (Def 20 and 21 from Modgil & Prakken 2018). Current implementation uses a unified `claim_strength()` that is closest to last-link. Weakest-link (considering the weakest component in a derivation chain) is absent.

- **Defeat table in sidecar**: The `aspic.md` design doc proposed caching the defeat relation in a `defeat` table. This was explicitly rejected -- `test_render_time_filtering.py` line 142 has a test `test_build_schema_has_no_defeat_table` asserting the defeat table does NOT exist. The design decision was to compute defeats at render time rather than build time, consistent with the non-commitment discipline.

- **Full ATMS**: Labels, nogoods, minimality maintenance are planned but not implemented.

### Brute-Force Scalability

The brute-force extension computation in `dung.py` is O(2^n) in the number of arguments. The Z3 backend provides a practical alternative, but the preferred_extensions Z3 path (lines 191-205 of `dung_z3.py`) still enumerates all complete extensions first, then filters. For very large AFs, a direct Z3 encoding of maximality would be more efficient.

### Conservative Fallbacks

The system consistently chooses conservative fallbacks when Z3 or CEL parsing fails:
- `z3_conditions.py` line 294: translation failure => assume not disjoint
- `z3_conditions.py` line 310: translation failure => assume not equivalent
- `condition_classifier.py` line 141: unparseable conditions => OVERLAP (not CONFLICT)

This is the correct design choice for a system that must "never collapse disagreement in storage."

---

## 14. File Index

### Core Argumentation
- `propstore/dung.py` -- Dung AF, all four extension semantics
- `propstore/dung_z3.py` -- Z3 SAT-encoded Dung solver
- `propstore/preference.py` -- ASPIC+ preference ordering
- `propstore/argumentation.py` -- Stance-to-AF bridge, Cayrol bipolar, MaxSMT path
- `propstore/maxsat_resolver.py` -- Z3 Optimize weighted resolution

### Render Layer
- `propstore/world/types.py` -- ArtifactStore, BeliefSpace, RenderPolicy, Environment, ValueResult, ResolvedResult
- `propstore/world/model.py` -- WorldModel (ArtifactStore impl), chain queries
- `propstore/world/bound.py` -- BoundWorld (BeliefSpace impl), condition-based activation
- `propstore/world/resolution.py` -- Resolution strategy dispatch (recency, sample_size, argumentation, override)
- `propstore/world/hypothetical.py` -- HypotheticalWorld, counterfactual reasoning, diff
- `propstore/world/value_resolver.py` -- ActiveClaimResolver, algorithm equivalence checking

### Condition Reasoning
- `propstore/cel_checker.py` -- CEL tokenizer, parser, type checker
- `propstore/z3_conditions.py` -- CEL-to-Z3 translation, disjointness/equivalence
- `propstore/condition_classifier.py` -- Z3 + interval arithmetic condition classification

### Conflict Detection
- `propstore/conflict_detector/` -- Orchestrated conflict detection (parameters, measurements, equations, algorithms)

### Analysis
- `propstore/sensitivity.py` -- SymPy-based sensitivity analysis with elasticity
- `propstore/propagation.py` -- SymPy parameterization evaluation

### Stance Vocabulary
- `propstore/stances.py` -- Stance type constants

### Tests
- `tests/test_dung.py` -- Property tests encoding Dung 1995 theorems
- `tests/test_dung_z3.py` -- Z3 solver equivalence tests
- `tests/test_preference.py` -- Preference ordering tests
- `tests/test_argumentation_integration.py` -- End-to-end AF pipeline with Hypothesis
- `tests/test_bipolar_argumentation.py` -- Cayrol derived defeats, attack-based CF
- `tests/test_render_contracts.py` -- RenderPolicy, Environment shape tests
- `tests/test_render_time_filtering.py` -- Confidence threshold, stance summary, no defeat table
- `tests/test_world_model.py` -- WorldModel and BoundWorld integration
- `tests/test_maxsat_resolver.py` -- MaxSAT resolution tests
- `tests/test_z3_conditions.py` -- Z3 condition solver tests
- `tests/test_cel_checker.py` -- CEL parser and type checker tests
- `tests/test_sensitivity.py` -- Sensitivity analysis tests
- `tests/test_condition_classifier.py` -- Condition classification tests
- `tests/test_conflict_detector.py` -- Conflict detection tests
- `tests/sqlite_argumentation_store.py` -- Test helper implementing ArtifactStore protocol

### Design Documents
- `aspic.md` -- Original ASPIC+ implementation specification
- `plans/render-layer-architecture-plan.md` -- Render layer refactoring plan (R0-R5, all completed)
- `plans/semantic-foundations-and-atms-plan.md` -- Semantic foundations plan (R0-R6, all completed)
- `plans/semantic-contract.md` -- Semantic contract for the current phase
- `plans/semantic-foundations-status.md` -- Implementation status tracking
