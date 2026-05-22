# Non-Core Fixed-Point Deletion Procedure - 2026-05-21

Status: mechanical fixed-point procedure for tracked Python files outside
`propstore/core`.

This is not a big inventory workstream. Do not spend a phase building a
complete repo-wide catalog before deleting code. The procedure is applied to a
small slice, the slice is edited, gates are run, and the remaining failures
choose the next slice. Repeat until the selected gates produce no new work.

## Governing Principles

Quire owns IO mechanics and generic infrastructure: artifact/document IO,
codecs, placement, storage roots, derived-store lifecycle, SQLAlchemy mapping,
table/session access, generated models, scalar/enum/JSON adapters, family
metadata lookup, main-model lookup, and reference/FK lookup.

Propstore owns semantic meaning only: semantic family declarations, validators,
compiler behavior, source-local authoring semantics, promotion/lowering policy,
world reasoning, grounding, argumentation, and behavior-only methods on family
models.

Field, schema, model, payload, row, constructor, and reference shape is written
once. It lives in Quire charter metadata or the exact Propstore semantic owner.
It does not live in helper families, DTOs, row classes, placeholder records,
manual kwargs builders, hand-authored mapped fields, broad normalizers, or
runtime repair constructors.

Delete old production surfaces first. Do not keep wrappers, aliases, adapters,
shims, fallback readers, bridge normalizers, compatibility branches, re-export
modules, renamed helpers, or old/new dual paths.

Runtime APIs receive typed/domain objects. `dict`, `Mapping[str, Any]`,
`object`, mixed `str | typed`, arbitrary stringification, and source-local
handles may not pass beyond the exact boundary that owns them.

Propstore semantic interpretation is applying domain rules to typed data. It is
not YAML/JSON/SQLite decoding, dict repair, enum coercion, missing-field
defaulting, old-shape rewriting, generic row loading, or generic reference
lookup.

Completion is mechanical. A symbol is complete only when its old path is gone
or the exact allowed owner/gate is recorded. A file is complete only after every
symbol in the file has a decision and the derived file disposition is applied.

## Fixed-Point Loop

The loop is the work:

1. Pick a bounded owner slice.
2. Read the files in that slice completely.
3. Decompose only those files per symbol/surface.
4. Delete, move, consolidate, or rewrite the first wrong surfaces in that
   slice. Do not just record them.
5. Run the slice gates.
6. Commit the kept source/procedure changes.
7. Record the iteration result: surfaces removed, surfaces moved, gates still
   failing, and the next slice chosen by those failures.
8. Repeat on the same slice until it has no wrong surfaces or the next required
   capability is in Quire.

Do not broaden to another slice because another failure is interesting. A slice
ends only when its gates are zero-hit, all remaining symbols have owner proof,
or the procedure records a named Quire capability blocker.

## Slice Unit

Operate per symbol/surface, not per file and not per repo-wide inventory.

For the current slice, decompose each file into these surfaces:

- module docstring and top-level comments that encode policy;
- imports;
- constants and module-level state;
- classes and dataclasses;
- public functions;
- private helpers;
- nested helper functions when they own policy or conversion;
- package re-exports and `__all__`;
- direct table/model/session lookup expressions;
- loose payload constructors and normalizers;
- compatibility/fallback branches;
- tests-only or presentation-only rows if they appear in production modules.

## Symbol Decision Values

Use exactly one decision for each surface.

### `delete`

Use `delete` when the surface is one of:

- old production path after a replacement exists or is required;
- wrapper, alias, shim, adapter, fallback, bridge, compatibility branch, or
  renamed old abstraction;
- helper that converts loose `object`/`str`/`dict` into semantic meaning after
  the exact boundary;
- row/DTO/record/model that restates fields owned by Quire charters, generated
  models, or one semantic owner;
- Propstore-local table/model registry or direct
  `schema.model("...")` / `schema.table("...")` / `derived.schema...` selector
  where Quire generic metadata/session APIs should be used;
- package re-export whose only job is to preserve a broad convenience or old
  import surface;
- test or fixture pattern that preserves dict-shaped or old API usage instead
  of typed/domain usage.

