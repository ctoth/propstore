---
title: "EpiPEn: A DSL for Solving Epistemic Logic Puzzles with Z3"
authors: "Josh Horowitz, Jack Zhang"
year: 2021
venue: "Project report"
doi_url: ""
pages: "1-6"
---

# EpiPEn: A DSL for Solving Epistemic Logic Puzzles with Z3

## One-Sentence Summary
Presents a Python DSL on top of Z3 for encoding epistemic-logic puzzle stories, tracking what each agent knows through announcements and simultaneous actions, and solving several classic puzzles with a mostly first-order representation plus a few targeted simplifications. *(p.1-6)*

## Problem Addressed
Epistemic logic puzzles require reasoning not just about facts, but about what individual agents know, what everyone knows, and how that knowledge changes after announcements or observations. Off-the-shelf first-order SMT solving does not directly expose that dynamic-epistemic structure, yet the authors observed that many puzzle instances can still be encoded if the right knowledge-state layer and update operations are built on top. *(p.1-2)*

The paper's practical target is therefore a DSL that lets users describe stories and knowledge updates at the level puzzle designers use, while compiling those descriptions down to Z3 constraints efficiently enough to solve real examples. *(p.1-3)*

## Key Contributions
- Defines a domain-specific language, **EpiPEn**, embedded in Python and backed by Z3, for expressing epistemic puzzle stories, announcements, and knowledge-state updates. *(p.1-3)*
- Introduces a first-order encoding of agent knowledge using `K_A ψ`, where knowledge is represented by universal quantification over the worlds still accessible to agent `A`. *(p.1-2)*
- Supports both ordinary public announcements and step-based simultaneous actions through a `World` object, `announce`, `learn_constant`, and an `assert_adds` block that freezes knowledge until a synchronized update is committed. *(p.2-5)*
- Demonstrates the approach on six puzzles, showing strong performance on several standard examples and documenting two representative cases the system cannot currently solve. *(p.3-6)*

## Methodology
The method starts with a finite set of constants describing the hidden world state and a set `knows(A)` of constants whose values are currently known by agent `A`. A knowledge formula is compiled into a universally quantified Z3 formula ranging over all constants not in `knows(A)`, so an agent knows `ψ` when `ψ` holds for every world still compatible with that agent's information. Puzzle dynamics are encoded as state-transforming operations: `learn_constant` adds newly learned facts into an agent's known set, `announce` publishes public statements into common knowledge, and `assert_adds` lets the user model simultaneous actions whose effects should become visible only after the whole block is processed. *(p.1-5)*

## Key Equations

$$
K_A \psi := \forall(\text{constants not in knows}(A)) : \kappa \rightarrow \psi
$$

Where:
- `A` = an agent
- `knows(A)` = the constants whose values agent `A` currently knows
- `\kappa` = the common-knowledge constraint describing the current edge state
- `\psi` = a formula being evaluated across the worlds compatible with `A`'s current knowledge
*(p.2)*

$$
KV_A e := \exists x \; K_A(e = x)
$$

Where:
- `KV_A e` means agent `A` knows the value of expression `e`
- `x` ranges over candidate values for `e`
- the definition reduces value knowledge to ordinary `K_A` knowledge over an equality
*(p.2)*

$$
K_A \psi \rightarrow K_A K_A \psi
$$

