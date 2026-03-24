# Review v1 Deep Analysis — 2026-03-22

## GOAL
Deeply understand the review, codebase, and paper collection, then identify possible actions.

## Codebase Architecture (observed)

### Core modules:
- `dung.py` — brute-force Dung AF: grounded/preferred/stable/complete extensions
- `dung_z3.py` — Z3 SAT encoding of same
- `argumentation.py` — ASPIC+ bridge: converts stances → defeats via preference ordering → Dung AF
- `preference.py` — elitist/democratic set comparison per Modgil & Prakken 2018 Def 19
- `maxsat_resolver.py` — MaxSMT weighted conflict resolution
- `world/model.py` — WorldModel: read-only reasoner over compiled sidecar SQLite
- `world/bound.py` — BoundWorld: condition-scoped view with Z3 disjointness checks
- `world/resolution.py` — conflict resolution strategies (recency, sample_size, argumentation, override)
- `world/hypothetical.py` — counterfactual reasoning (add/remove claims)
- `conflict_detector.py` — COMPATIBLE/PHI_NODE/CONFLICT/OVERLAP/PARAM_CONFLICT classification
- `z3_conditions.py` — Z3 solver for CEL condition disjointness
- `validate.py`, `validate_claims.py`, `validate_contexts.py` — compiler validation
- `build_sidecar.py` — SQLite compilation
- `embed.py` — vector embeddings via litellm
- `relate.py` — LLM stance classification

### Data model:
- Concepts (YAML) with forms, aliases, parameterization relationships
- Claims (9 types: parameter, equation, measurement, observation, model, algorithm, mechanism, comparison, limitation)
- Stances (6 types: rebuts, undercuts, undermines, supports, explains, supersedes)
- Contexts (research traditions scoping groups of claims)
- Forms (dimensional type signatures)
- Conditions (CEL expressions, Z3-checked)

### Knowledge directory (current state):
- claims/, concepts/, contexts/, forms/, stances/, sidecar/
- Many files deleted in working tree (massive cleanup in progress?)

## Review's Key Points

### What the review says is strong:
1. Claim-first storage (correct atomization)
2. Condition-scoped validity (PHI_NODE/CONFLICT/OVERLAP)
3. Contexts (escape hatch from forced global consistency)
4. Compiler mentality (build, validate, sidecar, content-hash)
5. World/render language (query, resolve, derive, hypothetical, extensions, sensitivity)
6. Typed forms and dimensions

### Main critique: PREMATURE CANONICALIZATION
- Automatic concept reconciliation without review
- LLM-generated stances feeding formal argumentation as if clean symbolic facts
- Adjudication rhetoric sounding like final truth
- Source rewrites erasing local meaning too early

### Proposed fix: PROPOSAL ARTIFACTS
- embedding similarity → equivalence_proposal
- LLM classifier → stance_proposal
- adjudication → verdict_proposal
- replacement values → migration_proposal
- Never mutate source-of-truth without explicit user migration

### Architectural recommendation: RE-STRATIFY
Six layers with one-way boundaries:
1. Source-of-truth storage
2. Theory/typing layer
3. Heuristic analysis layer
4. Editorial/governance layer
5. Render layer
6. Agent workflow layer

### Theoretical upgrade: LOCAL THEORIES + VIEWS/MORPHISMS
- Move from global concept registry to local theories
- Explicit coercions, views, preserves/loses annotations
- PHQ-9 ≠ clinician-rated depression severity, but both admit a view into weaker shared theory

## Paper Collection (42 papers)

### Truth Maintenance lineage:
- Doyle 1979 (original TMS)
- McAllester 1978 (three-valued TMS)
- McDermott 1983 (contexts + data dependencies)
- Martins 1983, 1988 (multiple belief spaces, SWM logic)
- de Kleer 1984 (qualitative physics)
- de Kleer 1986 (ATMS + problem solving with ATMS)
- Falkenhainer 1987 (belief maintenance with Dempster-Shafer)
- Forbus 1993 (building problem solvers textbook)
- Ginsberg 1985 (counterfactuals)

### Belief revision:
- Alchourron 1985 (AGM postulates)
- Gardenfors 1988 (epistemic entrenchment)
- Dixon 1993 (ATMS ↔ AGM bridge)
- Shapiro 1998 (TMS ↔ AGM survey)

### Abstract argumentation:
- Dung 1995 (THE foundational paper)
- Cayrol 2005 (bipolar argumentation)
- Caminada & Amgoud 2007 (evaluation of formalisms)

