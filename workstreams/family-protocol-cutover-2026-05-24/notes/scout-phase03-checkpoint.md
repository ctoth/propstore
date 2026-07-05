# Scout Phase 03 — Checkpoint 2026-05-25 (update 2)

## State

- HEAD `c8b83c77`. Clean.
- All reads from earlier checkpoint complete.
- Now verified all V005-V009 callsites at HEAD with surrounding 3-5 lines context.

## Quire accessor verdicts (definitive — re-confirmed via grep)

`main_model` / `reference_resolver`: zero hits across `.venv/Lib/site-packages/quire/`.
`reference_keys`: exists as FIELD on `FamilyDefinition` (`families.py:86`) and `SchemaObject` (`schema_ir.py:199`). NOT a method on `SqlAlchemySchema`.
`SqlAlchemySchema.table(family_name)` — present at `sqlalchemy_schema.py:100-104`.
`SqlAlchemySchema.model(family_name)` — present at `sqlalchemy_schema.py:112-116`.
`SqlAlchemySchema.identity_field(family_name)` — present at `sqlalchemy_schema.py:126-133`.
`SqlAlchemySchema.resolve_reference_id(session, family, ref)` — present at `:149-157` (session-bound).
`SqlAlchemySchema.require_reference_id(session, family, ref)` — `:159-168`.
`SqlAlchemySchema.reference_index_from_records(family, records)` — `:135-147`.

## propstore registry accessors at HEAD

`propstore/families/registry.py:1255-1298`:
- `world_catalog()` returns `SchemaCatalog` (lru_cached).
- `world_schema()` returns `SqlAlchemySchema` (lru_cached).
No `main_model`, `table`, `identity_field`, `reference_keys`, `reference_resolver` accessor methods on the registry itself.

## V005-V009 callsites at HEAD (line numbers DRIFTED from scout #2)

V005 — `derived.schema.table("claim_core")`:
- `propstore/source/status.py:60` (was :56 — line drift +4)
- `propstore/families/claims/declaration.py:1227` (was :770 — major drift +457)

V006 — `derived.schema.table("build_diagnostics")`:
- `propstore/families/diagnostics/declaration.py:225, 240, 264` (was :187, :202, :226)
V006 — `derived.schema.model("build_diagnostics")`:
- `propstore/families/diagnostics/declaration.py:226, 241` (was :188, :203)

V007 — `schema.model("claim_core")`:
- `propstore/families/claims/sidecar_runtime.py:78, 116`
- `propstore/families/embeddings/declaration.py:187, 370` (was :108, :291)
- `propstore/world/model.py:289, 313, 334, 411, 455, 629, 847`

V008 — `schema.model("concept")`:
- `propstore/app/concepts/display.py:51`
- `propstore/families/embeddings/declaration.py:213, 419` (was :134, :340)
- `propstore/world/model.py:237, 261, 553, 697, 846`
- `tests/test_concept_workflows.py:38`
- `tests/test_sidecar_concept_projection.py:55`

V008 — `schema.model("alias")`:
- `propstore/families/embeddings/declaration.py:214`
- `tests/test_sidecar_alias_projection.py:40`

V009 — `schema.model("context")`:
- `propstore/families/contexts/declaration.py:301` (was :191)
- `tests/test_contexts.py:371`

V009 — `schema.model("context_assumption")`:
- `propstore/families/contexts/declaration.py:302`
- `tests/test_contexts.py:372`

V009 — `schema.model("context_lifting_rule")`:
- `propstore/families/contexts/declaration.py:303`
- `tests/test_contexts.py:373`

V009 — `schema.model("context_lifting_materialization")`:
- `tests/test_context_lifting_ws5.py:263`
- `tests/test_sidecar_contexts.py:121`

Note: spec deletion targets are propstore production sites; tests appear too but Phase 03 search gates target propstore + tests.

## Consumer use patterns (verified by reading surrounding lines)

- V005 (`source/status.py:60`): consumer takes the returned `Table` object and uses `.c.id`, `.c.promotion_status`, `.c.branch`, `.c.seq` in a `select(...)`. Needs Table.
- V005 (`claims/declaration.py:1227`): similar — uses `claim_core.c.id`, `.c.promotion_status`. Needs Table.
- V006 diagnostics: interleaved Table+model — `table.c.*` for filtering, `model` for `select(model)`. Needs both.
- V007 (`sidecar_runtime.py:78`): consumer takes returned model class and does `select(claim).where(claim.id.in_(...))`. Needs model class.
- V008 (`embeddings/declaration.py:213-214`): consumer takes model classes and uses ORM-style `concept.id`, `alias.concept_id`. Needs model class.

## Section 8 verdict (preliminary)

Phase 03's named accessors map to existing `SqlAlchemySchema` methods as follows:
- `main_model(family_name)` -> `SqlAlchemySchema.model(family_name)` (EXISTING, different name)
- `table(family_name)` -> `SqlAlchemySchema.table(family_name)` (EXISTING, same name)
- `identity_field(family_name)` -> `SqlAlchemySchema.identity_field(family_name)` (EXISTING, same name)
- `reference_keys(family_name)` -> `SqlAlchemySchema.schema_object(family_name).reference_keys` (field-on-schema-object, not method)
- `reference_resolver(family_name)` -> `SqlAlchemySchema.resolve_reference_id` (session-bound, signature differs)

Verdict: (a) — Quire already exposes the full set; the spec name `main_model` is a NAMING DIFFERENCE (current name `model`), not absence of capability. The rewrite proceeds against existing `SqlAlchemySchema` methods. Phase 03 deletion targets are the propstore CALLSITES; Quire methods are KEPT and used.

OR (b) if the foreman prefers the Phase 03 spec names — propstore adds thin convenience wrappers in registry.py.

Will pick (a) in the report because spec at `03:14-16` says "generic Quire/family-registry infrastructure" (either is acceptable) and the existing Quire methods are functionally sufficient.

## Next steps

1. Read SOURCE_CHARTER for FamilyCharter shape sanity check.
2. Read Quire `__init__.py` for re-export confirmation.
3. Write the 10-section deliverable report.

## Blocker

None.
