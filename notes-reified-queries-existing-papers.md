# Reified Queries: What Existing Papers Say

**Goal:** For each of the 11 surveyed papers, extract mechanisms relevant to "reified queries" -- the concept of making query results into first-class knowledge artifacts with dependency tracking, provenance, and the ability to be argued about.

---

## Summary Table

| Paper | Derivation Dependencies | Invalidation | Stored vs Ephemeral | Closest Term for "Materialized Query" |
|-------|------------------------|--------------|---------------------|--------------------------------------|
| de Kleer 1986 (ATMS) | Labels: minimal assumption sets per datum | Label recomputation on nogood discovery | All reasoning stored (labels are permanent cache) | **Label** (a datum's label IS a materialized, incrementally maintained query result) |
| de Kleer 1986 (Problem Solving) | Consumer-produced justifications | Consumer architecture: never re-runs, but labels auto-update | Consumers compile once; results permanent | **Consumer output** (compiled inference = stored reasoning) |
| Dixon 1993 | Essential support sets (ES) | Entrenchment recomputation on context switch | ATMS justifications are permanent; AGM entrenchment is recomputed | **Entrenchment encoding** (the AGM state IS a materialized view of ATMS structure) |
| Martins 1983 | Origin sets (OS) | Restriction set (RS) updates on contradiction | Origin sets permanent; restriction sets grow | **Belief Space** (a context-defined projection = materialized query over the network) |
| Martins 1988 | Origin sets + restriction sets (4-tuple supported wffs) | URS rule propagates RS updates | All derivations stored permanently in SNePS network | **Supported wff** (the 4-tuple IS a reified derivation with provenance) |
| Groth 2010 | Named Graph URIs link statement to annotation | No invalidation model | Nanopublications are permanent, citable | **Nanopublication** (a reified, attributed assertion) |
| Clark 2014 | Support graph (DAG of supports/challenges) | No explicit invalidation; challenges model disagreement | Micropublications are persistent artifacts | **Micropublication** (a reified argument with provenance) |
| Carroll 2005 | [No notes available -- only metadata.json exists] | -- | -- | **Named Graph** (per metadata: provenance and trust via graph-level URIs) |
| Doyle 1979 | Justification chains (SL/CP justifications) | Truth maintenance process (7-step algorithm) | All justifications stored; belief status recomputed | **Node with justification-set** (stored reasoning with incremental maintenance) |
| Forbus 1993 | All three TMS families (JTMS/LTMS/ATMS justifications) | JTMS: 2-phase retraction; LTMS: BCP; ATMS: label propagation | Explicit design as cache: "TMS serves as cache for all inferences" | **TMS node** (explicitly described as an "intelligent cache") |
| de Kleer 1984 | Confluence constraint satisfaction + explanation-proofs | State transitions invalidate interpretations | Interpretations stored; causal explanations are proof objects | **Interpretation** (a consistent assignment = materialized query over confluences) |

---

## Per-Paper Analysis

### 1. de Kleer 1986 -- An Assumption-based TMS

**Derivation dependencies:** Every datum is labeled with the minimal sets of assumptions under which it holds. The label is computed by cross-product of antecedent labels, removing nogoods and subsumed environments. (notes.md, "Label Update Algorithm", citing pp.151-152)

**Invalidation:** When a new nogood is discovered, the nogood environment is removed from all node labels, triggering cascading label updates. Retraction of justifications is handled indirectly via "defeasability assumptions" -- conjoin an extra assumption with the justification, then contradict that assumption to effectively retract. (notes.md, "Retraction of Justifications", citing p.153)

**Stored vs ephemeral:** The ATMS is explicitly described as an "intelligent cache, or a very primitive learning scheme" (notes.md, "TMS as Cache and Learning Scheme", citing p.129). All inferences ever made are cached so they need not be repeated. Labels are permanently maintained and incrementally updated. This is the strongest articulation in the entire collection of stored reasoning as a design goal.

**Materialized query equivalent:** The **label** of an ATMS node IS a materialized query result. It answers the question "under what assumption sets does this datum hold?" and is incrementally maintained as new justifications and nogoods arrive. The label has four formal properties (consistency, soundness, completeness, minimality -- pp.144-145) that serve as correctness invariants for the materialized result.

**Key quote relevance:** "A rule examined by the problem solver (i.e., compiled) need never be examined again on the same data because it is already compiled within the TMS as a justification." (notes.md, citing p.130)

---

### 2. de Kleer 1986 -- Problem Solving with the ATMS

**Derivation dependencies:** Consumers produce justifications that encode inference steps. Each justification records its informant (problem-solver description), consequent, and antecedents. Consumer type system prevents self-triggering. (notes.md, "Consumer Restrictions" and "Consumer Type System", citing pp.202-203)

**Invalidation:** Consumers run exactly once and are discarded -- "like a compilation process" (notes.md, "Why consumers run exactly once", citing pp.201-202). The ATMS label propagation handles all invalidation automatically. No consumer needs to re-run because the label update mechanism propagates all changes.

**Stored vs ephemeral:** All consumer outputs (justifications) are permanent. "Once a consumer has run and constructed its justifications, all control over those justifications is lost -- they are permanent." (notes.md, "Why control is exercised before running consumers, not after", citing p.204-206). This is a strong stored-reasoning model.

**Materialized query equivalent:** The consumer output is a **compiled inference** -- a materialized rule application that persists and whose validity is tracked by the ATMS label mechanism. The constraint language (PLUS, TIMES, AND, OR, ONEOF) built on consumers creates a layer of persistent constraint relationships that function as materialized query infrastructure.

---

### 3. Dixon 1993 -- ATMS and AGM

**Derivation dependencies:** Essential Support sets ES(p, E) -- the assumptions that appear in every foundational belief set for p in environment E. These are computed from ATMS labels. (notes.md, "Essential Support", citing p.537)

**Invalidation:** On environment change (context switch), the ATMS_to_AGM algorithm recomputes entrenchment values for affected atoms. Essential supports shift as assumptions are added or removed. The algorithm processes removals (contraction) and additions (expansion) sequentially. (notes.md, "ATMS_to_AGM Algorithm", citing p.537)

**Stored vs ephemeral:** The entrenchment ordering is a derived view of ATMS justificational structure. It is recomputed per context switch rather than maintained incrementally. The ATMS justifications themselves are permanent; the entrenchment is ephemeral. This is a case where the "materialized" form (ATMS labels) and the "view" form (AGM entrenchment) coexist.

**Materialized query equivalent:** The **entrenchment encoding** is a materialized view: it translates the ATMS's structural information into a different formalism (AGM's epistemic entrenchment ordering) that answers a different question ("how firmly entrenched is this belief?"). Dixon shows these two views are formally equivalent (Theorem 1, p.538).

