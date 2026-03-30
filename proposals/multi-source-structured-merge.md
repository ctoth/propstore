# Proposal: Explicit Multi-Source Merge Semantics for Structured Argumentation

**Date:** 2026-03-29
**Status:** Draft for Phase 6 completion and consolidation
**Grounded in:** local codebase, `proposals/semantic-merge-spec.md`, `reviews/03-29-2026.md`, and the local paper corpus including Coste-Marquis 2007, Konieczny 2002, Modgil 2018, Odekerken 2023/2025, Dung 1995, Hunter 2017, Li 2011

---

## Problem

Propstore already has strong pieces:

- git-backed provenance and branch-aware storage
- ASPIC+-style structured argumentation
- Dung and probabilistic AF reasoning
- ATMS-style exact-support and bounded future-query analysis

What it does **not** yet have is a fully consolidated, system-level multi-source merge layer for argumentation.

Today, the repo has a split state:

- `merge_framework.py` defines a formal partial framework kernel
- `paf_merge.py` implements exact Sum / Max / Leximax operators over tiny profiles
- `paf_queries.py` exposes skeptical and credulous completion queries
- `merge_classifier.py` emits a repo-facing merge object over claim alternatives
- `structured_merge.py` provides a first branch-local structured-summary slice
- `branch_reasoning.py` still contains bridge code that exports merge attacks as synthetic contradiction stances for older consumers

This is a strong start, but it is not yet a clean, consolidated account of multi-source structured merge. In particular:

1. **The formal path is not yet the only path.** Some consumers still depend on bridge behavior such as synthetic contradiction stances rather than consuming merge objects directly.
2. **The structured/abstract boundary is only partially landed.** The repo has a first branch-local structured-summary slice, but not yet the full execution-grade structured merge path the architecture calls for.
3. **The draft proposal understates what is already implemented and overstates what remains greenfield.** The control surface needs to distinguish completion work from invention work.
4. **Source-aware preference aggregation is still ad hoc.** The repo can apply preferences inside ASPIC+, but it does not yet define a principled path from branch/source metadata to post-merge defeat behavior.

The missing work is not "generic incompleteness" in argumentation. The local literature already covers that fairly well. The missing work is **multi-source structured merge semantics**.

---

## Why This Is A Coherent Chunk Of Work

This proposal is a coherent package because it has:

- a clear formal gap
- a natural insertion point in the current architecture
- local papers covering most prerequisites
- an incremental implementation path

It does **not** require settling every open theoretical question up front. The proposal can deliver a principled merge object, explicit invariants, and honest documentation before solving every structured commutativity theorem.

---

## Existing Ground We Can Reuse

### Abstract merge and incompleteness

- **Coste-Marquis et al. 2007** gives the core merge formalism for Dung AFs via partial argumentation frameworks (PAFs), consensual expansion, completions, and distance-based merge operators.
- **Konieczny & Pino Perez 2002** gives the upstream IC-merge operator family and postulate vocabulary.
- **Dung 1995** gives the abstract semantics target.

### Structured argumentation

- **Prakken 2010** and **Modgil 2018** give the structured argumentation substrate already reflected in propstore's ASPIC+ implementation.
- **Odekerken 2023/2025** gives incomplete-information reasoning over ASPIC+-style theories with defended/out/blocked-style status, stability, and relevance.

### Uncertainty and source weighting

- **Li 2011**, **Hunter 2017/2021**, and **Popescu 2024** already cover probabilistic AF reasoning.
- The local subjective-logic cluster provides an optional source-fusion layer if premise-level uncertainty fusion becomes necessary.

The key point: we do **not** need more literature before we can define the architecture and first formal object boundary.

### Literature refresh verdict

The 2026-03-29 re-check against the local notes sharpens the boundary instead of changing the architecture:

- **Konieczny 2002** and **Coste-Marquis 2007** still justify a structural merge kernel over `attack / non-attack / ignorance`.
- **Prakken 2010** and **Modgil 2018** still place defeat and preference downstream of attack.
- **Odekerken 2023/2025** is relevant to later structured inquiry under incomplete information, but it is **not** a reason to widen Phase 6 merge completion.

