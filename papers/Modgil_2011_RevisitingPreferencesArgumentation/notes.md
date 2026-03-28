---
title: "Revisiting Preferences and Argumentation"
authors: "Sanjay Modgil; Henry Prakken"
year: 2011
venue: "Proceedings of the 22nd International Joint Conference on Artificial Intelligence (IJCAI 2011)"
produced_by:
  agent: "gpt-5-codex"
  skill: "paper-reader"
  timestamp: "2026-03-28T08:09:11Z"
---
# Revisiting Preferences and Argumentation

## One-Sentence Summary
Revises ASPIC+ so that conflict-freeness is defined using attacks, while preference-filtered defeats are used only for acceptability, and generalizes the framework enough to cover classical-logic instantiations without losing Dung-style properties or the standard rationality postulates. *(pp.1, 5-6)*

## Problem Addressed
Prior ASPIC+ presentations evaluated both conflict-freeness and acceptability using defeats, so preferences could erase attacks too early; the authors argue this obscures the intuitive role of attack and blocks clean coverage of classical-logic-based instantiations that do not assume premise consistency. *(pp.1, 3, 6)*

## Key Contributions
- Replaces defeat-based conflict-freeness with attack-based conflict-freeness while keeping defeats for acceptability only. *(pp.1, 3)*
- Defines a structured abstract argumentation framework (SAF) that separates the attack relation `C` from the defeat relation `D`. *(p.3)*
- Extends abstract ASPIC+ so it can model classical-logic approaches in which inconsistent premise sets are permitted, via `c`-consistency and `c`-SAFs. *(pp.1, 3)*
- Proves subargument closure, closure under strict rules, direct consistency, and indirect consistency for complete extensions under the revised setup. *(pp.5-6)*
- Shows that the common weakest-link ordering satisfies the paper's reasonableness conditions needed by the proofs. *(p.4)*

## Study Design (empirical papers)
Not applicable: this is a theoretical paper consisting of definitions, lemmas, propositions, and proof sketches over structured argumentation frameworks. *(pp.1-6)*

## Methodology
The paper starts from Dung's abstract framework, recalls ASPIC+'s recursive construction of arguments from a language, a contrariness relation, strict rules, defeasible rules, and a partitioned knowledge base, then redefines how preferences enter the semantics. *(pp.1-3)* It keeps syntactic attack notions such as undercutting, rebutting, and undermining at the object level, but evaluates Dung extensions on the derived defeat relation while reserving the raw attack relation for conflict-freeness. *(p.3)* The remainder of the paper proves that, under closure, consistency, and ordering assumptions inherited from ASPIC+, the revised construction retains Dung-style admissibility behavior and satisfies the rationality postulates. *(pp.2, 4-6)*

## Key Equations / Statistical Models

$$
AF = \langle \mathcal{A}, attack \rangle
$$
Where: `\mathcal{A}` is a set of arguments and `attack \subseteq \mathcal{A} \times \mathcal{A}`; a complete extension is a conflict-free set containing every argument it defends. *(p.1)*

$$
AS = (\mathcal{L}, -, \mathcal{R}, n)
$$
Where: `\mathcal{L}` is the logical language, `-` is the contrariness function, `\mathcal{R} = \mathcal{R}_s \cup \mathcal{R}_d` splits strict and defeasible rules, and `n` names defeasible rules in the language. *(p.2)*

$$
K = K_n \cup K_p \cup K_a
$$
Where: `K_n` are axioms that cannot be attacked, `K_p` are ordinary premises that can be attacked, and `K_a` are assumptions whose attacks always succeed in the assumption-based-argumentation style. *(p.2)*

$$
SAF = \langle \mathcal{A}, \mathcal{C}, \preceq \rangle
$$
Where: `\mathcal{A}` is the set of structured arguments, `\mathcal{C}` is the attack relation, and `\preceq` is an argument preference ordering; the induced defeat relation `\mathcal{D}` is used for Dung semantics, but conflict-free sets are defined by `\mathcal{C}`, not by `\mathcal{D}`. *(p.3)*

