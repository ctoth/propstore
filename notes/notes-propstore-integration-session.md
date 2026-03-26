# Propstore Integration Session — 2026-03-19

## Goal
Figure out how to make propstore actually work across domain repos, improve stance/citation graphs, add staleness detection, and demonstrate real value.

## What I've Observed

### Propstore Repo (this repo)
- **Substantial codebase**: world model, build_sidecar, conflict_detector, graph_export, CEL checker, Z3 conditions, sympy generator, parameterization groups, sensitivity analysis
- **Schema**: LinkML schemas for claims and concept registry in `schema/`
- **CLI**: `pks` command via click
- **Dependencies**: linkml, sympy, z3-solver, graphviz, ast-equiv
- **Design doc** (`propositional-knowledge-store-design.md`): comprehensive 800-line design covering SSA for knowledge, concept registry, form system, parameterization relationships, claim types, sidecar architecture
- **main.py**: still just `print("Hello from propstore!")` — the real entry is `pks` CLI
- **Graph export**: builds KnowledgeGraph with concept nodes, claim nodes, and edges for parameterization/relationship/stance/claim_of. Outputs DOT and JSON.
- **World model**: sophisticated — BoundWorld with condition filtering, chain_query for parameterization traversal, conflict detection, FTS5 search, explain (stance graph BFS)
- **No propstore.sqlite currently exists with real data** (there is a propstore.sqlite file but unclear if populated)

### Research Papers Plugin
- Lives at `../research-papers-plugin/plugins/research-papers/`
- Skills: adjudicate, extract-claims, lint-paper, make-skill, paper-process, paper-reader, paper-retriever, process-leads, process-new-papers, reconcile, research, tag-papers
- **extract-claims skill**: well-defined, supports enrich mode (improve existing claims.yaml) and create mode (from notes.md). Knows about concept registry, CEL conditions, stances, uncertainty, measurement claims.
- **generate_claims.py** script exists in the plugin for mechanical baseline extraction

### Domain Repos — Current State

#### qlatt (speech synthesis)
- **392 paper directories**, **361 have claims.yaml**
- But: the claims.yaml files I checked are **EMPTY** (`claims: []`). The mechanical generator ran but produced nothing.
- Has `concept_candidates.yaml` and propstore integration notes (`notes-propstore-friction.md`, `notes-propstore-integration.md`, `notes-propstore-seed.md`)
- No concepts/ or forms/ directories visible at repo root
- This is the most mature domain — 361 papers with notes.md, extensive reconciliation work already done

#### a11y-papers (accessibility)
- **30 paper directories**, **28 with notes.md**
- **0 claims.yaml files** — no claim extraction has been done
- Fresh territory for demonstrating the pipeline

#### metanovel (narratology/writing craft)
- **193 paper directories**, **186 with notes.md**
- **0 claims.yaml files** — no claim extraction has been done
- Interesting test case: narratology concepts are qualitative, not parametric like speech

## Key Findings

### Claims: Not All Empty (corrected)
My initial sampling hit empty files, but scout found **110 of 361** papers DID produce claims via generate_claims.py. 251 (70%) produced `claims: []`.

The script works on Klatt-style parameter tables (`Name | Symbol | Units | Default | Range`). Fails on domain-specific headers, prose, equations, bullet lists. Working as designed — narrow mechanical extractor.