So the merge roadmap should stay narrow:

1. consolidate the structural merge kernel
2. keep source preference out of the kernel by default
3. leave `j`-stability / `j`-relevance to later world/query and investigation work

---

## Current Repo Baseline

Already implemented in the repo:

- `propstore/repo/merge_framework.py`
  - `PartialArgumentationFramework`
  - exact completion enumeration
  - exact per-pair edit distance
- `propstore/repo/paf_merge.py`
  - exact `consensual_expand()`
  - exact `sum`, `max`, and `leximax` merge over tiny AF profiles
- `propstore/repo/paf_queries.py`
  - skeptical and credulous completion queries
- `propstore/repo/merge_classifier.py`
  - `RepoMergeFramework` direct emission from repo snapshots
- `propstore/repo/merge_report.py`
  - repo-facing inspection summaries
- `propstore/cli/merge_cmds.py`
  - `pks merge inspect`
  - `pks merge commit`
- `propstore/repo/structured_merge.py`
  - first branch-local structured summary pipeline via ASPIC projection

Still acting as bridge or incomplete surface:

- `propstore/repo/branch_reasoning.py`
  - still exports synthetic `contradicts` stances for older consumers
- `propstore/repo/structured_merge.py`
  - still works at a first-slice summary level rather than a fully specified structured merge contract
- source-preference handling
  - still not formalized as part of merge semantics

Therefore the next work is **not** “invent the merge kernel.” It is:

1. finish the remaining formal boundary work
2. remove semantic bridges where the formal path should now be authoritative
3. tighten the structured boundary and policy story

---

## Proposal

Introduce a first-class **multi-source merge layer** between branch-local structured theories and existing render/query backends.

The core idea is:

1. Each branch/source induces a local structured theory.
2. Each local structured theory projects to a shared abstract merge object.
3. The merge object preserves `attack / non-attack / ignorance` explicitly rather than collapsing them into claim buckets.
4. Existing reasoning backends query merged completions or merged summaries rather than raw branch conflicts.

This proposal does **not** claim that abstract merge and structured instantiation commute. It makes that boundary explicit and testable.

Because propstore controls the whole application stack, this proposal assumes a **direct replacement strategy**:

- no long-lived migration path
- no fallback merge-bucket semantics
- no adapter layer preserved for compatibility

The repo-layer merge object should be upgraded directly to the new formal object, and all consumers should be updated in lockstep.

---

## Target Architecture

The stack should be read as four distinct levels:

### 1. Stored knowledge entities

These remain the source of truth:

- concepts
- claims
- justifications
- stances
- provenance and source metadata

This proposal does **not** replace these objects.

### 2. Branch-local structured theory

Each branch/source induces a structured theory from the stored entities:

- claims become premise/conclusion-bearing statements
- justifications become inference rules
- stances contribute contrariness / attack-support structure
- source metadata may induce preferences

This is the level where ASPIC+-style reasoning lives.

### 3. Branch-local argumentation summary

Each structured theory induces a branch-local argumentation summary suitable for merge:

- arguments
- attacks
- known non-attacks where determinable
- ignorance where the branch/source does not determine a relation

This is the smallest principled merge input for v1.

### 4. Merged partial framework

The branch-local summaries are merged into a shared partial framework:

- explicit attack
- explicit non-attack
- explicit ignorance
- provenance of which source supported which structure

Queries and render-time reasoning operate over this merged object and explain results back in terms of claims, justifications, and sources.

This merged object remains structural. It is not the place to encode source-trust defeat policy, and it is not the place to import structured future-information machinery from the incomplete-information literature.

The final target architecture is therefore:

1. stored entities
2. branch-local structured theories
3. branch-local argumentation summaries
4. merged partial framework
5. query/render/explanation back to stored entities

## Working Decisions For V1

The following design choices are settled for the first implementation:

1. **Merge over attacks, not defeats.**
   - Attack is the source-facing structural relation.
   - Defeat remains downstream and may still depend on preference policy.
   - The literature refresh keeps this as a hard boundary for Phase 6.

