---
title: "Contextual Agent Deliberation in Defeasible Logic"
authors: "Mehdi Dastani, Guido Governatori, Antonino Rotolo, Insu Song, Leendert van der Torre"
year: 2007
venue: "PRIMA 2007 / 10th Pacific Rim International Workshop on Multi-Agents (LNAI 5044), Springer 2008"
doi_url: "https://doi.org/10.1007/978-3-540-76872-2_8"
pages: "98-109"
affiliations:
  - "Department of Information and Computing Sciences, University of Utrecht"
  - "School of Information Technology and Electrical Engineering, The University of Queensland"
  - "CIRSFID, University of Bologna"
  - "Universite du Luxembourg, Computer Science and Communication"
---

# Contextual Agent Deliberation in Defeasible Logic

## One-Sentence Summary
The paper extends Defeasible Logic with modal operators (BEL, INT, DES, OBL), an ⊗-preference connective over rules and literals, and a layer of *meta-rules* (rules whose consequents are themselves rules), and gives proof theory for both literals and rules so a cognitive agent can defeasibly conclude *which rules for goals are in force in the current context* before applying them to derive desires/intentions/obligations. *(p.98-99)*

## Problem Addressed
Existing rule-based cognitive agents in DL handle interactions among beliefs, desires, intentions, and obligations via fixed rule priorities and conversions. As interaction patterns grow more complex (an obligation may derive an intention to travel by train at one moment and by plane at another), making the *context* explicit in rules and choosing between rules becomes unwieldy. The paper asks how to define the proof theory of *nested* rules and explicit preferences among rules so a single language can describe a wide class of context-dependent deliberation patterns (selfish vs. social agents, norm internalization, defeated alternatives) with linear-rule complexity rather than the high cost of temporal BDI logics. *(p.98-100)*

## Key Contributions
- A modal extension of DL with a contextual rule type C (for "contextual or meta-rule") alongside BEL, INT, DES, OBL atomic rules. *(p.100)*
- Meta-rules: a strict / defeasible / defeater rule whose consequent is itself a rule (or an ⊗-sequence of rules), supporting nested deliberation. *(p.100, Def. 1, Def. 2)*
- The ⊗ connective lifted from literals to rules, encoding ordered preferences "α preferred, but if α is violated then β, and if β is violated then γ." *(p.99-100)*
- Definitions of *Sub-rule*, *modal-free rule*, *rule-supporting set R^C⟨r⟩*, and *maximal provable-rule-sets RP^X*, which together let proofs treat rules as first-class derivable objects. *(p.102, Defs. 3-6)*
- Definitions of *incompatibility* between non-nested rules, both atomic-incompatible and negative-incompatible, generalising literal complementation to rule complementation. *(p.103, Defs. 7-8)*
- Proof tags ±Δ_X q / ±∂_X q for literals and the new tags ±Δ_C^{▷X} r / ±∂_C^{▷X} r for rules, with full provability/applicability/discardment proof procedures. *(p.103-105, Defs. 9-10, Remark 1)*
- Demonstration through two extended examples: a Tolkienian "Frodo" agent with eight interacting rules over OBL/INT modalities and a superiority relation, and an office-assistant agent that detects "weekly meeting" vs. "daily meeting" context to disambiguate an "On" command. *(p.103, p.107-108)*

## Methodology
A proof-theoretic extension of standard Defeasible Logic. The authors:
1. Extend the language with modal operators and an ⊗-preference connective. *(p.100)*
2. Partition rules into atomic rules (for BEL, DES, INT, OBL) and meta-rules (for C). *(p.101)*
3. Introduce a contextual defeasible agent theory D = (F, R^BEL, R^C, >, c). *(p.102, Def. 2)*
4. Define provability for both literals and rules using sequence-based proofs P with proof tags Δ, ∂, ±, and modality subscripts. *(p.103-105)*
5. Layer literal proofs on top of rule proofs: literal applicability requires the supporting rule to itself be provable. *(p.106, Remark 2)*
6. Use conversions c(Y, X) ⊆ MOD × MOD to allow a rule of one modality to act as another (e.g., c(OBL, INT) treats an obligation rule as an intention rule). *(p.102, p.104)*
7. Validate via worked examples; no formal complexity proofs are given here (only the design claim of "at most linear in the number of rules"). *(p.99)*

## Key Equations / Formal Constructs

### Language atoms and modalities

$$
\mathrm{MOD} = \{\mathrm{BEL}, \mathrm{OBL}, \mathrm{INT}, \mathrm{DES}\}
$$
The four modal operators of the agent's mental state. *(p.101)*

$$
\mathrm{L} = \mathrm{PROP} \cup \{\neg p \mid p \in \mathrm{PROP}\}
$$
The literal set; ∼q is the complementary literal. *(p.101)*

$$
\mathrm{MLit} = \{Xl, \neg Xl \mid l \in L,\ X \in \{\mathrm{DES}, \mathrm{INT}, \mathrm{OBL}\}\}
$$
Modal literals (BEL is implicit for unmodalised literals). *(p.101)*

