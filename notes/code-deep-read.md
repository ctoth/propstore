# Deep Code Read: Argumentation and World Model Data Flow

Date: 2026-03-25
Scout: claude-opus-4-6 (gauntlet protocol)

---

## Executive Summary

The propstore argumentation pipeline has a well-documented and self-aware architecture. The code comments honestly flag known limitations (flat argument construction, no full ASPIC+, P_A/tau conflation). The core data flow is: claims -> active filtering (Z3 conditions) -> stances become attacks/supports -> preference filtering -> Dung AF -> extension computation. Opinions from Josang 2001 flow through the PrAF layer for probabilistic argumentation but are NOT used in the base argumentation or world resolution decisions. The ATMS is a parallel backend, not connected to the argumentation layer. Several design tensions exist between the theoretical grounding and the implementation.

---

## File-by-File Analysis

### 1. argumentation.py

**What it does:** Central orchestrator that builds argumentation frameworks from claims and stances. Three entry points: `build_argumentation_framework()` for deterministic AF, `build_praf()` for probabilistic AF, and `compute_claim_graph_justified_claims()` for direct extension computation. Also provides `compute_consistent_beliefs()` via MaxSMT.

**Inputs:** `ArtifactStore` (the WorldModel/sidecar), a set of active claim IDs, comparison mode (elitist/democratic).

**Outputs:** `ArgumentationFramework` (frozensets of arguments, defeats, attacks) or extension sets.

**Assumptions:**
- Claims map 1:1 to arguments (line 5-6 docstring explicitly states this).
- Stances have `claim_id`, `target_claim_id`, `stance_type`, and optionally `confidence`.
- Stance types are one of the `_ATTACK_TYPES`, `_SUPPORT_TYPES`, or `_NON_ATTACK_TYPES`.

**Key behaviors:**
- Lines 134-165: Iterates over stances. Attack-type stances become attacks. Unconditional attacks (undercuts, supersedes) become defeats automatically. Preference-type attacks (rebuts, undermines) pass through `defeat_holds()`.
- Lines 168-170: Cayrol 2005 derived defeats computed from support chains via fixpoint iteration.
- Lines 179-233: `build_praf()` wraps the AF with opinion probabilities for each argument and defeat.

**Mismatch/concern:** `build_praf()` loads stances twice -- once inside `build_argumentation_framework()` (line 201) and again at line 205. This is redundant but not incorrect (the second load is needed to index stances by pair for P_D lookup).

### 2. dung.py

**What it does:** Implements Dung 1995 abstract argumentation: grounded, preferred, stable, and complete extensions.

**Inputs:** `ArgumentationFramework` dataclass with `arguments`, `defeats`, and optional `attacks`.

**Outputs:** Extension sets (frozenset of argument IDs).

**Key design decision (lines 106-151):** The grounded extension computation has a non-standard post-hoc reconciliation step. It computes the least fixed point using defeats (standard Dung), then enforces attack-based conflict-freeness by removing attacked arguments and re-computing the fixpoint. The docstring at line 121-123 honestly flags this: "This is not a standard least fixed point of a single well-defined characteristic function."

**FINDING: Non-standard grounded extension.** The post-hoc attack removal loop (lines 132-149) iteratively removes arguments that attack each other within the extension, then re-verifies defense. This could produce results different from standard Dung semantics when the attack and defeat relations diverge significantly. The loop could also potentially oscillate in pathological cases (though it shrinks monotonically, so it terminates).

**Brute-force fallback:** Lines 172-174 enumerate all subsets for complete extensions. Z3 backend is available and preferred. The brute force is O(2^n) -- only used when Z3 is not available or for PrAF sub-evaluations (praf.py line 202 calls `preferred_extensions(af, backend="brute")`).

### 3. preference.py

**What it does:** Implements ASPIC+ preference ordering (Modgil & Prakken 2018, Def 19) for determining which attacks succeed as defeats.

**Inputs:** Multi-dimensional strength vectors (list[float]) and comparison mode.

**Outputs:** Boolean: does the attack survive as a defeat?

**Key logic:**
- `claim_strength()` (lines 56-89) builds a multi-dimensional strength vector from claim metadata: log(sample_size), 1/uncertainty, confidence. Missing dimensions are omitted; if nothing is available, returns `[1.0]`.
- `defeat_holds()` (lines 37-53): undercuts/supersedes always succeed. Rebuts/undermines succeed iff attacker is NOT strictly weaker.
- `strictly_weaker()` (lines 16-34): Elitist = exists x in A such that forall y in B, x < y. Democratic = forall x in A exists y in B, x < y.