### Structured argumentation:
- Pollock 1987 (defeasible reasoning, rebutting vs undercutting)
- Reiter 1980 (default logic)
- Modgil & Prakken 2014 (ASPIC+ tutorial)
- Modgil & Prakken 2018 (ASPIC+ full technical treatment)
- Prakken 2010 (abstract framework for structured arg)
- Prakken & Horty 2012 (appreciation of Pollock)
- Odekerken 2023 (ASPIC+ with incomplete info)
- Bench-Capon 2003 (value-based argumentation)
- Bondarenko 1997 (abstract assumption-based arg)
- Toni 2014 (ABA tutorial)
- Verheij 2003 (artificial argument assistants)

### Argumentation schemes:
- Walton 2015 (classification system)

### Argument mining:
- Mayer 2020 (transformer-based, healthcare)
- Stab 2016 (parsing arg structures in essays)

### Scientific publishing/claims:
- Clark 2014 (micropublications)
- Groth 2010 (nanopublications)
- Greenberg 2009 (citation distortions)

### Computational argumentation:
- Charwat 2015 (methods for solving reasoning problems)
- Dvorak 2012 (fixed-parameter tractability)
- Fichte 2021 (decomposition-guided reductions)
- Jarvisalo 2025 (ICCMA 2023 competition)
- Niskanen 2020 (Toksia solver)
- Mahmood 2025 (structure-aware encodings)
- Tang 2025 (propositional encodings)

### What the paper collection reveals about the system's ACTUAL theoretical foundations:
The collection is extremely deep on both the TMS/belief-revision lineage AND the argumentation lineage.
This is not casual — someone (Q) has systematically collected the key papers from both traditions
and the bridge papers between them (Dixon 1993, Shapiro 1998).

## KEY OBSERVATIONS SO FAR

1. The review's critique about "premature canonicalization" maps directly to what the papers warn about:
   - Doyle 1979's TMS was criticized for its non-monotonic dependencies
   - de Kleer's ATMS was designed specifically to avoid premature commitment by tracking ALL assumption sets
   - The AGM postulates (Alchourron 1985) formalize minimal information loss
   - Dixon 1993 proved ATMS context switching = AGM operations

2. The ATMS design philosophy IS the proposal-artifact pattern:
   - ATMS never commits to one context — it labels every datum with ALL minimal assumption sets
   - The "render" happens when you choose a context (set of assumptions)
   - This is EXACTLY what the review is asking for

3. The review's "local theories + views" recommendation has a concrete realization:
   - ATMS environments are literally local theories
   - The ATMS label on a datum tells you which local theories it belongs to
   - Views/morphisms between environments = the label transformation rules

## Current State of Knowledge (observed)

- 60 concept YAML files remain (many deleted in working tree — 651 files changed, ~37k lines deleted)
- 1 claims file remains: Dung_1995_AcceptabilityArguments.yaml (the rest deleted)
- Stances directory: mostly deleted
- Contexts: ctx_abstract_argumentation.yaml
- Massive cleanup in progress — working tree has deleted most of the old knowledge files
- Remaining concepts are argumentation-domain: argumentation_framework, admissible_set, grounded_extension, preferred_extension, etc.
- Concept quality: many still "placeholder" definitions (e.g. argumentation_framework: "placeholder")

## What relate.py Does (verified by scout report tranche1-scout-relate-report.md)
- Two-pass LLM stance classification via litellm
- First pass: all embedding-similar pairs. Second pass: high-similarity "none" verdicts
- Confidence mapping: first pass strong=0.95, second pass strong=0.70
- Internal pipeline returns plain dicts, never touches disk
- **Single mutation point: `write_stance_file()` at line 463** — writes to `knowledge/stances/<safe_id>.yaml`
- Called from CLI: `cli/claim.py` lines 373 (single) and 391 (all)
- Two paths into claim_stance SQLite: inline stances in claim YAML + standalone stance files
- `argumentation.py` loads claim_stance, filters out supports/explains, applies preference ordering → defeats
- No tests exist for relate.py itself. Downstream tested indirectly via test_world_model.py
- All stance files currently deleted in working tree

