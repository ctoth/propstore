# Abstract

## Original Text (Verbatim)

The concept of one event happening before another in a distributed system is examined, and is shown to define a partial ordering of the events. A distributed algorithm is given for synchronizing a system of logical clocks which can be used to totally order the events. The use of the total ordering is illustrated with a method for solving synchronization problems. The algorithm is then specialized for synchronizing physical clocks, and a bound is derived on how far out of synchrony the clocks can become.

Key Words and Phrases: distributed systems, computer networks, clock synchronization, multiprocess systems

CR Categories: 4.32, 5.29

---

## Our Interpretation

Event order in a distributed system is only partial, determined by process order and messages actually sent; logical clocks give a consistent but non-unique total order on top of it. The paper shows how to use that order for decentralized synchronization and bounds physical clock skew. For propstore it grounds keeping orderings partial in storage and choosing a linearization only by explicit policy.
