# Abstract

## Original Text (Verbatim)

Truth maintenance systems have been used in recently developed problem solving systems. A truth maintenance system (TMS) is designed to be used by deductive systems to maintain the logical relations among the beliefs which those systems manipulate. These relations are used to incrementally modify the belief structure when premises are changed, giving a more flexible context mechanism than has been present in earlier artificial intelligence systems. The relations among beliefs can also be used to directly trace the source of contradictions or failures, resulting in far more efficient backtracking.

In this paper a new approach is taken to truth maintenance algorithms. Each belief, or proposition, can be in any one of three truth states, true, false, or unknown. The relations among propositions are represented in disjunctive clauses. By representing an implication in a clause the same algorithm that is used to deduce its consequent can be used to deduce the negation of antecedents that would lead to contradictions. A simple approach is also taken to the handling of assumptions and backtracking which does not involve the non-monotonic dependency structures present in other truth maintenance systems.

---

## Our Interpretation

McAllester addresses the complexity of maintaining consistent beliefs in AI problem-solving systems by introducing a three-valued logic (true/false/unknown) with clause-based representation. The key insight is that disjunctive clause representation makes deduction of negations natural and symmetric, eliminating the need for separate negation tracking. This is the intermediate system (the "RUP" TMS) between Doyle's original TMS and de Kleer's ATMS, directly relevant to the propstore's justification and assumption-tracking architecture.
