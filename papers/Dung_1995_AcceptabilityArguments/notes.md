---
title: "On the Acceptability of Arguments and its Fundamental Role in Nonmonotonic Reasoning, Logic Programming and n-Person Games"
authors: "Phan Minh Dung"
year: 1995
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(94)00041-X"
pages: "321-357"
affiliation: "Division of Computer Science, Asian Institute of Technology, Bangkok, Thailand"
---

# On the Acceptability of Arguments and its Fundamental Role in Nonmonotonic Reasoning, Logic Programming and n-Person Games

## One-Sentence Summary

Introduces abstract argumentation frameworks --- a pair (AR, attacks) of arguments and an attack relation --- and defines multiple semantics (admissible, preferred, stable, grounded, complete extensions) that unify nonmonotonic reasoning, logic programming semantics, and n-person game solutions under a single formal theory of argument acceptability.

## Problem Addressed

Prior to this work, the notion of *acceptability* of arguments had not been formalized despite extensive work on argument *structure*. The paper addresses the gap between argument structure analysis and determining which arguments a rational agent should accept. It also addresses the disconnect between "internal stability" approaches (logic programming, nonmonotonic reasoning) and "external stability" approaches (argumentation), showing they are two sides of the same coin.

## Key Contributions

- Defines **argumentation frameworks** as abstract pairs AF = (AR, attacks) where AR is a set of arguments and attacks is a binary relation on AR
- Introduces a hierarchy of semantics: **admissible sets**, **preferred extensions**, **stable extensions**, **grounded extensions**, and **complete extensions**
- Proves that most major approaches to nonmonotonic reasoning (Reiter's default logic, Pollock's defeasible logic, logic programming with negation as failure) are special forms of argumentation
- Shows that solutions to **n-person games** (Von Neuman-Morgenstern solutions) and the **stable marriage problem** correspond exactly to stable extensions of corresponding argumentation frameworks
- Introduces a **meta-interpreter generation method** for argumentation systems using logic programming, analogous to the compiler-compiler idea

## Methodology

The paper proceeds in two steps: (1) develop an abstract, formal theory of argumentation based on acceptability of arguments, then (2) demonstrate its "correctness" through two arguments --- first showing it unifies nonmonotonic reasoning and logic programming, second showing it captures the logical structure of n-person games and the stable marriage problem.

## Key Definitions and Formal Framework

### Definition 2: Argumentation Framework

$$
AF = \langle AR, attacks \rangle
$$

Where: AR is a set of arguments, and attacks is a binary relation on AR, i.e. attacks $\subseteq AR \times AR$. An argument is an abstract entity whose role is solely determined by its relations to other arguments.

### Definition 5: Conflict-Free

A set S of arguments is **conflict-free** if there are no arguments A and B in S such that A attacks B.

### Definition 6: Acceptability and Admissibility

(1) An argument $A \in AR$ is **acceptable** with respect to a set S of arguments iff for each argument $B \in AR$: if B attacks A then B is attacked by S.

(2) A conflict-free set of arguments S is **admissible** iff each argument in S is acceptable with respect to S.

### Definition 7: Preferred Extension

A **preferred extension** of AF is a maximal (with respect to set inclusion) admissible set of AF.

### Definition 13: Stable Extension

A conflict-free set of arguments S is a **stable extension** iff S attacks each argument which does not belong to S.

### Definition 16: Characteristic Function

$$
F_{AF} : 2^{AR} \rightarrow 2^{AR}
$$

$$
F_{AF}(S) = \{A \mid A \text{ is acceptable with respect to } S\}
$$

### Definition 20: Grounded Extension

The **grounded extension**, denoted $GE_{AF}$, is the least fixed point of $F_{AF}$.

### Definition 23: Complete Extension

An admissible set S of arguments is a **complete extension** iff each argument which is acceptable with respect to S belongs to S.

### Definition 27: Finitary Framework

An argumentation framework AF = (AR, attacks) is **finitary** iff for each argument A, there are only finitely many arguments in AR which attack A.

### Definition 29: Well-Founded Framework

