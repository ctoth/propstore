# Alternatives to Naive Float-Probability Mappings

Research into representing belief strength, confidence, and uncertainty in
knowledge/argumentation systems. Context: propstore holds competing claims with
provenance, uses Dung AF / ASPIC+ argumentation, has an ATMS, and currently maps
NLI and embedding similarity to bare floats.

---

## 1. Dempster-Shafer Theory / Belief Functions

**Core idea:** Instead of a single probability P(A), assign two measures: belief
Bel(A) (evidence directly supporting A) and plausibility Pl(A) (evidence not
contradicting A). The gap [Bel(A), Pl(A)] explicitly represents ignorance. Mass
is assigned to subsets of the frame of discernment, not just singletons --
meaning "I don't know which of {A, B}" is a first-class citizen.

### Key papers

**Shafer, G. (1976). A Mathematical Theory of Evidence.**
Princeton University Press.
https://glennshafer.com/books/amte.html

The foundational monograph. Introduces belief functions, plausibility, and
Dempster's rule of combination. Directly relevant because it provides a
principled way to represent "I have evidence for A but also substantial
ignorance" -- exactly the situation when an NLI model returns a moderate
entailment score. The interval [Bel, Pl] is strictly more expressive than a
single float.

**Denoeux, T. (2019). Decision-Making with Belief Functions: a Review.**
International Journal of Approximate Reasoning, 109, 87-110.
https://arxiv.org/abs/1808.05322

Comprehensive review of how to make decisions under DS theory. Shows that most
methods blend criteria for decision under ignorance with Bayesian expected
utility. Relevant because propstore's render layer must eventually select among
competing claims -- this paper catalogs the options for doing so under DS
uncertainty rather than point probabilities.

**Pichon, F., Dubois, D., & Denoeux, T. (2012). Relevance and truthfulness in
information correction and fusion.**
International Journal of Approximate Reasoning, 53(2), 159-175.
https://hal.science/hal-00652236/document

Generalizes Shafer's discounting operation to handle sources that may be
irrelevant OR untruthful. Introduces correction schemes with uncertain
meta-knowledge about source behavior. Directly applicable to propstore's problem
of fusing claims from sources with varying reliability -- separates "this source
might be wrong" from "this source might be lying" from "this source might be
irrelevant."

### ATMS compatibility: HIGH
DS theory and ATMS share a natural affinity. Both work with sets of assumptions.
An ATMS label is a set of environments (assumption sets) under which a datum
holds; a DS mass function assigns mass to subsets of hypotheses. The ATMS can
maintain multiple DS mass assignments simultaneously without committing to any
single one. de Kleer's original ATMS work and DS theory are both
assumption-set-based, making integration straightforward.

---

## 2. Subjective Logic (Josang)

**Core idea:** An "opinion" is a tuple (b, d, u, a) -- belief, disbelief,
uncertainty, and base rate -- where b + d + u = 1. Opinions live on a triangle
(or simplex for multinomial). Crucially, u > 0 means "I explicitly don't know."
Fusion operators (cumulative, averaging, weighted) combine opinions from multiple
sources while tracking uncertainty mass.

### Key papers

**Josang, A. (2001). A Logic for Uncertain Probabilities.**
International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems,
9(3), 279-311.
https://www.mn.uio.no/ifi/english/people/aca/josang/publications/jos2001-ijufks.pdf

The original paper defining opinions, the opinion triangle, and logical operators
for subjective logic. Builds on DS belief theory but adds the base rate parameter
and defines a complete algebra of operators. Relevant because it gives us a
concrete replacement for bare floats: instead of "similarity = 0.73" we get
(b=0.5, d=0.1, u=0.4, a=0.5), which explicitly says "40% of the evidence is
missing."

**Josang, A. (2016). Subjective Logic: A Formalism for Reasoning Under
Uncertainty.**
Springer (Artificial Intelligence: Foundations, Theory, and Algorithms).
https://link.springer.com/book/10.1007/978-3-319-42337-1

