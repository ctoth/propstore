---
title: "Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers"
authors: "Alejandro J. García, Guillermo R. Simari"
year: 2014
venue: "Argument & Computation"
doi_url: "http://dx.doi.org/10.1080/19462166.2013.869767"
pages: "63-88"
affiliations:
  - "Artificial Intelligence Research and Development Laboratory, Department of Computer Science and Engineering, Universidad Nacional del Sur, Bahía Blanca, Argentina"
  - "Consejo Nacional de Investigaciones Científicas y Técnicas, Buenos Aires, Argentina"
---

# Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers

## One-Sentence Summary
Presents the DeLP knowledge-representation language plus the DeLP-Server architecture for serving argumentative queries in a multi-agent setting, with two key extensions on top of plain DeLP: *contextual queries* that let a client send a private d.l.p. fragment together with each query, and *explanations for answers* in the form of fully labelled dialectical analysis trees.

## Problem Addressed
- How to deliver defeasible argumentative reasoning as a service to multiple distributed clients (multi-agent systems) over a shared knowledge base, while letting each client temporarily contextualise the server's program with its own private rules and facts.
- How to make the dialectical reasoning behind an answer transparent to the receiver — i.e., produce explanations that expose every argument and counterargument considered, with their statuses, not just the final warrant verdict.

## Key Contributions
- DeLP knowledge-representation language: facts, strict rules `L0 ← L1,…,Ln`, defeasible rules `L0 -< L1,…,Ln`, classical (strong) negation `~`, default negation `not`, presumptions (defeasible rules with empty body).
- A defeasible-derivation / argument construction discipline that filters out arguments whose strict closure is contradictory (consistency) and forbids redundant subsets (minimality).
- Dialectical-tree based warrant procedure with proper / blocking defeaters and an *argumentation line* discipline (acceptable lines) to block fallacious dialectical reasoning.
- DeLP-Server architecture: a server hosts one or more DeLP knowledge bases and answers queries from many remote client agents; supports public, private, and shared KBs.
- *Contextual queries* (\<contextual query\>): a query carries a temporary d.l.p. fragment that the server merges with its KB for that query only — enabling per-agent perspective without mutating the server.
- Explanation facility: server returns the full set of dialectical trees (and possibly trees for the complement) used to compute the warrant of the queried literal, so the receiver can audit the reasoning.

## Methodology
Formal definitions plus worked examples. Each new construct is introduced as a numbered Definition or Example, then exercised on a running scenario (going to the beach, hiring a gardener, ill / surf, etc.). The architecture portion is described as an interaction protocol between client agents and the DeLP-Server with merging operators over (Π, Δ) program pairs.

## Knowledge representation (Section 2)

### Atoms, literals, complementary pairs *(p.65)*
- *Atoms* are propositional or predicate-style terms that may be preceded by *strong negation* `~`.
- *Literal* / *objective literal*: any atom or strongly-negated atom.
- *Positive literal*: atom not preceded by `~`. *Negative literal*: atom preceded by `~`.
- A pair {L, ~L} is *complementary* / *contradictory*. Example: `~guilty` and `guilty`.
- Atoms are propositional in nature but written first-order-style with variables as place-holders; an atom with variables denotes its set of ground instantiations under the program signature (cites Lifschitz 1996).
- Naming convention: atoms start lowercase, variables uppercase. Example schematics: `~dangerous(X)`, `dangerous(X)`.

### Defeasible logic program (d.l.p.) *(p.65–67)*
A *d.l.p.* is a set of facts, strict rules, and defeasible rules:
- **Facts**: ground objective literals (e.g., `guilty`, `price(100)`, `~alive`). A valid d.l.p. cannot contain two complementary facts.
- **Strict Rules** `L0 ← L1,…,Ln`: ground head plus ground body of literals. Syntactically the *basic rules* of Logic Programming (Lifschitz 1996). Acceptance of body forces acceptance of head. Examples: `~innocent ← guilty`, `mammal ← cat`, `few_surfers ← ~many_surfers`.
- **Defeasible Rules** `L0 -< L1,…,Ln`: weak link, body literals may be preceded by *default negation* `not`. Acceptance of body does not always force acceptance of head. Examples: `~dangerous -< mosquito`, `dangerous -< mosquito, dengue`.
- *Presumption*: defeasible rule with empty body, used as fallback information when no contrary evidence exists (cites García & Simari 2004; Martínez et al. 2012; Nute 1988).