An argumentation framework is **well-founded** iff there exists no infinite sequence $A_0, A_1, \ldots, A_n, \ldots$ such that for each $i$, $A_{i+1}$ attacks $A_i$.

### Definition 31: Coherent and Relatively Grounded

(1) AF is **coherent** if each preferred extension of AF is stable.
(2) AF is **relatively grounded** if its grounded extension coincides with the intersection of all preferred extensions.

### Definition 32: Controversial, Limited Controversial, Uncontroversial

An argument B **indirectly attacks** A if there exists a finite sequence $A_0, \ldots, A_{2n+1}$ such that $A = A_0$ and $B = A_{2n+1}$, and for each $i$, $0 \leq i \leq 2n$, $A_{i+1}$ attacks $A_i$. B **indirectly defends** A if there exists a similar sequence of length $2n$.

(1) AF is **uncontroversial** if none of its arguments is controversial.
(2) AF is **limited controversial** if there exists no infinite sequence $A_0, \ldots, A_n, \ldots$ such that $A_{i+1}$ is controversial with respect to $A_i$.

## Key Theorems

### Lemma 10 (Fundamental Lemma)

Let S be an admissible set of arguments, and A and A' be arguments which are acceptable with respect to S. Then:
(1) $S' = S \cup \{A\}$ is admissible, and
(2) A' is acceptable with respect to S'.

### Theorem 11

(1) The set of all admissible sets of AF form a complete partial order with respect to set inclusion.
(2) For each admissible set S of AF, there exists a preferred extension E of AF such that $S \subseteq E$.

### Corollary 12

Every argumentation framework possesses at least one preferred extension.

### Lemma 14: Characterization of Stable Extensions

S is a stable extension iff $S = \{A \mid A \text{ is not attacked by } S\}$.

### Lemma 15

Every stable extension is a preferred extension, but not vice versa.

### Lemma 18

A conflict-free set S of arguments is admissible iff $S \subseteq F(S)$.

### Lemma 19

$F_{AF}$ is monotonic (with respect to set inclusion).

### Lemma 24

A conflict-free set of arguments E is a complete extension iff $E = F_{AF}(E)$.

### Theorem 25: Relations Between Semantics

(1) Each preferred extension is a complete extension, but not vice versa.
(2) The grounded extension is the least (with respect to set inclusion) complete extension.
(3) The complete extensions form a complete semilattice with respect to set inclusion.

### Lemma 28

If AF is finitary, then $F_{AF}$ is $\omega$-continuous.

### Theorem 30

Every well-founded argumentation framework has exactly one complete extension which is grounded, preferred, and stable.

### Theorem 33

(1) Every limited controversial argumentation framework is coherent.
(2) Every uncontroversial argumentation framework is coherent and relatively grounded.

### Corollary 36

Every limited controversial argumentation framework possesses at least one stable extension.

### Theorem 37: N-Person Games

Let IMP be the set of imputations of a cooperative n-person game G and let attacks be the corresponding domination relation between them. Then each NM-solution of (IMP, attacks) interpreted as an argumentation framework is a stable extension, and vice versa.

### Theorem 38: Core of N-Person Games

Let IMP be the set of imputations of an n-person game G and let attacks be the corresponding domination relation. Then the core of G coincides with $F(\phi)$ where F is the characteristic function of (IMP, attacks) interpreted as an argumentation framework.

### Theorem 39: Stable Marriage Problem

A set $S \subseteq AR$ constitutes a solution to the SMP iff S is a stable extension of the corresponding argumentation framework.

### Theorem 43: Default Logic Correspondence

