---
tags: [truth-maintenance, data-dependencies, contexts, belief-revision, non-monotonic-reasoning]
---
Presents a synthesis of two AI data-organization mechanisms -- data pools (contexts) and data dependencies -- showing they can be unified into a single framework where labels are Boolean expressions over beads rather than simple IN/OUT values. The paper provides an efficient Boolean substitution algorithm for computing consistent, well-founded status assignments in the combined system, with benchmarks showing ~0.3 ms per node on 1983-era hardware. This work bridges Conniver-style context switching with Doyle's TMS-style reason maintenance and is a direct precursor to de Kleer's ATMS.
