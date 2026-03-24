# Review Fixes Session Notes

## CURRENT TOPIC: Unit-Aware Propagation Design

### Forms Directory Investigation
- `C:\Users\Q\code\propstore\forms\` — 37 seed form YAMLs with `common_alternatives` + multipliers. Used by `pks init` to seed new knowledge bases.
- `C:\Users\Q\code\propstore\knowledge\forms\` — 16 form YAMLs, the ACTUAL forms the build uses. No multipliers. This is `repo.forms_dir`.
- `Repository._root` = `C:\Users\Q\code\propstore\knowledge\` (confirmed from repository.py docstring + line 19)
- `repo.forms_dir` = `C:\Users\Q\code\propstore\knowledge\forms\` (line 36)
- The seed directory at `C:\Users\Q\code\propstore\forms\` is ONLY referenced by `pks init` (init.py:25)
- **The conversion multipliers are in the seed forms but NOT in the knowledge base forms.** Either `pks init` strips them during copy, or the seed forms were enriched after init ran.

### Implication for Unit Design
The multipliers need to be in `C:\Users\Q\code\propstore\knowledge\forms\` (the actual forms dir) for propagation to use them. Either:
- Update `pks init` to copy `common_alternatives` into knowledge forms
- Or add multipliers to `C:\Users\Q\code\propstore\knowledge\forms\` directly

### StrEnum Fix
- Completed. Commit `987d822`. 1022 passed.

## STATUS
- All 27 fixes complete (26 review + 1 StrEnum)
- Design discussion with Q on unit-aware propagation in progress
- Q wants gauge scalars and offsets handled, not just multiplicative
