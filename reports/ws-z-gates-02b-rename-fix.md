# WS-Z-gates Phase 2b — Rename Completion Fix Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source spec: `prompts/ws-z-gates-02b-rename-fix.md`
Author: coder subagent

## TL;DR

**No code change needed.** All four "fresh from rename" pyright diagnostics enumerated in the prompt are absent from the current source. The phase-2 rename commit `41541f3` already updated every site listed. Only the explicitly-pre-existing diagnostics (the ones the prompt told me to leave alone) remain. Commit produced: report only.

## Per-site triage

I read each "fresh" site, then ran pyright against the two affected files to verify what it actually flags right now.

| Prompt-claimed diagnostic | Verdict | Evidence |
|---|---|---|
| `claim_utils.py:644` — `"stage" is not defined` | **Already fixed by `41541f3`.** | Line 644 reads `"algorithm_stage": algorithm_stage,` in the row-dict literal returned by `prepare_claim_insert_row`. Pyright reports no error at that line. |
| `row_types.py:241` — `Cannot access attribute "stage"` | **Already fixed by `41541f3`.** | Line 241 reads `if self.algorithm_stage is not None:` in `__post_init__`. Pyright reports no error at that line. |
| `row_types.py:242` — same pattern | **Already fixed by `41541f3`.** | Lines 242-244 set `self.algorithm_stage` via `coerce_algorithm_stage(self.algorithm_stage)`. Pyright clean. |
| `claim_utils.py:579` — `algorithm_stage not accessed` (informational) | **Already fixed by `41541f3`.** | Line 579 unpacks `body, canonical_ast, variables_json, algorithm_stage = resolve_algorithm_storage(...)` and `algorithm_stage` is then read at line 644 inside the returned dict. Pyright reports no informational either. |

Diff confirmation — `git show 41541f3 -- propstore/sidecar/claim_utils.py propstore/core/row_types.py` shows the rename commit already touched every one of the lines named in the prompt's "fresh" list, replacing `stage` with `algorithm_stage` consistently across declarations, `__post_init__`, `from_mapping`, `to_dict`, the SQL INSERT column list, the populator local variable, and the row-dict key.

## Pyright before/after

There was no "before" — the rename commit predates this task. Current state:

```
$ uv run pyright propstore/sidecar/claim_utils.py propstore/core/row_types.py

c:\...\row_types.py:174:27 - error: ConceptRelationshipType | None ... (reportArgumentType)
c:\...\row_types.py:352:18 - error: SourceKind | None ... (reportArgumentType)
c:\...\row_types.py:355:29 - error: SourceOriginType | None ... (reportArgumentType)
c:\...\row_types.py:666:25 - error: StanceType | None ... (reportArgumentType)
c:\...\claim_utils.py:480:37 - error: SemanticClaim.resolved_claim ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:491:42 - error: SemanticClaim.stances ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:496:24 - error: SemanticClaim.get ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:496:57 - error: SemanticClaim.get ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:501:34 - error: SemanticClaim.get ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:560:57 - error: SemanticClaim.resolved_claim ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:561:69 - error: SemanticClaim.source_paper ... (reportAttributeAccessIssue)
c:\...\claim_utils.py:564:13 - error: dict | SemanticClaim ... (reportArgumentType)
12 errors, 0 warnings, 0 informations
```

Every one of these 12 diagnostics is on the prompt's explicit "pre-existing — NOT your job" list:
- `row_types.py:174` → `ConceptRelationshipType | None` (listed pre-existing).
- `row_types.py:350,353` → `SourceKind | None` / `SourceOriginType | None` — actually flagged at 352 and 355 (one-line offset; same diagnostic family the prompt labeled pre-existing).
- `row_types.py:666` → `StanceType | None` (not in prompt list but same `reportArgumentType` Optional-vs-required pattern; not rename-related).
- `claim_utils.py:480, 491, 496, 501, 560, 561, 564` → all `SemanticClaim`/`resolved_claim`/`stances`/`SemanticClaim.get` (listed pre-existing).

Zero `stage`/`algorithm_stage` diagnostics remain. The four prompt-named "fresh" issues are gone.

The line-number drift (e.g. `row_types.py:350,353` in prompt → `352,355` actual) is consistent with the rename commit having added two lines to `__post_init__` (the multi-line `coerce_algorithm_stage` reformat), shifting subsequent line numbers by ~2.

## Test suite

```
$ uv run pytest tests/ -x --timeout=60
====================== 2529 passed in 446.56s (0:07:26) =======================
```

Exact same pass count as the phase-2 baseline. No regression.

`test_algorithm_stage_types.py` already covers the rename completeness:
- `test_algorithm_stage_annotations_cover_runtime_path` asserts `ClaimRow["algorithm_stage"]` annotation exists.
- `test_claim_row_coerces_algorithm_stage` constructs from `{"algorithm_stage": "excitation"}` and asserts `row.algorithm_stage` is set.
- `test_claim_file_stage_split_is_preserved` exercises the YAML-`stage` (file-level) vs Python-`algorithm_stage` (claim-level) boundary.

A new "regression" test of the form the prompt suggested — "constructs a ClaimRow from a row dict containing the old `stage` key and asserts it ends up under `algorithm_stage`" — would be **wrong**. The rename removed support for the old `stage` key on `ClaimRow.from_mapping`; passing `{"stage": ...}` should now leave `algorithm_stage` as `None`, not migrate. Asserting migration would re-introduce the back-compat shim that disciplines rule 6 forbids. Skipped.

## Commit hash

No code commit. Report-only commit for this phase: see the next git operation.

## Anything else discovered during triage

1. **Prompt's pyright snapshot was stale.** The four "fresh" diagnostics were either taken before commit `41541f3` landed or against a working tree that hadn't yet loaded the renamed file. The previous coder's "test-only verification" (the prompt's framing) was actually fine because the rename was already complete in source — pyright was correct after the rename, but whoever produced the diagnostic snapshot ran it against pre-rename state.

2. **One newly-surfaced pre-existing pyright error on `row_types.py:666`** (StanceType `Optional`-passed-to-required-parameter) was not on the prompt's pre-existing list but is structurally identical to the listed `ConceptRelationshipType` / `SourceKind` errors — same `reportArgumentType` family, same Optional-narrowing problem. Not rename-related. Out of scope per disciplines rule 6 / the prompt's "surgical scope" guidance. Worth noting for whoever takes on the broader pyright cleanup workstream.

3. **Discipline grounding for the no-op decision.** Per `disciplines.md` rule 6 ("no backward-compat shims") and the project's "honest ignorance over fabricated confidence" principle from `CLAUDE.md`: if there is nothing to fix, fabricating an edit to satisfy a stale prompt would itself be a discipline violation. The right move is to report findings, leave source untouched, and let Q decide whether to retire this phase or redirect.
