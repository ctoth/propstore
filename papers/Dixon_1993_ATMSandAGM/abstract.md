# Abstract

## Original Text (Verbatim)

The Assumption-based Truth Maintenance System (ATMS) [de Kleer, 1986] is the most well known implementation of any dynamic reasoning system. Some connections have been established between the ATMS and various nonmonotonic logics (e.g. autoepistemic logic [Reinfrank *et al.*, 1989]). We describe the relationship between the ATMS and the AGM logic of belief [Gardenfors, 1988], and show that it is possible to simulate the behaviour of the ATMS using the AGM logic by encoding the justificational information as an epistemic entrenchment ordering. The ATMS context switching is performed by AGM expansion and contraction operations. We present an algorithm for calculating this entrenchment ordering, and prove its correctness relative to a functional specification of the ATMS. This result demonstrates that the AGM logic, which is based on the coherence theory of justification, is able to achieve both coherence and foundational style behaviour via the choice of epistemic entrenchment orderings.

---

## Our Interpretation

The paper addresses the gap between two major frameworks for managing beliefs under change: the ATMS (a foundational, implementation-oriented system) and AGM belief revision (a coherence-based logical theory). By constructing an algorithm that translates ATMS justifications into AGM epistemic entrenchment orderings, the authors prove formal behavioural equivalence between the two systems. This is relevant to the propstore because it shows the ATMS architecture already in use can be understood through AGM theory, enabling principled belief revision strategies and assumption prioritization.
