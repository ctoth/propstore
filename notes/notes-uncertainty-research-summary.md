# Uncertainty Representation Research — Session Summary

Date: 2026-03-24

## Goal

Replace propstore's broken NLI/embedding/confidence pipeline (bare floats, hardcoded lookup tables, build-time gates) with a principled uncertainty representation grounded in the literature.

## What's Wrong (5 problems from code survey)

1. **Confidence is fabricated** (`relate.py:76-83`). A 6-entry lookup table maps (pass_number, strength_category) → float. The LLM's actual epistemic state is never captured.

2. **Raw embedding distance in LLM prompts** (`relate.py:52`). Model-specific, unnormalized distances interpolated into second-pass prompts. The LLM can't interpret these numbers.

3. **Three conflated float concepts.** `strength` (categorical), `confidence` (lookup float), `claim_strength` (computed float) share no type distinction. Semantically orthogonal quantities stored as interchangeable bare floats.

4. **Build-time threshold gate** (`argumentation.py:106,133`). Stances with confidence < 0.5 are silently dropped before the AF is constructed. Violates non-commitment discipline (CLAUDE.md design checklist: "Is filtering happening at build time or render time? If build → WRONG").

5. **Single-element strength lists** (`argumentation.py:158-159`). Modgil set-comparison machinery exists but is never used — everything averages into one float.

## Papers Processed (7 retrieved, read, annotated)

| Paper | Pages | Key contribution |
|-------|-------|-----------------|
| Guo et al. 2017 — On Calibration of Modern Neural Networks | 6 | Raw neural scores are miscalibrated. Temperature scaling (single param T) fixes it. Proves our lookup table is indefensible. |
| Jøsang 2001 — A Logic for Uncertain Probabilities | 31 | Opinion tuples (b,d,u,a) with complete algebra. Consensus/discounting operators. Bijective mapping to Beta distributions. The core replacement for bare floats. |
| Sensoy et al. 2018 — Evidential Deep Learning | ~10 | Dirichlet params from neural nets → subjective logic opinions. Train models to output uncertainty, not just predictions. Evidence-to-opinion pipeline. |
| Hunter & Thimm 2017 — Probabilistic Argumentation (Epistemic) | 47 | Rationality postulates (COH, FOU, RAT) as LP constraints on AF probabilities. Max entropy propagation for partial assessments. Connects to ATMS nogoods. |
| Li et al. 2012 — Probabilistic Argumentation Frameworks | 15 | Constellations approach: each subgraph is an ATMS environment. PrAF = (A, P_A, D, P_D). MC sampler with Agresti-Coull convergence. Replaces the threshold gate. |
| Denoeux 2019 — Decision-Making with Belief Functions | 39 | Three render-time decision rules: pignistic (default point estimate), Bel/Pl (uncertainty bounds), E-admissibility (honest choice sets via LP). |
| Fang et al. 2025 — LLM-ASPIC+ | 8 | Validated LLM→ASPIC+ architecture. Structured extraction not bare floats. 7-category error taxonomy. Binary beliefs only (gap 7). |

## Proposed Architecture (from design proposal)

**Storage:** Beta(α, β) as canonical representation. Two numbers encoding estimate + evidence strength. Vacuous = Beta(1,1) = "I don't know." Isomorphic to Jøsang opinions, derivable to DS intervals / credal sets at render time.

**Input pipeline:** Raw score → calibration (Guo temperature scaling) → distributional mapping (Sensoy evidence → Beta params). Until calibration data exists, everything starts vacuous — honest ignorance.

**Argumentation:** PrAF replaces threshold gate (Li). Each stance's Beta expectation becomes P_D (existence probability). AF marginalizes over subgraphs via MC sampling. Hunter's epistemic constraints (COH: P(A)+P(B)≤1 for attacks) provide topology-aware propagation.

**Preferences:** Multi-dimensional strength sets replace single floats. Source reliability, evidential support, sample size as separate dimensions. Makes elitist/democratic comparison meaningful.

**Render:** Decision criterion selection per RenderPolicy — pignistic (default), lower/upper bounds, E-admissibility (choice sets), Hurwicz (tunable pessimism). All from Denoeux.

**Non-commitment:** Passes all 4 design checklist items. No data gated before render time.

## 7 Changes in Dependency Order

```
1. Opinion module (new, leaf) — dataclasses + operators from Jøsang
   ↓
2. Calibration module (new) — temperature scaling + corpus CDF from Guo
   ↓
3. relate.py — replace _CONFIDENCE_MAP with BetaEvidence
4. Schema — add Beta columns alongside existing bare floats
   ↓
5. Remove threshold gate — PrAF existence probabilities (Li)
6. Multi-dim preferences — structured dimensions to set comparison
7. Render policies — decision criterion selection (Denoeux)
```

Changes 5, 6, 7 can proceed in parallel after 1-4.

## Open Gaps and Papers to Close Them

| Gap | Description | Paper-closable? | Candidate paper |
|-----|-------------|----------------|-----------------|
| 1 | No calibration data exists | No — needs data collection | — |
| 2 | PrAF computational cost at scale | **Yes** | Fazzinga et al. 2013/2016 (MC sampling for extension probabilities) |
| 3 | Consensus operator + ATMS interaction | No — novel, needs prototyping | — |
| 4 | Hunter scalability for large AFs | **Yes** | Popescu & Wallner 2024 (tree-decomposition DP) |
| 5 | LLM logprob availability | No — needs API survey | — |
| 6 | Multinomial (Dirichlet) extension | **Yes** | Jøsang 2010 IPMU (multinomial opinions) |
| 7 | Binary vs graded beliefs bridge | **Yes** | Freedman et al. 2025 AAAI (LLM→QBAF→gradual semantics) |

### Round 2 papers to acquire

1. **Jøsang 2010** — "Cumulative and Averaging Fusion of Beliefs" (multinomial opinions)
   URL: https://www.mn.uio.no/ifi/english/people/aca/josang/publications/jo2010-ipmu.pdf

2. **Fazzinga, Flesca & Parisi 2013/2016** — "On Efficiently Estimating the Probability of Extensions in Abstract Argumentation Frameworks"
   DOI: 10.1016/j.ijar.2015.11.006

3. **Popescu & Wallner 2024** — "Advancing Algorithmic Approaches to Probabilistic Argumentation under the Constellation Approach"
   URL: https://arxiv.org/abs/2407.05058

4. **Freedman et al. 2025** — "Argumentative Large Language Models for Explainable and Contestable Claim Verification" (AAAI 2025)
   URL: https://arxiv.org/abs/2405.02079
   Code: https://github.com/CLArg-group/argumentative-llms

## Detailed Notes

- Full code survey: `notes-nli-embedding-survey.md`
- Full research survey: `notes-probability-representation-research.md`
- Full design proposal: `notes-uncertainty-design-proposal.md`
- Gap papers research: `notes-gap-papers-research.md`
- Pipeline tracking: `notes-uncertainty-pipeline.md`
- Per-paper notes: `papers/*/notes.md` (7 papers)
