---
title: "A Model for Belief Revision"
authors: "Joao P. Martins, Stuart C. Shapiro"
year: 1988
venue: "Artificial Intelligence"
doi_url: "https://cse.buffalo.edu/~shapiro/Papers/marsha88.pdf"
---

# A Model for Belief Revision

## One-Sentence Summary
Presents the SWM logic (an assumption-based relevance logic that automatically computes propositional dependencies), its extension with nonstandard connectives, the MBR abstract belief-revision model built on SWM, and the SNeBR implementation using the SNePS semantic network.

## Problem Addressed
Prior belief revision systems (Doyle's TMS, McAllester's three-valued TMS, de Kleer's ATMS, McDermott's systems) either require the user to manually compute dependencies among propositions, do not use the rules of inference of the underlying logic to compute dependencies automatically, or operate on justifications rather than on sets of assumptions. No previous system combined all of: (1) a logic-based approach where the system itself computes dependencies, (2) assumption-based support tracking, and (3) a working implementation that manipulates sets of assumptions rather than justifications.

## Key Contributions
- The SWM deductive system: a relevance logic that tracks propositional dependencies via origin sets (OS) and restriction sets (RS), preventing introduction of irrelevancies via relevance constraints
- Extension of SWM with nonstandard connectives (and-entailment, or-entailment, and-or, thresh) from the SNePS representation language, with full introduction and elimination rules
- The MBR (Multiple Belief Reasoner) abstract model: defines contexts, belief spaces, and two levels of belief revision (within current context, and within a context strictly containing the current context)
- SNeBR: a concrete implementation of MBR using SNePS semantic networks, including representation of propositions, supported wffs, contexts, contradiction detection, and interactive belief revision
- Formal proofs (Appendix A) that SWM guarantees: minimal RS for all supported wffs (Theorem 4), identical RS for wffs with identical OS (Theorem 5), every OS has recorded every known inconsistent set (Corollary 5.1), and combinability in non-inconsistent contexts (Theorem 6, Corollary 6.1)

## Methodology
The paper proceeds in layers: (1) surveys problems in belief revision (Section 1), (2) defines the SWM logic with its syntax, supported wffs, inference rules, and proved properties (Section 2), (3) extends SWM with nonstandard connectives from SNePS (Section 3), (4) defines the MBR abstract model with contexts and belief spaces (Section 4), (5) describes the SNeBR implementation (Section 5), and (6) demonstrates with a worked puzzle example (Section 6).

## Key Equations

### Supported Wff Structure
A supported wff is a quadruple:

$$
\langle A, \tau, \alpha, \rho \rangle
$$

Where:
- $A$ = a well-formed formula (wff)
- $\tau$ = origin tag (OT), one of {hyp, der, ext}
- $\alpha$ = origin set (OS), a set of hypotheses
- $\rho$ = restriction set (RS), a set of sets of hypotheses known to be inconsistent with the wff's OS

### Accessor Functions
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
$$
\mu(\{r_1, \ldots, r_m\}, \{o_1, \ldots, o_n\}) = \sigma(\Psi(r_1 \cup \cdots \cup r_m, o_1 \cup \cdots \cup o_n))
$$

Where $\Psi(R, O)$ filters $R$ to keep only elements disjoint from $O$:

$$
\Psi(R, O) = \{\alpha \mid \alpha \in R \wedge \alpha \cap O = \emptyset\} \vee \exists(\beta)[\beta \in R \wedge \beta \cap O \neq \emptyset \wedge \alpha = \beta - O]
$$

And $\sigma(R)$ removes supersets:

$$
\sigma(R) = \{\alpha \mid \alpha \in R \wedge \neg\exists(\beta)(\beta \neq \alpha \wedge \beta \in R \wedge \beta \subset \alpha)\}
$$

### The integral function (RS computation for smaller OS)
$$
\textstyle\int(O) = \mu(\{r \mid \exists(H)\; \text{wff}(H) \in O \wedge \text{ot}(H) = \text{hyp} \wedge r = \text{rs}(H)\}, \{o \mid \exists(H)\; \text{wff}(H) \in O \wedge \text{ot}(H) = \text{hyp} \wedge o = \text{os}(H)\})
$$

### The A function (origin tag computation)
$$
A(\alpha, \beta) = \begin{cases} \text{ext}, & \text{if } \alpha = \text{ext or } \beta = \text{ext} \\ \text{der}, & \text{otherwise} \end{cases}
$$

$$
A(\alpha, \beta, \ldots, \gamma) = A(\alpha, A(\beta, \ldots, \gamma))
$$

