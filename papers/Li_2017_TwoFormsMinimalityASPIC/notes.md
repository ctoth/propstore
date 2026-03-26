---
title: "Two forms of minimality in ASPIC+"
authors: "Zimi Li, Andrea Cohen, Simon Parsons"
year: 2017
venue: "arXiv preprint / February 2017 note"
doi_url: "https://arxiv.org/abs/1702.00780"
---

# Two forms of minimality in ASPIC+

## One-Sentence Summary
Distinguishes ASPIC+'s native "all included ingredients are used" minimality from a stronger closure-based minimality, and shows that the stronger notion is recovered exactly by excluding circular and redundant arguments, yielding regular arguments uniquely described by `(grounds, rules, conclusion)`. *(p.1-10)*

## Problem Addressed
Many structured-argumentation systems informally assume that an argument for a conclusion uses the smallest support needed to derive that conclusion. ASPIC+ does not enforce that stronger condition; it only enforces that every premise and rule appearing in an argument participates in its recursive construction. The paper clarifies this mismatch and proposes a stronger notion suitable when canonical arguments are needed. *(p.1-2, p.4-9)*

## Key Contributions
- Makes explicit that ASPIC+ already enforces a weak minimality condition: no unused premises or rules may appear in an argument. *(p.1-4)*
- Shows via examples that this does not prevent circular or redundant arguments, so ASPIC+ arguments need not be minimal in the stronger sense used elsewhere in structured argumentation. *(p.4-6)*
- Formalizes circular arguments and redundant arguments as the two failure modes behind non-minimal derivations. *(p.6)*
- Defines a closure operator over propositions and rules, then uses it to define a stronger minimal argument notion based on minimal grounds and minimal rules sufficient to derive the conclusion. *(p.6-7)*
- Proves that the stronger minimal arguments are exactly the regular arguments, i.e. those that are neither circular nor redundant. *(p.7-8)*
- Proves that every minimal argument is uniquely characterized by its triple `(G, R, p)`, unlike ordinary ASPIC+ arguments where distinct derivations can share the same triple. *(p.8-9)*

## Background and Definitions

### ASPIC+ Setup
The paper restates ASPIC+ with an argumentation system `AS = (L, -, R, n)` over a language with contrariness, strict rules `->`, defeasible rules `=>`, and a naming function `n` for defeasible rules. A knowledge base `K` is split into axioms `K_n` and ordinary premises `K_p`, and an argumentation theory is `AT = (AS, K)`. *(p.2)*

### Standard ASPIC+ Arguments
Arguments are built recursively. A premise `phi` yields the base argument `[phi]`. If arguments `A_1, ..., A_n` conclude `phi_1, ..., phi_n` and there is a rule `phi_1, ..., phi_n ~> phi`, then a new argument combines them into `A_1, ..., A_n ~> phi`. The paper also defines:
- `Prem(A)` for the premises used,
- `Conc(A)` for the conclusion,
- `Sub(A)` for the set of subarguments,
- `TopRule(A)` for the final rule,
- `Rules(A)` for the set of rules used,
- and a triple presentation `A = (G, R, p)` with grounds `G`, rules `R`, and conclusion `p`. *(p.3)*

## The Two Minimality Notions

### Native ASPIC+ Minimality
Definition 4's recursive construction guarantees that every premise or rule appearing in an argument is actually used in the derivation. Proposition 1 proves this formally: every element of the grounds and every rule in `Rules(A)` occurs in the derivation tree of `Conc(A)`. This rules out explicitly extraneous support elements. *(p.4)*

### Stronger Closure-Based Minimality
The stronger notion asks whether there exists a smaller set of grounds and/or rules that derives the same conclusion. To express this, the authors define the closure `Cl_P(R)` of propositions derivable from premises `P` using rules `R`, then write `P |-R p` when `p` belongs to that closure. A strong-minimal argument `A = (G, R, p)` is one where no strict subset of `G` with the same `R` derives `p`, and no strict subset of `R` with the same `G` derives `p`. *(p.6-7)*

## Why Native Minimality Is Not Enough

### Circular Arguments
Example 4 and Definition 8 show how an argument can reuse its own intermediate conclusions in a loop. Such arguments satisfy ASPIC+'s native construction discipline but are intuitively non-minimal because part of the derivation is self-supporting. *(p.6)*

### Redundant Arguments
Definition 9 and Example 6 show another failure mode: an argument can contain two distinct subarguments with the same conclusion, so one branch is unnecessary even though every local step is used. This produces duplicated support structure without changing the derived claim. *(p.6)*

