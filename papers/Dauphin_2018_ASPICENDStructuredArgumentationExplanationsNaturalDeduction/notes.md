---
title: "ASPIC-END: Structured Argumentation with Explanations and Natural Deduction"
authors: "Jeremie Dauphin, Marcos Cramer"
year: 2018
venue: "Computational Models of Argument"
doi_url: "https://doi.org/10.1007/978-3-319-75553-3_5"
---

# ASPIC-END: Structured Argumentation with Explanations and Natural Deduction

## One-Sentence Summary
Extends ASPIC+ with hypothetical reasoning, proof by contradiction, and explicit explanation relations between arguments, then shows on semantic-paradox examples that the resulting framework preserves ASPIC+-style rationality plus non-triviality guarantees needed for paradox applications. *(p.1, p.14-15)*

## Problem Addressed
ASPIC+ is strong at structured argumentation with strict and defeasible rules, but it cannot directly express some forms of reasoning common in philosophy and logic: hypothetical reasoning from local assumptions, proofs by contradiction, arguments about whether logical rules are correct, and explicit explanations of why one argument or premise supports another. *(p.1-5)*

The paper therefore asks how to modify ASPIC+ so that it can model natural-deduction-style arguments and explanation structures without losing the metatheoretic discipline that made ASPIC+ useful in the first place. *(p.1-3, p.11-15)*

## Key Contributions
- Introduces **ASPIC-END**, an ASPIC+-style framework with a third rule class, **intuitively strict rules**, whose applicability can still be attacked while preserving a stricter status than ordinary defeasible rules. *(p.5-7)*
- Adds **hypothetical arguments** via assumptions and proof-by-contradiction arguments, while forbidding defeasible rules inside hypothetical reasoning itself. *(p.3-7)*
- Defines an **explanatory argumentation framework (EAF)** that augments arguments and attacks with an explanation relation from arguments to arguments or explananda. *(p.3-4, p.8)*
- Defines two explanation-oriented extension types: **argumentative core extensions (AC-extensions)** and **explanatory core extensions (EC-extensions)**. *(p.8-9)*
- Instantiates the framework for explanations of semantic paradoxes, especially the liar paradox. *(p.9-11)*
- Proves six metatheoretic results: subargument closure, closure under accepted intuitively strict rules, direct consistency, indirect consistency, direct non-triviality, and indirect non-triviality. *(p.11-15)*

## Methodology
The paper starts from ASPIC+ and modifies the rule language and argument-construction rules to support assumptions, contradiction arguments, and explanation edges. It first motivates the changes against limitations of ordinary ASPIC+, then formally defines ASPIC-END, then lifts the resulting arguments into an explanatory argumentation framework, and finally defines explanation-oriented extensions for selecting informative and defensible sets of arguments. The framework is instantiated on semantic-paradox reasoning, where the authors use liar-style examples to show both how explanations are represented and why the added rationality and non-triviality postulates matter. *(p.2-15)*

## Key Equations

$$
\mathrm{EAF} = (\mathcal{A}, \mathcal{X}, \rightarrow, \rightsquigarrow)
$$

Where: `\mathcal{A}` is the set of arguments, `\mathcal{X}` is the set of explananda, `\rightarrow` is the attack relation, and `\rightsquigarrow` is the explanation relation from arguments to explananda or arguments. *(p.3, p.8)*

$$
\Sigma = (\mathcal{L}, \mathcal{C}, \mathcal{R}, n, \preceq)
$$

Where: `\mathcal{L}` is a language closed under two negations, `\mathcal{C}` is the contrariness function, `\mathcal{R} = \mathcal{R}_{iu} \cup \mathcal{R}_{str} \cup \mathcal{R}_d` is the partition into intuitively strict, strict, and defeasible rules, `n` names defeasible and intuitively strict rules, and `\preceq` is a preference relation over rules. *(p.5)*

$$
\mathrm{Concs}(S) = \{\mathrm{Conc}(A) \mid A \in S\}
$$

Where: `S` is an AC- or EC-extension and `Concs(S)` is the set of conclusions supported by that extension. *(p.9)*

$$
\mathrm{Cl}_{\mathcal{R}_{iu}(S)}(\mathrm{Concs}(S))
$$

