# Family Document Family-Generation Cleanup

Date: 2026-05-27

## Target

All persisted/source IO `*Document` shapes come from family charters through
`FamilyCharter.generated_document()` or an equivalent Quire-generated family
document API. Hand-written `msgspec.Struct` or `DocumentStruct` classes do not
own persisted/source IO shape.

This workstream grounds out in the installed CLI:

```powershell
uv tool install --upgrade --force .
pks init "$env:TEMP\propstore-pks-cli-smoke-20260527-family-docs"
```

## Current Inventory

### Deleted old package

- `propstore/families/documents/__init__.py` deleted.
- `propstore/families/documents/sources.py` deleted.
- Remaining references to `propstore.families.documents` are forbidden and must
  go to zero.

### Regression introduced during deletion repair

These were moved into owner modules as hand-written documents and must be
converted to charter-generated family documents, not kept:

- `propstore/families/sources/declaration.py`: `SourceOriginDocument`,
  `SourceTrustQualityDocument`, `SourceTrustDocument`,
  `SourceMetadataDocument`, `SourceParameterizationGroupMergeDocument`,
  `SourceFinalizeCalibrationDocument`, `SourceFinalizeReportDocument`.
- `propstore/families/concepts/declaration.py`: `SourceConceptAliasDocument`,
  `SourceConceptRegistryMatchDocument`,
  `SourceConceptFormParametersDocument`,
  `SourceParameterizationRelationshipDocument`.
- `propstore/families/claims/declaration.py`: `ExtractionProvenanceDocument`,
  `SourceProvenanceDocument`, `SourceAttackTargetDocument`.

### Existing hand-written document shapes

These predate this slice and violate the same target unless proven to be
non-persisted semantic value objects with a different name:

- `propstore/families/forms/declaration.py`: `FormAlternativeDocument`,
  `FormExtraUnitDocument`.
- `propstore/families/worldlines/declaration.py`: `Worldline*Document`
  helper shapes.
- `propstore/families/micropublications/declaration.py`:
  `MicropublicationEvidenceDocument`.
- `propstore/families/contexts/declaration.py`: `ContextReferenceDocument`.
- `propstore/families/merge/declaration.py`: merge manifest helper document
  shapes and custom generated-document implementation.
- `propstore/families/predicates/declaration.py`: predicate payload structs.
- `propstore/families/source_alignment/declaration.py`: alignment helper
  document shapes.
- `propstore/families/rules/declaration.py`: rule payload structs.
- `propstore/families/concepts/declaration.py`: concept nested document
  structs.
- `propstore/families/claims/declaration.py`: claim nested document structs,
  proposition document structs, and justification nested document structs.
- `propstore/repository.py`: `RepositoryConfigDocument`.
- `propstore/provenance/__init__.py`: `_NamedGraphDocument`.

## Checklist

### Phase 1 - Restore CLI by fixing the source-local regression

- [x] Replace source value/report hand-written documents with generated
  charter documents in `propstore/families/sources/declaration.py`.
- [x] Replace source concept nested hand-written documents with generated
  charter documents in `propstore/families/concepts/declaration.py`.
- [x] Replace source claim/justification nested hand-written documents with
  generated charter documents in `propstore/families/claims/declaration.py`.
- [x] Reroute all production imports away from `propstore.families.documents`.
- [x] Regenerate/update contract manifest entries that still name
  `propstore.families.documents`.
- [x] Run `uv run pyright propstore`.
- [x] Reinstall and smoke the real CLI with `pks init`.

### Phase 2 - Existing family nested document cleanup

- [ ] Convert claims nested/proposition/justification helper documents to
  generated family documents or non-document semantic value objects.
- [ ] Convert concepts nested helper documents to generated family documents or
  non-document semantic value objects.
- [ ] Convert forms nested helper documents.
- [ ] Convert contexts nested helper documents.
- [ ] Convert rules, predicates, micropublications, merge, source-alignment,
  worldline, provenance, and repository config helper documents.

### Phase 3 - Fixed point

- [ ] `rg -n "class .*Document\\b.*msgspec\\.Struct|class .*Document\\b.*DocumentStruct" propstore` has zero production hits, or each remaining hit is renamed because it is not persisted/source IO shape.
- [ ] `rg -n -F "propstore.families.documents" propstore tests` has zero hits.
- [ ] `uv run pyright propstore` passes.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label family-doc-family-generation tests/test_contract_manifest.py tests/test_source_claims.py tests/test_source_relations.py tests/test_verify_cli.py` passes.
- [ ] `uv tool install --upgrade --force .` succeeds.
- [ ] `pks init "$env:TEMP\propstore-pks-cli-smoke-20260527-family-docs"` succeeds.

## Execution Notes

- Do not recreate `propstore.families.documents`.
- Do not move hand-written `*Document` classes under new owner files as the
  final state.
- Add charters/families first only when they replace a deleted hand-written
  shape with `generated_document()`.
- Commit each kept reduction before moving to another file.
