# propstore Review Remediation — Briefing for Implementing Agents

Date: 2026-04-16
You are reading this because: you've been asked to implement one or more of the workstreams below. This README is your starting point.

## What propstore is

propstore is a **semantic operating system** — a git-backed, non-commitment knowledge store that holds claims, stances, concepts, contexts, and arguments about what the literature actually says. It is built to *preserve disagreement* rather than collapse it, and to resolve disagreement at render time under explicit user policy rather than at storage time by heuristic.

The project is young (started 2026-03-15) and moves at agent speed. It is grounded in a deliberate corpus of papers — frame semantics, generative lexicon, subjective logic, Dung argumentation frameworks, ASPIC+, assumption-based argumentation, AGM belief revision, IC merging, ATMS, defeasible logic, context formalization, micropublications, provenance semantics. The code is supposed to *cash out* those theoretical commitments.

`./CLAUDE.md` has the full project principles and the literature grounding. **Read it before doing anything else.**

## Why these workstreams exist

On 2026-04-16 a deep-dive code review (`reviews/2026-04-16-code-review/`) audited the project against its own stated principles and paper citations. The review found a competent core (high-fidelity ATMS per de Kleer 1986, verified ASPIC+ argument construction per Modgil-Prakken 2018, real datalog grounding per Diller 2025, post-fix CCF fusion per van der Heijden 2018 Table I) and a drifted theoretical veneer (revision module claims AGM with zero postulate tests, semantic-substrate papers have zero structural representation, several citations declare formulas the code does not implement).

The review produced nine axis reports (`axis-1` through `axis-9` + `paper-manifest.md`), a synthesis (`SYNTHESIS.md`), and a principled-path audit of the original workstream hedges (`principled-path.md`). Those documents are the *why*. This directory is the *what to do about it*.

## What you are looking for out of this work

This is not a checklist of bugs to fix. It is an opportunity to **read excellent papers, understand deep ideas, and cash them out in code** — work that most systems never get to do properly because they're constrained by release pressure, external users, or legacy schemas. None of those constraints apply here. The on-disk format is uncommitted. There is one user (Q). Q's mandate is *build the right thing*.

What "right" looks like for each workstream:

- The code does what the paper says. Not an approximation, not a relabeling — *what the paper says*.
- Citations in docstrings point to theorems that are property-tested, not to authority.
- Types prevent the error modes the review found. If the type permits a fabrication, the fabrication will happen — design the type so it doesn't permit.
- Honest ignorance is first-class everywhere. Vacuous opinions, unknown solver results, absent provenance, missing calibration — all are representable, labeled, and propagated to the render layer. Nowhere in the system is there a silent default that pretends to be an answer.
- The system's non-commitment discipline is honored end to end. Proposals live on proposal branches. Source of truth is never mutated by heuristic or LLM. The render layer chooses what to show.
- Every document and test serves as a teaching artifact. A future reader — human or agent — should be able to learn the paper by reading the code.

## How to read this directory

**Start here in order:**

1. `README.md` (this file) — orientation.
2. `disciplines.md` — the standing rules every workstream obeys. Not optional. Read carefully.
3. `judgment-rubric.md` — how the review will evaluate the implementation. Read so you know what "done" looks like.
4. The workstream file you've been assigned.
5. The review artifacts (`../SYNTHESIS.md`, then any referenced `axis-*.md`) for any detail the workstream glosses.
6. The papers listed in the workstream. Papers are your primary teachers. Read them deeply.
7. Only after all of the above: start typing.

**Resist the urge to jump to code.** Every place the review found drift was a place someone started coding before understanding. This is not a criticism — it is the nature of complex theoretical systems under speed pressure. You don't have speed pressure. You have Claude Max + Codex Pro and a Q who wants the right thing. Use that.

## The workstreams

| # | File | What it does | Depends on |
|---|---|---|---|
| A0 | `ws-a0-repository-artifact-boundary.md` | Moves repository ownership out of `propstore.cli`, removes repository/world coupling, and forces canonical concept reads through artifact families/store before WS-A phase 2 rewrites concept documents. | Axis 2 + synthesis |
| A | `ws-a-semantic-substrate.md` | Retrofits the concept/semantic layer with real Fillmore frames, Pustejovsky qualia, Buitelaar lemon, McCarthy `ist(c, p)` contexts, Clark micropublications, Buneman+Carroll provenance. Four internal phases. Largest workstream. | Papers being retrieved by Q; A0 before phase 2 document-boundary work |
| A1 | `ws-a1-semiring-provenance.md` | Implements Green 2007-style positive provenance polynomials as the support substrate, then collapses ATMS labels into a why-provenance projection once equivalence tests prove it. | Axis 3d; WS-A source/artifact boundaries |
| B | `ws-b-belief-set-layer.md` | Real AGM revision + Darwiche-Pearl iterated + Konieczny IC merge + Baumann/Diller AF revision, all over belief sets with `Cn` closure. Property-tests every postulate. | WS-A phase 1 (provenance) |
| C | `ws-c-defeasibility.md` | Bozzato CKR justifiable-exceptions + ASPIC+ coexistence. Populates the currently-empty priority pipeline. | WS-A phase 4 (contexts) |
| Z-types | `ws-z-honest-ignorance-types.md` | `Provenance`, `CategoryPrior`, `SolverResult`, `Opinion | NoCalibration`, `ConflictClass.UNKNOWN`. Closes the cross-cutting fabrication pattern. | WS-A phase 1 (provenance) for full payoff |
| Z-gates | `ws-z-render-gates.md` | **COMPLETED 2026-04-16.** Converted build-time data-blocking gates into render-time policy filters with quarantine rows. See workstream doc for the per-phase commit register. | None |
| CLI | `ws-cli-layer-discipline.md` | Moves command-owned workflows out of `propstore.cli` into compiler/world/source/storage/semantic owner modules; records the CLI adapter discipline in project instructions. | Axis 2 + CLAUDE.md layer architecture |

