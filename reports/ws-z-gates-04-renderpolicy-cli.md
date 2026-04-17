# WS-Z-gates Phase 4 — RenderPolicy Fields + CLI Flags + `pks source status` Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source spec: `prompts/ws-z-gates-04-renderpolicy-cli.md`
Author: coder subagent

Phase 4 takes the Phase 3 sidecar lifecycle population and makes it
visible through render policy and the CLI. Three `RenderPolicy`
visibility flags gate the default view; five `pks world` subcommands
expose the flags; a new `pks source status <name>` subcommand surfaces
per-claim promotion outcome directly from `claim_core` and
`build_diagnostics`. Closes axis-1 findings 3.1 / 3.2 / 3.3 in the
render layer.

## Commits

One red + one green per TDD cycle, plus one cleanup commit.

| SHA | Deliverable | Phase | Message |
|-----|-------------|-------|---------|
| `cb9a7e1` | 1 | red | `test(render_policy): include_drafts/include_blocked/show_quarantined fields round-trip (failing)` |
| `d489635` | 1 | green | `feat(render_policy): add include_drafts/include_blocked/show_quarantined boolean fields` |
| `009dda2` | 2 | red | `test(render_policy): lifecycle visibility flags filter claim_core + surface build_diagnostics (failing)` |
| `1c47816` | 2 | green | `feat(world_model): claims_with_policy + build_diagnostics apply lifecycle-visibility flags` |
| `74176b1` | 3 | red | `test(cli): pks world {status,query,resolve,chain,derive} accept lifecycle flags (failing)` |
| `f930d74` | 3 | green | `feat(cli): pks world {status,query,resolve,chain,derive} accept lifecycle flags` |
| `b48f62d` | 4 | red | `test(cli): pks source status lists promotion_status='blocked' rows per source (failing)` |
| `c263db6` | 4 | green | `feat(cli): pks source status lists per-claim promotion status from sidecar` |
| `5a47bfa` | 5 | cleanup | `fix(cli): resolve source.py pyright unknown-import warning after phase-3 refactor` |

No refactor-only commits were needed — the green commits land cohesive
changes with docstrings + tests in one pass.

## Final test suite

```
........................................................................ [ 98%]
..........................................                               [100%]
2562 passed in 518.62s (0:08:38)
```

Phase 3 baseline was 2535. Net delta: **+27 tests**:

- `tests/test_render_policy_opinions.py` — 3 new tests for the three
  visibility fields (default False, round-trip, omit-when-default).
- `tests/test_render_policy_filtering.py` — 11 new tests exercising
  `claims_with_policy` + `build_diagnostics` across the full
  lifecycle matrix (1 fixture sanity + 4 default-hides + 1 default-
  omits-diagnostics + 5 opt-in flags + 1 everything-visible).
- `tests/test_cli_render_policy_flags.py` — 10 new tests covering
  `pks world status` (4 count assertions), `pks world query` (3
  visibility assertions), and a 3-parametrized flag-acceptance check
  for `resolve` / `chain` / `derive`.
- `tests/test_cli_source_status.py` — 3 new tests for
  `pks source status` (blocked rows listed, promoted claims excluded,
  empty source handled).

27 new + 0 inversions = consistent with 2562 − 2535 = 27.

No flake activity this phase — the Hypothesis deadline flakes that
phases 2 and 3 flagged (`test_aspic_bridge.py::TestBridgeRationalityPostulates::test_direct_consistency`,
`test_form_dimensions.py::TestDimensionsPropertyBased::test_dimensionless_implies_empty_or_absent_dimensions`)
surfaced once during intermediate runs at `--timeout=180` but passed
on isolation re-run and on the final full-suite pass.

## Surface area (`git diff --stat f594972..HEAD -- propstore/ tests/`)

```
 propstore/cli/compiler_cmds.py        | 257 ++++++++++++++++++++++--
 propstore/cli/source.py               |  94 +++++++++
 propstore/source/common.py            |  10 +
 propstore/world/model.py              |  96 ++++++++-
 propstore/world/types.py              |  24 +++
 tests/conftest.py                     |   5 +-
 tests/test_cli_render_policy_flags.py | 357 ++++++++++++++++++++++++++++++++++
 tests/test_cli_source_status.py       | 279 ++++++++++++++++++++++++++
 tests/test_graph_build.py             |   5 +-
 tests/test_render_policy_filtering.py | 356 +++++++++++++++++++++++++++++++++
 tests/test_render_policy_opinions.py  |  55 ++++++
 11 files changed, 1523 insertions(+), 15 deletions(-)
```

