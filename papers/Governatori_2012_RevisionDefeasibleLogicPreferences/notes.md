---
title: "Revision of Defeasible Logic Preferences"
authors: "Guido Governatori, Francesco Olivieri, Simone Scannapieco, Matteo Cristani"
year: 2012
venue: "arXiv:1206.5833 [cs.AI] (v2, 23 Nov 2012)"
doi_url: "https://arxiv.org/abs/1206.5833"
pages: 41
affiliation: "Department of Computer Science, University of Verona, Italy; NICTA, Queensland Research Laboratory, Australia; Institute for Integrated and Intelligent Systems, Griffith University, Australia"
---

# Revision of Defeasible Logic Preferences

## One-Sentence Summary
Studies how to revise the *superiority/preference relation* `>` (not facts, not rules) of a Defeasible Logic theory so that the theory's defeasible extension changes to a desired conclusion; introduces 8 new auxiliary proof tags ($\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$) that locate where the change must happen; proves the general decision problem is **NP-complete** (3-SAT reduction); enumerates three "canonical cases" of revision and analyses each instance combinatorially; reframes AGM contraction/expansion/revision in terms of defeasible-theory belief sets and shows **only some AGM postulates survive** — concretely $(K\dot-1)$, $(K\dot-3)$, $(K\dot-6)$ hold; $(K\dot-2)$, $(K\dot-4)$ ($K\dot-4'$), $(K\dot-5)$, $(K\dot-7)$, $(K\dot-8)$ do not.

## Problem Addressed
Real reasoning (legal, security, forensics, medical) typically holds *facts* and *rules* fixed (a citizen cannot rewrite the Law) but allows participants to argue about *which rule beats which* — the superiority relation `>` over rules. Prior belief-revision work in non-monotonic logic addressed update of facts ([1]) and modification of rules ([2]) but **revision of the underlying preference / superiority relation has been neglected**. This paper builds the missing operator family and asks the AGM-rationality question for it.

