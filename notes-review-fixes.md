# Session Notes — Unit-Aware Propagation

## GOAL
Wire unit conversion through propstore's propagation system. f64. Handle multiplicative, affine, logarithmic conversions.

## ARCHITECTURE (finally understood)
- `C:\Users\Q\code\propstore\` = propstore tool source repo
- `C:\Users\Q\code\propstore\knowledge\` = a propstore PROJECT (data managed by the tool, not part of it)
- `C:\Users\Q\code\propstore\propstore\_resources\forms\` = canonical form definitions shipped with the package (just moved here from root forms/)
- `C:\Users\Q\code\propstore\knowledge\forms\` = user's project forms (seeded by pks init from _resources)
- Conversion multipliers are in `_resources/forms/` YAML `common_alternatives`

## PLAN (approved)
- Phase 1: UnitConversion dataclass + normalize_to_si in form_utils.py — DISPATCHED, running
- Phase 2: Wire into param_conflicts.py
- Phase 3: Wire into value_comparison.py
- Phase 4: Add affine/logarithmic examples to YAML
- Phase 5: value_si column in sidecar

## STATUS
- Phase 1 agent running (strict TDD)
- Phases 2-5 prompts not yet written

## PREVIOUS WORK (this session)
- 27 review fixes complete (26 planned + StrEnum)
- Forms moved to _resources (commit 7d9688a)
- 1022 tests passing
