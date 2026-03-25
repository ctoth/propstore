# Why Propstore Won't Work — Deep Analysis

Date: 2026-03-25

## GOAL
Identify fundamental (not superficial) reasons the program cannot produce correct results.

## FINDINGS

### 1. THE OPINION PIPELINE IS INERT (the biggest problem)

The entire Jøsang 2001 opinion algebra is correctly implemented but empirically dead:

- `relate.py:196` calls `categorical_to_opinion(strength, pass_number)` with NO calibration data
- `calibrate.py:258-259` returns `Opinion.vacuous(a=base_rate)` when calibration_counts is None
- Vacuous opinion = (b=0, d=0, u=1, a=base_rate)
- `opinion.expectation()` = b + a*u = 0 + base_rate*1 = base_rate
- So every stance "confidence" is just a hardcoded base rate (0.3-0.7 per category)
- PrAF MC sampling uses these base rates as defeat existence probabilities
- The system samples defeats at 30-70% probability based on category labels, not evidence

This means: the probabilistic argumentation layer is rolling dice with hardcoded weights, not reasoning under uncertainty. The opinion algebra exists but never receives real evidence.

### 2. STANCES ARE THE SOLE SOURCE OF DEFEATS — BUT MOST CLAIM PAIRS HAVE NO STANCE

- `argumentation.py` builds the AF from `claim_stance` table entries
- `conflict_detector/` finds value conflicts and stores them in `conflicts` table
- **These two systems do not connect.** No code converts conflict records into attacks.
- If two claims for the same concept disagree on value but no LLM-generated stance exists between them, the AF sees NO defeat. Both claims survive.
- The conflict detector runs at build time; argumentation runs at render time. Different data, different purpose.
- `compute_consistent_beliefs()` (argumentation.py:320) does use both — it calls conflict_detector AND maxsat_resolver — but this function is separate from the main AF path used by resolution.py.

This means: the argumentation layer is blind to most conflicts. It only sees conflicts that an LLM happened to classify. Unclassified conflicts pass through silently.

### 3. DECISION CRITERIA ARE DEAD CODE

- `apply_decision_criterion()` at `types.py:216` implements pignistic, lower_bound, upper_bound, hurwicz (Denoeux 2019)
- `resolution.py:330-332` extracts the policy fields as `_decision_criterion`, `_pessimism_index`, `_show_uncertainty_interval` — prefixed with underscore, never used
- The PRAF backend picks winners by `max(acceptance_probs)` — a bare float
- Uncertainty is collapsed to a point estimate and never recovered
- The entire uncertainty-aware decision framework exists in types.py but is disconnected from the resolution pipeline

This means: the render layer cannot distinguish "confident answer" from "ignorant guess." A claim with 95% evidence-backed belief beats nothing that a claim with a lucky base rate and vacuous opinion wouldn't also beat.

### 4. ATMS AND ARGUMENTATION ARE PARALLEL, NOT COMPOSED

- ATMS operates on conditions/assumptions (CEL expressions, context hierarchy)
- Argumentation operates on stances (LLM-classified epistemic relations)
- They are alternative backends in `resolution.py` (ReasoningBackend.ATMS vs CLAIM_GRAPH/PRAF)
- You get label-based support tracking OR defeat-based extension computation, never both
- Dixon 1993 proves ATMS context switching = AGM belief revision, but no AGM operations are implemented

This means: the system cannot answer "under which assumptions does claim X survive argumentation?" It can only answer "does X have ATMS support?" OR "does X survive defeats?" independently.

### 5. FLAT ARGUMENT STRUCTURE BREAKS ASPIC+ GUARANTEES

- Each claim maps 1:1 to an argument (argumentation.py:1-6 docstring)
- ASPIC+ per Modgil & Prakken 2018 requires: strict/defeasible rules, recursive sub-arguments, last-link/weakest-link comparison
- Without sub-arguments, there are no sub-argument closure guarantees (Prakken 2010 Prop 6.1)
- Without strict rule transposition closure (Modgil 2018 Def 12), extensions may be inconsistent (Theorem 6.10)
- The preference ordering (preference.py) correctly implements Def 9/19, but compares flat claims, not structured arguments

This means: the system claims ASPIC+ preference ordering but cannot satisfy ASPIC+ rationality postulates. The guarantees that make ASPIC+ trustworthy do not hold.

### 6. PREFERENCE DIMENSIONS ARE INCOMMENSURABLE

- `claim_strength()` in preference.py builds a vector from [log(sample_size), 1/uncertainty, confidence]
- Different claims may have different subsets of these dimensions
- Elitist/democratic comparison operates over vectors of different lengths
- log(sample_size) and 1/uncertainty are numerically incommensurable quantities
- A claim with sample_size=1000 (log=6.9) vs a claim with confidence=0.95 — these numbers aren't comparable

This means: the preference ordering may produce arbitrary results when claims have different metadata profiles.

### 7. P_A CONFLATED WITH TAU IN DF-QuAD

- `praf.py:71-78`: p_arg_from_claim() always returns dogmatic_true (expectation 1.0) for all active claims
- DF-QuAD (praf_dfquad.py) uses P_A as base score (tau)
- All base scores = 1.0, so argument intrinsic strength is uniform
- DF-QuAD strength is determined entirely by graph structure, not argument quality

### 8. COH CONSTRAINT NOT ENFORCED

- Hunter & Thimm 2017 require COH: P(A) + P(B) <= 1 when A attacks B
- CLAUDE.md acknowledges this is not enforced
- Without COH, probability assignments can be incoherent with the attack graph
- PrAF sampling may produce worlds that violate basic probabilistic argumentation constraints

### 9. STRUCTURED_ARGUMENT.PY CONTRADICTS DESIGN PRINCIPLES

- Line 149 prunes stances with opinion_uncertainty > 0.99 (vacuous)
- Since ALL opinions are vacuous (finding #1), this prunes ALL stances
- The structured_projection backend would have an empty AF
- This contradicts CLAUDE.md design checklist item 1: "Does this prevent ANY data from reaching the sidecar? If yes → WRONG"
- The code even has a comment (lines 145-147) citing the design checklist, then immediately violates it

## SYNTHESIS: Why the program won't work

The fundamental problem is a **pipeline that never closes its loops:**

1. Opinions are created vacuous → they need calibration data that doesn't exist
2. Conflicts are detected → but never converted to defeats
3. Decision criteria are implemented → but never called
4. ATMS and argumentation exist → but never compose
5. ASPIC+ preferences are applied → but over flat structures that can't satisfy ASPIC+ guarantees

The system has correct individual components (opinion algebra, Dung semantics, ATMS labels, calibration math) but the wiring between them is incomplete. Data enters the pipeline and hits dead ends everywhere. The render layer, which is supposed to be where everything comes together, can only collapse uncertainty to point estimates and pick the max.

## FILES READ
- All 20 core source files (argumentation, dung, preference, opinion, calibrate, praf, world/*, etc.)
- 20 paper notes (Dung, Modgil, Prakken, Josang, Hunter, Li, Guo, Sensoy, Denoeux, etc.)
- Infrastructure files (build_sidecar, conflict_detector/*, validate, etc.)
- resolution.py lines 320-350 (dead decision criteria)
- types.py lines 210-265 (apply_decision_criterion)
- calibrate.py lines 250-271 (vacuous opinion path)
- relate.py lines 185-220 (opinion creation)
