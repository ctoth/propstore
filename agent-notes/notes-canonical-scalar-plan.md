# Canonical Scalar Convergence Planning Record

## Literal outcome

Fully plan Workstream A of `plans/unwired-and-missing-code-convergence.md`:
one canonical scalar domain (`str | bool | int | float`, with `None` as absence)
preserved from source authoring through canonical storage, derived sidecar, and
runtime consumers, without a second claim representation or compatibility path.

This is a planning-only pass. No production edits are authorized in this pass.

## Active control surface

- `protocols:cleanup-refactor`
- `plans/unwired-and-missing-code-convergence.md`, Workstream A
- Project `AGENTS.md` deletion-first, classification, Git-ledger, Python, and
  logged-test requirements supplied by the user

## Confirmed target architecture

- Propstore owns scalar semantics: `str | bool | int | float`, `None` for
  absence; signed 64-bit integers; finite binary64 floats; bool distinct from
  int; no silent int-to-float conversion.
- Quire owns one generic charter-derived MessagePack BLOB storage mechanism;
  SQL `NULL` alone represents absence.
- Domain and authoring APIs expose native scalar values, not codec DTOs or
  payload wrappers.
- MessagePack sidecar bytes never participate in canonical identity, Git
  serialization, or content hashing.
- Numeric derivation consumers remain explicitly numeric.
- The standalone Claim LinkML/JSON schema contract is retired; unrelated schema
  resources remain unaffected.

## Confirmed forbidden surfaces

- `Claim.value: float | None` and `SourceClaimDocument.value: float | None`.
- Bool-to-string and int-to-float normalization in direct scalar paths.
- `_claim_to_payload` or any renamed/replacement mutable semantic payload helper.
- A Propstore-local MessagePack adapter, scalar wrapper/DTO, discriminator
  columns, parallel old/new storage, fallback decoder, or compatibility branch.
- MessagePack bytes in artifact/version/hash inputs.
- Category/boolean values entering numeric bounds, unit, dimensional,
  sensitivity, equation, parameterization, conflict, or assignment math.

## Current observations

- The active plan already fixes the semantic/storage decision and orders
  Workstream A before consumer-specific categorical/ATMS work.
- Current production types remain inconsistent across source, canonical, and
  runtime layers.
- Source identity normalization and authored-form restoration decode a typed
  `SourceClaimDocument` to a mutable dictionary through `_claim_to_payload`,
  mutate fields, then convert it back. This is core semantic manipulation, not
  an IO-only carrier, and must be dispositioned during the cutover.
- The plan requires a cross-package Quire storage change; the exact installed
  Quire source and codec/schema-generation surfaces still need verification.
- Existing tests are predominantly numeric and must be mapped into exact
  round-trip, form-validation, numeric-rejection, grounding, worldline, and ATMS
  gates.
- Propstore pins Quire commit `f89b1080dcee943b90314f40d00773ddfe735ca0`;
  the local `C:/Users/Q/code/quire` checkout is exactly that clean tracked HEAD.
  Its many untracked notes/reports are unrelated and must remain untouched.
- Quire has no MessagePack charter-field storage codec. `charter_field` exposes
  `json=True`, which becomes `parse_boundary="json"`; arbitrary unions otherwise
  reach `python_type_to_sql` and fall through to `TEXT`, losing scalar type.
- Existing `parse_boundary` concerns document parsing as well as SQL lowering,
  so overloading it for MessagePack would risk leaking derived storage encoding
  into canonical YAML documents. The required mechanism is a separate, generic,
  explicitly typed Quire storage-codec property, not `msgpack=True`, opaque
  metadata, `json=True`, or a Propstore adapter.
- The likely Quire owner surface spans `charter_class.CharterFieldSpec` /
  `charter_field`, `charters.CharterField`, `schema_ir.SchemaField`,
  `sql_types.SqlTypeSpec` lowering, and the SQLAlchemy type decorator. The exact
  property spelling and contract payload must be fixed in the executable plan.
- Propstore source promotion already copies `SourceClaimDocument.value` directly
  into `Claim.value`; no separate promotion representation is required.
- Source value-bound validation currently assumes every present `claim.value` is
  numeric. It must become form-kind-aware before the scalar union can safely flow
  through authoring.

## Git state

- Branch: `master`, ahead of `origin/master` by 28 commits.
- Unrelated untracked path: `pyghidra_mcp_projects/`; it must remain untouched.
- This note is required to remain uncommitted.

## Current state

The architecture and cross-repository storage seam are mapped. Caller and test
classification is still in progress. No implementation slice has started and
no production file has changed.

## Blocker

None yet. The plan cannot be declared executable until the generic Quire codec
property is specified, the full caller classification is complete, supported
Claim schema retirement is exact, and logged test commands are verified.

## Next action

## Proven design details after the second mapping pass

### Exact Claim schema retirement surface

- Delete `schema/claim.linkml.yaml`.
- Delete `schema/generated/claim.schema.json`.
- Delete `propstore/_resources/schemas/claim.schema.json`.
- Delete `schema/generate.py`; its only supported generation target is the Claim schema.
- Remove the now-unneeded `linkml` and `linkml-runtime` dependencies and refresh `uv.lock` during the schema-retirement slice.
- Keep the unrelated Form schemas: `schema/generated/form.schema.json` and `propstore/_resources/schemas/form.schema.json`.
- Update the current statement in `docs/data-model.md`; historical plans/reviews remain historical records.

### Exact generic Quire storage design

- Quire has no current MessagePack charter-field codec at the pinned commit.
- The required mechanism is a generic, explicit charter-field storage-codec property, not `json=True`, opaque metadata, a Propstore adapter, or a parallel `msgpack=True` flag.
- The planned API is `storage_codec: Literal["messagepack"] | None` on Quire's `CharterFieldSpec`, `charter_field(...)`, and `CharterField`.
- `CharterField.to_schema_field` passes that choice to SQL type derivation; a MessagePack field derives a BLOB SQL type.
- SQLAlchemy storage uses a generic typed `MessagePackValue` decorator: strict conversion to the charter field's declared Python type, MessagePack encode on bind, typed decode on result.
- SQL `NULL` is the sole absence representation. An encoded MessagePack `nil` is rejected rather than accepted as a second absence representation.
- `SchemaField` already retains its originating `charter_field`, so the codec must not duplicate the declared Python type in another schema field.
- Propstore will mark only canonical `Claim.value` as nullable MessagePack storage; source YAML remains native typed source data.

### Canonical scalar owner and validation

- The canonical semantic type is one Propstore-owned alias: `str | bool | int | float`; `None` represents absence outside that alias.
- Signed 64-bit integer bounds and finite-float validation belong to Propstore claim semantics, not Quire's generic storage codec.
- Direct construction must be validated because annotation-only `msgspec.Struct` construction does not prove the semantic bounds.
- Boolean is always tested before numeric `isinstance` checks because Python `bool` is an `int` subclass.
- Category and Boolean form validation must be shared by source authoring and canonical compilation; a source-only validator would recreate the semantic rule in the wrong owner.

### Runtime disposition split

- Direct scalar consumers preserve the exact native scalar, including the distinction among `True`, `1`, `1.0`, and `"1"`.
- Numeric consumers reject strings and booleans at their explicit boundary; they may convert accepted `int` values to `float` only for computation.
- `DerivedResult.value` remains numeric because it is produced by mathematical evaluation.
- `ResolvedResult`, `SyntheticClaim`, ATMS claim-node values, active-claim values, and worldline direct/input/step values require the full canonical scalar type.
- Delete `world/model.py::_as_scalar`; its bool-to-string and int-to-float coercions violate canonical scalar identity.
- Existing numeric boundaries need bool-first rejection audits, especially causal evaluation and known-value collection.
- Grounding already supports native string, bool, int, and float scalars; the remaining work is wiring Claim values through and proving exact round trips.

