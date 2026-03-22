# propstore — Project Instructions

## Core Design Principle

**The system needs a formal non-commitment discipline at the semantic core.**

Do not collapse disagreement in storage unless the user explicitly requests a migration. The repository must be able to hold multiple rival normalizations, multiple candidate stances, multiple competing supersession stories, and multiple render policies — without forcing one to become canonical just because a heuristic found it plausible.

This principle governs every design decision. The system is lazy until rendering. Everything flows into storage with provenance. The render layer filters based on policy.

### Design checklist (before any data-flow decision)

1. Does this prevent ANY data from reaching the sidecar? If yes → WRONG.
2. Does this require human action before data becomes queryable? If yes → WRONG.
3. Does this add a gate anywhere before render time? If yes → WRONG.
4. Is filtering happening at build time or render time? If build → WRONG.

## Architectural Layers (one-way dependencies, top depends on bottom)

1. **Source-of-truth storage** — Claims, concepts, forms, contexts, conditions, provenance. Immutable except by explicit user migration. Never mutated by heuristic or LLM output.
2. **Theory / typing layer** — Forms, dimensions, condition languages, parameterization graphs, CEL type-checking, Z3 condition reasoning.
3. **Heuristic analysis layer** — Embedding similarity, LLM stance classification, candidate concept merges. All output is **proposal artifacts**, never source mutations.
4. **Argumentation layer** — Dung AF construction, ASPIC+ preference ordering, extension computation. Operates over assumption-labeled data, not hardened source facts.
5. **Render layer** — Resolution strategies (recency, sample_size, argumentation, override), world queries, hypothetical reasoning. Multiple render policies over the same underlying corpus.
6. **Agent workflow layer** — extract-claims, reconcile-vocabulary, relate, adjudicate. These produce proposals, not truth.

## Key Literature Grounding

| Paper | What it grounds |
|-------|----------------|
| Dung 1995 | AF = (Args, Defeats), grounded/preferred/stable/complete extensions |
| de Kleer 1986 | ATMS: label every datum with minimal assumption sets, never commit to one context |
| Dixon 1993 | ATMS context switching = AGM operations; entrenchment from justification structure |
| Alchourron 1985 | AGM postulates: correctness criteria for any belief revision operation |
| Modgil & Prakken 2018 | ASPIC+: attack-based conflict-free, rationality postulates, preference orderings |
| Pollock 1987 | Rebutting vs undercutting defeat, warrant = ultimately undefeated argument |
| Cayrol 2005 | Bipolar argumentation: support creates new defeat paths |
| Odekerken 2023 | ASPIC+ with incomplete information: stability and relevance |

## Technical Conventions

- `uv run` for all Python execution
- `pks` CLI for all propstore operations
- Tests: `uv run pytest tests/`
- Build: `uv run pks build`
- Sidecar is content-hash addressed, rebuilt only when source changes
- Knowledge lives in `knowledge/` (concepts, claims, stances, contexts, forms)
- Papers live in `papers/` with notes.md per paper
