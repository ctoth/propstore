# Design Proposal: Replacing Bare Float Probability/Confidence

## Part 1: Problems (Grounded in Code Survey)

### Problem 1: Confidence is a Hardcoded Lookup Table

**What's broken:** `relate.py:76-83` defines `_CONFIDENCE_MAP`, a fixed dictionary mapping `(pass_number, strength_category)` to a float. The LLM classifies stance strength as "strong"/"moderate"/"weak" (a categorical label), and the system converts this to a float via a hand-written table. The LLM's actual epistemic state about its classification is never captured. The fallback is `0.5` (`relate.py:83`).

**Why it's broken:** This conflates two distinct quantities: (a) the LLM's categorical assessment of stance strength, and (b) the system's confidence that the LLM's classification is correct. The lookup table pretends to produce the latter from the former, but it fabricates it. A "strong" first-pass classification gets 0.95 regardless of whether the LLM was uncertain between "strong" and "none". The float has no evidential grounding -- it is not derived from any calibration data, validation set, or uncertainty quantification method.

**What the literature says:** Guo et al. (2017, p.0, p.5-7) demonstrate that raw neural network output scores are systematically miscalibrated -- modern deep networks are overconfident. The fix is post-hoc calibration (temperature scaling: a single learned parameter T dividing logits before softmax, optimized on a validation set). Sensoy et al. (2018, p.3-4) go further: instead of calibrating a point estimate, output Dirichlet distribution parameters that represent both a prediction and uncertainty about that prediction. The network outputs evidence $e_k \geq 0$ per class, yielding Dirichlet parameters $\alpha_k = e_k + 1$, belief mass $b_k = e_k/S$, and uncertainty mass $u = K/S$ where $S = \sum \alpha_k$. When total evidence is zero, $u = 1$ (total ignorance).

The lookup table should be replaced with either: (a) calibrated probabilities from a validation set (Guo), or (b) distributional outputs encoding uncertainty (Sensoy/Josang).

### Problem 2: Embedding Distance Used Raw in LLM Prompt

**What's broken:** At `relate.py:52`, the raw embedding distance float is interpolated directly into the second-pass LLM prompt as `"HIGHLY SIMILAR by embedding distance ({distance:.4f})"`. The meaning of this number depends on the embedding model, the distance metric (cosine, L2, etc.), and the corpus distribution. No normalization, calibration, or semantic interpretation is provided. The LLM receives a number it cannot meaningfully interpret.

**Why it's broken:** Embedding distances are not probabilities. A cosine distance of 0.34 from model A and 0.34 from model B may indicate very different degrees of similarity. Feeding raw distances to an LLM without context violates the principle that scores need transformation before interpretation (Guo 2017) and also wastes information -- the multi-model consensus machinery in `embed.py:372-446` operates on set membership rather than distance values, discarding the distributional information.

**What the literature says:** Guo et al. (2017, p.0) establish that raw model scores should not be treated as calibrated probabilities. For embedding distances specifically, the correct approach is: (a) calibrate distances against a reference distribution (e.g., compute percentile rank within the corpus), producing a statement like "more similar than 95% of claim pairs", or (b) map distances to opinion tuples (Josang 2001, p.20-21) where the uncertainty component explicitly represents how much we don't know. Josang's vacuous opinion (b=0, d=0, u=1, a=0.5) is the correct representation when we have no calibration data for a given embedding model.

### Problem 3: Three Conflated Uncertainty Concepts

**What's broken:** The system uses three different things called "strength" or "confidence":
- `strength`: categorical string from LLM output ("strong"/"moderate"/"weak"), stored in `claim_stance.strength`
- `confidence`: float [0,1] from lookup table (`relate.py:76-83`), stored in `claim_stance.confidence`, used as threshold gate at `argumentation.py:133`
- `claim_strength`: computed float from claim metadata (`preference.py:56-87`) -- averages `log1p(sample_size)`, `1/uncertainty`, and `confidence`

