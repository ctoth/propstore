---
title: "Maintaining Knowledge about Temporal Intervals"
authors: "James F. Allen"
year: 1983
venue: "University of Rochester, Department of Computer Science, TR 86 (revised), October 1983; to appear in Communications of the ACM, 1984"
doi_url: null
pages: "45 PDF pages (tech report); body pp.1-21 printed, figures pp.22-26, references p.27"
institution: "University of Rochester"
funding: "NSF grants IST-80-12418 and IST-82-10564; ONR grant N00014-80-C-0197"
note: "Source is the revised Rochester tech report, not the typeset CACM article (CACM 26(11):832-843, DOI 10.1145/182.358434). All page citations below are PDF pages of this tech report (p.1 = pngs/page-000.png), not CACM pages and not the report's printed page numbers. Printed page n of the body = PDF page n+2. PDF pp.30-45 are NOT part of this paper (see Source Defects)."
---

# Maintaining Knowledge about Temporal Intervals

## Citation convention for these notes

- `p.N` = PDF page N of `paper.pdf` (page image `pngs/page-{N-1:03d}.png`). *(p.1, p.3)*
- PDF p.1 is the library cover (TECH REPORT, TR 86 (revised), October 1983; Carlson Library stamp). PDF p.2 is the title/abstract page marked "To appear, Commun. of the ACM, 1984." Body text starts at PDF p.3 = printed page 1. *(p.1, p.2, p.3)*

## Source Defects (read first)

1. **Foreign pages appended.** PDF pp.30-45 are figures from a different, unrelated document about connectionist networks: "Figure 1: Contemporary view of (visual) memory phases" (p.30), "Figure 2: A simple example of encapsulation" (p.31), conjunctive connections (p.32), multiplication table via conjunctive connections (p.33), mutual inhibition / coalitions (p.34), Winner-Take-All and regulated networks (p.35), depth / retinal size / physical size networks (p.36), dynamic links (pp.37-41), "Figure 13: The 4N^{3/2} dynamic connection network" (p.42), "Figure 14: Making a connection" with P̄ = (1-F)^{B^K} (p.43), "Figure 15: Random chunking network" (p.44), "Figure 16: Expected number of links into a small random subset" (p.45). Their figure numbering restarts at 1 and their typography differs. They have no connection to Allen's text. The Allen paper proper ends at p.29 (References). These pages are not extracted further here. *(pp.30-45)*
2. **Pseudocode index typos in "To Add R(i,j)".** In the first inner loop the printed code computes `R(k,j) <- N(k,j) ∩ Constraints(N(k,i), R(i,j))` but then tests `If R(k,i) ⊂ N(k,i) then add <k,i> to ToDo`; in the second loop it computes `R(i,k)` but tests `If R(i,k) ⊂ N(k,i)`. The tests do not match the variables just computed; the evident intent is `R(k,j) ⊂ N(k,j)` → add `<k,j>`, and `R(i,k) ⊂ N(i,k)` → add `<i,k>`. This intent is my reading, not stated in the source. *(p.9)*
3. **Inconsistent L–R label in worked example.** The text says the computed L–R constraint is "(< > o m di s si fi =)", but the network drawn immediately after labels the L–R arc "(< > o oi m di s si fi =)" (extra `oi`). *(p.10)*
4. **Transitivity-table cell di∘d appears incomplete.** Row "contains" (di), column d shows only "o oi d di s =" (checked at 300 dpi). Composing "A contains B" with "B during C" admits o, oi, d, di, s, si, f, fi, = ; the cell as printed omits si, f, fi. I checked this cell and the cells quoted in the paper's worked examples; I did not verify all 144 cells. *(p.25)*
5. **Modification-bound formula.** The bound is printed as 13 × (N-1)(N-2)/2 "the number of binary relations between N nodes"; the number of unordered pairs of N nodes is N(N-1)/2. Recorded verbatim. *(p.11)*
6. **Summary wording.** The Summary says the approach "is partially useful in domains where temporal information is imprecise and relative"; recorded verbatim (possibly intended "particularly"). *(p.23)*

## One-Sentence Summary

Defines the 13 mutually exclusive relations between two temporal intervals, stores uncertain relative temporal knowledge as a network whose arcs carry disjunctive sets of these relations, maintains it by queue-driven constraint propagation over a 12×12 transitivity (composition) table, and controls cost with *reference intervals* that cluster nodes so that propagation happens only within clusters and cross-cluster relations are computed at retrieval by composing along paths up the reference hierarchy. *(pp.2, 8-9, 12-14, 24)*

## Problem Addressed

- Temporal knowledge in AI, databases, NLP, planning and medical records is often imprecise and relative ("A before B", "while John was away"); date lines and time instants cannot represent it. *(pp.2, 3, 4)*
- Requirements listed: allow significant imprecision; allow uncertainty (only constraints on how two times relate are known); allow varying the grain of reasoning (days/years for history, nanoseconds for circuits); support *persistence* (default reasoning: "If I parked my car in lot A this morning, it should still be there now"). *(p.4)*

## Key Contributions

