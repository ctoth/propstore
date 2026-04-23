# research-papers-plugin Integration

This document defines the mechanical handoff between `propstore` and
`../research-papers-plugin`.

## What propstore owns

- the claim schema
- validation of source-local claim files
- sidecar compilation
- conflict detection
- the source lifecycle CLI: `pks source ...`

## What the plugin must produce

For each paper directory in `../research-papers-plugin/papers/`, the plugin
must write source-local artifacts such as:

```text
papers/<PaperDir>/concepts.yaml
papers/<PaperDir>/claims.yaml
papers/<PaperDir>/justifications.yaml
papers/<PaperDir>/stances.yaml
```

Those files should already conform to propstore's source-local schemas. In practice,
that means:

- top-level `source` mapping naming the source branch
- top-level typed lists (`concepts`, `claims`, `justifications`, `stances`)
- source-local IDs that are stable within the source branch
- concept references that resolve through the source branch concept inventory
- CEL conditions using propstore canonical names when appropriate

## Source-branch behavior

Propstore no longer scans a `papers/` directory and bulk-imports it. The plugin
or orchestrator should call the source CLI explicitly:

```text
pks source init <PaperDir> ...
pks source add-concepts <PaperDir> --batch papers/<PaperDir>/concepts.yaml
pks source add-claim <PaperDir> --batch papers/<PaperDir>/claims.yaml
pks source add-justification <PaperDir> --batch papers/<PaperDir>/justifications.yaml
pks source add-stance <PaperDir> --batch papers/<PaperDir>/stances.yaml
pks source finalize <PaperDir>
pks source promote <PaperDir>
```

During source ingestion, local IDs are rewritten to canonical artifact IDs and
preserved as source-local logical IDs on the source branch.

## Recommended workflow

From `../research-papers-plugin`:

1. Run the paper extraction flow and produce `claims.yaml` alongside
   `concepts.yaml`, `justifications.yaml`, `stances.yaml`, `notes.md`,
   `description.md`, `abstract.md`, and `citations.md`.
2. Keep markdown as the human-facing view, but treat the YAML artifacts as the
   machine-readable source package.

From `propstore`:

1. Run the `pks source ...` sequence for each source package
2. Run `pks validate`
3. Run `pks build`
4. Query the sidecar with `pks sidecar query ...`

## Current state

The import bridge is gone on the `propstore` side. The remaining integration
work is to have the plugin orchestrate `pks source` directly and emit the full
source package consistently:

- paper-reader must write or stage source-local artifacts
- register-concepts must populate `concepts.yaml`
- extract-claims, extract-justifications, and extract-stances must target the
  source package files that `pks source` consumes
