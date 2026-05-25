# Codex Cut 36 Phase 06 Report

## Workflow actually used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut36-phase06.md`
against HEAD `9dcb7f96` on `master`.

Result: **PARTIAL under H-D**. I halted before source edits because Phase 06's
required replacement owner, generic lifecycle transition execution over typed
family records, is not present as callable Quire/Propstore runtime code.

## Reads completed

- `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut36-phase06.md`
- `workstreams/family-protocol-cutover-2026-05-24/06-source-lifecycle-state-machines.md`
- `workstreams/family-protocol-cutover-2026-05-24/reports/scout-field-ownership-violations.md`
- `propstore/source/status.py`
- `propstore/source/claim_concepts.py`
- `propstore/source/claims.py`
- `propstore/source/relations.py`
- `propstore/source/common.py`
- `propstore/source/stages.py`
- `propstore/source/alignment.py`
- `propstore/source/concepts.py`
- `propstore/source/promote.py`
- `propstore/source/finalize.py`
- `propstore/source/registry.py`
- `propstore/source/reference_indexes.py`
- `propstore/families/registry.py`
- `propstore/families/claims/declaration.py`
- `propstore/families/claims/references.py`
- `propstore/families/identity/claims.py`
- `workstreams/family-protocol-cutover-2026-05-24/reports/codex-cut35-phase05-full-report.md`

## H-D evidence

Phase 06 target requires source-local authoring, finalization, promotion,
status, and alignment to become lifecycle transitions over typed family records.
The concrete replacement is not available yet:

- `workstreams/family-protocol-cutover-2026-05-24/02-quire-generated-family-protocols.md`
  lists "Implement generic lifecycle transition metadata and execution" as a
  prerequisite.
- `reports/charter-cutover-breakdown/quire-prereqs-report.md` states that
  current Quire carries lifecycle states as metadata only and has no transition
  execution hits under `../quire/quire` or `../quire/tests`.
- Current repo searches for `generic lifecycle` and `lifecycle transition`
  found workstream/report references, CLI labels, tests, and unrelated journal
  code, but no generic Quire/Propstore transition executor for source-local to
  canonical family records.
- `propstore/source/stages.py::SourcePromotionPlan` still carries concrete
  document-class maps, and `propstore/source/promote.py::_assemble_source_promotion_plan`
  still constructs that concrete plan. Replacing it correctly requires the
  missing generic transition execution owner; moving the same behavior to a new
  root helper would violate the no-shim/no-alias directive.

## Baseline deletion-target state

The first Phase 06 deletion target is already removed in the current checkout:

```powershell
rg -n -F -- 'derived.schema.table("claim_core")' propstore/source propstore tests
```

returned no hits.

The remaining Phase 06 gates are still nonzero before implementation. Examples:

```powershell
rg -n -F -- "ClaimDocument | SourceClaimDocument | Mapping" propstore/source propstore tests
```

returns `propstore/source/claim_concepts.py:18`.

```powershell
rg -n -F -- "SourcePromotionPlan" propstore tests workstreams/family-protocol-cutover-2026-05-24/reports
```

returns `propstore/source/stages.py`, `propstore/source/promote.py`, and the
scout report.

```powershell
rg -n -F -- "from propstore.families.documents" propstore/source
```

returns source-module imports in `claim_concepts.py`, `claims.py`, `concepts.py`,
`common.py`, `promote.py`, `finalize.py`, `reference_indexes.py`,
`registry.py`, `relations.py`, and `stages.py`.

## Disposition

No source code was changed. The prompt's H-D hard-stop applies before any safe
Phase 06 deletion can replace concrete document plans, source relation payload
normalization, concept projection dictionaries, or root alignment workflow shape
with the requested typed family-record lifecycle transition owner.

No gates were run after edits because there were no source edits.

## Remaining work

Implement the missing Quire-side generic lifecycle transition execution
capability, then rerun Phase 06 from the same prompt. The first source slice
after that prerequisite exists should delete `SourcePromotionPlan`'s concrete
document maps and drive promotion through typed family-record transition plans,
then use the Phase 06 search gates as the fixed-point queue for the remaining
source helper deletions.
