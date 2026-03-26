---
title: "Using Z3 to Verify Inferences in Fragments of Linear Logic"
authors: "Alen Docef, Radu Negulescu, Mihai Prunescu"
year: 2023
venue: "7th Symposium on Working Formal Methods (FROM 2023), EPTCS 389"
doi_url: "https://doi.org/10.4204/EPTCS.389.2"
pages: "11-25"
---

# Using Z3 to Verify Inferences in Fragments of Linear Logic

## One-Sentence Summary
Presents a practical Z3-based template for verifying whether candidate Gentzen-style inference rules are derivable from a base set of linear-logic rules, then applies it to MLL+Mix and MILL to prove some derived rules, reject others, and expose memory limits on harder checks. *(p.1-10)*

## Problem Addressed
The paper asks how to mechanically validate derived inference rules for fragments of linear logic without building a bespoke proof-search engine for each fragment. The authors want a reusable solver-based pattern that works directly over Gentzen-style sequent rules and can tell whether a proposed rule follows from an existing rule set. *(p.1-3)*

Linear logic rules can be subtle, and switching from classical logic intuitions to the proof-theoretic setting is error-prone. The paper proposes to flatten that learning curve by encoding inference-rule validity as a satisfiability check in Z3. *(p.2, p.10)*

## Key Contributions
- Defines a general Z3 encoding pattern for Gentzen-style inference rules using formulas, contexts, and Boolean predicates/functions such as `entails`, `tensor`, and `lollipop`. *(p.2-3)*
- Shows how to verify a candidate derived rule by adding its negation to a solver already containing the base rules and interpreting `unsat` as validity of the candidate rule. *(p.2-4)*
- Applies the pattern to the MLL+Mix fragment, proving several derived rules, identifying non-derivable variants, and extending the theory with contraction and empty-context conventions. *(p.4-7)*
- Applies the same pattern to MILL, proving modus ponens, internal composition, and several dual/par/tensor properties while also documenting cases where Z3 runs out of memory. *(p.7-10)*
- Provides complete Python/Z3 listings for the core encodings. *(p.10-14)*

## Methodology
The workflow is uniform across fragments. Start from a base set of inference rules. Encode each rule as a universally quantified Z3 formula over sorts for formulas and contexts. To test whether a new rule is derivable, add the negation of that candidate rule to the solver together with the base rules. If the result is `unsat`, the candidate rule follows from the base set; if the result is `sat`, the candidate rule does not follow, and the returned model witnesses a counterexample. The paper then reuses this pattern for MLL+Mix and MILL by changing the rule vocabulary and operators. *(p.2-4, p.7-10)*

## Formal Setup

### Sequents and Rule Shape
A rule is treated as a Gentzen-style implication from sequents in the antecedent to a sequent in the conclusion:

$$
\frac{\Gamma_1 \vdash A_1 \quad \Gamma_2 \vdash A_2 \quad \ldots \quad \Gamma_n \vdash A_n}{\Gamma \vdash A}
$$

Each `\Gamma_i \vdash A_i` is a sequent, where `\Gamma_i` is a context and `A_i` is a formula. The rule states that if all antecedent sequents hold, then the conclusion sequent holds. *(p.2)*

The same rule can be read as an implication over Boolean-valued predicates:

$$
(\Gamma_1 \vdash A_1) \land (\Gamma_2 \vdash A_2) \land \ldots \land (\Gamma_n \vdash A_n) \rightarrow (\Gamma \vdash A)
$$

This is the shape encoded into Z3. *(p.2)*

### Z3 Vocabulary
Section 2 introduces:
- a solver `ll` that stores the base rules and checks consistency *(p.2-3)*
- a sort `F` for formulas and contexts/multisets of formulas *(p.2-3)*
- a Boolean-valued function `entails : F × F -> Bool` to model the turnstile *(p.2-3)*
- operators such as `tensor` and `lollipop` as functions `F × F -> F` *(p.2-3)*
- universally quantified variables over formulas/contexts *(p.2-3)*

### Derived-Rule Verification Pattern
To verify a candidate rule `r`, add `Not(r)` to the existing base rules and check satisfiability:

$$
\text{base-rules} \land \neg r
$$

- If Z3 returns `unsat`, `r` is a consequence of the base rule set. *(p.3)*
- If Z3 returns `sat`, the candidate rule is not derivable from the current base rules, and a model can witness the failure. *(p.3-4)*

## Key Equations and Encodings

$$
entails(\Gamma, A)
$$

Represents the sequent `\Gamma \vdash A`. When the antecedent context is empty, the paper sometimes abbreviates this with a unary predicate such as `provable(A)`. *(p.2, p.4, p.7)*

$$
tensor(F, F) : F \times F \to F
$$

Binary constructor for multiplicative conjunction. It appears both in the base-rule encodings and in derived-rule checks such as modus ponens-style properties. *(p.2-3, p.7-8)*

$$
lpop(F, F) : F \times F \to F
$$

Binary constructor for linear implication/lollipop. The paper uses it to express rules such as the derived modus ponens pattern in linear logic. *(p.2-3, p.7-8)*

