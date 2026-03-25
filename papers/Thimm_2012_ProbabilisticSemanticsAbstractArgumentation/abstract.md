# Abstract

## Original Text (Verbatim)

Classical semantics for abstract argumentation frameworks are usually defined in terms of extensions or, more recently, labellings. That is, an argument is either regarded as accepted or not — there is no middle ground. In most real-world reasoning activities, however, we have to face various kinds of uncertainties and cannot claim that there are grounds to believe in a certain statement and that can be in conflict with some conflicting (probabilistic) certainties. There does not exist either a credibility of a skeptical approach, i.e. an argument is ultimately accepted if it is accepted in all or, respectively, in at least one extension. In this paper, we propose a more general approach for a semantics that allows for a more fine-grained differentiation between arguments. More precisely, we develop a probabilistic semantics for abstract argumentation that assigns probabilities to single arguments. We show that our semantics generalizes the classical notion of semantics and we point out interesting relationships between concepts from probabilistic and information-theoretic reasoning. We illustrate the usefulness of our semantics on an example from the medical domain.

---

## Our Interpretation

This paper addresses the limitation of binary (in/out) argument acceptance in Dung-style frameworks by assigning each argument a probability reflecting epistemic belief in its acceptability. The key contribution is a set of rationality postulates constraining these probabilities to cohere with classical complete labellings, plus a maximum entropy model for uniquely selecting among valid probability functions. Directly relevant to propstore's argumentation layer as a principled way to express graded acceptance without committing to a single extension.
