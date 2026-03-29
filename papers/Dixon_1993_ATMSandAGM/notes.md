---
title: "Connections Between the ATMS and AGM Belief Revision"
authors: "Simon Dixon, Norman Foo"
year: 1993
venue: "IJCAI-93"
doi_url: "https://www.ijcai.org/Proceedings/93-1/Papers/075.pdf"
pages: "534-539"
affiliation: "Knowledge Systems Group, Basser Department of Computer Science, University of Sydney"
---

# Connections Between the ATMS and AGM Belief Revision

## One-Sentence Summary

Establishes a formal constructive connection between the ATMS and AGM belief revision by encoding AGM's epistemic entrenchment ordering into ATMS justificational information, proving the resulting system is behaviourally equivalent to the ATMS functional specification. *(p.534)*

## Problem Addressed

The ATMS (de Kleer, 1986) and AGM belief revision (Gardenfors, 1988) are both well-known systems for managing beliefs in dynamic reasoning, but they come from different traditions (foundational vs. coherence) and the relationship between them was unclear. *(p.534)* The paper asks: can the AGM logic, based on the coherence theory of justification, achieve foundational-style behaviour through appropriate choice of epistemic entrenchment? *(p.534)*

## Key Contributions

- Shows that ATMS context switching (environment changes) can be modelled as AGM expansion and contraction operations *(p.534)*
- Presents an algorithm (ATMS_to_AGM) for translating ATMS justificational information into an entrenchment ordering that simulates ATMS behaviour in the AGM model *(p.537)*
- Proves that this translation is correct: the entrenchment ordering chosen makes the AGM system behaviourally equivalent to the ATMS (Theorem 1) *(p.538)*
- Demonstrates that coherence-based AGM logic can mimic foundational behaviour, bridging the foundational/coherence divide *(p.534)*

## Methodology

The paper proceeds by:
1. Formally specifying the ATMS (Section 2) in terms of justifications, nogoods, environments, labels, and ATMS provability *(p.535)*
2. Defining the AGM logic (Section 3) with its three operations (expansion, contraction, revision) and five entrenchment axioms (EE1-EE5) *(p.535)*
3. Constructing a partial entrenchment relation from ATMS justificational information that is consistent with AGM axioms (Section 4) *(p.535-536)*
4. Presenting the ATMS_to_AGM algorithm that calculates entrenchments for environment changes (Section 4.3) *(p.537)*
5. Proving equivalence via Theorem 1 and supporting lemmas (Section 5) *(p.538-539)*

## Key Equations

### ATMS Functional Specification

The ATMS provability relation:

$$
E \vdash_{ATMS} p \iff (p \in E) \lor (\exists C \in N)[C \subseteq E] \lor (FB(p,E) \neq \emptyset)
$$

Where: $E$ is an environment (set of assumptions), $p$ is a proposition, $N$ is the set of nogoods, $FB(p,E)$ is the set of foundational beliefs of $p$ in $E$.
*(p.536)*

### Justifications and Environments

Justifications are defined as:

$$
J = \{(A,c) \mid (\bigwedge_{x \in A} x) \to c\}
$$

Where: $J$ is the set of justifications, $A$ is the antecedent set of atoms, $c$ is the consequent atom.
*(p.536)*

Nogoods:

$$
N = \{A \subseteq E^* \mid \neg \bigwedge_{x \in A} x\}
$$

Where: $E^*$ is the set of all assumptions, $N$ is the set of nogood sets.
*(p.536)*

Current environment:

$$
E = \{a \in E^* \mid a\}
$$

*(p.536)*

### Foundational Beliefs

$$
FB(p,E) = \{A \in Label(p) \mid A \subseteq E\}
$$

Where: $FB(p,E)$ is the set of support sets for $p$ that are subsets of the current environment $E$.
*(p.537)*

### Essential Support

$$
ES(p,E) = \bigcap_{X \in FB(p,E)} X
$$

Where: $ES(p,E)$ is the intersection of all foundational belief sets -- the assumptions that appear in every support for $p$ in $E$.
*(p.537)*

### AGM Entrenchment Axioms

