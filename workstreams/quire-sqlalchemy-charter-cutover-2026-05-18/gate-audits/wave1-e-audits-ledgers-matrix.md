# Wave 1-E Gate Audit: Audits, Ledgers, Matrix

Date: 2026-05-21

## Scope

Files audited:

- `charter-field-metadata-spec-2026-05-20.md`
- `coercion-compatibility-audit-2026-05-20.md`
- `duplicate-definition-audit-2026-05-20.md`
- `helper-ledger.md`
- `inventory-matrix.md`

I did not use `git log`. I did not run pyright or pytest. I did not edit
source code.

## Workdirs Used

- Propstore gates were run from `C:\Users\Q\code\propstore`.
- Quire gates with `quire tests` paths were run from `C:\Users\Q\code\quire`.

## Commands Run

Literal `rg` gates extracted from the audited files and run from Propstore:

```powershell
rg -n -F -- "legacy" propstore tests
rg -n -F -- "backward compat" propstore tests
rg -n -F -- "backwards compat" propstore tests
rg -n -F -- "compat shim" propstore tests
rg -n -F -- "fallback" propstore tests
rg -n -F -- "from_row_mapping" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
rg -n -F -- "ConceptInput" propstore tests
rg -n -F -- "ParameterizationInput" propstore tests
rg -n -F -- "ActiveClaimInput" propstore tests
rg -n -F -- "coerce_active_claim" propstore tests
rg -n -F -- "coerce_active_claims" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL.coerce" propstore tests
rg -n -F -- "CONFLICT_ROW_MODEL.coerce" propstore tests
rg -n -F -- "STANCE_ROW_MODEL.coerce" propstore tests
rg -n -- "\bcoerce_[A-Za-z0-9_]+" propstore tests
rg -n -F -- "prepare_claim_insert_row" propstore tests
rg -n -F -- "canonicalize_claim_for_storage" propstore tests
rg -n -F -- "normalize_claim_file_payload" propstore tests
rg -n -F -- "normalize_canonical_claim_payload" propstore tests
rg -n -F -- "normalize_canonical_concept_payload" propstore tests
rg -n -F -- "normalize_source_claims_payload" propstore tests
rg -n -F -- 'metadata={"coerce"' propstore tests
rg -n -F -- '"coerce":' propstore tests
rg -n -F -- "CompiledPayload" propstore tests
rg -n -F -- "_from_payload" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "**values" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "__init__(self, **values" propstore/families propstore/core propstore/world tests
rg -n -F -- "from_row_mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- ".coerce(" propstore/families propstore/core propstore/world tests
rg -n -F -- "Input = " propstore/families propstore/core propstore/world tests
rg -n -F -- "to_row_mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- "class WorldModel" propstore tests
rg -n -- "class .*Record\(" propstore/families/world_charters.py propstore tests
rg -n -F -- "claim_model_from_payload" propstore tests
rg -n -F -- "_from_payload" propstore/families/claims propstore/core tests
rg -n -- "Input\s*=.*Mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- "def resolve_concept" propstore tests
rg -n -F -- "def resolve_alias" propstore tests
rg -n -F -- ".resolve_claim(" propstore tests
rg -n -F -- ".resolve_concept(" propstore tests
rg -n -F -- ".resolve_alias(" propstore tests
rg -n -F -- "resolve_claim_id" propstore tests
rg -n -F -- "resolve_concept_id" propstore tests
rg -n -F -- "resolve_concept_alias" propstore tests
```

Literal `rg` gates extracted from the audited files and run from Quire:

```powershell
rg -n -F -- "CompiledPayload" quire tests
rg -n -F -- "from_payload" quire tests
rg -n -F -- 'metadata={"coerce"' quire tests
rg -n -F -- '"coerce":' quire tests
rg -n -F -- "**values" quire tests
```

Additional concrete named-symbol gates extracted from narrative text in the
spec, duplicate audit, helper ledger, and matrix:

```powershell
rg -n -F -- "ActiveClaimResolver" propstore tests
rg -n -F -- "main_model" propstore tests
rg -n -F -- "projection primitives" propstore tests
rg -n -F -- "sidecar-schema validation" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "TypedClaimFields" propstore tests
rg -n -F -- "extract_numeric_claim_fields" propstore tests
rg -n -F -- "extract_typed_claim_fields" propstore tests
rg -n -F -- "resolve_equation_sympy" propstore tests
rg -n -F -- "resolve_algorithm_storage" propstore tests
rg -n -F -- "_iter_claim_concept_link_values" propstore tests
rg -n -F -- "_claim_concept_link_values_for_declaration" propstore tests
rg -n -F -- "prepare_claim_concept_link_rows" propstore tests
rg -n -F -- "normalize_conditions_differ" propstore tests
rg -n -F -- "coerce_stance_resolution" propstore tests
rg -n -F -- "resolution_opinion_columns" propstore tests
rg -n -F -- "extract_deferred_stance_rows_with_diagnostics" propstore tests
rg -n -F -- "compile_claim_sidecar_rows" propstore tests
rg -n -F -- "populate_claims" propstore tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "ActiveClaim" propstore tests
rg -n -F -- "ActiveMicropublication" propstore tests
rg -n -F -- "ActiveWorldGraph" propstore tests
rg -n -F -- "WorldBindActiveReport" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CONFLICT_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "SidecarClaimRelationStore" propstore tests
rg -n -F -- "find_similar_claim_rows" propstore tests
rg -n -F -- "find_similar_concept_rows" propstore tests
rg -n -F -- "resolve_sidecar_concept_id" propstore tests
rg -n -F -- "SidecarClaimEmbeddingStore" propstore tests
rg -n -F -- "SidecarConceptEmbeddingStore" propstore tests
rg -n -F -- "ActiveMicropublicationInput" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "MicropublicationProjectionRow" propstore tests
rg -n -F -- "MicropublicationClaimProjectionRow" propstore tests
rg -n -F -- "MicropublicationSidecarRows" propstore tests
rg -n -F -- "compile_micropublication_sidecar_rows" propstore tests
rg -n -F -- "populate_micropublications" propstore tests
rg -n -F -- "RelationshipRow" propstore tests
rg -n -F -- "StanceRow" propstore tests
rg -n -F -- "ConflictRow" propstore tests
rg -n -F -- "compile_authored_stance_sidecar_rows" propstore tests
rg -n -F -- "select_stances_between" propstore tests
rg -n -F -- "select_conflicts" propstore tests
rg -n -F -- "select_all_relationships" propstore tests
rg -n -F -- "select_all_claim_stances" propstore tests
rg -n -F -- "select_claim_stances_with_policy" propstore tests
rg -n -F -- "select_explanation_stances" propstore tests
```

## Result Summary

Pass: zero-hit deletion/absence gates passed for the named old-path surfaces
below:

- `from_row_mapping`, `ConceptInput`, `ActiveClaimInput`,
  `coerce_active_claim`, `coerce_active_claims`,
  `CLAIM_ROW_MODEL.coerce`, `CONFLICT_ROW_MODEL.coerce`,
  `STANCE_ROW_MODEL.coerce`, `prepare_claim_insert_row`,
  `canonicalize_claim_for_storage`, `metadata={"coerce"`, `"coerce":`,
  `CompiledPayload`, `claim_model_from_payload`, `**values`,
  `__init__(self, **values`, `.coerce(`, `Input = `, `to_row_mapping`,
  `class WorldModel`, `class .*Record\(`, `Input\s*=.*Mapping`,
  all `resolve_claim` / `resolve_concept` / `resolve_alias` wrapper gates,
  `ActiveClaimResolver`, `main_model`, claim storage helper names,
  active-object names, row-model names, sidecar helper names, and the
  relation/micropublication helper names listed in the command block above.

Ambiguous or failing: these gates produced hits and need owner classification
or cleanup before they can be reported complete.