## Key Contributions
- **Eight new auxiliary proof tags** for Defeasible Logic ($\pm\Sigma$, $\pm\sigma$, $\pm\omega$, $\pm\varphi$) that *do not change expressive power* but expose the structural roles different rules play in a derivation, enabling a clean revision calculus *(p.7-9)*.
- **Implication chains** between tags (Fig. 1, p.10): positive chain $+\Delta \to +\varphi \to +\partial \to \{+\omega, +\Sigma, +\sigma\}$; symmetric negative chain.
- **NP-completeness** of "is there `>'` such that `(F,R,>')` proves `q`?" via 3-SAT reduction (Theorem 16, p.16; the $\Gamma$-transformation in Definition 12, p.15).
- **Corollary 17** (p.17): there exist theories and literals for which a `>`-only revision is impossible.
- **Theorem 19** (p.23): revising `>` always yields again an acyclic `>` — superiority-revision preserves the structural well-formedness of the theory.
- **Three canonical cases** (Section 4.2-4.5): (1) $+\partial p \to -\partial p$; (2) $+\partial p \to +\partial \sim p$; (3) $-\partial p \to +\partial p$. Each enumerated tree of instances by $\pm\sigma\sim p, \pm\omega\sim p$ (Figs. 2, 3) with an explicit revision recipe per instance.
- **Two algorithmic strategies** for the second canonical case (p.20-21): the "unique winning chain" (faster, fewer rounds) vs. the "team defeater" approach (more priorities to track but only revisit the broken chain after a future defeat).
- **Belief-set reformulation** of a defeasible theory (Definition 20, p.24) as $BS(D) = BS^{+\partial}(D) \cup BS^{-\partial}(D)$: positive beliefs $= \{p: D \vdash +\partial p\}$, negative beliefs $= \{p: D \vdash -\partial p\}$.
- **Mapping AGM operators to canonical cases:** contraction $\leftrightarrow$ case 1; revision $\leftrightarrow$ case 2; expansion $\leftrightarrow$ case 3 (p.24).
- **AGM postulate audit** (Section 5.1 + 5.2):
  - $(K\dot-1)$ closure as "$D^-_p$ is a theory" — **holds** (Proposition 21, p.25 — superiority erasure preserves acyclicity).
  - $(K\dot-2)$ inclusion postulate $BS^{+\partial}(D^-_p) \subseteq BS^{+\partial}(D)$ and $BS^{-\partial}(D^-_p) \supseteq BS^{-\partial}(D)$ — **does not hold**: in any sceptical non-monotonic formalism, contracting $a$ can *create* new defeasible derivations of $p$ (witness: $\Rightarrow p$ and $a \Rightarrow \neg p$, p.25-26).
  - $(K\dot-3)$ vacuity (if $p \in BS^{-\partial}(D)$ then $BS(D^-_p) = BS(D)$) — **holds trivially** (p.26).
  - $(K\dot-4)$ success (if $p \in BS(D^-_p)$ then $D \vdash +\Delta p$) reformulated as $(K\dot-4')$ using $+\varphi$ — **does not hold** (Examples 6-8, p.27, illustrate counterexamples and counter-counterexamples; even the $+\varphi$-reformulation fails because tautologous-3-SAT-image theories produce non-contractible literals).
  - $(K\dot-5)$ recovery — **does not hold**; contraction is non-deterministic w.r.t. the inverse direction (Example 9, p.28).
  - $(K\dot-6)$ syntax-irrelevance — **holds trivially** (the language is restricted to literals so equivalence is identity, p.28).
  - $(K\dot-7)$ + $(K\dot-8)$ conjunctive contraction — **do not hold** for the same reason as $(K\dot-2)$ (Example 10, p.29).

## Study Design
Pure formal/theoretical paper (definitions, theorems, proofs, worked examples). No empirical/clinical study.

## Methodology
1. Reconstruct standard Defeasible Logic ($D = (F, R, >)$ with strict, defeasible, defeater rules and acyclic `>` over rules).
2. Restrict attention to defeasible rules only (footnote 2, p.5: justified by [12] showing equivalence-preserving normalisations).
3. Introduce eight auxiliary proof tags ($\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$) to *locate* the structural step where superiority changes can flip a conclusion.
4. Reduce 3-SAT to the revision-decision problem ($\Gamma$-transformation, Definition 12) to prove NP-completeness.
5. Enumerate the three canonical cases by which tag the original/target conclusion bears (Figs. 2 and 3), giving instance-by-instance revision algorithms.
6. Define a belief-set $BS(D)$ over a defeasible theory and check AGM postulates K\dot-1 through K\dot-8 against each.

## Defeasible Logic — Recap (Section 3)

### Definitions

- **Defeasible theory** $D = (F, R, >)$ with $F$ finite consistent literal set, $R$ finite rule set, `>` acyclic on $R$. *(p.5)*
- **Rule kinds:** strict ($\to$), defeasible ($\Rightarrow$), defeater ($\rightsquigarrow$). *(p.4)*
- **Tagged literals (standard):** $+\Delta q$, $-\Delta q$, $+\partial q$, $-\partial q$. *(p.5)*
- **Conclusion / extension:** $E(D) = (+\partial, -\partial)$ where $\pm\partial = \{l : D \vdash \pm\partial l\}$. *(Definition 1, p.7)*
- **Inconsistency (Definition 2, p.7):** $D$ is inconsistent iff some $p$ has both $D \vdash +\partial p$ and $D \vdash +\partial \sim p$ iff $D \vdash +\Delta p$ and $D \vdash +\Delta \sim p$.

### Standard proof conditions

$$
+\Delta:\ \text{If } P(n+1) = +\Delta q \text{ then } (1)\ q \in F\ \text{or}\ (2)\ \exists r \in R_s[q]\, \forall a \in A(r):\ +\Delta a \in P(1..n).
$$
*(p.5)*

$$
-\Delta:\ \text{If } P(n+1) = -\Delta q \text{ then } (1)\ q \notin F\ \text{and}\ (2)\ \forall r \in R_s[q]\, \exists a \in A(r):\ -\Delta a \in P(1..n).
$$
*(p.6)*

$$
+\partial:\ \text{If } P(n+1) = +\partial q \text{ then either } (1)\ +\Delta q \in P(1..n),\ \text{or } (2):\ -\Delta\sim q \in P(1..n)\ \text{and}\ \exists r \in R_{sd}[q]\, \forall a \in A(r): +\partial a \in P(1..n)\ \text{and}\ \forall s \in R[\sim q]\ \text{either}\ \exists a \in A(s): -\partial a \in P(1..n)\ \text{or}\ \exists t \in R_{sd}[q]: \forall a \in A(t): +\partial a \in P(1..n)\ \text{and}\ t > s.
$$
*(p.6)*

(Negative counterpart $-\partial$ obtained by *Principle of Strong Negation* [13], p.6.)

### New auxiliary tags (this paper, p.7-9)

5. $+\Sigma q$: there is a reasoning chain supporting $q$.
6. $-\Sigma q$: no reasoning chain supports $q$.
7. $+\sigma q$: there exists a reasoning chain for $q$ that is *not defeated* by any applicable attacking chain.
8. $-\sigma q$: every chain for $q$ is attacked by an applicable chain.
9. $+\omega q$: there is a chain for $q$ whose antecedents are *defeasibly* proved (chain "fails only on its last step" if it fails).
10. $-\omega q$: every chain for $q$ has at least one antecedent not defeasibly provable.
11. $+\varphi q$: there is a chain that defeasibly proves $q$ using elements such that *no rule for the opposite conclusion exists*.
12. $-\varphi q$: every chain for $q$ admits some rule for the opposite conclusion.

### Auxiliary proof conditions (verbatim, p.9-10)

$$
+\Sigma:\ P(n+1)=+\Sigma q \text{ iff } (1)\ +\Delta q \in P(1..n)\ \text{or}\ (2)\ \exists r \in R_{sd}[q]\, \forall a \in A(r): +\Sigma a \in P(1..n).
$$

$$
-\Sigma:\ P(n+1)=-\Sigma q \text{ iff } (1)\ +\Delta q \notin P(1..n)\ \text{and}\ (2)\ \forall r \in R_{sd}[q]: \exists a \in A(r): -\Sigma a \in P(1..n).
$$

$$
+\sigma:\ P(n+1)=+\sigma q \text{ iff } (1)\ +\Delta q \in P(1..n)\ \text{or}\ (2)\ \exists r \in R_{sd}[q]: (2.1)\ \forall a \in A(r):+\sigma a \in P(1..n)\ \text{and}\ (2.2)\ \forall s \in R[\sim q]\, \exists a \in A(s): -\partial a \in P(1..n)\ \text{or}\ s \not> r.
$$

$$
-\sigma:\ P(n+1)=-\sigma q \text{ iff } (1)\ +\Delta q \notin P(1..n)\ \text{and}\ (2)\ \forall r \in R_{sd}[q]: (2.1)\ \exists a \in A(r):-\sigma a \in P(1..n)\ \text{or}\ (2.2)\ \exists s \in R[\sim q]: \forall a \in A(s):+\partial a \in P(1..n)\ \text{and}\ s > r.
$$

$$
+\omega:\ P(n+1)=+\omega q \text{ iff } (1)\ +\Delta q \in P(1..n)\ \text{or}\ (2)\ \exists r \in R_{sd}[q]: \forall a \in A(r): +\partial a \in P(1..n).
$$

$$
-\omega:\ P(n+1)=-\omega q \text{ iff } (1)\ +\Delta q \notin P(1..n)\ \text{and}\ (2)\ \forall r \in R_{sd}[q]: \exists a \in A(r): -\partial a \in P(1..n).
$$

$$
+\varphi:\ P(n+1)=+\varphi q \text{ iff } (1)\ +\Delta q \in P(1..n)\ \text{or}\ (2)\ \exists r \in R_{sd}[q]: (2.1)\ \forall a \in A(r): +\varphi a \in P(1..n)\ \text{and}\ (2.2)\ \forall s \in R[\sim q]: \exists a \in A(s): -\Sigma a \in P(1..n).
$$

$$
-\varphi:\ P(n+1)=-\varphi q \text{ iff } (1)\ +\Delta q \notin P(1..n)\ \text{and}\ (2)\ \forall r \in R_{sd}[q]: (2.1)\ \exists a \in A(r): -\varphi a \in P(1..n)\ \text{or}\ (2.2)\ \exists s \in R[\sim q]: \forall a \in A(s): +\Sigma a \in P(1..n).
$$

(Negative counterparts via Principle of Strong Negation; details in [13,14].)

**Worked Example 1 (p.8-9)** uses 11-rule theory with `>` $= \{(r_1,r_4),(r_5,r_3)\}$. Result table on p.10 (Table 1) gives $a: +\partial,+\sigma; b: +\sigma; c: +\omega+\sigma; d: +\omega+\varphi; e:+\varphi; f:+\partial; \neg a: +\omega+\sigma; \neg b: +\sigma; \neg c: +\sigma; \neg d:+\partial$, etc. Demonstrates the tag mechanics.

### Implication chains (Fig. 1, p.10)

Positive: $+\Delta \to +\varphi \to +\partial \to (+\omega, +\Sigma, +\sigma)$.
Negative: symmetric — $(-\omega, -\Sigma, -\sigma) \to -\partial \to -\varphi \to -\Delta$.

Key non-implication: $+\sigma$ does **not** imply $+\omega$ (and $-\omega$ does not imply $-\sigma$). Witness from Example 1: $+\omega d \wedge -\sigma d$, $+\sigma\neg c \wedge -\omega\neg c$.

### Useful theoretical results

- **Proposition 3** (p.11): If $D \vdash +\varphi p$ for $p \notin F$, then $D \vdash -\Sigma\sim p$ — a $+\varphi$-provable literal admits no chain for its complement.
- **Proposition 4** (p.11): If $D \vdash +\partial p$ and $D \vdash +\omega\sim p$ (with $p \notin F$), then $D \vdash -\sigma\sim p$ — a $+\omega\sim p$ chain whose all antecedents are $+\partial$-proved is necessarily defeated at the last step.
- **Definition 5** (p.11) — *dependency*: $a$ depends on $b$ iff $b=a$ or every rule in $R[a]$ either has $b$ as an antecedent or has some antecedent that depends on $b$.
- **Proposition 6** (p.12): $+\partial p$ and $p$ depends on $q$ $\Rightarrow$ $+\partial q$ — defeasibility propagates backward through the dependency relation.
- **Definition 7** (p.12) — $\partial$-unreachable: $p$ is $\partial$-unreachable iff every rule in $R[p]$ either contains complementary antecedents that depend on a literal and its complement, or has an antecedent that is itself $\partial$-unreachable.
- **Proposition 8** (p.12): $\partial$-unreachable $p$ with $D \vdash +\partial p$ $\Rightarrow$ $D$ is inconsistent.
- **Proposition 9** (p.13): If $D$ is consistent and $p$ is $\partial$-reachable with $D \vdash +\Sigma p$, then there exists `>'` such that $(F,R,>') \vdash +\partial p$ — the *positive existence theorem* for revision.

### Counterexample showing both conditions of Prop 9 are needed (p.13)

Theory with $\Rightarrow_{r_1} a$, $\Rightarrow_{r_2} \neg a$, $a, \neg a \Rightarrow_{r_3} p$ has $+\Sigma a$ and $+\Sigma \neg a$ giving $+\Sigma p$, but $p$ is $\partial$-unreachable (depends on a contradiction), so no revision can prove $p$.

### Cystic-fibrosis worked legal example (Example 2, p.13-14)

Italian Legislative Act 40/2004 forbids medically-assisted reproduction except for sterility. Couple has cystic-fibrosis-affected genes. ECHR appeal forces inversion of `(r_1, r_3)` priority based on Art. 8 of the Convention. Concretely: $F=\{Embryo, GeneticAnomalies\}$, six rules, original `>` = $\{(r_1,r_3)\}$, revised `>'` = $\{(r_3,r_1)\}$.

## NP-completeness construction (Section 4.1)

### Definition 10 (p.14)
$D$ is *based on* $R$ iff $D = (\emptyset, R, >)$.

### Definition 11 (p.15) — tautology classification
For literal $p$ and rule set $R$:
1. $>$-$R$-tautological: $\forall D$ based on $R$, $D \vdash +\partial p$.
2. $>$-$R$-non-tautological: $\exists D$ based on $R$, $D \not\vdash +\partial p$.
3. $>$-$R$-refutable: $\exists D$ based on $R$, $D \vdash -\partial p$.
4. $>$-$R$-irrefutable: $\forall D$ based on $R$, $D \not\vdash -\partial p$.

A $>$-$R$-tautological literal cannot be revised away by any priority change.

### Definition 12 (p.15) — $\Gamma$-transformation (3-SAT $\Rightarrow$ defeasible theory)
For 3-SAT formula $\Gamma = \bigwedge_{i=1}^n C_i$ with $C_i = \bigvee_{j=1}^3 a_j^i$:
$$
R_\Gamma = \{r^a_{ij}: \Rightarrow a^i_j,\ r_{ij}: a^i_j \Rightarrow c_i,\ r_{\sim i}: \Rightarrow \sim c_i,\ r_i: \sim c_i \Rightarrow p\}.
$$

### Definitions 13-15 (p.15-16)
- *Decisive* theory: every literal proves $+\partial p$ or $-\partial p$.
- Proposition 14: acyclic atom-dependency-graph $\Rightarrow$ decisive.
- Lemma 15: every $\Gamma$-transformed theory is decisive.

### Theorem 16 (p.16) — main
Determining whether `>` can be revised so that $D \vdash \pm\partial p$ for desired sign is **NP-complete**.
- Membership in NP: oracle guesses `>'`, checks extensions in linear time [18].
- NP-hardness: $p$ is $>$-$R_\Gamma$-tautological iff $\Gamma$ is unsatisfiable.

### Corollary 17 (p.17)
There exist theories and literals for which a revision modifying only `>` is impossible.

## Three canonical revision cases (Section 4.2-4.5)

### The four legal-debate situations (p.17)
- (a) reasonable doubt: prove rules don't imply conclusion → case 1
- (b) beyond reasonable doubt: prove rules do imply conclusion → case 3
- (c) proof of innocence/guilt: derive opposite conclusion → case 2
- (d) impossible cases (subsumed by (a)-(c) tautological situations)

### Case 1: $+\partial p \to -\partial p$ (Section 4.3, Fig. 2 p.19)
Premise: $-\varphi p \wedge +\Sigma\sim p$ (else $+\varphi p$ blocks revision per Proposition 18, p.19).
Tree of instances over $\pm\sigma\sim p, \pm\omega\sim p$:
- $-\Sigma\sim p \wedge +\partial p$: revise rules of $-\varphi p$ chain to fire opposing rule.
- $+\omega\sim p \wedge +\sigma\sim p$: impossible (Proposition 4).
- $+\omega\sim p \wedge -\sigma\sim p$: erase the priorities defeating the $\sim p$ chain (Proposition 4).
- $-\omega\sim p \wedge +\sigma\sim p$: there's an undefeated $P_{\sim p}$; strengthen its rules' priorities to win.
- $-\omega\sim p \wedge -\sigma\sim p$: most generic; act on both $P_{\sim p}$ and $P_p$, possibly erase or invert priorities.

### Case 2: $+\partial p \to +\partial\sim p$ (Section 4.4)
Same instances. Two algorithmic strategies for $+\omega\sim p \wedge -\sigma\sim p$ (p.20-21):
1. **Unique winning chain**: pick chain in $N$ (chains for $\sim p$ where premises hold), invert priority for every $P_{ls}$ (chains for $p$ with priority at last step) it loses on, introduce new priorities to defeat remaining $P$.
2. **Team defeater**: case (a) $|P_{ls}| > |N|$: invert at last-proof-step priorities. Case (b) $|N| > |P_{ls}|$: pick $|P_{ls}|$ chains in $N$, invert at the defeating step, then iterate.

The first approach is faster and minimum-changes. The second is "team defeater" — robust against future single-rule defeats. Worked example p.21 demonstrates trade-off concretely: first approach yields $\{r_1>r_3, r_4>r_1, r_4>r_2\}$, second yields $\{r_3>r_1, r_4>r_2\}$.

### Case 3: $-\partial p \to +\partial p$ (Section 4.5, Fig. 3 p.22)
Premise: $-\partial\sim p \wedge +\Sigma p$. Note: $+\omega p \wedge -\sigma p$ is impossible.
- $+\omega p \wedge +\sigma p$: choose chain meeting both, introduce priorities equal to count of chains for $\sim p$ where $+\omega\sim p$ holds.
- $-\omega p \wedge +\sigma p$: analogous to case 1 instance.
- $-\omega p \wedge -\sigma p$: analogous to case 1 instance.

### Theorem 19 (p.23) — closure
Revising a superiority relation generates a superiority relation (still acyclic).

## AGM postulate audit (Section 5)

### Definition 20 (p.24) — belief set
$$
BS(D) = BS^{+\partial}(D) \cup BS^{-\partial}(D)
$$
where $BS^{+\partial}(D) = \{p: p \in D \text{ and } D \vdash +\partial p\}$, $BS^{-\partial}(D) = \{p: p \in D \text{ and } D \vdash -\partial p\}$.

### Mapping to canonical cases (p.24)
- Belief contraction $\leftrightarrow$ canonical case 1 ($+\partial p \to -\partial p$).
- Belief revision $\leftrightarrow$ canonical case 2 ($+\partial\sim p \to +\partial p$).
- Belief expansion (the "force-only-if-opposite-not-believed" version) $\leftrightarrow$ canonical case 3.

### Postulates for contraction (Section 5.1, p.25-29)

| Postulate | Statement (DL form) | Holds? | Reason |
|---|---|---|---|
| $(K\dot-1)$ | $D^-_p$ is a theory | YES | Proposition 21: erasing priorities preserves acyclicity *(p.25)* |
| $(K\dot-2)$ | $BS^{+\partial}(D^-_p) \subseteq BS^{+\partial}(D)$ and $BS^{-\partial}(D^-_p) \supseteq BS^{-\partial}(D)$ | NO | Counterexample $\Rightarrow p$, $a \Rightarrow \neg p$: contracting $a$ enables $+\partial p$ *(p.25-26)*; "behaviour holds in any sceptical non-monotonic formalism" |
| $(K\dot-3)$ | If $p \in BS^{-\partial}(D)$ then $BS(D^-_p) = BS(D)$ | YES | Trivial: target already met *(p.26)* |
| $(K\dot-4)$ / $(K\dot-4')$ | $p \in BS(D^-_p) \Rightarrow D \vdash +\Delta p$ (or $D \vdash +\varphi p$) | NO | Tautologous-3-SAT theories yield literals with no $+\Delta$/$+\varphi$ proof yet uncontractible (Examples 6-8, p.27) |
| $(K\dot-5)$ | $p \in BS^{+\partial}(D) \Rightarrow BS(D) \subseteq BS((D^-_p)^+_p)$ | NO | Contraction is irreversible / non-deterministic backward (Example 9, p.28) |
| $(K\dot-6)$ | $\vdash p \equiv q \Rightarrow BS(D^-_p) = BS(D^-_q)$ | YES | Literals only: equivalence = identity *(p.28)* |
| $(K\dot-7)$ | $BS^{+\partial}(D^-_p) \cap BS^{+\partial}(D^-_q) \subseteq BS^{+\partial}(D^-_{p,q})$ + dual | NO | Same reason as $(K\dot-2)$ — Example 10 (p.29) gives a 9-rule theory with concrete intersections |
| $(K\dot-8)$ | $p \in BS^{-\partial}(D^-_{p,q}) \Rightarrow BS^{+\partial}(D^-_{p,q}) \subseteq BS^{+\partial}(D^-_p)$ + dual | NO | Same as $(K\dot-7)$ |

### Postulates for revision (Section 5.2, p.30-31)

Throughout: $D \vdash +\partial\sim p$ and $D \vdash +\Sigma p$.

| Postulate | Statement (DL form) | Holds? | Reason |
|---|---|---|---|
| $(K*1)$ | $D^*_p$ is a theory | YES | Same as $(K\dot-1)$ — superiority revision preserves acyclicity *(p.30)* |
| $(K*2)$ | $p \in BS^{+\partial}(D^*_p)$ | YES | Definition of canonical case 2 forces $+\partial p$ *(p.30)* |
| $(K*3)$ | $BS^{+\partial}(D^*_p) \subseteq BS^{+\partial}(D^+_p)$ | YES | Trivially holds (only when both $+\partial\sim p$ and $-\partial\sim p$ apply, but they're mutually exclusive when expansion is "proper") *(p.30)* |
| $(K*4)$ | If $\sim p \in BS^{-\partial}(D)$ then $BS^{+\partial}(D^+_p) \subseteq BS^{+\partial}(D^*_p)$ | YES | Trivially — preconditions for revision and expansion are mutually exclusive *(p.30)* |
| $(K*5)$ | If $p$ consistent then $BS^{+\partial}(D^*_p)$ is consistent | YES | Literals are always consistent and consistent theories yield consistent extensions *(p.30)* |
| $(K*6)$ | If $\vdash p \equiv q$ then $BS^{+\partial}(D^*_p) = BS^{+\partial}(D^*_q)$ | YES | Literal-only language: equivalence is identity *(p.31)* |
| $(K*7)$ | $BS^{+\partial}(D^*_{p,q}) \subseteq BS^{+\partial}((D^*_p)^+_q)$ + dual | NO | Sceptical non-monotonic nature; Example 11 (p.31) gives 11-rule counterexample with $BS^{+\partial}(D^*_{p,q})=\{b,c,p,q\}$ vs. $BS^{+\partial}((D^*_p)^+_q)=\{a,c,p,q\}$ — neither contained in the other |
| $(K*8)$ | If $\neg q \in BS^{-\partial}(D^*_p)$ then $BS^{+\partial}((D^*_p)^+_q) \subseteq BS^{+\partial}(D^*_{p,q})$ + dual | NO | Same Example 11 *(p.31)* |

### Postulates for expansion (Section 5.3, p.32)

Throughout: $D \vdash -\partial p$, $D \vdash -\partial\sim p$, $D \vdash +\Sigma p$.

| Postulate | Statement (DL form) | Holds? | Reason |
|---|---|---|---|
| $(K+1)$ | $D^+_p$ is a theory | YES | Same as $(K\dot-1)$ |
| $(K+2)$ | $p \in BS^{+\partial}(D^+_p)$ | YES | Trivially — by hypothesis the expansion forces $+\partial p$ *(p.32)* |
| $(K+3)$ | $BS^{+\partial}(T) \subseteq BS^{+\partial}(T^+_p)$ and $BS^{-\partial}(T^+_p) \subseteq BS^{-\partial}(T)$ | (joint with K+4) | — |
| $(K+4)$ | If $p \in BS^{+\partial}(T)$ then $BS^{+\partial}(T^+_p) \subseteq BS^{+\partial}(T)$ and $BS^{-\partial}(T) \subseteq BS^{-\partial}(T^+_p)$ | YES | Premise $p \in BS^{+\partial}(T)$ does not hold under our preconditions, so the conditional is vacuously satisfied *(p.32)* |
| $(K+5)$ | If $BS^{+\partial}(D) \subseteq BS^{+\partial}(D')$ then $BS^{+\partial}(D^+_p) \subseteq BS^{+\partial}(D'^+_p)$ | NO | Sceptical non-monotonic nature, same reason as $(K\dot-2)$ *(p.32)* |
| $(K+6)$ | $BS(D^+_p)$ is the smallest belief set satisfying $(K+1)$-$(K+5)$ | (implicit) | Notion of "smallest resulting set" is meaningless in non-monotonic systems with tagged conclusions; expanding to prove $p$ via priority change necessarily falsifies some other previously provable literal *(p.33)* |

### Section 5.4 — Preference identities (p.33-34)

**Levi identity (LI)**: $BS(D^*_p) = BS((D^-_{\sim p})^+_p)$ — revising by $p$ = first contracting by $\sim p$ then expanding by $p$.

**Result**: Levi identity **does not hold** in this framework. Example 12 (p.33) provides a 7-rule witness where revising for $p$ vs. contracting-by-$\neg p$-then-expanding-by-$p$ gives different belief sets. Reason: revision concerns *why* a belief is obtained, not just *whether*; multiple-reason support means contraction and expansion need not invert.

**Harper identity (HI)**: $BS(D^-_p) = BS(D^*_{\neg p}) \cap BS(D)$ — contraction reconstructable from revision and the original theory.

**Result**: Harper identity **does not hold** either. Example 13 (p.34) provides a 5-rule witness. Reason: in non-monotonic logic the consequences of a formula cannot be controlled in general.

### Summary of section's contribution (p.34)
1. Canonical cases give precise formal meaning to AGM intuitions in DL.
2. Postulates reconstructed for canonical cases and adapted.
3. Confirms outcome of [2]: in general, AGM postulates describing inclusion relationships do not hold in DL, and shouldn't be expected for non-monotonic reasoning broadly.
4. Footnote 8 (p.34): canonical cases are general — the "from $+\partial p$ to $+\partial\neg p$" pattern is meaningful well beyond superiority-only revision.

## Section 6 — Related Work (p.34-36)

- **[21] Inoue & Sakama 1999** — closest related: abducting preference relations to derive intended conclusions. Different problem from modifying superiority.
- **[2] Billington et al. 1999** — revision of DL theories vs. AGM postulates: revises by introducing new exceptional rules and adapts AGM to non-monotonic. Same aim, different mechanism.
- **[22, 23] Boella, Governatori, Rotolo, van der Torre 2010** — Defeasible Logic for *lex minus dixit / magis dixit quam voluit* extensive vs. restrictive legal interpretation: revision via constitutive-rule-strength changes (adding/removing facts, strict rules, defeaters).
- **[4] Governatori & Rotolo 2010** — modelling abrogation/annulment in the legal domain. Shows AGM is inappropriate for legal-reasoning theories; theories fully satisfying AGM can produce legally meaningless outcomes.
- **[9] Governatori, Maher, Billington, Antoniou 2004** — argumentation semantics for DL: Dung grounded characterises ambiguity-propagating DL; alternative acceptability for ambiguity-blocking DL.
- **[26, 27] Moguillansky et al. 2008/2010** — Argument Theory Change applied to DeLP (Defeasible Logic Programming): a *defeater-activation* revision operator. Critique: imposes preferences over whole arguments, not single rules; argument can be warranted while all sub-arguments are defeated. Techniques here can be ported to DeLP.
- **[28-31] Prakken-Sartor, Antoniou (dynamic priorities), Brewka (well-founded extended LP), Modgil (hierarchical argumentation)** — extensions where the superiority relation is *dynamically derived from arguments and rules*. Differs from this paper which investigates modifying `>` to change conclusions, not deriving `>` from context. **Key remark (p.36)**: encoding all dynamic-derivation cases as static rules requires exponentially-many rules of the form $a_1, \ldots, a_n \Rightarrow (r_i > r_j)$.

## Section 7 — Conclusions and Further Work (p.36-38)

### Summary of contributions
- Eight tagged literals to simplify categorisation and revision calculus (Section 3).
- Three canonical cases of revision and systematic per-instance analysis (Section 4).
- Comparison to AGM: contraction $\leftrightarrow$ case 1, revision $\leftrightarrow$ case 2, expansion $\leftrightarrow$ case 3 (Section 5).
- Reconstructed and adapted AGM postulates for each operator.

### Future work directions (explicitly named, p.37-38)
1. **Multi-literal revision** (Example 14, p.37): change the status of *sets* of literals, not just single literals. Conditions for when this is possible are non-trivial.
2. **Scope-limiting revision** — protect "minimal" defeasible rules and "untouchable" `>` pairs (rules that win against all others, or principles explicitly stated by the legislator).
3. **Typed preferences** — preference type and algebraic structure can be applied [37]; partial-order generalisation [38, 39].
4. **Minimal change criteria** (Example 15, p.38): cardinality of `>` instances changed vs. cardinality of literals whose status changed in the extension. Two superiority revisions yielding different "minimality" by different metrics. Open questions: when is a revision minimal? How do minimality criteria compare?
5. **Alternative postulates** for non-monotonic belief revision: authors are sceptical that one postulate-set fits all non-monotonic logics; a logic-and-operator-specific axiomatisation is more realistic.

### Acknowledgements (p.38)
Earlier versions presented at NMR 2010 [40] and RuleML 2010 [41]. NICTA funded by Australian Government / ARC ICT Centre of Excellence / Queensland Government.

## Figures of Interest

- **Fig. 1 (p.10):** Implication chains over the proof tags (positive and negative). Shows $+\Delta \to +\varphi \to +\partial \to (+\omega, +\Sigma, +\sigma)$.
- **Fig. 2 (p.19):** Tree of revision instances for canonical case 1 ($+\partial p \to -\partial p$), branching on $\pm\omega\sim p$ and $\pm\sigma\sim p$.
- **Fig. 3 (p.22):** Analogous tree for canonical case 3 ($-\partial p \to +\partial p$).
- **Table 1 (p.10):** Conclusions for literals in worked Example 1 — minimal proof tag for each literal.

## Parameters / Quantities

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of new auxiliary proof tags | — | — | 8 | — | 7 | $\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$ |
| Decision-problem complexity class | — | — | NP-complete | — | 16 | Theorem 16, 3-SAT reduction |
| Extension-computation cost | — | — | linear in `|D|` | — | 16 | Cited from [18] |
| Number of canonical cases | — | — | 3 | — | 18 | $+\partial p \to -\partial p$, $+\partial p \to +\partial\sim p$, $-\partial p \to +\partial p$ |
| Rules in $\Gamma$-transformation | — | — | $4 \cdot |\text{lits}|$ | — | 15 | Polynomial blow-up |
| AGM contraction postulates checked | — | — | 8 | — | 25-29 | $K\dot-1$ through $K\dot-8$; 3 hold ($K\dot-1, K\dot-3, K\dot-6$), 5 fail |
| AGM revision postulates checked | — | — | 8 | — | 30-31 | $K*1$ through $K*8$; 6 hold ($K*1$-$K*6$), 2 fail ($K*7, K*8$) |
| AGM expansion postulates checked | — | — | 6 | — | 32 | $K+1$ through $K+6$; 4 hold ($K+1$-$K+4$), $K+5$ fails, $K+6$ vacuous |

## Testable Properties

- **Acyclicity preservation:** A `>`-only revision generates an acyclic `>` (Theorem 19, p.23).
- **Tautology obstruction:** If $p$ is $>$-$R$-tautological, no `>` change can refute $p$ (Definition 11, p.15).
- **Reachability gate:** If $D \vdash -\Sigma p$, no `>` change can prove $p$ (p.10, p.13).
- **$\partial$-unreachable obstruction:** If $p$ is $\partial$-unreachable, $D \vdash +\partial p$ implies $D$ inconsistent (Proposition 8, p.12).
- **Positive existence:** Consistent $D$, $\partial$-reachable $p$, $D \vdash +\Sigma p$ $\Rightarrow$ $\exists `>'`$ s.t. $(F,R,>') \vdash +\partial p$ (Proposition 9, p.13).
- **AGM partial-fit:** Revision-as-superiority-change satisfies $K*1$-$K*6$ but fails $K*7$, $K*8$; contraction satisfies $K\dot-1$, $K\dot-3$, $K\dot-6$ only; Levi and Harper identities both fail (Sections 5.1-5.4, p.25-34).
- **Argument-team-defeater advantage:** Team-defeater strategy (case 2 strategy 2, p.20-21) is robust against future single-rule defeats; unique-winning-chain strategy (strategy 1) makes fewer changes per round but must restart on defeat.

## Limitations (acknowledged by authors)

- Multi-literal revision not formalised (acknowledged future work).
- Minimality criterion for revision unspecified — paper offers no canonical "minimal change" metric.
- Typed preferences and partial-order preferences not handled.
- Postulate failure: AGM postulates $(K\dot-2)$, $(K\dot-4)$, $(K\dot-5)$, $(K\dot-7)$, $(K\dot-8)$, $(K*7)$, $(K*8)$, $(K+5)$, plus Levi (LI) and Harper (HI) identities all fail. Authors are sceptical that a "rational set of postulates" exists for non-monotonic belief revision in general.
- Defeaters and strict rules excluded from the technical analysis (footnote 2, p.5).

## Arguments Against Prior Work

- **AGM applied uncritically to non-monotonic theories produces legally meaningless results** [4]: theories satisfying AGM can be useless to lawyers (p.2-3, p.35).
- **Delgrande [5, 6] dismisses postulates 3 and 4** as inappropriate for non-monotonic belief revision, but this paper argues those same postulates *can* be adopted in the superiority-revision setting (p.3).
- **DeLP-based revision [26, 27]** imposes priorities over arguments (whole reasoning chains), which leads to anomaly: an argument can be warranted while all its sub-arguments are defeated (p.35-36). Single-rule priority avoids this.
- **Dynamic-priority approaches [28-31]** are different in kind: they *derive* `>` from rules and arguments rather than studying how to *modify* a given `>`. Encoding the dynamic case statically requires exponentially many rules (p.36).
- **Inoue & Sakama [21]** abducts priorities to support a conclusion — a conceptually different problem from modifying superiority.

## Design Rationale

- **Why fix facts and rules, vary `>` only?** In legal/regulatory reasoning, citizens cannot rewrite the law but can argue about which rule's priority should prevail (lex superior, lex specialis, lex posterior). The paper makes this asymmetry primary rather than treating preference change as a special case of rule change (p.1-4).
- **Why eight new tags?** Because Defeasible Logic's standard $\pm\Delta, \pm\partial$ doesn't expose *where* a chain fails (last step? earlier? attacker rules? no opposing rule?). The eight tags are not new expressive power; they are a forensic instrumentation for the revision calculus (p.7-9, p.18).
- **Why no defeaters/strict rules in revision analysis?** Footnote 2 (p.5): existing equivalence-preserving normalisations [12] let any DL theory be rewritten without defeaters and without strict rules participating in `>`. The restriction is strategic not foundational.
- **Why three canonical cases (and not four)?** Combinatorially $+\partial p \to -\partial p$, $+\partial p \to +\partial\sim p$, $-\partial p \to +\partial p$, and "$-\partial p \to -\partial\sim p$" exist; the fourth is partially subsumed by case 3 since $+\partial p$ implies $-\partial\sim p$ (p.18).
- **Why team-defeater alongside unique-winning-chain?** Team-defeater handles future defeats incrementally rather than restarting the whole revision (p.21).

## Worked Examples Referenced

- **Example 1 (p.8-10):** 11-rule baseline showing all 8 tags compute distinct minimal tags per literal.
- **Example 2 (p.13-14):** Italian cystic-fibrosis legal case (Art. 4 of Italian Legislative Act 40/2004 vs. ECHR appeal); concrete `>` inversion.
- **Example 3 (p.21):** $-\omega\sim p \wedge -\sigma\sim p$ instance (canonical case 2) — shows that defeating one rule may be insufficient.
- **Examples 4 & 5 (p.22-23):** Multiple revisions exist (different `>'`) for the same canonical-case-3 target.
- **Examples 6-8 (p.27):** $K\dot-4$ and $K\dot-4'$ counterexamples — non-contractible literals with no $+\Delta$/$+\varphi$ proof.
- **Example 9 (p.28):** $K\dot-5$ (recovery) failure.
- **Example 10 (p.29):** $K\dot-7$, $K\dot-8$ failure with concrete intersections.
- **Example 11 (p.31):** $K*7$, $K*8$ failure; 11-rule theory.
- **Example 12 (p.33):** Levi identity fails.
- **Example 13 (p.34):** Harper identity fails.
- **Examples 14, 15 (p.37-38):** Multi-literal revision and minimality-metric comparison.

## Implementation Notes for propstore

This paper is **directly relevant** to propstore's `belief_set` lane and the AGM-iterated workstream:

1. **Static-priority limitation closure:** Al-Anbaki et al. (2019) confessed in `papers/Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md` that their framework's superiority is static. This paper *is* the systematic study of dynamic superiority change. propstore's `propstore.belief_set` AGM revision can adopt the canonical-case taxonomy.
2. **NP-completeness as concrete budget:** Theorem 16 means a SAT-style solver is the reasonable engine for "is there `>'` proving $q$?" in propstore's argumentation layer. The 3-SAT reduction in Definition 12 is a constructive mapping, useful as a property-test generator.
3. **Belief set $BS(D) = BS^{+\partial} \cup BS^{-\partial}$:** Aligns with propstore's stance representation where both "p is supported" and "p is opposed" are first-class. Imports cleanly into `propstore.belief_set` typed records.
4. **Eight proof tags as defeasibility provenance:** In propstore's language, $\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$ are *typed structural provenance* for why a defeasible conclusion stands. They map to the project's "non-commitment discipline" — distinct provenance types ($+\sigma p$ "undefeated chain present" vs. $+\omega p$ "chain whose last step is the only weakness") would let a render policy resolve disagreement at multiple granularities.
5. **AGM postulate audit as a discipline:** This paper's mode of work (axiomatically-checked operators with explicit per-postulate adoption decisions) is a model for propstore's `propstore.belief_set.ic_merge` and Darwiche-Pearl iteration code: each postulate either holds, fails with a counterexample, or is reformulated.
6. **Team-defeater idea:** Maps to propstore's argumentation layer where a defeat may be witnessed by a *set* of arguments rather than one — useful for the merge-argument concept already in the design.
7. **Levi/Harper identity failure as architectural signal:** propstore should not derive contraction from revision (or vice-versa) by identity in non-monotonic settings. The two operators must be implemented independently.

## Relevance to Project

This paper is the **canonical reference** for "revising what wins, not what's true," which is exactly the architectural stance propstore takes with its render-time stance resolution and rule-level (rather than argument-level) preference handling. It also directly supports the existing AGM/Darwiche-Pearl workstream in `propstore.belief_set` by providing a non-monotonic-aware adaptation of the AGM postulates.

## Open Questions

- [ ] Does the canonical-case taxonomy generalise to ASPIC+ (where attacks/defeats are richer than DL's superiority)?
- [ ] How does this paper's NP-completeness interact with propstore's existing `propstore.aspic_bridge` complexity profile?
- [ ] Can the team-defeater strategy be implemented as a propstore stance-resolution policy?
- [ ] What is the relationship between this paper's eight proof tags and propstore's existing typed-provenance tags (`measured`, `calibrated`, `stated`, `defaulted`, `vacuous`)?
- [ ] Does propstore's `propstore.defeasibility` (CKR-style justifiable exceptions) need to absorb any of this paper's machinery for its lifting-rule layer?

## Related Work Worth Reading (cross-collection)

- **Billington et al. 1999 [2]** — original AGM-vs-defeasible-logic paper.
- **Alchourrón, Gärdenfors, Makinson 1985 [3]** — the original AGM paper.
- **Delgrande 2008/2010 [5, 6]** — answer-set program revision; partial AGM compliance.
- **Governatori & Rotolo 2010 [4]** — abrogation/annulment in DL.
- **Levi 1977 [19], Gärdenfors 1988 [20]** — Levi/Harper identity foundations.
- **Inoue & Sakama 1999 [21]** — abducting preferences.
- **Moguillansky et al. 2008/2010 [26, 27]** — DeLP argument-theory-change.
- **Prakken & Sartor 1997 [28]** — argument-based extended LP with priorities.

## Collection Cross-References

### Already in Collection
- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — cited as ref [10]; foundational work on the relationship between DL and LP. Provides the canonical `±Δ / ±∂` proof-tag system reused by this paper, plus Theorem 4.1 (LPwNF ⊆ DL under translation `T(P)`) and the team-of-rules trumping argument (Example 3, platypus) showing DL is strictly stronger than sceptical LPwNF.
- [Propositional Defeasible Logic has Linear Complexity](../Maher_2001_PropositionalDefeasibleLogicLinearComplexity/notes.md) — cited as ref [18]; load-bearing for this paper's NP-completeness reduction. Maher's `O(N)` algorithm (Theorem 5, p.17) is the linear-time DL extension oracle the reduction invokes. Together with Antoniou_2000_RepresentationResultsDefeasibleLogic (the representation/normalisation companion), Maher 2001 supplies the formal underpinning that lets this paper's `>`-revision sit at NP rather than higher.
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — conceptually adjacent (rational closure / non-monotonic conditionals); not directly cited but in the same scientific lineage as AGM-for-non-monotonic.

### Cited By (in Collection)
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this as ref [24] in the static-priority discussion; this paper directly addresses the dynamic-priority limitation Al-Anbaki et al. acknowledge as future work.

### New Leads (Not Yet in Collection)
- Billington, Antoniou, Governatori & Maher (1999) — "Revising non-monotonic belief sets: The case of defeasible logic" (KI-99) [ref 2] — direct precursor to this paper; first paper on AGM-vs-DL revision.
- Alchourrón, Gärdenfors & Makinson (1985) — "On the logic of theory change: Partial meet contraction and revision functions" (J. Symbolic Logic 50) [ref 3] — the foundational AGM paper.
- Governatori & Rotolo (2010) — "Changing legal systems: Legal abrogations and annulments in defeasible logic" (Logic J. IGPL 18) [ref 4] — DL-based legal-system revision; argues AGM is unsuitable for legal reasoning.
- Delgrande, Schaub, Tompits & Woltran (2008) — "Belief revision of logic programs under answer set semantics" (KR) [ref 5] — claims full AGM compliance under ASP semantics; this paper argues otherwise for DL.
- Delgrande (2010) — "A program-level approach to revising logic programs under the answer set semantics" (TPLP 10) [ref 6] — companion to ref [5].
- Levi (1977) — "Subjunctives, dispositions, and chances" (Synthese 34) [ref 19] — original Levi identity.
- Gärdenfors (1988) — "Knowledge in Flux: Modeling the Dynamics of Epistemic States" [ref 20] — original Harper identity.
- Inoue & Sakama (1999) — "Abducing priorities to derive intended conclusions" (IJCAI) [ref 21] — closest related work; abduction of priorities (vs. modification).
- Moguillansky, Rotstein, Falappa, García & Simari (2008/2010) — Argument Theory Change for DeLP [refs 26, 27] — explicitly compared and critiqued in this paper.
- Prakken & Sartor (1997) — "Argument-based extended logic programming with defeasible priorities" (J. Applied Non-Classical Logics 7) [ref 28] — legal-reasoning rule-priority encoding.
- Antoniou (2004) — "Defeasible logic with dynamic priorities" (Int. J. Intell. Syst. 19) [ref 29] — dynamic priority derivation, conceptually adjacent.
- Brewka (1996) — "Well-founded semantics for extended logic programs with dynamic preferences" (JAIR 4) [ref 30].
- Maher (2001) — "Propositional defeasible logic has linear complexity" (TPLP 1) [ref 18] — linear-time DL extension computation, key for this paper's NP-completeness proof. → NOW IN COLLECTION: [Propositional Defeasible Logic has Linear Complexity](../Maher_2001_PropositionalDefeasibleLogicLinearComplexity/notes.md). Confirms its load-bearing role: Maher's `O(N)` algorithm (Theorem 5, p.17) is the linear-time DL extension oracle the NP-completeness reduction here invokes — without it, the upper bound on the `>`-revision decision problem would be weaker.
- Boella, Governatori, Rotolo & van der Torre (2010) — "Lex minus dixit / lex magis dixit quam voluit" + "A logical understanding of legal interpretation" [refs 22, 23] — DL-based legal interpretation framework, contractive and extensive interpretations.
- Antoniou, Billington, Governatori & Maher (2001) — "Representation results for defeasible logic" (ACM TOCL 2) [ref 12] — equivalence-preserving normalisations used in footnote 2. → NOW IN COLLECTION: [Representation Results for Defeasible Logic](../Antoniou_2000_RepresentationResultsDefeasibleLogic/notes.md). The negative results in §5.2 of that paper (no modular sup-eliminator in general) are exactly the formal obstruction this revision paper routes around: rather than compile away `>`, introduce dedicated revision tags and reason about how to *modify* `>` in place.
- Sartor (2005) — "Legal Reasoning" (Springer) [ref 8] — legal-reasoning textbook; source of lex superior / lex posterior / lex specialis.
- Nute (1994) — "Defeasible logic" (Handbook of Logic in AI) [ref 32] — original DL formulation.
- Modgil (2006) — "Hierarchical argumentation" (JELIA) [ref 31] — dynamic-priority extension of argumentation.

### Conceptual Links (not citation-based)

**AGM and belief-revision foundations (propstore.belief_set lane):**
- [AGM Meets Abstract Argumentation: Contraction for Dung Frameworks](../Baumann_2019_AGMContractionDung/notes.md) — Baumann lifts AGM contraction to Dung AFs (set-of-extensions level); this paper lifts it to DL theories with rule-level superiority. Different lifting strategies for the same AGM-meets-non-monotonic problem.
- [Axiomatic Characterization of the AGM Theory of Belief Revision in a Temporal Logic](../Bonanno_2007_AGMBeliefRevisionTemporalLogic/notes.md) — Bonanno gives a temporal-logic axiomatisation of AGM; this paper gives a DL-with-superiority-revision adaptation. Both audit AGM's reach into non-classical settings.
- [Argument Theory Change: Revision Upon Warrant](../Rotstein_2008_ArgumentTheoryChangeRevision/notes.md) — Rotstein's ATC for argument-level change is exactly the framework this paper critiques (refs 26-27 in Section 6 are by the same group). Rule-level revision avoids the "warranted argument with all sub-arguments defeated" anomaly noted on p.36.
- [Constraints and changes: A survey of abstract argumentation dynamics](../Doutre_2018_ConstraintsChangesSurveyAbstract/notes.md) — survey covering enforcement, expansion, revision in abstract argumentation; this paper occupies the rule-level-DL slot in that landscape.
- [Expanding Argumentation Frameworks: Enforcing and Monotonicity Results](../Baumann_2010_ExpandingArgumentationFrameworksEnforcing/notes.md) — Baumann's enforcement problem (find an AF expansion that enforces a target conclusion) is the structural twin of this paper's "find a `>'` that proves $q$" problem; both NP-hard, both characterise success/failure cases.
- [Dynamics in Argumentation with Single Extensions: Abstraction Principles and the Grounded Extension](../Boella_2009_DynamicsArgumentationSingleExtensions/notes.md) — argumentation dynamics for grounded semantics; conceptually adjacent change-operator theory.

**Preferences in argumentation:**
- [Reasoning about preferences in argumentation frameworks](../Modgil_2009_ReasoningAboutPreferencesArgumentation/notes.md) — Modgil's PAF (preference-based AF); this paper's superiority is the rule-level analogue. PAF makes preferences first-class objects of argumentation.
- [Revisiting Preferences and Argumentation](../Modgil_2011_RevisitingPreferencesArgumentation/notes.md) — Modgil's reconsideration of preferences in argumentation; complements the rule-level approach here.
- [The ASPIC+ framework for structured argumentation: a tutorial](../Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md) — ASPIC+ also has a rule-priority mechanism. Direct integration target for propstore's `propstore.aspic_bridge` if it adopts this paper's revision operators.

**Defeasibility and contexts (propstore.defeasibility lane):**
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — CKR-style justifiable exceptions; the propstore.defeasibility module already implements these. This paper's superiority-revision is the "what changes" while CKR exceptions answer "what is currently in force" — complementary mechanisms.
- [A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility](../Bozzato_2020_DatalogDefeasibleDLLite/notes.md) — Datalog DL-Lite with defeasibility; another rule-priority setting where this paper's revision algorithms could plausibly transfer.
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — explicitly cites this paper as the dynamic-priority follow-up to their static-priority framework (already captured under "Cited By").
- [Defeasible Contextual Reasoning with Arguments in Ambient Intelligence](../Bikakis_2010_DefeasibleContextualReasoningArguments/notes.md) — Strong. Bikakis & Antoniou build a defeasible MCS with per-context total preference orderings $T_i$ over other contexts; this paper revises the rule-level superiority `>` in single-context DL. A multi-context generalisation of this paper's revision operators is exactly what Bikakis & Antoniou's $T_i$ would need to become dynamic. Direct pairing for any propstore work that wants dynamic per-context preferences.
- [Contextual Agent Deliberation in Defeasible Logic](../Dastani_2007_ContextualAgentDeliberationDefeasible/notes.md) — Strong. Governatori is co-author on both papers. Dastani et al. 2007 introduce *meta-rules* (rules whose consequents are rules) and an ⊗-on-rules connective Q that can functionally re-prioritise rules in a context-sensitive way; this 2012 paper revises the underlying superiority `>`. Open question worth pursuing: can the eight auxiliary tags ($\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$) and the three canonical revision cases of this paper be lifted from `>` to the meta-rule layer, giving a dynamic-priority calculus over both `>` and the meta-rule heads?

**Non-monotonic reasoning foundations:**
- [Defeasible Strict Consistency](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — Goldszmidt's defeasible-strict reasoning; foundational for understanding what "defeasible" means in this paper.
- [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md) — KLM preferential models; the abstract setting that DL specialises.
- [Rational Closure for Defeasible Description Logics](../Casini_2010_RationalClosure/notes.md) — rational-closure approach to defeasible DLs; alternative to DL's superiority-relation conflict resolution.
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — Lehmann-Magidor entailment and the rational-closure programme; AGM-adjacent foundations.
- [A Logic for Default Reasoning](../Reiter_1980_DefaultReasoning/notes.md) — Reiter's default logic; an alternative to DL with different conflict-resolution mechanisms.
- [Circumscription — A Form of Non-Monotonic Reasoning](../McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/notes.md) — circumscription as a non-monotonic alternative; preferences are implicit in the minimisation order rather than explicit on rules.

### Status checkpoint (reconcile in progress)

Reverse search done: 1 collection paper (Al-Anbaki 2019) cites this paper. Forward search done: 1 cited paper (Antoniou 2000) is in the collection; 17 high-priority new leads identified. Conceptual links done: 13 strong/moderate connections surfaced across AGM/argumentation-dynamics/preferences/defeasibility/NMR-foundations clusters. Backward annotation to Al-Anbaki 2019 still to do.

