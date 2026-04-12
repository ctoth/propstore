---
title: "Enhancing Context Knowledge Repositories with Justifiable Exceptions"
authors: "Loris Bozzato, Thomas Eiter, Luciano Serafini"
year: 2018
venue: "Artificial Intelligence, Volume 257, Pages 72-126"
doi_url: "https://doi.org/10.1016/j.artint.2017.12.005"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-11T06:50:52Z"
---
# Enhancing Context Knowledge Repositories with Justifiable Exceptions

## One-Sentence Summary
This paper defines Contextualized Knowledge Repositories (CKRs) with defeasible axioms that allow local contexts to override global knowledge via justified exceptions, provides a complete datalog translation for reasoning, and proves tractability of model checking with coNP-completeness for entailment. *(p.1)*

## Problem Addressed
Standard CKR frameworks propagate global knowledge to all local contexts without exception. In many practical cases, local contexts need to override inherited global knowledge when justified by local evidence (e.g., a global axiom "all Italian restaurants serve Italian food" should be overridable in a local context about a specific fusion restaurant). The paper addresses how to extend the CKR framework with a principled mechanism for defeasible inheritance that (1) allows overriding only when justified by local clashing evidence, (2) preserves the modular two-layer structure, and (3) admits tractable reasoning via datalog translation. *(p.2-3)*

## Key Contributions
- A new syntax and semantics for CKR with defeasible axioms, extending the CKR framework (previously monotonic) with non-monotonic overriding of global axioms at local contexts *(p.3)*
- Global defeasible axioms with "clashing assumptions" — sets of assertions that, if locally instantiated, justify overriding *(p.3)*
- CKR interpretations that distinguish exceptional from non-exceptional instances of defeasible axioms in each local context *(p.3)*
- Characterization of reasoning complexity: model checking in P, satisfiability testing tractable for acyclic CKRs, entailment in coNP (Sigma_2^P for general case) *(p.3, 21-24)*
- A materialization calculus translating CKR reasoning into datalog programs, with soundness and completeness proofs *(p.3, 25-38)*
- CKRev prototype implementation using DLV solver, with scalability experiments *(p.3, 39-49)*

## Methodology
The paper takes a formal/theoretical approach grounded in description logics and logic programming:

1. **Syntax extension**: The DL language SROIQ-RL is extended with defeasible axiom markers D(alpha) and eval() expressions for inter-context propagation *(p.7-9)*
2. **Model-theoretic semantics**: CAS (Clashing Assumption Set) interpretations pair standard CKR interpretations with exception sets; justified CAS models require every exception to be supported by a clashing set *(p.12-15)*
3. **Complexity analysis**: Reductions to/from standard reasoning problems establish tight complexity bounds *(p.20-24)*
4. **Datalog translation**: A complete translation from CKR to datalog programs enables reasoning via answer set computation *(p.25-38)*
5. **Experimental evaluation**: Synthetic CKR benchmarks test scalability across dimensions of context count, ontology size, and defeasibility percentage *(p.40-49)*

## Key Equations / Statistical Models

### CKR Structure

$$
\mathbf{K} = \langle \mathbf{G}, \overline{\mathcal{K}}_G, \mathcal{D}_G \rangle
$$
Where: **G** is a DL knowledge base over the meta-language, $\overline{\mathcal{K}}_G$ is a DL knowledge base over the object language for each module $\mathfrak{m} \in \mathbf{M}$, and $\mathcal{D}_G$ is the set of global defeasible axioms.
*(p.9, Definition 6)*

### CAS Interpretation

$$
\mathfrak{I}_{CAS} = \langle \mathbf{M}, \mathbf{I}, \xi \rangle
$$
Where: **M** is a DL interpretation of the meta-knowledge (upper layer), **I** assigns a DL interpretation $I_\mathfrak{c}$ to each context $\mathfrak{c}$, and $\xi$ assigns an exception set $E_\mathfrak{m} \subseteq \mathcal{E}_\mathfrak{m}$ to each local context module $\mathfrak{m}$.
*(p.13, Definition 10)*

