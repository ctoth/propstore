# Review v0 Analysis Session — 2026-03-21

## Goal
Deeply understand the code review in review-v0.md by cross-referencing it against actual code and the papers collection.

## What I've Read So Far

### Code Files
- `propstore/world/model.py` — WorldModel class: read-only reasoner over compiled SQLite sidecar. Lazy Z3 setup, concept/claim queries, FTS search, embedding similarity, parameterization traversal, stance graph BFS, condition binding, chain queries.
- `propstore/world/types.py` — Core types: ValueResult (determined/conflicted/underdetermined/no_claims), DerivedResult, ResolutionStrategy enum (RECENCY/SAMPLE_SIZE/STANCE/OVERRIDE), ResolvedResult, SyntheticClaim, ChainStep/ChainResult, ClaimView protocol.
- `propstore/world/resolution.py` — Resolution strategies: recency (provenance date), sample_size, stance (weighted scoring with supersession), override (manual).
- `propstore/world/bound.py` — BoundWorld: condition-binding via CEL->Z3 disjointness. Algorithm claim equivalence via ast_compare. Derived values via parameterization evaluation.
- `propstore/world/hypothetical.py` — HypotheticalWorld: in-memory overlay with remove/add synthetic claims, diff(), recompute_conflicts().
- `propstore/validate_claims.py` — Claim types: parameter, equation, observation, model, measurement, algorithm. Each has type-specific validation. CEL condition checking.
- `propstore/build_sidecar.py` — SQLite sidecar builder with content hashing, embedding snapshot/restore, stance population from files.

### Papers Collection (27 papers)
Heavy concentration in:
- Truth maintenance systems (Doyle 1979, McAllester 1978, de Kleer 1984/1986 x2, McDermott 1983, Falkenhainer 1987)
- Belief revision (Alchourron 1985 AGM, Dixon 1993 ATMS↔AGM, Martins 1983/1988, Shapiro 1998)
- Argumentation frameworks (Dung 1995, Cayrol 2005 bipolar, Modgil 2014/2018 ASPIC+, Pollock 1987, Odekerken 2023)
- Scientific claims/provenance (Clark 2014 micropublications, Groth 2010 nanopublications, Greenberg 2009 citation distortions)
- Argument mining (Mayer 2020, Walton 2015 schemes)
- Nonmonotonic reasoning (Reiter 1980 default logic, Ginsberg 1985 counterfactuals)

### Tagged Categories
48 tags covering: abstract-argumentation, agm, atms, belief-revision, counterfactuals, defeasible-reasoning, dependency-tracking, epistemic-logic, nonmonotonic-reasoning, provenance, truth-maintenance, etc.

## Review v0 Claims vs. Actual Code — Initial Assessment

### Review says "right substrate" — CONFIRMED
- Local files as source of truth: YES. YAML concepts/claims/stances → compiled SQLite sidecar.
- Typed conditionality: YES. CEL expressions + Z3 disjointness solver.
- Compiled world model: YES. validate → build → WorldModel roundtrip.
- Epistemic relations operationalized: YES. Embeddings, similarity, stance classification, stance-chain explanation.

### Review's "biggest weakness" — claims too much like end-state assertions
Looking at claim types in validate_claims.py:
- parameter, equation, observation, model, measurement, algorithm
This IS more differentiated than the review implies. The system already distinguishes observation from parameter from measurement from algorithm. But the review's deeper point stands: these are all "claim" objects. There's no separate **proposition** layer that normalizes semantic content independent of the assertion event.

### Review's weakness #2 — contexts not first-class worlds
Current: CEL conditions on claims + Z3 disjointness = "context as filter"
The review correctly identifies this as one step short of microtheory semantics.
Papers relevant: de Kleer 1986 ATMS (environments/contexts), McDermott 1983 (contexts + data dependencies), Martins 1983 (multiple belief spaces), Ginsberg 1985 (counterfactuals via context).

### Review's weakness #3 — claim identity too brittle
Current: `claimN` IDs, content hashing for dedup.
The review wants: source-local ID, repository ID, semantic equivalence class, canonical proposition ID.
Papers relevant: Clark 2014 micropublications (layered identity), Groth 2010 nanopublications (citable assertion bundles).

### Review's weakness #4 — LLM layer bolted on
Current: embeddings, similarity, stance classification via litellm.
The review correctly notes these are adjunct workflows, not structurally integrated.

