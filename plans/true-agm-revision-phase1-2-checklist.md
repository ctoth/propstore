# True AGM Revision — Phase 1/2 Checklist

**Date:** 2026-03-29
**Depends on:** `proposals/true-agm-revision-proposal.md`
**Scope:** concrete implementation checklist for Phase 1 (belief-base projection + entrenchment) and Phase 2 (single-shot contraction/revision)

---

## Merge Dependency Decision

**Do not wait for merge objects to land before starting Phase 1 and Phase 2.**

Reason:

- Phase 1 and Phase 2 can be built entirely on top of existing `WorldModel`, `BoundWorld`, and ATMS support surfaces.
- The current merge work in `proposals/multi-source-structured-merge.md` is only a blocker for consumers that want to revise **merged partial frameworks** or branch-local argumentation summaries directly.
- V1 revision should operate on a scoped bound world, not on merge objects.

Safe to do now:

- belief-base projection from `BoundWorld`
- entrenchment computation from ATMS support
- one-shot `expand` / `contract` / `revise`
- explanation surfaces
- CLI commands for revision over the current sidecar-backed world

Defer until merge-object boundary is stable:

- any adapter from merged partial frameworks into revision state
- any AF-level revision path that depends on the new merge object
- any attempt to interpret merge outputs as revision states

Hard guard:

- Phase 1 and Phase 2 code must not call `propstore/repo/ic_merge.py`

---

## Existing Code Surface

### World / store layer already available

- `propstore/world/model.py`
  - `WorldModel.bind(...)`
  - `WorldModel.get_claim(...)`
  - `WorldModel.claims_for(...)`
  - `WorldModel.explain(...)`

- `propstore/world/bound.py`
  - `BoundWorld.active_claims(...)`
  - `BoundWorld.collect_known_values(...)`
  - `BoundWorld.value_of(...)`
  - `BoundWorld.atms_engine(...)`
  - `BoundWorld.explain(...)`

- `propstore/world/atms.py`
  - `ATMSEngine.essential_support(...)`
  - label propagation and future-analysis substrate

- `propstore/world/hypothetical.py`
  - useful as a contrast surface
  - should **not** be used as the implementation of revision

### CLI surfaces already available

- `propstore/cli/compiler_cmds.py`
  - existing `world` group
  - existing `world_hypothetical(...)`
  - existing ATMS commands
  - existing `world_fragility(...)`

- `propstore/cli/worldline_cmds.py`
  - future integration surface for recording revision episodes

### Repo layer already available

- `propstore/repo/git_backend.py`
  - branch-aware commit/read/log

- `propstore/repo/branch.py`
  - branch-local sequencing and merge-base support

- `propstore/repo/ic_merge.py`
  - merge-only operators
  - must remain outside Phase 1/2 revision code paths

---

## Phase 1 Goal

Build a revision-facing finite belief base from the current scoped world and derive an explainable entrenchment ordering from ATMS support.

Deliverables:

- `propstore/revision/state.py`
- `propstore/revision/projection.py`
- `propstore/revision/entrenchment.py`
- tests for projection and ordering

---

## Phase 1 Checklist

### 1. Create revision package skeleton

Files:

- `propstore/revision/__init__.py`
- `propstore/revision/state.py`
- `propstore/revision/projection.py`
- `propstore/revision/entrenchment.py`

Tasks:

- define `RevisionScope`
- define `BeliefAtom`
- define `BeliefBase`
- define a minimal `EntrenchmentReport` or equivalent return object

Acceptance:

- package imports cleanly
- no runtime dependency on merge modules

### 2. Add scoped belief-base projection from `BoundWorld`

Primary file:

- `propstore/revision/projection.py`

Existing code to consume:

- `propstore/world/bound.py`
- `propstore/world/model.py`
- `propstore/world/atms.py`

Tasks:

- implement `project_belief_base(bound: BoundWorld, *, include_assumptions: bool = True) -> BeliefBase`
- include V1 atoms:
  - exact-support claims
  - active assumptions relevant to those claims
- exclude:
  - merged objects
  - synthetic merge buckets
  - AF-level artifacts
  - non-exact support unless explicitly marked for future phases

Acceptance:

- identical `BoundWorld` inputs yield identical projected belief bases
- projected atom ids are stable and deterministic
- projection explains where each atom came from

### 3. Define atom identity rules

Primary file:

- `propstore/revision/projection.py`

Tasks:

- define stable atom ids for:
  - claims
  - assumptions
- ensure no hidden dependence on Python object identity
- make payloads serializable for later worldline capture