### Existing ATMS completion evidence

- `tests/test_atms_categorical_provider_visibility.py` contains the single skipped categorical-provider test named by Workstream A.
- The ATMS engine already contains categorical/non-numeric input rejection behavior.
- The final ATMS slice must unskip and satisfy that production-path test; it must not recreate the engine behavior under a new helper or adapter.

### Source payload fallout classification

- `source/claims.py::_claim_to_payload` is a semantic dict surface and must be deleted first in its slice.
- Its normalization and authored-form restoration callers are valid capabilities with the wrong representation; rewrite them with typed `msgspec.structs.replace` operations.
- Its identity caller is an encoding-boundary case: version hashing should accept the typed `SourceClaimDocument`, convert to builtins only inside the identity encoding owner, and never return or pass a semantic payload dict through core code.
- A `TYPE_CHECKING`-only import can type the identity API without introducing the runtime source/identity import cycle.

## Next action

## Findings from construction, validation, identity, and runtime inspection

### Construction and semantic validation

- `Claim` and `SourceClaimDocument` currently have no scalar `__post_init__` validation hook.
- `ClaimCheckPass` calls `claim_contracts.validate_claim(claim)` and already receives a `CompilationContext` containing `form_registry`, `concepts_by_id`, and the checked `condition_registry`.
- Canonical claim form-aware validation therefore belongs in the existing claim-contract/check pipeline, not in the CLI, world layer, or storage layer.
- Source authoring already resolves source and canonical concepts to existing `ConceptInfo` objects, including category vocabulary and extensibility, and resolves their existing `FormDefinition`.
- One Propstore claim-semantic validation operation can consume the existing typed `FormDefinition`, `ConceptInfo`, scalar value, and numeric bound fields. Source authoring and canonical claim checking resolve those existing objects at their own boundary and invoke the same semantic rule; no payload, adapter, or second concept/claim representation is needed.
- The relevant form kinds are quantity, category, boolean, structural, and timepoint. Workstream A explicitly requires quantity/numeric, category, and boolean direct-value behavior; structural claims are not given a scalar-value contract by this workstream, and timepoint handling must remain explicit rather than fall through a generic numeric check.

### Identity and artifact-code fallout

- `families/identity/claims.py` currently exposes `canonicalize_claim_for_version(dict)` and `compute_claim_version_id(dict)`; it also contains `normalize_canonical_claim_payload(dict)`, which has no production or test callers.
- Delete the dead `normalize_canonical_claim_payload` scaffold rather than migrate it.
- Change claim version canonicalization and version hashing to accept the typed `SourceClaimDocument`; any builtins/dictionary conversion stays private and local to the canonical encoding boundary.
- `artifact_codes.claim_artifact_code` also calls the dictionary canonicalizer. Rewrite only its Claim edge to use the typed claim identity operation; the other artifact-code `_payload` uses are separate source-artifact encoding-boundary work and are not broadened into this scalar slice.
- `source/claims.py` normalization and restoration can use `msgspec.structs.replace`; logical IDs remain typed `ClaimLogicalIdDocument` tuples.

### Form-aware gate placement

- Numeric bounds currently run only in `source/claims.py::validate_source_claim_value_bounds`, through two production validation paths.
- Delete that numeric-only function first. Classify both broken edges as valid claim-form validation with the wrong representation/semantics, then wire them to the shared claim-semantic rule.
- Canonical compilation must add the same form-aware diagnostics through `ClaimCheckPass`; source-only enforcement is insufficient because canonical Claims can be authored directly.
- Closed/extensible category data already has one typed path: source `form_parameters` becomes canonical `Concept.category_values` and `category_extensible`, and checked concept compilation exposes that as `ConceptInfo`.

### Exact ATMS test status

- `tests/test_atms_categorical_provider_visibility.py` is not an implemented skipped test: its test function contains only a docstring.
- The final slice must replace that placeholder with a real authored categorical provider flowing through the bound world and asserting the existing visible incompatibility node. Merely removing the skip marker would be false completion evidence.

### Concrete runtime consumer map

- Direct/presentation consumers that must carry the full scalar include `core/active_claims.py`, ATMS claim nodes, direct world resolution, `world/model.py`, worldline resolution/result/revision types, and relevant reasoning reports.
- Numeric-only boundaries include conflict comparison/parameterization conflicts, causal/equation/parameterization derivation, sensitivity, dimensional comparison, overlay arithmetic, and assignment selection.
- Current coercion surfaces include `world/model.py::_as_scalar`, `world/resolution.py::_normalize_numeric`, and `world/value_resolver.py::_normalize_numeric`; each broken dependency edge must be classified before replacement. Direct callers preserve exact scalar identity; numeric callers reject strings and bools before optional int-to-float computational conversion.
- `world/atms.py`, `world/reasoning_reports.py`, `world/types.py`, `worldline/result_types.py`, and `worldline/revision_types.py` still contain float/string-only annotations that omit bool and int.

## Next action

## Final planning evidence

### Form-kind dispositions

- Current `docs/data-model.md` defines timepoints as numeric epoch seconds with numeric comparison, while explicitly excluding them from parameterization and dimensional algebra. Workstream A therefore validates timepoint direct values as numeric but does not route them into equation/parameterization/unit machinery.
- Structural concepts cannot participate in CEL. Workstream A does not create a new structural scalar-value contract; structural values must not accidentally fall into numeric logic, but any broader structural-value policy is outside this slice.

### Direct versus numeric caller decisions

- `world/resolution.py::_normalize_numeric` currently does two incompatible jobs: it converts ints to floats while also passing strings through. Delete it and classify its callers individually.
- Ordinary determined values, override/recency/sample-size/argumentation winners, and direct worldline/reporting paths preserve the exact Claim scalar.
- Assignment-selection callers are numeric-only per the active plan: reject bool/string values before constructing the package request and compare accepted numeric values only.
- `world/value_resolver.py::_normalize_numeric` has the same mixed responsibility. Delete it; direct value consensus preserves exact scalar equality, while known-value collection and algorithm comparison use explicit numeric-only extraction.
- `world/model.py::_as_scalar` is deleted. Environment bindings already have the canonical scalar union; chain steps accept those exact values and reject unsupported objects rather than stringify them.
- `world/causal.py::_as_float` must reject bool before the int/float branch.
- ATMS parameterization already performs the correct bool-first/non-numeric rejection. Its claim-node, derived lookup, key, and normalization annotations must accept the full direct scalar even though derived arithmetic values remain numeric.

### Quire schema-IR design closure

- Add `storage_codec: Literal["messagepack"] | None` only to `CharterFieldSpec`, `charter_field(...)`, and `CharterField`; do not duplicate it as a new `SchemaField` attribute.
- `CharterField.to_schema_field` calls `python_type_to_sql(..., storage_codec=self.storage_codec)`.
- MessagePack lowering produces `SqlTypeSpec(storage_kind="messagepack", ddl_name="BLOB", sqlalchemy_type="MessagePackValue", python_type=<declared type path>)`.
- `SchemaField.payload()` records the codec directly from `self.charter_field.storage_codec`; this makes the storage contract visible without a second owner.
- `_sqlalchemy_type` dispatches `MessagePackValue` using the original `field.charter_field.python_type`, so typed decode does not rely on reloading an unresolvable union type path.
- The MessagePack decorator strictly validates/encodes on bind, returns the declared typed value on result, maps SQL NULL only to absence, and rejects an encoded MessagePack nil.

