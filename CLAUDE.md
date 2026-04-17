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

When the system lacks evidence, it must say so — not fabricate a number. Vacuous opinions (Jøsang 2001, p.8) represent total ignorance honestly. Calibration (Guo et al. 2017) bridges raw model outputs to the opinion algebra. Every probability-bearing document value that enters the argumentation layer must carry typed provenance: `measured`, `calibrated`, `stated`, `defaulted`, or `vacuous`. The logical provenance carrier is a deterministic JSON-LD named graph (Carroll 2005); the physical carrier is a git note on `refs/notes/provenance`, so provenance does not contaminate claim identity. "I don't know" is a valid and important signal; a made-up 0.75 is not.

## Architectural Layers (one-way dependencies, top depends on bottom)

1. **Source-of-truth storage** — Claims, concepts, forms, contexts, conditions, provenance. Immutable except by explicit user migration. Never mutated by heuristic or LLM output. `propstore/repo/` provides git-backed storage with branch isolation, semantic merge classification, two-parent merge commits, branch reasoning (ATMS/ASPIC+ bridge), and IC merge operators.
2. **Concept/semantic layer** — Concepts are not labels; they are frame elements (Fillmore 1982) with structured internal composition (Pustejovsky 1991 qualia). The concept registry formally links linguistic expressions to ontological entities (lemon model). Contexts are first-class logical objects qualifying when propositions hold (McCarthy 1993 `ist(c, p)`). Forms define dimensional structure; CEL + Z3 provide type-checking and condition reasoning. `KindType.TIMEPOINT` maps to `z3.Real` (same as QUANTITY) but is semantically distinct — not valid for parameterization or dimensional algebra. Vocabulary reconciliation operates at the frame level, not string level.
3. **Heuristic analysis layer** — Embedding similarity, LLM stance classification, candidate concept merges. All output is **proposal artifacts**, never source mutations.
4. **Argumentation layer** — Dung AF construction, ASPIC+ bridge (`aspic_bridge.py` translates claims/stances to formal ASPIC+ types, `aspic.py` builds recursive arguments), preference ordering, extension computation. Goal-directed queries use `query_claim()` / `build_arguments_for()` for backward chaining from a specific conclusion. Operates over assumption-labeled data, not hardened source facts.
5. **Render layer** — Resolution strategies (recency, sample_size, argumentation, override), world queries, hypothetical reasoning. Multiple render policies over the same underlying corpus.
6. **Agent workflow layer** — extract-claims, reconcile-vocabulary, relate, adjudicate. These produce proposals, not truth.

## Literature Grounding

See `papers/index.md` for the full collection with descriptions and tags. Each paper directory contains `notes.md` with detailed extraction, `claims.yaml` where extracted, and cross-references via `reconcile`.

## Gaps

Known gaps between the paper citations / intended behavior and the current implementation are tracked in [`docs/gaps.md`](docs/gaps.md). This replaces an earlier Known Limitations section whose claims the 2026-04-16 code review found to be materially inaccurate (`reviews/2026-04-16-code-review/axis-6-limitation-honesty.md`).

New gaps are added to `docs/gaps.md` when observed; closures happen in the same commit that implements the fix.

## Technical Conventions

- `uv run` for all Python execution
- `pks` CLI for all propstore operations
- Tests: `uv run pytest tests/`
- Build: `uv run pks build`
- Sidecar is content-hash addressed, rebuilt only when source changes
- Knowledge lives in `knowledge/` (concepts, claims, stances, contexts, forms)
- Papers live in `papers/` with notes.md per paper
