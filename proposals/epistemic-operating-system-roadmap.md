# Proposal: Epistemic Operating System Roadmap

**Date:** 2026-03-29
**Status:** Draft
**Depends on:** `proposals/true-agm-revision-proposal.md`, `proposals/multi-source-structured-merge.md`, `proposals/first-class-justifications.md`, `proposals/fragility-plan.md`

---

## Problem

Propstore now has a serious epistemic core:

- immutable source storage with provenance
- typed compilation and sidecar materialization
- multiple argumentation backends
- ATMS-style exact support and bounded future analysis
- one-shot and iterated AGM-style revision over derived belief state
- revision-aware worldlines and replay

That is not yet an epistemic operating system.

An operating system needs more than a reviser and a few CLI commands. It needs a coherent stack for:

- representing competing epistemic states
- merging multi-source states without semantic cheating
- projecting those states into argumentation, decision, and intervention services
- governing how policies, preferences, and provenance affect belief change
- recording, replaying, comparing, and auditing state transitions
- orchestrating long-running investigative workflows rather than only answering isolated queries

The current repo is close enough that the next work should be planned as one integrated program, not as scattered future-work bullets.

---

## Scope

This roadmap covers the post-Phase-5 horizon:

- completion of the formal merge layer
- structured and warrant-level revision consumers
- policy and governance over epistemic state change
- durable snapshots, journals, and diffs
- investigation and intervention orchestration
- observability, evaluation, and operator audits
- public surfaces that make these capabilities usable

This roadmap does **not** reopen the already-implemented core revision phases unless a later phase proves they need revision.

---

## Vision

The target system should let a user or agent do all of the following without crossing semantic wires:

- ingest new evidence without mutating source truth
- revise one epistemic state rationally
- merge multiple epistemic states formally
- inspect why a belief is in, out, fragile, or blocked
- ask what to observe next
- record the exact transition that changed the answer
- compare alternative policies and operator families
- replay old decisions under new evidence or new merge policies
- expose all of that through durable programmatic and CLI surfaces

That is the minimum bar for calling this an epistemic operating system rather than a claim compiler with reasoning plugins.

---

## Architectural Thesis

The system should converge on seven layers:

1. **Source storage**
   - claims, concepts, contexts, justifications, stances, provenance
   - immutable except by explicit migration or source edits

2. **Compiled substrate**
   - sidecar indexes
   - typed conditions
   - parameterization graph
   - conflict records
   - branch-local materialization helpers

3. **Epistemic kernel**
   - `BoundWorld`
   - ATMS support substrate
   - one-shot revision
   - iterated `EpistemicState`
   - formal merge objects

4. **Argumentation and semantic services**
   - Dung / ASPIC+ / PrAF / bipolar consumers
   - structured projection from revised and merged state
   - warrant and defeat explanations

5. **Policy and governance**
   - entrenchment overrides
   - source preferences
   - merge policies
   - admissibility profiles
   - audit and approval hooks

6. **Epistemic process manager**
   - worldlines
   - investigation plans
   - intervention plans
   - queued revision/merge jobs
   - state diffs and journaled episodes

7. **Public surfaces**
   - CLI
   - Python API
   - agent-facing workflows
   - export and observability endpoints

The thesis is simple:

**propstore becomes an operating system when the epistemic kernel, policy layer, and process manager are first-class and connected by explicit state objects rather than ad hoc command flows.**

---

## Non-Negotiable Invariants

1. **Revision is not merge.**
   - Within-branch change uses revision operators over explicit epistemic state.
   - Multi-parent aggregation uses formal merge objects and merge operators.

2. **Storage is not state.**
   - Source rows remain provenance-bearing artifacts.
   - Belief state, merge state, and worldline replay state are derived objects.

3. **ATMS is not the reviser.**
   - ATMS remains support machinery and future-analysis substrate.
   - It may inform entrenchment, fragility, and intervention planning.

4. **Argumentation consumers do not own belief change.**
   - AF / ASPIC+ / PrAF observe or project revised and merged state.
   - They do not silently implement replacement revision semantics.

5. **Policy is explicit.**
   - Operator family, preference profile, merge policy, and override sources must be inspectable and replayable.

6. **Every state transition is auditable.**
   - State-in, policy, operator, incision/merge outcome, state-out, and explanation must all be reconstructable.

7. **The stack must prefer principled direct replacement over dual legacy semantics.**
   - When a formal layer supersedes an ad hoc one, the plan should migrate consumers rather than carry both indefinitely.

---

## Current Baseline

Already implemented:

- true AGM-style one-shot revision over derived belief bases
- iterated epistemic state with restrained and lexicographic operator families
- revision explanations and local stabilization
- `BoundWorld` and CLI revision surfaces
- revision-aware worldlines and replay
- revision-to-argumentation adapter surface

Not yet implemented as first-class, system-level capabilities:

- structured/warrant-level revision beyond the current adapter projection
- a first-class policy/governance subsystem
- durable state snapshots and journal/diff APIs beyond worldline payload capture
- orchestration of investigations, interventions, and queued epistemic work
- benchmark and audit infrastructure that compares operator families and policies on the same corpus

Partially implemented and needing consolidation rather than invention:

- fragility ranking and bounded ATMS intervention planning
- worldlines as the seed of a later process manager

Implemented through Phase 6:

- the formal merge-object stack from `proposals/multi-source-structured-merge.md` as the single authoritative merge path for the current architecture
- repo-level partial merge framework objects
- exact AF merge operators over tiny profiles
- completion-query/report and storage-merge surfaces over the canonical merge object
- first-slice branch-local structured merge summaries with explicit lossiness boundary

---

## Missing Capability Clusters

### A. Multi-source epistemic merge

The Phase 6 merge kernel is now landed. The remaining work is no longer basic multi-source merge existence, but richer structured-state, policy, and governance layers on top of it.

### B. Structured epistemic consumers

The current adapter lets argumentation consumers observe revised state, but it does not yet give a full warrant-level account of how structured arguments evolve under revision and merge.

### C. Policy/governance

The repo has local policy knobs, but not a coherent policy object model for:

- source trust profiles
- domain-specific admissibility
- review gates
- operator-family selection
- escalation rules for conflicts, fragility, and merge ambiguity

### D. State durability and observability

Worldlines record replayable episodes, but the system still lacks:

- explicit snapshot objects
- transition journals
- semantic diffs between epistemic states
- audit queries over historical policy/operator choices

### E. Epistemic process orchestration

The ATMS and fragility work can already suggest interventions, but the repo does not yet expose a process layer for:

- investigation plans
- queued revision/merge runs
- compare-and-select workflows over alternative policies
- automated “what should I learn next?” workflows that end in durable state transitions

---

## Program Roadmap

### Phase 6: Formal Merge Kernel Completion

Goal:

- complete and consolidate the formal merge-object architecture as a first-class peer to revision

Primary proposal:

- `proposals/multi-source-structured-merge.md`

Deliverables:

- direct replacement of remaining legacy merge-bucket production paths with the explicit merge object
- branch-local argumentation summaries
- merged partial framework with `attack / non-attack / ignorance`
- exact merge operators and query surfaces
- explicit boundary tests proving merge does not route through revision

Success criteria:

- merged states are queryable and explainable without semantic collapse into branch buckets
- merge products are durable typed objects
- branch-local summaries can be consumed by later policy and audit layers

### Phase 7: Structured State Semantics

Goal:

- lift revision and merge results into full structured argumentation consumers

Deliverables:

- AF-level and warrant-level projection from revised and merged state
- structured defeat explanations that preserve provenance and policy choices
- explicit tests for when revised claim acceptance changes warrant status
- optional warrant-level revision hooks only if they preserve the revision/consumer boundary

Success criteria:

- ASPIC+ and related consumers can explain changes in warrant under revision and merge
- structured consumers remain projections, not shadow revisers

### Phase 8: Policy and Governance Layer

Goal:

- make epistemic policy a first-class, replayable object instead of scattered flags

Deliverables:

- `PolicyProfile` / `RevisionPolicy` / `MergePolicy` objects with stable serialization
- source-trust and domain-preference models
- admissibility and escalation profiles
- policy-aware worldlines and state transitions
- explicit default-policy resolution rules for CLI and API entry points
- audit surfaces for “why this operator/policy was used”

Success criteria:

- every state transition names a concrete policy profile
- changing policy predictably changes output and replay hashes
- no hidden defaults remain in critical revision/merge paths

### Phase 9: Snapshot, Journal, and Diff Layer

Goal:

- make epistemic state history queryable as history, not just replayable side effects

Deliverables:

- durable `EpistemicSnapshot` object
- transition journal over revision, merge, intervention, and policy-change episodes
- semantic diff engine:
  - accepted/rejected deltas
  - ranking deltas
  - warrant-status deltas
  - dependency/provenance deltas
- CLI and Python APIs for snapshot/diff inspection

Success criteria:

- users can inspect how and why a state changed without replaying everything manually
- snapshots and journals compose cleanly with worldlines
- worldlines remain the query/replay artifact, while snapshots and journals become the authoritative state-history layer

