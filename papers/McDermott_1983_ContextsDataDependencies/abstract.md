# Abstract

## Original Text (Verbatim)

Two data-organization devices that have come out of AI research are data pools ("contexts") and data dependencies. The latter are more flexible than the former, and have supplanted them. Data pools offer certain advantages of efficiency, however, so it is worth trying to make the two mechanisms compatible. Doing this requires generalizing the mark-and-sweep algorithms that maintain consistency in a data-dependency network, so that the labels passed around do not simply say whether a datum is IN or OUT, but say which data pools it is present in. The revised algorithm is essentially an algorithm for solving simultaneous Boolean equations. Other mechanisms are needed for performing useful chores like maintaining well-founded support links and orchestrating demon calls.

---

## Our Interpretation

The paper addresses the fragmentation between two approaches to managing hypothetical reasoning in AI: context-based data pools (fast switching, coarse control) and data dependencies (fine-grained reason tracking, expensive recomputation). McDermott's key insight is that by generalizing labels from simple IN/OUT to Boolean expressions over "beads" (data pool identifiers), both mechanisms become instances of the same framework. The resulting Boolean equation solver provides an efficient, unified algorithm that preserves the strengths of both approaches and directly influenced subsequent work on assumption-based truth maintenance systems.
