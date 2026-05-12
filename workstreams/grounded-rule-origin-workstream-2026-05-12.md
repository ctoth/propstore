# Grounded Rule Origin Workstream

Date: 2026-05-12

## Goal

Delete string-encoded grounded rule identity from the Gunray -> argumentation
-> Propstore path.

The current path uses ASPIC `Rule.name` as both:

- the formal ASPIC+ rule name `n(r)` needed for undercutting; and
- a carrier for source rule id and substitution data, shaped like
  `<source_rule_id>#<substitution-json>`.

That second use is the problem. Diller-style grounded substitutions and
Propstore projection provenance are structured backend data. They must not be
recovered by parsing ASPIC rule names.

## Target Architecture

ASPIC `Rule.name` remains only the formal undercut name `n(r)`.

Generated grounded rule names are opaque implementation identifiers such as
`gr0`, `gr1`, `uc0`. They must be stable within one projection, unique for
defeasible rules, and suitable for Modgil-Prakken undercutting. They must not
encode source rule ids, substitutions, target rule ids, or JSON payloads.

Structured grounded-rule origin data is carried separately:

```python
@dataclass(frozen=True)
class GroundRuleOrigin:
    source_rule_id: str
    substitution: tuple[tuple[str, Scalar], ...]
    role: Literal["ground", "undercut"]
    target_rule: Rule | None = None
```

`argumentation.datalog_grounding.GroundedDatalogTheory` owns the mapping:

```python
rule_origins: Mapping[Rule, GroundRuleOrigin]
```

Propstore consumes that mapping through a typed projection object. It does not
split or partition `Rule.name` to recover source identity.

## Non-Goals

- Do not remove ASPIC `Rule.name`; undercutting needs `n(r)`.
- Do not encode Propstore source identity inside the `argumentation.Rule`
  dataclass.
- Do not add compatibility readers for old generated names.
- Do not keep old parsed-name provenance and new structured origins in
  production at the same time.
- Do not pin Propstore to a local `argumentation` checkout.
- Do not change Gunray unless a hard API gap is discovered. Gunray already
  exposes `GroundingInspection` with typed substitutions.

## Execution Rules

- Work test-first and deletion-first.
- If replacing an interface, delete the old production surface first, then use
  type, search, and test failures as the work queue.
- Commit every intentional edit slice atomically with path-limited git
  commands.
- After every commit, reread this workstream before choosing the next slice.
- After every passing substantial targeted test run, reread this workstream
  before choosing the next slice.
- Use logged pytest wrappers in Propstore.
- Use `uv run ...` for Python tooling.
- Push `argumentation` changes first, then pin Propstore to a pushed immutable
  commit SHA or tag. Never pin to a local path or editable dependency.

## Dependency Order

Execute in this order:

1. Argumentation origin contract red tests
2. Argumentation deletion-first origin implementation
3. Argumentation origin gates and pushed dependency commit
4. Propstore projection contract red tests
5. Propstore deletion-first projection API replacement
6. Propstore fragility and undercut consumers
7. Search gates, docs, dependency pin, and full closure

Before implementation, make this dependency order mechanically executable:
write or run an order check proving each dependent phase appears after its
prerequisites. If the check fails, repair this workstream before editing
production code.

## Phase 1: Argumentation Origin Contract Red Tests

Repository: `../argumentation`

Goal: pin the structured origin contract before touching implementation.

Tests first:

- `tests/test_datalog_grounding.py` asserts
  `grounding_inspection_to_aspic(...).rule_origins` maps every generated
  defeasible ground rule to:
  - `source_rule_id`
  - exact typed substitution tuple
  - `role == "ground"`
- The same test asserts generated ground rule names do not contain `#`, `{`,
  `}`, or source rule ids.
- Superiority projection still maps source rule ids to the correct generated
  ground rules.
- Defeater projection still produces undercut rules whose consequents attack
  the target rule's opaque `n(r)` literal.
- Undercut rule origins use `role == "undercut"` and record the structured
  target rule object.
- `source_to_ground_rules` remains available but is populated from origins, not
  parsed names.

Expected red:

- Tests fail because rule names still contain `rule_id#substitution-json`.
- Tests fail because `GroundedDatalogTheory` has no `rule_origins` field.

Gate:

```powershell
Push-Location ..\argumentation
uv run pytest tests/test_datalog_grounding.py -q
Pop-Location
```

## Phase 2: Argumentation Deletion-First Origin Implementation

Repository: `../argumentation`

Delete first:

- Delete `_substitution_key(...)` from name generation.
- Delete `_source_rule_id(rule_name)` and all production calls that parse
  source ids from generated names.
- Delete any production assertion that generated names begin with source ids.

Then implement:

- Add `GroundRuleOrigin`.
- Add `rule_origins` to `GroundedDatalogTheory`.
- Generate opaque names deterministically:
  - ground defeasible rules: `gr0`, `gr1`, ...
  - generated undercut rules: `uc0`, `uc1`, ...