2. **Keep the existing semantic identity layer for v1.**
   - This proposal does not fold content-addressed identity redesign into merge semantics work.
   - A future dual `artifact_id` / `logical_id` design can be proposed separately if needed.

3. **Use branch-local argumentation-summary IDs as the shared merge universe.**
   - V1 does not merge raw claim IDs directly.
   - V1 also does not require full structured derivation-tree identity to be the shared merge key.

4. **Upgrade the repo merge object directly.**
   - No migration path.
   - No compatibility adapter.
   - No long-lived fallback bucket semantics.

5. **Treat full structured merge as the target architecture, but not the first code chunk.**
   - The first implementation lands the abstract merge backbone that branch-local structured theories compile into.
   - Structured projection is still part of this proposal and remains on the milestone path.

6. **Do not widen Phase 6 into structured incomplete-information inquiry.**
   - `j`-stability, `j`-relevance, and future-theory search belong to later inquiry layers.
   - They are not prerequisites for completing the merge kernel or its public surfaces.

---

## Formal Objects

### 1. Branch-Local Structured Theory

For each branch/source, define a local structured theory consisting of:

- claims
- justifications / inference rules
- stances / contrariness data
- source-local preferences or metadata-derived orderings

This is the branch-local object from which arguments, attacks, and defeats are derived.

### 2. Source-Projected Merge Graph

Define a shared abstract merge object over a common argument universe:

- `A`: the shared argument set
- `R_s`: attacks explicitly present according to source `s`
- `N_s`: non-attacks explicitly determined by source `s`
- `I_s`: ignorance according to source `s`

This is the branch/source-indexed analogue of a PAF expansion.

### 3. Merged Partial Framework

Aggregate the source-projected views into a merged partial framework:

- preserve attack, non-attack, and ignorance as first-class states
- support Sum / Max / Leximax-style merge policies over disagreement
- optionally support source weights later

This object is the first point where "merge semantics" properly begins.

### 4. Completion / Query Layer

Define queries over:

- completions of the merged partial framework
- skeptical / credulous acceptance
- merged-status explanations
- future-query / relevance / stability style questions

This is where existing Dung, PrAF, and ATMS-style query machinery can be reused.

## Concrete Forked-Repo Example

Consider a forked knowledge repository where two agents add different papers and then attempt a merge.

- `agent/a` adds Paper A
- `agent/b` adds Paper B

Each branch may add:

- concepts, if needed
- claims extracted from the paper
- justifications encoding why those claims should hold
- stances toward existing claims or within-paper claims
- provenance tying those objects back to the paper

The merge should **not** ask "which YAML row wins?" Instead it should do this:

1. **Read the branch-local additions.**
   - Gather the concepts, claims, justifications, stances, and provenance added on each branch.

2. **Build branch-local structured theories.**
   - Claims become premise/conclusion-bearing statements.
   - Justifications become inference rules.
   - Stances contribute attack, contrariness, or support structure.
   - Source metadata may contribute preferences later.

3. **Project each branch-local theory to an argumentation summary.**
   - This yields arguments, attacks, known non-attacks, and ignorance where the branch does not determine a relation.

4. **Merge those summaries into a partial framework.**
   - If both branches induce the same attack, keep it as attack.
   - If one branch induces an attack and the other is silent, preserve ignorance rather than collapsing it.
   - If the branches induce incompatible structures, preserve that disagreement explicitly with provenance.
   - If the branches add disjoint but compatible new material, the merged framework simply grows.

5. **Query the merged result.**
   - Skeptical queries ask what is accepted across all completions.
   - Credulous queries ask what is accepted in some completion.
   - Explanatory queries trace outcomes back to the claims, justifications, and papers that induced them.

A simple example:

- Branch A adds a claim that drug `X` reduces symptom `Y`, justified by a trial.
- Branch B adds a claim that drug `X` does not reduce symptom `Y`, justified by a replication study.

After structured construction:

- Branch A contains an argument for the positive effect claim.
- Branch B contains an argument for the negative effect claim.
- The merge preserves both source contributions and the induced conflict between them.
- Query-time reasoning can then say whether the result is unresolved, skeptically rejected, credulously supported on one side, or preference-sensitive.

This is the motivating application shape for the proposal: merging knowledge contributions as structured theories, not picking winners among rows.

---

## Minimal Pipeline

### Phase A: Make The Boundary Honest

- Stop describing merge commits themselves as IC merge.
- Document merge commits as provenance-preserving storage objects.
- Reserve "merge operator" for the formal render/query layer.

### Phase B: Consolidate The Real Merge Object

- Keep `PartialArgumentationFramework` as the canonical merge kernel.
- Eliminate remaining production paths that bypass or reinterpret it.
- Tighten branch-local projection into that datatype.
- Define invariants and tests for expansion, completion, and profile aggregation.

### Phase C: Query The Merge Object Directly

- Add completion-based acceptance queries.
- Add skeptical / credulous / majority-style status reporting.
- Integrate with worldline / render outputs without routing through stance-bridge code.

### Phase D: Reconnect Structured Reasoning

- Feed merged abstract results back into the structured stack carefully.
- Make any approximation explicit if the structured and abstract paths do not align perfectly.

---

## What This Proposal Solves Immediately

Without further literature work, this proposal can solve:

1. **Architecture.** Where multi-source merge belongs in the stack.
2. **Terminology.** What is storage merge, what is formal merge, and what is still only an analogy.
3. **Interfaces.** The boundary between branch-local structured theories and merged abstract objects.
4. **A minimal formal object.** Explicit partial merge semantics instead of claim-level conflict buckets.
5. **A testable roadmap.** Invariants for expansion, completion, merge-policy behavior, and query semantics.

This is enough for a serious design and implementation phase.

---

## What This Proposal Does Not Yet Solve

This proposal intentionally leaves the following as explicit open questions:

1. **Commutativity.** Does instantiate-then-merge equal merge-then-instantiate for the structured layer? Probably not in full generality.
2. **Best merge substrate.** PAFs are the default target because they align best with the current stack, but ADFs and subjective-logic-first fusion remain alternatives.
3. **Full source-preference theory.** We can derive preferences from source metadata, but the exact aggregation theory still needs careful design.
4. **Structured completeness theorems.** The proposal does not pretend we already have proofs connecting every structured construction to the abstract merge layer.

---

## Out Of Scope For This Proposal

To keep the work coherent, the following are explicitly out of scope for this proposal:

- content-addressed identity redesign for claims/arguments
- replacing semantic IDs with git/blob/tree hashes
- a full dual `artifact_id` / `logical_id` identity system
- a proof that abstract merge and structured instantiation commute
- a final source-trust or preference aggregation theory
- an ADF-based rewrite of the argumentation layer
- a subjective-logic-first replacement for completion semantics

These may become separate proposals later, but they are not prerequisites for this work.

---

## Why PAF-Style Merge Is The Default Path

Among the available options, PAF-style merge is the smallest principled step from the current codebase because:

- the repo already uses Dung/ASPIC abstractions
- the local literature already contains the exact AF-merging formalism
- the current `CONFLICT` / `PHI_NODE` behavior is already gesturing toward `attack` vs `ignorance`
- it preserves non-commitment cleanly

By contrast:

- **ADFs** are expressive but would be a larger conceptual and implementation pivot
- **subjective logic** is attractive for source fusion but does not by itself replace completion-based attack uncertainty
- **KB-constrained AF variants** are better viewed as later refinements on candidate merged frameworks

---

## Integration Points In The Current Repo

This proposal fits naturally with existing components:

- `propstore/repo/merge_classifier.py`
  - should be rewritten to emit the new formal merge object directly
- `propstore/repo/branch_reasoning.py`
  - should consume the new merge object directly instead of synthetic conflict buckets
- `propstore/aspic.py` and `propstore/aspic_bridge.py`
  - remain the structured reasoning substrate for branch-local theories
- `propstore/world/*`
  - host the query/render semantics over merged uncertainty
