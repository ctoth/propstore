# Semantic Merge

propstore now exposes a formal repository merge layer built around partial argumentation frameworks rather than the older public six-bucket merge-classification API.

The central split is:

- **storage merge**: a two-parent git commit that preserves both sides with provenance
- **formal merge**: an explicit partial framework with `attack / ignorance / non_attack`, completion semantics, exact merge operators, and query/report surfaces

Merge commits are not themselves the IC merge operator. They are provenance-preserving storage objects built from the formal merge object.

## What Exists Now

The repository layer exposes these public merge modules:

| Module | What it does |
|---|---|
| `propstore/repo/merge_framework.py` | `PartialArgumentationFramework`, completion enumeration, exact per-pair edit distance |
| `propstore/repo/merge_classifier.py` | `MergeArgument`, `RepoMergeFramework`, `build_merge_framework()` — direct repo emission of the formal merge object |
| `propstore/repo/merge_commit.py` | `create_merge_commit()` — two-parent storage merge built from the formal merge object |
| `propstore/repo/branch_reasoning.py` | branch assumptions, nogoods, and synthetic contradiction stances derived from the merge framework |
| `propstore/repo/paf_merge.py` | exact `consensual_expand()`, `sum_merge_frameworks()`, `max_merge_frameworks()`, `leximax_merge_frameworks()` |
| `propstore/repo/paf_queries.py` | skeptical and credulous completion queries |
| `propstore/repo/merge_report.py` | repo-facing summary/report helper over merge frameworks |
| `propstore/repo/structured_merge.py` | branch-local structured summaries via ASPIC projection, then exact merge candidates over those summaries |

`propstore/repo/__init__.py` re-exports the public merge surface.

## Formal Mapping

| Git operation | Formal role | Status |
|---|---|---|
| branch | isolated source belief state | implemented operationally |
| merge-base | common ancestor for source comparison | implemented |
| repo merge object | partial argumentation framework over emitted alternatives | implemented |
| completion query | skeptical / credulous acceptance over completions | implemented |
| exact AF merge operators | Sum / Max / Leximax over tiny AF profiles | implemented |
| storage merge commit | provenance-preserving two-parent commit | implemented |
| branch-local structured summary | ASPIC-derived AF summary per branch | implemented first slice |

The literature alignment is:

- **Coste-Marquis et al. 2007**: partial frameworks, consensual expansion, completions, AF-level merge operators
- **Konieczny & Pino Perez 2002**: operator vocabulary and aggregation intuition
- **Modgil / Prakken / ASPIC+**: branch-local structured summaries
- **Mason & Johnson 1989**: branch assumptions and nogoods

## Repository Merge Object

`propstore/repo/merge_classifier.py`

### `build_merge_framework()`

```python
def build_merge_framework(
    kr: KnowledgeRepo,
    branch_a: str,
    branch_b: str,
) -> RepoMergeFramework
```

This is the public repo merge boundary.

It:

1. finds the merge base
2. loads claims from base, left, and right snapshots via `GitTreeReader`
3. emits branch-specific alternatives as `MergeArgument` objects
4. constructs a `PartialArgumentationFramework` over the emitted alternatives

The output is:

- `RepoMergeFramework.branch_a`, `branch_b`
- `RepoMergeFramework.arguments`: emitted alternatives with provenance
- `RepoMergeFramework.framework`: the formal partial framework

### `MergeArgument`

Each emitted alternative carries:

- `claim_id`: emitted ID, possibly disambiguated
- `canonical_claim_id`: original semantic claim identity before emission
- `concept_id`
- `claim`: full claim dict ready for storage serialization
- `branch_origins`: source branches supporting this emitted alternative

### How disagreement is represented

The public output is no longer a six-valued merge enum. Instead:

- **compatible / identical / one-sided edit** cases collapse to one emitted alternative where appropriate
- **conflict** cases emit both branch alternatives and mark them as mutual `attack`
- **phi-node / regime split** cases emit both branch alternatives and mark them as mutual `ignorance`

The internal left-v-right conflict check still uses the existing conflict detector to distinguish genuine overlap from regime split. But that distinction now feeds the formal merge object directly instead of becoming the public API.

## Partial Framework Kernel

`propstore/repo/merge_framework.py`

### `PartialArgumentationFramework`

The kernel is a strict partition of all ordered pairs in `A x A` into:

- `attacks`
- `ignorance`
- `non_attacks`

Construction fails if the partition is incomplete or overlapping.

### Completions

