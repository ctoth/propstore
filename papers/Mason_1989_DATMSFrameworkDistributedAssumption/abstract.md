# Abstract

## Original Text (Verbatim)

The Distributed ATMS, DATMS, is a problem solving framework for multiagent assumption based reasoning. It is based on the problem solving paradigm of result sharing rule-based expert systems using assumption based truth maintenance systems. We are implementing and experimenting with the DATMS under MATE, a Multi-Agent Test Environment, using C and Common Lisp on a network of Sun workstations. This framework was motivated by the problem of seismic interpretation for Comprehensive or Low-Yield Test Ban Treaty verification, where a widespread network of seismic sensor stations are required to monitor treaty compliance, and seismologists use assumption based reasoning in a collaborative fashion to interpret the seismic data. The DATMS framework differs from other previously designed problem solving organizations in (1) its method of reasoning, (2) its ability to support an explanation facility, and (3) its addressing of the problem of culpability.

---

## Our Interpretation

The paper addresses how to scale assumption-based truth maintenance to multiple cooperating agents, where each agent has its own ATMS and shares results via messages. The key finding is that forcing global consistency is both impractical and undesirable; instead, agents should maintain local consistency while tolerating network-level disagreement, using contradiction knowledge (nogoods) to prune the context space. This is directly relevant to propstore's concern about nogood set explosion when adding branch assumptions to the ATMS, as the paper confirms context explosion is a real threat in multi-context settings and validates the non-commitment philosophy.
