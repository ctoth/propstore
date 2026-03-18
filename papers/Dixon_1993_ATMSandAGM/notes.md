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

Establishes a formal constructive connection between the ATMS and AGM belief revision by encoding AGM's epistemic entrenchment ordering into ATMS justificational information, proving the resulting system is behaviourally equivalent to the ATMS functional specification.

## Problem Addressed

The ATMS (de Kleer, 1986) and AGM belief revision (Gardenfors, 1988) are both well-known systems for managing beliefs in dynamic reasoning, but they come from different traditions (foundational vs. coherence) and the relationship between them was unclear. The paper asks: can the AGM logic, based on the coherence theory of justification, achieve foundational-style behaviour through appropriate choice of epistemic entrenchment?

## Key Contributions

- Shows that ATMS context switching (environment changes) can be modelled as AGM expansion and contraction operations
- Presents an algorithm (ATMS_to_AGM) for translating ATMS justificational information into an entrenchment ordering that simulates ATMS behaviour in the AGM model
- Proves that this translation is correct: the entrenchment ordering chosen makes the AGM system behaviourally equivalent to the ATMS (Theorem 1)
- Demonstrates that coherence-based AGM logic can mimic foundational behaviour, bridging the foundational/coherence divide

## Methodology

The paper proceeds by:
1. Formally specifying the ATMS (Section 2) in terms of justifications, nogoods, environments, labels, and ATMS provability
2. Defining the AGM logic (Section 3) with its three operations (expansion, contraction, revision) and five entrenchment axioms (EE1-EE5)
3. Constructing a partial entrenchment relation from ATMS justificational information that is consistent with AGM axioms (Section 4)
4. Presenting the ATMS_to_AGM algorithm that calculates entrenchments for environment changes (Section 4.3)
5. Proving equivalence via Theorem 1 and supporting lemmas (Section 5)

## Key Equations

### ATMS Functional Specification

The ATMS provability relation:

$$
E \vdash_{ATMS} p \iff (p \in E) \lor (\exists C \in N)[C \subseteq E] \lor (FB(p,E) \neq \emptyset)
$$

Where: $E$ is an environment (set of assumptions), $p$ is a proposition, $N$ is the set of nogoods, $FB(p,E)$ is the set of foundational beliefs of $p$ in $E$.

### Justifications and Environments

Justifications are defined as:

$$
J = \{(A,c) \mid (\bigwedge_{x \in A} x) \to c\}
$$

Where: $J$ is the set of justifications, $A$ is the antecedent set of atoms, $c$ is the consequent atom.

Nogoods:

$$
N = \{A \subseteq E^* \mid \neg \bigwedge_{x \in A} x\}
$$

Where: $E^*$ is the set of all assumptions, $N$ is the set of nogood sets.

Current environment:

$$
E = \{a \in E^* \mid a\}
$$

### Foundational Beliefs

$$
FB(p,E) = \{A \in Label(p) \mid A \subseteq E\}
$$

Where: $FB(p,E)$ is the set of support sets for $p$ that are subsets of the current environment $E$.

### Essential Support

$$
ES(p,E) = \bigcap_{X \in FB(p,E)} X
$$

Where: $ES(p,E)$ is the intersection of all foundational belief sets -- the assumptions that appear in every support for $p$ in $E$.

### AGM Entrenchment Axioms

(EE1): If $Ent(A) \leq Ent(B)$ and $Ent(B) \leq Ent(C)$, then $Ent(A) \leq Ent(C)$

(EE2): If $A \vdash B$ then $Ent(A) \leq Ent(B)$

(EE3): For any $A$ and $B$, $Ent(A) \leq Ent(A \wedge B)$ or $Ent(B) \leq Ent(A \wedge B)$

(EE4): When $K \neq K_\bot$, $A \notin K$ iff $Ent(A) \leq Ent(B)$ for all $B$

(EE5): If $Ent(B) \leq Ent(A)$ for all $B$ then $\vdash A$

### AGM Operators

Expansion:

$$
K^+_\alpha = Conseq(K \cup \alpha)
$$

Contraction:

$$
K^-_\alpha = \{\beta \in K \mid \beta \vdash \alpha \text{ or } Ent(\alpha) < Ent(\alpha \lor \beta)\}
$$

Revision (Levi identity):

$$
K^*_\alpha = (K^-_{\neg\alpha})^+_\alpha
$$

### Entrenchment Values in the Algorithm

The paper uses 5 distinct entrenchment levels $E_1 < E_2 < E_3 < E_4 < E_5$:

- $E_1$: assigned to assumptions removed during contraction (via AGM logic: $Ent(x) := E_1$)
- $E_2$: assigned to new essential supports being entrenched ($Ent(y \lor c) := E_2$ where $Ent(y) = Ent(y \lor c)$)
- $E_3$: assigned to old essential supports whose relative entrenchment decreases ($Ent(y \lor c) := E_3$ where $Ent(y) < Ent(y \lor c)$)
- $E_4$: default entrenchment for all atoms ($\forall y \in \Sigma$, $Ent(x \lor y) := E_3$ as default)
- $E_5$: tautologies only (by EE5, $Ent(p) = E_5$ only if $p$ is a tautology)

### ATMS Label Conditions

For $A \in Label(p)$ if and only if:

1. $A \subseteq E^*$ (assumptions only)
2. $A \vdash_{ATMS} p$ (soundness)
3. $(\forall A' \subset A)\{A' \vdash_{ATMS} p\}$ (minimality)
4. $(\neg \exists C \in N)[C \subseteq A]$ (consistency)

### Entrenchment-to-ATMS Mapping

For the translation, the paper establishes:

(EE4) constrains: $Ent(a) \leq Ent(a \lor b)$, which allows two possibilities: $Ent(a) < Ent(a \lor b)$ or $Ent(a) = Ent(a \lor b)$.

