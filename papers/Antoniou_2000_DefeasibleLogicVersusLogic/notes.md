---
title: "Defeasible logic versus Logic Programming without Negation as Failure"
authors: "G. Antoniou, M. J. Maher, D. Billington"
year: 2000
venue: "The Journal of Logic Programming, vol. 42, no. 1, pp. 47-57"
doi_url: "https://doi.org/10.1016/S0743-1066(99)00060-6"
pages: "47-57"
affiliation: "School of Computing & Information Technology, Griffith University, Nathan, QLD 4111, Australia"
---

# Defeasible logic versus Logic Programming without Negation as Failure

## One-Sentence Summary
This paper compares the expressive power of Defeasible Logic (DL) with sceptical Logic Programming without Negation as Failure (LPwNF), proving DL is strictly stronger because LPwNF cannot capture *teams of rules* jointly supporting a conclusion. *(p.47)*

## Problem Addressed
Both DL and LPwNF are rule-based default reasoning frameworks that avoid negation-as-failure and instead use a priority relation among rules. The paper asks: are these frameworks interchangeable, or do they differ in inference strength and expressiveness? The answer matters because subsequent literature relies on the `±Δ / ±∂` proof tags introduced/canonicalised here. *(p.47-48)*

## Key Contributions
- A canonical proof-tag inference system for Defeasible Logic with four tagged conclusions: `+Δq` (definitely provable), `-Δq` (definitely not provable), `+∂q` (defeasibly provable), `-∂q` (defeasibly not provable). *(p.48)*
- A complete inference system with full inductive conditions for `+Δ`, `-Δ`, `+∂`, `-∂` derivations as finite tagged sequences. *(p.48-49)*
- A formal demonstration that DL is strictly stronger than sceptical LPwNF: every sceptical LPwNF conclusion is a defeasible DL conclusion, but not the reverse. *(p.47, throughout)*
- Identification of the *team-of-rules* gap: LPwNF treats each rule individually for attack/counterattack; DL aggregates all rules with the same head when assessing whether the head is supported. *(p.48, mid-paper)*
- Brief comparison to Courteous Logic Programs and Priority Logic. *(p.48)*

## Methodology
Pure formal-theoretical comparison. The paper:
1. Reviews/restates the proof theory of (propositional) Defeasible Logic with four proof tags and explicit derivation conditions.
2. Reviews LPwNF's proof theory based on type-A (top-level SLD-style) and type-B (attack) derivations.
3. Translates DL theories into LPwNF-style programs (Example 2 mirrors Example 1) to align syntactic surfaces.
4. Demonstrates by example and by structural argument that LPwNF lacks DL's team-aggregation, then proves general containment results.

## Definitions and Formal Apparatus

### Notation *(p.48)*
- Literals: if `q` is a literal, `~q` denotes the complementary literal (`~q = ¬p` when `q = p`; `~q = p` when `q = ¬p`).
- Rule `r`: antecedent `A(r)` (finite set of literals, may be empty), arrow, consequent `C(r)` (a literal).
- Three rule kinds: **strict** `A → p` ("Emus are birds"); **defeasible** `A ⇒ p` ("Birds usually fly"); **defeater** `A ⤳ p` ("Heavy animals may not fly" — blocks contrary conclusion without supporting its own).
- `R_s`: strict rules in `R`. `R_sd`: strict + defeasible rules. `R[q]`: rules with consequent `q`.
- **Superiority relation `>` on R:** acyclic (transitive closure is irreflexive), used to encode priority among rules.
- **Defeasible theory `T = (F, R, >)`:** `F` finite set of facts (literals), `R` finite rule set, `>` superiority relation on `R`.

### Conclusions (proof tags) *(p.48)*
A conclusion is a tagged literal in one of four forms:
- `+Δq`: `q` is **definitely provable** in `T`.
- `-Δq`: it has been proved that `q` is **not definitely provable** in `T`.
- `+∂q`: `q` is **defeasibly provable** in `T`.
- `-∂q`: it has been proved that `q` is **not defeasibly provable** in `T`.

### Derivations *(p.48-49)*
A derivation in `T = (F, R, >)` is a finite sequence `P = (P(1), ..., P(n))` of tagged literals; `P(1..i)` denotes the first `i` lines. Conditions:

**`+Δ` step:** If `P(i+1) = +Δq` then either
- `q ∈ F`, or
- `∃ r ∈ R_s[q]` such that `∀ a ∈ A(r) : +Δa ∈ P(1..i)`.

**`-Δ` step:** If `P(i+1) = -Δq` then
- `q ∉ F`, and
- `∀ r ∈ R_s[q]` `∃ a ∈ A(r) : -Δa ∈ P(1..i)`.

**`+∂` step:** If `P(i+1) = +∂q` then either
1. `+Δq ∈ P(1..i)`, or
2. `∃ r ∈ R_sd[q]` such that
   - 2.1. `∀ a ∈ A(r) : +∂a ∈ P(1..i)`, and
   - 2.2. `-Δ~q ∈ P(1..i)`, and
   - 2.3. `∀ s ∈ R[~q]`, either
     - 2.3.1. `∃ a ∈ A(s) : -∂a ∈ P(1..i)`, or
     - 2.3.2. `∃ t ∈ R_sd[q]` such that `∀ a ∈ A(t) : +∂a ∈ P(1..i)` and `t > s`.