- `RenderPolicy`
  - can expose merge policy choices explicitly

The implementation target is a **stack-wide direct upgrade**, not a migration architecture.

---

## Success Criteria

This proposal should be considered successful if it delivers:

1. a first-class partial merge datatype with clear semantics
2. branch-local projection rules into that datatype
3. tests for expansion, completions, and merge-policy invariants
4. honest docs distinguishing storage merge from formal merge
5. at least one user-visible query path over merged partial frameworks

Stretch goals:

- source-weighted merge policies
- preference-aware post-merge defeat
- explanation graphs over merged results

---

## TDD Strategy

This work should be implemented test-first. The merge kernel is small enough that we can define exact semantics on tiny objects and use those semantics as a brute-force oracle in property tests.

The testing pattern should match the rest of the repo:

- algebraic kernel properties as in `tests/test_labels_properties.py`
- operator invariants as in `tests/test_ic_merge.py`
- translation invariants as in `tests/test_aspic_bridge.py`
- concrete regression fixtures alongside Hypothesis generators

### New test files

- `tests/test_paf_core.py`
  - datatype invariants for partial frameworks
- `tests/test_paf_merge.py`
  - expansion, distance, and merge-operator properties
- `tests/test_paf_queries.py`
  - skeptical / credulous / completion-based query semantics
- `tests/test_repo_merge_object.py`
  - repo-layer direct production of the new merge object
- `tests/test_structured_merge_projection.py`
  - later phase: structured-theory projection invariants

### RED -> GREEN discipline

For each implementation chunk:

1. write failing tests first
2. make the smallest kernel implementation pass
3. run the relevant targeted suite with `uv run pytest -vv`, teeing to `logs/test-runs/`
4. reread the plan before choosing the next chunk
5. commit only after the chunk is green

This proposal assumes atomic chunks, each with its own RED and GREEN cycle.

---

## Property Tests We Can Write Immediately

### 1. Partial framework kernel

For a `PartialArgumentationFramework(A, R, I, N)`:

- **Partition**: `R`, `I`, and `N` are pairwise disjoint and their union is `A x A`
- **Completion soundness**: every completion `AF = (A, R')` satisfies `R subseteq R' subseteq (R union I)`
- **Completion exactness**: every completion corresponds to choosing a subset of `I`
- **Completion count**: number of completions is exactly `2^|I|`

These are direct small-object kernel properties and are ideal for Hypothesis.

### 2. Edit distance

For a PAF edit distance:

- **Identity**: `d(x, x) == 0`
- **Symmetry**: `d(x, y) == d(y, x)`
- **Triangle inequality**: `d(x, z) <= d(x, y) + d(y, z)`

Because the objects are tiny, these can be checked exactly.

### 3. Consensual expansion

For expansion of a source AF into a shared universe:

- **Source preservation**: known attacks remain attacks
- **Known non-attack preservation**: known non-attacks remain non-attacks
- **Unknown becomes ignorance**: pairs involving out-of-scope source arguments become ignorance
- **Same-argument-set stability**: when all sources share the same argument set, expansion introduces no spurious ignorance on in-scope pairs

### 4. Merge operators

For Sum / Max / Leximax-style merge over tiny profiles:

- **Profile-order invariance**: permuting source order does not change the merge result set
- **Unanimity**: identical source frameworks merge back to that framework
- **Majority-PAF correspondence for Sum**: on same-argument-set profiles, Sum minimizers are completions of the majority PAF
- **Concordance collapse**: concordant profiles yield a unique merge result
- **Max / Leximax refinement checks**: Leximax should respect the usual worst-case-vs-lexicographic ordering distinction on tiny exact profiles

### 5. Query semantics over completions

For skeptical and credulous acceptance:

- **Skeptical acceptance**: true iff accepted in every completion
- **Credulous acceptance**: true iff accepted in some completion
- **Ignorance monotonicity under fixation**: replacing ignorance by fixed attack/non-attack can only shrink the completion set, and query results must match brute-force recomputation

### 6. Repo-layer direct emission properties

