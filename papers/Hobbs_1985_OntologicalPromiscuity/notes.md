---
title: "Ontological Promiscuity"
authors: "Jerry R. Hobbs"
year: 1985
venue: "Annual Meeting of the Association for Computational Linguistics (ACL-23), pp. 61-69"
doi_url: "10.3115/981210.981218"
pages: "61-69"
affiliation: "Artificial Intelligence Center, SRI International; Center for the Study of Language and Information, Stanford University"
funding: "NIH Grant LM03611; NSF Grant IST-8209346; Systems Development Foundation gift"
produced_by:
  agent: "claude-opus-4-7"
  skill: "paper-reader"
  timestamp: "2026-04-17T04:00:46Z"
---
# Ontological Promiscuity

## One-Sentence Summary
Hobbs argues that for discourse interpretation the best logical form is a **flat, first-order, non-intensional notation** where every natural-language predicate `p` has a nominalized companion `p'` whose extra first argument denotes the *eventuality/condition* of `p` being true, and that a sufficiently promiscuous Platonic ontology (objects, events, states, conditions, and nonexistent individuals) lets the notation remain naively compositional while handling opaque adverbials, de re/de dicto belief, and identity in intensional contexts. *(p.61-63)*

## Problem Addressed
Prior logical notations for NL interpretation impose three constraints that make them structurally complicated and ill-suited to discourse processing: (i) **ontological parsimony** (Quinean chastity), (ii) demanding that syntactic regularities fall out of the notation as a by-product, and (iii) building efficient deduction into the notation. These constraints force non-first-order, intensional, nested-quantifier, disjunctive, negation-heavy, modal forms. Hobbs claims the correct move is to drop all three constraints, thereby allowing a flat first-order notation suitable for inferential discourse interpretation. *(p.61)*

## Key Contributions
- **Ontological promiscuity**: take the universe of discourse to be a Platonic universe containing everything nameable — real, possible, impossible, nonexistent, abstract. `Exist(x)` is then a predicate, not a quantifier obligation. *(p.62)*
- **Nominalization operator `'`**: for every n-ary predicate `p` there is an (n+1)-ary `p'` whose first argument is the eventuality/condition `e` of `p(x₁,…,xₙ)` being true. Truth and existence of events/conditions are separated from truth-of-predication. *(p.62)*
- **Axiom schema (3)** linking `p` and `p'` by: `p(x₁,…,xₙ) ≡ (∃e) Exist(e) ∧ p'(e,x₁,…,xₙ)`. *(p.63)*
- **Transparency axiom**: a predicate `p` is transparent in its nth argument `x` iff `(∀e,…,x,…) p'(e,…,x,…) ∧ Exist(e) ⊃ Exist(x)` — equivalently `(∀…,x,…) p(…,x,…) ⊃ Exist(x)`. Otherwise `p` is opaque in that argument. *(p.63)*
- **Flat logical form**: a conjunction of atomic predications with outermost existential quantifiers, no functions, no functionals, no nested quantifiers, no disjunctions, no negations, no modal operators. *(p.62)*
- **Opaque adverbials** as predications over eventualities via nominalization — e.g., `almost'(E) ∧ man'(E,J)` rather than `almost(man)(J)`. Showed (p.64) the functional treatment can be recoded as a predicate in a suitably rich finite model.
- **De re/de dicto distinction** reframed: the neutral reading uses an existential over the Platonic universe inside `believe`; stronger *de re* readings add `know(J,R) ∧ wh'(R,S)` conjuncts expressing contextually-determined identification. *(p.64-65)* Knowledge-of-identity is conversational implicature, not literal meaning.
- **Frege puzzle (identity in intensional contexts)** handled by a `rw-identical` ("real-world identical") relation plus an axiom schema (17) that propagates substitution inside referentially transparent argument positions but not opaque ones. Three strategies discussed and rejected/modified: restrict Leibniz's Law via a belief operator (rejected for flatness), deny Platonic identity (second solution using `rw-identical`), or metonymic reinterpretation via abstract-object function α (Zalta/Frege/Montague variant). Hobbs prefers to mostly ignore the identity problem and invoke metonymic ruses only when interpretation breaks. *(p.66-68)*
- **Semantic stance**: semantics is a theory of the relation between language and world; simplicity of semantics is achieved by *choosing* a theory of the world that is already isomorphic to how we talk. *(p.68)*

## Study Design (empirical papers)
*Non-empirical — theory paper with illustrative NL examples. Section skipped.*

