---
title: "Formalizing Context (Expanded Notes)"
authors: "John McCarthy, Saša Buvač"
year: 1998
venue: "Computing Natural Language (Aliseda, van Glabbeek, Westerståhl, eds), CSLI Publications, volume 81 of CSLI Lecture Notes"
doi_url: null
pages: 38
note: "Expanded and revised version of McCarthy 1993 [42]. Earlier draft: Stanford CS Technical Note STAN-CS-TN-94-13 (1994). This version adds sections §7 (Combining Planning Contexts) and §13 (Conclusion). Title page date 'February 28, 2012' is the LaTeX compile date of the Stanford Project JMC mirror copy."
---

# Formalizing Context (Expanded Notes)

## One-Sentence Summary
Introduces a first-order logic of context in which `ist(c, p)` ("`p` is true in context `c`") and `value(c, e)` ("the value of term `e` in context `c`") are the primitive relations, defines entering/exiting contexts and **lifting axioms** between contexts, and applies the apparatus to blocks-world theory, database integration, planning integration, discourse representation, belief revision, and the "transcendence" of outer contexts *(pp.1–3)*.

## Problem Addressed
The "generality problem" in AI (McCarthy 1987 [39]): axiomatizations useful for one purpose carry implicit assumptions that make them unusable when a system needs to reason more generally. Authors want AI systems that are "never permanently stuck with the concepts they use" and can always transcend the current context by adding lifting axioms rather than rewriting the theory *(p.2, p.33)*.

## Key Contributions
- `ist(c, p)` and `value(c, e)` as first-class first-order relations with explicit outer context: the notation `c' : ist(c, p)` asserts `ist(c, p)` itself in context `c'` *(p.2)*.
- Enter/exit operations as push/pop on a context stack; `ist(c,p) ⊢ c:p` (enter) and `c:p ⊢ c₀:ist(c,p)` (exit) *(p.6)*.
- **Lifting axioms** relate truths across contexts; several named relations: `specialize-time(t, c)`, `specializes-time(t, c1, c2)`, general `specializes(c1, c2)` with nonmonotonic `ab1`, `ab2` *(pp.5–6)*, and `assuming(c, p)` that creates a new context in which `p` is assumed *(p.10)*.
- Natural-deduction-style rules **importation** and **discharge** turning `c: p ⊃ q ↔ assuming(c, p): q` into a formal move *(p.10)*.
- Worked example: deriving `blocks: (∀sxy)on(x,y,s) ⊃ above(x,y,s)` from the two-argument `above-theory` via `spec-sit(s)` sub-contexts in two ways — Hilbert-style derivation (formulas 1–18, pp.7–9) and natural-deduction derivation (formulas 19–37, pp.10–12).
- Database integration: GE/Navy/AF jet-engine price example. Shows how lifting axioms (formulas 40–42, 58–59) reconcile incompatible `price` predicates under a problem-solving context `c_ps` *(pp.13–18)*.
- Existence predicate `E(c, x)` for varying domains (free-logic style) and redefinition of the `value` abbreviation (formulas 64–66) so previous axioms remain sound *(pp.19)*.
- Planning integration: supply-planner and route-planner produce plans in different languages, combined via a lifting axiom (formula 70) in `ps`; kindness assumptions are discharged by moving to `ps_urgent` with `timely_route` preconditions (formulas 71–73) *(pp.20–23)*.
- Discourse representation: `query(c, φ)` and `reply(c, φ)` functions on discourse contexts with interpretation axioms, frame axioms, and reply axiom `ist(reply(c,φ), ψ) ≡ ist(c, φ ⊃ ψ)` *(pp.23–28)*.
- Transcendence: `c₀`, `c_{−1}`, ..., possibly transfinite; mentions Tarski/Montague reflexion principles for going beyond the outermost context *(pp.29–30)*.
- Relative decontextualization: "relatively eternal" sentences lifted into a common outer context, a constructive re-reading of Quine's eternal sentences *(pp.30–31)*.
- Mental states as outer contexts: `believe(p, because ...)` outer / `p` inner, bridging reason-maintenance systems and context logic *(pp.31–32)*.