**`-∂` step:** If `P(i+1) = -∂q` then
1. `-Δq ∈ P(1..i)`, and
2. either
   - 2.1. `∀ r ∈ R_sd[q]` `∃ a ∈ A(r) : -∂a ∈ P(1..i)`, or
   - 2.2. `+Δ~q ∈ P(1..i)`, or
   - 2.3. `∃ s ∈ R[~q]` such that
     - 2.3.1. `∀ a ∈ A(s) : +∂a ∈ P(1..i)`, and
     - 2.3.2. `∀ t ∈ R_sd[q]` either `∃ a ∈ A(t) : -∂a ∈ P(1..i)` or `t ≯ s`.

A tagged literal `L` is **provable** (`T ⊢ L`) iff there is a derivation in `T` whose lines include `L`. *(p.49)*

For the rest of the paper only defeasible rules and superiority are used; facts/strict rules/defeaters are dropped from the comparison. *(p.49)*

### Example 1 *(p.49)* — DL theory
Rules:
- `r1: bird(X) ⇒ fly(X)`
- `r2: penguin(X) ⇒ ¬fly(X)`
- `r3: walkslikepeng(X) ⇒ penguin(X)`
- `r4: ¬flatfeet(X) ⇒ ¬penguin(X)`
- `r5: penguin(X) ⇒ bird(X)`
Facts: `f1: bird(tweety)`, `f2: walkslikepeng(tweety)`, `f3: ¬flatfeet(tweety)`.
Priorities: `r2 > r1`, `r4 > r3`.

Reasoning:
- Both `r3` and `r4` (instantiated for `tweety`) are applicable; `r4 > r3` so `r4` wins, deriving `+∂¬penguin(tweety)` and `-∂penguin(tweety)`.
- `f1` gives `+Δbird(tweety)` and hence `+∂bird(tweety)`, so `r1` is applicable.
- `r2` (the only counter-rule) cannot apply because `-∂penguin(tweety)` was already established.
- Therefore `+∂fly(tweety)` is derivable.

### Example 2 *(p.50)* — LPwNF translation of Example 1
Same content rewritten as logic-program clauses (negative literals allowed in heads):
- `r1: fly(X) ← bird(X)`
- `r2: ¬fly(X) ← penguin(X)`
- `r3: penguin(X) ← walkslikepeng(X)`
- `r4: ¬penguin(X) ← ¬flatfeet(X)`
- `r5: bird(X) ← penguin(X)`
- `r6: bird(tweety) ←`
- `r7: walkslikepeng(tweety) ←`
- `r8: ¬flatfeet(tweety) ←`
- Priorities: `r2 > r1`, `r4 > r3`.

LPwNF can prove `fly(tweety)` via the standard SLD refutation of `← fly(tweety)` using `r1` and `r6` (the type-A derivation), with the only attack `← ¬fly(tweety)` (via `r2`) successfully counter-attacked because `r3` is in turn defeated by `r4`. The paper shows this with an argument / attack / counter-attack diagram across A, B, A derivations. *(p.50)*

## LPwNF Proof Theory (verbatim) *(p.51)*

LPwNF supports either credulous or sceptical reasoning; this paper restricts to the sceptical case.

### Type A derivation
A type-A derivation from `(G_1, r)` to `(G_n, r)` is a sequence `(G_1, r), (G_2, r), ..., (G_n, r)` where `r` is a rule and each `G_i` has the form `← q, Q` (`q` selected literal, `Q` remaining literals). For each `i ≥ 1`, there must be a rule `r_i` such that either:
1. `i = 1`, `r_i > r`, `r_i` resolves with `G_i` on `q`, and there is a type-B derivation from `({← ~q}, r_i)` to `(∅, r_i)`; **or**
2. `i > 1`, `r_i` resolves with `G_i` on `q`, and there is a type-B derivation from `({← ~q}, r_i)` to `(∅, r_i)`.
Then `G_{i+1}` is the resolvent of `r_i` with `G_i`.

### Type B derivation
A type-B derivation from `(F_1, r)` to `(F_n, r)` is a sequence `(F_1, r), ..., (F_n, r)` where every `F_i` has the form `F_i = {← q, Q} ∪ F_i'`, `q` is the selected literal, and `F_{i+1}` is constructed as follows:
1. **Base case** (`i = 1`): `F_1` must be `← q`. Let `R` be the set of rules `r_i` which resolve with `← q` and satisfy `r_i ≮ r`. Let `C` be the set of resolvents of `← q` with rules in `R`. If `[]` (the empty clause) `∉ C`, then `F_2 = C`; otherwise no `F_2`.
2. **Inductive step** (`i > 1`): Let `R` be the set of rules `r_i` which resolve with `← q, Q` on `q`. Let `R'` be the subset of `R` containing all `r_i` such that there is no A derivation from `(← ~q, r_i)` to `([], r_i)`. Let `C` be the set of resolvents of rules in `R'` with `← q, Q`. If `[]` ∉ `C`, then `F_{i+1} = C ∪ F_i'`; otherwise no `F_{i+1}`.