Where: `\mathcal{R}_{iu}(S)` is the set of intuitively strict rules accepted by extension `S`, and the expression denotes closure of the extension's conclusions under those accepted intuitively strict rules. *(p.12)*

## Parameters

This is a theoretical framework paper. It introduces no numeric hyperparameters, thresholds, or empirical benchmark settings. The important "parameters" are symbolic choices such as the set of explananda, the explanation criterion, the rule partition, and the accepted intuitively strict rules. *(p.3-5, p.8-12)*

## Core Definitions

### Explanatory Power and Depth
The paper extends abstract argumentation with explanatory criteria. An explanation offered by a set of arguments should account for as many explananda as possible while also doing so in as much detail as possible. Explanatory power compares sets by how many explananda they explain, while explanatory depth compares them by how detailed the explanations are for a fixed explanandum. *(p.4)*

### Intuitively Strict Rules
ASPIC-END introduces a middle rule class between strict and defeasible rules. Intuitively strict rules are rules that are initially plausible and behave like strict rules inside proofs, but unlike strict rules their applicability can be attacked. They are intended to capture prima facie laws of logic or inference rules that make sense at first but are still open to debate. *(p.5)*

### Hypothetical Arguments
Arguments may introduce assumptions, and proof by contradiction lets an argument derive `-\varphi` from an argument for `\bot` constructed under assumption `\varphi`. However, defeasible rules are not allowed inside hypothetical reasoning itself; only strict and intuitively strict rules may operate there. Defeasible conclusions may still be imported into a proof-by-contradiction argument from outside. *(p.3, p.6)*

### Assumption-Attacks
Unlike ASPIC+, ASPIC-END allows a conclusion to attack an assumption directly if it concludes something contrary to that assumption. This lets the framework model attacks on temporary hypotheses used in hypothetical reasoning. *(p.6-7)*

### Explanation Relation
Argument `B` explains argument `A` or explanandum `A'` when `B` non-trivially concludes one of `A`'s premises or one of the inference rules used by `A`. The formal definition excludes vacuous self-explanation and tracks the rule attacked or supported via `TopRule`. *(p.7-8)*

### AC- and EC-Extensions
The paper defines two explanation-aware extension concepts:
- **AC-extension**: an argumentative core extension, prioritizing defensibility/completeness of the argumentative core. *(p.8)*
- **EC-extension**: an explanatory core extension, prioritizing explanatory insightfulness once admissibility is secured. *(p.8)*

## Implementation Details
- Represent three rule classes explicitly: strict, intuitively strict, and defeasible. The extra middle tier is essential; it cannot be emulated just by relabeling ordinary ASPIC+ rules. *(p.5-7)*
- Track assumptions as first-class argument metadata via `As(A)`. Hypothetical reasoning depends on knowing which local assumptions remain open in a derivation. *(p.5-6)*
- Include explicit proof-by-contradiction argument nodes with a special constructor such as `ProofByContrad(-\varphi, A')`. *(p.6)*
- Disallow defeasible-rule use inside hypothetical arguments. This is a modeling constraint, not an optimization. The paper treats it as necessary to avoid problematic forms of hypothetical defeasible reasoning. *(p.3, p.6)*
- Add an assumption-attack relation alongside rebuttal and undercutting. This matters because assumptions introduced locally must be attackable. *(p.6-7)*
- Lift preferences from rules to arguments with a weakest-link-style condition over the rules used, replacing ASPIC+'s usual strict/defeasible-only setup with one that includes intuitively strict rules. *(p.7)*
- Construct a separate explanation graph over the arguments after argument generation. The EAF needs both attacks and explanation edges; explanation is not reducible to defeat. *(p.7-8)*
- Define extension selection in two phases: admissibility first, then maximize explanatory power or depth depending on whether AC- or EC-extensions are desired. *(p.4, p.8)*
- For paradox applications, encode source arguments for explananda explicitly. In the liar example, the explanandum is tied to a specific source argument, then other arguments explain it by defeating that source. *(p.9-11)*