Deletion final state must name the zero-hit search gate.

### `move`

Use `move` when behavior is real but the owner is wrong.

Allowed target owners:

- `propstore.cli.*`: Click options/commands, command-string parsing, typed
  request construction, result rendering, exit-code mapping only.
- `propstore.app.*`: application workflow/report orchestration only; no
  reusable storage/query/domain semantics.
- `propstore.source.*`: source-local authoring, proposal, finalize, promote,
  and explicit lowering of source-local references before canonical writes.
- `propstore.families.<family>.*`: family semantic documents, validators,
  compiler hooks, identity/lowering policy, and behavior-only model methods.
- `propstore.world.*`: world runtime, query, graph, ATMS, activation,
  reasoning, intervention, and value resolution.
- `propstore.worldline.*`: journal, capture, replay, trace, revision history.
- `propstore.heuristic.*`, `propstore.grounding.*`,
  `propstore.asp_*`/argumentation owners: only their domain-specific algorithms.
- `quire`: generic storage, family metadata, main-model lookup, reference/FK
  lookup, session/table access, generated model construction, scalar/enum/JSON
  storage adapters, FTS/vector machinery, and derived-store lifecycle.

Move final state must delete the old import path. No re-export shim remains.

### `consolidate`

Use `consolidate` when two or more surfaces implement the same real behavior.

The target must be the exact owner. Do not consolidate into broad `helpers.py`,
`utils.py`, `normalize_*`, `coerce_*`, or a generic service object.

Consolidation final state must name all duplicate symbols and the one surviving
owner symbol.

### `rewrite`

Use `rewrite` when behavior is needed but representation violates the rules.

Rewrite triggers:

- accepts `dict`, `Mapping[str, Any]`, `object`, mixed `str | typed`, or
  source-local handles past the owner boundary;
- stringifies arbitrary values to create semantic IDs or enum values;
- hardcodes field names, table names, family names, or constructor kwargs that
  should come from typed objects, Quire charters, or family metadata;
- silently repairs old shapes, defaults malformed data to empty values, or
  accepts compatibility variants;
- uses direct schema/table/model lookup instead of family metadata/session APIs.

Rewrite final state must name the typed/domain input and the owner metadata API.

### `keep`

Use `keep` only when all are true:

- correct owner layer;
- owns real semantic behavior or presentation behavior, not generic mechanics;
- does not duplicate field/schema/reference/storage shape;
- does not preserve an old or convenience import path;
- does not parse loose payloads after the exact boundary;
- public API carries typed/domain objects;
- literal search does not reveal an equivalent owner elsewhere.

Keep final state must name why the symbol is the exact owner.

### `quire-needed`

Use `quire-needed` only when the Propstore surface is wrong to keep but cannot
be deleted until Quire exposes a generic capability.

The missing capability must be named exactly, such as:

- family main-model lookup;
- reference/FK lookup over declared surfaces;
- session/table access by family metadata;
- generated model construction;
- generic JSON/enum/scalar storage adapter;
- generic FTS/vector integration.

Do not add a Propstore workaround. The next action is Quire capability, push,
pin, then delete the Propstore surface.

## Boundary Rules

### Source Boundary

`propstore.source.*` may own source-local authoring, source proposals, source
finalize, source promotion, and explicit lowering from source-local references
to canonical typed family references.

It may not own generic decode mechanics, generic enum/scalar coercion, old-shape
compatibility, generic family lookup, or direct sidecar table/model routing.

Source-local handles must not leak into canonical/master runtime paths.

### Presentation Boundary

App/CLI/web rows may stay only when they are pure presentation:

- no storage identity authority;
- no semantic field authority;
- no family lookup;
- no domain parsing;
- no reusable business logic.

If a presentation object starts carrying storage or semantic shape, delete it
or move the behavior to the owner.

### IO Boundary

Quire owns generic IO. In Propstore, an IO-boundary exception is only a named
semantic/request boundary after Quire or the request layer has decoded bytes.

The parser must convert immediately to typed/domain objects and hard-fail
malformed input. It must not be reused as runtime normalization.

## Required Per-Slice Procedure

For each bounded slice:

1. Read the whole file.
2. List every surface in file order.
3. For each surface, assign one decision value.
4. Record the final owner.
5. Record the exact action.
6. Record the reason using the governing principles.
7. Record the search gate that proves the old surface is gone.
8. Execute the first deletion/move/rewrite actions for the slice.
9. Run the gates.
10. Derive file disposition only for files touched by the slice.

Do not skip small helpers, imports, nested functions, or `__all__` entries.
Do not wait for a complete non-core inventory before editing.

## Derived File Disposition

After every symbol is classified, derive exactly one file disposition:

- `keep-file`: every remaining symbol is correctly owned by this file.
- `split-file`: some symbols remain here and others move/delete/rewrite.
- `move-file`: all real behavior moves to one other owner, then this file is
  deleted.
- `delete-file`: every symbol is deleted or moved elsewhere; file becomes empty.
- `shallow-init`: package initializer keeps only package docstring or a narrow
  intentionally owned export surface.
- `quire-needed`: file cannot be deleted until named Quire capability lands.

If a file becomes empty after actions, delete it. If a package becomes empty
after deleting files, delete the package directory only when no tracked files
remain.

## Iteration Record Template

Use this exact shape:

```markdown
## Iteration N - slice-name - YYYY-MM-DD

Slice files read:
- `path/to/file.py`

Actions executed:
- `symbol_or_surface`
  - Decision: `delete|move|consolidate|rewrite|keep|quire-needed`.
  - Final owner: `owner.path` or `none`.
  - Edit: concrete edit performed or Quire blocker named.
  - Reason: principle-backed reason.
  - Gate: exact `rg`/test/type gate.

Gate results:
- Pass: ...
- Fail: ...

Derived file disposition:
- `path/to/file.py`: `keep-file|split-file|move-file|delete-file|shallow-init|quire-needed`.

Next slice:
- Chosen from failing gate: ...
```

## Agent Prompt

Use this prompt for one bounded fixed-point iteration:

```text
Run one fixed-point deletion iteration on the assigned tracked Python files
outside propstore/core using
workstreams/non-core-per-symbol-deletion-audit-procedure-2026-05-21.md.

Do not build a full inventory. Do not use git log. Read each assigned file
completely. Decompose it per symbol/surface in file order. Execute the first
wrong-surface deletions/moves/rewrites in the slice. Use deletion-first: delete
the old surface, then fix callers from failures. Assign exactly one decision
value to every surface touched in this iteration: delete, move, consolidate,
rewrite, keep, or quire-needed.

Apply the project rules strictly:
- Quire owns generic IO/storage/schema/session/reference/family mechanics.
- Propstore owns semantic meaning only.
- Field/schema/model/payload/row/constructor shape is written once.
- Delete old production surfaces first.
- No wrappers, aliases, adapters, shims, fallback readers, compatibility
  branches, re-export modules, renamed helpers, or old/new dual paths.
- Runtime receives typed/domain objects.
- Source-local authoring state stays source-local and is lowered explicitly
  before canonical writes.

Run the slice's literal gates after edits. Commit each intentional edit slice
with explicit path-limited git commands. Write one iteration record to the path
assigned by the coordinator using the template in the procedure. Do not modify
files outside the assigned slice and assigned iteration record.
```

## Search Hints

Run targeted searches as evidence, not as substitutes for reading:

```powershell
rg -n -F -- "coerce_" <paths>
rg -n -F -- "normalize_" <paths>
rg -n -F -- "from_payload" <paths>
rg -n -F -- "from_mapping" <paths>
rg -n -F -- "from_row_mapping" <paths>
rg -n -F -- "schema.model(" <paths>
rg -n -F -- "schema.table(" <paths>
rg -n -F -- "derived.schema" <paths>
rg -n -F -- "fallback" <paths>
rg -n -F -- "compat" <paths>
rg -n -F -- "legacy" <paths>
rg -n -- "Mapping\\[str, Any\\]|dict\\[str, Any\\]|object" <paths>
```

Every nonzero hit in the current slice must either become an edit in this
iteration, be recorded as an owner-proven keep, or name a Quire blocker. A
zero-hit search does not replace reading the slice.
