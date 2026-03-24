# Research: Reified Queries / Materialized Scenarios as Knowledge Artifacts

Session: 2026-03-23

## Goal

Survey foundational and applicable literature for designing **materialized queries/scenarios** as a new primitive in propstore. A scenario binds inputs, runs derivation chains under a resolution policy, stores the result with full dependency tracking, and becomes a referenceable, arguable artifact.

---

## 1. Reified Queries / Materialized Views in Knowledge Representation

### Calvanese, De Giacomo, Lembo, Lenzerini, Rosati. "View-Based Query Answering over Description Logic Ontologies." KR 2008, pp. 242-251.

Defines the problem of answering queries using only precomputed view answers in the context of DL ontologies (not just relational databases). Introduces two notions of view-based query answering grounded in certain answers. Directly relevant: views over ontologies are reified query results that can be reasoned about -- the closest DL analogue to our materialized scenarios.

### Bienvenu, Ortiz. "Ontology-Mediated Query Answering with Data-Tractable Description Logics." Reasoning Web 2015, Springer LNCS.

Survey of ontology-mediated query answering (OMQA), where an ontology and a query are composed into an "ontology-mediated query" (OMQ) -- effectively reifying the query+ontology pair as a single artifact. Relevant for the idea that the query itself becomes a first-class composite object with its own semantics and tractability properties.

### Volz, Staab, Motik. "Incremental Maintenance of Materialized Ontologies." OTM 2003, Springer LNCS; extended version in J. Data Semantics 2005.

Addresses how to maintain materialized entailments when the underlying ontology changes. Proposes incremental update techniques that avoid full recomputation. Directly relevant to our invalidation problem: when upstream claims change, which materialized scenarios need recomputation?

---

## 2. Assumption-Based Derivation Provenance

### de Kleer. "An Assumption-Based TMS." Artificial Intelligence 28(2), 1986, pp. 127-162.

The foundational ATMS paper. Every derived datum is labeled with the minimal sets of assumptions on which it depends. Context switching is free -- you never retract, you just change which assumptions are "in." This is the core architecture propstore already draws on: our materialized scenarios should carry ATMS-style labels so that when assumptions change, we know exactly which results are affected.

### Doyle. "A Truth Maintenance System." Artificial Intelligence 12(3), 1979, pp. 231-272.

The original justification-based TMS (JTMS). Every belief records its justification (the inference step that produced it). Supports dependency-directed backtracking. Relevant as the origin of the idea that derived facts must carry their derivation provenance, which is exactly what materialized scenarios need.

### Forbus, de Kleer. "Building Problem Solvers." MIT Press, 1993.

The definitive implementation guide for JTMS, ATMS, and constraint systems. Chapters on ATMS cover context management, assumption sets, and how to use the ATMS for focused problem solving. Essential reference for the engineering of our scenario dependency tracking.

### Green, Karvounarakis, Tannen. "Provenance Semirings." PODS 2007, pp. 31-40.

Shows that provenance for positive relational algebra can be captured uniformly using commutative semirings of polynomials. Each output tuple is annotated with a polynomial over input tuple identifiers, encoding "how" and "why" it was derived. Directly applicable: our derivation chains produce results that could carry semiring annotations showing exactly which input claims contributed and how.

### Buneman, Khanna, Tan. "Why and Where: A Characterization of Data Provenance." ICDT 2001, Springer LNCS, pp. 316-330.

Distinguishes "why-provenance" (which source tuples influenced the existence of a result) from "where-provenance" (which source locations a value was copied from). Foundational taxonomy for our design: materialized scenarios need both why-provenance (which claims) and where-provenance (which specific values from which claim fields).

### Cheney, Chiticariu, Tan. "Provenance in Databases: Why, How, and Where." Foundations and Trends in Databases 1(4), 2009, pp. 379-474.

Comprehensive survey unifying why, how, and where provenance. Covers applications in confidence computation, view maintenance, debugging, and annotation propagation. The definitive reference for understanding the design space of provenance representations -- essential reading before committing to a provenance model for scenarios.

---

## 3. Persistent Inference Results / Incremental Reasoning

### Urbani, Margara, Jacobs, van Harmelen, Bal. "DynamiTE: Parallel Materialization of Dynamic RDF Data." ISWC 2013, Springer LNCS, pp. 657-672.

Addresses incremental materialization of RDF entailments under additions and deletions. Uses parallel semi-naive evaluation for additions, and two deletion algorithms (one avoiding full input scans). Relevant engineering model: when upstream claims are added/removed, how to incrementally update materialized scenarios rather than recomputing from scratch.

