# WS-05: Contexts, publication identity, ATMS, and provenance

## Review findings covered

- Nested `ist`/`proposition` claims are document-schema-only and do not reach validation, sidecar, search, conflict detection, or context stacks.
- Context-bearing ATMS environments are serialized/reported as assumption-only.
- Exact ATMS support depends on raw CEL string equality.
- Derived-vs-derived contradictions are hidden instead of becoming nogoods.
- Semiring provenance collapses to ATMS why-label projection too early.
- Duplicate concept `canonical_name` is a warning while lookup is first-wins.
- Invalid form `kind` silently becomes `quantity`.
- Micropublication identity work from `ws-03` feeds this stream.

## Dependencies

- Depends on `ws-02-schema-and-test-infrastructure.md`.
- Depends on the identity portions of `ws-03-storage-sidecar-identity-atomicity.md`.
- Should precede `ws-06-argumentation-belief-and-probability.md` where context-aware support and provenance affect semantics.

## First failing tests

1. Nested `ist` semantic lowering:
   - Create a claim document with `proposition: {kind: ist, context: C, proposition: atomic parameter claim}`.
   - Expected:
     - validation sees the inner atomic type
     - sidecar has claim/concept links for the inner proposition
     - context stack is queryable
     - FTS indexes inner statement
     - conflict detection can reason over the inner atomic claim when context rules permit it

2. Duplicate concept canonical name:
   - Two concept docs with distinct IDs but same `canonical_name`.
   - Expected: hard validation/build failure, not warning.
   - Add a claim/CEL reference by canonical name and assert no first-wins ambiguity is possible.

3. Invalid form kind:
   - Form doc with `kind: structual` or another typo.
   - Expected: validation failure at form boundary.
   - Assert no default to `quantity` reaches CEL/type behavior.

4. Context-preserving ATMS serialization:
   - Build an ATMS environment with assumptions and contexts.
   - Expected status/explain/JSON/CLI reports include both assumption IDs and context IDs.
   - Nogood details should preserve context-bearing environments.

5. CEL-semantic ATMS support:
   - Two equivalent CEL conditions with different surface syntax.
   - Runtime activation says compatible/active.
   - Expected ATMS support also recognizes them, rather than matching raw strings.

6. Derived-vs-derived nogood:
   - Two parameterizations derive incompatible values for the same target under compatible assumptions.
   - Expected:
     - resolver reports conflict, or
     - ATMS creates a nogood over the provider environments.
   - The first compatible derived value must not hide the later contradiction.

7. Semiring preservation:
   - Construct provenance with coefficient/exponent-sensitive polynomial or non-assumption where/source variable.
   - Combine labels.
   - Expected: full provenance object remains available; ATMS environments are a projection, not the stored truth.

## Production change sequence

1. Canonical identity hardening:
   - Make duplicate concept canonical names hard failures before any registry or CEL lookup.
   - Make invalid form kind a typed validation error; delete fallback-to-quantity behavior for unknown kind strings.

2. Nested proposition lowering:
   - Define a typed internal representation for nested propositions/`ist`.
   - Lower document payloads into that representation at the family boundary.
   - Update validation, sidecar rows, search, conflict detection, context lifting, and rendering to consume the typed structure.
   - Delete any parallel top-level-only path that claims nested support.

3. ATMS context preservation:
   - Update environment serialization to include contexts.
   - Update app support summaries and CLI renderers to preserve contexts.
   - Ensure minimality/consistency checks compare full environment keys, not assumptions only.

4. ATMS condition matching:
   - Replace raw CEL string equality in exact antecedent matching with typed parsed/canonical CEL or solver-equivalence checks.
   - Reuse the condition pipeline from `ws-04` rather than inventing a second parser.

5. Derived contradiction propagation:
   - Make value resolution collect all compatible derived candidates before selecting.
   - If incompatible candidates exist, emit structured conflicts.
   - Feed those conflicts into ATMS nogood generation with provider environments.

6. Provenance semiring architecture:
   - Keep Green-style polynomial/provenance as the primary support object.
   - Derive ATMS why-labels as a projection for TMS operations.
   - Preserve where/source variables and coefficients/exponents where the semiring needs them.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label contexts-atms tests/test_context*.py tests/test_world_atms*.py tests/test_labels_properties.py tests/test_source_relations.py`
  - Add new tests for nested `ist`, duplicate canonical names, invalid form kinds, derived nogoods, and semiring preservation.
- `uv run pyright propstore`
- `uv run lint-imports` if context/source/world ownership moves.

## Done means

- Nested context propositions are semantic objects, not just serialized document fields.
- Canonical concept/form identity is unambiguous and hard-failing on invalid input.
- ATMS reports and nogoods preserve context dimensions.
- Derived contradictions become explicit conflicts/nogoods.
- Provenance semiring information is not destroyed by ATMS projection.
