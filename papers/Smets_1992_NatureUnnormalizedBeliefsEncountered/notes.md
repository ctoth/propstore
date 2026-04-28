---
title: "The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model"
authors: "Philippe Smets"
year: 1992
venue: "Uncertainty in Artificial Intelligence (UAI 1992), pp. 292-297"
doi_url: "10.1016/B978-1-4832-8287-9.50044-X"
arxiv_id: "1303.5430"
affiliation: "IRIDIA, Universite Libre de Bruxelles, Brussels, Belgium"
produced_by:
  agent: "claude-opus-4-7"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T07:27:46Z"
---
# The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model

## One-Sentence Summary
Smets justifies allowing positive basic belief mass on the empty set, m(empty) > 0, within the Transferable Belief Model (TBM), interpreting it as a quantified amount of conflict and / or as evidence that the actual world lies *outside* the assumed frame of discernment (open-world assumption), and shows this is needed for a coherent unnormalized Dempster combination, conditioning, and disjunctive aggregation.  *(p.292)*

## Problem Addressed
Classical Dempster-Shafer theory (Shafer 1976) imposes the normalization m(empty) = 0 by dividing through by 1 - K after Dempster combination, where K is the conflict mass. Smets argues this normalization step is *unjustified*: it discards information about how much the combined sources disagree, breaks otherwise-natural axiomatizations of conditioning, and presupposes a closed-world assumption (truth lies in the frame Y) that is often unwarranted. The paper analyses what m(empty) > 0 *means* and why the unnormalized form is the natural one in the TBM.  *(p.292, p.296)*

## Key Contributions
- Distinguishes the **credal level** (where beliefs are entertained, represented by belief functions) from the **pignistic level** (where decisions force a probability via the pignistic transformation BetP). m(empty) > 0 lives at the credal level only.  *(p.292, p.296)*
- Provides three justifications for m(empty) > 0:
  (1) it quantifies the **conflict** between combined evidence sources,
  (2) it represents **belief committed to "none of Y is the actual answer"** under an open-world assumption,
  (3) it preserves **homomorphism** of conditioning (and by extension disjunctive combination) with respect to refinement of the frame.  *(p.293-295)*
- Derives the unnormalized Dempster rule m1 (+) m2 (X) = sum over A intersect B = X of m1(A) m2(B), with positive mass on the empty set when sources disagree, and shows this is the unique form compatible with Dempster's multivalued-mapping construction without an arbitrary closing-up step.  *(p.293, p.294)*
- Shows that requiring **conditioning to commute with refinement** (a homomorphism axiom over the lattice of frames) forces the unnormalized form: the normalized rule fails this property.  *(p.294-295)*
- Argues the open-world reading lets TBM model "the actual world might lie outside Y" honestly, instead of coercing such evidence into the frame.  *(p.296)*
- Frames the underlying philosophical position as an **epistemic construct of the frame of discernment**: Y is built by the agent as a finite linguistic / conceptual partition, not given a priori, so "Y is exhaustive" is a closure assumption that need not hold.  *(p.296)*

## Study Design (empirical papers)
*Not applicable. Pure theory paper.*

## Methodology
Axiomatic / algebraic. Smets:
1. Defines belief, plausibility, and basic belief assignment (bba) on a finite frame Y, allowing m(empty) >= 0.
2. Defines unnormalized Dempster combination and unnormalized conditioning.
3. Imposes a homomorphism requirement on conditioning over the lattice of frames (refinement / coarsening) and derives constraints on the rule.
4. Solves the resulting functional equation (linear in 1-bel(.) and bel(.)) to show the unnormalized form is forced.
5. Reinterprets m(empty) at three levels (conflict, open-world residual, latent error) and connects to the pignistic transformation for decision-making.  *(p.293-295)*

## Key Equations / Statistical Models

