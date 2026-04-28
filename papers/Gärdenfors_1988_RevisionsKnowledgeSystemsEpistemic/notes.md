---
title: "Revisions of Knowledge Systems Using Epistemic Entrenchment"
authors: "Peter Gärdenfors, David Makinson"
year: 1988
venue: "Proceedings of the 2nd Conference on Theoretical Aspects of Reasoning About Knowledge (TARK)"
pages: "83-95"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-28T23:20:39Z"
---
# Revisions of Knowledge Systems Using Epistemic Entrenchment

## One-Sentence Summary

Defines epistemic entrenchment as a total preorder over sentences in a knowledge set that determines retraction priority during belief revision and contraction, proves a representation theorem showing entrenchment orderings and AGM-rational contraction/revision functions are interchangeable, and shows the information required to specify the ordering is linear in the number of atomic facts.

## Problem Addressed

How to revise a knowledge system when new information contradicts existing beliefs, and the related problem of contraction (removing information). The challenge is determining *which* beliefs to retract — this requires a principled ordering of beliefs by their epistemic importance. *(p.83)*

## Key Contributions

- Two sets of rationality postulates: 8 for revision (K\*1-K\*8), 8 for contraction (K-1 to K-8), shown equivalent to prior work by AGM *(p.86-87)*
- Five postulates for epistemic entrenchment orderings (EE1-EE5) *(p.89)*
- Two bridging conditions (C≤) and (C-) connecting entrenchment to contraction *(p.89-90)*
- Representation theorem (Theorems 3-6): a revision/contraction method satisfies the rationality postulates if and only if there exists an epistemic entrenchment ordering satisfying the appropriate constraints *(p.90)*
- Computational complexity result: the information needed to determine the entrenchment ordering is linear in the number of atomic facts of the knowledge system *(p.90)*
- Theorem 7: for a finite Boolean knowledge set with 2^n elements, there are exactly n! distinct total orderings satisfying EE1-EE5 *(p.94)*

## Methodology

The paper proceeds axiomatically. It defines knowledge systems as logically closed sets, introduces revision and contraction functions via rationality postulates, then defines epistemic entrenchment as an ordering relation on sentences. Representation theorems connect these three concepts: entrenchment orderings uniquely determine contraction functions and vice versa.

## Formal Framework

### Knowledge Systems

A knowledge set K is a set of sentences in some language L which is closed under logical consequence (if K logically entails B, then B ∈ K). The underlying logic includes classical propositional logic and is compact. *(p.84)*

Key notation:
- K_1 = the set of logical truths (smallest knowledge set) *(p.84)*
- K^+A = expansion of K by A (add A and close under logic) = {B : K ∪ {A} ⊢ B} *(p.85)*
- Cn(X) = logical closure of set X *(p.84)*

### Revision Function K\*A

A revision function \* takes a knowledge set K and a sentence A and returns a revised knowledge set K\*A. *(p.86)*

### Contraction Function K⁻A

A contraction function - takes a knowledge set K and a sentence A and returns a contracted knowledge set K⁻A (K with A removed, preserving consistency). *(p.85)*

### Three Operations on Knowledge Sets *(p.85)*

1. **Expansion** K^+A: Add A and close. Result: K^+A = {B : K ∪ {A} ⊢ B}
2. **Revision** K\*A: Add A while maintaining consistency. Defined via contraction: K\*A = (K⁻¬A)^+A (Levi identity)
3. **Contraction** K⁻A: Remove A while preserving as much as possible. Defined via revision: K⁻A = K ∩ K\*¬A (Harper identity)

## Key Equations / Statistical Models

### Levi Identity (Def \*)

$$
K*A = (K^{-}\neg A)^{+}A
$$

Where: K\*A is the revision of K by A, K⁻¬A is the contraction of K by ¬A, and (...)^+A is the expansion by A.
*(p.87)*

### Harper Identity (Def -)

$$
K^{-}A = K \cap K*\neg A
$$

Where: K⁻A is the contraction of K by A, K\*¬A is the revision of K by ¬A.
*(p.87)*

### Condition (C≤): Entrenchment from Contraction

$$
A \leq B \text{ if and only if } A \notin K^{-}(A \wedge B) \text{ or } A \wedge B \in K_1
$$

Where: ≤ is the epistemic entrenchment ordering, K⁻(A&B) is the contraction of K by A&B, K_1 is the set of logical truths.
*(p.89)*

Intuition: When forced to give up A&B, if A is retracted (not B), then A is at most as entrenched as B.

