# Semantic Merge

propstore now exposes a formal repository merge layer built around partial argumentation frameworks rather than the older public six-bucket merge-classification API.

The central split is:

- **storage merge**: a two-parent git commit that preserves both sides with provenance
- **formal merge**: an explicit partial framework with `attack / ignorance / non_attack`, completion semantics, exact merge operators, and query/report surfaces

Merge commits are not themselves the IC merge operator. They are provenance-preserving storage objects built from the formal merge object.

The important consequence is:

- source branch artifacts remain the epistemic source of truth
- the formal merge object is the semantic merge state
- materialized merge claim files are storage/export projections, not the ontological truth of the merge

## What Exists Now

The storage layer exposes these public merge modules:

| Module | What it does |
|---|---|
| `argumentation.partial_af` | `PartialArgumentationFramework`, completion enumeration, exact per-pair edit distance, exact AF merge operators, skeptical and credulous completion queries |
| `propstore/merge/merge_classifier.py` | `MergeArgument`, `RepositoryMergeFramework`, `IntegrityConstraint`, `build_merge_framework()` — direct storage emission of the formal merge object |
| `propstore/merge/merge_commit.py` | `create_merge_commit()` — two-parent storage merge built from the formal merge object |
| `propstore/merge/merge_report.py` | storage-facing summary/report helper over merge frameworks |
| `propstore/merge/structured_merge.py` | branch-local structured summaries via ASPIC projection, then exact merge candidates over those summaries |
| `propstore/families/sameas/` | graded sameAs assertion documents for explicit identity evidence |

The CLI and application layers consume these owner modules rather than owning merge semantics themselves.

## Formal Mapping

| Git operation | Formal role | Status |
|---|---|---|
| branch | isolated source belief state | implemented operationally |
| merge-base | common ancestor for source comparison | implemented |
| repo merge object | partial argumentation framework over emitted alternatives | implemented |
| n-ary profile input | additional branch snapshots beyond the two git parents | implemented for merge-framework construction |
| integrity constraint surface | required/forbidden artifact pruning for candidate arguments | implemented first slice |
| completion query | skeptical / credulous acceptance over completions | implemented |
| exact AF merge operators | Sum / Max / Leximax over tiny AF profiles | implemented |
| storage merge commit | provenance-preserving two-parent commit | implemented |
| branch-local structured summary | ASPIC-derived AF summary per branch | implemented first slice |

The literature alignment is:

- **Coste-Marquis et al. 2007**: partial frameworks, consensual expansion, completions, AF-level merge operators
- **Konieczny & Pino Perez 2002**: operator vocabulary and aggregation intuition
- **Halpin et al. 2010 / Beek et al. 2018**: sameAs links are explicit graded evidence, not unconditional union-find closure
- **Buneman et al. 2001**: materialized alternatives carry source witness basis and where/why provenance
- **Roddick 1995**: non-claim file disagreement is surfaced as conflict, not silently resolved by side bias
- **Modgil / Prakken / ASPIC+**: branch-local structured summaries

## Repository Merge Object

`propstore/merge/merge_classifier.py`

### `build_merge_framework()`

```python
def build_merge_framework(
    snapshot: RepositorySnapshot,
    branch_a: str,
    branch_b: str,
    *,
    integrity_constraint: IntegrityConstraint | None = None,
    additional_branches: Sequence[str] = (),
) -> RepositoryMergeFramework
```

This is the public storage merge boundary.

It:

1. finds the merge base
2. loads claims from base and branch snapshots through the repository family layer
3. emits branch-specific alternatives as `MergeArgument` objects
4. constructs a `PartialArgumentationFramework` over the emitted alternatives
5. optionally prunes emitted alternatives against the integrity-constraint surface

The output is:

- `RepositoryMergeFramework.branch_a`, `branch_b`
- `RepositoryMergeFramework.arguments`: emitted alternatives with provenance
- `RepositoryMergeFramework.framework`: the formal partial framework
- `RepositoryMergeFramework.semantic_candidates`: non-collapsed semantic-near matches that require explicit identity evidence before convergence

### `MergeArgument`

Each emitted alternative carries:

- `assertion_id`: situated assertion identity, including provenance and conditions
- `artifact_id`: canonical claim artifact identity
- `logical_id`: source logical handle when available
- `canonical_claim_id`: merge grouping key; logical-id aliases do not union artifacts unless accepted sameAs evidence supports that grouping
- `concept_id`
- `claim`: typed merge claim ready for storage serialization
- `branch_origins`: source branches supporting this emitted alternative
- `witness_basis`: source artifact/paper/page/branch witness records

### How disagreement is represented

The public output is no longer a six-valued merge enum. Instead:

- **compatible / identical / one-sided edit** cases collapse to one emitted alternative where appropriate
- **conflict** cases emit both branch alternatives and mark them as mutual `attack`
- **phi-node / regime split** cases emit both branch alternatives and mark them as mutual `ignorance`
- **untranslatable condition** cases emit ignorance rather than being relabelled as phi-nodes
- **unknown detector output** remains explicit ignorance; the merge layer no longer guesses from concept equality