## Methodology
Argumentation-by-example in logical-form engineering. The paper:
1. Establishes criteria (close to English, syntactically simple). *(p.61)*
2. Rejects three prior constraints (ontological scruples, syntax-as-byproduct, deduction-as-notation). *(p.61)*
3. Extends Davidson's (1967) event-as-individual treatment of action sentences from verbs to *every* predication. *(p.62)*
4. Proposes the Platonic universe + `Exist` + `p/p'` nominalization apparatus. *(p.62-63)*
5. Addresses four historical objections in sequence (quantifiers, opaque adverbials, de re/de dicto, identity), with § 3-5 doing the work for adverbials, belief, and identity. Quantifiers handled separately in Hobbs 1983. *(p.63-67)*
6. Closes by situating the proposal on a "spectrum of semantics" between Fodor-style despair and trivially-isomorphic-world simplicity. *(p.68)*

## Key Equations / Statistical Models

Naïve representation of "A boy builds a boat":
$$
(\exists x, y)\; build(x, y) \wedge boy(x) \wedge boat(y)
$$
*(p.62)*

Target flat representation of "A boy wanted to build a boat quickly":
$$
(\exists e_1, e_2, e_3, x, y)\; Past(e_1) \wedge want'(e_1, x, e_2) \wedge quick'(e_2, e_3) \wedge build'(e_3, x, y) \wedge boy(x) \wedge boat(y)
$$
Where: `e_i` are eventualities in the Platonic universe, the primed predicates are nominalizations of the unprimed, `Past(e_1)` locates the wanting in past time. *(p.62)*

Equation (2) — event-splitting of "John runs":
$$
Exist(E) \wedge run'(E, JOHN)
$$
Where: `E` denotes the condition of John running; asserting `Exist(E)` commits to that condition obtaining in the real world. *(p.63)*

Axiom schema linking primed and unprimed predicates:
$$
(\forall x_1, \ldots, x_n)\; p(x_1, \ldots, x_n) \supset (\exists e)\, Exist(e) \wedge p'(e, x_1, \ldots, x_n)
$$
*(p.63)*

Converse direction:
$$
(\forall e, x_1, \ldots, x_n)\; Exist(e) \wedge p'(e, x_1, \ldots, x_n) \supset p(x_1, \ldots, x_n)
$$
*(p.63)*

Compressed biconditional — axiom schema (3):
$$
(\forall x_1, \ldots, x_n)\; p(x_1, \ldots, x_n) \equiv (\exists e)\, Exist(e) \wedge p'(e, x_1, \ldots, x_n)
$$
*(p.63)*

Logical form of "John worships Zeus" — sentence (1):
$$
Exist(E) \wedge worship'(E, JOHN, ZEUS)
$$
This implies `Exist(JOHN)` but not `Exist(ZEUS)` — `worship` is opaque in its second argument. *(p.63)*

Transparency axiom — a predicate `p` is transparent in argument `x` iff:
$$
(\forall e, \ldots, x, \ldots)\; p'(e, \ldots, x, \ldots) \wedge Exist(e) \supset Exist(x)
$$
Equivalently:
$$
(\forall \ldots, x, \ldots)\; p(\ldots, x, \ldots) \supset Exist(x)
$$
In the absence of such axioms, predicates are assumed **opaque**. *(p.63)*

Representation of sentence (4) (Thatcher/Channel-Tunnel/Mitterrand, with tense & nominalization stacking):
$$
Perfect(E_1) \wedge repeated(E_1) \wedge refuse'(E_1, GOVT, E_2) \wedge deny'(E_2, GOVT, E_3) \wedge veto'(E_3, MT, CT) \wedge at'(E_4, E_3, E_5) \wedge meet'(E_5, MT, PM) \wedge on'(E_5, 18MAY) \wedge Past(E_6) \wedge reveal'(E_6, NS, E_3) \wedge last\text{-}week(E_6)
$$
*(p.63)*

Opaque adverbial "John is almost a man" — functional treatment (rejected for flatness):
$$
almost(man)(J)
$$
*(p.64)*

Preferred flat representation:
$$
almost'(E) \wedge man'(E, J)
$$
Note: does not imply `man(J)` because `Exist(E)` is not asserted and `almost` is opaque. *(p.64)*

Equivalence axiom relating functionals to predicates — demonstration that functional `F` can be replaced by a predicate `q`:
$$
(\forall p, x)\; F(p)(x) \equiv (\exists e)\, q(e) \wedge p'(e, x)
$$
*(p.64)*

Interpretation scheme for the non-contradictory model: let `D` = class of finite sets built out of a finite set of urelements; constant `X` interpreted as `I(X) ∈ D`; monadic predicate `p` interpreted as `I(p) ⊆ D`; if `E` is such that `p'(E, X)`, then `I(E) = ⟨I(p), I(X)⟩`. Predicate `q` of predicates-into-predicates is then defined:
$$
q(E) \text{ is true iff there are } p, X \text{ with } I(E)=\langle I(p), I(X)\rangle \text{ and } F(p)(X) \text{ is true.}
$$
*(p.64)*

