---
title: "Inferences from Multinomial Data: Learning About a Bag of Marbles"
authors: "Peter Walley"
year: 1996
venue: "Journal of the Royal Statistical Society Series B: Statistical Methodology"
doi_url: "https://doi.org/10.1111/j.2517-6161.1996.tb02065.x"
pages: "3-57"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-28T22:06:05Z"
---
# Inferences from Multinomial Data: Learning About a Bag of Marbles

## One-Sentence Summary
Introduces the Imprecise Dirichlet Model (IDM), a set of Dirichlet priors parameterized by a single hyperparameter s that produces initially vacuous upper and lower probabilities which converge with data, satisfying the embedding, symmetry, and representation invariance principles that no single Bayesian prior can jointly satisfy.

## Problem Addressed
When making inferences from multinomial data with no prior information, objective Bayesian methods require choosing a single prior distribution, which produces inferences that depend on the arbitrary choice of sample space. The principle of indifference cannot be applied without first fixing the set of "equipossible" outcomes, but in many practical problems the sample space is initially unknown or evolving. *(p.3)*

## Key Contributions
- Defines the **Imprecise Dirichlet Model (IDM)**: a set of Dirichlet(s, **t**) priors where s is fixed and **t** ranges over the probability simplex *(p.9)*
- Proves the IDM satisfies three key principles that no Bayesian model can jointly satisfy: embedding principle, symmetry principle, and representation invariance principle (RIP) *(p.5, p.16)*
- Derives closed-form upper and lower posterior probabilities, means, variances, and credible intervals *(p.10, p.17)*
- Shows the IDM with s=1 agrees numerically with Clopper-Pearson confidence intervals and Fisher's exact test *(p.12-13)*
- Demonstrates application to clinical trial decision-making with the ECMO vs CT example *(p.25-31)*
- Provides a principled framework for deciding when to terminate randomized clinical trials *(p.29-30)*

## Methodology
The paper develops a theoretical statistical model (the IDM) from first principles, derives its mathematical properties, and demonstrates it on two examples: (1) inferring marble colours from a bag, and (2) comparing two medical treatments from a 2x2 contingency table. The approach is grounded in the theory of coherent upper and lower probabilities from Walley (1991).

## Key Equations / Statistical Models

### Multinomial Likelihood

$$
L(\boldsymbol{\theta}|\mathbf{n}) \propto \prod_{j=1}^{k} \theta_j^{n_j}
$$
Where: $\boldsymbol{\theta} = (\theta_1, \ldots, \theta_k)$ are category probabilities, $\mathbf{n} = (n_1, \ldots, n_k)$ are observed frequencies, $N = \sum n_j$ is total observations.
*(p.8)*

### Dirichlet Prior Density

$$
\pi(\boldsymbol{\theta}) \propto \prod_{j=1}^{k} \theta_j^{st_j - 1}
$$
Where: $s > 0$ is the hyperparameter, $0 < t_j < 1$ for $j = 1, \ldots, k$, $\sum_{j=1}^{k} t_j = 1$. Here $t_j$ is the prior mean of $\theta_j$ and $s$ determines the influence of the prior on posterior probabilities.
*(p.9)*

### Dirichlet Posterior Density

$$
\pi(\boldsymbol{\theta}|\mathbf{n}) \propto \prod_{j=1}^{k} \theta_j^{n_j + st_j - 1}
$$
This is a Dirichlet$(N+s, \mathbf{t}^*)$ distribution where $t_j^* = (n_j + st_j)/(N+s)$.
*(p.9)*

### Posterior Upper and Lower Probabilities (Single Category)

$$
\overline{P}(A_j|\mathbf{n}) = \frac{n_j + s}{N + s}
$$
Achieved in the limit as $t_j \to 1$.

$$
\underline{P}(A_j|\mathbf{n}) = \frac{n_j}{N + s}
$$
Achieved as $t_j \to 0$.
*(p.10)*

### Posterior Upper and Lower Probabilities (General Event)

$$
\overline{P}(A|\mathbf{n}) = \frac{n(A) + s}{N + s}
$$

