# Declarative Claim Validation Workstream

Date: 2026-04-18

## Target

Claim-type validation is declared in the claim document model and executed by the compiler. The compiler should not keep one hand-written required-field and concept-reference validator per claim type.

The declaration is part of propstore's semantic contract surface:

- each claim type has a versioned contract;
- required fields, non-empty collection fields, value/bounds rules, unit policy, and concept references are declared once;
- the contract manifest records those declarations so schema drift requires a versioned contract change;
- compiler validation dispatches through one generic claim-contract runner;
- runtime checks that cannot be expressed as static declarations remain as named semantic checks attached to the contract.

## Non-Goals

- Do not introduce compatibility shims or old/new dual paths.
- Do not rewrite YAML authoring into a closed msgspec union in this workstream.
- Do not weaken existing diagnostics.
- Do not materialize large git working trees or scan by loading avoidable artifact bodies.

## Workstream

1. Add declaration primitives to `propstore.artifacts.documents.claims`.
   - `ClaimFieldReferenceDeclaration`
   - `ClaimValueGroupDeclaration`
   - `ClaimUnitPolicyDeclaration`
   - `ClaimTypeContract`
   - `CLAIM_TYPE_CONTRACTS`
   - `claim_type_contract_for`
   - `iter_claim_type_contracts`

2. Encode every current claim-type obligation in `CLAIM_TYPE_CONTRACTS`.
   - `parameter`: `concept`, value group, required unit with dimensionless default, concept form unit check.
   - `equation`: `expression`, non-empty `variables`, variable concept references, sympy and dimensional semantic checks.
   - `observation`, `mechanism`, `comparison`, `limitation`: `statement`, non-empty `concepts`, concept references.
   - `model`: `name`, non-empty `equations`, non-empty `parameters`, parameter concept references.
   - `measurement`: `target_concept`, `measure`, value group, required unit, target concept reference.
   - `algorithm`: `body`, non-empty `variables`, variable concept references, parse and unbound-name semantic checks.

3. Add tests before changing compiler dispatch.
   - Assert contract declarations contain the expected rules.
   - Assert observation-like claim types share the same declared validation shape.
   - Assert the contract manifest includes claim-type contracts.

4. Replace hand-written per-type compiler dispatch with a generic declaration runner.
   - Add `validate_claim_semantics(...)`.
   - Execute required-field, non-empty-field, value-group, unit-policy, and concept-reference declarations generically.
   - Keep runtime-only semantic checks as small functions selected by the contract's `semantic_checks`.
   - Remove per-type validator entry points from `passes.py`.

5. Expose claim-type contracts in `propstore.contracts`.
   - Add `iter_claim_type_contracts()`.
   - Add `claim_type_contract` entries to the manifest.
   - Regenerate `propstore/contract_manifests/semantic-contracts.yaml`.

6. Verification.
   - Run targeted contract/compiler tests.
   - Run `uv run pyright propstore`.
   - Run the full test suite in parallel with eight workers.
   - Commit and push the completed slice.

## Completion Criteria

- There is no compiler `if ctype == ...` dispatch for claim-type validators.
- `passes.py` imports one claim semantics validator, not six per-type validators.
- Claim-type obligations are visible from the data model.
- Claim-type declarations are represented in the checked-in contract manifest.
- Existing validation behavior is preserved.
- Targeted tests, pyright, and full parallel tests pass.
