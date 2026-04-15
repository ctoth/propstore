# Fragility Intervention Architecture

**Date:** 2026-04-14
**Status:** target architecture
**Supersedes:** [proposals/fragility-plan.md](./fragility-plan.md) for the canonical fragility surface

## Goal

Replace concept-ranked fragility with a strongly typed, intervention-ranked system.

The canonical question is not:

- "Which concept has a high fragility score?"

The canonical question is:

- "Which exact intervention is carrying this conclusion, and what is the cheapest high-leverage thing to inspect next?"

This proposal is a direct replacement architecture, not a migration plan. We control the stack. The implementation shape is:

1. define the final intervention surface
2. make every fragility contributor emit that surface
3. update every caller
4. delete concept-as-target production output

## Design Verdicts

### 1. Concepts are subjects, not targets

Concepts remain useful as the thing whose value or status is at issue. They are not the thing the user investigates next. The thing the user investigates is an intervention target.

Examples:

- ATMS queryable assumption
- missing measurement for a concept
- conflict between claims
- grounded fact from the gunray bundle
- grounded rule instance
- bridge-level undercut or defeasible rule handle

### 2. The fragility core must be fully typed

The core semantic pipeline must not pass around:

- `dict[str, Any]` payloads
- `(score, detail)` tuples
- ad hoc interaction dicts

The boundary should look like the rest of the repo's typed surfaces:

- immutable dataclasses
- enums for kind/status/policy
- explicit provider protocols
- IO coercion at the boundary only

### 3. Provenance is first-class

Every intervention target must carry enough provenance to map back to the authored or grounded source that created it.

This is already available in the repo:

- `QueryableAssumption` for future assumptions
- `GroundedRulesBundle` for gunray facts/rules/arguments
- grounded ASPIC rule names via `rule_doc.id#<canonical substitution>`

The fragility layer should preserve these identities, not flatten them into concept labels.

### 4. A single universal scalar is not pinned down yet

The literature supports:

- value-of-information as the outer objective
- stability/relevance as the structured incomplete-information lens
- local dialectical impact as the conflict/rule perturbation lens

The literature does **not** force one honest cross-family scalar for our current stack, because we do not yet have a single project-wide payoff function.

So the target architecture must separate:

- target identity
- family-local scoring
- ranking policy

That is not a shim. It is the correct architecture until a true payoff surface exists.

## Canonical Model

```python
from dataclasses import dataclass
from enum import StrEnum


class InterventionKind(StrEnum):
    ASSUMPTION = "assumption"
    MISSING_MEASUREMENT = "missing_measurement"
    CONFLICT = "conflict"
    GROUND_FACT = "ground_fact"
    GROUNDED_RULE = "grounded_rule"
    BRIDGE_UNDERCUT = "bridge_undercut"


class InterventionFamily(StrEnum):
    ATMS = "atms"
    DISCOVERY = "discovery"
    CONFLICT = "conflict"
    GROUNDING = "grounding"
    BRIDGE = "bridge"


class RankingPolicy(StrEnum):
    HEURISTIC_ROI = "heuristic_roi"
    FAMILY_LOCAL_ONLY = "family_local_only"
    PARETO = "pareto"


@dataclass(frozen=True)
class InterventionProvenance:
    family: InterventionFamily
    source_ids: tuple[str, ...]
    subject_concept_ids: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class InterventionTarget:
    intervention_id: str
    kind: InterventionKind
    family: InterventionFamily
    subject_id: str | None
    description: str
    cost_tier: int
    provenance: InterventionProvenance
    payload: object


@dataclass(frozen=True)
class RankedIntervention:
    target: InterventionTarget
    local_fragility: float
    roi: float
    ranking_policy: RankingPolicy
    score_explanation: str
```

The important point is not the exact field spellings. The important point is the separation:

- `InterventionTarget` answers identity and provenance
- `payload` is typed per intervention family
- `RankedIntervention` answers ranking

## Typed Payload Families

Each intervention family gets its own payload type.

### ATMS assumption payload

Wrap `QueryableAssumption` directly instead of reducing it to CEL text.

```python
@dataclass(frozen=True)
class AssumptionTarget:
    queryable: QueryableAssumption
    stabilizes_concepts: tuple[str, ...]
    witness_count: int
    consistent_future_count: int
```

### Missing-measurement payload

```python
@dataclass(frozen=True)
class MissingMeasurementTarget:
    concept_id: str
    discovered_from_parameterizations: tuple[str, ...]
    downstream_subjects: tuple[str, ...]
```

### Conflict payload

```python
@dataclass(frozen=True)
class ConflictTarget:
    claim_a_id: str
    claim_b_id: str
    affected_concept_ids: tuple[str, ...]
```

### Grounding payload

Use the identities the repo already has.

