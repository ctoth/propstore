---
title: "Defining the structure of arguments with AI models of argumentation"
authors: "Bin Wei, Henry Prakken"
year: 2012
venue: "Proceedings of the ECAI-12 Workshop on Computational Models of Natural Argument (CMNA-12)"
doi_url: ""
pages: "1-5"
---

# Defining the structure of arguments with AI models of argumentation

## One-Sentence Summary
Recasts the informal-logic taxonomy of argument structure inside ASPIC+ and argues that the right distinction is between the type of an individual argument and the structure formed by multiple arguments, which makes Vorobej's "hybrid argument" category unnecessary. *(p.1-5)*

## Problem Addressed
The paper studies a long-running ambiguity in the standard informal-logic treatment of argument structure associated with Walton, Freeman, and related work. The standard account distinguishes atomic, convergent, linked, serial, divergent, and sometimes hybrid arguments, but the boundaries between these categories are unclear and some categories appear to mix properties of single arguments with properties of collections of arguments. *(p.1-2)*

The authors identify two concrete problems. First, the standard approach does not cleanly distinguish between types of individual arguments and types of argument structures. Second, once that distinction is blurred, Vorobej's proposed "hybrid" category looks necessary even though it is arguably an artifact of the taxonomy rather than a real additional type. *(p.1-2, p.4-5)*

## Key Contributions
- Reconstructs the informal standard approach to argument structure inside the formal ASPIC+ framework. *(p.1-3)*
- Distinguishes **argument types** from **argument structures**, instead of treating all structural labels as belonging to the same level. *(p.1-2, p.4-5)*
- Defines three types of individual arguments in the formal setting: **unit**, **linked**, and **multiple** arguments. *(p.2-3)*
- Defines argument-structure categories such as **serial divergent**, **linked convergent**, and related mixed structures over sets of arguments rather than over single arguments. *(p.3-4)*
- Argues that, once the formal distinction is made, Vorobej's hybrid-argument category is not needed. *(p.1, p.4-5)*

## Methodology
The paper proceeds by taking the standard informal examples of argument structure and translating them into ASPIC+. ASPIC+ provides a recursively generated notion of arguments, explicit subargument structure, and a distinction between strict and defeasible inferences. The authors then use that formal machinery to define types of individual arguments and types of structures over sets of arguments, and finally show how the standard approach can be reconstructed without introducing hybrid arguments as a primitive category. *(p.1-5)*

## Formal Background Reused from ASPIC+
The paper uses ASPIC+ as the formal metalanguage. In the simplified setup used here, an argumentation system is an abstract tuple over a language, a contrary relation, a rule set partitioned into strict and defeasible rules, and a naming function for defeasible rules. A knowledge base is split into premises, and arguments are recursively generated from premises and rule applications. *(p.2)*

Arguments are associated with the usual ASPIC+ functions such as:
- `Prem(A)` for the premises used in argument `A` *(p.2)*
- `Conc(A)` for the conclusion of `A` *(p.2)*
- `Sub(A)` for the set of subarguments of `A` *(p.2)*
- `TopRule(A)` for the last applied rule in `A` when `A` is non-atomic *(p.2)*

This formalization matters because the paper's core claim depends on the recursive structure of arguments: what counts as linked, multiple, serial, or divergent is recovered from how subarguments and inference steps are organized. *(p.2-4)*

## Key Equations

$$
AS = (L, C, R, n)
$$

Where:
- `L` is the logical language
- `C` is the contrary relation
- `R` is the rule set, partitioned into strict and defeasible rules
- `n` names defeasible rules for undercutting and related ASPIC+ machinery
*(p.2)*

$$
AT = (AS, K)
$$

Where:
- `AS` is the ASPIC+ argumentation system
- `K` is the knowledge base from which arguments are recursively constructed
*(p.2)*

## Parameters
This is a conceptual and definitional paper. It introduces no numeric hyperparameters, thresholds, or empirical measurement tables. Its operative "parameters" are categorical distinctions between kinds of arguments and kinds of structures. *(p.1-5)*

## Standard Informal Taxonomy Reviewed
The paper reviews the familiar informal categories of atomic, convergent, linked, serial, and divergent arguments. In the standard presentation, these are usually illustrated with diagrammatic patterns rather than recursively defined argument objects. The authors argue that this becomes problematic once one tries to decide whether a phenomenon belongs to a single argument or to a combination of arguments. *(p.1-2)*

