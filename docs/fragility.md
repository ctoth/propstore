# Fragility Analysis

Fragility answers the question: "what is the cheapest thing I could learn that would most change what I believe?" It ranks concepts by how sensitive the system's conclusions are to new information, then weighs that sensitivity against investigation cost. A concept with high fragility and low cost is the highest-leverage target for further research.

The fragility subsystem lives in the render layer (layer 5). It reads from the argumentation layer (Dung AF, ATMS), the theory layer (sensitivity analysis, parameterizations), and the opinion layer (subjective logic fusion). It never mutates source storage -- it produces a ranked `FragilityReport` of recommendations.

## The three dimensions

Fragility is measured along three independent dimensions. Each captures a different way that new information could change conclusions.

### Parametric fragility

Parametric fragility measures how sensitive a concept's computed value is to changes in its inputs. A concept whose output swings wildly when one input nudges slightly is parametrically fragile -- a better measurement of that input would substantially change the derived value.

The computation uses SymPy elasticities from the sensitivity analysis module (`propstore/sensitivity.py:analyze_sensitivity`). For each concept with a parameterization formula, the system computes the elasticity of the output with respect to each input, then takes the maximum absolute elasticity as the raw score. Raw scores are normalized globally across all concepts (`propstore/fragility.py:_normalize_parametric_scores`), so the most sensitive concept always scores 1.0 and others get proportional scores.

### Epistemic fragility

Epistemic fragility measures how likely it is that learning something new would change what the system believes about a concept. A concept that sits in the current extension but could be flipped out in many alternative futures is epistemically fragile -- the current belief rests on thin ice.

The computation uses the ATMS engine's `concept_stability()` to enumerate consistent futures bounded by `atms_limit` (default 2^8 = 256 futures). It counts "flip witnesses" -- futures where the concept's in/out status changes -- and delegates to `propstore/fragility.py:weighted_epistemic_score`.

**Sign correction:** The scoring inverts for IN vs OUT nodes. For a concept currently IN the extension, the score equals witnesses/consistent_futures (many flips = fragile). For a concept currently OUT, the score equals 1 - witnesses/consistent_futures (many entries = well-supported = low fragility). This ensures that fragility always points toward instability regardless of current status.

**Probability weighting:** When probability weights are provided, the system sums witness weights divided by total weight instead of counting. When absent, uniform weighting applies (simple ratio).

Two papers ground this dimension:

- **Howard 1966** (Information Value Theory): the clairvoyance formula averages over the prior distribution to compute the value of perfect information. Epistemic fragility is a discrete analogue -- it averages over consistent ATMS futures.
- **Gardenfors & Makinson 1988** (Revisions of Knowledge Systems using Epistemic Entrenchment): entrenchment deficit = 1 - support ratio. Concepts with low entrenchment are the ones most likely to be revised.

### Conflict fragility

Conflict fragility measures how much resolving a conflict would change the argumentation outcome. A concept involved in a conflict whose resolution would rearrange the entire grounded extension is conflict-fragile -- settling that one dispute has outsized consequences.

The computation uses `propstore/fragility.py:score_conflict`. For each conflict on a concept, it builds hypothetical Dung AFs with each conflicting claim removed in turn, computes the grounded extension of each hypothetical, and measures the Hamming distance to the current grounded extension. The maximum normalized distance (clamped to [0, 1]) becomes the score. If no active argumentation graph is available, the system falls back to a placeholder score of 1.0.

**Paper citation:** AlAnaissy 2024 defines ImpS^rev -- a revised impact measure via hypothetical removal. The Hamming distance on extensions is a discrete analogue of this measure.

## Combination methods

The three dimension scores are combined into a single fragility score. Four combination methods are available (`propstore/fragility.py:combine_fragility`):

| Method | Formula | When to use |
|--------|---------|-------------|
| `top2` (default) | Average of two highest available scores | Rewards multi-dimensional fragility. A concept fragile in only one dimension is penalized relative to one fragile in two. |
| `mean` | Average of all available scores | Uniform weighting. Use when all dimensions are equally important. |
| `max` | Maximum of available scores | Only the worst dimension matters. Use when any single source of fragility is sufficient reason to investigate. |
| `product` | Product of all available scores | All dimensions must be high for the combined score to be high. Use when you only care about concepts that are fragile in every way simultaneously. |

If only one dimension score is available, all methods return that score. If no scores are available, the combined score is 0.0.

## Cost tiers and ROI

Each fragility target is assigned an investigation cost tier based on what kind of thing it is:

| Tier | Cost | Target kinds | Intuition |
|------|------|-------------|-----------|
| 1 | Trivial | Assumptions | Check existing data, toggle an assumption |
| 2 | Cheap | Conflicts; concepts with existing parametric data | Read a paper, run a calculation |
| 3 | Moderate | Concepts with no claims; unknown kinds | Commission new analysis, collect new samples |
| 4 | Expensive | (Not currently assigned by default) | Run an experiment, replicate a study |

