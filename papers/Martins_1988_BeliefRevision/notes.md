---
title: "A Model for Belief Revision"
authors: "Joao P. Martins, Stuart C. Shapiro"
year: 1988
venue: "Artificial Intelligence"
doi_url: "https://cse.buffalo.edu/~shapiro/Papers/marsha88.pdf"
---

# A Model for Belief Revision

## One-Sentence Summary
Presents the SWM logic (an assumption-based relevance logic that automatically computes propositional dependencies), its extension with nonstandard connectives, the MBR abstract belief-revision model built on SWM, and the SNeBR implementation using the SNePS semantic network. *(p.25)*

## Problem Addressed
Prior belief revision systems (Doyle's TMS, McAllester's three-valued TMS, de Kleer's ATMS, McDermott's systems) either require the user to manually compute dependencies among propositions, do not use the rules of inference of the underlying logic to compute dependencies automatically, or operate on justifications rather than on sets of assumptions. *(p.25)* No previous system combined all of: (1) a logic-based approach where the system itself computes dependencies, (2) assumption-based support tracking, and (3) a working implementation that manipulates sets of assumptions rather than justifications. *(p.25)*

The authors identify five specific problems in belief revision that researchers have addressed: *(p.26)*
1. The *inference* problem: how do new beliefs follow from old ones *(p.27)*
2. The *nonmonotonicity* problem: how to record that one belief depends on the absence of another *(p.27)*
3. *Dependency recording*: how to keep track of where each proposition came from (justification-based vs assumption-based) *(pp.27-29)*
4. *Disbelief propagation*: what happens when a proposition is disbelieved *(pp.29-30)*
5. *Revision of beliefs*: the ultimate task of deciding about culprits and changing beliefs *(p.31)*

## Key Contributions
- The SWM deductive system: a relevance logic that tracks propositional dependencies via origin sets (OS) and restriction sets (RS), preventing introduction of irrelevancies via relevance constraints *(pp.32-34)*
- Extension of SWM with nonstandard connectives (and-entailment, or-entailment, and-or, thresh) from the SNePS representation language, with full introduction and elimination rules *(pp.43-48)*
- The MBR (Multiple Belief Reasoner) abstract model: defines contexts, belief spaces, and two levels of belief revision (within current context, and within a context strictly containing the current context) *(pp.49-51)*
- SNeBR: a concrete implementation of MBR using SNePS semantic networks, including representation of propositions, supported wffs, contexts, contradiction detection, and interactive belief revision *(pp.51-62)*
- Formal proofs (Appendix A) that SWM guarantees: minimal RS for all supported wffs (Theorem 4), identical RS for wffs with identical OS (Theorem 5), every OS has recorded every known inconsistent set (Corollary 5.1), and combinability in non-inconsistent contexts (Theorem 6, Corollary 6.1) *(pp.71-76)*
- SNeBR was the first assumption-based belief revision system implemented *(p.31)*

## Methodology
The paper proceeds in layers: (1) surveys problems in belief revision (Section 1, pp.25-31), (2) defines the SWM logic with its syntax, supported wffs, inference rules, and proved properties (Section 2, pp.32-42), (3) extends SWM with nonstandard connectives from SNePS (Section 3, pp.43-48), (4) defines the MBR abstract model with contexts and belief spaces (Section 4, pp.49-51), (5) describes the SNeBR implementation (Section 5, pp.51-62), and (6) demonstrates with a worked puzzle example (Section 6, pp.62-69). *(p.31)*

## Key Equations

### Supported Wff Structure
A supported wff is a quadruple: *(p.37)*

$$
\langle A, \tau, \alpha, \rho \rangle
$$

Where:
- $A$ = a well-formed formula (wff)
- $\tau$ = origin tag (OT), one of {hyp, der, ext}
- $\alpha$ = origin set (OS), a set of hypotheses
- $\rho$ = restriction set (RS), a set of sets of hypotheses known to be inconsistent with the wff's OS

*(p.37)*

### Accessor Functions
*(p.37)*

$$
\text{wff}(\langle A, \tau, \alpha, \rho \rangle) = A
$$

$$
\text{ot}(\langle A, \tau, \alpha, \rho \rangle) = \tau
$$

$$
\text{os}(\langle A, \tau, \alpha, \rho \rangle) = \alpha
$$