The internal conflict check still uses the existing conflict detector to distinguish genuine overlap from regime split. That distinction feeds the formal merge object directly instead of becoming a storage-time commitment. Comparisons without source-paper provenance fail instead of inventing a synthetic source.

### sameAs Discipline

Logical-id aliases are not transitive truth. Shared handles can suggest candidate identity, but they do not trigger unconditional union-find closure. Explicit sameAs evidence lives under the `sameas/` family with graded Halpin-style relation values:

- `sim:sameIndividual`
- `sim:claimsIdentical`
- `sim:almostSameAs`

The merge boundary keeps artifacts distinct unless accepted sameAs evidence supports convergence.

## Partial Framework Kernel

`argumentation.partial_af`

### `PartialArgumentationFramework`

The kernel is a strict partition of all ordered pairs in `A x A` into:

- `attacks`
- `ignorance`
- `non_attacks`

Construction fails if the partition is incomplete or overlapping.

### Completions

`enumerate_completions()` returns every Dung AF produced by resolving each ignorance pair either as attack or non-attack.

This is exact and intended for tiny merge objects and exact tests, not large-scale approximate inference.

### Distance

`merge_framework_edit_distance()` is exact Hamming distance over per-pair labels on a shared argument universe. It also accepts ordinary Dung AFs by coercing them to total partial frameworks with empty ignorance.

## Exact Merge Operators

`argumentation.partial_af`

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

`argumentation.partial_af`

### `skeptically_accepted_arguments()`

Returns arguments accepted in every extension of every completion under the chosen semantics.

### `credulously_accepted_arguments()`

Returns arguments accepted in some extension of some completion under the chosen semantics.

Currently supported semantics are:

- `grounded`
- `preferred`
- `stable`

## Storage Merge Commits

`propstore/merge/merge_commit.py`

### `create_merge_commit()`

```python
def create_merge_commit(
    snapshot: RepositorySnapshot,
    branch_a: str,
    branch_b: str,
    message: str = "",
    *,
    target_branch: str | None = None,
) -> str
```

This creates a two-parent commit from the formal merge framework.

Behavior:

- non-claim file disagreements raise an explicit conflict instead of silently choosing a side
- claim content is serialized from `RepositoryMergeFramework.arguments`
- conflicting emitted alternatives keep canonical artifact IDs and branch-origin provenance
- manifest rows include witness-basis records
- claim-file source papers come from the materialized source claims, not a synthetic `"merged"` paper
- the commit stores both parents and updates `target_branch`

This is the storage representation of a merge, not the query-time merge operator.
It should be read as a projection artifact, not as the thing that makes the disagreement disappear.

## Structured Merge Slice

`propstore/merge/structured_merge.py`

### `build_branch_structured_summary()`

Reads a branch snapshot directly from git:

- claims from claim files
- stance rows from both inline claim stances and `stances/*.yaml`

Then it builds a branch-local ASPIC projection via `build_aspic_projection()`.

### `build_structured_merge_candidates()`

Builds two branch-local structured summaries, extracts their AFs, and feeds those AFs through the exact operator layer (`sum`, `max`, or `leximax`).

This is the first implemented slice of the structured boundary. It is a branch-local structured summary pipeline, not yet a full theorem about instantiate-then-merge versus merge-then-instantiate.

### `argumentation_evidence_from_projection()`

Structured merge evidence supports grounded, preferred, and stable semantics. For multi-extension semantics, `accepted_assertion_ids` is the credulous set and `skeptical_assertion_ids` is the skeptical set.

## CLI Surface

`propstore/cli/merge_cmds.py`

### `pks merge inspect BRANCH_A BRANCH_B`

Builds the formal merge framework and prints a YAML summary including:

- `surface: formal_merge_report`
- `framework_type: partial_argumentation_framework`
- emitted arguments
- attack and ignorance pairs
- relation counts
- completion count
- skeptical results
- credulous results
- per-argument status summary

### `pks merge commit BRANCH_A BRANCH_B`

Creates the two-parent storage merge commit from the same formal merge object and prints a YAML payload including:

- `surface: storage_merge_commit`
- `branch_a`, `branch_b`, and `target_branch`
- materialized claim files grouped by source and rival origin
- `manifest_path: merge/manifest.yaml`
- `commit_sha`

## What This Does Not Claim

- merge commits are not themselves IC merge operators
- `claims/merged.yaml` is not a claim that the merge has produced a single final epistemic truth
- the old public `MergeClassification` / `MergeItem` API is not the current public contract
- full structured merge equivalence theorems are not yet established
- the exact AF merge operators are not optimized for large profiles
- source-weighted structured preference aggregation is not yet implemented
- the first IC surface is a repository merge constraint hook, not a full proof that every IC0-IC8 postulate holds for every future merge policy

## References

- **Coste-Marquis et al. (2007).** Partial frameworks, completions, consensual expansion, and AF merge operators.
- **Konieczny & Pino Perez (2002).** IC-merge operator family and aggregation vocabulary.
- **Modgil / Prakken.** ASPIC+ structured argumentation substrate.
- **Mason & Johnson (1989).** DATMS-style assumption-space interpretation for branch assumptions and nogoods.
