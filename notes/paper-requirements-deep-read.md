# Paper Requirements Deep Read

**Date:** 2026-03-25
**Role:** Scout (Gauntlet protocol -- survey and report, do NOT implement)
**Task:** Extract core formal requirements, correctness properties, inter-paper connections, and common implementation warnings from 20 papers in the propstore collection.

---

## Part 1: Core Argumentation Theory (5 papers)

### 1. Dung 1995 -- Abstract Argumentation Frameworks

**Core formal definitions:**
- AF = (AR, attacks) where AR is a set of arguments, attacks is binary relation on AR. (p.326)
- Conflict-free: no A,B in S such that A attacks B. (p.326)
- Acceptable: A is acceptable w.r.t. S iff for each attacker B, S attacks B. (p.326)
- Admissible: conflict-free + each argument acceptable w.r.t. S. (p.326)
- Preferred extension: maximal admissible set. (p.327)
- Stable extension: conflict-free + attacks every argument not in S. (p.328)
- Grounded extension: least fixed point of F_AF(S) = {A | A acceptable w.r.t. S}. (p.329)
- Complete extension: admissible + contains every argument acceptable w.r.t. itself. (p.329)

**Properties that MUST hold:**
- Every AF has at least one preferred extension. (Corollary 12, p.327)
- Every stable extension is preferred, but not vice versa. (Lemma 15, p.328)
- Grounded = least complete extension. (Theorem 25, p.330)
- F_AF is monotonic. (Lemma 19, p.329)
- Complete extension E iff E = F_AF(E). (Lemma 24, p.330)
- Well-founded AF has exactly one extension that is simultaneously grounded, preferred, and stable. (Theorem 30, p.331)
- Empty set is always admissible. (p.327)

**Common implementation errors:**
- Self-attacking arguments (e.g., AF = ({A,B}, {(A,A),(A,B)})): A is in no preferred extension, so B may appear undefended. This edge case is acknowledged but not resolved. (p.328)
- Absence of stable extensions is NOT a bug -- it reflects genuine indeterminacy (stable marriage with gays example). (p.338)

**File:** `papers/Dung_1995_AcceptabilityArguments/notes.md`

---

### 2. Prakken 2010 -- ASPIC Framework

**Core formal definitions:**
- Argumentation system: tuple (L, contrariness, R_s union R_d, ordering). (Def 3.1, p.31 of notes)
- Knowledge base: K = K_n (axioms, unattackable) union K_p (ordinary premises) union K_a (assumptions) union K_i (issues). (Def 3.5)
- Arguments constructed recursively: atomic premises, then strict/defeasible rule application. (Def 3.6)
- Three attack types: undermining (on premises), rebutting (on defeasible conclusions), undercutting (on defeasible rule applicability via naming function). (Defs 3.12, 3.14, 3.16)
- Defeat: undercutting always succeeds; rebutting/undermining succeed only when attacker is not strictly weaker. (Def 3.20)

**Properties that MUST hold:**
- Sub-argument closure: every sub-argument of an argument in an extension is also in that extension. (Prop 6.1)
- Closure under strict rules: conclusions derivable by strict rules from extension conclusions are in the extension. (Prop 6.2)
- Consistency of extensions requires: well-formedness + closure under contraposition/transposition + reasonable ordering + consistent axioms. (Theorem 6.10)
- A firm and strict argument has NO attackers. (p.38 of notes)

**Common implementation errors:**
- If strict rules are NOT closed under transposition, consistency can FAIL. (Def 5.1-5.3, Example 4.4) This is the single most important structural requirement.
- Self-defeating arguments create problems especially for grounded semantics. (Section 7)
- Adding wrong antecedents to justifications: too few makes labels too general (nodes appear in wrong contexts), too many makes labels too specific (solutions are missed). (p.200-201 of companion problem-solving paper)

**File:** `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/notes.md`

---

### 3. Modgil & Prakken 2014 -- ASPIC+ Tutorial