Where:
- the paper checks this positive-introspection axiom for the implemented knowledge operator
- the same reasoning is used to justify iterating `know(...)` expressions inside the DSL
*(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of children in Muddy Children example | `n` | - | 6 | - | 4 | Set in the example program as `n, k = 6, 3` |
| Number of muddy children in Muddy Children example | `k` | - | 3 | - | 4 | Determines the hidden actual world in the example |
| Candidate consecutive-number range lower bound | `A` | - | - | infinite positive integers | 3-4 | The example starts with an infinite set of possible worlds and narrows it by announcements |
| Candidate consecutive-number range upper expression | `B` | - | `A + 1` | infinite positive integers | 3-4 | Encoded symbolically rather than as a finite enumerated set |

## Implementation Details
- The DSL is implemented as an embedded Python language on top of Z3 because Python gives the user familiar syntax while still allowing direct construction of SMT formulas. *(p.2)*
- A story begins with `start_story()` and a set of symbolic constants created with helpers such as `Ints(...)`. *(p.2-3)*
- Characters are explicit objects, e.g. `Characters('Albert Bernard')`, and the current hidden world is constrained through Z3 formulas over those symbolic constants. *(p.2-3)*
- `announce(Character, formula)` models a public assertion; its effect is to conjoin the asserted fact into common knowledge when appropriate. *(p.2-4)*
- `learn_constant(Character, symbol)` records that a character learns the value of a constant, thereby shrinking the space quantified over by `K_A`. *(p.2-3)*
- To encode "A knows whether φ", the DSL uses `know(A, φ)`, which expands into a first-order formula over all worlds still compatible with `A`'s knowledge. *(p.2-3)*
- The implementation goal is to keep formulas inside the common-knowledge accumulator `κ` as small as possible, because large quantified formulas make Z3 much slower. *(p.3)*
- One optimization is a special quantifier-elimination and simplification pass that replaces `∀x Q(x)` with `Q(v)` when the quantified formula is independent of `x`; this produced about a 20x speedup on some examples and more than 100x on harder ones. *(p.3)*
- A second optimization rewrites announcements of the form `know(A, φ)` into `KV_A φ` when sound, and sometimes replaces knowledge-check formulas with an explicit `assert_adds` update instead of deeper nested modal reasoning. *(p.3-5)*
- Simultaneous actions are modeled with `assert_adds(...)`, which freezes all `know()` and `announce()` calls inside the block so their effects are applied only after the whole block closes. *(p.5)*
- For stepwise simulations such as Muddy Children, the implementation uses an explicit `World` object storing the actual valuation of constants, then iterates a loop of announcements and state updates until convergence. *(p.4-5)*

## Figures of Interest
- **Code listing on p.2:** Cheryl's Birthday encoded in EpiPEn, showing the core user-facing API: `start_story`, `Characters`, `Ints`, `announce`, `learn_constant`, and `print_possible_worlds`.
- **Code listing on p.4:** Muddy Children loop, showing how repeated public statements interact with a persistent `World` object and iterative knowledge updates.
- **Code listing on p.5:** `assert_adds` example for the "Who Has the Sum?" puzzle, illustrating simultaneous action semantics.

## Results Summary
- Cheryl's Birthday serves as the central introductory benchmark and is solved cleanly; the final solution is July 16, and the implementation runs in under a second on the authors' machine. *(p.3)*
- The Consecutive Numbers puzzle begins with an infinite family of worlds, but the first two public announcements already force enough structure that the model can be explored incrementally with additional printed world states. *(p.3-4)*
- The Muddy Children encoding is the most complex example in the paper and shows that the DSL can simulate repeated synchronized updates rather than just one-shot public announcements. *(p.4-5)*
- The "Who Has the Sum?" puzzle required the `assert_adds` simplification to reflect simultaneous reasoning; with that hint, the solver verifies the intended outcome, though in about a minute. *(p.5)*
- Two puzzles remain outside the current capability envelope: the unexpected hanging paradox and the sum-product puzzle. *(p.5-6)*

## Limitations
- The unexpected hanging paradox appears to require reasoning about a claim concerning future surprise relative to a knowledge state that already includes the announcement itself; the authors conclude this kind of self-reference is beyond the current EpiPEn model. *(p.5)*
- The sum-product puzzle is awkward because encoding multiplication over unbounded integers requires expensive non-linear arithmetic that Z3 does not handle well in this setup. *(p.6)*
- Even on solvable problems, some examples require hand-written simplifications or structural hints, so the current implementation is not fully automatic. *(p.3-5)*
- The paper explicitly frames the work as a DSL plus practical encodings rather than as a complete solver for arbitrary dynamic epistemic logic. *(p.1-6)*

## Arguments Against Prior Work
- Standard first-order logic can say that a fact `φ` is true, but not directly that agent `A` knows `φ`; the paper's central motivation is that this missing modal layer must be modeled explicitly. *(p.1-2)*
- A naive quantified encoding causes the common-knowledge formula `κ` to grow quickly and become slow for Z3, so direct unoptimized translation is treated as impractical for harder puzzles. *(p.3)*
- Purely declarative modeling of simultaneous actions is not enough for some puzzles; the authors needed `assert_adds` to delay the effects of announcements until a synchronized block ends. *(p.5)*
- The authors treat self-referential surprise reasoning and non-linear arithmetic puzzles as evidence that a straightforward first-order-plus-Z3 embedding has important expressive and performance boundaries. *(p.5-6)*

## Design Rationale
- **Why a Python-embedded DSL?** It lets users write puzzles with familiar programming constructs while still generating Z3 formulas underneath. *(p.2)*
- **Why define `K_A ψ` via quantification over unknown constants?** Because the accessible worlds for an agent are exactly the worlds differing only on values the agent does not yet know. *(p.1-2)*
- **Why define `KV_A e` through `∃x · K_A(e=x)`?** It captures knowledge of an expression's value using the same underlying knowledge operator rather than a separate primitive. *(p.2)*
- **Why keep `κ` small?** Solver performance depends heavily on common-knowledge formula size, so each announcement/update should avoid unnecessary quantified baggage. *(p.3)*
- **Why introduce `assert_adds`?** Simultaneous actions should not let one participant observe another participant's update halfway through the same step. *(p.5)*
- **Why use a `World` object in Muddy Children?** That puzzle describes actions unfolding step by step relative to an actual hidden state, so an explicit actual-world record is more natural than a purely static constraint set. *(p.4-5)*

## Testable Properties
- If `A` knows `ψ` under the encoded operator, then `A` also knows that `A` knows `ψ` (positive introspection), and the authors verified this with Z3. *(p.2)*
- Replacing an announcement of `know(A, φ)` with the corresponding `KV_A φ` simplification can cut announcement cost from about 0.05 seconds to much larger formula costs otherwise, yielding significant speedups. *(p.3)*
- In Cheryl's Birthday, the sequence of announcements should reduce the possible worlds to the single solution July 16. *(p.1-3)*
- In Muddy Children with `n = 6` and `k = 3`, repeated public statements should eventually cause the muddy children to step forward while the clean children do not. *(p.4)*
- In the "Who Has the Sum?" example, the `assert_adds` block should produce a final world where `C = 30`, `A = 60`, and `B = 20`. *(p.5)*

## Relevance to Project
This paper is useful as an implementation sketch for representing epistemic state updates over a symbolic backend rather than as a pure logic formalism. For propstore, its main value is showing how to place a lightweight DSL over Z3 that tracks who knows what, compiles dynamic updates into solver constraints, and introduces targeted simplifications when the direct modal encoding becomes too expensive. *(p.1-6)*

## Open Questions
- [ ] Can the current knowledge encoding be generalized to handle self-referential surprise paradoxes without breaking the first-order backend? *(p.5)*
- [ ] Can the DSL support arithmetic-heavy epistemic puzzles like sum-product without requiring impractical non-linear reasoning? *(p.6)*
- [ ] Which of the paper's hand-written simplifications can be recognized and applied automatically by the system? *(p.3-5)*
- [ ] Would a tighter integration with dynamic-epistemic-logic semantics produce cleaner simultaneous-action encodings than `assert_adds`? *(p.4-5)*

## Related Work Worth Reading
- Baltag and Renne (2016), *Dynamic Epistemic Logic* — formal background for the public-announcement perspective used here. *(ref.1)*
- Rendsvig and Symons (2021), *Epistemic Logic* — background on `K_A` and accessible-world semantics. *(ref.3)*
- de Moura and Bjørner (2008), *Z3: An Efficient SMT Solver* — the solver backend the DSL relies on. *(ref.2)*

## Collection Cross-References

### Already in Collection
- [[Moura_2008_Z3EfficientSMTSolver]] — the foundational Z3 solver paper this DSL is built on top of. *(ref.2)*

### New Leads (Not Yet in Collection)
- Baltag and Renne (2016), *Dynamic Epistemic Logic*. *(ref.1)*
- Rendsvig and Symons (2021), *Epistemic Logic*. *(ref.3)*
- van Ditmarsch and Kooi (2015), *One Hundred Prisoners and a Light Bulb*. *(ref.4)*
- Garson (2021), *Modal Logic*. *(ref.5)*

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Moura_2008_Z3EfficientSMTSolver]] — Strong: EpiPEn is directly a DSL layer over Z3, so the solver architecture and quantifier behavior from the Z3 paper determine what this project can and cannot scale to.
- [[Docef_2023_UsingZ3VerifyInferencesFragmentsLinearLogic]] — Moderate: both papers use Z3 to encode logical reasoning tasks, but Docef focuses on proof checking in linear-logic fragments while this paper focuses on dynamic epistemic state updates.
