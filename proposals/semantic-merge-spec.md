# Proposal: Git as Belief Revision — Semantic Branching and Merging for Propstore

## Context

Propstore stores claims, stances, and concepts as YAML files in a git repo. Currently git is dumb storage — single branch (master), no merge awareness. The system has ATMS and ASPIC+ as parallel reasoning backends, but neither is git-aware. Dixon 1993 showed ATMS context-switching maps to AGM belief revision operations, but this connection is purely aspirational in propstore today (`atms.py` line 11-12 explicitly disclaims it).

A literature survey (March 2026) confirmed: **nobody has formalized VCS operations as belief revision**. The pieces exist separately — branching-time belief revision (Bonanno 2012), IC merging (Konieczny & Pino Pérez 2002), AF merging (Coste-Marquis et al. 2007), AGM for Dung frameworks (Baumann & Brewka 2015), iterated revision (Darwiche & Pearl 1997) — but nobody has composed them. That composition is what this proposal describes.

### The key insight

The merge driver **classifies conflicts rather than resolving them**. Both sides flow into storage with provenance. IC merging is a render-time computation parameterized by operator choice. This preserves propstore's non-commitment discipline while giving git's DAG formal belief-revision semantics.

## Formal Mapping

| Git operation | Belief revision operation | Correctness criteria | Source |
|---|---|---|---|
| commit on branch | iterated revision of epistemic state | DP postulates C1-C4 | Darwiche & Pearl 1997 |
| branch | context fork in branching-time frame | PLS property | Bonanno 2012 |
| merge | IC merging of multiple belief bases | IC0-IC8 | Konieczny & Pino Pérez 2002 |
| AF merge | edit distance + aggregation on PAFs | concordance, clash-free | Coste-Marquis et al. 2007 |
| AF expansion | kernel union | K1-K6 | Baumann & Brewka 2015 |

## What Gets Branches

Three kinds, distinguished by convention:

- **`paper/{slug}`** — each paper being processed. Claims land on a paper branch, then merge into mainline. Merge conflicts = the paper disagrees with existing knowledge.
- **`agent/{run_id}`** — each LLM extraction session. Human reviews, merges. Quality gate pattern.
- **`hypothesis/{name}`** — exploratory forks. "What if we adopt grounded semantics instead of preferred?" Branch, explore, compare without committing.

Master is the integration branch. It contains only what has been explicitly accepted or classified through a merge operation.

## Existing Architecture (integration points)

| Component | File | Key detail |
|---|---|---|
| Git backend | `propstore/cli/git_backend.py:348` | Hardcoded `refs/heads/master` — the single line to parameterize |
| TreeReader | `propstore/tree_reader.py:60` | `GitTreeReader(repo, commit=sha)` — already branch-ready |
| Sidecar builder | `propstore/build_sidecar.py:266` | `commit_hash` as rebuild key — can be branch-specific |
| Repository | `propstore/cli/repository.py:62-68` | `Repository.git` → KnowledgeRepo, no branch param |
| RenderPolicy | `propstore/world/types.py:178` | Dataclass with strategy, backend, decision criteria |
| ResolutionStrategy | `propstore/world/types.py:114` | Enum: recency, sample_size, argumentation, override |
| ATMS | `propstore/world/atms.py` | AssumptionRef has kind, source, cel — extensible to branch assumptions |
| ASPIC+ bridge | `propstore/aspic_bridge.py` | T1-T7 translation rules, PAF not yet used |

Data flow: YAML on disk → git commit → sidecar build (SQLite) → WorldModel → resolution (ASPIC+ or ATMS) → render.

---

## Phase 1: Multi-Branch Git Primitives

**Goal**: Branch CRUD in KnowledgeRepo. Commits can target any named branch. Existing single-branch behavior is the default.

### Package Structure: `propstore/repo/`

All repository-layer concerns live in a new subpackage:

```
propstore/repo/
    __init__.py          # re-exports KnowledgeRepo, BranchInfo, classify_merge, etc.
    git_backend.py       # KnowledgeRepo (moved from propstore/cli/git_backend.py)
    branch.py            # BranchInfo dataclass, branch CRUD methods
    merge_classifier.py  # MergeClassification enum, MergeItem, classify_merge()
    merge_commit.py      # two-parent commit construction, provenance annotation
    ic_merge.py          # Sigma/Max/GMax render-time operators (Phase 4)
```

`propstore/cli/git_backend.py` becomes a thin re-export shim during transition, then removed. All new callers import from `propstore.repo`.

