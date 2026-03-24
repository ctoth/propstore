# Honesty Audit: Run 2B Design

## GOAL
Attack the Run 2B design from the standpoint of semantic dishonesty and accidental overclaiming. Focus on boundary between exact labelled support, semantic compatibility via Z3, context visibility, and ASPIC+ naming.

## FILES READ
- `propstore/world/labelled.py` — ATMS-style label kernel (AssumptionRef, EnvironmentKey, Label, NogoodSet, JustificationRecord)
- `propstore/world/types.py` — ValueResult, DerivedResult, ResolvedResult, RenderPolicy, BeliefSpace protocol
- `propstore/world/model.py` — WorldModel (read-only reasoner over compiled sidecar)
- `propstore/world/bound.py` — BoundWorld (condition-bound view, Z3 activation, label attachment)
- `propstore/world/value_resolver.py` — ActiveClaimResolver (value_of_from_active, derived_value)
- `propstore/world/resolution.py` — resolve() with RECENCY/SAMPLE_SIZE/ARGUMENTATION/OVERRIDE strategies
- `propstore/worldline.py` — WorldlineDefinition, WorldlineResult, content hashing
- `propstore/worldline_runner.py` — run_worldline() materialization engine
- `propstore/argumentation.py` — claim-graph backend (Dung AF, NOT full ASPIC+)
- `tests/test_labelled_core.py` — label kernel tests including honesty boundaries
- `tests/test_semantic_repairs.py` — semantic integration tests

## KEY OBSERVATIONS

### 1. Label Honesty Boundary (the good)
- `_claim_support_label()` in bound.py:406-435 correctly returns `None` (no label) when:
  - Claim has a `context_id` (context-scoped, not unconditional)
  - Claim conditions don't have exact CEL string match in compiled assumptions
- This means Z3 semantic compatibility (claim active because `x==1` satisfies `x>0`) does NOT get a label
- Test `test_semantically_active_claim_without_exact_assumption_match_gets_no_label` confirms this

### 2. The Three Activation Tiers (observed)
- **Tier 1 — Exact match**: claim condition CEL string == binding CEL string → gets Label
- **Tier 2 — Z3 compatible**: Z3 says not disjoint → claim is ACTIVE but gets NO label (label=None)
- **Tier 3 — Context visible**: claim's context_id in ancestor set → claim is ACTIVE but gets NO label

### 3. Argumentation Backend Naming
- `argumentation.py` line 1-7: Module docstring explicitly says "This module does not build full structured ASPIC+ arguments"
- But `ReasoningBackend` enum only has `CLAIM_GRAPH`, and the worldline policy defaults to `semantics="grounded"` and `comparison="elitist"` — these ARE ASPIC+ terminology
- The `RenderPolicy` dataclass uses `semantics` and `comparison` fields that name ASPIC+ concepts

### 4. Worldline Runner Overclaiming Risks
- `run_worldline()` reports status="determined" for claims found via Z3 compatibility WITHOUT attaching any label
- The worldline output serialization strips labels (test confirms `"label" not in result.values`)
- But the STATUS still says "determined" even when the support basis is semantically approximate

### 5. Where Labels Lie
- Context-scoped claims: active via context hierarchy, reported as "determined", but label=None means no provenance trail
- Z3-compatible claims: active via Z3 non-disjointness, but user sees same "determined" status as exact-match claims
- Derived values: `_attach_derived_label` combines input labels, but if ANY input has label=None, the whole derived label is None — this is correct but invisible to the consumer

## DANGEROUS PATTERNS
1. `is_active()` conflates three different activation mechanisms under one boolean — consumer can't distinguish "exact match" from "Z3 says probably compatible" from "context ancestor says visible"
2. `value_of` returns `status="determined"` regardless of whether support is exact or approximate
3. Resolution strategies operate on active claims without knowing HOW they became active
4. The worldline output has no field indicating "this value was determined under approximate activation"