### Rabbi, MacCaull, Faruqui. "A Scalable Ontology Reasoner via Incremental Materialization." IEEE CBMS 2013, pp. 221-226.

Identifies the fragment of an ontology affected by ABox/TBox changes, reducing recomputation. Relevant to our narrower problem: given a change to one claim, which materialized scenarios actually need updates?

### Blazegraph. "Inference and Truth Maintenance." (Documentation, blazegraph/database wiki.)

Production system implementing incremental truth maintenance for RDF. On triple addition, forward-chains new entailments. On removal, uses proof chains to determine which inferences can still be proven and retracts those that cannot. Practical existence proof that TMS-style invalidation works at scale for materialized inferences.

---

## 4. Nanopublications / Micropublications

### Groth, Gibson, Velterop. "The Anatomy of a Nanopublication." Information Services & Use 30, 2010, pp. 51-56.

Defines the nanopublication as three named graphs: assertion (the claim), provenance (how the claim was derived), and publication info (metadata about the nanopub itself). Directly maps to our scenario structure: a materialized result is an assertion, its derivation chain is provenance, and its resolution policy / input bindings are publication info.

### Clark, Ciccarese, Goble. "Micropublications: A Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications." Journal of Biomedical Semantics 5:28, 2014.

Goes beyond nanopublications by modeling the full argument structure: claims, evidence, support, challenge, and commentary. Minimal form = statement + attribution; maximal form = statement + complete supporting argument with evidence and challenges. This is almost exactly what a propstore scenario should be: a derived claim with its full argument chain, open to challenge and comparison.

### Carroll, Bizer, Hayes, Stickler. "Named Graphs, Provenance and Trust." WWW 2005, pp. 613-622.

Extends RDF with named graphs to enable statements about graphs (provenance, trust, signatures). Provides the formal foundation for grouping related statements and attaching metadata. Relevant architectural pattern: each materialized scenario is a named graph with its own provenance and trust assessment.

### W3C. "PROV-DM: The PROV Data Model." W3C Recommendation, 2013.

Standard data model for provenance: entities, activities, agents, derivations, and bundles (provenance of provenance). Six components covering creation/use/end times, entity-to-entity derivations, agent responsibility, bundles, identity linking, and collections. Our scenario provenance should be expressible in PROV-DM terms for interoperability, even if the internal representation is richer.

---

## 5. Hypothetical / Counterfactual Reasoning as Stored Artifacts

### Halpern, Pearl. "Causes and Explanations: A Structural-Model Approach." British Journal for the Philosophy of Science 56(4), 2005.

Part I (Causes) and Part II (Explanations). Uses structural equations to model counterfactuals. An explanation is a fact that, if true, would constitute an actual cause. Relevant: our hypothetical scenarios are structural equation models where we intervene on variables (add/remove claims) and observe effects. The Halpern-Pearl framework gives us formal criteria for when a scenario result counts as an explanation.

### Dixon. "Assumption-Based Context Switching in an ATMS = Partial-Meet AGM Contraction." Unpublished manuscript, 1993 (cited in propstore CLAUDE.md).

Shows that ATMS context switching (choosing which assumptions are "in") is equivalent to AGM belief revision operations. Directly foundational: each materialized scenario corresponds to a specific ATMS context (assumption set), and switching between scenarios is formally an AGM operation.

### Gardenfors. "Knowledge in Flux: Modeling the Dynamics of Epistemic States." MIT Press, 1988.

The definitive treatment of AGM belief revision. Defines contraction, expansion, and revision as rational operations on belief states, governed by postulates. Scenarios that add/remove claims are performing AGM operations; Gardenfors provides the rationality criteria these operations must satisfy.

---

## 6. Cyc's Persistence of Inference / Microtheories

### Lenat, Guha. "Building Large Knowledge-Based Systems: Representation and Inference in the Cyc Project." Addison-Wesley, 1990.

Describes Cyc's architecture including the partitioning of knowledge into microtheories -- locally consistent knowledge bundles with context-specific assumptions. Inference uses a community-of-agents architecture with specialized modules. Relevant: microtheories are the closest production system to our "worlds" concept, and Cyc's struggles with scaling inference are cautionary tales for materialization.

### Guha. "Contexts: A Formalization and Some Applications." PhD Thesis, Stanford University, 1991. Also MCC Tech Report ACT-CYC-423-91.