- Build `rule_origins` at the same time rules are created.
- Implement `source_to_ground_rules` by grouping rules whose origin has
  `role == "ground"` by `origin.source_rule_id`.
- Implement superiority projection from `source_to_ground_rules`.
- Implement defeater target lookup from structured source ids and rule objects,
  not parsed names.
- Keep undercut semantics unchanged: the undercut consequent is still
  `Literal(GroundAtom(target_rule.name), negated=True)`.

Do not:

- Add `source_rule_id` or `substitution` fields to `argumentation.aspic.Rule`.
- Preserve generated names containing source ids "for debugging".
- Add a helper that parses old generated names.

Search gates:

```powershell
rg -n -F "_substitution_key" src tests
rg -n -F "split(\"#\"" src tests
rg -n -F "partition(\"#\"" src tests
rg -n -F "startswith(\"d1#\"" tests
```

The only allowed hits are historical docs outside `src` and active tests that
assert the old pattern is absent.

Targeted gates:

```powershell
uv run pytest tests/test_datalog_grounding.py -q
uv run pyright src
```

Full gate before Propstore pin:

```powershell
uv run pytest
uv run pyright src
```

Commit and push:

- Commit the argumentation change.
- Push it.
- Record the pushed immutable SHA for Propstore Phase 7.

## Phase 3: Propstore Projection Contract Red Tests

Repository: `propstore`

Goal: make Propstore fail wherever it still treats rule names as provenance.

Tests first:

- Add or update a boundary test asserting production Propstore has no:
  - `partition("#")`
  - `split("#"`
  - rule-name `startswith("<source>#")`
  for grounded rule identity.
- Add a grounding/ASPIC test asserting `grounded_rules_to_rules(...)` or its
  replacement returns structured origins alongside rules and literals.
- Add a fragility test asserting `GroundedRuleTarget.substitution_key` is
  derived from structured origin data, not from `Rule.name`.
- Add an undercut stance test where
  `target_justification_id="birds_fly"` resolves the generated ground rule via
  `origin.source_rule_id == "birds_fly"`, even though no rule name starts with
  `birds_fly#`.
- Update existing tests that assert `rule.name.startswith("...#")` so they
  assert structured origin fields instead.

Expected red:

- Tests fail at `propstore/fragility_contributors.py` because it partitions
  rule names.
- Tests fail at `propstore/aspic_bridge/translate.py` because undercut target
  matching partitions rule names.
- Tests fail at older integration assertions expecting `rule.name` to contain
  substitution JSON.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label grounded-origin-red `
  tests/test_gunray_boundary_ws6.py `
  tests/test_grounding_grounder.py `
  tests/test_gunray_integration.py `
  tests/test_ws_f_aspic_bridge.py `
  tests/test_fragility.py
```

## Phase 4: Propstore Deletion-First Projection API Replacement

Repository: `propstore`

Delete first:

- Delete tuple-shaped production assumptions around
  `grounded_rules_to_rules(...) -> (strict_rules, defeasible_rules, literals)`.
- Delete production use of `_source_rule_id(rule.name)`.
- Delete production uses of `rule.name.partition("#")` for grounded rule
  identity.
- Delete production tests that require generated names to carry source ids or
  substitution JSON.

Then implement:

- Add a typed projection object in `propstore/aspic_bridge/grounding.py`, for
  example:

```python
@dataclass(frozen=True)
class GroundedAspicProjection:
    strict_rules: frozenset[Rule]
    defeasible_rules: frozenset[Rule]
    literals: dict[LiteralKey, Literal]
    origins: Mapping[Rule, GroundRuleOrigin]
```

- Replace `grounded_rules_to_rules(...)` with
  `project_grounded_rules(...) -> GroundedAspicProjection`, or change the
  existing function to return that object if all callers are updated in the same
  slice.
- Update `compile_bridge_context` to consume `projection.strict_rules`,
  `projection.defeasible_rules`, `projection.literals`, and
  `projection.origins`.
- Keep Propstore's `GroundedRulesBundle.projection_frames` as the Propstore
  source/fact frame surface. Do not move it into `argumentation`.
- Keep `argumentation.datalog_grounding` as the formal reduction over Gunray
  public types. Do not move it in this workstream.

Search gate:

```powershell
rg -n -F "grounded_rules_to_rules(" propstore tests
```

Every hit must either call the new object-returning API or be renamed to the
new API. No tuple unpacking of grounded rule projection remains.

Targeted gates:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label grounded-origin-projection `
  tests/test_gunray_boundary_ws6.py `
  tests/test_grounding_grounder.py `
  tests/test_gunray_integration.py `
  tests/test_ws_f_aspic_bridge.py