Let $T = (D, W)$ be a default theory. Let E be an R-extension of T and E' be a stable extension of $AF(T)$. Then:
(1) $arg(E)$ is a stable extension of $AF(T)$.
(2) $flat(E')$ is an R-extension of T.

### Theorem 47: Pollock's Defeasible Reasoning

(1) An argument A is indefeasible iff $A \in AR_{inf}$.
(2) $AR_{inf} \subseteq GE_{AF}$.
(3) If AF is finitary, then $AR_{inf} = GE_{AF}$.

### Theorem 49: Logic Programming (Negation as Possibly Infinite Failure)

Let P be a logic program. Then a Herbrand interpretation M is a stable model of P iff there is a stable extension E of $AF_{napif}(P)$ such that $M \cup \neg.CM = \{k \mid \exists(K,k) \in E\}$.

### Theorem 50: Well-Founded Model

Let P be a logic program, and WFM be the well-founded model of P. Let GE be the grounded extension of $AF_{napif}(P)$. Then $WFM = \{h \mid \exists(K,h) \in GE\}$.

### Theorem 52

Let P be an arbitrary logic program. Then the stable, well-founded and preferred extension semantics of P are in general incomputable.

### Theorem 55: Clark's Completion (Negation as Finite Failure)

Let P be an arbitrary logic program. Then a Herbrand interpretation M is a model of Clark's completion of P, $comp(P)$, if there is a stable extension E of $AF_{naff}(P)$ such that $M \cup \neg.CM = \{k \mid \exists(K,k) \in E\}$.

### Theorem 56: Fitting's Model

Let P be a logic program, and FM be Fitting's model of P. Let GE be the grounded extension of $AF_{naff}(P)$. Then $FM = \{h \mid \exists(K,h) \in GE\}$.

### Theorem 62: Meta-Interpreter Architecture

Let AF = (AR, attacks) be an argumentation framework and E be an extension of AF. Then:
(1) E is a stable extension of AF iff m(E) is a stable model of $P_{AF}$.
(2) E is a grounded extension of AF iff $m(E) \cup \{\neg defeat(A) \mid A \in E\}$ is the well-founded model of $P_{AF}$.
(3) The well-founded model and Fitting's model of $P_{AF}$ coincide.

Where $P_{AF} = APU + AGU$ with:
- $APU = \{C1, C2\}$ where $C1: acc(X) \leftarrow \neg defeat(X)$ and $C2: defeat(X) \leftarrow attack(Y, X), acc(Y)$
- $AGU = \{attack(A,B) \leftarrow \mid (A,B) \in attacks\}$

## Parameters

This is a purely theoretical/formal paper. There are no empirical parameters, numerical constants, or measurable quantities.

## Implementation Details

### Meta-Interpreter Architecture (Section 5)

An argumentation system consists of two components:
1. **AGU (Argument Generation Unit)**: generates arguments and the attack relationship between them
2. **APU (Argument Processing Unit)**: determines acceptability of arguments

The APU is a logic program with two clauses:
- C1: $acc(X) \leftarrow \neg defeat(X)$ --- an argument X is acceptable if it is not defeated
- C2: $defeat(X) \leftarrow attack(Y, X), acc(Y)$ --- an argument X is defeated if it is attacked by an acceptable argument Y

The AGU generates facts of the form $attack(A, B)$ for each $(A, B) \in attacks$.

This architecture acts as a **schema for generating meta-interpreters** for argumentation systems, analogous to a compiler-compiler.

### Argumentation Framework for Default Logic (Section 4.1)

Given a default theory $T = (D, W)$:
- $AR_T = \{(K, k) \mid K \subseteq Jus(D), K$ is a support for $k$ with respect to $T\}$
- $(K, k)$ attacks $(K', k')$ iff $\neg k \in K'$

### Argumentation Framework for Logic Programming --- Negation as Possibly Infinite Failure (Section 4.3.1)

Given logic program P:
- $AR = \{(K, k) \mid K$ is a support for $k$ with respect to $P\} \cup \{(\{\neg k\}, \neg k) \mid k$ is a ground atom$\}$
- $(K, h)$ attacks $(K', h')$ iff $h^* \in K'$

### Argumentation Framework for Logic Programming --- Negation as Finite Failure (Section 4.3.2)

Given logic program P:
- $AR = \{(K, k) \mid \exists C \in G_P: head(C) = k$ and $body(C) = K\} \cup \{(\{\neg k\}, \neg k) \mid k$ is a ground atom$\}$
- $(K, h)$ attacks $(K', h')$ iff $h^* \in K'$

### Stable Marriage Problem Encoding (Section 3.2)

Given sets M (men) and W (women):
- $AR = M \times W$
- $(C, D)$ attacks $(A, B)$ iff (1) $A = C$ and A prefers D to B, or (2) $D = B$ and B prefers C to A

## Figures of Interest

- **Fig (page 5/p.325):** Dependency tree showing Section 2 is prerequisite for Sections 3, 4, and 5
- **Fig (page 29/p.349):** Architecture diagram showing AGU feeding attack relations to APU, which outputs acceptable arguments

## Results Summary

The paper establishes a complete hierarchy of argumentation semantics and proves their correspondences:
- Stable $\subset$ Preferred $\subset$ Complete (as sets)
- Grounded = least Complete extension = least fixed point of $F_{AF}$
- Every stable extension is preferred, but not vice versa
- Every preferred extension is complete, but not vice versa
- Well-founded frameworks have a single extension that is simultaneously grounded, preferred, and stable
- The framework unifies Reiter's default logic, Pollock's defeasible reasoning, and logic programming (both finite and infinite failure) as special cases

## Limitations

- Arguments are treated as abstract entities with no internal structure --- this abstraction is powerful but means the theory cannot differentiate between types of attacks (e.g., rebutting vs. undercutting)
- The theory does not address the **strength** of arguments or attacks --- all attacks are treated equally
- For logic programming with negation as possibly infinite failure, the resulting semantics are in general **incomputable** (Theorem 52)
- The problem of self-defeating arguments (e.g., argumentation framework $\langle\{A,B\}, \{(A,A), (A,B)\}\rangle$) is acknowledged but not resolved
- The theory provides no mechanism for **preference** among arguments beyond the basic attack relation

## Testable Properties

- Every argumentation framework has at least one preferred extension (Corollary 12)
- Every stable extension is a preferred extension (Lemma 15)
- Not every preferred extension is stable (Lemma 15, counterexample: AF with AR={A} and attacks={(A,A)})
- The empty set is always admissible
- $F_{AF}$ is monotonic with respect to set inclusion (Lemma 19)
- Every well-founded framework has exactly one complete extension which is grounded, preferred, and stable (Theorem 30)
- Every limited controversial framework is coherent (Theorem 33(1))
- Every limited controversial framework has at least one stable extension (Corollary 36)
- For finitary frameworks, $F_{AF}$ is $\omega$-continuous (Lemma 28)
- Grounded extension = intersection of all preferred extensions, for uncontroversial frameworks (Theorem 33(2))
- NM-solutions of cooperative n-person games = stable extensions of corresponding argumentation framework (Theorem 37)
- Solutions to stable marriage problem = stable extensions of corresponding argumentation framework (Theorem 39)
- R-extensions of default theories = stable extensions of corresponding argumentation framework (Theorem 43)

## Relevance to Project

This paper is foundational for the propstore's world model architecture. Argumentation frameworks provide the theoretical basis for reasoning about conflicting claims: when two claims from different papers contradict each other, they can be modeled as arguments that attack each other. The different semantics (preferred, stable, grounded) offer different strategies for resolving conflicts --- credulous (preferred) vs. skeptical (grounded). The paper also connects directly to the truth maintenance systems already in the collection (Doyle 1979, de Kleer 1986) since both TMS and argumentation deal with maintaining consistent belief sets under conflicting evidence.

## Open Questions

- [ ] How to extend the framework with argument strength/preference (addressed in Dung's later work [13])
- [ ] How to handle self-defeating arguments systematically
- [ ] Practical computational complexity of preferred/stable extension computation for real-world argumentation frameworks
- [ ] Connection to structured argumentation frameworks (ASPIC+, ABA) that build on this abstract foundation

## Related Work Worth Reading

- Bondarenko, Toni and Kowalski [7] --- assumption-based framework unifying many nonmonotonic approaches
- Pollock [45, 46] --- defeasible reasoning theory based on prima facie reasons and defeaters
- Reiter [52] --- default logic (R-extensions correspond to stable extensions)
- Lin and Shoham [36] --- argument systems as uniform basis for nonmonotonic reasoning
- Kakas, Kowalski and Toni [27] --- argumentational approach to logic programming
- Vreeswijk [61] --- feasibility of defeat in defeasible reasoning
- Von Neuman and Morgenstern [62] --- original theory of n-person games