$$
\text{rs}(\langle A, \tau, \alpha, \rho \rangle) = \rho
$$

### The mu function (RS computation from parent wffs)
*(p.38)*

$$
\mu(\{r_1, \ldots, r_m\}, \{o_1, \ldots, o_n\}) = \sigma(\Psi(r_1 \cup \cdots \cup r_m, o_1 \cup \cdots \cup o_n))
$$

Where $\Psi(R, O)$ filters $R$ to keep only elements disjoint from $O$: *(p.38)*

$$
\Psi(R, O) = \{\alpha \mid \alpha \in R \wedge \alpha \cap O = \emptyset\} \vee \exists(\beta)[\beta \in R \wedge \beta \cap O \neq \emptyset \wedge \alpha = \beta - O]
$$

And $\sigma(R)$ removes supersets: *(p.39)*

$$
\sigma(R) = \{\alpha \mid \alpha \in R \wedge \neg\exists(\beta)(\beta \neq \alpha \wedge \beta \in R \wedge \beta \subset \alpha)\}
$$

### The integral function (RS computation for smaller OS)
*(p.39)*

$$
\textstyle\int(O) = \mu(\{r \mid \exists(H)\; \text{wff}(H) \in O \wedge \text{ot}(H) = \text{hyp} \wedge r = \text{rs}(H)\}, \{o \mid \exists(H)\; \text{wff}(H) \in O \wedge \text{ot}(H) = \text{hyp} \wedge o = \text{os}(H)\})
$$

### The A function (origin tag computation)
*(p.39)*

$$
A(\alpha, \beta) = \begin{cases} \text{ext}, & \text{if } \alpha = \text{ext or } \beta = \text{ext} \\ \text{der}, & \text{otherwise} \end{cases}
$$

$$
A(\alpha, \beta, \ldots, \gamma) = A(\alpha, A(\beta, \ldots, \gamma))
$$

### Combinability Predicate
*(p.39)*

$$
\text{Combine}(A, B) = \begin{cases} \text{false}, & \text{if } \exists r \in \text{rs}(A): r \subset \text{os}(B) \\ \text{false}, & \text{if } \exists r \in \text{rs}(B): r \subset \text{os}(A) \\ \text{true}, & \text{otherwise} \end{cases}
$$

### Generalized Combinability (for n wffs)
*(p.44)*

$$
\text{Combine}(A_1, \ldots, A_n) = \begin{cases} \text{false}, & \text{if } \exists r \in \mu(\text{rs}(\langle\{A_1 \ldots A_n\}\rangle), \text{os}(\langle\{A_1 \ldots A_n\}\rangle)): r \subset \bigcup[\text{os}(\langle\{A_1 \ldots A_n\}\rangle)] \\ \text{true}, & \text{otherwise} \end{cases}
$$

### Context Consistency Condition
Given context $\{H_1, \ldots, H_n\}$, the condition: *(p.49)*

$$
\forall(H)\; \text{ot}(H) = \text{hyp} \wedge \text{wff}(H) = H \wedge H \in \{H_1, \ldots, H_n\}
$$

$$
\forall r \in \text{rs}(H):\; r \not\subseteq \{H_1, \ldots, H_n\} - \{H\}
$$

guarantees that the context is not known to be inconsistent. *(p.49)*

## Parameters

This paper is a formal logic/systems paper and does not contain empirical parameters with numeric values. The key "parameters" are structural:

| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| Number of hypotheses in context | n | - | - | >= 0 | Defines the size of a belief space | p.49 |
| Number of restriction sets per wff | - | - | - | >= 0 | Grows as contradictions are discovered | p.38 |
| Origin tag | OT/tau | - | hyp | {hyp, der, ext} | hyp=hypothesis, der=derived, ext=special/external | p.37 |

## Implementation Details

### Data Structures
- **Supported wff**: quadruple (A, tau, alpha, rho) where A is a wff, tau is origin tag, alpha is origin set, rho is restriction set *(p.37)*
- **Origin set (OS)**: set of hypotheses actually used in deriving the wff; guaranteed to contain only hypotheses genuinely used *(p.34, p.39)*
- **Restriction set (RS)**: set of sets of hypotheses; each element is a set known to be inconsistent with the wff's OS; guaranteed minimal (no element is a superset of another) *(p.38)*
- **Origin tag (OT)**: one of {hyp, der, ext}; hyp = introduced as hypothesis, der = normally derived, ext = special proposition (treated specially to avoid smuggling hypotheses into conjunctions) *(p.37)*
- **Context**: a set of hypotheses defining a belief space (BS) *(p.49)*
- **Belief space (BS)**: the set of all hypotheses defining the context plus all propositions derived exclusively from them *(p.49)*
- **Current context**: the context currently under consideration; operations (query, inference) are scoped to it *(p.49)*

