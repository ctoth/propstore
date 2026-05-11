# Abstract

## Original Text (Verbatim)

The importance of transformations and normal forms in logic programming, and generally in computer science, is well documented. This paper investigates transformations and normal forms in the context of Defeasible Logic, a simple but efficient formalism for nonmonotonic reasoning based on rules and priorities. The transformations described in this paper have two main benefits: on one hand they can be used as a theoretical tool that leads to a deeper understanding of the formalism, and on the other hand they have been used in the development of an efficient implementation of defeasible logic.

---

## Our Interpretation

Antoniou, Billington, Governatori, and Maher prove that three of Defeasible Logic's five primitives — facts, defeaters, and the superiority relation — are syntactic conveniences that can be simulated by strict and defeasible rules alone, while preserving the full four-tagged conclusion set on the original language. They give explicit transformations (`normal`, `elim_sup`, `elim_dft`), prove modularity and incrementality where they hold, and prove non-existence theorems where they fail; the simplified post-transformation proof theory underpins the linear-time Delores consequence engine. For propstore, this paper supplies the formal license to normalize defeasible theories before reasoning, and bounds the asymptotic cost.
