---
title: "Notes on Formalizing Context"
authors: "John McCarthy"
year: 1993
venue: "Proceedings of the Thirteenth International Joint Conference on Artificial Intelligence (IJCAI-93)"
doi_url: ""
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-03T08:10:56Z"
---
# Notes on Formalizing Context

## One-Sentence Summary
McCarthy introduces contexts as first-class formal objects in logic via the relation ist(c, p) meaning "proposition p is true in context c," defines lifting rules that relate propositions across contexts, and proposes transcendence as the mechanism for expanding limited axiomatizations beyond their original scope. *(p.1)*

## Problem Addressed
AI systems need to reason with limited, domain-specific axiomatizations but also need the ability to go beyond those limits when necessary. Human common sense reasoning operates in contexts that are usually left implicit, but AI requires formalizing these contexts as first-class objects to enable: (1) relating facts across different contexts, (2) entering and leaving contexts during reasoning, and (3) transcending the original limitations of a context's axiomatization. *(p.1)*

## Key Contributions
- Formalization of contexts as first-class objects in logic with the basic relation ist(c, p) *(p.1)*
- Lifting rules that relate propositions true in different contexts, enabling cross-context reasoning *(p.4)*
- The concept of transcendence: ability to expand limited axiomatizations beyond their original scope *(p.8)*
- Nonmonotonic inheritance between contexts via abnormality predicates *(p.4)*
- The notion of entering and leaving contexts analogous to natural deduction assumption introduction and discharge *(p.5)*
- Relative decontextualization via Quine's "eternal sentences" and a common supercontext *(p.9)*
- Mental states as outer contexts for belief revision databases *(p.10)*
- value(c, term) for context-dependent term denotation *(p.3)*

## Study Design
*Non-empirical — pure theory/formalization paper.*

## Methodology
The paper develops a formal logical framework treating contexts as mathematical objects. It builds on McCarthy 1987 and Guha 1991, using a notation adapted from Guha's Cyc work. The approach is tentative and exploratory — McCarthy explicitly states the formulas are not final and may be incompatible across sections. The methodology is axiomatic: define the basic relation, give axiom schemas for lifting, demonstrate via worked examples (blocks world, Sherlock Holmes, belief databases). *(p.1)*

## Key Equations / Statistical Models

$$
ist(c, p)
$$
Where: $c$ is a context (first-class object), $p$ is a proposition. The formula asserts that proposition $p$ is true in context $c$. This is the basic relation of the entire formalization.
*(p.2)*

$$
c0: \quad ist(c, p) \quad \text{(1)}
$$
Where: $c0$ is the outer context in which unqualified formulas are true. Formulas are always relative to some outermost context.
*(p.2)*

$$
(\forall xy)(on(x,y) \supset above(x,y)) \quad \text{(2)}
$$
$$
(\forall xyz)(above(x,y) \wedge above(y,z) \supset above(x,z)) \quad \text{(3)}
$$
Where: These are the axioms of above-theory expressed informally (within the context above-theory).
*(p.6)*

$$
c0: \quad ist(above\text{-}theory, (\forall xy)(on(x,y) \supset above(x,y))) \quad \text{(4)}
$$
Where: This is the formal version — the above-theory axiom expressed as an ist assertion in the outer context c0.
*(p.6)*

$$
c: \quad (\forall xys)(on(x,y,s) \equiv ist(c1(s), on(x,y))) \quad \text{(5)}
$$
$$
c: \quad (\forall xys)(above(x,y,s) \equiv ist(c1(s), above(x,y))) \quad \text{(6)}
$$
Where: $c1(s)$ associates a context with each situation $s$. These are the lifting rules that translate between a situational context and the above-theory context. Predicates gain a situation argument when lifted out of above-theory.
*(p.7)*

$$
c0: \quad ist(c, (\forall p\; s)(ist(above\text{-}theory, p) \supset ist(c1(s), p))) \quad \text{(7)}
$$
Which abbreviates to:
$$
c: \quad (\forall p\; s)(ist(above\text{-}theory, p) \supset ist(c1(s), p)) \quad \text{(8)}
$$
Where: This asserts that all facts of above-theory hold in the situation-specific contexts c1(s). Note: quantifying over $p$ in ist necessarily involves quantifying into an ist, which is problematic in first-order logic. *(p.7)*