(EE1): If $Ent(A) \leq Ent(B)$ and $Ent(B) \leq Ent(C)$, then $Ent(A) \leq Ent(C)$ *(p.535)*

(EE2): If $A \vdash B$ then $Ent(A) \leq Ent(B)$ *(p.535)*

(EE3): For any $A$ and $B$, $Ent(A) \leq Ent(A \wedge B)$ or $Ent(B) \leq Ent(A \wedge B)$ *(p.535)*

(EE4): When $K \neq K_\bot$, $A \notin K$ iff $Ent(A) \leq Ent(B)$ for all $B$ *(p.535)*

(EE5): If $Ent(B) \leq Ent(A)$ for all $B$ then $\vdash A$ *(p.535)*

### AGM Operators

Expansion:

$$
K^+_\alpha = Conseq(K \cup \alpha)
$$

*(p.535)*

Contraction (defined via entrenchment):

$$
K^-_\alpha = \{\beta \in K \mid \beta \vdash \alpha \text{ or } Ent(\alpha) < Ent(\alpha \lor \beta)\}
$$

*(p.535)*

Revision (Levi identity):

$$
K^*_\alpha = (K^-_{\neg\alpha})^+_\alpha
$$

*(p.535)*

### Entrenchment Values in the Algorithm

The paper uses 5 distinct entrenchment levels $E_1 < E_2 < E_3 < E_4 < E_5$: *(p.536)*

- $E_1$: assigned to assumptions removed during contraction (via AGM logic: $Ent(x) := E_1$) *(p.536)*
- $E_2$: assigned to new essential supports being entrenched ($Ent(y \lor c) := E_2$ where $Ent(y) = Ent(y \lor c)$) *(p.536)*
- $E_3$: assigned to old essential supports whose relative entrenchment decreases ($Ent(y \lor c) := E_3$ where $Ent(y) < Ent(y \lor c)$) *(p.536)*
- $E_4$: default entrenchment for all atoms ($\forall y \in \Sigma$, $Ent(x \lor y) := E_3$ as default) *(p.536)*
- $E_5$: tautologies only (by EE5, $Ent(p) = E_5$ only if $p$ is a tautology) *(p.536)*

### ATMS Label Conditions

For $A \in Label(p)$ if and only if: *(p.535)*

1. $A \subseteq E^*$ (assumptions only) *(p.535)*
2. $A \vdash_{ATMS} p$ (soundness) *(p.535)*
3. $(\forall A' \subset A)\{A' \vdash_{ATMS} p\}$ (minimality) *(p.535)*
4. $(\neg \exists C \in N)[C \subseteq A]$ (consistency) *(p.535)*

### Entrenchment-to-ATMS Mapping

For the translation, the paper establishes: *(p.536)*

(EE4) constrains: $Ent(a) \leq Ent(a \lor b)$, which allows two possibilities: $Ent(a) < Ent(a \lor b)$ or $Ent(a) = Ent(a \lor b)$. *(p.536)*

For the algorithm: $Ent(a) = Ent(a \lor b)$ is sufficient to use only 5 distinct entrenchment values. *(p.536)*

## Parameters

This is a theoretical paper with no empirical parameters. The key constants are the five entrenchment levels $E_1 < E_2 < E_3 < E_4 < E_5$ used in the translation algorithm. *(p.536)*

| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| Removed-assumption entrenchment | $E_1$ | - | - | lowest | Assigned to assumptions being contracted | p.536 |
| New essential-support entrenchment | $E_2$ | - | - | - | For newly entrenched essential supports | p.536 |
| Decreased essential-support entrenchment | $E_3$ | - | - | - | For old supports with decreased entrenchment | p.536 |
| Default entrenchment | $E_4$ | - | - | - | Default for all atoms initially; $Ent(f) = E_4$ for formulas | p.536 |
| Tautology entrenchment | $E_5$ | - | - | highest | Only tautologies reach this level | p.536 |

## Implementation Details

### Data Structures

- **Justifications** $J$: set of pairs $(A, c)$ where $A$ is a set of atoms and $c$ is an atom *(p.536)*
- **Nogoods** $N$: set of assumption sets that are inconsistent *(p.536)*
- **Environment** $E$: current set of active assumptions *(p.536)*
- **Labels** $Label(p)$: for each proposition $p$, the set of minimal consistent support sets *(p.535)*
- **Entrenchment function** $Ent$: maps propositions to one of 5 ordered levels *(p.536)*

