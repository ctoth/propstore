# Typed Literal Identity Workstream

Date: 2026-04-13
Status: completed

## Goal

Replace the current stringly literal-key surface in the ASPIC bridge with typed
literal identity objects, and use `pyright` to keep the cutover honest.

The specific target is to delete the production path where grounded literals are
interned and queried through serialized string keys such as the JSON emitted by
[`_ground_literal_key`](C:/Users/Q/code/propstore/propstore/aspic_bridge.py:307).

The desired end state is:

- core identity is typed, not serialized
- claim literals and grounded literals do not share a key namespace
- core maps use `LiteralKey` objects rather than `str`
- parsing/serialization happens only at explicit CLI or API boundaries
- `query_claim()` no longer guesses whether a string is a claim id or an
  encoded ground atom

## Why This Exists

The current implementation is correct enough after the review-v2 fixes, but it
still has an ugly internal protocol:

- [`claims_to_literals`](C:/Users/Q/code/propstore/propstore/aspic_bridge.py:106)
  returns `dict[str, Literal]`
- grounded literals are keyed by serialized JSON strings in
  [`_ground_literal_key`](C:/Users/Q/code/propstore/propstore/aspic_bridge.py:307)
- [`_parse_ground_atom_key`](C:/Users/Q/code/propstore/propstore/aspic_bridge.py:492)
  exists to recover structure from strings
- [`query_claim`](C:/Users/Q/code/propstore/propstore/aspic_bridge.py:1060)
  still branches on "claim id vs parseable ground atom string"

That is a stringly protocol pretending to be a domain model. We control the
stack, so the right move is to cut directly to typed identity.

## Scope

Writable repo for this workstream:

- `C:/Users/Q/code/propstore`

Primary files likely involved:

- `propstore/aspic_bridge.py`
- `propstore/structured_projection.py`
- `propstore/worldline/argumentation.py`
- `propstore/core/analyzers.py`
- any tests that currently assert string-key internals
- `pyproject.toml` for `pyright` strict-surface ratcheting

## Non-goals

- Do not redesign `Literal`, `GroundAtom`, or `Rule`.
- Do not re-open the review-v2 semantics work unless the typed cutover exposes
  a real bug.
- Do not keep both typed and string key paths as first-class production paths.
- Do not add fallback parsers or compatibility aliases unless an external
  boundary we do not control forces it.

## Target Architecture

Add a new identity module, preferably:

- `propstore/core/literal_keys.py`

Define:

### `ClaimLiteralKey`

- frozen dataclass
- field: `claim_id: str`

### `GroundLiteralKey`

- frozen dataclass
- fields:
  - `predicate: str`
  - `arguments: tuple[Scalar, ...]`
  - `negated: bool`

### `LiteralKey`

- type alias:
  - `ClaimLiteralKey | GroundLiteralKey`

Core maps should become:

- `dict[LiteralKey, Literal]`

Core helpers should become:

- `claim_key(claim_id: str) -> ClaimLiteralKey`
- `ground_key(atom: GroundAtom, negated: bool) -> GroundLiteralKey`

Delete from the production path:

- `_ground_literal_key()`
- `_parse_ground_atom_key()`
- any internal `dict[str, Literal]` that mixes claim ids with grounded atoms

Boundary-only serialization may exist, but only in explicit UI/query adapters,
not inside ASPIC construction and reasoning.

## Pyright Discipline

`pyright` is not optional for this cutover. It is the main guardrail against
accidentally carrying the old string path forward.

Current config:

- [`pyproject.toml`](C:/Users/Q/code/propstore/pyproject.toml:44)

Use these commands during the workstream:

1. whole-repo baseline:
   - `uv run pyright`
2. targeted file checks after each slice:
   - `uv run pyright propstore/aspic_bridge.py`
   - plus any newly touched files
3. after each slice is green, ratchet strict coverage in `pyproject.toml`
   for the newly cleaned files when practical

Type-specific rules for this workstream:

- when a function still accepts a string boundary input, convert it to a typed
  `LiteralKey` immediately