## Study Design
*Pure theory paper. No empirical study. Examples are hypothetical (Sherlock Holmes, blocks world, GE/Navy/AF, AF–GE negotiation, Rome-NYC-Frankfurt transport).*

## Methodology
First-order (or modal) logic extended with context terms. Contexts are **abstract objects**; the paper does not define context but offers examples (situation-calculus situations, conversation contexts, microtheories, wire-signal-time contexts, planner contexts, discourse contexts) *(pp.3–6)*. Axioms are written in the format `c : p` meaning "`p` is true in `c`"; `c` itself can appear inside an outer `ist`. Informal abbreviation convention: the outermost context `c₀` is omitted unless relevant *(p.3)*.

Two derivation styles are developed:
1. **Hilbert style** with explicit enter/exit and universal instantiation.
2. **Natural deduction** using `assuming(c, p)` contexts and rules:
   - **importation**: `c : p ⊃ q ⊢ assuming(c, p) : q` *(p.10)*
   - **discharge**: `assuming(c, p) : q ⊢ c : p ⊃ q` *(p.10)*
   - **assumption** (derived): `⊢ assuming(c, p) : p` *(p.10)*
   - Restriction on ∀-introduction: variable being generalized must not occur free in any `assuming(c, p)` term of the current context (analog of Prawitz [49]) *(p.10)*.

The `assuming` function is also used to *postpone preconditions* (flying example, formulas 38–39) *(p.13)* and is renamed `reply` when used for discourse updates *(p.13, p.25)*.

## Key Equations / Formal Definitions

### Primitive relations

`ist(c, p)` asserts that proposition `p` is true in context `c`.
`value(c, e)` designates the value of term `e` in context `c` *(p.1)*.

Basic sentential form:

$$
c' : ist(c, p)
$$

Read as: "In outer context `c'`, it is asserted that `p` is true in context `c`" *(p.2)*.

### Specialization / lifting (formula 1)

$$
c_0 : ist(\text{specialize-time}(t, c), \text{at}(jmc, Stanford)) \equiv ist(c, \text{at-time}(t, \text{at}(jmc, Stanford)))
$$

Where `specialize-time(t, c)` is a context like `c` in which the time is fixed to `t`, and `at-time(t, p)` asserts `p` holds at time `t` *(p.5)*.

### Nonmonotonic specialization (pp.5–6)

$$
specializes(c_1, c_2) \wedge \neg ab_1(p, c_1, c_2) \wedge ist(c_1, p) \supset ist(c_2, p)
$$

$$
specializes(c_1, c_2) \wedge \neg ab_2(p, c_1, c_2) \wedge ist(c_2, p) \supset ist(c_1, p)
$$

`specializes(c_1, c_2)` = "`c_2` makes no more assumptions than `c_1`"; `ab_1`, `ab_2` are abnormality predicates in McCarthy-style circumscription. Gives nonmonotonic inheritance in both directions *(p.6)*.

### Wire-signal example (formula unlabeled)

$$
(\forall t)(ist(c_{wire117}(t), signal = 0) \equiv \text{door-open}(t))
$$

A lifting axiom that relates a boolean signal on a wire to the physical state of a microwave oven door *(p.6)*.

### Above-theory (formulas 1–6)

Informal:

$$
\text{above-theory} : (\forall xy)(on(x, y) \supset above(x, y))
$$

$$
\text{above-theory} : (\forall xyz)(above(x, y) \wedge above(y, z) \supset above(x, z))
$$

Formalized via `ist` in `c₀`:

$$
c_0 : ist(\text{above-theory}, (\forall xy)(on(x, y) \supset above(x, y)))
$$

Blocks context uses three-argument predicates tied to situations `s`:

$$
blocks : (\forall xys)(on(x, y, s) \equiv ist(\text{spec-sit}(s), on(x, y)))
$$