### Changes to `propstore/repo/git_backend.py` (moved from cli/)

1. **Parameterize `_commit()`** with `branch: str = "master"`.
   - Line 348: `self._repo.refs[f"refs/heads/{branch}".encode()] = commit.id`
   - Parent lookup reads from `refs/heads/{branch}` instead of `self._repo.head()`
   - HEAD symref only set when `branch == "master"`

2. **Branch CRUD methods** (in `propstore/repo/branch.py`):
   - `create_branch(name: str, source_commit: str | None = None) -> str`
   - `delete_branch(name: str) -> None` (refuse to delete master)
   - `list_branches() -> list[str]`
   - `branch_head(name: str) -> str | None`
   - `merge_base(branch_a: str, branch_b: str) -> str | None` — walk parents to common ancestor

3. **Parameterize** `commit_files()`, `commit_deletes()`, `commit_batch()` with optional `branch` arg.

### `propstore/repo/branch.py`

```python
@dataclass(frozen=True)
class BranchInfo:
    name: str
    tip_sha: str
    kind: str  # "paper", "agent", "hypothesis"
    parent_branch: str
    created_at: int
```

Branch metadata stored as YAML at `branches/meta/{name}.yaml` inside the repo (committed on master).

### What doesn't change

- `sync_worktree()` — always materializes HEAD (master). Multi-branch data accessed via `GitTreeReader(repo, commit=branch_tip_sha)`.
- `tree_reader.py` — already accepts arbitrary commit SHA. No changes needed.

### Tests

- `test_branch_crud`: create, list, delete; verify Dulwich refs
- `test_commit_to_branch`: commit to non-master, verify master unchanged
- `test_branch_read_isolation`: same path, different content on different branches
- `test_merge_base`: fork, diverge, find common ancestor
- `test_existing_tests_unchanged`: all existing tests pass (they target master by default)

### Formal properties

- **DP C1-C4**: each branch is an epistemic state (ordered commit sequence), not just a belief set
- **PLS**: `merge_base()` gives the branching point; git's DAG satisfies PLS because branches share a unique common ancestor

---

## Phase 2: Semantic Merge Classification

**Goal**: When two branches touch the same knowledge, classify the relationship without resolving it. Both sides flow into a merge commit with provenance.

### New file: `propstore/merge_classifier.py`

Operates at **claim granularity** (not file, not concept).

```python
class MergeClassification(Enum):
    IDENTICAL = "identical"       # same claim, same value
    COMPATIBLE = "compatible"     # different claims, no conflict
    PHI_NODE = "phi_node"        # same concept, different values — both kept
    CONFLICT = "conflict"        # contradictory (via conflict_detector)
    NOVEL_LEFT = "novel_left"    # claim only on left branch
    NOVEL_RIGHT = "novel_right"  # claim only on right branch

@dataclass(frozen=True)
class MergeItem:
    classification: MergeClassification
    claim_id: str
    concept_id: str
    left_value: Any | None
    right_value: Any | None
    base_value: Any | None
    left_branch: str
    right_branch: str

def classify_merge(
    repo: KnowledgeRepo,
    branch_a: str,
    branch_b: str,
) -> list[MergeItem]:
    """Three-way diff at claim granularity."""
```

Algorithm:
1. Find merge-base via `repo.merge_base(branch_a, branch_b)`
2. Read all claim files from base, branch_a tip, branch_b tip via `GitTreeReader`
3. For each claim ID in the union: classify using existing `ConflictClass` as sub-check
4. Return classification list

### Changes to `propstore/cli/git_backend.py`

Add `merge_commit()`:
- Creates a commit with **two parents** (tips of branch_a and branch_b)
- Tree built from classification: IDENTICAL/COMPATIBLE/NOVEL items included directly; PHI_NODE/CONFLICT items include BOTH claims with `branch_origin` provenance annotation
- Auto-generates stance files for PHI_NODE (stance type `"none"`) and CONFLICT (type recorded but unresolved)

### Interaction with .gitattributes

None. Merge is entirely in application code (Dulwich object-store level). No working-tree merge, no git merge machinery.

### Tests

- `test_classify_identical`: same claim on both branches → IDENTICAL
- `test_classify_phi_node`: same concept, different values → PHI_NODE
- `test_classify_conflict`: contradictory claims → CONFLICT
- `test_merge_commit_two_parents`: Dulwich commit has two parent SHAs
- `test_merge_preserves_both_sides`: both values readable from merged tree
- `test_merge_provenance`: claims carry `branch_origin` metadata