Belief function (no longer normalized):
$$
\mathrm{bel}(A) = \sum_{\emptyset \neq X \subseteq A} m(X)
$$
Where: m is the basic belief assignment (bba) with m(X) >= 0 for all X subseteq Y and sum over X subseteq Y of m(X) = 1; **the empty set is excluded from the bel sum but allowed to carry positive mass** in the bba. Plausibility:
$$
\mathrm{pl}(A) = \sum_{X \cap A \neq \emptyset} m(X)
$$
*(p.292, eq. 1-2)*

Sum constraint (note: empty set IS counted here, distinguishing this from the normalized theory):
$$
\sum_{A \subseteq Y} m(A) = 1
$$
*(p.292)*

Identity used throughout (with m(empty) possibly > 0):
$$
\mathrm{bel}(A) + \mathrm{bel}(\bar A) + m(\emptyset) = 1 - q(A)
$$
where q(A) is mass strictly straddling A and complement(A). When m(empty) > 0 the additivity gap is widened beyond the usual q(A).  *(p.292)*

Unnormalized Dempster combination:
$$
m_{12}(X) = \sum_{A \cap B = X} m_1(A)\, m_2(B), \qquad X \subseteq Y
$$
With, in particular,
$$
m_{12}(\emptyset) = K = \sum_{A \cap B = \emptyset} m_1(A)\, m_2(B)
$$
This conflict mass K is **kept**, not divided out.  *(p.293)*

Unnormalized conditioning by C subseteq Y (Dempster conditioning, no renormalization):
$$
m(X \mid C) = \sum_{B \subseteq \bar C} m(X \cup B), \quad X \subseteq C; \qquad m(X \mid C) = 0,\ X \not\subseteq C
$$
Equivalently bel(A | C) = bel(A union complement(C)) - bel(complement(C)) without dividing by 1 - bel(complement(C)).  *(p.294)*

Homomorphism requirement for conditioning over a refinement rho: Y -> X (sketch from p.294):
$$
\mathrm{bel}_X(\rho(A)\mid \rho(C)) = (1 \otimes \mathrm{bel}_Y)(A \mid C) \quad \forall A, C
$$
i.e. the conditioning operator on the refined frame X must equal the lifted conditioning from Y; only the unnormalized rule satisfies this for all refinements.  *(p.294-295)*

Functional equation form Smets solves: bel(A | C) is forced to be linear in bel(.) and 1 - bel(.) over the relevant subsets, yielding the unnormalized Dempster conditioning above.  *(p.294-295)*

Pignistic transformation BetP (referenced for decision-making at the pignistic level):
$$
\mathrm{BetP}(\{y\}) = \sum_{A \subseteq Y,\ y \in A} \frac{m(A)}{|A|\,(1 - m(\emptyset))}
$$
The 1 - m(empty) factor in the denominator is the only place mass on the empty set is removed: *only when forced to commit to a decision*.  *(p.295-296)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Frame of discernment | Y | - | - | finite | 292 | finite set of mutually exclusive, jointly exhaustive (under closed-world) hypotheses |
| Basic belief mass | m(A) | - | - | [0, 1] | 292 | sum_{A subseteq Y} m(A) = 1; m(empty) >= 0 allowed |
| Conflict mass | K = m12(empty) | - | 0 | [0, 1] | 293 | mass on empty set after Dempster combination; quantifies disagreement |
| Belief | bel(A) | - | - | [0, 1] | 292 | sum over nonempty subsets of A |
| Plausibility | pl(A) | - | - | [0, 1] | 292 | pl(A) >= bel(A); pl(A) = 1 - bel(complement(A)) only in normalized case |
| Pignistic mass-on-empty correction | 1 - m(empty) | - | 1 | (0, 1] | 295 | BetP denominator factor, isolates closure assumption to decision time |

## Effect Sizes / Key Quantitative Results
*Not applicable; theoretical paper.*

