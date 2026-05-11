---
title: "Defeasible Contextual Reasoning with Arguments in Ambient Intelligence"
authors: "Antonis Bikakis, Grigoris Antoniou"
year: 2010
venue: "IEEE Transactions on Knowledge and Data Engineering, vol. 22, no. 11"
pages: "1492-1506"
doi_url: "https://doi.org/10.1109/TKDE.2010.37"
---

# Defeasible Contextual Reasoning with Arguments in Ambient Intelligence

## One-Sentence Summary
Extends Multi-Context Systems (MCS) with local defeasible theories, defeasible mapping rules, and a total preference ordering over contexts, then layers a Dung-style argumentation semantics and a distributed P2P query-evaluation algorithm on top to resolve conflicts arising from cross-context information flow in Ambient Intelligence settings.

## Problem Addressed
Ambient Intelligence (AmI) environments introduce four hard properties that prior MCS work does not jointly address: (i) imperfect, incomplete, possibly inconsistent local context knowledge; (ii) heterogeneous representations across autonomous ambient agents; (iii) inconsistencies created when imperfect information flows between contexts via mappings; (iv) the distributed nature of context, with no central reasoner. Existing MCS proposals (McCarthy 1993; Giunchiglia & Serafini 1994; Ghidini & Giunchiglia 2001; Roelofsen & Serafini 2005; Brewka & Eiter 2007) lack mechanisms tailored to these AmI characteristics, particularly for resolving inconsistencies that arise specifically through mapping rules. *(p.1493-1494)*

## Key Contributions
- **Representation model:** Multi-Context System where each context has a local defeasible theory (strict + defeasible local rules) plus a separate set of defeasible mapping rules whose body literals come from foreign contexts. *(p.1494)*
- **Total preference ordering** over contexts, used both for breaking ambiguity from foreign mappings and for prioritizing the trust placed in different agents' contributions. *(p.1494, p.1495)*
- **Argumentation framework** (Section 5) translating the MCS into Dung-style arguments-and-attacks, with novel attack/defeat notions that consult the context preference ordering on rules from different contexts. *(p.1496-1497)*
- **Distributed algorithm P2P_DR** (Section 6) for query evaluation across networked contexts; handles cycles, missing/unreachable peers, and incremental discovery. *(p.1497-1499)*
- **Soundness, completeness, termination** results relating P2P_DR to the model-theoretic and argumentation semantics. *(p.1500)*
- **Implementation and evaluation** in a P2P testbed showing scalability across context counts, theory sizes, and mapping density. *(p.1500-1501)*

## Methodology
The paper composes three interlocking layers. First, a representation layer recasts MCS contexts as defeasible theories (strict rules, defeasible rules) plus defeasible mapping rules whose bodies reference literals from other contexts, with each context's mapping vocabulary disjoint from foreign contexts' local vocabularies. Second, an argumentation semantics layer interprets the resulting MCS as a Dung argumentation framework, where arguments are proof trees whose internal edges may cross context boundaries through mappings, and where attacks combine standard rebuttal/undermining with a context-preference test. Third, a distributed algorithm layer (P2P_DR) implements the semantics over a network of cooperating peers that exchange partial proofs and bookkeep cycles via histories. *(p.1494-1499)*

## Motivating Scenario
A "Smart Classroom" scenario (Section 2) is used throughout the paper. Five autonomous ambient agents — the smart phone, the laptop, the projector, the lecturer's mobile, and a classroom manager — each hold local context information (e.g., whether a phone is currently in use, whether a lecture is on, who the user is, current activity). They communicate via mapping rules to decide whether to ring, mute, project, etc. The example exposes how local incompleteness and inter-agent disagreement produce conflicts that must be defeasibly resolved. *(p.1493-1495)*

## Representation Model

A Multi-Context System $C = \{C_1, \dots, C_n\}$ where each $C_i = (V_i, R_i, T_i)$ with:
- $V_i$ — local vocabulary (finite set of positive and negative literals)
- $R_i$ — set of rules: local rules $r_l$ and mapping rules $r_m$
- $T_i$ — total preference ordering over contexts (irreflexive, antisymmetric, transitive); for $i \neq j$, exactly one of $C_i \succ_{T_i} C_j$ or $C_j \succ_{T_i} C_i$ holds. *(p.1494)*