## Worked Example: Liar Paradox
The paper uses a liar-style sentence `L` where "if `L` is true, then `L` is false" and "if `L` is false, then `L` is true." It distinguishes two explananda:
- a **truth-value-gap explanation**, where `L` is false because `L` is not true, derived under a proof-by-contradiction style assumption; *(p.10)*
- a **paracomplete explanation**, where `L` is not true because assuming `L` is true yields absurdity, but without using excluded middle for self-referential truth statements. *(p.10)*

The ASPIC-END encoding generates arguments `A_1`, `A_2`, `B_1`, `B_2`, and `C`, with `B_2` defeating `A_2` and `C` defeating `A_2` on the assumption `T(L)`. In the resulting EAF, `B_1` explains `B_2` by non-trivially concluding `\neg T(L) \wedge \neg F(L)`, while `C` explains the explanandum by attacking its source argument. The AC-extension is `{B_1, B_2, C}` and the EC-extension is `{B_1, B_2}`. *(p.10-11)*

## Figures of Interest
- **Fig. 1 (p.11):** Shows the liar-paradox example graph with explanandum `E`, arguments `A_1`, `A_2`, `B_1`, `B_2`, and `C`, plus the attack and explanation edges. This is the clearest implementation picture of how explanation and defeat coexist in ASPIC-END.

## Results Summary
The paper is theoretical rather than empirical. Its main results are six metatheoretic theorems:
- **Theorem 1:** AC-extensions are closed under subarguments. *(p.11-12)*
- **Theorem 2:** Conclusions of AC-extensions are closed under accepted intuitively strict rules. *(p.12)*
- **Theorem 3:** Direct consistency holds for AC- and EC-extensions under a consistency-inducing argumentation theory. *(p.13)*
- **Theorem 4:** Indirect consistency follows from closure under accepted intuitively strict rules plus direct consistency. *(p.13)*
- **Theorem 5:** Direct non-triviality holds: extensions do not conclude `\bot`. *(p.14)*
- **Theorem 6:** Indirect non-triviality also holds under accepted intuitively strict rules. *(p.14)*

## Limitations
- The framework only treats one restricted form of proof by contradiction, namely the inference scheme corresponding to proof by cases and `\bot`-introduction / negation-introduction. It does not claim to cover all forms of hypothetical reasoning. *(p.3, p.6)*
- Defeasible rules are forbidden inside hypothetical reasoning. This avoids one class of problems, but it narrows expressivity. *(p.3, p.6)*
- The paper's main concrete instantiation is philosophical logic and semantic paradoxes. The authors explicitly leave other domains and richer languages for future work. *(p.1, p.14-15)*
- The consistency postulates are intentionally not meant for paraconsistent settings where some contradictions are acceptable. The authors note that their postulates do not make sense for such applications. *(p.13)*
- The explanation notion is argument-centered and tailored to structured argumentation; it does not attempt a broader semantic theory of explanation outside that setting. *(p.3-4, p.7-8)*

## Arguments Against Prior Work
- Standard ASPIC+ cannot model arguments about whether the rules of logic are correct, because arguments about strict rules cannot themselves be attacked. ASPIC-END introduces intuitively strict rules precisely to break that limitation. *(p.4-5)*
- Hilbert-style ASPIC+ argument construction cannot naturally capture hypothetical reasoning from a locally assumed premise without global commitment. ASPIC-END adds assumptions and proof-by-contradiction arguments to address this. *(p.2-3, p.6)*
- Existing explanation work in abstract argumentation is too detached from structured arguments for the paper's goals. The authors want explanations grounded in premises and inference steps, not just abstract nodes. *(p.3-4, p.7-8)*
- The authors modify the Seelja/Strasser-style explanation-selection procedures to prioritize defense completion over sheer explanatory power, arguing that otherwise plausible but undefended explanations can beat sounder ones. *(p.4, p.8)*

