# Abstract

## Original Text (Verbatim)

Abstract argumentation frameworks (AFs) are a well-known formalism for modelling and deciding over conflicting information. While several algorithms and evaluation algorithms have been deeply investigated for static AFs, whose structure does not change over the time. However, AFs are often dynamic as a consequence of the fact that can be added or deleted, and new attacks and stances can be introduced. In this paper, we tackle the problem of incrementally computing extensions for dynamic AFs, given an initial extension and an update (or a set of updates), i.e. derive a technique for computing an extension of the updated AF under four well-known semantics (i.e., complete, preferred, stable, and grounded). Our approach is based on identifying a sub-AF called reduced AF sufficient to compute an extension of the whole AF and make the use of the algorithms to compute an extension of the reduced AF only. The experiments reveal that, for all the semantics considered and using different solvers, the incremental technique is on average two orders of magnitude faster than computing the semantics from scratch.

---

## Our Interpretation

The paper addresses the inefficiency of recomputing argumentation framework extensions from scratch whenever arguments or attacks change. It introduces an incremental approach that identifies a "reduced AF" containing only the influenced portion, achieving 100x speedup on average. This is directly relevant to propstore's dynamic argumentation scenarios where claims and stances are continuously added or modified.