**FINDING: Dimension mismatch risk.** If claim A has `[log(sample_size)]` (1 dim) and claim B has `[1/uncertainty, confidence]` (2 dims), the elitist/democratic comparison operates over vectors of different lengths. This is mathematically valid per the definitions but may produce surprising results. E.g., with elitist: A is weaker if ANY element of A is less than ALL elements of B. With mismatched dimensions, this becomes: is the single sample_size dimension weaker than both the uncertainty and confidence dimensions of B? These are incommensurable quantities being compared numerically.

### 4. structured_argument.py

**What it does:** Provides a "structured projection" backend -- each claim becomes one `StructuredArgument`, then the same Dung machinery runs over argument IDs (prefixed `arg:`).

**Inputs:** `ArtifactStore`, list of active claim dicts, optional support metadata.

**Outputs:** `StructuredProjection` containing arguments, the AF, and bidirectional claim<->argument mappings.

**Key difference from argumentation.py:**
- Lines 148-152: **Prunes vacuous opinions** (uncertainty > 0.99). This contradicts the design checklist in CLAUDE.md ("Does this prevent ANY data from reaching the sidecar? If yes -> WRONG") and contradicts the comment at line 146-147 which cites Li et al. and the design checklist. The `argumentation.py` version does NOT prune vacuous opinions.

**FINDING: Inconsistent vacuous opinion handling.** `structured_argument.py` line 149 prunes stances with `opinion_uncertainty > 0.99` (vacuous per Josang 2001), while `argumentation.py` does not prune them. The structured_argument.py code even has a comment (lines 145-147) saying stances SHOULD participate, then immediately prunes them on line 149. This is a direct self-contradiction.

### 5. opinion.py

**What it does:** Implements Josang 2001 subjective logic. Pure data module with zero propstore imports.

**Core type:** `Opinion(b, d, u, a)` where b+d+u=1, a in (0,1).

**Operations:** negation (`~`), conjunction (`&`), disjunction (`|`), `consensus_pair()`, `discount()`, `expectation()` (E = b + a*u), `uncertainty_interval()` ([b, 1-d]).

**Also provides:** `BetaEvidence(r, s, a)` with bidirectional conversion to Opinion. `from_probability(p, n)` and `from_evidence(r, s)` convenience constructors.

**Assumptions:** Well-validated -- `__post_init__` checks all constraints.

**No issues found.** This is a clean, self-contained algebra module.

### 6. calibrate.py

**What it does:** Bridges raw model outputs to Opinion algebra. Four components:
1. `TemperatureScaler` -- post-hoc calibration via Guo et al. 2017
2. `CorpusCalibrator` -- converts embedding distances to opinions via corpus CDF
3. `categorical_to_opinion()` -- converts LLM categorical output (strong/moderate/weak/none) to opinions
4. `expected_calibration_error()` -- ECE metric

**Key design (lines 258-271):** `categorical_to_opinion()` without calibration data returns a VACUOUS opinion -- honest ignorance. With calibration counts, it maps (correct, total) to evidence counts via `from_evidence()`.

**This is the ONLY entry point where opinions get created for stance data** -- called from `relate.py` line 196.

**FINDING: Without calibration data, ALL stance opinions are vacuous.** The system currently has no calibration data infrastructure visible in these files. `categorical_to_opinion()` is always called with `calibration_counts=None` (relate.py line 196 does not pass calibration_counts). This means every stance gets a vacuous opinion (b=0, d=0, u=1). The `expectation()` of a vacuous opinion equals the base rate `a` (0.3-0.7 depending on category). So "confidence" in relate.py line 198 is just the base rate, not empirical evidence.

### 7. praf.py

**What it does:** Implements Probabilistic Argumentation Frameworks per Li et al. 2012. PrAF = (A, P_A, D, P_D) where P_A and P_D are existence probabilities as Opinions.

**Key types:**
- `ProbabilisticAF(framework, p_args, p_defeats)` -- AF plus opinion annotations
- `PrAFResult(acceptance_probs, strategy_used, samples, ci_half, semantics)`

**Strategy dispatch (lines 108-166):**
- "auto": deterministic if all expectations >= 0.999, exact enumeration if <= 13 args, tree-decomposition DP if treewidth <= 12, else MC sampling
- MC uses Agresti-Coull stopping criterion (Li 2012 Eq. 5)
- Connected component decomposition per Hunter & Thimm 2017

