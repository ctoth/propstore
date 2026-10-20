---
tags: [distributed-systems, logical-clocks, partial-order, clock-synchronization]
---
Lamport defines the "happened before" partial order on events in a distributed system, gives logical-clock rules (IR1/IR2) satisfying the Clock Condition, extends the partial order to a total order by process tie-breaking, and uses it for fully distributed mutual exclusion and replicated state machines. He then specializes the rules to physical clocks and proves that clocks never set backwards stay synchronized within about d(2*kappa*tau + xi) on a strongly connected graph of diameter d. For propstore it is the reference account of keeping event order partial and treating any total order as a policy-chosen linearization, relevant to provenance, federation, and recency-based render policies.
