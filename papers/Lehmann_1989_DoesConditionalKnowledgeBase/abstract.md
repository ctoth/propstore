# Abstract

## Original Text (Verbatim)

This paper presents a logical approach to nonmonotonic reasoning based on the notion of a nonmonotonic consequence relation. A conditional knowledge base, consisting of a set of conditional assertions of the type **if … then …**, represents the explicit defeasible knowledge an agent has about the way the world generally behaves. We look for a plausible definition of the set of all conditional assertions entailed by a conditional knowledge base. In a previous paper [17], S. Kraus and the authors defined and studied *preferential* consequence relations. They noticed that not all preferential relations could be considered as reasonable inference procedures. This paper studies a more restricted class of consequence relations, *rational* relations. It is argued that any reasonable nonmonotonic inference procedure should define a rational relation. It is shown that the rational relations are exactly those that may be represented by a *ranked* preferential model, or by a (non-standard) probabilistic model. The rational closure of a conditional knowledge base is defined and shown to provide an attractive answer to the question of the title. Global properties of this closure operation are proved: it is a cumulative operation. It is also computationally tractable. This paper assumes the underlying language is propositional.

---

## Our Interpretation

The paper isolates **Rational Monotonicity** as the missing ingredient turning System-P preferential consequence into a usable nonmonotonic logic, then defines **rational closure** K̄ as the unique ≺-least rational extension of K. The result is a tractable, well-behaved, cumulative answer to "what does K entail?", grounded in a ranked-model representation theorem and equivalent under non-standard probability semantics, with explicit limitations (inheritance failure for exceptional subclasses) that motivate the strengthened Thesis 2: any reasonable answer should be a rational superset of K̄.

Relevant for propstore as the canonical theoretical foundation for rank-based defeasibility, choice of inference policy at render time, and the lazy multi-policy commitment in storage.