$$
c0: \quad ist(c, on(A, B, S0)) \quad \text{(9)}
$$
$$
c: \quad ist(c1(S0), on(A, B)) \quad \text{(10)}
$$
$$
c1(S0): \quad on(A, B) \quad \text{(11)}
$$
$$
c: \quad ist(c1(S0), (\forall xy)(on(x,y) \supset above(x,y))) \quad \text{(12)}
$$
$$
c1(S0): \quad (\forall xy)(on(x,y) \supset above(x,y)) \quad \text{(13)}
$$
$$
c1(S0): \quad above(A, B) \quad \text{(14)}
$$
$$
c: \quad ist(c1(S0), above(A, B)) \quad \text{(15)}
$$
Where: This is the complete worked derivation showing how to derive above(A,B) from on(A,B,S0) by entering context c1(S0), applying above-theory, and optionally leaving the context.
*(p.7)*

$$
ist(specialize\text{-}time(t, c), at(jmc, Stanford))
$$
$$
\equiv ist(c, at\text{-}time(t, at(jmc, Stanford)))
$$
Where: specialize-time(t,c) is a context related to c in which time is specialized to value t. at-time(t,p) is a lifting relation.
*(p.4)*

$$
c0: \quad specializes\text{-}time(t, c1, c2) \wedge ist(p, c1) \supset ist(c2, at\text{-}time(t, p))
$$
Where: This is the axiom for the specializes-time predicate. It enables lifting propositions from a time-specialized subcontext to a more general context with explicit time parameter.
*(p.4)*

$$
specializes(c1, c2) \wedge \neg ab1(p, c1, c2) \wedge ist(c1, p) \supset ist(c2, p)
$$
$$
specializes(c1, c2) \wedge \neg ab2(p, c1, c2) \wedge ist(c2, p) \supset ist(c1, p)
$$
Where: $specializes(c1,c2)$ means c2 involves no more assumptions than c1 and every proposition meaningful in c1 translates to one meaningful in c2. $ab1$ and $ab2$ are abnormality predicates enabling nonmonotonic inheritance of ist in both directions (subcontext to supercontext and vice versa).
*(p.4)*

$$
assuming(p, c)
$$
Where: $assuming(p,c)$ is a context like $c$ in which $p$ is assumed (in the natural deduction sense).
*(p.4)*

$$
\exists x(present(c, x) \wedge P(x))
$$
Where: If we have shown $\exists x P(x)$ within context $c$, we can infer the existence of something present in $c$ satisfying $P$. This relates quantifiers to context domains.
*(p.6)*

$$
\forall x (present(c, x) \supset P(x))
$$
Where: Analogous rule — presently(c, exp) allows quantifier manipulation when entering context $c$.
*(p.5-6)*

$$
ist(c_{wire117}(331), signal = 0)
$$
Where: $c_{wire117}(t)$ is a context associated with wire 117 at time $t$. Signal is a term whose value is 0 or 1. This shows contexts for physical system components parameterized by time.
*(p.4-5)*

$$
ist(c0, ist(c1, p))
$$
Where: ist sentences can themselves be true in contexts, creating nested context assertions. $Ist(c,p)$ as a term (rather than wff) is proposed for reification but deferred.
*(p.6)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Outer context | c0 | — | — | — | 2 | Default context in which unqualified formulas hold |
| Abnormality predicate (up) | ab1 | — | — | — | 4 | Guards nonmonotonic inheritance subcontext→supercontext |
| Abnormality predicate (down) | ab2 | — | — | — | 4 | Guards nonmonotonic inheritance supercontext→subcontext |

