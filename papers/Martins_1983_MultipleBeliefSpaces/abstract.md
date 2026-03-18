# Abstract

## Original Text (Verbatim)

MBR is a reasoning system which allows multiple beliefs (beliefs from multiple agents, contradictory beliefs, hypothetical beliefs) to be represented simultaneously in the same knowledge base and performs reasoning within sets of these beliefs. MBR also contains provisos to detect contradictions and to recover from them.

This paper describes MBR's method of detecting and recording contradictions within beliefs of different agents, showing an example of such process.

---

## Our Interpretation

MBR addresses the problem of maintaining a shared knowledge base where multiple agents hold potentially contradictory beliefs, without requiring separate databases or belief retraction. The key finding is that by defining "contexts" as sets of hypotheses and tracking both origin sets (which hypotheses were used to derive a proposition) and restriction sets (which hypothesis combinations are known to be inconsistent), contradictions can be detected and resolved through only two inference rules operating on network arcs. This is relevant as a precursor to the ATMS approach already in the collection, offering an alternative architecture for multi-perspective assumption tracking.