$$
blocks : (\forall xys)(above(x, y, s) \equiv ist(\text{spec-sit}(s), above(x, y)))
$$

Importation axiom:

$$
c_0 : (\forall p)(ist(\text{above-theory}, p) \supset ist(blocks, (\forall s)(ist(\text{spec-sit}(s), p))))
$$

These allow the derivation of `blocks : (∀sxy) on(x,y,s) ⊃ above(x,y,s)` *(pp.7–9)*.

### Importation rule as axiom (formula 19)

$$
(\forall cpq)(ist(c, p \supset q) \supset ist(assuming(c, p), q))
$$

*(p.10)*.

### Postponing preconditions (formulas 38–39)

$$
c : \text{have-ticket}(x) \wedge \text{clothed}(x) \supset \text{can-fly}(x)
$$

$$
assuming(c, \text{clothed}(x)) : \text{have-ticket}(x) \supset \text{can-fly}(x)
$$

*(p.13)*.

### Price lifting (formulas 40–42)

$$
c_{ps} : (\forall x) value(c_{GE}, price(x)) = GE\text{-}price(x)
$$

$$
c_{ps} : (\forall x) value(c_{NAVY}, price(x)) = GE\text{-}price(x) + GE\text{-}price(spares(c_{NAVY}, x)) + GE\text{-}price(warranty(c_{NAVY}, x))
$$

$$
c_{ps} : (\forall x) value(c_{AF}, price(x)) = f(x, GE\text{-}price(x), GE\text{-}price(spares(c_{AF}, x)), GE\text{-}price(warranty(c_{AF}, x)))
$$

Where `f` is an AF-specific cost function (possibly only approximately bounded) *(pp.15)*. Navy's FX-22 price example derives `c_NAVY : price(FX-22-engine) = $3611K` from $3600K (engine) + $5K (fan blades) + $6K (two-year warranty) *(p.16)*.

### Bargaining variants (formulas 58–59)

$$
c_{ps} : (\forall x) value(c_{GE}, price(x)) = \text{manufacturer-price}(c_{GE}, x)
$$

$$
c_{ps} : (\forall x) value(c_{AF}, price(x)) = \text{budget-price}(c_{AF}, x) + \text{budget-price}(c_{AF}, spares(c_{AF}, x))
$$

Here `price` in AF DB means "price we plan to pay"; lifting axioms only enforce that both sides are comparing engine-only figures rather than letting one side bake in spares implicitly *(p.18)*.

### value as abbreviation (formulas 60–63)

$$
value(c, x) = y \equiv (\forall z)(y = z \equiv ist(c, x = z))
$$

Eliminating `value`, axioms 40–42 become (examples):

$$
c_{ps} : (\forall xy) ist(c_{GE}, y = price(x)) \equiv y = GE\text{-}price(x)
$$

*(p.18)*.

### Existence predicate and domain-sensitive value (formulas 64–65)

$$
c_{ps} : (\forall xy)(E(c, x) \wedge E(c, y)) \supset (ist(c_{GE}, y = price(x)) \equiv y = GE\text{-}price(x))
$$

$$
value(c, x) = y \equiv E(c, x) \supset (\forall z)(E(c, z) \supset (y = z \equiv ist(c, x = z)))
$$

Where `E(c, x)` holds iff `x` exists in context `c`; main implication may not be classical (see Buvač/Buvač/Mason [12]) *(p.19)*.

### Problem-solving enclosure (formula 66)

$$
c_0 : (\forall c) \text{involved-in-ps}(c) \supset (\forall x)(E(c, x) \supset E(c_{ps}, x))
$$

*(p.19)*.

### Planning lifting (formula 70)

$$
ps : (\forall x)(\forall l_1)(\forall l_2)(\forall d_1)(\forall d_2) \; ist(supply\_planner, transport(x, l_1, d_1, l_2, d_2)) \supset transport(x, value(route\_planner, route(l_1, l_2)), d_1, d_2)
$$