**p_arg_from_claim() (lines 71-78):** Always returns `Opinion.dogmatic_true()` -- all active claims exist with certainty. This is reasonable given claims are already condition-filtered.

**p_defeat_from_stance() (lines 81-105):** Fallback chain: opinion columns -> confidence -> dogmatic_true. This correctly picks up the opinion data stored in stance rows.

**FINDING: Since categorical_to_opinion() returns vacuous opinions (see calibrate.py finding), the stance opinions stored in the DB have b=0, d=0, u=1. The expectation of a vacuous opinion is the base rate a (0.3-0.7). So P_D for MC sampling is the base rate of the category label, not an empirically grounded probability. The system honestly represents ignorance but then uses the base rate as a sampling probability, which may not be what users expect.**

### 8. praf_dfquad.py

**What it does:** Implements DF-QuAD gradual semantics per Freedman et al. 2025. Computes continuous argument strengths in [0,1] by propagating base scores through attack/support relations.

**Key functions:**
- `dfquad_aggregate(base, influence)` -- push toward 1 (positive) or 0 (negative)
- `dfquad_combine(supporters, attackers)` -- noisy-OR aggregation
- `compute_dfquad_strengths(praf, supports)` -- topological evaluation with cycle fallback

**FINDING (already documented in code, line 543-546 of praf.py):** P_A (argument existence probability for MC sampling) is used as tau (intrinsic strength for DF-QuAD). These are conceptually distinct: a rarely-existing argument is not the same as a weak argument. Since P_A is always dogmatic_true (expectation 1.0), all base scores are 1.0, meaning DF-QuAD strength is determined entirely by the attack/support graph structure, not by any intrinsic argument quality.

### 9. propagation.py

**What it does:** Evaluates SymPy parameterization expressions for derived quantities. Handles bare expressions and `Eq(y, expr)` forms.

**Inputs:** SymPy expression string, input values dict, output concept ID.
**Outputs:** float or None.

**No connection to argumentation.** This is purely for the parameterization/derivation layer (concepts like "density = mass / volume").

### 10. sensitivity.py

**What it does:** Computes partial derivatives, numerical sensitivities, and elasticities for parameterized concepts. Answers "which input most influences this output?"

**Inputs:** WorldModel, concept_id, BoundWorld, optional override values.
**Outputs:** `SensitivityResult` with sorted entries by |elasticity|.

**No connection to argumentation.** This is a utility for the parameterization layer.

### 11. world/model.py (WorldModel)

**What it does:** Read-only reasoner over a compiled SQLite sidecar. Implements the `ArtifactStore` protocol. Central hub that provides:
- Concept/claim/stance queries
- Z3 condition solver (lazy init)
- Context hierarchy loading
- Binding to produce `BoundWorld`
- Chain queries for derived values

**Key method `bind()` (lines 502-551):** Creates a `BoundWorld` with environment bindings and context hierarchy. Compiles environment assumptions via `compile_environment_assumptions()`.

**Key method `chain_query()` (lines 555-644):** Iterative resolution loop that tries value_of, then resolved_value (if conflicted and strategy given), then derived_value for each concept in the parameterization group.

**No direct argumentation calls.** The WorldModel delegates to resolution.py when resolving conflicted values, which in turn calls argumentation.

### 12. world/resolution.py

**What it does:** The resolution dispatch layer. When a concept has conflicting claims, this module picks a winner based on the configured strategy.

**Strategies:**
- OVERRIDE: user-specified winner
- RECENCY: most recent provenance date
- SAMPLE_SIZE: largest sample_size
- ARGUMENTATION: delegates to one of four backends

**Argumentation backends (lines 373-410):**
- CLAIM_GRAPH: calls `compute_claim_graph_justified_claims()` -- builds AF over ALL active claims, projects back to target
- STRUCTURED_PROJECTION: calls `build_structured_projection()` + `compute_structured_justified_arguments()`
- PRAF: calls `build_praf()` + `compute_praf_acceptance()` -- winner by highest acceptance probability
- ATMS: calls `_resolve_atms_support()` -- winner by ATMS-supported status

**FINDING: The argumentation builds the AF over ALL active claims in the entire belief space (line 98: `active_ids = {c["id"] for c in active_claims}`), not just the conflicting concept's claims. The full AF is computed, then the result is projected back to the target concept's claims (line 107: `survivors = result & target_ids`). This is correct per argumentation theory -- defeat relations between claims about different concepts can affect which claims survive.**

