# codex-cut9-phase04-pilot-single-family report

Workflow actually used: `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut9-phase04-pilot-single-family.md`.

## Outcome

Hard-stop: H-A.

No family document file was deleted and no importer was updated. The pilot selected the smallest candidate, `forms`, but `propstore/families/forms/declaration.py` has only the iterable `FORMS_CHARTERS`, not a named individual charter constant for the `FormDocument` document shape. The prompt says to halt under H-A when the chosen family's declaration has no `<FAMILY>_CHARTER` named-individual constant.

## Family chosen

Candidate line counts:

```text
609 propstore/families/claims/documents.py
 87 propstore/families/concepts/documents.py
 68 propstore/families/contexts/documents.py
 30 propstore/families/forms/documents.py
 31 propstore/families/sameas/documents.py
```

`forms` was chosen because it is the smallest candidate.

## Inventory

`propstore/families/forms/documents.py` public classes:

- `FormAlternativeDocument`
- `FormExtraUnitDocument`
- `FormDocument`

Public methods: none.

Constants: none.

`FormDocument` fields:

- `name`
- `dimensionless`
- `base`
- `unit_symbol`
- `qudt`
- `parameters`
- `common_alternatives`
- `delta_alternatives`
- `kind`
- `note`
- `dimensions`
- `extra_units`
- `min`
- `max`

`propstore/families/forms/declaration.py` charter evidence:

- `rg -n -F -- "CHARTER" propstore/families/forms/declaration.py` returned only `13:FORMS_CHARTERS: tuple[FamilyCharter, FamilyCharter] = (`.
- I did not find a named individual charter constant such as `FORM_CHARTER` or `FORMS_CHARTER`.

The available charter fields also do not cover the handwritten document shape: the `form` charter uses fields such as `is_dimensionless` and `dimensions`, while the handwritten document has fields such as `dimensionless`, `base`, `qudt`, `parameters`, `common_alternatives`, `delta_alternatives`, `note`, `extra_units`, `min`, and `max`.

## Importers found

Search command:

```powershell
rg -n -F -- "FormDocument" propstore tests
```

Relevant handwritten `FormDocument` importers/usages found:

- `tests/test_artifact_identity_policy.py`
- `propstore/contracts.py`
- `propstore/app/forms.py`
- `propstore/app/project_init.py`
- `tests/test_concept_alignment_cli.py`
- `propstore/families/registry.py`
- `propstore/families/forms/__init__.py`
- `propstore/families/forms/stages.py`
- `propstore/_resources/contract_manifests/semantic-contracts.yaml`
- `tests/test_lemon_concept_documents.py`

None were updated because H-A requires halting before conversion.

## Methods and validators

No custom public methods or validators exist on the selected handwritten document classes. Nothing was converted, so no method survived or failed to survive the conversion.

## Gates

Not run. The prompt requires halting under H-A before edits when no named individual charter constant exists for the chosen family.

## Downstream recommendation

Phase 04 cannot pilot `forms` until the family declaration exposes a named individual charter for the document shape and that charter covers every persisted document field. This looks like charter-authoring work before document deletion work.

Based only on the line-count pass required by this prompt, `sameas` is the next smallest candidate at 31 lines. I did not read `sameas/declaration.py` during this halted pilot, so I do not know whether it has the required named individual charter or complete field coverage.