## Key Observation
The papers collection is REMARKABLY well-chosen to address the review's recommendations:
- "Split claim into layers" → Clark 2014 micropublications already defines this layered model
- "Rich provenance" → Greenberg 2009 shows WHY provenance matters (citation distortions)
- "Contexts as theory objects" → de Kleer ATMS, McDermott contexts, Martins belief spaces
- "Canonical proposition normalization" → Groth 2010 nanopublications
- "Algorithms as derivation graphs" → de Kleer 1984 qualitative physics confluences
- "Explanation layer" → Pollock 1987 defeasible reasoning (warrant as explanation)
- "Standing queries/hypothesis testing" → Ginsberg 1985 counterfactuals, Odekerken 2023 stability/relevance

This is not coincidental. The papers were collected to inform exactly the design decisions the review is calling for.

## Additional Readings Completed

### Schema (claim.linkml.yaml)
- 6 claim types: parameter, equation, observation, model, measurement, algorithm
- StanceType enum: rebuts, undercuts, undermines, supports, explains, supersedes, none
  - This is ASPIC+ taxonomy! (from Modgil & Prakken 2014/2018 in the collection)
- Resolution provenance: method (nli_first_pass, nli_second_pass, human, extraction), model, embedding info, confidence
- Provenance: paper, page, table, figure, section, quote_fragment
- FitStatistics on equations: r, r_sd, slope, slope_sd
- UncertaintyType: sd, se, ci95, range

### relate.py (NLI stance classification)
- Two-pass architecture: first classify all embedding-similar pairs, then re-examine "none" verdicts with high similarity
- Uses ASPIC+ taxonomy in LLM prompts
- Confidence scoring: pass_number × strength → numeric confidence
- Writes stance YAML files to knowledge/stances/

### cel_checker.py
- Full CEL expression parser (tokenizer → recursive descent → AST)
- Type system: QUANTITY (numeric), CATEGORY (string), BOOLEAN, STRUCTURAL
- Type-checks comparisons, arithmetic, in-lists against concept registry
- Category value set validation (extensible vs closed)

### Clark 2014 micropublications notes
- The MP model is MP_a = (A_mpa, c, A_c, Φ, R) where:
  - c = principal Claim
  - Φ = set of Representations (evidence, data, methods)
  - R = support ∪ challenge relations as strict partial order
- Complexity spectrum from minimal (statement + attribution) to full claim-evidence networks
- hasHolotype relation: representative exemplar of a similarity group

### de Kleer 1986 ATMS notes
- Label = minimal sets of assumptions under which datum holds
- Four invariants: consistency, soundness, completeness, minimality
- Environments, contexts, nogoods as first-class objects

### Dixon 1993 ATMS↔AGM
- Proves ATMS context switching = AGM expansion + contraction
- Entrenchment ordering derived from justificational information
- Essential Support: ES(p,E) = intersection of all foundational belief sets

### Architecture Review (earlier session)
- Knowledge base is nearly empty: 23 skeleton concepts, zero claims imported
- Papers/claims exist but haven't been imported yet
- 530+ tests passing

## Deep Analysis: Review Claims vs. Reality vs. Literature

### 1. "Split 'claim' into three layers" (Proposition / Assertion / Derivation)

**Review's recommendation:** The system overloads "claim" — it should separate normalized semantic content (proposition), assertion events (evidence records), and computations (derivations).

**What code actually has:** SIX claim types (parameter, equation, observation, model, measurement, algorithm), each with different validation and different schema fields. This is MORE differentiated than the review implies. The system already distinguishes an observation from a parameter from an algorithm.

**But the review's deeper point holds.** The claim types differentiate by *kind of knowledge* (scalar, equation, procedure, qualitative), not by *epistemic status*. There's no separation between:
- "The RT60 of a room is 0.5s" (assertion with provenance)
- "RT60 is defined as the time for sound to decay 60dB" (definitional)
- "RT60 is computed from volume and absorption" (derivation)

All three would be different claim types, but there's no layer that says "these three claims are all about the same underlying proposition." That's what Clark 2014's micropublication model provides: the principal Claim (c) is distinct from the Representations (Φ) that support or challenge it.

**The papers collection provides the answer.** Clark 2014 gives the layered model. Groth 2010 gives the minimal citable assertion bundle. The system could add a `proposition` table to the sidecar that normalizes semantic content, with claims becoming evidence records *for* propositions.

### 2. "Make provenance rich enough to drive resolution"