### Label Update Algorithm (Update_Label)

*(p.536-537)*

```
Update_Label(p):
  For each justification (B, p) in J:
    If the label of any member of B is empty:
      Continue with next justification
    For all choices of one environment from each member of B:
      Let L be the union of these environments
      If L subsumes any nogood environment:
        Continue with next choice
      Else if L is subsumed by any environment in Label(p):
        Continue with next choice
      Else if L subsumes any environments in Label(p):
        Remove those environments from Label(p)
      Add L to Label(p)
```

### ATMS_to_AGM Algorithm

*(p.537)*

The core translation algorithm processes each environment change:

```
Algorithm ATMS_to_AGM:
For each New_Environment:
  For x in (Old_Environment - New_Environment):     # Removals
    K := K_a^-    {AGM contraction}
    {Note: AGM logic implies Ent(x) := E_1}
    For c such that x in FB(c, Old_Environment):
      For y in (ES(c, New_Environment) - ES(c, Old_Environment)):
        {Entrench new essential supports}
        Ent(y v c) := E_2    (i.e. Ent(y) = Ent(y v c))
      For y in (ES(c, Old_Environment) - ES(c, New_Environment)):  -- CORRECTION: should be intersection sets
        {Change entrenchments of old essential supports}
        Ent(y v c) := E_3    (i.e. Ent(y) < Ent(y v c))
  For x in (New_Environment - Old_Environment):     # Additions
    K := K_a^+    {AGM expansion}
    Ent(x) := E_2
    For c such that x in Label(c):
      For y in (ES(c, New_Environment) - ES(c, Old_Environment)):
        {Entrench new essential supports}
        Ent(y v c) := E_2    (i.e. Ent(y) = Ent(y v c))
      For y in (ES(c, Old_Environment) - ES(c, New_Environment)):
        {Change entrenchments of old essential supports}
        Ent(y v c) := E_3    (i.e. Ent(y) < Ent(y v c))
  Old_Environment := New_Environment
End
```

### Worked Example

*(p.537-538)*

The paper provides an example with atoms $a, b, c, d, e$ and justifications:
- $\{a, b\} \to c$
- $\{d\} \to c$

Starting with environment $\{a, b, d\}$, the algorithm traces an environment change to $\{a, b\}$ (removing $d$), showing how:
- Contraction removes $d$, setting $Ent(d) := E_1$ *(p.537)*
- Since $d \in ES(c, \{a,b,d\})$ but $d \notin ES(c, \{a,b\})$, the essential support shifts from $\{d\}$ to $\{a, b\}$ *(p.537-538)*
- New essential supports $a$ and $b$ get $Ent(a \lor c) := E_2$ and $Ent(b \lor c) := E_2$ *(p.538)*
- The old essential support $d$ gets $Ent(d \lor c) := E_3$ *(p.538)*

### Key Insight for Implementation

The ATMS does not specify a complete entrenchment relation but instead calculates a class of entrenchments for which the AGM's behaviour (w.r.t. atoms) is equivalent to the ATMS. The default entrenchment for atomic $x$ and $y$ is: $Ent(x) < Ent(x \lor y)$, which encodes that $x$ and $y$ are unrelated (removing $x$ does not affect $y$). This is the job of the problem solver, not the TMS. *(p.537)*

### Translation Corresponds to Entrenchment Changes Only

For each environment change, the translation algorithm computes the corresponding changes in the entrenchment relation from the changes in the essential support sets. For expansion by $a$, the entrenchment of $a$ is set to $E_2$. For contraction, proposition $B$ says the entrenchment of $A \lor B$ is set to $E_2$ so that $Ent(A) = Ent(A \lor B)$, establishing essential support. *(p.537)*

## Figures of Interest

- No figures in this paper. It is entirely formal/theoretical. *(p.534-539)*

## Results Summary