Two test-fixture updates are co-located with the Deliverable 2 green
commit because the new always-on projection of
`build_status`/`stage`/`promotion_status` in `_claim_select_sql`
required the canonical test schema in `tests/conftest.py`
(`create_world_model_schema`) plus the in-test `NormalizedProjectionStore`
SELECT in `tests/test_graph_build.py` to mirror the columns — both
tests that compare projection shapes against the real WorldModel's
output.

## Deliverable 1 — `RenderPolicy` fields

Three new booleans at `propstore/world/types.py:821` (after
`concept_strategies`), with docstring block citing the workstream + the
three axis-1 findings:

- `include_drafts: bool = False` — lifts the default filter hiding
  `stage='draft'` rows.
- `include_blocked: bool = False` — lifts the default filter hiding
  `build_status='blocked'` OR `promotion_status='blocked'` rows.
- `show_quarantined: bool = False` — surfaces `build_diagnostics`
  rows.

`from_dict` reads the three keys with `bool(... default=False)`;
`to_dict` follows the existing omit-when-default pattern
(`if self.include_drafts: data["include_drafts"] = True`).

## Deliverable 2 — Render-layer consumption

`_claim_select_sql()` now always projects `core.build_status`,
`core.stage`, `core.promotion_status` — the sidecar is the source of
truth; lifecycle state rides alongside every row regardless of render
choice. The values land on `ClaimRow.attributes` via the row-types
`known` fallback (None values are filtered out, so clean claims carry
no extra attributes).

Two new methods on `WorldModel`:

- `_render_policy_predicates(policy) -> (list[str], tuple[Any, ...])`
  — private helper translating a `RenderPolicy` into SQL `WHERE`
  predicates. Default policy produces three predicates
  (`stage IS NULL OR stage != 'draft'`, `build_status IS NULL OR
  build_status != 'blocked'`, `promotion_status IS NULL OR
  promotion_status != 'blocked'`).
- `claims_with_policy(concept_id, policy) -> list[ClaimRow]` —
  policy-aware render entry point. Composes the existing
  `_claim_rows` helper with the policy predicates + any
  concept-scoped WHERE clause.
- `build_diagnostics(policy) -> list[dict[str, Any]]` — returns
  diagnostic rows only under `policy.show_quarantined=True`. Guards
  with `_has_table("build_diagnostics")` so older schemas (if any)
  degrade to an empty list rather than raising.

The existing `claims_for` / `claims_by_ids` are unchanged — internal
callers that don't have a policy (compile path, index building) keep
using them. The `ArtifactStore` Protocol signature stays untouched.

## Deliverable 3 — CLI flags on `pks world ...`

Five subcommands grew the three flags, each with
`is_flag=True, default=False` and kebab-case naming:

- `pks world status` — now reports `Claims:` under the policy
  (uses `claims_with_policy(None, policy)`);
  `--show-quarantined` appends a `Diagnostics: <n>` line.
- `pks world query <concept>` — swaps `claims_for` for
  `claims_with_policy`; `--show-quarantined` appends a Diagnostics
  block iterating `build_diagnostics` rows.
- `pks world derive` — threads the policy through `_bind_world(...,
  policy=policy)`.
- `pks world resolve` — its existing `RenderPolicy(...)` construction
  now carries `include_drafts`/`include_blocked`/`show_quarantined`
  alongside strategy + decision-criterion settings.
- `pks world chain` — accepts the flags for CLI symmetry. Policy is
  constructed (`_lifecycle_policy(...)`) and held in a `_` binding so
  a future chain implementation can thread it. Flagged in phase-5
  follow-ups if anyone wants chain to actually filter; behavior today
  is unchanged.

The shared `_lifecycle_policy(include_drafts, include_blocked,
show_quarantined, *, base=None)` helper sits alongside `_bind_world`
and either constructs a fresh `RenderPolicy` or clones an existing
`base` via `dataclasses.replace` — keeps the construction site
consistent across the five subcommands.

The helper uses a local runtime import of `RenderPolicy` (the
module-level import of `RenderPolicy` in `compiler_cmds.py` is
TYPE_CHECKING-only; the helper must not trigger a NameError at call
time). Initially I missed that and the first suite-run hit
`NameError: name 'RenderPolicy' is not defined`; the fix was one-line.

## Deliverable 4 — `pks source status` subcommand

New `source_status` subcommand at `propstore/cli/source.py`, added
between `promote` and `sync`. Queries the primary-branch sidecar:

```sql
SELECT id, promotion_status
FROM claim_core
WHERE branch = ? AND promotion_status IS NOT NULL
```

joined with the corresponding `build_diagnostics` rows via either
`diag.claim_id = claim_core.id` or
`diag.source_ref LIKE '<branch>:%'`. Output follows the `pks log`
tabular style (`propstore/cli/__init__.py:155-187`): three columns
(`CLAIM ID`, `STATUS`, `MESSAGE`) with a separator rule.

Missing-sidecar and empty-source cases emit a short status message
rather than erroring (e.g., `"No sidecar built yet — run 'pks build'
first."`, `"No promotion-status rows for source/<name>."`). The three
new tests cover (a) blocked rows surface, (b) successfully-promoted
claims are NOT listed (they're on master now), (c) empty source
produces a clean 0-rows output.

## Deliverable 5 — pyright cleanup

**Investigation finding.** `propstore/cli/source.py:33` imports
`source_branch_name` (and six other symbols) from `propstore.source`.
`propstore/source/__init__.py` in turn imports `source_branch_name`
and `normalize_source_slug` from `.common`. But
`propstore/source/common.py` pulls those two names from
`propstore.artifacts`, which exposes them through a lazy
`__getattr__` dispatch table (`_EXPORTS` + module-level `__getattr__`
in `propstore/artifacts/__init__.py:122`). Pyright cannot follow the
dispatch — it types the dispatched bindings as `object`, which then
cascades: `common.py`'s rebound names are `object`, `source.__init__`
re-export is `object`, and `cli/source.py:33` sees an unknown symbol.

**Fix.** Import `normalize_source_slug` and `source_branch_name`
directly from the source module `propstore.artifacts.refs` in
`common.py` — bypassing the `__getattr__` indirection. Runtime
behavior is unchanged; static analysis now resolves the chain.

**Verification.**

```
$ uv run pyright propstore/cli/source.py
0 errors, 0 warnings, 0 informations
```

`propstore/source/common.py` still produces ten pyright errors of the
form `Object of type "object" is not callable` — same root cause (other
`SOURCE_*_FAMILY` constants + identity helpers accessed via the
`propstore.artifacts` `__getattr__` dispatch). Those are out of Phase 4
scope; flagged for the broader pyright follow-up below.

## Deviations from the scout's proposed shape

1. **Scout D "three flags plumb through `_bind_world`"** (compiler_cmds.py:87):
   for `status` and `query` the plumbing is simpler than via
   `_bind_world` — those commands don't bind a world and don't need a
   BoundWorld. They call `claims_with_policy` / `build_diagnostics`
   directly on the `WorldModel`. For `derive` and `resolve` the
   plumbing does go via `_bind_world` (for `derive`) or the existing
   `RenderPolicy(...)` construction (for `resolve`). The helper
   `_lifecycle_policy` is the shared construction site.

2. **Scout D "pks world chain materially involves claim visibility":**
   I accepted the three flags on `chain` for CLI symmetry but did NOT
   thread them into the `chain_query` call — `chain_query` today reads
   parameterization + relationship state rather than a lifecycle-
   filtered claim set. The flags are silent today; a future chain
   reimplementation can consume them from the constructed policy.
   Documented in the subcommand docstring. Test `TestWorldCommandFlagsAccepted`
   asserts the flags parse rather than behaviorally change the output.

3. **Scout C "`include_blocked` subsumes both build_status='blocked'
   and promotion_status='blocked'":** I kept them as two predicates
   under the single flag per scout recommendation. The test
   `test_include_blocked_surfaces_both_blocked_variants` asserts both
   variants surface together.

4. **Scout C "three new lines each in from_dict/to_dict":** verified
   literally — three lines each. `from_dict` adds three kwargs at the
   end of the constructor call; `to_dict` adds three `if …:` blocks
   after `concept_strategies`.

5. **Fixture completeness for Deliverable 2 tests:** the render-policy
   filter tests needed a real schema-v3 sidecar (not a hand-rolled
   minimal one). The fixture was iterated through four fixes: missing
   NOT NULL columns on `concept`, explicit-NULL vs DEFAULT behaviour on
   `claim_core.version_id`/`content_hash`, missing `concept_fts`
   virtual table (WorldModel's `_validate_schema` requires it), and
   invalid `SourceKind`/`SourceOriginType` enum values. Final fixture
   uses `create_tables` + `create_context_tables` + `create_claim_tables`
   + an inline `CREATE VIRTUAL TABLE concept_fts`. Documented in the
   test file's module docstring.

## Pyright `cli/source.py:33` investigation status

**Resolved.** The warning was an analysis-only artifact caused by
`propstore.artifacts`'s lazy `__getattr__` dispatch pattern typing
re-exported names as `object`. Fix: one-line change in
`propstore/source/common.py` importing the two offending names
directly from `propstore.artifacts.refs`. Runtime behavior unchanged;
full suite green; pyright on `cli/source.py` is clean.

## Flags for Phase 5

1. **Broader pyright cleanup of the `propstore.artifacts` `__getattr__`
   dispatch pattern.** Phase 4's fix narrowly addresses `cli/source.py:33`.
   `propstore/source/common.py` still reports 10 "Object of type
   'object' is not callable" errors from the same root cause (other
   `SOURCE_*_FAMILY` constants, `normalize_canonical_claim_payload`,
   etc.). Two paths: (a) import everything directly from the source
   submodules (`.families`, `.refs`, `.identity`); (b) rework the
   `_EXPORTS` dispatch so pyright can see the names statically
   (e.g., typed `TYPE_CHECKING` block listing them). Cosmetic; out of
   scope here.

2. **`pks world chain` lifecycle plumbing.** Today the three flags are
   accepted but `chain_query` ignores them. If a future chain
   implementation reads claim sets (not just parameterizations), the
   constructed `_lifecycle_policy` already exists at the call site and
   needs only to be forwarded.

3. **`docs/gaps.md` closure records.** The prompt says explicitly that
   CLAUDE.md / `docs/gaps.md` cleanup is Phase 5's scope. Phase 4 did
   NOT touch either. The findings 3.1 / 3.2 / 3.3 entries in
   `docs/gaps.md` (if present there) should flip to closed.

4. **`--output-format=json` on `pks source status`.** Today the
   subcommand emits tabular text matching `pks log`. A JSON variant
   would make automation easier. Not required by the spec; noted as a
   UX follow-up.

5. **Module-level `RenderPolicy` import in `compiler_cmds.py`.**
   Currently TYPE_CHECKING-only; `_lifecycle_policy` has a runtime
   import. Pulling `RenderPolicy` out of the `TYPE_CHECKING` block
   would eliminate the double import. Cosmetic.

## Citation-as-claim discipline

Per discipline rule 1: citations in docstrings must be backed by tests.
Every new function docstring in this phase cites
`reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md` plus
the specific axis-1 finding number (3.1 / 3.2 / 3.3). Each is backed
by at least one of the new tests enumerated above:

- `RenderPolicy.include_drafts/include_blocked/show_quarantined`
  field docstrings → `tests/test_render_policy_opinions.py::test_lifecycle_visibility_flags_*`.
- `WorldModel._render_policy_predicates` / `claims_with_policy` /
  `build_diagnostics` → `tests/test_render_policy_filtering.py`.
- CLI subcommand docstrings (status/query/derive/resolve/chain) →
  `tests/test_cli_render_policy_flags.py`.
- `pks source status` docstring →
  `tests/test_cli_source_status.py::test_source_status_lists_blocked_promotion_rows`.
- `_lifecycle_policy` helper docstring → tested indirectly through
  every CLI test that exercises the five subcommands.

## File path reference (absolute paths)

- Source:
  - `C:\Users\Q\code\propstore\propstore\world\types.py` (RenderPolicy fields)
  - `C:\Users\Q\code\propstore\propstore\world\model.py` (claims_with_policy + build_diagnostics)
  - `C:\Users\Q\code\propstore\propstore\cli\compiler_cmds.py` (five subcommand flag additions + _lifecycle_policy)
  - `C:\Users\Q\code\propstore\propstore\cli\source.py` (source_status subcommand + sqlite3 import)
  - `C:\Users\Q\code\propstore\propstore\source\common.py` (pyright fix)
- Tests:
  - `C:\Users\Q\code\propstore\tests\test_render_policy_opinions.py` (+3 tests)
  - `C:\Users\Q\code\propstore\tests\test_render_policy_filtering.py` (new file)
  - `C:\Users\Q\code\propstore\tests\test_cli_render_policy_flags.py` (new file)
  - `C:\Users\Q\code\propstore\tests\test_cli_source_status.py` (new file)
  - `C:\Users\Q\code\propstore\tests\conftest.py` (canonical schema lifecycle cols)
  - `C:\Users\Q\code\propstore\tests\test_graph_build.py` (projection mirror update)