Integrates a `transport(x, l1, d1, l2, d2)` plan from supply-planner with a `route(l1, l2)` value from route-planner into a `ps`-context plan *(p.21)*.

### Kindness assumption discharge (formulas 71–73)

$$
ps\_urgent : timely\_route(d_1, d_2, [Rome, NYC, Frankfurt]) \supset transport(equipment1, [Rome, NYC, Frankfurt], 11/6/95, 1/20/96)
$$

$$
ps\_urgent : (\forall x)(\forall r)(\forall d_1)(\forall d_2) \; ist(ps, transport(x, r, d_1, d_2)) \supset timely\_route(d_1, d_2, r) \supset transport(x, r, d_1, d_2)
$$

$$
ps\_urgent : (\forall x)(\forall r)(\forall l_1)(\forall l_2)(\forall d_1)(\forall d_2) (ist(supply\_planner, transport(x, l_1, l_2, d_1, d_2)) \wedge timely\_route(d_1, d_2, value(route\_planner, route(l_1, l_2)))) \supset transport(x, value(route\_planner, route(l_1, l_2)), d_1, d_2)
$$

*(pp.22–23)*. Allows promoting a regular plan to an urgent-context plan conditional on a discharged timeliness predicate.

### Discourse axioms *(p.25)*

- **interpretation axiom (propositional)**, `φ` closed:
$$
ist(query(c, \phi), \phi \equiv yes)
$$
- **frame axiom (propositional)**, `yes` not free in `ψ`:
$$
ist(c, \psi) \supset ist(query(c, \phi), \psi)
$$
- **interpretation axiom (qualitative)**, `x` only free variable:
$$
ist(query(c, \phi(x)), \phi(x) \equiv answer(x))
$$
- **frame axiom (qualitative)**, `answer` not free in `ψ`:
$$
ist(c, \psi) \supset ist(query(c, \phi(x)), \psi)
$$
- **reply axiom**:
$$
ist(reply(c, \phi), \psi) \equiv ist(c, \phi \supset \psi)
$$

### Outer context regress *(p.29)*

Transcendence: from `p` infer `ist(c_0, p)`, thus creating a new outer context `c_{−1}`; may proceed indefinitely, possibly transfinitely. Transcending the outermost context seems to require reflexion principles à la Tarski/Montague: `true(p*) ≡ p` *(p.30)*.

## Parameters / Named Entities (Ontology Table)

| Name | Symbol | Role | Units | Page | Notes |
|------|--------|------|-------|------|-------|
| is-true-in relation | `ist(c, p)` | binary predicate | — | 1 | Primitive. May itself be asserted in another context: `ist(c₀, ist(c₁, p))`. |
| value-in relation | `value(c, e)` | binary function | depends on e | 1, 3 | May be abbreviation of `ist` via formula 60. |
| outer context | `c₀` | constant | — | 4, 7 | Implicit outer context when none named. |
| generic context | `c`, `c'`, `c₁`, `c₂` | variables/constants | — | throughout | |
| lifting context | `at-time(t, p)` | function | — | 5 | Asserts `p` holds at time `t`. |
| specialize-time | `specialize-time(t, c)` | function | — | 5 | Sub-context of `c` with time fixed to `t`. |
| specializes-time | `specializes-time(t, c1, c2)` | predicate | — | 5 | Relation form. |
| specializes | `specializes(c1, c2)` | predicate | — | 5 | General specialization. |
| abnormality 1 | `ab1(p, c1, c2)` | predicate | — | 5 | Circumscription-style abnormality, subcontext→supercontext. |
| abnormality 2 | `ab2(p, c1, c2)` | predicate | — | 5 | Abnormality supercontext→subcontext. |
| assuming context | `assuming(c, p)` | function | — | 5, 10 | Context like `c` with `p` assumed. |
| situation context | `spec-sit(s)` | function | — | 8 | Situation-calculus-valued context. |
| discourse context | `c_d`, `c`, `c1..c6` | constant | — | 24, 26 | Discourse state. |
| query function | `query(c, φ)` | function | context→context | 24, 25 | Updates semantic state. |
| reply function | `reply(c, φ)` | function | context→context | 24, 25 | Updates epistemic state. |
| yes marker | `yes` | proposition | — | 23, 25 | Answer marker for propositional questions. |
| answer predicate | `answer(x)` | unary predicate | — | 23, 25 | Answer marker for qualitative questions. |
| existence predicate | `E(c, x)` | binary predicate | — | 19 | Free-logic-style existence. |
| involved-in-ps | `involved-in-ps(c)` | predicate | — | 19 | Context is part of current problem solving. |
| transcended context | `c_{−1}` | constant | — | 29 | Outer-than-`c₀`. |
| truths-of | `truths(c₀)` | function | set | 29 | Possible extension representing all sentences true in `c₀`. |
| reflexion-style truth | `true(p*) ≡ p` | — | — | 30 | Tarski/Montague style reflexion. |

