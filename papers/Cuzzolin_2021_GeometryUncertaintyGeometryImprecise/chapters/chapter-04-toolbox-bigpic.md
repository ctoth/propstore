# Chunk #4 — Chapter 5 (A toolbox for the working scientist) + Chapter 6 (The bigger picture)

**Book pages:** 237-322 (chunk also catches pdf-256 = p.235 tail of Ch.4)
**PDF idx:** 256-353

## Sections covered

- (Ch.4 tail, p.235) §4.10 mathematics of belief functions — final paragraphs only (handled by chunk #3).
- §5 (p.237) chapter intro — machine learning, estimation, prediction, time series, optimisation.
- §5.1 Clustering (p.238-243): 5.1.1 Fuzzy/evidential/belief C-means (ECM, BCM, RECM, CECM, SECM, CCM, MECM); 5.1.2 EVCLUS and later developments (Ek-NNclus, Belief K-modes); 5.1.3 Clustering belief functions (Schubert metaconflict).
- §5.2 Classification (p.244-...): 5.2.1 Generalised Bayesian; 5.2.2 Evidential k-NN; 5.2.3 TBM model-based; 5.2.4 SVM classification; 5.2.5 Partial training data; 5.2.6 Decision trees; 5.2.7 Neural networks; 5.2.8 Other classification approaches.
- §5.3 Ensemble classification.
- §5.4 Ranking aggregation.
- §5.5 Regression: 5.5.1 fuzzy-belief non-parametric; 5.5.2 belief modeling regression.
- §5.6 Estimation, prediction, identification: 5.6.1 state estimation; 5.6.2 time series; 5.6.3 particle filtering; 5.6.4 system identification.
- §5.7 Optimisation.
- §6 Imprecise probability and the bigger picture.
- §6.1 Imprecise probabilities: lower/upper, gambles, lower/upper previsions, indicator gambles, rules of rational behaviour, natural extension, BFs and IP.
- §6.2 Capacities / fuzzy measures.
- §6.3 Probability intervals as 2-monotone capacities.
- §6.4 Higher-order probabilities.
- §6.5 Fuzzy theory.
- §6.6 Logic frameworks (Saffiotti, Josang's subjective logic, Fagin-Halpern, probabilistic argumentation, default logic, Ruspini, modal logic, probability of provability).
- §6.7 Rough sets.
- §6.8 Probability boxes.
- §6.9 Spohn's epistemic beliefs / disbelief functions / α-conditionalisation.
- §6.10 Zadeh's GTU.
- §6.11 Liu's uncertainty theory.
- §6.12 Info-gap decision theory.
- §6.13 Vovk-Shafer game-theoretic framework.
- §6.14 Other formalisms (endorsements, fril-fuzzy, granular computing, Laskey, Harper, Shastri, evidential confirmation, Groen, Padovitz, similarity-based, neighbourhood systems, comparative belief structures).

## Chapter overview

Chapter 5 catalogues belief-function generalisations of the standard machine-learning toolbox: clustering (credal partitions, ECM/BCM/EVCLUS/Ek-NNclus), classification (Generalised Bayesian, evidential k-NN, TBM model-based, SVM, decision trees, evidential neural networks), ensembles, ranking, regression, estimation/filtering, system identification, and optimisation. Each algorithm is presented as the analogue of a classical method but with mass functions / belief functions as either inputs, outputs, or internal carriers of uncertainty. The chapter is a working scientist's tour of "what already exists" so later chapters can position the geometric-belief programme.

Chapter 6 is the comparative landscape. Cuzzolin places belief theory beside every other competing imprecise-probability formalism and traces the relationships: Walley's lower/upper previsions and gambles (the canonical IP framework); capacities / fuzzy measures; 2-monotone probability intervals; higher-order probabilities (probabilities of probabilities, Gaifman/Kyburg/Fung-Chong); fuzzy theory and possibility theory; logic-flavoured frameworks (Saffiotti, Josang's subjective logic, Fagin-Halpern's algebra, probabilistic argumentation, Ruspini's logical foundations, modal logic); rough sets; p-boxes; Spohn's ranking functions; Zadeh's GTU; Liu's uncertainty theory; info-gap decision theory; Vovk-Shafer's game-theoretic probability; and a long tail of less-mainstream formalisms. For each formalism Cuzzolin gives axioms/definitions, the relationship to belief functions, and key citations. This is the chapter that propstore must engage with when justifying any of its formal commitments.

## Definitions and key formulas — Chapter 5

### Credal partition (p.238)

A *credal partition* is $M = (m_1, \ldots, m_n)$, i.e., one mass function per object over the frame $\Omega = \{\omega_1, \ldots, \omega_c\}$ of clusters, mapping $2^\Omega \to [0,1]$ for each object. Generalises fuzzy, possibilistic, and rough partitions.

### ECM cost function (p.239)

$$
\sum_{i=1}^n \sum_{j=1}^f |A_j|^\alpha (m_i(A_j))^\beta d^2(\mathbf{x}_i, \bar{\mathbf{v}}_j) + \delta^2 \sum_{i=1}^n (m_i(\emptyset))^\beta
$$
**(p.239)** Where: $\bar{\mathbf{v}}_j$ is the prototype of focal-set cluster $A_j$; $d$ Euclidean distance in $\mathbb{R}^p$; $\alpha$ controls specificity (penalty on size of $A_j$); $\beta$ controls 'hardness' of credal partition; $\delta^2$ controls outlier proportion. Coordinate descent alternates between prototypes and credal partition.

### Belief C-means (BCM) (p.240)
Liu et al. [657]: objects in the middle of specific clusters get equal belief on each specific cluster; outliers committed to disjunctive meta-cluster; mass of meta-cluster computed using both object-to-centre distances and centre-to-centre distances.

### ECM variants (p.240)
- **RECM** (relational ECM, [1263]) — proximity data input.
- **CECM** (constrained, [46]) — pairwise must-link/cannot-link.
- **SECM** (spatial, [1131]) — image segmentation.
- **CCM** (credal, [659]) — different vector-to-meta-cluster distance.
- **MECM** (median, [2120]) — median variant of fuzzy C-means.
- **ECM with adaptive metrics** [47] — non-spherical clusters.

### EVCLUS (p.240)
Input: $n \times n$ dissimilarity matrix. Each pair $(i,j)$ gets mass $m_{ij}$ on $\{S, NS\}$ frame (same group / not same group). Pairwise plausibility of belonging to same group:
$$
1 - k_{ij} = \sum_{A \cap B \neq \emptyset} m_i(A) m_j(B)
$$
Cost: minimise $\sum_{i<j} (k_{ij} - \phi(d_{ij}))^2$ with $\phi$ increasing $[0,\infty) \to [0,1]$, e.g., $\phi(d) = 1 - \exp(-\gamma d^2)$. Extended to interval-valued dissimilarities [1261].

### E2GK (p.240) — evidential evolving Gustafson-Kessel — online clustering.

### Ek-NNclus (p.241)
Frame $\mathcal{R}$ = all equivalence relations on $n$ objects. Mass $m_{ij}(\{S\}) = \phi(d_{ij}), m_{ij}(\{S,NS\}) = 1 - \phi(d_{ij})$ vacuously extended to $\mathcal{R}$. Combined contour function:
$$
pl(R) \propto \prod_{i<j} (1 - \phi(d_{ij}))^{1-r_{ij}}, \quad R \in \mathcal{R}
$$
where $r_{ij} = 1$ if $o_i, o_j$ in same group. Maximising log-contour = binary linear program; for large $n$, **Algorithm 11** does heuristic greedy search via Ek-NN rule.

### Belief K-modes (BKM, Algorithm 12, p.242)
Each object has $s$ attribute values $x_i \in \Theta_i$; learning input: $K$, BPAs $m_{\Theta_j}[\mathbf{x}_i]$. Mode of cluster:
$$
m_{\Theta_j}[Q_k](A_j) = \frac{\sum_{i=1}^{|C_k|} m_{\Theta_j}[\mathbf{x}_i](A_j)}{|C_k|}
$$
Distance: $D(\mathbf{x}, Q) = \sum_{j=1}^s d(m_{\Theta_j}[\mathbf{x}], m_{\Theta_j}[Q])$ (Euclidean on mass vectors).

### Ensemble clustering [1264] (p.242)
Belief functions on lattice of interval partitions; combine via combination rule; consensus partition.

### Schubert clustering of belief functions (§5.1.3, p.243)
Cluster $2^n - 1$ pieces of evidence into $n$ clusters by minimising metaconflict. Frame $\Theta = \{\text{AdP}, \neg \text{AdP}\}$ with $m_i(\neg \text{AdP}) \doteq \kappa(\oplus Bel_k, k \in \Pi_i)$. Metaconflict:
$$
1 - (1 - c_0) \prod_i (1 - \kappa_i) \quad (5.1, p.243)
$$
where $c_0$ = conflict between hypothesised number of clusters and prior, $\kappa_i$ = pairwise conflict in cluster $i$. Reduces to a Potts model [1960].

### Generalised Bayesian classifier (§5.2.1, p.244)
Lower / upper expected loss after observing $\mathbf{x}$:
$$
\underline{E}_i(\mathbf{x}) = \sum_{j=1}^C \lambda(\theta_i | \theta_j) Bel(\theta_j | \mathbf{x}), \quad \overline{E}_i(\mathbf{x}) = \sum_{j=1}^C \lambda(\theta_i | \theta_j) Pl(\theta_j | \mathbf{x})
$$
**(p.244)** Decision rules: minimum upper expected loss $\hat{\theta}(\mathbf{x}) = \theta_i$ if $\overline{E}_i \le \overline{E}_j \forall j \neq i$; or minimum lower expected loss (analogous). Origin: Kim-Swain [968], multisource classification with class densities/priors as belief functions in partly consonant form (Shafer's likelihood-based proposal).

### Evidential k-NN classifier (Denoeux-Zouhal, [443, 456], p.245)
Each $\mathbf{x}_i \in \mathcal{N}_k(\mathbf{x})$ is a piece of evidence with mass on $\Theta$:
$$
m_i(\{y_i\}) = \varphi(d_i), \quad m_i(\Theta) = 1 - \varphi(d_i)
$$
$\varphi$ is a decreasing function with $\varphi(d) \to 0$ as $d \to \infty$. Combine: $m = \bigoplus_{\mathbf{x}_i \in \mathcal{N}_k(\mathbf{x})} m_i$. Family $\{\varphi_\lambda | \lambda \in \Lambda\}$, e.g. cross-validation, parameterises selection. Class with highest plausibility wins.

**Fuzzy extension** (p.245) — class membership is a fuzzy set; transformed either to consonant belief function or to general focal-element BFs.

**Evidential k-NN with partial supervision** (p.246) — training set $\mathcal{T} = \{(\mathbf{x}_i, m_i)\}$ where $m_i$ is a mass function on classes; supervised iff $m_i(\{\theta_{j_i}\}) = 1$, unsupervised iff $m_i(\Theta) = 1$. Discount each:
$$
m'_i(A) = \varphi(d_i) m_i(A), \quad m'_i(\Theta) = 1 - \sum_{A \subset \Theta} m'_i(A)
$$

### TBM model-based classifier (§5.2.3, p.246-247)
Builds on Generalised Bayesian Theorem (GBT). Conditional mass $m_\mathbb{X}[\theta_j]: 2^\mathbb{X} \to [0,1]$ given class. Steps: (1) ballooning extension of conditional BPAs to $\mathbb{X} \times \Theta$; (2) conjunctive combination; (3) Dempster conditioning on $\Theta \times \{\mathbf{x}\}$; (4) marginalisation on $\Theta$. Result [1689]:
$$
m_\Theta[\mathbf{x}](A) = \prod_{\theta_j \in A} Pl_\mathbb{X}[\theta_j](\mathbf{x}) \prod_{\theta_j \in A^c}(1 - Pl_\mathbb{X}[\theta_j](\mathbf{x})), \quad A \subset \Theta
$$
Two flavours: TBM model-based vs TBM case-based (= evidential k-NN). Both reduce to a kernel rule for precise/categorical training data.

### SVM classification (Liu-Zheng [1207], §5.2.4, p.247-248)
For multiclass via one-vs-all $C$ classifiers $\text{SVM}_j$ with decision $f_j$. For positive ($y_{f_j}=1$):
$$
m_j(A) = \begin{cases} 1 - \exp(-|f_j(\mathbf{x})|) & A = \{\theta_j\} \\ \exp(-|f_j(\mathbf{x})|) & A = \Theta \\ 0 & \text{otherwise} \end{cases}
$$
For negative ($y_{f_j}=0$): $A=\{\theta_j\}^c$ instead of $\{\theta_j\}$. Combine via Dempster's rule. Decision: $\arg\max_j Bel(\{\theta_j\})$ collapses to $\arg\max_j f_j(\mathbf{x})$. Reliability measures: SRM (static, constant), DRM (dynamic, location-dependent).

### Classification with partial training data (§5.2.5, p.248)
- Denoeux 1997 [444] — small/incomplete training sets.
- Côme et al. 2009 [303,304] — soft labels via mass on classes; mixture model + EM-generalised likelihood.
- Vannoorenberghe-Smets credal EM (CrEM) [1848].
- Tabassian et al. [1793,1794] — relabel by ambiguity, MLP learns new labels.

### Decision trees (§5.2.6, p.249-250)
Standard Shannon-entropy info gain:
$$
\text{Info}(\mathcal{T}) \doteq -\sum_{c \in \Theta} p_c \log_2 p_c \quad (5.2, p.249)
$$
$$
\text{Info}_A(\mathcal{T}) = \sum_{a \in \text{range}(A)} \frac{|\mathcal{T}_{A=a}|}{|\mathcal{T}|} \text{Info}(\mathcal{T}_{A=a}) \quad (5.3, p.249)
$$
**Belief decision trees** (Elouedi et al., [573,570,571]) — leaf nodes carry BPA over classes. Algorithm 13 (BDT averaging training, p.250): per-instance pignistic $BetP[\mathbf{x}]$ on each split; entropy of average; pick attribute with highest gain.

**Aggregation (Denoeux-Bjanger [467])** uses Klir's composite uncertainty measure (4.14) on:
$$
m_\Theta(\theta_c) = \frac{n_c(t)}{n(t)+1}, \quad m_\Theta(\Theta) = \frac{1}{n(t)+1}
$$
where $n_c(t)$ = samples with class $c$ in split, $n(t) = |\mathcal{T}|$. Vannoorenberghe-Denoeux 2002 [1847] — multiclass via two-class coarsenings + averaging operator. Trabelsi 2016 [1822] — uncertainty at attribute-value level; pruning [1825].

### Neural networks (§5.2.7, p.251)
Denoeux 2000 [448] — adaptive version of evidential k-NN: reference patterns are prototypes in an MLP hidden layer; outputs combined via Dempster's rule. Connectionist view [1436] = neural net with one input layer, two hidden layers, one output layer; reduced to nearest neighbours mitigates complexity. Fig.5.3 architecture. Trainable to recover best prototypes ([448] §III-C).

Binaghi et al. [155] — neural fuzzy DS classifier: learning task = search for fuzzy aggregation operators + BPAs.

Loonis [1212] — empirical comparison NN multiclassifier fusion vs Dempster's rule. Giacinto et al. [683] — earthquake risk evaluation. Fay et al. [593] — hierarchical NNs with belief outputs at different abstraction levels; ramp function normalises non-fuzzy-kNN classifier outputs into BPAs; discounting weakens insular strong responses.

### Other classification approaches (§5.2.8, p.252-254)
- **Bloch (1996, [171])** — multisource sensing: max-belief, max-plausibility, absolute rule [1785], Wesley's $\arg\max (Bel(A)+Pl(A))/2$ [1927].
- **Le Hégarat-Mascle, Bloch, Vidal-Madjar (1997, [1106])** — DS for unsupervised classification in multisource remote sensing.
- **Modified Dempster-Shafer (MDS), Fixsen-Mahler [623,624]** — incorporates Bayesian priors; reduces to Bayes under strong independence.
- **Fuzzy DS rule-based, Binaghi-Madella [156]** — empirical learning of fuzzy DS classification rules.
- **ICM (Foucher et al. [638])** — iterated conditional mode for image MAP using local belief-theoretic relaxation.
- **Credal bagging (François et al. [641])** — bootstrap $B$ training sets, evidential k-NN per bag, aggregate at credal level:
$$
m_B(A) = \frac{1}{B} \sum_{b=1}^B m_b(A)
$$
Aggregation via averaging on credal level instead of majority vote.
- **PDESCS (Zhu-Basir [2127])** — proportional difference evidence structure for class scores $s_1 \ge \cdots \ge s_n$:
$$
m(\{c_1, \ldots, c_j\}) = \frac{s_j - s_{j+1}}{s_1} \quad (5.4, p.253)
$$
Combined via Dempster's rule; under max-commonality decision = Bayesian MAP.
- **Erkmen-Stephanou [577]** — fractal-based BFs.
- **Lefevre-Colot [1124,1117]** — DS classification with attenuation factor based on dissimilarity between probability distributions.
- **Vannoorenberghe [1846]** — derives Appriou's separable [51] and evidential k-NN from minimisation of lower / pignistic expected loss.
- **Perry-Stephanou [1421]** — classify aggregates of BFs via divergence to prototype aggregates; fuzzy epitome coefficients.
- **Dempster-Chiu [427]** — uncertain-input/uncertain-output classification, marginal BFs over class subsets.
- **Trabelsi et al. [1823,1824]** — rough-set classification under uncertain decision attribute values modelled by BFs.
- **Fiche et al. [610,609]** — fitting α-stable feature distributions, mass via GBT.

## §5.3 Ensemble classification (p.254-)

Multiclass SVM [1207] is a special case. Xu-Krzyzak-Suen 1992 [1997] — first systematic study of combination methods. Fig.5.4 — feature extractor → classifiers $e_1, \ldots, e_N$ → combination. Combination rules (Dempster's especially) lend themselves naturally.

### Xu's distance-based approach (§5.3.1, p.255)
Frame $\Theta$, classifier $e_k$ outputs class $j_k \in \{1, \ldots, C+1\}$ where $C+1$ = "undecided". For each piece of evidence $e_k$:
$$
m_k(A) = \begin{cases} \epsilon_r^k & A = \{j_k\} \\ \epsilon_s^k & A = \{j_k\}^c \\ 1 - \epsilon_r^k - \epsilon_s^k & A = \Theta \end{cases} \quad (5.5, p.255)
$$
where $\epsilon_r^k, \epsilon_s^k$ = recognition / substitution rates of $k$-th classifier (with $\epsilon_r^k + \epsilon_s^k \le 1$). Vacuous when $j_k = C+1$. Belief and plausibilities of result combination computed; Liu-Zheng [1207] uses $m = m_1 \oplus \cdots \oplus m_K$.

Decision rules (p.256):
1. $E(\mathbf{x}) = m$ if $m = \arg\max_j Bel(\{j\})$, else $C+1$.
2. Same with threshold $Bel(\{m\}) \ge \alpha$.
3. $m = \arg\max_j[Bel(\{j\}) - Bel(\{j\}^c)]$ with threshold.
4. Highest recognition under bounded substitution: $E(\mathbf{x}) = m$ iff $Bel(\{m\}) = \max_j\{Bel(\{j\}) : Bel(\{j\}^c) \le \alpha \forall j\}$.

Drawback: classifier outputs are probability-like, not binary; classifiers vary across classes. Fixed by Ani-Deriche [22]. Zhang-Srihari [2102] use classwise performances $\epsilon_r^k(\{j\}), \epsilon_s^k(\{j\})$ instead of global. Mercier et al. [1281] — hierarchical fusion under TBM.

### Rogova's approach (p.256-257)
$X_j$ = training points of class $j$; $\mathbf{y}_k = f_k(\mathbf{x})$ classifier output; $\bar{f}_k^j = \text{mean}\{f_k(\mathbf{x}), \mathbf{x} \in X_j\}$; proximity $d_k^j = \phi(\bar{f}_k^j, \mathbf{y}_k)$. Pair of BPAs:
$$
m_k^j(\{j\}) = d_k^j, \quad m_k^j(\Theta) = 1 - d_k^j; \quad m_k^{\neg j}(\{j\}^c) = 1 - \prod_{m \neq j} d_k^m, \quad m_k^{\neg j}(\Theta) = \prod_{m \neq j} d_k^m
$$
Combination $\bigoplus_k(m_k^j \oplus m_k^{\neg j})$ → Bayesian after normalisation, $E(\mathbf{x}) = \arg\max_{j} \prod_k \frac{d_k^j \prod_{i \neq j}(1-d_k^i)}{1 - d_k^j[1 - \prod_{i \neq j}(1-d_k^i)]}$. Origin: Mandler-Schurmann 1988 [1241].

### Ani-Deriche (p.257-258)
$N$ classifiers on distinct features $\mathbf{f}^1(\mathbf{x}), \ldots, \mathbf{f}^N(\mathbf{x})$. Evidence:
$$
m_k(\theta_j) = \frac{d_k(\theta_j)}{\sum_{j=1}^C d_k(\theta_j) + g_k}, \quad m_k(\Theta) = \frac{g_k}{\sum_{j=1}^C d_k(\theta_j) + g_k} \quad (5.6, p.257)
$$
where $d_k(\theta_j) = \exp(-\|\mathbf{w}_k^j - \mathbf{y}_k\|^2)$. Combine $z(\theta_j) = m_1(\theta_j) \oplus \cdots \oplus m_K(\theta_j)$. Train $\mathbf{w}_k^j, g_k$ to minimise $\sum_{\mathbf{x} \in \mathcal{T}} \|z(\mathbf{x}) - \mathbf{t}(\mathbf{x})\|^2$.

### Empirical comparison (§5.3.2, p.258)
- Kuncheva [1085] — DS fusion closest to decision template (DT) rule; Bahler-Navarro [73] compared 5 schemes (Dempster-Shafer, Bayesian, BKS, logistic regression). DS improved with non-zero rejection rates.
- Shlien [1644] — Dempster combination of decision trees for higher accuracy.
- Bell [103] — combine SVM/kNN/kNNM mass functions for text categorisation.
- Altnay [33,34] — relative beliefs > accurate joint estimation; dependent classifiers can outperform independent under Dempster's rule.
- Data equalisation [676] — minimise output activation differences.
- Ahmadzadeh-Petrou [15,14] — combining classifiers with different class sets via common refinement.
- Bi [150,151,152] — diversity measures, triplet-and-quartet structures.
- Burger [207] — multiclass SVM fusion via belief.
- Martin-Quidu [1255] — interpret one-vs-one / one-vs-rest decisions as BFs.
- Sannen [1532] — trainable evidential fusion via discounting.
- Aregui-Denoeux [57] — convert novelty (one-class SVM, kernel PCA) into BF.
- Reformat-Yager [1475] — fusion of Dempster's rule + generalised OWA (cf §4.8.1).
- Quost [1452,1451,1453] — t-norm-based combination, parametric family of t-norms.

## §5.4 Ranking aggregation (p.260-261)

Frame: alternatives $O = \{o_1, \ldots, o_n\}$ with unknown linear order $L^*$. $n$ agents propose pairwise comparisons. Tritchler-Lockwood [1826,1265] example p.260 with 4 alternatives $\{A,B,C,D\}$ showing pairwise mass weights (Fig.5.5).

For each pair $(o_i, o_j)$, frame $\Theta_{ij} = \{o_i \succ o_j, o_j \succ o_i\}$ with mass $m^{\Theta_{ij}}(o_i \succ o_j) = \alpha_{ij}$, $m^{\Theta_{ij}}(o_j \succ o_i) = \beta_{ij}$, $m^{\Theta_{ij}}(\Theta_{ij}) = 1 - \alpha_{ij} - \beta_{ij}$. Vacuous extension to $\mathcal{L}_{ij} = \{L : (o_i, o_j) \in L\}$. Combined plausibility:
$$
Pl(L) = \frac{1}{1-\kappa} \prod_{i<j} (1-\beta_{ij})^{\ell_{ij}} (1-\alpha_{ij})^{1-\ell_{ij}}
$$
**(p.261)** Optimise log → integer linear program:
$$
\max_{\ell_{ij} \in \{0,1\}} \sum_{i<j} \ell_{ij} \ln\left(\frac{1-\beta_{ij}}{1-\alpha_{ij}}\right)
$$
subject to transitivity: $\ell_{ij} + \ell_{jk} - 1 \le \ell_{ik}$ and $\ell_{ik} \le \ell_{ij} + \ell_{jk}$ for $i < j < k$.

**Belief Ranking Estimator (BRE)** — Argentini-Blanzieri — unsupervised; expert quality + position uncertainty.

## §5.5 Regression (p.261-264)

### 5.5.1 Fuzzy-belief non-parametric (Petit-Renaud-Denoeux [1423], p.262)
Training data $\mathcal{T} = \{(\mathbf{x}_i, m_i)\}$ where $m_i$ is a *fuzzy belief assignment* (FBA) [447] over continuous $Y$. Predict via instance-based: discount FBAs by distance, conjunctively combine, get $m_Y$; pignistic for median/expectation; upper/lower expectations:
$$
\hat{y}^*(\mathbf{x}) = \sum_{A \in \mathcal{E}} m_Y(A) \sup_{y \in A} y, \quad \hat{y}_*(\mathbf{x}) = \sum_{A \in \mathcal{E}} m_Y(A) \inf_{y \in A} y \quad (5.7, p.262)
$$
Heterogeneous data: numbers, intervals, fuzzy numbers.

Laanaya 2010 [1089] — fuzzy SVM and belief SVM via Vapnik regression on memberships/BFs.

### 5.5.2 Belief modelling regression (Cuzzolin et al. [365,366,370,704], p.262-264)
Originally for object pose estimation. Training poses $q_k \in \mathcal{Q} \subset \mathbb{R}^D$. Sample poses + features:
$$
\tilde{\mathcal{Q}} \doteq \{q_k, k=1,\ldots,T\}, \quad \tilde{\mathcal{Y}} \doteq \{y_i(k), k=1,\ldots,T\} \quad (5.8, p.263)
$$
EM clustering over $N$ training sequences gives $\Gamma_i^j \sim \mathcal{N}(\mu_i^j, \Sigma_i^j)$, $j=1,\ldots,n_i$, → approximate feature space:
$$
\Theta_i \doteq \{\mathcal{Y}_i^1, \ldots, \mathcal{Y}_i^{n_i}\} \quad (5.9, p.263)
$$
Refining map $\rho_i: \mathcal{Y}_i^j \mapsto \tilde{\mathcal{Q}}_i^j \doteq \{q_k \in \tilde{\mathcal{Q}} : y_i(k) \in \mathcal{Y}_i^j\}$ **(5.10, p.263)**. At test time: extract features $y_1, \ldots, y_N$, map to BFs $Bel_1, \ldots, Bel_N$ on $\tilde{\mathcal{Q}}$, conjunctively combine. Estimate:
$$
\hat{q} = \sum_{k=1}^T p(q_k) q_k, \quad p \text{ vertex of } \mathcal{P}[Bel]
$$
Fig.5.6 evidential model. Compared favourably to RVM [1818] and GPR [1464] on $\text{DV}^{54}$ video sequences [704].

## §5.6 Estimation, prediction, identification (p.264-)

### 5.6.1 State estimation (p.264-265)
- **Reece 1997 [1472]** — model-based parameter estimation for noisy processes; weighted opinion pool over real-value intervals; mean-minimum-mean-square-error estimators with correlated noise; multistate frame refining.
- **Rombaut 1999 [1497]** — Petri-net dynamical systems with TBM resolution.
- **Hong 1996 [887]** — belief Petri net evolution.
- **Nassreddine et al. [1338]** — multiple-model state estimation: candidate models with measurement-likelihood masses, expectation w.r.t. pignistic.

### 5.6.2 Time series (p.265)
- **Kalman filter** — Dempster 2001 [423] graphical model + Gaussian belief functions; Smets-Ristic [1733] joint tracking/classification; Mahler [1238] Kalman extensions.
- **Nassreddine [1339]** — nonlinear state estimation via interval-analysis BFs (axis-aligned boxes propagated by interval arithmetic + constraint satisfaction).
- **Ramasso TCF-CMC [1457]** — temporal credal filter with conflict-based model change.
- **Ramasso [1456]** — credal forward / backward / Viterbi for HMMs.
- **Niu-Yang [1359]** — DS regression for time series prediction with iterated multistep-ahead.

### 5.6.3 Particle filtering (p.266)
- **Muñoz-Salinas et al. [1360]** — multitarget tracking, multiple sensor reliability, BFs over particle locations.
- **Reineking [1478]** — particle filtering within DS framework: maintain belief over HMM states via recursive update equations (strict generalisation of Bayesian filtering); importance sampling tractable for large state spaces.

### 5.6.4 System identification (p.266-267)
- **Jraidi-Elouedi [940]** — generalise EM to imperfect attribute values & class labels (TBM).
- **Boukharouba et al. [188]** — piecewise ARX systems via evidential clustering + soft multicategory SVM for polyhedral partition of regressor space.

## §5.7 Optimisation (p.267-268)
- **Limbourg [1165]** — multi-objective evolutionary algorithms (MOEAs) handling epistemic uncertainty as belief functions.
- **Cucka-Rosenfeld 1993 [320]** — DS for relaxation labelling pooling.
- **Perneel 1994 [1419]** — heuristic search via BFs.
- **Chen-Rao [258]** — modified DS for iterative multicriteria design optimisation; satisfaction function combines criteria 0-1.
- **Resconi 1998 [1486]** — Monte Carlo speedup using BF Boltzmann analogue + Harmanec-Klir.
- **Mueller-Piché [1323]** — DS surrogate model selection (response surface).
- **Reformat et al. [1474]** — *belief linear programming* — uncertain LP with BF objective/constraints.

# CHAPTER 6 — THE BIGGER PICTURE (p.269+)

## §6 chapter framing (p.269-271)

Several mathematical theories of uncertainty are competing. Klir 2004 [987] surveyed; Smets [1696,1706] distinguished imprecision vs uncertainty [962]; Desterке et al. [486] unified via 'generalised p-boxes'; Walley's IP [1874,1877], Klir's generalised information theory [987], Zadeh's GTU [2093], Resconi [1484] modal-logic unification.

**Fig.6.1 (p.270)** Hierarchy diagram (adapted from [987]): probability measures → Sugeno λ-measures → belief functions → capacities of order 2 → lower/upper probabilities (top of generality). Side branches: probability of fuzzy events; fuzzy belief functions; fuzzy λ-measures; feasible probability intervals; feasible fuzzy probabilities. **Less general at bottom, more general at top; arrow = top contains bottom as special case.**

Cuzzolin's book thesis (p.269): "most situations do require one to assess the uncertainty associated with set-valued observations, and therefore random sets (and their belief function incarnation) are a fundamental tool."

## §6.1 Imprecise probability (p.271+)

Reference: Walley [1874,1877], Miranda [1292], lower previsions [311].

### §6.1.1 Lower and upper probabilities (p.272)
A *lower probability* $\underline{P}: 2^\Theta \to [0,1]$ [617]; dual upper: $\overline{P}(A) = 1 - \underline{P}(A^c)$.

**Credal set** [1141]:
$$
\mathcal{P}(\underline{P}) = \{P : P(A) \ge \underline{P}(A), \forall A \subseteq \Theta\} \quad (6.1, p.272)
$$

When $\underline{P} = Bel$: $\mathcal{P}(\underline{P})$ = credal set of probabilities consistent with $Bel$ (eq. 3.10).

**Definition 88. (Consistent / 'avoids sure loss')** *(p.272)* — $\underline{P}$ is consistent iff $\mathcal{P}(\underline{P}) \neq \emptyset$, equivalently
$$
\sup_{\theta \in \Theta} \sum_{i=1}^n 1_{E_i}(\theta) \ge \sum_{i=1}^n \underline{P}(E_i) \quad (6.2, p.272)
$$
for any finite $E_1, \ldots, E_n \in \mathcal{F}$.

**Definition 89. (Tight / 'coherent')** *(p.272)* — $\inf_{P \in \mathcal{P}(\underline{P})} P(A) = \underline{P}(A)$, equivalently
$$
\sup_{\theta \in \Theta}\left[\sum_{i=1}^n 1_{E_i}(\theta) - m \cdot 1_{E_0}(\theta)\right] \ge \sum_{i=1}^n \underline{P}(E_i) - m \cdot \underline{P}(E_0) \quad (6.3, p.272)
$$
Coherent ⇒ monotone + superadditive.

### §6.1.2 Gambles and behavioural interpretation (p.273)
Behavioural rationale (de Finetti [403,404]): *belief = inclination to act*; agent believes in outcome to extent willing to accept gamble.

**Definition 90. (Gamble)** *(p.273)* — Bounded real-valued function $X: \Omega \to \mathbb{R}$.

**Definition 91. (Coherent set of desirable gambles)** *(p.273)* $\mathcal{D} \subseteq \mathcal{L}(\Omega)$ coherent iff
1. $0 \notin \mathcal{D}$;
2. $X > 0 \Rightarrow X \in \mathcal{D}$;
3. $X, Y \in \mathcal{D} \Rightarrow X + Y \in \mathcal{D}$;
4. $X \in \mathcal{D}, \lambda > 0 \Rightarrow \lambda X \in \mathcal{D}$.

Convex cone. Fig.6.2 (p.274) shows two gambles $X, Y$ in the cone.

### §6.1.3 Lower/upper previsions (p.273-274)

**Definition 92. (Lower prevision)** *(p.273)* — supremum acceptable buying price:
$$
\underline{P}(X) \doteq \sup\{\mu : X - \mu \in \mathcal{D}\}
$$

**Definition 93. (Upper prevision)** *(p.274)*:
$$
\overline{P}(X) \doteq \inf\{\mu : \mu - X \in \mathcal{D}\}
$$
Duality: $\overline{P}(X) = -\underline{P}(-X)$. When $\overline{P}=\underline{P}=P(X)$, it is the precise *prevision* (de Finetti [403]). Fig.6.3 (p.274) — interval $[\underline{P}(X), \overline{P}(X)]$ = price range where agent undecided.

### §6.1.4 Events as indicator gambles (p.274-275)
$1_A(\omega) = 1$ if $\omega \in A$, else 0. $\underline{P}(A) = \underline{P}(1_A)$, $\overline{P}(A) = \overline{P}(1_A)$.

### §6.1.5 Rules of rational behaviour (p.275)
1. Avoid sure loss (Def 88) for indicator gambles.
2. Coherence (Def 89) for indicator gambles.
Consequence of avoid-sure-loss: $\underline{P}(A) \le \overline{P}(A)$.
Consequence of coherence: subadditivity $\underline{P}(A) + \underline{P}(B) \le \underline{P}(A \cup B)$ for $A \cap B \neq \emptyset$.
Precise prevision $P$ coherent iff: (i) $P(\lambda X + \mu Y) = \lambda P(X) + \mu P(Y)$; (ii) $X > 0 \Rightarrow P(X) \ge 0$; (iii) $P(\Omega)=1$. Coincides with de Finetti.

Special cases of coherent lower/upper previsions: probability measures, de Finetti previsions, 2-monotone capacities, Choquet capacities, possibility/necessity, belief/plausibility, random sets, p-boxes, credal sets, robust Bayesian.

### §6.1.6 Natural and marginal extension (p.275)
*Natural extension* $\mathcal{E}$ of $\mathcal{D}$ = smallest coherent set of desirable gambles containing $\mathcal{D}$, i.e. smallest convex cone with all positive gambles but not zero.

**Definition 94. (Natural extension of $\underline{P}$)** *(p.276)*:
$$
\underline{E}(f) = \sup\Big\{\sum_{i=1}^n \lambda_i \underline{P}(E_i) + c \,\Big|\, f \ge \sum_{i=1}^n \lambda_i 1_{E_i} + c, \, n \ge 0, E_i \subseteq \Omega, \lambda_i \ge 0, c \in \{-\infty, +\infty\}\Big\} \quad (6.4)
$$
For precise $\underline{P}$, $\underline{E}$ = expectation. $\underline{E}(1_A) = \underline{P}(A)$ iff $\underline{P}$ coherent. *Marginal extension* operator [1294] handles aggregation of conditional lower previsions.

### §6.1.7 Belief functions and imprecise probabilities (p.276-277)

**Belief functions as coherent lower probabilities** — Wang-Klir [1912]: on 2-element frame, coherence + complete monotonicity collapse to superadditivity ⇒ any coherent lower probability is a belief measure. On 3-element frame, 2-monotone (coherent) lower probabilities exist that are not 3-monotone (belief). BFs are a special class of coherent lower previsions ([1874] §5.13). Closed under convex combination.

**Natural extension and Choquet integrals** — Wang-Klir [1911]:
$$
\text{Choquet integral } \int f\, d\underline{P} \ge \underline{E}(f) \text{ when } \underline{P} \text{ is a belief measure}
$$
**Proposition 37** *(p.276)*: $\underline{E}(f) \le \int f\, d\underline{P}$ for any $f \in \mathcal{L}$ whenever $\underline{P}$ is a belief measure.

**Conceptual autonomy** — Baroni-Vicig [94]: BFs and coherent lower probabilities have *different roots*; common conceptual basis "doomed to fail" from TBM perspective.
**Proposition 38** *(p.277)*: If $\underline{P}$ is coherent on $|\Theta|=3$, then Möbius inverse $m(\Theta) \ge -1/2$ — illustrates BFs' nonneg-mass property is strictly stronger.

**Kerkvliet 2017 [957]** — recent behavioural interpretation of BFs (PhD thesis).

## §6.2 Capacities (a.k.a. fuzzy measures) (p.277-279)

References: [1910,1782,724]; Choquet 1953 [283]; Sugeno 1974 [1781].

**Definition 95. (Monotone capacity / fuzzy measure)** *(p.277)* — $\mu: \mathcal{F} \to [0,1]$:
1. $\mu(\emptyset) = 0$;
2. $A \subseteq B \Rightarrow \mu(A) \le \mu(B)$;
3. continuity from below: $\mu(\bigcup A_i) = \lim \mu(A_i)$ for increasing $A_i$;
4. continuity from above: $\mu(\bigcap A_i) = \lim \mu(A_i)$ for decreasing $A_i$ with $\mu(A_1) < \infty$.

Finite $\Theta$ ⇒ continuity conditions trivial.

### §6.2.1 Special types of capacities (p.278)

**Definition 96. (Capacity of order $k$)** *(p.278)*:
$$
\mu\Big(\bigcup_{j=1}^k A_j\Big) \ge \sum_{\emptyset \neq K \subseteq [1,\ldots,k]} (-1)^{|K|+1} \mu\Big(\bigcap_{j \in K} A_j\Big) \quad (6.5, p.278)
$$
**Proposition 39** *(p.278)*: Belief functions are infinitely monotone capacities ($k = \infty$).

Möbius:
$$
m(A) = \sum_{B \subseteq A} (-1)^{|A-B|} \mu(B) \quad (6.6, p.278)
$$
For $\infty$-monotone, $m \ge 0$ — same as BPA.

Klir [997] surveys belief vs possibility relations [402,1113]. Yang-style products [821] = unnormalised Dempster combination, satisfy linearity. Yager [2018] — fuzzy measures generated by belief measures provide partial info.

### Sugeno's λ-measures (p.279)
[1782]:
$$
g_\lambda(A \cup B) = g_\lambda(A) + g_\lambda(B) + \lambda g_\lambda(A) g_\lambda(B) \quad (6.7, p.279)
$$
for disjoint $A,B$, $\lambda \in (-1, \infty)$. Determined by $g_\lambda(\theta), \theta \in \Theta$ and:
$$
1 + \lambda = \prod_{\theta \in \Theta} [1 + \lambda g_\lambda(\theta)] \quad (6.8, p.279)
$$
Three cases:
1. $\sum_\theta g_\lambda(\theta) < 1$ → lower probability (superadditive); $\lambda \in (0, \infty)$.
2. $\sum_\theta g_\lambda(\theta) = 1$ → probability; $\lambda = 0$.
3. $\sum_\theta g_\lambda(\theta) > 1$ → upper probability (subadditive); $\lambda \in (-1, 0)$.
Lower/upper λ-measures = special belief/plausibility [135].

**Proposition 40 ([393])** *(p.279)* — feasible probability intervals are Choquet capacities of order 2:
$$
l(A \cup B) + l(A \cap B) \ge l(A) + l(B); \quad u(A \cup B) + u(A \cap B) \le u(A) + u(B) \quad (6.9)
$$

## §6.3 Probability intervals (2-monotone capacities) (p.280-)

**System of probability intervals** [939,1808,393]: $p: \Theta \to [0,1]$ on finite $\Theta$:
$$
\mathcal{P}(l, u) \doteq \{p : l(x) \le p(x) \le u(x), \forall x \in \Theta\} \quad (6.10)
$$
Origin: De Campos, Huete, Moral [393], Tessem [1797]; Hailperin [1955]; Weichselberger [863]. Subclass of credal sets generated by lower/upper probabilities [1673].

**Definition 97. (Feasible)** *(p.280)*: For each $x$ and each $v(x) \in [l(x), u(x)]$, $\exists p$ with $p(x) = v(x)$. Conversion to feasible:
$$
l'(x) = \max\{l(x), 1 - \sum_{y \neq x} u(y)\}, \quad u'(x) = \min\{u(x), 1 - \sum_{y \neq x} l(y)\}
$$
From bounds, lower/upper of subset:
$$
\underline{P}(A) = \max\{\sum_{x \in A} l(x), 1 - \sum_{x \notin A} u(x)\}, \quad \overline{P}(A) = \min\{\sum_{x \in A} u(x), 1 - \sum_{x \notin A} l(x)\} \quad (6.11)
$$
Combination, marginalisation, conditioning operators developed in [393]. Pan [1385] — generalised Bayesian inference on intervals.

### §6.3.1 Probability intervals and belief measures (p.281)

**Proposition 41 ([1134]; [393] Prop.13)** *(p.281)* — minimal probability interval containing $(Bel, Pl)$:
$$
l^*(x) = Bel(x), \quad u^*(x) = Pl(x) \quad (6.12, p.281)
$$
Reverse: when do probability intervals admit a $(Bel, Pl)$ pair? Conditions ([393] Prop.14):
$$
\sum_x l(x) \le 1, \quad \sum_{y \neq x} l(y) + u(x) \le 1 \forall x, \quad \sum_x l(x) + \sum_x u(x) \ge 2
$$
Lemmer-Kyburg [1134] — selection algorithm. BF approximations have only focal elements of size ≤ 2 ([393] Prop.16).

## §6.4 Higher-order probabilities (p.282)

Belief functions ↔ convex sets of probabilities (1-1) when ignoring updating. Ferson [605]: "bounding probability ≠ second-order/two-dimensional probability [831,322]." Cuzzolin's ch.3 §3.1.7 noted the connection: credal sets correspond to indicator-function support on the probability simplex.

References: Savage [580], Gaifman [660], Domotor [505], Jeffrey [891] (higher-order preferences), Skyrms [1660] (HOP essential for belief).

### §6.4.1 Second-order probabilities and belief functions (p.282)
- **Baron [90]** — second-order probability $Q(P)$ = probability that true probability has value $P$. Showed Dempster's rule is special case of HOP rule for combining independent sources. BFs = restriction of full Bayesian.
- **Josang [921]** — bijection Dirichlet distributions ↔ Dirichlet belief functions (focal elements size 1 or $|\Theta|$); link belief reasoning to statistical data.

### §6.4.2 Gaifman's higher-order probability spaces (p.282)
Gaifman 1988 [660]: simple HOP = probability space + operation $PR$ such that $PR(A, \Delta)$ is the event that $A$'s true probability lies in real closed interval $\Delta$. General HOP includes time argument $PR(A, t, \Delta)$. Connections to modal logic.

### §6.4.3 Kyburg's analysis (p.283)
[1087]: HOPs always replaceable by marginals of joint on $I \times \Omega$ where $I$ indexes possible distributions $P_i$. Justification:
$$
P(\omega) = \sum_{i \in I} Q(P_i) P_i(\omega) = E[P_i(\omega)] \quad (\text{p.283})
$$
plus expected utilities. Considered both same-kind HOPs/lower-order, and HOP-as-frequency vs HOP-as-degree-of-belief. Conclusion: no conceptual or computational advantage.

### §6.4.4 Fung-Chong's metaprobability (p.283)
[654]: second-order probability ("metaprobability") provides constraints on beliefs as DS provides constraints on probability masses. Bayes update:
$$
p^2(p | D, Pr) \propto p^2(D | p, Pr) \cdot p^2(p | Pr) \quad (\text{p.283})
$$

## §6.5 Fuzzy theory (p.283-)

Zadeh 1965 [2083] (also Klaua 1965 [973]). Membership function $\mu_A: \Omega \to [0,1]$. Possibility theory = extension; Dubois [531] / Prade refinement.

### §6.5.1 Possibility theory (p.284)
**Definition 98. (Possibility measure)** *(p.284)*: $Pos: 2^\Theta \to [0,1]$ with $Pos(\emptyset)=0$, $Pos(\Theta)=1$, $Pos(\bigcup A_i) = \sup_i Pos(A_i)$ (countably).

Possibility distribution: $\pi(x) \doteq Pos(\{x\})$, then $Pos(A) = \sup_{x \in A} \pi(x)$. Necessity: $Nec(A) = 1 - Pos(A^c)$.

**Proposition 42** *(p.284)*: $Pl$ associated with $Bel$ is a possibility measure iff $Bel$ is consonant; then membership = contour function: $\pi = pl$. Equivalently, $Bel$ = necessity iff consonant.

[1679] — possibility ↔ TBM points of contact.

**Related work**: Heilpern [816], Yager [2018,2007], Palacharla [1381], Romer [1500], Kreinovich [1071], [1424,707,598,1167,632,1580], Ferier [402] (membership = pl/Bel), Goodman [707] (membership = one-point coverage of equivalence class of random subsets), Wang 1985 [1909] (necessary+sufficient extension to consonant BF), Shafer [1596] (compatibility relations across frames), Yager [2031] (DS for fuzzy systems control), [1580] (interval/fuzzy number comparison via evidence theory), Smets [1679,1710] (degrees of possibility = modal extensions; conjunctive combination of possibilities = hyper-cautious of induced BFs), Dubois [550,521] (fuzzy connectives via belief structures; multiple combination), Feng 2012 [598] (fuzzy covering reduction via DS+rough sets).

### §6.5.2 Belief functions on fuzzy sets (p.285)
[1670,2063,153,447]; Ishizuka [872], Ogawa-Fu [1364], Yager [2000], Yen [2062,2064], Biacino [153]. Zhang [749]; Wang [1909] analogue.

**Implication operators** (Romer-Candell [1498]):
$$
Bel(A) = \sum_{B \in \mathcal{M}} \mathcal{I}(B \subseteq A) m(B) \quad (6.13, p.285)
$$
where $\mathcal{I}$ is a fuzzy implication operator measuring inclusion of fuzzy sets.

Inclusion via fuzzy implication operator $I: [0,1]^2 \to [0,1]$:
$$
\mathcal{I}(A \subseteq B) = \bigwedge_{x \in \Theta} I(A(x), B(x)) \quad (\text{p.286})
$$
Common implications: Lukasiewicz $I(x,y) = \min\{1, 1-x+y\}$ (Ishizuka [872]); Kleene-Dienes $I(x,y) = \max\{1-x, y\}$ (Yager [2000]).

**Yen's linear optimisation [2064]** *(p.286-287)*: $Bel(A)$ as LP:
$$
\min \sum_{x \in A} \sum_B m(x:B) \quad (6.14, p.286)
$$
subject to $m(x:B) \ge 0$ for all $x, B$; $m(x:B) = 0 \forall x \notin B$; $\sum_x m(x:B) = m(B) \forall B$. Generalisation to fuzzy sets: minimise $\sum_{x \in A} \sum_B m(x:B) \mu_A(x)$. Optimal solution = mass of $B$ on element of lowest membership in $A$.

Wu et al. [1965] semicontinuous implicator: $I(\vee_j a_j, \wedge_k b_k) = \bigwedge_{j,k} I(a_j, b_k)$.

**Proposition 43 ([1965] Thm 10)** *(p.287)*: Fuzzy belief structure $(\mathcal{M}, m)$ on potentially infinite $\Theta$ with semicontinuous $I$ ⇒ $Bel$ = fuzzy monotone Choquet capacity of infinite order; $Pl$ = fuzzy alternating Choquet capacity of infinite order.

**Definition 99. (Yen's generalised compatibility relation)** *(p.286)*: $C: 2^{\Omega \times \Theta} \to [0,1]$ representing joint possibility distribution $\Pi_{X,Y}(\omega, \theta)$.

### §6.5.3 Vague sets (p.287-288)
[669]: vague set $A$ has truth-membership $t_A(x)$ and false-membership $f_A(x)$, $t_A + f_A \le 1$; gap $1 - (t_A + f_A)$ = ignorance. [1151] showed BF theory is special case of vague-set theory: $t_A(x) = Bel(A), f_A(x) = Pl(A)$ (Cuzzolin: analysis "simplistic and possibly flawed"). **Atanassov's intuitionistic fuzzy sets [62]** mathematically equivalent to vague sets, [560].

### §6.5.4 Other fuzzy extensions of evidence theory (p.288-289)
- **Zadeh [2090]** — generalisation of Dempster's multivalued mappings: $X$ random with $P_X$ on $\Omega$, $\Pi_{Y|X}$ possibility on $\Theta$; for each $\omega_i$, $\Pi_{Y|X=\omega_i} = F_i$ fuzzy set; $m(F_i) = P_X(\omega_i)$ (Yager's *fuzzy belief structure*).
- **Yager [2031,2006,2018]** — combined fuzzy-evidential framework; *smooth normalisation* for empty-set conflict.
- **Denoeux [447]** — interval-valued and fuzzy-valued belief structures.
**Definition 100. (Fuzzy-valued belief structure)** *(p.288)*: normal fuzzy subset $\tilde{m}$ of $\mathcal{M}_\Theta$ with $\mu_{\tilde{m}}(m) = \min_i \mu_{\tilde{m}_i}(m(F_i))$ if $\sum_i m(F_i) = 1$, else 0.
- **Mahler FCDS [1235]** — fuzzy conditioned DS, finite-level Zadeh fuzzy logic + conditioned Dempster combination, generalisation of Bayes when both evidence and priors imprecise.
- **Lucas-Araabi [1223]** — fuzzy-valued generalisation of Yen's measure.
- **Aminravan IGIB [37]** — fuzzy interval-grade + interval-valued belief degrees.

## §6.6 Logic (p.289-)

Cox's theorem [1842] for probability as plausible-reasoning logic; Van Horn note its requirements are debatable.

Ruspini [1510,1511], Saffiotti [1526], Josang [918], Haenni [767] foundational. Long bibliography [1503,77,1510,2116,1513,124,1442,408,730,1388,1842,786,775,776,136,2087,43,862,787,762,1337,1326,2128,1525,1274,1198,121,777,264,1935,279,282,280].

### §6.6.1 Saffiotti's belief function logic (BFL) (p.289-290)
[1526]: hybrid logic over first-order language, formula $F: [a,b]$ with $0 \le a \le b \le 1$; $a$ = degree of belief $F$ true, $1-b$ = degree $F$ false. Frame = all interpretations; $A(\phi) \subseteq \Theta$ = models. $Bel(A(\phi)) \in [0,1]$ = total support for $\phi$.

**Definition 101. (bf-model)** *(p.290)*: $Bel$ is a bf-model of $F:[a,b]$ iff $Bel(F) \ge a$ and $Bel(F) \le b$ (i.e. $Bel(\neg F) \le 1-b$).

**Definition 102. (bf-entailment)** *(p.290)*: $\Phi$ bf-entails $\Psi$ iff every bf-model of $\Phi$ is also one of $\Psi$.

D-model = Dempster combination of formula models. Coherent ⇒ D-consistent (zero mass to ∅).
Andersen-Hooker [43] — probabilistic logic ⊕ DS = special LP type with exponentially many variables.

### §6.6.2 Josang's subjective logic (p.291)
[918,914,922]: *opinion* = subjective belief; operations: propositional conjunction ([918] Thm 3), disjunction ([918] Thm 4), negation, multiplication / comultiplication of beliefs (generalising probability and binary AND/OR) [922]. Equivalent to Baldwin's support logic [77] AND/OR except for relative atomicity. Includes consensus, recommendation operators (DS-specific). Subjective logic = logic with continuous uncertainty + belief parameters; alternatively second-order probability extension of probability calculus.

### §6.6.3 Fagin-Halpern's axiomatisation (p.291)
[586]: language for reasoning about probability ("$Pr(E_1) < 1/3$", "$Pr(E_1) \ge 2 Pr(E_2)$"). Measurable case = Nilsson [1358]; non-measurable case = replacing probability with belief function. Complete axiomatisation; satisfiability NP-complete.
- **Halpern [786]** — logic for evidence as function from prior to posterior beliefs.
- **Halpern [787]** — propositional logic for expectation; complete axiomatisation under BF semantics.

### §6.6.4 Probabilistic argumentation systems (PAS) (p.292)
Haenni-Lehmann [44,771,1125,767]: assumption-based reasoning; supporting arguments + assumptions + probabilities. Lehmann [1125]: degree of support = normalised belief in DS. PAS ↔ independent mass functions. ABEL [44] = formal language. PAS = modelling layer on top of belief theory; DS = computational tool. [767] sees logic and probability as opposite extremes of probabilistic argumentation.

### §6.6.5 Default logic (p.292-293)
Reiter [1481] default rule "$a:b/c$" = "if $a$ and $b$ consistent with current beliefs, conclude $c$".
- **Wilson [1939,1945]** — DS-based simplification of Reiter; "if $a$ then $c$ with reliability $\alpha$" = mass $\alpha$ on $a \to c$ + mass $1-\alpha$ on tautology (criticised by Pearl). Reinterpretation: "$a \to c$ is true in proportion $\alpha$ of worlds." Default ↔ uncertain rule with unknown antecedent.
- **Benferhat-Saffiotti-Smets [125,124]** — *epsilon belief assignments* via Adams's epsilon semantics [10,1361]:

**Definition 103. (ε-mass assignment)** *(p.293)*: $m_\mathcal{E}: 2^\Theta \to \mathbb{E}$ where $\mathbb{E} = \mathbb{E}_0 \cup \mathbb{E}_1 \cup \{0\} \cup \{1\}$ contains infinitesimals; for $\eta \in (0,1)$: $m_\mathcal{E}(\emptyset)(\eta) = 0$, $\sum_{A \subseteq \Theta} m_\mathcal{E}(A)(\eta) = 1$.
Provides uniform semantics for Kraus-Lehmann-Magidor system **P**, Goldszmidt-Pearl $\mathbf{Z}^+$ [701], Brewka subtheories, Geffner conditional entailment, Pinkas penalty logic [1434], possibilistic logic, lexicographic.

### §6.6.6 Ruspini's logical foundations (p.293-294)
Ruspini [1510,1513] 1986-87: Carnap-style [228] generalisation of probability logic [2116] via *epistemic logic*, modal logic for agent knowledge. Possible world $W: S \to \{T, F\}$; modal axioms [1510 II-2-2] ≡ S5; $K$ = knowledge operator.

**Definition 104. (Epistemic equivalence)** *(p.293)*: $W_1 \sim W_2$ iff for any $\mathcal{E}$, $K\mathcal{E}$ true in $W_1$ iff in $W_2$.

**Definition 105. (Epistemic space)** *(p.293)*: $\mathcal{U}(S) = $ quotient of possible worlds by $\sim$; members = epistemic states.

*Support sets* = those mapping $K\mathcal{E}$ to T. *Epistemic algebra* = smallest σ-algebra containing support sets. Probabilities on epistemic algebra ≡ belief / basic probability functions. Extending probability on epistemic to truth algebra forces interval bounds of DS theory.

Combination [1510,1513] (p.294):
$$
m(p) = \kappa \sum_{p_1 \wedge p_2 = p} P(e_1(p_1) \cap e_2(p_2)) \quad (6.15, p.294)
$$
where $e_i(p)$ = epistemic set for $p$ wrt operator $K_i$. Generalises Dempster's rule under independence.

Wilkins-Lavington [1935] — model theory of BFs simpler than lower-monotone capacities; conjunction operator partly resolved.

### §6.6.7 Modal logic interpretation (p.294-295)
Resconi-Harmanec [1484,800,799,1485,804]: propositional modal logic semantics for fuzzy/possibility/evidence. Modal operators $\Box$ (necessity), $\Diamond$ (possibility); standard model $M = \langle W, R, V \rangle$ with accessibility $R$ on possible worlds $W$, valuation $V$. T-model: $R$ reflexive. Truth set:
$$
\|p\|^M = \{w \in W : V(w, p) = T\} \quad (6.16, p.295)
$$

**Proposition 44 ([1483])** *(p.295)*: Finite T-model + singleton valuation assumption (SVA) (exactly one $e_{\{\theta\}}$ true in each world) induces:
$$
Bel_M(A) = \frac{|\|\Box e_A\|^M|}{|W|}, \quad Pl_M(A) = \frac{|\|\Diamond e_A\|^M|}{|W|} \quad (6.17, p.295)
$$

**Proposition 45 ([800])** *(p.295)*: SVA T-model induces BPA $m_M(A) = |\|E_A\|^M|/|W|$ with
$$
E_A = \Box e_A \wedge \bigwedge_{B \subset A} \neg \Box e_B
$$

**Proposition 46 ([800])** *(p.295)*: For every rational-valued BPA $m$ on $2^\Theta$, there exists a finite T-model satisfying SVA with $m_M = m$. (Completeness.)

To extend modal-logic interpretation to arbitrary universes: add probability measure on possible worlds [804]. Tsiporkova [1830,1829,1831] — multivalued mappings inducing belief; modal interpretation of Dempster's rule. Murai [1326] — soundness/completeness for several modal logic systems against BF models. [698,84,1485,804] further work.

### §6.6.8 Probability of provability (p.296)
Pearl [1405,1682,137], Ruspini [1510]. Smets: probability-of-provability ≡ original Dempster framework [415] but explains conditioning rule's origin.
- **Besnard-Kohlas [137]** — DS over Tarski-style consequence relations; support functions = monotone capacities of infinite order; plausibility lacks duality (no negation).
- **Hajek [777]** — extension of Resconi-Harmanec [803]: every BF on finite frame (incl. unnormalised) = probability of provability in Gödel-Löb modal provability logic. Esteva-Godo [579] follow-up.

### §6.6.9 Other logical frameworks (p.296-298)

**Incidence calculus (Bundy [205], p.296-297)** — probabilistic logic; incidences = logic conditions for formula truth. **Definition 106 (Incidence map)** *(p.297)*: $i: \mathcal{A} \to 2^\mathcal{W}$, $i(\phi) = \{w : w \models \phi\}$. Liu-Bundy [1205] — basic incidence assignment for BFs.

**Baldwin's evidential support logic programming (1987, [77])** — generalises logic programming; conclusions degree-supported, negation also supported, sums need not be 1.

**Provan's analysis (1990, [1442])** — DS via propositional logic + provability; tuple $(\Sigma, \rho)$ = clauses + mass. Disjunction of minimal support clauses ↔ symbolic BF. Dempster combination ↔ combined support clauses. Disjointness necessary; intractability ⇒ approximations.

**Penalty logic (Pinkas [1434])** — formula has price-if-violated; selects preferred consistent subsets. Dupin-Lang-Schiex [408] — penalty logic ↔ DS in infinitesimal case.

**Other contributions** *(p.297-299)*:
- Grosof [730] — generalised probabilistic logic; DS = special case.
- Chen [264] — analogous formal identity.
- Paris [1388] — Dutch book argument generalisations for modal/intuitionistic/paraconsistent.
- Hjek [775,776] — many-valued + modal logic; degrees of belief vs degrees of truth.
- Bertschy-Monney [136,1027] — disjoint disjunctive normal form.
- Zadeh [2087] — generalised syllogistic reasoning; six basic syllogisms suffice for certainty factors.
- Andersen-Hooker [43] — uncertainty logics as exponential-variable LP.
- Hunter [862] — DS combination vs probabilistic logic combination; sufficient agreement conditions.
- Cholvy [279,280] — logical interpretation; degree of belief = proportion of proofs of $A$; new combination rule.
- Benavoli [118] — uncertain implication rules → BF transformation; reflexivity, transitivity, contrapositivity.
- Narens [1337] — qualitative foundations of probability; intuitionistic event algebra.
- Qing [2128] — DS within logic calculus.
- Saffiotti [1525] — *DS belief bases* coupling DS + knowledge representation.
- McLeish [1274] — extension of Nilsson's entailment scheme [1358] to BFs (overcoming consistent-worlds limitation).
- Bharadwaj [147] — variable precision logic, *censored production rule* (CPR), hierarchical CPR for variable certainty/specificity.
- Kroupa [1076] — BFs in Lukasiewicz logic.

## §6.7 Rough sets (p.299-301)

Pawlak [1393]: lower/upper set approximation via partition. [1396,1658,1397] DS-rough relations.

### §6.7.1 Pawlak's algebras of rough sets (p.299)
Equivalence relation $\mathcal{R} \subseteq \Theta \times \Theta$; quotient $\Theta/\mathcal{R}$ = elementary sets. Definable/measurable: $\sigma(\Theta/\mathcal{R})$.
Lower approx: $\underline{apr}(A)$ = elementary sets contained in $A$. Upper approx: $\overline{apr}(A)$ = elementary sets meeting $A$. Fig.6.4 (p.300) illustration.

### §6.7.2 Belief functions and rough sets (p.300-301)
Yao-Lingras [2057]; [1166,1966,1395,1182,2107,2056,1005,1642]. Kopotek 1998 [1005] — DS as measures of diversity in relational databases via join.

Pawlak rough algebra → qualities:
$$
\underline{q}(A) \doteq \frac{|\underline{apr}(A)|}{|\Theta|}, \quad \overline{q}(A) \doteq \frac{|\overline{apr}(A)|}{|\Theta|} \quad (\text{p.300})
$$
Pawlak rough algebra ≡ modal logic system S5 [2053]; thus lower/upper approx ↔ belief/possibility under (6.17).

**Proposition 47** *(p.300)*: $\underline{q}$ is a BF with BPA $m(E) = |E|/|\Theta|$ for $E \in \Theta/\mathcal{R}$, 0 otherwise.

**Proposition 48** *(p.301)*: If $Bel$ has focal elements forming a partition of $\Theta$ with $m(A) = |A|/|\Theta|$, then $\exists$ rough set algebra with $\underline{q}(A) = Bel(A)$.

General: σ-algebra $\mathcal{F}$ on $\Theta$, probability $P$ on $\mathcal{F}$, extend to $2^\Theta$:
$$
P_*(A) = \sup\{P(X) : X \in \sigma(\Theta/\mathcal{R}), X \subseteq A\} = P(\underline{apr}(A))
$$
$$
P^*(A) = \inf\{P(X) : X \supseteq A\} = P(\overline{apr}(A))
$$
"Rough probabilities" = pair of belief and plausibility. Restriction: focal elements must form a partition. Yao [2057] generalises via serial / interval algebras.

Yao-related [2056] — granular computing via zooming-in/out. Wu [1968,1964,1966] — plausibility/belief reduct in incomplete info systems. Zhang [2107] inclusion-degree knowledge reduction. Liu [1182] — arbitrary binary relations on two universal sets.

## §6.8 Probability boxes (p.301-304)
Reliability analysis [605,2027,604]: $P_X(F) = \int_F f(x) dx$.

**Definition 107. (P-box)** *(p.302)* — $\langle \underline{F}, \overline{F} \rangle$ = class of CDFs:
$$
\langle \underline{F}, \overline{F} \rangle = \{F \text{ CDF} : \underline{F} \le F \le \overline{F}\}
$$

### §6.8.1 P-boxes and belief functions (p.302)
Every $(Bel, Pl)$ on $\mathbb{R}$ ⇒ p-box:
$$
\underline{F}(x) = Bel((-\infty, x]), \quad \overline{F}(x) = Pl((-\infty, x]) \quad (6.18, p.302)
$$
Conversely [928,604,781] every p-box ↔ equivalence class of random intervals; non-unique discretisation:
$$
\mathcal{F} = \{\gamma = [\overline{F}^{-1}(\alpha), \underline{F}^{-1}(\alpha)] : \alpha \in [0,1]\} \quad (6.19, p.302)
$$
with quasi-inverses $\overline{F}^{-1}(\alpha) = \inf\{\overline{F}(x) \ge \alpha\}$, $\underline{F}^{-1}(\alpha) = \inf\{\underline{F}(x) \ge \alpha\}$.

### §6.8.2 Approximate computations for random sets (p.303)
P-box ↔ multivalued mapping $\Gamma: \Omega \to 2^\mathbb{R}$, $\gamma = \Gamma(\alpha)$:
$$
Bel(A) = \int_{\omega \in \Omega} I[\Gamma(\omega) \subseteq A] dP(\omega), \quad Pl(A) = \int I[\Gamma(\omega) \cap A \neq \emptyset] dP(\omega) \quad (6.20)
$$
Sampling representation: $d$ random sets, focal element $\gamma = \times_{i=1}^d \gamma_i \subseteq X$, joint via copula $C$ on $[0,1]^d$; $P_\Gamma(G) = \int_{\alpha \in G} dC(\alpha)$. If independent: copula = product; nested integrals (Alvarez [36], eq.36).

**Algorithm 14 (MonteCarloAlvarez)** *(p.304)*: For $j=1,\ldots,n$: sample $\alpha_j$ from $C$; form $A_j = \times_i \gamma_i^{d}$; mass $m(A_j) = 1/n$. Converges as $n \to \infty$.

### §6.8.3 Generalised probability boxes (p.304)
Desterке [486]: standard p-boxes inadequate for $|\tilde{x} - \rho| < \epsilon$ queries. Two CDFs comonotonic: $F(x) < F(y) \Rightarrow F'(x) < F'(y)$.

**Definition 108. (Generalised p-box)** *(p.304)*: $\langle \underline{F}, \overline{F} \rangle$ pair of comonotonic mappings $X \to [0,1]$ with $\underline{F} \le \overline{F}$, $\exists x: \underline{F}(x) = \overline{F}(x) = 1$.

Permutation reduces to traditional p-box. Associated nested family $A_y = \{x: \underline{F}(x) \le \underline{F}(y), \overline{F}(x) \le \overline{F}(y)\}$ → possibility distribution. Special case of random sets ($\infty$-monotone) and probability intervals (Fig.6.6, p.305).

## §6.9 Spohn's theory of epistemic beliefs (p.304-305)

Epistemic state for $X$: each proposition is *believed*, *disbelieved*, or *neither*.

### §6.9.1 Epistemic states (p.305)
**Definition 109 (Consistent epistemic state)** *(p.305)*:
1. Exactly one of: $A$ believed; $A$ disbelieved; neither.
2. $\Theta_X$ believed.
3. $A$ believed iff $A^c$ disbelieved.
4. $A$ believed and $B \supseteq A$ ⇒ $B$ believed.
5. $A, B$ believed ⇒ $A \cap B$ believed.

**Proposition 49** *(p.305)*: epistemic state consistent iff $\exists$ unique non-empty $C \subseteq \Theta_X$ such that $\mathcal{B} = \{A : A \supseteq C\}$ — like *consistent belief functions* (focal elements with common intersection, ch.10.4).

### §6.9.2 Disbelief functions and Spohnian belief functions (p.306)

Spohn's *ordinal conditional function* (OCF) [1752] / *natural conditional function* [1753]; Shenoy [1625] calls it a *disbelief function*.

**Definition 110 ([1753] p.316; Disbelief function)** *(p.306)* $\delta: 2^{\Theta_g} \to \mathbb{N}^+$ such that
1. $\delta(\theta) \in \mathbb{N}$ for all $\theta \in \Theta_g$.
2. $\exists \theta \in \Theta_g: \delta(\theta) = 0$.
3. $\delta(A) = \min\{\delta(\theta) : \theta \in A\}$ for $A \subset \Theta_g, A \neq \emptyset$.
4. $\delta(\emptyset) = +\infty$.

Like a possibility measure, $\delta$ is determined by its singleton values. Belief semantics: $A$ believed iff $A \supseteq C$ where $C = \{\theta : \delta(\theta) = 0\}$, equivalently iff $\delta(A^c) > 0$. $A$ disbelieved iff $\delta(A) > 0$. Neither iff $\delta(A) = \delta(A^c) = 0$. $\delta(A^c)$ is degree of belief in $A$. Consequence: a disbelief function models disbelief degrees directly, beliefs only indirectly.

**Definition 111 (Spohnian belief function)** *(p.306)* $\beta: 2^{\Theta_g} \to \mathbb{Z}^+$ where
$$
\beta(A) = \begin{cases} -\delta(A) & \delta(A) > 0 \\ \delta(A^c) & \delta(A) = 0 \end{cases}
$$
Spohnian belief models both beliefs and disbeliefs directly; $\delta$ uniquely recoverable from $\beta$. Properties enumerated in [1625].

### §6.9.3 α-conditionalisation (p.306-307)

Spohn's update rule on learning $A$ to degree $\alpha$ (equivalently disbelieving $A^c$ to degree $\alpha$), $\alpha \in \mathbb{N}$.

**Definition 112 ([1752] p.117; α-conditionalisation)** *(p.306-307)*:
$$
\delta_{A,\alpha}(\theta) = \begin{cases} \delta(\theta) - \delta(A) & \theta \in A \\ \delta(\theta) + \alpha - \delta(A^c) & \theta \notin A \end{cases}
$$
for all $\theta \in \Theta_g$.

Shenoy [1625]: Spohn's epistemic-belief theory shares with probability and DS theory (1) functional knowledge representation, (2) marginalisation rule, (3) combination rule. Disbelief functions propagate via local computations (cf. Ch.4 §4.7.4).

## §6.10 Zadeh's generalised theory of uncertainty (GTU) (p.307-308)

GTU [2091,2093]: replaces statistical-information assumption with a *generalised constraint*. A generalised constraint $GC(X): X \text{ isr } R$ where $r \in \{\text{blank, probabilistic, veristic, random set, fuzzy graph, } \ldots\}$ labels constraint type and $R$ is the constraining relation (probability distribution, random set, etc.). Operates on perception-based information ("Usually Robert returns from work at about 6 p.m.", "It is very unlikely there will be a significant increase in the price of oil…").

Generalised constraints serve to define imprecise probabilities, utilities, etc.; *generalised constraint propagation* is the GTU's reasoning mechanism. A generalised constraint generalises a belief function (a "rather nomenclative" generalisation). Zadeh: BF theory = mixture of probabilistic + possibilistic constraints; GTU embraces all mixtures and most other uncertainty theories.

GTU abandons bivalence — fuzzy logic substrate; everything is or may be a matter of degree. Variables are "granular" (a *granule* = a clump of values drawn together by indistinguishability, equivalence, similarity, proximity, functionality).

**Generalised constraint language (GCL)** = set of all generalised constraints with rules governing syntax, semantics, generation. Examples: $X$ is small; likely $(X, Y)$ isp $A) \wedge (X \text{ is } B)$. Computation/deduction = question-answering: system $p$, query $q$ in natural language, propagation governed by deduction rules in modules drawn from natural fields and uncertainty modalities. Computation/Deduction module = collection of agent-controlled modules + submodules (each contains protoformal deduction rules drawn from various fields and modalities of generalised constraints).

**Fig.6.7 (p.308):** quantisation (left) vs granulation (right) of variable "Age", from [2092] — quantisation gives crisp intervals, granulation gives fuzzy categories Young / Middle-aged / Old.

Cuzzolin's verdict: "generality is achieved by the GTU in a rather nomenclative way, which explains the complexity and lack of naturalness of the formalism" (p.308).

## §6.11 Baoding Liu's uncertainty theory (p.308-310)

Liu's *uncertainty theory* [1177,1178] based on an *uncertain measure* $\mathcal{M}: \mathcal{F} \to [0,1]$ on σ-algebra $\mathcal{F}$ of events over non-empty set $\Theta$:
1. $\mathcal{M}(\Theta) = 1$ (normality).
2. $\mathcal{M}(A_1) \le \mathcal{M}(A_2)$ when $A_1 \subset A_2$ (monotonicity).
3. $\mathcal{M}(A) + \mathcal{M}(A^c) = 1$ (self-duality).
4. Countable subadditivity: $\mathcal{M}(\bigcup A_i) \le \sum \mathcal{M}(A_i)$.

Liu's claim: probability theory is a special case. Cuzzolin's response: probability satisfies a stronger *product axiom* $\mathcal{M}(\prod A_k) = \bigwedge \mathcal{M}_k(A_k)$ which Liu's uncertain measures need not satisfy. Cuzzolin: "the extension of uncertain measures to any subset of a product algebra is somewhat cumbersome and unjustified (see eq.(1.10) in [1177], or Fig.6.8)."

**Fig.6.8 (p.309):** disc $A$ vs inscribed rectangle $A^*$ in product algebra. Uncertain measure of $A$ is the size of the inscribed rectangle $A^* = A_1 \times A_2$ if the latter is greater than 0.5 (else 0.5).

Liu's uncertain measures are monotone capacities (Def 95). Uncertain variables = measurable functions $(\Theta, \mathcal{F}, \mathcal{M}) \to \mathbb{R}$. Independent if $\mathcal{M}(\bigcap_i \{\xi_i \in B_i\}) = \min_i \mathcal{M}(\{\xi_i \in B_i\})$. Characterised by *identification functions* $(\lambda, \rho)$, subject to complex axioms (eq. 6.21 p.310):
$$
\sup_B \lambda(x) + \int_B \rho(x)\,dx \ge 0.5 \text{ and/or } \sup_{B^c}\lambda(x) + \int_{B^c}\rho(x)\,dx \ge 0.5
$$
**(Eq. 6.21, p.310)** $\lambda, \rho$ non-negative real-line functions; $B$ Borel set of reals. Mirrors extension method of Fig.6.8.

Cuzzolin's verdict (p.310): "the general lack of rigour and of a convincing justification for a number of elements of the theory leaves the author of this book quite unimpressed with this work. No mention of belief functions or other well-established alternative representations of subjective probabilities is made in [1177]."

## §6.12 Info-gap decision theory (p.310-311)

Yakov Ben-Haim's *info-gap theory* [107]: assesses robustness of dynamical models. Transfer function $F(\omega, \delta)$ with parameters $\delta$; performance $\hat{f}(F, \delta)$. Question: how wrong can the model be without jeopardising performance? Approach: maximise robustness, sacrificing performance.

### §6.12.1 Info-gap models (p.310-311)

**Definition 113 (Info-gap model)** *(p.310)*: an info-gap model for the uncertainty in the dynamic behaviour of a structure is an *unbounded family of nested sets* of dynamic models.

Describes non-probabilistically the uncertain difference between best-estimated $\tilde{F}(\omega, \delta)$ and other possible $F(\omega,\delta)$. Variants:

**Uniform-bound info-gap model (Eq.6.22, p.311):**
$$
\mathcal{F}(\alpha, \tilde{F}) = \{F(\omega, \delta) : |F(\omega,\delta) - \tilde{F}(\omega,\delta)| \le \alpha\}, \quad \alpha \ge 0
$$

**Constrained-rate-of-variation:**
$$
\mathcal{F}(\alpha, \tilde{F}) = \Big\{F(\omega, c, \delta) : \Big|\frac{c_i - \tilde{c}_i}{\tilde{c}_i}\Big| \le \alpha, i = 1,\ldots,J\Big\}, \quad \alpha \ge 0
$$

Two levels of uncertainty: set of possible models $\mathcal{F}(\alpha,\tilde{F})$ + uncertainty in $\alpha$ ("horizon of uncertainty"). Uncertainty is *unbounded*, not convex.

### §6.12.2 Robustness of design (p.311)

Performance = vector $\hat{f}(F,\delta)$, $R$ components, requirements $\hat{f}_i(F,\delta) \le f_{c,i}, i=1,\ldots,R$.

**Definition 114 (Robustness of design)** *(p.311)*: greatest horizon of uncertainty up to which the response satisfies all performance requirements:
$$
\hat{\alpha}(\delta, f_c) = \max\Big\{\alpha \;\Big|\; \max_{F \in \mathcal{F}(\alpha,\tilde{F})} \hat{f}_i(F,\delta) \le f_{c,i}, i=1,\ldots,R\Big\}
$$

Application: climate-change mitigation [782].

## §6.13 Vovk and Shafer's game-theoretic framework (p.311-315)

*Game-theoretic probability* [1615,1863,1862]: epistemic probability based on a game-theoretic scenario where good probability forecasts can be made relative to whatever state of knowledge exists. Probabilistic predictions are proven by constructing a betting strategy that multiplies capital indefinitely if the prediction fails. Defensive forecasting [1861,1864] yields additive probabilities. Open to diverse interpretations like Kolmogorov's measure-theoretic probability [1615].

Mathematical lineage: Dawid's *prequential probability* [392] — forecasting success of a probability distribution should be evaluated using only actual outcomes and the conditional-probability forecasts they trigger.

Cuzzolin: extension to non-repetitive situations (e.g. belief theory) "still being sought." Shafer [1605] attempted a betting interpretation of DS belief. Walley relations: [397, 1292].

### §6.13.1 Game-theoretic probability (p.312)

Lineage: Pascal ("probability is about betting"), Cournot ("events of small probability do not happen"), Jean Ville [1604] — *Cournot's principle*: "you will not multiply the capital you risk by a large factor."

**Algorithm 15 (Game-theoretical protocol)** *(p.312)*:
```
K_0 = 1
for n = 1,…,N:
  Forecaster announces prices for various payoffs.
  Skeptic decides which payoffs to buy.
  Reality determines the payoffs.
  Skeptic's capital changes: K_n = K_{n-1} + net gain or loss.
```

Markov: $P(X \ge E(X)/\epsilon) \le \epsilon$. Ville generalised to **Doob's inequality** for sequence of bets:
$$
P\Big(\sup_{0 \le t \le T} X_t \ge C\Big) \le \frac{E[X_T^p]}{C^p} \quad (6.23, p.313)
$$
for $C > 0, p \ge 1$, $X$ submartingale taking non-negative real values: $E[X_{n+1}|X_1,\ldots,X_n] \ge X_n$.

### §6.13.2 Ville/Vovk game-theoretic testing (p.313)

**Algorithm 16 (Ville's setting)** *(p.314)*:
```
K_0 = 1
for n = 1,2,…:
  Skeptic announces s_n ∈ R
  Reality announces y_n ∈ {0,1}
  K_n = K_{n-1} + s_n(y_n - P(y_n=1|y_1,…,y_{n-1}))
Skeptic wins if K_n is never negative AND
  lim_{n→∞} (1/n) Σ(y_i - P(y_i=1|y_1,…,y_{i-1})) = 0   (6.24)
or lim K_n = ∞.
```

**Proposition 50 (Ville)** *(p.313)*: Skeptic has a winning strategy.

**Algorithm 17 (Vovk's setting)** *(p.314)*: like Ville but Forecaster announces $p_n \in [0,1]$ (no fixed distribution), $K_n = K_{n-1} + s_n(y_n - p_n)$. Skeptic wins if $K_n$ never negative AND $\lim (1/n)\sum(y_i - p_i) = 0$ or $\lim K_n = \infty$.

**Proposition 51 (Vovk weak law of large numbers, [1604])** *(p.313)*: Skeptic has a winning strategy if $N \ge C/4\epsilon^2$, where winning is defined as $K_n$ never negative and either $K_N \ge C$ or $|(1/N)\sum_{n=1}^N (y_n - p_n)| < \epsilon$.

Footnote 62: Kumon et al. [1084,1604] — game-theoretic strong LLN for unbounded variables.

**Definition 115 (Discrete-time martingale)** *(p.314)*: discrete-time stochastic process $X_1,X_2,\ldots$ satisfying for any $n$:
$$
E(|X_n|) < \infty, \quad E(X_{n+1} | X_1,\ldots,X_n) = X_n
$$
i.e. $E(X_{n+1}|X_1,\ldots,X_n) - X_n = 0$ (Eq.6.25, p.314).

Comparing (6.24) with (6.25) shows that Skeptic's capital $\{K_n\}$ is a martingale. "Shafer and Vovk's game-theoretical framework puts martingales first" (p.314).

### §6.13.3 Upper price and upper probability (p.315)

Initial capital $K_0 = \alpha$.

**Definition 116 (Upper price)** *(p.315)*: For any real-valued $X$ on $([0,1] \times \{0,1\})^N$:
$$
\overline{E}X = \inf\{\alpha \mid \text{Skeptic has a strategy guaranteeing } K_n \ge X(p_1,y_1,\ldots,p_N,y_N)\}
$$

**Definition 117 (Upper probability)** *(p.315)*: For any subset $A \subseteq ([0,1] \times \{0,1\})^N$:
$$
\overline{P}A = \inf\{\alpha \mid \text{Skeptic has strategy with } K_N \ge 1 \text{ if } A \text{ happens, } K_N \ge 0 \text{ otherwise}\}
$$

**Proposition 52** *(p.315)* — restatement of (51) in upper-probability form:
$$
\overline{P}\Big(\Big|\frac{1}{N}\sum_{n=1}^N (y_n - p_n)\Big| \ge \epsilon\Big) \le \frac{1}{4N\epsilon^2}
$$

Defensive forecasting [1864] not covered in book.

## §6.14 Other formalisms (p.315-322)

### §6.14.1 Endorsements (Cohen-Grinberg 1983, [297,296], p.315)
Reasoning about uncertainty via *endorsements* — records of certainty states. Claim: numerical representations hide reasoning that produced them; numbers have unclear meanings; numerical approaches are not rich enough to support heuristic knowledge about uncertainty/evidence. *Justifications* are needed in support of evidence; different kinds of evidence should be distinguished by explicit records of what makes them different, not by [0,1] numbers.

### §6.14.2 Fril-fuzzy theory (Baldwin et al. [83,79], p.315)
Theory of uncertainty consistent with and combining probability and fuzzy sets; extends logic programming representation to include probabilistic knowledge and fuzzy incompleteness. Applications: expert / decision support systems, evidential / case-based reasoning, fuzzy control, databases.

### §6.14.3 Granular computing (Yao [2055], p.316)
Theories using *granules* (groups/clusters of concepts). Set-theoretic model based on *power algebras*: any binary $\circ$ on $U$ lifts to $\circ^+$ on $2^U$:
$$
X \circ^+ Y = \{x \circ y \mid x \in X, y \in Y\}
$$
Examples: arithmetic on intervals lifted from reals → interval algebra. Used for: interval fuzzy reasoning [2058], interval probabilistic reasoning [1450], reasoning with granular probabilities [985].

### §6.14.4 Laskey's assumptions (Laskey [1100], p.316)
Formal equivalence between belief theory and *assumption-based truth maintenance systems* (ATMS) [372]: any DS inference network = set of ATMS justifications with probabilities on assumptions. *A proposition's belief equals the probability of its label conditioned on label consistency.* [1100] gives algorithm to compute these. ATMS use automatically and correctly accounts for non-independencies between nodes. **(propstore: this is the bridge for the world/ATMS layer.)**

### §6.14.5 Harper's Popperian rational belief change (Harper [806], p.316-317)
Uses Popper's *propensity* probability + epistemic constraint on conditional assignments to extend Bayesian rational belief representation so that *previously accepted evidence can be revised*.

**Definition 118 (Popper probability function)** *(p.316)* $P: \mathcal{F} \times \mathcal{F} \to [0,1]$ on minimal algebra with $AB$, $\bar A$:
1. $0 \le P(B|A) \le P(A|A) = 1$.
2. $P(A|B) = 1 = P(B|A) \Rightarrow P(C|A) = P(C|B)$.
3. $P(C|A) \neq 1 \Rightarrow P(\bar B | A) = 1 - P(B|A)$.
4. $P(AB|C) = P(A|C) \cdot P(B|AC)$.
5. $P(AB|C) \le P(B|C)$.

In Popperian probability, *conditional probability is primitive*; $P(A) \doteq P(A|T)$ with $T = \overline{A\bar A}$ (on σ-algebra $T = \Omega$). When $P(A) > 0$, classical $P(B|A) = P(AB)/P(A)$ recovered. **Key advantage:** $P(B|A)$ exists even when $P(A) = 0$ — allows revision of previously accepted evidence by conditioning on currently zero-probability events. Provides epistemic semantics for Lewis's *counterfactual conditionals* [1144,1145].

### §6.14.6 Shastri's evidential reasoning in semantic networks (Shastri [1620,1621], p.317)
PhD thesis: best way to cope with partial / incomplete information is *evidential reasoning* — inference = finding most likely hypothesis among alternatives, not establishing truth. Real-time inference requires computational account in acceptable time. *Inheritance* and *categorisation* in conceptual hierarchy = humans' fast operations underlying intelligent behaviour. Framework uses maximum entropy for uncertainty, encoded as interpreter-free connectionist network. Shastri-Feldman [1621] combination rule: incremental, commutative, associative; "demonstrably better" than Dempster's rule in their setting.

### §6.14.7 Evidential confirmation theory (Grosof [732], p.317)
Aggregating measures of confirmatory and disconfirmatory evidence. Showed revised MYCIN certainty factor [812] and PROSPECTOR [554] are special cases of DS theory. Nonlinear invertible transformation makes a special case of Dempster's rule equivalent to conditional independence. Resolves the "take-them-or-leave-them" prior problem (MYCIN out, PROSPECTOR in).

### §6.14.8 Groen's extension of Bayesian theory (Groen-Mosleh [727], p.318)
Inference uses observations to *rule out possible valuations* of variables. Different from Jeffrey's rule (cf §4.6.2) and Cheeseman's distributed meaning [256].

*Interpretation* $I$ of observation $O$ = union of values of variable $X$ consistent with (not contradicted by) $O$. Evidence uncertainty = uncertainty about interpretation, expressed as PDF $\pi(I|H)$ on space $\mathcal{I}$ of interpretations or via *interpretation function*:
$$
\rho(x) \doteq Pr(x \in I | H), \quad 0 \le \rho(x) \le 1
$$
Equivalence: $\rho(x) = \sum_{I \in \mathcal{I}: x \in I} \pi(I|H)$. Modified Bayes:
$$
\pi(x,\theta|H,O) = \frac{\rho(x) \pi(x|\theta,H) \pi(\theta|H)}{\int \rho(x) \pi(x|\theta,H) \pi(\theta|H)\,dx\,d\theta}
$$
Under "interpretations are certain" constraint, $\rho(x) \in \{0,1\}$ (1 iff $x$ not contradicted by $O$). Rationale: observations provide no basis for preferring among non-contradicted representations.

### §6.14.9 Padovitz's unifying model (Padovitz et al. 2006, [1375], p.319)
Novel approach to representing/reasoning about *context* under uncertainty, based on *multi-attribute utility theory* as a means to integrate heuristics about relative importance, inaccuracy and characteristics of sensory information. Authors qualitatively and quantitatively compared their approach with Dempster-Shafer sensor data fusion.

### §6.14.10 Similarity-based reasoning (SBR) ([857], p.319)
Principle: "similar causes bring about similar effects." [857] proposed a probabilistic framework for SBR based on a *similarity profile* that probabilistically characterises similarity between observed cases (instances).

**Definition 119 (Similarity-based inference (SBI) set-up)** *(p.319)* — 6-tuple
$$
\Sigma = \langle (\mathcal{S}, \mu_\mathcal{S}), \mathcal{R}, \phi, \sigma_\mathcal{S}, \sigma_\mathcal{R}, \mathcal{M} \rangle
$$
where: $\mathcal{S}$ = finite set of situations with probability measure $\mu_\mathcal{S}$ on $2^\mathcal{S}$; $\mathcal{R}$ = set of results; $\phi: \mathcal{S} \to \mathcal{R}$ assigns unique results; $\sigma_\mathcal{S}: \mathcal{S} \times \mathcal{S} \to [0,1]$ and $\sigma_\mathcal{R}: \mathcal{R} \times \mathcal{R} \to [0,1]$ reflexive/symmetric/normalised similarity measures; $\mathcal{M} = \{(s_1,r_1),\ldots,(s_n,r_n)\}$ finite memory of cases. Goal: given new $s_0$, predict $r_0 = \phi(s_0)$ (regression).

[857] further: *imperfect specification* of outcome $\phi(s_0)$ induced by case $(s,r)$ as a multivalued mapping from contexts $C$ to responses $\mathcal{R}$ — i.e., a random set / belief function $\Gamma: C \to 2^\mathcal{R}$ with
$$
C = \{\sigma_\mathcal{R}(\phi(s), \phi(s')) | s, s' \in \mathcal{S}\} \subset [0,1]
$$
$$
\Gamma(c) = \sigma_\mathcal{R}^{(-1)}(r, c) \doteq \{r' \in \mathcal{R} | \sigma_\mathcal{R}(r, r') = c\} \subset \mathcal{R}
$$
and $P(c) = \mu(c)$ where $\mu$ is a probability measure over $C$ derived from $(s,r)$, mapping similarity values to response sets.

### §6.14.11 Neighbourhood systems ([1170], p.320)
Formalises "negligible quantity":
$$
\mathcal{NS} = \{NS(p) | p \in U\}
$$
$NS(p)$ = maximal family of neighbourhoods of $p$, $U$ = universe. *Minimal* neighbourhood system: pick all minimal neighbourhoods of all points. *Basic*: minimal where every point has single minimal neighbourhood, i.e. mapping $p \mapsto A(p) \subset U$. Span topology (topological neighbourhood systems), rough sets, binary relations (basic). [1170] showed real-valued functions on neighbourhood systems cover BFs, measures, probability distributions.

Assigning a basic probability to each basic neighbourhood (zero elsewhere) → BF on $U$. More generally, assigning to all minimal neighbourhoods → BF on $U$. Converse [1170]:

**Proposition 53** *(p.320)*: Let $U$ be finite. Then $U$ has a belief function iff there is a neighbourhood system on $U$.

### §6.14.12 Comparative belief structures ([1957], p.320)
*Comparative belief* generalises Fine's *comparative probability* [615]: for any two propositions $A, B$ one can say whether $Bel(A) \gtrless Bel(B)$ without numerical magnitude. [1957] gave axiomatic system for belief relations $\succ$ on $2^\Theta$, showed BFs "almost agree" with comparative belief relations:
$$
A \succ B \Rightarrow Bel(A) > Bel(B) \quad \forall A, B \in 2^\Theta
$$

## Geometric structures (Ch.6 picks up only the lattice of formalisms)

Chapter 6 does not introduce geometric simplices/polytopes — that programme begins in Chapter 7. The "geometric" content in Chapter 6 is the *containment hierarchy* of formalism families pictured in **Fig.6.1 (p.270)**: probability ⊂ Sugeno-λ measures ⊂ belief functions ⊂ 2-monotone capacities ⊂ lower/upper probabilities, with a parallel fuzzy lane (probability of fuzzy events; fuzzy belief; fuzzy λ-measures; feasible probability intervals; feasible fuzzy probabilities).

## Algorithms — Chapter 6 list

| Number | Name | Page |
|--------|------|------|
| 14 | MonteCarloAlvarez (sample copula → focal element approximation for p-boxes) | p.304 |
| 15 | Game-theoretical protocol (Forecaster/Skeptic/Reality) | p.312 |
| 16 | Ville's setting (known $P$, Skeptic+Reality, Doob/CLT) | p.314 |
| 17 | Vovk's setting (Forecaster announces $p_n$, no fixed distribution) | p.314 |

(Chapter 5 contains Algorithms 11 = Ek-NNclus heuristic, 12 = Belief K-modes, 13 = Belief decision tree.)

## Parameters / quantities (Ch.6 selection)

| Name | Symbol | Domain | Page | Notes |
|------|--------|--------|------|-------|
| Sugeno λ-parameter | $\lambda$ | $(-1, \infty)$ | 279 | $<0$ subadditive (upper-prob), $0$ probability, $>0$ superadditive (lower-prob) |
| Probability interval bounds | $l(x), u(x)$ | $[0,1]$ | 280 | Subject to feasibility (eqs after 6.10) |
| Disbelief degree | $\delta(\theta)$ | $\mathbb{N}^+$ | 306 | $\delta(\theta_0)=0$ for some $\theta_0$ |
| Spohnian belief degree | $\beta(A)$ | $\mathbb{Z}^+$ | 306 | Negative when $\delta(A)>0$ |
| α-conditionalisation degree | $\alpha$ | $\mathbb{N}$ | 306 | Strength of new evidence |
| Info-gap horizon | $\alpha$ | $[0, \infty)$ | 311 | Unbounded uncertainty horizon |
| Liu uncertain measure | $\mathcal{M}(A)$ | $[0,1]$ | 308 | Self-dual: $\mathcal{M}(A) + \mathcal{M}(A^c) = 1$ |
| Skeptic capital | $\mathcal{K}_n$ | $\mathbb{R}_{\ge 0}$ | 312 | Martingale under Vovk-Shafer |
| Vovk forecast | $p_n$ | $[0,1]$ | 314 | No distributional commitment |

## Worked example — Liu's uncertain measure on a product (Fig.6.8, p.309)
Two algebras $\mathcal{F}_1, \mathcal{F}_2$ with measures $\mathcal{M}_1, \mathcal{M}_2$. To extend to subset $A$ of product space, find largest inscribed rectangle $A^* = \Lambda_1 \times \Lambda_2 \subseteq A$; if $\mathcal{M}_1(\Lambda_1) \wedge \mathcal{M}_2(\Lambda_2) > 0.5$ then $\mathcal{M}(A) = \mathcal{M}_1(\Lambda_1) \wedge \mathcal{M}_2(\Lambda_2)$; if no inscribed rectangle for $A$ or $A^c$ has measure $>0.5$, then $\mathcal{M}(A) = 0.5$. Cuzzolin's complaint: this construction is "somewhat cumbersome and unjustified."

## Figures of interest — Chapter 6

- **Fig.6.1 (p.270):** Containment hierarchy of uncertainty formalisms (adapted from Klir [987]).
- **Fig.6.2 (p.274):** Two gambles $X, Y$ inside the convex cone of desirable gambles.
- **Fig.6.3 (p.274):** Interval $[\underline{P}(X), \overline{P}(X)]$ — agent's indecision range.
- **Fig.6.4 (p.300):** Pawlak rough-set lower / upper approximations of a set $A$ by elementary equivalence classes.
- **Fig.6.5 (p.302):** P-box envelope $\langle \underline{F}, \overline{F} \rangle$ of CDFs.
- **Fig.6.6 (p.305):** Inclusion diagram showing generalised p-boxes as a special case of random sets and probability intervals.
- **Fig.6.7 (p.308):** Quantisation vs granulation of "Age" variable in GTU.
- **Fig.6.8 (p.309):** Inscribed rectangle in product algebra under Liu's uncertain-measure extension.

## Criticisms of prior work — captured in Chapter 6

- Walley's IP via belief functions: Baroni-Vicig [94] argue BFs and coherent lower probabilities have *different roots*; common conceptual basis "doomed to fail" from TBM perspective *(p.276)*.
- Vague sets / intuitionistic fuzzy sets equivalence with belief: [1151]'s claim that BF theory is special case of vague-set theory is "simplistic and possibly flawed" *(p.288)*.
- Wilson's DS-default-logic translation: criticised by Pearl as misrepresenting "$a \to c$ with reliability $\alpha$" *(p.292)*.
- GTU: "generality is achieved in a rather nomenclative way, which explains the complexity and lack of naturalness of the formalism" *(p.308)*.
- Liu's uncertainty theory: "general lack of rigour and convincing justification … No mention of belief functions or other well-established alternative representations" *(p.310)*.
- Cohen-Grinberg endorsements *(p.315)*: "numerical representations of certainty hide the reasoning that produces them and limit one's reasoning about uncertainty"; numbers between 0 and 1 are an impoverished record.

## Design rationale captured in Chapter 6

- Choice of belief functions over generic 2-monotone lower probabilities: Möbius non-negativity is strictly stronger than 2-monotonicity (Proposition 38, p.277, $m(\Theta) \ge -1/2$ for arbitrary 2-monotone on $|\Theta|=3$ — the Möbius inverse of a coherent lower prob can be negative).
- Behavioural foundation: lower previsions / desirable gambles cleanly support a Dutch-book-style operational interpretation; BFs are coherent lower probabilities (closed under convex combination) but Cuzzolin treats their semantics as evidential rather than betting (cf. Kerkvliet [957]).
- Spohn over BF for rank-only beliefs: $\delta$ takes integer values — appropriate when all the agent has is *order of plausibility* (no quantitative grades).
- Game-theoretic over measure-theoretic probability: avoids commitment to a fixed measure; supports defensive forecasting against arbitrary betting strategies.
- Info-gap vs Walley/p-boxes: info-gap uncertainty is *unbounded* (not convex, not a probability) — appropriate when no plausible bound exists.
- Rough sets as belief: when focal elements are an equivalence-class partition with $m(A) = |A|/|\Theta|$, $\underline{q}$ is exactly $Bel$ (Prop 47, p.300); equivalence is via S5 modal logic [2053] linking lower-approximation with $\Box$.

## Open / research questions called out in Chapter 6

- Extension of Vovk-Shafer's prequential / game-theoretic principle to *non-repetitive* situations (e.g. belief theory) is "still being sought." *(p.312)*
- Whether BFs admit a coherent betting interpretation — Shafer [1605] attempted; Kerkvliet 2017 [957] revives; not yet settled. *(p.277)*
- Reconciling Liu's "uncertain measures" with the rest of the imprecise-probability literature given Liu's silence on competing formalisms. *(p.310)*
- Defensive forecasting [1864] for belief theory: not covered. *(p.315)*
- Whether descriptive notions like "endorsements" or "justifications" (Cohen-Grinberg) can be lifted to a formal numerical layer without losing the heuristics they emphasise. *(p.315)*

## Notable references cited (Chapter 6 selection)

- `[1874,1877]` Walley — lower/upper previsions, statistical reasoning with imprecise probabilities *(p.271+)*.
- `[1292]` Miranda — survey of lower previsions *(p.271)*.
- `[403,404]` de Finetti — gamble-based probability, prevision *(p.273-274)*.
- `[1912,1911]` Wang-Klir — coherent lower probabilities ↔ belief functions, Choquet integral comparisons *(p.276)*.
- `[94]` Baroni-Vicig — separation of BFs from coherent lower probabilities *(p.277)*.
- `[957]` Kerkvliet 2017 — recent betting interpretation of BFs *(p.277)*.
- `[283]` Choquet 1953 — capacities *(p.277)*.
- `[1781,1782]` Sugeno — fuzzy measures, λ-measures *(p.279)*.
- `[393]` De Campos-Huete-Moral — probability intervals, Choquet 2-monotone *(p.279, 280, 281)*.
- `[1134]` Lemmer-Kyburg — selection algorithm for probability intervals *(p.281)*.
- `[660]` Gaifman 1988 — higher-order probability spaces *(p.282)*.
- `[1087]` Kyburg — HOPs replaceable by joint marginals *(p.283)*.
- `[654]` Fung-Chong — metaprobability / Bayesian update on second-order *(p.283)*.
- `[2083]` Zadeh 1965 — fuzzy sets *(p.283)*.
- `[531]` Dubois — possibility theory *(p.284)*.
- `[447]` Denoeux — fuzzy-valued belief structures *(p.288)*.
- `[1526]` Saffiotti — belief function logic *(p.289)*.
- `[918,914,922]` Josang — subjective logic *(p.291)*.
- `[586]` Fagin-Halpern — probability axiomatisation, BF version *(p.291)*.
- `[786,787]` Halpern — logics of evidence and expectation *(p.291)*.
- `[44,771,1125,767]` Haenni-Lehmann-Kohlas — probabilistic argumentation, ABEL *(p.292)*.
- `[1481]` Reiter — default logic *(p.292)*.
- `[1939,1945]` Wilson — DS-default-logic *(p.292)*.
- `[125,124]` Benferhat-Saffiotti-Smets — ε belief assignments / system P *(p.293)*.
- `[10,1361]` Adams — ε semantics for conditionals *(p.293)*.
- `[1510,1513]` Ruspini — epistemic logic foundations *(p.293-294)*.
- `[1484,800,799,1485,804]` Resconi-Harmanec — modal logic interpretation *(p.294-295)*.
- `[1326,698,84]` Murai — soundness/completeness for modal+BF *(p.296)*.
- `[137]` Besnard-Kohlas — DS over Tarskian consequence relations *(p.296)*.
- `[777]` Hájek — Gödel-Löb modal probability of provability ↔ BFs *(p.296)*.
- `[205]` Bundy — incidence calculus *(p.296-297)*.
- `[77]` Baldwin — evidential support logic programming *(p.297)*.
- `[1442]` Provan — DS via propositional + provability *(p.297)*.
- `[1434, 408]` Pinkas / Dupin-Lang-Schiex — penalty logic ↔ ε-DS *(p.297)*.
- `[730]` Grosof — generalised probabilistic logic *(p.297, 317)*.
- `[1393,1396,1397,1658]` Pawlak / rough sets *(p.299-301)*.
- `[2057,2056]` Yao — granular computing, neighbourhood/zoom rough sets *(p.300-301, 316)*.
- `[1005]` Kopotek 1998 — DS as relational-database join measures *(p.300)*.
- `[605,2027,604]` Ferson — p-boxes for reliability *(p.301-303)*.
- `[486]` Destercke — generalised p-boxes / unification *(p.304)*.
- `[36]` Alvarez — Monte Carlo over copula-driven random sets *(p.304)*.
- `[1752,1753]` Spohn — ordinal/natural conditional functions *(p.305-307)*.
- `[1625]` Shenoy — Spohnian belief functions, local computation *(p.306-307)*.
- `[2091,2093]` Zadeh — perception-based GTU *(p.307)*.
- `[1177,1178,1179]` Liu — uncertainty theory, uncertain measures *(p.308-310)*.
- `[107]` Ben-Haim — info-gap *(p.310)*.
- `[782]` Hall — climate-change application of info-gap *(p.311)*.
- `[1615,1863,1862]` Shafer-Vovk — game-theoretic probability *(p.311+)*.
- `[1604]` Ville 1939 — capital-multiplication law *(p.312, 313)*.
- `[392]` Dawid — prequential principle *(p.312)*.
- `[1605]` Shafer — betting interpretation of DS *(p.312)*.
- `[397, 1292]` Cooman / Miranda — Vovk-Shafer ↔ Walley relations *(p.312)*.
- `[1864,1861]` Shafer-Vovk — defensive forecasting *(p.311, 315)*.
- `[1084]` Kumon et al. — game-theoretic strong LLN *(p.313)*.
- `[297,296]` Cohen-Grinberg — endorsements *(p.315)*.
- `[83,79]` Baldwin — fril-fuzzy *(p.315)*.
- `[2055,2058,1450,985]` Yao — granular computing constructions *(p.316)*.
- `[1100, 372]` Laskey — BF ↔ ATMS equivalence *(p.316)*.
- `[806]` Harper — Popper conditional / counterfactual *(p.316-317)*.
- `[1144,1145]` Lewis — counterfactual conditionals *(p.317)*.
- `[1620,1621]` Shastri / Shastri-Feldman — semantic-network evidential reasoning *(p.317)*.
- `[812,554]` MYCIN / PROSPECTOR *(p.317)*.
- `[727,256]` Groen-Mosleh / Cheeseman *(p.318)*.
- `[1375]` Padovitz et al. — multi-attribute utility for context *(p.319)*.
- `[857]` Hüllermeier — similarity-based inference / random-set imperfect specification *(p.319)*.
- `[1170]` Lin — neighbourhood systems ↔ BFs *(p.320)*.
- `[615]` Fine — comparative probability *(p.320)*.
- `[1957]` Wong et al. — comparative belief axiomatisation *(p.320)*.

## Implementation notes for propstore

This chunk is the most relevant single chapter in the book to several propstore design commitments. Concrete touch-points:

- **`propstore.world` (ATMS layer):** §6.14.4 *Laskey's assumptions* (p.316) is the canonical citation for "any DS inference network = ATMS justifications + assumption probabilities; belief = $P(\text{label} | \text{label-consistent})$." This is the formal warrant for propstore's choice to materialise micropublications as ATMS bundle nodes with context-labelled environments and propagate beliefs by environment consistency. Propstore's CLAUDE.md explicitly references this lineage; the Cuzzolin reading replaces the sketch with the source [1100] + [372] de Kleer.

- **`propstore.aspic_bridge` + `propstore.defeasibility`:** §6.6.2 (Josang subjective logic, p.291) and §6.6.4 (probabilistic argumentation systems, p.292) are the citations for propstore's bridge from Dung AFs to subjective-logic opinions; Haenni-Lehmann's "PAS = modelling layer on top of belief theory; DS = computational tool" is the warrant for keeping ASPIC+ as the inference layer and DS/SL as the carrier algebra. §6.6.5 (p.292-293) — Wilson, Benferhat-Saffiotti-Smets ε-belief assignments — gives the formal connection between defeasible defaults (system P, $\mathbf{Z}^+$, possibilistic logic, lexicographic), which is exactly what `propstore.defeasibility` operates over for CKR-style justifiable exceptions.

- **`propstore.belief_set` (AGM/IC merge):** §6.9 Spohn's theory (p.305-307). `δ`-functions are integer-valued OCFs supporting Darwiche-Pearl iteration; α-conditionalisation (Definition 112, p.306-307) is the canonical update rule that propstore's `belief_set.iterated_revision` implements. Shenoy [1625] local-computation result is the warrant for propagating belief updates without enumerating worlds. The Spohnian beta variant (Def 111) is what propstore should expose when both belief and disbelief degrees must be reported separately.

- **`propstore.dimensions` + p-boxes:** §6.8 (p.301-304) — every $(Bel,Pl)$ on $\mathbb{R}$ induces a p-box (eq.6.18); Alvarez Monte Carlo (Algorithm 14, p.304) is the importable algorithm if propstore needs to push p-boxes through dimension/parameter propagation. Generalised p-boxes (Def 108, p.304) are what should be used when CDFs are not comonotonic.

- **`propstore.world.assignment_selection_merge`:** §6.4 (higher-order probabilities, p.282-283) — Kyburg's reduction "HOPs = marginals of joint on $I \times \Omega$" (p.283) is essentially the design that propstore uses for assignment-selection merge: the index $I$ ranges over typed assignments, the joint distribution is the merge artifact. The Fung-Chong metaprobability update (p.283) gives the Bayesian update rule under that view.

- **Calibration / vacuous opinions:** §6.1.7 (p.276-277) — BFs as a strict sub-class of coherent lower previsions (closed under convex combination). The propstore principle "vacuous opinions represent total ignorance honestly" is exactly the *natural extension* construction (Def 94, eq.6.4, p.276): the smallest coherent lower prevision extending observed assessments. Provenance kinds `measured / calibrated / stated / defaulted / vacuous` map onto the way a $(Bel, Pl)$ pair is constructed (precise observation → BF on singletons; calibration → discounting; vacuous → $m(\Theta)=1$).

- **Modal logic of belief:** §6.6.7 (p.294-295) Resconi-Harmanec — every rational BF is realised by a finite T-model with the singleton valuation assumption (Prop 46). Propstore can use this when serialising a BF as a Kripke structure for ATMS / world-line reasoning.

- **Rough sets ↔ partition-focal BFs:** §6.7 (p.299-301). When propstore's concept layer encounters partitions of $\Theta$ (e.g. equivalence classes from `LexicalSense.reference`), Prop 47/48 (p.300-301) say the resulting belief is exactly the rough-set lower-approximation quality.

- **Game-theoretic probability:** §6.13 (p.311-315). Currently outside propstore scope, but the Vovk-Shafer protocol (Algorithms 15-17) is the natural framework for online belief-revision agents that need to defend forecasts against adversarial sequences; propstore.support_revision can borrow the martingale capital-process discipline if/when iterated revision needs adversarial evaluation.

- **What Cuzzolin warns against:** info-gap (§6.12) and Liu's uncertainty theory (§6.11) — propstore should avoid silent commitments to either; both are flagged as either non-convex / unbounded or insufficiently rigorous.

## Quotes worth preserving

- "Belief functions … are a special class of coherent lower previsions, closed under convex combination." *(p.276, ref [1874] §5.13)*
- "Common conceptual basis for BFs and coherent lower probabilities is doomed to fail [from the TBM perspective]." — Baroni-Vicig [94] *(p.276)*
- Ville's principle: "You will not multiply the capital you risk by a large factor." *(p.312)*
- "Generality is achieved by the GTU in a rather nomenclative way, which explains the complexity and lack of naturalness of the formalism." *(p.308)*
- "The general lack of rigour and of a convincing justification for a number of elements of the theory leaves the author of this book quite unimpressed with this work." — on Liu's uncertainty theory *(p.310)*
- "Numerical representations of certainty hide the reasoning that produces them and thus limit one's reasoning about uncertainty" — Cohen-Grinberg *(p.315)*
- "A proposition's belief equals the probability of its label conditioned on label consistency." — Laskey [1100] *(p.316)*
- "Most situations do require one to assess the uncertainty associated with set-valued observations, and therefore random sets (and their belief function incarnation) are a fundamental tool." *(p.269)*
- Cournot: "Events of small probability do not happen." *(p.312)*

## Pages read

All page images 256-340 in the chunk range belong to Chapter 5 (p.237-268) + Chapter 6 (p.269-320). Page-341 is the Part II divider page (no number); page-342 (book p.323) and onward are Chapter 7, the responsibility of chunk #5 reader. No pages failed to read.