Local rules in $C_i$ have body and head literals both drawn from $V_i$ and come in two kinds:
- **Strict local rules** $r_{li}^s : a_1, \dots, a_n \to a_h$ — express monotonic, definitionally certain knowledge. *(p.1494)*
- **Defeasible local rules** $r_{li}^d : a_1, \dots, a_n \Rightarrow a_h$ — express uncertainty; supportable but defeated by adequate contrary evidence. *(p.1494)*

Mapping rules in $C_i$ have heads in $V_i$ but body literals drawn from foreign vocabularies $V_j, j \neq i$:
$$
r_{mi} : a_1^j, a_2^k, \dots, a_n^l \Rightarrow a_h^i
$$
where each $a_p^x$ associates literal $a_p$ of $C_x$ with local literals of $C_i$ ($a_p^x$ at the body), and $a_h^i$ is a literal of $V_i$. Mapping rules are necessarily defeasible. *(p.1494)*

Loops in mapping graphs are addressed in Section 5 via histories. The body of a local rule cannot mix vocabularies of different contexts; only mapping rules allow that. *(p.1494)*

### Comparison to Brewka & Eiter MCS
Authors emphasize differences from Brewka & Eiter 2007: "their bridge rules can have mixed bodies and they assume a totally ordered preference relation only over the rules of a single context"; this paper's mapping rules separate inconsistency resolution to the mapping layer and use a context-level preference order. *(p.1494)*

## Argumentation Semantics

**Argument** $A$ for literal $p$ in context $C_i$ is a proof tree of rules $\mathrm{Rl}(A)$ from $C_i$ ranked by $T_i$. Built recursively in steps as follows:
- Step 1 (leaf): an argument for $p$ if there is a strict local rule with empty body and head $p$, or a fact.
- Steps n: extend by applying a strict or defeasible local rule, or a mapping rule whose body has been argued for in the relevant foreign contexts. *(p.1496)*

**Argument types:**
- **Supportive** — a proof of $p$ using only rules.
- **Strict** — uses only strict local rules.
- **Defeasible** — uses at least one defeasible rule (local or mapping).
- **Local** — uses only rules from $C_i$ (no mappings).

**Definitions of attack and defeat (informal, drawn from Definitions on p.1496):**
- $A$ attacks $B$ if their conclusions are complementary literals.
- $A$ defeats $B$ if $A$ is at least as strong as $B$ under context preference $T_i$ (the context whose conclusion is attacked).
- $A$ strictly defeats $B$ if $A$ defeats $B$ but $B$ does not defeat $A$.

**Acceptable argument:** $A$ is acceptable w.r.t. argument set $S$ if every argument $B$ that defeats $A$ is itself attacked by some argument in $S$. *(p.1496)*

**Justified argument** (Definition on p.1496): $A$ is justified iff (i) $A$ is a strict local argument, OR (ii) $A$ is supported by $S$ and every argument defeating $A$ is undercut by $S$.

**Justified literal:** $p$ is justified in $C_i$ iff there is a justified argument with conclusion $p$ in $C_i$. *(p.1496)*

**Rejected arguments:** $A$ is rejected by sets $S, T$ when (a) a proper subargument is in $S$, or (b) for every argument $A'$ defeating $A$, $A'$ is not defeated by an argument of $C_i$ supported by $T$, or (c) some sub-argument is rejected. *(p.1496)*

**Rejected literal:** $p$ is rejected in $C_i$ if every supporting argument for $p$ is rejected. *(p.1496)*

### Key Lemmas / Theorems
- **Lemma 1:** Justified literals satisfy monotonicity in $\mathcal{J}_i^C$ and $\mathcal{R}_i^C(T)$. *(p.1496)*
- **Lemma 2:** In a defeasible MCS $C$: no argument is both justified and rejected; no literal is both justified and rejected. *(p.1496)*
- **Lemma 3:** If the set of justified arguments in an MCS contains no two arguments with complementary conclusions, then both arguments are strict local arguments. *(p.1496)*
- **Theorem (correspondence to model theory)**: connects justified literals to the model-theoretic semantics introduced earlier in the paper (Section 4 and Appendix). *(p.1496-1497)*