De dicto reading of "John believes a man at the next table is a spy" — sentence (5)/(8)/(10):
$$
believe(J, P) \wedge spy'(P, S)
$$
*(p.64-65)* (`(10)`; `(8)` is `(∃x) believe(J, spy(x))`, `(9)` is `believe(J, (∃x) spy(x))`, `(11)` adds `∧ believe(J,Q) ∧ at'(Q,S,T)` for explicit location knowledge.)

De re reading with knowledge-of-identity — sentence (5) decomposition (12):
$$
believe(J, P) \wedge spy'(P, S) \wedge believe(J, Q) \wedge at'(Q, S, T)
$$
De re representation (13a)/(13b):
$$
believe(J, P) \wedge spy'(P, S) \wedge Exist(Q) \wedge at'(Q, S, T) \wedge know(J, R) \wedge wh'(R, S)
$$
Where `wh'(R, S)` denotes the contextually-determined essential property identifying `S`. *(p.65)*

Frege puzzle — sentence (14)/(15)/(16):

"John believes the Evening Star is rising" (de dicto reading, eq. 16):
$$
believe(J, P_1) \wedge rise'(P_1, ES) \wedge believe(J, Q_1) \wedge Evening\text{-}Star'(Q_1, ES)
$$
Belief in Morning Star:
$$
believe(J, Q_2) \wedge Morning\text{-}Star'(Q_2, MS)
$$
Existence of both morning/evening star beliefs:
$$
Exist(Q_1) \wedge Exist(Q_2)
$$
Uniqueness of proper name "Evening Star":
$$
(\forall x, y)\; Evening\text{-}Star(x) \wedge Evening\text{-}Star(y) \supset x = y
$$
Platonic identity of Evening Star and Morning Star:
$$
(\forall x)\; Evening\text{-}Star(x) \equiv Morning\text{-}Star(x)
$$
*(p.66)*

`rw-identical` replacement for substitution-in-real-world — identity only in the real world:
$$
rw\text{-}identical(ES, MS)
$$
Equivalently:
$$
(\forall x, y)\; Morning\text{-}Star(x) \wedge Evening\text{-}Star(y) \supset rw\text{-}identical(x, y)
$$
*(p.66-67)*

Substitution-under-`rw-identical` — axiom schema (17):
$$
(\forall e_1, e_3, e_4, \ldots)\; p'(e_1, \ldots, e_3, \ldots) \wedge rw\text{-}identical(e_3, e_4) \supset (\exists e_2)\, p'(e_2, \ldots, e_4, \ldots) \wedge rw\text{-}identical(e_2, e_1)
$$
Where `e_3` is the kth argument of `p` and `p` is referentially transparent in its kth argument. *(p.67)* Substitution of `rw-identicals` yields an `rw-identical` condition, not the same condition — matching the intuition that "John's being a man" and "John's being a mammal" are not the same eventuality.

Equivalence axioms for `rw-identical`:
$$
(\forall x)\; rw\text{-}identical(x, x)
$$
$$
(\forall x, y)\; rw\text{-}identical(x, y) \supset rw\text{-}identical(y, x)
$$
$$
(\forall x, y, z)\; rw\text{-}identical(x, y) \wedge rw\text{-}identical(y, z) \supset rw\text{-}identical(x, z)
$$
Leibniz's Law restricted:
$$
(\forall e_1, e_2)\; rw\text{-}identical(e_1, e_2) \supset (Exist(e_1) \equiv Exist(e_2))
$$
*(p.67)*

Uniqueness of proper name (restated under `rw-identical`):
$$
(\forall x, y)\; Evening\text{-}Star(x) \wedge Evening\text{-}Star(y) \supset rw\text{-}identical(x, y)
$$
*(p.67)*

Uniqueness of a functional value (functions recoded):
$$
(\forall x, y, z)\; father(x, z) \wedge father(y, z) \supset rw\text{-}identical(x, y)
$$
*(p.67)*

Third-solution / metonymic treatment of (14) — function `α(actual_entity, cognizer, condition)` returning an abstract entity/sense — sentence (18):
$$
believe(J, P_1) \wedge rise'(P_1, \alpha(ES, J, Q_1)) \wedge believe(J, Q_1) \wedge Evening\text{-}Star'(Q_1, ES)
$$
Key consequence: `α(ES, J, Q_1) ≠ α(ES, J, Q_2)` where `Morning-Star'(Q_2, ES)` — different conditions yield different abstract objects, blocking intersubstitutivity. *(p.67-68)*

## Parameters

