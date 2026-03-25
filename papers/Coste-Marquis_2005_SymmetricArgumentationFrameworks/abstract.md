# Abstract

## Original Text (Verbatim)

This paper is centered on the family of Dung's finite argumentation frameworks when the attacks relation is symmetric (and nonempty and irreflexive). We show that while this family does not contain any well-founded framework, every element of it is both coherent and relatively grounded. Then we focus on the acceptability problems for the various semantics introduced by Dung, yet generalized to sets of arguments. We show that only two distinct forms of acceptability are quite simple, but tractable; this contrasts with the general case for which all the forms of acceptability are intractable (except for the ones based on grounded or naive extensions).

---

## Our Interpretation

The paper investigates what happens to Dung's argumentation semantics when attacks are always mutual (symmetric). It finds that the standard semantics hierarchy collapses: preferred, stable, and naive extensions all coincide, and the grounded extension is simply the set of unattacked arguments. The complexity analysis shows that while single-argument acceptability trivializes, set-of-arguments acceptability remains hard (NP/coNP-complete) for preferred semantics but tractable for grounded and naive. This is relevant to propstore because symmetric attacks naturally arise when two claims rebut each other, and the collapse results simplify the choice of semantics in such cases.
