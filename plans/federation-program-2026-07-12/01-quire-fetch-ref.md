# Slice 1 - Quire Fetch One Ref

Status: active candidate.

## Outcome

`GitStore` fetches one advertised Git ref's reachable object closure from a caller-supplied transport location, then publishes the fetched commit to a caller-supplied local ref under compare-and-swap.

## Owner

Quire `GitStore`; Dulwich remains the transport implementation.

## Scope

- `../quire/quire/git_store.py`
- `../quire/tests/test_git_store.py`
- `../quire/tests/test_git_properties.py`
- `../quire/README.md`

## Required behavior

- Inputs: transport location, remote `RefName`, local `RefName`, mandatory expected local-ref value.
- Fetch only the selected ref's reachable closure.
- Validate that the advertised target is a commit.
- Move the local ref only after fetch and CAS validation succeed.
- Return the fetched commit SHA.
- Missing remote ref, stale local ref, transport failure, or invalid object type leaves every local ref unchanged.
- Re-fetching an unchanged ref is idempotent.

## Forbidden substitutions

- no remote manager, sender, backend adapter, location registry, lazy overlay, or atom API;
- no Propstore vocabulary or semantic normalization;
- no schema negotiation, merge, trust, or import policy;
- no `ArtifactAddress` repository field in this slice.

## Gates

- Local-path transport against disk and memory destinations.
- Selected snapshot is byte-identical and readable through existing tree APIs.
- Unrelated refs and source repository remain unchanged.
- Source advancement fetches the new closure and CAS-updates the tracking ref.
- `uv run pytest tests/test_git_store.py tests/test_git_properties.py`
- `uv run pyright quire`
- `uv run pytest`
- One live HTTP or SSH fetch proof before claiming network transport complete.

## Completion

Commit and publish the Quire slice. Propstore pinning and remote-import consumption are separate later slices.
