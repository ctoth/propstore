# Semantic Family Registry Convergence Workstream

Date: 2026-04-18

## Goal

Make semantic family definitions the single production source of truth for
repository schema facts. A semantic family is a repository-owned kind of
semantic artifact such as claim, concept, form, context, stance, worldline,
predicate, or rule. The registry owns each family's root directory, document
type, artifact family, import participation, reference/index behavior, contract
version, and cross-family foreign keys.

This is a direct cutover. We control both sides of the interface, so there are
no compatibility shims, duplicate dispatch paths, fallback readers, or old/new
parallel production paths.

## Current Problems

- `propstore.storage.repository_import` hardcodes semantic roots and path-root
  family dispatch.
- Repository import hardcodes claim/concept/stance normalization and reference
  rewrite sequencing by literal path prefix.
- `propstore.artifacts.families` defines `ArtifactFamily` objects, but root
  directories, source collection fields, reference paths, FK declarations, and
  import policies still live elsewhere.
- `propstore.compiler.references` owns semantic FK declarations separately from
  family and claim-type declarations.
- `rules` and `predicates` have typed document schemas and repository
  directories but are not first-class artifact/import families.
- `Repository.init`, grounding loaders, artifact-code helpers, and several
  workflows spell semantic roots directly.

## Target Architecture

Add a propstore-owned semantic family registry. Quire remains generic; propstore
owns the domain meanings.

The registry exposes:

- `by_name(name)`
- `by_root(root)`
- `family_for_path(path)`
- `artifact_families()`
- `importable()`
- `import_roots()`
- `init_roots()`
- `foreign_keys()`

Each family definition owns:

- stable family name
- contract version
- `ArtifactFamily`
- document type
- root directory
- optional collection field
- whether repository init creates the root
- whether repository import imports the root
- import order
- optional import normalizer
- reference rewrite declarations
- reference index declaration
- foreign key declarations

## Family Set

The first complete registry must include:

- `claim`
- `concept`
- `context`
- `form`
- `stance`
- `worldline`
- `predicate`
- `rule`

Source-branch-only artifacts, merge manifests, concept alignments, and proposal
stance families remain artifact families but are not canonical semantic-tree
families unless they become canonical repository roots.

## Repository Import

Repository import must:

1. Read only committed snapshots.
2. Ask the registry for import roots.
3. Ask the registry which family owns each path.
4. Coerce through `DocumentFamilyStore`.
5. Run import normalizers in declared order.
6. Build declared reference lookup maps.
7. Apply declared reference rewrites.
8. Save and delete through artifact transactions.

The importer may own orchestration, branch selection, transaction boundaries,
and result reporting. It must not own semantic root lists, path-to-family
dispatch, or family-specific reference field tables.

## References And Foreign Keys

`propstore.compiler.references.iter_semantic_foreign_keys()` must derive from
the semantic family registry. The standalone FK table goes away.

Claim-type contracts can still declare per-type requirements, but cross-family
reference paths must converge with the registry's FK declarations. There must
not be one string table for claim-type validation and a separate unrelated
string table for compiler FKs.

## Rules And Predicates

Add first-class artifact and semantic families for:

- `predicates/{name}.yaml` with `PredicatesFileDocument`
- `rules/{name}.yaml` with `RulesFileDocument`

Grounding loaders should use these family declarations instead of spelling the
document schemas and roots separately.

## Contract Manifest

The manifest must include semantic family contracts. The contract body must
include root, document type, artifact family name, collection field,
importability, import order, reference index, reference rewrites, and foreign
keys.

The existing checked-in manifest test remains the enforcement mechanism:
changing a semantic family body without a contract version bump fails.

## Tests First

Add or update tests that fail before implementation:

1. The registry contains the complete family set.
2. `Repository.init` roots are derived from the registry.
3. Repository import roots are derived from the registry.
4. Repository import imports `predicates/` and `rules/` from committed
   snapshots and ignores uncommitted worktree changes.
5. Repository import has no local `SEMANTIC_ROOT_DIRS` or local path-root
   family dispatch table.
6. Compiler foreign keys derive from the registry.
7. Semantic family contracts are present in the contract manifest.
8. `rules` and `predicates` are artifact families.

## Execution Phases

### Phase 1: Registry Model

- Add semantic family declaration dataclasses.
- Add the registry object and lookup helpers.
- Declare canonical semantic families.
- Add rule and predicate ref types, relpath helpers, artifact families, and
  list/path ref helpers.

### Phase 2: Contracts

- Emit semantic family contracts from the registry.
- Make FK contracts derive from registry declarations.
- Update checked-in manifest after tests prove the shape.

### Phase 3: Repository Init

- Replace the local semantic directory list in `Repository.init` with registry
  roots.
- Keep non-semantic support directories explicit only if they are not semantic
  families.

### Phase 4: Repository Import

- Replace local import root list with `SEMANTIC_FAMILIES.import_roots()`.
- Replace local path-root dispatch with `SEMANTIC_FAMILIES.family_for_path()`.
- Move concept, claim, and stance import policies behind family declarations.
- Add rule/predicate import coverage.

### Phase 5: Compiler References

- Delete the standalone FK tuple.
- Build `ForeignKeySpec` values from registry declarations.
- Keep domain-specific reference-index construction only where the data shape
  requires it.

### Phase 6: Grounding

- Load predicates and rules through registered family metadata.
- Keep grounding semantics in grounding modules; remove duplicate schema facts.

### Phase 7: Cleanup Gates

- Add focused architectural tests that prevent new importer root lists,
  importer path-root dispatch tables, and standalone FK tables.
- Do not scan prose or tests as production violations.

## Definition Of Done

- One production registry declares semantic roots, artifact families, document
  types, collection fields, importability, reference declarations, and FKs.
- Repository import uses the registry for roots, path ownership, import order,
  and declared policies.
- `rules` and `predicates` are first-class semantic families.
- Compiler FKs derive from the registry.
- Repository init uses registry roots.
- Grounding loaders no longer own rules/predicates root/schema facts.
- Contract manifest covers semantic families and remains current.
- Targeted tests pass.
- Full suite is attempted through the logged pytest wrapper.
- No compatibility shims or old production dispatch paths remain.