### Combinability Predicate
$$
\text{Combine}(A, B) = \begin{cases} \text{false}, & \text{if } \exists r \in \mu(\text{rs}(\langle\{A_1 \ldots A_n\}\rangle), \text{os}(\langle\{A_1 \ldots A_n\}\rangle)): r \subset \bigcup[\text{os}(\langle\{A_1 \ldots A_n\}\rangle)] \\ \text{false}, & \text{if } \exists r \in \text{rs}(B): r \subset \text{os}(A) \\ \text{true}, & \text{otherwise} \end{cases}
$$

### Context Consistency Condition
Given context $\{H_1, \ldots, H_n\}$, the condition:

$$
\forall(H)\; \text{ot}(H) = \text{hyp} \wedge \text{wff}(H) = H \wedge H \in \{H_1, \ldots, H_n\}
$$

$$
\forall r \in \text{rs}(H):\; r \not\subseteq \{H_1, \ldots, H_n\} - \{H\}
$$

guarantees that the context is not known to be inconsistent.

## Parameters

This paper is a formal logic/systems paper and does not contain empirical parameters with numeric values. The key "parameters" are structural:

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Number of hypotheses in context | n | - | - | >= 0 | Defines the size of a belief space |
| Number of restriction sets per wff | - | - | - | >= 0 | Grows as contradictions are discovered |
| Origin tag | OT/tau | - | hyp | {hyp, der, ext} | hyp=hypothesis, der=derived, ext=special/external |

## Implementation Details

### Data Structures
- **Supported wff**: quadruple (A, tau, alpha, rho) where A is a wff, tau is origin tag, alpha is origin set, rho is restriction set
- **Origin set (OS)**: set of hypotheses actually used in deriving the wff; guaranteed to contain only hypotheses genuinely used
- **Restriction set (RS)**: set of sets of hypotheses; each element is a set known to be inconsistent with the wff's OS; guaranteed minimal (no element is a superset of another)
- **Origin tag (OT)**: one of {hyp, der, ext}; hyp = introduced as hypothesis, der = normally derived, ext = special proposition (treated specially to avoid smuggling hypotheses into conjunctions)
- **Context**: a set of hypotheses defining a belief space (BS)
- **Belief space (BS)**: the set of all hypotheses defining the context plus all propositions derived exclusively from them
- **Current context**: the context currently under consideration; operations (query, inference) are scoped to it

### SNeBR Network Representation
- Propositions are SNePS nodes; each concept has a unique node (uniqueness principle)
- Each proposition node has a supporting node with arcs: "os" to hypothesis nodes, "rs" to restriction set element nodes (each element has "ers" arcs to its hypotheses), OT arc (hyp/der/ext)
- Contradictory propositions P and not-P share network structure (and-or connective node with min=0, max=0)
- Contexts represented by a node with "val" arcs to each hypothesis node
- Multiple derivations of same proposition: multiple supporting nodes pointing to the same proposition node (shared via uniqueness principle)

### Inference in SNeBR
- Uses bi-directional inference via active connection graphs (acg)
- Pattern matching filters propositions by context (BS membership)
- Inference processes are compiled into a multi-processing system (MULTI)
- Rules of inference are embodied by processes that compute OT, OS, and RS for results
- Contradiction detection occurs in two ways: (1) when building contradictory nodes into the network, and (2) when a process gathers data that invalidates a rule

### Belief Revision Process (URS rule)
1. When contradiction detected, find all hypotheses underlying both contradictory wffs by following OT and "os" arcs
2. Update RS of each hypothesis by creating new RS nodes representing the discovered inconsistent sets
3. Update RS of all supported wffs whose OS is not disjoint from the newly discovered inconsistent set (follow os-inverse arcs from each hypothesis)
4. Two cases: (a) RS simplified (if existing RS already contains relevant info), (b) one contradictory wff obtained by more than one derivation (multiple supporting nodes)

### Initialization
- Knowledge base starts empty or with user-provided hypotheses
- Each new hypothesis gets OT=hyp, OS={itself}, RS={}
- Derived wffs get OT=der, OS=union of parent OSes (computed by mu), RS=computed from parent RSes (computed by mu)

### Edge Cases
- When RS is simplified during URS, the resulting RS may be smaller than before
- Multiple derivations of the same proposition share the proposition node but have separate supporting nodes
- If a context is known inconsistent, Combine returns true for all wff pairs in that context's BS (Theorem 6), avoiding unnecessary combinability checks
- Empty antecedent or consequent in and-or/thresh connective introductions are handled as degenerate cases

