# Proposal: True AGM Revision Layer for Propstore

**Date:** 2026-03-29
**Status:** Draft
**Grounded in:** local codebase, [reports/research-true-agm-revision-feasibility.md](C:/Users/Q/code/propstore/reports/research-true-agm-revision-feasibility.md), the local paper corpus including Alchourron 1985, Gärdenfors 1988, Dixon 1993, Darwiche 1997, Spohn 1988, Booth 2006, Bonanno 2007/2010, Konieczny 2002, Coste-Marquis 2007, Baumann 2015, Rotstein 2008, Martins 1988, and Shapiro 1998

---

## Problem

Propstore currently has:

- immutable source storage with provenance
- a compiled sidecar and read-only `WorldModel`
- a `BoundWorld` view over active claims and contexts
- an ATMS backend that tracks exact support and bounded additive futures
- branch isolation plus IC merge operators for multi-branch aggregation

What it does **not** have is true belief revision.

Today:

- `docs/atms.md` explicitly says ATMS replay is additive only and not AGM revision
- `docs/semantic-merge.md` correctly separates branch-local revision analogies from merge-time IC merging
- `proposals/multi-source-structured-merge.md` is formalizing merge objects, not revision state

This is the correct boundary. The missing piece is a dedicated revision layer that performs contraction, expansion, and revision over a **derived epistemic state** without mutating source storage or collapsing multi-source merge into a fake revision operator.

---

## Non-Negotiable Rule

**Revision in propstore must operate over derived belief states, contexts, or branch-local theories, never by deleting or canonicalizing source claims in storage.**

Corollaries:

- source YAML remains immutable except by explicit user migration
- ATMS remains a justification engine, not the revision engine
- IC merging remains a merge-time/source-aggregation operation, not the revision operator
- merge objects and revision states must be different datatypes
- fixed-point iteration may be used to evaluate a revision episode, but convergence alone is not the semantics of revision

If this rule is broken, the proposal fails.

---

## Why This Is A Coherent Chunk Of Work

This proposal is a coherent package because:

- the repo already has the necessary descriptive substrate: `WorldModel`, `BoundWorld`, ATMS labels, branch isolation, render-time policies
- the local literature covers one-shot AGM revision, entrenchment, ATMS/AGM translation, iterated revision, and merge separation
- the missing work is architectural: introducing a first-class revision layer and wiring it to existing state providers

This proposal does **not** require finishing every higher-level argumentation-dynamics question up front. It only requires making the revision boundary explicit and implementing the revision object stack in the right order.

---

## What This Proposal Covers

### V1

- one-shot expansion
- one-shot contraction
- one-shot revision via Levi identity
- entrenchment computation from current support structure
- explanation/provenance for what was retracted and why
- non-destructive operation over derived belief states

### Later phases

- iterated revision with first-class epistemic state
- DP-style operator selection and tests
- AF-level or structured-argument revision adapters
- optional persistence of revision-state snapshots for reproducibility

### Explicit non-goals for V1

- replacing the ATMS
- replacing IC merge
- resolving the full AF-level revision problem first
- changing stored claim identity or canonicalization rules
- deleting source claims as a “revision” operation

---

## Required Separation

The architecture must preserve these separations:

### 1. Source storage vs revision state

Stored claims, concepts, justifications, stances, and provenance remain the source of truth. Revision state is a separate derived object built from them.

### 2. ATMS support vs revision operator

ATMS labels and essential support inform entrenchment and explanation, but ATMS is not itself the reviser.

### 3. One-shot AGM vs iterated revision

One-shot revision can be implemented with entrenchment and finite belief-base operations. Iterated revision needs first-class epistemic state beyond “current accepted claims.”

### 4. Within-branch revision vs merge-time aggregation

Linear within-branch epistemic change is revision territory. Multi-parent merge points remain IC-merging territory. Do not route within-branch revision through `ic_merge.py`.

### 5. Claim-level revision vs AF-level revision

Claim/context revision should land first. AF-level and structured-argument revision are downstream consumers or adapters, not the foundation.

---

## Existing Ground We Can Reuse

### In the codebase

- `propstore/world/model.py`
  - read-only world substrate
- `propstore/world/bound.py`
  - environment-bound active world view
- `propstore/world/atms.py`
  - exact support, essential support, bounded future analysis
- `propstore/world/types.py`
  - render policies and world-facing dataclasses
- `propstore/repo/branch.py`
  - branch-local sequencing