- Interval-based temporal representation with intervals as primitive (no zero-width points). *(pp.3, 6-7)*
- Thirteen basic relations (7 named relations plus 6 inverses) with symbols `< > = m mi o oi d di s si f fi`. *(pp.8, 24)*
- Network representation: nodes = intervals, arcs labelled by disjunctive sets of basic relations; restricted disjunction only between a pair of intervals. *(pp.8, 18)*
- Constraint-propagation algorithm with the transitivity table (Fig. 4) that computes the closure when a relation is added. *(pp.8-9, 24)*
- Complexity analysis: bounded number of arc modifications, average O(N) per addition, O(N²) space; guarantees only 3-node (path) consistency, not global consistency. *(pp.11-12)*
- Reference intervals and the Comparable predicate to cut space and propagation; retrieval by path search up a reference hierarchy. *(pp.12-14)*
- Applications: personal history, process/plan decomposition, representing a moving NOW. *(pp.14-18)*
- Extensions: duration reasoner (implemented), date lines (designed, not implemented), persistent intervals for default persistence and assumption-based belief revision. *(pp.3, 19-22)*

## Methodology

Formal representation plus algorithms, illustrated with worked examples; no empirical evaluation. The system was implemented in FRANZ LISP and INTERLISP on a VAX 11/780 under UNIX, and includes the duration reasoner. *(p.18)*

## Section-by-section extraction

### I. Introduction *(p.3)*
- Temporal representation is a core problem for information systems, program verification, AI and process modeling; points to the April 1982 SIGART and SIGMOD Newsletter special sections. *(p.3)*
- Deleting outdated data loses history; queries like "Which employees worked for us last year and made over $15,000" need temporal information. *(p.3)*
- The paper takes the temporal interval as primitive and represents relations hierarchically with constraint propagation; reference intervals make the computation for adding a fact controllable "in a predictable manner"; designed for knowledge that "can't be described by a date (or even a 'fuzzy' date)". *(p.3)*
- Section V system is implemented; of the extensions, "the duration reasoner is fully implemented and incorporated into the system, whereas the date reasoner has been designed but not implemented." *(p.3)*

### II. Background *(pp.4-5)*
Four prior categories:
- **State space** (Fikes & Nilsson 1971; Sacerdoti 1977): a state is a database of facts at an instant; actions map states; add P / delete Q. Keeping all states too expensive, so usually only the present; provides persistence (a fact stays true until deleted). *(p.4)*
- **Date-based** (Kahn & Gorry 1977; Bruce 1972; Hendrix 1973; Bubenko 1980): every fact indexed by a date with cheap ordering. Fails when events cannot be dated. Even date ranges cannot capture "A and B did not happen at the same time": one must pick A before B, B before A, or allow overlap. Intervals need fuzzy ranges for both ends plus min/max duration. *(pp.4-5)*
- **Before/after chaining** (Kahn & Gorry 1977; Bruce 1972): captures relative information but suffers search (long chains) or space (precomputing all relations); alleviated by Kahn & Gorry's reference intervals; cannot express "A and B are disjoint" without disjunction. Allen's approach "can be viewed as an extension of this type of approach". *(p.5)*
- **Formal models**: Rescher & Urquhart 1971 (philosophy); situation calculus (McCarthy & Hayes 1969) - only one event at a time, events take no time, transitions not decomposable, and "the reverse notion of persistence": a fact must be reproven at each succeeding instant; McDermott 1982. These are point-based. Hayes' Naive Physics *histories* (1978; 1979) are compatible with intervals; this work can be seen as a reasoning mechanism for the temporal component of Naive Physics. *(p.5)*

### III. Time Points vs. Time Intervals *(pp.6-7)*
- English refers to times as points ("at twelve noon") or intervals ("yesterday"), but most temporal reference is implicit via tense and relations to other events ("while John was away", "after we made the decision"). *(p.6)*
- Events that seem instantaneous can be decomposed ("turn up the magnification"); so "the formal notion of a time point, which would not be decomposable, is not useful." An informal notion of points as very small intervals is useful. *(p.6)*
- **Light-switch argument**: light off interval followed by on interval. Open intervals leave a point where the light is neither on nor off; closed intervals give a point where it is both. Half-open convention (closed lower, open upper) works but each interval has only one endpoint; "The artificiality of this solution merely emphasizes that a model of time based on points on the real line does not correspond to our intuitive notion of time." Hence intervals as primitive. *(pp.6-7)*
- Endpoint encoding is possible (Bruce 1972): interval = ordered pair of points, t- < t+ (Fig. 1), but "the representation is too uniform" and does not support structuring knowledge. *(p.7)*
- The *during* relation supports inheritance: if t during T and P holds during T, then P holds during t; a during hierarchy localizes reasoning (for "today" consider only intervals during or above "today"; facts wholly inside "yesterday" cannot affect now). *(p.7)*

### IV. Maintaining Temporal Relations *(pp.7-12)*

