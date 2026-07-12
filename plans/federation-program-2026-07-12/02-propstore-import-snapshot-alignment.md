# Slice 2 - Align Imported KB Snapshots

Status: queued. Activate `protocols:cleanup-refactor` before mutation.

## Outcome

Two committed Propstore repositories import onto distinct pinned import branches and produce one durable, open, partial-argumentation concept-alignment proposal without merging either KB or collapsing same-named concepts.

## Owners

- Repository snapshot normalization: `propstore.importing.snapshot_passes`.
- Alignment semantics: `propstore.source.alignment`.
- Durable alignment document: `propstore.families.alignment`.

## Scope

- `propstore/importing/snapshot_passes.py`
- `propstore/source/stages.py`
- `propstore/source/alignment.py`
- `propstore/families/alignment.py`
- `propstore/cli/concept/alignment.py`
- focused import/alignment tests

## Required behavior

- Imported concept identity remains namespaced by repository origin; canonical-name equality never merges candidates.
- Claim-to-concept, stance-to-claim, and context references remain branch-local and valid.
- Alignment reads typed concepts from pinned import commits through family APIs.
- Each alignment argument records repository origin, source commit, import branch/commit, concept artifact identity, ontology reference, lexical entry, definition, and form.
- Repeating identical imports and alignment produces identical semantic documents.
- Master remains unchanged.

## Forbidden substitutions

- no `align_imports` wrapper, adapter, bridge normalizer, or fallback reader;
- no loose proposal dictionaries;
- no name/token/Jaccard identity decision;
- no unconditional `sameAs` closure or union-find;
- no flattening import branches into master before alignment;
- no branch-name parsing as provenance.

## Gates

- Same-named rival concepts remain independently addressable.
- Shared ontology identity plus conflicting definitions becomes attack.
- Distinct ontology identities remain distinct even with matching names.
- Imported provenance remains `STATED` and retains source commit.
- Logged focused pytest gates, `uv run pyright propstore`, Ruff, and `git diff --check`.

## Completion

One committed Propstore slice proving committed KB snapshots can enter defeasible alignment. No promotion, graph composition, reasoning, or transport work belongs here.
