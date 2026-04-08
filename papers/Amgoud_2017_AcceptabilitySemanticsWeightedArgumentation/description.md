This paper provides an axiomatic foundation for evaluating arguments in weighted argumentation graphs (WAGs), where each argument has a basic strength in [0,1] and may be attacked by other arguments. The paper makes three contributions:

1. **15 Principles for acceptability semantics:** Extends prior work on flat graphs to weighted graphs. Principles cover anonymity, independence, directionality, neutrality, equivalence, maximality, weakening, counting, weakening soundness, reinforcement, resilience, proportionality, and three strategic principles for resolving quality-vs-quantity conflicts: Cardinality Precedence (CP), Quality Precedence (QP), and Compensation.

2. **Three novel semantics:** Each addresses one of the three strategic principles:
   - **Weighted Max-Based (Mbs):** Satisfies QP. Uses only the strongest attacker: Deg(a) = w(a) / (1 + max_{b in Att(a)} Deg(b)). Bounds: [w(a)/2, w(a)].
   - **Weighted Card-Based (Cbs):** Satisfies CP. Uses attacker count plus average strength: Deg(a) = w(a) / (1 + |AttF(a)| + avg_{b in AttF(a)} Deg(b)). Only considers founded (w>0) attackers.
   - **Weighted h-Categorizer (Hbs):** Satisfies Compensation. Uses sum of attacker strengths: Deg(a) = w(a) / (1 + sum_{b in Att(a)} Deg(b)). Extends Besnard & Hunter 2001 to weighted cyclic graphs.

3. **Formal comparison (Table 1):** First principled comparison of 10 semantics (Grounded, Stable, Preferred, Complete, IS, DF-QuAD, TB, Mbs, Cbs, Hbs) against all 15 principles. Shows Dung-family semantics satisfy very few principles in weighted settings. The three novel semantics each satisfy all principles compatible with their strategic choice.

Key theoretical results: CP, QP, and Compensation are pairwise incompatible (Prop 1). All three scoring functions converge (Thms 3, 8, 12). Each fixed-point equation uniquely characterizes its semantics (Thms 5, 10, 14). Counter-Transitivity follows from a subset of principles (Thm 2).

Published at IJCAI 2017, pages 56-62.