Formalizes Cyc's microtheories. Each has its own axioms and vocabulary. "Lifting axioms" relate truth in one context to truth in another. This is the formal machinery for inter-scenario reasoning: if scenario A derives X under assumptions P, and scenario B derives Y under assumptions Q, lifting axioms let us reason about X and Y together.

---

## 7. Belief Spaces / Multiple Worlds

### Martins, Shapiro. "Reasoning in Multiple Belief Spaces." IJCAI 1983, Karlsruhe, pp. 370-373.

Introduces the concept of multiple, possibly contradictory belief spaces that a problem-solver can consider simultaneously. Context switching between belief spaces is essentially free. Foundational for propstore's world model: each materialized scenario lives in a belief space, and the system can maintain and compare multiple such spaces without committing to one.

### Martins, Shapiro. "A Model for Belief Revision." Artificial Intelligence 35(1), 1988, pp. 25-79.

Extends the multiple belief spaces idea with formal belief revision within the SNePS framework. The system automatically computes dependencies among propositions using the rules of inference. Relevant: provides a concrete implementation model for how derived scenario results can be automatically revised when underlying beliefs change.

### Ghidini, Giunchiglia. "Local Models Semantics, or Contextual Reasoning = Locality + Compatibility." Artificial Intelligence 127(2), 2001, pp. 221-259. (Original version KR 1998.)

Formalizes contextual reasoning via two principles: locality (reasoning uses only part of available knowledge) and compatibility (different contexts must be mutually coherent). Multi-context systems formalize information flow between contexts. Directly applicable: each materialized scenario is a local context, and compatibility constraints define how scenarios relate to each other and to the base knowledge.

---

## 8. Provenance in Argumentation

### Odekerken, Lehtonen, Testerink, Prakken, Borg. "Argumentative Reasoning in ASPIC+ under Incomplete Information." KR 2023, pp. 531-541.

Studies stability and relevance in ASPIC+ with incomplete information. Stability asks: will an argument's status survive any possible completion of the missing information? Relevance asks: does a specific piece of missing information matter? Directly applicable: when a materialized scenario has incomplete upstream data, these results tell us whether the scenario's conclusions are stable or could flip.

### Dvorak, Rapberger, Woltran. "Choices and their Provenance: Explaining Stable Solutions of Abstract Argumentation Frameworks." ProvenanceWeek 2025 / arXiv:2506.01087.

Identifies minimal critical attack sets underlying each stable extension, providing a provenance overlay that explains why a particular extension was chosen. The grounded extension needs no such provenance (it is deterministic), but stable extensions involve non-deterministic choice. Directly relevant: when a materialized scenario uses preferred or stable semantics, this paper tells us how to track and explain the choices that produced the result.

### Timmer, Meyer, Prakken, Renooij, Verheij. "A Two-Phase Method for Extracting Explanatory Arguments from Bayesian Networks." International Journal of Approximate Reasoning 80, 2017, pp. 475-494.

Translates Bayesian network information into ASPIC+ argumentation frameworks to produce human-readable explanations. Relevant pattern: a materialized scenario's numerical derivation chain (SymPy/parameterization) could be translated into arguments for explanation and challenge.

---

## Design Implications for Propstore

Based on this survey, a materialized scenario should be:

1. **A named artifact** with identity (content-hash, like nanopublications)
2. **Labeled with assumptions** (ATMS-style: which claims are assumed, which resolution policy)
3. **Carrying full derivation provenance** (why-provenance at minimum; how-provenance via semiring annotations if we want to support sensitivity analysis)
4. **Incrementally maintainable** (dependency graph enables targeted invalidation when upstream claims change, rather than full recomputation)
5. **Arguable** (scenarios can be challenged, compared, and can serve as premises in further argumentation)
6. **Composable** (one scenario's output can be another's input, with lifting axioms a la Guha connecting contexts)
7. **Explanation-ready** (the provenance trail supports generating human-readable justifications, especially for non-deterministic choices in preferred/stable semantics)

Key open questions:
- How heavy should the provenance be? Semiring polynomials are maximally informative but expensive. ATMS labels (assumption sets only) are lightweight but lose "how" information.
- Should scenarios be eagerly or lazily materialized? ATMS is lazy (labels are always current); materialized views are eager (precomputed, then maintained). Hybrid approaches exist.
- How do we handle scenarios that reference other scenarios? Guha's lifting axioms provide the formal machinery, but the engineering complexity is significant.