---

### 4. Martins 1983 -- Multiple Belief Spaces

**Derivation dependencies:** Supported wffs of the form F!:t,a,p where t is origin tag, a is origin set (hypotheses used), p is restriction set (known inconsistencies). Origin sets track exactly which hypotheses were used in derivation. (notes.md, citing p.370)

**Invalidation:** Restriction sets grow as contradictions are discovered. The URS (Updating Restriction Sets) rule propagates new inconsistency information to all affected hypotheses and derived wffs. No deletion occurs -- information is additive. (notes.md, "Contradiction Detection and Recovery", citing p.371)

**Stored vs ephemeral:** All derivations are permanently stored in the SNePS network. Contradiction recovery works by dropping hypotheses from the current context, not by deleting network nodes. "The network preserves all derivations -- propositions are represented in the SNePS network permanently." (notes.md, "Non-destructive contradiction recovery", citing p.373)

**Materialized query equivalent:** A **Belief Space** is a materialized query. It is defined by a context (set of hypotheses) and consists of all propositions derivable from that context. Retrieval operations return only propositions within the current belief space -- this is exactly a materialized view with a filter predicate. From n hypotheses, 2^n distinct belief spaces can be defined over the same underlying network. (notes.md, citing p.371)

---

### 5. Martins 1988 -- Belief Revision (SWM/MBR/SNeBR)

**Derivation dependencies:** The supported wff 4-tuple (A, tau, alpha, rho) -- wff, origin tag, origin set, restriction set -- is the core dependency-tracking structure. The mu function computes restriction sets from parent wffs. The integral function computes RS for compound origin sets. (notes.md, "Supported Wff Structure" and "The mu function", citing pp.37-38)

**Invalidation:** The URS rule is the sole invalidation mechanism. When contradiction is detected, RS of every hypothesis in the combined origin set is updated. Two special cases: RS simplification (existing RS already contains relevant info) and multiple derivations (multiple supporting nodes). (notes.md, "Belief Revision Process", citing pp.60-62)

**Stored vs ephemeral:** The SWM logic automatically computes and stores dependencies via its inference rules. "The interesting aspect of supporting a belief revision system in SWM is that the dependencies among propositions can be computed by the system itself rather than having to force the user to do this." (notes.md, "Design Rationale", citing p.32). Multiple derivations of the same proposition are preserved as separate supporting nodes sharing the proposition node. (notes.md, citing p.56)