- `propstore/repo/ic_merge.py`
  - merge-specific IC operators already separated

### In the paper corpus

- Alchourron 1985
  - AGM postulates, partial meet contraction, Levi/Harper identities
- Gärdenfors 1988
  - epistemic entrenchment as the constructive bridge to contraction
- Dixon 1993
  - ATMS support structure to AGM-equivalent entrenchment behavior
- Darwiche 1997
  - iterated revision requires epistemic states, not just belief sets
- Spohn 1988
  - OCF/ranking representation for iterated state
- Booth 2006
  - admissible/restrained operators for iterated revision
- Bonanno 2007/2010
  - branch/history sensitivity and the merge-point boundary
- Baumann 2015 and Rotstein 2008
  - downstream argumentation-level revision
- Konieczny 2002 and Coste-Marquis 2007
  - revision/merging separation and explicit merge semantics

---

## Proposed Architecture

## Layer picture

```text
stored entities
  -> WorldModel / BoundWorld / ATMS support graph
  -> revision projection
  -> entrenchment / epistemic state
  -> revision operator
  -> revised belief state
  -> render / explanation / optional AF adapter
```

The revision layer sits **between** descriptive world construction and render-time resolution. It consumes a scoped world and produces a revised scoped world-state. It does not rewrite storage.

## Semantic Rule

Revision semantics are **operator-based, not fixed-point-defined**.

For each revision episode:

1. start from an explicit pre-revision state
2. apply a defined revision operator to that state and the new input
3. recompute induced support, acceptance, and derived consequences until the resulting post-revision world stabilizes
4. treat that stabilized result as the next epistemic state

This means:

- the operator defines the semantics
- the fixed point is the evaluation method for one revision episode
- the stabilized post-revision state becomes the input to the next revision episode

This proposal therefore rejects two bad alternatives:

- defining revision as “keep looping until nothing changes”
- returning a revised state before downstream support and derivations have stabilized

## New package: `propstore/revision/`

```text
propstore/revision/
    __init__.py
    projection.py      # BoundWorld/ATMS -> finite belief base
    entrenchment.py    # compute entrenchment ordering from support + overrides
    operators.py       # expansion, contraction, revision (V1)
    state.py           # RevisionScope, BeliefBase, RevisionResult, EpistemicState
    explain.py         # retraction and support explanations
    iterated.py        # OCF / preorder-based iterated state (Phase 3+)
    af_adapter.py      # optional AF/ASPIC+ adapter (Phase 4+)
```

### `state.py`

Core V1 dataclasses:

```python
@dataclass(frozen=True)
class RevisionScope:
    bindings: dict[str, Any]
    context_id: str | None = None
    branch: str | None = None
    commit: str | None = None

@dataclass(frozen=True)
class BeliefAtom:
    atom_id: str
    kind: str        # "claim" | "assumption" | "derived"
    payload: dict[str, Any]

@dataclass(frozen=True)
class BeliefBase:
    atoms: tuple[BeliefAtom, ...]
    supports: Mapping[str, Label]
    exact_atoms: tuple[str, ...]

@dataclass(frozen=True)
class RevisionResult:
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    explanation: Mapping[str, Any]
```

Phase 3 adds:

```python
@dataclass(frozen=True)
class EpistemicState:
    scope: RevisionScope
    accepted_atom_ids: tuple[str, ...]
    entrenchment: Mapping[str, float]
    history: tuple[str, ...]
    ranking: Mapping[str, int] | None = None
```

The V1 `RevisionResult` can exist without first-class iterated state. `EpistemicState` becomes mandatory once we claim iterated revision.

### `projection.py`

Responsibilities:

- derive a finite belief base from `BoundWorld`
- include only exact-support claims and assumptions for V1
- expose claim/assumption provenance back to the world layer
- keep the mapping stable and explainable

Non-goal:

- full deductive closure

This is an operational belief-base projection, not a theorem prover over all consequences.

### `entrenchment.py`

Responsibilities:

- compute a default entrenchment ordering from:
  - ATMS labels
  - `ATMSEngine.essential_support()`
  - support multiplicity / environment coverage
  - optional explicit policy overrides
- expose round-trippable explanation of why one atom outranks another

Hard rule:

- computed entrenchment is **derived**, not stored as an independent source of truth

What may be stored:

- explicit override categories or user preferences

What must not be stored:

- stale computed entrenchment detached from support structure