Notation: a d.l.p. is denoted `(Π, Δ)` where Π is the set of facts + strict rules and Δ is the set of defeasible rules. The Π/Δ split is the *central* working object for the rest of the paper *(p.67)*.

### Negation discipline *(p.66)*
- Strong negation `~` is part of the object language.
- Default negation `not` is the meta-level absence-of-evidence operator and is recommended only inside the body of defeasible rules.
- Literals appearing under `not` are *extended literals*; bodies that mention them give another form of defeasibility.
- Strict rules with extended literals would themselves become defeasible — discouraged.
- Examples illustrate the difference: `alive -< not dead` ("if we cannot be sure something is dead, there are reasons to believe it is alive"), `~cross_railway_tracks -< not ~train_is_coming`.

### Symbols `-<` and `←` are meta-relations *(p.67)*
They relate a head literal to a body literal-set; they are NOT object-language conditionals. Therefore *no contraposition* applies to either kind of rule. All d.l.p. programs are ground; schematic rules with variables are syntactic sugar for the set of ground instantiations.

## Running Example (Π_2.1, Δ_2.1) *(p.67)*

Π_2.1 (facts + strict rules):
```
monday
cloudy
dry_season
waves
grass_grown
hire_gardener
vacation
~working ← vacation
few_surfers ← ~many_surfers
~surf ← ill
```

Δ_2.1 (defeasible rules):
```
surf -< nice, spare_time
nice -< waves
~nice -< rain
rain -< cloudy
~rain -< dry_season
spare_time -< ~busy
~busy -< ~working
cold -< winter
working -< monday
busy -< yard_work
yard_work -< grass_grown
~yard_work -< hire_gardener
many_surfers -< waves
~many_surfers -< monday
```

Used throughout to demonstrate argument construction, defeat, dialectical trees, and warrant.

## Defeasible derivations and arguments (Section 3)

### Defeasible derivation *(p.68)*
A ground literal `L` has a *defeasible derivation* from `(Π, Δ)` iff there is a finite sequence of ground literals `L1,L2,…,Ln = L` where each `Li` is either:
- a fact in Π, or
- the head of a (strict or defeasible) rule in `(Π, Δ)` whose body literals are each `Lk` (k < i) earlier in the sequence, or an *extended literal* (literal under default negation).

A literal is *strictly derived* if its derivation uses only facts and strict rules from Π (no defeasible rules).

**Coherence requirement on Π** *(p.68)*: from Π alone no pair of contradictory literals can be strictly derived; i.e. Π is required to be representationally coherent.

In `(Π_2.1, Δ_2.1)`: `surf` has the defeasible derivation `vacation, ~working, ~busy, spare_time, waves, nice, surf` (uses two facts and four defeasible rules). Both `rain` (via `rain -< cloudy`) and `~rain` (via `~rain -< dry_season`) are defeasibly derivable — defeasible derivations of contradictory literals are allowed; this is exactly the situation the dialectical layer is for.

### Definition 3.1 — Argument *(p.68)*
Given `(Π, Δ)` and ground literal `L`, `A` is an *argument* for conclusion `L` (denoted `⟨A, L⟩`) iff `A ⊆ Δ` is a **minimal** set of defeasible rules such that:
1. There exists a defeasible derivation for `L` from `Π ∪ A`.
2. No pair of contradictory literals can be defeasibly derived from `Π ∪ A` (consistency).
3. If `A` contains a rule with extended literal `not F` in its body, then `F` cannot be in the defeasible derivation of `L` from `Π ∪ A` (default-negation faithfulness).

### Worked arguments from running example *(p.68–69)*
Eleven arguments are exhibited (`A_0` through `A_11`), e.g.:
- `⟨A_0, surf⟩ = ⟨{surf -< nice,spare_time; nice -< waves; spare_time -< ~busy; ~busy -< ~working}, surf⟩`
- `⟨A_1, ~nice⟩ = ⟨{~nice -< rain; rain -< cloudy}, ~nice⟩`
- `⟨A_2, nice⟩`, `⟨A_3, rain⟩`, `⟨A_4, ~rain⟩`, `⟨A_5, busy⟩`, `⟨A_6, ~yard_work⟩`, `⟨A_7, yard_work⟩`, `⟨A_8, spare_time⟩`, `⟨A_9, ~busy⟩`, `⟨A_10, many_surfers⟩`, `⟨A_11, ~many_surfers⟩`.