### Verified baseline gates

- Propstore focused baseline, through the required logged wrapper:
  `powershell -File scripts/run_logged_pytest.ps1 --label canonical-scalar-plan-baseline tests/test_claim_charter.py tests/test_source_authoring_p82.py tests/test_source_promote_p83b.py tests/test_world_query.py tests/test_world_model_glue.py tests/test_value_resolver_mixed_algorithm.py tests/test_grounding_facts.py tests/test_worldline_result_boundaries.py tests/test_atms_categorical_provider_visibility.py -q`
  Result: 107 passed, 1 skipped in 11.37 seconds. The skip is the empty categorical ATMS placeholder.
- Quire focused baseline:
  `uv run pytest tests/test_charters_schema_ir.py tests/test_sqlalchemy_engine.py -q`
  Result: 24 passed in 1.74 seconds.
- Propstore typing baseline: `uv run pyright propstore` -> 0 errors.
- Quire typing baseline: `uv run pyright quire` -> 0 errors.

### Exact CLI/import/presentation cutover

- `propstore/importing/contract.py::ImportClaimRow.value` is still `float | None`; change it to the canonical Claim scalar and keep `source/passes.py` as a direct typed transfer into `SourceClaimDocument`.
- `propstore/cli/source/proposal.py` declares `--value` as `type=float` and the command parameter as `float | None`; change the Click boundary to accept text and invoke the already-owned scalar coercion in `propstore/cli/helpers.py`.
- Tighten the existing `_coerce_cli_scalar` return annotation from `object` to the canonical scalar type. Do not introduce a second parser, callback adapter, DTO, or wrapper.
- Lower/upper bound and uncertainty CLI options remain float-only.
- `propstore/app/claim_views.py::ClaimViewValue.value` is a direct presentation surface and changes to the canonical scalar type; `ClaimViewUncertainty` remains numeric.
- Add CLI and import tests proving `"red"`, `true`, integer, and float values reach the typed source document without changing their runtime type.

## Next action

Produce the fully executable deletion-first plan: ordered atomic commits, file/symbol dispositions, focused tests, completion searches, full gates, and the cross-repository pin handoff. No production edits are authorized in this pass.

## Execution iteration Q1 - Quire generic MessagePack charter storage

Slice:
- `C:/Users/Q/code/quire/quire/charter_class.py`
- `C:/Users/Q/code/quire/quire/charters.py`
- `C:/Users/Q/code/quire/quire/schema_ir.py`
- `C:/Users/Q/code/quire/quire/sql_types.py`
- `C:/Users/Q/code/quire/quire/sqlalchemy_schema.py`
- `C:/Users/Q/code/quire/tests/test_messagepack_charter_storage.py`

Dispositions:
- Explicit charter storage encoding: create at the generic Quire charter owner.
- Arbitrary-union TEXT fallback for an explicitly MessagePack-coded field: replace with typed BLOB lowering.
- Propstore adapter, codec wrapper, parallel path, encoded-nil absence: forbidden and absent.
- Test positional model construction failure: dead/test-scaffold edge; corrected to the charter model's keyword construction without changing production code.

Evidence:
- `storage_codec="messagepack"` is carried by `CharterFieldSpec` and `CharterField`.
- Schema lowering records `storage_kind="messagepack"`, `ddl_name="BLOB"`, and `sqlalchemy_type="MessagePackValue"`.
- The SQLAlchemy decorator uses the originating charter field's Python type, preserves exact scalar runtime types, maps `None` to SQL NULL, and rejects encoded MessagePack nil.
- The schema contract payload includes the codec without adding a duplicate `SchemaField` owner.

Gates:
- Focused: 32 passed in 1.51 seconds.
- Ruff: all checks passed.
- Pyright: 0 errors, 0 warnings, 0 informations.
- Full pytest: 508 passed, 12 deselected in 139.33 seconds.
- Build: source distribution and wheel built successfully.
- `git diff --check`: passed.

Commit:
- `9f9d9ff Add charter-derived MessagePack storage`

State:
- Quire tracked worktree is clean after the commit; unrelated pre-existing untracked notes/reports remain untouched.
- The commit has not yet been pushed.

Next action:
- Push Quire commit `9f9d9ff` to its configured `origin/master`, verify the remote branch, then begin Propstore P1 by deleting the Claim semantic payload surfaces before rewriting their callers.

## Execution iteration P1 - typed Claim identity

Remote prerequisite:
- Quire `9f9d9ff155b482e139011969ae73fc603c5e4ff5` was pushed to and verified at `origin/master`.

Surfaces and dispositions:
- `source/claims.py::_claim_to_payload`: deleted old semantic-dict surface.
- Source normalization/restoration callers: rewritten to `msgspec.structs.replace` over `SourceClaimDocument` and typed `ClaimLogicalIdDocument` tuples.
- Claim version identity: rewritten in the existing identity owner to accept and return typed `SourceClaimDocument`; builtins conversion is private to the hash boundary.
- `normalize_canonical_claim_payload`: deleted dead scaffold; not recreated.
- `artifact_codes.claim_artifact_code`: keeps dictionary conversion only inside its own encoding boundary and receives the typed canonical Claim.

Search gate:
- `rg -n "_claim_to_payload|normalize_canonical_claim_payload" propstore tests` -> zero matches.

Runtime gates:
- Focused logged pytest: 39 passed in 6.10 seconds.
- Pyright: 0 errors.
- Ruff over touched files: all checks passed.
- `git diff --check`: passed.

Commit:
- `c4b015b0 Delete Claim payload identity surfaces`

State:
- P1 is committed; no tracked Propstore diff remains from that slice.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Begin P2 canonical scalar storage cutover: create the storage-pure scalar type owner, change source/import/canonical fields together, pin Quire `9f9d9ff`, retire the Claim schemas atomically, and prove the full source-to-WorldQuery runtime-type gate.

## Execution iteration P2 - partial scalar/storage cutover state

Completed mutations in the active uncommitted slice:
- Added `propstore/core/scalars.py` as the storage-pure owner of `ScalarValue` and signed-int64/finite-float validation.
- Changed canonical `Claim.value` to a nullable charter field using `storage_codec="messagepack"`; bumped the Claim contract version.
- Changed `SourceClaimDocument.value` and `ImportClaimRow.value` to the same scalar type and construction validation.
- Changed direct `ClaimViewValue.value` to the scalar type.
- Changed source `propose-claim --value` from float-only Click parsing to the existing CLI scalar parser, now exposed as typed `coerce_cli_scalar`; numeric bound/uncertainty options remain floats.
- Updated the Quire source pin to `9f9d9ff155b482e139011969ae73fc603c5e4ff5`.
- Removed `linkml` and `linkml-runtime` from project dependencies.
- Deleted `schema/claim.linkml.yaml`, both generated/packaged Claim JSON schemas, and the Claim-only `schema/generate.py`.
- Updated the current data-model schema statement; Form schemas remain.

Current state:
- P2 is intentionally uncommitted and incomplete.
- `uv.lock` has not yet been regenerated.
- Type fallout and the required source-to-WorldQuery five-case integration test have not yet been processed.
- No compatibility or parallel storage path has been added.

Blocker:
- None. The next exact action is the dependency lock refresh against the now-pushed Quire revision.