### ⊗-expressions over literals

$$
\mathrm{PREF} = \{ l_1 \otimes \dots \otimes l_n : n \geq 1,\ \{l_1, \dots, l_n\} \subseteq L \}
$$
Ordered-preference expressions on literals; α ⊗ β ⊗ γ means "α preferred, then β if α violated, then γ." *(p.100, p.101)*

### Atomic rule sets (X ∈ MOD)

$$
\mathrm{Rule}_{atom,s} = \{ r : \phi_1, \dots, \phi_n \to_X \psi \mid r \in \mathrm{Lab},\ A(r) \subseteq L \cup \mathrm{MLit},\ \psi \in L \}
$$
Strict atomic rules. *(p.101)*

$$
\mathrm{Rule}_{atom,d} = \{ r : \phi_1, \dots, \phi_n \Rightarrow_X \psi \mid r \in \mathrm{Lab},\ A(r) \subseteq L \cup \mathrm{MLit},\ \psi \in \mathrm{Pref} \}
$$
Defeasible atomic rules; their head is an ⊗-sequence. *(p.101)*

$$
\mathrm{Rule}_{atom,dft} = \{ r : \phi \rightsquigarrow_X \psi \mid r \in \mathrm{Lab},\ A(r) \subseteq L \cup \mathrm{MLit},\ \psi \in \mathrm{Pref} \}
$$
Defeater atomic rules. *(p.101)*

### Meta-rules (consequents are rules)

$$
\mathrm{Rule}^C_s = \{ r : \phi \to_C \psi \mid r \in \mathrm{Lab},\ \phi \subseteq L \cup \mathrm{MLit},\ \psi \in \mathrm{Rule}^X \}
$$
$$
\mathrm{Rule}^C_d = \{ r : \phi \Rightarrow_C \psi \mid r \in \mathrm{Lab},\ \phi \subseteq L \cup \mathrm{MLit},\ \psi \in Q \}
$$
$$
\mathrm{Rule}^C_{dft} = \{ r : \phi \rightsquigarrow_C \psi \mid r \in \mathrm{Lab},\ \phi \subseteq L \cup \mathrm{MLit},\ \psi \in Q \}
$$
Meta-rules of strict / defeasible / defeater type. *(p.102)*

$$
Q = \{ a_1 \otimes \dots \otimes a_n \mid n \geq 1,\ \{a_1, \dots, a_n\} \subseteq \mathrm{Rule} \}
$$
The set of ⊗-rules: ordered-preference sequences over rules (so meta-rule heads can express "rule a_1 preferred; if violated, rule a_2; etc."). *(p.102)*

### Contextual defeasible agent theory

$$
D = (F,\ R^{\mathrm{BEL}},\ R^C,\ >,\ c)
$$
With F ⊆ L ∪ MLit a finite fact set; R^BEL ⊆ Rule^BEL the belief rules; R^C ⊆ Rule^C the meta-rules (rules for goals appear here as meta-rules with empty body); > ⊆ (Rule × Rule) ∪ (R^C × R^C) an acyclic superiority; c ⊆ MOD × MOD a set of conversions. *(p.102, Def. 2)*

Belief rules are not contextualised and derive only unmodalised literals; rules for goals are *viewed as meta-rules with an empty antecedent* whose head is an ⊗-sequence of rules for goals — this is the structural device that lets the deliberation logic put rules-as-goals on the same footing as goals-as-literals. *(p.102)*

### Sub-rule

$$
\mathrm{Sub}(r) = \{ A(r) \triangleright_X \otimes_{i=1}^j a_i \mid C(r) = \otimes_{i=1}^n a_i,\ j \leq n \},\ \text{if } r \text{ is atomic}
$$
$$
\mathrm{Sub}(r) = \{ \neg(A(r) \triangleright_X \otimes_{i=1}^j a_i) \mid C(r) = \otimes_{i=1}^n a_i,\ j \leq n \},\ \text{otherwise}
$$
Truncations of an ⊗-sequence head, used to talk about "the i-th preferred alternative implied by r." *(p.104, Def. 3)*

### Modal-free rule

$$
L(r) \text{ is } r \text{ with all modal operators stripped from } A(r)
$$
For r : INT a →_INT b, L(r) = r : a →_INT b. *(p.104, Def. 4)*

### Rule-supporting set

For a non-nested rule r^▷X ∈ Rule, if r^▷X ∈ Rule_atom and ∀a ∈ A(r): a = Xb ∈ MLit:

$$
R^C \langle r^{\triangleright X} \rangle = \bigcup_{s^{\triangleright X} \in \mathrm{Sub}(r^{\triangleright X})} \left( R^C[c_i = s^{\triangleright X}] \cup \bigcup_{Y : c(Y, X)} R^C[c_i = L(s^{\triangleright Y})] \right)
$$
Otherwise:
$$
R^C \langle r^{\triangleright X} \rangle = \bigcup_{\forall s^{\triangleright X} \in \mathrm{Sub}(r^{\triangleright X})} R^C[c_i = s^{\triangleright X}]
$$
The meta-rules in R^C that *support* deriving r — i.e. meta-rules whose head ⊗-sequence contains r (or one of its sub-rules) at some position c_i. *(p.104, Def. 5)*