```python
@dataclass(frozen=True)
class GroundFactTarget:
    section: str
    predicate_id: str
    row: tuple[object, ...]


@dataclass(frozen=True)
class GroundedRuleTarget:
    rule_name: str  # rule_doc.id#<canonical substitution>
    substitution_key: str
    head_literal: str
```

### Bridge payload

```python
@dataclass(frozen=True)
class BridgeUndercutTarget:
    defeater_rule_name: str
    target_rule_name: str
    undercut_literal_key: str
```

## Canonical Identities

Identity must be deterministic and permutation-invariant.

### Assumptions

Use `QueryableAssumption.assumption_id`.

### Missing measurements

Use a deterministic discovery key:

- `missing_measurement:<concept_id>`

### Conflicts

Canonicalize the endpoint pair:

- `conflict:<min(claim_a_id, claim_b_id)>:<max(claim_a_id, claim_b_id)>`

### Ground facts

Use section + predicate id + typed row tuple:

- `ground_fact:<section>:<predicate_id>:<typed-row-key>`

### Grounded rules

Use the bridge's existing grounded rule name:

- `grounded_rule:<rule_doc.id#canonical_substitution_key>`

### Bridge undercuts

Use the bridge's existing defeater naming:

- `bridge_undercut:<defeater_name>-><target_rule_name>`

## Contributor Boundaries

The public orchestrator should depend on protocols, not private fields.

```python
class FragilityContributor(Protocol):
    def collect_targets(self, bound: FragilityWorld) -> tuple[InterventionTarget, ...]: ...
    def score_targets(self, bound: FragilityWorld, targets: tuple[InterventionTarget, ...]) -> tuple[RankedIntervention, ...]: ...
```

Target contributor families:

1. `fragility_atms.py`
2. `fragility_discovery.py`
3. `fragility_conflicts.py`
4. `fragility_grounding.py`
5. `fragility_bridge.py`
6. `fragility_orchestrator.py`

`propstore/fragility.py` should become the orchestrator and typed public entrypoint, not the place where every family-specific hack accumulates.

## How This Fits Gunray and Grounded Rules

This design matches the repo's existing grounded surfaces directly.

### Ground facts

`GroundedRulesBundle.sections` already exposes four explicit sections. Those sectioned ground atoms are intervention-shaped identities:

- `definitely:bird(tweety)`
- `defeasibly:flies(tweety)`
- `undecided:dangerous(tweety)`

Fragility should not coerce these back into concept outputs. It should emit them as ground-fact interventions with their bundle provenance attached.

### Grounded rule instances

`propstore/aspic_bridge/grounding.py` already constructs stable grounded rule names:

- `rule_doc.id#<canonical substitution>`

That is the correct identity for a grounded-rule intervention target. It is already typed, stable, and provenance-preserving.

### Bridge undercuts

The bridge already synthesizes defeater names of the form:

- `<defeater_name>-><target_rule_name>`

That is the correct identity for undercut-shaped bridge interventions.

## Scoring Verdict

### Pinned down now

We can pin down now:

- score bounds are in `[0, 1]`
- cost tiers are positive integers
- ROI is `local_fragility / cost_tier`
- contributors score only their own family
- ranking policy is explicit

### Not pinned down now

We should **not** fake a literature-backed universal scalar across:

- ATMS futures
- missing measurements
- conflict topology
- gunray ground facts
- grounded rule instances
- bridge undercuts

without a genuine payoff model.

### Therefore

The orchestrator should support explicit policies:

1. `HEURISTIC_ROI`
   Uses contributor-local fragility and cost tiers. Honest heuristic.
2. `FAMILY_LOCAL_ONLY`
   No cross-family scalar. Sort within family only.
3. `PARETO`
   Surface non-dominated interventions across fragility and cost.

If later we define a real payoff surface, we can add a true VOI policy. That will be a new ranking policy, not a rewrite of the target identity model.

## Tests First

The test suite should define the architecture before the implementation does.

### Contract tests

These must exist before implementation:

1. intervention targets are immutable and hashable
2. reordering source rows does not change intervention identities
3. duplicate authored/grounded evidence does not emit duplicate intervention targets
4. every target carries provenance back to the exact authored or grounded source
5. no contributor emits targets outside its declared family
6. ranking policy is always explicit in `RankedIntervention`

### Property tests

These should be Hypothesis-driven:

1. conflict identity is symmetric under endpoint swap
2. queryable order does not change emitted assumption targets
3. parameterization order does not change missing-measurement targets
4. permuting rule files, facts, or grounded sections does not change grounded intervention identities
5. a rule with `n` satisfying substitutions emits exactly `n` grounded-rule identities
6. all family-local scores remain in `[0, 1]`
7. ROI is monotone decreasing in `cost_tier` for fixed local fragility
8. adding unrelated facts/rules/queryables does not create duplicate identities or change canonical ids of existing targets

## Workstreams

Each workstream is tests-first and ends by deleting the old production path for the slice it replaces.

