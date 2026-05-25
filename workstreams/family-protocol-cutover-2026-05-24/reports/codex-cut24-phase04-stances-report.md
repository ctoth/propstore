# Phase 04 Stances Report

## Workflow Used

Read and executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut24-phase04-stances.md` until its H-A hard-stop fired.

## Outcome

Blocked by H-A. I did not author `propstore/families/stances/declaration.py`, did not delete `propstore/families/documents/stances.py`, did not regenerate the contract manifest, did not run the gates, and did not create the implementation commit.

## Hard-Stop

The prompt requires the generated stance charter to use:

- `strength` as `float` (`codex-cut24-phase04-stances.md:18`)
- `conditions_differ` as `bool` (`codex-cut24-phase04-stances.md:20`)

But current consumers and adjacent family declarations still expect the old string-valued stance shape:

- `propstore/families/documents/stances.py:17` has `strength: str | None`
- `propstore/families/documents/stances.py:19` has `conditions_differ: str | None`
- `propstore/families/documents/sources.py:432` has source stance `strength: str | None`
- `propstore/families/documents/sources.py:434` has source stance `conditions_differ: str | None`
- `propstore/families/claims/documents.py:438` has inline claim stance `conditions_differ: str | None`
- `propstore/families/relations/declaration.py:137` declares relation `strength` as `str`
- `propstore/families/relations/declaration.py:138` declares relation `conditions_differ` as `str`
- `propstore/source/promote.py:358` forwards `stance.strength` into the canonical stance document
- `propstore/source/promote.py:360` forwards `stance.conditions_differ` into the canonical stance document
- `propstore/families/relations/declaration.py:280-281` forwards those fields into relation rows
- `propstore/families/relations/declaration.py:413-414` forwards those fields into relation rows
- `tests/test_classify.py:369-371` samples stance strengths from `"strong"`, `"moderate"`, and `"weak"`
- `tests/test_claim_workflows.py:156` uses `"strength": "strong"`
- `tests/test_build_sidecar.py:914` uses `"strength": "strong"`

This is exactly the prompt's H-A condition:

> A consumer expects the OLD `propstore.families.documents.stances.StanceDocument` shape that the generated document can't match. Halt; report.

## Notes

The audit/prompt field count is internally inconsistent: the audit text says 12 CharterFields but enumerates 13 payload fields, and the prompt adds the `id` / `artifact_id` primary key, for 14 total fields. That inconsistency did not become the active blocker; the active blocker is the requested `float`/`bool` generated shape conflicting with current string-valued consumers.