### FX-22 pricing (§6.2, concrete example)

| Entity | Value | Page |
|--------|-------|------|
| `price(FX-22-engine)` in c_GE | $3600K | 15 |
| `price(FX-22-engine-fan-blades)` in c_GE | $5K | 15 |
| `price(FX-22-engine-two-year-warranty)` in c_GE | $6K | 15 |
| `price(FX-22-engine)` in c_NAVY (theorem) | $3611K | 16 |

## Methods & Implementation Details
- Outer context `c₀` elided unless relevant; formulas written `c:p` (bind colon) to mean `ist(c, p)` in an understood outer context *(p.4)*.
- Enter `c` = push; exit `c` = pop; EKL-style [35] interactive-prover discussion for keeping track of context stack and avoiding source-line ambiguity *(pp.6–7)*.
- Reification: in a cleaner first-order formalization one would write `ist(c₀, Ist(c₁, p))` with `Ist` a term; this paper admits informal use of `ist` at both term and wff positions *(p.7)*.
- Universal-generalization restriction in natural deduction: variable being generalized must not be free in any `assuming(c, p)` term of current context *(p.10)*.
- Rigid-designator assumption used in GE/Navy proof; dropping it requires careful proof adjustment *(p.17)*.
- Domain variation handled via `E(c, x)`; classical universal instantiation invalid for non-rigid terms *(p.19)*.
- Discourse: system receives utterances already-translated into logical formulas (parser+understander upstream [40]); reference markers / DRT-style anaphora not modeled *(p.24)*.
- No single definition of "context"; approximate theory in the sense of [37]; only useful axioms, no iff-definition *(p.32)*.
- Authors explicitly note propositional logic of context is reducible to multi-modal logic [12], [26]; quantificational logic of context is not reducible to standard quantificational modal logic [9] *(pp.32–33)*.

## Figures of Interest
No figures. Paper is entirely formula-driven.

## Results Summary
Paper is a proposal, not an evaluation. The worked theorems are:
- Blocks-world above theorem: `blocks : (∀sxy) on(x,y,s) ⊃ above(x,y,s)` derived two ways *(pp.7–9, pp.10–12)*.
- FX-22 engine price theorem: `c_NAVY : price(FX-22-engine) = $3611K` *(p.16)*.
- Discourse-c2 theorem: `ist(c2, will-bid-on(engine(FX22)))` *(pp.26–27)*.
- Discourse-c4 theorem: `ist(c4, price(engine(FX22), $4M))` *(p.27)*.
- Frame theorem: `ist(c2, will-bid-on(engine(FX22)))` carried across to `c4` via frame axioms *(pp.27–28)*.
- KB theorem: `ist(c_kb, price-including-spares(engine(FX22), $4M))` disambiguates ambiguous `price` predicate *(p.29)*.