The key intuition (paraphrased): a type-A derivation builds a top-level proof by SLD-style resolution; every literal selected on this top-level proof must, additionally, withstand every type-B attack that could be mounted. Each type-B attack consists of resolving on `~q` and showing that no counter-A-derivation succeeds. An attacker `r'` of `r` is admissible iff `r' ≮ r` (i.e., `r` is **not** strictly stronger than `r'`); a counter-attacker `r''` of `r'` is admissible iff `r'' > r'`. *(p.50, end of §3)*

This asymmetry — attack admissibility uses `≮`, counter-attack uses `>` — encodes scepticism: it is easier to attack a positive argument than to counterattack. *(p.50)*

## Comparison: §4 *(p.51-...)*

Translation `T(P)`: given an LPwNF program `P`, `T(P)` is the defeasible theory containing the same rules (as defeasible rules) and the same superiority relation. So LPwNF rules become DL defeasible rules verbatim. *(p.51)*

Both proof systems can prove `fly(tweety)` for Examples 1/2; the structure is similar (build a chain ending in `r1`, refute the attack via `r2` because `penguin(tweety)` cannot be proved). LPwNF is top-down; DL is bottom-up. The paper claims this difference is "not fundamental" and proceeds to prove containment.

### Theorem 4.1 *(p.52)* — LPwNF ⊆ DL
**Statement:** Let `q` be a literal which can be sceptically proven in the LPwNF program `P`, that is, there is a type-A derivation from `(← q, r)` to `([], r)` for some rule `r`. Then `T(P) ⊢ +∂q`.

The proof relies on:

**Lemma 4.1 *(p.52)*** (cited from [2]): Let `T` be a defeasible theory containing no strict rules. If `T ⊢ +∂q` then `T ⊢ -∂~q`.

**Lemma 4.2 *(p.52)*** (the workhorse): Suppose there is a type-A derivation from `(G, r)` to `([], r)` in `P` where `G = ← q_1, ..., q_n`. Then `T(P) ⊢ +∂q_i` for all `i = 1, ..., n`.

**Proof sketch of Lemma 4.2 *(p.52-53)*:** Induction on the *total* length of the type-A derivation, counting all type-A and type-B steps used. Decompose: `r_1 = q_1 ← p_1, ..., p_s` is the first resolving rule, so `G_2 = ← p_1, ..., p_s, q_2, ..., q_n`. There must be a type-B derivation from `({← ~q_1}, r_1)` to `(∅, r_1)` (eq. 2). The subsequent A derivation is shorter, so apply IH to obtain `T(P) ⊢ +∂p_j` (j=1..s) and `T(P) ⊢ +∂q_i` (i=2..n) (eq. 3). Remaining: show `T(P) ⊢ +∂q_1` using +∂ clause definition. Auxiliary inductive proof shows: within a successful type-A derivation, if there is a B derivation from `(F, r')` to `(∅, r')`, then for every goal `G ∈ F` there is a literal `q ∈ G` with `T(P) ⊢ -∂q`. Two cases:

- **Case 1** (base of B-derivation, `F_1 = {← q}`): The set of attacker rules `r'' ≮ r'` whose resolvents do not derive `[]` gives `F_2 = C`. By auxiliary IH, every `G' ∈ F_2` has a literal `q'` with `T(P) ⊢ -∂q'`. From the construction, every rule with head `q` (`r''`) that satisfies `r'' ≮ r'` has some antecedent `a ∈ A(r'')` with `T(P) ⊢ -∂a` (eq. 4). Since `T(P)` has no strict rules, `T(P) ⊢ -Δq`. Then by clause (2.3) of `-∂` definition (taking `s = r'`), `T(P) ⊢ -∂q`. *(p.53)*

- **Case 2** (inductive step on B-derivation): Subcases based on whether `R' ≠ R`. **Case 2.1:** if `R' ≠ R`, some rule `r' ∈ R` has a counter-A-derivation. By the *outer* induction hypothesis, `T(P) ⊢ +∂~q`; by Lemma 4.1 `T(P) ⊢ -∂q`, completing the auxiliary claim for `← q, Q`. **Case 2.2** (`R = R'`): every rule `q ← B` produces goal `← B, Q ∈ F_2`; by auxiliary IH every such goal has a literal `s` with `T(P) ⊢ -∂s`. **Subcase 2.2.1:** if some `s` is in `Q`, the same `s` works for `← q, A`. **Subcase 2.2.2:** otherwise the `-∂` literal is in the body `B` for every rule with head `q`, so no rule with head `q` has all antecedents provable; by `-∂` clause (2.1), `T(P) ⊢ -∂q`. *(p.53)*