**FINDING: Opinion uncertainty is NOT used in the resolution decision.** The `_resolve_praf()` function at lines 248-249 picks the winner by highest acceptance probability (`max(target_probs.values())`). The acceptance probability is a float (0.0 to 1.0) with no uncertainty attached. The opinion's uncertainty has already been collapsed to a point estimate during PrAF MC sampling (via `Opinion.expectation()`). The `decision_criterion` and `pessimism_index` fields from RenderPolicy (lines 328-332) are extracted but stored as unused locals (`_decision_criterion`, `_pessimism_index`). They are available in types.py `apply_decision_criterion()` but that function is not called from resolution.py.

### 13. world/atms.py (ATMSEngine)

**What it does:** ATMS-style exact-support propagation engine. Assigns each claim a Label (set of minimal assumption environments under which it holds). Propagates labels through parameterization justifications. Computes nogoods from conflicts. Provides bounded future replay, stability, relevance, intervention planning, and next-query suggestions.

**Build process (_build, line 784):**
1. Create assumption nodes from the BoundWorld's compiled assumptions
2. Create claim nodes and justifications (claim conditions map to assumption antecedents)
3. Iteratively: propagate labels, materialize parameterization justifications, update nogoods -- until fixpoint

**FINDING: The ATMS does NOT connect to the argumentation layer.** The ATMS operates on conditions/assumptions (CEL expressions and context membership), NOT on stance-based attack/defeat relations. The argumentation layer (argumentation.py) operates on stances between claims. These are parallel, independent systems:
- ATMS: "under which assumptions does this claim hold?" (label propagation)
- Argumentation: "given active claims, which survive defeat?" (extension computation)

The ATMS is a resolution backend (ReasoningBackend.ATMS in resolution.py line 405-406), where "supported" means "has a non-empty ATMS label under current assumptions." This is fundamentally different from argumentation-based resolution where "justified" means "survives in an extension."

**The ATMS does connect to the value layer:** When the reasoning backend is ATMS, `BoundWorld.value_of()` (bound.py line 258-263) filters active claims to only ATMS-supported ones before determining value status. This means the ATMS affects what claims are visible, not how conflicts between visible claims are resolved.

### 14. world/labelled.py

**What it does:** Core ATMS data structures: `AssumptionRef`, `EnvironmentKey`, `NogoodSet`, `Label`, `JustificationRecord`, `SupportQuality`. Also provides label algebra: `combine_labels()` (cross-product), `merge_labels()` (union), `normalize_environments()` (dedup + subsumption pruning + nogood filtering).

**No connection to argumentation or opinions.** This is purely the ATMS label algebra.

### 15. world/bound.py (BoundWorld)

**What it does:** The condition-bound view over a WorldModel. Filters claims by Z3 condition compatibility and context hierarchy. Provides `value_of()`, `derived_value()`, `resolved_value()`. Attaches ATMS labels to results when the reasoning backend is ATMS.

**Key flow:**
- `is_active()` (lines 169-190): claim passes if context is visible AND conditions are not disjoint with bindings (Z3)
- `value_of()` (lines 256-267): gets active claims, optionally filters by ATMS support, delegates to `ActiveClaimResolver.value_of_from_active()`
- `resolved_value()` (lines 284-302): delegates to `resolution.resolve()`

**The BoundWorld is the bridge between the world model and the argumentation layer.** It computes the active belief space (which claims are "alive" under current conditions), and resolution.py builds the AF over that active set.

### 16. world/hypothetical.py (HypotheticalWorld)

**What it does:** In-memory overlay on a BoundWorld that can add/remove claims without mutation. Supports what-if analysis via `diff()`.

**No direct connection to argumentation.** Uses resolution.py indirectly through `resolved_value()`.

### 17. world/types.py

**What it does:** Data classes, enums, and protocols. Defines `ValueStatus`, `ValueResult`, `DerivedResult`, `ResolvedResult`, `RenderPolicy`, `ResolutionStrategy`, `ReasoningBackend`, `ArtifactStore` protocol, `BeliefSpace` protocol.

**Key: `apply_decision_criterion()` (lines 216-264).** This function implements pignistic, lower_bound, upper_bound, and hurwicz criteria from Denoeux 2019. It takes raw opinion components and returns a decision value.

**FINDING: `apply_decision_criterion()` exists but is not called from any of the 20 files reviewed.** It is defined in types.py but resolution.py extracts the policy fields as unused locals (line 331: `_decision_criterion = policy.decision_criterion`). The function would need to be called somewhere in the render layer to actually use opinion uncertainty in decisions. The opinion algebra (Josang 2001) is correctly implemented but does not influence final resolution outcomes in the current code.