For the upgraded repo merge object:

- the repo layer emits explicit `attack / ignorance / non-attack` structure rather than claim buckets
- former `CONFLICT` cases become explicit attack disagreement, not silent collapse
- former `PHI_NODE` cases become ignorance / non-defeat semantics, not synthetic contradiction
- provenance-preserving merge output does not lose branch identity in the emitted merge object

---

## Hypothesis Strategy Shape

The repo already uses tiny exact generators to make property tests meaningful and shrinkable. This work should do the same.

Recommended generators:

- argument universe `A`: size 1 to 4
- source profiles: 1 to 4 sources
- AFs: arbitrary tiny attack relations over `A`
- PAFs: arbitrary partitions of `A x A` into `R / I / N`

This keeps completion enumeration and exact merge oracles tractable.

The key design rule is:

- use Hypothesis to generate tiny objects
- use brute-force exact semantics as the oracle
- test algebraic and semantic properties, not just examples

---

## Risks

1. **Projection mismatch.** Branch-local structured theories may not project cleanly to a shared abstract universe without losing important distinctions.
2. **Semantic drift.** If the merged abstract object is too coarse, the structured layer may no longer explain outcomes faithfully.
3. **Complexity.** Completion-based reasoning can blow up quickly.
4. **Overclaiming.** The docs must not outrun the implementation again.

These are manageable if treated as design constraints rather than after-the-fact surprises.

---

## Implementation Sequence

This sequence is for the **remaining** work, starting from the current repo baseline rather than from zero.

1. Audit the current merge implementation against this proposal and mark what is already landed.
2. Tighten docs so current behavior is described honestly and the remaining gap is explicit.
3. Identify and remove remaining legacy/bridge production paths that still bypass the formal merge object.
4. Tighten user-visible query/report surfaces around the canonical merge object.
5. Strengthen branch-local structured projection and its invariants.
6. Revisit source weighting and explanation overlays.

---

## Milestones

### V1 Design Decisions

These choices are fixed for the first implementation and should be treated as plan constraints:

1. **Merge over attacks.**
   - Defeats stay downstream and remain preference-sensitive.

2. **Use branch-local argumentation-summary IDs as the shared merge universe.**
   - This keeps the first implementation above claim buckets without forcing full structured identity design into the same series.

3. **Make the repo layer emit the formal partial merge object directly, with provenance.**
   - No migration path, no fallback path, no duplicate semantics.

4. **Land the abstract merge backbone first, then structured projection.**
   - Full structured merge remains the target architecture.
   - The first code chunks establish the merge backbone that structured theories compile into.

Given those choices, the work is implementable now.

---

### Milestone 1: Consolidation audit and boundary cleanup

Deliverables:

- proposal/checklist/audit aligned to current code
- explicit classification of:
  - canonical formal paths
  - bridge paths
  - remaining legacy paths
- doc cleanup separating storage merge from formal merge

Required artifacts:

- merge implementation checklist
- merge gap audit

### Milestone 2: Canonical merge object everywhere

Deliverables:

- repo-layer direct emission remains canonical
- remaining bridge or legacy production paths are either removed or explicitly marked transitional
- immediate consumers are updated to speak merge object semantics directly where feasible

Required tests:

- existing merge kernel tests stay green
- targeted tests for any replaced bridge/legacy consumers

### Milestone 3: Exact merge operators

Deliverables:

- exact operator layer remains authoritative
- missing literature regressions and operator comparison cases are added where absent

Required tests:

- `tests/test_paf_merge.py`
- named literature regressions

### Milestone 4: Query semantics

Deliverables:

- skeptical and credulous queries over completions
- user-facing query/report helpers over the canonical merge object

Required tests:

- `tests/test_paf_queries.py`

### Milestone 5: World/query integration

Deliverables:

- worldline / render integration for the new merge object
- one user-visible query/report path over merged partial frameworks

Required tests:

- world/query integration tests

### Milestone 6: Structured projection

Deliverables:

- explicit projection from branch-local structured theories into AF/PAF summaries
- first integration path with existing ASPIC+ structures