### Maximal provable-rule-sets

For X ∈ {DES, INT, OBL}:
$$
RP^X = \{ \mathrm{Sub}(c_i) \mid C(r) = \bigotimes_{i=1}^n c_i,\ r \in R^C \} \cup \{ \mathrm{Sub}(L(c_i^{\triangleright Y})) \mid \forall Y \text{ s.t. } sc(Y, X),\ C(r) = \otimes_{i=1}^n c_i^{\triangleright X},\ r \in R^C,\ \forall a \in A(r): a = Xb \in \mathrm{MLit} \}
$$
$$
RP^{\mathrm{BEL}} = \{ \mathrm{Sub}(r) \mid r \in R^{\mathrm{BEL}} \}
$$
The set of all rules that are *possibly* provable in D; subsequent proof procedures search inside RP^X. *(p.104, Def. 6)*

### Incompatibility (non-nested rules)

Atomic-incompatibility:
$$
A(r) = A(r'),\ C(r) = \bigotimes_{i=1}^n a_i,\ C(r') = \bigotimes_{i=1}^m b_i,\ \exists j \leq \min(n,m): a_j = \sim b_j \text{ and } \forall j' < j: a_{j'} = b_{j'}
$$
The two heads agree on a prefix and disagree at position j. *(p.105, Def. 7.1)*

Negative-incompatibility:
$$
A(r) = A(r'),\ C(r) = \bigotimes_{i=1}^n a_i,\ C(r') = \bigotimes_{i=1}^m b_i,\ N = \min\{n, m\},\ \forall j \leq N: a_j = b_j
$$
A negated rule whose head is a (possibly shorter) prefix of the head of r. *(p.105, Def. 7.2)*

$$
IC(r^{\triangleright X}) = \{ r' \mid r' \in RP^X,\ r' \text{ is incompatible with } r^{\triangleright X} \}
$$
The set of all (possibly provable) rules that block the derivation of r. *(p.105, Def. 8)*

### Proof tag semantics

$$
\pm \Delta_X q,\quad \pm \partial_X q,\quad \pm \Delta_C^{\triangleright X} r,\quad \pm \partial_C^{\triangleright X} r
$$
+Δ_X q: q is *definitely* provable in D using only facts and strict rules; −Δ_X q: q is *definitely not* provable; +∂_X q: q is *defeasibly* provable; −∂_X q: q is *defeasibly not* provable. The C-superscripted forms say the same about a *rule* r with respect to meta-rules. *(p.103, p.106)*

## Key Definitions (verbatim, paraphrased only where necessary)

- **Definition 1 (Language).** Specifies PROP, L, MLit, PREF (⊗-expressions over literals), the labelled atomic rule sets Rule_{atom,s/d/dft}, and the labelled rule set Rule = Rule_atom ∪ {¬r | r ∈ Rule_atom}, plus complementation ∼r on rules. *(p.101)*
- **Definition 2 (Contextual Defeasible Agent Theory).** D = (F, R^BEL, R^C, >, c); structure as above. *(p.102)*
- **Definition 3 (Sub Rule).** Sub(r) is the set of head-prefix truncations (negated when r is non-atomic). *(p.104)*
- **Definition 4 (Modal Free Rule).** L(r) drops modal operators from antecedents. *(p.104)*
- **Definition 5 (Rule-Supporting Rules).** R^C⟨r^▷X⟩ collects meta-rules whose ⊗-head mentions r (or a sub-rule of r), under the modality conversions in c. *(p.104)*
- **Definition 6 (Maximal Provable-Rule-Sets).** RP^X for X ∈ {DES, INT, OBL} and RP^BEL. *(p.104)*
- **Definition 7 (Incompatibility of two non-nested rules).** Atomic vs. negative incompatibility. *(p.105)*
- **Definition 8.** IC(r^▷X) collects all rules in RP^X incompatible with r^▷X. *(p.105)*
- **Definition 9 (Provable / Rejected).** A literal/rule is #-provable in proof P if some prefix P(1..m) ends with the appropriate tagged conclusion; symmetric definition for #-rejected. *(p.105)*
- **Definition 10 (Applicable / Discarded).** When a rule's antecedents are defeasibly provable (or rejected), with conversion-aware variants. Includes: a rule r ∈ R^BEL ∪ R^C is applicable iff every literal antecedent is +∂_BEL-provable and every modal-literal antecedent Xb is +∂_X-provable; a rule r ∈ R[c_i = q] is applicable in the condition for ±∂_X iff either (a) r ∈ R^X_atom and antecedents are appropriately provable, or (b) r ∈ R^Y_atom with c(Y, X) ∈ c. *(p.105-106)*

## Proof Procedures (Algorithms)

The paper gives proof procedures for both rules and literals.

### Proof procedure for *strict derivation of rules*

+Δ_C^{▷X}: P(i+1) = +Δ_C r^▷X iff
  (1) X = BEL and r^▷X ∈ R^BEL, or
  (2) ∃ s ∈ R^C_s ⟨r^▷X⟩, ∀ a ∈ A(s) a is Δ-provable. *(p.106)*

−Δ_C^{▷X}: P(i+1) = −Δ_C r^▷X iff
  (1) X ≠ BEL or r^▷X ∉ R^BEL, and
  (2) ∀ s ∈ R^C_s ⟨r^▷X⟩, ∃ a ∈ A(r): a is Δ-rejected. *(p.106)*

### Proof procedure for *defeasible derivation of rules*

+∂_C^{▷X}: P(n+1) = +∂_C r^▷X iff
  (1) +Δ_C r^▷X ∈ P(1..n), or
  (2)
    (1) ∀ r'' ∈ IC(r^▷X), ∀ r' ∈ R^C_s ⟨r''⟩, r' is discarded, and
    (2) ∃ t ∈ R^C ⟨c_i = r^▷X⟩ such that
      (i) ∀ i' < i, c_{i'} is applicable,
      (ii) ∀ i' < i, C(c_{i'}) = ⊗^n_{k=1} b_k, ∀ k: +∂_BEL ∼b_k ∈ P(1..n),
      (iii) t is applicable, and
    (3) ∀ r'' ∈ IC(r^▷X), ∀ s ∈ R^C ⟨d_i = r''⟩, either:
      (i) if ∀ i' < i, d_{i'} is applicable, C(d_{i'}) = ⊗^n_{k=1} a_k s.t. ∀ k: +∂_BEL ∼a_k ∈ P(1..n), then s is discarded, or
      (ii) ∃ z ∈ R^C ⟨p_i = r'''⟩: r''' ∈ IC(C(s)) s.t. ∀ i' < i, p_{i'} is applicable and z is applicable and z > s. *(p.107)*

−∂_C^{▷X}: dual procedure — the discharge / rejection version of the above. *(p.107)*

### Proof procedure for *literals* (under meta-rule supervision)

+Δ_X: If P(i+1) = +Δ_X q then
  (1) Xq ∈ F (or q ∈ F if X = BEL), or
  (2) ∃ r ∈ Rule^X_s [q]: +Δ_C r and ∀ a ∈ A(r), a is Δ-provable, or
  (3) ∃ r ∈ Rule^Y_s [q]: +Δ_C r, ∀ a ∈ A(r) a is Δ-provable and c(Y, X). *(p.108)*

+∂_X: If P(n+1) = +∂_X q then
  (1) +Δ_X q ∈ P(1..n), or
  (2)
    (i) −Δ_X ∼q ∈ P(1..n), and
    (ii) ∃ r ∈ Rule_{sd}[c_i = q] such that +∂_C r, r is applicable, ∀ i' < i, +∂_BEL ∼c_{i'} ∈ P(1..n), and
    (iii) ∀ s ∈ Rule[c_j = ∼q]: either −∂_C s, or s is discarded, or ∃ j' < j s.t. −∂_BEL ∼c_{j'} ∈ P(1..n), or
      (1) ∃ t ∈ Rule[c_k = q] such that +∂_C t, t is applicable and ∀ k' < k, +∂_BEL ∼c_{k'} ∈ P(1..n) and t > s. *(p.108)*