### `operators.py`

V1 operators:

- `expand(base, atom)`
- `contract(base, atom, *, policy=...)`
- `revise(base, atom, *, policy=...)`

`revise` should be defined in terms of contraction + expansion, not as a separate ad hoc shortcut.

V1 contraction should be **support-sensitive**, not a bare claim-deletion primitive:

- define an explicit V1 conflict basis over the projected exact-support belief base
- identify the support / culprit sets responsible for the target contradiction or incompatibility
- compute a minimal low-entrenchment incision set over that support structure
- let claim-level acceptance and rejection be the visible consequence of those incisions

In other words, the primitive action is not “drop whichever conflicting claim looks weakest.” The primitive action is “cut the least entrenched support necessary to contract or to admit the revising input,” then recompute the resulting belief state.

The operator API should be pluggable so later phases can choose restrained, lexicographic, or other admissible iterated operators without changing the rest of the package shape.

Each operator returns a result only after local post-revision stabilization:

- recompute acceptance/support on the projected belief base
- recompute derived consequences
- repeat until the revised scoped world reaches local fixed point

The fixed point is therefore part of operator evaluation, not a substitute for the operator.

### `explain.py`

Responsibilities:

- explain which atoms were lost during contraction
- identify the incision set and the support sets it cut
- point back to essential support, support multiplicity, and explicit override priorities
- distinguish:
  - retracted because contradicted by new input
  - retracted because less entrenched than competing support
  - retracted because their supporting assumptions were incised
  - unchanged because protected by higher entrenchment

This explanation surface is required. Without it, the revision layer will be impossible to trust.

---

## Integration Points

### `BoundWorld`

Add a delegating entry point:

```python
def revise(self, target: str, **kwargs) -> RevisionResult:
    ...
```

And similarly for:

- `expand(...)`
- `contract(...)`
- `revision_state(...)`

The `BoundWorld` remains the context-bound descriptive view. It does not own the operator logic.

### `WorldModel`

No revision logic should live here. `WorldModel` remains read-only.

At most:

- helper to construct a `BoundWorld`
- helper to persist or reload revision-state snapshots later

### `RenderPolicy`

Do **not** overload `RenderPolicy` with revision semantics in V1.

Revision is not just another resolution strategy like `RECENCY` or `IC_MERGE`. It is a different state-transform layer. If needed, add a separate `RevisionPolicy` in `propstore/revision/state.py`.

### `worldline.py`

Worldlines are the natural place to record reproducible revision traces later:

- scope
- operator
- input atom
- accepted/rejected sets
- explanation

This should be Phase 2 or 3, not Phase 1.

### CLI

Add a dedicated CLI module rather than burying this in existing command groups:

```text
propstore/cli/revision.py
```

Initial commands:

```bash
pks world revise <claim-or-concept> [bindings...]
pks world contract <claim-or-concept> [bindings...]
pks world expand <claim-or-concept> [bindings...]
pks world revision-explain <claim-or-concept> [bindings...]
```

These commands operate on derived state and print results plus explanation. They do not rewrite YAML.

---

## Interaction With `multi-source-structured-merge.md`

This proposal is compatible with the in-progress merge proposal if these rules hold:

1. The merge proposal owns source aggregation.
2. This proposal owns epistemic state change.
3. Neither reuses the other’s internal datatype as a shortcut.

### Safe sequencing

Safe now:

- V1 revision projection from `BoundWorld`
- entrenchment computation from ATMS support
- one-shot contraction/revision commands and tests

Should wait until merge object boundary is stable:

- any revision adapter that consumes merged partial frameworks directly
- any AF-level revision that depends on the new branch-local argumentation summaries

### Explicit anti-goal

Do not implement “revision” by feeding a merge profile into `ic_merge()` and calling the output the revised belief state.

---

## Phased Implementation Plan

### Phase 0: Boundary Cleanup

Goal:

- make the docs and naming line up with the intended boundary before code lands

Tasks:

- audit wording in docs that still overstates current branch operations as true revision
- cross-link this proposal with `multi-source-structured-merge.md`
- make the “not AGM revision” boundary in `docs/atms.md` remain explicit

### Phase 1: Belief-Base Projection And Entrenchment

Goal:

- derive an operational finite belief base from `BoundWorld`
- compute explainable entrenchment from ATMS support

Tasks:

1. Add `propstore/revision/projection.py`
2. Add `propstore/revision/entrenchment.py`
3. Define `RevisionScope`, `BeliefAtom`, and `BeliefBase`
4. Add toy fixtures and unit tests

Success criteria:

- a scoped `BoundWorld` can project to a stable belief base
- entrenchment ordering is deterministic and explainable
- no source data is mutated

### Phase 2: Single-Shot Contraction And Revision

Goal:

- implement true one-shot AGM-style operators over the projected belief base
- evaluate each revision episode to local fixed point before returning

Tasks:

1. Add `operators.py`
2. Add `RevisionResult`
3. Add `explain.py`
4. Add `BoundWorld` delegation methods
5. Add CLI commands
6. Add local stabilization loop for post-revision support/derivation closure

Success criteria:

- revise/contract/expand work on toy cases and real sidecar-backed scopes
- Levi and Harper identities hold at the operational level used by the package
- explanations identify what moved and why
- each revision episode returns a stabilized post-revision state rather than an intermediate one

### Phase 3: Iterated Revision State

Goal:

- add first-class epistemic state and operator families for revision sequences

Tasks:

1. Add `EpistemicState`
2. Add `iterated.py`
3. Add ranking or preorder representation
4. Add operator selection for admissible/restrained behavior
5. Add sequence tests corresponding to DP-style scenarios
6. Derive episode `n+1` entrenchment/ranking from the stabilized result of episode `n`

Success criteria:

- repeated revisions depend on history, not just current acceptance set
- the state object is explicit and serializable
- merge points are still excluded from this operator path
- fixed-point recomputation is scoped to each episode, not used as a replacement for explicit iterated-state semantics

### Phase 4: Downstream AF / Structured Revision Adapters

Goal:

- expose revision-informed updates into abstract and structured argumentation

Tasks:

1. Add `af_adapter.py`
2. Define how revised claim/context states project into AF changes
3. Optionally add warrant-style structured revision hooks

Success criteria:

- AF/ASPIC+ consumers can observe revised state without becoming the primary reviser

---

## Testing Strategy

### Phase 1 tests

- projection stability under identical `BoundWorld` inputs
- exact-support-only inclusion for V1
- entrenchment ordering explanation is stable
- stronger support outranks weaker support on toy ATMS setups

### Phase 2 tests

- revision success
- contraction removes target support appropriately
- vacuity on irrelevant input
- Levi identity holds operationally
- Harper round-trip is consistent with the package semantics
- no mutation of source YAML or repo refs
- post-revision episodes converge to a local fixed point
- rerunning stabilization on an already stabilized result is idempotent

### Phase 3 tests

- same current acceptance set but different history yields different future revision behavior
- linear within-branch sequences stay on the iterated-revision path
- merge points are refused or rerouted explicitly
- operator-specific tests for restrained vs more aggressive options
- episode `n+1` uses the stabilized state from episode `n`, not a pre-closure intermediate

### Cross-cutting tests

- revision commands do not call merge operators
- merge commands do not call revision operators
- `docs/atms.md` boundary remains true after implementation

---

## Main Risks

### Risk 1: Architectural self-deception

Mistake:

- treating ATMS labels, merge outputs, or branch history as if they already were a revision state

Mitigation:

- keep separate datatypes and packages
- explicit tests for “merge is not revision”
- explicit tests for “ATMS replay is not contraction”

### Risk 2: Overcoupling to the in-progress merge proposal

Mistake:

- waiting for full multi-source structured merge before starting any revision work

Mitigation:

- phase revision V1 over `BoundWorld` now
- defer only merge-object consumers, not the whole proposal

### Risk 3: Starting at AF-level first

Mistake:

- trying to solve abstract or structured argument revision before claim/context revision is stable

Mitigation:

- phase AF adapters after single-shot and iterated claim-level revision land

### Risk 4: Stale entrenchment

Mistake:

- persisting computed entrenchment independently of support structure

Mitigation:

- compute entrenchment from current support
- store only explicit overrides

---

## Recommendation

Proceed with this proposal.

The right implementation order is:

1. belief-base projection and entrenchment
2. one-shot revision operators
3. first-class iterated state
4. downstream argumentation adapters

And the right coexistence rule with the current merge draft is:

**finish revision as revision, finish merge as merge, and never let either pretend to be the other.**

---

## Decisions To Pin Down

This section is the active decision surface for implementation. Each item includes a recommended default so work can start without reopening the whole proposal.

### 1. What is a belief atom in V1?