The comprehensive book treatment. Covers all operators (deduction, abduction,
fusion, discounting, trust transitivity), multinomial and hyper opinions, and
subjective Bayesian networks. This is the reference for implementation. Chapter
on trust networks is directly applicable to propstore's source-reliability
problem.

**Josang, A., Wang, S., & Zhang, J. (2017). Multi-Source Fusion in Subjective
Logic.**
Proc. 20th International Conference on Information Fusion (Fusion 2017).
https://www.mn.uio.no/ifi/english/people/aca/josang/publications/jwz2017-fusion.pdf

Compares cumulative, averaging, and weighted belief fusion operators for
combining evidence from multiple sources. Directly relevant: propstore has
multiple extractors (NLI, embedding, LLM stance) producing competing assessments
of the same claim -- this paper addresses exactly how to combine them.

### ATMS compatibility: HIGH
Subjective opinions are isomorphic to Beta/Dirichlet distributions (see section
4 below) and thus to DS belief functions. The vacuous opinion (b=0, d=0, u=1)
represents total ignorance, which is exactly an ATMS assumption with no
supporting evidence. Multiple rival opinions can be maintained simultaneously in
different ATMS contexts without fusion, and fused only at render time. The
non-commitment principle maps perfectly: hold the raw opinions, fuse only when
the user asks.

---

## 3. Imprecise Probabilities / Credal Sets

**Core idea:** Instead of a single probability distribution, maintain a SET of
distributions (a "credal set") that are consistent with the available evidence.
Any query returns an interval [lower, upper] rather than a point. Strictly
generalizes both Bayesian probability (singleton credal set) and DS theory
(credal sets generated by belief functions).

### Key papers

**Walley, P. (1991). Statistical Reasoning with Imprecise Probabilities.**
Chapman & Hall.
https://philpapers.org/rec/WALSRW

The foundational monograph on imprecise probabilities as coherent lower
previsions. Establishes that whenever evidence is insufficient to pin down a
single distribution, the honest representation is a set of distributions.
Directly relevant: propstore's extractors often produce scores that don't justify
a precise probability, and Walley's framework says we shouldn't pretend they do.

**Augustin, T., Coolen, F.P.A., de Cooman, G., & Troffaes, M.C.M. (eds.)
(2014). Introduction to Imprecise Probabilities.**
Wiley (Series in Probability and Statistics).
https://onlinelibrary.wiley.com/doi/book/10.1002/9781118763117