Figure 1 collects the standard diagrams. The important point is not the pictures themselves, but that the pictures mix two levels:
- some patterns describe how one conclusion depends on one or several premises within a single argument *(p.1-2)*
- other patterns describe how several arguments share premises or conclusions across a larger structure *(p.1-2)*

## Vorobej's Hybrid-Argument Proposal
The paper explicitly engages Vorobej's critique of the standard approach. Vorobej argues that the standard taxonomy should distinguish types of arguments from types of argument structures and proposes "hybrid arguments" to capture cases that combine features of serial and linked/convergent organization. *(p.1-2)*

Wei and Prakken agree with the need to distinguish levels, but they reject the need for hybrid arguments as a separate primitive category. Their claim is that the hybrid cases can be reconstructed once ASPIC+ is used to formalize both individual arguments and relations among arguments more carefully. *(p.1, p.4-5)*

## Core Definitions

### Unit Argument
A **unit argument** is the formal counterpart of the simplest case: one premise leading to one conclusion. This corresponds to the atomic case in the standard approach. It is an individual argument type, not a structure over several arguments. *(p.2-3)*

### Linked Argument
A **linked argument** is an individual argument in which multiple premises function together in a single inferential step. The key idea is joint support: the premises belong to the same argument and jointly support the conclusion. *(p.2-3)*

### Multiple Argument
A **multiple argument** is an individual argument type that packages more than one line of support. The paper uses this category where the standard approach would often speak of convergent support, but the formal point is that ASPIC+ can separate the internal type of the argument from the broader configuration in which it occurs. *(p.2-3)*

### Argument Structures
Once individual arguments are typed, the paper then defines **argument structures** over sets of arguments. These include serial and divergent patterns and mixed forms built from combinations of subarguments and support relations. This is the level at which the paper relocates many cases that the informal literature treats too loosely. *(p.3-4)*

## Formal Results

### Proposition 1
Every argument is of exactly one argument type. In the paper's reconstruction, the types are mutually exclusive and collectively exhaustive at the level of individual arguments. This is a key cleanup result because it eliminates the overlapping classifications that motivate hybrid categories in the informal literature. *(p.3)*

### Corollary
Because every individual argument has exactly one type, mixed cases should be described at the structural level rather than by multiplying the set of primitive argument types. This is what allows the paper to preserve the intuition behind hybrid cases without treating "hybrid" as a fourth basic type beside unit, linked, and multiple. *(p.3-5)*

## Figures of Interest
- **Figure 1 (p.1):** Standard informal diagrams for atomic, convergent, linked, serial, divergent, and hybrid patterns. This is the paper's starting point and the source of the taxonomy it later repairs.
- **Figure 2 (p.3):** Concrete ASPIC+ argument example showing recursive argument construction and the relation between premises, subarguments, and conclusions.
- **Figure 3 (p.3):** Formal argument-type diagrams used to support the claim that every individual argument falls into exactly one type.
- **Figure 4 (p.4):** Argument-structure diagrams showing how mixed structures should be represented as structures over sets of arguments rather than as new basic argument types.
- **Figure 5 (p.5):** Hybrid-style examples reconstructed in the new framework to show that the standard cases can be represented without adding a hybrid primitive.

## Implementation Details
- Represent **argument type** and **argument structure** as different layers in the data model. Do not encode serial, divergent, linked, convergent, and hybrid as one flat enum. *(p.1-5)*
- Use recursive ASPIC+ argument objects with explicit `Prem`, `Conc`, `Sub`, and `TopRule` accessors so that type classification is computed from structure instead of being manually assigned. *(p.2-3)*
- Treat **unit**, **linked**, and **multiple** as properties of individual arguments. *(p.2-3)*
- Treat **serial**, **divergent**, and mixed patterns as properties of graphs or sets of arguments. *(p.3-4)*
- Do not add a separate "hybrid argument" node type unless your formalism genuinely lacks the ability to distinguish argument-level and structure-level properties. In ASPIC+, that extra type is unnecessary. *(p.4-5)*
- If the system supports diagram rendering, derive rendered argument diagrams from recursive argument structure rather than storing diagram classes as primary semantics. *(p.1-5)*

## Results Summary
This is not an empirical paper. Its main results are conceptual and classificatory:
- the standard informal taxonomy can be reconstructed inside ASPIC+ *(p.1-5)*
- individual arguments can be given mutually exclusive types *(p.3)*
- mixed or composite cases belong at the level of argument structure rather than argument type *(p.3-4)*
- Vorobej's hybrid-argument category is not needed once the formal distinction is made *(p.4-5)*

