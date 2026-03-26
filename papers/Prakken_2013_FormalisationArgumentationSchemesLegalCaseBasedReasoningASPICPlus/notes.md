---
title: "A formalisation of argumentation schemes for legal case-based reasoning in ASPIC+"
authors: "Henry Prakken, Adam Wyner, Trevor Bench-Capon, Katie Atkinson"
year: 2013
venue: "Proceedings of the Twentieth International Conference on Legal Knowledge and Information Systems (JURIX 2007 paper extended and substantially rewritten)"
doi_url: ""
pages: "1-31"
---

# A formalisation of argumentation schemes for legal case-based reasoning in ASPIC+

## One-Sentence Summary
Recasts CATO-style legal case-based reasoning as a set of explicit ASPIC+ defeasible argumentation schemes over factor partitions, substitution/cancellation moves, and preference arguments, and proves the resulting theory satisfies ASPIC+'s rationality requirements. *(p.2-5, p.19-22, p.29)*

## Problem Addressed
Earlier legal case-based reasoning systems such as HYPO and CATO model cases using factors and precedents, but the core reasoning patterns were largely informal or only semi-formal. This made it hard to precisely analyze how precedent comparison, distinctions, substitutions, and preference arguments interact. *(p.1-2)*

The paper addresses how to formalize these legal case-based reasoning moves as explicit defeasible arguments, so they can be constructed, attacked, and evaluated inside a general structured-argumentation framework rather than being hard-coded procedural steps. *(p.2, p.5-6, p.13-18)*

## Key Contributions
- Formalizes six CATO-style legal case-based argumentation schemes inside ASPIC+, including plaintiff-side preference arguments and undercutters based on distinguishing factors. *(p.13-18)*
- Encodes cases as sets of plaintiff and defendant factors plus functions for common, current-only, and precedent-only factor partitions. *(p.7-12)*
- Introduces explicit predicates for factor substitution and cancellation via a factor hierarchy, allowing attacks on distinctions to be represented as arguments rather than as ad hoc procedural checks. *(p.11-15)*
- Shows how the formalization yields a Dung-style abstract argumentation framework whose attack structure captures precedent-based legal debate. *(p.4-5, p.18)*
- Proves the resulting argumentation theory satisfies ASPIC+'s rationality postulates of consistency and closure under strict rules. *(p.19-22)*
- Identifies important extensions beyond CATO's factor-only reasoning: dimensions, reasoning from facts to factors, factor incompatibility, and value preferences. *(p.22-29)*

## Methodology
The paper first specifies a simplified ASPIC+ setting with a first-order language, strict and defeasible rules, ordinary premises, axioms, attack relations, and preference-based defeat. It then defines a legal case language with factors, factor sets, outcomes, factor hierarchies, and comparison functions between a current case and a precedent. On top of that language, it defines defeasible schemes `CS1`-`CS4` and attack schemes `U1.1`, `U1.1.1`, `U1.1.2`, `U2.1`, `U2.1.1`, `U2.1.2`, plus rebuttal-style counterexample moves. These are instantiated on the running `Mason`/`Bryce` example and analyzed as an ASPIC+/Dung argument graph. Finally, the authors use ASPIC+'s metatheory to prove closure and consistency results and discuss how to extend the approach beyond factor sets. *(p.3-5, p.7-18, p.19-29)*

## Key Equations

$$
AF = (A, Def)
$$

Where `A` is the set of arguments constructible from the ASPIC+ argumentation theory and `Def` is the defeat relation induced from successful rebuttal, successful undermining, and undercutting. *(p.4-5)*

$$
commonPFactors(curr, prec) = pFactors(curr) \cap pFactors(prec)
$$

Where `commonPFactors(curr, prec)` is the set of plaintiff factors shared by the current case and the precedent. *(p.10-11)*

$$
currPFactors(curr, prec) = pFactors(curr) \setminus commonPFactors(curr, prec)
$$