Paper is not parameterized in the empirical sense. The following "parameters" are structural choices/axiom-schema markers the notation uses.

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Universe of discourse | D (Platonic universe) | — | all nameable entities (real + possible + impossible + abstract) | — | 62 | Includes logically impossible entities like "the condition John believes when he thinks 6+7=15" |
| Existence predicate | `Exist` | unary predicate | — | truth-valued on Platonic entities | 62-63 | Replaces existential-quantifier commitment; `Exist(x)` = x exists in the real world |
| Nominalization arity shift | `p → p'` | — | primed predicate adds 1 argument (eventuality) | n-ary → (n+1)-ary | 62 | First argument of `p'` is the condition/eventuality `e` |
| Transparency default | opacity | boolean | opaque | transparent/opaque per predicate argument | 63 | Absent an axiom, predicates are opaque; transparency must be stated |
| Model dimension (adverbial model) | `D` | finite sets of finite urelements | — | — | 64 | Just enough structure to interpret `F(p)(x)` predicates as `q(E) ∧ p'(E, x)` |
| `rw-identical` relation | `rw-identical` | binary predicate | — | equivalence relation | 66-67 | Real-world identity; supports substitution only under (17) |
| `wh'` placeholder predicate | `wh'` | binary predicate | — | contextually-determined essential property | 65 | Represents contextually-determined identification criterion ("who/what is it") |
| Abstract-object function | `α(x, cognizer, condition)` | ternary function | — | returns sense/intension | 67-68 | Zalta/Frege variant: different conditions → different abstract objects |

## Effect Sizes / Key Quantitative Results

*Non-empirical. No effect sizes.*

## Methods & Implementation Details
- **Flat logical form construction**: every NL sentence maps to a conjunction of atomic predications existentially quantified at widest scope. Predicates are identical or nearly identical to NL morphemes. No functions, functionals, nested quantifiers, disjunction, negation, modal operators. *(p.62)*
- **Davidson (1967) extension**: events are individuals; the extension is to treat *every* predication (not just action verbs) as involving an eventuality. *(p.62)*
- **Predicate-nominalization discipline**: for each `p` produce `p'`. `run(JOHN)` and `run'(E, JOHN)` are systematically related via axiom schema (3). *(p.62-63)*
- **Assertion vs. content split**: a sentence's content is `p'(e, ...)` and its assertion is `Exist(e)`. This decoupling is useful when the content is in doubt or embedded (e.g., in counterfactuals, indirect proofs). *(p.63)*
- **Transparency marking**: transparency is per-argument per-predicate. Declared via the axiom `(∀...,x,...) p(...,x,...) ⊃ Exist(x)`. Opacity is the default. *(p.63)*
- **Adverbials**: opaque adverbial `almost` becomes a unary predicate `almost'` on the eventuality. Requires a rich-enough model (finite sets over finite urelements) to define `q(E)` such that `(∀p, x) F(p)(x) ≡ (∃e) q(e) ∧ p'(e, x)`. *(p.64)*
- **Belief reports**: `believe(J, P)` where `P` is a condition that may or may not exist in the real world. De re reading adds `know(J, R) ∧ wh'(R, S)` as *conversational implicature*, not literal meaning. FBI-agent example shows a continuum of belief states. *(p.64-65)*
- **Contextual identification / `wh'`**: the essential identifying property is context-dependent (Kripke-at-conference example). `wh'` is a place-holder for whatever property does the identifying in that context. *(p.65)*
- **Excluded-middle handling**: `married(S)` is an abbreviation for `(∃E) married'(E, S) ∧ Exist(E)`. For merely-possible `S`, both `married(S)` and `unmarried(S)` are false — the falsity is about existence of `S`, not marital status. Primed predicates don't raise excluded-middle problems. *(p.65)*
- **Frege puzzle resolution via `rw-identical`**: `ES ≠ MS` in the Platonic universe; they are `rw-identical`. Substitution inside transparent argument positions is mediated by axiom (17), producing an `rw-identical` condition rather than the same condition. *(p.66-67)*
- **Functions become predicates**: `father` as a function is replaced by a predicate with a uniqueness axiom under `rw-identical`. *(p.67)*
- **Metonymic ruse**: rather than paying the `rw-identical` cost everywhere, keep (16) as the default representation for (14) and invoke a metonymic reinterpretation to an abstract entity `α(ES, J, Q_1)` only when interpretation breaks. *(p.67-68)*
- **Quantifier handling deferred**: universally-quantified variables reified as typical elements of sets; existential quantifiers inside universal scope handled via Skolem-like dependency functions; quantifier structure encoded as indices on predicates. Treated in detail in Hobbs 1983 ("An Improper Treatment of Quantification in Ordinary English"). *(p.63)*

## Figures of Interest
No figures. The paper is all text + inline formulas.