## Limitations
- The paper is a short workshop paper, so many definitions are given at a high level rather than proved in a fully developed technical treatment. *(p.1-5)*
- The contribution is taxonomic and formal-conceptual, not algorithmic or empirical; it does not provide implementations, complexity analysis, or experiments. *(p.1-5)*
- The paper depends on adopting ASPIC+ as the formal framework. Readers committed to another structured-argumentation formalism would need a translation of the taxonomy into that framework. *(p.2-5)*

## Arguments Against Prior Work
- The standard informal approach conflates types of individual arguments with types of structures over multiple arguments. The authors treat this as the central defect of the prevailing taxonomy. *(p.1-2)*
- Vorobej's hybrid category is presented as an attempted repair, but the paper argues that it is a symptom of the taxonomy problem rather than a genuine new primitive. *(p.1, p.4-5)*
- Purely diagrammatic treatments are too weak for precise classification because they do not expose the recursive structure needed to determine whether support is joint, parallel, serial, or mixed. *(p.1-3)*

## Design Rationale
- **Why ASPIC+?** Because it provides recursively defined arguments with explicit subargument structure and a clean distinction between strict and defeasible inferences, which is exactly what the argument-structure taxonomy needs. *(p.1-3)*
- **Why distinguish types from structures?** Because otherwise one category system is forced to do two jobs at once: classify a single argument and classify a graph of several arguments. *(p.1-2, p.4)*
- **Why reject hybrid arguments as primitive?** Because mixed cases can be explained compositionally once the two levels are separated. Adding a primitive "hybrid" category hides the real structure. *(p.4-5)*

## Testable Properties
- Every individual argument in the reconstructed system should receive exactly one argument-type label. *(p.3)*
- A structure that mixes serial and linked/convergent behavior should be representable as a composition of typed arguments plus structural relations, without inventing a new primitive argument type. *(p.4-5)*
- Any implementation that stores serial/divergent/convergent/linked as one undifferentiated category layer is at risk of reproducing the ambiguity criticized in the paper. *(p.1-5)*

## Relevance to Project
This paper is directly relevant if propstore needs to model argument diagrams, structured support, or explanations over structured arguments. Its main architectural lesson is that the system should distinguish:
1. the recursive internal type of an argument object
2. the larger support/derivation structure formed by several arguments

That distinction is useful for:
- UI diagrams of reasoning structure *(p.1-5)*
- any future argument-mining representation that wants to map informal diagrams into formal objects *(p.1-3)*
- keeping structured-argumentation schemas compatible with ASPIC+ instead of drifting into ad hoc diagram taxonomies *(p.2-5)*

## Open Questions
- [ ] How should the unit/linked/multiple vs structure-level distinction be encoded in a claim graph or provenance graph meant for interactive use? *(p.1-5)*
- [ ] Would the same taxonomy collapse of "hybrid" occur in other structured-argumentation systems besides ASPIC+? *(p.4-5)*
- [ ] What is the cleanest way to map informal argument-mining outputs into ASPIC+-style typed arguments and structures? *(p.1-5)*

## Related Work Worth Reading
- Walton (1996), *Argument Structure: A Pragmatic Theory* — the main standard-approach source under critique. *(p.1-2)*
- Freeman (2011), *Argument Structure: Representation and Theory* — another core source for the informal taxonomy discussed here. *(p.1-2)*
- Vorobej (1995), *Hybrid Arguments* — the direct foil for the paper's claim that hybrid arguments are not needed. *(p.1-2, p.4-5)*
- Prakken (2010), *An abstract framework for argumentation with structured arguments* — the immediate ASPIC+-style formal background used to make the reconstruction precise. *(p.2)*

## Collection Cross-References

### Already in Collection
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — the fuller ASPIC+ framework tutorial whose recursive argument machinery underwrites the taxonomy used here. *(p.2-3)*
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — related at the informal side of argument-structure and scheme classification, though it focuses on schemes rather than the type/structure split. *(conceptual)*

### New Leads (Not Yet in Collection)
- Prakken (2010), *An abstract framework for argumentation with structured arguments*. *(ref.6)*
- Freeman (2011), *Argument Structure: Representation and Theory*. *(ref.3)*
- Vorobej (1995), *Hybrid Arguments*. *(ref.4)*

### Cited By (in Collection)
- (none found)