Next action:
- Run `uv lock`, then classify all Pyright/test fallout from the scalar cutover, update direct carrier annotations without changing numeric-only semantics, add the five-case vertical integration/CLI/import tests, and run the P2 search/runtime gates before committing.

## Execution iteration P2 - checkpoint before import-boundary test

Additional completed work in the active uncommitted slice:
- Regenerated `uv.lock`; the pinned Quire revision is resolved and the retired LinkML dependency tree is absent.
- Classified direct scalar carriers and changed `ClaimViewValue`, `ATMSClaimNode`, and `WorldExplainReport` to preserve `ScalarValue`.
- Classified conflict/source numeric consumers as numeric-only boundaries and added explicit non-boolean `int | float` selection; no string/bool coercion was introduced.
- Added charter/codec and scalar-domain tests, CLI scalar parsing/storage tests, and a source-proposal through promotion and `WorldQuery` runtime-type test.
- `uv run pyright propstore` currently passes with 0 errors.

Current state:
- P2 remains one active uncommitted vertical slice. No second source slice may begin until it is either committed or fully restored.
- The tracked diff is limited to the intended scalar/storage/schema/dependency surfaces; unrelated untracked `pyghidra_mcp_projects/` remains untouched.
- The import-row scalar preservation regression is the last known missing focused test before running the named P2 gates.

Blocker:
- None.

Next action:
- Add exact-runtime-type coverage for `ImportClaimRow` through `coerce_claim_rows`, run the logged focused P2 suite, then run completion searches, Ruff, Pyright, and `git diff --check`. Commit P2 only if all gates pass.

## Formatting reconciliation authorized by user

User-directed sequence:
1. Format the full repository Python tree and commit formatting alone.
2. Make the ATMS `ScalarValue` import and `ATMSClaimNode.value` annotation the immediately following two-line commit.
3. Restore and finish the remainder of P2 only after those commits.

Current state:
- The complete active P2 diff, including the untracked `propstore/core/scalars.py`, is recoverably parked in `stash@{0}` with message `canonical-scalar-p2-before-format`.
- The duplicate tracked/worktree copies left by the path-limited stash were removed only after the stash contents were verified.
- Unrelated `pyghidra_mcp_projects/` remains untouched and was explicitly excluded from formatting.
- `uv run ruff format --exclude pyghidra_mcp_projects .` reformatted 366 files and left 278 unchanged.
- The repository-wide formatting diff is uncommitted and has not yet been gated.

Blocker:
- None.

Next action:
- Verify that the current diff is formatting-only, run Ruff format/check, package Pyright, and `git diff --check`, then commit only the formatting diff. After that, reapply and commit exactly the two ATMS scalar lines as the next commit.

Formatting gate results:
- Ruff formatter idempotence: 644 files already formatted.
- Production-package Ruff: all checks passed.
- Package Pyright: 0 errors, 0 warnings, 0 informations.
- `git diff --check`: passed.
- Initial full logged suite exposed one test-scaffold dependency on a one-line CLI registry tuple; the lazy registry capability remained present.
- Rewrote only that expected textual shape to the canonical Ruff multiline rendering.
- Targeted regression: 1 passed.
- Full logged rerun: 1739 passed, 2 skipped in 76.34 seconds.

Commit:
- `5fbd2070 Format Python tree with Ruff`

State:
- Repository-wide formatting is committed.
- The P2 stash is still intact.
- The next commit must contain only the two ATMS scalar lines authorized by the user.

Next action:
- Add the `ScalarValue` import and change `ATMSClaimNode.value` to `ScalarValue | None`; run focused formatting/lint/type/runtime gates and commit those two lines without restoring the remainder of P2 first.

## Execution iteration P2a - scalar owner and ATMS direct carrier

Surfaces and dispositions:
- `propstore/core/scalars.py`: created as the one Propstore domain owner for canonical scalar type and storage-domain validation; this is a real domain type, not a helper or codec DTO.
- `ATMSClaimNode.value`: valid direct scalar carrier with the wrong numeric-only annotation; rewritten to use the domain owner directly.
- No normalization, conversion, adapter, compatibility path, or duplicate representation was added.

Gates:
- Ruff formatter: 2 files already formatted.
- Ruff lint: all checks passed.
- Package Pyright: 0 errors.
- Logged ATMS tests: 20 passed, 1 existing placeholder skipped.
- `git diff --check`: passed.

Commit:
- `45d888ff Type ATMS Claim values as canonical scalars`

State:
- Formatting and the ATMS prerequisite are committed in the user-directed order.
- The remaining P2 tracked diff is still parked in `stash@{0}`; its untracked scalar owner is now superseded by committed `45d888ff`.

Next action:
- Restore only the remaining tracked P2 paths from the stash, excluding `propstore/world/atms.py` and the now-committed scalar owner; reconcile against the formatting commit, rerun P2 gates, and commit the completed scalar storage/CLI/schema/pin slice.

## Execution iteration P2b - canonical scalar storage cutover complete

Surfaces and dispositions:
- Canonical `Claim.value`, source `SourceClaimDocument.value`, and import `ImportClaimRow.value`: rewritten to the one committed `ScalarValue` owner.
- Canonical Claim storage: rewritten to charter-derived nullable MessagePack BLOB storage through pinned Quire `9f9d9ff155b482e139011969ae73fc603c5e4ff5`.
- CLI `--value`: rewritten from float-only parsing to the existing scalar parser with a typed return; numeric bounds and uncertainty remain numeric.
- Conflict/source validation callers: kept as explicit numeric-only boundaries with bool/string rejection; no direct scalar normalization was added.
- Claim LinkML, generated JSON schemas, packaged Claim schema, and Claim-only generator: deleted parallel schema surfaces.
- LinkML dependencies: removed and `uv.lock` refreshed.

Gates:
- Logged focused P2 suite: 146 passed in 13.36 seconds.
- Ruff formatter: 13 files already formatted.
- Ruff lint: all checks passed.
- Package Pyright: 0 errors.
- `uv lock --check`: passed.
- `git diff --check`: passed.
- Retired Claim schema reference search: zero matches outside historical docs.
- Old cut-over scalar/payload surface search: zero matches.

Commit:
- `bb7de3cc Converge Claim scalar storage`

State:
- P2 is committed; no tracked P2 work remains.
- The temporary stash is now redundant because its scalar owner/ATMS content is in `45d888ff` and its remaining content is in `bb7de3cc`.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Verify the tracked worktree is clean, remove the now-redundant temporary stash, then begin P3 by deleting `validate_source_claim_value_bounds` and `_value_fields_for_claim` before classifying and rewriting their caller edges to shared form-aware Claim semantics.
### P3 in progress: shared form-aware Claim validation

- Deleted `propstore.source.claims._value_fields_for_claim` and
  `validate_source_claim_value_bounds`; neither deleted name will be restored.
- Classified the exposed source-authoring and import dependency edges as valid
  source boundaries carrying the wrong representation. Their disposition is to
  use the existing typed whole-claim `validate_source_claims` boundary.
- Generalization check: form-aware scalar validation is Claim-domain behavior,
  not a source-family mechanism. The shared owner accepts typed Claim scalar
  fields plus `FormDefinition` and `ConceptInfo`; it owns no repository scan,
  source lifecycle, counter, naming, or reservation protocol.
- Added the shared Claim-domain rule in `propstore.claim_contracts` and began
  consolidating source validation onto it. The import pipeline now calls
  `validate_source_claims` once instead of three separate source validators.
- Current uncommitted production files: `propstore/claim_contracts.py`,
  `propstore/source/claims.py`, and `propstore/source/passes.py`. Unrelated
  untracked `pyghidra_mcp_projects/` remains untouched.
