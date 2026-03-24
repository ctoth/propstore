# Abstract

## Original Text (Verbatim)

Multinomial subjective opinions are a special type of belief functions, where belief mass can be assigned to singletons of the frame as well as to the whole frame, but not to overlapping subsets of the frame. The multiplicative product of two multinomial opinions applies to the Cartesian product of the two corresponding frames. The challenge when multiplying multinomial opinions is that the raw product initially produces belief mass terms on overlapping subsets which does not fit into the opinion requirement of only having belief mass on singletons and on the whole frame. It is therefore necessary to reassign belief mass from overlapping subsets to singletons and to the frame in a way that preserves consistency for multinomial opinions. This paper describes a method for computing multinomial products of opinions according to this principle.

---

## Our Interpretation

This paper solves the problem of combining subjective opinions about different (orthogonal) aspects of a situation into a joint opinion over the combined state space. The key contribution is two methods for redistributing "excess" belief mass that arises from the Dempster-Shafer product, with the "Assumed Uncertainty" method recommended as the safer choice because it preserves more uncertainty. For propstore, this provides the formal multinomial opinion representation needed for K-ary stance classification, though fusion operators (combining same-frame opinions from different sources) require a separate paper.
