# Family Protocol Breakdown Index

Date: 2026-05-24

Parent workstream: `../04c-family-document-and-relationship-protocol.md`.

## Workflow Used

This split was produced from explicitly forked scout reports:

- `reports/charter-cutover-breakdown/quire-prereqs-report.md`
- `reports/charter-cutover-breakdown/family-docs-registry-report.md`
- `reports/charter-cutover-breakdown/source-lifecycle-report.md`
- `reports/charter-cutover-breakdown/root-semantic-surfaces-report.md`
- `reports/charter-cutover-breakdown/worldline-resolution-report.md`
- `reports/charter-cutover-breakdown/old-workstream-reconciliation-report.md`

`reports/` is ignored, so this directory is the tracked control surface.

## Refactor Rule

Every field, schema, storage, reference, lifecycle, document, identity,
relationship, graph, and artifact fact is declared once in the family charter
or Quire family metadata. Propstore owns semantic behavior on family/domain
owners. No duplicate document classes, row DTOs, broad kwargs builders,
fallback readers, compatibility shims, aliases, adapters, per-family lookup
wrappers, root helper modules, or repeated field-name lists survive.

Deletion-first remains binding. Delete the old production surface first, use
compiler/type/test/search failures as the repair queue, and satisfy those
failures from the named owner. Do not restore deleted files.

## Sequence

1. `01-deleted-file-fallout.md`
2. `02-quire-document-and-family-protocol.md`
3. `03-generic-family-model-lookup.md`
4. `04-family-document-class-deletion.md`
5. `05-source-proposal-lifecycle.md`
6. `06-artifact-graph-context-worldline.md`
7. `07-concept-local-id-and-world-query-fixtures.md`
8. `08-justification-and-payload-boundaries.md`
9. `09-compatibility-classification-gates.md`
10. `10-final-gates.md`

No later file starts until every gate in the previous file passes or the
previous file records a failing gate as the active blocker.

## First Repair Principle

The already-deleted files stay deleted:

- `propstore/families/world_charters.py`
- `propstore/families/claims/metadata.py`

The repair is not to write them back. The repair is to route callers through
the real family charter/catalog/schema owner and typed claim/world model
behavior.

## Completion Criteria

- All child workstreams above are checked off in order.
- All old-path search gates in `10-final-gates.md` are zero-hit outside notes,
  workstreams, docs, and reports, except the explicit broad classification
  gates whose remaining production hits are listed as `io-boundary` or
  `semantic-owner`.
- Quire changes are pushed before Propstore pins them.
- Propstore uses an immutable pushed Quire dependency, never a local path.
- `uv run scripts/check_workstream_order.py ../00-index.md` passes.
- `uv run pyright propstore` passes.
- The logged pytest gates in each child pass.