| Gate | Status | Expected meaning | Hits |
| --- | --- | --- | --- |
| `rg -n -F -- "_from_payload" propstore/families/claims propstore/core tests` | Fail unless each production hit is proven a true IO boundary | Duplicate audit says the exact allowed set must be zero for active cutover production code unless the workstream marks a true IO boundary and owner. | `propstore/core/assertions/conversion.py:38`, `propstore/core/assertions/conversion.py:56`, `propstore/core/assertions/__init__.py:8`, `propstore/core/assertions/__init__.py:26`, `propstore/families/claims/stages.py:57`, `propstore/families/claims/stages.py:114` |
| `rg -n -F -- "_from_payload" propstore/families propstore/core propstore/world propstore/worldline tests` | Fail/ambiguous | Same as above, broader scope; production hits outside claims/core also need explicit boundary classification. | `propstore/world/bound.py:146`, `propstore/world/bound.py:157`, plus the production hits from the narrower gate above |
| `rg -n -F -- "from_payload" quire tests` | Ambiguous, expected nonzero per duplicate audit | Duplicate audit says Quire `from_payload` hits were in `quire/contracts.py` and not part of the SQLAlchemy/charter mistake. Current search still has those hits. | `quire/contracts.py:39`, `quire/contracts.py:62`, `quire/contracts.py:168`, `quire/contracts.py:172` |
| `rg -n -F -- "**values" quire tests` | Ambiguous/fail | Duplicate audit expected Quire `**values` hits only in old projection row builders. Current hit is in `quire/charters.py`, so the file-specific expectation no longer matches the audit text. | `quire/charters.py:28` |
| `rg -n -F -- "ParameterizationInput" propstore tests` | Pass for the exact symbol, with one false-positive substring | The intended illegal symbol is absent. The only hit is a plural test class name, not `ParameterizationInput`. | `tests/test_validator.py:606` |
| `rg -n -F -- "normalize_claim_file_payload" propstore tests` | Ambiguous but likely semantic-lowering | Coercion audit says identity/source-local lowering names are not automatically illegal; hits must be classified by owner. | `propstore/families/identity/claims.py:76`, `propstore/source/claim_concepts.py:92`, `propstore/demo/reasoning_demo.py:83`, test helper hits |
| `rg -n -F -- "normalize_canonical_claim_payload" propstore tests` | Ambiguous but likely semantic-lowering | Same expected meaning as above. | `propstore/families/identity/claims.py:103`, `propstore/app/concepts/mutation.py:1151`, `propstore/source/claim_concepts.py:72`, `propstore/source/claim_concepts.py:141`, registry/test hits |
| `rg -n -F -- "normalize_canonical_concept_payload" propstore tests` | Ambiguous but likely semantic-lowering | Same expected meaning as above. | `propstore/families/identity/concepts.py:65`, `propstore/app/concepts/mutation.py:653`, `propstore/source/alignment.py:322`, `propstore/source/promote.py:573`, `propstore/source/promote.py:644`, `propstore/importing/passes.py:164`, `propstore/importing/passes.py:173`, family/test hits |
| `rg -n -F -- "normalize_source_claims_payload" propstore tests` | Ambiguous but likely source-local semantic boundary | Coercion audit names source-local claim/concept lowering as likely semantic-lowering, not automatically illegal. | `propstore/source/claims.py:90`, `propstore/source/claims.py:440`, `propstore/source/claims.py:553`, `propstore/source/__init__.py:14`, `propstore/source/__init__.py:76`, `propstore/source/promote.py:700`, test hits |
| `rg -n -F -- "legacy" propstore tests` | Ambiguous classification gate, not an absence gate | Coercion audit requires every hit classified as real IO boundary, semantic lowering, or illegal compat shim. | Production examples: `propstore/grounding/bundle.py:138`, `propstore/grounding/bundle.py:142`, `propstore/grounding/bundle.py:159`, `propstore/world/atms.py:2117`; many test hits |
| `rg -n -F -- "backward compat" propstore tests` | Ambiguous classification gate, not an absence gate | Same classification requirement. | `propstore/world/types.py:784`, `propstore/world/resolution.py:515`, `propstore/world/bound.py:96`, plus test hits |
| `rg -n -F -- "backwards compat" propstore tests` | Ambiguous classification gate, not an absence gate | Same classification requirement. | `tests/test_no_old_data_shims.py:17`, `tests/test_source_cli.py:725` |
| `rg -n -F -- "compat shim" propstore tests` | Ambiguous classification gate, not an absence gate | Same classification requirement. | `propstore/source/promote.py:14`, `propstore/grounding/bundle.py:161` |
| `rg -n -F -- "fallback" propstore tests` | Ambiguous classification gate, not an absence gate | Same classification requirement; some hits are likely ordinary fallback policy rather than old-shape compatibility. | Production examples: `propstore/source/promote.py:274`, `propstore/source/finalize.py:250`, `propstore/families/identity/claims.py:187`, `propstore/families/identity/claims.py:210`, `propstore/families/identity/concepts.py:311`, `propstore/world/resolution.py:543`, `propstore/world/atms.py:701` |
| `rg -n -- "\bcoerce_[A-Za-z0-9_]+" propstore tests` | Ambiguous classification gate, not an absence gate | Coercion audit requires classification; many hits are typed boundary/domain coercers, but this command is intentionally broad. | Production examples: `propstore/stances.py:30`, `propstore/core/claim_types.py:28`, `propstore/world/types.py:108`, `propstore/world/types.py:206`, `propstore/families/registry.py:559`, `propstore/cli/worldline/__init__.py:36` |

## Gates I Could Not Interpret

- `metadata that names parser/converter callables`: no exact literal or path
  scope is given in the audited files.
- `metadata that lists old input aliases for compatibility`: no exact literal
  or path scope is given.
- `new per-family table routing helpers`: no exact literal is given.
- `old sidecar-schema validation wording`: the exact old wording is not named.
  I ran `rg -n -F -- "sidecar-schema validation" propstore tests`, which was
  zero-hit, but that is only my best literal extraction.
- `projection primitives`, `row-model names`, `deleted helper/coercer names`,
  `active-object names`, `sidecar helper names`, and `lookup-wrapper names`
  from `helper-ledger.md` are category gates. I ran the concrete names present
  in the five audited files, but the category wording is not itself a complete
  exhaustive command.
- `inventory-matrix.md` says each delete action needs an old-path search gate
  outside notes, workstreams, docs, and reports. The matrix rows do not provide
  one literal command per row, so I could not interpret those rows as a fully
  mechanical exhaustive command set from the five audited files alone.

## Conclusion

The zero-hit deletion gates for the old row/coercion/resolver/helper surfaces
largely pass in Propstore. The audit is not fully complete because several
classification gates still have hits and because `_from_payload` has production
hits in active searched surfaces. Quire also has current hits for `from_payload`
and `**values`; the `from_payload` hits match the duplicate audit's expected
nonzero Quire result, but the `**values` hit is in `quire/charters.py`, not the
old projection location described by the audit.
