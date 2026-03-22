---
tags: [argumentation-semantics, sat-encoding, computational-complexity, clique-width]
---
Provides complete SAT and QSAT encodings for all standard Dung argumentation semantics (stable, admissible, complete, preferred, semi-stable, stage) using directed decomposition-guided reductions that linearly preserve clique-width.
Establishes tight complexity bounds under ETH: 2^O(k)·poly(s) for stable/admissible/complete and 2^O(k²)·poly(s) for preferred/semi-stable/stage, with matching lower bounds proving these are optimal.
Directly relevant to propstore's argumentation framework: the SAT encodings can be implemented in z3 to compute extensions, and the credulous/skeptical reasoning reductions enable determining which claims are accepted under various semantics.