## Design Rationale
- **Why intuitively strict rules?** Because the correctness of some logical rules is itself debated in philosophy, so the framework needs something more contestable than strict rules but more principled than ordinary defeasible rules. *(p.4-5)*
- **Why ban defeasible rules inside hypothetical reasoning?** Because allowing them produces problematic forms of hypothetical defeasible reasoning already criticized in prior work; the authors prefer a safer restricted natural-deduction fragment. *(p.3, p.6)*
- **Why explanation between arguments rather than only between premises and conclusions?** Because structured arguments make it possible to say not just what conclusion is supported, but which subargument or rule use is explained. *(p.3-4, p.7-8)*
- **Why define both AC- and EC-extensions?** Because one selection procedure should favor the defensible argumentative core, while another should favor explanatory richness once admissibility is secured. *(p.4, p.8-9)*
- **Why closure only under accepted intuitively strict rules rather than all intuitively strict rules?** Because intuitively strict rules can themselves be attacked, so closure under all of them would be too strong. *(p.12)*
- **Why add non-triviality postulates?** Because paradox applications care not only about consistency but also about avoiding triviality, i.e. deriving everything from contradictions. *(p.11-15)*

## Testable Properties
- If `S` is an AC-extension and `A` is in `S`, then every subargument of `A` must also be in `S`. *(p.11-12)*
- If a formula is derivable from the accepted conclusions of an AC-extension using only intuitively strict rules that are themselves accepted by the extension, then that formula must also belong to the extension's conclusion set. *(p.12)*
- In a consistency-inducing argumentation theory, no AC- or EC-extension may contain both `\varphi` and `-\varphi` among its conclusions. *(p.13)*
- In a consistency-inducing argumentation theory, no AC- or EC-extension may derive `\bot` directly. *(p.14)*
- Indirect non-triviality follows from direct non-triviality plus closure under accepted intuitively strict rules: no extension may derive `\bot` after taking that closure. *(p.14)*

## Relevance to Project
This paper matters if the project needs argumentation structures that do more than compute winners. ASPIC-END gives a concrete design for:
- explanation links between arguments and claims; *(p.3-4, p.7-9)*
- local assumptions and contradiction-based reasoning inside a structured-argument framework; *(p.2-3, p.6)*
- treating some inference rules as provisionally accepted but still attackable; *(p.4-7)*
- selecting a defensible explanatory core rather than just an admissible extension. *(p.4, p.8-9)*

For propstore specifically, the useful pattern is the separation between argumentative support/defeat and explanatory structure. If the system needs to answer not only "is this accepted?" but also "which arguments explain why this premise or rule matters?", ASPIC-END provides a formal route. *(p.3-4, p.7-9)*

## Open Questions
- [ ] How should ASPIC-END be instantiated in domains other than philosophical logic, especially scientific debates or legal reasoning? *(p.15)*
- [ ] How should the framework be extended to richer rule languages, including modal accessibility and causal notions? *(p.15)*
- [ ] How should reasoning by cases in structured argumentation be integrated with ASPIC-END? *(p.15)*
- [ ] If a target domain is paraconsistent, which of the consistency and non-triviality postulates should be weakened or dropped? *(p.13-15)*

## Related Work Worth Reading
- Beirlaen, Heyninck, and Strasser (2017), *Reasoning by Cases in Structured Argumentation* — explicitly named as future integration work. *(p.15)*
- Seselja and Strasser (2013), *Abstract argumentation and explanation applied to scientific debates* — the explanation-centered predecessor that motivates the EAF machinery. *(p.3-4)*
- Modgil and Prakken (2014), *The ASPIC+ framework for structured argumentation: a tutorial* — the base structured framework ASPIC-END modifies. *(p.2-3, p.15)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — the abstract semantics base beneath the EAF and the attack/defense notions ASPIC-END reuses. *(p.2, p.8)*
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — the primary ASPIC+ reference whose rationality-postulate program ASPIC-END extends. *(p.2-3, p.11-15)*
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — the direct structured-argument precursor cited as an ASPIC-family base paper. *(p.2, p.15)*
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — cited for rationality-postulate discussion and background on evaluation of argumentation formalisms. *(p.3)*

### New Leads (Not Yet in Collection)
- Beirlaen, Heyninck, and Strasser (2017), *Reasoning by Cases in Structured Argumentation*. *(p.15)*
- Seselja and Strasser (2013), *Abstract argumentation and explanation applied to scientific debates*. *(p.3-4, p.15)*
- Besnard et al. (2014), *Introduction to structured argumentation*. *(ref.4)*

### Cited By (in Collection)
- (none found)