Modern textbook covering the state of the art: sets of desirable gambles,
coherent lower previsions, graphical models, classification, statistical
inference. Written by multiple experts. Relevant as the implementation reference
-- particularly the chapters on decision making under imprecision and on
graphical models (which relate to propstore's argumentation graphs).

### ATMS compatibility: VERY HIGH
This is arguably the most natural fit. An ATMS already maintains multiple
contexts (environments). Each context can be associated with a probability
distribution, and the set of all consistent contexts IS a credal set. The ATMS's
non-commitment -- holding all environments simultaneously -- is exactly
imprecise-probability non-commitment. Dixon (1993, already in propstore's
literature list) showed ATMS context switching implements AGM belief revision;
credal sets add quantitative uncertainty to this qualitative structure.

---

## 4. Distributional Representations (Beta / Dirichlet)

**Core idea:** Instead of storing "probability = 0.73", store the parameters of
a Beta(alpha, beta) distribution (for binary) or Dirichlet(alpha_1, ...,
alpha_K) (for K-ary). The distribution represents uncertainty ABOUT the
probability. Beta(7.3, 2.7) means "best estimate 0.73 but only ~10 observations
worth of evidence" while Beta(73, 27) means "best estimate 0.73 with ~100
observations worth of evidence." The distribution's width encodes epistemic
uncertainty.

### Key papers

**Sensoy, M., Kaplan, L., & Kandemir, M. (2018). Evidential Deep Learning to
Quantify Classification Uncertainty.**
NeurIPS 2018.
https://arxiv.org/abs/1806.01768

Places a Dirichlet distribution on class probabilities and treats neural network
predictions as subjective opinions (connecting directly to Josang's subjective
logic). A single forward pass produces both a prediction and an uncertainty
estimate. Directly relevant: this is the state-of-the-art approach for getting
distributional uncertainty out of the kind of models propstore already uses (NLI,
embedding similarity). Instead of a bare float, the model outputs Dirichlet
parameters.

**Abdar, M., Pourpanah, F., Hussain, S., et al. (2021). A Review of Uncertainty
Quantification in Deep Learning: Techniques, Applications and Challenges.**
Information Fusion, 76, 243-297.
https://arxiv.org/abs/2011.06225

Comprehensive survey covering Bayesian neural nets, MC dropout, ensembles,
evidential deep learning, and more. Relevant as a map of the landscape -- shows
where Dirichlet/Beta approaches fit relative to other UQ methods, and which
methods are practical for different model types.

### ATMS compatibility: HIGH
Beta/Dirichlet parameters are equivalent to subjective logic opinions (Section 2)
and thus to DS mass functions (Section 1). A Beta(alpha, beta) encodes (b, d, u)
where u = K/(alpha + beta + K) for some prior weight K. The ATMS can hold
different Beta distributions for the same proposition under different assumption
sets. Updating is simple: adding evidence means adding to alpha/beta counts.
This is particularly attractive because the representation is compact (just two
numbers for binary, K numbers for K-ary) and update is trivial.

---

## 5. Structured Confidence (Multi-Dimensional Decomposition)

**Core idea:** A single "confidence = 0.73" conflates at least three orthogonal
dimensions: (1) source reliability -- how trustworthy is the provenance? (2)
evidential support -- how much evidence backs this specific claim? (3)
inferential strength -- how strong is the reasoning chain from evidence to
claim? These should be tracked separately and composed only at render time.

### Key papers

**Pichon, F., Dubois, D., & Denoeux, T. (2012). Relevance and truthfulness in
information correction and fusion.**
International Journal of Approximate Reasoning, 53(2), 159-175.
(Also cited under Section 1 above.)

Formally decomposes source assessment into relevance and truthfulness dimensions,
with separate uncertainty about each. This is the most rigorous treatment of
"what makes a source unreliable" -- it's not one thing, it's at least two
orthogonal dimensions. Maps directly to propstore's need to separate "this
extractor is generally unreliable" from "this specific extraction is weakly
supported."

**Malle, B.F. & Ullman, D. (2021). A Multi-Dimensional Conception and Measure
of Human-Machine Trust.**
In Trust in Human-Robot Interaction, Cambridge University Press.
https://research.clps.brown.edu/SocCogSci/Publications/Pubs/Malle_Ullman_inpress.pdf

Decomposes trust into capacity trust (reliable, competent) and moral trust
(ethical, transparent, benevolent). While aimed at human-robot interaction, the
dimensional decomposition is directly applicable: propstore sources have capacity
dimensions (does the NLI model get this class of claim right?) and integrity
dimensions (is the original source of the claim trustworthy?). Keeping these
separate prevents a high-capacity but low-integrity source from inheriting
undeserved trust.

**Parsons, S., Wooldridge, M., & Amgoud, L. (2003). Properties and Complexity
of Some Formal Inter-agent Dialogues.**
Journal of Logic and Computation, 13(3), 347-376.
https://www.cs.ox.ac.uk/people/michael.wooldridge/pubs/jlc2003.pdf

Formalizes argument trading between agents with different attitudes (beliefs,
capabilities, protocols). Relevant because it models the situation where
confidence about a claim depends on WHO is making the argument and WHAT
argumentative resources they have -- i.e., confidence is not intrinsic to the
claim but structured by the argumentation context.

### ATMS compatibility: HIGH
Multi-dimensional confidence fits ATMS perfectly because each dimension can be an
independent assumption. "Source S is reliable" is one assumption; "evidence E
supports claim C" is another; "the inference from E to C is valid" is a third.
The ATMS naturally tracks which conclusions depend on which combinations of these
assumptions. Different ATMS contexts can embody different assessments of the same
dimensions (e.g., one context assumes source S is reliable, another doesn't).

---

## 6. Probabilistic Argumentation

**Core idea:** Extend Dung AFs with probability. Two main approaches: (1)
constellations -- uncertainty about the STRUCTURE of the AF (which arguments and
attacks exist), modeled as a distribution over subgraphs; (2) epistemic --
uncertainty about the ACCEPTANCE STATUS of arguments in a fixed AF, modeled as
probability assignments constrained by attack relations.

### Key papers

**Hunter, A. & Thimm, M. (2017). Probabilistic Reasoning with Abstract
Argumentation Frameworks.**
Journal of Artificial Intelligence Research, 59, 565-611.
https://jair.org/index.php/jair/article/view/11074

The main reference for the epistemic approach. Defines probability functions over
arguments constrained by the topology of the AF -- if you believe in an argument,
you must disbelieve its attackers. Derives probabilities of remaining arguments
from partial assessments. Directly relevant: propstore already has Dung AFs; this
paper shows exactly how to add probabilistic assessments to them while respecting
the attack structure.

**Li, H., Oren, N., & Norman, T.J. (2012). Probabilistic Argumentation
Frameworks.**
Proc. TAFA 2011, LNCS 7132, Springer.
https://link.springer.com/chapter/10.1007/978-3-642-29184-5_1

The main reference for the constellations approach. Associates probabilities with
individual arguments and attacks, then computes likelihood of acceptance by
marginalizing over possible subgraphs. Relevant because propstore's claims and
attacks have varying evidential support -- some attacks are well-evidenced, others
speculative. The constellations approach lets us say "this attack exists with
probability 0.6" rather than forcing a binary include/exclude decision.

**Hunter, A., Polberg, S., Potyka, N., Rienstra, T., & Thimm, M. (2021).
Probabilistic Argumentation: A Survey.**
In Handbook of Formal Argumentation, Vol. 2, pp. 397-441.

Comprehensive survey covering both approaches plus connections to DS theory,
possibility theory, and fuzzy sets. The essential map of the landscape for anyone
implementing probabilistic argumentation.

### ATMS compatibility: VERY HIGH
The constellations approach is essentially ATMS reasoning: each possible
subgraph is a context (environment), and the ATMS tracks which conclusions hold
under which subgraphs. The probability distribution over subgraphs is metadata on
the ATMS environments. The epistemic approach constrains probability assignments
using the AF topology, which can be implemented as ATMS justifications (if
argument A is in, its attackers are out). Both approaches maintain multiple
simultaneous interpretations -- exactly what the ATMS does.

---

## 7. Calibration Literature

**Core idea:** Raw neural network output scores (softmax probabilities, cosine
similarities, NLI logits) are NOT calibrated probabilities. A model that outputs
0.8 for a class may be correct only 60% of the time. Post-hoc calibration
methods (temperature scaling, Platt scaling, isotonic regression) can fix this,
but the fundamental lesson is: model scores need transformation before they
can be interpreted as probabilities, let alone as belief strengths.

### Key papers

**Guo, C., Pleiss, G., Sun, Y., & Weinberger, K.Q. (2017). On Calibration of
Modern Neural Networks.**
ICML 2017.
https://arxiv.org/abs/1706.04599

The paper that demonstrated modern deep nets are systematically miscalibrated --
deeper and wider networks are MORE confident but not more accurate. Temperature
scaling (a single learned parameter) fixes most miscalibration. Directly
relevant: propstore's NLI and embedding scores come from exactly these kinds of
models. This paper proves those raw scores should not be stored as-is.

**Niculescu-Mizil, A. & Caruana, R. (2005). Predicting Good Probabilities with
Supervised Learning.**
ICML 2005, pp. 625-632.
https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf

The systematic comparison of Platt scaling (fit a sigmoid to model outputs) vs.
isotonic regression (fit a non-parametric monotone function) for calibrating
classifiers. Shows that different model families have characteristic calibration
distortions (SVMs push mass away from 0/1; neural nets are better calibrated
before post-hoc correction). Relevant as the practical reference for which
calibration method to use on propstore's extractor outputs.

**Minderer, M., Djolonga, J., Romijnders, R., et al. (2021). Revisiting the
Calibration of Modern Neural Networks.**
NeurIPS 2021.
https://arxiv.org/abs/2106.07998

Updates Guo et al.'s findings for modern architectures (Vision Transformers,
etc.). Finds that the most recent models are actually better calibrated,
and that trends like "bigger = less calibrated" don't hold for all architectures.
Relevant because it tells us which model families we can trust more or less with
raw scores -- important for choosing propstore's extractors.

### ATMS compatibility: MODERATE (indirect)
Calibration is a preprocessing step, not a representation framework. However, it
interacts with ATMS in an important way: calibrated scores are a prerequisite for
any of the frameworks above to produce meaningful results. If we feed uncalibrated
scores into DS theory or subjective logic, the resulting belief functions will be
systematically biased. Calibration should happen BEFORE mapping to any of the
richer representations.

---

## Synthesis: Compatibility and Recommendations

### ATMS compatibility ranking (for non-commitment)

1. **Imprecise probabilities / credal sets** -- Most natural fit. ATMS
   environments ARE a credal set. No additional machinery needed.
2. **Probabilistic argumentation (constellations)** -- Subgraphs map directly to
   ATMS environments. Probability is metadata on existing structure.
3. **Subjective Logic** -- Opinions are compact, fusable, and represent ignorance
   explicitly. Vacuous opinion = assumption with no evidence.
4. **Dempster-Shafer / belief functions** -- Mass functions on assumption subsets
   align naturally with ATMS labels.
5. **Beta/Dirichlet distributions** -- Equivalent to subjective logic opinions;
   compact storage, trivial update.
6. **Structured confidence** -- Orthogonal dimensions map to independent ATMS
   assumptions. Maximally compatible with non-commitment.
7. **Calibration** -- Preprocessing step, not a representation. Required
   regardless of chosen framework.

### What actually replaces the bare float

The bare float "similarity = 0.73" could become any of:

| Representation | Storage | What it captures |
|---|---|---|
| DS belief interval | [Bel=0.45, Pl=0.85] | Evidence for + explicit ignorance |
| Subjective opinion | (b=0.45, d=0.15, u=0.40, a=0.5) | Belief + disbelief + ignorance + prior |
| Credal interval | [0.45, 0.85] | Range of consistent probabilities |
| Beta distribution | Beta(4.5, 1.5) | Uncertainty about the probability itself |
| Structured tuple | {source_rel=0.8, evid_support=0.6, infer_strength=0.9} | Decomposed dimensions |

All of these are strictly more informative than a single float while being
compatible with propstore's ATMS-based non-commitment discipline.

### Recommended reading order for implementation

1. Guo et al. 2017 (calibration) -- understand why raw scores are broken
2. Josang 2001 or 2016 (subjective logic) -- the most practical replacement
3. Sensoy et al. 2018 (evidential deep learning) -- how to get Dirichlet
   outputs from existing model types
4. Hunter & Thimm 2017 (probabilistic argumentation) -- how to wire
   probabilities into the existing Dung AF
5. Walley 1991 or Augustin et al. 2014 (imprecise probabilities) -- for the
   theoretical foundation connecting everything to ATMS

### Key insight for propstore

Subjective logic opinions and Beta distributions are isomorphic. A Beta(alpha,
beta) maps to opinion (b, d, u, a) via:

    b = (alpha - a*W) / (alpha + beta)  [roughly]
    u = W / (alpha + beta + W)

where W is a prior weight parameter. This means propstore could store
Beta(alpha, beta) as the canonical representation and derive opinions, DS
intervals, or credal intervals as needed at render time. The ATMS would hold
Beta parameters per assumption set, and different rendering policies could
interpret them differently -- which is exactly the non-commitment discipline.