$$
provable(A)
$$

Unary predicate used in the MLL+Mix setting to model an empty-left-context sequent `\vdash A`. *(p.4)*

## Implementation Details
- Represent formulas and contexts uniformly with a single Z3 sort `F`; then add semantic structure through uninterpreted functions such as `tensor`, `lollipop`, `comma`, `par`, and `dual`. *(p.2-5, p.7-9)*
- Encode each inference rule as a universally quantified implication, so the solver can reason over arbitrary formulas/contexts rather than a fixed ground instance. *(p.2-5, p.7-9)*
- Keep the base rules in a persistent solver and test each candidate rule by pushing in its negation as an additional constraint. *(p.3-4, p.5-6, p.7-10)*
- Use `unsat` as the success criterion for a derived rule and `sat` as a witness that the rule does not follow from the current theory. *(p.3-4)*
- Check the consistency of the given base rule set separately from the candidate-rule test; a spurious `unsat` caused by an inconsistent base theory would invalidate the interpretation. *(p.4)*
- For MLL+Mix, add an explicit operator `comma` to represent multiset union of formulas/contexts and axiomatize its associativity and commutativity. *(p.4-5)*
- For MILL, model equivalence-style rules by using biconditional constraints rather than one-way implications, since some rules behave like logical equivalences. *(p.7-8)*
- The appendix provides runnable Python/Z3 fragments showing the exact declaration order and verification calls (`print(ll.check())`, `print(ll.model())`). *(p.10-14)*

## Worked Results: MLL+Mix
- The paper starts from a rule set for MLL+Mix and shows the set is consistent by obtaining `sat` when checking the theory without a negated candidate rule. *(p.5-6)*
- Several derived rules are proved by the `unsat` method, including examples involving `1`, `⊥`, `mix`, and tensor/lollipop interactions. *(p.5-6)*
- Several alternate formulations of Mix are shown not to hold, because the negated rules are satisfiable in the encoded theory. *(p.6)*
- Adding a contraction-style rule over the `comma` operator yields a stronger theory, and the extended theory proves `⊢ ⊥`. *(p.6-7)*
- The paper also discusses adding an empty-conclusion/empty-context style axiom, though the corresponding Z3 implementation is left incomplete. *(p.7)*

## Worked Results: MILL
- Starting from the eight core MILL rules, the paper verifies a modus-ponens-style rule by adding its negation and obtaining `unsat`. *(p.7-8)*
- It then verifies an internal-composition rule of the form `(X -o Y) ⊗ (Y -o Z) ⊢ (X -o Z)`. *(p.8-9)*
- The authors introduce `dual` and `par` via new rules and check several of their properties one by one. *(p.8-10)*
- Some dual/par/tensor properties are proved (`unsat`), while other checks run out of memory, so the paper treats those results as inconclusive rather than proven false. *(p.8-10)*
- The paper summarizes the derived MILL rules as a theorem and explicitly distinguishes them from claims that were not resolved due to solver limits. *(p.10)*

## Experimental Setup
- The implementation language is Python 3.9.13 with the Z3 Python API. *(p.10)*
- Successful runs are reported on a Rocky Linux system with an Intel Xeon E7-4870, 30 MB cache, and 1024 GB RAM. *(p.10)*
- Successful experiments finished in a few seconds; experiments that exhausted memory were not completed. *(p.10)*

## Figures and Listings of Interest
- **Listing 1 (p.10):** Minimal Python/Z3 encoding for the general rule-verification template from Section 2.
- **Listing 2 (p.10-11):** Full MLL+Mix encoding, including `comma`, associativity/commutativity axioms, base rules, derived-rule checks, and contraction.
- **Listing 3 (p.12-13):** Full MILL encoding, including `dual`, `par`, and the corresponding derived-rule verification checks.

## Results Summary
- The Z3 template successfully validates several derived inference rules in both MLL+Mix and MILL. *(p.5-10)*
- The method can also falsify candidate rules by producing satisfiable negations, so it is not just a theorem-confirmation trick. *(p.3-4, p.6)*
- Solver resource limits are a real practical boundary: some plausible dual/par/tensor properties in MILL caused out-of-memory failures instead of proofs or counterexamples. *(p.8-10)*
- The authors argue the same approach should transfer to other proof systems and even other provers such as Lean, not just the specific linear-logic fragments in the paper. *(p.10)*

## Limitations
- The approach is demonstrated only on selected fragments of linear logic, not on full linear logic. *(p.1, p.10)*
- Some target rules lead Z3 to run out of memory or time, so the procedure is not uniformly decisive on harder properties. *(p.8-10)*
- The paper does not claim completeness of the method as a proof procedure for all target fragments; it is a practical verification template. *(p.1, p.10)*
- One proposed extension involving empty sequents is discussed conceptually but left incomplete in the Z3 implementation. *(p.7)*