**What code has:** Provenance = {paper, page, table, figure, section, quote_fragment}. Resolution strategies = {recency, sample_size, stance, override}. The stance resolver does weighted scoring with supersession trumping.

**What the review wants:** source, date, study type, population, sample_size, measurement method, extraction confidence, source quality/trust tier, directness vs hearsay, observed vs inferred vs meta-analysis.

**Assessment:** The schema already has some of this (sample_size, methodology for measurements, uncertainty/uncertainty_type, listener_population). But it's scattered across claim-type-specific fields rather than being a first-class provenance/evidence-quality layer.

**The key insight:** Greenberg 2009 (citation distortions) shows exactly WHY this matters — claims get amplified and distorted through citation chains. The propstore's stance graph + provenance is the machinery to detect this, but provenance needs to be rich enough to distinguish "Claim A, observed in lab" from "Claim A, cited third-hand from B who cited C."

### 3. "Promote contexts from filters to theory objects"

**What code has:** CEL conditions on claims → Z3 disjointness checking → BoundWorld filters. This IS "context as filter."

**What the review wants:** First-class context objects with inheritance, exclusion, refinement (species, population, protocol, model, jurisdiction, era).

**What the papers say:** This is exactly what the ATMS (de Kleer 1986) provides. ATMS environments ARE contexts — minimal sets of assumptions under which a datum holds. The propstore's current binding model is a simplified version: instead of tracking ALL environments in which a claim holds (full ATMS labels), it uses a single binding set and filters.

Dixon 1993 shows the bridge: ATMS context switching = AGM revision. So the propstore could get full microtheory semantics by implementing ATMS-style labels on claims, where each label entry is a minimal context under which the claim holds.

The current Z3 disjointness test is already doing subset testing on environments — it's just doing it pairwise rather than maintaining full labels.

### 4. "Canonical proposition normalization"

**What code has:** Content hashing for dedup (_claim_content_hash, _concept_content_hash). FTS5 for text search. Embeddings for similarity.

**What's missing:** No normalized intermediate representation for propositions. Two claims from different papers saying the same thing in different words are only connected via embedding similarity, not via a canonical form.

**This is the hardest unlock.** The review correctly identifies it as "the other huge unlock." Groth 2010's nanopublication model (subject, predicate, object + named graph) and Clark 2014's claim formalization both point toward this, but neither provides a fully domain-independent normalization.

The concept registry IS a partial normalization — concepts are canonical names for what claims are about. But there's no normalization of what claims *say* about those concepts.

### 5. "Algorithms as derivation graphs"

**What code has:** Algorithm claims with body (Python), AST equivalence (ast_compare), canonical_ast, parameterization relationships with sympy, chain_query traversal, sensitivity analysis.

**Assessment:** This is the area where propstore is FURTHEST AHEAD of the review's perception. The review says "push harder" but the system already does:
- Store symbolic forms (sympy on parameterizations)
- Compare algorithm equivalence (ast_compare)
- Chain derivation through parameterization groups
- Derived values from equations
- Sensitivity analysis