### SWM Inference Rules
The complete set of inference rules in SWM, each computing OT, OS, and RS for results: *(pp.40-42)*
- **Hypothesis (Hyp)**: introduces a new hypothesis with OT=hyp, OS={itself}, RS from known incompatibilities *(p.40)*
- **Implication Introduction (->I)**: from hypothesis A with OS {k} and derived B with OS alpha union {k}, infer A->B with OS alpha, using set difference to remove the hypothesis *(p.40)*
- **Modus Ponens (MP)**: from A and A->B, with Combine check, infer B with OS = union of parent OSes *(p.40)*
- **Modus Tollens (MT)**: from neg-B and A->B, with Combine check, infer neg-A *(p.40)*
- **Negation Introduction (neg-I)**: from the hypotheses underlying a contradiction, infer the negation of their conjunction; produces wffs with OT=ext *(p.41)*
- **Negation Elimination (neg-E)**: double negation elimination *(p.41)*
- **Updating Restriction Sets (URS)**: obligatorily applied when a contradiction is detected; updates RS of all hypotheses and derived wffs whose OS overlaps the discovered inconsistent set *(p.41)*
- **And-Introduction (^I)**: two forms -- same OS produces standard conjunction; different OSes checked via Combine, result gets OT=ext to prevent smuggling hypotheses *(p.41)*
- **And-Elimination (^E)**: only applicable if OT is not ext, preventing smuggling *(p.41)*
- **Or-Introduction (vI)** and **Or-Elimination (vE)**: standard disjunction rules *(p.41)*
- **Universal Introduction (VI)** and **Universal Elimination (VE)**: quantifier rules *(p.42)*
- **Existential Introduction (EI)** and **Existential Elimination (EE)**: quantifier rules, EE requires a fresh constant *(p.42)*

### Nonstandard Connectives (SNePS extensions)
- **And-entailment** (^->): conjunction of antecedents implies conjunction of consequents; eliminates only from antecedent to consequent (unlike MP which is bidirectional via MT) *(pp.44-45)*
- **Or-entailment** (v->): any antecedent implies the conjunction of consequents *(p.45)*
- **And-or** (x with i,j parameters): generalizes negation, and, or, exclusive or, nand; at least i and at most j of n propositions must be true *(pp.45-48)*
- **Thresh** (theta with i parameter): either fewer than i are true or all are true; generalizes biconditional *(pp.47-48)*

### SNeBR Network Representation
- Propositions are SNePS nodes; each concept has a unique node (uniqueness principle) *(p.52)*
- Each proposition node has a supporting node with arcs: "os" to hypothesis nodes, "rs" to restriction set element nodes (each element has "ers" arcs to its hypotheses), OT arc (hyp/der/ext) *(p.53)*
- Contradictory propositions P and not-P share network structure (and-or connective node with min=0, max=0) *(p.55)*
- Contexts represented by a node with "val" arcs to each hypothesis node *(p.57)*
- Multiple derivations of same proposition: multiple supporting nodes pointing to the same proposition node (shared via uniqueness principle) *(p.56)*
- Propositions with the same OS share supporting nodes, yielding memory and processing savings *(p.57)*

### SNeBR Operations
When using SNeBR, the user can perform five operations: *(pp.51-52)*
1. **Add new hypotheses to the network**: takes a proposition and context name, adds as hypothesis *(p.51)*
2. **Name a context**: assign a name to a given context for reference *(p.52)*
3. **Ask for all nodes matching a pattern in a BS**: pattern matching with context filtering *(p.52)*
4. **Perform backward inference in a BS**: given a proposition, try to deduce it from rules in the specified context *(p.52)*
5. **Perform forward inference in a BS**: given a hypothesis, add it and derive all consequences *(p.52)*