### Clashing Instantiation

$$
\phi_\mathfrak{m}(\mathbf{d}_i) = \text{specialization of } \phi(\mathbf{d}_i) \text{ to module } \mathfrak{m}
$$
Where: $\phi(\mathbf{d}_i)$ is the FO-translation of defeasible axiom $\mathbf{d}_i$, and the specialization restricts it to individuals and assertions in context $\mathfrak{m}$.
*(p.13, Definition 8)*

### Clashing Assumption

$$
(d, \mathfrak{a}) \text{ where } d \in \mathcal{D}_G, \ \mathfrak{a} \subseteq \mathcal{A}(\mathfrak{m})
$$
Where: $d$ is a defeasible axiom, $\mathfrak{a}$ is a satisfiable set of ABox assertions such that $\mathfrak{a}$ is a clashing set for $d$ in module $\mathfrak{m}$ — meaning $\mathfrak{a}$ together with the non-defeasible knowledge entails a violation of $d$.
*(p.13, Definition 9)*

### Justified CAS Model Condition

$$
\forall (d, \mathfrak{a}) \in E_\mathfrak{m}: \exists S \text{ clashing set for } (d, \mathfrak{a}) \text{ in } \mathfrak{I}_{CAS}
$$
Where: a clashing set $S$ is a set of assertions providing the "justification" that the exception to $d$ is warranted — i.e., $S$ is satisfiable and consistent with the local knowledge, and $d$ together with $S$ leads to an inconsistency.
*(p.15, Definition 12)*

### Datalog Translation

$$
P(\mathbf{K}) = P(\mathbf{G}) \cup \bigcup_{\mathfrak{c} \in \mathbf{N}_\mathfrak{c}} P(\mathfrak{c}, \mathbf{K}_\mathfrak{c})
$$
Where: $P(\mathbf{G})$ is the global program encoding the meta-knowledge and global context structure, and $P(\mathfrak{c}, \mathbf{K}_\mathfrak{c})$ for each context $\mathfrak{c}$ encodes its local knowledge with deduction rules $P_d$, defeasible deduction rules $P_D$, and output translation $O$.
*(p.35, step 4)*

### Overriding Rule (Datalog)

$$
\text{instd}(x, z, c, t) \leftarrow \text{insta}(x, z, g, t), \text{prec}(c, g), \text{not ovr}(\text{insta}, x, z, c)
$$
Where: instd = derived instance, insta = asserted instance, prec(c,g) = context c is covered by global context g, ovr = overriding predicate. The "not ovr" condition implements defeasible inheritance: the global axiom applies unless overridden.
*(p.29, rule ovr-instd)*

### Test Rule (Datalog)

$$
\text{test}(\text{nlit}(x, z, c)) \leftarrow \text{def\_insta}(x, y), \text{prec}(c, g)
$$
$$
\leftarrow \text{test\_fails}(\text{nlit}(x, y, c)), \text{ovr}(\text{insta}, x, y, c)
$$
Where: test rules check whether overriding is justified by instantiating a copy of the program with the complement of the tested literal. If the test succeeds (no contradiction found without the overriding), the overriding cannot take place.
*(p.32-34, Table 8)*

### Propagation Rule for Defeasible Axioms