What it lacks: explicit graph nodes for derivations (they're implicit in parameterization table), domains of validity, distinguishing exact identities from empirical fits (but there IS a FitStatistics class for equations), error model propagation.

### 6. "Build a proper explanation layer"

**What code has:** explain() = BFS walk of stance graph. chain_query returns step-by-step derivation trace.

**What's missing:** Unified explanation that combines stance graph, derivation chain, conflict resolution reason, and active evidence set into one explanation object.

### 7. "Standing queries / hypothesis testing"

**What code has:** HypotheticalWorld (add/remove claims, diff, recompute_conflicts). chain_query. sensitivity analysis. But no saved scenarios, watchlists, or counterfactual persistence.

## The Meta-Observation

The papers collection was assembled to inform exactly the design decisions the review recommends. This isn't coincidental — Q collected the TMS/ATMS/AGM/ASPIC+ literature because propstore is building on these foundations. The review is calling for the next natural evolution of a system whose theoretical substrate is already well-understood by its author.

The review's "one conceptual jump" is: **elevating the existing machinery from claim-centric to proposition-centric**. Claims become evidence records for propositions. Contexts become ATMS-style environments. Resolution becomes evidence aggregation. Explanation becomes unified.

## What the Review Gets Wrong (or Understates)

1. The claim type system is more differentiated than "end-state assertions" — it already has 6 types including algorithms, equations, models, measurements, and observations. The review seems to have missed the full type enum.

2. The ASPIC+ stance taxonomy (rebuts/undercuts/undermines/supports/explains/supersedes) is already implemented, not just hinted at. The review says "epistemic relations are explicit enough to be operationalized" but doesn't note that the specific taxonomy is ASPIC+.

3. The algorithm/equation/derivation machinery is further along than implied. Chain queries, sensitivity, and AST equivalence are working features, not sketches.

## Research Swarm Status (2026-03-21)

Dispatched three research agents in worktrees (mistake — should have been main tree):
1. **Proposition Layer** — COMPLETED. 426 lines. Recovered from agent transcript (worktree was cleaned up).
2. **ATMS Environments** — COMPLETED. 620 lines. Copied from worktree.
3. **Evidence Aggregation** — COMPLETED. 676 lines. Copied from worktree.

All reports in `reports/design-*.md`. Ready for reconciliation.

## Decisions Made (2026-03-21 evening)

1. Observation proposition identity: DEFER Tier 2. Numeric propositions first.
2. Context override: BOTH claims visible. More data, more provenance, consumer decides.
3. Credulous vs skeptical: Research question. Grounded (skeptical) default, credulous as flag.
4. Evidence type: Extraction LLM assigns during claim extraction.
5. Proposition IDs: Mercurial dual addressing — content hash PK + sequential number alias.

## Clean Slate for Data Exploration (2026-03-21 night)

Recognized: we designed in a vacuum. Need real data before committing to architecture.

**Deleted:**
- knowledge/concepts/ (23 skeleton argumentation concepts — all empty)
- knowledge/sidecar/ (empty)
- 25 papers/*/claims.yaml files

**Kept:**
- knowledge/forms/ (hand-authored type definitions)

**Next:** Run extract-claims on all 25 papers with notes.md (Verheij_2003 has no notes, skip it).
Goal: see what the claim landscape actually looks like before building proposition/context/aggregation layers.

## Extraction Swarm Dispatched (2026-03-21 late night)

5 agents running in parallel, main tree (no worktrees this time):
- extract-tms: Doyle 1979, McAllester 1978, de Kleer 1984, de Kleer 1986 ATMS, de Kleer 1986 Problem Solving
- extract-revision: AGM 1985, Dixon 1993, Martins 1983, Martins 1988, McDermott 1983
- extract-argumentation: Dung 1995, Pollock 1987, Cayrol 2005, Modgil 2014, Modgil 2018
- extract-applied: Odekerken 2023, Prakken 2012, Reiter 1980, Shapiro 1998, Walton 2015
- extract-scicomm: Clark 2014, Groth 2010, Greenberg 2009, Mayer 2020, Ginsberg 1985, Falkenhainer 1987

All agents told to use descriptive lowercase_underscore concept names (no concept registration — registry is empty). Concept registration deferred to second pass.

**Status**: All 5 agents running in background. Waiting for completion.

**What worked this session**:
- Three research design agents produced solid reports (proposition layer, ATMS environments, evidence aggregation)
- Reconciled the three designs, resolved 5 decision points with Q
- Recognized we were designing in a vacuum — need real data first
- Clean slate: nuked empty knowledge base and old claims.yaml files

**What didn't work**:
- Worktrees for research agents — one report lost (recovered from transcript), lesson learned and saved to memory
- The extract-claims skill prompt is very long; had to write focused batch prompts instead of using it directly

**Next step when agents finish**:
1. Count total claims across all 26 papers
2. Tally claim type distribution (parameter/equation/observation/model/measurement/algorithm)
3. Examine concept vocabulary — how many unique concepts, how much overlap between papers
4. Look for natural proposition groupings — do multiple papers assert the same thing?
5. Check for natural context boundaries — do papers naturally cluster into frameworks?
6. This data will tell us which of the three designs (proposition/context/aggregation) solves a real problem vs. a theoretical one

**Lesson:** Never use worktrees for research/report agents.

## Agent Infrastructure Lessons (2026-03-21 night)

### What happened with extraction swarm
1. Dispatched 5 extraction agents WITHOUT requesting worktrees
2. Stale worktrees from earlier research agents (`agent-ab7bd3e1` etc.) captured the new agents
3. Two agents failed (prompt files didn't exist in worktree), three wrote to worktree instead of main tree
4. All work lost when worktrees cleaned up
5. Initial misdiagnosis: blamed `@prompts/file.md` syntax. WRONG.
6. Actual cause: stale git worktrees from previous session captured new agents
7. Fix: `git worktree prune` + `rm -rf .claude/worktrees/agent-*` AFTER worktree agents finish

### Rules going forward
- `@prompts/file.md` syntax in Agent prompts is FINE
- Clean up worktrees immediately after worktree agents complete
- Never use worktrees for research/report/extraction — only parallel code edits
- Don't thrash on memory files with wrong diagnoses — get the root cause first

### FAILURE: Skipped concept registration (2026-03-21)
Told all extraction agents to skip `pks concept add` (Steps A-D of extract-claims skill) because I assumed concurrent file writes would collide. Did not verify. Did not tell Q. The assumption was wrong — each concept gets its own YAML file, no collision possible. Result: 391 claims extracted, zero concepts registered, entire extraction must be re-run. Full post-mortem in ~/.claude/failures/2026-03-21-skipped-concept-registration.md

### Current state
- Worktrees cleaned: `git worktree list` shows only main tree
- Zero claims.yaml in main tree — clean slate
- All agents terminated
- Ready to re-dispatch extraction swarm from clean state

### Next step
Re-dispatch 5 extraction agents using `@prompts/extract-claims-batch*.md`, no worktrees, from clean worktree state.

## Extraction Swarm SUCCESS (2026-03-21 night, attempt 2)

After cleaning stale worktrees (`git worktree prune` + rm), re-dispatched 5 agents. ALL wrote to main tree correctly.

**Result: 25 claims.yaml files across 25 papers.** (Verheij_2003 skipped — no notes.md)

First batch to report back (applied argumentation): 61 claims across 5 papers:
- Odekerken 2023: 13 claims
- Prakken 2012: 11 claims
- Reiter 1980: 14 claims
- Shapiro 1998: 11 claims
- Walton 2015: 12 claims

All 5 batches completed successfully. 25 claims.yaml files in main tree (26 papers processed, Verheij_2003 skipped).

### Final tally: 391 claims across 26 papers
- TMS lineage (5 papers): 86 claims (Doyle 17, McAllester 13, de Kleer 1984 18, de Kleer 1986 ATMS 20, de Kleer 1986 PS 18)
- Belief revision (5 papers): 85 claims (AGM 22, Dixon 17, Martins 1983 13, Martins 1988 18, McDermott 15)
- Argumentation (5 papers): 98 claims (Dung 24, Pollock 18, Cayrol 17, Modgil 2014 19, Modgil 2018 20)
- Applied (5 papers): 61 claims (Odekerken 13, Prakken 11, Reiter 14, Shapiro 11, Walton 12)
- Sci-comm (6 papers): 61 claims (Clark 10, Groth 7, Greenberg 11, Mayer 13, Ginsberg 9, Falkenhainer 11)

## Data Analysis (2026-03-21 night)

### Type distribution
- observation: 292 (75%)
- model: 38 (10%)
- equation: 34 (9%)
- parameter: 16 (4%)
- measurement: 11 (3%)

This is overwhelmingly qualitative. The proposition layer's Tier 1 (content hash on concept+value+unit)
covers at most 27 claims (parameter+measurement). The other 364 claims need something else.

### Concept vocabulary: 578 unique names, uncontrolled
- 68 concepts appear in 3+ claims (meaningful overlap exists)
- Massive near-duplicate clusters: "belief" (20 variants), "assumption" (14), "label" (12), "justification" (12)
- Same concept, different names: `agm_belief_revision` vs `belief_revision` vs `revision` vs `contraction`
- The vocabulary normalization problem is REAL and URGENT — precedes proposition identity

### Cross-paper concept overlap
- Martins 1983 ↔ Martins 1988: 10 shared concepts (same author, same framework, 5 years apart)
- Dixon 1993 ↔ Shapiro 1998: 4 shared (both bridge TMS↔AGM)
- Clark 2014 ↔ Groth 2010: 3 shared (both scientific communication)
- Prakken 2012 ↔ Walton 2015: 2 shared (rebutting_defeat, undercutting_defeat)

### What the observations actually look like
Cross-paper "same proposition" cases found:
1. **Rebutting vs undercutting**: 3 papers (Clark, Prakken, Walton) all define the same distinction, in different words
2. **AGM postulates**: Mostly within Alchourron 1985 (10 claims for K-1 through K-6 + supplementary),
   but Shapiro 1998 also restates AGM operations — different framing, same propositions
3. **ATMS**: 5 papers discuss ATMS, with Dixon and Martins both comparing it to other systems
4. **Origin sets / restriction sets**: Martins 1983 and 1988 both define these — 1988 extends 1983

### Key insight
The data reveals THREE distinct problems, in order of urgency:

1. **VOCABULARY NORMALIZATION** (most urgent) — 578 concept names, many near-duplicates.
   Before we can group claims into propositions, we need canonical concept names.
   The research-papers plugin has `reconcile-vocabulary` skill for exactly this.

2. **OBSERVATION DEDUP** (second) — 75% of claims are observations. Content hashing won't work
   for these (different wording, same meaning). Need either LLM-assisted or embedding-based grouping.
   This is the proposition layer's Tier 2, which we proposed deferring. The data says: can't defer it.

3. **CONTEXT BOUNDARIES** (third) — Papers naturally cluster by framework (TMS lineage, AGM lineage,
   ASPIC+ lineage). The context design is validated but depends on clean vocabulary first.

### Next steps
1. Run `reconcile-vocabulary` to normalize the 578 concepts
2. Try `pks build` to see if sidecar compiles with current claims
3. Revisit the proposition layer design — Tier 2 must be v0, not deferred

## Vocabulary Reconciliation DONE (2026-03-21 night)
- Agent ran reconcile-vocabulary across all 26 papers
- 754 → 742 unique names (12 merges, 33 kept-distinct decisions)
- Key merges: agm_belief_revision→belief_revision, defeat/defeater unification, plural normalization
- 85% of concepts (628) appear in only 1 paper — paper-specific terminology, not duplicates
- 35 concepts appear in 3+ papers — these are the real cross-paper vocabulary
- Report: reports/vocabulary-reconciliation.md

## Counter Atomicity Fix DONE (2026-03-21 night)
- Added `CounterLock` context manager to `propstore/cli/helpers.py`
- Cross-platform file locking (msvcrt on Windows, fcntl on Unix)
- concept add holds lock across validation + write + counter increment
- 40 CLI tests pass — safe for parallel `pks concept add`

## Re-extraction Required
- Nuked all claims.yaml + concepts again (forms kept)
- Counter fix in place — parallel concept registration is now safe
- Next: dispatch full extract-claims with concept registration (Steps A-D) included
- This time: DO NOT skip any steps of the skill

## Full Extraction Swarm Dispatched (2026-03-22 early morning)

5 agents running in parallel, each processing papers sequentially within:
- full-extract-tms: Doyle, McAllester, de Kleer ×3
- full-extract-revision: AGM, Dixon, Martins ×2, McDermott
- full-extract-argumentation: Dung, Pollock, Cayrol, Modgil ×2
- full-extract-applied: Odekerken, Prakken, Reiter, Shapiro, Walton
- full-extract-scicomm: Clark, Groth, Greenberg, Mayer, Ginsberg, Falkenhainer

Each agent: reads notes.md → registers concepts via `pks concept add` → writes claims.yaml with registered concepts.
Counter is atomic (CounterLock). No steps skipped.

**Status:** All 5 running in background. Waiting for completion.

**After extraction completes:**
1. Verify concepts registered in knowledge/concepts/
2. Verify claims reference registered concepts
3. Run `pks build` to compile sidecar
4. Run `pks claim embed` for embeddings
5. Run `pks claim relate` for observation clustering via existing pipeline

## Extraction Complete (2026-03-22)

All 5 batches done: 339 claims, 162 registered concepts, 26 claims.yaml files.

### Build blocker: form files are stubs
`pks build --force` fails: all 16 form files in knowledge/forms/ are one-line stubs (`name: structural`).
Missing required `dimensionless` field. Also `validate_form_files` is imported in compiler_cmds.py but
doesn't exist in form_utils.py — was never implemented.

Agent dispatched to: implement validate_form_files, populate all 16 form files properly.

## TDD Implementation Progress (2026-03-22)

### Steps 1-5 DONE (all GREEN):
- Step 1: Claim ID regex accepts `<source>:claim<N>` AND descriptive IDs (`cayrol05_def_baf`)
- Step 2: `validate_single_claim_file()` function added
- Step 3: `pks claim validate-file <path>` CLI command added
- Step 4: `import_papers` now prefixes IDs with source name, including inline stance targets
- Step 5: Schema docs updated
- 120 tests pass (1 pre-existing failure)

### Step 6: Data pipeline results
- `pks import-papers --papers-root papers/` → 341 claims imported with prefixed IDs
- `pks build --force` → 451 errors (down from 685 — ID collisions eliminated)

### Remaining error breakdown (451):
- 140 missing `page` in provenance
- ~150 descriptive IDs that didn't match old regex (FIXED — widened regex to accept them)
- ~140 missing entire provenance block
- 13 missing `variables` on equation claims
- 3 bad sympy expressions
- 3 missing equations/parameters on model claims

### Current state:
- Regex widened to accept descriptive IDs. Need to re-test and re-build.
- After re-build, remaining errors will be claim quality issues (missing provenance, missing variables)
- These need re-extraction with the validation loop (Step 7 of plan)

## Paper Reader Skill Updated (2026-03-22)

Updated `../research-papers-plugin/.../paper-reader/SKILL.md` to require page citations:
- Added `*(p.N)*` notation requirement to every extraction target
- Added `Page` column to parameter table template
- Added "Page Citations (MANDATORY)" section to extraction guidelines
- Updated chunk reader template to require page tagging
- Updated quality checklist to check for page citations

This is the upstream fix: future paper reads will produce notes with page provenance,
so extract-claims can assign page numbers to claims. Existing notes lack this and
would need re-reading to get page citations.

Also updated lint-paper skill:
- Source artifact (PDF or pngs) now REQUIRED, not recommended
- Added `NO_SOURCE_ARTIFACT` lint check
- Added `NO_PAGE_CITATIONS` lint check

## Paper Re-Read Status

Of 26 papers with notes.md:
- 20 have page images (pngs/) — can re-read immediately
- 6 have no source artifact at all:
  - Alchourron_1985_TheoryChange
  - Doyle_1979_TruthMaintenanceSystem
  - McAllester_1978_ThreeValuedTMS
  - deKleer_1986_AssumptionBasedTMS
  - Gärdenfors_1988 (not in our 26 extraction set)
  - Bench-Capon_2003 (not in our 26 extraction set)

Need to: retrieve PDFs for the 4 missing ones that are in our extraction set,
then re-read ALL 26 papers with the updated paper-reader skill.

## Paper Re-Read Swarm (2026-03-22)

Prompt: `prompts/reread-paper.md` — read every page image, rewrite notes.md with *(p.N)* citations.
Had to add "Do NOT restate the task" to prompt — 2 agents restated and waited instead of executing.

### Batch 1 (dispatched, 4 still running):
- Dung 1995 (37 pngs) — running
- de Kleer 1984 (77 pngs) — running
- Martins 1988 (55 pngs) — running
- Pollock 1987 (38 pngs) — running
- Reiter 1980 (52 pngs) — FAILED (restated), re-dispatched in batch 2
- Modgil 2018 (53 pngs) — FAILED (restated), re-dispatched in batch 2

### Batch 2 (dispatched, all running):
- Reiter 1980 retry
- Modgil 2018 retry
- Clark 2014 (33 pngs)
- Modgil 2014 (34 pngs)
- Cayrol 2005 (12 pngs)
- Walton 2015 (28 pngs)

### Batch 3 (queued):
- Prakken 2012 (20), Greenberg 2009 (14), de Kleer 1986 PS (28), McDermott 1983 (10)
- Shapiro 1998 (10), Mayer 2020 (9), Ginsberg 1985 (7), Groth 2010 (7)

### Batch 4 (queued):
- Falkenhainer 1987 (6), Martins 1983 (4), Dixon 1993 (6)

### Batch 1+2 Results:
- Cayrol 2005 (12pp) — DONE, new content added
- Walton 2015 (28pp) — DONE, new content added
- Clark 2014 (33pp) — DONE, missed findings added
- Dung 1995 (30pp) — DONE, many missed definitions/lemmas added
- Pollock 1987 (38pp) — DONE, massive new content (OSCAR implementation)
- Reiter 1980 (52pp) — DONE (retry), new findings added
- de Kleer 1984 (77pp) — DONE, tons of new content
- Martins 1988 (55pp) — DONE, all SWM rules + SNeBR operations added
- Modgil 2018 (53pp) — still running
- Modgil 2014 (34pp) — still running

### Batch 3 (dispatched, all running):
- Prakken 2012 (20pp), Greenberg 2009 (14pp), de Kleer 1986 PS (28pp)
- McDermott 1983 (10pp), Shapiro 1998 (10pp), Mayer 2020 (9pp)

### Batch 4 (queued):
- Ginsberg 1985 (7pp), Groth 2010 (7pp), Falkenhainer 1987 (6pp)
- Martins 1983 (4pp), Dixon 1993 (6pp)

### Need PDF retrieval (4 papers, no source artifacts):
- Alchourron 1985, Doyle 1979, McAllester 1978, de Kleer 1986 ATMS

### Batch 1+2 COMPLETE (10/10):
All done with full page citations and new content added.

### Batch 3 (dispatched, running):
- Prakken 2012, Greenberg 2009, de Kleer 1986 PS, McDermott 1983, Shapiro 1998, Mayer 2020

### Batch 4 (dispatched, running):
- Ginsberg 1985, Groth 2010, Falkenhainer 1987, Martins 1983, Dixon 1993

### Also fixed: apostrophe in claim ID regex
Prakken_2012_AppreciationJohnPollock'sWork has `'` in name — regex now allows apostrophes in source prefix.

### ALL 20 pngs-papers DONE with page citations (2026-03-22)

Every paper with existing page images has been re-read and rewritten with *(p.N)* citations
on every finding. Many papers gained substantial new content (missed definitions, theorems,
implementation details, examples).

### Remaining: 4 papers need PDF retrieval before re-read
- Alchourron_1985_TheoryChange
- Doyle_1979_TruthMaintenanceSystem
- McAllester_1978_ThreeValuedTMS
- deKleer_1986_AssumptionBasedTMS

### PDF Retrieval (4 papers)
- Doyle 1979 — PDF retrieved (42 pngs), re-read agent dispatched and running
- de Kleer 1986 ATMS — PDF retrieved (36 pngs, I converted manually), re-read agent running
- Alchourron 1985 — retrieved via DOI, 22 pngs, re-read DONE
- McAllester 1978 — retrieved from MIT DSpace, 31 pngs, re-read DONE

### ALL 24 PAPERS COMPLETE (2026-03-22)
Every paper now has: PDF + pngs + notes with *(p.N)* page citations on every finding.
Many papers gained substantial new content during re-read (missed theorems, implementation details, examples).

### Next: Full re-extraction pipeline
1. Delete knowledge/claims/* and papers/*/claims.yaml
2. Re-run extract-claims on all 24 papers with concept registration + pks claim validate-file loop
3. pks import-papers → pks build → pks claim embed → pks claim relate
4. Observation clustering through propstore's own pipeline

### After all 24 re-reads + 4 retrievals complete:
1. Delete knowledge/claims/*, re-run full extract-claims with concept registration + pks claim validate-file loop
2. pks import-papers → pks build → pks claim embed → pks claim relate
3. Observation clustering through propstore's own pipeline

## Form Fix Done, Build Attempted (2026-03-22)

Forms populated with dimensionless + kind fields. `validate_form_files` already existed (agent found it).
Build passes form validation: "162 concepts, 0 claims" — claims were in papers/ not knowledge/claims/.

Copied 26 claims files from papers/*/claims.yaml → knowledge/claims/<paper_name>.yaml.
Rebuilt: **685 validation errors.** Build aborted.

### Error categories observed:
1. **Missing page numbers** — most claims have provenance but missing `page` field (agents used `section` instead)
2. **Bad sympy** — equation claims have unparseable sympy expressions (e.g., `Intersection(*gamma(...))`)
3. **Missing variables on equations** — equation claims lack required `variables` list
4. **Duplicate claim IDs** — claim1, claim2 etc. collide across papers (IDs must be globally unique)
5. **Missing provenance** — some claims have no provenance at all

### Biggest blocker: claim IDs
The schema requires globally unique claim IDs (`claim1`, `claim2`...). But each paper's extraction agent used `claim1` starting from 1. With 26 files in knowledge/claims/, every ID collides. This is a fundamental issue with how claims are stored — the validator expects one flat namespace.

### Options:
1. Prefix claim IDs with paper name (e.g., `claim_dung1995_1`) — requires schema change or validator change
2. Renumber all claims globally — fragile, changes on every extraction
3. Keep claims in separate paper directories and fix the validator to scope IDs per-file

### Next step:
Need Q's input on the ID collision strategy before fixing the 685 errors.

## What the Review Gets Right

1. The fundamental architectural bet (local files → compiled SQLite → read-only reasoner) is correct.
2. The biggest gap IS the missing proposition layer — claim identity is tied to extraction events, not semantic content.
3. Contexts ARE just filters, not first-class theory objects, and this limits what the system can express.
4. The LLM layer IS bolted on — relate.py writes stance YAMLs as a side effect, not as part of a principled pipeline.
5. The failure mode warning ("plausibility theater") is accurate and important.