At `preference.py:79`, `confidence` is read from the claim dict with no type distinction -- it could be the NLI-derived confidence or any other float on the claim. These three quantities are semantically orthogonal but are stored and consumed as interchangeable bare floats.

**Why it's broken:** Josang (2001, p.1) identifies this exact problem: "it is also necessary to take into account that beliefs always are held by individuals and that beliefs for this reason are fundamentally subjective." A single float conflates at minimum three orthogonal dimensions identified in the research survey (notes-probability-representation-research.md, Section 5): (1) source reliability, (2) evidential support, (3) inferential strength. Collapsing these into one number makes it impossible to reason about which dimension is weak.

**What the literature says:** Josang (2001, p.7) provides the opinion tuple (b, d, u, a) which separates belief from uncertainty. Sensoy (2018, p.3) adds the distinction between vacuity (epistemic -- lack of evidence) and dissonance (aleatoric -- conflicting evidence). The structured confidence approach (Pichon et al. 2012, per research survey Section 5) further decomposes into relevance and truthfulness dimensions. The fix is: each source of uncertainty gets its own representation, composed only at render time.

### Problem 4: Confidence Threshold Gate Violates Non-Commitment

**What's broken:** At `argumentation.py:106,133`, `build_argumentation_framework` takes `confidence_threshold: float = 0.5`. Any stance with `confidence < confidence_threshold` is silently dropped before the AF is constructed. The same pattern appears at `structured_argument.py:60-61,147-148`. The `RenderPolicy` default is `confidence_threshold: float = 0.5` (`world/types.py:157`).

**Why it's broken:** This is a build-time filter, not a render-time filter. It violates the project's design checklist (CLAUDE.md): "Does this prevent ANY data from reaching the sidecar? If yes -> WRONG" and "Is filtering happening at build time or render time? If build -> WRONG." A stance with confidence 0.49 is treated identically to a stance that doesn't exist, permanently destroying information before the argumentation layer can reason about it.

**What the literature says:** Li et al. (2011, p.2) define PrAF where every argument and defeat has an existence probability. Instead of a binary gate (include if >= 0.5, exclude otherwise), the confidence becomes $P_D$ -- the probability that this defeat relation exists. The AF then marginalizes over all possible subgraphs (constellations approach), naturally handling low-confidence stances without discarding them. Hunter & Thimm (2017, p.8-9) provide the epistemic approach: assign probability $P(A)$ to each argument constrained by AF topology (COH: if $A \to B$ then $P(A) + P(B) \leq 1$). Both approaches keep all data and handle uncertainty formally rather than with a binary gate.

### Problem 5: Single-Element Strength Lists Waste Preference Machinery

**What's broken:** At `argumentation.py:158-159`, the system creates `[claim_strength(claim)]` -- always a single-element list -- for the preference comparison. The `strictly_weaker` function at `preference.py:16-34` supports both elitist and democratic set comparison (Modgil & Prakken Def 19), but the current projection never produces multi-element strength sets. The module self-documents this limitation at `argumentation.py:1-7`.

**Why it's broken:** With single-element lists, elitist and democratic comparison are identical. The preference ordering reduces to a simple float comparison, losing the multi-dimensional reasoning that Modgil & Prakken's framework provides. The `claim_strength` function itself (`preference.py:56-87`) averages heterogeneous components (log-scaled sample size, inverse uncertainty, raw confidence) into a single float, destroying the dimensional information that the set-comparison machinery was designed to preserve.

**What the literature says:** The opinion tuple (Josang 2001, p.7) naturally provides multiple dimensions: (b, d, u, a). Hunter & Thimm (2017, p.36-38) define ranking-based semantics where arguments are compared by probability values constrained by the AF topology. The fix is: pass the individual strength dimensions as separate elements of the strength set rather than averaging them into one number. For example, `[source_reliability, evidential_support, inferential_strength]` as a 3-element set would make elitist vs. democratic comparison meaningful.

---

## Part 2: Proposed Architecture

### Storage Representation: Beta Parameters

**The replacement for bare floats is `Beta(alpha, beta)` -- two non-negative reals per uncertainty estimate.**