Where `currPFactors(curr, prec)` is the set of plaintiff factors present only in the current case. Similar definitions are given for `commonDFactors`, `currDFactors`, `precPFactors`, and `precDFactors`. *(p.10-11)*

$$
CS1(curr, prec, p, d):\ \ commonPFactors(curr,prec)=p,\ commonDFactors(curr,prec)=d,\ preferred(p,d),\ outcome(prec)=Plaintiff \Rightarrow outcome(curr)=Plaintiff
$$

This is the main plaintiff-side precedent scheme: if the shared plaintiff factors are preferred over the shared defendant factors and the precedent was decided for the plaintiff, the current case should also be decided for the plaintiff. *(p.13-14)*

$$
U1.1(curr, prec, p, d):\ \ f \in currDFactors(curr,prec) \Rightarrow \neg CS1(curr,prec,p,d)
$$

This undercutter captures a defendant distinction: a defendant-side factor in the current case but not in the precedent undermines direct application of the precedent. *(p.14)*

$$
CS2(curr, prec, p, d):\ \ commonPFactors(curr,prec)=p,\ commonDFactors(curr,prec)=d,\ outcome(prec)=Plaintiff \Rightarrow preferred(p,d)
$$

This scheme derives the preference relation between the common plaintiff and defendant factor sets from the precedent itself. *(p.15)*

## Parameters

The paper does not introduce numeric hyperparameters, thresholds, or empirical tuning constants. Its main adjustable objects are symbolic:

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Current case | `curr` | - | - | case term | 11-18 | Variable standing for the case to be decided |
| Precedent case | `prec` | - | - | case term | 11-18 | Variable standing for the precedent used in comparison |
| Shared plaintiff factor set | `p` | - | - | set of factors | 13-17 | Used in `CS1`-`CS4` |
| Shared defendant factor set | `d` | - | - | set of factors | 13-17 | Used in `CS1`-`CS4` |

## Implementation Details
- Represent cases with explicit predicates and functions for `hasFactor`, `hasPFactor`, `hasDFactor`, `pFactors(case)`, `dFactors(case)`, and `outcome(case)` rather than treating factor partitions as opaque records. *(p.8-10)*
- Put type axioms, set-theoretic axioms, factor polarity declarations, and fixed factor-hierarchy facts in the strict base `K_n`, while case-specific factor statements go into the ordinary-premise base `K_p`. *(p.7-10)*
- Derive comparison partitions with explicit functions: `commonPFactors`, `commonDFactors`, `currPFactors`, `currDFactors`, `precPFactors`, and `precDFactors`. These become the building blocks of precedent arguments. *(p.10-12)*
- Model substitutions and cancellations through abstract-factor ancestry using `parentFactor`, recursive `ancestor`, `substitutes`, and `cancels`. Substitution compares factors across cases; cancellation compares opposing factors inside the current case. *(p.11-15)*
- Instantiate schemes as defeasible rules named by scheme identifiers so they can be undercut through ASPIC+'s rule-naming mechanism. *(p.13-16)*
- Use the plaintiff-side main scheme `CS1` plus its undercutters and defenders to capture direct precedent application, and `CS2` to justify the preference relation used inside `CS1`. *(p.13-16)*
- Use `CS3` and `CS4` as supplementary schemes that point to additional current-case factors not consumed in substitution/cancellation, effectively modeling "emphasis strengths" rather than minimal proof obligations. *(p.16-18)*
- Generate the corresponding Dung AF from the ASPIC+ argumentation theory and compute defeat among instantiated arguments and subarguments; attacks on subarguments propagate to the containing argument. *(p.4-5, p.18)*
- Treat factor hierarchy as fixed in this model. The paper explicitly does not reason about disputes over the hierarchy itself; if that is needed, `parentFactor` would have to become a conclusion of arguments rather than a premise. *(p.10-12)*

