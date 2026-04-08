# Local Models Semantics, or Contextual Reasoning = Locality + Compatibility

**Authors:** Chiara Ghidini, Fausto Giunchiglia
**Year:** 2001
**Venue:** Artificial Intelligence 127(2), pp. 221-259
**DOI:** 10.1016/S0004-3702(01)00064-9

## Summary

Defines Local Models Semantics (LMS), a formal semantics for contextual reasoning grounded in two principles:

1. **Locality**: Reasoning uses only part of what is potentially available; that part is the "context"
2. **Compatibility**: There is agreement among reasoning performed in different contexts

## Core Constructs

### Model Theory

- **Languages**: Family {L_i} of (first-order) languages indexed by I, each describing what is true in a context
- **Local models**: Standard Tarskian models m of a language L_i
- **Compatibility sequence**: c = <c_0, c_1, ..., c_i, ...> where each c_i is a subset of the models of L_i
- **Compatibility relation**: C = set of compatibility sequences; C is a subset of the product of powersets of model classes
- **Model**: A non-empty compatibility relation not containing the all-empty sequence
- **Chain model**: Every c_i is a singleton (complete contexts)
- **Weak chain model**: Every c_i has cardinality <= 1 (complete or inconsistent contexts)

### Contexts

A context c_i is the set of local models allowed by C within a compatibility sequence. Contexts are **partial objects** (sets of models), unlike possible worlds which are complete. This is a key advantage: a formula can be neither true nor false in a context when some local models satisfy it and others don't.

### Satisfiability and Logical Consequence

- **Local satisfiability**: Classical satisfiability m |=_cl phi
- **Satisfiability**: C |= i:phi iff for all c in C, all m in c_i satisfy phi
- **Logical consequence** (Def 3.6): Gamma |=_C i:phi if every sequence c in C satisfies: assumptions in other contexts (Gamma_j, j != i) prune sequences, then remaining local models in c_i that satisfy Gamma_i must satisfy phi
- Extends local logical consequence: if Gamma_i |=_cl phi then Gamma |= i:phi

### Multi-Context Systems (Proof Theory)

- MC system MS = <{T_i}, Delta_br> where T_i = <L_i, Omega_i, Delta_i> is an axiomatic system
- **Internal rules**: Operate within a single language/context
- **Bridge rules**: Have premises and conclusions in different languages; formalize compatibility
- Deductions are trees using both internal and bridge rules
- Context c_i (proof-theoretic) = set of L_i-formulae in the deductive closure Th(MS)

## Two Examples

### 1. Reasoning with Viewpoints (Magic Box)

- Two observers (Mr.1, Mr.2) with partial views of a box with sectors containing balls
- L_1 = {r, l} (right, left); L_2 = {r, c, l} (right, center, left)
- Compatibility constraints: if one sees balls, the other does too; observers have complete views (chain model)
- V-models: chain models satisfying the constraints
- MC system MV with bridge rules br12, br21 (ball existence propagation) and bot_12, bot_21 (cross-context reductio)
- **Soundness and completeness** proved (Appendix A) via canonical model construction

### 2. Reasoning about Belief (HMB Systems)

- Agent a with beliefs about beliefs, organized in infinite chain of belief contexts
- All contexts use same language L(B) with propositional letters + belief predicate B("phi")
- **Rdw rule**: If B("phi") in c_i, then phi in c_{i+1} (downward reflection)
- **Rupr rule**: If phi derivable in c_{i+1} from assumptions with index < i+1, then B("phi") in c_i (upward reflection, with restriction)
- Three systems: Rdw-only, Rupr-only, MBK (both)
- MBK is theorem-equivalent to minimal normal modal logic K
- **Soundness and completeness** proved (Appendix B)
- Framework can model agents with bounded reasoning capabilities

## Comparison with Other Frameworks

- **vs Possible Worlds**: LMS has multiple local languages (no single global language), local models are Tarskian (not modal), satisfiability is independent of model structure, contexts are partial objects
- **vs Guha's contexts**: Guha uses single global language with three-valued logic for meaningless formulae
- LMS provides more general foundation applicable beyond modal logics

## Relevance to Propstore

**High relevance.** This paper provides formal foundations directly applicable to propstore's context system:

1. **Contexts as partial objects**: Propstore contexts hold partial information; LMS formalizes this as sets of models rather than single worlds
2. **Multiple local languages/theories**: Different propstore contexts can have different vocabularies and inference capabilities, matching LMS's local languages
3. **Compatibility via bridge rules**: Propstore's cross-context relationships (context exclusions, context dependencies) are bridge rules
4. **Non-commitment**: LMS's compatibility relations allow multiple compatible combinations without forcing a single interpretation---directly aligned with propstore's non-commitment discipline
5. **Belief modeling**: The HMB framework for reasoning about beliefs maps to propstore's stance system where agents hold beliefs about claims
6. **Formal consequence**: The labelled formula i:phi and cross-context logical consequence provide a formal basis for propstore's render-time reasoning across contexts

The paper also connects to Distributed First Order Logics (DFOL) for heterogeneous knowledge base federation, which is directly relevant to propstore's use case of integrating heterogeneous knowledge sources.

---

**See also:** [[McCarthy_1993_FormalizingContext]] - Ghidini's Local Models Semantics provides the rigorous model-theoretic foundation for the multi-context systems that McCarthy's 1993 paper sketches informally. McCarthy's lifting rules correspond to Ghidini's bridge rules; McCarthy's ist(c,p) maps to Ghidini's labelled formulas i:phi.