**Justification:** Josang (2001, p.19-21, Def 12) proves a bijective mapping between opinion tuples (b, d, u, a) and Beta distributions. Given opinion components:
- $r = 2b/u$ (positive evidence count)
- $s = 2d/u$ (negative evidence count)
- $\alpha_{Beta} = r + 1$, $\beta_{Beta} = s + 1$ (standard Beta parameterization)

And the inverse: $b = r/(r+s+2)$, $d = s/(r+s+2)$, $u = 2/(r+s+2)$.

Sensoy (2018, p.3) confirms this: Dirichlet parameters $\alpha_k = e_k + 1$ directly encode evidence, and for the binary case (stance exists vs. doesn't), this reduces to Beta.

**Why Beta over opinion tuples directly:** Beta parameters are the canonical storage form because:
1. They are the most compact (2 numbers vs. 4 for opinion, though a is derivable from context)
2. They admit trivial evidence accumulation: adding evidence from a new source means adding to alpha/beta counts (Josang 2001, p.22, Def 13)
3. They are the native parameterization for both the Josang and Sensoy frameworks
4. Opinions, DS intervals [Bel, Pl], and credal intervals can all be derived from Beta params at render time (Josang 2001, p.20-21)

**Concrete storage:** Each uncertainty estimate becomes a row or tuple with:
- `alpha: REAL NOT NULL` -- positive evidence + 1 (minimum 1.0 = no positive evidence)
- `beta_param: REAL NOT NULL` -- negative evidence + 1 (minimum 1.0 = no negative evidence)
- `base_rate: REAL DEFAULT 0.5` -- relative atomicity $a$, the prior probability absent evidence

The vacuous state (total ignorance) is `Beta(1, 1)` with `base_rate = 0.5`. This is the starting point for any quantity with no evidence, replacing the current ambiguous `0.5` fallback.

**What this replaces in the schema:** The `claim_stance` table's `confidence REAL` column becomes `confidence_alpha REAL, confidence_beta REAL, confidence_base_rate REAL DEFAULT 0.5`. The `embedding_distance REAL` column is preserved as raw provenance data but gains a companion `similarity_alpha REAL, similarity_beta REAL` derived from calibration.

### Input Pipeline: Calibration then Distributional Mapping

The pipeline from raw model output to stored Beta parameters has three stages.

**Stage 1: Raw Score Preservation.** Store the raw model output (softmax logit, cosine distance, categorical label) with full provenance (model name, model version, metric type). This is source-of-truth data and is never modified. Currently done correctly for `embedding_distance` and `strength`.

**Stage 2: Calibration.** Apply post-hoc calibration to raw scores. Guo et al. (2017, p.5-7) show that temperature scaling (dividing logits by a single learned parameter T before softmax) reduces ECE from 14.4% to 1.34% on CIFAR-100 with ResNet-110. For propstore:

- **LLM stance classification:** The LLM returns a categorical label + optional logprobs. If logprobs are available, apply temperature scaling (T learned on a validation set of human-judged stances). If only categorical labels, use the calibrated frequency of correctness per category (an empirical version of the current lookup table, but derived from data rather than fabricated).
- **Embedding distances:** Calibrate against the corpus distribution. Compute the CDF of pairwise distances within the corpus to get a percentile rank. This converts "distance = 0.34" to "more similar than X% of pairs" -- a frequency-calibrated score.

**Stage 3: Distributional Mapping.** Convert calibrated scores to Beta parameters. Following Sensoy (2018, p.3-4):

- For a calibrated probability $p$ with effective sample size $n$ (number of validation examples backing the calibration): $\alpha = p \cdot n + 1$, $\beta = (1-p) \cdot n + 1$.
- For the current lookup table case (no validation data, $n = 0$): $\alpha = 1$, $\beta = 1$ -- the vacuous opinion. This is the honest representation of "we fabricated this number."
- For embedding distances with corpus calibration ($n$ = number of corpus pairs used): $\alpha$ and $\beta$ scale with $n$, narrowing the Beta distribution as more calibration data is available.

The base rate $a$ is set from corpus statistics: for stance existence, $a$ = empirical frequency of that stance type in the corpus. For embedding similarity, $a$ = 0.5 (symmetric prior).

### Argumentation Integration

The new representation feeds into argumentation through three mechanisms.

**Mechanism 1: PrAF Existence Probabilities (replaces threshold gate).** Following Li et al. (2011, p.2, Def 2):

Each stance's Beta parameters yield a probability expectation $E = b + a \cdot u$ (Josang 2001, p.5, Def 6), which becomes $P_D$ -- the probability that this defeat/support relation exists. The argumentation framework becomes a PrAF = $(A, P_A, D, P_D)$ where:
- $P_A(claim) = 1$ for all active claims (claims are taken as given)
- $P_D(stance) = E(\omega_{stance})$ = the probability expectation of the stance's opinion

This replaces the binary gate at `argumentation.py:133`. No stance is discarded. Instead, the AF marginalizes over possible subgraphs (Li 2011, p.4, Eq. 2), either exactly (for small AFs) or via Monte Carlo sampling (Li 2011, p.5, Algorithm 1) with Agresti-Coull stopping (Li 2011, p.7, Eq. 5).

**Mechanism 2: Epistemic Probability Constraints (replaces bare float ordering).** Following Hunter & Thimm (2017, p.8-9, Def 5):

Argument acceptability probabilities $P(A)$ are constrained by the AF topology. At minimum, the COH constraint applies: if $A \to B$ then $P(A) + P(B) \leq 1$ (Hunter 2017, p.9). For propstore's default (grounded semantics), the maximum entropy completion (Hunter 2017, p.22, Def 7) provides a unique probability assignment from partial assessments -- this replaces the current situation where `claim_strength` floats are compared without any topological constraint.

**Mechanism 3: Multi-Dimensional Preference Sets (replaces single-element lists).** Instead of `[claim_strength(claim)]`, pass a set of Beta-derived quantities to the preference comparison:

- Source reliability: Beta params from source provenance
- Evidential support: Beta params from stance classification
- Sample size: log-scaled as currently done, but as a separate dimension

This makes elitist vs. democratic comparison (`preference.py:16-34`) meaningful. Under elitist comparison, a claim is strictly weaker only if there exists a dimension where it is weaker than all of the target's dimensions. Under democratic, it must be weaker in every dimension.

### Render-Time Decisions

The render layer consumes Beta parameters through Denoeux's (2018) taxonomy of decision criteria. Different render policies select different criteria:

**Default (pignistic):** Convert Beta to opinion, compute $E(\omega) = b + a \cdot u$ (Josang 2001, p.5). This is equivalent to the pignistic transformation (Denoeux 2018, p.17-18) -- the unique transformation satisfying linearity + MEU. Use as the "best point estimate" when a single number is needed for display or simple ranking.

**Conservative (lower bound):** Use $Bel = b$ (Josang 2001, p.4). This is the lower bound of the credal interval -- the probability supported by direct evidence only, ignoring uncertainty. Equivalent to Denoeux's pessimistic Hurwicz criterion with $\alpha = 1$ (Denoeux 2018, p.17).

**Optimistic (upper bound):** Use $Pl = 1 - d$ (Josang 2001, p.4). The upper bound -- everything not contradicted by evidence. Equivalent to Hurwicz with $\alpha = 0$.

**Choice set (E-admissibility):** When multiple competing claims exist, compute the E-admissible set (Denoeux 2018, p.27-28) via linear programming: a claim is E-admissible iff there exists some probability distribution compatible with the belief function under which it maximizes expected utility. This directly implements non-commitment -- return the set of claims that *could* be correct, not a single winner.

**Uncertainty display:** Show the full interval $[Bel, Pl]$ alongside the point estimate. The width $Pl - Bel = u$ is the uncertainty mass -- directly interpretable as "how much we don't know."

### Non-Commitment Check

Verifying against CLAUDE.md design checklist:

1. **"Does this prevent ANY data from reaching the sidecar?"** No. Raw scores are preserved with provenance. Beta parameters are added alongside, not instead of. The calibration and mapping are additional columns, not filters.

2. **"Does this require human action before data becomes queryable?"** No. The pipeline from raw score to Beta params to opinion is fully automatic. Vacuous opinions (Beta(1,1)) are the default for uncalibrated data -- no human must supply calibration before the system works.

3. **"Does this add a gate anywhere before render time?"** No. The confidence threshold gate at `argumentation.py:133` is replaced by PrAF existence probabilities. All stances participate in the AF with their uncertainty; none are silently dropped.

4. **"Is filtering happening at build time or render time?"** Render time only. The sidecar stores Beta parameters for everything. The render layer applies decision criteria (pignistic, E-admissibility, etc.) based on `RenderPolicy`. Different policies can produce different results from the same stored data.

---

## Part 3: Concrete Changes

### Change 1: Opinion Module (new)

**What changes:** Create a new module (e.g., `propstore/opinion.py`) implementing:
- `Opinion` dataclass: (b, d, u, a) with constraint validation (b + d + u = 1)
- `BetaEvidence` dataclass: (alpha, beta_param, base_rate)
- Bijective conversions between Opinion and BetaEvidence (Josang 2001, p.20-21, Def 12)
- Probability expectation: $E = b + a \cdot u$ (Josang 2001, p.5)
- Consensus operator for combining independent sources (Josang 2001, p.25, Theorem 7)
- Discounting operator for trust chains (Josang 2001, p.24, Def 14)
- Interval extraction: $[Bel, Pl] = [b, 1-d]$

**Grounding:** Josang (2001) for all operators; Sensoy (2018) for the evidence-to-Dirichlet-to-opinion pipeline.

**Dependencies:** None. This is a leaf module with no imports from propstore.

### Change 2: Calibration Module (new)

**What changes:** Create a module (e.g., `propstore/calibrate.py`) implementing:
- Temperature scaling: given logits and a learned T, produce calibrated softmax (Guo 2017, p.5)
- Corpus CDF calibration: given a distance and a reference distribution, produce a percentile rank
- Calibrated-probability-to-Beta mapping: given calibrated $p$ and effective sample size $n$, produce BetaEvidence

**Grounding:** Guo et al. (2017) for temperature scaling; Sensoy (2018, p.3) for the evidence parameterization.

**Dependencies:** Depends on Change 1 (opinion module) for BetaEvidence dataclass.

### Change 3: Replace `_CONFIDENCE_MAP` in `relate.py`

**What changes:** The `_compute_confidence` function at `relate.py:82-83` should produce a `BetaEvidence` instead of a bare float. For the current lookup-table case (no validation data), the output should be `BetaEvidence(alpha=1, beta_param=1, base_rate=0.5)` -- the vacuous opinion, honestly representing that we have no calibrated confidence. When calibration data becomes available (a validation set of human-judged stances), the effective sample size $n$ grows and the Beta distribution narrows.

The categorical `strength` label from the LLM remains stored as-is (it is source data). The manufactured float is replaced by an honest uncertainty representation.

**Grounding:** Guo (2017) for why the current approach is wrong; Josang (2001, p.8) for the vacuous opinion as the correct "I don't know" representation.

**Dependencies:** Depends on Changes 1 and 2.

### Change 4: Schema Changes in `build_sidecar.py`

**What changes:** The `claim_stance` table schema (currently at `build_sidecar.py:826-841`) gains new columns:
- `confidence_alpha REAL` -- Beta alpha parameter for stance confidence
- `confidence_beta REAL` -- Beta beta parameter for stance confidence
- `confidence_base_rate REAL DEFAULT 0.5` -- base rate
- `similarity_alpha REAL` -- Beta alpha for calibrated embedding similarity (nullable, populated only when calibration data exists)
- `similarity_beta REAL` -- Beta beta for calibrated embedding similarity

The existing `confidence REAL` and `embedding_distance REAL` columns are preserved as raw provenance. New columns are *additional*, not replacements.

**Grounding:** Non-commitment principle (CLAUDE.md): raw data preserved, richer representation added alongside.

**Dependencies:** Depends on Changes 1-3 (opinion module produces the values to store).

### Change 5: Replace Confidence Threshold Gate in `argumentation.py`

**What changes:** The `confidence_threshold` parameter at `argumentation.py:106` and the gate at `argumentation.py:133` are removed. Instead, `build_argumentation_framework` constructs a PrAF (Li 2011, Def 2): each stance's Beta-derived probability expectation becomes $P_D$ on the defeat/support relation. The AF computation marginalizes over possible subgraphs rather than including/excluding stances based on a threshold.

For backward compatibility during transition, the threshold gate can be preserved as a fast approximation: stances with $E(\omega) < \epsilon$ (for very small $\epsilon$, e.g., 0.01) can be pruned as a performance optimization without semantic impact.

The same change applies to `structured_argument.py:60-61,147-148`.

**Grounding:** Li et al. (2011) for PrAF definition; Hunter & Thimm (2017) for epistemic probability constraints.

**Dependencies:** Depends on Changes 1 and 4 (Beta params must be in the sidecar).

### Change 6: Multi-Dimensional Preference Sets in `argumentation.py` and `preference.py`

**What changes:** At `argumentation.py:158-159`, replace `[claim_strength(claim)]` with a multi-element set derived from the claim's structured uncertainty:
- Element 1: source reliability (from provenance metadata, as a Beta expectation)
- Element 2: evidential support (from stance Beta params)
- Element 3: sample size (log-scaled, as currently computed)

The `claim_strength` function at `preference.py:56-87` becomes a multi-valued function returning a list of floats rather than averaging them. The `strictly_weaker` function at `preference.py:16-34` already supports this -- no change needed there.

**Grounding:** Modgil & Prakken (2018, Def 19) for multi-dimensional preference; Josang (2001) for opinion-derived dimensions.

**Dependencies:** Depends on Changes 1 and 4.

### Change 7: Render Policy Extensions in `world/types.py` and `world/resolution.py`

**What changes:** `RenderPolicy` at `world/types.py:181-196` gains new fields:
- `decision_criterion: str = "pignistic"` -- one of "pignistic", "lower_bound", "upper_bound", "e_admissible", "hurwicz"
- `pessimism_index: float = 0.5` -- Hurwicz alpha parameter (only used when criterion is "hurwicz")
- `show_uncertainty_interval: bool = False` -- whether to include [Bel, Pl] in output

The `confidence_threshold` field is deprecated (kept for backward compat) but no longer used by the argumentation layer.

`resolution.py` dispatch at `resolve()` uses the opinion module to convert Beta params to the chosen decision criterion's output.

**Grounding:** Denoeux (2018) for the taxonomy of decision criteria; Josang (2001) for interval extraction.

**Dependencies:** Depends on Changes 1 and 5.

### Dependency Order

```
Change 1 (opinion module) -- no dependencies
    |
    v
Change 2 (calibration module) -- depends on 1
    |
    v
Change 3 (relate.py confidence) -- depends on 1, 2
Change 4 (schema) -- depends on 1, 2, 3
    |
    v
Change 5 (remove threshold gate) -- depends on 1, 4
Change 6 (multi-dim preferences) -- depends on 1, 4
Change 7 (render policies) -- depends on 1, 5
```

Changes 5, 6, and 7 can proceed in parallel once 1-4 are complete.

---

## Part 4: What We Still Don't Know

### Gap 1: Calibration Data Does Not Exist Yet

Temperature scaling (Guo 2017) requires a held-out validation set of human-judged stances. Corpus CDF calibration requires a reference distribution of pairwise embedding distances. Neither exists. Until calibration data is collected, all Beta parameters will be vacuous or near-vacuous -- the system will be *correct* (honestly representing ignorance) but not *informative*. Calibration data collection is a prerequisite for the new representation to add value beyond honesty.

**Needed:** A small validation set (Guo 2017, p.7 suggests even small sets suffice for temperature scaling's single parameter) of human-judged stance classifications, and a corpus-level embedding distance distribution.

### Gap 2: PrAF Computational Cost

Li et al. (2011, p.8) show exact PrAF computation is exponential in $|A| + |D|$ and only practical for ~13 arguments. Monte Carlo is the alternative (Li 2011, p.5, Algorithm 1), but this requires running Dung extension computation many times per query. Propstore AFs can have hundreds of claims. The practical performance of MC sampling at propstore scale is unknown.

**Needed:** Benchmark propstore's existing `dung.grounded_extension` performance, estimate how many MC iterations are feasible per query, determine if the Agresti-Coull stopping criterion (Li 2011, p.7, Eq. 5) converges fast enough for interactive use.

### Gap 3: Consensus Operator Interaction with ATMS

Josang's consensus operator (2001, p.25, Theorem 7) combines opinions from independent sources. The ATMS maintains multiple contexts (assumption sets). It is not yet clear how consensus combination interacts with ATMS label propagation. Specifically: should consensus happen *within* a single ATMS context (combining sources that share the same assumptions) or *across* contexts? Dixon (1993) showed ATMS context switching implements AGM revision, but the quantitative (opinion/Beta) aspect is not addressed.

**Needed:** Prototype the interaction between opinion consensus and ATMS context switching. Determine whether combining Beta parameters across ATMS contexts preserves the non-commitment discipline or inadvertently collapses contexts.

### Gap 4: Hunter's Epistemic Approach Scalability

Hunter & Thimm (2017, p.7) note that the probability function maps $2^{Arg} \to [0,1]$ -- exponential in the number of arguments. Their maximum entropy completion (p.22) requires convex optimization over this space. For propstore AFs with hundreds of arguments, this is intractable without decomposition. Proposition 18 (p.27) shows the problem separates over connected components, but propstore AFs may have large connected components.

**Needed:** Analyze the connected component structure of typical propstore AFs. If components are small (< 20 arguments), Hunter's approach is feasible. If not, approximation methods are needed.

### Gap 5: LLM Logprob Availability

The calibration pipeline assumes LLM logprobs are available for stance classification. Not all LLM APIs expose logprobs (Guo 2017 predates the current LLM API landscape). If logprobs are unavailable, the only signal is the categorical label, and the Beta representation collapses to the vacuous opinion -- honest but uninformative.

**Needed:** Survey which LLM APIs used by propstore (via litellm) expose logprobs for classification tasks. If logprobs are available, temperature scaling is straightforward. If not, alternative UQ methods are needed (e.g., self-consistency sampling: run the classification N times and count agreements, directly yielding evidence counts for Beta parameters).

### Gap 6: Multinomial Extension

The current design uses binary Beta distributions (stance exists vs. doesn't). But stance *type* classification is multinomial: 7 types (rebuts, undercuts, undermines, supports, explains, supersedes, none). The natural extension is Dirichlet parameters (Sensoy 2018, p.3), one per type, representing uncertainty over which type a stance has. This is a more principled replacement for the current two-pass architecture but adds significant complexity.

**Needed:** Decide whether to model stance type uncertainty (Dirichlet over 7 types) or just stance existence uncertainty (Beta for each type independently). The former is more principled but harder to implement; the latter is simpler and may suffice initially.

### Gap 7: Fang (2025) Binary vs. Graded Beliefs

Fang's LLM-ASPIC+ (2025) demonstrates a clean neuro-symbolic pipeline but uses binary beliefs (in the belief set or not). Hunter (2017) provides graded/probabilistic acceptability. The bridge between these -- using LLM extraction with graded confidence feeding into probabilistic argumentation -- has not been implemented anywhere in the literature. Propstore would be building this bridge.

**Needed:** Design the interface between LLM-based extraction (which naturally produces graded confidence) and formal argumentation (which traditionally expects binary or probability-constrained inputs). The opinion tuple is the candidate bridge, but the full pipeline needs prototyping.