## Results Summary
The paper demonstrates, by worked examples, that the flat first-order nonintensional notation with a Platonic universe can represent (and support inference over):
- Tensed and adverbially-modified predications, including `Perfect`, `Past`, `repeated`, `at`, `meet`, `on`, `last-week` stacked on a single veto event. *(p.63)*
- Opaque adverbials without functional types. *(p.64)*
- The de re / de dicto continuum of belief reports including the FBI-agent progression and the Rotary-Club variant where only partial identification holds. *(p.64-65)*
- Frege's Morning-Star / Evening-Star puzzle via `rw-identical`, at an axiomatic cost *(p.66-67)* or via metonymic reinterpretation with an abstract-object function *(p.67-68)*.

## Limitations
- **Referential opacity of sentence-level interpretation**: the metonymic third approach makes noun-phrase interpretation depend on the embedding context (intensional → metonymic; extensional → non-metonymic), partially violating the compositionality the paper pains to preserve. *(p.68)*
- **`rw-identical` reasoning is "very cumbersome"**: common equality reasoning becomes equality-modulo-`rw-identical`, which is computationally heavier than simple substitution. *(p.67)*
- **Very fine-grained individuation of eventualities**: we cannot identify "John is almost a man" with "John is almost a mammal" even if `man ⊂ mammal`, which forces individuation of conditions by very fine-grained criteria. *(p.64)*
- **Quantifier treatment omitted**: only three of the four original problems (quantifiers, opaque adverbials, de re/dicto, identity) are handled in this paper. Quantifiers handled in Hobbs 1983. *(p.63)*
- **Metonymy claimed to be irregular, not systematic**: Hobbs prefers to treat metonymy as occurring irregularly; this is a substantive empirical claim not argued for in detail. *(p.68)*
- **Excluded-middle argument is defensive**: relies on the position that `married(S)` for merely-possible `S` is legitimately false; some readers will prefer a three-valued or truth-value-gap solution. *(p.65)*

## Arguments Against Prior Work
- **Against ontological parsimony (Quine 1953/1956)**: Quine's argument that we should adopt "the simplest conceptual scheme" is itself non-simple — Quine admits simplicity has a "double or multiple standard". Simplicity of the *rules* can be achieved by *multiplying kinds of entities*, allowing anything referable-to-by-a-noun-phrase to be an entity. *(p.61)* Representational difficulties go away if you reject ontological chastity.
- **Against syntactic-explanation constraint**: requiring that syntactic behavior (e.g., of count vs. mass nouns) fall out of ontological structure at no cost is fine; but if the cost is "great complication in statements of discourse operations", that cost outweighs the benefit. *(p.61)*
- **Against efficient-deduction-as-notation (Quillian 1968, Simmons 1973, Hendrix 1975, Schmolze & Brachman 1982, Hayes 1979, Moore 1980)**: building control information into the notation ties the theory to a particular implementation and reduces its generality. One should first empirically determine common inference classes, then optimize. *(p.62)*
- **Against intensional logics / scope-ambiguity encodings of de re/de dicto (Quine 1956)**: the scope maneuver (`(∃x) believe(J, spy(x))` vs. `believe(J, (∃x) spy(x))`) fails to cover the case where John believes someone is a spy without any identifying knowledge. *(p.64)*
- **Against belief-as-operator with restricted substitution (unnamed proponents)**: purely syntactic approaches to substitution under `believe` work as axiomatic syntax but fail to construct a semantics; they are forced back to the metonymic (third) approach when you try. *(p.66)*
- **Against Montagovian obligatory-intension**: Montague's move to always refer to intensions (with meaning postulates making extensional predicates equivalent) over-generalizes metonymy; intensional and extensional predicates must still be distinguished explicitly. *(p.67)*
- **Against Fodor 1980 "methodological solipsism" despair about semantics**: Fodor's view is that semantics = all of science, hence hopeless. Hobbs: by *adopting a theory of the world that is nearly isomorphic to how we talk*, semantics becomes nearly trivial and tractable. *(p.68)*
- **Implicit critique of Leibniz's Law as unrestricted**: Leibniz intersubstitutivity fails in intensional contexts; `rw-identical` restricts substitution to transparent argument positions. *(p.66-67)*

