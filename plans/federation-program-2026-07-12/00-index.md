# Federation Program - Slice Index

Goal: make independently versioned knowledge repositories and heterogeneous corpora participate in typed, provenance-preserving reasoning without moving Propstore semantics into Quire.

## Active

1. `01-quire-fetch-ref.md` - fetch one remote Git ref into a local tracking ref under CAS.

## Queued

2. `02-propstore-import-snapshot-alignment.md` - align two committed imported KB snapshots without canonical-name collapse.
3. `03-propstore-mailing-list-source-kind.md` - admit mailing-list messages as an honest source kind.
4. `04-corpus-mailing-list-root-message.md` - carry one real BlindHandyman message through the `pks source` validation boundary.

## Ordering

- Slice 1 is independent in `../quire`.
- Slices 2 and 3 both modify Propstore and must run sequentially, one committed slice at a time.
- Slice 4 depends on Slice 3 and then runs in `../corpus-plugins`.
- Remote Propstore import consuming Slice 1 is deliberately deferred until the Quire primitive is proven and pinned.

## Global invariants

- Imported assertions are stated evidence, not truth.
- Source-local identity survives import.
- Alignment remains defeasible and non-mutating.
- Quire stays ontology-neutral.
- No wrappers, adapters, remote managers, fallback readers, or duplicate semantic representations.
- Each kept implementation slice is committed before another slice starts in the same repository.