### Inference in SNeBR
- Uses bi-directional inference via active connection graphs (acg) *(p.58)*
- Pattern matching filters propositions by context (BS membership); matching is done as if no contexts exist, then results are "filtered" *(p.58)*
- Inference processes are compiled into a multi-processing system (MULTI), a LISP-based system with an evaluator, scheduler, and system primitives *(p.58)*
- Rules of inference are embodied by processes that compute OT, OS, and RS for results; one process per rule *(p.59)*
- Contradiction detection occurs in two ways: (1) when building contradictory nodes into the network (node exists and its negation is being built), and (2) when a process gathers data that invalidates a rule (e.g., and-or with wrong number of true arguments) *(p.59)*

### Belief Revision Process (URS rule)
1. When contradiction detected, find all hypotheses underlying both contradictory wffs by following OT and "os" arcs *(p.60)*
2. Update RS of each hypothesis by creating new RS nodes representing the discovered inconsistent sets *(p.60)*
3. Update RS of all supported wffs whose OS is not disjoint from the newly discovered inconsistent set (follow os-inverse arcs from each hypothesis) *(p.60)*
4. Two special cases: (a) RS simplification -- when existing RS already contains relevant info, the resulting RS may be smaller than before *(p.61)*, (b) one contradictory wff obtained by more than one derivation (multiple supporting nodes) -- uncovers multiple inconsistent sets *(p.62)*

### Two Levels of Belief Revision
*(p.50)*
1. **Belief revision within a context strictly containing the current context**: only one of the contradictory wffs belongs to the current BS; URS records the new inconsistent set but does not change the current context *(p.51)*
2. **Belief revision within the current context**: both contradictory wffs belong to the current BS; URS is applied and neg-I may also fire, producing disbelief in some hypotheses; the current context must be changed *(p.51)*

### Initialization
- Knowledge base starts empty or with user-provided hypotheses *(p.40)*
- Each new hypothesis gets OT=hyp, OS={itself}, RS={} (or populated if known incompatibilities exist) *(p.40)*
- Derived wffs get OT=der, OS=union of parent OSes (computed by mu), RS=computed from parent RSes (computed by mu) *(pp.38-39)*

### Edge Cases
- When RS is simplified during URS, the resulting RS may be smaller than before *(p.61)*
- Multiple derivations of the same proposition share the proposition node but have separate supporting nodes *(p.56)*
- If a context is not known to be inconsistent, Combine returns true for all wff pairs in that context's BS (Theorem 6), avoiding unnecessary combinability checks *(p.50)*
- Empty antecedent or consequent in and-or/thresh connective introductions are handled as degenerate cases *(p.47)*
- The "ext" origin tag prevents and-elimination from smuggling hypotheses into a conjunction of wffs that individually depend on different assumptions *(p.37, p.41)*

## Figures of Interest
- **Fig. 1 (p.28):** Knowledge base dependencies in justification-based systems (Doyle-style)
- **Fig. 2 (p.29):** Knowledge base dependencies in assumption-based systems (de Kleer-style)
- **Fig. 3 (p.35):** FR system implication introduction rule
- **Fig. 4 (p.35):** FR system and-introduction rule
- **Fig. 5 (p.36):** "Proof" in the FR system showing paradox of implication
- **Fig. 6 (p.52):** SNePS node representation of propositions ("John hits Mary", "Mary likes soup")
- **Fig. 7 (p.53):** Network representation of hypothesis-supported wffs
- **Fig. 8 (p.54):** Network representation of derived (der) supported wffs
- **Fig. 9 (p.55):** Network representation of contradictory propositions P and not-P (via and-or min=0 max=0)
- **Fig. 10 (p.56):** Multiple derivations of the same proposition (three supporting nodes for C)
- **Fig. 11 (p.57):** Propositions sharing a supporting node (same OS)
- **Fig. 12 (p.58):** Network representation of context "ct1"
- **Fig. 13 (p.61):** Network after URS application (showing RS update with new r1-r6 nodes)
- **Fig. 14 (p.62):** Network before URS when n5 has two supporting nodes
- **Figs. 15-25 (pp.65-69):** Complete worked example: "The Woman Freeman Will Marry" puzzle