### Condition (C-): Contraction from Entrenchment

$$
B \in K^{-}A \text{ if and only if } B \in K \text{ and either } A < A \vee B \text{ or } \vdash A
$$

Where: A < B means A ≤ B and not B ≤ A (strict entrenchment).
*(p.89)*

Intuition: B survives contraction by A if and only if B is in K and giving up A∨B would be a bigger loss than giving up A alone (i.e., B contributes something beyond A).

## Postulates

### Postulates for Revisions (K\*1 - K\*8) *(p.86)*

| ID | Statement | Name |
|----|-----------|------|
| K\*1 | K\*A is a knowledge set | closure |
| K\*2 | A ∈ K\*A | success |
| K\*3 | K\*A ⊆ K^+A | inclusion |
| K\*4 | If ¬A ∉ K, then K^+A ⊆ K\*A | preservation |
| K\*5 | K\*A = K_1 only if ⊢ ¬A | consistency |
| K\*6 | If ⊢ A ↔ B, then K\*A = K\*B | extensionality |
| K\*7 | K\*A&B ⊆ (K\*A)^+B | conjunction 1 |
| K\*8 | If ¬B ∉ K\*A, then (K\*A)^+B ⊆ K\*A&B | conjunction 2 |

Basic postulates: K\*1 - K\*6. Supplementary: K\*7, K\*8. *(p.86-87)*

The conjunction of (K\*7) and (K\*8) is equivalent to the vacuity principle:

$$
K*A \vee B = K*A \text{ or } K*A \vee B = K*B \text{ or } K*A \vee B = K*A \cap K*B
$$

*(p.87)*

### Postulates for Contractions (K-1 to K-8) *(p.87)*

| ID | Statement | Name |
|----|-----------|------|
| K-1 | K⁻A is a knowledge set | closure |
| K-2 | K⁻A ⊆ K | inclusion |
| K-3 | If A ∉ K, then K⁻A = K | vacuity |
| K-4 | If not ⊢ A, then A ∉ K⁻A | success |
| K-5 | K ⊆ (K⁻A)^+A | recovery |
| K-6 | If ⊢ A ↔ B, then K⁻A = K⁻B | extensionality |
| K-7 | K⁻A ∩ K⁻B ⊆ K⁻A&B | conjunction 1 |
| K-8 | If A ∉ K⁻A&B, then K⁻A&B ⊆ K⁻A | conjunction 2 |

Basic postulates: K-1 to K-6. Supplementary: K-7, K-8. *(p.87)*

The conjunction of (K-7) and (K-8) is equivalent to:

$$
\text{Either } K^{-}A \wedge B = K^{-}A \text{ or } K^{-}A \wedge B = K^{-}B \text{ or } K^{-}A \wedge B = K^{-}A \cap K^{-}B
$$

*(p.87)*

### Postulates for Epistemic Entrenchment (EE1 - EE5) *(p.89)*

| ID | Statement | Name |
|----|-----------|------|
| EE1 | If A ≤ B and B ≤ C, then A ≤ C | transitivity |
| EE2 | If A ⊢ B, then A ≤ B | dominance |
| EE3 | For any A and B, A ≤ A&B or B ≤ A&B | conjunctiveness |
| EE4 | When K ≠ K_1, A ∉ K iff A ≤ B for all B | minimality |
| EE5 | If B ≤ A for all B, then ⊢ A | maximality |

Justifications:
- **EE2 (dominance)**: If A logically entails B, retracting A is a smaller change than retracting B, so A should be retracted first *(p.89)*
- **EE3 (conjunctiveness)**: To retract A&B, you must give up A or B (or both); informational loss is equal either way *(p.89)*
- **EE4 (minimality)**: Sentences not in K have minimal entrenchment *(p.89)*
- **EE5 (maximality)**: Only logically valid sentences can be maximally entrenched *(p.89)*

## Theorems

### Theorem 1: Revision-Contraction Correspondence *(p.87)*

If a contraction function satisfies (K-1) to (K-6), then the revision function defined by (Def \*) satisfies (K\*1) to (K\*6). Furthermore, if (K-7) is satisfied, (K\*7) will be satisfied; and if (K-8) is satisfied, (K\*8) will be satisfied.

### Theorem 2: Contraction-Revision Correspondence *(p.87)*

If a revision function satisfies (K\*1) to (K\*6), then the contraction function defined by (Def -) satisfies (K-1) to (K-6). Furthermore, if (K\*7) is satisfied, (K-7) will be satisfied; and if (K\*8) is satisfied, (K-8) will be satisfied.