**Materialized query equivalent:** The **supported wff** is the most direct analog to a reified query result. It packages together the result (wff), its provenance (origin tag + origin set), and its known limitations (restriction set) into a single first-class object. Propositions with the same OS share supporting nodes, yielding memory savings -- this is essentially shared materialization. (notes.md, citing p.57)

---

### 6. Groth 2010 -- Anatomy of a Nanopublication

**Derivation dependencies:** The nanopublication model layers: concept -> triple -> statement -> annotation -> nanopublication. Annotations track provenance (importedFrom, importedBy, authoredBy). The SWP ontology's assertedBy relationship links a Named Graph to an authority. (notes.md, "Core Model Definitions" and "Annotations", citing pp.52, 54)

**Invalidation:** No invalidation model exists. Nanopublications are immutable once published. The S-Evidence aggregation mechanism collects all nanopublications about the same statement, but there is no mechanism for retracting or updating a nanopublication. No discussion of versioning or retraction. (notes.md, "Limitations", citing p.56)

**Stored vs ephemeral:** All reasoning is stored -- nanopublications are permanent, citable artifacts by design. The entire model is oriented toward persistence and aggregation. "Statements need to be taken into account in full view of their context." (notes.md, citing p.51)

**Materialized query equivalent:** The **nanopublication** itself is the reified query result -- it makes a single scientific assertion into a first-class, citable, annotatable object with provenance. The **S-Evidence** concept (all nanopublications about the same statement) is a materialized aggregation query. However, nanopublications lack dependency tracking and invalidation -- they are reified assertions, not reified derivations.

---

### 7. Clark 2014 -- Micropublications

**Derivation dependencies:** The support graph is a DAG (directed acyclic graph) of supports/challenges rooted at the principal Claim. The formal definition MP_a = (A_mpa, c, A_c, Phi, R) where R is the union of support (R+) and challenge (R-) relations. R+ must be a strict partial order. (notes.md, "Mathematical Representation", citing p.12)

**Invalidation:** No explicit invalidation mechanism. The model captures disagreement via challenge relations (directlyChallenges, indirectlyChallenges) rather than through retraction. The literature is treated as "a defeasible record rather than a fixed truth store." (notes.md, citing p.4)

**Stored vs ephemeral:** Micropublications are persistent artifacts. The asserts/quotes distinction tracks whether a representation was originally instantiated by a micropublication or referred to from another. Claim lineages trace support across publication boundaries. (notes.md, "Asserts vs. Quotes", citing p.11)

**Materialized query equivalent:** The **micropublication** is a reified argument -- a first-class artifact containing a claim, its evidentiary support graph, attribution, and challenge relations. It is richer than a nanopublication because it reifies the entire argument structure, not just the assertion. The **similarity group with holotype** is a materialized equivalence class over claims. (notes.md, "Similarity Groups and Holotypes", citing pp.19-20)

---

### 8. Carroll 2005 -- Named Graphs, Provenance and Trust

**Status:** This paper has only a metadata.json file in the collection -- no notes.md or description.md exists yet. Per the metadata (doi: 10.1145/1060745.1060835), it introduces Named Graphs as an RDF extension that assigns URIs to graphs, enabling provenance and trust assertions about graph-level units. Named Graphs are referenced extensively by Groth 2010 as the serialization substrate for nanopublications.

**Relevance to reified queries (from context in other papers):** Named Graphs provide the mechanism for making RDF graph fragments into first-class objects with identity (URIs). This is the serialization-level prerequisite for reified queries in the Semantic Web -- without graph-level identity, statements about statements (provenance, trust, attribution) cannot be expressed. Groth 2010 (notes.md, "Named Graph Realization", citing p.53) uses Named Graphs directly: "each statement is a separate Named Graph" and "each annotation has as its subject the URI of a Named Graph."

---

### 9. Doyle 1979 -- A Truth Maintenance System

**Derivation dependencies:** SL-justifications (support-list: inlist + outlist) and CP-justifications (conditional-proof: consequent + hypotheses). Each node has a justification-set, a supporting-justification (the selected well-founded justification), and dependency relationships (antecedents, foundations, consequences, repercussions). (notes.md, "Data Structures", citing pp.241-242)

**Invalidation:** The 7-step truth maintenance process incrementally updates belief statuses when justifications are added. Dependency-directed backtracking traces maximal assumptions of a contradiction, creates a nogood, selects a culprit, and retracts it. Retraction triggers cascading status changes through the dependency network. (notes.md, "Truth Maintenance Process" and "Dependency-Directed Backtracking", citing pp.246-252)

