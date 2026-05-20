# Coercion And Compatibility Audit

Date: 2026-05-20

## Verdict

The next work is classification and deletion, not continued feature work.

Any production path that accepts an old row/dict/mapping shape after a typed
boundary exists is illegal unless this workstream names an external
compatibility target. The current cutover does not name such a target.

## Required Classification

Every hit from the searches below must be classified before the next Phase 10
implementation slice:

- `real-io-boundary`: parser/decode entrypoint that uses typed `msgspec` or an
  equivalent strict boundary and fails hard on bad shape.
- `semantic-lowering`: source-local reference lowering, import-time reference
  rewriting, concept rename propagation, or other actual Propstore semantics.
- `illegal-compat-shim`: old-shape support, row repair, `Mapping | Model`
  unions, projection-model coercion, fallback old query paths, broad repair
  constructors, or old/new dual behavior.

Only `real-io-boundary` and `semantic-lowering` may remain. Every
`illegal-compat-shim` must become a deletion target in the owning phase.

## Required Searches

Run these exact searches and record the classification:

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
```

## Initial Known Illegal Set

These are already known from the first search pass and do not need more
debate:

- `ActiveClaim.from_row_mapping`
- `coerce_active_claim`
- `coerce_active_claims`
- `ActiveClaimInput`
- `CLAIM_ROW_MODEL.coerce`
- `Concept.from_row_mapping`
- `Concept.coerce`
- `ConceptInput = Concept | Mapping[...]`
- `Parameterization.from_row_mapping`
- `Parameterization.coerce`
- `ParameterizationInput = Parameterization | Mapping[...]`
- `prepare_claim_insert_row`
- `canonicalize_claim_for_storage` as a storage-row repair surface
- `_optional_string`
- `_optional_float_input`
- `_optional_int`
- `extract_numeric_claim_fields`
- `extract_typed_claim_fields`
- any `*CompiledPayload`
- any new `*_from_payload` factory replacing a projection surface

## Likely Semantic-Lowering Set

These names are not automatically illegal. They must be kept only if their
callers prove they are semantic owner code, not old-shape compatibility:

- import-time reference rewriting in `propstore/importing/passes.py`;
- source-local claim/concept reference lowering in `propstore/source`;
- concept rename propagation in app/CLI concept mutation code;
- `rewrite_parameterization_symbols`;
- raw-id/logical-id artifact identity derivation in
  `propstore/families/identity`.

## Likely Real IO Boundary Set

These may remain only if they are strict typed decode/encode boundaries and not
runtime repair helpers:

- YAML/JSON authored document decode;
- `msgspec` document parsing;
- CLI request parsing from strings to typed requests;
- boundary-specific names such as `from_yaml_payload`,
  `from_json_payload`, or `from_row_mapping` only when the row is actually an
  external IO row and the object returned is a typed boundary object.

Runtime world, family, and semantic pipeline code is not an IO boundary.

## Required Workstream Consequence

Before Phase 10 resumes:

1. Run the searches.
2. Record every production hit classification in this file.
3. Add each `illegal-compat-shim` to the owning child workstream deletion
   target if it is not already listed.
4. For Phase 10, delete the known claim illegal set before adding any new claim
   construction code.
5. If deleting the illegal set requires a generic constructor/write-routing
   capability that Quire lacks, return to the Quire workstream first.

No code slice may add or keep a compatibility surface because it is convenient
for tests.