`enumerate_paf_completions()` returns every Dung AF produced by resolving each ignorance pair either as attack or non-attack.

This is exact and intended for tiny merge objects and exact tests, not large-scale approximate inference.

### Distance

`merge_framework_edit_distance()` is exact Hamming distance over per-pair labels on a shared argument universe. It also accepts ordinary Dung AFs by coercing them to total partial frameworks with empty ignorance.

## Exact Merge Operators

`propstore/repo/paf_merge.py`

### `consensual_expand()`

Expands a source AF to a shared universe:

- in-scope known attacks stay attacks
- in-scope absent attacks become explicit non-attacks
- out-of-scope pairs become ignorance

### `sum_merge_frameworks()`

Exact search over tiny candidate AFs minimizing total edit distance to the expanded source profile.

### `max_merge_frameworks()`

Exact search minimizing worst-case edit distance to any source.

### `leximax_merge_frameworks()`

Exact lexicographic refinement of `max_merge_frameworks()`.

These operators currently target tiny AF profiles and are intended as exact merge kernels, not large-corpus approximations.

## Completion Queries

`propstore/repo/paf_queries.py`

### `skeptically_accepted_arguments()`

Returns arguments accepted in every extension of every completion under the chosen semantics.

### `credulously_accepted_arguments()`

Returns arguments accepted in some extension of some completion under the chosen semantics.

Currently supported semantics are:

- `grounded`
- `preferred`
- `stable`

## Branch Reasoning

`propstore/repo/branch_reasoning.py`

This module now consumes `RepoMergeFramework`, not legacy merge items.

### `make_branch_assumption()`

Builds branch assumption refs for ATMS reasoning.

### `branch_nogoods_from_merge()`

Generates nogoods only from **mutual attacks** between single-origin emitted alternatives.

Ignorance does not produce nogoods.

### `inject_branch_stances()`

Exports merge attacks as synthetic `contradicts` stances for current consumers that still speak in stance rows.

This is a bridge from the formal merge framework to existing contradiction-based consumers. It does not define the merge semantics itself.

## Storage Merge Commits

`propstore/repo/merge_commit.py`

### `create_merge_commit()`

```python
def create_merge_commit(
    kr: KnowledgeRepo,
    branch_a: str,
    branch_b: str,
    message: str = "",
    *,
    target_branch: str = "master",
) -> str
```

This creates a two-parent commit from the formal merge framework.

Behavior:

- non-claim files are merged left-over-right
- claim content is serialized from `RepoMergeFramework.arguments`
- conflicting emitted alternatives keep disambiguated IDs and `branch_origin` provenance
- the commit stores both parents and updates `target_branch`

This is the storage representation of a merge, not the query-time merge operator.

## Structured Merge Slice

`propstore/repo/structured_merge.py`

### `build_branch_structured_summary()`

Reads a branch snapshot directly from git:

- claims from claim files
- stance rows from both inline claim stances and `stances/*.yaml`

Then it builds a branch-local ASPIC projection via `build_aspic_projection()`.

### `build_structured_merge_candidates()`

Builds two branch-local structured summaries, extracts their AFs, and feeds those AFs through the exact operator layer (`sum`, `max`, or `leximax`).

This is the first implemented slice of the structured boundary. It is a branch-local structured summary pipeline, not yet a full theorem about instantiate-then-merge versus merge-then-instantiate.

## CLI Surface

`propstore/cli/merge_cmds.py`

### `pks merge inspect BRANCH_A BRANCH_B`

Builds the formal merge framework and prints a YAML summary including:

- emitted arguments
- attack and ignorance pairs
- completion count
- skeptical results
- credulous results
- per-argument status summary

### `pks merge commit BRANCH_A BRANCH_B`

Creates the two-parent storage merge commit from the same formal merge object and prints the commit SHA.

## What This Does Not Claim

- merge commits are not themselves IC merge operators
- the old public `MergeClassification` / `MergeItem` API is not the current public contract
- full structured merge equivalence theorems are not yet established
- the exact AF merge operators are not optimized for large profiles
- source-weighted structured preference aggregation is not yet implemented

## References

- **Coste-Marquis et al. (2007).** Partial frameworks, completions, consensual expansion, and AF merge operators.
- **Konieczny & Pino Perez (2002).** IC-merge operator family and aggregation vocabulary.
- **Modgil / Prakken.** ASPIC+ structured argumentation substrate.
- **Mason & Johnson (1989).** DATMS-style assumption-space interpretation for branch assumptions and nogoods.