## Design Rationale
- **Why first-order**: discourse interpretation is inferential manipulation of logical expressions. First-order predicate calculus has well-understood, general inference mechanisms. *(p.61)*
- **Why flat (no nested quantifiers, disjunctions, negations, modals)**: to minimize the number of rule shapes needed for discourse interpretation. Rules operating on flat conjunctions of atomic predications are simpler than rules operating on arbitrary formula trees. *(p.62)*
- **Why Platonic universe**: lets reference and existence be orthogonal. `John worships Zeus` references Zeus without committing to Zeus existing. *(p.62)*
- **Why primed predicates**: gives a handle (`e`) by which higher predications (tense, modality, causation, propositional attitudes, pronominal reference, nominalization) can grasp a predication. A similar move is used in many AI systems. *(p.62)*
- **Why nominalization and existence are orthogonal**: "John's running tired him out" presumes the existence of an event; "John may run" doesn't. Splitting content from assertion handles this. *(p.62)*
- **Why opaque-by-default**: most embedded positions in natural language do not imply existence; making transparency optional catches only the cases that need it. *(p.63)*
- **Why `rw-identical` rather than identity**: preserves fine-grained individuation of eventualities (so `almost-a-man` ≠ `almost-a-mammal`) while admitting the Frege-style real-world identity `ES = MS` as an external fact. *(p.66-67)*
- **Why `wh'` rather than explicit identification conjuncts**: identification is context-dependent; a placeholder predicate leaves specification to the context of interpretation. *(p.65)*
- **Why not Montagovian uniform intensional**: makes the intensional/extensional distinction semantically heavier without the discourse-processing benefit. *(p.67)*
- **Why resist efficient-deduction-in-notation**: it trades generality for optimization before the target inference distribution is known. *(p.62)*
- **Why prefer metonymic ruse to `rw-identical` by default**: keeps the common case cheap; invoke metonymy only when interpretation breaks. *(p.67-68)*
- **Why the Platonic universe can contain impossible entities**: so we can represent "the condition John believes to exist when he believes 6+7=15" without breaking down. *(p.62, footnote 2)*

## Testable Properties
- **(T1)** For every NL predicate `p` there exists a primed predicate `p'` with arity `arity(p)+1`, and `p(x₁,…,xₙ) ≡ (∃e) Exist(e) ∧ p'(e, x₁,…,xₙ)`. *(p.63)*
- **(T2)** A predicate `p` is transparent in argument `x` iff `p(…,x,…) ⊃ Exist(x)`. Without such an axiom, `p` is opaque in `x`. *(p.63)*
- **(T3)** Logical form is a single conjunction of atomic predications with outermost existential quantifiers — no functions, functionals, nested quantifiers, disjunction, negation, modal operators appear inside. *(p.62)*
- **(T4)** For any eventuality `E`, `Exist(E)` is a truth-valued predication; falsity of `Exist(E)` does not entail falsity of predications about `E` (example: `married'(E, S) ∧ ¬Exist(S)` is consistent). *(p.65)*
- **(T5)** `rw-identical` is a reflexive, symmetric, transitive relation on the Platonic universe. *(p.67)*
- **(T6)** `rw-identical(e₁, e₂) ⊃ (Exist(e₁) ≡ Exist(e₂))`. *(p.67)*
- **(T7)** Substitution under `rw-identical` in a transparent argument position yields an `rw-identical` condition, not the same condition. *(p.67)*
- **(T8)** De re / de dicto distinction is conversational implicature (knowledge of `wh'`-identification), not literal meaning; the `wh'`-conjunct can be absent even for genuinely *de re* uses (Rotary-Club case). *(p.65)*
- **(T9)** In the Platonic universe, `Evening-Star ≢ Morning-Star`; they are `rw-identical` only. *(p.66)*
- **(T10)** An abstract-object function `α(actual, cognizer, condition)` must return distinct values for distinct conditions: `α(ES, J, Q₁) ≠ α(ES, J, Q₂)` when `Q₁ ≠ Q₂`. *(p.67-68)*
- **(T11)** Monotonic/ordinary equality reasoning can be recovered as reasoning about `rw-identical`, at a cost in inference complexity. *(p.67)*
- **(T12)** Eventualities are individuated at very fine grain — non-coextensive predicates give non-identical eventualities even when the objects involved are the same. *(p.64)*

## Relevance to Project
Hobbs's proposal is a **direct ancestor of the propstore semantic layer**. Several principles in the project CLAUDE.md have explicit antecedents here:

- **Concepts-as-predicates-plus-eventualities**: Hobbs's primed predicates `p'(e, x₁,…,xₙ)` are the shape we need for frame-element-style concept storage. The extra argument `e` plays the role propstore gives to context / eventuality / condition.
- **Context as first-class logical object**: the condition-of-truth `e` is Hobbs's analog to McCarthy's `ist(c, p)` context formalization, which propstore names in `CLAUDE.md`. Hobbs's `e` is the *per-predication* instance; McCarthy's `c` is a more stable structure over many predications.
- **Honest ignorance over fabricated confidence**: Hobbs's `Exist(e)` machinery lets a condition be stored without committing to its reality. This aligns with propstore's principle of never collapsing disagreement in storage. A condition-without-`Exist` is a candidate; `Exist` is asserted only when evidence supports it.
- **Transparent/opaque argument positions**: directly informs how propstore's concept/stance layer should handle inheritance of existence through argument positions — e.g., a stance conjuncting over believed-but-unverified entities should mark the positions in which existence does *not* propagate.
- **Metonymy is irregular**: supports propstore's preference to keep heuristic/LLM metonymic reinterpretations as **proposal artifacts**, never hardened into the source branch.
- **Flat conjunction as storage format**: propstore's claims/concepts/stances are essentially flat atomic predications; Hobbs supplies the formal justification.
- **`rw-identical` ≠ logical identity**: crisp motivation for keeping multiple rival normalizations of a concept without collapsing them — two concepts can be `rw-identical` (same real-world referent) while remaining distinct entities in storage with different provenance, conditions, and supporting evidence.

Implementation implications:
- Concept registry entries should expose an `eventuality` slot analogous to Hobbs's `e`.
- Existence should be a storable, queryable predicate over concept/claim instances, not a trivial precondition of being present in the store.
- Stances should be representable as flat conjunctions of primed-style predications.
- Rival normalizations should be stored as `rw-identical`-related, not merged.

## Open Questions
- [ ] How does Hobbs 1985's eventuality match propstore's current `KindType.EVENT` / `TIMEPOINT` distinction, especially given CLAUDE.md notes that `TIMEPOINT` maps to `z3.Real` but is "not valid for parameterization or dimensional algebra"? Hobbs's `e` conflates time, condition, and event — propstore may want a finer taxonomy.
- [ ] Does propstore have an `Exist`-style predicate at the claim layer, or is existence implicit in storage? (CLAUDE.md says storage is immutable except by migration, implying existence is not separately asserted.)
- [ ] Hobbs handles quantifiers via reification and dependency functions (deferred to Hobbs 1983) — is propstore's claim/stance layer equipped for that level of quantifier reification?
- [ ] How does the `wh'` placeholder (contextually-determined identification) interact with lemon-model linguistic grounding in the propstore concept layer?
- [ ] Does propstore's ASPIC+ bridge need a notion of `rw-identical` to handle co-referring concepts without collapsing them?

## Collection Cross-References

### Already in Collection
- (none — Hobbs cites McCarthy 1977 and Moore 1980, but the collection holds later works by those authors: McCarthy 1980/1993/1997 and Moore 1985, which are distinct citations.)

### New Leads (Not Yet in Collection)
- **Davidson (1967)** — "The Logical Form of Action Sentences", in *The Logic of Decision and Action*. The paper Hobbs generalizes: events-as-individuals for action sentences. **Primary lead.**
- **Hobbs (1983)** — "An Improper Treatment of Quantification in Ordinary English", ACL-21. Companion paper handling the quantifier problem Hobbs 1985 defers. **Primary lead.**
- **McCarthy (1977)** — "Epistemological Problems of Artificial Intelligence", IJCAI. Earlier McCarthy paper credited for a similar nominalization technique; precedes the 1993 context formalization already in the collection.
- **Moore (1980)** — "Reasoning about Knowledge and Action", SRI Tech Report 191. Earlier Moore paper on possible-worlds belief representation.
- **Moore & Hendrix (1982)** — "Computational Models of Belief and the Semantics of Belief Sentences". Source of the spy example and alternative framework for belief.
- **Frege (1892)** — "On Sense and Nominatum". Foil for the Morning-Star/Evening-Star puzzle.
- **Quine (1953)** — "On What There Is" and **Quine (1956)** — "Quantifiers and Propositional Attitudes". Ontological-parsimony and scope-ambiguity positions Hobbs rejects.
- **Zalta (1983)** — *Abstract Objects: An Introduction to Axiomatic Metaphysics*. Substrate for the metonymic third-solution to Frege's puzzle.
- **Hayes (1979)** — "The Logic of Frames". Frames-as-axioms-with-control argument, adjacent to Hobbs's anti-efficient-deduction position.
- **Fodor (1980)** — "Methodological Solipsism Considered as a Research Strategy in Cognitive Psychology". The despair-about-semantics view Hobbs rebuts.
- **Reichenbach (1947)** — *Elements of Symbolic Logic*. Functional treatment of opaque adverbials Hobbs rejects.

### Supersedes or Recontextualizes
- (none — Hobbs 1985 builds on Davidson 1967 but does not supersede any collection paper.)

### Cited By (in Collection)
- (none — searched for "Hobbs 1985"/"Hobbs 1983"/"Hobbs, Jerry" across all collection notes and citations; Forbus_1993 cites Hobbs 1983/1989 and Hobbs & Moore 1985 anthology; Pustejovsky_1991 cites Hobbs 1987/1988. Neither cites Hobbs 1985 Ontological Promiscuity specifically.)

### Conceptual Links (not citation-based)

**Semantic substrate — context / eventuality / condition:**
- [Notes on Formalizing Context](../McCarthy_1993_FormalizingContext/notes.md) — Strong. McCarthy's `ist(c, p)` context-as-first-class-object is exactly Hobbs's eventuality-as-first-class-entity move at a larger grain. Hobbs's `e` is the per-predication instance; McCarthy's `c` is a stable structure over many predications. Together they give propstore a two-tier context model: per-claim eventualities nested inside stable context objects. Different formalisms converging on the same architectural move — contexts/conditions must be logical objects, not metadata.
- [Microtheories](../Kallem_2006_Microtheories/notes.md) — Strong. Microtheories extend McCarthy's contexts with inheritance and lifting rules; the Hobbs-eventuality / microtheory pairing is the direct antecedent of propstore's context-qualified claim storage.