## Figures of Interest
- **Fig. 1 (page 4):** Knowledge base dependencies in justification-based systems (Doyle-style)
- **Fig. 2 (page 5):** Knowledge base dependencies in assumption-based systems (de Kleer-style)
- **Fig. 3 (page 11):** FR system implication introduction rule
- **Fig. 4 (page 11):** FR system and-introduction rule
- **Fig. 5 (page 12):** "Proof" in the FR system showing paradox of implication
- **Fig. 6 (page 28):** SNePS node representation of propositions
- **Fig. 7 (page 29):** Network representation of hypothesis-supported wffs
- **Fig. 8 (page 30):** Network representation of derived (der) supported wffs
- **Fig. 9 (page 31):** Network representation of contradictory propositions P and not-P
- **Fig. 10 (page 32):** Multiple derivations of the same proposition
- **Fig. 11 (page 33):** Propositions sharing a supporting node (same OS)
- **Fig. 12 (page 34):** Network representation of context "ct1"
- **Fig. 13 (page 37):** Network after URS application (showing RS update)
- **Fig. 14 (page 38):** Network before URS when n5 has two supporting nodes
- **Figs. 15-25 (pages 41-45):** Complete worked example: "The Woman Freeman Will Marry" puzzle

## Results Summary
- SWM provides a formal logic for tracking propositional dependencies via origin sets and restriction sets
- All supported wffs have minimal RS (Theorem 4)
- Wffs with the same OS have the same RS (Theorem 5)
- Every OS has recorded every known inconsistent set (Corollary 5.1)
- In contexts not known to be inconsistent, combinability checking is unnecessary (Corollary 6.1)
- SNeBR (the implementation) successfully solves the "Woman Freeman Will Marry" puzzle, demonstrating contradiction detection, culprit identification, interactive belief revision, and resumption of inference

## Limitations
- SWM has syntax but no semantics (no model theory / truth conditions defined); the authors acknowledge this and express hope future work will define semantics
- The system does not address the nonmonotonicity problem (how to record that one belief depends on the absence of another)
- Multiple derivations of the same proposition are not fully addressed (the system records each derivation separately but does not merge them optimally)
- Belief revision is interactive (the user must choose which hypothesis to discard); the system does not automate the selection of culprits
- The system was implemented in FRANZLISP on VAX-11, which limits practical deployment

## Testable Properties
- For any supported wff in the knowledge base, its RS is minimal: no element of the RS is a superset of another element (Theorem 4)
- If two supported wffs have the same OS, they have the same RS (Theorem 5)
- Every OS has recorded every known inconsistent set: Corollary 5.1
- In a context not known to be inconsistent, for any two supported wffs A and B defined by the context, Combine(A, B) = true (Theorem 6, Corollary 6.1)
- If A is an inconsistent set, then any set containing A is also inconsistent (Theorem 3)
- The removal of exactly one hypothesis from a set of culprits for a contradiction must produce a context that is not known to be inconsistent (guaranteed by SWM formalism)
- The OS of a supported wff contains only hypotheses that were genuinely used in its derivation (guaranteed by relevance logic rules)

## Relevance to Project
This paper is directly foundational for the propstore's assumption-tracking and belief-revision architecture. It provides the formal model (SWM) for tracking which assumptions support each proposition and which assumption sets are known to be inconsistent, plus the MBR abstraction layer defining contexts and belief spaces. The SNeBR implementation demonstrates a working system that does exactly what the propstore's world model needs: maintaining multiple belief contexts, detecting contradictions, identifying culprits, and revising beliefs. This complements the de Kleer ATMS papers already in the collection by providing an alternative approach (relevance-logic-based with richer connectives, user-interactive revision) to the same family of problems.

## Open Questions
- [ ] How does SWM's handling of contradictions compare to the ATMS's nogood sets in terms of computational efficiency?
- [ ] Can the MBR model be extended with automated culprit selection (rather than interactive)?
- [ ] What would a model-theoretic semantics for SWM look like?
- [ ] How does the approach scale with large numbers of hypotheses and contexts?

## Related Work Worth Reading
- Martins, J., "Reasoning in multiple belief spaces" (Ph.D. Dissertation, 1983, SUNY Buffalo) - the full dissertation underlying this paper [25]
- Martins, J. and Shapiro, S., "Reasoning in multiple belief spaces" (IJCAI-83) [28]
- Martins, J., "Belief revision" in Encyclopedia of AI (Wiley, 1987) [26]
- Shapiro, S. and Rapaport, W., "SNePS considered as a fully intensional propositional semantic network" (1987) [49]
- Goodwin, J.W., "A Theory and System for Non-Monotonic Reasoning" (Linkoping dissertation, 1987) [18]
