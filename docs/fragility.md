# Fragility Analysis

Fragility analysis now ranks **interventions**, not concepts.

The core question is:

- "What exact thing should I inspect next if I want to change or stabilize what I currently believe?"

The fragility subsystem lives in the render layer. It reads from:

- ATMS futures
- conflict topology
- grounded-rule bundles
- the ASPIC bridge

It does not mutate source storage. It produces a typed `FragilityReport` whose main payload is a ranked tuple of intervention targets.

## Canonical Surface

The public surface is intervention-first:

- `InterventionTarget`
- `RankedIntervention`
- `FragilityReport`

Concepts are still present as **subjects** in provenance and scoring context, but they are no longer the primary ranked output.

Current intervention families:

- `assumption`
- `missing_measurement`
- `conflict`
- `ground_fact`
- `grounded_rule`
- `bridge_undercut`

Each target carries:

- canonical identity
- family
- kind
- cost tier
- provenance
- typed payload

## Family Semantics

### Assumptions

ATMS assumption targets come from `QueryableAssumption` and are ranked by how strongly they participate in witness futures that flip a concept's status.

The scoring uses `weighted_epistemic_score()`. For currently supported concepts, many flip witnesses means high fragility. For currently unsupported concepts, many future entries reduce fragility because the concept is actually well-supported under future completions.

### Missing Measurements

Missing-measurement targets are discovered from parameterization inputs that have no active claims. They are intervention targets because the next action is to obtain a measurement, not to stare at the downstream concept.

Their current score is a discovery heuristic based on how many downstream subjects depend on the missing value.

### Conflicts

Conflict targets represent canonical claim pairs. Their score is the maximum grounded-extension delta from removing either side of the pair, via `score_conflict()`.

### Ground Facts

Ground-fact targets come from `GroundedRulesBundle.sections`. Their score combines:

- section-level uncertainty
- how many grounded-rule antecedents depend on the fact

This keeps the identity surface exact while making the score depend on actual grounded structure rather than a flat constant.

### Grounded Rules

Grounded-rule targets are keyed by the existing bridge-grounding rule name:

- `rule_doc.id#<canonical substitution>`

Their current score combines:

- antecedent count
- how many grounded defeaters target the rule

### Bridge Undercuts

Bridge undercut targets are keyed by the existing synthesized name:

- `<defeater_name>-><target_rule_name>`

Their score is computed from actual bridge behavior:

- number of attacks launched by arguments using that undercut rule
- number of defeats that actually survive preference filtering

## Ranking Policies

The system does **not** currently pretend to have a single literature-settled cross-family scalar.

Instead it exposes explicit ranking policies:

- `heuristic_roi`
- `family_local_only`
- `pareto`

`heuristic_roi` is the default. It ranks by family-local fragility divided by cost tier.

`family_local_only` keeps families separate instead of forcing a cross-family total order.

`pareto` returns the non-dominated frontier over local fragility and cost tier.

## Pairwise Interactions

Interaction detection currently operates on assumption interventions. It looks at ATMS witness structure and reports:

- `synergistic`
- `redundant`
- `mixed`
- `independent`
- `unknown`

This is where the Howard 1966 non-additivity story appears operationally: two assumptions can have more or less joint value than their individual scores suggest.

## Additional Scoring Helpers

Two standalone scoring helpers still exist outside the main ranking pipeline:

- `opinion_sensitivity()`
- `imps_rev()`

They remain available as local analytical tools, but they are not yet primary ranking contributors.

## CLI Usage

```bash
# Default ranking across all intervention families
uv run pks world fragility

# Only ATMS and conflict contributors
uv run pks world fragility --skip-grounding --skip-bridge

# Pareto frontier instead of heuristic ROI
uv run pks world fragility --ranking-policy pareto

# JSON output
uv run pks world fragility --format json
```

Text output now shows intervention-oriented columns:

- `Rank`
- `Score`
- `ROI`
- `Cost`
- `Family`
- `Kind`
- `Intervention`

JSON output includes:

- `world_fragility`
- `analysis_scope`
- `interventions`
- `interactions`

## References

- Howard 1966: value of information and non-additive joint value
- Gärdenfors 1988 and Dixon 1993: entrenchment/revision background for ATMS-side fragility
- Odekerken 2025: stability and relevance under incomplete ASPIC+ information
- Al Anaissy 2024: local impact measures for gradual semantics
- Diller 2025: grounded fact/rule instances as first-class grounded units
- Ballester-Ripoll 2024: interaction-sensitive sensitivity analysis