Acceptance:

- atom ids survive reruns
- atom ids are reproducible from sidecar-backed inputs

### 4. Derive entrenchment from ATMS support

Primary file:

- `propstore/revision/entrenchment.py`

Existing code to consume:

- `BoundWorld.atms_engine()`
- `ATMSEngine.essential_support(...)`
- support labels already surfaced through ATMS inspection
- fragility/entrenchment grounding in `proposals/fragility-plan.md`

Tasks:

- implement `compute_entrenchment(bound: BoundWorld, base: BeliefBase, *, overrides: ... = None) -> ...`
- start with the V1 recommended ordering shape:
  1. explicit override categories
  2. exact-support status
  3. essential-support sensitivity
  4. supporting-environment coverage
  5. stable tiebreak

- produce explanation fields for each atom:
  - support count
  - essential support
  - override source if any

Acceptance:

- entrenchment is deterministic
- stronger-supported toy atoms outrank weaker-supported ones
- explanation is stable and human-readable

### 5. Define override model

Primary files:

- `propstore/revision/state.py`
- `propstore/revision/entrenchment.py`

Tasks:

- define the V1 override structure
- support:
  - category-level priority
  - source/context-level priority
  - optional per-claim override
- do **not** add arbitrary plugin hooks yet

Acceptance:

- overrides are optional
- without overrides, entrenchment is fully derived
- with overrides, explanation clearly shows which override fired

### 6. Add BoundWorld delegation hooks for Phase 1 inspection

Primary file:

- `propstore/world/bound.py`

Tasks:

- add lightweight methods that delegate into the revision package:
  - `revision_base(...)`
  - `revision_entrenchment(...)`

- keep operator logic outside `BoundWorld`

Acceptance:

- `BoundWorld` remains a descriptive view
- delegation only; no contraction/revision logic embedded here yet

### 7. Add Phase 1 CLI inspection commands

Primary file:

- `propstore/cli/compiler_cmds.py`

Tasks:

- add under the existing `world` group:
  - `pks world revision-base`
  - `pks world revision-entrenchment`

- mirror the style of existing ATMS commands

Acceptance:

- commands can inspect the projected base and ordering for a scoped world
- commands do not mutate source storage

---

## Phase 1 Tests

Add tests in:

- `tests/test_revision_projection.py`
- `tests/test_revision_entrenchment.py`

Core tests:

- stable projection under repeated runs
- exact-support claims appear; non-exact-only claims do not in V1
- assumptions linked to projected claims are present
- entrenchment ordering is deterministic
- overrides outrank computed defaults when configured
- no revision code imports `propstore/repo/ic_merge.py`

Optional cross-check tests:

- compare entrenchment ordering against toy ATMS essential-support scenarios
- ensure projection works identically on a plain `BoundWorld` regardless of whether the repo is git-backed

---

## Phase 2 Goal

Implement true one-shot expansion, contraction, and revision over the projected belief base, with operator-based semantics and local fixed-point stabilization before returning.

Deliverables:

- support/incision-ready belief-base structures
- `propstore/revision/operators.py`
- `propstore/revision/explain.py`
- `RevisionResult`
- `BoundWorld` delegation methods
- CLI commands for `expand`, `contract`, `revise`, `revision-explain`

---

## Phase 2 Checklist

### 1. Strengthen belief-base structures for support-sensitive contraction

Primary files:

- `propstore/revision/state.py`
- `propstore/revision/projection.py`

Tasks:

- extend the projected revision state so contraction can operate on support, not just top-level atoms
- expose for each projected claim atom:
  - supporting environments / support sets
  - essential support where available
  - stable assumption ids participating in each support set
- keep the representation serializable and deterministic
- do **not** yet implement operator behavior here

Acceptance:

- the projected belief base makes support/incision candidates explicit
- later operator code can choose incision sets without re-deriving support structure ad hoc
- the support representation remains independent of merge-layer objects

### 2. Add operator surface

Primary file:

- `propstore/revision/operators.py`

Tasks:

- implement:
  - `expand(...)`
  - `contract(...)`
  - `revise(...)`

- define `revise` in terms of contraction + expansion
- define V1 contraction over an explicit conflict/support basis, not as direct claim deletion
- compute a minimal low-entrenchment incision set over the support structure
- keep operator API pluggable for later iterated operator families

Acceptance:

- operators work over `BeliefBase` + entrenchment + input atom
- contraction explanations identify the incision set and affected support
- no merge-layer dependencies

### 3. Define revision input adapters

Primary files:

- `propstore/revision/operators.py`
- `propstore/revision/projection.py`