## Limitations
- "Present proposals are incomplete and tentative. In particular the formulas are not what we will eventually want" *(p.2)*.
- No definition of context; authors expect a set of axioms, not an iff definition *(p.2, p.32)*.
- Reasoning with contexts depending on parameters (e.g. `spec-sit(s)`) is acknowledged to need further study *(p.10)*.
- Authors are "doubtful" that interactive-theorem-prover-style enter/exit is what programs will actually do *(p.7)*.
- Discourse model does not capture reference markers / DRT anaphora or Grosz-Sidner pragmatics *(p.24)*.
- Kindness-assumption discharge mechanism is sketched; does not cover the heuristics of *when* a system should transcend *(p.30)*.
- Transcending the outermost context requires reflexion principles beyond ordinary first-order logic *(p.30)*.
- Nonmonotonic lifting rules "will surely be more complex than the examples given" *(p.33)*, see [20].
- `f` in AF pricing (formula 42) admitted as possibly only approximately known *(p.15)*.
- Authors state "we are more attached to the derivation than to any specific logical system" — so the exact proof system is deliberately left open *(p.10)*.

## Arguments Against Prior Work
- Quine's "eternal sentence" notion (Quine 1969) is criticized as incompatible with his own other ideas because no language lets one express eternal sentences without *some* context; paper proposes `relatively eternal` sentences instead *(pp.30–31)*.
- Cyc-style context (Guha [29]) is acknowledged as a source; authors adopt Guha's notation over McCarthy 1993 [42] because it was already built into Cyc and "easy for us to change ours" *(p.2)*.
- Principle of charity in natural language: AI usage probably shouldn't make assertions requiring hearer charity for disambiguation *(p.7)*.
- Systems that revise beliefs purely as a function of new belief + old beliefs (classical belief revision) are "inadequate even to take into account the information used by TMS's" — outer-sentence framing with pedigrees subsumes them *(p.32)*.
- Barwise/Perry situation theory [6] is "similar to formal theories of context"; authors cite [44, 2] for direct situation-theory-based context work and [59] for comparison *(p.33)*.
- Gabbay's fibred semantics [23] — "weaving of logics" — is treated as a different technical road to similar ends; comparison in [24] *(p.33)*.

## Design Rationale
- Contexts as first-class objects rather than collections-of-assumptions: lets lifting relations be expressed as sentences in the language, giving in-logic inferences that would otherwise be meta-level *(p.6)*.
- Lifting axioms instead of a single universal theory: "no matter what corners the specialists paint themselves into, what they do can be lifted out and used in a more general context" *(p.33)*.
- `assuming` used both for natural deduction and for postponing preconditions / replies — one mechanism, several applications *(pp.10, 13, 25)*.
- Separating `ist` and `value` because term-denotation spaces may themselves be context-dependent (formula 60 caveat) *(p.3, p.18)*.
- Existence predicate `E(c, x)` preferred over global classical universal instantiation for heterogeneous domains *(p.19)*.
- Outer/inner sentence split for mental states so that reason-maintenance pedigree can live at the modal-operator level, not the asserted-proposition level *(p.31)*.
- Hilbert-style vs natural-deduction-style derivations given as parallel options because "this kind of proof transformation is logical routine" — choice is deliberately left to implementer *(p.12)*.

## Testable Properties
- Enter/exit must be inverses on the context stack: if `ist(c,p)` is entered and `q` derived, then exiting yields `ist(c,q)` *(p.6)*.
- `specializes(c1, c2) ∧ ¬ab1(p, c1, c2) ∧ ist(c1, p) ⊃ ist(c2, p)` (and symmetric `ab2` version) *(p.6)*.
- Importation rule: `c : p ⊃ q ⊢ assuming(c, p) : q` *(p.10)*.
- Discharge rule (inverse of importation): `assuming(c, p) : q ⊢ c : p ⊃ q` *(p.10)*.
- Assumption rule: `⊢ assuming(c, p) : p` *(p.10)*.
- Universal-generalization restriction: cannot ∀-generalize a variable free in any `assuming(c, p)` term currently on the context stack *(p.10)*.
- Reply axiom: `ist(reply(c, φ), ψ) ≡ ist(c, φ ⊃ ψ)` *(p.25)*.
- Frame axiom (propositional): `ist(c, ψ) ⊃ ist(query(c, φ), ψ)` whenever `yes` ∉ free(ψ) *(p.25)*.
- Existence-gated abbreviation: with `value` defined via formula 65, axioms 40–42 and 58–59 remain sound under varying domains *(p.19)*.
- `c_ps` subsumes existence of involved contexts: `(∀c) involved-in-ps(c) ⊃ (∀x)(E(c, x) ⊃ E(c_ps, x))` *(p.19)*.
- Propositional logic of context reduces bijectively to multi-modal logic with modalities `□_{c_β}` per context `c_β` *(p.32)*. Quantificational logic of context does **not** so reduce *(p.33)*.

