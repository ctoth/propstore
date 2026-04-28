# Abstract

## Original Text (Verbatim)

In the field of non-monotonic logics, the notion of *rational closure* is acknowledged as a landmark, and we are going to see that such a construction can be characterised by means of a simple method in the context of propositional logic. We then propose an application of our approach to rational closure in the field of Description Logics, an important knowledge representation formalism, and provide a simple decision procedure for this case.

---

## Our Interpretation

Casini & Straccia recast Lehmann–Magidor rational closure as a default-assumption (Poole/Freund-style) construction that only requires classical entailment ⊨ tests, then port it line-for-line to ALC and to ABox reasoning under unfoldable TBoxes. The decision procedure reduces to: build ⟨T̃, Δ̃⟩ once via an exceptionality-ranking pass, then for each query find the first consistent default formula δ_i and check one classical subsumption — yielding coNP-completeness for propositional, EXPTIME-completeness for ALC, and PSPACE-completeness for ABox queries, with no asymptotic overhead over the underlying entailment problem. Relevant to propstore as a directly implementable rational-closure recipe atop a black-box DL reasoner, compatible with the lazy-until-render storage discipline.