Important caveats illustrated *(p.69)*:
- A literal can have a defeasible derivation but no argument — example `(Π_3.2, Δ_3.2)` with `Π_3.2 = {night, at_market, ~at_home ← at_market}, Δ_3.2 = {at_home -< night}`: `Π_3.2 ∪ {at_home -< night}` is contradictory, so no argument for `at_home` exists.
- Minimality is required: `S = {nice -< waves; ~busy -< ~working}` is consistent and yields `nice`, but `S` is not an argument for `nice` because the proper subset `A_2 ⊂ S` already does.

### Subargument / superargument / counterargument *(p.69)*
- `⟨B, Q⟩` is a *subargument* of `⟨A, L⟩` iff `B ⊆ A` (every argument is sub/super of itself).
- Two literals `L`, `Q` *disagree* in `(Π, Δ)` if `Π ∪ {L, Q}` is contradictory; in particular, complementary literals always disagree.
- `⟨B, Q⟩` is a *counterargument* for `⟨A, L⟩` *at literal P* if there exists subargument `⟨C, P⟩` of `⟨A, L⟩` such that `P` and `Q` disagree. `P` is the *counterargument point*; `⟨C, P⟩` is the *disagreement subargument*. Synonyms: `⟨B, Q⟩` *attacks* `⟨A, L⟩`; the two are *in conflict*.
- A counterargument for `A` is automatically a counterargument for any superargument of `A` *(p.70)*.
- Strict-derivation immunity *(p.70)*: any literal with a strict derivation has the trivial empty argument with no possible counter-argument — proved in García & Simari 2004.

## Warrants and answers for queries (Section 4)

### Four-valued answer space *(p.70)*
Given query (ground literal) `Q` against program `P`:
- **YES** — `Q` is warranted from `P`.
- **NO** — the complement of `Q` is warranted from `P`.
- **UNDECIDED** — neither `Q` nor its complement is warranted from `P`.
- **UNKNOWN** — `Q` is not in the signature (language) of `P`.

In `(Π_2.1, Δ_2.1)`: `surf` → YES, `busy` → NO, `many_surfers` → UNDECIDED, `beach_closed` → UNKNOWN.

### Defeater relation *(p.70–71)*
Given a *preference criterion* over arguments, `D` is a *defeater* for `A` if `D` counter-argues `A` with disagreement subargument `B`, AND one of:
- (a) `D` is preferred to `B` → `D` is a *proper defeater* for `A`.
- (b) `D` and `B` are equally preferred OR incomparable → `D` is a *blocking defeater* for `A`.
- (c) `D` is an argument for `F` and `not F` appears in some rule of `A` → `D` is an attack on an *assumption* of `A`.

If `B` is preferred to `D`, then `D` is still a counter-argument but NOT a defeater.

### Argument-comparison criterion is modular *(p.71)*
Any preference criterion over arguments may be plugged in. Different criteria are introduced in García 2000, García & Simari 2004, Ferretti, Errecalde, García & Simari 2008. The paper's running examples use the *rule-priorities* criterion from García & Simari 2004:

Given a partial order `<_R` over defeasible rules with intuitive reading "`R_2` is preferred to `R_1` in the application domain", `A_1` is preferred to `A_2` iff:
1. ∃ rule `r_a ∈ A_1` and rule `r_b ∈ A_2` with `r_b <_R r_a`, AND
2. there is no rule `r'_b ∈ A_2`, `r'_a ∈ A_1` with `r'_a <_R r'_b`.

Example 4.1 priorities for the running program:
- `(rain -< cloudy) <_R (~rain -< dry_season)`
- `(yard_work -< grass_grown) <_R (~yard_work -< hire_gardener)`

Consequences in the example *(p.71)*:
- `⟨A_4, ~rain⟩` is a proper defeater of `⟨A_1, ~nice⟩` (and of `⟨A_3, rain⟩`).
- `⟨A_1, ~nice⟩` and `⟨A_2, nice⟩` are mutual blocking defeaters.
- `⟨A_0, surf⟩` has two blocking defeaters: `⟨A_1, ~nice⟩` at point *nice* and `⟨A_5, busy⟩` at point *~busy*.
- `⟨A_6, ~yard_work⟩` properly defeats `⟨A_7, yard_work⟩` and `⟨A_5, busy⟩`.
- `⟨A_10, many_surfers⟩` and `⟨A_11, ~many_surfers⟩` are mutual blockers.

