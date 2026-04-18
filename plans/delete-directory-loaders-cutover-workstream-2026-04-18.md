# Delete Directory Loaders Cutover Workstream

Date: 2026-04-18

## Purpose

Delete the old directory/path loader layer for semantic artifacts and update
production callers to use the Quire family API directly.

This is intentionally short. The work is not to design another abstraction. The
work is deletion, then iteration until tests pass.

## Quire Family Understanding

The provisional model for Quire-owned family registries lives in the Quire repo:

`../quire/plans/family-registry-provisional-understanding-2026-04-18.md`

This propstore workstream only tracks the downstream deletion/cutover work.

## Rule

Delete first.

Do not replace deleted surfaces with renamed wrappers such as
`load_claim_artifacts`, `claims_root_path`, `family_root`, or other helper-shaped
versions of the same directory abstraction.

After deletion, the resulting import errors, attribute errors, test failures, and
literal remaining references are the work queue. Fix each caller by using the
target API directly:

```python
repo.artifacts.list(FAMILY, branch=..., commit=...)
repo.artifacts.load(FAMILY, ref, commit=...)
repo.artifacts.require(FAMILY, ref, commit=...)
repo.artifacts.handle(FAMILY, ref, commit=...)
repo.artifacts.save(FAMILY, ref, document, ...)
repo.artifacts.prepare(FAMILY, ref, document, ...)
```

## Delete

Delete production surfaces whose job is "given a directory/root/path, enumerate
or load semantic artifacts" for all semantic families:

- path-era compiler entrypoints that accept repository semantic directories,
  including `build_compilation_context_from_paths`
- claim directory loaders, including `load_claim_files`
- concept directory loaders when used for repository-native semantic loading
- context directory loaders when fed repository semantic roots
- form directory loaders/validators when fed repository semantic roots
- predicate and rule directory loaders
- stance, worldline, micropub, justification, and source loaders that enumerate
  semantic storage directories

Delete root/path variables that exist only to feed those loaders:

- `claims_root`, `claims_dir`
- `concepts_root`, `concepts_dir`
- `forms_root`, `forms_dir`
- `contexts_root`, `contexts_dir`
- `predicates_root`, `predicates_dir`
- `rules_root`, `rules_dir`
- `stances_root`, `stances_dir`
- any production `repo.tree() / "<semantic-root>"` or
  `tree / "<semantic-root>"` whose purpose is semantic artifact loading

Delete non-canonical path surfaces too:

- source branch fixed filenames outside placement declarations
- proposal branch constants outside placement declarations
- merge manifest paths outside placement declarations

## Keep

Path/file loading may remain only at explicit external IO boundaries, such as:

- CLI options that validate an arbitrary user-provided file or directory
- tests that intentionally exercise loose file IO independent of a repository
- packaged seed-resource loading from package resource directories

These boundaries must not become repository-native semantic loading paths.
They must pass already-loaded typed documents into compiler APIs rather than
calling repository-oriented path/context builders.

## Iterate

1. Delete one old production surface.
2. Search for remaining production references.
3. Run the smallest relevant logged pytest slice.
4. Fix failures by moving callers to direct family-store operations.
5. Keep the reduction if tests improve or pass.
6. Revert the slice if it produces no kept reduction after two focused attempts.
7. Continue until the old production loader/root/path surface is gone.

## Completion

The workstream is complete when:

- production code no longer imports semantic-family directory loaders for
  repository-native artifacts
- production code no longer creates semantic `*_root` variables solely to load
  repository artifacts
- production code uses `repo.artifacts` and `ArtifactFamily` directly for
  repository-native semantic artifact loading
- placement declarations are the only production source of semantic storage
  roots, source fixed filenames, proposal branches, and merge manifest paths
- logged targeted tests and then the full suite pass