#### IV.1 The basic algorithm *(pp.7-9)*
- Aim: characterize inferences made "automatically or effortlessly" in dialogue, story comprehension, simple problem solving; not arbitrarily complex puzzle reasoning. *(p.7)*
- Subdividing *during* gives a better computational model (credited to Marc Vilain; first used in Vilain 1982). With inverses, 13 relations between an ordered pair of intervals (Fig. 2). *(p.8)*
- `dur` = {d, s, f} (the three during relations); `con` = {di, si, fi} (containment). *(p.8)*
- "these thirteen relationships can be used to express any relationship that can hold between two intervals." *(p.8)*
- Network: nodes = intervals; arc labelled with all possible relations; "since the thirteen possible relationships are mutually exclusive, there is no ambiguity in this notation." N_i = node for interval i. *(p.8)*
- Assumes for now the network maintains complete information; on adding a relation, all consequences are computed via transitive closure through the transitivity rules (e.g., i during j, j before k ⇒ i before k). *(p.8)*

### Figure 1: Interval relations defined by endpoints *(p.24)*

| Interval relation | Endpoint condition |
|---|---|
| t < s | t+ < s- |
| t = s | (t- = s-) & (t+ = s+) |
| t overlaps s | (t- < s-) & (t+ > s-) & (t+ < s+) |
| t meets s | t+ = s- |
| t during s | ((t- > s-) & (t+ =< s+)) or ((t- >= s-) & (t+ < s+)) |

Note: in Fig. 1, "during" is the collapsed during (covers d, s, f). *(p.24)*

### Figure 2: The thirteen relations *(p.24)*

| Relation | Symbol | Inverse | Picture |
|---|---|---|---|
| X before Y | < | > | XXX YYY |
| X equal Y | = | = | XXX / YYY |
| X meets Y | m | mi | XXXYYY |
| X overlaps Y | o | oi | XXX / ·YYY |
| X during Y | d | di | ·XXX· / YYYYYY |
| X starts Y | s | si | XXX / YYYYY |
| X finishes Y | f | fi | ··XXX / YYYYY |

### Figure 3: Network notation examples *(p.24)*
1. i during j: N_i --(d)→ N_j
2. i during j or i before j or j during i: N_i --(< d di)→ N_j
3. (i < j) or (i > j) or i meets j or j meets i: N_i --(< > m mi)→ N_j - this is how *disjoint* is expressed. *(pp.8, 24)*

Notation policy: network form when an arc has more than one relation, relation form when only one. *(p.8)*

### Constraints function (composition of label sets) *(p.9)*

T(r1, r2) is the Fig. 4 transitivity entry; ε is the empty set.

```
Constraints(R1, R2)
  C <- ε;
  For each r1 in R1
    For each r2 in R2
      C <- C ∪ T(r1, r2);
  Return C;
```

$$
\mathrm{Constraints}(R_1, R_2) = \bigcup_{r_1 \in R_1} \bigcup_{r_2 \in R_2} T(r_1, r_2)
$$
Where: R_1, R_2 are arc labels (sets of basic relations); T is the transitivity table. *(p.9)*

### Add algorithm (verbatim, including source typos; see Source Defects 2) *(p.9)*

ToDo is a queue; N(i,j) = current relations on arc i–j; R(i,j) = new relation to add.

```
To Add R(i,j)
  Add <i,j> to queue ToDo;
  While ToDo is not empty do
  begin
    Get next <i,j> from queue ToDo;
    N(i,j) <- R(i,j);
    For each node k such that Comparable(k,j) do
    begin
      R(k,j) <- N(k,j) ∩ Constraints(N(k,i), R(i,j))
      If R(k,i) ⊂ N(k,i)
        then add <k,i> to ToDo;
    end
    For each node k such that Comparable(i,k) do
    begin
      R(i,k) <- N(i,k) ∩ Constraints(R(i,j), N(j,k))
      If R(i,k) ⊂ N(k,i)
        then add <i,k> to ToDo;
    end
  end;
```

Comparable(i,j) is defined in Section V; for now it is always true. ⊂ is proper subset, so a pair is re-queued only when its label strictly shrinks. *(p.9)*

$$
R(k,j) \leftarrow N(k,j) \cap \mathrm{Constraints}(N(k,i), R(i,j))
$$
$$
R(i,k) \leftarrow N(i,k) \cap \mathrm{Constraints}(R(i,j), N(j,k))
$$
*(p.9)*

Inverse labels: the inverse of an arc label is obtained by inverting each relation in it. *(p.10)*

### IV.2 Worked example *(pp.9-11)*
- Facts: S overlaps or meets L; S is before, meets, is met by, or after R. Story: "John was not in the room when I touched the switch to turn on the light." S = time of touching switch; L = time light was on; R = time John was in the room. Network: R ←(< m mi >)– S –(o m)→ L. *(pp.9-10)*
- L–R via S: Constraints({oi mi}, {< m mi >}) using T(oi,<)=(< o m di fi), T(oi,m)=(o di fi), T(oi,mi)=(>), T(oi,>)=(>), T(mi,<)=(< o m di fi), T(mi,m)=(s si =), T(mi,mi)=(>), T(mi,>)=(>); result (< > o m di s si fi =). *(p.10)*
- Add "L overlaps, starts, or is during R" ("But John was in the room later while the light went out."); intersect → L --(o s)→ R. *(p.10)*
- Propagate along S --(o m)→ L --(o s)→ R with T(o,o)=(< o m), T(o,s)=(o), T(m,o)=(<), T(m,s)=(m) → S --(< o m)→ R; intersect with previous S–R → S --(< m)→ R, i.e., John entered after I touched the switch or exactly when I finished touching it. *(p.11)*
- Adding D --(d)→ S would yield D --(<)→ R and D --(< o m d s)→ L. *(p.11)*

