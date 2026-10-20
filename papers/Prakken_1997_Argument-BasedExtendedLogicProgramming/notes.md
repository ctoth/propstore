---
title: "Argument-Based Extended Logic Programming with Defeasible Priorities"
authors: "Henry Prakken, Giovanni Sartor"
year: 1997
venue: "Journal of Applied Non-Classical Logics 7(1-2):25-75"
doi_url: "https://doi.org/10.1080/11663081.1997.10510900"
pages: "25-75"
note: "Read from the authors' PDF (webspace.science.uu.nl/~prakk101/pubs/DefArgJANCL97.pdf, linked from Prakken's publication list under this JANCL citation; 52 pages, journal-style layout without printed page numbers). Page citations are PDF pages: p.N = page-image index N-1. They are not journal page numbers."
---

# Argument-Based Extended Logic Programming with Defeasible Priorities

## One-Sentence Summary
An argumentation system over extended logic programs (strict and defeasible rules, strong ¬ and weak ~ negation) with rebutting and undercutting defeat, priorities on defeasible rules compared over the rules relevant to each conflict, a grounded fixpoint semantics giving justified/overruled/defensible status, a sound and complete dialectical proof theory, and a lifting of object-level priority conclusions (≺) into the defeat relation so that priorities are themselves defeasibly argued. *(p.1-36)*

## Problem Addressed
Legal (and bureaucratic) reasoning needs to represent conflicting opinions and debatable conflict-resolution criteria (lex superior, posterior, specialis, domain priority rules) that may conflict with each other, plus explicit exception clauses, without fixing a single overriding standard such as specificity. *(p.1-3)*

## Key Contributions
- Attack/rebut/undercut/defeat definitions handling strict-rule-mediated conflicts and relevant-rule sets. *(p.8-14)*
- Grounded fixpoint semantics and dialectical proof theory for fixed priorities. *(p.14-25)*
- Defeasible priorities: semantics with ≺ lifted via <_Args and priority dialogues. *(p.25-34)*
- Credulous (stable, defensible-extension) variants; formal comparison with Dung 93b (strictly more conclusions, no collapse under contradiction). *(p.34-39)*

## Introduction *(p.1-4)*
- Motivation: uncertainty/inconsistency often stems from unavoidable disagreement (law, bureaucracies), not from missing information; a system should record/produce alternative arguments for and against a claim and reason about the strengths and hierarchical status of opinions, rather than "improve" the KB. *(p.1-2)*
- Argument-based systems cited: [POL 87, Loui 87, Nute 88, SL 92, VRE 93a, PRA 93, BTK 93, Dung 95]; legal applications [PRA 91, Loui 93, SAR 94, LN 95, GOR 95, PS 96b]. *(p.2)*
- Three legal desiderata *(p.2-3)*:
  1. Criteria for comparing arguments are part of the domain theory and debatable: hierarchy (lex superior: constitution over statutes), temporality (lex posterior), specificity (lex specialis), and domain-specific priority rules (Italian town planning: artistic-buildings rules prevail over town-planning rules). These conflict-rules can themselves conflict (e.g. an earlier artistic-buildings rule vs later town-planning rule: town-planning conflict rule vs temporal principle), so reasoning about priorities is defeasible.
  2. Specificity is not the overriding standard; in most legal systems it is subordinate to hierarchy and time. Systems making specificity overriding, e.g. [GP 92], are inadequate.
  3. Legal reasoning combines priorities between conflicting rules with assumptions / weak negation for explicit exceptions (Dutch Civil Code 3:32-(1) capacity "unless the law provides otherwise"; Dutch rent act section 2 excluding short-term leases). Hence both strong and weak negation: attack by contradictory conclusion, or by a conclusion that provides an 'unless' clause. Not reducing priorities to assumptions or vice versa preserves the surface structure of legal texts and supports modular formalisation.
- Setting: logic-programming-like, Dung [Dung 93b] argument-based semantics of extended logic programming; sceptical semantics via fixpoint; dialectical proof theory (proponent vs opponent; justified iff proponent can make the opponent run out of moves). *(p.3)*
- Structure: §1 informal AFs; §2-4 fixed priorities; §5-6 defeasible priorities; §7 credulous semantics; §8 implementation; §9 related work; §10 conclusions; proofs in appendix. Revised and extended version of [PS 96a]; less technical companion [PS 96b] applies the dialectical form to law. *(p.3-4)*

## 1 Argumentation Frameworks: General Ideas *(p.4-5)*
Five elements of an AF: underlying logical language; argument (proof in the underlying logic; narrow sense, excludes inductive/abductive/analogical); conflicts between arguments; defeat (comparison by standards, here domain-theory content and debatable); status of arguments, considering all interactions. Output: three classes — justified (won), overruled (lost), defensible (undecided). *(p.4-5)*

## 2 Formal System I: Fixed Priorities *(p.5-14)*

### 2.1 Language *(p.5-6)*
- Strong literal: atomic first-order formula or its strong negation ¬A. Complement of L written L̄ (A and ¬A complements). Weak literal: ~L with L strong; ~L reads "there is no evidence that L is the case", ¬L "L is definitely not the case". (Footnote: ¬ and ~ symbols switched relative to some other articles in the same journal issue, to match extended logic programming literature.) *(p.5)*

**Definition 2.1 (rule)** *(p.5)*:

$$
r : L_0 \wedge \ldots \wedge L_j \wedge {\sim} L_k \wedge \ldots \wedge {\sim} L_m \Rightarrow L_n
$$
r (a first-order term) is the rule's name; each Lᵢ (0 ≤ i ≤ n) strong; antecedent left, consequent right; rules with variables are schemes for ground instances. Rules may have empty antecedents (unconditional statements). Variables x, y, z; other letters/words are constants; literals written casually ("x is earlier than y" for Earlier(x, y)). *(p.5)*

- **Ordered theory** (S, D, <): S strict rules (no weak literals), D defeasible rules, < a strict partial order on D (transitive, asymmetric); x < y means y is preferred over x. No ordering on S (beyond debate). *(p.6)*
- Defeasible rules can be defeated two ways: overridden by stronger rules with contradicting consequent, or containing unwarranted assumptions. Strict rules: meaning postulates ("Bachelors are not married"), relation properties (transitivity of older-than, asymmetry of father-of); role like the first-order part of a default theory. *(p.6)*
- The strict/defeasible distinction is pragmatic/epistemological, not syntactic (only defeasible rules may contain assumptions); → for strict and ⇒ for defeasible is notational shorthand, → is not part of the object language. *(p.6)*

### 2.2 Arguments *(p.6-7)*
**Definition 2.2** *(p.6-7)*: an argument is a finite sequence A = [r₀, …, rₙ] of ground rule instances such that
1. for every i (0 ≤ i ≤ n), for every strong literal Lⱼ in the antecedent of rᵢ there is k < i with Lⱼ the consequent of rₖ;
2. no two distinct rules in the sequence have the same consequent.
A is based on (S, D, <) iff all its rules are in S ∪ D. Condition 1 chains rules, ignoring weak literals; it builds in conjunction and "defeasible modus ponens" (from rule and L₀ ∧ … ∧ Lⱼ infer Lₙ, assumptions ignored). Condition 2 prevents circular chains. Args_Γ = all arguments on Γ; Args_R = arguments using only rules in R. *(p.7)*

**Definition 2.3** *(p.7)*:
1. A is strict iff it contains no defeasible rule; defeasible otherwise.
2. A′ is a (proper) subargument of A iff A′ is a (proper) subsequence of A.
3. L is a conclusion of A iff L is the consequent of some rule in A (every intermediate consequent counts; chosen to simplify definitions).
4. L is an assumption of A iff ~L̄ occurs in some rule in A.
Example: A = [r₁: → a, r₂: a ∧ ~¬b ⇒ c, r₃: c ∧ ~d ⇒ e]: conclusions {a, c, e}; subarguments {[], [r₁], [r₁, r₂], [r₁, r₂, r₃]}, only [] and [r₁] strict; assumptions {b, ¬d}. *(p.7)*

**Example 2.4** *(p.8)*: r₁: ~ x is a minor ⇒ x has legal capacity; r₂: ¬ x is a minor ⇒ x has the right to vote. Argument for capacity exists, not for voting (no rule gives ¬minor).