**Stored vs ephemeral:** All justifications are permanently stored. "If we throw away information about derivations, we may be condemning ourselves to continually rederiving information in large searches caused by changing irrelevant assumptions." (notes.md, "Design Rationale", citing p.269). The argument for storing justifications is explicitly framed as a caching/performance argument -- the stored reasoning prevents redundant work.

**Materialized query equivalent:** Each **TMS node with its justification-set** is a reified derivation result. The node's support-status (in/out) is a maintained view that is incrementally updated. CP-justifications enable **summarizing arguments** -- abstracting away low-level details while preserving the dependency structure -- which is explicitly a form of reified reasoning at different granularities. (notes.md, "Summarizing Arguments", citing pp.253-256)

---

### 10. Forbus & de Kleer 1993 -- Building Problem Solvers

**Derivation dependencies:** The book implements three TMS families, each with different dependency models: JTMS (justification chains, well-founded support), LTMS (clauses with BCP, prime implicates), ATMS (labels as sets of environments). The ATMS PROPAGATE/UPDATE/WEAVE/NOGOOD algorithms maintain label properties incrementally. (notes.md, Ch 12, citing pp.448-451)

**Invalidation:** JTMS: 2-phase retraction (propagate outness, then find alternative support). LTMS: BCP counter-based clause maintenance. ATMS: NOGOOD marks environment as nogood and removes from all node labels. Each TMS family handles invalidation differently but all maintain consistency incrementally. (notes.md, various chapters)

**Stored vs ephemeral:** The textbook explicitly frames the TMS as a cache. From the ATMS description: the TMS serves three roles -- (1) cache for all inferences, (2) enables nonmonotonic inferences, (3) constraint satisfaction. The ATMS solution construction (via GOAL node with label = all solutions) is a materialized query over the entire assumption space. (description.md tags; de Kleer 1986 notes citing p.129)

**Materialized query equivalent:** The **GOAL node** in ATMS solution construction is the clearest materialized query analog: its label directly contains all solutions, maintained incrementally. The `interpretations` procedure (given choice sets and defaults, returns maximal consistent environments) is a query operation over the materialized label structure. (notes.md, "Solution construction", citing pp.452-454)

---

### 11. de Kleer & Brown 1984 -- Qualitative Physics (Confluences)

**Derivation dependencies:** Explanation-proofs: three kinds of justifications -- "Given" (from confluences), "Substitution" (value assignments into confluences), "Premise" (unsubstantiated). Proofs are constructed automatically by ENVISION. RAA (reductio ad absurdum) adds "Unique Value," "RAA," and "Discharge" inference rules. (notes.md, "Explanation-Proof Structure", citing pp.50-52)

**Invalidation:** State transitions invalidate interpretations. When a device's qualitative state changes (a variable crosses a boundary), the constraint satisfaction must be re-run for the new state's confluences. State transition rules (ordering, equality change, epsilon ordering, contradiction avoidance, continuity) govern when invalidation occurs. (notes.md, "State Transition Rules", citing p.42)

**Stored vs ephemeral:** Interpretations (consistent assignments of qualitative values) are stored. The episode diagram (graph of qualitative states with transitions) is a persistent structure. Causal explanations are proof objects that can be inspected. However, interpretations are recomputed from scratch on state transitions -- they are stored within an episode but not incrementally maintained across episodes. (notes.md, "Implementation Details", citing pp.33-37)

**Materialized query equivalent:** An **interpretation** is a materialized query: "an assignment of qualitative values to all variables that satisfies all confluences" (notes.md, citing p.35). Multiple interpretations represent qualitative ambiguity -- they are all the valid answers to the constraint query. The **episode diagram** is a higher-level materialized query showing all possible behavioral trajectories.

---

## Cross-Cutting Findings

### 1. The TMS Family Papers All Treat Stored Reasoning as Primary

Every TMS paper (Doyle 1979, de Kleer 1986 x2, Martins 1983/1988, Forbus 1993) explicitly frames the TMS as a persistent cache of derived results with dependency tracking and incremental maintenance. De Kleer calls it "an intelligent cache, or a very primitive learning scheme" (ATMS notes, p.129). Doyle argues against discarding derivations because it "condemns ourselves to continually rederiving information" (TMS notes, p.269). This is the core insight for reified queries: **the TMS node IS a materialized query result**, and the label/justification structure IS the dependency tracking.

### 2. Two Distinct Invalidation Strategies

The papers reveal two fundamentally different approaches to invalidation:

- **Retraction-based** (Doyle 1979, JTMS/LTMS in Forbus 1993): When upstream data changes, propagate "outness" through the dependency network, then search for alternative support. Destructive -- node statuses change.
- **Label-based** (de Kleer 1986, ATMS in Forbus 1993): No retraction. Instead, track all contexts simultaneously. When a nogood is discovered, remove the environment from all labels. Non-destructive -- data grows monotonically.

The ATMS approach is more natural for reified queries because materialized results are never destroyed -- they become inapplicable in certain contexts rather than being retracted.

### 3. The Publication Models Lack Dependency Tracking

Groth 2010 and Clark 2014 define reified assertions (nanopublications, micropublications) with provenance and attribution, but neither has a dependency-tracking or invalidation mechanism. They model disagreement through challenge relations rather than through dependency-directed revision. This is a significant gap: **propstore's "reified query" concept bridges the TMS world (dependency tracking, invalidation) with the publication world (provenance, attribution, citability).**

### 4. What Propstore Would Call a "Materialized Query"

Based on this survey, the closest existing terms are:

| Tradition | Term | What It Reifies | What It Lacks (for propstore) |
|-----------|------|-----------------|-------------------------------|
| TMS | ATMS Label | All contexts supporting a datum | Provenance, attribution, arguability |
| TMS | Supported Wff (Martins) | Derivation + provenance + known inconsistencies | Citability, publication identity |
| TMS | Belief Space (Martins) | Context-filtered projection of knowledge | Persistence as independent artifact |
| Publication | Nanopublication | Attributed assertion | Dependency tracking, invalidation |
| Publication | Micropublication | Argument with evidence graph | Dependency tracking, invalidation |
| Qualitative Physics | Interpretation | Constraint satisfaction result | Incremental maintenance across state changes |

Propstore's materialized query concept would be: **a Supported Wff (Martins-style 4-tuple with provenance) that also has ATMS-style label tracking (multi-context validity) and nanopublication-style citability (URI, attribution, assertedBy)**. No single paper in the collection combines all three properties.

### 5. The Belief Space as Proto-Materialized View

Martins 1983's Belief Space concept (notes.md, p.371) is the closest existing concept to what databases call a "materialized view." A belief space is defined by a context (set of hypotheses) and consists of all propositions derivable from that context. Retrieval operations only return propositions within the current belief space. Different contexts yield different belief spaces from the same underlying network. This is precisely a parameterized materialized view with dependency tracking via origin sets and invalidation via restriction set updates.

### 6. Carroll 2005 Gap

The Carroll 2005 paper (Named Graphs, Provenance and Trust) exists in the collection as metadata only -- no notes.md or description.md. This paper is foundational to the nanopublication serialization (Groth 2010 relies on it directly). It should be processed to complete the picture of how graph-level identity enables reified queries in the Semantic Web stack.

---

## Files Consulted

- `papers/deKleer_1986_AssumptionBasedTMS/notes.md` -- full notes
- `papers/deKleer_1986_AssumptionBasedTMS/description.md` -- description
- `papers/deKleer_1986_ProblemSolvingATMS/notes.md` -- full notes
- `papers/deKleer_1986_ProblemSolvingATMS/description.md` -- description
- `papers/Dixon_1993_ATMSandAGM/notes.md` -- full notes
- `papers/Dixon_1993_ATMSandAGM/description.md` -- description
- `papers/Martins_1983_MultipleBeliefSpaces/notes.md` -- full notes
- `papers/Martins_1983_MultipleBeliefSpaces/description.md` -- description
- `papers/Martins_1988_BeliefRevision/notes.md` -- full notes
- `papers/Martins_1988_BeliefRevision/description.md` -- description
- `papers/Groth_2010_AnatomyNanopublication/notes.md` -- full notes
- `papers/Groth_2010_AnatomyNanopublication/description.md` -- description
- `papers/Clark_2014_Micropublications/notes.md` -- full notes
- `papers/Clark_2014_Micropublications/description.md` -- description
- `papers/Carroll_2005_NamedGraphsProvenanceTrust/metadata.json` -- metadata only (no notes/description exist)
- `papers/Doyle_1979_TruthMaintenanceSystem/notes.md` -- full notes
- `papers/Doyle_1979_TruthMaintenanceSystem/description.md` -- description
- `papers/Forbus_1993_BuildingProblemSolvers/notes.md` -- partial read (first 200 lines of large file)
- `papers/Forbus_1993_BuildingProblemSolvers/description.md` -- description
- `papers/deKleer_1984_QualitativePhysicsConfluences/notes.md` -- full notes
- `papers/deKleer_1984_QualitativePhysicsConfluences/description.md` -- description