## Figures of Interest
- **Figure 1 (p.4):** Basic ASPIC+ argument tree showing premises `P1`-`P4`, defeasible and strict inferences, and the `Prem`, `Sub`, `Conc`, and `TopRule` structure the formal definitions operate on.
- **Figure 2 (p.18):** Partial argument graph for the `Mason(Bryce)` running example, showing the main plaintiff argument, the preference subargument, two distinction attacks, and the substitution/cancellation defenses.

## Results Summary
- In the `Mason`/`Bryce` example, the instantiated argument graph contains a unique extension with the cancellation-based defense and the distinction argument, but without the full direct-precedent plaintiff argument, because one precedent-only plaintiff factor (`F18`) remains undefeated. *(p.18-19)*
- If an additional substitution were available for `F18`, the stronger plaintiff argument applying the precedent directly would survive. *(p.18-19)*
- The formalization satisfies ASPIC+'s rationality postulates because the strict theory is shown consistent and the corresponding Dung framework therefore inherits the required closure/consistency properties. *(p.19-22)*
- The paper also shows that the factor-set formalization does not yet capture all aspects of legal reasoning; dimensions, facts-to-factors moves, factor incompatibility, and value preferences require more expressive schemes. *(p.22-29)*

## Limitations
- The formalization mainly covers factor-based precedent reasoning as in CATO; it does not fully model reasoning from underlying facts to factors. *(p.24-25)*
- It treats the factor hierarchy as fixed and not itself arguable, even though in principle parties might dispute abstract-factor parent relations. *(p.10)*
- It does not settle how to compare factor strength along HYPO-style dimensions; the discussion only sketches how substitution/cancellation might need refinement there. *(p.23-26)*
- Factor incompatibility in CATO is recognized, but only informally discussed here; explicit argumentation schemes for proving or defeating incompatible factors are left for future work. *(p.25-26)*
- Value-based explanations of why certain factors or precedents should control are not formalized in the present system. *(p.27, p.29)*

## Arguments Against Prior Work
- Prior legal case-based systems left central precedent-comparison reasoning patterns only semi-formal, which limited precise analysis of how distinctions and precedent application interact. *(p.1-2)*
- CATO's factor-only representation cannot adequately express where a case lies along a dimension or how facts support factor attribution; some important issues are therefore hidden inside procedures rather than arguable content. *(p.22-26)*
- Existing systems may support some stages of legal reasoning but not others: CATO supports substitution/cancellation moves but not arguments about facts; HYPO links facts and dimensions but does not support the same explicit factor-argument and counterargument structure; AGATHA uses weighted search but keeps the reasoning less transparent. *(p.27-28)*
- The authors argue that reducing case-based reasoning to a single plaintiff-vs-defendant preference choice is too coarse. Once preferences themselves are argued for, the reasoning decomposes into multiple finer-grained attack/defense stages. *(p.27-28)*

## Design Rationale
- **Why ASPIC+?** Because it provides explicit structured arguments, undercutters via rule names, and a metatheory strong enough to prove consistency and closure results for the legal formalization. *(p.3-5, p.19-22, p.29)*
- **Why represent schemes as defeasible rules instead of procedures?** Because the legal moves should themselves be contestable objects that can be attacked, defended, and compared in the same framework. *(p.2, p.13-18, p.27-28)*
- **Why derive preference with `CS2` from a specific precedent rather than from an abstract preference rule?** Because CATO-style reasoning argues from particular precedents, not from free-floating global set preferences detached from cases. *(p.15)*
- **Why use substitution and cancellation?** Because not every difference between current and precedent cases should defeat precedent application; some can be argued away by showing analogous supporting factors or offsetting contrary factors. *(p.12-15)*
- **Why add `CS3` and `CS4` after `CS1` and `CS2`?** To model the extra persuasive force of unused current-case strengths, even when they are not strictly needed for substitution or cancellation. *(p.16-18)*