### Workstream 0: Core typed model

1. add canonical enums, payload dataclasses, provenance objects, ranking policy
2. add identity canonicalizers
3. add contract tests for immutability, hashability, determinism, provenance

### Workstream 1: ATMS interventions

1. emit `ASSUMPTION` targets from `QueryableAssumption`
2. emit `MISSING_MEASUREMENT` targets from parameterization/discovery
3. add Hypothesis tests for order invariance and no-duplication
4. delete concept-target epistemic output

### Workstream 2: Conflict interventions

1. emit `CONFLICT` targets with canonical endpoint ordering
2. score them with typed conflict details
3. add symmetry and score-bound properties
4. delete concept-target conflict output

### Workstream 3: Grounding interventions

1. emit `GROUND_FACT` and `GROUNDED_RULE` targets from `GroundedRulesBundle`
2. use bundle and rule-name provenance directly
3. add permutation-invariance and substitution-count properties

### Workstream 4: Bridge interventions

1. emit `BRIDGE_UNDERCUT` targets from the compiled bridge
2. attach exact rule-name and undercut-literal provenance
3. add identity-stability tests against bridge rebuilds

### Workstream 5: Orchestrator and CLI

1. aggregate typed contributors
2. implement explicit ranking policies
3. update CLI/json/text rendering for intervention targets
4. delete concept-oriented rendering paths

## Dedicated Execution Slices

The future execution slices are dedicated by family. We do not mix families inside one slice.

### Slice 0A: Core typed model only

- `InterventionKind`
- `InterventionFamily`
- `RankingPolicy`
- `InterventionProvenance`
- `InterventionTarget`
- `RankedIntervention`
- canonical identity helpers

Exit condition:

- typed model exists
- contract tests pass
- no family logic added yet

### Slice 1A: ATMS assumption targets only

- emit assumption interventions from `QueryableAssumption`
- no missing-measurement discovery in this slice
- no conflict/grounding/bridge work in this slice

Exit condition:

- assumption targets are the only scored fragility targets
- old concept-ranked ATMS output is deleted
- ATMS assumption tests pass

### Slice 1B: Missing-measurement targets only

- emit missing-measurement interventions from parameterization discovery
- keep this separate from ATMS assumption scoring

Exit condition:

- missing-measurement identities are canonical and tested
- old concept-ranked discovery output is deleted

### Slice 2A: Conflict targets only

- emit canonical conflict interventions
- score only conflict interventions in this slice

Exit condition:

- old concept-ranked conflict output is deleted
- conflict symmetry and score-bound tests pass

### Slice 3A: Ground-fact targets only

- emit `GROUND_FACT` interventions from `GroundedRulesBundle.sections`
- no grounded-rule scoring in this slice

Exit condition:

- permutation-invariance tests pass for ground-fact identities

### Slice 3B: Grounded-rule targets only

- emit `GROUNDED_RULE` interventions from grounded rule-instance names
- no bridge-undercut work in this slice

Exit condition:

- substitution-count and identity-stability tests pass

### Slice 4A: Bridge undercut targets only

- emit `BRIDGE_UNDERCUT` interventions from the compiled bridge

Exit condition:

- undercut identities are stable across rebuilds
- bridge-only tests pass

### Slice 5A: Orchestrator only

- aggregate all family contributors
- implement ranking-policy selection
- no new family logic in this slice

Exit condition:

- orchestrator and CLI run only on intervention targets
- concept-oriented rendering path is gone

## Execution Discipline

The implementation plan must enforce plan rereads and tight scope control.

1. Before starting a workstream slice, reread this plan and name the exact slice being executed.
2. After every commit, reread this plan before choosing the next action.
3. After every passing substantial targeted test run, reread this plan before choosing the next action.
4. After every passing full-suite run, reread this plan before reporting status or picking follow-up work.
5. Keep commits small and numerous. The default should be many commits, each tied to one kept reduction or one completed test-first slice.
6. Do not widen to a new target family while the current workstream slice remains incomplete.
7. If a slice header says "only", that means exactly that family and no adjacent family work until the slice exit condition is met.

## Literature Position

What the local paper collection already supports:

- Howard 1966 supports value-of-information as the outer objective and warns that joint information value is non-additive.
- Gärdenfors 1988 and Dixon 1993 support the entrenchment/revision interpretation of ATMS-side fragility.
- Odekerken 2025 supports stability and relevance under incomplete ASPIC+ information.
- Al Anaissy 2024 supports local impact measures for gradual semantics.
- Diller 2025 supports grounded fact/rule instances as first-class grounded units.
- Ballester-Ripoll 2024 warns against one-at-a-time sensitivity stories that miss interactions.

What remains open by design:

- the exact universal cross-family scalar
- the eventual payoff surface for true decision-theoretic VOI

Those are ranking-policy questions. They are not blockers for defining the canonical intervention architecture.