### Formal properties

- **IC0**: merged tree validated against same schema as any commit
- **IC3**: classification based on claim semantics (concept_id, value, type), not syntax
- **PAF**: classification maps to three-valued attack relation (CONFLICT → attack, COMPATIBLE → non-attack, PHI_NODE → ignorance)
- **Non-commitment**: no conflict resolved in storage; both sides persist with provenance

---

## Phase 3: Branch-Aware ATMS and ASPIC+

**Goal**: Reasoning backends become branch-aware. ATMS treats branches as assumption sets. ASPIC+ uses cross-branch attack relations.

### ATMS changes (`propstore/world/atms.py`)

1. **New assumption kind `"branch"`**: `AssumptionRef(assumption_id=f"branch:{name}", kind="branch", source=name, cel=f"branch == '{name}'")`
2. **Branch environments**: `EnvironmentKey` containing branch assumptions = "what is true under this branch's worldview"
3. **Nogoods from merge classification**: CONFLICT between branches A and B → `NogoodSet` entry scoping those claims
4. **New method**: `add_branch_assumptions(branch_name, claim_ids)` — register branch-scoped assumptions, propagate labels

No structural changes to `propstore/core/labels.py` — `AssumptionRef` already supports arbitrary kinds; `EnvironmentKey` algebra works for branch assumptions without modification.

### ASPIC+ changes (`propstore/aspic_bridge.py`)

1. **Cross-branch attack generation**: new function `branch_stances_to_contrariness(merge_items) -> ContrarinessFn` — CONFLICT items generate rebuts, PHI_NODE items generate undermines
2. **Branch-aware KB**: `build_branch_kb(branch_claims) -> KnowledgeBase` — claims tagged with branch origin, enabling branch-preference orderings

### Sidecar changes (`propstore/build_sidecar.py`)

Unified sidecar (not per-branch):
- Add `branch TEXT` column to `claim_core` table
- Add `branch_meta` table
- Add `merge_classification` table
- `build_sidecar()` gets `branches: list[str] | None` parameter; iterates branch tips via `GitTreeReader`
- Content hash incorporates all branch tip SHAs

### Tests

- `test_atms_branch_assumptions`: two branches as assumptions, labels propagate correctly
- `test_atms_branch_nogood`: conflicting branches create nogoods
- `test_aspic_cross_branch_attacks`: CONFLICT items generate rebut attacks
- `test_unified_sidecar_multi_branch`: sidecar contains claims from multiple branches with branch tags

### Formal properties

- **K1-K6**: adding branch claims follows kernel union expansion
- **PAF formalism**: three-valued attack relation from merge classification
- **ATMS completeness**: every claim labeled with supporting branch combinations

---

## Phase 4: Render-Time Merge Operators

**Goal**: IC merging operators become selectable render policies. Users choose aggregation at query time, not storage time.

### New file: `propstore/ic_merge.py`

Three operator families from Konieczny & Pino Pérez 2002:

```python
def sigma_merge(branch_claims, concept_id) -> ResolvedResult:
    """Majority: accept value supported by most branches."""

def max_merge(branch_claims, concept_id) -> ResolvedResult:
    """Quasi-merge: minimize total edit distance to all branches."""

def gmax_merge(branch_claims, concept_id) -> ResolvedResult:
    """Arbitration: minimize maximum edit distance to any branch."""
```

Distance measured by edit distance on claim sets (PAF edit distance from Coste-Marquis et al.).

### Changes to `propstore/world/types.py`

```python
class MergeOperator(StrEnum):
    SIGMA = "sigma"    # majority
    MAX = "max"        # quasi-merging
    GMAX = "gmax"      # arbitration

# Add to RenderPolicy:
merge_operator: MergeOperator = MergeOperator.SIGMA
branch_filter: tuple[str, ...] | None = None
branch_weights: dict[str, float] | None = None
```

### Changes to `propstore/world/resolution.py`

New resolution path: when `RenderPolicy.merge_operator` is set and concept has multi-branch claims, delegate to `ic_merge.py`. Existing within-branch strategies (recency, sample_size, argumentation) remain available.

### CLI (`propstore/cli/compiler_cmds.py`)

- `pks query` gets `--branch` and `--merge-operator` flags
- `pks branch` command group: `list`, `create`, `merge`, `diff`
- `pks build` gets `--branches` flag

### Tests