## Methods & Implementation Details
- **Two-level architecture (credal vs pignistic)**: store unnormalized bbas (with m(empty) > 0) at the credal level; only apply BetP and the 1 - m(empty) renormalization at the pignistic level when a decision must be made. Conditioning, combination, and refinement happen at the credal level without normalization.  *(p.292, p.295-296)*
- **Implement Dempster combination without final divide-by-(1-K)**: keep K = m12(empty) as a first-class output of combination.  *(p.293)*
- **Implement conditioning unnormalized**: bel(A | C) = bel(A union complement(C)) - bel(complement(C)), with no division. The "compatibility with refinement" property is a *test* every implementation should satisfy.  *(p.294-295)*
- **Two open-world readings of m(empty) > 0**:
  - "outside-frame" reading: probability 1 - sum_{A subseteq Y} m(A) of "the answer is none of Y" is shifted onto m(empty), making the bba a normalized object on Y union {outside}. (p.295)
  - "conflict residue" reading: m(empty) is interpreted as quantitative inconsistency to be reported, not silenced. (p.293)
- **Homomorphism / refinement axiom** as design constraint: conditioning rule on refined frame must be the lifting of conditioning on the coarse frame, for every refinement rho. Smets proves only the unnormalized rule passes for all rho.  *(p.294-295)*
- **Three-level hierarchy** (Smets 1990, referenced p.295): Credal level (belief functions) -> pignistic level (BetP) -> betting / decision level. m(empty) > 0 is invisible at the betting level; its information is preserved at credal level and integrated into BetP at pignistic level.

## Figures of Interest
- No figures; paper is purely textual / algebraic. Section structure: 1. Introduction (p.292), 2. The frame of discernment (p.293), 3. Conditioning in the TBM (p.293-295), 4. Updating beliefs (p.295), 5. The epistemic construct of the frame of discernment (p.296), 6. Conclusions (p.296), Acknowledgments + Bibliography (p.297).

## Results Summary
- Unnormalized Dempster combination is the unique combination rule satisfying Dempster's multivalued mapping construction without the ad-hoc normalization step.  *(p.293)*
- Unnormalized conditioning is the unique conditioning rule that commutes with refinement of the frame of discernment.  *(p.294-295)*
- Both results support, but are independent of, the open-world interpretation of m(empty) > 0.  *(p.295-296)*
- The pignistic transformation absorbs the 1 - m(empty) factor at decision time, so closed-world commitment is *deferred* rather than *built in*.  *(p.295-296)*

## Limitations
- Smets explicitly notes the analysis assumes a *finite* frame Y. Infinite frames are not treated.  *(p.292, p.293)*
- The paper does not give an axiomatic uniqueness result for the disjunctive rule of combination — only for unnormalized Dempster (conjunctive) combination and conditioning. Disjunctive aggregation is left to a companion paper (Smets 1993, "Belief functions: the disjunctive rule of combination and the generalized Bayesian theorem").  *(p.295, footnote)*
- The "pignistic" decision layer is asserted as the right place to recover a probability but its full justification is in Smets 1990 (referenced), not derived here.  *(p.295-296)*
- Smets acknowledges his epistemic construct of the frame of discernment is contested and gives only a brief defence.  *(p.296)*

## Arguments Against Prior Work
- **Against Shafer's normalized Dempster's rule**: the normalization step (dividing by 1 - K) discards the magnitude of conflict K, which is informative. The unnormalized form preserves K and exposes it as m(empty).  *(p.293, p.296)*
- **Against the closed-world assumption built into classical DS**: forcing sum_{A subseteq Y} m(A) = 1 with m(empty) = 0 implicitly asserts that the truth lies in Y; this is an assumption, not a theorem. Smets argues it should be made explicit and applied only when decisions are required.  *(p.296)*
- **Against probability theory as an immediate framework for belief**: probabilities at the credal level conflate epistemic state with betting commitment; Smets's two-level architecture separates them.  *(p.292, p.296)*
- **Against ad-hoc patches that re-attribute conflict mass to non-empty sets** (e.g. Yager's combination rule that pushes K onto Y; Dubois-Prade's disjunctive rule): such patches "pretend the conflict didn't happen" by relabeling, which discards the information that the sources actually disagreed.  *(p.295-296)*