**ROI = fragility / cost_tier.** A concept with fragility 0.9 and cost tier 1 has ROI 0.9 -- it is both highly fragile and trivial to investigate. A concept with fragility 0.9 and cost tier 3 has ROI 0.3 -- equally fragile, but expensive to resolve. Sorting by ROI surfaces the highest epistemic leverage per unit of investigation cost.

## Discovery tiers

Discovery tiers control which concepts are included in the analysis.

- **Tier 1 (default):** Only concepts already known to the ATMS -- those with parameterizations or active claims. These are the "queryable" assumptions the system already tracks.
- **Tier 2:** Also discovers "known unknowns" via `propstore/fragility.py:_discover_tier2_concepts` -- concepts that appear as inputs in parameterization formulas but have no active claims. These receive fragility = 1.0 (maximally fragile because completely unknown), cost_tier = 3, and ROI = 1.0/3. Tier 2 surfaces blind spots: variables the system depends on but has never measured.

## Pairwise interactions

After ranking, the system detects pairwise interactions among the top fragility targets (`propstore/fragility.py:detect_interactions`). This matters because learning two things together may be worth more or less than the sum of learning each separately.

| Interaction | Meaning | Detection |
|-------------|---------|-----------|
| **synergistic** | A flip requires 2+ queryables simultaneously -- neither alone suffices | Multi-queryable ATMS witnesses |
| **redundant** | Both targets can independently flip the same concept -- learning either one suffices | Multiple singleton witnesses for the same concept |
| **mixed** | Both synergistic and redundant for different concepts | Both patterns detected |
| **independent** | No shared effect detected between the pair | No shared witnesses |
| **unknown** | No ATMS available; interaction type cannot be determined | ATMS engine absent |

**Paper citation:** Howard 1966 (Information Value Theory): the joint clairvoyance value V_c(x, y) may exceed or fall below V_cx + V_cy. Investigating two variables together may be synergistic (the whole exceeds the sum) or redundant (they provide overlapping information).

## Additional scoring functions

Two additional scoring functions are implemented but not wired into the main ranking pipeline:

- **`opinion_sensitivity()`** (`propstore/fragility.py:opinion_sensitivity`): Computes the marginal derivative dE(wbf)/du_i at the current operating point via central finite difference. Measures how much changing one opinion's uncertainty shifts the fused expectation. Uses adaptive delta with up to 3 retries at shrinking step sizes. Returns None if fewer than 2 opinions or if any opinion is dogmatic (u near 0). Grounded in Josang 2001: E(omega) = b + a*u, WBF fuses N opinions.

- **`imps_rev()`** (`propstore/fragility.py:imps_rev`): Implements AlAnaissy 2024's revised impact measure: sigma(B | remove A->B) - sigma(B). Computes how much removing an attack changes the target's DF-QuAD strength (Freedman et al. 2025). Builds a ProbabilisticAF with dogmatic argument/defeat existence, computes DF-QuAD strengths with and without the attack, returns the difference.

## CLI usage

```bash
# Top 10 most fragile concepts
pks world fragility --top-k 10

# Sort by ROI, discover unknown inputs
pks world fragility --sort-by roi --discovery-tier 2

# Focus on a single concept, use mean combination
pks world fragility --concept concept5 --combination mean

# Skip epistemic dimension, output JSON
pks world fragility --skip-epistemic --format json
```

Full option reference:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--concept` | TEXT | None | Focus on a single concept |
| `--top-k` | INTEGER | 20 | Number of results to return |
| `--combination` | `top2`/`mean`/`max`/`product` | `top2` | Combination method |
| `--skip-parametric` | FLAG | false | Skip parametric fragility dimension |
| `--skip-epistemic` | FLAG | false | Skip epistemic fragility dimension |
| `--skip-conflict` | FLAG | false | Skip conflict fragility dimension |
| `--sort-by` | `fragility`/`roi` | `fragility` | Sort order for results |
| `--discovery-tier` | INTEGER | 1 | 1 = ATMS-known only, 2 = also discover unknown inputs |
| `--format` | `text`/`json` | `text` | Output format |

Text output produces a table with columns: Rank, Score, ROI, Cost, Kind, Target. Followed by a "World fragility" summary (mean of top min(10, len) scores). If interactions are detected, an Interactions section follows.

JSON output produces a dict with `world_fragility`, `analysis_scope`, `targets` array, and `interactions` array.

## References

- **AlAnaissy 2024.** ImpS^rev: revised impact measure via hypothetical removal. Grounds conflict fragility scoring and the `imps_rev()` function.
- **Freedman et al. 2025.** DF-QuAD gradual semantics for quantitative bipolar argumentation frameworks. Used by `imps_rev()` for strength computation.
- **Gardenfors & Makinson 1988.** Revisions of Knowledge Systems using Epistemic Entrenchment. Entrenchment deficit = 1 - support ratio. Grounds the epistemic fragility dimension.
- **Howard 1966.** Information Value Theory. Clairvoyance weighting, non-additivity of joint value of information. Grounds epistemic fragility weighting and pairwise interaction detection.
- **Josang 2001.** A Logic for Uncertain Probabilities. E(omega) = b + a*u, WBF fusion. Grounds `opinion_sensitivity()`.