- Next action: wire canonical `ClaimCheckPass` to resolve the form-bearing
  concept and call the same Claim-owned validator, then format, add focused
  source/canonical regressions, run the logged focused suite plus Ruff/Pyright,
  update this record, and commit the P3 slice before starting P4.

### Execution iteration P3 - shared form-aware Claim semantics complete

Surfaces and dispositions:
- `_value_fields_for_claim` and `validate_source_claim_value_bounds`: deleted
  old source-only numeric surfaces; neither was recreated or renamed.
- Source authoring/import callers: valid typed source boundaries consolidated
  onto the existing whole-claim `validate_source_claims` operation.
- Form-aware scalar validation: owned by `propstore.claim_contracts` and called
  by both source validation and canonical `ClaimCheckPass` with existing typed
  `FormDefinition` and `ConceptInfo` objects.
- Quantity/timepoint values are numeric and bounds-aware; category values are
  textual and honor closed/extensible vocabulary; boolean values require bool;
  category/boolean bounds are rejected; structural receives no new scalar
  policy.
- No repository scan, source lifecycle, adapter, payload, compatibility path,
  or second Claim/concept representation was added to the shared owner.

Gates:
- Logged focused suite: 74 passed in 8.86 seconds; log
  `logs/test-runs/canonical-scalar-p3-final-20260721-180313.log`.
- Ruff over all seven touched production/test files: all checks passed.
- Package Pyright: 0 errors.
- `git diff --check`: passed.
- Deleted-name search across `propstore` and `tests`: zero matches.

State:
- P3 is fully implemented and gated but not yet committed.
- Intended tracked diff is seven files: four production files and three test
  files. Unrelated `pyghidra_mcp_projects/` remains untouched.
- Blocker: none.

Next action:
- Inspect the exact diff/stat, stage only the seven P3 files, commit this kept
  slice, verify the tracked worktree, then proceed to the next unchecked
  Workstream A slice.

Commit:
- `9f199373 Share form-aware Claim validation`

### P4a in progress - delete lossy chain scalar coercion

Surfaces and dispositions:
- `world.model._as_scalar`: deleted. Its bool-to-string, int-to-float, and
  arbitrary-object-to-string behavior is forbidden on direct scalar paths.
- Typed keyword-binding to `ChainStep` edge: already-owned canonical binding
  value; disposition is direct use.
- `ActiveClaim.value` to chain step edge: already-owned Claim scalar;
  disposition is direct use through the existing active view.
- `ActiveClaim.value`, `ChainStep.value`, and the `ClaimSpec` test carrier now
  use the existing `ScalarValue` owner; no replacement helper or normalization
  surface was introduced.

Current evidence:
- Package Pyright: 0 errors.
- Ruff over all five touched files: all checks passed.
- `_as_scalar` search across `propstore` and `tests`: zero matches.
- The existing chain-binding regression now also asserts exact bool and int
  runtime types on recorded `ChainStep` values.

State:
- P4a is an active uncommitted vertical slice in five tracked files.
- Unrelated `pyghidra_mcp_projects/` remains untouched.
- Blocker: none.

Next action:
- Run the logged world-model/query/chain/ATMS focused runtime gate, reread this
  plan, run diff hygiene, and commit P4a before deleting either resolution
  module's mixed `_normalize_numeric` surface.

P4a completion:
- Logged focused suite: 73 passed in 11.87 seconds.
- `git diff --check`: passed.
- Commit: `b61ed5c4 Delete lossy chain scalar coercion`.

### P4b ready to commit - separate resolution scalar paths

Surfaces and dispositions:
- `world.resolution._normalize_numeric`: deleted; no renamed replacement exists.
- Determined pass-through and strategy winner edges: valid direct-resolution
  capabilities using `ActiveClaim.value` directly, preserving exact scalar
  runtime type.
- Assignment-selection filter/request/winner-match edges: numeric-only package
  boundary. Bool and string values are rejected before package construction;
  accepted ints/floats are converted to float only for package computation.
- `ResolvedResult.value`: direct carrier now uses the existing `ScalarValue`
  owner.

Gates:
- Logged resolution/assignment/world-model suite: 67 passed in 10.40 seconds;
  log `logs/test-runs/canonical-scalar-p4b-20260721-181200.log`.
- Direct resolution preserves value and runtime type for string, bool, int, and
  float; override preserves a categorical winner.
- Assignment-selection rejects bool and string claims while existing numeric
  behavior remains green.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed. Deleted-name search in the active surface: zero
  matches.

State:
- P4b is an active uncommitted three-file slice. Blocker: none.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Inspect and commit the exact P4b diff, verify the tracked worktree, then begin
  a new slice by deleting `world.value_resolver._normalize_numeric`.

P4b commit:
- `c51d8d36 Separate direct and numeric resolution values`

### P4c ready to commit - separate value-resolver scalar paths

Surfaces and dispositions:
- `world.value_resolver._normalize_numeric`: deleted; no renamed replacement.
- `_active_claim_value`: deleted wrong caller that existed only to preserve the
  removed mixed surface.
- Direct consensus: compares typed scalar identity without coercion and keeps
  bool, int, float, and string distinct.
- Known-value collection, parameterization inputs, overrides, and algorithm
  constants: numeric-only boundaries that reject bool/string and convert
  accepted int/float only for computation.

Gates:
- Logged value-resolver/sensitivity/world-model suite: 40 passed in 5.44
  seconds; log
  `logs/test-runs/canonical-scalar-p4c-20260721-181620.log`.
- Tests prove exact direct consensus for all four scalar types, conflict for
  `True` versus `1` and `1` versus `1.0`, numeric-only known-value collection,
  and bool/string override rejection.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed. Both deleted-name searches across world/tests:
  zero matches.

State:
- P4c is an active uncommitted two-file slice. Blocker: none.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Inspect and commit P4c, verify the tracked worktree, then audit the remaining
  numeric-only consumers and direct scalar carrier annotations for the next
  smallest executable slice.

P4c commit:
- `9fc710fc Separate direct and numeric value resolution`

### P5a ready to commit - causal bool rejection

Disposition:
- `world.causal._as_float` is a valid numeric-only structural-equation
  boundary, not a mixed direct-value surface. It now rejects bool before the
  int/float conversion branch.

Gates:
- Logged causal/world-model suite: 13 passed in 4.95 seconds; log
  `logs/test-runs/canonical-scalar-p5a-20260721-181837.log`.
- Integration regression proves a boolean exogenous equation input fails as
  nonnumeric while existing integer/float causal evaluation is unchanged.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P5a is an active uncommitted two-file slice. Blocker: none.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Commit P5a, verify tracked state, then classify the remaining audit hits in
  conflict, overlay, worldline, runner, base-rate, activation, and ATMS code
  before choosing the next source slice.

P5a commit:
- `8dcacef9 Reject boolean causal inputs`

### P5b ready to commit - strict numeric range constraints

Disposition:
- Assignment-selection RANGE compilation is a numeric-only constraint boundary.
  It now rejects bool and string values instead of accepting Python bool-as-int
  or parsing numeric-looking text; int/float behavior is unchanged.

Gates:
- Logged assignment-selection/resolution suite: 59 passed in 7.81 seconds; log
  `logs/test-runs/canonical-scalar-p5b-20260721-182046.log`.
- Regressions prove `True` and `"5"` fail range predicates.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P5b is an active uncommitted two-file slice. Blocker: none.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Commit P5b, verify tracked state, then continue the classified numeric audit
  with base-rate source values and worldline-derived numeric override maps.

