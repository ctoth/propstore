# Workstream CLI/App Surface Convergence

Date: 2026-04-23
Status: COMPLETED
Depends on: `disciplines.md`, `judgment-rubric.md`, `ws-cli-layer-discipline.md`, `ws-z-render-gates.md`
Blocks: honest `docs/gaps.md` cleanup for CLI/app drift
Review context: `../axis-2-layer-discipline.md`, `../axis-1-principle-adherence.md`, `../axis-9-doc-drift.md`, and the standing CLI/app rules in `CLAUDE.md`.

## What triggered this

The first CLI discipline pass extracted a large amount of behavior out of
`propstore.cli`, but the current repo still does not converge on one coherent
app-layer surface.

Current drift:

- `claim` has no `list` or lexical `search`, while `concept`, `form`,
  `context`, `source`, and `worldline` already expose list-style reads.
- claim reads are split across `propstore.app.claims` and
  `propstore.app.claim_views`.
- `propstore.app.concepts` is a large monolith while its CLI family is already
  split by concern.
- `propstore.app.forms` and `propstore.app.contexts` are mostly re-export
  facades rather than clear owner surfaces.
- `predicate`, `rule`, and `micropub` remain asymmetric: write/add or
  inspect-one exists, enumerate/browse does not.
- root verbs still collide semantically: top-level `promote` vs
  `source promote`, top-level `query` vs `world query`.

## Target architecture

The rule for this workstream is simple:

- CLI modules remain presentation adapters only.
- Every repository-bound command family routes through one app-layer owner
  surface.
- Every read surface that exposes claims under visibility policy uses one
  canonical claim read model.
- No old/new read-model dual path survives this workstream.
- No compatibility aliases or temporary wrappers are retained unless Q
  explicitly asks for them.

Canonical owners after convergence:

- Claim reads: `propstore.app.claim_views`
- Claim operational workflows: `propstore.app.claims`
- Concept workflows: split app-layer surfaces under `propstore.app.concepts.*`
  package modules, not one monolith
- Form workflows: real app-layer owner module, not a thin facade
- Context workflows: real app-layer owner module, not a thin facade
- Source workflows: `propstore.app.sources`
- World workflows: `propstore.app.world*`
- Worldline workflows: `propstore.app.worldlines`

## Required command surface at exit

- `pks claim`: `show`, `list`, `search`, `neighborhood`, `validate`,
  `validate-file`, `conflicts`, `compare`, `embed`, `similar`, `relate`
- `pks concept`: keep existing surface; preserve `list`/`search`/`show`
- `pks context`: add `show`, `remove`, `search`
- `pks form`: add `search`
- `pks predicate`: add `list`, `show`
- `pks rule`: add `list`, `show`
- `pks micropub`: add `list`
- `pks source`: add `show` if source documents are first-class authored
  artifacts worth direct inspection
- Root command cleanup: replace ambiguous top-level `promote` and `query` with
  family-specific group surfaces and update every caller

Exit note:

- `pks source show` was deliberately not added. The stable source-facing CLI
  contract remains lifecycle/status/proposal operations under `pks source`;
  there is no separate authored source-document inspection surface that
  justifies a standalone `show` command.

## Phase structure

### Phase CLI-C1 - Lock the canonical claim read model

- Make `propstore.app.claim_views` the only app-layer owner for claim
  read/report surfaces.
- Repoint `pks claim show` to `build_claim_view` or its successor typed report.
- Delete `show_claim` / `show_claim_from_repo` style read ownership from
  `propstore.app.claims`.
- Reduce claim similarity search to candidate-id retrieval only; policy-aware
  projection happens in the claim-view layer.
- Add shared claim-view list/search/neighborhood reports with
  `AppRenderPolicyRequest`.

### Phase CLI-C2 - Fill the missing read surfaces

- Add `pks claim list` and `pks claim search`.
- Add `pks claim neighborhood` instead of leaving neighborhood reporting
  web-only.
- Add `pks context show/remove/search`.
- Add `pks form search`.
- Add `pks predicate list/show`.
- Add `pks rule list/show`.
- Add `pks micropub list`.
- Add `pks source show` only if the authored source document is a stable
  first-class surface; otherwise state explicitly that it is not part of the
  CLI contract.

### Phase CLI-C3 - Converge the app layer itself

- Split `propstore.app.concepts` by concern to mirror the existing CLI package
  structure.
- Replace facade-only `propstore.app.forms` and `propstore.app.contexts` with
  real app-layer request/report modules, or delete the facades and create
  honest owner modules under the app layer.
- Ensure no app-layer read API returns loose dict payloads when a typed report
  is practical.

### Phase CLI-C4 - Finish CLI family structure

- Promote `propstore.cli.claim` to a package with display/search, validation,
  embedding, and relation modules.
- Add layout guards so `claim` cannot regress into one flat workflow bucket.
- Apply the same package split to `predicate` and `rule` if the new read
  surfaces make the flat files non-trivial.
- Centralize shared render-policy option parsing for claim-facing read
  commands.

### Phase CLI-C5 - Deconflict root verbs

- Replace top-level `pks promote` with a proposal-specific family.
- Replace top-level `pks query` with a sidecar-specific family.
- Update docs, tests, and lazy root registration in one pass.
- Delete the old root verb path rather than carrying aliases, unless Q
  explicitly asks for alias retention.

### Phase CLI-C6 - Docs, gaps, and verification

- Update `docs/gaps.md` for any newly observed residual drift.
- Update CLI docs/help text to match the final surface exactly.
- Extend layout tests to guard the new package boundaries and owner routing.
- Run targeted logged pytest slices after each phase, `uv run pyright propstore`,
  then a full logged suite before declaring completion.

## Exit criteria

- `claim` read ownership exists in one place only: the claim-view app layer.
- All missing command families above exist, or the workstream explicitly
  records why a proposed surface is not a real artifact boundary.
- No CLI module owns repository mutation semantics, sidecar policy, or
  world/claim selection logic.
- No ambiguous root verb remains for proposal promotion or sidecar querying.
- New read APIs are typed and policy-aware where claim visibility is involved.
- Old production paths are deleted, not wrapped.

## Red flags

- Adding `claim list/search` directly to `propstore.app.claims`
- Keeping both `app.claims` and `app.claim_views` as live read-model owners
- Adding CLI-local SQL for enumeration surfaces
- Preserving ambiguous root verbs with "temporary" aliases
- Expanding `app.concepts` further before splitting it
- Calling a thin re-export facade "the app layer" when the real owner is
  somewhere else

## Review checks

- `rg -n -F "import click" propstore/app propstore/world propstore/source propstore/forms propstore/context`
  shows no owner-layer Click leakage introduced by this workstream.
- `rg -n -F "build_claim_view" propstore` shows CLI/web/read surfaces
  converging on one claim read model.
- `rg -n -F "@claim.command" propstore/cli/claim` shows commands living
  outside the group module once the package split lands.
- Logged pytest evidence exists for each phase plus a final full-suite run.
- `uv run pyright propstore` is green on the configured package surface.
