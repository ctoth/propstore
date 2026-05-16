# Nested Codec Ownership Decision

Workstream: `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`

## Decision

Phase 0c chooses option 2: domain nested types own their own parse/render.

Quire will own the projection codec protocol and generic projection mechanics.
Propstore will own domain codec declarations for semantic nested values.

That means Quire may call a declared `ProjectionCodec`, constructor, or typed
factory supplied by Propstore, but Quire must not learn the meaning of source
trust, provenance, opinion, context identity, micropublication claim lists, or
claim source structure.

## Reason

The nested codecs inspected here are not just row flattening:

- `SourceOrigin.from_mapping` normalizes `SourceOriginType` and represents a
  domain source-origin value.
- `SourceTrust.from_mapping` parses subjective-logic opinions and
  `derived_from` lists.
- `ClaimSource.from_mapping` owns source identity, kind, origin, trust, and
  emptiness semantics.
- `ProvenanceRecord.from_mapping` owns graph/runtime provenance extras, not a
  single projection table row.
- `ActiveMicropublication.from_mapping` validates runtime micropublication
  identity, context identity, claims, assumptions, stance, and source.

Putting those semantics into Quire would make Quire own Propstore domain
meaning. That is the wrong abstraction boundary.

## In Scope For Deletion

These remain in the projection-mapping deletion scope:

- family `*Row.from_mapping` and `*Row.to_dict` methods whose bodies flatten or
  unflatten projection columns;
- `coerce_*_row`, `_decode_*_row`, `_load_*_row`, `build_*_row`, and
  `make_*_row` helpers whose job is row decoding;
- row-factory lambdas, local closures, and select loops that call
  `Row.from_mapping(dict(row))`;
- duplicated projection column/FK/index declarations that can be derived from a
  single `ProjectionModel`;
- generic JSON, enum, scalar, optional, reference, and repeated-child projection
  mapping.

## Out Of Scope For This Workstream

These are not deleted by the projection-row mapping workstream unless a later
domain-codec workstream explicitly replaces them with a better domain type
surface:

- `SourceOrigin.from_mapping`
- `SourceTrust.from_mapping`
- `ClaimSource.from_mapping`
- `ProvenanceRecord.from_mapping`
- `ActiveMicropublication.from_mapping`

They must remain visible in scanner metrics so we do not mistake row-mapping
deletion for total codec deletion.

## Source Merge Consequence

The `ClaimRow.from_mapping` nested `source` plus flat `source_*` reconciliation
is blocked from generic mapping cleanup until a source-reconciliation slice
chooses a typed merge policy.

Until that happens:

- Phase 6 may delete generic claim fields such as logical IDs, provenance,
  enums, scalar claim values, and status fields.
- Phase 6 must not map `source_*` columns into Quire while leaving the old
  nested/flat source merge underneath it.
- The scanner metric `multi_source_merge_methods` must report the remaining
  source merge honestly.

## Quire API Consequence

`ProjectionCodec` belongs in Quire as a generic protocol. Domain codec
instances belong in Propstore projection declarations.

The target shape is:

- Quire owns when and where a codec runs.
- Propstore owns what a semantic codec means.
- The projection model remains the single declaration connecting a semantic
  field path to a storage column.