## Design Rationale
- **Why m(empty) > 0 is allowed**: doing so is the only way to keep Dempster combination and conditioning compatible with refinement of the frame, and the only way to honestly represent inter-source conflict and out-of-frame evidence.  *(p.293-295)*
- **Why two levels (credal vs pignistic)**: storing unnormalized beliefs preserves information and supports composition; renormalizing only at decision time confines the closed-world assumption to where it is operationally needed.  *(p.295-296)*
- **Why the homomorphism / refinement axiom**: a belief representation that does not commute with refinement is not a representation of belief about the *real* underlying world; it is an artifact of the frame the agent happens to have written down. Forcing commutativity rules out arbitrary normalization.  *(p.294-295)*
- **Why the frame is an epistemic construct**: Y is a linguistic / conceptual carving of possibility space, chosen by the agent. Treating it as exhaustive a priori is a category error; allowing m(empty) > 0 is the formal admission that the carving may be incomplete.  *(p.296)*

## Testable Properties
- **Conservation of mass**: sum_{A subseteq Y} m(A) = 1, *including* m(empty).  *(p.292)*
- **Monotonicity**: bel(A) <= bel(B) when A subseteq B; pl is the dual.  *(p.292)*
- **Conflict preservation under combination**: m12(empty) = sum_{A intersect B = empty} m1(A) m2(B); never zero unless sources are jointly consistent.  *(p.293)*
- **Refinement homomorphism**: for any refinement rho: Y -> X, bel_X(rho(A) | rho(C)) = (lift of bel_Y(A | C)). Tests must verify this on at least one nontrivial refinement.  *(p.294-295)*
- **Pignistic invariance**: BetP({y}) sums to 1 over y in Y after dividing by 1 - m(empty). Without that factor, BetP under-sums.  *(p.295-296)*
- **Idempotence under no information**: combining a vacuous bba (m(Y) = 1) with any other m yields m unchanged; m(empty) stays 0.  *(p.293, implicit)*
- **m(empty) monotonicity under combination**: combining more conflicting sources can only *increase* (or hold) m12(empty); never decrease.  *(p.293, implicit from formula)*

## Relevance to Project
This is foundational for propstore's argumentation / probabilistic-subjective layer. The two-level architecture (credal vs pignistic) maps directly onto propstore's "lazy until rendering" principle: store unnormalized belief / opinion structures with full conflict information at the source-of-truth layer, apply normalization or commitment only at the render layer when a render policy demands a probabilistic output. m(empty) > 0 is the formal carrier of "honest ignorance" at the credal level — directly aligned with the project design principle that vacuous opinions / non-commitment must survive into storage. Smets's homomorphism-under-refinement requirement is the analogue, in TBM space, of propstore's requirement that operations on the semantic layer be stable under coarsening / refinement of concept frames. Subjective Logic (Josang) inherits a normalized-with-uncertainty stance more analogous to Smets's pignistic level; this paper supplies the deeper credal-level justification for why uncertainty must not be silently absorbed by combination. The "open-world reading" maps to the propstore stance that the concept frame is an epistemic construct authored by users / lemon entries, never assumed exhaustive.

## Open Questions
- [ ] Does propstore's ATMS / belief-function carrier actually preserve m(empty) through combination? (Implementation check.)
- [ ] How does the homomorphism-under-refinement requirement interact with concept-merge proposals at the heuristic layer, where the "frame" is itself in flux?
- [ ] The disjunctive rule (Smets 1993) is treated separately and is needed for source-conjunction-vs-source-disjunction modeling — confirm propstore has both available.
- [ ] How should typed provenance (`measured`/`calibrated`/`stated`/`defaulted`/`vacuous`) relate to m(empty) magnitudes when transposing to opinion algebra?