## Tranche 1 Status: IN PROGRESS (second attempt, correct design)
- Scout complete (report: reports/tranche1-scout-relate-report.md)
- Coder complete (report: reports/tranche1-coder-proposals-report.md)
- Pyright fixes complete (report: reports/tranche1-fix-pyright-report.md)
- Branch: tranche1-proposal-artifacts (11 commits, 56d8572..8cf4560)
- 754 tests pass, 0 failures
- Changes:
  - relate.py: write_stance_file() now writes status: proposal
  - build_sidecar.py: gates on status field — rejects missing, skips proposal, loads accepted
  - validate_claims.py: validates status field on inline and file-based stances
  - cli/proposal.py: new `pks proposal accept` command
  - 9 new tests in test_proposal_status.py
  - 12 existing test fixture stances updated with status: accepted
- FIRST ATTEMPT WAS WRONG — built build-time gate, opposite of review's principle
- Branch deleted, starting over on tranche1-render-time-filtering
- See ~/.claude/failures/2026-03-22-built-opposite-of-stated-principle.md

### Second attempt (correct design) — MERGED TO MASTER (1fa1f21)
- Removed _populate_defeats(), defeat table
- Added stance_summary(), --confidence-threshold CLI, render explanations
- 8 new tests, 753 total passing
- NOW: removing tranche TODO list from CLAUDE.md, then planning tranche 2

## What the Paper Notes Reveal

### Dung 1995 (read notes in full)
- Definitions are crystal clear: AF = (AR, attacks), then admissible → preferred → stable → grounded → complete
- Key insight: arguments are ABSTRACT — their role is solely determined by relations to other arguments
- Proves default logic, defeasible reasoning, and logic programming are ALL special forms of argumentation
- The current dung.py implementation correctly follows the paper's definitions
- The brute-force enumeration (combinations over all subsets) is correct but O(2^n)

### de Kleer 1986 ATMS (read notes in full)
- Core idea: label every datum with MINIMAL assumption sets under which it holds
- Four invariants: consistency, soundness, completeness, minimality
- Four node categories: True (universal), In (nonmonotonically), Out (empty label), False (no context ever)
- Key: the ATMS NEVER commits to one context. Multiple worlds coexist simultaneously.
- Implementation: bit-vectors for environments, hash tables for subset tests
- THIS is what the review means by "non-collapsing claim ledger"

### Dixon 1993 (read notes in full)
- THE bridge paper: proves ATMS context switching = AGM expansion + contraction
- Uses 5 entrenchment levels derived from ATMS justificational information
- Theorem 1: behavioral equivalence between ATMS and AGM systems
- Essential support ES(p,E) = intersection of all foundational belief sets for p in E
- This gives propstore a principled way to derive preference orderings from justification structure

### Alchourron 1985 AGM (read notes in full)
- 6 basic contraction postulates, 2 supplementary
- Representation theorem: postulates characterize EXACTLY partial meet contraction functions
- Levi identity: revision = contract by negation, then expand
- Harper identity: contraction = intersect original with revision by negation
- This is the correctness criterion for any belief revision in propstore

### Modgil & Prakken 2018 (read first 100 lines)
- Attack-based conflict-free (stronger than defeat-based) — propstore currently uses defeat-based
- Elitist/Democratic set comparison (Def 19) — correctly implemented in preference.py
- Last-link and weakest-link principles — not yet in propstore
- Reasonable argument orderings (Def 18) — not yet checked
- Four rationality postulates proven under attack-conflict-free + reasonable orderings

## DEEP SYNTHESIS — What the Papers Actually Say vs What the System Does

### 1. The ATMS insight the review is reaching for
The review asks for "proposal artifacts" and "non-collapsing claim ledger." The ATMS paper gives the
exact mechanism: label every claim with its assumption set (environments), never commit to one context.
propstore currently commits too early via relate.py writing stances as source-of-truth.

### 2. Dixon 1993 gives the preference bridge
The review says argumentation should be "one renderer among many." Dixon proved ATMS ↔ AGM,
meaning the preference ordering for argumentation can be DERIVED from the assumption structure
rather than being a separate manual/LLM input. This is more principled than the current
claim_strength() heuristic in preference.py.

### 3. Modgil & Prakken 2018 says attack-conflict-free is stronger
propstore's dung.py uses defeat-based conflict-free (standard Dung). Modgil & Prakken 2018
revised this to attack-based conflict-free, which is strictly stronger and enables all four
rationality postulates. This is an actionable upgrade.

### 4. The "local theories" recommendation maps to ATMS environments
The review suggests "local theories + views/morphisms." ATMS environments ARE local theories.
The label on a datum tells you exactly which local theories it belongs to.
Contexts in propstore are a step toward this but much weaker.

