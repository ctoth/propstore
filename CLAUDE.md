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

### Honest ignorance over fabricated confidence

When the system lacks evidence, it must say so — not fabricate a number. Vacuous opinions (Jøsang 2001, p.8) represent total ignorance honestly. Calibration (Guo et al. 2017) bridges raw model outputs to the opinion algebra. Every probability that enters the argumentation layer must carry provenance: either empirical evidence counts, a calibrated model output, or an explicit vacuous marker. "I don't know" is a valid and important signal; a made-up 0.75 is not.

## Architectural Layers (one-way dependencies, top depends on bottom)

1. **Source-of-truth storage** — Claims, concepts, forms, contexts, conditions, provenance. Immutable except by explicit user migration. Never mutated by heuristic or LLM output.
2. **Theory / typing layer** — Forms, dimensions, condition languages, parameterization graphs, CEL type-checking, Z3 condition reasoning.
3. **Heuristic analysis layer** — Embedding similarity, LLM stance classification, candidate concept merges. All output is **proposal artifacts**, never source mutations.
4. **Argumentation layer** — Dung AF construction, ASPIC+ preference ordering, extension computation. Operates over assumption-labeled data, not hardened source facts.
5. **Render layer** — Resolution strategies (recency, sample_size, argumentation, override), world queries, hypothetical reasoning. Multiple render policies over the same underlying corpus.
6. **Agent workflow layer** — extract-claims, reconcile-vocabulary, relate, adjudicate. These produce proposals, not truth.

### Known Limitations

**ASPIC+ argument construction:** The current implementation maps claims 1:1 to arguments (flat structure). Full ASPIC+ per Modgil & Prakken 2018 Defs 3-7 requires: strict/defeasible rules, recursive argument building from sub-arguments, and last-link/weakest-link comparison (Defs 20-21). These are not yet implemented.

## Key Literature Grounding

| Paper | What it grounds | Status |
|-------|----------------|--------|
| Dung 1995 | AF = (Args, Defeats), grounded/preferred/stable/complete extensions | Implemented |
| de Kleer 1986 | ATMS: label every datum with minimal assumption sets, never commit to one context | Implemented |
| Dixon 1993 | ATMS context switching = AGM operations; entrenchment from justification structure | Aspirational — no AGM operations implemented |
| Alchourron 1985 | AGM postulates: correctness criteria for any belief revision operation | Aspirational — referenced via Dixon 1993 |
| Modgil & Prakken 2018 | ASPIC+: attack-based conflict-free, rationality postulates, preference orderings | Partial — preference ordering implemented, argument construction is flat (no rules/sub-arguments per Defs 3-7) |
| Pollock 1987 | Rebutting vs undercutting defeat, warrant = ultimately undefeated argument | Implemented |
| Cayrol 2005 | Bipolar argumentation: support creates new defeat paths | Implemented — derived defeats with fixpoint |
| Odekerken 2023 | ASPIC+ with incomplete information: stability and relevance | Partial — stability only |
| Jøsang 2001 | Subjective Logic: Opinion = (b,d,u,a), expectation E(ω) = b + a·u, consensus fusion | Implemented |
| Guo et al. 2017 | Temperature scaling for neural network calibration; ECE metric | Implemented |
| Sensoy et al. 2018 | Evidential deep learning: Dirichlet-based uncertainty from evidence counts | Implemented — evidence-to-opinion mapping |
| Hunter & Thimm 2017 | Probabilistic argumentation: acceptance probability, COH constraint, component decomposition | Partial — COH constraint not enforced |
| Li et al. 2012 | PrAF = (A, P_A, D, P_D): MC sampling with Agresti-Coull stopping for probabilistic AFs | Implemented — MC sampling with Agresti-Coull |
| Denoeux 2019 | Decision-making with belief functions: pignistic, Hurwicz, interval criteria | Aspirational — pignistic/Hurwicz/interval criteria not implemented |
| Fang et al. 2025 | DF-QuAD gradual semantics for quantitative bipolar argumentation frameworks | Implemented — but P_A conflated with base score |

## Technical Conventions

- `uv run` for all Python execution
- `pks` CLI for all propstore operations
- Tests: `uv run pytest tests/`
- Build: `uv run pks build`
- Sidecar is content-hash addressed, rebuilt only when source changes
- Knowledge lives in `knowledge/` (concepts, claims, stances, contexts, forms)
- Papers live in `papers/` with notes.md per paper