## Methods & Implementation Details
- **ist(c, p) as basic relation**: Proposition p is true in context c. Contexts are first-class objects. *(p.1-2)*
- **Contexts are abstract objects**: Not always fully definable. Some contexts are like points — we know their neighborhoods (nearby contexts) but cannot fully specify them. *(p.2)*
- **Outer context c0**: All formulas without explicit context qualification are implicitly asserted in c0. c0 is dropped from notation when convenient. *(p.2-3)*
- **context-of function**: context-of("Sherlock Holmes stories") returns a context in which Holmes is a detective. Used to create contexts from descriptions. *(p.2)*
- **value(c, term)**: Returns the value of a term in context c. Different from ist — values may themselves be context-dependent. The domain of terms may also vary by context. *(p.3)*
- **domain(c)**: Associates a domain of discourse with each context c. Allows different contexts to have different universes of objects. *(p.6)*
- **Lifting rules**: The core mechanism for relating propositions across contexts. A proposition in one context is lifted to another by adding/removing parameters (e.g., situation arguments, time parameters). Lifting rules are axiom schemas specific to pairs of context types. *(p.4, 6-7)*
- **Entering/leaving contexts**: Analogous to assumption introduction/discharge in natural deduction. Enter context c to use ist(c, p) as bare p; leave to get ist(c, derived-conclusion). Multiple entry/exit styles possible. *(p.5)*
- **Quantifying into ist**: Writing ist(c, (∀p)(...)  requires quantifying into the scope of ist, which is problematic in first-order logic. McCarthy acknowledges this and proposes fixing it via reified terms Ist(c,p) or modified logic. *(p.6-7)*
- **Blocks world derivation**: Complete worked example showing how on(A,B,S0) in context c yields above(A,B) in context c1(S0) by entering the situation context, applying above-theory axioms, and leaving. Equations (5)-(15). *(p.7)*
- **Nonmonotonic context relations**: specializes(c1,c2) with ab1/ab2 gives defeasible inheritance of facts between sub- and super-contexts. *(p.4)*
- **Transcendence (Section 5)**: The ability to go beyond a context's original axiomatization. Human intelligence does this routinely (e.g., Jules Verne's submarine prediction). AI programs need it. Not the same as full intelligence — "something less than full intelligence" can achieve it. *(p.8)*
- **Performing transcendence operationally**: The system should treat being in a context as using an outer context. A sentence p that the program believes without qualification is regarded as ist(c, p). Performing an operation on p should give a new outer context. *(p.8)*
- **Relative decontextualization (Section 6)**: Quine's "eternal sentences" — sentences whose truth doesn't depend on context. The idea is that when several contexts exist, there is a common supercontext above all of them into which all terms and predicates can be lifted. Sentences in this supercontext are "relatively eternal." This is needed for database integration across contexts. *(p.9)*
- **Mental states as outer contexts (Section 7)**: A person's state of mind can be regarded as a set of propositions — but more usefully as the set of contexts in which those propositions hold. Belief revision systems can use contexts: entering a new belief creates a new context. The system can use presently(c0, S.A.) = George Bush style notation but also needs provenance — where the belief came from, reasons for it. *(p.10)*
- **Belief revision via contexts**: A belief-revision system that revises a database of beliefs as a function of new beliefs being introduced and old beliefs. Such systems need to take into account the information used by TMS to revise beliefs. The outer context approach (provenance) might be adequate if the consequent revision of inner beliefs would take reasons into account. *(p.10)*
- **Database integration application (Section 8)**: Formalized contexts are practical tools for combining databases with different assumptions (Air Force vs General Electric parts databases with different price assumptions). The context associated with each database captures its assumptions; a program checks whether the Air Force database is up-to-date on GE prices. *(p.10-11)*

## Figures of Interest
- No numbered figures in this paper.

## Results Summary
This is a theoretical formalization paper with no experimental results. The key results are the formal framework itself: ist(c,p) as basic relation, lifting rules for cross-context reasoning, entering/leaving contexts for natural-deduction-style reasoning, nonmonotonic inheritance via abnormality predicates, transcendence as the mechanism for expanding limited axiomatizations, and relative decontextualization for finding common ground between contexts. The blocks world derivation (equations 5-15) serves as a complete worked proof-of-concept. *(p.1-11)*