## Results Summary
- SWM provides a formal logic for tracking propositional dependencies via origin sets and restriction sets *(p.43)*
- All supported wffs have minimal RS (Theorem 4) *(p.72)*
- Wffs with the same OS have the same RS (Theorem 5) *(p.74)*
- Every OS has recorded every known inconsistent set (Corollary 5.1) *(p.75)*
- In contexts not known to be inconsistent, combinability checking is unnecessary (Corollary 6.1) *(p.76)*
- SNeBR (the implementation) successfully solves the "Woman Freeman Will Marry" puzzle, demonstrating contradiction detection, culprit identification, interactive belief revision, and resumption of inference *(pp.65-69)*
- SWM guarantees that removing exactly one hypothesis from a set of culprits produces a context that is not known to be inconsistent *(p.67)*
- Information derived in one BS can be shared in another without re-derivation, since propositions derived from the same hypotheses share supporting nodes *(p.69)*

## Limitations
- SWM has syntax but no semantics (no model theory / truth conditions defined); the authors acknowledge this and express hope future work will define semantics *(p.32)*
- The system does not address the nonmonotonicity problem (how to record that one belief depends on the absence of another) *(p.70)*
- Multiple derivations of the same proposition are not fully addressed (the system records each derivation separately but does not merge them optimally) *(p.40)*
- Belief revision is interactive (the user must choose which hypothesis to discard); the system does not automate the selection of culprits *(p.67)*
- The system was implemented in FRANZLISP on VAX-11, which limits practical deployment *(p.31)*
- Work was underway at time of writing to pass the responsibility of revising beliefs to SNeBR itself rather than the user *(p.67)*

## Arguments Against Prior Work

- **Doyle's TMS does not automatically compute dependencies.** In Doyle's system [12], "the inferences are made outside the system, which just passively records them." The system requires the user to manually specify justifications rather than using the rules of inference of the underlying logic to compute dependencies automatically. *(p.27)*
- **McAllester's system uses axioms rather than inference rules.** McAllester generates justifications "for the truth values of the propositions in the knowledge base using axioms that define the rules of inference of each logical symbol." This is a different approach from computing dependencies via the logic's own inference rules. *(p.27)*
- **De Kleer's ATMS also does not address the inference problem.** De Kleer's ATMS, like Doyle's TMS, "do not address this issue at all" --- the dependency computation happens outside the system. *(p.27)*
- **Justification-based systems conflate direct and ultimate support.** In justification-based systems (Doyle, McAllester, McDermott), the support of each proposition contains the propositions that *directly* produced it, creating complex dependency graphs that must be traversed to find the ultimate hypotheses. Assumption-based systems (de Kleer, Martins/Shapiro) record the *hypotheses* (nonderived propositions) directly, avoiding this traversal. *(pp.27--29)*
- **No prior system automatically computes dependencies from logic.** "This is a problem area that has been mostly ignored by researchers. The systems of Doyle, McDermott, and de Kleer do not address this issue at all." Only McAllester generates justifications automatically, but using axioms rather than inference rules. *(p.27)*
- **Classical logic allows introduction of irrelevancies.** Classical logic permits deductions where "anything implies a true proposition" ($A \rightarrow (B \rightarrow A)$) and "a contradiction implies anything" ($(A \wedge \neg A) \rightarrow B$). These are the "paradoxes of implication" that relevance logic was designed to deny. SWM blocks these by tracking origin sets and restricting inference rules. *(pp.33--34)*
- **No prior system selects the culprit.** "No system has addressed the problem of selecting *the* culprit from the set of possible culprits for a contradiction, although some proposals have been made." *(p.31)*
- **Disbelief propagation approaches all have drawbacks.** Doyle and McAllester require two passes through the knowledge base (first to disbelieve dependents, then to check re-derivability). McDermott's data pool/labeling approach is efficient but uses both proposition dependencies and proposition labeling. De Kleer's context-based approach requires the knowledge base retrieval function to dynamically filter. *(pp.29--31)*

## Design Rationale