### Argumentation lines and acceptability *(p.72)*
An *argumentation line* `Λ = [⟨A_1, L_1⟩, ⟨A_2, L_2⟩, …]` for root `⟨A_1, L_1⟩` is a sequence in which each non-root element defeats its predecessor. The line splits into:
- *Supporting* set `Λ_S = {⟨A_1,L_1⟩, ⟨A_3,L_3⟩, ⟨A_5,L_5⟩, …}` (odd positions).
- *Interfering* set `Λ_I = {⟨A_2,L_2⟩, ⟨A_4,L_4⟩, …}` (even positions).

Lines must be *acceptable*: finite, no argument repetition, supporting/interfering subsets concordant. Formally `Λ` is acceptable iff:
1. `Λ` is finite.
2. `Λ_S` is concordant (no defeasible derivation of contradictory literal pair from `Π ∪ ⋃ A_i`); same for `Λ_I`.
3. No `⟨A_k, L_k⟩` in `Λ` is a *disagreement subargument* of any `⟨A_i, L_i⟩` earlier in the line (i < k).
4. Whenever `⟨A_i, L_i⟩` is a blocking defeater of its predecessor, the next defeater `⟨A_{i+1}, L_{i+1}⟩` (if any) must be a *proper* defeater of `⟨A_i, L_i⟩` — required to break blocking-vs-blocking standoffs.

Example: `[⟨A_0, surf⟩, ⟨A_1, ~nice⟩, ⟨A_4, ~rain⟩]` is an acceptable line — `A_1` interferes for `surf`, `A_4` supports `surf` again. Two acceptable lines for `⟨A_0, surf⟩` are: `Λ_1 = [⟨A_0,surf⟩, ⟨A_1,~nice⟩, ⟨A_4,~rain⟩]` and `Λ_2 = [⟨A_0,surf⟩, ⟨A_5,busy⟩, ⟨A_6,~yard_work⟩]`.

### Dialectical tree *(p.72–73)*
Multiple acceptable lines starting with the same root must be considered jointly. The *dialectical tree* `T_⟨A_1,L_1⟩` is constructed as:
1. Root labelled `⟨A_1, L_1⟩`.
2. For node `N` labelled `⟨A_n, L_n⟩` with line-from-root `[⟨A_1,L_1⟩,…,⟨A_n,L_n⟩]`: for each defeater `⟨B_i, Q_i⟩` of `⟨A_n, L_n⟩` such that the extended line `Λ' = [⟨A_1,L_1⟩,…,⟨A_n,L_n⟩,⟨B_i, Q_i⟩]` is acceptable, `N` gets a child labelled `⟨B_i, Q_i⟩`. Otherwise `N` is a leaf.

Each branch corresponds to a distinct acceptable line. Figure 1 shows `T_⟨A_0, surf⟩` for the running program.

### Marking procedure → warrant *(p.73)*
The dialectical tree is marked bottom-up to obtain `T*_⟨A,L⟩`:
- All leaves marked **U** (undefeated).
- Each inner node `⟨B, Q⟩`:
  - (a) Marked **U** iff every child is marked **D**.
  - (b) Marked **D** iff at least one child is marked **U**.

**Definition 4.2 — Warrant** *(p.74)*: `T*_⟨A,L⟩` warrants `L` iff the root mark is **U**. Then `L` is *warranted* from `P`. A literal `L` is warranted iff there exists *at least one* argument `A` for `L` whose marked dialectical tree has root **U**.

Bundle-set property (Chesñevar & Simari 2007): the order in which defeaters are explored does not change the root marking — only the underlying set of acceptable argumentation lines (the *bundle set*) matters. So warrant is well-defined. Fact: any literal with a strict derivation is warranted (no argument can disagree with it; García 2000, García & Simari 2004).

DeLP interpreter input/output: program `P`, query `L` (ground literal) → returns YES / NO / UNDECIDED / UNKNOWN.

### Worked answer table for running program *(p.75)*

| Query | Answer |
|-------|--------|
| `surf` | YES |
| `~surf` | NO |
| `many_surfers` | UNDECIDED |
| `~many_surfers` | UNDECIDED |
| `nice` | YES |
| `~nice` | NO |
| `beach_closed` | UNKNOWN |
| `~working` | YES |
| `working` | NO |
| `few_surfers` | UNDECIDED |

Notes:
- `beach_closed` is UNKNOWN because it is not in the program's signature.
- `~working` is YES because it has a strict derivation (any strict-derivation literal is automatically warranted).
- `few_surfers` is UNDECIDED because the strict rule that has it as head cannot fire (its body cannot be strictly derived); a defeasible derivation exists, but the supporting argument is blocked, hence no warrant.

## DeLP reasoning servers (Section 5)