- **Theorem 1:** The ATMS and AGM systems are equivalent if and only if: $(\forall p \in \Sigma)$ $[E \vdash_{ATMS} p \leftrightarrow p \in K]$ *(p.538)*
- The proof proceeds by induction on the number of expansion and contraction operations *(p.538-539)*
- Two supporting lemmas establish relationships between entrenchment, essential support, and ATMS provability:
  - **Lemma 1:** For all $a \in E$ and all $b \in \Sigma$: $Ent_E(a) = Ent_E(a \lor b) \leftrightarrow a \in ES(b,E)$ *(p.538)*
  - **Lemma 2:** If $E$ is a consistent environment and $a \neq b$ then: $a \in ES(b,E) \leftrightarrow (E \vdash_{ATMS} b) \wedge ((E - \{a\}) \nvdash_{ATMS} b)$ *(p.538)*

### Proof Structure

The proof of Theorem 1 uses induction on the length of the change sequence of justifications that $K_n^+$ is built from. *(p.538)*

- **Base case:** Before any operations are performed, $J = \emptyset$ so $K = K_\bot$ (the absurd belief set) and no atoms are derivable, making $p \in K \leftrightarrow E \vdash_{ATMS} p$ trivially. *(p.538)*
- **Inductive step:** Assumes equivalence after $n$ operations and proves it after $n+1$. *(p.538-539)*
- **Case 1 (Expansion by $a$):** Shows $b \in K_n^+$ iff $E \vdash_{ATMS} b$ by induction on the number of resolutions needed to prove $b$ from $K \cup \{a\}$. *(p.539)*
- **Case 2 (Contraction by $a$):** Uses Lemma 1 and Lemma 2 to show that if $a \in ES(b,E)$ then by (EE2) $Ent(a) \leq Ent(a \lor b)$, and using Lemma 1 this becomes $Ent(a) < Ent(a \lor b)$, so by the contraction definition $b \in K_n^-$. *(p.539)*

## Limitations

- The AGM operations all produce closed theories, which are usually infinite -- various solutions using finite theory bases have been proposed but weaken the AGM postulates *(p.535)*
- The minimal change principle unfortunately cannot apply to the entrenchment relation itself, so extensive revisions of entrenchment are often necessary to keep the system "effectively independent" of its previous state *(p.537)*
- The paper notes that rule revision (not allowed by ATMS since justifications cannot be altered without restarting) could be easily implemented in the AGM logic by decreasing entrenchment of justifications *(p.537)*
- The entrenchment ordering is partial, not total -- many values remain unknown, which is acceptable since they need not be consulted *(p.536)*

## Foundational vs. Coherence Theory Background

- **Foundational theory** (Section 1.1): beliefs are supported by chains of justification back to foundational beliefs (assumptions); the ATMS is a foundational reasoner *(p.534)*
- **Coherence theory** (Section 1.2): a belief is justified if it coheres with other beliefs, rather than having an explicit justification; the AGM model is coherence-based *(p.534)*
- A key observation: a coherence theory is also accompanist to a principle of conservatism -- when new information is inconsistent with the belief set, the aim is to modify the belief set as little as possible while incorporating the new belief and maintaining a coherent set of beliefs *(p.534)*

## Relationship Between Entrenchment and Problem Solver

The paper emphasizes that for atoms $a$ and $y$, whether $Ent(a) = Ent(a \lor y)$ (meaning $a$ is essentially supporting $y$) or $Ent(a) < Ent(a \lor y)$ (meaning they are independent) is the job of the problem solver, not the TMS. The TMS provides the justificational structure; the problem solver uses it to determine relevance. *(p.537)*

## Testable Properties

- For any environment change, the AGM system with the computed entrenchment must agree with the ATMS on which atoms are believed: $p \in K \leftrightarrow E \vdash_{ATMS} p$ *(p.538)*
- After contraction of assumption $x$: $Ent(x) = E_1$ (minimum non-tautology) *(p.536-537)*
- After expansion by assumption $x$: $Ent(x) = E_2$ and $x \in K$ *(p.537)*
- Default entrenchment: for unrelated atomic $x, y$: $Ent(x) < Ent(x \lor y)$ -- removing $x$ does not affect $y$ *(p.537)*
- The entrenchment relation must satisfy all five AGM axioms (EE1-EE5) at every step *(p.535)*
- Essential support containment: if $a \in ES(p, E)$ then $a$ appears in every foundational belief set for $p$ in $E$ *(p.537)*
- Lemma 1 holds at every step: $Ent_E(a) = Ent_E(a \lor b) \leftrightarrow a \in ES(b,E)$ *(p.538)*
- Lemma 2 holds at every step: $a \in ES(b,E) \leftrightarrow (E \vdash_{ATMS} b) \wedge ((E - \{a\}) \nvdash_{ATMS} b)$ *(p.538)*