- **Logic-based dependency computation.** The central design choice is to build a logic (SWM) whose inference rules automatically compute and propagate dependencies among propositions, rather than requiring the user or an external system to specify them. "The interesting aspect of supporting a belief revision system in SWM is that the dependencies among propositions can be computed by the system itself rather than having to force the user to do this." *(p.32)*
- **Relevance logic to prevent irrelevancies.** SWM adopts the key features of Anderson and Belnap's relevance logic [1] to block the paradoxes of classical implication. Each wff's origin set contains only the hypotheses "that were *really* used in its derivation," preventing conclusions from depending on irrelevant premises. *(pp.33--34)*
- **Assumption-based rather than justification-based.** The system records origin sets (sets of hypotheses) rather than justifications (sets of direct premises), following de Kleer's approach. This avoids the need to traverse dependency graphs to find ultimate sources of a proposition. *(pp.28--29)*
- **Four-tuple supported wffs.** Each proposition is represented as $\langle A, \tau, \alpha, \rho \rangle$ (wff, origin tag, origin set, restriction set), capturing both provenance and known inconsistencies in a single structure. The origin tag distinguishes hypotheses (hyp), derived propositions (der), and externally-introduced propositions (ext). *(p.37)*
- **Restriction sets for contradiction tracking.** The restriction set records which sets of hypotheses are known to be inconsistent with the wff's origin set. This is the mechanism for detecting contradictions without requiring an explicit inconsistency database separate from the propositions themselves. *(p.37)*
- **Contexts and belief spaces for multi-perspective reasoning.** The MBR model defines a context as any set of hypotheses, and a belief space as the set of all propositions whose origin set is contained in the context. This enables reasoning from multiple perspectives simultaneously. *(pp.49--50)*
- **Interactive culprit selection.** Rather than automating the choice of which hypothesis to retract upon contradiction, the system presents the user with the set of possible culprits and lets them decide. This reflects the authors' position that culprit selection is a domain-specific judgment that the system should not automate (though they note work is underway to change this). *(p.67)*
- **SWM has syntax but deliberately no semantics.** The authors acknowledge that SWM "doesn't (yet) have a semantics" --- they developed a proof technique suitable for belief revision without first defining truth conditions. This was a pragmatic choice to prioritize dependency-tracking functionality. *(p.32)*

## Testable Properties
- For any supported wff in the knowledge base, its RS is minimal: no element of the RS is a superset of another element (Theorem 4) *(p.72)*
- If two supported wffs have the same OS, they have the same RS (Theorem 5) *(p.74)*
- Every OS has recorded every known inconsistent set (Corollary 5.1) *(p.75)*
- In a context not known to be inconsistent, for any two supported wffs A and B defined by the context, Combine(A, B) = true (Theorem 6, Corollary 6.1) *(p.76)*
- If A is an inconsistent set, then any set containing A is also inconsistent (Theorem 3) *(p.71)*
- If A is not known to be inconsistent, then neither is any set contained in A (Corollary 3.1) *(p.72)*
- The removal of exactly one hypothesis from a set of culprits for a contradiction must produce a context that is not known to be inconsistent (guaranteed by SWM formalism) *(p.67)*
- The OS of a supported wff contains only hypotheses that were genuinely used in its derivation (guaranteed by relevance logic rules) *(pp.34-35)*
- The mu function is idempotent with respect to RS minimality: mu applied to already-minimal RSes produces a minimal RS (Theorem 1) *(p.71)*
- The integral function produces minimal RS from hypothesis RSes (Theorem 2) *(p.71)*

## Relevance to Project
This paper is directly foundational for the propstore's assumption-tracking and belief-revision architecture. It provides the formal model (SWM) for tracking which assumptions support each proposition and which assumption sets are known to be inconsistent, plus the MBR abstraction layer defining contexts and belief spaces. The SNeBR implementation demonstrates a working system that does exactly what the propstore's world model needs: maintaining multiple belief contexts, detecting contradictions, identifying culprits, and revising beliefs. This complements the de Kleer ATMS papers already in the collection by providing an alternative approach (relevance-logic-based with richer connectives, user-interactive revision) to the same family of problems. *(pp.25, 70)*

## Open Questions
- [ ] How does SWM's handling of contradictions compare to the ATMS's nogood sets in terms of computational efficiency?
- [ ] Can the MBR model be extended with automated culprit selection (rather than interactive)? (Work was underway per p.67)
- [ ] What would a model-theoretic semantics for SWM look like? *(p.32)*
- [ ] How does the approach scale with large numbers of hypotheses and contexts?

