# Literature Alignment Execution Plan

Date: 2026-03-28

## Purpose

This is the execution plan for the literature-alignment fixes that are now specified well enough to implement with strict TDD.

This plan is intended to be monkeyproof:

- every work item has an exact scope
- every work item starts with explicit RED tests
- every work item has a bounded implementation surface
- every work item has a stop condition
- no semantic rename or fallback is allowed to hide an unresolved paper mismatch

This plan supersedes the earlier "paper gaps" framing. After processing:

- `Hunter_2021_ProbabilisticArgumentationSurvey`
- `Popescu_2024_ProbabilisticArgumentationConstellation`
- `Rago_2016_DiscontinuityFreeQuAD`
- `Rago_2016_AdaptingDFQuADBipolarArgumentation`

the remaining work is implementation, schema migration, and careful API naming, not paper discovery.

## Global Rules

1. Do not implement before the RED tests exist.
2. Do not batch unrelated semantic changes into one patch.
3. Do not reuse old overloaded names when the papers distinguish different objects.
4. Do not silently preserve legacy behavior under a paper-backed name if the behavior is not paper-backed.
5. After each passing targeted test run, reread this plan and continue with the next unchecked item.

## Test Execution Discipline

All tests must be run with:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv <TEST_SELECTION> 2>&1 | Tee-Object -FilePath "logs/test-runs/<NAME>-$ts.log"
```

### Required RED-GREEN loop for every item

1. Add only the tests for the current item.
2. Run only the smallest relevant test selection.
3. Confirm the new tests fail for the expected reason.
4. Implement only the code needed for this item.
5. Re-run the same focused selection until green.
6. Re-run the accumulated suite for all completed items.
7. Only then move to the next item.

## Work Order

The order is fixed:

1. A1. ASPIC+ `link` threading
2. A2. `grounded` vs `hybrid-grounded`
3. A3. Rule-specific undercuting schema and behavior
4. B1. PrAF query-type split
5. B2. DF-QuAD split into QuAD-mode vs BAF-mode

Reason for this order:

- A1 and A2 are pure wiring/name repairs with minimal schema impact.
- A3 introduces the only required data-model change on the structured side.
- B1 and B2 are public API changes and should happen only after the structured layer is semantically honest again.

## Canonical Paper Anchors

These are the papers that control the implementation:

- Dung 1995:
  - grounded extension is the least fixed point
  - local image: `papers/Dung_1995_AcceptabilityArguments/pngs/page-008.png`
- Modgil and Prakken 2014:
  - undercut attacks a specific defeasible inference/rule application
  - local image: `papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/pngs/page-009.png`
- Modgil and Prakken 2018:
  - last-link and weakest-link are distinct
  - local images:
    - `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-019.png`
    - `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-020.png`
- Hunter et al. 2021:
  - constellation approach distinguishes labelling probability, acceptance probability, extension probability
  - PrAF acceptance uses explicit inference mode: credulous or skeptical
  - notes anchor:
    - `papers/Hunter_2021_ProbabilisticArgumentationSurvey/notes.md`
- Popescu and Wallner 2024:
  - exact algorithmic support for extension probability and credulous argument acceptance
  - notes anchor:
    - `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md`
- Rago et al. 2016 KR:
  - original DF-QuAD uses intrinsic base scores
  - notes anchor:
    - `papers/Rago_2016_DiscontinuityFreeQuAD/notes.md`
- Rago et al. 2016 SAFA/COMMA:
  - BAF adaptation removes base scores and fixes neutral initialization at 0.5
  - notes anchor:
    - `papers/Rago_2016_AdaptingDFQuADBipolarArgumentation/notes.md`

## A1. Thread ASPIC+ `link` End-To-End

### Goal

Expose `last` vs `weakest` as a real public choice and prove it reaches the ASPIC bridge from every public path.

### Files allowed to change

- `propstore/world/types.py`
- `propstore/cli/worldline_cmds.py`
- `propstore/structured_argument.py`
- `propstore/world/resolution.py`
- `propstore/worldline_runner.py`
- tests only in:
  - `tests/test_render_contracts.py`
  - `tests/test_worldline.py`
  - `tests/test_resolution_helpers.py`
  - `tests/test_structured_argument.py`

### RED tests to add first

- `test_render_policy_serialization_roundtrip_preserves_link`
- `test_render_policy_defaults_link_is_last`
- `test_create_link_principle_flag`
- `test_worldline_definition_roundtrip_preserves_link`
- `test_aspic_resolution_threads_link_to_build_aspic_projection`
- `test_worldline_aspic_capture_threads_link_to_build_aspic_projection`
- `test_build_structured_projection_threads_link_to_aspic_bridge`

### Expected RED failure mode

- `RenderPolicy` has no `link`
- CLI rejects the new flag
- structured/worldline/resolution calls reach `build_aspic_projection()` without `link="weakest"`

### Implementation steps

1. Add `link: str = "last"` to `RenderPolicy`.
2. Add `link` handling to `from_dict()` / `to_dict()`.
3. Add CLI option:
   - name: `--link-principle`
   - choices: `last`, `weakest`
4. Persist it into worldline policy YAML.
5. Add `link` kwarg to `build_structured_projection()`.
6. Thread `link` through:
   - structured projection path
   - ASPIC resolution path
   - worldline ASPIC capture path

### Stop condition

- every RED test above is green
- defaults still serialize/roundtrip cleanly
- no caller silently falls back to `last` when `weakest` was selected

## A2. Stop Calling Custom Hybrid Semantics `grounded`

### Goal

Make `grounded` mean Dung grounded everywhere. Keep the existing attack-aware behavior only under an explicit non-Dung name.

### Files allowed to change

- `propstore/structured_argument.py`
- `propstore/world/resolution.py`
- optionally:
  - `propstore/cli/worldline_cmds.py`
  - `propstore/world/types.py`
- tests only in:
  - `tests/test_structured_argument.py`
  - `tests/test_worldline.py`
  - `tests/test_resolution_helpers.py`

### RED tests to add first

- `test_grounded_semantics_uses_plain_dung_grounded_even_when_attacks_exist`
- `test_hybrid_grounded_requires_explicit_opt_in`
- `test_worldline_grounded_does_not_alias_hybrid_grounded`
- `test_structured_resolution_grounded_uses_plain_grounded_extension`

### Expected RED failure mode

- current code returns `hybrid_grounded_extension()` for `semantics="grounded"` whenever `attacks is not None`

### Implementation steps

1. Change `compute_structured_justified_arguments()` so:
   - `grounded` always dispatches to `grounded_extension()`
2. Keep old behavior only as `hybrid-grounded`
3. Decide public exposure:
   - recommended: expose `hybrid-grounded` only if there is a real caller that needs it
   - otherwise keep it internal and remove the aliasing bug only
4. Update reason strings in resolution helpers so they never call a hybrid result "grounded"

### Stop condition

- no code path returns hybrid semantics when the public request was `grounded`
- any hybrid fallback is explicitly named

## A3. Make Undercuts Target A Specific Rule

### Goal

Stop translating an undercut against a claim into attacks on all defeasible rules with that conclusion.

### Files allowed to change

- `propstore/aspic_bridge.py`
- any stance/relation schema or validation files needed to carry the target rule id
- any active-graph extraction code needed to preserve that field
- tests only in:
  - `tests/test_aspic_bridge.py`
  - `tests/test_structured_argument.py`
  - validation tests only if schema enforcement is touched

### Required schema decision

Use one field name consistently. Recommended:

- `target_justification_id`

Do not support multiple synonymous field names unless migration requires it.

### RED tests to add first

- `test_undercut_targets_only_named_defeasible_rule`
- `test_undercut_without_rule_id_errors_when_multiple_target_rules_exist`
- `test_undercut_without_rule_id_uses_only_rule_when_target_is_unambiguous`
- `test_undercut_does_not_bleed_across_alternative_justifications_for_same_claim`

### Expected RED failure mode

- current code in `stances_to_contrariness()` undercuts every defeasible rule whose consequent matches the target literal

### Implementation steps

1. Add `target_justification_id` to stance/relation validation.
2. Preserve it in:
   - store-backed stance rows
   - active-graph relation extraction
3. In `stances_to_contrariness()`:
   - if `target_justification_id` exists, map only to that named defeasible rule
   - if exactly one matching defeasible rule exists and no identifier is given, use it
   - if multiple matching defeasible rules exist and no identifier is given, raise a clear error or skip with an explicit diagnostic
4. Do not guess among multiple rules.

### Stop condition

- adding a second defeasible justification for the same claim no longer creates extra undercuts
- ambiguous undercut data is rejected or surfaced explicitly

## B1. Split The PrAF API By Query Kind And Inference Mode

### Goal

Stop pretending there is one generic “acceptance probability” API when the papers distinguish:

- acceptance probability
- extension probability
- credulous vs skeptical inference mode

### Files allowed to change

- `propstore/praf.py`
- any callers in:
  - `propstore/world/resolution.py`
  - `propstore/worldline_runner.py`
  - analyzers if needed
- tests only in:
  - `tests/test_praf.py`
  - `tests/test_praf_integration.py`
  - worldline tests only if public CLI/API changes are exposed there

### Required naming decision

Use explicit names. Recommended internal/public vocabulary:

- `query_kind`
  - `argument_acceptance`
  - `extension_probability`
- `inference_mode`
  - `credulous`
  - `skeptical`

Do not keep plain overloaded `semantics` as the only selector for these distinctions.

### RED tests to add first

- `test_credulous_acceptance_matches_union_of_extensions_on_deterministic_af`
- `test_skeptical_acceptance_matches_intersection_of_extensions_on_deterministic_af`
- `test_extension_probability_queries_exact_set_not_single_argument`
- `test_exact_dp_rejects_or_downgrades_unsupported_skeptical_acceptance_mode`
- `test_query_kind_argument_acceptance_requires_inference_mode`
- `test_query_kind_extension_probability_rejects_inference_mode`

### Expected RED failure mode

- current code always computes a credulous-style singleton notion for preferred/stable/complete
- there is no way to ask for extension probability as a first-class query kind
- exact DP may be selected for modes it does not actually implement

### Implementation steps

1. Refactor `compute_praf_acceptance()` into an explicit query API.
2. Preserve current behavior only as:
   - `query_kind="argument_acceptance"`
   - `inference_mode="credulous"`
3. Add skeptical singleton support:
   - exact enumeration
   - Monte Carlo
4. Add extension probability for exact queried sets.
5. Restrict exact DP to the modes supported by the current literature/code:
   - extension probability
   - credulous argument acceptance
6. If a caller requests unsupported exact skeptical mode:
   - either reject clearly
   - or downgrade explicitly and record that downgrade in metadata
   - do not silently pretend exact DP handled it

### Stop condition

- union-of-extensions behavior is no longer exposed under an unnamed generic API
- query kind and inference mode are explicit in both code and metadata
- unsupported exact skeptical mode cannot slip through silently

## B2. Split DF-QuAD Into QuAD-Mode And BAF-Mode

### Goal

Remove the `P_A -> tau` conflation and expose the two literature-backed families separately.

### Files allowed to change

- `propstore/praf.py`
- `propstore/praf_dfquad.py`
- any callers or policy/config surfaces that select DF-QuAD mode
- tests only in:
  - `tests/test_dfquad.py`
  - `tests/test_praf.py`
  - relevant integration tests if public dispatch changes

### Required mode names

Use explicit names. Recommended:

- `dfquad_quad`
- `dfquad_baf`

Do not keep one overloaded `dfquad` mode with hidden semantics.

### RED tests to add first

- `test_dfquad_quad_requires_explicit_tau`
- `test_dfquad_baf_uses_fixed_neutral_0_5_for_isolated_arguments`
- `test_dfquad_quad_tau_varies_independently_of_praf_argument_probability`
- `test_dfquad_baf_does_not_read_praf_argument_probability_as_base_score`
- `test_dfquad_baf_isolated_argument_scores_0_5`
- `test_dfquad_quad_missing_tau_errors_cleanly`

### Expected RED failure mode

- current code reads `praf.p_args[arg].expectation()` as the base score input

### Implementation steps

1. Introduce two explicit DF-QuAD modes:
   - `dfquad_quad`
   - `dfquad_baf`
2. In `dfquad_quad`:
   - require explicit `tau`
   - error if `tau` is missing
3. In `dfquad_baf`:
   - initialize every isolated argument at neutral `0.5`
   - do not read PrAF argument existence probability as base score
4. Keep `P_A` only as constellation existence probability.
5. Update dispatch metadata so the chosen DF-QuAD family is visible to callers.

### Stop condition

- `P_A` is never used as `tau`
- QuAD-style and BAF-style DF-QuAD are distinct, named modes
- missing `tau` errors only in QuAD mode

## Property Tests To Add After The Regression Tests Are Green

These are not phase-1 RED tests. Add them only after the corresponding regression tests are passing.

### ASPIC `link` properties

- End-to-end threading property:
  - any selected `link` value reaches the bridge unchanged from all public entry points

### Structured grounded properties

- For any projection, `semantics="grounded"` equals `grounded_extension(projection.framework)`

### Undercut locality properties

- Adding an unrelated defeasible rule with the same conclusion does not create new undercuts
- Adding a named target rule undercut only affects that rule's attacks/defeats

### PrAF query semantics properties

- skeptical acceptance probability for an argument is never greater than credulous acceptance probability
- extension probability over all candidate queried sets is bounded in `[0,1]`
- deterministic AF special case:
  - credulous singleton matches union-of-extensions membership
  - skeptical singleton matches intersection-of-extensions membership

### DF-QuAD separation properties

- in QuAD mode, changing `P_A` alone does not change the output if `tau` is fixed
- in QuAD mode, changing `tau` with fixed topology and fixed `P_A` changes the output
- in BAF mode, isolated arguments evaluate to `0.5`

## Commands By Phase

These are suggested focused test runs.

### Phase A1

```powershell
uv run pytest -vv tests/test_render_contracts.py tests/test_worldline.py tests/test_resolution_helpers.py tests/test_structured_argument.py
```

### Phase A2

```powershell
uv run pytest -vv tests/test_structured_argument.py tests/test_worldline.py tests/test_resolution_helpers.py
```

### Phase A3

```powershell
uv run pytest -vv tests/test_aspic_bridge.py tests/test_structured_argument.py
```

### Phase B1

```powershell
uv run pytest -vv tests/test_praf.py tests/test_praf_integration.py
```

### Phase B2

```powershell
uv run pytest -vv tests/test_dfquad.py tests/test_praf.py
```

### Final accumulated run

```powershell
uv run pytest -vv tests/test_render_contracts.py tests/test_worldline.py tests/test_resolution_helpers.py tests/test_structured_argument.py tests/test_aspic_bridge.py tests/test_praf.py tests/test_praf_integration.py tests/test_dfquad.py
```

## Explicit Non-Goals

- Do not solve correlated PrAF dependencies in this plan.
- Do not solve cyclic DF-QuAD semantics in this plan.
- Do not add skeptical exact-DP support unless the implementation and tests are real.
- Do not collapse QuAD-mode and BAF-mode back into one overloaded switch after the refactor.

## Completion Checklist

The plan is complete only when all boxes below are true:

- [ ] `link` exists in public policy serialization
- [ ] `link` is selectable from CLI/worldline surfaces
- [ ] `link` reaches ASPIC bridge from every public call path
- [ ] `grounded` means Dung grounded everywhere
- [ ] hybrid fallback is explicitly named or removed from public surface
- [ ] undercuting is rule-specific, not conclusion-wide
- [ ] ambiguous undercut data is surfaced explicitly
- [ ] PrAF query kind is explicit
- [ ] PrAF inference mode is explicit
- [ ] exact DP is limited to supported query modes
- [ ] credulous and skeptical acceptance are separate
- [ ] extension probability is separate from argument acceptance
- [ ] `P_A` is never treated as `tau`
- [ ] `dfquad_quad` and `dfquad_baf` are separate named modes
- [ ] QuAD mode requires explicit `tau`
- [ ] BAF mode uses neutral `0.5`
- [ ] all focused test slices are green
- [ ] final accumulated run is green

## Source Record

- Local paper anchors:
  - `papers/Dung_1995_AcceptabilityArguments/pngs/page-008.png`
  - `papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/pngs/page-009.png`
  - `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-019.png`
  - `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-020.png`
  - `papers/Hunter_2021_ProbabilisticArgumentationSurvey/notes.md`
  - `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md`
  - `papers/Rago_2016_DiscontinuityFreeQuAD/notes.md`
  - `papers/Rago_2016_AdaptingDFQuADBipolarArgumentation/notes.md`
