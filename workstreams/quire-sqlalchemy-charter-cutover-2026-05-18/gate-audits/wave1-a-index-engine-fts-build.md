# Wave 1A Gate Audit: Index, Engine, FTS, Build

## Files Audited

- `00-index.md`
- `02-quire-sqlalchemy-engine.md`
- `03-quire-fts-vector.md`
- `04-propstore-build-orchestration.md`

This audit used only read-only searches plus creation of this report. It did
not use `git log`, `pyright`, or `pytest`.

Repeated literal search gates appearing in more than one audited file were run
once per distinct command/workdir.

## Commands Run

### Propstore: dependency, Python floor, and build-orchestration gates

Run from `C:\Users\Q\code\propstore`:

```powershell
rg -n -F -- "quire" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- 'requires-python = ">=3.11"' pyproject.toml
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "ProjectionSchema" propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "ProjectionTable" propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "sqlite3.Connection" propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "Unsupported sidecar schema" propstore tests
rg -n -F -- "Rebuild with 'pks build'" propstore tests
rg -n -F -- "validate_derived_store_schema" propstore tests
rg -n -F -- "projection_catalog" propstore tests
rg -n -F -- "ProjectionSchemaError" propstore tests
rg -n -F -- "str(error)" propstore tests
rg -n -F -- "_MODELS" propstore/families/world_charters.py
rg -n -F -- "_CLAIM_MODEL_TABLES" propstore/families/world_charters.py
rg -n -F -- "def world_record" propstore/families/world_charters.py
rg -n -F -- "def world_model" propstore/families/world_charters.py
rg -n -F -- "world_model(" propstore/families/world_charters.py
rg -n -F -- "def _claim_models" propstore/families/world_charters.py
rg -n -F -- "_claim_models" propstore/families/world_charters.py
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- "def resolve_alias" propstore tests
rg -n -F -- "def resolve_concept" propstore tests
```

### Propstore: `00-index.md` final search gates

Run from `C:\Users\Q\code\propstore`:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionSchema" propstore tests
rg -n -F -- "ProjectionIndex" propstore tests
rg -n -F -- "ProjectionColumn" propstore tests
rg -n -F -- "ProjectionSelectedColumn" propstore tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "ProjectionRow" propstore tests
rg -n -F -- "ScalarPath" propstore tests
rg -n -F -- "ReferencePath" propstore tests
rg -n -F -- "FtsProjection" propstore tests
rg -n -F -- "VecProjection" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_FTS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_VEC_PROJECTION" propstore tests
rg -n -F -- "CONTEXT_SCHEMA" propstore tests
rg -n -F -- "TEXT_CODEC" propstore/families/contexts tests
rg -n -F -- "PARAMETERS_CODEC" propstore/families/contexts tests
rg -n -F -- "CONDITIONS_CODEC" propstore/families/contexts tests
rg -n -F -- "PROVENANCE_CODEC" propstore/families/contexts tests
rg -n -F -- "AUTOINCREMENT_CODEC" propstore/families/contexts tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "_claim_optional_float" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -- "class Active[A-Z]|\\bActive[A-Z][A-Za-z0-9_]*\\b" propstore tests
rg -n -F -- "WorldBindActiveReport" propstore tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "SidecarClaimRelationStore" propstore tests
rg -n -F -- "find_similar_claim_rows" propstore tests
rg -n -F -- "find_similar_concept_rows" propstore tests
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- "def resolve_concept" propstore tests
rg -n -F -- "def resolve_alias" propstore tests
rg -n -F -- ".resolve_claim(" propstore tests
rg -n -F -- ".resolve_concept(" propstore tests
rg -n -F -- ".resolve_alias(" propstore tests
rg -n -F -- "resolve_claim_id" propstore tests
rg -n -F -- "resolve_concept_id" propstore tests
rg -n -F -- "resolve_concept_alias" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
```

### Quire and `sqlalchemy-fts5`

Run from `C:\Users\Q\code\quire`:

```powershell
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "C:" pyproject.toml uv.lock
rg -n -F -- 'requires-python = ">=3.11"' pyproject.toml
rg -n -F -- "sqlalchemy-fts5" pyproject.toml uv.lock
rg -n -F -- "git =" pyproject.toml uv.lock
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionSchema" quire tests
rg -n -F -- "ProjectionIndex" quire tests
rg -n -F -- "ProjectionColumn" quire tests
rg -n -F -- "ProjectionSelectedColumn" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "ProjectionCodec" quire tests
rg -n -F -- "ScalarPath" quire tests
rg -n -F -- "ReferencePath" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Run from `C:\Users\Q\code\sqlalchemy-fts5`:

```powershell
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "C:" pyproject.toml uv.lock
rg -n -F -- 'requires-python = ">=3.11"' pyproject.toml
rg -n -F -- "sqlalchemy-fts5" pyproject.toml uv.lock
```

## Results

### Pass

- Propstore local Quire dependency absence gates passed: `path =`,
  `workspace = true`, `quire @ file`, `quire @ ..`, and `quire @ C:` returned
  zero hits.
- Propstore Quire dependency presence was confirmed: `pyproject.toml:83` and
  `uv.lock:2112`/`uv.lock:2518` point to
  `https://github.com/ctoth/quire` at
  `ac05ff5e66d8a744ec0be9406f8912c81dfaa6bd`.
- Propstore, Quire, and `sqlalchemy-fts5` Python floor checks passed with
  `requires-python = ">=3.11"` hits.
- Quire and `sqlalchemy-fts5` local dependency-pin absence gates passed:
  `file://`, `path =`, `workspace = true`, and `C:` returned zero hits in both
  repositories.
- Quire consumes `sqlalchemy-fts5` from GitHub at pushed SHA
  `ac6d05968f2f3bcf61c20a09efa41de4a605560d`.
- Quire projection old-path/final searches returned zero hits for all audited
  symbols: `ProjectionTable`, `ProjectionSchema`, `ProjectionIndex`,
  `ProjectionColumn`, `ProjectionSelectedColumn`, `ProjectionModel`,
  `ProjectionCodec`, `ScalarPath`, `ReferencePath`, `FtsProjection`, and
  `VecProjection`.
- Propstore build-orchestration deletion searches returned zero hits for
  `PROPSTORE_WORLD_PROJECTION_SCHEMA`, `ProjectionSchema`, `ProjectionTable`,
  and `sqlite3.Connection` over the specified build/test paths.
- Propstore old validation-wrapper searches returned zero hits for
  `Unsupported sidecar schema`, `Rebuild with 'pks build'`,
  `validate_derived_store_schema`, `projection_catalog`, and
  `ProjectionSchemaError`.
- Propstore `00-index.md` final zero-hit searches returned zero hits for all
  listed old-path/helper symbols, including the non-`-F` `Active*` regex gate
  and `from_mapping`.

### Fail / Open

The generic family-metadata correction in
`04-propstore-build-orchestration.md` remains open. The concrete named-symbol
gates found these hits:

```text
propstore\families\world_charters.py:72:_MODELS: dict[str, type[Any]] = {
propstore\families\world_charters.py:114:    return _MODELS[table_name]
propstore\families\world_charters.py:101:_CLAIM_MODEL_TABLES = {
propstore\families\world_charters.py:112:    if table_name in _CLAIM_MODEL_TABLES:
propstore\families\world_charters.py:111:def world_model(table_name: str) -> type[Any]:
propstore\families\world_charters.py:117:def world_record(table_name: str, values: object) -> Any:
propstore\families\world_charters.py:124:def world_records(table_name: str, rows: Iterable[object] | None) -> tuple[Any, ...]:
propstore\families\world_charters.py:113:        return _claim_models()[table_name]
propstore\families\world_charters.py:207:        _charter("claim_concept_link", _claim_models()["claim_concept_link"], "claim_id",
propstore\families\world_charters.py:385:def _claim_models() -> dict[str, type[Any]]:
propstore\families\world_charters.py:406:    claim = _claim_models()["claim_core"]
propstore\families\world_charters.py:474:    models = _claim_models()
propstore\families\world_charters.py:511:    models = _claim_models()
```

Interpretation: the Phase 5 build-orchestration deletion searches pass, but
the completed-phase correction explicitly says these model registry and
claim-special-case surfaces are not final. Search evidence confirms they still
exist.

### Ambiguous / Not Interpreted As Failure

- `rg -n -F -- "quire" pyproject.toml uv.lock` is a presence/dependency
  inventory gate, not an absence gate. It returned expected dependency hits.
- `rg -n -F -- "[tool.uv.sources]" pyproject.toml` is expected to hit the
  source table; it returned `pyproject.toml:81`.
- `rg -n -F -- "str(error)" propstore tests` returned unrelated app-level
  error rendering hits in `propstore/app/claims.py` and
  `propstore/app/world_atms.py`. The audited file names this as part of an old
  validation-wrapper investigation, but the current refresh only binds the
  exact old sidecar wording/searches, so I did not count these hits as a
  Phase 5 failure.
- Parsed dependency-table inspection, pushed-commit proof, parity JSON
  validity, `--help`, `pyright`, and pytest gates were not verified in this
  audit because the requested scope was read-only searches and explicitly
  forbade pyright and pytest.