## Related Work Worth Reading
- Martins, J., "Reasoning in multiple belief spaces" (Ph.D. Dissertation, 1983, SUNY Buffalo) - the full dissertation underlying this paper [25] *(p.77)*
- Martins, J. and Shapiro, S., "Reasoning in multiple belief spaces" (IJCAI-83) [28] *(p.77)*
- Martins, J., "Belief revision" in Encyclopedia of AI (Wiley, 1987) [26] *(p.77)*
- Shapiro, S. and Rapaport, W., "SNePS considered as a fully intensional propositional semantic network" (1987) [49] *(p.78)*
- Goodwin, J.W., "A Theory and System for Non-Monotonic Reasoning" (Linkoping dissertation, 1987) [18] *(p.77)*
- Martins, J. and Cravo, M.R., "Revising beliefs through communicating critics" (to appear) [27] *(p.77)* -- work on automating belief revision
- Shapiro, S. and Wand, M., "The relevance of relevance" (1976) [50] *(p.78)* -- SWM is a successor of this system

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] -- cited as [6]; the main alternative approach to assumption-based reasoning. SWM/MBR provides a relevance-logic-based alternative to the ATMS's logic-independent approach. *(p.26)*
- [[Doyle_1979_TruthMaintenanceSystem]] -- cited as [12]; the foundational TMS that MBR improves upon by computing dependencies automatically via the SWM logic rather than requiring user-provided justifications. *(p.26)*
- [[McAllester_1978_ThreeValuedTMS]] -- cited as [31]; referenced as part of the TMS lineage, using three-valued clausal representation compared to MBR's four-tuple supported wffs. *(p.26)*
- [[McDermott_1983_ContextsDataDependencies]] -- cited as [34]; McDermott's synthesis of contexts and data dependencies is an alternative approach to the same multi-context reasoning problem MBR addresses. *(p.26)*
- [[Martins_1983_MultipleBeliefSpaces]] -- cited as [28]; this is the full journal-length expansion of the 1983 conference paper, with complete formal proofs and the SNeBR implementation. *(p.77)*

### New Leads (Not Yet in Collection)
- Goodwin, J.W. (1987) -- "A Theory and System for Non-Monotonic Reasoning" -- Linkoping dissertation presenting an alternative non-monotonic reasoning system *(p.77)*
- Shapiro, S. and Rapaport, W. (1987) -- "SNePS considered as a fully intensional propositional semantic network" -- describes the representation substrate for SNeBR *(p.78)*
- Martins, J. and Cravo, M.R. -- "Revising beliefs through communicating critics" -- work on automating culprit selection in belief revision *(p.77)*

### Supersedes or Recontextualizes
- [[Martins_1983_MultipleBeliefSpaces]] -- this 1988 paper is the full journal treatment superseding the 1983 conference paper, adding formal proofs (Appendix A), the ext origin tag, nonstandard connectives (Section 3), and the complete SNeBR implementation (Section 5) *(p.31)*

### Cited By (in Collection)
- [[Shapiro_1998_BeliefRevisionTMS]] -- cites this as the primary reference for SNeBR; describes how SNeBR unites the ATMS with the reasoner by computing assumption sets per inference rule
- [[Dixon_1993_ATMSandAGM]] -- does not directly cite this paper but addresses the same ATMS-vs-belief-revision bridging problem from a different angle

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] -- **Strong.** Both systems track which assumptions support each derived proposition and which assumption sets are inconsistent. MBR's origin sets correspond to ATMS labels (minimal environments), and MBR's restriction sets correspond to ATMS nogoods. Key difference: MBR computes dependencies automatically from inference rules in a relevance logic, while the ATMS receives justifications from an external problem solver. *(pp.28-29)*
- [[Alchourron_1985_TheoryChange]] -- **Moderate.** MBR's belief revision via context manipulation and culprit selection during contradiction recovery is an informal implementation of the kind of rational belief change that AGM formalizes axiomatically. MBR's interactive culprit selection corresponds to AGM's selection function over remainder sets.
- [[Dixon_1993_ATMSandAGM]] -- **Moderate.** Dixon bridges the ATMS and AGM formally; this paper provides the alternative MBR/SNeBR architecture that Shapiro (1998) later proposes should be made AGM-compliant.
- [[Shapiro_1998_BeliefRevisionTMS]] -- **Strong.** Shapiro's 1998 proposal to build an AGM-compliant TMS on SNePS/SNeBR directly builds on the MBR model presented here. The 1998 paper explicitly identifies this as the implementation foundation.