$$
\underline{P}(A|\mathbf{n}) = \frac{n(A)}{N + s}
$$
Where $A$ is any non-trivial subset of $\Omega$, $n(A) = \sum_{\omega_j \in A} n_j$.
*(p.10)*

### Imprecision Measure

$$
\overline{P}(A|\mathbf{n}) - \underline{P}(A|\mathbf{n}) = \frac{s}{N + s}
$$
Imprecision is constant across all events and decreases as $N$ increases. The number of observations needed to halve the initial imprecision is $s$.
*(p.10)*

### Bayesian Posterior with Symmetric Dirichlet Prior

$$
P(A|\mathbf{n}) = \frac{n(A) + sk^{-1}c(A)}{N + s}
$$
Where $c(A)$ is the number of elements in $A$ and $k$ is the number of categories. This depends on $k$ (the sample space), violating the RIP.
*(p.11)*

### Posterior Upper and Lower Expected Values

$$
\overline{E}(\theta_j|\mathbf{n}) = \frac{n_j + s}{N + s}
$$

$$
\underline{E}(\theta_j|\mathbf{n}) = \frac{n_j}{N + s}
$$
Prior upper and lower expected values (when $N=0$) are 1 and 0 respectively, consistent with prior ignorance.
*(p.17)*

### Posterior Upper and Lower Variances

$$
\overline{V}(\theta_j|\mathbf{n}) = \frac{n_j(N - n_j) + \frac{1}{4}(N + s)(s + 1)^2}{(N + s)(N + s + 1)^2}
$$
Provided $s \geqslant 1$.

$$
\underline{V}(\theta_j|\mathbf{n}) = \frac{n_j(N - n_j) + s\min\{n_j, N - n_j\}}{(N + s)^2(N + s + 1)}
$$
*(p.17)*

### Predictive Probability for Two Future Trials

$$
P[(A, B)|\mathbf{n}] = E\{P[(A, B)|\boldsymbol{\theta}]|\mathbf{n}\} = \frac{\{n(A) + s\,t(A)\}\{n(B) + s\,t(B)\} + n(A \cap B) + s\,t(A \cap B)}{(N + s)(N + s + 1)}
$$
Where $t(C) = \sum_{\omega_j \in C} t_j$.
*(p.13)*

### Upper and Lower Probabilities for Joint Events (Two Trials)

$$
\alpha\,\underline{P}[(A,B)|\mathbf{n}] = \begin{cases} n(A)\,n(B) + n(A \cap B) & \text{if } A \cup B \neq \Omega \\ n(A)\,n(B) + n(A \cap B) + s\min\{n(A), n(B)\} & \text{if } A \cup B = \Omega \end{cases}
$$
Where $\alpha = (N+s)(N+s+1)$.
*(p.14)*

### Beta-Binomial CDF for Future Successes

$$
P(Y = i|\mathbf{n}) = \binom{M}{i} \frac{B(\alpha + x + i,\ \beta + N - x + M - i)}{B(\alpha + x,\ \beta + N - x)}
$$
For $i = 0, 1, \ldots, M$, where $Y$ is the number of occurrences of $A$ in $M$ future trials, $x = \sum_{\omega_j \in A} n_j$, $\alpha = s\,t(A)$, $\beta = s - s\,t(A)$.
*(p.14)*

### Upper and Lower CDFs for Future Successes

$$
\overline{P}(Y \leqslant y|\mathbf{n}) = \sum_{i=0}^{y} \binom{M}{i} \frac{B(x + i,\ s + N - x + M - i)}{B(x,\ s + N - x)}
$$

$$
\underline{P}(Y \leqslant y|\mathbf{n}) = \sum_{i=0}^{y} \binom{M}{i} \frac{B(s + x + i,\ N - x + M - i)}{B(s + x,\ N - x)}
$$
Except when $x = 0$ ($\overline{P} = 1$ for all $y$) or $x = N$ ($\underline{P} = 0$ for $y < M$, 1 for $y = M$).
*(p.15)*

### Hypothesis Testing Posterior Probabilities

For $H_0: \theta_R \geqslant \frac{1}{2}$ with data $n_R = 1, N = 6, s = 2$:

$$
\underline{P}(H_0|\mathbf{n}) = \int_{1/2}^{1} 7(1-\theta)^6\,\mathrm{d}\theta = 2^{-7} = 0.00781
$$

$$
\overline{P}(H_0|\mathbf{n}) = \int_{1/2}^{1} 105\theta^2(1-\theta)^4\,\mathrm{d}\theta = 29 \times 2^{-7} = 0.227
$$
*(p.23)*

### Imprecise Beta Model (Two-Parameter Case)

Prior densities for $(\theta_c, \theta_e)$:

$$
\pi(\theta_c, \theta_e) \propto \theta_c^{st_c - 1}(1-\theta_c)^{s(1-t_c)-1}\theta_e^{st_e - 1}(1-\theta_e)^{s(1-t_e)-1}
$$
Where $s > 0$, $0 < t_c < 1$, $0 < t_e < 1$, with $s$ fixed and $t_c, t_e$ ranging freely.
*(p.27)*

### Decision Criteria for Treatment Preference

$$
\underline{E}(\psi|\mathbf{n}) = \underline{E}(\theta_e|\mathbf{n}) - \overline{E}(\theta_c|\mathbf{n}) = \frac{9}{s+9} - \frac{s+6}{s+10}
$$

$$
\overline{E}(\psi|\mathbf{n}) = \overline{E}(\theta_e|\mathbf{n}) - \underline{E}(\theta_c|\mathbf{n}) = \frac{s+4}{s+10}
$$
Where $\psi = \theta_e - \theta_c$ is the treatment difference. ECMO preferred if $\underline{E}(\psi|\mathbf{n}) > 0$. With $s=2$: $\underline{E}(\psi|\mathbf{n}) = 0.152$, $\overline{E}(\psi|\mathbf{n}) = 0.5$.
*(p.29)*

### Stopping Rule for Clinical Trials

$$
\text{prefer treatment 1 if } Y > \kappa_2, \quad \text{prefer treatment 2 if } Y < -\kappa_1, \quad \text{no preference if } -\kappa_1 \leqslant Y \leqslant \kappa_2
$$
Where $\kappa_1 = s/(s+N_1)$, $\kappa_2 = s/(s+N_2)$, $Y = (1-\kappa_1)r_1 - (1-\kappa_2)r_2$, $r_i$ and $N_i$ are relative frequencies and sample sizes. For equal sample sizes: compare $r_1 - r_2$ with thresholds $\beta = s/N_1$ and $-\beta$.
*(p.30)*

### Nonparametric Upper and Lower CDFs (Ordered Categories)

$$
\overline{F}(x) = \overline{P}(X \leqslant x|\mathbf{n}) = \left(\sum_{j=1}^{i} n_j + s\right) / (N + s)
$$

$$
\underline{F}(x) = \underline{P}(X \leqslant x|\mathbf{n}) = \sum_{j=1}^{i-1} n_j / (N + s)
$$
For $x$ in interval $\omega_i$. These are simple nonparametric inferences not relying on distributional assumptions.
*(p.32)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Hyperparameter (prior strength) | $s$ | - | 2 | $[1, \infty)$ | p.9, 12 | Controls caution; s=1 gives frequentist agreement, s=2 recommended as reasonably cautious |
| Prior mean vector | $\mathbf{t}$ | - | - | Simplex: $0<t_j<1$, $\sum t_j=1$ | p.9 | Ranges freely over full simplex in IDM |
| Number of categories | $k$ | - | - | $\geqslant 2$ | p.8 | Must be finite; inferences do not depend on $k$ |
| Sample size | $N$ | - | - | $\geqslant 0$ | p.8 | Total number of observations |
| Category counts | $n_j$ | - | - | $[0, N]$ | p.8 | Non-negative integers summing to $N$ |
| Posterior parameter | $t_j^*$ | - | - | $(0, 1)$ | p.9 | $t_j^* = (n_j + st_j)/(N+s)$ |
| Imprecision | - | - | - | $(0, 1)$ | p.10 | $s/(N+s)$; independent of event $A$ |