## Arguments Against Prior Work
- The authors position their work against the difficulty of hand-validating inference rules in linear logic, especially when moving from familiar classical intuitions to proof-theoretic fragments. *(p.2)*
- They note that theorem provers such as Lean have been used on Gentzen-style systems before, but they were not aware of prior work using a theorem prover specifically for this style of linear-logic inference-rule modeling. *(p.2)*
- The paper implicitly argues that many textbook or literature-presented rule variants should not be trusted without formal verification, because some apparently natural variants turn out not to follow from the encoded base theories. *(p.5-6, p.8-10)*

## Design Rationale
- **Why Z3?** Because the authors want a flexible SMT-based platform where inference-rule validity can be reduced to satisfiability of formulas encoding rules and their negations. *(p.1-3)*
- **Why encode rules as universally quantified implications?** This mirrors the sequent-calculus reading of inference rules and makes the same template reusable across fragments. *(p.2-3)*
- **Why check the negation of a candidate rule?** Because `unsat` gives a simple and uniform criterion for derivability from the existing base rule set. *(p.3-4)*
- **Why introduce operators like `comma`, `par`, and `dual` as uninterpreted functions plus axioms?** This keeps the encoding modular and lets the solver reason from explicit algebraic/proof-theoretic constraints rather than a baked-in semantics. *(p.4-5, p.8-9)*
- **Why separate consistency checking of the base theory from candidate-rule verification?** To avoid misreading an inconsistent base theory as a successful proof of the candidate rule. *(p.4)*

## Testable Properties
- If `base-rules ∧ ¬r` is `unsat`, then candidate rule `r` is derivable from the encoded rule set. *(p.3-4)*
- If `base-rules ∧ ¬r` is `sat`, then `r` is not derivable from the encoded rule set, and the returned model is a counterexample witness. *(p.3-4)*
- The initial MLL+Mix rule set used in Section 3 is consistent. *(p.5-6)*
- Extending MLL+Mix with the contraction-style rule over `comma` yields a stronger theory that proves `⊢ ⊥`. *(p.6-7)*
- In MILL, the modus-ponens-style rule and internal-composition rule checked in Section 4 are derivable. *(p.7-9)*
- Some candidate dual/par/tensor laws in MILL exceed solver memory, so the current implementation does not decide them. *(p.8-10)*

## Relevance to Project
This paper is directly relevant if propstore wants a lightweight verification harness for rule systems rather than only an execution engine. The core pattern is reusable: encode a base rule theory, negate a proposed derived rule, and use SMT satisfiability to decide whether the proposal is justified. That is useful for validating hand-authored rule sets, checking invariants on symbolic reasoning modules, or testing whether new derived rules in an argumentation/logic layer are genuine consequences or merely plausible guesses. *(p.2-4, p.10)*

It is also relevant because it gives an example of using Z3 for proof-theoretic validation rather than only satisfiability over ordinary formulas. That is a good fit for any propstore component that mixes symbolic rule engineering with automated consistency checks. *(p.1-4)*

## Open Questions
- How far can this Z3 encoding pattern scale before quantifiers and memory pressure make it impractical on richer fragments of linear logic? *(p.8-10)*
- Which of the currently unresolved dual/par/tensor properties in MILL are actually false versus merely too hard for the present encoding/hardware? *(p.8-10)*
- Would a tighter encoding or a different prover backend reduce the out-of-memory cases without changing the high-level method? *(p.10)*
- How easily does the same template transfer to other rule systems beyond the linear-logic fragments demonstrated here? *(p.10)*

## Related Work Worth Reading
- Moura and Bjørner (2008), *Z3: An Efficient SMT Solver* — the underlying SMT engine used by the paper. *(p.13)*
- Girard (1987), *Linear Logic* — foundational source for the logic family being encoded. *(p.13)*
- Heijltjes and Houston (2016), *Proof equivalence in MLL is PSPACE-complete* — source for the MLL+Mix rule set used in the paper. *(p.13-14)*
- Toader and Moura (2017), *From Z3 to Lean, Efficient Interoperability and Certification* — background on Z3/Lean interoperability mentioned by the authors. *(p.13)*

## Collection Cross-References

### Already in Collection
- [[Moura_2008_Z3EfficientSMTSolver]] — direct background on the solver the paper uses to check rule validity. *(p.13)*

### New Leads (Not Yet in Collection)
- Girard (1987) — *Linear Logic*. *(p.13)*
- Heijltjes and Houston (2016) — *Proof equivalence in MLL is PSPACE-complete*. *(p.13)*
- Toader and Moura (2017) — *From Z3 to Lean, Efficient Interoperability and Certification*. *(p.13)*

### Cited By (in Collection)
- [[Horowitz_2021_EpiPen]] — Moderate: both papers use Z3 to encode logical reasoning tasks, but this paper focuses on proof checking for linear-logic fragments while Horowitz focuses on dynamic epistemic state updates.

### Conceptual Links (not citation-based)
- [[Moura_2008_ProofsRefutationsZ3]] — Strong: both papers use Z3 as a proof-oriented reasoning substrate rather than only a conventional SAT/SMT backend, making them close workflow companions inside this collection.