Required tests:

- `tests/test_structured_merge_projection.py`

This milestone is the first one that touches the structured/abstract boundary directly.

It is still not a license to collapse the merge roadmap into the Odekerken-style inquiry roadmap. The boundary work here is about projection into the merge kernel, not about future-information reasoning over incomplete ASPIC+ theories.

---

## Atomic Commit Plan

Each milestone should be split into one or more commits that are individually reviewable and testable.

### Commit 1: Proposal and terminology cleanup

- update proposal/docs to distinguish storage merge from formal merge
- no behavior change

### Commit 2: RED tests for PAF kernel

- add `tests/test_paf_core.py`
- no implementation yet

### Commit 3: GREEN kernel implementation

- add `PartialArgumentationFramework`, completions, and distance code
- make `tests/test_paf_core.py` pass

### Commit 4: RED tests for repo direct emission

- add `tests/test_repo_merge_object.py`

### Commit 5: GREEN repo direct emission

- rewrite repo merge object production to emit the new formal object directly
- update immediate consumers in the same chunk

### Commit 6: RED tests for merge operators

- add `tests/test_paf_merge.py`
- include small exact-profile regressions

### Commit 7: GREEN merge operators

- implement expansion and exact Sum / Max / Leximax merge

### Commit 8: RED tests for query semantics

- add `tests/test_paf_queries.py`

### Commit 9: GREEN query implementation

- implement skeptical / credulous completion queries

### Commit 10: RED tests for world/query integration

- add integration tests for user-visible merge-object queries

### Commit 11: GREEN world/query integration

- connect worldline/render reporting to the new merge object

### Commit 12: RED tests for structured projection

- add `tests/test_structured_merge_projection.py`

### Commit 13: GREEN structured projection slice

- minimal branch-local structured projection into AF/PAF summaries

At every GREEN checkpoint:

- run targeted tests with `uv run pytest -vv`
- tee output to `logs/test-runs/`
- reread the milestone list before selecting the next chunk
- commit only after the targeted suite is green

---

## Delegation Boundaries

This work is suitable for delegated implementation if workers own disjoint chunks.

Good worker boundaries:

- Worker A: kernel datatype + completion enumeration + distance
- Worker B: repo direct emission + immediate consumer updates
- Worker C: exact merge operators + merge-property tests
- Worker D: query semantics + query-property tests
- Worker E: world/query integration
- Worker F: structured projection slice

Poor worker boundaries:

- multiple workers editing the same test file at once
- splitting a single kernel datatype across workers
- having a worker implement structured projection before repo direct emission and query semantics are stable

The critical-path rule is:

- kernel first
- then repo direct emission
- then merge operators
- then queries
- then world/query integration
- then structured projection

This keeps ownership clear and makes integration reviewable.

---

## Open Questions

1. How rich must the branch-local argumentation summary be to avoid semantic drift at the structured boundary?
2. Should source trust influence merge itself, or only post-merge defeat/preference?
   - Current default: post-merge defeat/preference or explanation only, not kernel merge.
3. Do we want completions enumerated explicitly, symbolically, or probabilistically?
4. Where should explanation edges live: in the structured layer only, or also on merged abstract objects?

---

## References

- Dung (1995), *On the Acceptability of Arguments and Its Fundamental Role in Nonmonotonic Reasoning, Logic Programming and n-Person Games*
- Konieczny & Pino Perez (2002), *Merging Information under Constraints: A Logical Framework*
- Coste-Marquis et al. (2007), *On the Merging of Dung's Argumentation Systems*
- Prakken (2010), *An Abstract Framework for Argumentation with Structured Arguments*
- Modgil & Prakken / Modgil (2018), *A General Account of Argumentation with Preferences*
- Odekerken et al. (2023, 2025), *Argumentation Reasoning in ASPIC+ under Incomplete Information*
- Li, Oren, Norman (2011), *Probabilistic Argumentation Frameworks*
- Hunter & Thimm (2017), *Probabilistic Reasoning with Abstract Argumentation Frameworks*