### Worked example fragments (Smart Classroom)
Mapping conflicts on whether the phone should ring/silent are resolved by the context preference ordering: e.g., the lecturer's calendar context outranks the phone's default ring policy, so the silent conclusion wins. The example also illustrates how a chain of mappings through several contexts yields a justified argument when each link's defeaters are themselves rejected. *(p.1495-1497)*

## Distributed Algorithm P2P_DR

**Goal:** Given an MCS $C$ and a query literal $p$ at context $C_i$, return one of $\{+\Delta, -\Delta, +\partial, -\partial\}$ (definitely provable, definitely rejected, defeasibly provable, defeasibly rejected). *(p.1497-1498)*

**Inputs to a peer call (`P2P_DR`):**
- $p$ — query literal, in vocabulary of caller context
- $C_i$ — context being asked
- `Ans_set` — set of already-derived answers (cache)
- `Hist` — history (list) of pending queries forming the current path
- `BlockedQ_Set` — queries already proven blocked
- `Support_Set` — partial supportive arguments accumulated

**Outputs:** updated `Ans_set` (with the answer for $p$ at $C_i$), updated `BlockedQ_Set`, updated `Support_Set`. *(p.1498)*

**Cycle handling:** if the current query already appears in `Hist`, return blocked. Otherwise add the query to `Hist`, recurse on rule bodies, and remove on return. The local literals of $C_i$ are first decided via local strict/defeasible reasoning before consulting foreign contexts via mapping rules. *(p.1498-1499)*

**Subroutines (called within P2P_DR):**
- `Support` — checks whether body literals of a rule are all positively answered (provable / defeasibly provable, depending on rule kind), recurses into foreign contexts via P2P_DR.
- `Stronger` — compares two rules using $T_i$ to decide which prevails when their conclusions conflict.
- `Terminating_def_rules` — picks the next defeasible rule to consider.

**Algorithmic structure (high-level):**
1. If $p$ is in `Ans_set`, return cached answer.
2. Try strict local proof: if there is a strict rule with all body literals already in `+Δ`, conclude $+\Delta$.
3. Otherwise try defeasible local proof: a defeasible rule for $p$ whose body is supported and which is not defeated by any rule (local or mapping) for $\sim p$ that is itself supported and at least as strong. Conclude $+\partial$.
4. Mapping rules are processed analogously, but every body literal must be queried from its foreign context via a recursive `P2P_DR` call carrying the updated `Hist` and `BlockedQ_Set`.
5. Conflicting evidence is resolved by `Stronger` against $T_i$. *(p.1498-1499)*

**Properties:**
- **Soundness and completeness** with respect to the argumentation semantics on finite MCS (Section 6.2 / Theorem on p.1500).
- **Termination** in finite MCS due to the cycle-blocking history mechanism.
- **Complexity:** Polynomial in the size of the MCS for the propositional case, modulo the cost of cross-peer communication. *(p.1500)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of contexts | n | – | – | varies | 1494, 1500 | Size parameter for evaluation |
| Number of mapping rules | – | – | – | varies | 1500 | Density parameter for evaluation |
| Local theory size | – | rules | – | varies | 1500 | Per-context size driver |
| Preference relation | T_i | – | total order | total | 1494 | Irreflexive, antisymmetric, transitive |
| Vocabulary | V_i | literals | finite | – | 1494 | Disjoint mapping- vs local-vocabulary discipline |
| Answer labels | – | – | – | {+Δ, −Δ, +∂, −∂} | 1498 | Defeasible-logic style four-valued result |

## Methods & Implementation Details
- **Theory languages:** propositional defeasible logic for local theories; mapping rules are defeasible only. *(p.1494)*
- **Total preference ordering** is per-context; an agent ranks every other agent. No global ordering is assumed. *(p.1494)*
- **Argumentation construction:** arguments are proof trees with optional cross-context branches via mappings; trees are finite by construction in a finite MCS. *(p.1496)*
- **Distributed algorithm** uses peer-to-peer message passing; histories travel with calls to detect cycles; blocked queries are cached to avoid repeated work. *(p.1498-1499)*
- **Implementation:** prototype in Java built on a peer-to-peer overlay; experiments report query response time as a function of (a) number of contexts, (b) average local theory size, (c) average mapping rule count per context. *(p.1500-1501)*