## Methods & Implementation Details
- The IDM is defined as the set $\mathscr{M}_0$ of all Dirichlet$(s, \mathbf{t})$ distributions with $s$ fixed and $\mathbf{t}$ ranging over the open simplex *(p.9)*
- Upper/lower probabilities are computed by optimizing predictive probability $P(A_j|\mathbf{n}) = t_j^* = (n_j + st_j)/(N+s)$ over $t_j \in (0,1)$ *(p.9-10)*
- For events not yet observed ($n(A)=0$): $\underline{P}(A|\mathbf{n})=0$ and $\overline{P}(A|\mathbf{n})=s/(N+s) \to 0$ as $N \to \infty$ *(p.13)*
- When $s$ is an integer, $\overline{P}(H_0|\mathbf{n})$ for hypotheses can be computed as cumulative hypergeometric probabilities *(p.28)*
- The imprecise beta model generalizes to $k=2$ (Bernoulli) with product-of-betas priors for comparing treatments *(p.26-27)*
- Credible intervals: one-sided $\gamma$ credible interval $I = [0, \theta^*]$ where $\theta^*$ solves $G(\theta^*) = \gamma$ with $G$ the beta CDF; two-sided equitailed intervals by replacing $\gamma$ with $(1+\gamma)/2$ *(p.18)*
- Likelihood intervals $D(\lambda) = \{\theta : \theta^{n_j}(1-\theta)^{N-n_j} \geqslant \lambda\}$; when $s=1$, $Q\{D(\lambda), 0\} = Q\{D(\lambda), 1\}$ (remarkable property) *(p.19)*
- For the ECMO example with $s=2$: $\overline{P}(H_1|\mathbf{n}) \approx 1$ (always), $\underline{P}(H_1|\mathbf{n}) = 0.815$ *(p.27)*

## Figures of Interest
- **Fig 1 (p.29):** Posterior upper and lower CDFs for $\psi = \theta_e - \theta_c$ under the imprecise beta model with $s=2$, showing the gap between upper and lower CDFs representing imprecision in the treatment comparison

## Results Summary
- For the marbles example (1 red in 6 draws, $s=2$): $\overline{P}(R|\mathbf{n})=0.375$, $\underline{P}(R|\mathbf{n})=0.125$. The odds against red are between 5:3 and 7:1 *(p.20)*
- Bayesian methods produce $P(R|\mathbf{n})$ ranging from 0.179 to 0.333 depending on sample space choice, all within the IDM interval *(p.20, Table 1)*
- 95% credible intervals from various Bayesian priors have posterior lower probabilities ranging 0.80-0.97, but the IDM likelihood interval has posterior probability exactly 0.95 *(p.22, Table 2)*
- For ECMO vs CT: $\underline{P}(H_1|\mathbf{n}) = 0.815$ with $s=2$, meaning strong evidence ECMO is more effective. With $s=1$: $\underline{P}(H_1|\mathbf{n}) = 0.9458$, equal to Fisher's exact test p-value *(p.27-28)*
- Decision analysis: ECMO should be preferred for the next patient ($\underline{E}(\psi|\mathbf{n}) = 0.152 > 0$); continuing randomization would be unethical *(p.29-30)*

## Limitations
- The choice of $s$ is not uniquely determined; $s=1$ and $s=2$ are both reasonable but give different conclusions *(p.12)*
- The IDM does not address the case where prior information exists (though the imprecise beta model partially does) *(p.26)*
- Upper probability $\overline{P}(A|\mathbf{n})$ does not depend on the number of distinct observed categories when $n(A)=0$ and $N$ is fixed, which may seem unreasonable in some contexts *(p.13)*
- For ordered categories, the extension to continuous distributions requires further investigation *(p.32)*
- The model produces non-vacuous prior probabilities for some observable events involving more than one future trial, which may be seen as a limitation *(p.14)*

## Arguments Against Prior Work
- Bayesian methods using a single symmetric Dirichlet prior violate the RIP: $P(A|\mathbf{n})$ depends on the choice of sample space $\Omega$ *(p.5-6, 11)*
- The principle of indifference is inapplicable when the sample space is unknown or arbitrary *(p.4-5)*
- Bayesian inferences from different "objective" priors (uniform, Jeffreys, Haldane) are mutually inconsistent, differing by a factor of nearly 3 in the same example *(p.24)*
- Frequentist methods cannot draw conclusions without knowing the stopping rule *(p.24-25)*
- Haldane's improper prior ($s=0$) generates unreasonable posteriors: after observing one red marble, it implies odds of 1 million to 1 on red for the next draw *(p.11)*