**Puzzle**: papers/*/claims.yaml have claims in 110 cases, but knowledge/claims/*.yaml are all empty. The pipeline from papers/ to knowledge/ claims isn't wired up, or something overwrote them.

The LLM-based extract-claims skill (create mode) is the real solution for the 70% the script can't handle.

### Integration Gap
The propstore is designed as a standalone compiler, but there's no clear "glue" that:
- Points propstore at a domain repo's papers/
- Knows where that domain's concepts/ and forms/ live
- Builds the sidecar for a specific domain
- Makes the world model queryable from within the domain repo

### Staleness Detection
Not implemented yet. The design doc mentions `superseded_by` stances but there's no automated detection of when a newer paper's claims should mark older claims as potentially stale. The conflict_detector.py handles value conflicts but not temporal supersession.

### Stance/Citation Graphs
graph_export.py builds the graph structure. It handles stance edges (claim_stance table). But:
- No claims exist yet → no stance edges exist
- The graph is only as good as the stance annotations in claims.yaml
- No automated stance inference from reconcile output

## What Needs to Happen

### Immediate: Get Real Data Flowing
1. Pick one domain (qlatt is richest), pick a few papers with rich notes.md
2. Run extract-claims in create mode to build real claims.yaml
3. Build the sidecar and see what the world model can actually do
4. This is the "show it doing something cool" demo

### Integration Architecture
- Propstore needs a "repository" concept — point it at a domain repo
- Each domain repo gets its own concepts/, forms/, and sidecar
- The pks CLI should work from within a domain repo

### Staleness Detection Design
- Compare claim dates (from source paper years)
- When newer paper makes claim about same concept with different value → flag
- When newer paper explicitly supersedes → record superseded_by stance
- "Staleness score" based on: age, number of superseding claims, whether methodology was improved

### Stance Graph Improvement
- Mine existing reconcile output (notes.md cross-references) for stance relationships
- Auto-detect contradictions during sidecar build (conflict_detector already does value conflicts)
- Generate stance suggestions from the adjudicate skill output

## Updated Findings (after deeper investigation)

### Qlatt Knowledge Directory — MUCH more than I first saw
The qlatt repo has a full `knowledge/` directory (propstore repo structure):
- **445 concept files** in `knowledge/concepts/` — auto-proposed from claims
- **361 claim files** in `knowledge/claims/` — BUT ALL ARE EMPTY (`claims: []`)
- **11 form files** in `knowledge/forms/` — full set (frequency, time, pressure, etc.)
- **Sidecar directory exists but is EMPTY** — never built successfully because no claims

The concepts were auto-proposed (e.g. `fundamental_frequency.yaml` says "Auto-proposed from 9 claim(s) across 8 paper(s)") but have:
- No aliases
- No relationships
- No parameterization_relationships
- Generic definitions
- All `status: proposed`

So the concept auto-proposal ran and created 445 skeleton concepts, but the actual claims that should reference them are all empty arrays.

### The papers/ claims.yaml vs knowledge/claims/ distinction
- `papers/*/claims.yaml` — per-paper claim files (in the paper directories). ALL EMPTY.
- `knowledge/claims/*.yaml` — compiled claim files (one per paper, in the knowledge dir). ALL EMPTY.
- Both are `claims: []`

This means: the generate_claims.py script was run across all papers but produced no actual claims. The notes.md files exist and are rich, but the mechanical extractor couldn't parse them into structured claims.

### Previous Work (from integration notes)
A seed phase DID work:
- Phase A (seed agent): 21 concepts, 97 claims across 16 papers
- But those were hand-crafted by an agent reading notes.md, not by generate_claims.py
- After friction fixes, validation passed, 90 conflicts detected (87 phi-nodes, 2 real)

Then something happened — it looks like a mass re-run of generate_claims.py overwrote the hand-crafted claims with empty arrays, or the seed claims were in a different location.

### Key Realization
The generate_claims.py mechanical extractor is broken/inadequate for these notes. The LLM-based extract-claims skill (create mode) is what actually works. But it hasn't been run at scale.

## Revised Picture

### What exists and works:
1. Propstore compiler, validator, world model, conflict detector — all working (253 tests pass)
2. CLI (`pks`) with init, validate, build commands
3. Repository class that finds knowledge/ dirs
4. 445 auto-proposed concepts in qlatt (skeletons)
5. 11 form definitions
6. extract-claims skill in create mode (proven to work in seed phase)

### What's broken/missing:
1. **Zero actual claims** in the knowledge store — the data pipeline is dry
2. **generate_claims.py** produces empty results — mechanical extraction fails
3. **Sidecar never built** — no data to compile
4. **No stance relationships** — can't have stances without claims
5. **No staleness detection** — not even designed yet
6. **No cross-repo integration** — propstore is standalone, not wired into research-papers-plugin workflow
7. **a11y-papers and metanovel** have zero propstore infrastructure

## Staleness Detection Design (from scout report)

The scout read all the relevant source and produced a solid design:

**What exists**: claim_stance table has superseded_by/contradicted_by types but almost nothing uses them (one claim in the entire corpus). conflict_detector finds value disagreements but is temporally blind. Publication year is embedded in source_paper strings, not a separate field. sample_size and methodology are stored but unused by conflict detection.

**Five staleness categories**:
1. Superseded — explicit superseded_by stance (highest confidence)
2. Contradicted — contradicted_by stance + newer year
3. Value-drifted — same concept, different values, temporal ordering
4. Methodology-inferior — newer claim has larger N or better methodology
5. Uncontested-old — just old, no conflicts (low confidence flag only)

**Architecture**: Multi-dimensional StalenessReport, not a single score. New `staleness` table in sidecar. staleness_detector.py parallel to conflict_detector.py. Integration: sidecar build, CLI command, WorldModel queries, resolution strategy.

**Key insight**: staleness detection builds on top of conflict detection (which already finds the value disagreement pairs) by adding temporal ordering. The conflict detector does the hard work; staleness adds the "which one is newer?" dimension.

**Open questions**: staleness propagation through chains, domain-dependent age thresholds, reconciliation coverage as prerequisite for stance-based detection.

## What To Do Next

### Thread 1: Get Real Claims Flowing (demo value)
- Pick 5-10 qlatt papers with rich notes.md
- Run extract-claims in create mode to produce real claims
- Build sidecar, query world model, show actual results
- This proves the system works end-to-end

### Thread 2: Fix the Pipeline
- Diagnose why generate_claims.py produces empty results
- Either fix it or replace with LLM-based extraction as default
- Wire extract-claims into paper-process so new papers get claims automatically

### Thread 3: Staleness Detection
- Design: compare publication years, detect superseded_by relationships
- Implement as a propstore feature (pks staleness-check or similar)
- Flag claims from older papers when newer papers address same concepts

### Thread 4: Domain Bootstrapping
- Create `pks init` in a11y-papers and metanovel
- These domains need different concept registries (not speech params)
- Show that the system is truly domain-independent

## Claims Diagnosis Report (scout complete)

generate_claims.py is NOT broken — it's narrow by design.
- **110/361 papers** produced claims (667 total claims)
- Top papers: Klatt 1980 (31 claims), Allen 1987 (31), Anumanchipalli KLATTSTAT (30)
- Quality is LOW: all `page: 0`, no conditions, no stances, no equations, no observations
- Just parameter type with concept/value/bounds/unit — bare mechanical extraction
- These are Klatt-style parameter table scrapes, not real knowledge extraction

The 251 empty papers need LLM-based extract-claims (create mode).

## Tagged Subsets for Demo

Tag distribution (top tags by paper count):
- voice-quality: ~30 papers
- glottal-source: ~21
- fundamental-frequency: ~20
- perception: ~20
- speech-synthesis: ~19
- lf-model: 27 papers (the original seed cluster target)

**lf-model cluster** (27 papers) is the best candidate:
- Already identified as the seed cluster in the integration notes
- Well-defined domain (LF glottal flow model parameters)
- Rich in equations and parameterization relationships
- Includes Fant, Gobl, Doval, Henrich — the core LF model papers
- Small enough to process in one session
- Phase A already did 16 of these with 97 claims — we know it works

## Decision: Fresh Propstore on LF-Model Subset

Q wants:
1. Delete current knowledge/ in qlatt (445 skeleton concepts, all empty claims)
2. Fresh `pks init`
3. LLM-augmented ingestion on lf-model tagged papers (~27 papers)
4. Build real sidecar, demonstrate value

## Current Blocker
Waiting for Q's confirmation on the lf-model subset and fresh start approach.
