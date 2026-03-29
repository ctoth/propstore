# Semantic Merge

propstore formalizes git operations as belief revision. Branches are independent epistemic states; merges classify conflicts rather than resolving them; render-time operators aggregate multi-branch knowledge under different policies.

The key insight: merge drivers classify conflicts, never resolve them. Both sides flow into storage with provenance. Resolution is a render-time computation parameterized by operator choice. This preserves propstore's non-commitment discipline while giving git's DAG formal belief-revision semantics.

## Formal Mapping

| Git operation | Belief revision operation | Correctness criteria | Source |
|---|---|---|---|
| commit on branch | iterated revision of epistemic state | DP postulates C1-C4 | Darwiche & Pearl 1997 |
| branch | context fork in branching-time frame | BU validated | Bonanno 2007 |
| merge classification | three-way diff at claim granularity | IC3 syntax independence | Coste-Marquis et al. 2007 |
| merge commit | IC merging of multiple belief bases | IC0-IC8 | Konieczny & Pino Perez 2002 |
| branch assumption | DATMS agent belief space | nogood-based pruning | Mason & Johnson 1989 |
| cross-branch attack | PAF attack from merge conflict | contradicts stances | Coste-Marquis et al. 2007 |

Two frameworks apply to two operations:

- **Within a branch**: linear commit sequence, Backward Uniqueness holds (Bonanno 2007 claim 9), Darwiche-Pearl iterated revision applies.
- **At merge points**: IC merging (Konieczny & Pino Perez 2002) applies — this is belief MERGING, not revision.

The frameworks do not need unification. Branches are Darwiche-Pearl territory. Merges are Konieczny territory.

## Package Structure

All repository-layer concerns live in `propstore/repo/`:

| Module | What it does |
|--------|-------------|
| `git_backend.py` | `KnowledgeRepo` — Dulwich wrapper, commit/read/diff, branch-parameterized `_commit()` |
| `branch.py` | `BranchInfo` dataclass, `create_branch()`, `delete_branch()`, `list_branches()`, `branch_head()`, `merge_base()` |
| `merge_classifier.py` | `MergeClassification` enum (6 values), `MergeItem` dataclass, `classify_merge()` — three-way diff |
| `merge_commit.py` | `create_merge_commit()` — two-parent commits with provenance annotation |
| `branch_reasoning.py` | `make_branch_assumption()`, `branch_nogoods_from_merge()`, `inject_branch_stances()` — ATMS/ASPIC+ bridge |
| `ic_merge.py` | `MergeOperator` enum, `sigma_merge()`, `max_merge()`, `gmax_merge()`, `ic_merge()`, `claim_distance()` |

`propstore/repo/__init__.py` re-exports all public names.

## Merge Classification

`propstore/repo/merge_classifier.py`

### MergeClassification

Six-valued enum for claim-level merge results:

| Value | Meaning |
|-------|---------|
| `IDENTICAL` | Same claim, same value on both branches |
| `COMPATIBLE` | Different claims, no conflict (one-sided edit or disjoint additions) |
| `PHI_NODE` | Same concept, different values under mutually exclusive conditions — both kept |
| `CONFLICT` | Contradictory claims (via `conflict_detector`) |
| `NOVEL_LEFT` | Claim only on the left branch |
| `NOVEL_RIGHT` | Claim only on the right branch |

Classification is analogous to Coste-Marquis 2007 Definition 9: PAF three-valued attack relation (attack/non-attack/ignorance) applied to claim values rather than argument attack pairs.

### MergeItem

A frozen dataclass carrying the full three-way context for a single claim:

- `classification` — one of the six values above
- `claim_id`, `concept_id` — claim identity
- `left_value`, `right_value`, `base_value` — the claim dict from each version (or `None`)
- `left_branch`, `right_branch` — branch names

### classify_merge()

```python
def classify_merge(kr: KnowledgeRepo, branch_a: str, branch_b: str) -> list[MergeItem]
```

Three-way diff at claim granularity:

1. Find merge-base via `merge_base(kr, branch_a, branch_b)`
2. Load claims from base, left tip, and right tip via `GitTreeReader`
3. Index all claims by ID
4. For each claim ID in the union, classify:
   - All three present and unchanged → `IDENTICAL`
   - Only one side modified → `COMPATIBLE`
   - Both modified identically → `IDENTICAL`
   - Both modified differently → delegate to `_classify_modified_both()`
   - Present only on one side → `NOVEL_LEFT` or `NOVEL_RIGHT` (or `COMPATIBLE` when both branches diverged)

The `_classify_modified_both()` helper builds synthetic `LoadedClaimFile` objects and calls `detect_conflicts()` from the conflict detector to distinguish `CONFLICT` (genuine overlap) from `PHI_NODE` (mutually exclusive conditions).

Comparison uses `_claim_semantic_key()` which excludes provenance metadata, satisfying IC3 (syntax independence).

## Merge Commits

`propstore/repo/merge_commit.py`

### create_merge_commit()

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

Creates a Dulwich commit with two parents (the tips of `branch_a` and `branch_b`). The merged tree is built from the classification results:

- **IDENTICAL / NOVEL_LEFT / NOVEL_RIGHT**: included directly
- **COMPATIBLE**: the modified version is included (or both if disjoint additions)
- **CONFLICT / PHI_NODE**: both versions included with:
  - `branch_origin` provenance annotation via `_annotate_provenance()`
  - Disambiguated IDs via `_disambiguate_id()` (appends `__{branch_suffix}` so both can coexist)

All merged claims are serialized into a single `claims/merged.yaml` file. Non-claim files are merged with left-wins-on-conflict.

Returns the merge commit SHA as a string. Updates the `target_branch` ref.

## Branch Reasoning

`propstore/repo/branch_reasoning.py`

Three functions bridge merge classification to the ATMS and ASPIC+ reasoning backends.

### make_branch_assumption()

```python
def make_branch_assumption(branch_name: str) -> AssumptionRef
```

Creates an `AssumptionRef` with `kind="branch"` for use in ATMS label propagation. Per Mason & Johnson 1989: each agent's belief space maps to an assumption set. A git branch is an agent.

Branch names are sanitized (slashes and hyphens become underscores) for `assumption_id`, but the original name is preserved in the `source` field.

### branch_nogoods_from_merge()

```python
def branch_nogoods_from_merge(items: list[MergeItem]) -> NogoodSet
```

Generates ATMS nogoods from merge classification. Per Mason & Johnson 1989, claim 2: contradictions detected across agents become nogoods that limit context explosion.

Only `CONFLICT` items generate nogoods. Each creates a nogood `EnvironmentKey` containing both branch assumption IDs, meaning you cannot simultaneously accept both branches' values for that claim.

### inject_branch_stances()

```python
def inject_branch_stances(items: list[MergeItem]) -> list[dict[str, str]]
```

Synthesizes cross-branch stances for ASPIC+ attack generation. Per Coste-Marquis et al. 2007: conflicts between sources become attacks in the merged AF.

Only `CONFLICT` items produce stances (symmetric `contradicts`). `PHI_NODE` items produce no stances — per PAF Definition 9, ignorance is NOT attack. Each conflict produces two stance dicts (both attack directions).

## IC Merge Operators

`propstore/repo/ic_merge.py`

Render-time belief merging from Konieczny & Pino Perez 2002. Each operator takes a branch profile (dict mapping branch names to claim values) and returns the winning value.

### claim_distance()

```python
def claim_distance(a: Any, b: Any) -> float
```

Distance between two claim values. Numeric values use absolute difference; non-numeric use Hamming distance (0 if equal, 1 if different). Adapts Konieczny 2002 claim 13/17 from propositional Hamming distance to a scalar-value domain.

### sigma_merge() — Majority

```python
def sigma_merge(profile: dict[str, Any]) -> Any
```

Minimizes sum of distances to all branches (Konieczny 2002 claims 13-15). Satisfies IC0-IC8 + Maj. Candidates are drawn from the profile values (discrete selection, no interpolation). Ties broken by smaller value for IC3 syntax independence.

### max_merge() — Quasi-merge

```python
def max_merge(profile: dict[str, Any]) -> Any
```

Minimizes maximum distance to any branch (Konieczny 2002 claims 17-18). Satisfies IC0-IC3, IC7-IC8, Arb. Does NOT satisfy IC4-IC6. Uses deduplicated values for the Arb property (insensitivity to source multiplicity).

