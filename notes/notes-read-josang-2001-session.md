# Session: Reading Josang 2001 - A Logic for Uncertain Probabilities

## GOAL
Read all 31 pages of Josang 2001 and create implementation-focused notes for propstore.

## DONE
- Confirmed paper directory exists at papers/Josang_2001_LogicUncertainProbabilities/
- Converted all 31 pages to PNGs
- Read pages 0-10 (pages 1-11 of paper)

## KEY FINDINGS SO FAR (pages 1-11)

### Belief Model (Sec 2.1, p.2-3)
- Based on Dempster-Shafer theory of evidence
- Frame of discernment Theta = set of mutually exclusive states
- Power set 2^Theta contains all subsets
- Belief mass assignment (BMA): m_Theta(x) assigns mass to each subset
- Constraints: m(empty)=0, sum of all masses = 1
- Belief function b(x) = sum of masses of all subsets of x
- Disbelief function d(x) = sum of masses of all subsets of complement of x
- Uncertainty function u(x) = sum of masses that overlap both x and not-x

### Theorem 1 (p.4): b(x) + d(x) + u(x) = 1 for x != Theta, x != empty

### Relative Atomicity (Def 5, p.5)
- a(x) = |x|/|Theta| for dogmatic BMA (u=0)
- General: weighted average of relative sizes

### Probability Expectation (Def 6, p.5)
- E(x) = b(x) + a(x) * u(x)
- Maps opinion to single probability by distributing uncertainty proportionally

### Focused Frame of Discernment (Sec 2.2, p.6)
- Binary frame focusing on state x vs not-x
- Focused BMA preserves belief, disbelief, uncertainty

### Opinion Space (Sec 2.4, p.7-8)
- **CORE DEFINITION**: omega_x = {b(x), d(x), u(x), a(x)} — the opinion tuple
- b + d + u = 1, 0 <= a <= 1
- Graphically represented as triangle (belief-disbelief-uncertainty)
- Probability expectation E(x) = b + a*u
- Director line: base of triangle from disbelief to belief
- Projector: line from opinion point to director, determines E(x)

### Opinion Types (p.8)
- Dynamic opinions: on probability axis (u > 0)
- Absolute opinions: corners, b=1 or d=1 or u=1 (correspond to TRUE/FALSE/vacuous)

### Kolmogorov Axioms (Theorem 2, p.9)
- Probability expectation satisfies Kolmogorov axioms
- E(Theta) = 1, E(x) >= 0, disjoint union additive

### Ordering of Opinions (Def 10, p.9)
- Three criteria: highest E(x), least uncertainty, least relative atomicity

### Ellsberg Paradox Example (p.10-11)
- Demonstrates how opinions capture uncertainty that bare probabilities miss
- Two options with same E(x) but different uncertainty are distinguishable

## FINDINGS FROM PAGES 12-21

### Ordering Opinions Example (p.12-13)
- 9-color urn example showing opinions with same E(x)=1/2 but different uncertainty/atomicity
- Demonstrates all three ordering criteria from Def 10