- `test_sigma_majority`: 3 branches, 2 agree → majority wins
- `test_max_minimizes_total`: verify Max operator
- `test_gmax_minimizes_worst`: verify GMax operator
- `test_ic0_integrity`: merged result satisfies schema
- `test_render_policy_selects_operator`: same data, different policies, different results
- `test_branch_weights`: weighted merge respects trust ordering

### Formal properties

- **IC0-IC8**: each operator family satisfies full postulate set
- **Sigma/Max/GMax correctness**: distance-based characterization per KP2002
- **Non-commitment in storage**: IC merge operators are pure functions of branch data at render time; nothing written back

---

## Execution Protocol

### TDD-First, Paper-Verified

Every phase follows the same discipline:

1. **Paper check**: Before writing any code, read the relevant paper PNGs (not just notes.md). Verify the formal definitions against the actual source. Cite at docstring AND inline level.
2. **Write failing tests first**: Tests derived directly from the paper's formal definitions and theorems. Each test names the paper, theorem/definition number, and what property it verifies.
3. **Implement to pass tests**: Coder writes implementation. Tests must pass.
4. **Review**: Reviewer agent checks implementation against both the tests AND the paper claims. Catches drift from formal specification.
5. **Phase gate**: Phase is not complete until reviewer signs off.

### Foreman Protocol

Each phase chunk is dispatched via foreman protocol:
- **Foreman** (coordination-only): dispatches coder + reviewer, does not touch code
- **Coder**: reads papers, writes tests first, then implementation. Cites papers.
- **Reviewer**: checks code against paper PNGs, verifies test coverage, checks formal properties

This keeps theoretical fidelity high. The formal properties listed in each phase are not aspirational — they are test requirements.

## Dependency Graph

```
Phase 1 (git primitives)
   │
   ▼
Phase 2 (merge classification) ───► Phase 3 (ATMS/ASPIC+ integration)
   │                                       │
   ▼                                       ▼
Phase 4 (render-time operators) ◄─── Phase 3 complete
```

Phase 1 is strict prerequisite. Phases 2 and 3 can partially overlap. Phase 4 depends on both.

## Risk Areas

1. **Dulwich merge-base**: no built-in algorithm; must walk parents manually. Mitigate: cache in branch metadata table.
2. **Sidecar size**: N branches × claims. Mitigate: `branch_filter` on RenderPolicy, lazy loading.
3. **Backward compatibility**: existing repos have no branch metadata. Phase 1 treats single-branch repos as master-only; `branches/meta/` created on first branch operation.
4. **Theory drift**: Implementation subtly diverges from paper definitions. Mitigate: paper PNG checks at every phase, reviewer agent, TDD from formal properties.

## Papers Grounding This Proposal

| Paper | Claims | What it provides |
|---|---|---|
| Konieczny & Pino Pérez 2002 | 25 | IC postulates IC0-IC8, Sigma/Max/GMax operators, representation theorems |
| Coste-Marquis et al. 2007 | 18 | PAF formalism, AF edit distance, aggregation lifting IC to argumentation |
| Bonanno 2012 | 17 | Branching-time belief revision, PLS criterion for AGM-consistency |
| Darwiche & Pearl 1997 | 17 | Iterated revision postulates C1-C4, epistemic states |
| Baumann & Brewka 2015 | 12 | AGM expansion/revision for Dung AFs, kernel union operator |

Total: 89 claims extracted and registered in propstore.

## Open Questions and Gap-Closing Papers

Five theoretical gaps identified during design review. Each maps to specific papers being retrieved:

| Gap | Question | Paper to close it | Status |
|-----|----------|-------------------|--------|
| 1+4 | What's the distance metric for structured claims? What's the epistemic state representation? | **Spohn 1988** — OCFs are both the distance and the epistemic state | Retrieving |
| 2 | Does PLS hold on acyclic DAGs (git's commit graph)? | **Bonanno 2007** — frame conditions in temporal logic | Retrieving |
| 3 | Does ATMS scale with N branch assumptions and pairwise conflicts? | **Mason & Johnson 1989** — DATMS distributed scaling | Retrieving |
| 5 | Do ASPIC+ argumentation and IC merging compose or compete? | **Booth & Meyer 2006** — admissible revision operators | Retrieving |
| 5 | How do IC merge preference orderings feed ASPIC+ preferences? | **Amgoud & Vesic 2014** — rich preference-based AFs | Retrieving |

**Implementation must not begin until these gaps are closed.** Each paper's claims will be extracted and the formal properties verified against the design before coding starts.