### gmax_merge() — Arbitration

```python
def gmax_merge(profile: dict[str, Any]) -> Any
```

Lexicographic comparison of sorted distance vectors (Konieczny 2002 claims 19-20). Refines Max. Satisfies IC0-IC8 + Arb. Uses deduplicated values for the Arb property.

### ic_merge() — Dispatcher

```python
def ic_merge(profile: dict[str, Any], *, operator: str = "sigma") -> Any
```

Dispatches to `sigma_merge`, `max_merge`, or `gmax_merge`. Default is Sigma.

## RenderPolicy Integration

`propstore/world/types.py`

`ResolutionStrategy` includes `IC_MERGE = "ic_merge"` as a strategy enum value.

`RenderPolicy` includes three fields for IC merge configuration:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `merge_operator` | `str` | `"sigma"` | Distance aggregation: `"sigma"`, `"max"`, or `"gmax"` |
| `branch_filter` | `tuple[str, ...] \| None` | `None` | Restricts which branches are included as sources |
| `branch_weights` | `Mapping[str, float] \| None` | `None` | Per-branch importance weights (not yet consumed by operators) |

`RenderPolicy` validates `merge_operator` on construction and supports YAML round-tripping via `from_dict()` / `to_dict()`.

## Future Work

- **Integrity constraints**: the mu parameter from IC0 (merged result must entail mu) is not yet implemented. When form-level validation is wired in, mu will map to the concept's form constraints.
- **Branch weights**: `branch_weights` is declared on `RenderPolicy` but not yet consumed by the merge operators. When implemented, weighted Sigma would use `w_i * d(I, phi_i)`.
- **Rich PAF attack inversion**: Amgoud & Vesic 2014 attack inversion (not removal) for preference-based defeat. Currently deferred — `aspic_bridge.py` would need enrichment.
- **Stability postulate verification**: Booth & Meyer 2006 admissible/restrained revision. Confirmed that argumentation and merging compose as a pipeline, but the formal verification is not implemented.

## References

- **Konieczny, S. & Pino Perez, R. (2002).** "Merging Information under Constraints: A Logical Framework." — IC postulates IC0-IC8, Sigma/Max/GMax operators, representation theorems. Grounds the IC merge operators.

- **Coste-Marquis, S. et al. (2007).** "Merging Argumentation Systems." — PAF three-valued attack relation, AF edit distance, aggregation lifting IC to argumentation. Grounds merge classification and cross-branch attack generation.

- **Darwiche, A. & Pearl, J. (1997).** "On the Logic of Iterated Belief Revision." — C1-C4 postulates for iterated revision. Each branch is an independent epistemic state. Grounds branch isolation.

- **Bonanno, G. (2007).** "Axiomatic Characterization of the AGM Theory of Belief Revision in a Temporal Logic." — Backward Uniqueness (BU). Git merge commits violate BU, confirming that merge points require IC merging rather than temporal revision. Grounds the two-framework separation.

- **Mason, C. & Johnson, R. (1989).** "DATMS: A Framework for Distributed Assumption Based Reasoning." — DATMS: each agent's belief space maps to an ATMS assumption set. Nogoods from cross-agent contradictions. Grounds branch assumptions and nogood generation.

- **Baumann, R. & Brewka, G. (2015).** "AGM Meets Abstract Argumentation: Expansion and Revision for Dung Frameworks." — AGM expansion/revision for Dung AFs, kernel union operator. Referenced for AF expansion semantics.

- **Spohn, W. (1988).** "Ordinal Conditional Functions: A Dynamic Theory of Epistemic States." — OCFs as epistemic states and distance metric. Branch commit histories carry implicit OCFs. Referenced for distance metric grounding.

- **Booth, R. & Meyer, T. (2006).** "Admissible and Restrained Revision." — Argumentation and merging compose as a pipeline, not alternatives. Confirmed but not formally verified.

- **Amgoud, L. & Vesic, S. (2014).** "Rich Preference-based Argumentation Frameworks." — Attack inversion for preference-based defeat, democratic preference lifting. Deferred — would enrich `aspic_bridge.py`.
