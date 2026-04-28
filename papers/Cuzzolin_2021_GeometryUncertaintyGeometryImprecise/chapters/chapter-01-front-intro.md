# Chunk #1 — Front matter + Chapter 1 Introduction

**Book pages:** front matter (i-XXV) through book p.30 (chapter ends p.27; pages 28-30 are blank/Part-I divider/start of Ch.2 p.31-33)
**PDF idx:** 0-55

## Sections covered

- Front matter (cover, AI series page, copyright, dedication) *(pdf p.000–005)*
- Preface — Uncertainty *(p.VII)*
- Preface — Probability *(p.VIII)*
- Preface — Beyond probability + imprecise-probabilistic theories timeline *(pp.VIII–IX)*
- Preface — Belief functions *(pp.IX–X)*
- Preface — Aim(s) of the book *(pp.XI–XII)*
- Preface — Structure and topics (Part I–V tour, Chapters 1–17) *(pp.XII–XIII)*
- Preface — Acknowledgements *(p.XIV)*
- Table of Contents (Chapters 1–17 + Parts I–V) *(pp.XV–XXV)*
- §1.1 Mathematical probability *(p.1)*
- §1.2 Interpretations of probability *(p.3)*; 1.2.1 Does probability exist at all? *(p.3)*; 1.2.2 Competing interpretations *(p.3)*; 1.2.3 Frequentist probability *(p.4)* with subsections on hypothesis testing, p-values, MLE; 1.2.4 Propensity *(p.6)*; 1.2.5 Subjective and Bayesian probability *(p.7)*; 1.2.6 Bayesian vs frequentist inference (Lindley's paradox) *(p.9)*
- §1.3 Beyond probability *(p.9)*; 1.3.1 Something is wrong with probability *(p.9)*; 1.3.2 Pure data: Beware of the prior *(p.10)*; 1.3.3 Pure data: Designing the universe? *(p.10)*; 1.3.4 No data: Modelling ignorance *(p.11)*; 1.3.5 Set-valued observations: The cloaked die *(p.12)*; 1.3.6 Propositional data *(p.13)*; 1.3.7 Scarce data: Beware the size of the sample *(p.14)*; 1.3.8 Unusual data: Rare events *(p.17)*; 1.3.9 Uncertain data *(p.18)*; 1.3.10 Knightian uncertainty *(p.20)*
- §1.4 Mathematics (plural) of uncertainty *(p.23)*; 1.4.1 Debate on uncertainty theory *(p.23)*; 1.4.2 Belief, evidence and probability *(p.26)*
- (Bleed-through) Part I divider; first three pages of Chapter 2 — Belief functions *(pp.31–33)*

## Chapter overview

Chunk #1 is **Cuzzolin's manifesto**. The Preface and Chapter 1 together state both the diagnostic case against classical probability (why it is inadequate to model second-order, set-valued, scarce, rare, qualitative, or absent data) and the constructive thesis (a *plurality* of mathematics of uncertainty exists, with belief-function / random-set theory as Cuzzolin's preferred home, and his own contribution being the *geometric* approach to it).

Cuzzolin frames the book as the consolidation of his twenty-year research programme begun during his Padua doctorate. The `geometric approach to uncertainty' treats uncertainty measures as points in geometric spaces (simplices, polytopes, fibre bundles) so that combination, conditioning, transformation, and approximation become geometric operations. Chapter 1 is presented as an extended version of his IJCAI 2016 tutorial and 2016 Harvard talk. Three messages dominate:

1. **Probability is not enough.** Both frequentist and Bayesian readings of Kolmogorov fail in well-defined empirical situations: pure data without a designed experiment, scarce data, rare events ('black swans'), uncertain/qualitative/unreliable data, set-valued observations (the *cloaked die*), and outright ignorance. Cuzzolin lists these failure modes systematically in §1.3 and ties each to a concrete remedy (belief functions, random sets, credal sets, possibility theory, capacities).

2. **There is not one mathematics of uncertainty but many** — a hierarchy of *imprecise probabilities* (Keynes 1921 → Walley 1991 → Vovk-Shafer 2001) that contain classical probability as a special case. The Preface lists ten such formalisms in a timeline; Chapter 6 will give the full taxonomy.

3. **Belief-function / random-set theory is the right home, and the right way to study it is geometrically.** §1.4.2 names belief functions as the book's central object: "belief theory is a theory of *epistemic probability*" (p.27). Cuzzolin commits to a random-set agenda for Part V (Chapter 17): a comprehensive statistical theory of random sets as the natural destination of imprecise-probability research, motivating climate-change modelling, robust ML, and a generalised statistical learning theory.

The Table of Contents read here (pp.XV-XXV) maps the rest of the book: Part I (Ch.1–6) recapitulates state of the art; Part II (Ch.7–10) introduces the geometric machinery (belief space, geometry of Dempster's rule, three equivalent simplicial models — belief / plausibility / commonality, geometry of possibility / consonant subspace); Part III (Ch.11–14) — geometric interplays — affine and epistemic probability transforms, consonant approximation, consistent approximation; Part IV (Ch.15–16) — geometric reasoning — geometric conditioning and decision making with epistemic transforms; Part V (Ch.17) — the random-set research agenda. Part V is what Cuzzolin most wants to seed.

## Definitions

### Definition 1 (σ-algebra) *(p.1)*

A collection $\mathcal F$ of subsets of the sample space, $\mathcal F \subset 2^\Omega$, is called a σ-algebra (or σ-field) if it satisfies:
- $\mathcal F$ is non-empty: there is at least one $A \subset \Omega$ in $\mathcal F$;
- $\mathcal F$ is closed under complementation: if $A \in \mathcal F$ then $\overline A = \{\omega \in \Omega, \omega \notin A\} \in \mathcal F$;
- $\mathcal F$ is closed under countable union: if $A_1, A_2, A_3, \dots \in \mathcal F$ then $A = A_1 \cup A_2 \cup A_3 \cup \dots \in \mathcal F$.

### Definition 2 (probability measure) *(p.2)*

A probability measure over a σ-algebra $\mathcal F \subset 2^\Omega$, associated with sample space $\Omega$, is a function $P : \mathcal F \to [0,1]$ such that:
- $P(\emptyset) = 0$;
- $P(\Omega) = 1$;
- if $A \cap B = \emptyset$, $A, B \in \mathcal F$, then $P(A \cup B) = P(A) + P(B)$ (additivity).

### Definition 3 (maximum likelihood estimate) *(p.6)*

Given a parametric model $\{f(\cdot \mid \theta), \theta \in \Theta\}$ — a family of conditional probability distributions of the data given a vector parameter $\theta$ — the maximum likelihood estimate of $\theta$ is

$$
\hat\theta_{\mathrm{MLE}} \subseteq \left\{ \arg\max_{\theta \in \Theta} \mathcal L(\theta\,;\,x_1, \dots, x_n) \right\}
$$

where the likelihood given observed data $x_1, \dots, x_n$ is $\mathcal L(\theta\,;\,x_1, \dots, x_n) = f(x_1, x_2, \dots, x_n \mid \theta)$.

(Chapter 1 introduces these three formal objects only; later chapters carry the heavy load.)

## Theorems, propositions, lemmas

Chapter 1 invokes but does not formally prove theorems. Named results referenced:

- **Bayes' theorem (Eq. 1.1)** *(p.7)*: $P(B \mid A) = P(B \cap A)/P(A)$.
- **Bernstein–von Mises theorem** *(p.10)* [1841]: under regularity, posterior distribution on parameters becomes asymptotically Gaussian centred at the true value, independent of the prior, when sample size is large enough. Caveat [644]: theorem fails almost surely if random variable has a countably infinite probability space.
- **Cramér–Rao lower bound** *(p.6)* [1841]: MLE achieves the bound asymptotically (efficiency).
- **Likelihood principle** *(p.6)*: all evidence in a sample relevant to model parameters is contained in the likelihood function — disputed by some significance tests.
- **Law of total probability (Eq. 1.6)** *(p.20)*: generalisation of Bayesian conditioning via Jeffrey's rule.

## Equations

$$
2^\Omega \doteq \{A \subset \Omega\}
$$
**(p.1)** Where $\Omega$ is the sample space; $2^\Omega$ is its power set, also denoted $\mathcal P(\Theta)$.

$$
P(B \mid A) = \frac{P(B \cap A)}{P(A)}
$$
**(Eq. 1.1, p.7)** Bayes' rule. $P$ is a Kolmogorov probability measure; conditional probability of $B$ given $A$ when $P(A)>0$.

$$
p(\mathbf X \mid \alpha) = \int_\theta p(\mathbf X \mid \theta)\,p(\theta \mid \alpha)\,\mathrm d\theta
$$
**(p.8)** Marginal likelihood (also called the *evidence*). $\mathbf X = \{x_1,\dots,x_n\}$ observed data, $\theta$ parameters, $\alpha$ hyperparameters, $p(\theta\mid\alpha)$ prior, $p(\mathbf X\mid\theta)$ likelihood.

$$
p(\theta \mid \mathbf X, \alpha) = \frac{p(\mathbf X \mid \theta)\,p(\theta \mid \alpha)}{p(\mathbf X \mid \alpha)} \propto p(\mathbf X \mid \theta)\,p(\theta \mid \alpha)
$$
**(Eq. 1.2, p.8)** Bayesian posterior distribution.

$$
p(x' \mid \mathbf X, \alpha) = \int_\theta p(x' \mid \theta)\,p(\theta \mid \mathbf X, \alpha)\,\mathrm d\theta
$$
**(p.8)** Posterior predictive distribution for new data point $x'$.

$$
p(x' \mid \alpha) = \int_\theta p(x' \mid \theta)\,p(\theta \mid \alpha)\,\mathrm d\theta
$$
**(p.8)** Prior predictive distribution.

$$
\hat\theta_{\mathrm{MAP}}(x) \doteq \arg\max_\theta \frac{p(x \mid \theta)\,p(\theta)}{\int_\vartheta p(x \mid \vartheta)\,p(\vartheta)\,\mathrm d\vartheta} = \arg\max_\theta p(x \mid \theta)\,p(\theta)
$$
**(p.8)** Maximum a posteriori estimator: mode of the posterior.

$$
p(\theta) \propto \sqrt{\det \mathcal I(\theta)}, \quad \mathcal I(\theta) \doteq E\left[\left(\frac{\partial}{\partial \theta}\log f(\mathbb X \mid \theta)\right)^2 \,\bigg|\, \theta\right]
$$
**(Eq. 1.3, p.11)** Jeffreys' prior. $\mathcal I(\theta)$ is the Fisher information matrix; the prior is proportional to its square-root determinant. Cuzzolin notes Jeffreys' priors can be improper and violate the strong likelihood principle since $\mathcal I(\theta)$ depends on $\Omega$.

$$
P(Y = 1 \mid x) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x)}}
$$
**(Eq. 1.4, p.16)** Logistic regression: conditional probability of binary outcome $Y \in \{0,1\}$ given measurement $x$, parameters $\beta_0, \beta_1$ scalars.

$$
L(\beta \mid Y) = \prod_{i=1}^n \pi_i^{Y_i}(1 - \pi_i)^{Y_i}
$$
**(p.16)** Logistic-regression likelihood, $\pi_i = P(Y_i = 1 \mid x_i)$. (Note: Cuzzolin's printed exponent on the second factor reads `Y_i`; standard form would be $(1-Y_i)$.)

$$
\mathbb P(u(X) < x < v(X) \mid \theta, \phi) = \gamma \quad \forall (\theta, \phi)
$$
**(Eq. 1.5, p.17)** Confidence-interval defining property: random interval $[u(X), v(X)]$ covers $\theta$ with frequency $\gamma$ for all parameter values.

$$
\frac{P''(X)}{P''(Y)} = \begin{cases} P(X)/P(Y) & \text{if } P(Y) > 0\\ 0 & \text{if } P(Y) = 0\end{cases}
$$
**(p.20)** Constraint defining Jeffrey's rule of conditioning.

$$
P''(A) = \sum_{B \in \mathcal B} P(A \mid B)\,P'(B)
$$
**(Eq. 1.6, p.20)** Jeffrey's rule / law of total probability. $P$ defined on σ-algebra $\mathcal A$, $P'$ on subalgebra $\mathcal B$; updated probability $P''$ has values $P'$ on $\mathcal B$ and is determined elsewhere by this sum.

$$
(fEh)(\omega) = \begin{cases} f(\omega) & \omega \in E\\ h(\omega) & \omega \notin E\end{cases}
$$
**(Eq. 1.7, p.21)** Savage's sure-thing notation for an act $\mathcal F$ that pays $f$ on event $E$ and $h$ otherwise. Sure-thing principle: $f Eg \succcurlyeq h E g \Leftrightarrow f Eh \succcurlyeq h Eh$.

## Geometric structures

Chapter 1 is *not* yet about geometry — that begins formally in Chapter 7 — but it lays the groundwork by signposting the geometric programme:

- **Probability simplex** *(Fig. 1.6, p.15)*: the standard geometric object on which probability distributions live; classical machine-learning sample distributions are points inside it. Cuzzolin contrasts this single-point view with the **random-set** view in which training and test distributions correspond to *regions* (sets of points) inside the simplex.
- **Frame of discernment** *(p.X, p.26)*: Shafer's term for the universe of discourse (sample space) over which belief functions are defined; ignorance is encoded geometrically by mass on the whole frame.
- **Family of compatible frames** *(pp.X, 11, 31)*: Shafer's hierarchy of refining frames, the natural framework for belief functions on different but related representations. Cuzzolin notes (p.11) Bayesian formalism *cannot* handle multiple hypothesis spaces consistently — a deficiency the geometric / belief framework remedies.

Cuzzolin previews that later chapters will exhibit:
- **Belief space** as a higher-dimensional simplex with simplicial face structure (Ch.7).
- **Recursive bundle structure** of belief space (Ch.7.4).
- **Conditional subspaces** for Dempster's rule (Ch.8).
- **Three equivalent simplicial models** — belief, plausibility, commonality — congruent simplices (Ch.9).
- **Consonant subspace** for possibility measures (Ch.10).
- **Affine** and **epistemic** families of probability transforms (Ch.11–12).
- **Conditioning simplex** for geometric conditioning (Ch.15).

## Algorithms

**Hypothesis-testing procedure (numbered, p.4-5):**
1. State $H_0$ and alternative $H_1$.
2. State the statistical assumptions (e.g. independence, sample distribution).
3. State the relevant test statistic $T$.
4. Derive the distribution of $T$ under $H_0$ from the assumptions.
5. Set a significance level $\alpha$.
6. Compute from observations the observed value $t_{\mathrm{obs}}$ of $T$.
7. Compute the p-value (probability under $H_0$ of sampling a test statistic 'at least as extreme' as observed).
8. Reject $H_0$ in favour of the alternative iff p-value < significance threshold.

**Smets' three-step model-quality procedure** *(p.25)*:
1. Provide canonical examples justifying the origin of the numbers used.
2. Justify the fundamental axioms via 'natural' requirements.
3. Study the consequence of the derived models in practical contexts.

(No pseudocode for belief-function operations appears in this chapter.)

## Parameters / quantities

| Name | Symbol | Domain/Units | Default | Range | Page | Notes |
|------|--------|--------------|---------|-------|------|-------|
| Sample space | $\Omega$ | Set | – | – | p.1 | Universe of discourse |
| Power set | $2^\Omega = \mathcal P(\Theta)$ | Set of subsets | – | – | p.1 | All measurable events |
| σ-algebra | $\mathcal F$ | $\subset 2^\Omega$ | – | – | p.1 | Closed under complement and countable union |
| Probability measure | $P$ | $\mathcal F \to [0,1]$ | – | – | p.2 | Additive, $P(\Omega)=1$ |
| Random variable | $X$ | $\Omega \to \mathbb R$ | – | measurable | p.2 | Function such that pre-image of measurable set is in $\mathcal F$ |
| Significance level | $\alpha$ | probability | 0.05 / 0.01 | $(0,1)$ | p.4 | Threshold for rejecting $H_0$ |
| p-value | $p$ | probability | – | $(0,1)$ | p.5 | $P(X \geq x \mid H)$ etc. |
| Test statistic | $T$ | random variable | – | – | p.4 | Quantity derived from sample |
| Likelihood | $\mathcal L(\theta\,;\,x)$ | function | – | $\geq 0$ | p.6 | $f(x_1,\dots,x_n \mid \theta)$ |
| Hyperparameters | $\alpha$ | parameter vector | – | – | p.8 | Index prior $p(\theta\mid\alpha)$ |
| Prior | $p(\theta \mid \alpha)$ | density | – | $\geq 0$ | p.8 | Distribution before data |
| Posterior | $p(\theta \mid \mathbf X, \alpha)$ | density | – | $\geq 0$ | p.8 | After data |
| Marginal likelihood / evidence | $p(\mathbf X \mid \alpha)$ | density | – | $\geq 0$ | p.8 | Normaliser |
| Fisher information | $\mathcal I(\theta)$ | matrix | – | PSD | p.11 | Drives Jeffreys' prior |
| Logistic intercept / slope | $\beta_0, \beta_1$ | scalar | – | $\mathbb R$ | p.16 | Logistic-regression parameters |
| Mass assignment | $m: 2^\Omega \to [0,1]$ | function | – | – | p.32 | $\sum m(A)=1$ on subsets of frame |
| Frame of discernment | $\Theta$ | finite set | – | – | p.X, 26, 32 | Universe of discourse for belief functions |

## Worked examples

### Example: Spinning wheel *(Fig. 1.1, p.2)*

A discrete spinning wheel with three sectors (red, yellow, green) defines $\Omega = \{1, 2, 3\}$ and a probability measure $P$ on $2^\Omega$ assigning $P(\{i\}) = $ proportion of arc occupied by colour $i$. The example illustrates Definition 2 and the geometric intuition of probability-measure values along $[0,1]$. Cuzzolin uses it as the simplest case to anchor the σ-algebra / probability-measure / random-variable triple.

### Example: Cloaked die *(Figs. 1.3, 1.4, pp.12-13)*

A die has faces 1-6 mapped to $\mathbb R$ by random variable $X$. The physics is unchanged so probabilities $P(\{i\}) = 1/6$ remain. Now imagine faces 1 and 2 are *cloaked* (invisible): when one of them comes up the observer cannot tell which. The mapping changes: $\{1\} \cup \{2\} = \{1,2\}$ is mapped to a set on $\mathbb R$, faces 3–6 remain pointwise. We are now sampling not a scalar but a *random set* [1268, 950, 1344, 1304] — the die produces set-valued outcomes.

A more realistic variant: only some faces are cloaked, e.g. red faces 5,6 and green faces 2,3 are visible; if any blue face $\{2,5,6\}$ is rolled, only the proposition $\{2,5,6\}$ is reported. **Takeaway:** real observations in computer vision, medicine, etc. routinely deliver such set-valued evidence; classical probability cannot natively model 'I observed *one of* $\{2,5,6\}$' — only belief / random-set theory can.

### Example: Murder trial (Peter, John, Mary) *(p.13, fig. 2.1 p.33)*

Hypothesis space $\Theta = \{\text{Peter, John, Mary}\}$. A witness testifies they saw a *man* — supporting proposition $A = \{\text{Peter, John}\} \subset \Theta$ — but the witness was 80% sober (i.e. evidence has reliability 0.8). 80% mass should support the *set* $\{$Peter, John$\}$, not be split among individuals. Cuzzolin uses this to motivate why probability is too rigid: additivity forces $P(\{$Peter$\}) + P(\{$John$\}) = 0.8$, but no information says how to distribute. Belief functions handle this by *assigning mass directly to subsets*.

In Chapter 2 (p.33) the example becomes formal: $\Omega = \{\text{Drunk, Not drunk}\}$ with $P(\text{Drunk}) = 0.2$, $P(\text{Not drunk}) = 0.8$, mapped via multivalued $\Gamma : \Omega \to 2^\Theta$ to outcomes in $\Theta$; $\Gamma(\text{Drunk}) = \Theta$ (no information when drunk); $\Gamma(\text{Not drunk}) = \{\text{Peter, John}\}$. Mass assignment becomes $m_2(\{\text{John, Mary}\})=0.6, m_2(\Theta)=0.4$ for a second piece of evidence (blood-stain match), to be combined via Dempster's rule.

### Example: Logistic regression and rare events *(Eq. 1.4, Fig. 1.7, pp.16-18)*

A binary outcome $Y$ versus measurement $x$ with sigmoid fit $P(Y=1\mid x) = 1/(1+e^{-(\beta_0+\beta_1 x)})$. Training samples cluster near $x \in [-2, 2]$. Logistic regression underestimates rare events at the tail (e.g. $x \approx 8$): the sigmoid asymptotes to 1 only with abundant tail data. King's [970] correction oversamples 1s vs 0s.

### Example: Ellsberg's paradox *(Eq. 1.7, p.21)*

Urn $U$: 30 red balls + 60 black-or-yellow balls in unknown proportion. Decision space $D$ = {red, blue, yellow}.
- Gamble $f_1$: 100 if red, 0 otherwise.
- $f_2$: 100 if black, 0 otherwise.
- $f_3$: 100 if red or yellow, 0 otherwise.
- $f_4$: 100 if black or yellow, 0 otherwise.

Empirically people prefer $f_1 \succ f_2$ (guaranteed 1/3 vs interval $[0, 2/3]$) but $f_4 \succ f_3$. Sure-thing principle would force $f_1 \succ f_2 \Rightarrow f_3 \succ f_4$. The empirical reversal is the **Ellsberg paradox** — direct evidence of human aversion to second-order (Knightian) uncertainty, hence direct evidence the Bayesian framework is descriptively wrong.

### Example: Multiple Kalman filters *(p.19)*

Two Kalman filters — one based on colour, another on motion — each output a Gaussian PDF on the same state space (target location). Bayesian conditioning with Bayes' rule cannot combine two PDFs on the same σ-algebra; Jeffrey's rule cannot either. **Belief functions** combine the two PDFs symmetrically by combination, not asymmetric conditioning.

## Figures of interest

- **Fig. 1.1 (p.2):** A spinning wheel. Shows $\Omega = \{1,2,3\}$ partitioned into coloured arcs, σ-algebra $\mathcal F$ over $2^\Omega$, probability $P$ as a function $\mathcal F \to [0,1]$ with values $\{0, 1/4, 1/2, 3/4, 1\}$ visualised on a number line. Anchors the formal triple $(\Omega, \mathcal F, P)$ in pictorial form.
- **Fig. 1.2 (p.5):** P-value diagram. PDF of the test statistic with shaded tail beyond the observed data point; introduces the visual idiom of left/right-tail and double-tail events.
- **Fig. 1.3 (p.12):** A standard die viewed as a random variable $X : \Omega \to \mathbb R$, with faces 1-6 mapped to numbers 1-6.
- **Fig. 1.4 (p.13):** The cloaked die: faces 1,2 invisible, so the mapping is now to a *set*-valued image on $\mathbb R$. Visual core of the random-set motivation.
- **Fig. 1.5 (p.14):** A capacity $\mu : 2^\Theta \to [0,1]$ with $A \subset B \Rightarrow \mu(A) \leq \mu(B)$ (monotonicity). Illustrates that capacities, not just additive measures, are the right object when evidence is set-valued.
- **Fig. 1.6 (p.15):** Random-set generalisation of statistical learning theory. Inside a probability simplex, the training distribution (set of training samples) and the test distribution (set of test samples) are *random sets* (regions), not single points. Foreshadows Chapter 17.
- **Fig. 1.7 (p.17):** Logistic regression with the 'rare event' tail explicitly marked — few or no training samples there but the model is asked to extrapolate.
- **Fig. 1.8 (p.21):** Urn picture for Ellsberg's paradox — 30 red, 60 black-or-yellow.
- **Fig. 1.9 (p.27):** Belief function theory as evidential, epistemic probability. A diagram showing Evidence → Probabilistic knowledge → (Truth, Belief). Belief is a state of mind which is *justified* by evidence; epistemology is the branch of philosophy concerned with knowledge.
- **Fig. 2.1 (p.33):** Multivalued mapping $\Gamma : \Omega \to 2^\Theta$ encoding the murder-trial example. (Bleed-through to Ch.2 in our chunk range.)

## Criticisms of prior work

- **Frequentism — narrow scope** *(p.9)*: testing only rejects/does-not-reject hypotheses. Choice of $\alpha$ (0.05, 0.01) is arbitrary. The 'tail event' contraption is a patch for the fact that under measure theory point outcomes have probability zero. Cannot cope with pure data without designed-experiment assumptions.
- **Frequentism — same data, opposite conclusions** *(p.11)*: same data can support opposite conclusions because parametric models are tied to specific experiments. "Apparently, frequentists are just fine with this" [2131].
- **Bayesianism — cannot represent ignorance** *(p.10)*: Jeffreys' uninformative priors give different results under reparametrisation; Bayes' rule requires evidence in the form 'A is true', not the typical real form. Klir [988]: a precise probabilistic model defined only on some events determines only *interval* probabilities for events outside.
- **Bayesianism — model selection** *(p.10)*: no clear-cut criterion for selecting a prior beyond the formalism's demand for one.
- **Bayesianism — confusion of subjective vs objectivist views** *(p.10)*: Cuzzolin's view is that there is "a fundamental confusion between the original Bayesian description of a person's subjective system of beliefs ... and the 'objectivist' view of Bayesian reasoning as a rigorous procedure for updating probabilities."
- **Asymptotic crutch** *(pp.10, 16)*: both frequentists and Bayesians lean on Bernstein–von Mises and MLE asymptotics. "This hardly fits with current AI applications, in which machines need to make decisions on the spot to the best of their abilities."
- **Bayesian rare-event underestimation** *(pp.17–18)*: logistic regression underestimates probability of positive outcomes when 1s are rare. King [970] proposes oversampling fix; some authors abandon generative models entirely [74].
- **Bayesian Dutch-book argument is not airtight** *(p.7)*: Dutch-book arguments leave open the possibility that *non-Bayesian* updating rules avoid Dutch books. Cuzzolin: "one of the purposes of this book is indeed to show that this is the case."
- **Bayesianism contradicts evidence on humans** *(pp.7-8)*: Kahneman (Nobel Prize) and Tversky empirically disprove the assumption that humans maintain coherent beliefs / behave rationally. Ellsberg's paradox empirically violates the sure-thing principle.
- **Climate-change modellers ignore statistical uncertainty** *(p.22)*: mainstream climate modelling does not explicitly model uncertainty; relies on ever more complex deterministic models which themselves exhibit chaotic behaviour. Lack of priors, complex dependencies in long climate-vector data, scarcity of historical data, no designed experiment — none of frequentism nor Bayesianism is suitable.
- **Walley's imprecise probability requires abandoning events** *(p.X)*: belief functions retain events; Walley's framework does not.
- **Pearl's intensional/extensional distinction** *(p.24)* [1401]: contrasts rule-based extensional (logical) systems with intensional 'states-of-the-world' frameworks; computational aspects of belief networks emphasised.
- **Smets's caution against 'it worked before' inference** *(p.25)* [1702]: empirical results can only falsify a model, never prove it correct. Greatest danger in approximate reasoning is using inappropriate, unjustified models.
- **Henkind's MYCIN/EMYCIN survey** *(p.24)* [822]: no single calculus is best for all situations.
- **Gelman's coin-flip / box-wrestling example** *(pp.25-26)* [672]: robust Bayes lets ignorance spread too broadly; belief functions inappropriately collapse to simple Bayesian models. Cuzzolin nonetheless prefers belief functions.

## Design rationale

- **Random sets as the right primitive** *(pp.12-13, p.26)*: when observations are inherently set-valued (cloaked die, missing data, occlusion in computer vision), they are samples not from a scalar random variable but from a *random set*. The natural mathematical object for set-valued data is the random set / belief function, not the additive probability measure with deletion-imputation patches. "Multiple imputation involves drawing values of the parameters from a posterior distribution, therefore simulating both the process generating the data and the uncertainty associated with the parameters of the probability distribution."
- **Mass on subsets, not on points** *(p.14)*: capacities allow assigning mass to propositions directly rather than forcing decomposition to singletons; the murder-trial example illustrates that assigning 80% to $\{$Peter, John$\}$ + 20% to $\Theta$ is the *natural* representation of "the witness saw a man with 80% reliability."
- **Combination, not conditioning** *(p.20)*: belief functions deal with uncertain evidence by *combining* pieces of evidence simultaneously supporting multiple propositions; combination is symmetric, conditioning is asymmetric. Bayes' rule (asymmetric) cannot handle two sensor PDFs on the same space; Dempster's rule can.
- **Geometric approach** *(Preface p.XI)*: encoding uncertainty measures as points in geometric spaces enables principled reasoning about combination, transformation, approximation; reasoning by distance, projection, congruence rather than algebraic manipulation alone.
- **Frame of discernment + family of compatible frames** *(p.X)*: granularity of knowledge representation is a first-class structural notion in belief theory; Bayesian formalism cannot do this consistently across hypothesis spaces.
- **Reject 'one calculus to rule them all'** *(p.24)*: Cuzzolin sides with Henkind, Krause, Zimmerman: the right formalism is context-dependent. He nevertheless argues belief / random-set theory is the most general, encompassing fuzzy and possibility theory and convex sets of probabilities as special cases.
- **Why belief functions rather than Walley** *(p.26)*: belief functions retain events, are a direct generalisation of probability, and include fuzzy and possibility theory as special cases; Walley's framework requires abandoning the notion of an event.
- **Random-set agenda for the future** *(Preface p.XII)*: research problems in the book point toward a comprehensive statistical theory of random sets; uncertainty theory must compete on real high-stakes problems (climate change, robust AI, rare-event estimation).

## Open / research questions

- **Epistemic interpretation of belief functions** *(Preface p.X)*: "what is the correct epistemic interpretation of belief functions[?]"
- **Intervals of belief functions** *(p.X)*: "whether we should actually manipulate intervals of belief functions rather than single quantities"
- **Continuous case** *(p.X)*: "how to formulate an effective general theory for the case of continuous sample spaces"
- **Combination rule debate** *(p.X)*: "what combination rule is most appropriate under what circumstances has been hotly debated"
- **Computational complexity of working with sets of hypotheses** *(p.X)*: ongoing.
- **Modelling rare events when training data are scarce** *(pp.17-18)*: King's correction or abandoning generative models — neither is fully satisfactory.
- **Climate change as the canonical hard uncertainty problem** *(p.22)*: how to model second-order uncertainty in long-horizon, chaotic, scarce-data, no-designed-experiment settings.
- **Generalising statistical learning theory to random sets** *(Preface p.XIII; Fig. 1.6, p.15)*: the open programme of Chapter 17.
- **A 'true' geometry of uncertainty** *(Preface p.XII; TOC §17.2.3)*: extension of the geometric programme beyond belief functions.

## Notable references cited

(Numbers are Cuzzolin's bibliography keys, copied verbatim where cited.)

- `[1030]` Kolmogorov — Foundations of measure-theoretic probability *(pp.VIII, 1)*.
- `[1175]` Lindley — quoted on uncertainty being everywhere *(p.VII)*.
- `[1007, 831]` Knight — risk vs uncertainty *(p.VII)*.
- `[569]`, `[565]` Ellsberg — Ellsberg paradox *(pp.VIII, 20)*.
- `[1739]` source of the 'common cause / special cause' distinction *(p.VIII)*.
- `[961]` Keynes — economic interpretation of probability *(p.VIII)*; treatise of probability 1921 *(p.IX)*.
- `[1841]` Bernstein–von Mises asymptotic theorem; also Cramér–Rao lower bound *(pp.VIII, 6, 10)*.
- `[1583]` Shafer — *A Mathematical Theory of Evidence* (1976) *(pp.IX-X, 11, 26-27)*.
- `[415, 417, 418, 416]` Dempster — seminal upper-and-lower-probability papers *(pp.IX, 26)*; `[424]` Dempster (Ch.2 opener, p.31).
- `[1268, 1857, 826, 1344, 1304, 1302, 950]` Random-sets bibliography (Molchanov, Matheron, etc.) *(pp.X, 12, 26)*.
- `[773]` Dempster's rule of combination *(pp.X, 31)*.
- `[1949]` no-prior reasoning *(pp.X, 31)*.
- `[1607]` Shafer's canonical examples *(pp.13, 33)*.
- `[1874]` Walley — *Statistical Reasoning with Imprecise Probabilities* (1991) *(pp.IX, X, 26)*.
- `[2084, 533, 973, 531, 2083]` Zadeh / Klaua — fuzzy theory *(pp.IX, 19)*.
- `[784]` probability intervals *(p.IX)*.
- `[1141, 1086]` Levi — credal sets *(p.IX)*; `[401]` belief functions and credal sets *(p.13)*.
- `[1911]` monotone capacities *(p.IX)*.
- `[1877]` Walley on behavioural probability *(pp.IX, 4)*.
- `[1615]` Shafer–Vovk game-theoretical probability *(p.IX)*.
- `[403, 404]` de Finetti — subjective probability and Dutch book *(pp.IX, 7)*.
- `[783]` measure theory reference *(p.1)*.
- `[1736]` Doc Smith *Lensman* (Arisians) — playful illustration of perfect-knowledge determinism *(p.3)*.
- `[119]` argument from quantum mechanics *(p.3)*.
- `[45]` Savage on probability interpretation *(p.3)*.
- `[620]` Fisher 1922 — coined 'likelihood' *(p.6)*.
- `[1415]` Popper-style propensity theory *(p.6)*; `[1439]` Popper revisited *(p.7)*.
- `[419]` Bayes' framework *(p.7)*; `[1143]` conditional probability *(p.7)*.
- `[894]` Jeffreys, *Theory of Probability* *(p.7)*; `[895]` Jeffreys' priors *(pp.10, 11)*.
- `[1870]` Wald 1950 *(p.7)*; `[1537]` Savage 1954 *(p.7)*.
- `[644]` caveat to Bernstein–von Mises *(p.10)*; `[564]` Edwards *(p.11)*.
- `[1690, 1227]` Jeffrey's rule of conditioning *(p.19)*.
- `[1141]` Spies — propositional belief functions *(p.13)*.
- `[988]` Klir — imprecision needed *(pp.10, 16)*; `[1589]` constraints on 'true' distributions *(p.16)*.
- `[1849, 1851, 1850]` Vovk-Shafer-style robust learning *(p.15)*.
- `[970]` King — rare-events logistic correction *(pp.16, 18)*.
- `[673]` Gelman & King — election decisiveness *(p.18)*.
- `[2131]` frequentist defence *(p.11)*.
- `[1590]` Shafer on Lindley's paradox *(pp.9, 24)*; `[426]` Lindley's response *(p.24)*; `[828, 706, 1828]` Lindley's-paradox literature *(p.24)*.
- `[635, 87, 1619]` Forster — likelihood theory of evidence *(p.24)*.
- `[841]` Horvitz 1986 — relations between uncertainty calculi *(p.23)*.
- `[822]` Henkind — DS, fuzzy, MYCIN, EMYCIN survey *(p.24)*.
- `[200, 778]` MYCIN, EMYCIN *(p.24)*; `[2132]` Zimmerman *(p.24)*.
- `[1401]` Pearl 1988 — extensional vs intensional uncertainty reasoning *(p.24)*.
- `[540]` Dubois–Prade *(p.24)*; `[1088]` Kyburg *(p.24)*.
- `[1702, 1684]` Smets *(p.25)*; `[1597]` Shafer 1987 *(p.25)*; `[1816]` Thompson *(p.25)*; `[1512]` Ruspini 1991 *(p.25)*; `[1067]` Krause 1993 book *(p.25)*.
- `[235]` Castelfranchi et al. — expectations / beliefs / goals *(p.25)*.
- `[672]` Gelman — coin-flip example *(p.25)*.
- `[956]` Keppens — subjective probability in crime investigation *(p.26)*.
- `[1583]` Shafer's framing of belief theory *(p.26)*.
- `[153, 1078]` extensions of belief to real-valued functions *(p.26)*.
- `[1893, 1892]` Wang on limitation of Bayesianism *(p.23)*; `[255]` Cheeseman 'In defense of probability' *(p.23)*.
- `[890]` debate on uncertainty quantification *(p.23)*; `[943]` Kahneman–Tversky 1982 paper *(p.23)*.
- `[586, 205]` probabilistic logic *(p.27)*; `[1405, 1682, 137]` belief as probability of provability *(p.27)*; `[800]` modal logic interpretation *(p.27)*.
- `[1607]` Shafer's canonical examples *(pp.13, 33)*.
- `[2083]` Zadeh's generalised theory of uncertainty *(p.IX)*.
- `[587]` rare events / credible vs confidence intervals *(p.17)*.
- `[74]` discriminative-only models *(p.18)*.

## Implementation notes for propstore

- **§1.1's σ-algebra and probability-measure definitions (Defs 1, 2)** are the *background axioms* against which propstore's belief / opinion / capacity machinery is positioned. The `propstore.world.assignment_selection_merge` and the broader belief substrate operate at a layer *strictly more general* than Def. 2 (additivity dropped). Cross-reference these definitions in any propstore documentation that explains why `OpinionDocument` carries non-additive mass.
- **Cuzzolin's enumeration of failure modes of probability (§1.3)** maps almost one-to-one onto propstore's design rationale:
  - 'No data: modelling ignorance' (§1.3.4) → propstore's *vacuous opinion* provenance type (Jøsang). Cuzzolin's Jeffreys-prior critique justifies why `provenance: vacuous` is preferred over `provenance: defaulted` with a fabricated uniform.
  - 'Set-valued observations: cloaked die' (§1.3.5) → propstore's `LexicalSense.reference` carrying potentially multiple supports; ATMS environments labelling sets of assumptions; lemon-shaped concepts inherently set-rather-than-point.
  - 'Propositional data' (§1.3.6) → DeLP rules + ATMS + ASPIC+ bridge: propstore models evidence as supporting *propositions / subsets of the frame*, not pointwise outcomes.
  - 'Scarce data' (§1.3.7) and 'Unusual data: rare events' (§1.3.8) → calibration provenance (Guo et al. 2017) plus typed `provenance: calibrated` vs `measured`; honest-ignorance discipline in `propstore.belief_set`.
  - 'Uncertain data' (§1.3.9) → multi-source evidence combination via Dempster (or alternative) rule rather than single-rule Bayes; aligns with `propstore.aspic_bridge` and Smets-style discounting.
  - 'Knightian uncertainty' (§1.3.10) → second-order uncertainty representation; the Ellsberg-paradox illustration validates *not collapsing* disagreement at storage time (the `non-commitment discipline` of CLAUDE.md).
- **Family of compatible frames (Preface p.X; §1.3.4)** → propstore's `family-of-compatible-frames` notion already implicit in: lemon-shaped concept refinement, structured contexts with explicit lifting rules. The Cuzzolin refinement-and-marginalisation operator is the formal counterpart to propstore's `ist(c, p)` lifting + Carroll JSON-LD named graph provenance.
- **Combination vs conditioning (Eq. 1.6 + p.20)**: propstore's argumentation layer should treat `combine` (symmetric, both arguments belief-typed) and `condition` (asymmetric, on a precise event) as distinct primitives. Jeffrey's rule (Eq. 1.6) is the right reference for `update with belief-typed evidence on a sub-σ-algebra'.
- **Geometric programme**: Cuzzolin's belief-space simplex / commonality / plausibility congruences (Ch.7-9) are not yet implemented in propstore; if/when implemented they would live alongside `propstore.belief_set` as alternative coordinate systems for the same underlying mass assignment. Useful for visualisation of stance disagreement (a stance is a point; rival stances are points to be compared by belief-space distance).
- **Random-set view of statistical learning (Fig. 1.6, p.15; Ch.17)** → propstore's "every imported KB row is a defeasible claim with provenance" principle is a discrete cousin of the random-set view: instead of a single training distribution we maintain a *set* of admissible distributions, indexed by source.
- **Smets' three-step model-quality procedure (p.25)** is a useful checklist for adding new uncertainty types to propstore: (1) canonical example justifying numbers; (2) axioms with natural-requirement justification; (3) practical-context validation. Cite when adding a new opinion or merge framework.
- **Ellsberg's paradox (Eq. 1.7, p.21)** is the canonical empirical demonstration that humans require something stronger than a single additive probability for decision under ignorance. Useful as a regression-test case for any propstore decision-making apparatus.

## Quotes worth preserving

- *(p.VII)* "There are some things that you know to be true, and others that you know to be false; yet, despite this extensive knowledge that you have, there remain many things whose truth or falsity is not known to you. ... Uncertainty is everywhere and you cannot escape from it." — Lindley, quoted by Cuzzolin.
- *(p.VII)* "Uncertainty must be taken in a sense radically distinct from the familiar notion of risk, from which it has never been properly separated... a measurable uncertainty, or 'risk' proper, ... is so far different from an unmeasurable one that it is not in effect an uncertainty at all." — Knight.
- *(p.VIII)* "Bayesian reasoning is also plagued by many serious limitations: (i) it just cannot model ignorance (absence of data); (ii) it cannot model pure data (without artificially introducing a prior, even when there is no justification for doing so); (iii) it cannot model 'uncertain' data, i.e., information not in the form of propositions of the kind 'A is true'; and (iv) again, it is able to model scarce data only asymptotically, thanks to the Bernstein–von Mises theorem."
- *(p.XI)* "In this *geometric approach to uncertainty*, uncertainty measures can be seen as points of a suitably complex geometric space, and there manipulated (e.g. combined, conditioned and so on)."
- *(p.XII)* "...my intuition brings me to favour a random-set view of uncertainty theory, driven by an analysis of the actual issues with data that expose the limitations of probability theory."
- *(p.4)* "It is unanimously agreed that statistics depends somehow on probability. But, as to what probability is and how it is connected with statistics, there has seldom been such complete disagreement and breakdown of communication since the Tower of Babel." — Savage, quoted.
- *(p.10)* "...this is the result of a fundamental confusion between the original Bayesian description of a person's subjective system of beliefs and the way it is updated, and the 'objectivist' view of Bayesian reasoning as a rigorous procedure for updating probabilities when presented with new information."
- *(p.11)* (Edwards, quoted) "It is sometimes said, in defence of the Bayesian concept, that the choice of prior distribution is unimportant in practice, because it hardly influences the posterior distribution at all when there are moderate amounts of data. The less said about this 'defence' the better."
- *(p.16)* (Klir, quoted) "Imprecision of probabilities is needed to reflect the amount of information on which they are based."
- *(p.20)* "Belief functions deal with uncertain evidence by moving away from the concept of *conditioning* (e.g., via Bayes' rule) to that of *combining* pieces of evidence simultaneously supporting multiple propositions to various degrees. While conditioning is an inherently asymmetric operation, ... combination in belief function reasoning is completely symmetric."
- *(p.27)* "Belief theory is a theory of *epistemic probability*: it is about probabilities as a mathematical representation of knowledge."