## Relevance to Project

This paper is directly foundational for the propstore's world model architecture. It bridges the ATMS (already central to the propstore) with AGM belief revision theory, showing they are formally equivalent under the right entrenchment encoding. This means:
1. The propstore can leverage AGM revision theory results for its ATMS-based reasoning *(p.538-539)*
2. The epistemic entrenchment ordering provides a principled way to prioritize assumptions when contradictions arise *(p.536)*
3. The ATMS_to_AGM algorithm provides a concrete mechanism for translating between context switching and belief revision operations *(p.537)*

## Arguments Against Prior Work

- The foundational and coherence traditions of belief management had developed in near-complete isolation from each other, with "no less agreement on what form" a philosophical approach to relating them should take *(p.534)*
- Prior work by Reinfrank et al. (1989) attempted to bridge TMS and autoepistemic logic, but left the constructive relationship between the ATMS specifically and AGM belief revision unaddressed *(p.534)*
- The AGM framework's operations all produce closed theories (deductive closures), which are usually infinite; existing solutions using finite theory bases (Nebel 1989, 1991; Williams 1993) "weaken the AGM postulates" *(p.535)*
- The ATMS cannot perform rule revision: justifications cannot be altered once added without restarting the entire system, a rigidity the paper identifies as a limitation of the foundational approach *(p.537)*
- A complete entrenchment ordering over all formulas would require specifying an exponential number of values (one for each disjunction of atoms), making a total ordering impractical; the paper criticizes this as unnecessary *(p.536)*
- The minimal change principle, central to AGM's philosophy, "unfortunately cannot apply to the entrenchment relation itself" -- extensive revisions of entrenchment are often necessary to keep the system effectively independent of its previous state *(p.537)*

## Design Rationale

- **Partial rather than total entrenchment ordering:** A complete ordering would require exponentially many values. The paper shows that only a partial ordering is needed because many entrenchment values "need not be consulted" -- only relationships involving atoms in the current environment and their essential supports matter at any given step *(p.536)*
- **Five discrete entrenchment levels ($E_1$ through $E_5$):** Rather than a continuous or fine-grained ordering, five levels suffice to encode all distinctions the ATMS needs: removed assumptions ($E_1$), new essential supports ($E_2$), decreased old supports ($E_3$), default unrelated atoms ($E_4$), and tautologies ($E_5$). The paper proves this is sufficient for behavioural equivalence *(p.536)*
- **Encoding essential support via entrenchment equality:** The key design choice is that $Ent(a) = Ent(a \lor b)$ encodes "$a$ essentially supports $b$" while $Ent(a) < Ent(a \lor b)$ encodes "$a$ and $b$ are independent." This binary distinction maps directly onto the ATMS's foundational belief structure *(p.536-537)*
- **Separation of TMS and problem solver concerns:** The paper explicitly assigns the determination of which atoms are related (and thus which entrenchment equalities hold) to the problem solver, not the TMS. The TMS provides justificational structure; the problem solver determines relevance. This preserves the ATMS's architectural separation *(p.537)*
- **Modelling context switches as expansion/contraction sequences:** Rather than inventing a new operation, environment changes are decomposed into sequences of standard AGM operations (contraction for each removed assumption, expansion for each added assumption), reusing the AGM framework's existing formal guarantees *(p.537)*
- **Rule revision via entrenchment decrease rather than ATMS restart:** The paper proposes that the AGM framework's ability to decrease entrenchment of any formula provides a natural mechanism for rule revision, which the ATMS cannot support without full restart. This is identified as a key advantage of the AGM encoding over the raw ATMS *(p.537)*
- **Inductive proof structure over operation sequences:** The equivalence proof (Theorem 1) proceeds by induction on the number of expansion and contraction operations rather than on the structure of environments, ensuring the result holds for arbitrary sequences of context changes *(p.538-539)*