Together, Theorems 1 and 2 show revision and contraction are interdefinable via the Levi and Harper identities.

### Lemma 3: Properties of Entrenchment *(p.89)*

If the ordering ≤ satisfies (EE1) - (EE3), then:
- (i) A ≤ B or B ≤ A (connectivity/totality)
- (ii) If B&C ≤ A, then B ≤ A or C ≤ A
- (iii) A < B iff A&B < B (strict ordering and conjunction)
- (iv) If C ≤ A and C ≤ B, then C ≤ A&B
- (v) If A ≤ B, then A ≤ A&B

Note: By (i), A < B may be more simply defined as not B ≤ A. *(p.89)*

### Theorem 3: Entrenchment Determines Contraction *(p.90)*

If an ordering ≤ satisfies (EE1) - (EE5), then the contraction function defined by (C-) satisfies (K-1) - (K-6). With the aid of condition (C≤), the ordering will have the desired properties.

### Theorem 4: Contraction Determines Entrenchment *(p.90)*

If a contraction function satisfies (K-1) - (K-6), then the ordering ≤ defined by (C≤) satisfies (EE1) - (EE5).

### Theorem 5: Interchangeability *(p.90)*

Theorems 4 and 5 imply that conditions (C≤) and (C-) are interchangeable in the following sense: Let C be the class of contraction functions satisfying (K-1) - (K-8) and E the class of orderings satisfying (EE1) - (EE5). Let C→ be a map from E to C such that C→(≤) is the contraction function determined by (C-) for a given ordering ≤, and let E→ be a map from C to E such that E→(⁻) = ≤ is the ordering determined by (C≤) for a given contraction function ⁻. Then there is an immediate consequence: C→ and E→ are inverses of each other.

### Theorem 6: Linearity of Information *(p.90)*

The amount of information needed to uniquely determine the required ordering is linear in the number of atomic facts of the knowledge system. This follows from condition (C≤): one needs only specify the ordering of n elements (where n is the number of atomic propositions), and the ordering over all 2^n elements of K follows by the entrenchment postulates.

### Theorem 7: Counting Orderings *(p.94)*

Let K be a finite knowledge set, and let T be the set of all top elements of K (i.e., all dual atoms of K). Then any two orderings ≤ and ≤' each satisfying (EE1) - (EE5) that agree on all pairs of elements of T are identical.

**Proof**: If ≤ and ≤' agree on top elements and both satisfy EE1-EE5, then they agree everywhere. This means: for a Boolean knowledge set with 2^n elements (n atoms), there are exactly n! different total orderings satisfying EE1-EE5 (since the ordering is completely determined by how it orders the n dual atoms, which are the co-atoms/top elements, and there are n! permutations). *(p.94)*

## Methods & Implementation Details

- Knowledge sets are modeled as logically closed sets of sentences in a finitary language with classical propositional logic *(p.84)*
- The framework assumes compactness of the underlying logic *(p.84)*
- Epistemic entrenchment is a total preorder (reflexive, transitive, connected) over sentences *(p.89, Lemma 3(i))*
- The constructive direction is (C-): given an entrenchment ordering, define the contraction function; then use the Levi identity to get the revision function *(p.89-90)*
- The analytic direction is (C≤): given a contraction function satisfying the postulates, extract the entrenchment ordering *(p.89)*
- Proofs of Theorems 1 and 2 are provided in the Appendix *(p.91-94)*
- The proof of Theorem 7 uses Boolean algebra structure and the fact that top elements (dual atoms) determine the entire ordering *(p.94-95)*

## Figures of Interest

None (purely formal/axiomatic paper).

## Results Summary

The central result is a representation theorem: AGM-rational belief revision/contraction methods are in exact correspondence with epistemic entrenchment orderings satisfying EE1-EE5. The ordering can be read off from the contraction function (via C≤) or used to construct the contraction function (via C-). The information needed to specify the ordering is linear in the number of propositional atoms, and the number of possible orderings is n! for n atoms. *(p.90, 94)*

## Limitations

- Framework restricted to finitary classical propositional logic with compactness *(p.84)*
- Does not address how to initially construct or learn the entrenchment ordering from empirical data — the ordering is assumed given or derived from a contraction function *(p.88)*
- Does not handle first-order logic or non-monotonic extensions
- The paper acknowledges this is foundational: "we must first find further information about the epistemic status of the elements of a knowledge state in order to solve the uniqueness problem" *(p.88)*
- The equivalence class structure (Theorem 7) applies only to finite Boolean algebras
- Does not address computational aspects of actually performing contractions on large knowledge bases