Tasks:

- support V1 inputs:
  - existing claim id
  - synthetic claim
  - assumption

- normalize all inputs into a revision atom form

Acceptance:

- caller can revise by existing or exploratory input without storage mutation

### 4. Implement local post-revision stabilization

Primary files:

- `propstore/revision/operators.py`
- `propstore/revision/projection.py`

Tasks:

- after each operator fires:
  - recompute acceptance on the projected base
  - recompute affected derived consequences
  - iterate until local fixed point

- explicitly keep this as an evaluation loop for one episode

Acceptance:

- stabilized result is returned, not an intermediate state
- rerunning stabilization on a stabilized result is idempotent

### 5. Add explanation surface

Primary files:

- `propstore/revision/explain.py`
- `propstore/revision/state.py`

Tasks:

- define the default explanation contract:
  - accepted atoms
  - rejected atoms
  - incision set
  - support sets cut by the incision
  - ranking rationale
  - support-trace-on-demand hook

- distinguish:
  - dropped by lower entrenchment
  - retained by stronger support
  - dropped because supporting assumptions were incised
  - unchanged because irrelevant to input

Acceptance:

- every contraction/revision result includes actionable rationale

### 6. Add BoundWorld delegation hooks for operators

Primary file:

- `propstore/world/bound.py`

Tasks:

- add:
  - `expand(...)`
  - `contract(...)`
  - `revise(...)`
  - `revision_explain(...)`

- each should delegate into `propstore/revision/*`

Acceptance:

- `BoundWorld` is the entry surface, not the operator owner

### 7. Add Phase 2 CLI commands

Primary file:

- `propstore/cli/compiler_cmds.py`

Tasks:

- add under `world`:
  - `pks world expand`
  - `pks world contract`
  - `pks world revise`
  - `pks world revision-explain`

- follow the existing `world_hypothetical(...)` and ATMS command style
- make it obvious in help text that these commands do not mutate source YAML

Acceptance:

- commands work over the current scoped sidecar-backed world
- command output surfaces accepted/rejected atoms and reason summary

### 8. Decide whether to add worldline capture now

Primary files:

- `propstore/worldline.py`
- `propstore/cli/worldline_cmds.py`

Default:

- **do not add declarative revision inputs to worldlines in Phase 2**
- **do allow later code to serialize revision results into worldline results**

Reason:

- Phase 2 only defines one-shot revision over a scoped `BoundWorld`
- `RevisionResult` is an operation result, not yet a durable iterated epistemic-state schema
- adding worldline-declared revision inputs now would risk freezing the wrong persistence shape before Phase 3 defines explicit iterated state
- Phase 3 should decide what is replayed:
  - one revision episode
  - a persistent epistemic state snapshot
  - or both, with distinct datatypes

Tasks:

- if minimal capture is cheap, add a field under `WorldlineResult.argumentation` sibling or a new revision payload later
- do not redesign `WorldlineDefinition` in this slice

Acceptance:

- no Phase 2 dependency on worldline schema changes

---

## Phase 2 Tests

Add tests in:

- `tests/test_revision_state.py`
- `tests/test_revision_operators.py`
- `tests/test_revision_cli.py`

Core tests:

- projected belief base exposes deterministic support/incision candidates
- essential support is available to explanation and contraction code
- revision success
- contraction removes a minimal low-entrenchment incision set over support
- rejected claim atoms are explained as consequences of support loss
- irrelevant input is vacuous
- Levi identity holds at the package’s operational level
- Harper round-trip is consistent with package semantics
- local fixed-point stabilization converges
- stabilization rerun is idempotent
- source YAML and repo refs are unchanged after revision calls
- revision code path never calls `propstore/repo/ic_merge.py`

Integration tests:

- `BoundWorld.revise(...)` works on a real sidecar-backed world
- revising by synthetic claim does not mutate the base world
- revision CLI works alongside existing `world hypothetical`
- `HypotheticalWorld` still behaves as overlay, not revision

---

## Explicit Out-Of-Scope For Phase 1/2

- iterated revision state
- OCF / preorder persistence
- worldline-declared revision episodes
- AF-level revision adapters
- any merged-partial-framework consumer
- any code that interprets merge outputs as revised belief states

---

## Exit Criteria Before Starting Phase 3

Do not start iterated revision until all of these are true:

- projected belief base is stable and explainable
- one-shot operators are implemented
- local stabilization is in place
- revision and merge code paths are mechanically separated
- CLI surface is usable for manual inspection
- tests prove no source mutation and no merge/revision conflation