$$
\text{instd}(x, z, c, t) \leftarrow \text{triplea}(x, r, y, g, t), \text{prec}(c, g), \text{not ovr}(\text{triplea}, x, r, y, c)
$$
Where: defeasible role assertions propagate from global to local contexts subject to the same overriding mechanism.
*(p.33, Table 7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of contexts | \|N_c\| | - | - | 1-100 | 41-44 | Test set TS1 parameter |
| Number of classes | \|NC\| | - | - | 10-1000 | 41-44 | Per-context ontology size |
| Number of roles | \|NR\| | - | - | 10-1000 | 41-44 | Equals number of classes in TS1 |
| Number of individuals | \|NI\| | - | - | 20-2000 | 41-44 | 2x number of classes in TS1 |
| Percentage defeasible | Def.% | % | - | 10-100 | 47-48 | TS2: fraction of global axioms marked defeasible |
| Percentage overriding | Ovr.% | % | - | 10-100 | 47-48 | TS2: fraction of defeasible axioms actually overridden locally |
| Global TBox axioms | - | - | - | 10-1000 | 44 | Number of TBox statements in global context |
| Global RBox axioms | - | - | - | 5-500 | 44 | Number of RBox statements in global context |
| Global ABox axioms | - | - | - | 20-2000 | 44 | Number of ABox assertions in global context |
| Local TBox axioms | - | - | - | 10-1000 | 44 | Per local context |
| Local RBox axioms | - | - | - | 5-500 | 44 | Per local context |
| Local ABox axioms | - | - | - | 20-2000 | 44 | Per local context |

## Methods & Implementation Details

### CKR Two-Layer Architecture *(p.7)*
- **Upper layer (meta-knowledge)**: Knowledge graph G defining contexts, their coverage relations, and cross-context structure. Represented as a DL knowledge base over a meta-vocabulary.
- **Lower layer (object knowledge)**: Each context c has a local knowledge module K_c containing locally valid facts. These are DL knowledge bases over the object vocabulary.
- **Coverage relation**: prec(c, g) defines when context c inherits from global context g. This is the mechanism for knowledge propagation — global axioms flow down to covered contexts. *(p.7-8)*

### Defeasible Axiom Mechanism *(p.8-9)*
- A defeasible axiom D(alpha) marks an axiom alpha as overridable. Only global axioms can be defeasible (in this paper's formulation).
- Overriding requires **justification**: a clashing set S must exist that demonstrates the axiom would cause inconsistency if applied without exception.
- The clashing assumption (d, a) pairs a defeasible axiom d with a set of assertions a that provide the basis for the exception.
- **Key design choice**: Overriding is not a blanket mechanism; it operates at the level of individual instances. An individual fbresch can be exceptional w.r.t. "cheap events" while other instances of the same class remain non-exceptional. *(p.8-9)*

### eval() Expressions *(p.8)*
- eval(C, c) and eval(R, C) allow referring to the extension of a concept C or role R in another context c from within the current context.
- These are the mechanism for defeasible propagation of information across contexts.
- eval() expressions can only appear on the left-hand side of concept/role inclusions.

### CAS Model Construction *(p.12-15)*
1. Start with standard CKR interpretation (M, I)
2. For each local context m, compute the clashing assumptions E_m — sets of assertions that justify overriding
3. A CAS interpretation (M, I, xi) extends with exception assignment xi mapping each module to its exception set
4. CAS model conditions: (a) standard CKR model conditions hold for non-exceptional assertions, (b) every exception in E_m is justified by a clashing set
5. Justified CAS model: minimal model satisfying all conditions with justified exceptions *(p.15, Def 12)*

### Normal Form Conversion *(p.25-26)*
- CKR K = (G, E, d_g) is converted to normal form where:
  - All axioms in K are in normal form (Table 2 transformations)
  - Every defeasible axiom in G is of the form D(B) where B is from Table 1
  - The size of normal form is linear in the original (Lemma 5) *(p.25)*

### Datalog Translation Components *(p.28-35)*
The translation has four components:

**(i) Input instantiation rules I_n(S, c)**: Translate SROIQ-RL axioms and ABox assertions into datalog facts. Table 3 lists all rules (irl-nom through irl-irr). *(p.30)*

**(ii) Deduction rules P_d**: Standard SROIQ-RL inference rules for instance-level reasoning. Table 3 lists prl-instd through prl-sat. These implement concept/role subsumption, existential restrictions, universal restrictions, etc. *(p.30)*

**(iii) Defeasible deduction rules P_D**: Three sub-groups:
- **Overriding rules** (Table 6, p.31): ovr-instd, ovr-tripled, etc. — inherit from global with "not ovr()" condition
- **Inheritance rules** (Table 7, p.33): prop-inst, prop-triple, etc. — propagate defeasible axioms with prec(c,g) and not ovr() guards
- **Test rules** (Table 8, p.34): test-inst, constr-inst, test-triple, etc. — verify overriding justification by checking for contradiction

**(iv) Output translation O(a, c)**: Maps derived atoms back to ABox assertions verifiable in each context. *(p.33)*

### CKRev Prototype Architecture *(p.39-40)*
- Java-based command line application
- Input: OWL files or single TBox/RBox DL axioms
- Translates OWL to OWL-RL, then to RDF vocabulary, then to datalog
- Uses DLV solver via DLVWrapper library for answer set computation
- Process: Translate P(G) -> Translate P(c, K_c) -> Merge P_G + P_c -> DLV system -> extract results
- Available on GitHub

### Synthetic CKR Generator *(p.41)*
Generation procedure:
1. Generate contexts (named c_1...c_n) in global context, associated with graph nodes
2. Generate base classes, roles, properties, individuals per context
3. Generate global axioms as random selection criteria (concept inclusions, class/role assertions)
4. Generate defeasible axioms: specified percentage of global axioms marked defeasible
5. Generate overriding: specified percentage of defeasible axioms have local overriding via "fresh" individuals

## Figures of Interest
- **Fig 1 (p.10)**: CKR knowledge base K_ex — complete example showing context hierarchy (CulturalEvent, VolleyMatch, SportsEvent, etc.), coverage relations, knowledge modules, and eval() expressions
- **Fig 2 (p.40)**: CKRev architecture — pipeline from CKR input through translation to DLV evaluation
- **Fig 3 (p.46)**: Scalability graphs for TS1 — log-log plots showing (a) rewriting time and (b) DLV time vs input statements, parameterized by number of contexts (1, 5, 10, 50, 100)
- **Fig 4 (p.49)**: Experiment graphs for TS2 — (a) program size, (b) rewriting time, (c) DLV time vs overriding percentage, parameterized by defeasibility percentage (10%, 30%, 50%, 70%, 100%)

## Results Summary

### Complexity Results *(p.20-24)*
- **Model checking**: Polynomial time for CAS models (Proposition 8, Corollary 1) *(p.21)*
- **Satisfiability**: Tractable when clashing assumptions play no role (Proposition 9); NP-complete in general (Proposition 10) *(p.22)*
- **Entailment**: coNP-complete for global entailment (Corollary 2); polynomial for acyclic CKRs (Proposition 11) *(p.22-23)*
- **Conjunctive query answering**: coNP for combined complexity (Theorem 5) *(p.24)*
- **Data complexity**: Tractable for acyclic CKRs *(p.24)*

### Scalability (TS1) *(p.43-46)*
- Rewriting time grows linearly with number of input statements
- DLV time grows super-linearly (expected for ASP)
- Configurations up to 10 contexts × 1000 classes complete within reasonable time
- 50+ contexts × 500+ classes approach memory limits
- Rewriting time dominated by DLV computation time for large inputs

### Defeasibility Impact (TS2) *(p.47-49)*
- Program size grows linearly with percentage of defeasible axioms and overridings
- Rewriting time grows polynomially with defeasibility percentage
- DLV time is the dominant factor; grows significantly with overriding percentage
- At 100% defeasible / 100% overriding: DLV time reaches ~1.2M ms for the test configuration

## Limitations
- Only **global** defeasible axioms supported; local defeasible axioms are deferred to future work *(p.57-58)*
- No preference ordering among multiple global contexts — would be needed for deciding clashes between inherited defeasible axioms from different global contexts *(p.58)*
- CKR consistency is assumed (no local inconsistencies allowed) *(p.58)*
- eval() operator currently monotonic; defeasible propagation via eval() is future work *(p.58)*
- Scalability limited by ASP solver performance for large numbers of contexts (50+) with large ontologies (500+ classes) *(p.45-46)*
- No comparison with non-contextual defeasible DL reasoners on standard benchmarks *(p.56)*
- Formalism does not handle property inheritance at instance level — only class-level defeasible inclusions *(p.55)*

## Arguments Against Prior Work
- **Non-monotonic MCS [31]**: MCS bridge rules propagate beliefs between contexts, but lack the structured global/local hierarchy of CKR. CKR's coverage relation provides a natural mechanism for defeasible inheritance that bridge rules cannot express directly. *(p.50-51)*
- **Argumentation-based MCS [29]**: Uses local preference ordering on contexts, which is more restrictive than CKR's clashing-assumption-based justification. CKR does not require a total preference order; it uses evidence-based justification. *(p.51-52)*
- **Typicality in DLs [18,19]**: ALC+T and related approaches handle defeasible reasoning within a single knowledge base but lack the modular context structure of CKR. They cannot express that the same individual is typical in one context but exceptional in another. *(p.53-54)*
- **Bonatti et al. [5,7,42]**: Normality concepts (NC) approach cannot distinguish "normal" from "exceptional" at the instance level — it operates at the class level only. CKR's clashing assumptions provide finer-grained, instance-level exception handling. *(p.54-55)*
- **Circumscription-based approaches [58,59]**: Too coarse for contextual reasoning; minimize globally rather than allowing context-specific exceptions. *(p.54)*

## Design Rationale
- **Two-layer architecture**: Separates meta-knowledge (context structure) from object knowledge (domain facts), enabling modular knowledge management. Global axioms can be defined once and inherited by all contexts, with local exceptions where justified. *(p.7)*
- **Clashing assumptions over preferences**: Rather than imposing a preference ordering on axioms (as in most defeasible logics), CKR uses evidence-based justification via clashing sets. An exception is justified only if there is positive evidence (a satisfiable clashing set) that the axiom would cause inconsistency locally. This prevents unmotivated overriding. *(p.13-15)*
- **Datalog translation over tableau**: The translation to datalog programs (rather than tableau-based reasoning) enables reuse of existing ASP infrastructure (DLV, clingo) and provides a clear path to scalability via database technology. *(p.25, 57)*
- **Instance-level exceptions**: Defeasible axioms are overridden per-instance, not per-class. This allows fine-grained exception handling where individual a can be exceptional w.r.t. axiom d while individual b in the same context remains non-exceptional. *(p.8-9)*
- **Test-based justification**: The test rules in the datalog translation (Table 8) implement a "prove by contradiction" strategy: to justify overriding, the system must show that without the exception, a contradiction would arise. This is more conservative than simply allowing any override. *(p.32-34)*

## Testable Properties
- Preference of syntax: the syntactic form of a defeasible axiom (D(C ⊑ D) vs D(A ⊑ B) with A ≡ C, B ≡ D) does not affect the set of CAS models (Proposition 3) *(p.16)*
- Non-monotonicity: adding a defeasible axiom to a CKR can invalidate previously valid entailments (Proposition 4) *(p.17)*
- Named model uniqueness: for every satisfiable clashing assumption set, there exists a unique least justified named CAS model (Theorem 1) *(p.18)*
- CAS model characterization: if K is satisfiable with clashing assumption set xi, then a CAS model exists with (M, I, xi) where M is the least Herbrand model (Theorem 2) *(p.19)*
- Model checking is in P: deciding whether a structure is a CAS model is polynomial (Proposition 8) *(p.21)*
- Entailment is coNP-complete: deciding whether K entails an axiom alpha is coNP-complete in general (Corollary 2) *(p.22)*
- Acyclic CKR entailment is in P: for acyclic CKRs (no cyclic coverage), entailment is polynomial (Proposition 11) *(p.23)*
- Translation correctness: the answer sets of P(K) correspond exactly to justified CAS models of K (Theorem 6) *(p.37)*
- Normal form linearity: converting a CKR to normal form increases size by at most a linear factor (Lemma 5) *(p.25)*
- Rewriting time scales linearly with input size (experimentally confirmed, Figure 3a) *(p.43-46)*

## Relevance to Project
This paper is directly relevant to propstore's context and argumentation layers:

1. **Context formalization**: CKR's two-layer architecture (global context + local contexts with coverage relations) maps directly to propstore's context system (McCarthy 1993 ist(c, p)). The coverage relation provides a formal mechanism for context inheritance that propstore could adopt.

2. **Defeasible reasoning in contexts**: The clashing assumption mechanism provides a principled way to handle exceptions in contextual knowledge — exactly what propstore needs for its "non-commitment discipline." Global claims can be defeasible, with local contexts providing evidence for exceptions.

3. **Datalog translation**: The complete translation from CKR to datalog programs is directly implementable. propstore already has datalog infrastructure; this paper provides the rules needed to extend it with contextual defeasible reasoning.

4. **Connection to ASPIC+**: CKR's clashing assumptions can be viewed as undercutting defeaters in ASPIC+ terms — they attack the applicability of a strict rule (the global axiom) by providing evidence that the rule's conclusion doesn't hold in a specific context.

5. **Instance-level granularity**: CKR's per-instance exception handling aligns with propstore's claim-level granularity. A claim can be defeasible at the individual assertion level, not just at the schema level.

## Open Questions
- [ ] How do CKR clashing assumptions map to ASPIC+ attack relations? Are they undercutting or undermining defeaters?
- [ ] Can CKR's coverage relation be used to formalize propstore's context hierarchy?
- [ ] How does the datalog translation interact with propstore's existing Z3-based condition reasoning?
- [ ] What is the relationship between CKR's eval() expressions and propstore's cross-context references?
- [ ] Can CKR's defeasible axiom mechanism be extended to handle propstore's subjective logic opinions?

## Related Work Worth Reading
- Brewka, Eiter (2007) [31]: Equilibria in heterogeneous nonmonotonic MCS — foundation for multi-context reasoning
- Bikakis, Antoniou (2010) [25]: Defeasible contextual reasoning with argumentation semantics — alternative approach to defeasible MCS
- Giordano et al. (2009) [18]: ALC+T typicality in DLs — non-contextual defeasible DL approach
- Bonatti et al. (2015) [42]: Overriding in DLs via normality concepts — class-level defeasibility
- Bozzato, Eiter, Serafini (2020) [already in collection]: Datalog and Defeasible Reasoning in DL-Lite — extends CKR ideas to DL-Lite
- Brewka, Ellmauthaler, Strass, Wallner, Woltran (2017) [29]: Abstract dialectical frameworks — argumentation semantics for MCS

## Collection Cross-References

### Already in Collection
- [[Bozzato_2020_DatalogDefeasibleDLLite]] — cited as the single-context DL-Lite simplification of this paper's CKR framework; Bozzato 2020 adapts the justifiable exception semantics and clashing assumptions from this paper to the lighter DL-Lite_R language
- [[Antoniou_2007_DefeasibleReasoningSemanticWeb]] — cited as related work on defeasible reasoning in Semantic Web; Antoniou uses well-founded semantics for defeasible logic programs, contrasting with CKR's answer-set-based approach
- [[McCarthy_1993_FormalizingContext]] — cited as foundational work on context formalization; CKR's ist(c, p) style contextualization directly inherits from McCarthy's lifting rules
- [[McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning]] — cited as [58]; CKR explicitly contrasts its "justifiable exception" semantics against circumscription-based defeasibility
- [[Brewka_2010_AbstractDialecticalFrameworks]] — Brewka's work on multi-context systems (MCS) is the primary comparison target; CKR's coverage relations replace MCS bridge rules
- [[Brewka_2013_AbstractDialecticalFrameworksRevisited]] — extended ADF semantics relevant to CKR's argumentation connections
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — Brewka's preferred subtheories are an alternative approach to handling inconsistency that CKR's clashing assumptions formalize differently

### New Leads (Not Yet in Collection)
- Serafini, Homola (2012) — "Contextualized knowledge repositories for the semantic web" — the monotonic predecessor of CKR that this paper extends; essential background for understanding the base framework
- Giordano, Gliozzi, Olivetti, Pozzato (2009) — "ALC+T: a preferential extension of description logics" — primary alternative for defeasible DLs using typicality operators; direct comparison point
- Bonatti, Faella, Petrova, Sauro (2015) — "A new semantics for overriding in description logics" — class-level defeasibility via normality concepts; CKR argues for instance-level granularity over this
- Bikakis, Antoniou (2010) — "Defeasible contextual reasoning with arguments" — argumentation-based approach to defeasible MCS with local preference orderings

### Supersedes or Recontextualizes
- [[Bozzato_2020_DatalogDefeasibleDLLite]] — Bozzato 2020 is a simplification/extension of this paper to DL-Lite_R (single-context). This 2018 paper is the full multi-context CKR treatment with SROIQ-RL expressiveness and hierarchical context coverage.

### Cited By (in Collection)
- [[Bozzato_2020_DatalogDefeasibleDLLite]] — cites this as the foundation for the CKR framework with justifiable exceptions; adapts the clashing assumption mechanism to DL-Lite_R

### Conceptual Links (not citation-based)
**Defeasible reasoning and datalog:**
- [[Maher_2021_DefeasibleReasoningDatalog]] — Both papers compile defeasible reasoning into datalog programs. Maher compiles defeasible logic D(1,1) via metaprogram unfold/fold; Bozzato translates CKR defeasible axioms via overriding/test rules. Different source formalisms (defeasible logic vs. defeasible DL) but converge on datalog as the execution substrate.
- [[Morris_2020_DefeasibleDisjunctiveDatalog]] — Morris extends defeasible reasoning to disjunctive datalog; Bozzato's CKR translation uses standard (non-disjunctive) datalog with answer set semantics. Morris's disjunctive extension could provide richer reasoning over CKR-style knowledge.
- [[Garcia_2004_DefeasibleLogicProgramming]] — DeLP provides argumentation-based defeasible reasoning; CKR's clashing assumptions serve a similar role to DeLP's defeaters but operate at the DL axiom level rather than logic program rules.
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] — Diller grounds ASPIC+ in datalog; Bozzato translates defeasible DL knowledge into datalog. The two could compose: CKR's datalog output could feed into Diller's ASPIC+ grounding for argumentative evaluation of defeasible knowledge.

**Context formalization:**
- [[Ghidini_2001_LocalModelsSemanticsContextual]] — CKR's multi-context architecture draws on local models semantics. Ghidini's bridge rules between local theories map to CKR's inter-context knowledge flow, which CKR's defeasible axioms can override.

**Argumentation connections:**
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — CKR's clashing assumptions can be viewed as undercutting defeaters in ASPIC+ terms. Modgil & Prakken's preference-based framework could formalize the priority ordering that CKR currently lacks among multiple global contexts.
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — ASPIC+ structured argumentation provides an alternative framework for handling the same exception/override problem that CKR addresses via clashing assumptions.

**Non-monotonic reasoning foundations:**
- [[Reiter_1980_DefaultReasoning]] — CKR's defeasible axioms are conceptually similar to Reiter defaults (apply unless exceptional); CKR formalizes the exception mechanism via clashing sets rather than consistency checks.
- [[Goldszmidt_1992_DefeasibleStrictConsistency]] — Goldszmidt addresses interaction of defeasible and strict knowledge; CKR's mechanism for when defeasible axioms conflict with strict local knowledge is a contextualized version of this problem.