uv run pyright propstore
```

## Phase 5: Propstore Fragility And Undercut Consumers

Repository: `propstore`

Goal: update all consumers that need source ids, substitutions, or undercut
targets to use structured origins.

Tasks:

- Update `propstore/fragility_contributors.py`:
  - group undercut counts by target rule object or target origin, not by parsed
    target name;
  - populate `GroundedRuleTarget.rule_name` from the opaque formal rule name
    only if the payload still needs a display/debug name;
  - populate `GroundedRuleTarget.substitution_key` from origin substitution
    using a local typed renderer, or replace the payload field with structured
    substitution data if the domain model allows it in this slice;
  - populate provenance `source_ids` with structured source rule ids.
- Update undercut intervention payloads:
  - `defeater_rule_name` and `target_rule_name` should be formal names only if
    they are explicitly display/debug fields;
  - source ids and target links must come from origins.
- Update `propstore/aspic_bridge/translate.py` stance undercut resolution:
  - exact authored justifications may still match authored rule names;
  - grounded generated rules must match by `origin.source_rule_id`;
  - ambiguity messages list source rule ids and opaque formal names separately.
- Update tests that inspect intervention ids or descriptions if they currently
  assume `source#substitution` strings.

Do not:

- Parse opaque names in a different helper.
- Use `Rule.name.startswith(source_id)` as a replacement for `partition("#")`.

Search gates:

```powershell
rg -n -F "partition(\"#\"" propstore tests
rg -n -F "split(\"#\"" propstore tests
rg -n -F "startswith(\"birds_fly#\"" tests
rg -n -F "startswith('r_flies_bird#{\" tests
```

Allowed hits: only historical notes/reviews outside production and tests, or
negative tests asserting absence.

Targeted gates:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label grounded-origin-consumers `
  tests/test_fragility.py `
  tests/test_ws_f_aspic_bridge.py `
  tests/test_aspic_bridge_grounded.py `
  tests/test_gunray_integration.py
uv run pyright propstore
```

## Phase 6: Dependency Pin And Boundary Closure

Repository: `propstore`

Tasks:

- Update Propstore dependency pin for `formal-argumentation` or
  `argumentation` to the pushed SHA from Phase 2.
- Inspect `pyproject.toml` and `uv.lock` before editing to reject any local path
  or local repository pin.
- Regenerate lockfile only through `uv`.
- Update `docs/gaps.md` if this closes an open gap or changes the evidence for
  the Gunray/argumentation boundary.
- Update relevant workstream review notes only if they are active status
  records, not historical evidence.

Pin safety gates:

```powershell
rg -n -F 'path = "../' pyproject.toml uv.lock
rg -n -F 'file://' pyproject.toml uv.lock
rg -n -F 'editable = true' pyproject.toml uv.lock
```

No dependency entry may point at a local path.

Propstore targeted gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label grounded-origin-boundary `
  tests/test_gunray_boundary_ws6.py `
  tests/test_grounding_grounder.py `
  tests/test_gunray_integration.py `
  tests/test_ws_f_aspic_bridge.py `
  tests/test_aspic_bridge_grounded.py `
  tests/test_fragility.py
uv run pyright propstore
```

Dependency gates:

```powershell
Push-Location ..\argumentation
uv run pytest
uv run pyright src
Pop-Location

Push-Location ..\gunray
uv run pytest tests/test_public_api.py tests/test_grounding_inspection.py tests/test_diller_def12.py
uv run pyright src
Pop-Location
```

## Full Completion Gate

Run after all phase gates pass:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label grounded-origin-full tests
uv run pyright propstore
```

Then run:

```powershell
Push-Location ..\argumentation
uv run pytest
uv run pyright src
Pop-Location

Push-Location ..\gunray
uv run pytest
uv run pyright src
Pop-Location
```

Final search gates:

```powershell
rg -n -F "partition(\"#\"" propstore tests ..\argumentation\src ..\argumentation\tests
rg -n -F "split(\"#\"" propstore tests ..\argumentation\src ..\argumentation\tests
rg -n -F "startswith(\"d1#\"" tests ..\argumentation\tests
rg -n -F "startswith(\"birds_fly#\"" tests
rg -n -F "rule_id}#" ..\argumentation\src
```

All hits must be either absent, in historical notes/reviews, or in negative
tests asserting absence.

## Completion Definition

The workstream is complete only when:

- Generated grounded ASPIC rule names are opaque formal `n(r)` identifiers.
- No production code recovers source rule ids or substitutions from
  `Rule.name`.
- Argumentation exposes structured `GroundRuleOrigin` data for every generated
  grounded and undercut rule.
- Propstore consumes structured origins for fragility scoring, undercut target
  resolution, intervention provenance, and diagnostics.
- Gunray `GroundingInspection` remains the source of grounded substitutions.
- Propstore projection frames remain the source/fact provenance carrier.
- Propstore is pinned to a pushed argumentation commit or tag.
- Propstore, argumentation, and Gunray targeted and full gates pass.