**Scientific discourse / non-commitment / provenance:**
- [Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications](../Clark_2014_Micropublications/notes.md) — Strong. Hobbs's separation of `Exist(e)` from `p'(e, ...)` is the logical-form analog of Clark's separation of a claim's propositional content from its evidence and attribution. Both resist collapsing reference onto commitment. Propstore's "never collapse disagreement in storage" principle has a philosophical precursor in Hobbs (storing conditions without asserting their existence) and a scientific-discourse precursor in Clark (storing claims without collapsing argumentative structure).

**Frame semantics / concepts-as-structured-entities:**
- [Frame Semantics](../Fillmore_1982_FrameSemantics/notes.md) — Strong. Hobbs's primed predicates reify the event so that modifiers and adjuncts can attach as predications over it — structurally the same move Fillmore makes with frame elements. Hobbs supplies the logical-form mechanics; Fillmore supplies the conceptual apparatus (frames as cognitive-linguistic schemata). Propstore's concept layer needs both: the formal shape (Hobbs) and the frame-theoretic grounding (Fillmore).
- [The Berkeley FrameNet Project](../Baker_1998_BerkeleyFrameNet/notes.md) — Moderate. FrameNet operationalizes Fillmore's frames as a database of predicate-argument structures; Hobbs's primed predicates are the logical-form shape that such a database entries take when reified for inference.

**Lexical semantics / generative & argument-selection machinery:**
- [The Generative Lexicon](../Pustejovsky_1991_GenerativeLexicon/notes.md) — Strong. Pustejovsky's qualia structure internally structures concepts (formal, constitutive, telic, agentive); Hobbs's `p/p'` pair externalizes the event/condition as a handle. The two are complementary: qualia structure tells us what a concept is made of; Hobbs's nominalization tells us how it participates in discourse predications. Propstore's concept layer should carry both — internal qualia and external eventuality handles.
- [Thematic Proto-Roles and Argument Selection](../Dowty_1991_ThematicProtoRoles/notes.md) — Moderate. Dowty's proto-roles decompose thematic roles into graded entailment clusters; Hobbs's primed predicates expose the argument slots of `p'` as first-order positions where such entailments can be stated as axioms. Both are graded-categorical-refusal moves: Dowty refuses discrete role categories, Hobbs refuses ontological parsimony. Same methodological instinct applied at different levels.

**Ontology lexicalization:**
- [Ontology Lexicalization: The lemon Perspective](../Buitelaar_2011_OntologyLexicalizationLemon/notes.md) — Moderate. Lemon formally separates lexical entries from ontological entities; Hobbs's Platonic universe + `Exist` is a logic-level precursor to that separation. In Hobbs, a linguistic expression can refer to an entity without that entity existing in the real world; in lemon, a lexical entry can reference an ontological concept without committing to one specific denotation. Both refuse to collapse word onto world.

## Related Work Worth Reading
- **Davidson 1967** "The Logical Form of Action Sentences" — the event-as-individual move Hobbs generalizes. *(reference [2])*
- **Hobbs 1983** "An Improper Treatment of Quantification in Ordinary English" — companion paper handling the quantifier problem. *(reference [7])*
- **McCarthy 1977** "Epistemological Problems of Artificial Intelligence" — early context/belief formalization Hobbs credits. *(reference [8])*
- **Moore & Hendrix 1982** "Computational Models of Belief and the Semantics of Belief Sentences" — source of the de re spy example. *(reference [11])*
- **Frege 1892** "On Sense and Nominatum" — Hobbs's foil on the Evening-Star puzzle. *(reference [4])*
- **Quine 1953** "On What There Is" and **Quine 1956** "Quantifiers and Propositional Attitudes" — the ontological-parsimony and scope-ambiguity positions Hobbs rejects. *(references [13], [14])*
- **Zalta 1983** *Abstract Objects* — the abstract-objects-as-intensions approach Hobbs draws on for the metonymic treatment. *(reference [18])*
- **Hayes 1979** "The Logic of Frames" — argues frame representations can be axiomatized as predicate calculus with a control component; adjacent to Hobbs's anti-efficient-deduction position. *(reference [5])*
- **Reichenbach 1947** *Elements of Symbolic Logic* — functional treatment of opaque adverbials Hobbs rejects. *(reference [15])*
- **Fodor 1980** "Methodological Solipsism" — the despair-about-semantics view Hobbs rebuts. *(reference [3])*