### 18. world/value_resolver.py (ActiveClaimResolver)

**What it does:** Shared value resolution logic for BoundWorld and HypotheticalWorld. Determines if a concept is determined (one unique value), conflicted (multiple values), or needs derivation.

**Key method `value_of_from_active()` (lines 102-157):** Handles algorithm claims, direct value claims, and mixed cases. Uses AST comparison for algorithm equivalence.

**No connection to argumentation or opinions.** This determines the "raw" value status before any resolution strategy is applied.

### 19. stances.py

**What it does:** Defines `VALID_STANCE_TYPES` -- the vocabulary of epistemic relationships: rebuts, undercuts, undermines, supports, explains, supersedes, none.

**Trivial module.** Just a frozenset.

### 20. relate.py

**What it does:** NLI stance classification via LLM. Two-pass system: first pass classifies all embedding-similar claim pairs, second pass re-examines "none" verdicts for high-similarity pairs.

**Key opinion creation (lines 193-213):** When the LLM classifies a stance, the strength category (strong/moderate/weak) is passed to `categorical_to_opinion(strength, pass_number)`. Without calibration data, this returns a vacuous opinion. The opinion's `expectation()` becomes the backward-compatible `confidence` field. The full opinion components (b, d, u, a) are stored in the resolution dict and eventually reach the stance database.

**FINDING: Raw embedding distances are interpolated into LLM prompts (lines 53, 127: `{distance:.4f}`) without normalization or calibration.** The `CorpusCalibrator` in calibrate.py exists to address this, but relate.py does not use it. The distance value in the second-pass prompt is a raw model-specific number. The code comment at calibrate.py line 111 explicitly notes this problem.

---

## Cross-Cutting Analysis

### A. How Claims Become Arguments

Path: `WorldModel.claims_for()` -> `BoundWorld.is_active()` (Z3 filter) -> `BoundWorld.active_claims()` -> `resolution.py` passes active claims to argumentation -> `argumentation.build_argumentation_framework()` creates `ArgumentationFramework(arguments=frozenset(active_claim_ids), ...)`.

**Each active claim IS an argument.** There is no rule-based construction, no sub-arguments, no premises. The code is explicit about this (argumentation.py docstring lines 1-6, CLAUDE.md Known Limitations section). Claim IDs are used directly as argument IDs in the claim_graph backend; the structured_projection backend prefixes them with `arg:`.

### B. How Arguments Get Defeat Relations

Path: `store.stances_between(active_claim_ids)` returns stance rows -> each stance with attack-type goes through preference filtering -> `defeat_holds()` checks if attacker is not strictly weaker -> surviving attacks become defeats.

**Stances are the SOLE source of defeat relations.** If two claims conflict (same concept, different values) but no stance exists between them, there is NO defeat relation in the AF. The conflict detector (used in `compute_consistent_beliefs`) is separate from the AF builder.

**FINDING: The AF and the conflict detector operate on different conflict models.** The AF uses stances (explicitly classified epistemic relationships from LLM). The conflict detector uses value disagreement + condition analysis. A pair of claims can be in conflict (per conflict detector) but have no stance between them, in which case the AF sees no defeat and both survive. Conversely, claims can have a "rebuts" stance but not trigger the conflict detector (e.g., if they have different conditions).

### C. How Opinions/Uncertainty Flow Through Argumentation

1. LLM classifies stance -> `categorical_to_opinion()` -> vacuous opinion (no calibration data) -> stored in stance row
2. `build_praf()` reads opinion columns from stances -> creates `ProbabilisticAF`
3. `compute_praf_acceptance()` uses `Opinion.expectation()` as sampling probability for MC
4. Winner picked by highest acceptance probability (a float)

**Uncertainty is collapsed at step 3.** The `expectation()` function maps Opinion(b,d,u,a) to a single float (b + a*u). For vacuous opinions, this equals the base rate `a`. After this point, all uncertainty information is lost.

**`apply_decision_criterion()` in types.py could preserve uncertainty** (via lower_bound/upper_bound/hurwicz) but is not called from the resolution path.

### D. How the World Model Resolves Competing Claims

1. `BoundWorld.value_of()` determines status: determined, conflicted, no_claims, etc.
2. If conflicted and a strategy is configured, `BoundWorld.resolved_value()` -> `resolution.resolve()`
3. `resolve()` dispatches to the configured strategy (recency, sample_size, argumentation, override)
4. For argumentation: builds AF over ALL active claims, computes extension, projects to target concept's claims
5. If one claim survives, it wins. If multiple survive or none survive, result is still conflicted.