P5b commit:
- `944482ff Reject nonnumeric range constraint values`

### P5c ready to commit - base-rate bool rejection

Disposition:
- `BaseRateAssertionRecord.from_parameter_claim` is an IO-boundary carrier into
  a numeric-only base-rate domain record. It now rejects bool before accepting
  int/float values.

Gates:
- Logged base-rate suite: 11 passed in 5.30 seconds; log
  `logs/test-runs/canonical-scalar-p5c-20260721-182230.log`.
- Regression proves a boolean source-claim value is rejected as nonnumeric.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P5c is an active uncommitted two-file slice. Blocker: none.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Commit P5c, verify tracked state, then harden the worldline sensitivity and
  derived-override numeric projections without changing direct result values.

P5c commit:
- `36fa240b Reject boolean base-rate values`

### P5d ready to commit - strict worldline numeric projections

Dispositions:
- `ResolutionContext.override_values` remains a direct scalar carrier; this
  slice does not coerce or otherwise change its direct result values.
- `ResolutionContext.numeric_overrides()` is a valid numeric-only projection
  into derived evaluation. It now rejects bool and string values and returns
  only float-projected int/float inputs.
- `_capture_sensitivity`'s `float_overrides` map is a valid numeric-only
  sensitivity boundary. It now rejects bool and string values before package
  evaluation.

Gates:
- Logged worldline/sensitivity suite: 17 passed in 7.08 seconds; log
  `logs/test-runs/pytest-20260721-182700.log`.
- Regressions prove bool/string rejection and unchanged int/float projection
  for both derived resolution and sensitivity capture.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P5d is an active uncommitted three-file slice. Blocker: none.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

Next action:
- Commit P5d, verify tracked state, then classify and cut over persisted
  worldline inputs/results/trace fields that still narrow canonical scalar
  values to `float | str`.

P5d commit:
- `dc30f836 Reject nonnumeric worldline projections`

### P5e ready to commit - canonical worldline scalar carriers

Findings and dispositions:
- `WorldlineInputs.overrides`, `ResolutionContext.override_values`, the runner's
  resolved override map, `WorldlineInputSource.value`,
  `WorldlineTargetValue.value`, `WorldlineStep.value`, and worldline app diff
  values are valid direct scalar carriers with the wrong narrow annotation;
  they now use the existing `ScalarValue` owner.
- CLI `_coerce_override_values` was a deleted old surface whose only behavior
  was lossy bool-to-string and int-to-float conversion. It is deleted, and both
  callers now pass the already-typed `parse_kv_args` result directly.
- `RevisionAtomRef.value` is not used by revision execution and remains the
  only `float | str` hit in the worldline package. It is classified as a
  separate dead field, not disguised as part of this direct-carrier cutover.

Observations and gates:
- Logged family/result/app/CLI/execution/revision suite: 54 passed in 9.03
  seconds; log `logs/test-runs/pytest-20260721-183102.log`.
- Repository persistence, Quire result decoding, and CLI authoring each prove
  exact runtime identity for str, bool, int, and float values.
- Deleted-name search for `_coerce_override_values`: zero matches.
- Package Pyright: 0 errors. Ruff: all checks passed.
- `git diff --check`: passed.

State:
- P5e is an active uncommitted nine-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P5e, verify tracked state, then delete the unused
  `RevisionAtomRef.value` field and its parser/test scaffolding as a separate
  vertical slice before continuing the remaining scalar-carrier audit.

P5e commit:
- `a2ee2786 Preserve worldline scalar values`

### P5f ready to commit - delete unused revision atom values

Findings and dispositions:
- `RevisionAtomRef.value` was a dead/test/scaffold surface. Revision execution
  resolves an already-existing assertion/assumption atom by id, and neither
  `to_belief_atom_input`, dispatch, nor journal normalization reads the field.
- The field and all test-only arguments/assertions are deleted.
- The CLI parser's `value` extraction was a wrong caller that existed only for
  the dead field. It is deleted, and the IO boundary now rejects an explicit
  `value` key rather than accepting an input that cannot affect revision.

Gates:
- Logged revision/journal/CLI suite: 40 passed in 11.07 seconds; log
  `logs/test-runs/pytest-20260721-183246.log`.
- Search across the worldline package finds no remaining `float | str`
  carrier, `RevisionAtomRef` value use, or value forwarding into the ref.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P5f is an active uncommitted four-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P5f, verify tracked state, then continue the remaining direct scalar
  carrier and numeric-only boundary audit outside `propstore.worldline`.

P5f commit:
- `57d2bed0 Delete unused revision atom values`

### P6a in progress - complete the authored categorical ATMS path

Findings and dispositions:
- The active plan explicitly requires ATMS claim-provider, derived lookup/key,
  and normalization annotations to accept `ScalarValue`, while derived
  arithmetic remains numeric. Those six annotations now use the existing
  scalar owner; no engine helper or behavior was added.
- The empty/skipped categorical-provider scaffold has been replaced with a
  repository-authored Concept/Context/Claim/equation path intended to assert
  the existing visible incompatibility node through public `node_status`.

Observations:
- Ruff and package Pyright pass for the active production/test diff.
- An initial four-file ATMS command accidentally named one nonexistent test
  path and collected zero tests; it is not evidence.
- The corrected ATMS suite ran 22 tests: 21 passed and the new production-path
  test failed before ATMS construction because repository concept compilation
  rejected the fixture.
- Replacing hyphenated concept/claim ids with valid-symbol underscores did not
  change the failure. The earlier diagnosis that identifiers caused the
  compiler rejection was wrong.
- The focused retry again failed in `run_concept_pipeline`, before the target
  ATMS behavior ran; log
  `logs/test-runs/canonical-scalar-atms-target-20260721-183805.log`.

State and blocker:
- P6a is an active uncommitted two-file slice. The production annotations are
  statically green, but the required end-to-end test is not yet executable.
- Exact blocker: the authored Concept fixture is missing or violating a
  concept-pipeline requirement that the current exception does not print.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Inspect the concept compiler's exact diagnostics and existing minimal
  repository-backed concept/form fixtures, correct only the authored fixture,
  then rerun the same categorical ATMS target before the wider ATMS gate.

P6a completion:
- The exact fixture defect was the canonical names `Category input` and
  `Numeric output`: canonical concept names must be CEL identifiers. Changing
  them to `category_input` and `numeric_output` made the same authored
  repository path compile; no form or engine change was required.
- Focused production-path test: 1 passed in 8.56 seconds; log
  `logs/test-runs/canonical-scalar-atms-target-20260721-183910.log`.
- Wider ATMS/world-query/world-model gate: 74 passed in 10.38 seconds; log
  `logs/test-runs/canonical-scalar-atms-20260721-183939.log`.
- The real categorical Claim is loaded through `WorldQuery`, enters the bound
  ATMS provider graph, and produces a publicly inspectable derived OUT node
  with `PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE` and the provider/type reason.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P6a is a ready-to-commit two-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P6a, verify tracked state, then cut over the remaining direct scalar
  carriers in `world/types.py` and `world/reasoning_reports.py` before the
  grounding proof and final fixed-point gates.

P6a commit:
- `91d75f22 Complete categorical ATMS provider visibility`

### P6b ready to commit - canonical world report scalars

Findings and dispositions:
- `SyntheticClaim.value`, `WorldResolveReport.value`,
  `WorldChainStepLine.value`, and
  `WorldHypotheticalSyntheticClaimSpec.value` are valid direct scalar carriers
  with the wrong narrow annotation. They now use `ScalarValue`.