For the algorithm: $Ent(a) = Ent(a \lor b)$ is sufficient to use only 5 distinct entrenchment values.

## Parameters

This is a theoretical paper with no empirical parameters. The key constants are the five entrenchment levels $E_1 < E_2 < E_3 < E_4 < E_5$ used in the translation algorithm.

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Removed-assumption entrenchment | $E_1$ | - | - | lowest | Assigned to assumptions being contracted |
| New essential-support entrenchment | $E_2$ | - | - | - | For newly entrenched essential supports |
| Decreased essential-support entrenchment | $E_3$ | - | - | - | For old supports with decreased entrenchment |
| Default entrenchment | $E_4$ | - | - | - | Default for all atoms initially; $Ent(f) = E_4$ for formulas |
| Tautology entrenchment | $E_5$ | - | - | highest | Only tautologies reach this level |

## Implementation Details

### Data Structures

- **Justifications** $J$: set of pairs $(A, c)$ where $A$ is a set of atoms and $c$ is an atom
- **Nogoods** $N$: set of assumption sets that are inconsistent
- **Environment** $E$: current set of active assumptions
- **Labels** $Label(p)$: for each proposition $p$, the set of minimal consistent support sets
- **Entrenchment function** $Ent$: maps propositions to one of 5 ordered levels

### Label Update Algorithm (Update_Label)

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

### Key Insight for Implementation

The ATMS does not specify a complete entrenchment relation but instead calculates a class of entrenchments for which the AGM's behaviour (w.r.t. atoms) is equivalent to the ATMS. The default entrenchment for atomic $x$ and $y$ is: $Ent(x) < Ent(x \lor y)$, which encodes that $x$ and $y$ are unrelated (removing $x$ does not affect $y$). This is the job of the problem solver, not the TMS.

## Figures of Interest

- No figures in this paper. It is entirely formal/theoretical.

## Results Summary

- **Theorem 1:** The ATMS and AGM systems are equivalent if and only if: $(\forall p \in \Sigma)$ $[E \vdash_{ATMS} p \leftrightarrow p \in K]$
- The proof proceeds by induction on the number of expansion and contraction operations
- Two supporting lemmas establish relationships between entrenchment, essential support, and ATMS provability:
  - **Lemma 1:** For all $a \in E$ and all $b \in \Sigma$: $Ent_E(a) = Ent_E(a \lor b) \leftrightarrow a \in ES(b,E)$
  - **Lemma 2:** If $E$ is a consistent environment and $a \neq b$ then: $a \in ES(b,E) \leftrightarrow (E \vdash_{ATMS} b) \wedge ((E - \{a\}) \vdash_{ATMS} b)$

## Limitations

- The AGM operations all produce closed theories, which are usually infinite -- various solutions using finite theory bases have been proposed but weaken the AGM postulates
- The minimal change principle unfortunately cannot apply to the entrenchment relation itself, so extensive revisions of entrenchment are often necessary to keep the system "effectively independent" of its previous state
- The paper notes that rule revision (not allowed by ATMS since justifications cannot be altered without restarting) could be easily implemented in the AGM logic by decreasing entrenchment of justifications
- The entrenchment ordering is partial, not total -- many values remain unknown, which is acceptable since they need not be consulted

## Testable Properties

- For any environment change, the AGM system with the computed entrenchment must agree with the ATMS on which atoms are believed: $p \in K \leftrightarrow E \vdash_{ATMS} p$
- After contraction of assumption $x$: $Ent(x) = E_1$ (minimum non-tautology)
- After expansion by assumption $x$: $Ent(x) = E_2$ and $x \in K$
- Default entrenchment: for unrelated atomic $x, y$: $Ent(x) < Ent(x \lor y)$ -- removing $x$ does not affect $y$
- The entrenchment relation must satisfy all five AGM axioms (EE1-EE5) at every step
- Essential support containment: if $a \in ES(p, E)$ then $a$ appears in every foundational belief set for $p$ in $E$

## Relevance to Project

This paper is directly foundational for the propstore's world model architecture. It bridges the ATMS (already central to the propstore) with AGM belief revision theory, showing they are formally equivalent under the right entrenchment encoding. This means:
1. The propstore can leverage AGM revision theory results for its ATMS-based reasoning
2. The epistemic entrenchment ordering provides a principled way to prioritize assumptions when contradictions arise
3. The ATMS_to_AGM algorithm provides a concrete mechanism for translating between context switching and belief revision operations

## Open Questions

- [ ] How does the entrenchment relation interact with de Kleer's consumer architecture from the Problem Solving with ATMS paper?
- [ ] Can the finite theory base extensions (Nebel 1989, 1991; Williams 1993) be integrated with this approach?
- [ ] What is the computational cost of maintaining the entrenchment relation during rapid context switching?
- [ ] How does rule revision (mentioned as future work) relate to the propstore's ability to update justifications dynamically?

## Related Work Worth Reading

- [Gardenfors, 1988] *Knowledge in Flux* -- the definitive AGM reference
- [Gardenfors and Makinson, 1988] *Revisions of Knowledge Systems Using Epistemic Entrenchment* -- defines the entrenchment relation used here
- [Reinfrank et al., 1989] *On the Relation Between Truth Maintenance and Autoepistemic Logic* -- another bridge between TMS and logic
- [Williams, 1993] *On the Logic of Theory Base Change* -- finite theory base approach to AGM, implementation described in [Dixon, 1993]
- [Dixon and Foo, 1992a] *Encoding the ATMS in AGM Logic (Revised)* -- technical report predecessor
- [Nebel, 1991] *Belief Revision and Default Reasoning: Syntax-Based Approaches* -- finite belief revision