### E. Whether ATMS Connects to Argumentation

**No.** They are parallel systems operating on different foundations:

| Aspect | ATMS | Argumentation |
|--------|------|---------------|
| Input | Conditions (CEL), context hierarchy | Stances (LLM-classified) |
| Mechanism | Label propagation + nogoods | Extension computation |
| Question answered | "Under which assumptions does this claim hold?" | "Which claims survive mutual defeat?" |
| Connection point | `ReasoningBackend.ATMS` in resolution.py | `ReasoningBackend.CLAIM_GRAPH/STRUCTURED_PROJECTION/PRAF` |

The ATMS does not consider stance-based attacks. The argumentation does not consider assumption-based support labels. They are alternative resolution backends, not complementary layers.

### F. Whether Opinion Algebra Is Used in Decisions

**Partially.** Opinions are created (calibrate.py), stored (relate.py), loaded (praf.py), and their expectations are used as sampling probabilities (praf.py MC sampler). But:

1. The base argumentation path (CLAIM_GRAPH backend) does NOT use opinions at all. Defeats are determined by claim metadata (sample_size, uncertainty, confidence fields) through `claim_strength()`, not by opinion algebra.
2. The PRAF backend uses `Opinion.expectation()` to collapse opinions to floats for sampling. No other opinion operation (consensus, discounting, conjunction, disjunction) is used in the resolution path.
3. `apply_decision_criterion()` exists but is dead code in the resolution path.
4. Without calibration data, all opinions are vacuous, so the entire opinion machinery reduces to using base rates as probabilities.

### G. Whether Preference Ordering Connects to ASPIC+

**The preference ordering connects to a simplified version of ASPIC+ ideas, not full ASPIC+.** `claim_strength()` computes multi-dimensional strength from claim metadata. `defeat_holds()` applies Modgil & Prakken 2018 Def 9 (undercuts always succeed, rebuts/undermines succeed if not strictly weaker). `strictly_weaker()` applies Def 19 (elitist/democratic set comparison).

This correctly implements the preference filtering step. But the arguments being compared are not structured ASPIC+ arguments (no rules, no sub-arguments, no last-link/weakest-link). The code is honest about this (argumentation.py docstring, CLAUDE.md Known Limitations).

---

## Summary of Findings

### Design Tensions

1. **Vacuous opinion problem (calibrate.py + relate.py + praf.py):** Without calibration counts, all opinions are vacuous. The opinion machinery is theoretically sound but empirically inert. This makes PrAF equivalent to sampling with base-rate probabilities.

2. **ATMS/argumentation disconnect (atms.py vs argumentation.py):** Two independent reasoning systems that cannot be composed. You get ATMS label-based support OR argumentation-based defeat survival, never both.

3. **Dead decision criteria (types.py line 216):** `apply_decision_criterion()` implements Denoeux 2019 criteria but is not called from resolution.py. The RenderPolicy fields `decision_criterion`, `pessimism_index`, and `show_uncertainty_interval` are extracted but unused.

4. **Inconsistent vacuous pruning (structured_argument.py line 149):** The structured_argument backend prunes vacuous stances, contradicting both CLAUDE.md design principles and the argumentation.py backend which does not prune them.

### Correctly Implemented Pieces

1. **Opinion algebra (opinion.py):** Clean, well-validated Josang 2001 implementation.
2. **Dung semantics (dung.py):** Correct grounded/preferred/stable/complete (with the noted non-standard reconciliation step).
3. **Cayrol derived defeats (argumentation.py):** Correct fixpoint computation of support-mediated defeats.
4. **PrAF MC sampling (praf.py):** Correct Li 2012 implementation with component decomposition and Agresti-Coull stopping.
5. **ATMS label propagation (atms.py):** Full de Kleer 1986-style label algebra with nogoods, bounded future replay, stability, and intervention planning.
6. **Preference ordering (preference.py):** Correct Modgil & Prakken 2018 Def 9 and Def 19.

### Items Flagged But Not Bugs

These are self-documented limitations, not surprises:
- Flat argument structure (no ASPIC+ rules/sub-arguments) -- documented in CLAUDE.md
- P_A conflated with tau in DF-QuAD -- documented in praf.py line 543-546
- No AGM operations -- documented in CLAUDE.md literature table
- No COH constraint enforcement -- documented in CLAUDE.md literature table