Decision:

- claims only
- assumptions only
- claims plus assumptions
- claims plus assumptions plus derived propositions

Recommended default:

- **claims plus assumptions**

Why:

- assumptions are needed for support-sensitive entrenchment and contraction explanations
- claims are the user-facing objects that revision should visibly change
- derived propositions can be recomputed from the revised accepted base rather than treated as primitive V1 atoms

### 2. What semantics are we claiming in V1?

Decision:

- full AGM over deductively closed theories
- finite belief-base AGM-style operations

Recommended default:

- **finite belief-base AGM-style operations**

Why:

- propstore operates over finite compiled claim sets, not full deductive closure
- this keeps the implementation honest and testable
- it avoids pretending the sidecar already is a theorem-closed theory

### 3. How is entrenchment computed?

Decision:

- support count only
- essential-support-sensitive ordering
- fragility-derived ordering
- metadata override only
- weighted combination

Recommended default:

- **weighted combination with a fixed precedence shape**

Suggested shape:

1. explicit override categories
2. exact-support status
3. essential-support sensitivity
4. supporting-environment coverage
5. stable tiebreak by atom id

Why:

- support count alone is too coarse
- override-only throws away the ATMS bridge
- fragility-derived ordering is useful but should inform the ordering, not replace support structure

### 4. What kind of overrides are allowed?

Decision:

- none
- per-claim manual priorities
- category/source/context-based priorities
- arbitrary custom ordering hooks

Recommended default:

- **category/source/context-based priorities plus optional per-claim manual priorities**

Why:

- this matches the kind of ranking Shapiro-style systems want
- it stays understandable
- it avoids introducing arbitrary plugin hooks before the base operator is stable

### 5. What is the V1 revision input?

Decision:

- claim id only
- synthetic claim only
- assumption only
- all of the above

Recommended default:

- **claim id, synthetic claim, or assumption**

Why:

- claim id supports repo-native usage
- synthetic claim supports exploratory revision without mutating storage
- assumption revision is needed for context-sensitive workflows

### 6. Is iterated revision in scope for V1?

Decision:

- yes
- no

Recommended default:

- **no**

Why:

- the proposal is cleaner if V1 lands one-shot contraction/revision first
- iterated revision requires first-class epistemic state, ranking/preorder machinery, and extra tests
- deferring it avoids false claims about having DP-compliant behavior too early
- V1 can still and should compute each single revision episode to local fixed point before returning

### 7. Which iterated operator should be the default when Phase 3 lands?

Decision:

- restrained revision
- lexicographic revision
- expose several with no default

Recommended default:

- **restrained revision as default, lexicographic as opt-in**

Why:

- it is the safer, more conservative choice
- it avoids the most aggressive “latest input dominates” behavior by default
- it gives a principled baseline without overcommitting the whole architecture

### 8. Do we persist revision state?

Decision:

- ephemeral only
- persisted snapshots
- both

Recommended default:

- **ephemeral in V1, persisted snapshots in Phase 2 or 3**

Why:

- ephemeral state is enough to validate the operator surface
- persistence can piggyback on worldline infrastructure once the shape is stable

### 9. How do worldlines integrate?

Decision:

- worldlines only record revision results after the fact
- worldlines can declare revision operations as part of the question

Recommended default:

- **record revision results first; let worldlines declare revision inputs in the next slice**

Why:

- this keeps Phase 1 and 2 smaller
- it gives immediate provenance capture without redesigning `WorldlineDefinition` too early

### 10. What happens at merge points?

Decision:

- silently reuse revision operators
- route through merge machinery
- refuse and require explicit merge path

Recommended default:

- **refuse and require explicit merge path**

Why:

- this is the safest guard against architectural category error
- it forces the caller to distinguish revision from merging

### 11. What explanation is mandatory?

Decision:

- minimal accepted/rejected list only
- accepted/rejected plus ranking rationale
- full support trace

Recommended default:

- **accepted/rejected plus ranking rationale, with support trace on demand**

Why:

- a revision result without rationale is not trustworthy
- a full support trace on every call is too noisy for the default path

### 12. What guard prevents revision/merge conflation?

Decision:

- convention only
- doc warning only
- hard code-path refusal

Recommended default:

- **hard code-path refusal**

Concrete rule:

- revision modules must not call `propstore/repo/ic_merge.py`
- merge modules must not instantiate revision-state operators
- tests must assert both boundaries