The reverse direction is **false**, demonstrated by Example 3. *(p.53-54)*

### Example 3 *(p.54)* — DL strictly stronger
Defeasible theory:
- `r1: monotreme(X) ⇒ mammal(X)`,   `monotreme(platypus)` (fact)
- `r2: hasFur(X) ⇒ mammal(X)`,       `hasFur(platypus)`
- `r3: laysEggs(X) ⇒ ¬mammal(X)`,    `laysEggs(platypus)`
- `r4: hasBill(X) ⇒ ¬mammal(X)`,     `hasBill(platypus)`
- Priorities: `r1 > r3`, `r2 > r4`.

**DL outcome:** `+∂mammal(platypus)` is provable. There are two supporting rules (`r1`, `r2`) and two attacking rules (`r3`, `r4`); each attack is overridden by some supporting rule (`r1 > r3`, `r2 > r4`). The supporting team collectively defeats the attacking team. *(p.54)*

**LPwNF outcome:** `mammal(platypus)` is **not** provable. Starting an A-derivation with `r1`, the attack via `r4` (which is *not* inferior to `r1`) cannot be counterattacked because LPwNF only counter-attacks on `r4`'s head (`¬mammal`), not on its body. The only available counterattack route would be via `r2` against `r4`'s head, but LPwNF restricts B-derivations to attacks on the *original argument*, not transitive sibling counterattacks. Symmetrically, `r2` is attacked by `r3` and that attack also cannot be defeated. So the proof of `mammal(platypus)` via `r1` fails; via `r2` fails. *(p.54)*

The text is explicit (verbatim, p.54): *"LPwNF argues on the basis of individual rules, whereas defeasible logic argues on the basis of teams of rules with the same head."*

The paper notes that even allowing LPwNF counterattacks on the same literal (`r4` attacked by `r2`, then `r2` attacked by `r3`, then `r3` attacked by `r1`, etc.) creates an infinite regress; DL avoids this by *trumping* — any attacker can be trumped by a superior rule supporting the original conclusion. *(p.54)*

### Methodological remark on relative strength *(p.54)*
A general "swap" argument fails when comparing nonmonotonic systems: if `L1 > L2` strictly, adding rules `q ← p` and `¬q ← p` should "block `q` in `L1`" so `L1` proves something extra, suggesting `L1 ≤ L2`. The paper notes this argument is **not valid** because adding rules to a defeasible theory can both help and hurt; Example 4 (below) demonstrates the subtlety. *(p.54)*

### Example 4 *(p.54-55)* — Boundary case
Extend Example 3 with `r5: ⇒ q` and `r6: mammal(platypus) ⇒ ¬q`. As expected `q` is not derivable in DL because `r6` is applicable and not weaker than `r5`. Likewise `q` is not derivable in LPwNF: the only proof of `q` via `r5` is attacked by a B-derivation involving `r6` and one of `r1, r2`; since no rule is stronger than `r1`, the attack succeeds and `q` fails. *(p.55)* Parallels: well-founded semantics is stronger than Kunen's semantics, despite analogous structural concerns. *(p.55)*

## Section 5: Other approaches *(p.55-56)*

### Courteous Logic Programs (CLP) [Grosof, ref [6]]
Shares: logic-programming foundation, sceptical reasoning, *teams of rules*, priority relation. Differences relative to DL:
1. **Stratification requirement (CLP):** atom dependency graph must be acyclic; each stratum contains only rules with head `p` or `¬p`. Answer set is built stratum-by-stratum. DL imposes no such requirement. *(p.55)*
2. **Strict vs defeasible distinction:** CLP does not distinguish; DL does. DL is more fine-grained.
3. **Defeaters:** DL has them; CLP does not. DL is more flexible.
4. **Negation as failure:** CLP allows it; DL doesn't. But a courteous program `C` with NAF can be modularly translated to a NAF-free program `C'` using auxiliary atom `p_r` per rule `r`:

   ```
   r : L ← L_1 ∧ ... ∧ L_n ∧ fail M_1 ∧ ... ∧ fail M_k
   ```
   becomes:
   ```
   r  : L  ← L_1 ∧ ... ∧ L_n ∧ p_r
   p_r ←
   ¬p_r ← M_1
   ...
   ¬p_r ← M_k
   ```
   `p_r` is a new propositional atom. `C` and `C'` have the same answer set on the language of `C`. *(p.55-56)*

### Theorem 5.1 *(p.56)* — DL captures CLP
Let `C` be a courteous logic program. Define `df(C)`: replace every rule in `C'` (the NAF-free translation) by an equivalent defeasible rule, keeping the same priority relation. Then a literal `q` is in the answer set of `C` **iff** `df(C) ⊢ +∂q`.

Note: courteous logic programs are *not* a special case of LPwNF, because they incorporate teams. Example 3 shows `mammal(platypus)` is provable in CLP but not in LPwNF. *(p.56)*