## Limitations
- The proposals are explicitly "incomplete and tentative" — formulas across sections may be incompatible *(p.1)*
- Not proposing a single language with all desired capabilities *(p.1)*
- It is "presently doubtful" that the reasoning for entering/leaving contexts will correspond to an interactive theorem prover *(p.6)*
- Quantifying into ist (formula 7) is problematic in first-order logic and needs fixing via reification or modified logic *(p.6-7)*
- The formalism might need to be extended to provide that c0 (the whole truth) is not a context — or at least is an unusual one *(p.8)*
- Nonmonotonic rules for lifting "will surely be more complex than the examples given" *(p.11)*
- ist(c,p) can be considered a modal operator dependent on c applied to p — this was explained in [Shoham, 1991] *(p.11)*
- The paper does not develop a complete formal system — it is notes toward one *(p.1)*

## Arguments Against Prior Work
- Against modal logic approaches: Contexts require going "beyond the nonmonotonic inference methods first invented in AI and now studied as a new domain of logic" — standard nonmonotonic logic is insufficient *(p.1)*
- Against fixed-domain approaches: The domain of terms may itself be context-dependent, requiring value(c, term) rather than assuming fixed term denotation *(p.3)*
- Against situation calculus without contexts: The blocks world example shows that contexts simplify the representation by separating the static theory (above-theory) from the situational context, rather than adding situation arguments to every predicate *(p.6-7)*

## Design Rationale
- **Why first-class objects**: Contexts must be first-class to enable reasoning about which context to use, comparing contexts, and transcending contexts. Making them formal objects (not just metalinguistic labels) is essential. *(p.1-2)*
- **Why nonmonotonic inheritance**: Facts should flow between sub- and super-contexts by default, but with the ability to block inheritance for specific propositions via abnormality predicates. This matches how human reasoning about context works. *(p.4)*
- **Why entering/leaving rather than always using ist**: Working within a context (after entering it) allows using standard inference rules without the ist wrapper, which is more natural and corresponds to natural deduction practice. *(p.5)*
- **Why not commit to a single formalization**: Different applications need different context relations and lifting rules. A premature commitment to one language would be limiting. *(p.1)*
- **Why separate above-theory from situation context**: This separation allows the static theory to be reused across all situations without restating it, and makes the lifting rules explicit rather than implicit in the situation calculus. *(p.6-7)*
- **Why relative rather than absolute decontextualization**: True "eternal sentences" may not exist. Instead, decontextualization is relative to a set of contexts — finding a common supercontext. This is more practical and honest. *(p.9)*

## Testable Properties
- ist(c,p) is the basic formal relation: asserting p in context c *(p.2)*
- Lifting rules must be defined for each pair of context types — they are not universal *(p.4, 6-7)*
- Nonmonotonic inheritance of ist requires two abnormality predicates (ab1 for upward, ab2 for downward) *(p.4)*
- Entering a context c and having ist(c, p) must yield p within that context *(p.5)*
- Leaving context c with derived q must yield ist(c, q) in the outer context *(p.5)*
- specialize-time(t, c) produces a context where time is fixed to t *(p.4)*
- assuming(p, c) produces a context where p is assumed true *(p.4)*
- specializes(c1, c2) implies every proposition meaningful in c1 is translatable to c2 *(p.4)*
- value(c, term) can differ across contexts for the same term *(p.3)*
- The blocks world derivation (eqs 5-15) is a complete proof chain that must hold *(p.7)*
- Quantifying into ist creates formal problems that need resolution *(p.6-7)*
- Transcendence requires treating current context as ist(c, p) in an outer context *(p.8)*

## Relevance to Project
This paper is foundational for propstore's context system. The ist(c, p) relation directly maps to propstore's claim-in-context model where claims are qualified by contexts. The lifting rules correspond to how propstore might relate claims across different contexts (e.g., different experimental conditions, different theoretical frameworks). The nonmonotonic inheritance with abnormality predicates aligns with propstore's ATMS-based assumption management — contexts that inherit from each other unless specifically blocked. The transcendence concept maps to propstore's render-time resolution where limited axiomatizations (individual paper findings) can be expanded by combining with other papers' findings. The relative decontextualization concept maps to finding common ground between rival normalizations — exactly propstore's core design challenge.

## Open Questions
- [ ] How does ist(c, p) relate to propstore's existing context model in knowledge/contexts/?
- [ ] Can lifting rules be formalized in propstore's CEL condition language?
- [ ] Should propstore's ATMS labels be interpretable as McCarthy contexts?
- [ ] How does the specializes relation map to propstore's branch hierarchy?
- [ ] Does the mental-states-as-outer-contexts idea apply to propstore's branch reasoning?