## Testable Properties
- The set of arguments generated by the legal formalization can be mapped to a Dung AF and evaluated using ordinary abstract-argumentation semantics. *(p.4-5)*
- In the running example, the defeat relation includes at least `defeat(A2,A1)`, `defeat(A3,A2)`, `defeat(A5,A4)`, `defeat(A5',A4)`, and `defeat(A6,A5)`. *(p.18)*
- The strict closure of `K_n` for the specified argumentation theory is consistent. *(p.19-22)*
- The corresponding Dung-style AF satisfies all four ASPIC+ rationality postulates used by the authors. *(p.22)*
- If a new substitution neutralizing the remaining `F18` distinction were available in the running example, the stronger plaintiff-side precedent-application argument would become undefeated. *(p.18-19)*

## Relevance to Project
This paper is directly useful for any propstore work that wants precedent-style legal reasoning or factor-based structured argumentation without burying the reasoning inside procedural comparison code. It gives a clean recipe for turning case comparison into explicit ASPIC+ arguments whose attacks and defenses are inspectable. *(p.13-18, p.27-29)*

It is especially relevant if the project needs:
- case comparison over factor sets rather than only claim-to-claim attack *(p.5-18)*
- explicit modeling of distinctions, substitutions, and cancellations as first-class reasoning moves *(p.12-17)*
- a way to prove the metatheoretic sanity of a legal reasoning formalization by leaning on ASPIC+'s rationality results *(p.19-22)*

## Open Questions
- [ ] What are the right explicit argumentation schemes for deriving factors from raw facts instead of treating factors as givens? *(p.24-25)*
- [ ] How should factor incompatibility be turned into explicit attack and defense schemes rather than left as analyst-side knowledge? *(p.25-26)*
- [ ] How should substitution and cancellation interact with HYPO-style dimensions and factor strength? *(p.23-26)*
- [ ] How can value preferences explaining why factors matter be integrated into the same scheme-based ASPIC+ account? *(p.27, p.29)*

## Related Work Worth Reading
- Aleven (1997), *Teaching case-based argumentation through a model and examples* — direct source for the factor hierarchy and running-example style. *(p.6, p.29)*
- Ashley (1990), *Modeling Legal Argument* — HYPO's dimensions/cases/hypotheticals background. *(p.23, p.29)*
- Gordon and Walton (2006), *Legal reasoning with argumentation schemes* — related use of schemes for legal reasoning. *(p.2, p.30)*
- Modgil and Prakken (2013), *A general account of argumentation with preferences* — the broader ASPIC+ framework this paper instantiates. *(p.3-5, p.30)*

## Collection Cross-References

### Already in Collection
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — shorter ASPIC+ framework paper that provides the structured-argumentation machinery this legal instantiation depends on. *(p.3-5; ref.21)*
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — later journal version of the ASPIC+ preference framework used here as metatheoretic background. *(conceptual; ref.20 predecessor)*
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — broader scheme taxonomy that helps contextualize the legal schemes used here. *(p.2, p.24, ref.27)*

### New Leads (Not Yet in Collection)
- Aleven (1997) — *Teaching case-based argumentation through a model and examples*. *(ref.1)*
- Ashley (1990) — *Modeling Legal Argument: Reasoning with Cases and Hypotheticals*. *(ref.2)*
- Chorley and Bench-Capon (2005) — *AGATHA: Using heuristic search to automate the construction of case law theories*. *(ref.13)*
- Gordon and Walton (2006) — *Legal reasoning with argumentation schemes*. *(ref.17)*
- Bench-Capon and Sartor (2003) — value-based legal case reasoning with theories and values. *(ref.7)*

### Cited By (in Collection)
- [[Lehtonen_2020_AnswerSetProgrammingApproach]] — cites this paper as the technical-report precursor for ASPIC+-based legal case reasoning formalized over CATO-style factors. *(noted in that paper's cross-references)*
- [[Prakken_2019_ModellingAccrualArgumentsASPIC]] — links this paper as relevant background for the legal and factor-based applications of accrual in ASPIC+. *(noted in that paper's cross-references)*