- `WorldChainReport.value` remains `float | None` because it is populated only
  from mathematical `DerivedResult` output.
- CLI `_coerce_hypothetical_value` was a deleted old surface that rejected
  bool, converted int to float, and parsed numeric-looking text. It is deleted;
  the JSON IO boundary validates the existing JSON value as scalar and passes
  it directly into the typed request.

Observations and gates:
- The first report gate named a nonexistent `tests/test_world_resolution.py`
  path and collected zero tests; it is not evidence.
- Corrected logged CLI/report/overlay/model suite: 65 passed in 15.17 seconds;
  log `logs/test-runs/canonical-scalar-reports-20260721-184248.log`.
- Regressions prove exact str, bool, int, and float identity at hypothetical
  JSON parsing and rejection of nested nonscalar values.
- Deleted-name search for `_coerce_hypothetical_value`: zero matches.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P6b is a ready-to-commit four-file slice. Blocker: none.
- Remaining `float | str` annotations under `propstore.world` are confined to
  the separate bound/overlay/value-resolver override and numeric projection
  path.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P6b, verify tracked state, then classify the bound/overlay/value-
  resolver override carriers versus their numeric projection boundaries.

P6b commit:
- `9510fd95 Preserve world report scalar values`

### P6c ready to commit - delete lossy overlay scalar projection

Findings and dispositions:
- `overlay._numeric_value` was a deleted old surface on a direct semantic edge:
  it converted ints to floats and silently replaced string/bool synthetic Claim
  values with absence.
- `_synthetic_claim` is a valid canonical Claim construction edge with the
  wrong representation. It now passes the already-typed
  `SyntheticClaim.value` directly to `Claim.value`; no replacement helper or
  normalization surface exists.

Observations and gates:
- The first wider run failed only because the new test called the existing
  `build_bound` fixture without its required explicit `claims` argument; the
  target behavior had not run. Correcting the call to `claims=()` fixed the
  test scaffold without changing production.
- Focused overlay suite: 11 passed in 5.24 seconds; log
  `logs/test-runs/canonical-scalar-overlay-target-20260721-184633.log`.
- Wider overlay/report/CLI suite: 59 passed in 13.53 seconds; log
  `logs/test-runs/canonical-scalar-overlay-20260721-184645.log`.
- Regression proves exact runtime identity for str, bool, int, and float from
  synthetic input through the materialized canonical Claim and bound result.
- Deleted-name search for `_numeric_value`: zero matches.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P6c is a ready-to-commit two-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P6c, verify tracked state, then type the bound/overlay/BeliefSpace
  override carrier as `ScalarValue` while keeping sensitivity and derivation
  evaluation explicitly numeric.

P6c commit:
- `36deb734 Preserve synthetic overlay scalar values`

### P6d ready to commit - separate derived override carrier and numeric boundary

Findings and dispositions:
- BoundWorld, OverlayWorld, and the `BeliefSpace` protocol carry caller-supplied
  override values into the already-owned resolver; their mappings now use
  `ScalarValue | None` without coercion.
- `ActiveClaimResolver._coerce_override_value` remains the explicit
  parameterization numeric boundary. It rejects bool/string and converts only
  accepted int/float inputs for computation.
- `SensitivityBound` is a numeric-only package protocol; its override mapping
  is narrowed to `float`.
- `ActiveClaimResolver._normalize_value` was dead scaffold for
  `DerivedResult.value`, which is already `float | None`. It is deleted, and
  derived candidate comparison uses the canonical result values directly.

Gates:
- Logged model/value-resolver/sensitivity/overlay suite: 52 passed in 9.15
  seconds; log
  `logs/test-runs/canonical-scalar-derived-contract-20260721-184920.log`.
- Owner-level regressions prove BoundWorld rejects bool/string overrides; the
  existing exact scalar consensus and numeric known-value/override tests remain
  green.
- Search under `propstore.world` finds no remaining `float | str` annotation;
  `_normalize_value` remains only as the distinct ATMS numeric-equivalence
  operation over a `ScalarValue` annotation.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P6d is a ready-to-commit six-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P6d, verify tracked state, then execute the grounding scalar
  round-trip proof and audit any remaining top-level non-world scalar carrier
  annotations before the final fixed-point gates.

P6d commit:
- `7155b5f3 Separate derived scalar and numeric overrides`

### P7a ready to commit - strict typed grounding scalars

Findings and dispositions:
- `claim.attribute:value` was already wired from the canonical Claim through
  `GroundingFactInputs` into Gunray facts; no new grounding adapter was needed.
- The existing `_scalar_value` function is the valid Gunray IO boundary. Its
  canonical scalar branch preserves exact native values, but its fallback
  stringified arbitrary objects. That fallback is deleted; nonscalar Claim
  attributes now fail hard instead of fabricating a scalar string.
- `_scalar_value` now returns the existing `ScalarValue` owner directly.

Gates:
- Logged grounding fact/translator/loading/grounder/inspection/sidecar suite:
  51 passed in 7.09 seconds; log
  `logs/test-runs/canonical-scalar-grounding-20260721-185203.log`.
- Regressions prove exact runtime identity for str, bool, int, and float from
  canonical Claim through `gunray.GroundAtom` and
  `gunray.DefeasibleTheory.facts`.
- A tuple-valued Claim attribute is rejected as nonscalar rather than
  stringified.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P7a is a ready-to-commit two-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7a, verify tracked state, then run the repository-wide scalar
  annotation/coercion audit to identify any remaining executable slice before
  the final fixed-point and full gates.

P7a commit:
- `8fec8a32 Reject nonscalar grounding values`

### P7b ready to commit - typed direct value comparison

Findings and dispositions:
- `value_comparison._as_float` is a valid numeric-only boundary. It previously
  parsed numeric-looking strings; that path is deleted. Only non-bool int/float
  values enter interval/numeric comparison.
- The nonnumeric fallback is a valid direct scalar comparison. Python equality
  conflated `True` with `1`; it now requires matching runtime types as well as
  equal values.
- Numeric int/float values still compare computationally, so `1` and `1.0`
  remain compatible at this explicitly numeric boundary.

Gates:
- Logged value-comparison/conflict suite: 41 passed in 5.39 seconds; log
  `logs/test-runs/canonical-scalar-comparison-20260721-185507.log`.
- Regressions prove `"5"` versus `5` and `True` versus `1` are incompatible,
  exact same-type category/boolean values are compatible, and numeric int/float
  equivalence remains intact.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P7b is a ready-to-commit two-file slice. Blocker: none.
- The fixed-point audit still has one suspected bool-as-number boundary in
  metadata preference helpers and duplicated direct scalar union annotations
  to classify.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7b, verify tracked state, then harden metadata preference numeric
  inputs against bool before consolidating remaining direct scalar aliases.

P7b commit:
- `bcbfba94 Separate direct and numeric value comparison`

### P7c ready to commit - reject boolean preference metadata

Disposition:
- `_positive_float` and `_unit_float` are valid numeric-only metadata
  boundaries for sample size, uncertainty, and confidence. Both now reject bool
  before accepting int/float values; no direct scalar carrier is involved.

Gates:
- Logged preference/ASPIC/grounded-ASPIC suite: 42 passed in 6.88 seconds; log
  `logs/test-runs/canonical-scalar-preference-20260721-185651.log`.