## Related Work Worth Reading
- [McCarthy, 1987] "Generality in Artificial Intelligence" — the original context proposal this paper builds on *(p.1)*
- [Guha, 1991] "Contexts: A Formalization and Some Applications" — R.V. Guha's PhD thesis developing these ideas further with Cyc *(p.2)*
- [Buvac and Mason, 1993] "Propositional logic of context" — formal logic treatment, appears at same IJCAI *(p.12)*
- [Shoham, 1991] "Varieties of Context" — analyzes context as modal operator *(p.11, 13)*
- [McCarthy and Hayes, 1969] "Some Philosophical Problems from the Standpoint of Artificial Intelligence" — foundational AI philosophy *(p.12)*
- [Quine, 1969] "Propositional Objects" — eternal sentences concept used for decontextualization *(p.9, 13)*
- [McCarthy, 1979b] "First Order Theories of Individual Concepts and Propositions" — relevant to reification of ist *(p.12)*
- [Guha, 1991] thesis — most comprehensive development of McCarthy's context ideas *(p.2)*

## Collection Cross-References

### Already in Collection
- [[McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning]] — McCarthy's earlier circumscription work; this paper extends beyond circumscription to contexts as first-class objects, addressing limitations of pure nonmonotonic reasoning

### New Leads (Not Yet in Collection)
- Guha, R.V. (1991) — "Contexts: A Formalization and Some Applications" — PhD thesis, most comprehensive development of ist(c,p) formalization, directly implemented in Cyc
- Buvac, S. and Mason, I.A. (1993) — "Propositional logic of context" — formal propositional logic treatment of contexts at same IJCAI
- Shoham, Y. (1991) — "Varieties of Context" — analyzes ist(c,p) as a modal operator, alternative formalization perspective
- McCarthy, J. and Buvac, S. (1998) — "Formalizing context (expanded notes)" — expanded version of this paper

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Kallem_2006_Microtheories]] — directly uses McCarthy's ist operator as the foundation of Cyc's microtheory architecture
- [[Ghidini_2001_LocalModelsSemanticsContextual]] — cites in references as foundational work on context formalization

### Conceptual Links (not citation-based)
**Context and multi-context systems:**
- [[McDermott_1983_ContextsDataDependencies]] — **Strong.** McDermott's "data pools" (contexts) are an earlier operational mechanism for the same concept McCarthy formalizes. McDermott shows contexts and data dependencies are the same mechanism; McCarthy provides the logical formalization that McDermott's operational approach lacks.
- [[Martins_1983_MultipleBeliefSpaces]] — **Strong.** Martins' "belief spaces" with restriction sets are another operationalization of multiple contexts. McCarthy's ist(c,p) provides the formal relation; Martins provides the ATMS-based implementation of context switching.
- [[deKleer_1986_AssumptionBasedTMS]] — **Strong.** De Kleer's ATMS labels (assumption sets) are operationally equivalent to McCarthy's contexts. Each ATMS environment is a context in which certain propositions hold. McCarthy's entering/leaving contexts maps to ATMS assumption activation/deactivation.
- [[Kallem_2006_Microtheories]] — **Strong.** Direct implementation of McCarthy's ist in Cyc. Microtheory inheritance hierarchies are a practical realization of McCarthy's specializes relation with nonmonotonic inheritance.
- [[Ghidini_2001_LocalModelsSemanticsContextual]] — **Strong.** Provides rigorous model-theoretic semantics (local models) for multi-context systems that McCarthy's tentative notes sketch informally. Bridge rules formalize what McCarthy calls lifting rules.
- [Ontological Promiscuity](../Hobbs_1985_OntologicalPromiscuity/notes.md) — **Strong.** Hobbs's per-predication eventuality `e` in `p'(e, x₁,…,xₙ)` is the finer-grained sibling of McCarthy's `ist(c, p)`: Hobbs reifies the *condition* of a single predication being true, McCarthy reifies the *context* in which many predications hold. Different formalisms, same architectural move — conditions/contexts must be logical objects, not metadata. Together they give propstore a two-tier model: per-claim eventualities nested inside stable context objects.