### IV.3 Analysis *(pp.11-12)*
- The algorithm runs only while it produces further constrained relations; each arc can be modified at most 13 times. *(p.11)*

$$
\text{max modifications} = 13 \times \frac{(N-1)(N-2)}{2}
$$
Where: N = number of nodes. Bound holds "irrespective of how many constraints are added". (Formula verbatim; see Source Defect 5.) *(p.11)*

- If about as many constraints are added as there are nodes, N additions take O(N²) time; one addition on average O(N). *(p.11)*
- Major problem: O(N²) space for N intervals. *(p.11)*
- **Incompleteness**: the algorithm "does not generate inconsistencies" but "does not detect all inconsistencies in its input. In fact, it only guarantees consistency between three node subnetworks." Fig. 5 (due to Henry Kautz) is 3-consistent but has no overall labeling: A–C is accepted as (f fi), but neither A --(f)→ C nor A --(fi)→ C is consistent. *(p.12)*
- Full consistency would require constraints over 3, 4, ... arcs (Freuder 1982), exponential complexity. "In practice, we have not encountered problems from this deficiency." Any subnetwork can be checked by backtracking search over alternative labelings until every arc has one label. *(p.12)*

### Figure 5: An inconsistent labeling *(p.26)*
Arcs: A --(d di)→ B; B --(d di)→ C; D --(s m)→ A; D --(o)→ B; D --(s m)→ C; A --(f fi)→ C (dashed). *(p.26)*

### V. Controlling Propagation: Reference Intervals *(pp.12-18)*
- A reference interval is "simply another interval in the system" but with a special property affecting computation: it groups a cluster of intervals among which constraints are fully computed; the cluster relates to the rest only via the reference interval. *(p.12)*

#### V.1 Using reference intervals *(pp.12-14)*
- Each interval names one or more reference intervals in parentheses: I1(R1), I2(R1,R2); I2 is fully connected to two clusters (Fig. 6). *(p.12)*
- Refs(N) = set of reference intervals of N. Comparable(K,J) is true iff *(p.13)*:
  1. Refs(K) ∩ Refs(J) ≠ ∅ (they share a reference interval); or
  2. K ∈ Refs(J); or
  3. J ∈ Refs(K).
- The add algorithm is otherwise identical. Reference intervals may have their own reference intervals → hierarchy of clusters, typically tree-like (Fig. 7). *(p.13)*
- Retrieval for unrelated intervals: search up the reference hierarchy for a path (or all paths) and compose along it; "If one is careful about structuring the reference hierarchy, this can be done with little loss of information from the original complete propagation scheme." *(p.13)*