### Motivation *(p.75–76)*
- DeLP-Servers (introduced García, Rotstein, Tucat, & Simari 2007) provide argumentative reasoning services for multi-agent systems.
- Hosts/agents may be physically distributed; client agents remotely consult a DeLP-Server which holds a public DeLP-program acting as common/public knowledge.
- A client may attach private knowledge to a query; that knowledge does NOT permanently change the server's program — it is *temporal* and lasts only for the duration of the query.
- Multiple clients may query the same server concurrently with different private contexts and receive different answers depending on their context. Multiple servers per host, multiple agents per host, mixed topology — Figure 3 shows three servers, five clients, four hosts.
- Application example given: a real-estate DeLP-Server stores public properties + general suitability rules; clients add private contexts like `single, afford(3000)` or `has_children, work_at_home, ~conv_br(2)` and receive personalised answers about which properties are *suited*.

### Definition 5.1 — DeLP-Server *(p.77)*
A DeLP-Server is a triple `«I, O, P»` where:
- `I` is a DeLP-interpreter (function `I : D × L → {YES, NO, UNDECIDED, UNKNOWN}` — D is the domain of all DeLP-programs, L the domain of DeLP-queries).
- `O` is a set of DeLP-program operators (binary functions `o : D × D → D`).
- `P` is the DeLP-program (the public knowledge base).

Operators `O` are *modular*: each server defines its own set of operators appropriate to its application domain, but DeLP-program operators must always return a program where Π remains non-contradictory.

### Definition 5.2 — Contextual query *(p.78)*
A *contextual query* for a DeLP-Server `«I, O, P»` is a pair `(Co, Q)` where:
- `Q` is a DeLP-query (a literal).
- `Co` is a *sequence* `[({P_1}, o_1), ({P_2}, o_2), …, ({P_n}, o_n)]` where each `P_i ∈ D` is a DeLP-program (private context fragment) and each `o_i ∈ O` is a server operator.

The order of the pairs in `Co` matters — the operators are composed left-to-right.

### Definition 5.3 — Answer for a contextual query *(p.79)*

For `Co = [({P_1}, o_1), …, ({P_n}, o_n)]`, define the integration:
$$
\mathcal{P} \diamond Co \;=\; (o_n^{\mathcal{P}_n} \circ o_{n-1}^{\mathcal{P}_{n-1}} \circ \cdots \circ o_2^{\mathcal{P}_2} \circ o_1^{\mathcal{P}_1})(\mathcal{P})
$$
where `o_i^{P_j}(P_k)` is shorthand for `o_i(P_j, P_k)` — apply operator `o_i` with private fragment `P_i` and the running result.

The answer for `(Co, Q)` is `I((P ⋄ Co), Q)`.

### Three concrete operators (running example) *(p.77–78)*

For a restricted (Π, Δ) where Π contains facts only (no strict rules), define `x̄` as the strong-negation complement of fact `x` (i.e. `ā = ~a` and `~̄a = a`), and `X̄ = {x̄ | x ∈ X}`:

$$
(\Pi, \Delta) \oplus (\Pi_a, \Delta_a) = ((\Pi \setminus \overline{\Pi_a}) \cup \Pi_a,\; \Delta \cup \Delta_a)
$$

$$
(\Pi, \Delta) \otimes (\Pi_a, \Delta_a) = (\Pi \cup (\Pi_a \setminus \overline{\Pi}),\; \Delta \cup \Delta_a)
$$

$$
(\Pi, \Delta) \ominus (\Pi_a, \Delta_a) = (\Pi \setminus \Pi_a,\; \Delta \setminus \Delta_a)
$$

Semantics:
- `⊕` (private wins): merge defeasibles, but for facts the private side wins — drop any server fact whose complement is in the private fragment, then take union. Example: `({a,b}, Δ) ⊕ ({~a,c}, Δ_a) = ({b, ~a, c}, Δ ∪ Δ_a)`.
- `⊗` (public wins): merge defeasibles, but for facts the server side wins — keep all server facts, then add only those private facts whose complement is *not* already in the server. Example: `({a,b}, Δ) ⊗ ({~a,c}, Δ_a) = ({a,b,c}, Δ ∪ Δ_a)`.
- `⊖` (subtract): remove the named facts and defeasible rules from the server's program. Used to *forget* server knowledge for the purposes of one query. Example: `({a,b,p}, Δ) ⊖ ({a,b,~p}, Δ_a) = ({p}, Δ \ Δ_a)`.