## Related Work Worth Reading
- Shafer 1976 — *A Mathematical Theory of Evidence* — already in collection. Defines normalized Dempster-Shafer that this paper revises.
- Smets 1990 — *The combination of evidence in the Transferable Belief Model* — already in collection. Defines pignistic transformation; Smets 1992 cites it for the credal/pignistic split.
- Smets 1991 — *The Transferable Belief Model and other interpretations of Dempster-Shafer's model* — already in collection. Sets up TBM interpretation of belief functions.
- Smets 1993 — *Belief functions: the disjunctive rule of combination and the generalized Bayesian theorem* — already in collection. The disjunctive companion to this paper.
- Smets and Kennes 1994 — *The Transferable Belief Model* — already in collection. The full journal exposition.
- Klawonn and Smets 1992 — *The dynamic of belief in the transferable belief model and specialization-generalization matrices* — UAI 1992. Cited p.295 for the algebraic conditioning derivation.
- Yager 1987 — alternative normalization; criticized in this paper.
- Dubois and Prade 1986 — disjunctive rule; criticized in this paper.
- Zadeh 1986 — critique of Dempster's rule (the "two doctors" example); cited p.296.
- Voorbraak 1991 — alternative interpretation of belief functions; cited p.297.

## Collection Cross-References

### Already in Collection
- [A Mathematical Theory of Evidence](../Shafer_1976_MathematicalTheoryEvidence/notes.md) — the canonical normalized Dempster-Shafer formulation; Smets 1992 explicitly rejects its normalization step (`/(1-K)`) and reinterprets m(empty) > 0 as conflict / open-world residue rather than something to be eliminated.
- [The combination of evidence in the Transferable Belief Model](../Smets_1990_CombinationEvidenceTransferableBelief/notes.md) — defines the pignistic transformation BetP that Smets 1992 invokes (with the `1 - m(empty)` factor) at the decision level. The credal/pignistic split this paper depends on is established in 1990a.
- [The Transferable Belief Model and other interpretations of Dempster-Shafer's model](../Smets_1991_TransferableBeliefModel/notes.md) — sets up the TBM as a non-probabilistic two-level interpretation of belief functions, the framework Smets 1992 axiomatizes for the unnormalized case.
- [Belief functions: the disjunctive rule of combination and the generalized Bayesian theorem](../Smets_1993_BeliefFunctionsDisjunctiveRule/notes.md) — companion paper that gives the disjunctive rule explicitly left out of Smets 1992 (which proves uniqueness only for unnormalized conjunctive combination and conditioning).
- [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — the IRIDIA-90-14 technical report cited here (Smets and Kennes 1990) reappears as the 1994 AI journal paper; it is the full exposition of the two-level architecture.

### New Leads (Not Yet in Collection)
- Klawonn, F. and Smets, Ph. (1992) — "The dynamic of belief in the transferable belief model and specialization-generalization matrices" — same UAI-92 volume, supplies the algebraic specialization-generalization machinery behind the conditioning result.
- Walley, P. (1991) — *Statistical reasoning with imprecise probabilities* — alternative epistemic-uncertainty framework (lower/upper previsions). Walley 1996 multinomial paper is in collection but is not a substitute for the 1991 monograph.
- Gardenfors, P. (1988) — *Knowledge in flux. Modelling the dynamics of epistemic states* — the AGM belief revision framework canonical text; relevant to propstore's belief-set / iteration layer.
- Levi, I. (1980) — *The enterprise of knowledge* — credal-states philosophy; underpins Smets's defence of the credal/pignistic split.
- Yager, R. (1987) — alternative DS combination rule that re-attributes K to Y; explicit foil here.
- Dubois, D. and Prade, H. (1986) — early disjunctive rule of combination; another foil.
- Zadeh, L. (1984) — book review and "two doctors" critique of Dempster's rule.
- Voorbraak, F. (1991) — alternative interpretation of belief functions.
- Aczel, J. (1966) — *Lectures on functional equations* — used to solve the homomorphism functional equation in Section 3.
- Ruspini, E.H. (1986) — logical foundations of evidential reasoning; a logic-based reading of belief functions.
- Laskey, K. and Lehner, P.E. (1989) — assumptions, beliefs, probabilities; ATMS-flavoured belief functions.
- Nguyen, T.H. and Smets, Ph. (1991) — dynamics of cautious belief and conditional objects.
- Carnap, R. (1950, 1962) — logical foundations of probability; cited for the philosophical background on epistemic frames.

### Supersedes or Recontextualizes
- Smets 1992 explicitly recontextualizes the normalized Dempster's rule of [Shafer 1976](../Shafer_1976_MathematicalTheoryEvidence/notes.md): it argues the normalization step is not a definitional necessity but a closed-world commitment that should be deferred to decision time.

### Conceptual Links (not citation-based)
- [Subjective Logic](../Josang_2016_SubjectiveLogic/notes.md) — Subjective Logic's normalized opinion (b + d + u = 1) is directly comparable to Smets's pignistic-level commitment; Subjective Logic's "uncertainty mass u" plays a role analogous to the vacuous content but does *not* preserve m(empty)-style conflict information across fusion. The two frameworks can be read as making different choices about *where* to absorb out-of-frame information.
- [A Logic for Uncertain Probabilities](../Josang_2001_LogicUncertainProbabilities/notes.md) — first Josang formalization of opinions; the (b, d, u, a) carrier is analogous to a Smets bba simplified to a binary frame, but Josang's vacuous opinion (u = 1) and Smets's m(Y) = 1 vacuous bba carry different information about open-world assumptions.
- [Inferences from Multinomial Data: Learning About a Bag of Marbles](../Walley_1996_InferencesMultinomialDataLearning/notes.md) — Walley's IDM is another framework that explicitly preserves epistemic-state uncertainty under conditioning; same motivation as Smets's "don't normalize away the conflict", different formal vehicle (lower/upper prevision vs. unnormalized bba).
- [Decision-Making with Belief Functions: A Review](../Denoeux_2018_Decision-MakingBeliefFunctionsReview/notes.md) — Denoeux reviews TBM-style decision-making at the pignistic level with explicit handling of m(empty); a direct downstream consumer of Smets 1992's two-level architecture.
- [A Cumulative Belief Logic for Web Reputation Systems / Cumulative Averaging Fusion](../Josang_2010_CumulativeAveragingFusionBeliefs/notes.md) — Josang's fusion operators implicitly reject the Dempster-style conflict-discarding step Smets criticizes here; conceptual convergence on "fusion should not silently drop disagreement".
- [Subjective Logic Meta-Analysis](../Margoni_2024_SubjectiveLogicMetaAnalysis/notes.md) — empirical comparison of subjective-logic-style fusion to alternatives; relevant for evaluating how propstore's adopted fusion behaves under conflict, the very issue Smets 1992 isolates.
- [Named Graphs, Provenance and Trust](../Carroll_2005_NamedGraphsProvenanceTrust/notes.md) — propstore-side: the typed-provenance carrier (named graphs) is the storage substrate that lets m(empty)-bearing bbas survive into the credal layer with their conflict context attached; conceptual convergence with Smets's "don't lose information at storage time" position.
- [Circumscription — A Form of Non-Monotonic Reasoning](../McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/notes.md) — McCarthy's frame-of-discernment-as-construct concern (closed-world assumption made explicit, and overridable) parallels Smets's "the frame Y is an epistemic construct, not given" position in Section 5.
- [Revisions of Knowledge Systems Using Epistemic Entrenchment](../Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md) — Gardenfors's epistemic-entrenchment framework is the AGM analogue of Smets's "store credal state, defer commitment"; both insist epistemic dynamics belong on a layer above propositional commitment.

### Cited By (in Collection)
- [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — cites Smets 1992 as the source of the unnormalized-Dempster justification and the homomorphism-under-refinement argument.
- [Quantifying Beliefs Through Belief Functions](../Smets_1993_QuantifyingBeliefsBeliefFunctions/notes.md) — cites Smets 1992 for the open-world reading of m(empty) > 0.