### Shared Triple, Distinct Derivations
Example 3 shows that two distinct ASPIC+ arguments can have the same `(G, R, p)` description, because ASPIC+ records derivational structure rather than only inferential resources. This is exactly the ambiguity the stronger minimality notion removes. *(p.5, p.9)*

## Main Results
- Proposition 1: ordinary ASPIC+ arguments are minimal only in the weak sense that no support item is unused. *(p.4)*
- Proposition 2: every regular argument is a minimal argument in the stronger sense. *(p.7-8)*
- Example 8 demonstrates that the converse is not "obviously by syntax" but still holds through the regular/non-regular analysis: circular or redundant arguments fail the stronger notion. *(p.8)*
- Proposition 3: if `A` is a minimal argument, then there is no distinct argument `B` with the same `(G, R, p)` triple. Strong minimality therefore yields canonical argument identity by resources plus conclusion. *(p.9)*

## Implementation Details
- If propstore wants reproducible canonical arguments, ordinary ASPIC+ objects are not enough; two different derivation trees may collapse to the same support set and conclusion. *(p.5, p.8-9)*
- Circularity and redundancy need to be tested at the level of subarguments, not just final support sets. A derivation can use every ingredient and still be non-minimal. *(p.5-6)*
- A practical canonicalization pass can compute `Prem(A)`, `Rules(A)`, and `Conc(A)`, then check whether any strict subset of the grounds or rules derives the same conclusion. *(p.6-7)*
- If the system stores arguments as derivation trees, regular/minimal arguments should probably be a filtered subset or normalized view rather than the only internal representation. Ordinary ASPIC+ still allows non-regular arguments for some theoretical purposes. *(p.7-9)*
- The paper's closure-based definition is compatible with mixed strict/defeasible rule sets, so the regularity check belongs in the core argument-construction layer, not only in a special strict mode. *(p.6-7)*

## Relevance to Project
This paper is directly relevant if propstore needs a canonical argument identity or wants to deduplicate equivalent derivations. It says that `(grounds, rules, conclusion)` is safe as a unique representation only after filtering to stronger minimal arguments. Without that filter, two different ASPIC+ derivations can look identical at the resource level but still be distinct argument objects. *(p.5-9)*

## Open Questions
- [ ] Should propstore expose raw ASPIC+ derivation trees, regular/minimal arguments, or both?
- [ ] Does the project need explicit circularity and redundancy diagnostics?
- [ ] If argument equality is resource-based, when and where should canonicalization happen?
- [ ] Should minimality checks be exact or approximated for performance?

## Collection Cross-References

### This paper cites (in collection)
- **Besnard_2001_Logic-basedTheoryDeductiveArguments** - cited as [2]. The main comparison point for support-minimal logic-based arguments.
- **Modgil_2018_GeneralAccountArgumentationPreferences** - cited as [8] via the 2013/2018 "general account" paper. This is the core ASPIC+ reference whose notion of argument minimality is being clarified here.
- **Pollock_1987_DefeasibleReasoning** - cited as [10]. Part of the historical background on defeasible reasoners where circularity and redundancy are already recognized as bad argument patterns.

### Cited By (in Collection)
- None found by title, directory name, or author/year search at reconcile time.

### Conceptual Links
- **Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning** - another short ASPIC+ analysis note by the same lead author; that paper studies consequence-relation axioms, while this one studies argument identity and canonical support.
- **Prakken_2010_AbstractFrameworkArgumentationStructured** - explains how structured arguments are represented at a more abstract level; useful background for why the `(G, R, p)` triple matters.
- **Lehtonen_2020_AnswerSetProgrammingApproach** - provides a computational backend for ASPIC+ semantics. If propstore implements minimal/regular-argument filtering, this is the kind of solver-oriented paper that would need to reflect it.

## Related Work Worth Reading
- **Modgil and Prakken 2013** - base ASPIC+ definition being refined here. *(p.1-3, p.10)*
- **Prakken 2010** - structured-argument abstraction background. *(p.1, p.10)*
- **Besnard and Hunter 2001** - comparison point for logic-based arguments built from minimal support. *(p.1, p.10)*
- **Garcia and Simari 2004** - DeLP comparison where support-minimality is explicit. *(p.1, p.10)*
- **Pollock 1987 / 1995 / 1996** - historical motivation for avoiding circular or redundant inference patterns. *(p.5-10)*