## Design Rationale
- Using a SET of Dirichlet priors rather than a single prior is justified by the impossibility of simultaneously satisfying embedding and symmetry with any single distribution *(p.5)*
- The parameter $s$ is separated from $\mathbf{t}$ because $s$ determines the rate of learning while $\mathbf{t}$ is what we are ignorant about *(p.9)*
- Dirichlet priors are chosen because: (a) conjugacy with multinomial, (b) closure under category combination (ensuring RIP), (c) rich enough to approximate any prior via convex hulls, (d) standard choice for Bayesian prior ignorance *(p.9)*
- $s=2$ recommended because: encompasses three standard Bayesian priors (uniform, Jeffreys, Haldane), encompasses frequentist confidence intervals for two-sided tests, and is reasonably cautious *(p.12)*
- The vacuous probability model ($\underline{P}=0$, $\overline{P}=1$) is the unique coherent model satisfying both embedding and symmetry for complete ignorance *(p.5)*

## Testable Properties
- $\overline{P}(A|\mathbf{n}) - \underline{P}(A|\mathbf{n}) = s/(N+s)$ for all non-trivial events $A$ *(p.10)*
- Upper and lower probabilities must not depend on sample space $\Omega$ (RIP) *(p.6, 16)*
- Upper and lower probabilities must not depend on stopping rule (likelihood principle) *(p.8)*
- For $s=1$: equitailed credible intervals agree with Clopper-Pearson confidence intervals *(p.12)*
- For $s=1$: $\overline{P}(H_0|\mathbf{n})$ equals Fisher's exact test p-value *(p.28)*
- For $s \geqslant 1$: one-sided credible intervals are also one-sided $\gamma$ confidence intervals in the frequentist sense *(p.15)*
- Imprecision decreases monotonically with $N$: $s/(N+s)$ *(p.10)*
- When $n(A)=0$: $\underline{P}(A|\mathbf{n})=0$ for all $N$ (never bet on an unobserved event) *(p.13)*
- When $N=0$ (no data): $\overline{P}(A)=1$ and $\underline{P}(A)=0$ for all non-trivial $A$ (vacuous) *(p.10)*
- $\overline{P}(A|\mathbf{n}) + \overline{P}(A^c|\mathbf{n}) = 1 + s/(N+s) > 1$ (superadditivity of upper probability) *(p.10)*

## Relevance to Project
This paper is foundational for propstore's uncertainty representation. The IDM directly grounds Josang's subjective logic opinions: the parameter $s$ corresponds to the non-informativeness prior weight $W$ in Josang (2001), and the IDM's upper/lower probabilities map to belief and plausibility. The evidence-to-opinion mapping in propstore (Sensoy et al. 2018 implementation) uses Dirichlet distributions parameterized exactly as Walley describes. The IDM's vacuous state ($\overline{P}=1$, $\underline{P}=0$ when $N=0$) corresponds to Josang's vacuous opinion $(b=0, d=0, u=1)$. The imprecision measure $s/(N+s)$ directly maps to uncertainty $u$ in subjective logic.

## Open Questions
- [ ] What is the exact relationship between Walley's $s$ and Josang's $W$ parameter? (Likely $s = W$)
- [ ] Can the IDM's RIP be verified in the propstore implementation?
- [ ] Should the imprecise beta model (Section 5.3) be implemented for comparing treatments/stances?
- [ ] How does the IDM relate to Dempster-Shafer theory? (Walley notes agreement with Dempster (1966) and Smets (1994) when $s=1$)

## Related Work Worth Reading
- Walley (1991) *Statistical Reasoning with Imprecise Probabilities* - the comprehensive monograph grounding this paper's theory
- Good (1962, 1965, 1983) - Bayesian inferences from multinomial data using mixtures of Dirichlet distributions
- Dempster (1966) - posterior distributions from multinomial data; IDM with $s=1$ agrees
- Smets (1994) - belief functions from multinomial data; agrees with IDM when $s=1$
- Walley et al. (1995) - application of imprecise prior probabilities to clinical data analysis
- Carnap (1950, 1952) - inductive logic framework; IDM may solve Carnap's problem of choosing a "continuum of inductive methods"

