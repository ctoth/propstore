# research-papers-plugin Integration

This document defines the mechanical handoff between `propstore` and
`../research-papers-plugin`.

## What propstore owns

- the claim schema
- validation of imported claim files
- sidecar compilation
- conflict detection
- the import CLI: `pks import-papers --papers-root ../research-papers-plugin/papers`

## What the plugin must produce

For each paper directory in `../research-papers-plugin/papers/`, the plugin
must write:

```text
papers/<PaperDir>/claims.yaml
```

That file should already conform to propstore's claim schema. In practice,
that means:

- top-level `source` mapping
- top-level `claims` list
- claim IDs in `claimN` format
- concept references using propstore `conceptN` IDs
- CEL conditions using propstore canonical names

## Import behavior

`pks import-papers` scans immediate subdirectories of the given `papers/`
directory. For every `papers/<PaperDir>/claims.yaml` it finds, it writes:

```text
claims/<PaperDir>.yaml
```

During import, `source.paper` is normalized to `<PaperDir>` so the imported
claim file and the paper directory use the same paper identity.

## Recommended workflow

From `../research-papers-plugin`:

1. Run the paper extraction flow and produce `claims.yaml` alongside
   `notes.md`, `description.md`, `abstract.md`, and `citations.md`.
2. Keep markdown as the human-facing view, but treat `claims.yaml` as the
   machine-readable artifact.

From `propstore`:

1. Run `pks import-papers --papers-root ../research-papers-plugin/papers`
2. Run `pks validate`
3. Run `pks build`
4. Query the sidecar with `pks query ...`

## Current state

The import path is now mechanical on the `propstore` side.

The plugin repository does not yet emit `papers/*/claims.yaml`, so the remaining
integration work is in `../research-papers-plugin`:

- paper-reader must write `claims.yaml`
- reconcile should read and write claim-level stance information rather than
  only annotating markdown