### Real-estate example query results *(p.79)*
With server `«I, {⊕, ⊗, ⊖}, (Π_RS, Δ_RS)»` and the operator-`⊕` private contexts `{single, afford(3000)}`, `{single, afford(4000)}`, `{grown_children, afford(4000)}`, `{grown_children, afford(9000)}`, the paper exhibits explicit YES/NO answers per property `p1…p3`, plus an example with two operators in sequence `[({grown_children, afford(4000)}, ⊕), ({~conv_br(2) -< grown_children}, ⊖)]` returning YES for `suited(p2)` after the server's `~conv_br(2) -< grown_children` rule is removed.

## Explanations for answers (Section 6)

### Goal *(p.79–80)*
An *explanation* should transfer the *understanding* of how a warrant verdict was reached, not merely the verdict. Cited references on explanation in expert systems: Lacave & Diez 2004, Ye & Johnson 1995, Guida & Zanella 1997. From argumentation: Belanger 2007, Moulin, Irandoust, Bélanger & Desbordes 2002, Walton 2004. Walton's distinction: arguments persuade about something doubtful; explanations clarify something the hearer already accepts.

Quote (Lacave & Diez 2004) used as design target: explanation should *expose* something so it is *understandable*, *satisfactory*, and *improves* the receiver's knowledge.

The DeLP δ-Explanation does this by *exposing the entire set of dialectical trees* that led to the warrant verdict for both `Q` and its complement `Q̄` — every argument, every defeat, every U/D mark.

### Bob-and-the-opera example *(p.80–81)*

`Π_6.1 = {show_tonight, birthday, baby}`,
`Δ_6.1 = { go -< showTonight; go -< showTonight, friends; friends -< birthday; ~go -< friends; ~go -< showTonight, friends, baby }`.

Priorities:
- `(~go -< friends) <_R (go -< showTonight, friends)`
- `(go -< showTonight, friends) <_R (~go -< showTonight, friends, baby)`

Arguments: `O_1 = ⟨{go -< showTonight}, go⟩`, `O_2 = ⟨{(~go -< friends),(friends -< birthday)}, ~go⟩`, `O_3 = ⟨{(go -< showTonight,friends),(friends -< birthday)}, go⟩`, `O_4 = ⟨{(~go -< showTonight,friends,baby),(friends -< birthday)}, ~go⟩`.

`O_2` blocking-defeats `O_1` and vice versa. `O_3` properly defeats `O_2`. `O_4` properly defeats both `O_3` and `O_1`. Net: query `go` returns NO and `~go` returns YES.

### Definition 6.2 — δ-Explanation *(p.80)*
For DeLP-program `P` and DeLP-query `Q`:
- `T*(Q)` = set of marked dialectical trees for ALL arguments supporting `Q`.
- `T*(Q̄)` = set of marked dialectical trees for ALL arguments supporting the complement.
- `T*_U(Q)` = `{T ∈ T*(Q) | Mark(T) = U}` — marked trees that *warrant* `Q`.
- `T*_D(Q)` = `{T ∈ T*(Q) ∪ T*(Q̄) | Mark(T) = D}` — trees whose roots are defeated.

The δ-Explanation for `Q` from `P`:
$$
\mathbb{E}_\mathcal{P}(Q) \;=\; (\mathbb{T}^*_U(Q),\; \mathbb{T}^*_U(\overline{Q}),\; \mathbb{T}^*_D(Q))
$$

So an explanation is a triple of tree sets: warrant-providing trees for `Q`; warrant-providing trees for the complement; and all defeated trees from either side.

For the opera example, `E_{P_6.1}(~go) = ({T*}, ∅, {T*, T*, T*})` (4 trees total — Figure 5 shows them all marked).

### Definition 6.4 — Generalised δ-Explanation for schematic queries *(p.82–83)*
A *schematic query* contains at least one variable. The set of legal ground instances is restricted to constants in the program signature; instances using out-of-signature constants would be UNKNOWN with empty explanation.

For `Q` schematic with ground instances `{Q_1, …, Q_z}` over the signature:
$$
\mathbb{GE}_\mathcal{P}(Q) \;=\; \{ \mathbb{E}_\mathcal{P}(Q_1),\; \ldots,\; \mathbb{E}_\mathcal{P}(Q_z) \}
$$

Worked example (`Π_6.3, Δ_6.3` with `bird/chicken/scared/flies` and rule `flies -< bird`, `flies -< chicken,scared`, `~flies -< chicken`, facts `chicken(little)`, `chicken(tina)`, `scared(tina)`, `bird(rob)`):
- `~flies(little)` is warranted (chicken-not-flies dominates).
- `flies(rob)` is warranted (rob is a bird with no defeater).
- `flies(tina)` is NOT warranted (chicken-not-flies vs scared-flies blocks).
The generalised explanation packs three δ-Explanations, one per ground instance.