### Phase 10: Investigation and Intervention Manager

Goal:

- turn existing fragility/relevance/intervention analysis into executable epistemic workflows

Deliverables:

- investigation-plan object model
- durable queued jobs for:
  - gather evidence
  - test hypothetical additions/removals
  - compare revision operators
  - compare merge outcomes
- “next best query” and ROI planning that can emit worldlines, not just rankings
- explicit completion records tying investigations back to resulting state transitions
- direct reuse of the existing fragility, next-query, and bounded intervention machinery as planning primitives

Success criteria:

- the system can recommend, stage, execute, and audit multi-step epistemic work
- intervention planning is no longer an isolated query feature

### Phase 11: Evaluation and Observatory

Goal:

- measure whether the operating system is coherent, stable, and worth trusting

Deliverables:

- benchmark corpora and scenario suites for revision, merge, and argumentation
- operator-comparison harnesses
- replay determinism checks
- policy regression dashboards
- falsification cases where different operators should diverge

Success criteria:

- major semantic choices are backed by repeatable evaluation, not taste
- regressions in epistemic behavior are test failures, not surprises

### Phase 12: Product Surface Unification

Goal:

- expose the whole stack through coherent user and agent interfaces

Deliverables:

- unified CLI verbs for state, policy, snapshot, diff, and investigation operations
- Python API surfaces that mirror the same object model
- export contracts for external agents and UI layers
- documentation that explains the end-to-end state machine honestly

Success criteria:

- users can traverse from source artifact to epistemic decision and back
- the surface matches the architecture instead of hiding it behind ad hoc commands

---

## Sequencing Rules

1. **Do Phase 6 before pretending the OS has multi-source state.**
   - Without a completed merge kernel, the system is still largely single-lineage plus worldline replay.

2. **Do Phase 8 before over-expanding public surface area.**
   - A bigger CLI without a policy object model just hard-codes hidden semantics.

3. **Do Phase 9 before any serious automation.**
   - Long-running investigations without snapshots and journals are operationally sloppy.

4. **Do Phase 11 continuously, not only at the end.**
   - Every major phase should land with explicit scenario tests and operator comparisons.

5. **Do not let Phase 7 invent alternative belief-change semantics.**
   - Structured consumers project from kernel state; they do not fork the kernel.

---

## Immediate Next Execution Slice

The next precise execution target should be **Phase 6: Formal Merge Kernel Completion**.

Why this is first:

- it is the largest remaining semantic hole
- it is already separately proposed and partly implemented
- it is the missing peer to the revision kernel
- later policy, diff, and orchestration layers need first-class merge objects to be worth building

Concrete next actions:

1. tighten `proposals/multi-source-structured-merge.md` into an execution-grade control surface
2. write a checklist equivalent in precision to the revision Phase 1-5 checklists
3. identify and replace the remaining legacy merge-bucket production paths
4. audit the current merge implementation against the draft to separate already-landed pieces from missing ones
5. start TDD on the remaining branch-local summary and merged partial framework gaps rather than rewriting implemented pieces blindly

---

## Testing Program

Every phase after this roadmap should ship with:

- typed object tests
- boundary tests proving semantic separation
- replay and serialization tests
- CLI/API round-trip tests where public surfaces exist
- scenario suites grounded in local paper or toy corpora

Additional system-level requirements:

- revision and merge must remain mutually non-substitutable in tests
- snapshot/journal diffs must be deterministic
- policy changes must show up in hashes, journals, or explicit transition metadata
- worldline and future process-manager replays must stay stable under unchanged inputs

---

## Decision Surface Still To Pin Down

These questions should be answered before or during Phase 6 and Phase 8:

1. What is the canonical identity of a branch-local argumentation summary element?
2. Which merge operators are mandatory in v1 of the merge kernel, and which stay deferred?
3. What policy objects are globally scoped versus worldline- or episode-scoped?
4. Do snapshots store full ranked state, reconstruction inputs, or both?
5. Which orchestration jobs are first-class objects versus mere CLI commands?
6. What counts as a stable external API before any UI layer is built?
7. Which current worldline, fragility, and intervention outputs should be promoted directly into the process-manager object model versus retired?

---

## Recommendation

Proceed as if the revision proposal was the kernel bring-up, not the end of the system.

The immediate program should be:

1. finish the merge kernel
2. formalize policy/governance
3. add snapshots, journals, and diffs
4. promote investigation/intervention flows into a process manager
5. keep evaluation running the whole time

If propstore does that, it stops being “a compiler plus several reasoning backends” and starts becoming a real epistemic operating system.
