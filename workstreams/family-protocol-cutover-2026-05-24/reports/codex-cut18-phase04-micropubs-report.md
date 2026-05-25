# Cut 18 Phase 04 Micropubs Report

## Workflow Used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut18-phase04-micropubs.md` through hard-stop H-A.

## Outcome

Halted before implementation.

The audit's micropubs recommendation requires a design call for the behavior-bearing invariant on `MicropublicationDocument.__post_init__`: the handwritten document rejects an empty `claims` tuple, but `FamilyCharter.generated_document()` in the pinned Quire dependency emits a plain strict `msgspec.Struct` and does not expose a charter-level document validator or invariant hook.

## Evidence Read

- `workstreams/family-protocol-cutover-2026-05-24/reports/scout-phase04-field-coverage-audit.md` section 3.8: micropubs is `NEEDS-AUGMENTATION`, with missing `version_id`, four name/type alignments, JSON-bound fields, and behavior-bearing `MicropublicationDocument.__post_init__`.
- `propstore/families/documents/micropubs.py`: `MicropublicationDocument.__post_init__` raises `ValueError` when `claims` is empty.
- `propstore/families/micropublications/declaration.py`: imports the handwritten `MicropublicationDocument`, declares `MICROPUBLICATION_CHARTERS`, and compiles micropublication claim links from `micropub.claims`.
- `.venv/Lib/site-packages/quire/charters.py`: `FamilyCharter.generated_document()` calls `msgspec.defstruct(..., forbid_unknown_fields=True)` from generated fields; no validation hook was present in the read implementation.

## Gates

Not run. The prompt's H-A hard-stop applies before implementation and before pyright/test gates.

## Done Condition

Not complete.

- `propstore/families/documents/micropubs.py` was not deleted.
- `MICROPUBLICATION_CHARTER` was not augmented.
- Importers were not updated.
- Contract manifest was not regenerated.
- No micropubs cutover commit was created.

## Required Decision

Choose the owned invariant surface before this cutover can proceed:

- Add a Quire-supported generated-document validation/invariant mechanism and encode non-empty `claims` there.
- Or explicitly accept moving the non-empty check out of the generated document constructor into a boundary/owner-layer validation step, which changes the current direct `convert_document_value(..., MicropublicationDocument, ...)` behavior.
