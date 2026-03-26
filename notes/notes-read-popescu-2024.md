# Reading Popescu & Wallner 2024 — Probabilistic Argumentation Constellation

## GOAL
Read paper, extract implementation-focused notes for probabilistic argumentation in propstore.

## STATUS
- PDF: 11 pages, converted to PNGs
- Pages read: 0-2, 4-10 (page 3 is black/corrupt, need PDF fallback)
- Writing notes next

## KEY FINDINGS SO FAR

### Paper overview
- Authors: Andrei Popescu, Johannes P. Wallner (TU Graz)
- Title: "Advancing Algorithmic Approaches to Probabilistic Argumentation under the Constellation Approach"
- Constellation approach: each subset of arguments is a possible AF (probabilistic AF = PrAF)

### Complexity results (p.1, p.4)
- Computing probability of a set being an extension: #P-complete
- Computing probability of acceptability (argument in some extension): #P^NP-complete (under complete semantics)
- For admissible/stable: #P-complete for both extension probability and acceptability
- The #P^NP-completeness is for complete extensions specifically

### Core definitions (p.2-3)
- PrAF F = (A, R, P) where (A,R) is an AF and P: A ∪ R → (0,1]
- Probability distribution: independent — each arg/attack present with its probability
- P_ext^σ(F)(S) = probability of S being a σ-extension
- P_acc^σ(F)(a) = probability of a being accepted under σ
- Subframeworks: removing an argument removes all its attacks

### Tree decomposition DP algorithm (p.4-6)
- Algorithm operates on nice tree-decompositions
- Node types: leaf, introduce (arg or attack), forget, join
- Each bag maintains a table of rows: (subframework description, labeling, witnesses, probability)
- Row format: (E_i, att_i, c_i, p_i, w_i) for each node i
  - E_i = set of subframeworks (partial completions)
  - att_i = attacks within current context
  - c_i = complete labeling candidate
  - p_i = probability
  - w_i = witness (partial labeling for completeness check)
- Nice tree-decomposition has: leaf nodes, introduce nodes (arg or attack), forget nodes, join nodes

### Algorithm details (p.5-7)
- Algorithm 1: main algorithm — computes nice TD, iterates post-order
- Algorithm 2: introduce argument — adds arg to subframeworks
- Algorithm 3: forget argument — projects out forgotten args
- For introduce argument node: new arg gets label in/out/undec
- Completeness check via witnesses
- Join node: merge two child tables, multiply probabilities for independent parts
- Connected component optimization: only track labeling within current bag

### Preprocessing: Connected Components (p.4)
- Before tree-decomposition, decompose into connected components
- Process each component independently
- Combine results by multiplying probabilities

### Key implementation detail: "fixed-parameter tractable" (p.4)
- Under parameter tree-width, the algorithm is FPT
- Theorem 6: there is a fixed-parameter algorithm w.r.t. treewidth for computing probability of extensions being complete extensions

### Experimental evaluation (p.7-8)
- Implemented in Python (ASP/clingo for comparison)
- Two systems: (1) naive brute-force, (2) tree-decomposition DP
- Tested on grid-based PAFs with variable probabilities
- Grid sizes up to 150 args
- Treewidth bounded by grid width
- For treewidth ~6, DP feasible; as treewidth grows, exponential blowup
- Clique sizes bounded by tw+1
- DP outperforms brute force significantly for low treewidth
- For high treewidth (>15-20), neither approach feasible for exact computation

### Monte Carlo fallback (p.8)
- Paper mentions Li 2012 Monte Carlo approach as alternative
- Their exact DP is better when treewidth is low
- For high treewidth, sampling-based approaches needed

### Extensions discussion (p.8)
- Can extend to introduce dependencies between arguments
- Can handle "whenever a subframework contains an argument, it must also contain argument b"
- Forget nodes handle projection

## BLOCKED
- Page 3 (page-003.png) is black — need to read from PDF

## NEXT
- Read page 3 from PDF
- Write notes.md, description.md, abstract.md, citations.md
- Update index.md
- Write report