## Arguments Against Prior Work

- Against naive database update approaches (Fagin, Ullman, Vardi 1983): merely deleting a tuple from a relational database is inadequate because derived facts must also be handled — the database is not a flat collection but a system with logical interdependencies *(p.86)*
- The "simpleminded approach" of replacing deleted tuples with null values is shown to be insufficient *(p.86)*
- Prior work on partial meet contraction (AGM 1985) and safe contraction (Alchourrón & Makinson 1985) did not provide a computationally tractable way to determine retraction priority *(p.88)*

## Design Rationale

- **Why a total preorder?** Lemma 3(i) shows that EE1-EE3 already force connectivity — any two sentences are comparable. This is not an assumption but a consequence. *(p.89)*
- **Why entrenchment rather than direct specification of contraction?** The entrenchment ordering provides "a convenient way to update knowledge sets" even though "they do not present any axiomatisation of this notion" at this point *(p.88)*
- **Why the Levi identity for revision?** It decomposes revision into contraction + expansion, making contraction the more fundamental operation. Theorem 1 shows this preserves all rationality postulates. *(p.87)*
- **Why (C-) over (C≤)?** (C-) is the constructive direction: from entrenchment to contraction. (C≤) is the analytic direction: from contraction to entrenchment. Together they form the representation theorem. *(p.89-90)*

## Testable Properties

- **EE1-EE5 well-formedness**: Any proposed entrenchment ordering must satisfy all five postulates *(p.89)*
- **Connectivity**: For any A,B in K, either A ≤ B or B ≤ A *(p.89)*
- **Dominance preservation**: If A logically entails B, then A ≤ B *(p.89)*
- **Conjunctiveness**: For any A,B, either A ≤ A&B or B ≤ A&B *(p.89)*
- **Contraction-entrenchment roundtrip**: Applying (C≤) then (C-) (or vice versa) should return the original function/ordering *(p.90)*
- **Levi-Harper roundtrip**: Defining revision from contraction (Def \*) then contraction from that revision (Def -) should return the original contraction function *(p.87)*
- **Linear information**: For n atomic propositions, the entrenchment ordering over all 2^n sentences is determined by the ordering of n elements *(p.90)*
- **Factorial count**: For n atoms, exactly n! valid entrenchment orderings exist *(p.94)*

## Relevance to Project

This paper provides the formal foundation for constructing epistemic entrenchment orderings from justification structure — which is the formal inverse of the fragility concept in propstore. The entrenchment ordering determines which beliefs to retract first under pressure, directly corresponding to how fragile a belief is. Key connections:

1. **ATMS justification structure → entrenchment**: The ATMS tracks which assumptions support which beliefs. Beliefs supported by fewer/weaker assumptions should have lower entrenchment (higher fragility).
2. **Condition (C≤)** provides a concrete algorithm: observe what gets retracted when A&B is contracted; if A disappears, A ≤ B.
3. **Condition (C-)** provides the constructive direction: given an entrenchment ordering (which fragility analysis produces), define the contraction function.
4. **Dixon 1993** (already in CLAUDE.md as aspirational) connects ATMS context switching to AGM operations — this paper provides the other half: the formal structure of those AGM operations.
5. **Theorem 7**: The factorial count on orderings means the space of valid entrenchment orderings is manageable (n! for n atoms), which bounds the computational complexity of fragility scoring.

## Open Questions

- [ ] How to map ATMS assumption support counts to entrenchment ordering satisfying EE1-EE5
- [ ] Whether the existing sidecar's claim/stance structure can be viewed as defining an implicit contraction function
- [ ] How this connects to Jøsang's uncertainty parameter u — high u (ignorance) should correlate with low entrenchment
- [ ] Whether the bipolar argumentation (Cayrol 2005) support/defeat structure induces an entrenchment ordering
- [ ] Relationship between Dung AF grounded extension membership and entrenchment level

## Related Work Worth Reading