### Logical Operators (Sec 3, p.13)
- Subjective logic operates on opinions about binary propositions
- Opinions have ownership (agent A's opinion about x): omega_x^A
- Standard binary logic is special case of subjective logic

### Propositional Conjunction (Theorem 3, p.14)
- For x in Theta_X, y in Theta_Y on independent binary frames:
  - b_{x AND y} = b_x * b_y
  - d_{x AND y} = d_x + d_y - d_x * d_y
  - u_{x AND y} = b_x * u_y + u_x * b_y + u_x * u_y
  - a_{x AND y} = a_x * a_y

### Propositional Disjunction (Theorem 4, p.14-15)
- b_{x OR y} = b_x + b_y - b_x * b_y
- d_{x OR y} = d_x * d_y
- u_{x OR y} = d_x * u_y + u_x * d_y + u_x * u_y
- a_{x OR y} = a_{x OR y} (derived relative atomicity)

### Proof 5 (p.17): Probability expectation consistency
- E(omega_{x AND y}) = E(omega_x) * E(omega_y)
- E(omega_{x OR y}) = E(omega_x) + E(omega_y) - E(omega_x) * E(omega_y)
- Conjunction/disjunction preserve probability additivity

### Reliability Analysis Example (Sec 3.2, p.17-18)
- Conjunctive system Z = X AND Y
- Shows how conjunction propagates uncertainty through serial dependencies

### Negation (Theorem 6, p.18)
- NOT x: b_{NOT x} = d_x, d_{NOT x} = b_x, u_{NOT x} = u_x, a_{NOT x} = 1 - a_x
- De Morgan's laws hold

### Evidence Space (Sec 4, p.18-19)
- Beta distribution as alternative representation of uncertain probabilities
- f(p | r, s, a) = probability density function (ppdf)
- r = positive evidence, s = negative evidence, a = relative atomicity
- Parameters: 0 <= p <= 1, 0 <= r, 0 <= s, 0 <= a <= 1

### KEY: Beta distribution connection (Def 11, p.19)
$$f(p | r, s, a) = \frac{\Gamma(r+s+2)}{\Gamma(r+2a) \cdot \Gamma(s+2(1-a))} \cdot p^{r+2a-1} \cdot (1-p)^{s+2(1-a)-1}$$

### Probability expectation from evidence (Eq 18, p.20)
- E(p_i) = (n_i + 2/t) / (sum(n_j) + 2)
- where 1/t is relative atomicity, t = number of outcomes

### Mapping between Evidence and Opinion Spaces (Sec 4.2, p.20-21, Def 12)
- omega = (b, d, u, a) maps to f(p | r, s, a) via:
  - b = r / (r + s + 2)
  - d = s / (r + s + 2)
  - u = 2 / (r + s + 2)
- Inverse: r = 2b/u, s = 2d/u (when u != 0)
- Vacuous opinion (0,0,1,a) corresponds to uniform Beta(1,1)
- Absolute opinions (u=0) correspond to point distributions (Dirac delta)
- Dogmatic opinions excluded from ppdf representation

## FINDINGS FROM PAGES 22-31

### Combination of Evidence (Sec 4.3, p.22)
- Def 13: Combining Evidence - cumulative fusion via ppdf
- f(p | r1+r2, s1+s2, a_combined) where a is weighted average by observation count
- Observer with most observations has greatest influence on a
- Commutative and associative

### Propositional Conjunction of ppdf vs simultaneous pdfs (p.22-23)
- Conjunction of uniform ppdf produces f_{x AND y}(p | 0.00, 0.00, 0.25)
- Simultaneous uniform pdfs produce g(p) = -ln(p) (Eq 24)
- Same expectation E=0.25 but slightly different curves
- ppdf expression may be approximation for non-binary frames

### Evidential Operators (Sec 5, p.24)
- Discounting and consensus - the two non-standard operators

### Discounting (Sec 5.1, p.24)
- Def 14: Discounting operator
- A trusts B about x; B has opinion about x
- omega_x^{A:B} = discounted opinion: b' = b_x * b_B, d' = b_x * d_B (belief in B's opinion scaled by trust)
- u' adjusted, a preserved
- Designator: otimes symbol
- Key: trust transitivity — chain of recommendations

### Consensus (Sec 5.2, p.25-26)
- Theorem 7: Consensus operator (cumulative fusion)
- For two opinions omega_x^A and omega_x^B:
  - b = (b_A * u_B + b_B * u_A) / kappa
  - d = (d_A * u_B + d_B * u_A) / kappa
  - u = (u_A * u_B) / kappa
  - a = (a_B * u_A + a_A * u_B - (a_A + a_B) * u_A * u_B) / (u_A + u_B - 2*u_A*u_B)
- where kappa = u_A + u_B - u_A * u_B (when not both dogmatic)
- Commutative and associative
- Effect: reduces uncertainty — consensus of infinite independent non-dogmatic opinions produces zero uncertainty
- Two dogmatic opinions cannot be combined (undefined)

### Assessment of Testimony from Witnesses (Sec 5.3, p.26-27)
- Judge J evaluates witnesses W1, W2, W3 about proposition x
- Each witness testimony discounted by judge's trust in that witness
- Then discounted opinions combined via consensus operator
- Example: Judge's combined opinion mostly based on most-trusted witness

### Comparing Consensus with Dempster's Rule (Sec 5.4, p.27-28)
- Def 15: Non-normalized Dempster's rule
- Consensus operator gives almost same result as Dempster's rule
- Key advantage: consensus operator handles uncertainty introduction
- Dempster's rule produces dogmatic BMA from witnesses' dogmatic testimony
- Consensus operator introduces uncertainty (via kappa normalization)

### Zadeh's Example (p.28-29)
- Table 4: Consensus operator matches Dempster's rule closely
- Table 5: With uncertainty introduced, consensus gives intuitive result (no suspects guilty)
- Non-normalized Dempster's rule also gives similar result

### Uncertainty Maximization (Sec 6, p.29-30)
- Def 16: Uncertainty maximization
- For events that can only happen once (not repeatable):
  - b' = 0, d' = 0, u' = b + d (transfer all to uncertainty)
  - Actually: transforms belief mass to maximize uncertainty while keeping E(x) unchanged
  - b1 = u1 - u_a * d1/(1-a), d1 = u1 - u_a * b1/a (Eq 30... complex)
- Purpose: observers should express genuine uncertainty about one-time events
- Example: Zadeh's witnesses — uncertainty-maximized opinions are more honest

### Conclusion (Sec 7, p.30-31)
- Subjective logic = opinion metric + standard logical operators + evidential operators
- Makes subjective logic very general and applicable
- Compatible with AND/OR of binary logic
- Successfully applied to authentication, decision making, trust

### References (p.31) — 20 references total

## ALL PAGES READ - ALL OUTPUT FILES WRITTEN

## FILES CREATED
- papers/Josang_2001_LogicUncertainProbabilities/notes.md - comprehensive implementation notes
- papers/Josang_2001_LogicUncertainProbabilities/description.md - tagged description
- papers/Josang_2001_LogicUncertainProbabilities/abstract.md - verbatim abstract + interpretation
- papers/Josang_2001_LogicUncertainProbabilities/citations.md - all 20 references + key follow-ups
- papers/index.md - updated with new entry

## RECONCILIATION COMPLETE

### Forward: 0 already in collection (Josang cites Shafer 1976, Smets, Walley — none in collection)
### Reverse: 1 paper cites this — Sensoy_2018 (cites 2016 book version)
### Conceptual links: 4 total (3 strong, 1 moderate)
- Falkenhainer_1987 (strong) — both use DS theory, different extensions
- Sensoy_2018 (strong) — EDL uses Dirichlet/opinion mapping from Josang
- Denoeux_2018 (strong) — decision criteria for DS belief functions = render layer for opinions
- Li_2011 (moderate) — probabilistic AF could use opinions instead of bare floats

### Updated files:
- Sensoy_2018 notes.md — moved Josang lead to "Now in Collection", added conceptual link, annotated 2 open questions
- Falkenhainer_1987 notes.md — added conceptual link
- Denoeux_2018 notes.md — created Collection Cross-References section, annotated 1 open question

## NEXT
- Write report to reports/read-josang-2001-report.md