### 5. Odekerken 2023 handles the incomplete information case
When not all papers have been processed, propstore has incomplete information.
Odekerken 2023 extends ASPIC+ with four justification statuses (unsatisfiable, defended, out, blocked)
and defines stability (robust to new info) and relevance (which unresolved queries matter).
This is directly applicable to propstore's incremental paper processing.

## Resolution Strategies (observed in resolution.py)
Four strategies: recency, sample_size, argumentation, override
- Argumentation strategy: builds Dung AF from stances → computes grounded extension → sole survivor wins
- For preferred/stable: takes INTERSECTION across all extensions (skeptical over credulous)
- This is architecturally clean — resolution is a read-only view operation, not a mutation

## What Pollock 1987 Tells Us
- Rebutting defeater: reason for denying the conclusion
- Undercutting defeater: reason for denying the LINK between premise and conclusion
- propstore has both (rebuts, undercuts) but also undermines (weakens premise quality) — this third type
  comes from ASPIC+ (Modgil & Prakken) not from Pollock
- Key Pollock insight: warrant = ultimately undefeated argument through ALL levels of defeat
- This maps to grounded extension in Dung (least fixed point)
- OSCAR stores only immediate bases, not all arguments — propstore's sidecar approach is closer to ATMS

## What Cayrol 2005 Tells Us
- BAF = (A, R_def, R_sup) — support is INDEPENDENT of defeat
- New interactions: supported defeat (A supports B, B defeats C) and indirect defeat (A defeats B, B supports C)
- Three admissibility levels: d-admissible (defended), s-admissible (support-closed), c-admissible (both)
- propstore has support relations (supports, explains) but does NOT use them in the Dung AF construction
- argumentation.py line 69: supports/explains are excluded ("not attacks")
- Cayrol says this is wrong — support creates NEW defeat paths (supported defeat, indirect defeat)
- This is an actionable gap

## FINAL SYNTHESIS — Possible Actions

### Category 1: Architectural (what the review recommends, what the papers ground)

**A1. Proposal artifact layer**
- relate.py currently writes stances as source-of-truth
- Change to: write stance_proposals with provenance (model, confidence, date)
- Acceptance requires explicit user action (migration)
- ATMS analogy: proposals are "in" nodes labeled with {LLM_run_X} assumption set

**A2. Attack-based conflict-free (Modgil & Prakken 2018)**
- dung.py uses defeat-based conflict-free
- Upgrade to attack-based conflict-free (Def 14)
- Enables all four rationality postulates
- This is a correctness fix, not a feature

**A3. Bipolar argumentation (Cayrol 2005)**
- Support relations currently discarded in AF construction
- Implement supported defeat and indirect defeat
- d-admissible/s-admissible/c-admissible semantics
- The support data already exists (supports, explains stances)

**A4. Incomplete information handling (Odekerken 2023)**
- Four justification statuses: unsatisfiable, defended, out, blocked
- Stability: is a claim's status robust to new papers arriving?
- Relevance: which unresolved concepts would change the picture?
- Directly applicable to incremental paper processing

### Category 2: Theoretical upgrades

**B1. ATMS-style environment labels**
- Instead of "one context per claim," label each claim with ALL assumption sets under which it holds
- This is the non-collapsing ledger the review asks for
- Dixon 1993 proves this is AGM-equivalent
- Massive change — might be Phase 2

**B2. Local theories + views**
- The review's biggest theoretical suggestion
- ATMS environments as local theories
- Views = morphisms between environments preserving specified structure
- Would require new YAML types: equivalence_edge, coercion, view, preserves, loses

**B3. Entrenchment from justification structure (Dixon 1993)**
- Current claim_strength() in preference.py is ad hoc (log sample_size + 1/uncertainty + confidence)
- Dixon 1993 shows how to derive entrenchment from ATMS justificational information
- Would make preference ordering principled rather than heuristic

### Category 3: Immediate/tactical

**C1. Fill in placeholder concept definitions**
- Many concepts (e.g. argumentation_framework) have "placeholder" as definition
- These came from the cleanup — they need real definitions

**C2. Rebuild knowledge base from papers**
- Massive deletion in working tree suggests a reset/rebuild
- 60 concepts, 1 claims file remaining
- Need to re-extract claims with the new understanding

**C3. Last-link and weakest-link preference principles**
- Modgil & Prakken 2018 Defs 20-21
- Not yet implemented — only elitist/democratic set comparison exists
- These determine HOW arguments are compared, not just THAT they are