### Schematic-query answer table *(p.84)*
- **YES** if there exists at least one instance `Q_i` such that `T*_U(Q_i) ≠ ∅` (some grounding warranted).
- **NO** if for every instance, `T*_U(Q̄_i) ≠ ∅` (every grounding's complement is warranted).
- **UNDECIDED** if no instance is YES but at least one is UNDECIDED.
- **UNKNOWN** if `{Q_1,…,Q_n} = ∅`.

The schematic answer is hence a *quantification surface* over ground instances, not a single boolean: a YES schematic answer means "there exists an individual"; downstream reasoning can collect those individuals.

### Programmer use case *(p.84)*
δ-Explanations are described as a *debugging tool*: when a DeLP program returns an unexpected verdict, the explanation surfaces the exact tree where the unexpected interaction happened.

## Extensions and variations on DeLP (Section 7) *(p.84–85)*

The paper sketches DeLP-derived extensions:
- **P-DeLP** (Possibilistic DeLP, Alsinet, Chesñevar, Godo, Sandri & Simari 2008; Chesñevar, Simari, Alsinet & Godo 2004): possibilistic uncertainty + fuzzy knowledge at the object level. Built over PGL (Horn-rule fragment of Gödel fuzzy logic). Necessity-measure certainty degrees; argument-based consequence operators; complete calculus for max-degree possibilistic entailment.
- **ST-DeLP / E-TAF** (Budán, Gómez Lucero, Chesñevar & Simari 2012): Strength and Time DeLP. Temporal availability and strength factors per element. Compares argument strength over time to determine availability of attacks; defines temporal acceptability. Related: Pardo & Godo 2011.
- **APOP** (García, García & Simari 2008): argumentation-based partial-order planning. Extends POP with arguments-as-planning-steps. Introduces three threat types: action-action, action-argument, argument-argument.
- **ONTOarg / d-ontologies** (Gómez, Chesñevar & Simari 2013): defeasible argumentation over inconsistent Description-Logic ontologies. Dialectical analysis decides individual/concept membership in inconsistent KBs; supports local-as-view ontology integration.
- **Massively built arguments over RDBMS** (Deagustini et al. 2013): integrating DBMS with argument-based inference for warrant computation; targeted at decision-support and recommender systems.

## Collection Cross-References

### Already in Collection
- [Circumscription — A Form of Non-Monotonic Reasoning](../McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/notes.md) — cited in §1 introduction as canonical NMR antecedent of the argumentation tradition.
- [A Logic for Default Reasoning](../Reiter_1980_DefaultReasoning/notes.md) — cited in §1 introduction as canonical default-logic antecedent.
- [Semantical Considerations on Nonmonotonic Logic](../Moore_1985_SemanticalConsiderationsNonmonotonicLogic/notes.md) — citation lists the 1984 workshop precursor; the 1985 *AI* paper is the published-form companion of that work, cited for autoepistemic logic as a foundational NMR formalism.

### Cited By (in Collection)
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this paper as ref [40] for the DeLP-Server contextual-query framing; precedent for context-aware defeasible reasoning that Al-Anbaki's L = ⟨G, β, D, λ⟩ extends with a multi-authority spectrum.
- [Approximate Reasoning with ASPIC+ by Argument Sampling](../Thimm_2020_ApproximateReasoningASPICArgumentSampling/notes.md) — cites this paper as a DeLP reference in the structured-argumentation landscape that Thimm's approximate-reasoning sampling targets.

### New Leads (Not Yet in Collection)
- García & Simari (2004) "Defeasible logic programming: An argumentative approach" — *TPLP* 4. The canonical DeLP paper; defines (Π, Δ) programs, defeasible derivation, dialectical trees, warrant. Necessary upstream for any DeLP-grounded implementation.
- Simari & Loui (1992) "A mathematical treatment of defeasible reasoning and its implementation" — *AI* 53. Mathematical foundations of the dialectical procedure DeLP inherits.
- García (2000) PhD thesis. Operational semantics + parallelism for DeLP; context for the server execution model.
- Tucat, García & Simari (2009) "Using defeasible logic programming with contextual queries for developing recommender servers" — *AAAI Fall Symp.* Direct predecessor of §5–6 of this paper.
- García, Rotstein, Tucat & Simari (2007) "An argumentative reasoning service for deliberative agents" — *KSEM*. Initial argumentative-service architecture.
- García, Rotstein, Chesñevar & Simari (2009) "Explaining why something is warranted in DeLP" — *ExaCt*. Explanation lineage.
- García, Chesñevar, Rotstein & Simari (2013) "Formalizing dialectical explanation support" — *Expert Sys. Appl.* 40. The §6 explanation framework.
- Pardo & Godo (2011) "t-DeLP: A temporal extension of the DeLP argumentative framework" — *SUM*. Temporal DeLP, relevant to propstore's TIMEPOINT/Allen integration.
- Alsinet, Chesñevar, Godo, Sandri & Simari (2008) P-DeLP / possibilistic-fuzzy DeLP — *IJAR* 48. Relevant if subjective-logic-style certainty becomes a goal.
- Budán, Gómez Lucero, Chesñevar & Simari (2012) ST-DeLP / E-TAF (time + reliability) — *KR*. Temporal-strength structured argumentation.
- Gómez, Chesñevar & Simari (2013) ONTOarg — *Expert Sys. Appl.* 40. DeLP-style argumentation over ontology integration; closest to propstore's vocabulary/concept reconciliation use case.
- Deagustini et al. (2013) RDBMS as a defeasible argumentation source — *KBS*. Relevant when wiring storage to argumentation.
- Chesñevar, Maguitman & Loui (2000) "Logical models of argument" — *ACM Computing Surveys* 32. Foundational survey.
- Bench-Capon & Dunne (2007) "Argumentation in artificial intelligence" — *AI* 171. Survey.
- Besnard & Hunter (2008) *Elements of argumentation* — MIT Press.
- Prakken & Vreeswijk (2002) "Logics for defeasible argumentation" — *Handbook of Philosophical Logic*.
- Bondarenko, Dung, Kowalski & Toni (1997) "An abstract, argumentation-theoretic approach to default reasoning" — *AI* 93. ABA — relevant to ATMS-style assumption labels.
- Lifschitz (1996) "Foundations of logic programs" — provides the LP-syntax conventions DeLP inherits.
- Pollock (1987 / 1996) defeasible-reasoning foundations.
- Loui (1987) "Defeat among arguments" — *Computational Intelligence* 3.
- Nute (1987 / 1988) defeasible reasoning.

### Conceptual Links (not citation-based)

**Structured argumentation / ASPIC+ family:**
- [The ASPIC+ framework for structured argumentation: a tutorial](../Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md) — DeLP and ASPIC+ are sibling structured-argumentation formalisms. DeLP's strict/defeasible rule split, defeater taxonomy (proper/blocking), and dialectical-tree warrant correspond closely to ASPIC+'s strict/defeasible rules, rebut/undercut/undermine attack types, and grounded extension. Propstore's `propstore.aspic_bridge` implements ASPIC+; this paper supplies the DeLP-side reference for the same backward-chaining query semantics.
- [Approximate Reasoning with ASPIC+ by Argument Sampling](../Thimm_2020_ApproximateReasoningASPICArgumentSampling/notes.md) — Thimm samples arguments rather than enumerating dialectical trees exhaustively; complementary perspective on the same warrant-computation problem this paper solves enumeratively.

**Context-aware defeasible reasoning:**
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — Al-Anbaki's contextualisation L = ⟨G, β, D, λ⟩ generalises the DeLP-Server contextual-query operators ⊕ ⊗ ⊖ to a multi-authority spectrum with observational/undertaken/hidden context layers. DeLP-Server provides the per-query merge mechanism; Al-Anbaki provides the architectural enclosing layer.
- [Formalizing Context (1993)](../McCarthy_1993_FormalizingContext/notes.md) — McCarthy's `ist(c, p)` framework is the model-theoretic ancestor of contextual-query DeLP: the (Π, Δ) ⋄ (Π_a, Δ_a) merge under operator ⋄ is a concrete computational realisation of "what holds in context c after lifting from c_0". Propstore's `ist(c, p)` claim contexts inherit this lineage.

**Argumentation surveys / handbooks (mutual references):**
- [Argumentation in Artificial Intelligence](../Rahwan_2009_ArgumentationArtificialIntelligence/notes.md) (collection has metadata stub only) — Rahwan & Simari 2009 is co-edited by an author of this paper and is the standard handbook the structured-argumentation community references.

## Status / blocker

- All 28 pages read. Reference list pages (24-27) extracted in `citations.md`.
- Reconciliation completed 2026-05-06.
- No blocker.