Retrieval algorithm *(p.13)*:
```
If N(I,J) exists
then return N(I,J)
else do
  Paths := Find-Paths(I,J)
  For each path in Paths do
    R := R ∩ Constrain-along-path(path)
  return R;
end;
```
(R's initial value is not stated; it must start as the full set of 13 for the intersection to make sense - my reading.)

Find-Paths: graph search where each step is between a node and one of its reference intervals, except one direct connection. Path n_1, ..., n_k, n_{k+1}, ..., n_m with *(pp.13-14)*:
- for i = 1..k-1, n_{i+1} is a reference interval for n_i (climb up);
- n_k and n_{k+1} are connected explicitly;
- for i = k+1..m-1, n_i is a reference interval for n_{i+1} (climb down).

Constrain-along-path *(p.14)*:
```
R := N(n1,n2);
R := Constraints(R, N(n2,n3))
R := Constraints(R, N(n3,n4))
...
R := Constraints(R, N(n_{m-1}, n_m))
```

### Figure 6 *(p.26)*
Two cliques: {I1, I3, I4, I2} sharing R1 and {I2, I7, I5, I6} sharing R2; I2(R1,R2) connects both.

### Figure 7: Tree-like hierarchy *(p.27)*
R1 at top; R2(R1) - R5(R1); under R2: I6(R2), R3(R2) - R4(R2); under R3: I3(R3), I1(R3) - I2(R3); under R4: I4(R4) - I5(R4).

#### V.2 Examples *(pp.14-17)*
- "There are no restrictions imposed by the system on the use of reference intervals. Their organization is left up to the system designer." The more tree-like the hierarchy, the more efficient retrieval. *(p.14)*
- **History of a person** (Fig. 8): reference intervals between key events (Kahn & Gorry 1977 used reference events/points; here intervals between them). LIFE contains PRESCHOOL, PREGRAD, POSTGRAD (PRESCHOOL m PREGRAD m POSTGRAD; PRESCHOOL < POSTGRAD); PREGRAD decomposes into PRIM (s), SECOND (d), UNIV (f), with PRIM m SECOND m UNIV and PRIM < UNIV; CHESS(PRIM) d PRIM; WIN(UNIV) d UNIV; JOB(POSTGRAD) d POSTGRAD. An event spanning two reference intervals is stored under both (e.g., CHESS(PRIM, SECOND) if chess was learned in both). *(pp.14, 27)*
- Retrieval CHESS–WIN: single path CHESS(PRIM) --(d)→ PRIM(PREGRAD) --(<)→ UNIV(PREGRAD) --(di)→ WIN(UNIV) ⇒ CHESS before UNIV, then CHESS before WIN. CHESS before JOB via CHESS --(d)→ PRIM --(s)→ PREGRAD --(m)→ POSTGRAD --(di)→ JOB. *(p.15)*
- **Processes** (Fig. 9): P = sequence P1, P2, P3 (P1 s P, P2 d P, P3 f P; P1 m P2 m P3); Q = Q1, Q2 in either order but not simultaneously (Q1 --(< > m mi)→ Q2, both d Q); Q2 = Q21, Q22 simultaneous (e = equal, both e Q2). P begins before Q: Q(x) --(< m o)→ P(x) per figure. Works as long as decomposition is independent (NOAH, Sacerdoti 1977). *(pp.15, 28)*
- Adding Q1 before Q21: infer Q1–Q2 via Q1(Q) --(<)→ Q21(Q2) --(e)→ Q2(Q) because Q1 and Q2 share Q. *(p.16)*
- Limitation: adding Q2 overlaps P1 will NOT constrain Q–P to overlaps, though full propagation would, because no two-arc path from Q to P is affected. *(p.16)*
- Fix: when relating two noncomparable nodes, expand one node's reference list with the other's (add P to Q2's references). Then infer Q2(Q,P) --(o)→ P(X) from Q2(Q,P) --(o)→ P1(P) --(s)→ P(X), and Q(X) --(o)→ P(X) from Q(X) --(di)→ Q2(Q,P) --(o)→ P(X) plus prior constraints. Final state Fig. 10. *(p.16)*
- "Manipulating the reference hierarchies as in this example can be effective if used sparingly. With overuse, such tricks tend to 'flatten out' the reference hierarchy as more intervals become explicitly related." *(p.16)*

### Figure 10 *(p.28)*
Q(x) --(o)→ P(x); Q1(Q) --(<)→ Q2(Q,P); Q1 --(<)→ Q21(Q2); Q2(Q,P) --(o)→ P1(P), --(o)→ P(x), --(<)→ P2(P), --(<)→ P3(P); P1 --(m)→ P2 --(m)→ P3; P1 --(<)→ P3; Q21 --(e)→ Q22; both e Q2. The node is printed "Q22(A2)", presumably Q22(Q2). *(p.28)*

#### V.3 Representing the present moment *(pp.16-18)*
- NOW is a variable bound to an interval; update by rebinding to a new interval *after* the previous one. *(p.17)*
- Example: N1(R1) during R1; R1 before I1, R1 after I2, R1 during I3 ⇒ N1 during I3, before I1, after I2. Update: N2(R1) during R1, N2(R1) after N1(R1); effects propagate only to intervals referenced by R1 - R1 "protected" the rest of the database. *(p.17)*
- When NOW leaves R1, a new reference interval is needed; cost reduced if R1 itself has a protecting reference interval → hierarchy of reference intervals each containing the present, mirroring English ("Go now!", "this morning", "today", "this year", "during this lecture", "while at this bar"). These have well-defined start/end, so the database is notified when one ceases to contain the present. *(p.17)*
- Key assumption (verbatim): "When updating the NOW interval, unless otherwise stated, its relationship to its reference interval(s) remains constant." *(p.17)*
- When a reference interval ceases to contain the present, a new one is selected (usually provided by the user), updated the same way, relationship to the higher-level reference interval kept constant; a new NOW below it is introduced; e.g., a new day makes much of the old hierarchy "yesterday". *(pp.17-18)*
- Garbage collection: intervals not indexing any events/facts may be removed; in dialogue many intervals only index utterance times and can be deleted. *(p.18)*

### VI. Discussion *(pp.18-19)*
- Expressive and feasible: no fixed event order required; allows disjunctive knowledge (A before or after B) not expressible in date-based or simple before/after chaining. Less expressive than full temporal logic (McDermott 1982), which lacks viable implementations. *(p.18)*
- "This balance between expressive power and computational efficiency is achieved by the restricted form of disjunctions allowed in the system. One can only assert disjunctive information about the relationship of two intervals ... A is before or meets B, but not that (A meets B) or (C before D)." *(p.18)*
- Uses: ARGOT dialogue research (Allen, Frisch, Litman 1982); planning world model (Allen & Koomen 1983). *(p.18)*
- Vilain 1982: version with consistency maintenance (identifies the facts causing an inconsistency) at higher space cost; allows time points with a larger transitivity table (interval/point and point/point). "This violates the semantics of the interval representation, and so has not been adopted in our present system." *(p.18)*
- Endpoints may be intervals small enough to appear instantaneous; a minimum duration ε could treat intervals shorter than ε as points (then two such are either equal or one before the other), but ε cannot be fixed in advance - it depends on the task (historian: days; engineer: a day is an eternity). *(pp.18-19)*

### VII. Future Research and Extensions *(pp.19-22)*

#### VII.1 Duration reasoning *(pp.19-20)*
- Same principles: relative durations and uncertainty via constraint propagation; reference durations. *(p.19)*
- A duration relation is a range on the multiplicative factor between durations. dur(A) < dur(B) is A --(0 (1))→ B, i.e., dur(A) >= 0·dur(B) and dur(A) < 1·dur(B); parentheses mark an open endpoint; both limits may be open or closed. *(p.19)*

$$
l \cdot \mathrm{dur}(B) \le \mathrm{dur}(A) < u \cdot \mathrm{dur}(B)
$$
Where: label A --(l (u))→ B; brackets/parentheses select closed/open bounds. *(p.19)*

- Duration network is orthogonal to the relation network; propagation multiplies upper and lower limits. Example: dur(A) <= dur(B), dur(C) <= dur(B), dur(B) < 2·dur(C), network A --(0 1)→ B --(1 (2))→ C, derived A --(0 (2))→ C. *(pp.19-20)*

$$
[l_1, u_1] \circ [l_2, u_2] = [l_1 l_2,\; u_1 u_2]
$$
*(p.20)*

- Cross-network rule: If I --(d s f)→ J then dur(I) < dur(J); the networks may exchange information back and forth multiple times before propagation ends. *(p.20)*
- Reference durations = scales/common units; constraints do not propagate through them (HOUR example: dur(A) between 1 and 2 hours, dur(B) < half hour; no relation inferred at assertion time; derived at retrieval via HOUR). Details in Allen & Kautz 1983. *(p.20)*

#### VII.2 Date lines *(pp.20-21)*
- A date line = fully ordered set of values for times, e.g., (year month(1-12) day(1-31)), (50 3 25) = March 25, 1950, ordered lexicographically: (50 3 25) < (75 1 1). Comparison on a date line is cheap relative to network search. *(p.20)*
- Any interval may carry date-line info (dating system + start/end dates). Two intervals dated on the same line: compute their exact relation; if more specific than the network's, update and propagate. On retrieval, consult dates first; network search still needed when dates are insufficient. *(pp.20-21)*
- One dated, one not: use dates only if a relation exists between the undated one and another interval dated on the same line - generally too expensive; useful special case: a reference interval in the search is dated. *(p.21)*
- Time-of-day line for dialogue: basic duration one minute, hour-minute values; with clock access usable throughout the NOW hierarchy. Without a clock, create e.g. an "after 10 o'clock" reference interval when the time is learned; "Whether such a technique is feasible requires further research." *(p.21)*

#### VII.3 Persistence of intervals *(pp.21-22)*
- A *persistent interval* Tp is assumed to extend as far as constraints allow. Testing P (indexed by Tp) during t succeeds by assumption if it is *possible* that t is during Tp. *(p.22)*
- Car example: Tp met by Tarrive, Tnow after Tarrive ⇒ Tp --(< o di m)→ Tnow; di possible, so the test succeeds. If the car is found missing during Tmiss, Tp before Tmiss; if Tnow after or during Tmiss, it is no longer possible that Tnow is during Tp. *(p.22)*
- Managing this needs truth maintenance (Doyle 1979), independent of the temporal representation. *(p.22)*
- Belief-revision trick: if P holds during persistent Tp and P implies Q, index Q by Tp rather than t; if new constraints rule out t during Tp, both P and Q cease to hold (by assumption) during t. "by indexing all the consequences of P by the same interval, Tp, we can revise our beliefs about P and all its consequences simply by adding constraints about Tp ... it may allow a large class of assumption-based belief revision to be performed easily." *(p.22)*

### Summary and Acknowledgements *(p.23)*
- Reference-interval hierarchy "precisely control[s] the amount of deduction performed automatically by the system." Thanks Marc Vilain, Henry Kautz; criticism from Alan Frisch, Pat Hayes, Hans Koomen, Drew McDermott, Candy Sidner. *(p.23)*

## Figure 4: Transitivity table (p.25), full transcription

Rows: A r1 B. Columns: B r2 C. Entry: possible A–C relations. "no info" = any of the 13. The table omits "=" (= composes as identity). Cell di∘d transcribed as printed; see Source Defect 4.

| r1 \ r2 | < | > | d | di | o | oi | m | mi | s | si | f | fi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| < | < | no info | < o m d s | < | < | < o m d s | < | < o m d s | < | < | < o m d s | < |
| > | no info | > | > oi mi d f | > | > oi mi d f | > | > oi mi d f | > | > oi mi d f | > | > | > |
| d | < | > | d | no info | < o m d s | > oi mi d f | < | > | d | > oi mi d f | d | < o m d s |
| di | < o m di fi | > oi di mi si | o oi d di s = | di | o di fi | oi di si | o di fi | oi di si | di fi o | di | di si oi | di |
| o | < | > oi di mi si | o d s | < o m di fi | < o m | s o oi si d di f fi = | < | oi di si | o | di fi o | d s o | < o m |
| oi | < o m di fi | > | oi d f | > oi mi di si | o oi s si d di f fi = | > oi mi | o di fi | > | oi d f | oi > mi | oi | oi di si |
| m | < | > oi mi di si | o d s | < | < | o d s | < | f fi = | m | m | d s o | < |
| mi | < o m di fi | > | oi d f | > | oi d f | > | s si = | > | d f oi | > | mi | mi |
| s | < | > | d | < o m di fi | < o m | oi d f | < | mi | s | s si = | d | < m o |
| si | < o m di fi | > | oi d f | di | o di fi | oi | o di fi | mi | s si = | si | oi | di |
| f | < | > | d | > oi mi di si | < o d | > oi mi | m | > | d | > oi mi | f | f fi = |
| fi | < | > oi mi di si | < o d | di | o | oi di si | m | si oi d | o | di | f fi = | fi |

*(p.25)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|---|---|---|---|---|---|---|
| Number of basic interval relations | - | count | 13 | - | p.8 | 6 inverse pairs + equal |
| Transitivity table size | T | cells | 12×12 = 144 | - | p.25 | "=" omitted |
| Max modifications per arc | - | count | 13 | - | p.11 | label can only shrink |
| Total modification bound | - | count | 13×(N-1)(N-2)/2 | - | p.11 | verbatim formula |
| Average time per addition | - | - | O(N) | - | p.11 | when #constraints ≈ #nodes |
| Space for N intervals (no ref. intervals) | - | - | O(N²) | - | p.11 | full network |
| Consistency guaranteed | - | nodes | 3 | - | p.12 | path consistency only |
| Date-line month | - | - | - | 1-12 | p.20 | example calendar |
| Date-line day | - | - | - | 1-31 | p.20 | example calendar |
| Time-of-day line basic duration | - | minute | 1 | - | p.21 | hour-minute values |

## Testable Properties

- The 13 basic relations are mutually exclusive and jointly exhaustive for an ordered pair of intervals. *(p.8)*
- Each relation r has inverse r⁻¹ (< ↔ >, m ↔ mi, o ↔ oi, d ↔ di, s ↔ si, f ↔ fi, = ↔ =); the inverse of an arc label is the set of inverses. *(pp.10, 24)*
- Propagation only ever intersects labels (labels are monotonically non-increasing); a pair is re-queued only on strict shrinkage; hence termination with at most 13 changes per arc. *(pp.9, 11)*
- Constraints(R1,R2) is the union over member pairs of T(r1,r2). *(p.9)*
- After propagation, every 3-node subnetwork is consistent, but global consistency is not guaranteed (Fig. 5 counterexample: A–C label (f fi) has no consistent singleton refinement). *(p.12)*
- Worked example: from S (o m) L, S (< m mi >) R, L (o s d) R, the system derives L (o s) R and S (< m) R. *(pp.10-11)*
- With D (d) S added: D (<) R and D (< o m d s) L. *(p.11)*
- Comparable(K,J) ⇔ Refs(K) ∩ Refs(J) ≠ ∅ ∨ K ∈ Refs(J) ∨ J ∈ Refs(K). *(p.13)*
- Fig. 8 hierarchy: CHESS before WIN and CHESS before JOB are retrievable by path composition. *(p.15)*
- Q2 overlaps P1 does not by itself constrain Q–P to overlaps under reference intervals (loss of inference vs full propagation). *(p.16)*
- Duration composition: A (0 1) B, B (1 (2)) C ⇒ A (0 (2)) C. *(p.20)*
- Cross-network: I (d s f) J ⇒ dur(I) < dur(J). *(p.20)*
- Persistence: Tp mi Tarrive, Tarrive < Tnow ⇒ Tp (< o di m) Tnow. *(p.22)*

## Limitations

- Only 3-node consistency; inconsistent inputs may go undetected; complete checking exponential (Freuder 1982); backtracking available for subnetworks. *(p.12)*
- O(N²) space without reference intervals. *(p.11)*
- Reference intervals lose inferences across clusters unless the hierarchy is reorganized; reorganization overused flattens the hierarchy. *(p.16)*
- Disjunction only between two intervals; cannot express (A meets B) or (C before D). *(p.18)*
- Less expressive than full temporal logic (McDermott 1982). *(p.18)*
- No time points; minimum-duration ε not fixable in advance. *(pp.18-19)*
- Date reasoner designed, not implemented; time-of-day NOW scheme feasibility unknown. *(pp.3, 21)*
- Persistence requires separate truth maintenance. *(p.22)*

## Arguments Against Prior Work

- State-space: too expensive to keep all states; addresses few of the listed issues. *(p.4)*
- Date-based: cannot date many events; fuzzy dates cannot express non-simultaneity. *(pp.4-5)*
- Before/after chaining: search or space blowup; no disjointness without disjunction. *(p.5)*
- Situation calculus: one event at a time, no event duration, no decomposition, reversed persistence. *(p.5)*
- Point-based models: open/closed endpoint paradox in the light-switch example. *(pp.6-7)*
- Endpoint encoding: too uniform; does not exploit during-hierarchies. *(p.7)*
- Vilain 1982 points violate interval semantics. *(p.18)*

## Design Rationale

- Intervals primitive because events are decomposable and point semantics cause meeting paradoxes. *(pp.6-7)*
- Splitting during into d/s/f gives a better computational model (Vilain). *(p.8)*
- Restricted pairwise disjunction is "ideal for the constraint propagation algorithm" and gives the expressiveness/efficiency balance. *(p.18)*
- Reference intervals trade some inferential completeness for space/time; retrieval-time composition replaces build-time closure across clusters. *(pp.12-13)*
- Hierarchies of reference intervals mirror domain structure (life phases, process decompositions, English present-time expressions). *(pp.14-17)*

## Relevance to Project

- propstore's description-claim Allen relations (CLAUDE.md: "Allen relations over description-claim intervals reuse KindType.TIMEPOINT + Z3") cite this paper; note Allen rejects points as primitive, whereas propstore encodes interval endpoints as TIMEPOINT reals - closer to the Fig. 1 endpoint encoding Allen considers and sets aside (p.7). This is an observation about the paper, not a claim about propstore's code.
- Disjunctive arc labels are a non-commitment representation: the network stores all still-possible relations instead of picking one. *(p.8)*
- Reference intervals defer cross-cluster inference to retrieval time (render-time composition) rather than closure at assertion. *(p.13)*
- Persistent intervals plus indexing consequences by the same interval is an assumption-based belief-revision device related to TMS/ATMS (Doyle 1979 cited). *(p.22)*

## Open Questions

- [ ] Does the CACM version correct the pseudocode index typos (p.9), the extra `oi` (p.10), the di∘d cell (p.25), and the modification bound (p.11)? Not checkable from this copy.
- [ ] Initial value of R in the retrieval algorithm is unstated. *(p.13)*

## Related Work Worth Reading

- Vilain 1982, "A system for reasoning about time" (AAAI) - 13-relation subdivision, consistency maintenance, points. *(pp.8, 18)*
- Kahn & Gorry 1977, "Mechanizing temporal knowledge" - reference events. *(pp.5, 14)*
- Freuder 1982, "A sufficient condition for backtrack-free search" (JACM). *(p.12)*
- McDermott 1982, "A temporal logic for reasoning about processes and plans". *(pp.5, 18)*
- Doyle 1979, "A truth maintenance system". *(p.22)*
- Allen & Kautz 1983, "A model of naive temporal reasoning" - duration reasoner details. *(p.20)*

## Collection Cross-References

### Already in Collection
- [A Truth Maintenance System](../Doyle_1979_TruthMaintenanceSystem/notes.md) - cited for the truth maintenance needed to manage persistent-interval assumptions ("if fact P is true now, it will remain true until noticed otherwise"); Allen says these issues are independent of the temporal representation *(p.22)*

### New Leads (Not Yet in Collection)
- Vilain (1982) - "A system for reasoning about time" - source of the d/s/f subdivision that yields 13 relations; adds consistency maintenance and time points, which Allen rejects
- Kahn and Gorry (1977) - "Mechanizing temporal knowledge" - reference events in before/after chaining, the ancestor of reference intervals
- Freuder (1982) - "A sufficient condition for backtrack-free search" - the higher-order consistency Allen's 3-node propagation lacks
- McDermott (1982) - "A temporal logic for reasoning about processes and plans" - the point-based, more expressive temporal logic Allen contrasts with
- Allen and Kautz (1983) - "A model of naive temporal reasoning" - full description of the duration reasoner
- McCarthy and Hayes (1969) - "Some philosophical problems from the standpoint of artificial intelligence" - situation calculus, criticised for one-event-at-a-time and reversed persistence
- Hayes (1978; 1979) - Naive Physics histories, which Allen's reasoner can serve as the temporal component of
- Bruce (1972) - "A model for temporal references and its application in a question answering program" - endpoint-based interval encoding

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [Building Problem Solvers](../Forbus_1993_BuildingProblemSolvers/notes.md) - Ch.18 implements Allen's 13 relations and transitivity table as a WALTZER constraint network (temporal database with `allen.lisp`), composing R(A,B) and R(B,C) by union over the cross product, which matches this paper's Constraints function *(p.9)*
- [Formalizing Ontology Alignment and its Operations with Category Theory](../Zimmermann_2006_FormalizingOntologyAlignmentCategoryTheory/notes.md) - cites this as [2], a canonical qualitative calculus whose relation-composition table maps a pair of relations to a set of possible relations, the shape of the `Ont+` composition table phi

### Conceptual Links (not citation-based)
**Relative ordering without dates:**
- [Time, Clocks, and the Ordering of Events in a Distributed System](../Lamport_1978_TimeClocksOrderingEvents/notes.md) - Moderate. Both refuse to force a total order the evidence does not support: Lamport keeps a happened-before partial order over point events and chooses a linearization by tie-breaking, while Allen keeps disjunctive sets of interval relations and rejects points as primitive. Lamport's notes already contrast happened-before with Allen-style interval relations.
- [Microtheories](../Kallem_2006_Microtheories/notes.md) - Moderate. Kallem's temporal qualification of facts by event sequence rather than absolute dates, where only rough estimates exist, is the use case Allen's relative interval network was built for; Allen's during-inheritance (P holds during T and t during T implies P during t) is the interval analogue of microtheory visibility.

**Assumption management:**
- [Contexts and Data Dependencies: A Synthesis](../McDermott_1983_ContextsDataDependencies/notes.md) - Moderate. McDermott's chronsets chunk a database into temporal intervals and switch temporal viewpoints with data pools; Allen instead localizes temporal inference with reference-interval clusters, and his persistent-interval trick (index all consequences of P by Tp so that constraining Tp retracts them together) is an assumption-based belief-revision device of the same family.