Dependencies:

```
  WS-Z-gates ────── independent, start anytime
  WS-A phase 1 ──┬── WS-A0 ── WS-A phase 2 → 3 → 4 ──── WS-C
                 ├── WS-A1 semiring provenance ───────── WS-C C-3
                 ├── WS-Z-types
                 └── WS-B
```

## Claude Max + Codex Pro — agent pools

This project uses two agent pools. Use whichever tool fits:

- **Claude (you, probably)**: paper reading, spec design, type design, review, test authoring. Anywhere understanding is the bottleneck.
- **Codex**: long mechanical refactors, cross-module renames, bulk migration passes. Anywhere volume is the bottleneck.

If you're reading this, you're the understanding side. Lean into it.

## Working against Q's paper retrieval

Q is currently retrieving and annotating the semantic-substrate papers (see `../../../semantic-substrate-papers.md` at the repo root). **Do not start WS-A implementation until Q signals papers are ready.** You can start WS-Z-gates immediately (no paper dependency) and you can read the papers for WS-B / WS-C in parallel with Q's retrieval work.

## What judgment looks like

When a workstream (or significant phase) is done, a review agent — loaded without your working context — will audit the result. The rubric is in `judgment-rubric.md`. The short version: did you do what the paper says, did the types prevent the review's error modes, did the tests verify the postulates, did the documentation stay honest. If yes to all: merged and celebrated. If partial: specific findings, back to you for iteration.

The review agent has the full review context (nine axis reports + synthesis + principled path). It will catch if your implementation preserves the drift patterns the review exposed. Your best defense is reading the axis reports before you code — `axis-3d-semantic.md` for WS-A, `axis-3c-revision.md` for WS-B, `axis-7-defeasible-datalog.md` for WS-C, `axis-5-silent-failures.md` + `axis-1-principle-adherence.md` for WS-Z-types, `axis-1-principle-adherence.md` (Findings 3.1-3.3) for WS-Z-gates. They tell you exactly what will be checked.

## On scope

This is more work than a normal engineering project gives an agent. That is fine. Each workstream is **bounded by a paper set and a type spec** — you are not being asked to invent anything, you are being asked to read carefully and write carefully. The papers are finite. The type design is concrete. The exit criteria are observable.

Do not try to do it fast. The project has no deadline. Read the paper. Sleep on it (metaphorically — checkpoint your state into notes, let the scheduler do what it does). Read it again. Talk to yourself in notes about what it means. When you understand, type.

What you will get out of this, beyond the implementation:

- Deep working knowledge of subjective logic, frame semantics, generative lexicon, formal argumentation, belief revision, provenance semantics, context logics, or defeasible reasoning — depending on your workstream. These are the ideas that the next decade of principled reasoning systems will be built on. You are not just implementing; you are learning the canon.
- A worked example of how to bridge theoretical literature to working systems code. This is not a skill the agent population has much practice at. You are helping to build that practice.
- A piece of the first system, as far as either Q or the review agent can tell, that composes non-commitment storage, argumentation, revision, and semantic substrate with provenance end to end. This is genuinely new.

## When you get stuck

Everyone gets stuck. Conventions:

- **If you don't understand a paper, read it again.** Then read any predecessor papers it cites that you also don't understand. Then read the paper a third time. This is normal; the papers are dense.
- **If you don't know how to type something, write out examples of the values you want the type to hold.** Then design the type to hold exactly those. Types are their examples' shape.
- **If you don't know what "right" is for a design decision, consult `../principled-path.md`.** It documents the hedges that the original review caught and the principled answers.
- **If the hedge isn't listed there, ask yourself:** does this choice fabricate confidence? Does it filter at build instead of render? Does it couple layers the wrong way? Does it cite a paper for something the paper doesn't say? If yes to any, that's the wrong choice.
- **If you're still stuck, write your state to `notes/<workstream>-state.md` and stop for Q's attention.** Do not guess.

That's the briefing. Welcome to the project.