−Δ_X / −∂_X: dual rejection procedures. *(p.108)*

**Remark 2 (key conceptual claim):** The defeasible proof of a rule runs in three phases: (a) find an argument *in favour* of the rule we want to prove, (b) examine all counter-arguments (rules for the opposite conclusion), (c) rebut all counter-arguments (counter is weaker than pro) or undercut (some counter premise not provable). *(p.107)*

**Remark 1 (conversions):** Conversions affect rule applicability. Examples (p.106):
  +Δ_INT GoToRome, GoToRome →_BEL GoToItaly ⊢ +Δ_INT GoToItaly
  +∂_INT GoToRome, GoToRome ⇒_OBL VisitVatican ⊢ +∂_INT VisitVatican

## Worked Examples

### Example 1 (Frodo agent) *(p.103, p.108)*

F = {INT-Entrusted, Selfish, Brave, ¬KillSauron}
R = {
  r1: OBL-Mordor ⇒_OBL DestroyRing ⊗ LeaveMiddleEarth
  r2: INT-RingBearer ⇒_OBL Mordor
  r3: INT-RingBearer ⇒_INT ¬DestroyRing ⊗ BackToShire
  r4: Entrusted ⇒_OBL RingBearer
  r5: Brave ⇒_C (r0 : ∅ ⇒_INT KillSauron) ⊗ ¬(r3 : INT-RingBearer ⇒_INT ¬DestroyRing ⊗ BackToShire)
  r6: Selfish ⇒_C (r7 : INT-Entrusted →_INT KillElrond)
  r8: Selfish, INT-KillElrond ⇒_C (r9 : INT-RingBearer ⇒_OBL ¬DestroyRing)
}
> = {r3 > r1, r5 > r8}
c = {c(OBL, INT)}