### 2.3 Conflicts between Arguments *(p.8-10)*
Two attack modes: (a) head-to-head, contradicting a conclusion (symmetric); (b) contradicting an assumption (asymmetric; a special case of Pollock's undercutting defeaters [POL 87]). *(p.8)*
- **Example 2.5** *(p.8)*: r₁: A ⇒ x is a lease; r₂: B ⇒ ¬ x is a contract; s₁: x is a lease → x is a contract; facts f₁: → A, f₂: → B. Complementary consequents are r₂ and s₁, but intuitively r₂ competes with r₁ (s₁ is a linguistic convention).
- **Example 2.6** *(p.9)*: r₁: A ⇒ x married; r₂: B ⇒ x bachelor; s₁: married → ¬bachelor; s₂: bachelor → ¬married; facts f₁, f₂. The real conflict is r₁ vs r₂.
- Against [Nute 88, Nute 94] (two kinds of one-direction rules but no weak negation): Nute treats only rules with complementary consequents as conflicting, so [s₁, r₁] and [s₂, r₂] would not conflict and the r₁/r₂ priority is ignored. *(p.9)*
- Proposal: if A has conclusion or assumption L, A is attacked by all arguments that can be extended **with only strict rules** to an argument with conclusion L̄; for head-to-head, extend both sides with strict rules. *(p.9)*

**Definition 2.7**: A + T is the concatenation of argument A and rule sequence T (order immaterial except antecedent-before-use, so non-uniqueness ignored). *(p.9)*

**Definition 2.8 (attack)** *(p.9-10)*: A₁ attacks A₂ iff there are sequences S₁, S₂ of strict rules such that A₁ + S₁ is an argument with conclusion L and
1. A₂ + S₂ is an argument with a conclusion L̄; or
2. A₂ is an argument with an assumption L̄.
(Footnote: Dung 93b and BTK 93 use 'attack' closer to this paper's 'defeat'; they have no explicit notion of this 'attack'.) With defeasible rules having conflicting consequents, S₁ = S₂ = ∅. *(p.9-10)*
- **Example 2.9** *(p.10)*: r₁: ⇒ f forged evidence e; r₂: f forged evidence e ⇒ ¬ e is admissible evidence; r₃: ⇒ ¬ f forged evidence e. [r₃] attacks [r₁] and [r₁, r₂] (attack on a proper subargument).
- **Example 2.10** *(p.10)*: r₁: ⇒ f forged evidence e; r₂: f forged evidence e ⇒ ¬ f is honest; r₃: f is police officer ⇒ f is honest; r₄: f is honest ⇒ ¬ f forged evidence; s₁: → f is police officer. [r₁, r₂] attacks [s₁, r₃] and [s₁, r₃, r₄]; [s₁, r₃, r₄] attacks [r₁] and [r₁, r₂].
- **Definition 2.11**: an argument is coherent iff it does not attack itself. Incoherent examples: [r₁: ⇒ a, r₂: a ⇒ ¬a], [r₁: ~a ⇒ b, r₂: b ⇒ a]. *(p.10)*
- **Definition 2.12**: a set Args is conflict-free iff no argument in Args attacks an argument in Args. *(p.10)*

### 2.4 Defeat among Arguments *(p.11-14)*
Defeat is defined via rebutting (contradicting a conclusion; priorities used) and undercutting (contradicting an assumption; priorities not used). Priority comparison is over the rules relevant to the conflict, not "weakest link" over whole arguments (defended in [PRA 91, PRA 93]). With strict rules, several defeasible rules can be relevant: A = [r₁: ⇒ Rab, r₂: ⇒ Rbc], B = [r₃: ⇒ Rca], S with transitivity and asymmetry of R: A extends to ¬Rca; compare r₃ with {r₁, r₂}. *(p.11)*

**Definition 2.13 (relevant rules)** *(p.11-12)*: for argument A and strict-rule set S with A + S an argument with conclusion L, R_L(A + S) =
1. {r_d} iff A includes a defeasible rule r_d with consequent L;
2. R_{L₁}(A + S) ∪ … ∪ R_{Lₙ}(A + S) iff A is defeasible and S includes a strict rule r_s: L₁ ∧ … ∧ Lₙ → L.
Unique since no argument has two rules with the same consequent. Examples 2.6 and 2.10: compare r₁ and r₂. A = [r₁: ⇒ Rab, r₂: ⇒ Rbc, s₁: Rab ∧ Rbc → Rac]: R_Rac(A) = {r₁, r₂}; if s₁ were defeasible, R_Rac(A) = {s₁}. Entirely strict conflicts give empty relevant sets. *(p.12)*

**Definition 2.14 (set ordering)** *(p.12)*: for sets R, R′ of defeasible rules, R < R′ iff for some r ∈ R and all r′ ∈ R′, r < r′. (R can be improved by replacing some rule with any rule of R′, not conversely.)

$$
R < R' \iff \exists r \in R\ \forall r' \in R' : r < r'
$$

**Definition 2.15** *(p.12)*: A₁ rebuts A₂ iff condition (1) of Def 2.8 holds, provided

$$
R_L(A_1 + S_1) \not< R_{\bar L}(A_2 + S_2)
$$
A₁ undercuts A₂ iff condition (2) of Def 2.8 holds.
Properties: rebut/undercut can be direct or indirect; rebut or undercut implies attack; undercut not symmetric, but also A undercuts B does not exclude B undercutting A (A = [r₁: ~b ⇒ a], B = [r₂: ~a ⇒ b]); rebut not symmetric (A = [r₃: ⇒ a], B = [r₄: ⇒ ¬a], r₃ < r₄); but rebutting can be mutual even with < (Example 2.10 with r₁ < r₄ and r₃ < r₂: [r₁, r₂] and [s₁, r₃, r₄] rebut each other). *(p.12)*

**Definition 2.16 (defeat)** *(p.13)*: A₁ defeats A₂ iff A₁ is empty and A₂ is incoherent, or else
- A₁ undercuts A₂; or
- A₁ rebuts A₂ and A₂ does not undercut A₁.
A₁ strictly defeats A₂ iff A₁ defeats A₂ and A₂ does not defeat A₁. Defeat can be indirect (via strict subarguments... as printed "one of its strict subarguments"); attacks on assumptions always succeed and are stronger than attacks on conclusions. *(p.13)*

**Corollary 2.17** *(p.13)*: if A₁ attacks A₂ then A₁ defeats A₂ or A₂ defeats A₁; if A₁ defeats A₂ then A₁ attacks A₂.
Boundary cases: for nonempty R, R < ∅, so strict arguments strictly defeat conflicting defeasible arguments; ∅ ≮ ∅, so no strict argument strictly defeats a conflicting strict argument. *(p.13)*

**Design choice 1: undercutting ignores priorities** *(p.13-14)*: legal conflict-resolution rules resolve head-to-head conflicts only, not head-to-body. Brewka [BRE 96] (prioritised ELP, not argument-based) reduces head-to-head to mutual head-to-body by giving every defeasible rule the assumption ~L̄ of its consequent; this loses expressiveness (cannot distinguish 'If A then B' from 'If A then B unless the contrary can be shown') and resolves all mutual head-to-body conflicts by priority, e.g. r₁: ~a ∧ ~¬b ⇒ b; r₂: ~b ∧ ~¬a ⇒ a; r₂ < r₁: here both defeat each other, Brewka has [r₁] strictly defeating [r₂]. *(p.13-14)*

**Design choice 2: undercutting stronger than rebutting** *(p.14)*: **Example 2.18**: r₁: ~¬ OJ is innocent ⇒ OJ is innocent; r₂: ⇒ ¬ OJ is innocent; < = ∅. [r₁] rebuts [r₂] but does not defeat it since [r₂] undercuts [r₁]; [r₂] strictly defeats [r₁]. Accepting both rules is only possible by believing OJ is not innocent (r₁'s condition fails); believing innocence means rejecting r₂ (antecedent held, consequent not). Logical counterpart of the legal principle that law should be interpreted as coherently as possible. *(p.14)*

- Defeat is weak (only ≮ needed, a defeater must merely be not inferior), because justified arguments must be beyond reasonable doubt, and doubt is cast by any not-inferior counterargument. Strict defeat (asymmetric) captures "really better than" and is used so a counterargument fails to cast doubt if it is inferior to a counterargument that is itself protected from defeat. *(p.14)*

## 3 Status of Arguments: Fixpoint Semantics *(p.14-20)*

### 3.1 Definitions and Properties *(p.14-17)*
Requirements: reinstatement (a defeated argument is reinstated if its defeater is strictly defeated by another argument); weakest-link principle (argument not justified unless all subarguments are); justified set unique, conflict-free, and as small as possible; overruled = attacked by a justified argument; defensible = neither. "Semantics" = specification of a set of arguments; "proof theory" = procedure deciding membership (cf. declarative/procedural in [LN 95]); the underlying logic may still have a model theory (§10). Based on a variant of Dung 93b acceptability. *(p.14-15)*

**Definition 3.1 (acceptable)** *(p.15)*: A is acceptable w.r.t. Args iff each argument defeating A is strictly defeated by an argument in Args.

**Definition 3.2 (characteristic function)** *(p.15)*: for ordered theory Γ and S ⊆ Args_Γ:

$$
F_\Gamma : Pow(Args_\Gamma) \to Pow(Args_\Gamma)
$$

$$
F_\Gamma(S) = \{A \in Args_\Gamma \mid A \text{ is acceptable with respect to } S\}
$$
(Core of Dung 93b's grounded sceptical semantics of extended logic programs.)

**Proposition 3.3**: F_Γ is monotonic. *(p.15)*

Acceptability captures reinstatement: A defeated by B can still be justified iff B is strictly defeated by an argument already known to be justified. *(p.16)*

**Definition 3.4 (status)** *(p.16)*: on the basis of Γ:
1. A is justified iff A is in the least fixpoint of F_Γ (JustArgs_Γ);
2. A is overruled iff A is attacked by a justified argument;
3. A is defensible iff neither justified nor overruled.
Literal L: justified conclusion iff a conclusion of a justified argument; defensible conclusion iff not justified and a conclusion of some defensible argument; overruled conclusion iff not justified or defensible and a conclusion of an overruled argument.

**Definition 3.5 [Dung 93b]**: Γ is finitary iff each argument in Args_Γ is attacked by at most finitely many arguments. *(p.16)*

**Proposition 3.6** *(p.16)*: define

$$
F^1 = F_\Gamma(\emptyset), \qquad F^{i+1} = F^i \cup F_\Gamma(F^i)
$$
1. ⋃_{i=0}^∞ Fⁱ ⊆ JustArgs_Γ.
2. If Γ is finitary, ⋃_{i=0}^∞ Fⁱ = JustArgs_Γ.

Properties *(p.16-17)*: JustArgs unique; every member acceptable w.r.t. JustArgs; complete (everything acceptable w.r.t. it is in it); minimal (smallest such set; no circular dependencies).

**Proposition 3.7**: JustArgs is conflict-free. *(p.17)*
**Proposition 3.8**: if an argument is justified, all its subarguments are justified (implicit, as in [POL 87, SL 92, GP 92]; not an explicit requirement as in [Nute 94, VRE 93a, PRA 93]). *(p.17)*
**Corollary 3.9**: if Args_S is not conflict-free, every argument (including the empty one) attacks itself, so every argument is defensible on Γ. *(p.17)*

### 3.2 Illustrations *(p.17-20)*
- **Example 3.10** *(p.17-18)*: r₀: ⇒ a; r₁: a ⇒ b; r₂: ~b ⇒ c; r₃: ⇒ ¬a; r₀ < r₃. A₁ = [r₀, r₁] undercuts A₂ = [r₂]; A₃ = [r₃] defeats A₁ by rebutting its subargument A₀ = [r₀]. F¹ = {[], A₃}; A₁, A₀ not acceptable w.r.t. F¹; A₂ reinstated by A₃: F² = {[], A₃, A₂} = F³. A₂, A₃ justified; A₀, A₁ overruled (weakest link: A₁ overruled since A₀ is).
- **Example 3.11** *(p.18)*: S = {A, B}; C and D defeat each other; A strictly defeats C; B strictly defeats D. C ∉ F(S): its defeater D is strictly defeated by B ∈ S, but C is also defeated by A, which nothing in S strictly defeats.
- **Example 3.12** *(p.18)*: r₁: ⇒ Has_Porsche; r₂: Has_Porsche ⇒ Rich; r₃: ~Rich ⇒ ¬Has_Porsche; r₁ < r₃. Def 2.16 ignores the ordering: B = [r₃] does not defeat A = [r₁, r₂] since A undercuts B; A justified and its subargument A′ = [r₁] reinstated (A strictly defeats B).
- **Example 3.13** *(p.18)*: r₁: ⇒ a; r₂: a ⇒ a; r₃: ⇒ ¬a; r₃ < r₂. The text says "Condition (3) of Definition 2.2 is required" — Definition 2.2 as printed on p.7 has only conditions 1 and 2; the condition meant is the no-two-rules-same-consequent condition (2). Without it [r₁, r₂] would save [r₁] by defeating [r₃]; with it [r₁, r₂] is not an argument.
- **Example 3.14** *(p.18)*: step-by-step: r₁: ⇒ a; r₂: a ⇒ b; r₃: b ⇒ c; r₄: ⇒ ¬a; r₅: ¬a ⇒ d; r₆: d ⇒ ¬c; r₄ < r₁, r₃ < r₆. [r₁–r₃] and [r₄–r₆] defeat each other, but [r₁] (and [r₁, r₂]) strictly defeats [r₄–r₆] with no other counterarguments: F¹ = {[r₁], [r₁, r₂]}; [r₄–r₆] not acceptable w.r.t. F², [r₁–r₃] acceptable, reinstated by [r₁].
- **Example 3.15** *(p.19)*: sets reduced to individual arguments. S = {s₁, s₂} (transitivity, asymmetry of taller-than; printed with ⇒ though declared strict), D = {r₁: ⇒ John taller than Bob, r₂: ⇒ Bob taller than Al, r₃: ⇒ Al taller than John}. Pairs attacking: [r₁]/[r₂, r₃], [r₂]/[r₁, r₃], [r₃]/[r₁, r₂]. With r₃ < r₁, r₃ < r₂: [r₁] > [r₂, r₃], [r₂] > [r₁, r₃], [r₃] < [r₁, r₂]; [r₁], [r₂] justified; [r₁, r₂] also justified as it beats [r₁, r₃] and [r₂, r₃]. If r₃ < r₁ and r₂, r₃ incomparable: [r₁] justified, [r₂, r₃] overruled, [r₂], [r₃], [r₁, r₂] defensible.
- **Example 3.16 (perhaps too sceptical)** *(p.19-20)*: s₁: → a; r₁: a ⇒ b; s₂: → c; r₂: a ∧ c ⇒ ¬b; s₃: → d; r₃: d ⇒ b; r₄: c ∧ d ⇒ ¬b; specificity r₁ < r₂, r₃ < r₄. All arguments for b and ¬b are defensible: A₂ = [s₁, s₂, r₂] strictly defeats A₁ = [s₁, r₁], A₃ = [s₂, s₃, r₄] strictly defeats A₄ = [s₃, r₃], but A₂ is defeated by [s₃, r₃] and A₃ by [s₁, r₁]; F¹ = Args_S ∪ {[]}. [HTT 90] (inheritance) argue [s₁, s₂, r₂] and [s₃, r₃] should be justified [as printed; the ¬b arguments are A₂ and A₃]; {[s₁, s₂, r₂], [s₃, r₃]} is a conflict-free fixpoint of F, not the least. Open: which change gives that result. [as printed]
- **Example 3.17 (no extreme scepticism)** *(p.20)*: r₁: ⇒ f forged evidence e; r₂: f forged evidence e ⇒ ¬ e is admissible evidence; r₃: ⇒ ¬ f forged evidence e; r₄: ~¬ e is admissible evidence ⇒ e proves guilt; < = ∅. All arguments defensible. In extremely sceptical systems [HTT 90, Nute 94], [r₁, r₂] cannot block [r₄] because its subargument is only defensible, so [r₄] is justified though attacked by a not-worse argument. Authors: a judge would first determine whether r₁ < r₃ before deciding e proves guilt.

## 4 Proof Theory with Strict [fixed] Priorities *(p.21-25)*

### 4.1 General idea *(p.21-22)*
Using Prop 3.6: traverse F¹…Fⁿ backward from the first Fⁿ containing A: for every defeater B of A find C ∈ Fⁿ⁻¹ strictly defeating B, and so on, ending with an undefeatable supporter. Dialectical style inspired by [VRE 93b, Dung 94, BRE 94b, LN 95]: proof = dialogue tree; each branch a dialogue; root an argument for the formula; each move is a complete argument (argument search is 'monological', counterarguments dialectical). Proponent's moves must strictly defeat; opponent's need only defeat (mirrors acceptability). *(p.21)*

- **Example 4.1** *(p.21-22)*: r₁: ~¬ e is admissible evidence ⇒ e proves guilt; r₂: ⇒ f forged evidence e; r₃: x forged evidence y ⇒ ¬ y is admissible evidence; r₄: x is police officer ∧ ~ x is dishonest ⇒ ¬ x forged evidence y; f₅: → f is police officer in LA; f₆: x is police officer in LA → x is police officer; r₇: x is police officer in LA ⇒ x is dishonest; r₈: ⇒ f has received a medal of honour; r₉: x is police officer ∧ x has received a medal of honour ⇒ ¬ f is dishonest; r₂ < r₄, r₇ < r₉, all else incomparable. Dialogue: P₁ [r₁]; O₁ [r₂, r₃] (undercut); P₂ [f₅, f₆, r₄] (rebut, r₂ < r₄); O₂ [f₅, r₇] (undercut of r₄'s assumption); P₃ [r₈, f₅, f₆, r₉] (strict rebut, r₇ < r₉); O out of moves, no branching: r₁ provably justified.
- **Example 4.2** *(p.22-23)*: Example 3.12 again: P₁ [r₁: ⇒ John has a Porsche, r₂: John has a Porsche ⇒ John is rich]; [r₃: ~ John is rich ⇒ ¬ John has a Porsche] attacks but does not defeat P₁ (P₁ undercuts it); O has no move.
- **Loop checker**: no two proponent moves in a branch with the same content. *(p.23)*
- **Example 4.3** *(p.23)*: S = < = ∅, r₁: ~a ⇒ b, r₂: ~b ⇒ a. P₁ [r₁], O₁ [r₂]; P out of moves (only defeating reply has P₁'s content). Non-repetition never harms P (if O could move the first time, it can again).
- **Example 4.4** *(p.23)*: O must be allowed to repeat: r₁: ⇒ ¬a; r₂: ~b ⇒ a; r₃: ~c ⇒ b; r₄: ~a ⇒ c; S = < = ∅. P₁ [r₁], O₁ [r₂], P₂ [r₃], O₂ [r₄], P₃ [r₂], O₃ [r₃], P₄ [r₄]; if O could not repeat its first move, P would win, yet [r₁] is only defensible.

### 4.2 The proof theory *(p.24-25)*
**Definition 4.5 (dialogue)** *(p.24)*: finite nonempty sequence of moves moveᵢ = (Playerᵢ, Argᵢ), i > 0:
1. Playerᵢ = P iff i odd; O iff i even;
2. if Playerᵢ = Playerⱼ = P and i ≠ j then Argᵢ ≠ Argⱼ;
3. if Playerᵢ = P (i > 1), Argᵢ is a minimal (w.r.t. set inclusion) argument strictly defeating Argᵢ₋₁;
4. if Playerᵢ = O, Argᵢ defeats Argᵢ₋₁.
(Minimality prevents trivially different arguments by adding irrelevant material.)

**Definition 4.6 (dialogue tree)** *(p.24)*: finite tree of moves; each branch a dialogue; if Playerᵢ = P, the children of moveᵢ are all defeaters of Argᵢ.
**Definition 4.7**: a player wins a dialogue if the other cannot move; wins a tree iff it wins all branches (P's undefeated last argument reinstates all P's previous arguments in the branch). *(p.24)*
**Definition 4.8**: A is provably justified iff there is a dialogue tree with A as root won by P; strong literal L is a provably justified conclusion iff it is a conclusion of a provably justified argument. *(p.24)*
**Proposition 4.9 (soundness)**: all provably justified arguments are justified. *(p.24)*
**Proposition 4.10 (completeness)**: for finitary ordered theories each justified argument is provably justified. *(p.24)*
- For finite theories every proof of an unjustified argument fails finitely; not for finitary ones: rᵢ: ~aᵢ₊₁ ⇒ aᵢ for i ∈ N gives JustArgs = ∅ but no proof fails finitely. *(p.25)*
**Proposition 4.11**: if an argument is provably justified, all its subarguments are. *(p.25)*

### 4.3 More examples *(p.25)*
- **Example 4.12**: proof of Example 3.14: P₁ [r₁, r₂, r₃]; O₁ [r₄, r₅, r₆]; P₂ [r₁]; O cannot reply [r₄] since r₄ < r₁.
- **Example 4.13** (non-repetition): S = ∅, D = {r₁–r₅}, < = {r₃ < r₁}: P₁ [r₁: ⇒ a, r₂: a ⇒ b]; O₁ [r₃: ⇒ ¬a, r₄: ¬a ⇒ ¬b]; P₂ [r₁]; O₂ [r₅: ~b ⇒ ¬a]; P cannot repeat P₁, correctly, since no argument is justified.

## 5 Formal System II: Defeasible Priorities *(p.25-28)*

### 5.1 New fixpoint semantics *(p.25-27)*
Adding a priority predicate is not enough; object-level priority conclusions must be lifted to the metatheory (Def 2.14). Distinguished two-place predicate ≺; ordered theory is now (S, D). S contains all and only these ≺-rules (strict partial order, plus contrapositives for transitivity since strict rules lack contraposition; asymmetry's contrapositive redundant) *(p.26)*:
- t₁: x ≺ y ∧ y ≺ z → x ≺ z
- t₂: x ≺ y ∧ ¬ x ≺ z → ¬ y ≺ z
- t₃: y ≺ z ∧ ¬ x ≺ z → ¬ x ≺ y
- a: x ≺ y → ¬ y ≺ x
Goal: (r, r′) ∈ < iff there is a justified argument for r ≺ r′; ordering constructed step by step with the justified set (idea from an earlier version of [BRE 96]). *(p.26)*

**Definition 5.1** *(p.26)*:

$$
<_{Args} = \{ r < r' \mid r \prec r' \text{ is a conclusion of some } A \in Args \}
$$
A (strictly) Args-defeats B on Γ iff A (strictly) defeats B per Def 2.16 on (Γ, <_Args); similarly Args-rebuts; {A}-defeats written A-defeats.

**Corollary 5.2** *(p.26)*: if A₁ attacks A₂ then for any conflict-free Args, A₁ Args-defeats A₂ or A₂ Args-defeats A₁; if A₁ Args-defeats A₂ then A₁ attacks A₂.

**Definition 5.3 (acceptable)** *(p.27)*: A is acceptable w.r.t. Args iff all arguments Args-defeating A are strictly Args-defeated by some argument in Args.

**Definition 5.4** *(p.27)*: Γ = (S, D), Cargs_Γ = conflict-free subsets of Args_Γ:

$$
G_\Gamma : Cargs_\Gamma \to Pow(Args_\Gamma), \qquad G_\Gamma(S) = \{A \in Args_\Gamma \mid A \text{ acceptable w.r.t. } S\}
$$
(The operator is not monotonic in general; monotonic only on conflict-free sets.)

**Proposition 5.5**: G_Γ is monotonic. *(p.27)*
**Definition 5.6**: A justified on Γ iff in the least fixpoint of G_Γ (JustArgs_Γ); overruled/defensible as before. *(p.27)*
**Proposition 5.7** *(p.27)*: G¹ = G_Γ(∅), Gⁱ⁺¹ = Gⁱ ∪ G_Γ(Gⁱ); ⋃Gⁱ ⊆ JustArgs_Γ; equality if Γ finitary. Each step also extends the rule ordering (defeat relations re-determined from the justified set so far).
**Proposition 5.8**: JustArgs is conflict-free. **Proposition 5.9**: subarguments of justified arguments are justified. *(p.28)*

Non-monotonicity without the conflict-free restriction *(p.28)*: A₁ [r₁: ⇒ a]; A₂ [r₂: ⇒ b, r₃: b ⇒ ¬a]; A₃ [r₄: ⇒ ¬b]; A₄ [r₅: ⇒ r₂ ≺ r₄]; A₅ [r₆: ⇒ r₄ ≺ r₂]; G({A₃, A₄}) = {A₁, A₃}; G({A₃, A₄, A₅}) = {A₃}. (Footnote: strict arguments and combinations of independently justified arguments usually left implicit hereafter.)

**Definition 5.10** *(p.28)*: E is a complete extension iff it is a maximal (w.r.t. ⊆) set such that A ∈ E iff A is acceptable w.r.t. E. (Dung requires conflict-freeness; dropped here.) The least fixpoint of G is a complete extension.
**Proposition 5.11**: any complete extension that is not a superset of JustArgs is not conflict-free. **Corollary 5.12**: no complete extension is a [proper, presumably] subset of JustArgs [as printed: "is a subset"]. So restricting G to conflict-free sets does no harm: JustArgs is a minimal complete extension, and all other minimal complete extensions are not conflict-free. *(p.28)*

### 5.2 Examples *(p.28-29)*
- **Example 5.13** *(p.28-29)*: Example 3.10 plus r₄: ⇒ r₀ ≺ r₃; r₅: ⇒ r₃ ≺ r₀; r₆: ⇒ r₅ ≺ r₄. Only ∅-undefeated argument [r₆]: G¹ = {[r₆]}; <_{G¹} = {r₅ < r₄}; [r₄] strictly G¹-defeats [r₅], G² = G¹ ∪ {[r₄]}; <_{G²} = <_{G¹} ∪ {r₀ < r₃}; continue as in 3.10.
- **Example 5.14** *(p.29)*: S only priority axioms; D: r₄: ⇒ r₁ ≺ r₂; r₅: ⇒ r₂ ≺ r₃; r₆: ⇒ r₃ ≺ r₁; r₇: ⇒ r₆ ≺ r₄; r₈: ⇒ r₆ ≺ r₅. G¹ ∋ [r₇], [r₈], [r₇, r₈]; <_{G¹} = {r₆ < r₄, r₆ < r₅}; [r₄, r₅] strictly G¹-defeats its counterarguments [r₆], [r₄, r₆], [r₅, r₆]; [r₄, r₅] ∈ G².
- **Example 5.15** *(p.29)*: r₁: ⇒ a; r₂: ⇒ ¬a; r₃: ⇒ r₂ ≺ r₁: G¹ = {[r₃]}, G² = G¹ ∪ {[r₁]}. With r′₃: a ⇒ r₂ ≺ r₁ instead, G¹ = ∅ and all arguments are defensible (priority depending on the conclusion it would decide).
- **Example 5.16 (self-reference)** *(p.29)*: r₁: ⇒ r₁ ≺ r₂; r₂: ⇒ r₂ ≺ r₁; asymmetry makes them attack each other; G¹ = ∅ = G²; neither justified; both defensible.

## 6 Proof Theory with Defeasible Priorities *(p.30-33)*

### 6.1 Definitions *(p.30-31)*
Problem: which priorities determine a move's defeating force, without generating all priority arguments first. Solution: O's move need only ∅-defeat P's previous move (Def 2.16 implies an S-defeater of P's move for some S is also an ∅-defeater); P need only use priorities stated by its own move (if Argᵢ strictly Argᵢ-defeats O's move, it does so whatever more priorities are derived). P may also 'undo' O's defeating force with a pure priority argument. Illustration: P₁ [r₁: ⇒ a]; O₁ [r₂: ⇒ b, r₃: b ⇒ ¬a]; P₂ [r₄: ⇒ ¬b, r₅: ⇒ r₂ ≺ r₄]; O₂ [r₂: ⇒ b] (∅-defeats P₂); P₃ [r₅: ⇒ r₂ ≺ r₄]. *(p.30)*

**Definition 6.1 (priority dialogue)** *(p.30-31)*: finite sequence of moves moveᵢ = (Playerᵢ, Argᵢ), i > 0:
1. Playerᵢ = P iff i odd, O iff i even;
2. if Playerᵢ = Playerⱼ = P and i ≠ j then Argᵢ ≠ Argⱼ;
3. if Playerᵢ = P (i > 1), Argᵢ is a minimal (w.r.t. ⊆) argument such that
   - Argᵢ strictly Argᵢ-defeats Argᵢ₋₁; or
   - Argᵢ₋₁ does not Argᵢ-defeat Aᵢ₋₂ [printed "Aᵢ₋₂", i.e. Argᵢ₋₂];
4. if Playerᵢ = O then Argᵢ ∅-defeats Argᵢ₋₁.
**Definition 6.2 (priority dialogue tree)** *(p.31)*: each branch a dialogue; if Playerᵢ = P, children of moveᵢ are all ∅-defeaters of Argᵢ. Other definitions unchanged.
**Proposition 6.3**: all provably justified arguments are justified. **Proposition 6.4**: for **finite** ordered theories each justified argument is provably justified (stated for finite, not finitary as in Prop 4.10). **Proposition 6.5**: subarguments of provably justified arguments are provably justified. *(p.31)*

### 6.2 Examples *(p.31-33)*
- **Example 6.6** *(p.31)*: Example 5.15 theory: P₁ [r₁: ⇒ a, r₃: ⇒ r₂ ≺ r₁]; O₁ [r₂: ⇒ ¬a]; P₂ [r₃] — a proof for a. With r′₃: a ⇒ r₂ ≺ r₁: P₁ [r₁, r′₃] [printed "r₃: a ⇒ r₃ ≺ r₁"]; O₁ [r₂]; P could only undo by repeating P₁, which is not allowed; agrees with the fixpoint semantics.
- **Example 6.7** *(p.32)*: proof that in Example 5.14 r₁ ≺ r₃ is justified: P₁ [r₄, r₅] branches into O₁ [r₆] / P₂ [r₇, r₈]; O₁ [r₅, r₆] / P₂ [r₇]; O₁ [r₄, r₆] / P₂ [r₈]. In each conflict the relevant rules are all defeasible rules in the arguments.
- **Rule naming**: a rule with terms t₁…tₙ is named r(t₁, …, tₙ). *(p.32)*
- **Legal ordering principles as 'if' definitions** (ordering possibly partially unspecified) *(p.32)*:
  - H(x, y): x is inferior to y ⇒ x ≺ y (Lex Superior)
  - T(x, y): x is earlier than y ⇒ x ≺ y (Lex Posterior)
  - S(x, y): y is more specific than x ⇒ x ≺ y (Lex Specialis)
  - Antecedent rules, e.g. r₁(r₃(x), r₄(x)): ⇒ r₄(x) is more specific than r₃(x) (by hand, or from a logical specificity definition inducing an ordering on individual defaults, e.g. [SL 92]); r₂(x, y): x is in a statute ∧ y is in the constitution ⇒ x is inferior to y.
  - Relations between principles: O₁(T(x, y), H(x, y)): ⇒ T(x, y) ≺ H(x, y); O₂(S(x, y), T(x, y)): ⇒ S(x, y) ≺ T(x, y).
- **Example 6.8 (Italian building regulations vs Lex Posterior)** *(p.32-34)*: r₁(x): x is a protected building ⇒ ¬ x's exterior may be modified; r₂(x): x needs restructuring ⇒ x's exterior may be modified; r₃(y, x): x is a rule about protection of artistic buildings ∧ y is a town planning rule ⇒ y ≺ x; T(x, y): x is earlier than y ⇒ x ≺ y; r₄(r₁(x)): ⇒ r₁(x) is a rule about the protection of artistic buildings; r₅(r₂(x)): ⇒ r₂(x) is a town planning rule; r₆(r₁(x), r₂(y)): ⇒ r₁(x) is earlier than r₂(y); r₇(Villa₀): ⇒ Villa₀ is a protected building; r₈(Villa₀): ⇒ Villa₀ needs restructuring; r₉(T(x, y), r₃(x, y)): ⇒ T(x, y) is earlier than r₃(x, y). r₉ says r₃ is later than Lex Posterior T, so by T itself r₃ prevails over T (a priority rule applied to an instance of itself). Proof that Villa₀'s exterior may not be modified: P₁ [r₇, r₁]; O₁ [r₈, r₂]; P₂ [r₄, r₅, r₃] (r₂ ≺ r₁); O₂ [r₆, T] (r₁ ≺ r₂ by Lex Posterior, ∅-defeats P₂); P₃ [r₉, T′: T is earlier than r₃ ⇒ T ≺ r₃] (meta-meta level; not formally self-referential: one instance of Lex Posterior about another); O out of moves. *(p.33-34)*

## 7 Alternative, Credulous Semantics *(p.34-)*
Sceptical semantics gives a unique set; defensibility is individual. To know which defensible arguments can be defended together (coherent points of view), e.g. r₁: ⇒ a; r₂: ⇒ ¬a; r₃: ~a ⇒ b ([r₂] and [r₃] share one view, [r₁] another), use Dung 93b stable semantics, defined for defeasible priorities. *(p.34)*

**Definition 7.1** *(p.34)*: a conflict-free set S is a stable extension iff every argument not in S is S-defeated by some argument in S. (Coherent and maximal point of view: every argument accepted or rejected.)

**Proposition 7.2**: every stable extension includes JustArgs. *(p.35)*
**Proposition 7.3**: if A is in some but not all stable extensions, A is defensible. *(p.35)*
- **Example 7.4** (converse fails) *(p.35)*: r₁: ~a ⇒ b; r₂: ~b ⇒ c; r₃: ~c ⇒ a. All defensible, none in a stable extension; {[r₁]} is maximally conflict-free but does not defeat [r₃].
**Definition 7.5**: a defensible extension is any maximal (w.r.t. ⊆) conflict-free subset of Args that includes JustArgs. *(p.35)*
**Corollary 7.6**: every stable extension is defensible, not every defensible extension is stable. *(p.35)*
- Defensible extensions are not the final answer either: in {[r₁]} of Ex 7.4, [r₁] is saved from its strict defeater [r₃] by [r₂], which [r₁] itself strictly defeats — the extension owes its existence to an argument it rejects; stable semantics avoids this. But [r₁], [r₂], [r₃] are all equally good or bad, which defensible extensions capture. *(p.35)*
- With defeasible priorities (Ex 5.16: r₁: ⇒ r₁ ≺ r₂; r₂: ⇒ r₂ ≺ r₁): both arguments give priority to their attacker; neither singleton is stable ([r₁] does not {[r₁]}-defeat [r₂], and vice versa) but both are defensible extensions, since defensible extensions use only justified priority arguments for defeat while stable checking uses the defensible priority arguments in the set too. *(p.36)*
- Final evaluative classes: Justified; Defensible and stable; Defensible but not stable; Overruled. *(p.36)*

## 8 Implementation Remarks *(p.36)*
- The proof theory is already the top level of an implementation. Completeness for finitary theories does not give semi-decidability: with function symbols, argument search is undecidable and having counterarguments is not even semi-decidable.
- Finite number of rules: decidable, since no argument repeats a conclusion, so finitely many arguments; as rules are schemes this means no function symbols, which conflicts with the r(t₁…tₙ) naming convention, though simpler term-based naming should do in practice.

## 9 Related Research *(p.37-41)*

### 9.1 Relation with Dung's approach *(p.37-39)*
Builds on Dung 93b's version of well-founded semantics of ELP (cf. [BS 91]); Dung has no reasoning with/about priorities and inherits features the authors find less attractive. Comparison without priorities: *(p.37)*
- d-argument: a set of assumptions; defeasible proof = argument of Def 2.2 without condition (2); based on a d-argument A iff its assumptions are in A; L is a conclusion of A iff a defeasible proof for L is based on A. Self-defeating iff a defeasible proof based on A exists for two complementary literals; sound iff not. For sound A, B: A raa-defeats B iff A ∪ B is self-defeating; A g-defeats B iff A has a conclusion L̄ for some L ∈ B; d-defeats = raa- or g-defeats. (Dung says 'attack' for 'defeat'.) *(p.37)*
- **Observation 9.1**: for non-self-defeating d-arguments A, B: A raa-(g-)defeats B iff some argument based on A rebuts (undercuts) B; if an argument based on A defeats one based on B, A d-defeats B. *(p.37)*
- **Definition 9.2**: A is d-acceptable w.r.t. S iff any d-argument d-defeating A is g-defeated by a member of S. (Dung's g-defeated vs this paper's strictly defeated: no difference without priorities; differs with defeasible priorities, then "Lemma10.1(2)" [appendix] holds only for this paper's definition.) *(p.37-38)*
- **Observation 9.3** *(p.38)*: Γ = (T, <): (1) for S the least fixpoint of F^d_Γ, all d-arguments d-defeating a member of S are strictly d-defeated by a member of S; (2) for S the least fixpoint of F^ps_Γ, all arguments defeating a member of S are strictly defeated by a member of S.
- Self-defeating case: Γ = {⇒ a, ⇒ ¬a} has the single d-argument ∅, self-defeating; since Dung defines d-defeat only for sound arguments, {∅} is the least fixpoint, supporting both a and ¬a; following earlier well-founded semantics, the authors define the well-founded conclusions as empty here (cf. [BRE 96, pp. 22/3]). *(p.38)*
- **Definition 9.4**: the d-well-founded conclusions of Γ are empty if Dargs_Γ has a self-defeating argument, else the least fixpoint of F^d_Γ. *(p.38)*
- **Proposition 9.5**: if L is a d-well-founded conclusion of Γ, L is a justified conclusion on (Γ, ∅). Converse fails. *(p.38)*
- **Example 9.6** *(p.38-39)*: r₁: ⇒ a; r₂: ⇒ ¬a; r₃: ⇒ b. b is justified here, but the only d-argument ∅ is self-defeating, so no d-well-founded conclusions — a flaw in [Dung 93b] and [BS 91] well-founded semantics (also noted by [AP 95], [BRE 96]). Dung's semantics seeks assumption sets giving the whole program a noncontradictory interpretation and collapses otherwise; this system still derives conclusions from parts unaffected by the contradiction.
- **Proposition 9.7**: if L is justified on (Γ, <), then for any <′ ⊇ <, L is justified on (Γ, <′). (Adding priorities enlarges justified conclusions.) *(p.39)*

### 9.2 Other related research *(p.39-41)*
- Pollock [POL 87]: epistemological, probabilities rather than arbitrary rule orders, no reasoning about priorities; suppositional arguments; conclusive vs defeasible reasons; rebutting vs undercutting defeaters. This paper's two attack forms are a special case: attacking an assumption denies the connection made by the implicit 'defeasible modus ponens'. *(p.39)*
- [Loui 87], [SL 92]: similar one-direction rules; differences here: assumptions, any source of priorities instead of specificity, defeasible priorities. *(p.39)*
- [VRE 93a] abstract argumentation system (L, R, ≼): inference rules strict/defeasible, arguments as trees; rules are logic-defining, not domain-specific (as in Pollock); the ordering reflects strength of argument forms (deduction, induction, abduction) rather than premises; no reasoning about ordering; consequence notion close to [Dung 95] preferred semantics (maximal conflict-free E where each defeater of a member is defeated by a member). *(p.39-40)*
- Default logic: rule a ∧ ~b ⇒ c translates to default a : ¬b / c, but the semantics does not extend default logic: Γ = (∅, {r₁: ⇒ a, r₂: ⇒ ¬a}, ∅) has JustArgs = ∅ and two stable extensions {[r₁]}, {[r₂]}, while (W = ∅, D = {⊤ : ⊤/a, ⊤ : ⊤/¬a}) has no extension. r₁, r₂ cannot be translated as ⊤ : a/a and ⊤ : ¬a/¬a since those translate ~¬a ⇒ a and ~a ⇒ ¬a. *(p.40)*
- [AP 95]: revises well-founded semantics for similar reasons; not argument-based; two negations, prioritized rules, no reasoning about priorities. *(p.40)*
- [BRE 96]: ELP with defeasible priorities, not argument-based; monotonic operator over the program, on his modification of [BS 91] well-founded semantics; partly solves the §9.1 problem if Ex 9.6's rules are defeasible (assume their head in their body), not if strict. *(p.40-41)*
- 'Ordered logic' [LV 90] and Nute's defeasible logic [Nute 94]: prioritized rules, no assumptions, fixed priorities; both show the extreme scepticism of Ex 3.17; Nute has a 'might conditional' (like Pollock's undercutter, a conditional denial of a rule); Nute assumes finite theory and no function symbols for decidability; Nute's strict-rule conflict handling differs (§2.3). *(p.41)*
- Proof theory: for fixed priorities a variant of [Dung 94]'s dialogue-game formulation of [Dung 93b] well-founded semantics; main contribution is extension to defeasible priorities. Dialectical form suggested by [RES 1977]; reconstructed by [BRE 94b] with default logic; [VRE 93b] dialectical proof theory for [VRE 93a]; [Loui 93]. *(p.41)*
- Alternative approach to priorities for extension/model-based systems: [BRE 94a] for default logic, generalised/revised by [PRA 95]: a criterion filtering extensions so that what an extension says about priorities matches the ordering it is based on; every set of justified arguments here satisfies the criterion. *(p.41)*
- Prioritised circumscription: [LIF 88] monotonic priority reasoning; [GRO 93] defeasible, but priority defaults can only resolve conflicts between lower-priority defaults, which in the authors' view makes some realistic legal examples impossible. *(p.41)*

## 10 Open Problems *(p.41-42)*
- Dialectical proof theories for the alternative semantics of [Dung 95] and the prioritised variants of §7; relation to abstract accounts [POL 87, VRE 93a, BTK 93, Dung 95]. *(p.42)*
- Relation with model-theoretic partial semantics of ELP (e.g. [WAG 94]): interpretation as I⁺ (definitely true) and I⁻ (definitely false); Γ ⊨ ~P iff P ∉ I⁺; Γ ⊨ ¬P iff P ∈ I⁻. *(p.42)*
- Suggested semantic constraints (no priorities): if A has conclusion L, B undercuts A iff A ∪ B ⊭ L; A rebuts B iff A ∪ B ⊨ ⊥. The framework would add inconsistency handling for programs with no models (where priorities matter). Another constraint: if φ is justified on Γ and Γ′ ⊆ Γ is the set of rules occurring in all justified arguments, then Γ′ ⊨ φ; and if Γ has a model, Γ ⊨ φ iff φ is justified. The argument-based treatment of NAF as undercutting (from [BTK 93], [Dung 93b]) might help choose between semantic treatments. *(p.42)*

## Conclusion *(p.42-43)*
Main contribution: formalisation of reasoning about priorities, semantically and proof-theoretically; also reasoning with prioritised rules containing exception clauses, and an alternative to [Nute 94]'s treatment of strict one-direction rules. Argument-based form to respect natural-language surface structure. Alternative definitions (e.g. a different rebut/undercut relation) possible without changing the overall structure. As an instance of the abstract theory of [BTK 93] and [Dung 95], the general form applies to any underlying logical language. *(p.42-43)*

## Appendix: Proofs *(p.43-48)*
Fixed-priority results follow from the defeasible-priority ones by omitting Lemmas 10.1 and 10.3. *(p.43)*
- **Lemma 10.1** *(p.43)*: for conflict-free S ⊆ S′ and arguments A, B: (1) if A S′-defeats B then A S-defeats B; (2) if A strictly S-defeats B then A strictly S′-defeats B. Proof: undercutting is independent of S; (1) since if no argument in S′ concludes r ≺ r′ neither does S; (2) if S has an argument for r ≺ r′, so does S′, and by conflict-freeness S′ has none for r′ ≺ r.
- **Lemma 10.2** *(p.44)*: acceptability (Def 5.3) w.r.t. a conflict-free Args is preserved for any conflict-free superset (via Lemma 10.1). Prop 3.3 (F monotonic) by the same proof for Def 3.1; Prop 5.5 immediate from 10.2.
- **Prop 3.7 proof** *(p.44)*: suppose least fixpoint S not conflict-free; S^c = arguments in conflict with any argument in S, S⁻ = S/S^c [set difference]; show F(S⁻) = S⁻, contradiction with leastness.
- **Prop 5.7 proof**: (1) from monotonicity; (2) special case of Lemma 11 of [Dung 93b]. *(p.44)*
- **Prop 5.8 proof** *(p.45)*: if Args conflict-free then G(Args) conflict-free, using Corollary 5.2 and strict defeats from Args.
- **Prop 5.9 proof** *(p.45)*: for subargument A′ of A ∈ JustArgs and B JustArgs-defeating A′: if B does not JustArgs-defeat A, A undercuts B so A strictly defeats B; otherwise some C ∈ JustArgs strictly defeats B.
- **Prop 5.11 proof**: JustArgs is the smallest conflict-free fixpoint of G. *(p.45)*
- **Prop 6.3 (soundness) proof** *(p.45)*: induction from the leaves: the last P move has no ∅-defeaters, so by Lemma 10.1 no JustArgs-defeaters; if Argᵢ₊₂ ∈ JustArgs, every Argᵢ₊₁ that ∅-defeats Argᵢ is strictly Argᵢ₊₂- or Argᵢ-defeated, hence strictly JustArgs-defeated (Lemma 10.1(2)), so Argᵢ ∈ JustArgs.
- **Prop 6.5 proof** *(p.45-46)*: prune and extend the proof tree D of A to a proof of subargument A′, handling non-repetition by grafting the subtree rooted at another strict defeater C ≠ A.
- **Lemma 10.3** *(p.46)*: for conflict-free S, if A strictly S-defeats B, there is a minimal (⊆) X ⊆ S such that A strictly X-defeats and strictly A + X-defeats B (Def 2.16 uses finitely many priority relations).
- **Prop 6.4 (completeness, finite theories) proof** *(p.46-47)*: from the finite sequence G⁰…Gⁿ with Arg₁ first in Gⁿ, build a tree where P answers each ∅-defeater from Gⁿ⁻¹ with B + X (B ∈ Gʲ⁺¹, X ⊆ Gʲ minimal, Gʲ largest with no arguments in conflict with Arg₂); non-repetition holds by choice of Gⁿ⁻¹ and Prop 3.8; repeat finitely; leaves in G¹ have no ∅-defeaters.
- **Prop 7.2 proof** *(p.47)*: if J/E ≠ ∅ for stable E, some B ∈ E E-defeating a member of J must be strictly J ∩ E-defeated by C ∈ J ∩ E, so E is not conflict-free. Prop 7.3 immediate.
- **Obs 9.3 proof** *(p.47)*: else S − G (G = members of S g-defeating B) would be a fixpoint of F^d.
- **Prop 9.5 proof** *(p.47-48)*: trivial if a self-defeating d-argument exists; otherwise the semantics coincide without priorities. Notation S^ps / S^d, A^ps / A^d (argument based on d-argument; set of assumptions of an argument). **Lemma 10.4**: if Dargs_Γ has no self-defeating arguments, the least fixpoint of F^d_Γ is the least fixpoint of F^ps_Γ. **Lemma 10.5**: if A^ps is acceptable w.r.t. S^ps then A^d is acceptable w.r.t. S^d (via Obs 9.1). Two directions: least fixpoint of F^d gives S^ps a fixpoint of F^ps, and vice versa (the proof cites "Lemma 9.3(2)", i.e. Observation 9.3(2)). *(p.48)*
- **Prop 9.7 proof**: immediate from Lemma 10.1. *(p.49)*

## Parameters
None; formal paper with no numeric quantities.

## Figures of Interest
None (no figures; dialogues are given as move lists, e.g. p.22, p.33-34).

## Results Summary
- Fixed priorities: justified set = least fixpoint of a monotonic acceptability operator; unique, conflict-free, closed under subarguments; iterative construction exact for finitary theories; dialectical proof theory sound, and complete for finitary theories. *(p.15-17, p.24-25)*
- Defeasible priorities: priority conclusions lifted via <_Args; operator G monotonic on conflict-free sets; same properties; JustArgs is a minimal complete extension and the only conflict-free one; priority-dialogue proof theory sound, complete for finite theories. *(p.26-31)*
- Credulous: stable extensions include JustArgs; arguments in some-but-not-all stable extensions are defensible; defensible extensions generalise stable ones. *(p.34-36)*
- Justified conclusions include Dung's d-well-founded conclusions (strictly more, Ex 9.6); adding priorities never removes justified conclusions. *(p.38-39)*

## Limitations
- Possibly too sceptical (Ex 3.16, specificity/inheritance case). *(p.19-20)*
- Not semi-decidable with function symbols; decidable for finitely many rules, which excludes function symbols, at odds with the r(t₁…tₙ) naming convention. *(p.36)*
- Proof theory with defeasible priorities proven complete only for finite theories. *(p.31)*
- Finitary but infinite theories: failing proofs need not terminate. *(p.25)*
- Undercutting ignoring priorities may not suit non-legal domains. *(p.13)*
- No model-theoretic semantics for the underlying logic yet. *(p.42)*

## Arguments Against Prior Work
- Specificity-as-overriding systems [GP 92] unsuitable for law. *(p.3)*
- Nute [Nute 88, 94]: only complementary-consequent rules conflict, so priorities between defeasible rules are ignored when strict rules mediate the conflict; extreme scepticism. *(p.9, p.20, p.41)*
- Brewka [BRE 96]: reduces head-to-head to head-to-body conflicts, losing the distinction between rules with and without 'unless the contrary is shown', and settles all mutual head-to-body conflicts by priority. *(p.13-14)*
- Dung 93b / BS 91 well-founded semantics collapses when any contradiction exists (Ex 9.6). *(p.38-39)*
- Default logic: the system does not extend it (two contradictory unconditional rules give no default extension). *(p.40)*
- Pollock: probabilities, no arbitrary orders or reasoning about priorities; Vreeswijk: ordering on argument forms, not premises; [GRO 93]: priority defaults only settle lower-priority conflicts. *(p.39-41)*

## Design Rationale
- Both weak and strong negation, priorities not reduced to assumptions or vice versa, to preserve legal surface structure and modular formalisation. *(p.3)*
- Strict/defeasible distinction pragmatic, not logical. *(p.6)*
- Attack via strict-rule extension of both arguments; relevance of defeasible rules computed through strict rules (Def 2.13). *(p.9, p.11)*
- Priorities compare relevant rule sets, not weakest links. *(p.11)*
- Undercut ignores priorities and beats rebuttal (coherent interpretation of law). *(p.13-14)*
- Weak defeat (≮) for doubt, strict defeat for "really better". *(p.14)*
- Proponent strict defeat, opponent plain defeat; opponent may repeat, proponent may not; minimal moves. *(p.21-24)*
- Priority predicate ≺ with strict order axioms in S; ordering built stepwise with JustArgs. *(p.26)*
- In priority dialogues, O uses ∅-defeat; P uses only its own move's priorities, or makes a pure priority move. *(p.30)*

## Testable Properties
- If A₁ attacks A₂ then A₁ defeats A₂ or A₂ defeats A₁; defeat implies attack. *(p.13)*
- For nonempty R, R < ∅; ∅ ≮ ∅: strict arguments strictly defeat conflicting defeasible ones; no strict argument strictly defeats a conflicting strict one. *(p.13)*
- F_Γ monotonic; G_Γ monotonic on conflict-free sets, not otherwise (counterexample p.28). *(p.15, p.27-28)*
- JustArgs conflict-free and subargument-closed. *(p.17, p.28)*
- If Args_S is not conflict-free, every argument is defensible. *(p.17)*
- Proofs: soundness always; completeness for finitary (fixed) / finite (defeasible priorities). *(p.24, p.31)*
- Every stable extension ⊇ JustArgs. *(p.35)*
- Ex 7.4 cycle r₁: ~a ⇒ b, r₂: ~b ⇒ c, r₃: ~c ⇒ a: all defensible, no stable extension contains any of them. *(p.35)*
- d-well-founded conclusions ⊆ justified conclusions; Ex 9.6 b justified though d-well-founded set empty. *(p.38-39)*
- Enlarging < never removes justified conclusions. *(p.39)*
- Example 3.10 yields JustArgs = {[], [r₃], [r₂]}, [r₀], [r₀, r₁] overruled. *(p.17-18)*

## Relevance to Project
A direct ancestor of propstore's ASPIC+ layer: strict vs defeasible rules, rebutting vs undercutting with undercut ignoring priorities, set comparison of relevant defeasible rules (an elitist-style "some r in R below all of R′"), grounded semantics via a characteristic function, and three-way status (justified / overruled / defensible) that keeps unresolved disagreement visible instead of forcing a winner. The defeasible-priority machinery — a ≺ predicate with strict-order axioms, priorities lifted from justified arguments step by step, priority arguments themselves attackable — is the model for render-time, argued-over preference orderings (lex superior/posterior/specialis as defeasible rules whose own conflicts are argued, Ex 6.8). Example 9.6 (a contradiction elsewhere should not collapse unrelated conclusions) matches the non-commitment discipline. The dialectical proof theory is a goal-directed query procedure comparable to `query_claim()` / `build_arguments_for()`.

## Open Questions
- [ ] Which semantic change yields the [HTT 90] result in Ex 3.16. *(p.20)*
- [ ] Dialectical proof theories for credulous/prioritised Dung semantics. *(p.42)*
- [ ] Model-theoretic (partial semantics) grounding. *(p.42)*
- [ ] Several printed slips noted inline: Ex 3.13 cites "Condition (3) of Definition 2.2" (only two conditions); Def 6.1 "Aᵢ₋₂"; Ex 6.6 "r₃: a ⇒ r₃ ≺ r₁"; Ex 3.15 strict rules written with ⇒. *(p.18, p.19, p.31)*
- [ ] Whether this author PDF differs from the typeset JANCL version (not checked).

## Related Work Worth Reading
- [Dung 93b] argumentation semantics for logic programming with explicit negation; [Dung 95] acceptability of arguments (in collection: Dung 1995 if present).
- [BTK 93] Bondarenko, Toni, Kowalski assumption-based framework.
- [BRE 96] Brewka, well-founded semantics for ELP with dynamic preferences; [BRE 94a] reasoning about priorities in default logic.
- [Nute 94] decidable quantified defeasible logic.
- [POL 87] Pollock, defeasible reasoning; [SL 92] Simari & Loui.
- [VRE 93a, 93b] Vreeswijk, abstract argumentation and defeasible dialectics.
- [PS 96b] Prakken & Sartor, dialectical model for legal reasoning.
- [HTT 90] Horty, Thomason, Touretzky sceptical inheritance.

## Collection Cross-References

### Already in Collection
- (none - the collection's Vreeswijk paper is the 1997 "Abstract Argumentation Systems", not the cited Vreeswijk 1993 thesis/JLC paper; the collection's Brewka paper is the 1989 preferred-subtheories paper, not the cited Brewka 1994/1996 papers; Dung 1995, Pollock 1987, Simari and Loui 1992 and Bondarenko et al. have no directories in this checkout)

### New Leads (Not Yet in Collection)
- Dung (1993b) - "An argumentation semantics for logic programming with explicit negation" - the semantics this system revises
- Dung (1995) - "On the acceptability of arguments and its fundamental role in nonmonotonic reasoning, logic programming, and n-person games" - the abstract semantics this system instantiates
- Brewka (1996) - "Well-founded semantics for extended logic programs with dynamic preferences" - main rival for ELP with dynamic preferences
- Nute (1994) - "A decidable quantified defeasible logic" - defeasible logic whose conflict handling this paper replaces
- Bondarenko, Toni and Kowalski (1993) - "An assumption-based framework for non-monotonic reasoning" - the framework this system is an instance of
- Prakken and Sartor (1996b) - "A dialectical model of assessing conflicting arguments in legal reasoning" - companion legal application
- Simari and Loui (1992) - "A mathematical treatment of defeasible argumentation and its implementation"
- Pollock (1987) - "Defeasible reasoning"
- Vreeswijk (1993) - "Studies in defeasible argumentation" / "Defeasible dialectics"

### Supersedes or Recontextualizes
- (none in collection; the paper is the revised and extended version of Prakken and Sartor 1996a, which is not in the collection)

### Cited By (in Collection)
- [Reasoning about preferences in argumentation frameworks](../Modgil_2009_ReasoningAboutPreferencesArgumentation/notes.md) - instantiates this system (ALP-DP) in extended argumentation frameworks (Section 7)
- [A reasoning model based on the production of acceptable arguments](../Amgoud_2002_ReasoningModelProductionAcceptable/notes.md) - ref [20]; criticizes building priorities into the definition of defeat
- [A Recursive Approach to Argumentation: Motivation and Perspectives](../Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation/notes.md) - ref [7]; structured argumentation in the ASPIC+ lineage
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) - ref [28]; extensions with dynamic priorities
- [Social Abstract Argumentation](../Leite_2011_SocialAbstractArgumentation/notes.md) - preference-based defeasible priorities, set aside for the social-web aim
- [Rich preference-based argumentation frameworks](../Amgoud_2014_RichPreference-basedArgumentationFrameworks/notes.md) - ref [20] (reference list only in its notes)
- [LLM-ASPIC+: A Neuro-Symbolic Framework for Defeasible Reasoning](../Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/notes.md) - ref [7] (reference list only)
- [Two forms of minimality in ASPIC+](../Li_2017_TwoFormsMinimalityASPIC/notes.md) - ref [13] (reference list only)
- [The ASPIC+ framework for structured argumentation: a tutorial](../Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md) - reference list only
- [An appreciation of John Pollock's work on the computational study of argument](../Prakken_2012_AppreciationJohnPollock'sWork/notes.md) - reference list only

### Tensions
- [Reasoning about preferences in argumentation frameworks](../Modgil_2009_ReasoningAboutPreferencesArgumentation/notes.md) says this system provides "only grounded status"; §7 here (pp.34-36) defines credulous stable and defensible extensions. Neither paper's system as described here has Dung-style admissible or preferred semantics for ALP-DP, which Modgil's EAF instantiation supplies.

### Conceptual Links (not citation-based)
- [Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers](../García_2014_DefeasibleLogicProgrammingDeLP-servers/notes.md) - Moderate. DeLP is the other argument-based extended logic programming line (Simari and Loui descendants): strict and defeasible rules with strong negation and a pluggable preference criterion over arguments, but evaluated by dialectical trees rather than a fixpoint; the DeLP notes describe the preference criterion as supplied externally, whereas here priorities are themselves defeasible conclusions.