$$
S \subseteq \mathcal{A}\ \text{is conflict free iff}\ \forall X,Y \in S,\ (X,Y) \notin \mathcal{C}
$$
Where: conflict-freeness is attack-based, so a less preferred attacker still prevents coexistence in a conflict-free set even if it does not defeat its target. *(p.3)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Language of well-formed formulas | `\mathcal{L}` | - | formula language | theory-dependent | 2 | Base language for premises and conclusions. |
| Strict rules | `\mathcal{R}_s` | - | rule set | theory-dependent | 2 | Deductive rules; used in closure and consistency results. |
| Defeasible rules | `\mathcal{R}_d` | - | rule set | theory-dependent | 2 | Non-deductive rules; may be undercut by rule-name contraries. |
| Axiom premises | `K_n` | - | subset of `K` | theory-dependent | 2 | Necessary premises; attacks on them are disallowed. |
| Ordinary premises | `K_p` | - | subset of `K` | theory-dependent | 2 | Premises open to undermining attacks. |
| Assumptions | `K_a` | - | subset of `K` | theory-dependent | 2 | Special premises whose attacks always succeed. |
| Attack relation | `\mathcal{C}` | - | binary relation | subset of `\mathcal{A} \times \mathcal{A}` | 3 | Includes undercut, rebut, and undermine variants. |
| Defeat relation | `\mathcal{D}` | - | binary relation | subset of `\mathcal{A} \times \mathcal{A}` | 3 | Derived from attacks plus preferences; fed into Dung semantics. |
| Preference ordering | `\preceq` | - | preorder over arguments | partial preorder | 3-4 | Must satisfy the paper's reasonableness conditions. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Rationality preservation under revised ASPIC+ | theorem/proof result | four postulates shown to hold | - | - | complete extensions of SAFs and `c`-SAFs under stated assumptions | 5-6 |

## Methods & Implementation Details
- Arguments are built recursively: a premise yields a base argument, and applying a strict or defeasible rule to subarguments yields a new argument carrying `Prem`, `Conc`, `Sub`, `TopRule`, `DefRules`, and `StRules` metadata. *(p.2)*
- The framework distinguishes strict, defeasible, firm, and plausible arguments so proofs can track whether a challenge targets defeasible reasoning or non-axiom premises. *(p.2)*
- Attack is decomposed into undercutting defeasible rules, rebutting defeasible conclusions, and undermining ordinary premises, with contrary variants where a contrary rather than contradictory relation is used. *(p.3)*
- A structured abstract argumentation framework uses attack relation `C` for conflict-freeness and preference-aware defeat relation `D` for acceptability computations in the induced Dung framework. *(p.3)*
- To cover classical logic, the paper introduces `c`-consistency: no strict arguments from the premise set may derive contradictory conclusions. A `c`-SAF is a SAF built from a `c`-consistent underlying theory. *(p.3)*
- The ordering assumptions are calibrated so strict-and-firm arguments are never outranked by plausible ones, strict extensions cannot become weaker than the arguments they extend, and cyclic priority patterns over the designated comparison sets are excluded. *(p.4)*
- Lemmas establish that defeats against strict extensions can be pushed back to component subarguments and that acceptability can be preserved when extending admissible sets, enabling the later rationality proofs. *(pp.4-5)*

## Figures of Interest
- No figures; the paper is entirely definitional and proof-oriented. *(pp.1-6)*

## Results Summary
The paper proves that switching from defeat-based to attack-based conflict-freeness does not break the desirable proof-theoretic behavior of ASPIC+. *(pp.3-5)* Under the stated structural and ordering assumptions, complete extensions remain closed under subarguments and strict consequence, and their conclusions remain directly consistent; for `c`-SAFs the closure of those conclusions under strict rules is also indirectly consistent. *(p.5)* The authors argue these results support a cleaner conceptual division: attacks capture logical incompatibility among arguments, while defeats capture which attacks are strong enough, given preferences, to matter for justified acceptance. *(pp.1, 5-6)*

## Limitations
The framework still depends on nontrivial assumptions: the argumentation system must satisfy closure under contraposition, axiom consistency, and well-formedness, and the preference ordering must be reasonable. *(pp.2, 4)*
The paper explicitly notes that unrestricted rebut remains problematic in settings where asymmetric rebut succeeds; preserving consistency there may require a different treatment such as undercutting-style attacks. *(p.6)*
Future work is needed to extend the attack-based notion of conflict to structured extended argumentation frameworks (EAFs) and to analyze monotonicity questions for the induced `c`-AFs. *(p.6)*

## Arguments Against Prior Work
- Prior ASPIC+-style accounts that define conflict-free sets using defeats let preferences determine too early which logical incompatibilities count, whereas conflict-freeness should track attacking arguments as such. *(pp.1, 3)*
- Classical-logic-based approaches are excluded if the abstract framework requires premise consistency; the authors argue that abstract ASPIC+ should instead admit inconsistent premise sets and recover consistency at the extension level. *(pp.1, 3, 6)*
- The counterproposal of extending attacks to non-top-level rebuts in order to recover consistency is criticized because it does not exploit information inside the arguments and forces all attacks to rely on preference evaluation, even when the attack itself is structurally asymmetric. *(p.6)*

## Design Rationale
- Conflict-freeness is defined on `C` because it is about whether arguments attack one another, not about whether an ordering lets one attack prevail dialectically. *(pp.1, 3)*
- Defeats are retained for admissibility and acceptability because those notions ask whether an attacker should count against a candidate justified argument after preferences are considered. *(pp.1, 3)*
- The extra premise partition `K_n`, `K_p`, `K_a` allows the abstract framework to encode classical axioms, ordinary premises, and assumption-style premises within one recursive argument-construction scheme. *(p.2)*
- The `c`-SAF generalization is introduced so ASPIC+ can represent classical logic instantiations without forcing global premise consistency, while still recovering consistency at extension level through theorem proofs. *(pp.1, 3, 5-6)*