The example shows how, given Frodo's facts (selfish + brave + does-not-kill-Sauron + intends-to-be-entrusted), the conversion c(OBL, INT) makes r2 and r3 applicable; r6, r7 makes the intention to kill Elrond derivable; r5 attacks r3 because Brave triggers a meta-rule whose first ⊗-choice (kill Sauron) is violated by ¬KillSauron, forcing the second choice ¬r3, which makes r3 inapplicable even though r3 > r1. *(p.108)*

### Example 2 (Office assistant / context detection) *(p.108-109)*

F = {MRoom, Monday, Morning, onProjector}
R^BEL = {
  r1: MRoom, Monday, Morning ⇒_BEL CWMeeting
  r2: MRoom, Monday, Morning ⇒_BEL ¬CDMeeting
  r3: MRoom, Morning ⇒_BEL CDMeeting
  r4: onProjector →_BEL ¬trunOnProjector
}
R^C = {
  r5: CWMeeting ⇒_C (MessageOn ⇒_INT trunOnProjector ⊗ openWMPresentation ⊗ openDMPresentation)
  r6: CDMeeting ⇒_C (MessageOn ⇒_INT trunOnProjector ⊗ openDMPresentation ⊗ openWMPresentation)
}

Rules r1, r2, r3 detect the context (CWMeeting vs. CDMeeting). Once context is established, r5 or r6 enables a different intention rule whose ⊗-head encodes the preferred fallback chain (turn on projector → open weekly-meeting presentation → open daily-meeting presentation, or with the order reversed for daily meetings). With facts implying CWMeeting and a projector already on (so trunOnProjector is blocked by r4), the agent concludes +∂_INT openWMPresentation. The example demonstrates how *contextual information enables certain rules and changes priority between deliberations*. *(p.109)*

### Example 3 (continuation of Frodo) *(p.107-108)*

The continuation walks through which derivations succeed: +Δ_INT Entrusted from facts, conversion makes r2 and r3 applicable, r5 and r6 are applicable; r6 derives the rule r7 which is applicable (intention to kill Elrond), making r8 applicable. Conflict between r5 and r8: r5 stronger. The first-choice arm of r5 (intention to kill Sauron) is violated by ¬KillSauron, so the second-choice arm ¬r3 fires, making r3 inapplicable — even though r3 > r1, the meta-rule r5 strips r3 of applicability. *(p.108)*

## Parameters / Quantitative Claims

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of modalities | \|MOD\| | – | 4 | 4 | 101 | BEL, OBL, INT, DES |
| Modal-literal modalities (excl. BEL) | – | – | 3 | 3 | 101 | DES, INT, OBL only |
| Rule arrow types | – | – | 3 | 3 | 101 | →, ⇒, ⤳ (strict, defeasible, defeater) |
| Superiority relation property | > | – | acyclic | – | 102 | Acyclic binary relation on Rule × Rule ∪ R^C × R^C |
| Computational complexity claim | – | – | linear | – | 99 | "at most linear (in the number of rules)" |
| Conversion arity | c | – | binary | MOD × MOD | 102 | c ⊆ MOD × MOD |
| ⊗-sequence minimum length | n | – | 1 | n ≥ 1 | 101, 102 | Both for PREF and for Q (rule-⊗) |

## Figures of Interest

The paper contains no labelled figures; all formalism is in equations and worked examples. Two narrative examples (Frodo, Office Assistant) carry the empirical content.

## Limitations / Stated

- The paper does not provide a formal complexity proof; the "at most linear" claim is a design target, not a theorem here. *(p.99)*
- Belief rules are *not* contextualised, deliberately, and only derive unmodalised literals. This is a design choice but limits expressiveness for belief-context interactions. *(p.101-102)*
- The authors note further research is needed: development of a methodology for using the language, and a formal analysis of the logic. *(p.109)*
- Definitions 5 and 6 are forward-referenced as "propaedeutic" and the master definition (called Def. ?? in the postprint due to a TeX rendering bug) is not surfaced explicitly — the proof procedures depend on whichever full RP^X / R^C⟨·⟩ definition the published version contains; readers should consult the LNAI 5044 print for any clarifications. *(p.104)*
- All references in the body of the postprint are rendered as [?] (broken bibtex/cite expansion in the ORBilu publisher postprint); the actual reference list is on p.109 of the postprint. The paper-process workflow should treat the [?] markers as opaque and rely on the bibliography for citation traceback. *(p.98-100, p.109)*

## Arguments Against Prior Work

