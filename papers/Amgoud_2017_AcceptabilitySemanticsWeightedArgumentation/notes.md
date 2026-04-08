# Amgoud et al. 2017 — Acceptability Semantics for Weighted Argumentation Frameworks

## Key Definitions

### Weighted Argumentation Graph (WAG) — Definition 1
- G = <A, w, R> where A is finite set of arguments, w: A -> [0,1], R subset A x A
- w(a) is basic strength, (a,b) in R means a attacks b

### Acceptability Semantics — Definition 3
- Function S mapping WAG G to vector Deg^S_G in [0,1]^n
- Deg^S_G(a) is the acceptability degree (overall strength after aggregation)

## 15 Principles

1. **Anonymity** — isomorphism-invariant
2. **Independence** — disconnected components don't affect each other
3. **Directionality** — only arguments on paths to a affect a
4. **Neutrality** — attackers with degree 0 have no effect
5. **Equivalence** — same weight + bijection-matched attacker degrees => same degree
6. **Maximality** — unattacked argument gets degree = w(a)
7. **Weakening** — alive attacker reduces degree below w(a)
8. **Counting** — more alive attackers => lower degree
9. **Weakening Soundness** — strength loss only from alive attackers
10. **Reinforcement** — stronger attacker => greater impact
11. **Resilience** — w(a) > 0 implies Deg(a) > 0 (attacks can't kill)
12. **Proportionality** — stronger target resists attack better
13. **Cardinality Precedence (CP)** — more alive attackers => strictly weaker
14. **Quality Precedence (QP)** — one strong attacker outweighs many weak
15. **Compensation** — many weak can compensate one strong

## Key Incompatibilities (Proposition 1)
- CP, QP, Compensation are pairwise incompatible
- {Independence, Directionality, Equivalence, Resilience, Reinforcement, Maximality, QP} incompatible
- CP and Compensation each compatible with principles 1-12

## Three Novel Semantics

### Weighted Max-Based (Mbs) — Definition 4-5
- f^i_m(a) = w(a) / (1 + max_{b in Att(a)} f^{i-1}_m(b)), f^0_m(a) = w(a)
- Converges (Thm 3), fixed point is unique characterization (Thm 5)
- Deg in [w(a)/2, w(a)] (Thm 7)
- Satisfies QP, violates CP, Compensation, Counting, Reinforcement (Thm 6)

### Weighted Card-Based (Cbs) — Definition 7-8
- Uses "founded" attackers only (w > 0), notation AttF_G(a)
- f^i_c(a) = w(a) / (1 + |AttF(a)| + sum_{b in AttF(a)} f^{i-1}_c(b) / |AttF(a)|)
- Converges (Thm 8), unique characterization (Thm 10)
- Deg in (0, w(a)] (Corollary 1)
- Satisfies CP, all principles except QP and Compensation (Thm 11)

### Weighted h-Categorizer (Hbs) — Definition 9-10
- f^i_h(a) = w(a) / (1 + sum_{b in Att(a)} f^{i-1}_h(b)), f^0_h(a) = w(a)
- Extends Besnard & Hunter 2001 h-categorizer to weighted cyclic graphs
- Converges (Thm 12), unique characterization (Thm 14)
- Deg in (0, w(a)] (Corollary 2)
- Satisfies Compensation, all principles except CP and QP (Thm 15)

## Comparison Table (Table 1) — 10 semantics x 15 principles
- Dung-family (Grounded, Stable, Preferred, Complete): satisfy very few (Anonymity, some Independence/Directionality)
- IS: satisfies QP but violates Maximality (counter-intuitive: accepts worthless unattacked args)
- DF-QuAD: satisfies many but violates Weakening, Counting, Reinforcement, Resilience
- TB: violates Weakening
- Mbs: satisfies 11/15 (all compatible with QP)
- Cbs: satisfies 13/15 (all compatible with CP) — first CP semantics
- Hbs: satisfies 13/15 (all compatible with Compensation) — best compensation semantics

## Implementation Relevance for propstore

### Relationship to DF-QuAD (Freedman et al. 2025)
- DF-QuAD is analyzed in Table 1 — it violates Weakening, Counting, Reinforcement, Resilience
- Hbs (weighted h-categorizer) satisfies all these plus Compensation
- Hbs equation: Deg(a) = w(a) / (1 + sum Deg(attackers)) is simpler than DF-QuAD
- Key difference: DF-QuAD conflates P_A with base score (noted in propstore CLAUDE.md)

### Direct implementation value
- All three semantics have simple iterative formulas that converge
- Unique characterization theorems mean the fixed-point equations ARE the semantics
- Could implement as alternative gradual semantics alongside DF-QuAD
- The principled comparison framework (15 principles) lets users choose semantics for their use case

### Strategic choice matters
- CP for social-network-style debates (follower counts matter)
- QP for expert-dominated domains (Fields medalist beats students)
- Compensation for balanced deliberation (weak arguments can gang up)

## Provenance
- Read from PDF: 2026-03-30
- All 7 pages (56-62) read directly
