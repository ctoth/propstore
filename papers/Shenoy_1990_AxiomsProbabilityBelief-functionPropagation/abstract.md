# Abstract

## Original Text (Verbatim)

In this paper, we describe an abstract framework and axioms under which exact local computation of marginals is possible. The primitive objects of the framework are variables and valuations. The primitive operators of the framework are combination and marginalization. These operate on valuations. We state three axioms for these operators and we derive the possibility of local computation from the axioms. Next, we describe a propagation scheme for computing marginals of a valuation when we have a factorization of the valuation on a hypertree. Finally we show how the problem of computing marginals of joint probability distributions and joint belief functions fits the general framework.

---

## Our Interpretation

The paper establishes minimal algebraic axioms (commutativity/associativity of combination, consonance of marginalization, and distributivity of marginalization over combination) that guarantee exact local computation of marginals on hypertrees via message passing. It unifies Bayesian probability propagation and Dempster-Shafer belief-function propagation under a single framework, showing both are instances of the same abstract structure. This is relevant to propstore because subjective logic extends Dempster-Shafer theory, and the axioms characterize when local (efficient) computation is valid for fusion operations.