- Regression proves bool provides no numeric evidence to either helper.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P7c is a ready-to-commit two-file slice. Blocker: none.
- Runtime numeric consumer audit is at fixed point for the plan's named
  surfaces; the remaining repeated scalar unions are direct type-owner cleanup.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7c, verify tracked state, then replace repeated direct scalar unions
  with `ScalarValue` in the environment/binding/rule carriers and their typed
  request/protocol surfaces before the full fixed-point gates.

P7c commit:
- `b5e73fed Reject boolean preference metadata`

### P7d ready to commit - one canonical scalar type owner

Findings and dispositions:
- `defeasibility.CelScalar` was a duplicate direct-scalar alias. It is deleted;
  its callers import the existing `ScalarValue` owner directly.
- Environment bindings, context-lifting bindings, world/app/graph request
  bindings, rule constants, support-revision scope bindings, chain binding
  records, and worldline CLI key/value parsing are valid direct scalar carriers
  with repeated union annotations. They now use `ScalarValue` without changing
  runtime behavior or adding an adapter.
- Recursive JSON carrier types are unrelated IO-boundary representations and
  remain untouched.

Gates:
- Logged defeasibility/context/world/graph/worldline/revision focused suite:
  107 passed in 13.76 seconds; log
  `logs/test-runs/canonical-scalar-owner-20260721-190045.log`.
- Search finds no remaining `CelScalar` references or repeated direct scalar
  union annotations outside the canonical alias itself and runtime type checks.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P7d is a ready-to-commit 12-file slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7d, verify tracked state, then run the completion searches and the
  exact focused baseline, full logged suite, Ruff, Pyright, and diff gates.

P7d commit:
- `cf4c2b4f Use canonical scalar owner throughout`

### P7e ready to commit - type the numeric known-value carrier

Finding and disposition:
- `collect_known_values` is the existing numeric-only projection from direct
  Claim values into algorithm comparison. It already rejects bool/string and
  converts accepted int/float values to float, but its function, callback,
  bound-world, overlay, and comparison annotations still used `Any`/`object`.
- Those annotations now use `float` throughout the existing path. No new helper,
  adapter, or runtime behavior was introduced.

Gates:
- Logged value-resolver/world/overlay/parameterization suite: 54 passed in 6.70
  seconds; log
  `logs/test-runs/canonical-scalar-known-values-20260721-190637.log`.
- Regressions cover nonnumeric rejection, numeric collection, direct scalar
  identity, derivation, and overlay behavior.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P7e is a ready-to-commit three-file slice. Blocker: none.
- The completion search also found a separate stale closed-gap paragraph that
  still says `_as_scalar` remains and `ChainStep.value` is narrowed. It will be
  corrected only after this code slice is committed.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7e, verify tracked state, then correct the stale closed-gap record as
  a documentation-only commit before the final gates.

P7e commit:
- `29f56f6e Type numeric known-value carriers`

### P7f ready to commit - correct stale scalar gap history

Disposition:
- The closed `ChainResult.bindings_used` gap is a durable historical record, but
  its present-tense claim that `_as_scalar` remains and `ChainStep.value` is
  `float | str | None` became false after Workstream A.
- The paragraph now distinguishes the 2026-07-13 state from the later canonical
  scalar convergence: `ChainStep.value` uses `ScalarValue`, `_as_scalar` is
  deleted, and bool/int identity is preserved.

Gates:
- Documentation diff is one paragraph; `git diff --check` passes.
- Search finds no current-tense claim that `_as_scalar` stays or that the current
  `ChainStep.value` type remains narrowed.

State:
- P7f is a ready-to-commit one-file documentation slice. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7f, verify tracked state, then run the final fixed-point searches and
  Workstream A's exact vertical, focused, full-suite, Ruff, and Pyright gates.

P7f commit:
- `fe2c7ac1 Update canonical scalar gap history`

### P7g ready to commit - version and regenerate the contract manifest

Full-suite finding and disposition:
- The first full logged suite passed 1810 tests with one unrelated dependency
  skip, then failed two contract-manifest tests. Both failures were the same
  edge: Workstream A changed the charter-derived Claim/registry contract body
  while the registry contract revision and checked-in generated manifest still
  described the prior body.
- This is a valid durable contract artifact in its existing family-registry
  owner. `PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION` is bumped from
  `2026.07.21.2` to `2026.07.21.3`, and the manifest is regenerated through the
  existing `uv run pks contract-manifest --write` owner command.
- The generated manifest records the already-landed Claim family revision
  `2026.07.21` and registry revision `2026.07.21.3`; no helper or compatibility
  marker was added.

Gates:
- Logged contract-manifest and CLI suite: 12 passed in 6.11 seconds; log
  `logs/test-runs/canonical-scalar-contract-manifest-20260721-191211.log`.
- Ruff: all checks passed. Package Pyright: 0 errors.
- `git diff --check`: passed.

State:
- P7g is a ready-to-commit two-file repair slice. Blocker: none.
- The first full-suite result is not completion evidence because it was red;
  log `logs/test-runs/canonical-scalar-full-20260721-190912.log`.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit P7g, verify tracked state, reread Workstream A, then rerun the full
  logged suite and all final static/fixed-point gates.

P7g commit:
- `76a79ddb Version canonical scalar registry contract`

### Final formatting repair ready to commit

Finding and disposition:
- The literal whole-tree Ruff format check found one remaining unformatted test,
  `tests/test_cli_phase10_advanced.py`. Running `uv run ruff format .` changed
  only that file and made no semantic edit.
- Whole-tree Ruff lint also reports 72 unrelated existing errors in historical
  scripts/reviews and test imports. They are not Workstream A dependencies and
  are not auto-fixed or folded into this formatting slice.

Gates:
- `uv run ruff format --check .`: 644 files already formatted.
- File-level Ruff check: all checks passed.
- Logged file suite: 15 passed in 6.22 seconds; log
  `logs/test-runs/format-all-final-20260721-191731.log`.
- `git diff --check`: passed.

State:
- The one-file mechanical formatting slice is ready to commit. Blocker: none.
- The notes file remains uncommitted. Unrelated `pyghidra_mcp_projects/`
  remains untouched.

Next action:
- Commit the formatting slice, then rerun the final logged suite, package
  Pyright, import boundaries, format check, fixed-point searches, and plan audit
  from committed HEAD.

Formatting commit:
- `b456db95 Format remaining Python test`

## Workstream A complete

Final committed-HEAD evidence:
- Full logged suite: 1812 passed, 1 skipped in 80.36 seconds; log
  `logs/test-runs/canonical-scalar-final-head-20260721-191841.log`.
- The single skip is
  `test_praf_argument_enumeration_budget_surfaces_partial_result`, an explicit
  still-open Workstream B seam; no Workstream A test is skipped.
- Exact focused scalar vertical gate: 141 passed; log
  `logs/test-runs/canonical-scalar-final-focused-20260721-190836.log`.
- Package Pyright: 0 errors. Import-linter: 3 contracts kept, 0 broken.
- Whole-tree Ruff format check: 644 files already formatted.
- Completion searches: no deleted payload/coercion helper names, duplicate
  scalar aliases, narrowed known-value carriers, retired Claim schema/dependency,
  or categorical ATMS placeholder/skip remain. Only the canonical alias and
  explicit runtime boundary guards spell the scalar union directly.
- The durable Workstream A checklist and evidence were committed as
  `77f22115 Record canonical scalar workstream completion`.

Final state:
- Workstream A is complete with all kept slices committed.
- The notes file remains intentionally uncommitted/ignored.
- Unrelated `pyghidra_mcp_projects/` remains untouched.
- No blocker remains for Workstream A.
