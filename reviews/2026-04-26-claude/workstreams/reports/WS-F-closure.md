# WS-F Closure Report

Workstream: WS-F ASPIC+ bridge fidelity
Closing code commit: `c8b0c892`

## Findings Closed

- T2.1 / Codex #22 / Cluster D HIGH-2: directional stances now preserve asymmetric contrariness.
- T2.9 / Codex #12: ASPIC grounded/direct/incomplete grounded use attack-aware handling.
- T5.7 / Cluster D HIGH-5: private `_contraries_of` imports are gone.
- Cluster D HIGH-1 / LOW-18: transposition closure uses full contrariness and the upstream post-closure language.
- Cluster D HIGH-3: democratic premise ordering respects the comparison knob for Pareto-incomparable metadata vectors.
- Cluster D HIGH-4: defeater rules can target named rules and emit undercutters.
- Cluster D HIGH-6: `arguments_against` covers rebut, undermine, and undercut attackers.
- Cluster D HIGH-7: projection preserves attacks and defeats independently and rejects unprojected relation endpoints.
- Codex #13 / #21: advertised ASPIC `complete`, `aspic-direct-grounded`, and `aspic-incomplete-grounded` are executable.
- Codex #14: `praf-paper-td-complete` routes to `paper_td` extension-probability queries.
- Codex #36 bridge dimension: duplicate canonical concept names do not collapse ASPIC claim literals.

## TDD Evidence

- Red test log `logs/test-runs/WS-F-red-20260429-004517.log`: collection failed on private `_contraries_of`, proving the public upstream API prerequisite was absent before the pin bump.
- Target log `logs/test-runs/WS-F-target-20260429-004836.log`: the first WS-F bridge tests passed after the core implementation.
- Existing-coverage red/green logs:
  - `logs/test-runs/WS-F-aspic-existing-20260429-004929.log`: stale ASPIC expectations failed after the semantics correction.
  - `logs/test-runs/WS-F-aspic-existing-20260429-005316.log`: corrected existing ASPIC suite passed.
- Additional WS-F tightening:
  - `logs/test-runs/WS-F-praf-routing-20260429-010011.log`: PrAF paper-TD routing tests passed.
  - `logs/test-runs/WS-F-coverage-tightening-20260429-010409.log`: undercut/undermine `arguments_against` and canonical-name literal identity tests passed.
  - `logs/test-runs/WS-F-properties-20260429-010940.log`: WS-F property gates passed.

## Property Gates

- `test_strict_rule_closure_is_monotone_when_strict_rules_are_added`: generated strict-rule additions preserve prior strict closure.
- `test_generated_preference_cases_can_have_attack_without_defeat`: generated preference-filtered examples preserve attacks without forcing matching defeats.
- `test_alpha_renaming_rule_ids_preserves_claim_acceptance`: alpha-renaming rule ids that preserve rule identity does not change accepted claim ids.
- Existing `tests/test_aspic_bridge.py` property suite still gates projection endpoint validity, defeat endpoint validity, defeat-implies-attack, attack-based conflict-freeness, subargument closure, and direct consistency.

## Upstream Dependency

- Upstream `../argumentation` commits:
  - `5fbd3c9` added red public-API tests.
  - `bbfa7ef1db1d5db376f048d5bf789760923db9d4` implemented `transposition_closure(...) -> (closed_rules, post_closure_language)` and public `contraries_of`.
- Upstream was pushed to `origin/main`.
- Propstore remote Git pin was bumped in `pyproject.toml` and `uv.lock`; no local repository pin was introduced.

## Files Changed

- `propstore/aspic_bridge/build.py`
- `propstore/aspic_bridge/grounding.py`
- `propstore/aspic_bridge/projection.py`
- `propstore/aspic_bridge/query.py`
- `propstore/aspic_bridge/translate.py`
- `propstore/structured_projection.py`
- `propstore/world/types.py`
- `propstore/core/analyzers.py`
- `propstore/app/world_reasoning.py`
- `propstore/worldline/argumentation.py`
- `tests/test_ws_f_aspic_bridge.py`
- ASPIC existing tests adjusted to the corrected stance semantics.

## Validation Logs

- `uv run pyright propstore`: 0 errors, 0 warnings.
- `uv run lint-imports`: 4 contracts kept, 0 broken.
- `logs/test-runs/WS-F-aspic-existing-20260429-010521.log`: 135 passed.
- Full-suite log: to be added after the final full logged run.

## Remaining Risks / Successors

- T2.11 remains out of scope for WS-F and belongs to the argumentation package stream.
- Registry-level duplicate canonical-name rejection is not closed here; WS-F only proved the ASPIC bridge does not collapse two distinct claim ids that share a canonical concept name.
- Runtime preflight for arbitrary user-authored c-consistency remains a successor, not part of the WS-F closure.
