# propstore — Project Instructions

propstore is a **semantic operating system**. It has two theoretically serious halves:

1. **Concept/semantic layer** — What things mean, how linguistic expressions map to formal concepts, how frames structure knowledge, how contexts qualify truth. Grounded in frame semantics (Fillmore 1982), generative lexicon theory (Pustejovsky 1991), context formalization (McCarthy 1993), ontology lexicalization (lemon/Buitelaar 2011), and micropublication structure (Clark 2014).

2. **Argumentation/reasoning layer** — How claims conflict, how evidence accumulates, how disagreement resolves at render time. Grounded in Dung AFs, ASPIC+, ATMS, subjective logic, probabilistic argumentation, and IC merging.

Neither half is auxiliary to the other. The concept layer is not a "dumb key-value store for the argumentation engine." It is a theoretically grounded system for representing what concepts are, how they relate to language, and how the same concept participates in different contexts. The argumentation layer operates *over* this semantic substrate.

## Core Design Principle

**The system needs a formal non-commitment discipline at the semantic core.**

Do not collapse disagreement in storage unless the user explicitly requests a migration. The repository must be able to hold multiple rival normalizations, multiple candidate stances, multiple competing supersession stories, and multiple render policies — without forcing one to become canonical just because a heuristic found it plausible.

This principle governs every design decision. The system is lazy until rendering. Everything flows into storage with provenance. The render layer filters based on policy.

### Design checklist (before any data-flow decision)

1. Does this prevent ANY data from reaching the sidecar? If yes → WRONG.
2. Does this require human action before data becomes queryable? If yes → WRONG.
3. Does this add a gate anywhere before render time? If yes → WRONG.
4. Is filtering happening at build time or render time? If build → WRONG.

### Honest ignorance over fabricated confidence

When the system lacks evidence, it must say so — not fabricate a number. Vacuous opinions (Jøsang 2001, p.8) represent total ignorance honestly. Calibration (Guo et al. 2017) bridges raw model outputs to the opinion algebra. Every probability that enters the argumentation layer must carry provenance: either empirical evidence counts, a calibrated model output, or an explicit vacuous marker. "I don't know" is a valid and important signal; a made-up 0.75 is not.

## Architectural Layers (one-way dependencies, top depends on bottom)

1. **Source-of-truth storage** — Claims, concepts, forms, contexts, conditions, provenance. Immutable except by explicit user migration. Never mutated by heuristic or LLM output. `propstore/repo/` provides git-backed storage with branch isolation, semantic merge classification, two-parent merge commits, branch reasoning (ATMS/ASPIC+ bridge), and IC merge operators.
2. **Concept/semantic layer** — Concepts are not labels; they are frame elements (Fillmore 1982) with structured internal composition (Pustejovsky 1991 qualia). The concept registry formally links linguistic expressions to ontological entities (lemon model). Contexts are first-class logical objects qualifying when propositions hold (McCarthy 1993 `ist(c, p)`). Forms define dimensional structure; CEL + Z3 provide type-checking and condition reasoning. `KindType.TIMEPOINT` maps to `z3.Real` (same as QUANTITY) but is semantically distinct — not valid for parameterization or dimensional algebra. Vocabulary reconciliation operates at the frame level, not string level.
3. **Heuristic analysis layer** — Embedding similarity, LLM stance classification, candidate concept merges. All output is **proposal artifacts**, never source mutations.
4. **Argumentation layer** — Dung AF construction, ASPIC+ bridge (`aspic_bridge.py` translates claims/stances to formal ASPIC+ types, `aspic.py` builds recursive arguments), preference ordering, extension computation. Goal-directed queries use `query_claim()` / `build_arguments_for()` for backward chaining from a specific conclusion. Operates over assumption-labeled data, not hardened source facts.
5. **Render layer** — Resolution strategies (recency, sample_size, argumentation, override), world queries, hypothetical reasoning. Multiple render policies over the same underlying corpus.
6. **Agent workflow layer** — extract-claims, reconcile-vocabulary, relate, adjudicate. These produce proposals, not truth.

## Literature Grounding

See `papers/index.md` for the full collection with descriptions and tags. Each paper directory contains `notes.md` with detailed extraction, `claims.yaml` where extracted, and cross-references via `reconcile`.

## Known Limitations

**ASPIC+ argument construction:** The claim graph routes through `aspic_bridge.py` → `aspic.py` for recursive argument construction (Modgil & Prakken 2018 Defs 1-22). Rule ordering in the bridge is always empty — only premise ordering from metadata has discriminating power.

**Decision criteria:** Interval dominance (Denoeux 2019) not yet implemented. Pignistic, Hurwicz, lower/upper bound are in `world/types.py:apply_decision_criterion`.

**Semantic merge:** Assignment-level IC merge with CEL/Z3 is implemented. Full belief-base/model semantics for Konieczny IC0-IC8 and rich PAF attack inversion (Amgoud & Vesic 2014) are deferred.

**Deduction, comultiplication, abduction:** Extended Jøsang operators not implemented. Core 2001 operators are complete.

## Technical Conventions

- `uv run` for all Python execution
- `pks` CLI for all propstore operations
- Tests: `uv run pytest tests/`
- Build: `uv run pks build`
- Sidecar is content-hash addressed, rebuilt only when source changes
- Knowledge lives in `knowledge/` (concepts, claims, stances, contexts, forms)
- Papers live in `papers/` with notes.md per paper