### Priority Logic (Wang/You/Yuan, refs [12, 13]) *(p.56)*
A priority-logic theory consists of LP-style rules and a priority relation. **Semantics:** once a rule `r` is included in an argument, all rules inferior to `r` are automatically blocked from being included in the same argument. Two semantics: *stable argument* (credulous) and *well-founded argument* (sceptical). Comparison restrictions:
1. Only defeasible rules; no strict/defeater distinction.
2. Restrict to propositional literals (priority logic also allows formulae).
3. Priority/superiority only on pairs of rules with **complementary heads**.
4. Two basic instantiations via extensibility functions `R_1` and `R_2`.
5. Compare DL to the *sceptical* interpretation.

### Example 5 *(p.56)* — DL ≠ Priority Logic
Empty priority relation:
- `r1: quaker ←`,  `r2: republican ←`
- `r3: pacifist ← quaker`,  `r4: ¬pacifist ← republican`
- `r5: footballfan ← republican`
- `r6: antimilitary ← pacifist`,  `r7: ¬antimilitary ← footballfan`

**Under `R_1`:** the well-founded argument is the set of all rules → inconsistent. In DL `T ⊬ +∂pacifist`. Approaches differ. *(p.56)*

**Under `R_2`:** priority logic does **not** prove `¬antimilitary`. DL **does** prove `+∂¬antimilitary`. The reason: DL does **not propagate ambiguity**, whereas extension-based formalisms like priority logic do. (See Touretzky-Horty-Thomason "A clash of intuitions" [11] for general discussion.) *(p.56)*