## Testable Properties
- In every SAF built under this paper's proposal, conflict-free sets are defined by the absence of attacks in `C`, not by the absence of defeats in `D`. *(p.3)*
- If `A` belongs to a complete extension `E`, then every subargument of `A` also belongs to `E`. *(p.5)*
- If a complete extension contains arguments whose conclusions strictly imply `\varphi`, then a strict argument for `\varphi` is also in the extension. *(p.5)*
- For any SAF or `c`-SAF satisfying the paper's assumptions, the set of conclusions of a complete extension is directly consistent. *(p.5)*
- For any `c`-SAF satisfying the paper's assumptions, the strict closure of the conclusions of a complete extension is consistent. *(p.5)*
- The weakest-link lifting of premise/rule preferences satisfies the paper's definition of a reasonable ordering. *(p.4)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation layer because it gives the shorter, proof-focused 2011 case for the same attack-vs-defeat separation that later becomes central in the full 2013/2018 ASPIC+ account. *(pp.1, 5-6)* If propstore needs preference handling over structured arguments, this paper supports implementing conflict-freeness over raw attacks and reserving preference comparisons for the defeat relation used in admissibility and complete/grounded reasoning. *(pp.3, 5-6)*

## Open Questions
- [ ] Which of propstore's current or planned preference policies line up with the paper's reasonableness constraints, especially the conditions on strict extensions and cyclic comparisons? *(p.4)*
- [ ] Does propstore need unrestricted rebut, and if so, should that be modeled as rebut, undercut, or a separate attack family to preserve consistency? *(p.6)*
- [ ] Should the project adopt the `K_a` assumption partition explicitly, or is ordinary-premise handling sufficient for the intended use cases? *(p.2)*

## Related Work Worth Reading
- Prakken (2010), "An abstract framework for argumentation with structured arguments" for the base ASPIC+ setup that this paper revises. *(pp.1-2, 6)*
- Amgoud and Vesic (2010), "Generalizing stable semantics by preferences" for the semantics-level preference alternative explicitly discussed and criticized here. *(pp.1, 6)*
- Modgil (2009), "Reasoning about preferences in argumentation frameworks" for the unrestricted-rebut and asymmetric-attack issues discussed in the conclusion. *(p.6)*
- Amgoud and Besnard (2009), "Bridging the gap between abstract argumentation systems and logic" for the classical-logic line that motivates the paper's generalized abstraction. *(pp.1, 3, 6)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as the underlying abstract framework whose complete-extension semantics and attack/defense vocabulary are preserved.
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — cited as the immediate ASPIC+ predecessor whose defeat-based notion of conflict-freeness this paper revises.
- [[Amgoud_2002_ReasoningModelProductionAcceptable]] — cited as an earlier preference-based argumentation model that motivates the paper's insistence on separating attacks from preference-filtered defeats.
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — cited for the rationality postulates the revised framework is designed to preserve.

### New Leads (Not Yet in Collection)
- Amgoud and Besnard (2009) — "Bridging the gap between abstract argumentation systems and logic" — classical-logic motivation for the paper's generalized abstraction.
- Amgoud and Vesic (2010) — "Generalizing stable semantics by preferences" — semantics-level preference proposal explicitly criticized here.
- Kaci (2010) — "Refined preference-based argumentation frameworks" — nearby alternative preference framework cited in the comparison set.

### Cited By (in Collection)
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — listed as the IJCAI response to that paper's critique of attack-removal approaches.
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — cites this short IJCAI paper as part of the line leading to the fuller general account of preference-based defeat.
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — points to this paper as the modern ASPIC+ formulation integrating Pollock-style defeasible reasoning with structured argumentation.
- [[Wei_2012_DefiningStructureArgumentsAIModelsArgumentation]] — cites it in the landscape of formal models of argument structure.

### Conceptual Links (not citation-based)
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — Strong. The later full account expands the same attack-vs-defeat separation defended here and situates it against a broader range of preference formalisms.
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — Strong. This paper is the corrective bridge from Prakken's 2010 ASPIC abstract framework to the later attack-based conflict-freeness view.
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — Strong. Direct dispute pair: Amgoud and Vesic argue preferences should act at the semantics layer without deleting conflicts, and this paper responds from the ASPIC+ side by keeping attacks for conflict-freeness but defeats for acceptability.
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — Moderate. The journal ASPIC+ paper develops the same structured-argument machinery in a fuller setting, with this IJCAI paper supplying the concise preference-handling correction.
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — Moderate. Pollock's influence is used there to contextualize the modern ASPIC+ framework that this paper helps crystallize.