- Alchourrón, Gärdenfors, and Makinson (1985) "On the logic of theory change: Partial meet contraction" — the foundational AGM paper that this work builds on *(already in collection)*
- Gärdenfors (1988) *Knowledge in Flux* — book-length treatment of epistemic entrenchment, more detailed than this conference paper *(p.95)*
- Gärdenfors (1984) "Epistemic importance and minimal changes of belief" — earlier work on the concept *(p.88)*
- Makinson (1987) "On the status of the postulate of recovery in the logic of theory change" — discusses the controversial recovery postulate K-5 *(p.87)*
- Foo and Rao (1986) "DYNABELS" — connects to labelled systems / ATMS-style approaches *(p.95)*
- Martins and Shapiro (1986) "Theoretical foundations for belief revisions" — alternative approach presented at TARK 1 *(p.95)*
- Grove (1986) "Two modellings for theory change" — alternative formal models *(p.95)*

## Collection Cross-References

### Already in Collection
- [[Alchourron_1985_TheoryChange]] — directly cited as the foundational AGM paper; this paper builds the entrenchment representation on top of AGM's partial meet contraction
- [[Martins_1988_BeliefRevision]] — cited as Martins & Shapiro 1986 (TARK 1); alternative belief revision foundations via SNePS/reason maintenance
- [[Ginsberg_1985_Counterfactuals]] — cited for counterfactual reasoning connections to belief revision
- [[Reiter_1980_DefaultReasoning]] — cited indirectly via Reiter 1984 database reconstruction; default reasoning connects to non-monotonic extensions

### Cited By (in Collection)
- [[Dixon_1993_ATMSandAGM]] — directly builds on this paper; shows ATMS context switching implements AGM operations, using epistemic entrenchment from this paper
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — cites this paper's entrenchment framework in context of preferred subtheories
- [[Alchourron_1985_TheoryChange]] — mutual citation; this paper cites AGM 1985, and AGM framework references later entrenchment work
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — references epistemic entrenchment in context of ASPIC+ with incomplete information

### New Leads (Not Yet in Collection)
- Gärdenfors (1988) *Knowledge in Flux* — book-length treatment, more detailed proofs and additional entrenchment results
- Gärdenfors (1984) "Epistemic importance and minimal changes of belief" — earlier work defining the entrenchment concept
- Makinson (1987) "On the status of the postulate of recovery" — analysis of the controversial K-5 postulate
- Foo and Rao (1986) "DYNABELS" — label-based belief revision, potentially connecting to ATMS justification tracking

### Conceptual Links (not citation-based)
**Belief revision and justification tracking:**
- [[Dixon_1993_ATMSandAGM]] — Strong: the direct bridge paper; shows ATMS labels implement entrenchment orderings, making this paper's formal results computationally operational via de Kleer's ATMS
- [[deKleer_1986_AssumptionBasedTMS]] — Strong: ATMS justification structure provides the computational mechanism for entrenchment; assumption labels are the data structure from which entrenchment orderings can be extracted
- [[Martins_1983_MultipleBeliefSpaces]] — Moderate: multiple belief spaces in SNePS correspond to different contraction/revision outcomes

**Argumentation and defeat:**
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — Strong: ASPIC+ preference orderings over rules/premises serve the same role as entrenchment orderings — determining which arguments survive conflict. The preference-based defeat in ASPIC+ (Defs 19-21) is the argumentation-theoretic operationalization of epistemic entrenchment
- [[Dung_1995_AcceptabilityArguments]] — Moderate: grounded extension membership correlates with entrenchment level; beliefs in the grounded extension are maximally entrenched (hardest to retract)
- [[Pollock_1987_DefeasibleReasoning]] — Moderate: Pollock's degrees of justification correspond to entrenchment degrees; ultimately undefeated arguments have maximal entrenchment

**Dynamics and change in argumentation:**
- [[Cayrol_2014_ChangeAbstractArgumentationFrameworks]] — Moderate: change operations on AFs (adding/removing arguments/attacks) correspond to revision/contraction operations on knowledge sets
- [[Doutre_2018_ConstraintsChangesSurveyAbstract]] — Moderate: surveys AF dynamics through the lens of belief revision postulates, directly applying AGM concepts from this paper
- [[Rotstein_2008_ArgumentTheoryChangeRevision]] — Strong: explicitly connects argument theory change to AGM revision, operationalizing this paper's postulates in argumentation frameworks

---

**See also (citation - Smets uses Gardenfors here):** [Quantifying Beliefs by Belief Functions: An Axiomatic Justification](../Smets_1993_QuantifyingBeliefsBeliefFunctions/notes.md) - Smets imports the homomorphism and preservation properties from Gardenfors (1988) and uses their *joint* unsatisfiability in probability theory to reject probability as a credal-level belief representation. Only unnormalized Dempster's rule of conditioning satisfies both. This is one of the strongest applications of Gardenfors's revision properties outside of AGM revision proper.