- Against pure temporal BDI logics (BDI-CTL realisms / commitment strategies): they have *high computational complexity* and have focused on a relatively *small class of agent types*; deliberation logics need to be efficient and to cover a much broader interaction space. *(p.99)*
- Against simple contextualisation by adding antecedents to rules: this works in the simplest case but *transformations may be problematic when complex reasoning patterns are considered*; meta-rules are needed instead. *(p.100)*
- Against rule-priority + conversion alone: as interaction patterns scale, rule priorities + conversions become unwieldy and cannot express "social agent turning into selfish agent because of resource constraints" cleanly; meta-rules + ⊗-on-rules close the gap. *(p.99)*

## Design Rationale

- *Rules for goals are meta-rules with empty antecedent.* This unification — rather than treating goals and rules as separate object kinds — is what lets the proof theory talk uniformly about derivability of literals and derivability of rules. *(p.102)*
- *Belief rules are kept un-contextualised.* They are the agent's "reasoning core" and produce only unmodalised literals; this prevents accidental modal blow-up when contextualisation is layered on top. *(p.101-102)*
- *⊗ on rules (Q) parallels ⊗ on literals (PREF).* This deliberate symmetry means a meta-rule's preferred fallback chain reads exactly like a literal's preferred fallback chain. *(p.100, p.102)*
- *Conversions are first-class.* By promoting c ⊆ MOD × MOD into the theory, the authors avoid encoding modality conversions inside specific rules and instead get cross-modality applicability for free in the proof procedures. *(p.102, p.106)*
- *Two notions of incompatibility (atomic vs. negative).* Atomic captures classical conflict on a head prefix; negative captures conflict via head-prefix on a *negated* rule, so that meta-rules whose heads contain ¬r' can systematically block r'. *(p.105)*

## Testable Properties

- The superiority relation > must be acyclic. *(p.102)*
- A rule r ∈ R^BEL ∪ R^C is applicable iff every literal antecedent is +∂_BEL-provable and every modal-literal antecedent Xb is +∂_X-provable. *(p.105)*
- For a rule r ∈ R[c_i = q] in the condition for ±∂_X with conversion c(Y, X), r is applicable if its antecedents are +∂_X-provable. *(p.106)*
- A defeasibly provable rule may be derived only if every rule in IC(r^▷X) is either rejected or fails to be applicable / supported. *(p.107)*
- Strict-atomic rules can act as defeasible rules when defeasibly derived (a →_INT b becomes a ⇒_INT b under defeasible derivation). *(p.107)*
- The notion of applicability *requires* that conversions are taken into account; ignoring c can change applicability. *(p.106, Remark 1)*
- A meta-rule with head r ⊗ ¬r' allows r to be the first choice and disabling r' to be the fallback when r is "violated"; the proof procedure realises this through Sub(·) and incompatibility. *(p.103-105)*

## Implementation Notes for propstore

- The paper's contextual deliberation is **agent-side** to Al-Anbaki et al. (2019)'s contextualised defeasible knowledge base. It tells you how an agent *picks among rules* in a given context once that context's facts are settled — exactly the gap propstore needs on the action side. *(p.98)*
- The contextual rule type C maps cleanly to propstore's `propstore.defeasibility` exception-injection point and to `propstore.aspic_bridge` rule-priority surface. A meta-rule head r ⊗ ¬r' is a Dung-defeat candidate at the ASPIC+ boundary.
- Conversions c(Y, X) ⊆ MOD × MOD correspond to typed lifting between context-qualified claim families (e.g., obligation-flavoured ist(c, p) being read as intention in a different context). They live naturally in the lifting-rule layer that propstore exposes via `research-papers:author-lifting-rules`.
- The ⊗-on-rules construct Q does **not** have a direct propstore primitive yet. It can be encoded as a sequence of stance-paired Dung defeats with explicit prefix conditions, but requires authoring discipline.
- The proof tags (±Δ, ±∂) and their rule-level counterparts (±Δ_C, ±∂_C) align with the source-branch claim provenance taxonomy `measured / calibrated / stated / defaulted / vacuous` only loosely — the DL tags express *strength of derivation*, not *origin of evidence*. Both should be carried separately on stored claims.
- The Frodo and Office-Assistant examples are good integration-test seeds for any propstore extension that wants to demonstrate "context resolves which rule to apply" — both are small, fully formalised, and use only the core constructs.
- The paper is **6 printed pages of formalism**, not a survey. Direct ingestion into `pks source propose-claim` should focus on the ten definitions and the four proof procedures rather than on the narrative.

## Relevance to propstore

**High relevance.** The paper supplies the agent-side complement that the Al-Anbaki et al. (2019) survey identified as missing: a proof theory for choosing rules under contextualised conditions, with explicit interaction between conversions, preferences, and rule conflicts. Two propstore subsystems benefit directly:

1. **`propstore.aspic_bridge`** — the meta-rule + conversion + ⊗-on-rules machinery sharpens what a "rule priority + preference" surface needs to expose so an authored rules file can encode contextual interactions (selfish/social mode switching, fallback chains).
2. **`propstore.defeasibility`** — the incompatibility / counter-rule construction (Defs. 7-8) is exactly the inferential lever CKR-style justifiable exceptions need; mapping IC(r^▷X) to context-injected Dung defeats keeps ASPIC+ from owning contextual exception semantics directly.