**Core formal definitions:**
- Simplified AS = (L, R, n) with ordinary negation. (Def 3.1, p.35)
- K = (K_n, K_p) -- axioms and ordinary premises only (simplified from Prakken 2010's four-way split). (Def 3.3, p.35)
- Same three attack types and defeat relations as Prakken 2010.
- Last-link principle: compare only last defeasible rules applied. (Def 3.21, p.43)
- Weakest-link principle: compare ALL defeasible rules and ALL ordinary premises. (Def 3.23, p.43)

**Properties that MUST hold:**
- Same four rationality postulates as Prakken 2010 under same sufficient conditions.
- Undercutting attacks ALWAYS succeed as defeats regardless of preferences. (p.39-40)
- Contrary-based attacks (in generalized framework) ALWAYS succeed like undercutting. Contradictory-based attacks are preference-dependent. (p.58)

**Key design choice:**
- Last-link ordering suits legal/normative reasoning. Weakest-link suits epistemic reasoning. Choice is domain-dependent. (p.44)

**File:** `papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md`

---

### 4. Modgil & Prakken 2018 -- General Account with Preferences

**Core formal definitions:**
- Full generalized ASPIC+ with contrariness function (not just negation). (Def 2, p.8)
- CRITICAL CHANGE: Attack-based conflict-free (Def 14, p.14) replaces defeat-based conflict-free (Def 13). This is STRICTLY STRONGER and is the recommended definition.
- Reasonable argument orderings (Def 18, p.16-17): (i) strict+firm arguments dominate plausible/defeasible ones, (ii) strict+firm are never dominated, (iii) strict continuation preserves preference status.
- Elitist set comparison: exists X in Gamma s.t. forall Y in Gamma', X < Y. (Def 19, p.21)
- Democratic set comparison: forall X in Gamma, exists Y in Gamma' s.t. X < Y. (Def 19, p.21)

**Properties that MUST hold:**
- All four rationality postulates (sub-argument closure, strict closure, direct consistency, indirect consistency) proven for attack-conflict-free complete extensions of well-defined c-SAFs with reasonable orderings. (Thms 12-15, p.18-19)
- Transposition closure REQUIRED for well-definedness. (Def 12, p.13)
- Classical logic correspondence: stable extensions of classical-logic c-SAFs = Brewka's preferred subtheories. (Theorem 31, p.29)

**WARNING -- supersession:**
- This paper SUPERSEDES the 2014 tutorial. The 2014 tutorial uses defeat-based conflict-free; this paper uses attack-based conflict-free. The attack-based definition is stronger and should be used. (p.14-15)

**File:** `papers/Modgil_2018_GeneralAccountArgumentationPreferences/notes.md`

---

### 5. Pollock 1987 -- Defeasible Reasoning

**Core formal definitions:**
- Prima facie reason: P is a reason for Q that can be defeated by additional information. (Def 2.2, p.484)
- Rebutting defeater: reason for denying the conclusion. (Def 2.4, p.485)
- Undercutting defeater: reason for denying the connection between reason and conclusion. (Def 2.5, p.485)
- Warrant: P is warranted iff supported by an ultimately undefeated argument. (Principle 4.3, p.492)
- Ultimately undefeated: argument is level n for every n > some m, where level n+1 = level 0 arguments not defeated by any level n argument. (p.492)
- Self-defeating: argument supports a defeater for one of its own steps. (Def 4.5, p.495)

**Properties that MUST hold:**
- Warranted propositions are deductively consistent. (Principle 5.4, p.499)
- Warrant is closed under deductive consequence. (Principle 5.6, p.499)
- Self-defeating arguments MUST NOT contribute to warrant. (p.495-496)
- Reinstatement MUST occur: if a defeater is itself defeated, the original conclusion is restored. (p.492)
- Collective defeat: when two equally strong arguments lead to contradictory conclusions, neither is warranted. (p.493)

**Common implementation errors:**
- Treating all reasons as equal strength (OSCAR's simplification 3). This collapses real preference distinctions. (p.508)
- Undercutting defeaters have been "generally overlooked" in AI. Not implementing them is a fundamental gap. (p.485)
- Local vs global reasoning: real reasoners cannot survey all arguments, so justified belief only APPROXIMATES warrant. Deductively inconsistent justified beliefs ARE possible (unlike warrant). (p.504)

**File:** `papers/Pollock_1987_DefeasibleReasoning/notes.md`

---

## Part 2: Bipolar and Extensions (3 papers)

### 6. Cayrol & Lagasquie-Schiex 2005 -- Bipolar Argumentation

**Core formal definitions:**
- BAF = (A, R_def, R_sup) -- arguments with INDEPENDENT defeat and support relations. (Def 1, p.382)
- Supported defeat: support chain ending in defeat (A supports B, B defeats C => A supported-defeats C). (Def 3, p.383)
- Indirect defeat: defeat followed by support chain (A defeats B, B supports C => A indirect-defeats C). (Def 3, p.383)
- Set-defeat: includes direct, supported, and indirect defeat. (Def 4, p.383)
- Safe set: no argument simultaneously set-defeated and set-supported (or member) of S. (Def 7, p.385)
- Three admissibility levels: d-admissible (conflict-free + defence), s-admissible (safe + defence), c-admissible (conflict-free + closed for R_sup + defence). (Defs 9-11, p.386)

**Properties that MUST hold:**
- Safe implies conflict-free. (Property 1, p.385)
- Conflict-free + closed for R_sup implies safe. (Property 1, p.385)
- Hierarchy: c-admissible => s-admissible => d-admissible. (p.386)
- In acyclic BAFs: unique stable extension always exists (by instantiating Dung with set-defeats). (p.385)
- Stable extension may NOT be safe. (p.385-386) -- This is a key surprise.

**Common implementation errors:**
- Conflict-free in Dung's sense is INSUFFICIENT for bipolar coherence. Must use set-defeat, not just direct defeat. (p.384-385)
- Forgetting to compute supported and indirect defeats. These create NEW attack paths that do not exist in the raw defeat relation. (p.383)
- Results restricted to acyclic BAFs. Cyclic case is open. (p.387)

**File:** `papers/Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation/notes.md`

---

### 7. Amgoud et al. 2008 -- Bipolarity Survey

**Core formal definitions:**
- BAF = (A, R_def, R_sup) same as Cayrol 2005. (p.10)
- Local gradual valuation: v(A) = g(h_def(v(B_1),...,v(B_n)), h_sup(v(C_1),...,v(C_m))). (Def 9, p.15-16)
- Exclusivity constraint: if A R_sup B then NOT (A R_def B) and vice versa. (p.14)
- Closure for R_sup in admissibility: if A in S (admissible) and B R_sup A, then B in S. (p.23)
- Supported defeat: support chain ending in defeat. (Def 23, p.22)

**Properties that MUST hold:**
- Admissible sets MUST be closed for R_sup. (p.23)
- Exclusivity: no argument can both support and defeat the same argument. (p.14)
- Adding a defeater decreases value; adding a supporter increases value (monotonicity of gradual valuation). (p.15-16)

**Connection to other papers:**
- Gradual valuation provides an ALTERNATIVE to extension-based reasoning. The connection between the two approaches is not fully developed. (p.25)

**File:** `papers/Amgoud_2008_BipolarityArgumentationFrameworks/notes.md`

---

### 8. Baroni & Giacomin 2005 -- SCC-Recursiveness

**Core formal definitions:**
- SCC-recursive schema (Def 7): decompose AF along strongly connected components, process in topological order, apply base function per SCC. (p.3)
- CF2 semantics: base function = maximal conflict-free sets (NOT admissible). (p.7)
- Directionality: semantics determined only by relevant part of framework. SCC-recursive semantics automatically satisfy this. (p.2)

**Properties that MUST hold:**
- Grounded semantics IS SCC-recursive. (Prop 1, p.5)
- CF2 on 3-cycle: produces 3 extensions {a}, {b}, {c} (each node credulously accepted). Preferred produces only empty set. (p.7-8)
- Self-attacking argument: excluded from all extensions without affecting other arguments. (p.8)
- On acyclic AFs (all SCCs singletons): SCC-recursive semantics agree with standard semantics. (p.4-5)
- Directionality: adding/removing arguments not ancestors of a given argument in SCC DAG must not change that argument's status. (p.2)

**Common implementation errors:**
- CF2 departs from admissibility. It does NOT satisfy all of Dung's fundamental properties. This is intentional. (p.7)
- Preferred semantics fails on odd-length cycles (empty extension only). If your domain has odd cycles, consider CF2. (p.1-2, p.6)

**File:** `papers/Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation/notes.md`

---

## Part 3: Uncertainty and Probability (7 papers)

### 9. Josang 2001 -- Subjective Logic

**Core formal definitions:**
- Opinion: omega_x = (b, d, u, a) where b + d + u = 1, 0 < a < 1. (Def 9, p.7)
- Probability expectation: E(omega_x) = b + a*u. (Def 6, p.5)
- Evidence-to-opinion mapping: b = r/(r+s+2), d = s/(r+s+2), u = 2/(r+s+2). (Def 12, p.20-21)
- Consensus operator (fusion): b^{A diamond B} = (b^A * u^B + b^B * u^A) / kappa, where kappa = u_A + u_B - u_A*u_B. (Theorem 7, p.25)
- Discounting operator (trust transitivity): b^{A:B} = b_B^A * b_x^B. (Def 14, p.24)
- Vacuous opinion: (0, 0, 1, a) -- total ignorance. (p.8)

**Properties that MUST hold:**
- b + d + u = 1 for all valid opinions. (p.7)
- E(omega_x) satisfies Kolmogorov axioms. (Theorem 2, p.9)
- E(omega_{x AND y}) = E(omega_x) * E(omega_y) for independent propositions. (Proof 5, p.17)
- Consensus is commutative and associative. (p.25)
- Consensus reduces uncertainty: u_{A diamond B} <= min(u_A, u_B). (p.25-26)
- Discounting preserves relative atomicity: a_{A:B} = a_B. (p.24)
- Discounting with vacuous trust (b_B^A = 0) produces vacuous opinion. (p.24)
- Round-trip opinion->evidence->opinion preserves all components (when u > 0). (p.20-21)

**Common implementation errors:**
- Dogmatic opinions (u = 0): CANNOT be combined by consensus operator (kappa = 0, division by zero). (p.25)
- Dogmatic opinions have no Beta PDF representation. (p.21)
- Conjunction/disjunction REQUIRE independent frames of discernment. Dependent propositions cannot use these operators. (p.14)
- Vacuous opinion is NOT the same as 50/50 probability. E(vacuous) = a, but the uncertainty is maximal. This distinction is the whole point.

**File:** `papers/Josang_2001_LogicUncertainProbabilities/notes.md`

---

### 10. Hunter & Thimm 2017 -- Probabilistic Argumentation (Epistemic)

**Core formal definitions:**
- Probability function P: 2^Arg -> [0,1] with sum = 1. (p.7)
- Marginal: P(A) = sum over S containing A of P(S). (p.8)
- Epistemic labelling: P(A) > 0.5 => in, < 0.5 => out, = 0.5 => undec. (p.8)
- COH (coherent): if A attacks B then P(A) + P(B) <= 1. (p.9)
- RAT (rational): if A attacks B and P(A) > 0.5 then P(B) <= 0.5. (p.9)
- FOU (founded): P(A) <= 1 - P(B) for every attacker B of A. (p.10)

**Properties that MUST hold:**
- Class hierarchy: NEU subset INV subset COH subset SOPT subset RAT subset P(AF). (p.11-12, 16-17)
- For complete P: epistemic labelling L_P is a complete labelling in Dung's sense. (p.8)
- Maximum entropy gives unique, well-defined propagation from partial assessments. (p.22)
- Odd cycles under INV force NEU: all arguments get P(A) = 0.5. (Prop 9, p.17)
- Inconsistency with d_1 (Manhattan) satisfies all four properties: consistency, monotonicity, super-additivity, separability. (p.27)
- Framework decomposes by connected components (separability). (p.27-28)

**Common implementation errors:**
- Exponential representation: 2^n values for n arguments. Practical only for small AFs or with decomposition. (p.7)
- NP-complete to decide membership in constrained probability sets. (p.22)
- Constellation approach (probability over AF structure) and epistemic approach (probability over argument belief) are DIFFERENT things. Do not conflate them. (p.1-2)

**Connection to other papers:**
- Epistemic approach generalizes classical Dung semantics. Every classical extension corresponds to specific probability constraints. (p.12-13)
- Maximum entropy corresponds to grounded semantics for complete assignments with no partial info. (p.23)
- Consolidation operators map to AGM revision/update. (p.31-32)

**File:** `papers/Hunter_2017_ProbabilisticReasoningAbstractArgumentation/notes.md`

---

### 11. Li, Oren & Norman 2011 -- Probabilistic Argumentation Frameworks (PrAF)

**Core formal definitions:**
- PrAF = (A, P_A, D, P_D) where P_A: A->[0,1] and P_D: D->[0,1] assign independent probabilities to arguments and defeats. (Def 2, p.2)
- Induced DAF: subset of arguments and defeats sampled according to probabilities. (Def 3, p.2)
- Acceptance probability: P_PrAF(X) = sum over all induced DAFs where X is justified. (Eq 2, p.4)
- Monte Carlo approximation with Agresti-Coull stopping: N > 4p'(1-p')/epsilon^2 - 4. (Eq 5, p.7)

**Properties that MUST hold:**
- Sum of all induced DAF probabilities = 1. (Prop 1, p.4)
- When all P_A = 1 and P_D = 1: reduces to standard Dung evaluation. (p.2)
- MC iteration count is INDEPENDENT of PrAF size -- depends only on estimated probability. (p.9)
- Defeats only sampled when BOTH endpoints present. (Def 3, p.2-3, p.5)

**Common implementation errors:**
- Independence assumption: argument/defeat probabilities are treated as independent. Correlated uncertainties are NOT modeled. (p.3)
- Exact computation is exponential: only feasible for ~13 arguments. MC overtakes exact at ~13-15 arguments. (p.8)
- Agresti-Coull corrected CI needed, not normal approximation. Normal CI breaks when observed proportion is 0 or 1. (p.6-7)

**File:** `papers/Li_2011_ProbabilisticArgumentationFrameworks/notes.md`

---

### 12. Guo et al. 2017 -- Neural Network Calibration

**Core formal definitions:**
- ECE = sum_m (|B_m|/n) * |acc(B_m) - conf(B_m)|, M bins typically 15. (p.1)
- Temperature scaling: q_hat = max_k softmax(z_i / T)_k, T optimized on validation NLL. (p.5)
- T > 1 softens (reduces confidence), T < 1 sharpens. T does NOT change predictions (argmax invariant). (p.5)

**Properties that MUST hold:**
- Temperature scaling MUST NOT change model's top-1 predictions. (p.5)
- T > 1 MUST increase softmax entropy. (p.5)
- ECE = 0 iff perfectly calibrated (by construction). (p.1)
- Training NLL continues to decrease even as test NLL increases -- overfitting to confidence. (p.3)

**WARNING for propstore:**
- Raw softmax scores from NLI models and embedding similarity are NOT calibrated probabilities. They MUST be calibrated before being treated as probability estimates. (p.0)
- Deeper/wider models with batch normalization (i.e., all modern transformers) are expected to be overconfident. (p.2-3)
- Modern neural network confidence scores are systematically biased UPWARD. Any threshold-based reasoning over uncalibrated scores will produce different results than over calibrated scores. (p.5-7)

**File:** `papers/Guo_2017_CalibrationModernNeuralNetworks/notes.md`

---

### 13. Sensoy et al. 2018 -- Evidential Deep Learning

**Core formal definitions:**
- Network outputs evidence e_k >= 0 per class. Dirichlet parameters: alpha_k = e_k + 1. (p.3)
- Dirichlet strength: S = sum alpha_k = K + sum e_k. (p.3)
- Belief mass: b_k = e_k / S. Uncertainty mass: u = K / S. (p.3)
- Constraint: sum b_k + u = 1. (p.3)
- Expected class probability: p_hat_k = alpha_k / S. (p.3)
- Loss: SSE-based Bayes risk + annealed KL regularizer. (p.5-6)

**Properties that MUST hold:**
- u in (0, 1] where u = K/S; u = 1 when all e_k = 0 (total ignorance). (p.3)
- sum b_k + u = 1 for all predictions. (p.3)
- Increasing e_k MUST increase alpha_k and decrease u. (p.3)
- KL regularizer drives non-target evidence toward zero. (p.6)
- OOD data should have entropy approaching ln(K). (p.7-8)

**Connection to Josang 2001:**
- Sensoy's alpha_k corresponds to Josang's evidence counts (r, s). (Josang Def 12)
- The bijective mapping between opinions and Beta distributions (Josang Def 12) is exactly the mapping Sensoy exploits via the Dirichlet generalization.
- Combining evidence from multiple EDL models: use Josang's consensus operator on the evidence counts (Josang Def 13 -- evidence counts simply add).

**WARNING:**
- Cross-entropy loss variant generates EXCESSIVELY HIGH beliefs -- use SSE/Type II ML loss instead. (p.5)
- KL regularizer without annealing causes premature convergence to uniform Dirichlet. (p.6)

**File:** `papers/Sensoy_2018_EvidentialDeepLearningQuantifyClassification/notes.md`

---

### 14. Denoeux 2019 -- Decision-Making with Belief Functions

**Core formal definitions:**
- Mass function m: 2^Omega -> [0,1], Bel(A) = sum_{B subset A} m(B), Pl(A) = 1 - Bel(not-A). (p.12)
- Lower/upper expected utility: E_lower = sum_A m(A) min_{w in A} u(w), E_upper = sum_A m(A) max_{w in A} u(w). (p.15)
- Pignistic transformation: BetP(w) = sum_{A: w in A} m(A)/|A|. (p.17-18)
- Generalized Hurwicz: E_alpha = sum_A m(A) [alpha*min + (1-alpha)*max], alpha in [0,1]. (p.17)
- E-admissibility: act is E-admissible iff exists P in credal set P(m) s.t. it maximizes expected utility. Computable via LP. (p.27-28)

**Properties that MUST hold:**
- Bel(A) <= P(A) <= Pl(A) for all P in credal set. (p.12)
- E_lower <= E_pignistic <= E_upper. (p.15, 18)
- When m is Bayesian (all focal sets singletons): ALL criteria reduce to MEU. (p.33)
- Hurwicz at alpha=0: upper expected utility. At alpha=1: lower expected utility. (p.17)
- OWA at beta=0.5: equals pignistic. (p.19)
- E-admissibility choice set CONTAINS maximality choice set CONTAINS strong dominance choice set. (p.23, 26-27)
- Pignistic is the ONLY transformation satisfying linearity + MEU principle. (p.18)

**Relevance to propstore render layer:**
- Josang's E(omega_x) = b + a*u is EQUIVALENT to pignistic transformation for binary opinions. (p.17-18)
- Different render policies can use different alpha values: conservative (alpha=1, lower bound), optimistic (alpha=0, upper bound). (p.17)
- E-admissibility (via LP) gives the set of claims that could reasonably be "the answer" under some compatible probability. (p.27-28)
- Partial preferences (maximality, E-admissibility) are more honest than forcing a total order when information is genuinely imprecise. (p.23, 33-34)

**File:** `papers/Denoeux_2018_Decision-MakingBeliefFunctionsReview/notes.md`

---

### 15. Popescu & Wallner 2024 -- Exact DP for Probabilistic AFs

**Core formal definitions:**
- PAF = (A, R, P) where P: A union R -> (0,1] assigns probabilities. (p.2)
- Subframework probability: product of present/absent argument and attack probabilities. (p.3)
- P_sigma^ext(F, S): probability S is a sigma-extension. (p.3)
- P_sigma^acc(F, a): probability argument a is credulously accepted. (p.3)
- I/O/U labelling for tree-decomposition DP. (p.3)

**Complexity:**
- Counting subframeworks where S is an extension: #*P-complete. (Theorem 5, p.4)
- Counting subframeworks where argument is accepted: #*NP-complete (STRICTLY HARDER). (Theorem 6, p.5)
- Fixed-parameter algorithm w.r.t. treewidth exists. (Theorem 7, p.5)
- Table rows per bag bounded by 3^k (three labels per argument). (p.5)

**Properties that MUST hold:**
- Sum of P(F') over all subframeworks = 1. (p.2)
- For classical AF (all probabilities = 1): returns 1.0 for extensions, 0.0 for non-extensions. (p.2-3)
- Stable subset-of complete, preferred subset-of complete, complete subset-of admissible. (p.2)
- After forget node: rows with identical remaining labellings MUST be merged (summed). (p.7)

**When to use:**
- Tree-decomposition DP when treewidth <= 10-15. Monte Carlo when treewidth is high or unknown. (p.8)
- For higher treewidth (>10-15), exponential blowup in table size dominates. (p.8)

**File:** `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md`

---

## Part 4: ATMS/TMS (3 papers)

### 16. de Kleer 1986a -- Assumption-Based TMS

**Core formal definitions:**
- ATMS node: (datum, label, justifications, consequents, contradictory). (p.152)
- Justification: propositional Horn clause x_1,...,x_n => n. (p.143)
- Environment: set of assumptions. (p.143)
- Label: set of minimal consistent environments under which a node holds. (p.144)
- Nogood: inconsistent environment. (p.143)
- Context: consistent environment. (p.145)

**Four label properties that MUST hold:**
1. **Consistency**: no environment in any label is a superset of any nogood. (p.144)
2. **Soundness**: every environment in a label must entail the node given justifications. (p.144)
3. **Completeness**: every consistent environment from which node is derivable must be a superset of some label environment. (p.144)
4. **Minimality**: no environment in a label is a superset of another in the same label. (p.145)

**Properties that MUST hold:**
- Order independence: same assumptions + justifications must produce same labels regardless of introduction order. (p.150)
- Circular justifications are harmless: a => b and b => a produces no label propagation. (p.155)
- Nogoods closed under superset: if {A,B} is nogood, {A,B,C} is implied (need not be stored). (p.148)
- Label update terminates because finite number of assumptions. (p.152)

**Common implementation errors:**
- Direct justification retraction is expensive (isomorphic to LISP garbage collection). Use the defeasability-assumption workaround: conjoin extra assumption with justification, contradict it to retract. (p.153)
- Worst case is exponential (2^n environments). But in practice, most environments are inconsistent, so label sizes remain manageable. (p.152-153)

**File:** `papers/deKleer_1986_AssumptionBasedTMS/notes.md`

---

### 17. de Kleer 1986b -- Problem Solving with ATMS

**Core formal definitions:**
- Consumer architecture: rules that fire when antecedent nodes have nonempty labels. (p.201-202)
- Consumer restrictions: (1) only examine data, (2) only examine antecedent nodes, (3) justification antecedents = consumer antecedents exactly, (4) no internal state. (p.202)
- Control disjunctions: control{C1, C2, ...} partition search space. (p.205)
- Constraint language primitives: PLUS, TIMES, AND, OR, ONEOF, EQ, NOT, MINUS, DIVIDE. (p.209-213)

**Properties that MUST hold:**
- Consumers execute EXACTLY ONCE per node, then discarded. (p.202)
- Consumer type system prevents self-triggering. (p.202-203)
- ATMS never modifies or adds a justification to avoid a contradiction. (p.219)
- Control exercised BEFORE running consumers, not after. Once run, justifications are permanent. (p.204)
- No solution missed if control is later removed -- potential of exhaustivity not surrendered. (p.206)

**Common implementation errors:**
- Incorrect justification antecedents: too few makes labels too general (nodes in wrong contexts), too many makes labels too specific (solutions missed). (p.200-201)
- TIMES zero handling: when v=0, a oneof disjunction assumption set must be created. (p.212)
- Parity problem without control: exponential label growth (2^{i+2} + 2^i environments). WITH control: linear (4i environments). (p.216)

**WARNING:**
- ATMS is oriented toward finding ALL solutions. Extra cost incurred for fewer solutions (opposite of conventional TMS tradeoff). (p.137 of companion paper)
- No built-in support for time/action modeling. ATMS is purely inferential. (p.223)

**File:** `papers/deKleer_1986_ProblemSolvingATMS/notes.md`

---

### 18. Dixon & Foo 1993 -- ATMS and AGM Belief Revision

**Core formal definitions:**
- ATMS provability: E vdash_ATMS p iff (p in E) or (exists nogood C subset E) or (FB(p,E) != empty). (p.536)
- Foundational beliefs: FB(p,E) = {A in Label(p) | A subset E}. (p.537)
- Essential support: ES(p,E) = intersection of all foundational belief sets for p in E. (p.537)
- AGM entrenchment encoding: 5 levels E_1 < E_2 < E_3 < E_4 < E_5. (p.536)
- Key mapping: Ent(a) = Ent(a or b) encodes "a essentially supports b". (p.536-537)

**Properties that MUST hold (Theorem 1, p.538):**
- Behavioral equivalence: for all p, E vdash_ATMS p iff p in K (the AGM belief set).
- Lemma 1: Ent_E(a) = Ent_E(a or b) iff a in ES(b,E). (p.538)
- Lemma 2: a in ES(b,E) iff (E vdash_ATMS b) and ((E - {a}) not-vdash_ATMS b). (p.538)
- All five AGM entrenchment axioms (EE1-EE5) must hold at every step. (p.535)

**Key insight:**
- ATMS context switching = AGM expansion + contraction operations. (p.534)
- Coherence-based AGM logic CAN mimic foundational behaviour (bridging the foundational/coherence divide). (p.534)
- Rule revision (not supported by ATMS) could be implemented in AGM by decreasing entrenchment. (p.537)

**WARNING:**
- Minimal change principle cannot apply to entrenchment relation itself -- extensive revisions often necessary. (p.537)
- Entrenchment ordering is PARTIAL, not total. Many values remain unknown (acceptable since unneeded). (p.536)

**File:** `papers/Dixon_1993_ATMSandAGM/notes.md`

---

## Part 5: Structured/Applied (2 papers)

### 19. Fang et al. 2025 -- LLM-ASPIC+

**Core formal definitions:**
- Pipeline: Neural Grounding (LLM) -> Contradiction Detection -> Formal Argumentation (ASPIC+ solver). (p.1)
- Iterative belief formation: extract rules, transition to derive new beliefs, repeat. (p.3)
- Contradiction detection AFTER full belief set is built. (p.3)
- Grounded extension used exclusively (unique, always exists, most skeptical). (p.1)

**Properties that MUST hold:**
- Belief set monotonically grows during extract-transition loop. (p.3)
- Every contradiction pair (s_i, s_j) must satisfy: s_i = negation(s_j). (p.3)
- Axiom premises (K_n) CANNOT be undermined. (p.2)
- Strict rules CANNOT be undercut. (p.2)

**7 failure modes (error taxonomy, p.6):**
1. Error in extraction (LLM fails to match NL rules to formal counterparts)
2. Error in instantiation (LLM fails to derive conclusions from rules)
3. Error in trigger (LLM misidentifies which rules are satisfied)
4. Error in conclusion (LLM classifies final answer wrong)
5. NL-formal mismatch (discrepancy between NL and formal representations)
6. Overly narrow rule assumptions (LLM introduces spurious assumptions)
7. Misrepresentation of domain knowledge (LLM fabricates/hallucinates qualifiers)

**Key gap for propstore:**
- Beliefs are BINARY (in the set or not). No confidence/probability. This needs bridging to Hunter 2017's probabilistic reasoning or Josang 2001's opinion algebra. (p.6 of notes)
- Paper uses synthetic benchmark (BoardGameQA). Real-world extraction accuracy will be worse. (p.4)

**File:** `papers/Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/notes.md`

---

### 20. Odekerken et al. 2023 -- ASPIC+ with Incomplete Information

**Core formal definitions:**
- Observation-based AT: pair (AT, O) where O is observations. (Def 6)
- Four justification statuses: unsatisfiable (no argument exists), defended (in grounded extension), out (not in extension, defeated), blocked (neither defended nor definitively out). (Def 9)
- Queryables Q: unsettled literals whose truth value is unknown. (Def 11)
- Future AT: axioms can only grow by adding queryables, consistently. (Def 12)
- j-stability: literal's status remains j in ALL future ATs. (Def 13)
- j-relevance: queryable q is j-relevant for literal l if resolving q could be part of minimal information to stabilize l's status at j. (Def 15)

**Complexity results:**
- Justification status: polynomial time. (Section 4)
- Stability: coNP-complete. (Prop 7)
- Relevance: Sigma_2^P-complete. (Theorem 2)

**Properties that MUST hold:**
- Four justification labels partition all literals in L (for complete AT). (Section 3)
- Stability monotonicity: if j-stable, adding more observations cannot change status.
- Relevance soundness: if q is NOT j-relevant, resolving q in any direction does NOT change l's status.
- Grounded extension uniqueness: exactly one for any given complete AT.

**Connection to ATMS:**
- ATMS labels record which assumption sets support each datum; Odekerken determines which unsettled observations are relevant to a query's justification status. Both reason about conclusions under multiple possible worlds defined by unresolved choices.
- Complementary to Fang 2025: LLM extraction will inevitably produce incomplete KBs, and Odekerken's framework provides formal semantics for reasoning with whatever the LLM manages to extract.

**WARNING:**
- Grounded semantics ONLY. Extension to preferred/stable/other semantics is open. (Section 8)
- Binary observations only. No support for graded or probabilistic observations. (limitations)
- Scalability ceiling: ASP approach can time out (600s) for 100+ literals/rules. (p.8)

**File:** `papers/Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation/notes.md`

---

## Part 6: Cross-Paper Integration Requirements

### The Data Pipeline (what must flow where)

The papers collectively define a pipeline with strict ordering constraints:

1. **Raw model outputs (Guo 2017, Sensoy 2018)**: Neural network outputs are NOT calibrated probabilities. They must either be temperature-scaled (Guo) or produced via Dirichlet/EDL (Sensoy) before entering the system.

2. **Evidence to opinions (Josang 2001, Sensoy 2018)**: Evidence counts map to opinions via b = r/(r+s+2). Sensoy's alpha_k = e_k + 1 maps to Josang's evidence framework. Opinions MUST satisfy b + d + u = 1.

3. **Opinions before argumentation (Josang 2001 -> Hunter 2017 / Li 2011)**: Opinions can enter the argumentation layer as:
   - Epistemic probabilities on arguments (Hunter 2017): P(A) derived from opinion expectations E(omega)
   - Existence probabilities on arguments/defeats (Li 2011): P_A derived from opinion expectations
   - Either way, the COH constraint (P(A) + P(B) <= 1 when A attacks B) must be enforced at minimum.

4. **Structured arguments (Modgil & Prakken 2018 -> Dung 1995)**: ASPIC+ constructs arguments from premises and rules, generating a Dung-style AF. The AF then has Dung semantics applied. Requirements:
   - Transposition closure of strict rules (Modgil 2018 Def 12)
   - Consistent axioms (K_n)
   - Reasonable argument orderings (Modgil 2018 Def 18)
   - Attack-based conflict-free (not defeat-based) per Modgil 2018

5. **Bipolar extension (Cayrol 2005)**: If support relations exist, must compute set-defeat (including supported and indirect defeat), not just direct defeat. Admissible sets must be closed for R_sup.

6. **ATMS integration (de Kleer 1986)**: ATMS environments correspond to possible worlds. Labels track which assumption sets support each datum. Four label properties (consistency, soundness, completeness, minimality) must hold at all times.

7. **Decision at render time (Denoeux 2019)**: Pignistic transformation is the default (equivalent to Josang's E(omega_x) = b + a*u). Different render policies can use different decision criteria (Hurwicz with pessimism parameter, E-admissibility via LP).

### Critical Correctness Constraints (cross-paper)

| Constraint | Source | What breaks if violated |
|-----------|--------|------------------------|
| b + d + u = 1 | Josang 2001, p.7 | Invalid opinion, all downstream computation wrong |
| Transposition closure of strict rules | Modgil 2018, Def 12 | Extensions may be INCONSISTENT |
| Attack-based conflict-free (not defeat-based) | Modgil 2018, Def 14 | Rationality postulates may fail |
| Undercutting always succeeds regardless of preferences | Modgil 2014/2018 | Incorrect defeat computation |
| COH: P(A) + P(B) <= 1 when A attacks B | Hunter 2017, p.9 | Probability assignments incoherent with AF topology |
| Set-defeat (not just direct) for bipolar AFs | Cayrol 2005, Def 4 | Missing attack paths, wrong extensions |
| ATMS label minimality | de Kleer 1986, p.145 | Redundant environments, performance degradation |
| ATMS label consistency (no nogood superset in labels) | de Kleer 1986, p.144 | Contradictory conclusions presented as valid |
| Calibrate before treating as probability | Guo 2017 | Systematically overconfident judgments |
| Grounded extension is unique | Dung 1995, Theorem 25 | Implementation bug if multiple found |
| Empty set is always admissible | Dung 1995, p.327 | Basic sanity check failure |

### Surprising Findings

1. **Modgil 2018 supersedes 2014 in a non-obvious way.** The attack-based conflict-free definition (Def 14) is strictly stronger than the defeat-based one (Def 13). Under the 2018 definition, attack = defeat for conflict-free in practice (Prop 16, p.19), but the theoretical guarantee is that rationality postulates hold WITHOUT additional assumptions needed by the defeat-based definition. Implementations using defeat-based conflict-free from the 2014 tutorial may silently violate postulates.

2. **Stable extensions in bipolar AFs may not be safe.** (Cayrol 2005, p.385-386) A set can be the unique stable extension and yet be externally incoherent (simultaneously set-defeating and set-supporting the same argument outside the set). This is not a bug; it is a structural property of bipolar frameworks.

3. **CF2 semantics intentionally violates admissibility.** (Baroni 2005, p.7) This is by design to handle odd-length cycles where preferred semantics produces only the empty extension. If the codebase assumes all semantics satisfy admissibility, CF2 will break that assumption.

4. **Josang's consensus operator is undefined for two dogmatic opinions.** (Josang 2001, p.25) When u_A = u_B = 0, kappa = 0 and division by zero occurs. This is not an edge case -- it can happen whenever the system has two completely certain opinions to combine.

5. **Acceptability probability computation is strictly harder than extension probability.** (Popescu 2024, Theorem 6) Computing P^ext is #*P-complete; computing P^acc is #*NP-complete. These are different complexity classes. An implementation that handles one correctly does not automatically handle the other.

6. **Dixon 1993 proves ATMS context switching is AGM belief revision.** The entrenchment ordering only needs 5 discrete levels. This means ATMS operations have a clean belief-revision-theoretic interpretation that could inform how propstore manages world/context changes.

7. **Fang 2025's LLM-ASPIC+ uses binary beliefs only.** There is no mechanism for graded confidence. The paper achieves 67.1% on BoardGameQA, but this is a synthetic benchmark. The gap between binary beliefs (Fang) and probabilistic beliefs (Hunter/Li/Josang) is unresolved in the literature.
