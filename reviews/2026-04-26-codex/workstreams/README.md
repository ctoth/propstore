# TDD workstream map

Goal: convert the deep review into ordered, test-first repair streams. Each stream starts by proving one or more review findings with failing tests, then deletes or replaces the defective production path, then broadens gates so the issue class stays fixed.

The order matters. Do not start with the most interesting semantic code if the schema/test scaffolding it relies on can still lie. The sequence below front-loads visibility, atomicity, schema truth, and identity boundaries, then moves into reasoning semantics.

## Dependency order

1. `ws-01-render-policy-and-readonly-boundaries.md`
   - Fixes user-visible data leaks and read-only mutation before deeper behavior work.
   - Depends on no other stream.

2. `ws-02-schema-and-test-infrastructure.md`
   - Makes tests use production schema and closes stale schema validation gaps.
   - Depends on stream 1 only for any shared web/sidecar fixtures.

3. `ws-03-storage-sidecar-identity-atomicity.md`
   - Fixes materialize atomicity, branch-head CAS, and content/logical identity collapses.
   - Depends on stream 2 so duplicate/sidecar tests use the real schema.

4. `ws-04-formal-expressions-units-equations.md`
   - Fixes unit-normalized conflicts, Z3 guard scoping, CEL ternary typing, equation/algorithm equivalence.
   - Depends on stream 2 for reliable fixtures.

5. `ws-05-contexts-publications-and-atms.md`
   - Fixes nested `ist`, context identity/reporting, micropub identity, derived nogoods, semiring projection.
   - Depends on streams 2 and 3 because publication identity and sidecar rows must be trustworthy first.

6. `ws-06-argumentation-belief-and-probability.md`
   - Fixes ASPIC/Dung/PrAF/DF-QuAD/IC/AGM/worldline revision semantics.
   - Depends on stream 4 for correct formal-condition behavior and stream 5 for context-aware support.

7. `ws-07-cli-architecture-and-gates.md`
   - Moves CLI-shaped parsing out of app/owner layers and adds package-wide gates.
   - Can begin after stream 2, but should finish after streams 3-6 so new owner APIs are not designed around broken interfaces.

## TDD discipline for every stream

- First commit in a stream should be failing tests only, unless the issue is already proven by an existing failing test. The test must fail for the reviewed reason, not for setup noise.
- Prefer focused regression tests at the owner boundary first, then one integration test through CLI/web/world policy where the bug is user-visible.
- When replacing a surface, delete the old production path first and let compiler/test/search failures drive caller updates.
- Every stream ends with targeted logged pytest commands, `uv run pyright propstore`, and `uv run lint-imports` when imports or ownership moved.
- Do not claim a stream is complete while old/new production paths coexist, unless the stream explicitly documents an external compatibility constraint.

## Cross-stream proof gates

- Sidecar schema drift gate: fixture schemas must be generated from production schema or byte-compared against it.
- Render-policy gate: default web/app views must not expose blocked/draft content, IDs, counts, or relations unless include flags request them.
- Identity gate: same logical ID with different version/content must hard-fail; duplicate identical rows must be idempotent across parent and child tables.
- Semantic-surface gate: every advertised `WorldSemantics` value must either execute through the selected backend or fail during policy validation.
- Paper-conformance gate: each paper-backed operator gets at least one test for the postulate/property that distinguishes it from a weaker local approximation.