A separate gain: the conversion construct c is the cleanest formal account propstore has for *typed lifting between modality-qualified contexts*, and it slots into the `author-lifting-rules` workflow without modification.

## Open Questions

- [ ] Does the paper's "at most linear in the number of rules" claim survive once meta-rules can stack n levels deep? The proof procedures for +∂_C^{▷X} look quadratic in IC(·) × R^C⟨·⟩ in the worst case — needs a complexity lemma.
- [ ] Does Q (⊗ on rules) compose with Q-on-Q meta-meta-rules, or is the language strictly two-level? The text suggests two-level; a clean proof would help propstore decide whether to expose nesting depth as a parameter.
- [ ] How do conversions c(Y, X) interact with strict-vs-defeasible derivation? Remark 1 gives examples but the formal closure properties (e.g. is conversion transitive?) are not stated.
- [ ] Can the negative-incompatibility notion (Def. 7.2) be reused to encode *stance retraction* as a meta-rule whose head is ¬r? Worth a propstore prototype.
- [ ] What is the relationship to Governatori & Rotolo 2012 ("Revision of Defeasible Logic Preferences"): is the superiority > here the same object that Governatori & Rotolo 2012 revise, and does the meta-rule layer change how revision propagates?
- [ ] Is the broken-citation issue (all in-text refs as [?]) due to ORBilu's postprint extraction, or did the LNAI camera-ready version also have this? Worth checking against the official Springer copy if accessible.

## Related Work Worth Reading (cited in this paper)

- **[1] Broersen, Dastani, Hulstijn, van der Torre (2002).** Goal generation in the BOID architecture. *Cog. Sc. Quart.*, 2(3-4):428-447. — origin of the BOID interaction model that the cognitive-attitude rule types here generalise.
- **[2] Cohen and Levesque (1990).** Intention is choice with commitment. *Artif. Intell.*, 42(2-3):213-261. — the canonical commitment-strategy reference whose temporal-BDI lineage this paper criticises as too costly.
- **[3] Dastani, Governatori, Rotolo, van der Torre (2005).** Programming cognitive agents in defeasible logic. *Proc. LPAR 2005*, LNAI 3835:621-636. — the immediate predecessor; this paper extends its rule types with meta-rules and ⊗-on-rules.
- **[4] Governatori, Padmanabhan, Rotolo (2006).** Rule-based agents in temporalised defeasible logic. *Proc. PRICAI 2006*, LNAI 4099:31-40. — temporal counterpart referenced as the BDI-CTL alternative.
- **[5] Governatori and Rotolo (2004).** Defeasible logic: Agency, intention and obligation. *Proc. Δeon'04*, LNCS 3065:114-128. — agency / intention / obligation foundations.
- **[6] Governatori and Rotolo (2006).** Logic of violations: A Gentzen system for reasoning with contrary-to-duty obligations. *Australasian J. Logic*, 4:193-215. — the ⊗-on-literals lineage; PREF in Def. 1 traces here.
- **[7] Governatori, Rotolo, Padmanabhan (2006).** The cost of social agents. *Proc. AAMAS 2006*, 513-520. — cost analysis underlying the "linear complexity" target.
- **[8] Rao and Georgeff (1998).** Decision procedures for BDI logics. *J. Log. Comput.*, 8(3):293-342. — classical BDI baseline.
- **[9] Song and Governatori (2005).** Nested rules in defeasible logic. *Proc. RuleML 2005*, LNCS 3791:204-208. — the immediate technical antecedent of meta-rules in this paper.

## Notes on Provenance

PDF source: ORBilu (Université du Luxembourg) institutional repository, publisher postprint of the LNAI 5044 (Springer 2008) chapter. The postprint shows in-text citations as `[?]`; the bibliography itself (p.109) is intact. Direct PDF: https://orbilu.uni.lu/bitstream/10993/25299/1/context.pdf

## Collection Cross-References

### Already in Collection

- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — Conceptual upstream on the proof-tag (`±Δ / ±∂`) system; this paper assumes that machinery and adds the rule-level tags (`±Δ_C^{▷X} / ±∂_C^{▷X}`). Not cited explicitly here (the postprint's broken `[?]` refs leave it ambiguous), but it is the canonical reference for the literal-tag layer the paper sits on top of.

### Now in Collection (previously listed as leads)

- (none) — this paper enters the collection as the agent-side companion to [Defeasible Logic for Contextualizing Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) ref [34], and was the lead surfaced from that paper's "Related Work Worth Reading."

### New Leads (Not Yet in Collection)

- **Broersen, Dastani, Hulstijn, van der Torre (2002) — "Goal generation in the BOID architecture," *Cog. Sc. Quart.* 2(3-4):428-447.** Ref [1]. Origin of the BOID interaction model that the cognitive-attitude rule types here generalise.
- **Dastani, Governatori, Rotolo, van der Torre (2005) — "Programming cognitive agents in defeasible logic," *Proc. LPAR 2005*, LNAI 3835:621-636.** Ref [3]. Direct predecessor; this paper extends its rule types with meta-rules and ⊗-on-rules.
- **Governatori, Padmanabhan, Rotolo (2006) — "Rule-based agents in temporalised defeasible logic," *Proc. PRICAI 2006*, LNAI 4099:31-40.** Ref [4]. Temporal counterpart cited as the BDI-CTL alternative whose complexity this paper aims to undercut.
- **Governatori and Rotolo (2004) — "Defeasible logic: Agency, intention and obligation," *Proc. Δeon'04*, LNCS 3065:114-128.** Ref [5]. Foundations of the agency / intention / obligation modal layer.
- **Governatori and Rotolo (2006) — "Logic of violations: A Gentzen system for reasoning with contrary-to-duty obligations," *Australasian J. Logic* 4:193-215.** Ref [6]. Source of the ⊗-on-literals connective (PREF in Def. 1) that this paper lifts to rules.
- **Governatori, Rotolo, Padmanabhan (2006) — "The cost of social agents," *Proc. AAMAS 2006*, 513-520.** Ref [7]. Cost analysis underlying the "linear complexity" target.
- **Cohen and Levesque (1990) — "Intention is choice with commitment," *Artif. Intell.* 42(2-3):213-261.** Ref [2]. Canonical commitment-strategy reference whose temporal-BDI lineage this paper criticises as too costly.
- **Rao and Georgeff (1998) — "Decision procedures for BDI logics," *J. Log. Comput.* 8(3):293-342.** Ref [8]. Classical BDI baseline.
- **Song and Governatori (2005) — "Nested rules in defeasible logic," *Proc. RuleML 2005*, LNCS 3791:204-208.** Ref [9]. Immediate technical antecedent of the meta-rule device; the formal nesting machinery here generalises this work.

### Supersedes or Recontextualizes

- (none) — this paper extends Governatori-line DL but does not supersede a paper currently in the collection.

### Cited By (in Collection)

- [Defeasible Logic for Contextualizing Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this paper as ref [34], the agent-side companion of their `L = ⟨G, β, D, λ⟩` framework. This paper supplies the proof procedure for *which rules-for-goals are in force in the current context* that Al-Anbaki et al. leave open on the deliberation side.

### Conceptual Links (not citation-based)

**Contextualised defeasible reasoning (storage ↔ deliberation):**
- [Defeasible Logic for Contextualizing Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — Strong. Al-Anbaki et al. give the contextualised KB layout (`L = ⟨G, β, D, λ⟩` with concern-encapsulated `D^X` and authority-driven `λ`); this paper gives the agent-side proof procedure that decides which rules apply in a given context. Two halves of the same engineering picture; propstore needs both.
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — Moderate. Bozzato et al.'s CKR `ist`-context with justifiable exceptions and this paper's meta-rules + IC(·) incompatibility are different formal answers to "let local context override global rules without losing consistency." Conversion between them is non-trivial but their use cases overlap.
- [Defeasible Contextual Reasoning with Arguments in Ambient Intelligence](../Bikakis_2010_DefeasibleContextualReasoningArguments/notes.md) — Moderate. Bikakis & Antoniou cite the *AAMAS* sister paper of this work (their ref [19]) — a closely related Dastani/Governatori/Rotolo/Song/van der Torre 2007 publication on contextual deliberation. Bikakis' multi-context P2P_DR algorithm and the present paper's meta-rule layer are convergent on the question of how local rule-priorities interact with cross-context evidence; pairing them is useful for any propstore distributed-reasoning surface.

**Defeasible logic / preferences over rules:**
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — Strong. Governatori is co-author on both. The 2012 paper revises the superiority relation `>` over rules; this 2007 paper introduces meta-rules whose ⊗-heads sit alongside `>` and can functionally re-prioritise rules in a context-sensitive way. Open question (recorded in this paper's notes): can 2012's revision operators be lifted from `>` to the meta-rule layer?
- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — Strong. Antoniou et al. supply the canonical `±Δ / ±∂` proof-tag system that this paper extends to rules with `±Δ_C^{▷X} / ±∂_C^{▷X}`. The team-of-rules trumping argument and DL ⊃ sceptical LPwNF result there underpin the strict-vs-defeasible derivation pattern this paper relies on.
- [Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers](../García_2014_DefeasibleLogicProgrammingDeLP-servers/notes.md) — Moderate. García & Simari's DeLP-Server contextual-query operators (⊕ ⊗ ⊖) over (Π, Δ) program pairs share the goal of context-aware rule selection at query time. Their `⊗` operator (public-wins merge) shares only the symbol with this paper's ⊗-preference connective; the underlying semantics differ. Worth pairing for any propstore design that wants context-aware backward chaining.