## Figures of Interest
- **Fig 1 (p.1493):** Smart-classroom scenario — devices, lecturer, manager, mappings.
- **Fig 2 (p.1495):** Inheritance/conflict diagram for the Ambient Intelligence example.
- **Fig 3 (p.1500):** Architecture of the distributed query-evaluation prototype.
- **Fig 4-5 (p.1501-1502):** Scalability plots — response time vs context count, theory size, and mapping density.

## Results Summary
The argumentation semantics is shown sound and complete relative to the model-theoretic semantics, and the distributed algorithm is shown sound and complete relative to the argumentation semantics. Empirically, P2P_DR scales near-linearly with the number of contexts and sublinearly with theory size, while increasing mapping density predictably worsens latency due to additional cross-peer messages. The framework successfully resolves all motivating-scenario conflicts using only the encoded context preferences. *(p.1500-1502)*

## Limitations
- **Total preference ordering** assumption may not be realistic in many AmI settings; partial orders are deferred to follow-up work. *(p.1503)*
- **Propositional only**: the model is currently propositional defeasible logic; first-order extension is left for future work. *(p.1503)*
- **Cooperative peers** — peers are assumed to honestly share context; adversarial or strategic agents are out of scope. *(p.1503)*
- **No belief revision / dynamics** — context theories are static during query evaluation. *(p.1503)*

## Arguments Against Prior Work
- **Brewka & Eiter 2007** (Equilibria for Heterogeneous Nonmonotonic MCS): bridge rules with mixed bodies and only single-context preferences over rules cannot adequately resolve conflicts that originate in inter-context information flow. The proposed model isolates inconsistency to mapping rules and uses context-level preferences. *(p.1494)*
- **Roelofsen & Serafini 2005**: their MCS does not handle imperfect/defeasible context information; they assume each local theory is consistent. *(p.1494, p.1503)*
- **Ghidini & Giunchiglia 2001 (Local Models Semantics)**: provides only a model-theoretic semantics with no operational reasoning procedure suitable for distributed AmI deployment. *(p.1494)*
- **Single-context defeasible logic (Antoniou et al.)**: cannot model the heterogeneity and autonomy of AmI agents — every agent collapses into the same vocabulary. *(p.1494)*

## Design Rationale
- **Why mapping rules separate from local rules:** the source of cross-context inconsistency is exactly the use of foreign literals; isolating it to defeasible mapping rules localizes both the conflict and the resolution machinery. *(p.1494)*
- **Why context-level preference instead of rule-level:** an agent typically trusts other agents differently based on role/source rather than per-rule; context preferences are more interpretable and easier to author. *(p.1494)*
- **Why argumentation rather than direct fixed-point semantics:** argumentation makes proof structures explicit, so distributed peers can exchange and inspect partial supports across contexts. *(p.1496)*
- **Why P2P rather than centralized:** an AmI environment has no privileged controller; pushing all theories to a central reasoner is unrealistic. *(p.1497)*

## Testable Properties
- **No literal is both justified and rejected** in any defeasible MCS. *(p.1496)*
- **No argument is both justified and rejected**. *(p.1496)*
- **If two justified arguments have complementary conclusions, both are strict local arguments.** *(p.1496)*
- **P2P_DR terminates** on every finite MCS. *(p.1500)*
- **P2P_DR is sound and complete** with respect to the argumentation semantics. *(p.1500)*
- **Argumentation semantics agrees with the model-theoretic semantics.** *(p.1496-1497)*

## Relevance to Project
This paper is the canonical 2010 statement of distributed defeasible reasoning with arguments over Multi-Context Systems and the closest competitor / alternative to Al-Anbaki 2019's framework. For propstore it provides:
- A worked specification of how Dung-style arguments can be built across contexts via defeasible mapping rules — directly relevant to the `propstore.aspic_bridge` boundary and to the CKR-style justifiable-exception machinery in `propstore.defeasibility` that already injects exception-derived defeats at the ASPIC+ boundary.
- A concrete operational protocol (P2P_DR) for distributed evaluation that propstore can compare against its own ATMS-based world reasoning when contexts are physically partitioned.
- A precedent for using a context-level preference ordering instead of the rule-level priorities used in DeLP/ASPIC+, which is relevant to design choices in `propstore.aspic_bridge`'s priority translator.
- Soundness/completeness/termination results that double as testable properties for any propstore re-implementation.
- The total-ordering and propositional-only limitations match exactly the directions later papers (Bozzato 2018, Bozzato 2020, Governatori 2012) try to relax — propstore's storage layer can hold competing formalizations without committing.

