---
tags: [abstract-argumentation, sat-solving, argumentation-semantics, computational-argumentation]
---
Describes µ-toksia, a SAT-based abstract argumentation reasoner that won first place in all main-track reasoning tasks at ICCMA 2019, supporting credulous/skeptical acceptance and extension enumeration under all central semantics (complete, preferred, stable, semi-stable, stage, grounded, ideal) for both standard and dynamic argumentation frameworks.
Key contributions include concrete SAT encodings for each semantics, an iterative solving architecture with persistent solver state, unit propagation preprocessing for grounded semantics, and empirical evidence of superior scalability over competing systems.
Directly relevant as a practical implementation reference for the propstore's argumentation reasoning, providing tested SAT formulas and algorithmic patterns that complement the theoretical Dung (1995) framework and the encoding complexity analysis by Mahmood (2025) already in the collection.