## Relevance to Project
**High.** Propstore's project design explicitly cites this paper: contexts are "first-class logical objects qualifying when propositions hold (McCarthy 1993 `ist(c, p)`)". The paper is the primary source for:
- The `ist(c, p)` formalism used in propstore's context layer.
- The `value(c, e)` function that motivates context-dependent term denotation.
- Lifting axioms as the mechanism by which facts from one branch/source/render-policy can be re-stated under the assumptions of another.
- Nonmonotonic inheritance via `ab1`/`ab2` — maps onto propstore's stance/argumentation layer where inheritance can be defeated.
- `assuming(c, p)` as a formal device for postponing / provisionally accepting a precondition — directly analogous to propstore's "never mutate source, always produce proposals" discipline.
- The transcendence idea (dropping implicit assumptions by lifting into a wider context) maps onto propstore's "hold multiple rival normalizations" design principle.
- Query/reply discourse axioms are structurally similar to the propstore render-layer notion of policy-driven views over the same corpus.
- The kindness-assumption discharge (urgency sub-context) is a concrete pattern for propstore's hypothetical-reasoning flow.

## Open Questions
- [ ] How does `specializes(c1, c2)` interact with propstore's branch lattice semantics (ATMS/ASPIC+)?
- [ ] Is propstore's CEL+Z3 "context" the same notion as McCarthy's `c` or an orthogonal one? The latter is about entire language/ontology/time; CEL expressions are typically narrower.
- [ ] Which lifting axioms should be canonical in propstore (time, speaker, terminology, vocabulary)? Paper gives only examples; leaves the "taxonomy of contexts" open (references Hayes [30]).
- [ ] Is rigid-designator assumption acceptable for propstore's concept registry, or do we need `E(c, x)` machinery from §6.5?
- [ ] Should propstore's conflict detector treat `ab1` / `ab2` as first-class or as emergent from stance preferences?
- [ ] The paper's non-reducibility result for quantificational context logic (p.33) — does propstore need this level, or is propositional context logic + reification sufficient?

## Related Work Worth Reading
- **[29] Guha 1991 PhD thesis** — Cyc context formalization; direct ancestor of notation used here.
- **[39] McCarthy 1987 "Generality in AI"** — original motivation for the paper.
- **[42] McCarthy 1993 IJCAI** — the paper this expanded note revises.
- **[12] Buvač/Buvač/Mason 1995 "Metamathematics of contexts"** — propositional context → multi-modal reduction.
- **[9] Buvač 1996 "Quantificational logic of context"** — why that reduction does not extend to the quantified case.
- **[26] Giunchiglia & Serafini 1994 "Multilanguage hierarchical logics"** — proof-theoretic parallel.
- **[43] McCarthy & Hayes 1969** — epistemological/heuristic decomposition of AI.
- **[37] McCarthy 1979 "Ascribing mental qualities"** — approximate theories.
- **[54] Stalnaker 1998 "On the representation of context"** — philosophical discussion.
- **[59] van Benthem 1998 "Changing contexts and shifting assertions"** — same volume, comparison to situation theory.
- **[34] Kamp 1981 DRT** — reference markers the paper deliberately omits.
- **[1] Akman & Surav 1996 AI Magazine** — overview of context research.