## Open Questions
- [ ] How does P2P_DR's notion of "blocked" query interact with propstore's lazy/render-time resolution discipline?
- [ ] Can the context-preference test be expressed as an ASPIC+ priority on the translated rules in `propstore.aspic_bridge`?
- [ ] Is the soundness-vs-argumentation theorem strong enough that a centralized rebuild (over propstore's ATMS) yields the same justified literals?
- [ ] Where does this framework break under partial preference orders (the Bikakis & Antoniou 2011 follow-up addresses this)?

## Workflow Checkpoint (paper-reader + reconcile, 2026-05-07)

**State:**
- Retrieved via sci-hub (DOI 10.1109/TKDE.2010.37, S2 ID `ff56376e…`); 813 KB, 15 pages.
- All 15 page images read; notes.md / metadata.json / abstract.md / citations.md / description.md written.
- Reconcile in progress: forward refs identified (Ghidini_2001 already in collection; Antoniou_2000 already in collection; Brewka_2007 / Roelofsen_2005 / Governatori_2004 / Dung_1995 are new leads).
- Reverse cited-by: `grep` over the collection finds Bozzato_2018 (cites as [25]) and Al-Anbaki_2019 (cites as [16][22]). Two collection citers — both annotated.
- Bidirectional updates done in Al-Anbaki_2019 (lead → "Now in Collection" + inline `→ NOW IN COLLECTION:` marker) and Bozzato_2018 (inline marker on Related Work + lead-list annotation).
- Pending: Cited By section on this paper's notes; index.md update.

**Blocker:** none.

### Checkpoint update (post bidirectional Conceptual-Links)
- Bidirectional Conceptual-Links annotation done in:
  - `papers/Bozzato_2020_DatalogDefeasibleDLLite/notes.md` — appended Bikakis 2010 entry to existing Conceptual Links list (under defeasible-MCS theme).
  - `papers/Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md` — appended Bikakis 2010 entry under "Defeasibility and contexts" subsection.
- Bidirectional Cited-By annotation done in:
  - `papers/Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md` — moved Bikakis 2010 lead to "Now in Collection" + inline `→ NOW IN COLLECTION:` marker.
  - `papers/Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md` — inline marker on Related Work + lead-list annotation.
- Pending: papers/index.md update; final report.

## Related Work Worth Reading
- Brewka & Eiter 2007 (Equilibria of Heterogeneous Nonmonotonic Multi-Context Systems) — the immediate predecessor MCS proposal this paper criticizes.
- Roelofsen & Serafini 2005 — the consistent-context MCS variant the paper extends.
- Ghidini & Giunchiglia 2001 — Local Models Semantics, the founding MCS semantics. *(already in collection)*
- Antoniou et al., Defeasible Logic — single-context defeasible reasoning that the local-context layer instantiates.
- Dung 1995 — the abstract argumentation framework underlying the argumentation layer.
- Bikakis & Antoniou 2011 — partial-preference follow-up to relax the total-ordering assumption.
- Bozzato 2018 (Justifiable Exceptions for Contextual Knowledge Repair) — adjacent CKR-based exception machinery.

## Collection Cross-References

### Already in Collection
- [Local Models Semantics, or Contextual Reasoning = Locality + Compatibility](../Ghidini_2001_LocalModelsSemanticsContextual/notes.md) — cited as ref [13]; the Local Models Semantics this paper extends with defeasible local theories and defeasible mapping rules. Bikakis & Antoniou's MCS shape (per-context vocabulary + cross-context mappings) directly inherits LMS's locality+compatibility split.
- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — cited as ref [26]; the canonical single-context defeasible-logic paper whose proof system this paper lifts to the multi-context setting and re-uses the `±Δ / ±∂` derivation tags from.

### New Leads (Not Yet in Collection)
- **Brewka, Roelofsen & Serafini (2007) — "Contextual Default Reasoning," IJCAI.** Ref [16]. The MCS proposal this paper most directly criticizes (mixed bridge bodies + only single-context preferences). High priority for closing the MCS lineage in propstore.
- **Governatori, Maher, Antoniou & Billington (2004) — "Argumentation Semantics for Defeasible Logic," JLC 14(5):675-702.** Ref [24]. Single-context argumentation semantics for DL that the multi-context argumentation here generalizes.
- **Roelofsen & Serafini (2005) — "Minimal and Absent Information in Contexts," IJCAI.** Ref [15]. The consistent-context MCS variant being relaxed.
- **Dung (1995) — "On the Acceptability of Arguments and Its Fundamental Role in Nonmonotonic Reasoning, Logic Programming and N-Person Games," AIJ 77.** Ref [25]. The abstract argumentation framework underlying this paper's attack/defeat machinery; foundational and worth ingesting.
- **Adjiman, Chatalic, Goasdoué, Rousset & Simon (2006) — "Distributed Reasoning in a Peer-to-Peer Setting: Application to the Semantic Web," JAIR 25:269-314.** Ref [28]. Comparator distributed reasoner.
- **Bikakis, Patkos, Antoniou, Plexousakis (2008) — "A Survey of Semantics-Based Approaches for Context Reasoning in Ambient Intelligence."** Ref [4]. AmI context-reasoning survey.
- **Buvac & Mason (1993) — "Propositional Logic of Context," AAAI.** Ref [10]. Companion to McCarthy's `ist` formalisation.
- **Calvanese et al. (2005) — "Inconsistency Tolerance in P2P Data Integration: An Epistemic Logic Approach," DBPL.** Ref [20]. P2P data-integration comparator.
- **Chatalic, Nguyen & Rousset (2006) — "Reasoning with Inconsistencies in Propositional Peer-to-Peer Inference Systems," ECAI.** Ref [21]. P2P reasoning with inconsistency.
- **Dastani, Governatori, Rotolo, Song & van der Torre (2007) — "Contextual Deliberation of Cognitive Agents in Defeasible Logic," AAMAS.** Ref [19]. Agent-side defeasible-context companion.

### Supersedes or Recontextualizes
- (none) — this paper extends Brewka/Roelofsen/Serafini-style MCS but does not supersede a paper already in the collection.

### Cited By (in Collection)
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — cites this as ref [25] / "alternative argumentation-based approach to defeasible MCS"; CKR's clashing-assumption mechanism and Bikakis & Antoniou's context-preference-driven defeats are independent answers to the same exception-handling question. Direct comparison point.
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this as refs [16] and [22], naming Bikakis & Antoniou's line as the closest competitor for distributed defeasible reasoning. Al-Anbaki et al. characterise this paper's framework as a *characterisation* of distributed defeasible reasoning rather than a deployed-application framework, and position their `L = ⟨G, β, D, λ⟩` as the engineering counterpart.

### Conceptual Links (not citation-based)

**Multi-context defeasibility (direct mechanism overlap):**
- [A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility](../Bozzato_2020_DatalogDefeasibleDLLite/notes.md) — Strong. Bozzato et al. give a datalog operationalisation of CKR-style defeasible context reasoning over DL-Lite_R, while Bikakis & Antoniou give an argumentation/P2P operationalisation over propositional MCS. Both attach defeasibility to inter-context information flow; the choice between argumentation+context-preference and CKR clashing-assumptions is precisely the design choice propstore needs to hold without committing.
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — Strong. Governatori et al. revise the superiority relation `>` over single-context DL; this paper builds on a per-context preference ordering `T_i` that is exactly the multi-context generalisation Governatori 2012's machinery would need to revise. The two pair naturally for any propstore work that wants dynamic per-context preferences.

**Single-context defeasible foundations:**
- [Representation Results for Defeasible Logic](../Antoniou_2000_RepresentationResultsDefeasibleLogic/notes.md) — Moderate. Antoniou et al. show how to eliminate facts/defeaters/superiority by transformation in single-context DL; the same transformations would need a per-context generalisation to apply to Bikakis & Antoniou's MCS. Useful upstream theoretical anchor.

**Context formalisation lineage:**
- [Notes on Formalizing Context](../McCarthy_1993_FormalizingContext/notes.md) — Moderate. McCarthy's `ist(c, p)` is the philosophical ancestor of MCS-style context formalisations; Bikakis & Antoniou's per-context theories and mapping rules are a defeasibility-aware concretisation of `ist`-style locality.
- [Formalizing Context (Expanded Notes)](../McCarthy_1997_FormalizingContextExpanded/notes.md) — Moderate. Expanded version of the same McCarthy programme; same conceptual relationship.