## Section 6: Conclusion *(p.57)*
- Four LP-based formalisms with priority + sceptical inference: defeasible logic, LPwNF, courteous logic programs, priority logic.
- DL, LPwNF, CLP belong to the **same school**; priority logic is fundamentally different (ambiguity propagation).
- Within the same school, **DL is strictly the most powerful**:
  - draws more conclusions than LPwNF (because of teams);
  - draws more conclusions than CLP (CLP requires acyclic dependency graph; DL doesn't);
  - distinguishes definite (facts + strict) from defeasible knowledge.
- Refs [2,8] further characterise DL formally (representation, inference relation properties, semantics).

## Key Equations / Statistical Models

This is a pure formal-logic paper — no statistical models. The "equations" are inference rules (already enumerated in §2 above). The most reusable canonical objects:

$$\text{Triple } T = (F, R, >)$$
Where: `F` = finite set of facts (literals), `R` = finite rule set with three flavors (strict `→`, defeasible `⇒`, defeater `⤳`), `>` = acyclic superiority relation on `R`. *(p.48)*

$$T \vdash +\Delta q,\ -\Delta q,\ +\partial q,\ -\partial q$$
The four canonical proof-tag judgments. `Δ` = definite branch (facts + strict only); `∂` = defeasible branch (uses defeasible rules and superiority). *(p.48-49)*

The full inductive conditions for each tag are reproduced verbatim in the **Definitions** section above; they are the canonical reference cited by virtually all subsequent DL literature.

## Parameters

This paper has no numerical/statistical parameters. The relevant *qualitative* parameters are the structural choices listed below.

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Rule arrow flavor | →, ⇒, ⤳ | symbolic | n/a | strict / defeasible / defeater | 48 | Three rule kinds in DL |
| Superiority relation | `>` | binary on R | acyclic | irreflexive transitive closure | 48 | Encodes priority |
| Proof tags | `±Δ`, `±∂` | symbolic | n/a | 4 tag values | 48 | Canonical conclusion tags |
| Reasoning mode | sceptical vs credulous | discrete | sceptical | {sceptical, credulous} | 51 | LPwNF supports both; paper compares sceptical only |
| Counter-attack admissibility (LPwNF B-derivation, base) | `r'' ≮ r'` | binary | — | applies if `r'` is not strictly stronger than `r''` | 51 | Base-case attacker condition |
| Counter-counterattack admissibility (LPwNF type-A initiation) | `r_i > r` | binary | — | required for first attack on top-level argument | 51 | Asymmetry encodes scepticism |
| DL `+∂` defeat condition (clause 2.3.2) | `t > s` | binary | — | requires a stronger supporting rule to trump the attacker | 49 | Encodes *team trumping* |

## Effect Sizes / Key Quantitative Results

Not applicable — pure-theory paper.

## Methods & Implementation Details
- DL inference is a **bottom-up** tagged-derivation system; every conclusion has explicit support and explicit failure tags. *(p.49, 51)*
- LPwNF inference is **top-down** with mutually recursive type-A (proof) and type-B (attack) derivations resolving on selected literals. *(p.51)*
- DL has a Prolog implementation cited via [4]. *(p.47)*
- For comparisons, translate LPwNF rules to defeasible rules verbatim with the same priority relation: `T(P)`. *(p.51)*
- For NAF-bearing courteous programs, eliminate NAF modularly with auxiliary atom `p_r` per rule (one positive `p_r ←`, one `¬p_r ← M_i` per failed body literal `M_i`). *(p.55-56)*
- Every example explicitly walks the proof through both systems so the algorithm is testable by replication.

## Figures of Interest
- **Argument / attack / counter-attack diagram (p.50):** three columns labeled `argument (A derivation)`, `attack (B derivation)`, `counter-attack (A derivation)`. Boxes show goals `← fly(tweety)`, `← ¬fly(tweety)`, `← ¬penguin(tweety)`, with rules `r1, r2, r3, r4, r6, r7, r8` annotating the resolution edges. Visualises how scepticism unfolds in LPwNF.

## Results Summary
- **Theorem 4.1:** sceptical LPwNF ⊆ defeasible logic (under translation `T(P)`). *(p.52)*
- **Counterexample (Example 3):** the converse fails — DL proves `+∂mammal(platypus)`, sceptical LPwNF does not prove `mammal(platypus)`. *(p.54)*
- **Theorem 5.1:** courteous logic programs are captured by DL (under `df(C)`). *(p.56)*
- Priority logic (Wang/You/Yuan) is in a different school — it propagates ambiguity, DL does not. *(p.56)*

## Limitations
- Restricted to **propositional** defeasible logic. *(p.48)*
- Comparison only addresses the **sceptical** interpretation of LPwNF; the credulous case is not analysed. *(p.51)*
- Comparison to priority logic restricted to:
  1. defeasible rules only,
  2. propositional literals (no general formulae),
  3. priorities only on rules with complementary heads,
  4. two basic instantiations (`R_1`, `R_2`),
  5. sceptical interpretation only. *(p.56)*
- The general "`L1 strictly stronger ⇒ swap example`" technique fails for nonmonotonic systems; the comparisons here are constructive (specific examples + theorems) rather than via that swap argument. *(p.54)*
- Facts, strict rules, and defeaters are dropped from the comparison even though they are part of full DL. *(p.49)*

## Arguments Against Prior Work
- **vs LPwNF:** LPwNF "argues on the basis of individual rules" — every counterattack must be on the same single attacker — and so cannot exploit *teams of rules* with the same head. As a result it fails to derive intuitively desirable conclusions in cases like Example 3 (platypus). *(p.53-54)*
- LPwNF cannot be patched by allowing same-literal counterattacks; this leads to infinite regress (`r1` ↔ `r2` ↔ `r3` ↔ `r4` ↔ `r1`). DL avoids this with **rule trumping**: any attacker can be defeated by a superior rule supporting the original conclusion. *(p.54)*
- **vs Courteous Logic Programs:** CLP requires the atom dependency graph to be acyclic; DL does not. CLP also fails to distinguish strict vs defeasible knowledge and lacks defeaters. *(p.55)*
- **vs Priority Logic:** Priority logic propagates ambiguity (extension-based semantics force ambiguous conclusions to remain ambiguous); DL does not. Example 5 shows DL proves `+∂¬antimilitary` while priority logic (under `R_2`) cannot. *(p.56)*

## Design Rationale
- **Why four proof tags (`±Δ`, `±∂`) instead of two?** DL needs to express both *positive* support and *positive failure* (the system has proven that something is *not* derivable). This is the technical mechanism that enables the inductive `+∂` clause to require `-Δ~q` and `∀ s ∈ R[~q]` failure or trumping. Two-valued provability cannot encode "we have proved it is not provable". *(p.48-49)*
- **Why teams of rules instead of individual rule attack/counterattack?** Without team aggregation, the DL theorist cannot say "any rule attacking `q` must be trumped by *some* rule supporting `q`" in one inductive clause; they must instead chain pairwise attacks, which leads to the LPwNF infinite-regress issue. *(p.54)*
- **Why scepticism via `≮` for attack but `>` for counterattack?** Asymmetric admissibility encodes the principle "easier to attack a positive argument than to counterattack". *(p.50)*
- **Why drop facts/strict rules/defeaters from the comparison?** They are not necessary for the comparison, and including them would complicate the proofs without changing the relative-strength conclusions. *(p.49)*

## Testable Properties
- For any LPwNF program `P`: if `P ⊢ q` (sceptical), then `T(P) ⊢ +∂q`. *(p.52, Theorem 4.1)*
- If `T` has no strict rules and `T ⊢ +∂q`, then `T ⊢ -∂~q`. *(p.52, Lemma 4.1)*
- For a successful type-A LPwNF derivation from `(← q_1, ..., q_n, r)` to `([], r)`: `T(P) ⊢ +∂q_i` for **all** `i`. *(p.52, Lemma 4.2)*
- Translation `T(·)` is **not** surjective on conclusions: there exist defeasible theories of the form `T(P)` for some `P` such that `T(P) ⊢ +∂q` while `P ⊬ q` (Example 3). *(p.54)*
- For any courteous logic program `C` and literal `q`: `q ∈ AnswerSet(C) ⇔ df(C) ⊢ +∂q`. *(p.56, Theorem 5.1)*
- DL does **not** propagate ambiguity (Example 5 vs priority logic under `R_2`). *(p.56)*
- DL's superiority relation `>` must be acyclic (transitive closure irreflexive). *(p.48)*
- Every `+∂q` derivation either grounds in `+Δq` (strict path) or builds via clause (2) of the `+∂` rule, requiring `-Δ~q` plus team-trumping for every attacker. *(p.49)*
- Every `-∂q` derivation requires `-Δq` plus *either* every supporting rule has a `-∂a` antecedent, *or* `+Δ~q`, *or* there is an attacker `s` whose every team counter-trumper fails. *(p.49)*

## Relevance to Project
This is the **canonical reference for the DL proof-tag system** propstore's defeasibility infrastructure encodes. Specifically:
- `propstore.defeasibility` implements CKR-style justifiable exceptions that decide `ist(c, p)` applicability. The underlying defeasible reasoning component must be able to manipulate the four `±Δ / ±∂` tags exactly as defined here, since the rest of the literature builds on this presentation.
- The **team-of-rules trumping** semantics (clause 2.3.2 of `+∂`, clause 2.3.2 of `-∂`) is the formal heart of the DL proof theory. propstore must be able to faithfully express "every attacker must be trumped by some supporting rule" rather than the simpler pairwise "for each attacker, find one stronger rule".
- The **acyclic superiority relation** on rules (`>` with irreflexive transitive closure) is a precondition that propstore's rule-priority machinery must enforce when authoring per-paper rules in `knowledge/rules/`.
- The strict/defeasible/defeater **trichotomy** maps directly to the rule-flavor field already present in the rule schema.
- The **CLP-to-DL embedding** via `df(C)` justifies treating CLP-style courteous logic programs (with NAF removed via the `p_r` trick) as DL theories — useful when integrating older argumentation literature.
- The **priority-logic divergence** (ambiguity propagation) is a useful boundary marker: if a propstore extension or imported KB starts propagating ambiguity (e.g., via Dung-style extensions on ambiguous AFs), it has stepped outside the DL school the rest of the system assumes.
- Bidirectional cross-reference target: this is Al-Anbaki 2019's reference [38]; the team-trumping argument is exactly what Al-Anbaki's contextualisation needs to reason about rule conflicts inside a context.

## Open Questions
- [ ] **Credulous DL vs credulous LPwNF.** The paper compares only the sceptical case. propstore primarily uses sceptical inference, but parts of the heuristic / candidate-merge layer may want credulous reasoning.
- [ ] **First-order or function-symbol case.** The paper restricts to propositional DL; full lifting requires schema-instantiation discipline (handled by [2,8] but not in this paper).
- [ ] **Constructive priority-logic embedding under `R_2`.** The paper shows DL can prove things priority logic cannot but does not give a full embedding direction.
- [ ] **Computational complexity of the four tag judgments.** Not addressed here.
- [ ] **Interaction of teams with strict rules.** The team semantics is illustrated only with defeasible rules + superiority; behaviour when strict rules also share heads is left to other papers ([2], [8]).

## Related Work Worth Reading
- [1] G. Antoniou, *Nonmonotonic Reasoning*, MIT Press 1997 — book-length DL exposition.
- [2] G. Antoniou, D. Billington, M.J. Maher, "Normal forms for defeasible logic", *Joint ICLP/SLP* 1998 — supplies Lemma 4.1 and many structural properties.
- [3] D. Billington, "Defeasible logic is stable", *J. Logic Comput.* 3 (1993), 370-400 — concatenation-of-derivations result used in the proof of Theorem 4.1.
- [5] Y. Dimopoulos, A. Kakas, "Logic programming without negation as failure", *ISLP 1995* — the LPwNF source.
- [6] B.N. Grosof, "Prioritized conflict handling for logic programs", *ILPS 1997* — courteous logic programs.
- [8] M.J. Maher, G. Antoniou, D. Billington, "A study of provability in defeasible logic", *AI 1998* — companion analysis.
- [11] D. Touretzky, J.F. Horty, R.H. Thomason, "A clash of intuitions" (IJCAI-87) — ambiguity-propagation discussion.
- [12, 13] X. Wang, J. You, L. Yuan — priority logic.

## Collection Cross-References

### Already in Collection
- (none) — none of the references [1]–[13] in this paper currently exist as separate entries in the propstore collection. Ref [11] (Touretzky/Horty/Thomason "A clash of intuitions") is a foundational nonmonotonic-multiple-inheritance paper that may be worth retrieving; refs [2], [8] are companion DL-formalisation papers; ref [5] is the LPwNF source.

### New Leads (Not Yet in Collection)
- **G. Antoniou (1997) — *Nonmonotonic Reasoning*, MIT Press [ref 1].** Book-length DL exposition; canonical secondary source for the proof-tag system.
- **G. Antoniou, D. Billington, M.J. Maher (1998) — "Normal forms for defeasible logic," ICLP/SLP 1998 [ref 2].** Provides Lemma 4.1 used here; companion structural-properties paper.
- **D. Billington (1993) — "Defeasible logic is stable," *J. Logic Comput.* 3, 370-400 [ref 3].** Concatenation-of-derivations result needed for the proof of Theorem 4.1.
- **Y. Dimopoulos, A. Kakas (1995) — "Logic programming without negation as failure," ISLP 1995 [ref 5].** The LPwNF source — required reading for the type-A / type-B derivation structure.
- **B.N. Grosof (1997) — "Prioritized conflict handling for logic programs," ILPS 1997 [ref 6].** Courteous logic programs; captured by DL via Theorem 5.1.
- **A.C. Kakas, P. Mancarella, P.M. Dung (1994) — "The acceptability semantics for logic programs," ICLP'94 [ref 7].** Used in the NAF-elimination translation for courteous programs.
- **M.J. Maher, G. Antoniou, D. Billington (1998) — "A study of provability in defeasible logic," AJCAI 1998 [ref 8].** Companion deeper analysis of inference relation, representation, semantics.
- **D. Nute (1987, 1994) — Defeasible reasoning / defeasible logic [refs 9, 10].** Original Nute-style DL papers; predecessor formulations.
- **D. Touretzky, J.F. Horty, R.H. Thomason (1987) — "A clash of intuitions," IJCAI-87 [ref 11].** The classic ambiguity-propagation discussion; cited as the boundary marker between DL and priority logic.
- **X. Wang, J. You, L. Yuan (1997) — "Nonmonotonic reasoning by monotonic inferences with priority constraints," LNAI 1216 [ref 12]; "Logic programming without default negation revisited," IEEE-IPS 1997 [ref 13].** Priority logic — the paper compared *against* in §5; a different school because it propagates ambiguity.

### Cited By (in Collection)
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this as ref [38]; reuses the `±Δ / ±δ` proof-tag system verbatim to certify justifiable contextual decisions in its `L = ⟨G, β, D, λ⟩` framework. The single most important upstream cite for understanding Al-Anbaki's proof system.
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — cites this as ref [10]; the foundational comparison paper between defeasible logic and logic programming. Governatori et al.'s revision-of-`>` framework presupposes the proof-tag derivation conditions that this paper canonicalises.

### Sister Paper (same author group, same year, same calculus)
- [Representation Results for Defeasible Logic](../Antoniou_2000_RepresentationResultsDefeasibleLogic/notes.md) — Antoniou, Billington, Governatori & Maher (2001) ACM TOCL 2(2):255-287. The two papers are the complementary halves of the canonical formal program for DL: this 2000 JLP paper places DL in the LPwNF landscape and proves DL ⊋ sceptical LPwNF via the team-of-rules mechanism; the 2001 ACM TOCL sister paper takes the same calculus and proves which of its primitives carry expressive weight (facts, defeaters, and superiority are all eliminable; strict and defeasible rules are mutually irreducible). Anyone implementing DL needs both — this paper says "what tags exist and how they fire," the sister paper says "which primitives are essential and which are syntactic sugar."

### Supersedes or Recontextualizes
- (none) — this paper introduces the canonical `±Δ / ±∂` proof-tag system but does not supersede a paper already in the collection. It is itself an upstream foundation rather than a successor.

### Conceptual Links (not citation-based)
- [The Logic of Argumentation Schemes](../Modgil_2009_ReasoningAboutPreferencesArgumentation/notes.md) — Modgil's preference-based argumentation extends Dung-style attack frameworks with explicit preference reasoning, addressing the same general problem this paper studies (priority among rules) but at the abstract-argumentation level rather than the rule-level. Conceptual convergence: both treat preferences as defeasible, both face the choice between propagating ambiguity vs trumping; this paper takes the trumping side, Modgil's framework provides the AF-level formalisation of the same intuition. Relevant for propstore's ASPIC+ / `propstore.aspic_bridge` boundary.
- [Links Between Argumentation-based Reasoning and Nonmonotonic Reasoning](../Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning/notes.md) — Li et al. study the formal relationship between ASPIC+/Dung-style argumentation and nonmonotonic reasoning systems including DL. Direct conceptual descendant of the comparison methodology used here; the LPwNF-vs-DL relationship is one specialisation of the broader argumentation/NMR correspondence Li et al. characterise.
- [Contextual Agent Deliberation in Defeasible Logic](../Dastani_2007_ContextualAgentDeliberationDefeasible/notes.md) — Strong. Dastani et al. extend the proof-tag system formalised here (`±Δ / ±∂`) with rule-level tags `±Δ_C^{▷X} / ±∂_C^{▷X}` so that *rules* can be derived in the same way literals are. Their meta-rule layer R^C and ⊗-on-rules connective Q sit directly on top of this paper's literal-tag machinery; the team-of-rules trumping pattern of Example 3 (platypus) is the same structural device that lets a meta-rule's ⊗-head encode "preferred rule, fallback rule" without ambiguity propagation.

## Quotes Worth Preserving
- "LPwNF argues on the basis of individual rules, whereas defeasible logic argues on the basis of teams of rules with the same head." *(p.53)*
- "Defeasible logic breaks this cycle by recognising that any rule attacking the argument can be 'trumped' by a superior rule supporting the argument." *(p.54)*
- "Defeasible logic does not propagate ambiguity, as extension-based formalisms like priority logic do." *(p.56)*