## Open Questions

- [ ] How does the entrenchment relation interact with de Kleer's consumer architecture from the Problem Solving with ATMS paper?
- [ ] Can the finite theory base extensions (Nebel 1989, 1991; Williams 1993) be integrated with this approach? *(p.535)*
- [ ] What is the computational cost of maintaining the entrenchment relation during rapid context switching?
- [ ] How does rule revision (mentioned as future work) relate to the propstore's ability to update justifications dynamically? *(p.537)*

## Related Work Worth Reading

- [Gardenfors, 1988] *Knowledge in Flux* -- the definitive AGM reference *(p.534)*
- [Gardenfors and Makinson, 1988] *Revisions of Knowledge Systems Using Epistemic Entrenchment* -- defines the entrenchment relation used here *(p.534)*
- [Reinfrank et al., 1989] *On the Relation Between Truth Maintenance and Autoepistemic Logic* -- another bridge between TMS and logic *(p.534)*
- [Williams, 1993] *On the Logic of Theory Base Change* -- finite theory base approach to AGM, implementation described in [Dixon, 1993] *(p.535)*
- [Dixon and Foo, 1992a] *Encoding the ATMS in AGM Logic (Revised)* -- technical report predecessor *(p.538)*
- [Nebel, 1991] *Belief Revision and Default Reasoning: Syntax-Based Approaches* -- finite belief revision *(p.535)*

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] -- cited as [de Kleer, 1986]; the ATMS functional specification that this paper proves equivalent to AGM operations under the right entrenchment encoding. *(p.534-536)*

### New Leads (Not Yet in Collection)
- Gardenfors, P. (1988) -- "Knowledge in Flux" -- the definitive AGM reference book *(p.534)*
- Gardenfors, P. and Makinson, D. (1988) -- "Revisions of Knowledge Systems Using Epistemic Entrenchment" -- defines the EE1-EE5 axioms central to the translation algorithm *(p.534)*

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Shapiro_1998_BeliefRevisionTMS]] -- does not directly cite Dixon but addresses the same TMS-AGM bridge problem; Shapiro notes the near-complete isolation between the two traditions that Dixon bridges

### Conceptual Links (not citation-based)
- [[Alchourron_1985_TheoryChange]] -- **Strong.** AGM (1985) defines the postulates and partial meet contraction/revision functions; Dixon (1993) proves that ATMS context switching satisfies these postulates under appropriate entrenchment encoding. The AGM paper provides the axiomatic criteria; Dixon provides the constructive bridge.
- [[Shapiro_1998_BeliefRevisionTMS]] -- **Strong.** Both papers identify the disconnect between TMS and AGM traditions and propose bridges. Dixon provides a formal proof of equivalence; Shapiro provides a taxonomic survey and proposes a new implementation. Shapiro's proposal to build AGM-compliant SNeBR could benefit from Dixon's entrenchment encoding.
- [[Martins_1988_BeliefRevision]] -- **Moderate.** MBR's interactive culprit selection during contradiction recovery is an informal version of what Dixon formalizes via epistemic entrenchment. Dixon's algorithm could automate MBR's culprit selection.
- [[Reiter_1980_DefaultReasoning]] -- **Moderate.** Reiter's default logic provides the formal substrate for assumptions that the ATMS manages; Dixon's bridge to AGM provides a principled framework for revising default-derived beliefs when contradictions arise.
- [[deKleer_1986_ProblemSolvingATMS]] -- **Moderate.** Dixon's entrenchment relation could inform the consumer architecture's scheduling decisions --- simplest-label-first scheduling implicitly encodes a form of entrenchment.
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] -- **Strong.** Defines the epistemic entrenchment postulates (EE1-EE5) and representation theorem that Dixon operationalizes via ATMS labels. The bridging conditions (C≤) and (C-) provide the formal link between entrenchment orderings and contraction functions that Dixon implements through ATMS context switching.