## Collection Cross-References

### Already in Collection
- [[Shafer_1976_MathematicalTheoryEvidence]] -- Dempster-Shafer theory; Walley cites Dempster (1966) extensively and shows IDM with s=1 agrees with Dempster's method for multinomial data

### New Leads (Not Yet in Collection)
- Walley (1991) "Statistical Reasoning with Imprecise Probabilities" -- the comprehensive monograph grounding all theory in this paper; essential reference for coherent upper/lower probabilities
- Good (1962, 1965) "Subjective probability / The Estimation of Probabilities" -- Bayesian inferences from multinomial data using Dirichlet mixtures; closest Bayesian analogue to IDM
- Smets (1994) "Belief induced by the knowledge of the probabilities" -- belief functions from multinomial data; agrees with IDM when s=1
- Dempster (1966) "New methods for reasoning towards posterior distributions" -- foundational paper; IDM with s=1 agrees

### Cited By (in Collection)
- [[Josang_2001_LogicUncertainProbabilities]] -- cites Walley (1991) for the theory of imprecise probabilities grounding subjective logic's uncertainty representation
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] -- cites Walley in context of imprecise probability decision criteria
- [Subjective Logic: A Formalism for Reasoning Under Uncertainty](../Josang_2016_SubjectiveLogic/notes.md) -- cites Walley 1996 as book reference [98]; the IDM is presented as a baseline that subjective logic generalises by adding a base-rate distribution. The book criticises IDM upper/lower probabilities as not being literal bounds (p.85, 9-red-1-black-bag counterexample), recommending interpretation as "rough probability interval."

### Conceptual Links (not citation-based)
**Uncertainty representation and evidence-to-opinion mapping:**
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] -- Sensoy's Dirichlet parameterization of neural network outputs directly implements the evidence-to-Dirichlet mapping that Walley's IDM formalizes; evidence counts in Sensoy map to Walley's observation counts n_j, and the prior weight maps to s
- [[Josang_2001_LogicUncertainProbabilities]] -- Josang's subjective logic opinions are a direct application of Walley's framework: the W parameter in the Beta-opinion bijection corresponds to Walley's s, and the vacuous opinion (b=0,d=0,u=1) is exactly Walley's vacuous probability model
- [[Kaplan_2015_PartialObservableUpdateSubjectiveLogic]] -- Kaplan's Dirichlet moment-matching for partial observations extends the same Dirichlet updating framework that Walley formalizes for the complete-observation case
- [[Vasilakes_2025_SubjectiveLogicEncodings]] -- SLEs encode annotations as Dirichlet distributions via SL opinions, directly building on the Dirichlet-based uncertainty framework Walley established

**Belief functions and decision-making under imprecision:**
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] -- Denoeux's review of decision criteria under belief functions directly applies to the decision problems Walley solves in Section 5 (clinical trial termination); the pignistic transformation and E-admissibility criteria are alternatives to Walley's direct upper/lower expectation approach
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] -- BMS propagates Dempster-Shafer beliefs through dependency networks; Walley's IDM provides the foundational inference model for how those beliefs should be formed from data

**Multi-source fusion:**
- [[vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic]] -- van der Heijden proves WBF equivalence to confidence-weighted averaging of Dirichlet distributions; Walley's IDM provides the principled starting point (prior ignorance) from which those Dirichlet distributions are built
- [[Margoni_2024_SubjectiveLogicMetaAnalysis]] -- Margoni's use of SL for meta-analysis builds on the evidence-to-opinion pipeline that traces back to Walley's IDM as the foundational model for learning from data under prior ignorance

---

**See also (conceptual link):** [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — Walley notes IDM agrees with Smets' belief-function inference at `s=1`. The 1994 paper is the canonical TBM exposition; its sharp dissociation from underlying probability contrasts with Walley's coherent imprecise-probability programme — sibling responses to the same epistemic problem from different formal traditions.