- internal helper signatures should use `LiteralKey`, not `str`
- if `pyright` still permits a `dict[str, Literal]` in the core bridge flow,
  the slice is not done

## Execution Discipline

For each slice:

1. add or update a failing test first
2. run the red test and keep the log
3. change types first, then behavior
4. run focused tests
5. run `uv run pyright` on the touched surface
6. run the nearest broader regression suite
7. commit and push

Use the project test rule:

- always run pytest as `uv run pytest -vv`
- tee logs under `logs/test-runs/`

Use the repo sync rule:

- `uv sync --upgrade` before starting if the env may have drifted

## Phase Plan

### Phase 0: Baseline and Inventory

Tasks:

1. run `uv sync --upgrade`
2. run `uv run pyright` and capture the baseline
3. inventory every function in `aspic_bridge.py` that still uses
   `dict[str, Literal]`
4. inventory every test that asserts string-key internals

Exit criteria:

- baseline pyright log exists
- old string-key surfaces are enumerated

### Phase 1: Introduce Typed Key Objects

Tasks:

1. add `propstore/core/literal_keys.py`
2. define `ClaimLiteralKey`, `GroundLiteralKey`, `LiteralKey`
3. add focused tests for equality, hashing, and namespace separation
4. add pyright-visible annotations for the new types

Exit criteria:

- key objects exist and are tested
- pyright accepts the new module cleanly

### Phase 2: Cut Claims Side To Typed Keys

Tasks:

1. change `claims_to_literals()` to return `dict[LiteralKey, Literal]`
2. make claim lookup use `ClaimLiteralKey`
3. update callers in the bridge and nearby projections
4. delete any claim-side reliance on raw string keys in core flow

Exit criteria:

- claim literals are keyed only by `ClaimLiteralKey`
- core claim lookup no longer indexes by raw `str`

### Phase 3: Cut Grounded Side To Typed Keys

Tasks:

1. replace `_ground_literal_key()` usage with `GroundLiteralKey`
2. replace `_literal_for_atom()` to intern by typed key
3. update `grounded_rules_to_rules()` and `_ground_facts_to_axioms()`
4. update tests to assert typed-key behavior rather than string encoding

Exit criteria:

- grounded literals are keyed only by `GroundLiteralKey`
- no production code depends on serialized ground-literal strings

### Phase 4: Delete String Recovery Path

Tasks:

1. delete `_parse_ground_atom_key()`
2. refactor `query_claim()` so the internal goal resolution surface is typed
3. if a public boundary still accepts strings, convert at the boundary only
4. update docs/tests to reflect the boundary shape explicitly

Exit criteria:

- no internal parser-from-key remains
- `query_claim()` does not branch on "maybe claim id, maybe encoded atom" in
  the core reasoning path

### Phase 5: Pyright Ratchet

Tasks:

1. add the typed-key module to strict checking
2. add `propstore/aspic_bridge.py` to strict checking if still feasible
3. add any directly touched bridge callers to strict checking when they no
   longer depend on `dict[str, object]` glue

Exit criteria:

- strict list expanded in `pyproject.toml`
- touched identity surfaces are pyright-clean

### Phase 6: Broader Validation

Tasks:

1. rerun focused bridge suites
2. rerun full ASPIC/bridge suites
3. rerun whole-repo `uv run pyright`
4. rerun full repo pytest suite

Exit criteria:

- bridge tests green
- full repo pytest green
- whole-repo pyright rerun completed, with no new errors on the touched
  identity surfaces and no increase in the unrelated baseline count

## Test Plan

Add or update focused tests for:

1. `ClaimLiteralKey("bird(tweety)")` not colliding with
   `GroundLiteralKey("bird", ("tweety",), False)`
2. positive and negative ground literals not aliasing
3. two structurally equal ground atoms interning to the same key
4. bridge outputs remaining language-complete under typed keys
5. query goal resolution using typed identity internally
6. old repr/json key expectations removed from tests

## Pyright-Specific Checks

The following should be treated as failures during execution:

- `dict[str, Literal]` still flowing through ASPIC bridge core helpers
- functions in the bridge returning `Any` or untyped mappings to dodge the cut
- casts used to preserve the old string protocol instead of changing the types

Preferred pyright outcome:

- `LiteralKey` appears in helper signatures
- no `reportUnknown*` noise on the new key module
- strict coverage expands rather than shrinks

## Completion Criteria

This workstream is complete only when all of the following are true:

1. internal literal maps use typed key objects, not serialized strings
2. claim and grounded literal namespaces are disjoint by type, not convention
3. `_parse_ground_atom_key()` is gone from production code
4. tests assert typed identity behavior rather than string encoding internals
5. touched surfaces are pyright-clean
6. the repo-wide pytest suite is green
7. the touched identity surfaces are pyright-clean under the strict ratchet, and
   the whole-repo pyright baseline has not regressed
8. the resulting slices are committed and pushed

## Execution Log

### Phase 1: Introduce Typed Key Objects

Status: completed

Proof:

- red: `logs/test-runs/literal-keys-phase1-red-20260413-012735.log`
- green: `logs/test-runs/literal-keys-phase1-green-20260413-012757.log`
- pyright: `logs/test-runs/pyright-literal-keys-phase1-20260413-012757.log`

Notes:

- added `propstore/core/literal_keys.py`
- proved claim/ground namespace separation and polarity-sensitive identity

### Phase 2: Cut Claims Side To Typed Keys

Status: completed

Proof:

- red: `logs/test-runs/literal-keys-phase2-red-20260413-012856.log`
- green: `logs/test-runs/literal-keys-phase2-green-20260413-013216.log`
- pyright: `logs/test-runs/pyright-aspic-bridge-phase2-20260413-013216.log`

Notes:

- `claims_to_literals()` now keys authored claims with `ClaimLiteralKey`
- bridge claim lookups no longer index the core literal map by raw `str`

### Phase 3: Cut Grounded Side To Typed Keys

Status: completed

Proof:

- green: `logs/test-runs/literal-keys-phase34-rerun-20260413-013721.log`
- pyright: `logs/test-runs/pyright-aspic-bridge-phase34-rerun-20260413-013721.log`

Notes:

- grounded literal internment now uses `GroundLiteralKey`
- `grounded_rules_to_rules()` and `_ground_facts_to_axioms()` operate on
  `dict[LiteralKey, Literal]`
- deleted `_ground_literal_key()` from the bridge; callers now use
  `ground_key()` directly
- grounded tests now assert typed-key behavior rather than serialized-key
  internals

### Phase 4: Delete String Recovery Path

Status: completed

Proof:

- red: `logs/test-runs/literal-keys-phase4-red-20260413-013424.log`
- green: `logs/test-runs/literal-keys-phase34-rerun-20260413-013721.log`

Notes:

- deleted `_parse_ground_atom_key()` from production code
- `query_claim()` now accepts explicit typed goal references:
  `str` for authored claim ids, `GroundAtom` for grounded goals, or `LiteralKey`
  when the caller already has one
- updated gunray integration tests to pass grounded goals explicitly

### Phase 5: Pyright Ratchet

Status: completed

Proof:

- strict ratchet: `logs/test-runs/pyright-strict-ratchet-rerun-20260413-013834.log`

Notes:

- added `propstore/core/literal_keys.py` and `propstore/aspic_bridge.py` to the
  `strict` list in `pyproject.toml`

### Phase 6: Broader Validation

Status: completed

Proof:

- broader bridge suite: `logs/test-runs/literal-keys-broader-bridge-20260413-013758.log`
- final helper-removal regression: `logs/test-runs/literal-keys-ground-helper-removal-20260413-015232.log`
- whole-repo pyright baseline rerun: `logs/test-runs/pyright-whole-repo-final-20260413-015249.log`
- final full repo pytest: `logs/test-runs/full-suite-literal-identity-final-20260413-015249.log`

Notes:

- whole-repo pyright is still not green because the repo already had a large
  unrelated baseline; the baseline improved from `1325` errors to `1323`
  without widening this workstream
- full repo pytest is green: `2401 passed`
