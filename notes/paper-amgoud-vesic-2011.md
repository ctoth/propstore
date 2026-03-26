# Paper Processing: Amgoud & Vesic 2011

## Date: 2026-03-24

## GOAL
Process Amgoud & Vesic (2011) "A new approach for preference-based argumentation frameworks" through full pipeline.

## STATUS
- [x] PDF retrieved (36 pages, 370KB) via DOI 10.1007/s10472-011-9271-9
- [x] Page images converted (36 PNGs)
- [ ] Reading pages (pages 0-11 done, 12-35 remaining)
- [ ] notes.md
- [ ] abstract.md
- [ ] description.md
- [ ] citations.md
- [ ] metadata.json (exists from fetch)
- [ ] extract-claims
- [ ] report

## FILES
- `papers/Amgoud_2011_NewApproachPreference-basedArgumentation/` — paper directory
- `papers/Amgoud_2011_NewApproachPreference-basedArgumentation/paper.pdf` — 36-page PDF
- `papers/Amgoud_2011_NewApproachPreference-basedArgumentation/metadata.json` — basic metadata
- `papers/Amgoud_2011_NewApproachPreference-basedArgumentation/pngs/` — 36 page images

## KEY FINDINGS SO FAR (pages 0-11)

### Core Critique
Existing preference-based argumentation frameworks (PAFs) that remove critical attacks (where stronger argument is attacked by weaker) can produce **conflicting extensions** when the attack relation is asymmetric. Three approaches criticized: [6] Amgoud & Cayrol, [17] Bench-Capon, [38] Simari & Loui.

### Example 1 (p.6): The key counterexample
- A = {a,b}, R = {(a,b)}, b > a (asymmetric attack)
- Removing critical attack leaves Def = empty set
- {a,b} becomes stable extension — but it's NOT conflict-free w.r.t. R
- Violates that extensions should represent coherent positions

### The Paper's Approach — Two Key Novelties
1. **Preferences at the semantics level** (not the attack level): Don't remove attacks; instead define a dominance relation on the powerset of arguments
2. **Semantics as dominance relation**: Extensions are maximal elements of a dominance relation on P(A)

### Formal Framework
- **PAF** = (A, R, ≥) where A is arguments, R is attack, ≥ is partial/total preorder on A
- **Definition 7 (New semantics)**: A semantics τ is a binary relation ≽ on P(A) (the powerset). The relation ≽ is the strict part. Extensions = elements of ≽_max.
- **Three Postulates** for any valid dominance relation:
  - P1: Conflict-free sets strictly preferred to conflicting ones
  - P2: Attack wins when not critical (attacker not weaker than attacked)
  - P3: Preferences privileged in critical attacks (if a attacks a' and a' > a, then {a'} ≻ {a})

### Pref-stable semantics (Definition 11, p.12)
- E ≽_s E' iff:
  - E ∈ CF(T) and E' ∉ CF(T), or
  - E,E' ∈ CF(T) and ∀a' ∈ E'\E, ∃a ∈ E\E' s.t. (aRa' and not(a'>a)) or (a > a')
- ≽_s is NOT transitive
- Satisfies P1, P2, P3
- Generalizes stable semantics (Theorem 2)

### Running Example (p.12)
- A={a,b,c}, a>b, attack chain a←→b←→c
- Conflict-free sets: ∅, {a}, {b}, {c}, {a,c}
- ≽_{s,max} = {{a,c}} — the unique Pref-stable extension

## FINDINGS FROM PAGES 12-23

### Pref-preferred semantics (Definition 12, p.13)
- E ≽_p E' iff: E ∈ CF(T) and E' ∉ CF(T), or both CF and for every attack from E' to E that doesn't fail, E can defend; and for every attack from E to E' that fails, there's a defender in E.
- Satisfies P1, P2, P3 (Property 4)
- Generalizes preferred semantics (Theorem 3)
- Every pref-stable extension is pref-preferred (Theorem 4)
- ≽_p is NOT transitive

### Pref-grounded semantics (Definition 13-14, p.14)
- Strongly defends: E strongly defends a from attacks
- Pref-grounded extension: starts from ∅, iteratively adds strongly defended arguments
- Satisfies P1, P2, P3 (Property 6)
- Generalizes grounded semantics (Theorem 5)
- Unique pref-grounded extension (Property 5: |≽_{g,max}| = 1)
- Pref-grounded ⊆ intersection of all pref-preferred (Theorem 6)

### Section 6: Characterizing Pref-stable (p.15-18) — KEY THEORETICAL CONTRIBUTION
- **Additional Postulates P4-P6** for full characterization:
  - P4: If an argument in E' can't be compared to ANY argument in E (no attack, no preference), then E cannot be preferred to E'
  - P5: E ≽ E' if for every a' in E', there's an a in E that "wins" against a' (via attack+not weaker, or reverse attack+stronger)
  - P6: Dominance depends only on distinct elements (E\E' vs E'\E)
- **Definition 15**: Pref-stable semantics = satisfies P1, P4, P5, P6
- **Theorem 7**: All pref-stable relations yield the SAME maximal elements (unique extensions)
- **Property 9**: No transitive relation generalizes stable semantics and satisfies P1+P5
- **General pref-stable** (Definition 16, ≽_gn): most general — E ≽_gn E' iff provable from postulates
- **Specific pref-stable** (Definition 17, ≽_sp): most specific — E ≽_sp E' iff cannot be disproved
- **Theorem 9**: ≽_gn ⊆ any pref-stable ⊆ ≽_sp

### Theorem 10 (p.18) — Direct characterization of pref-stable extensions
E ∈ ≽_max iff:
- E ∈ CF(T), and
- ∀a' ∈ A\E, ∃a ∈ E such that (aRa' and not(a'>a)) or (a'Ra and a>a')

### Theorem 11 (p.18) — Attack inversion method
Compute pref-stable extensions by inverting critical attacks:
- If (a,b) ∈ R and not(b>a), keep (a,b) ∈ R'
- If (a,b) ∈ R and b>a, then (b,a) ∈ R'
- Then Ext_s(A,R') = pref-stable extensions

### Complexity (Theorem 12, p.19)
- Verification (is E a pref-stable extension?): polynomial
- Existence (does PAF have a pref-stable extension?): NP-complete
- Credulous acceptance: NP-complete
- Skeptical acceptance: coNP-complete
Same complexity as standard Dung stable semantics.

### Section 7: Preferred sub-theories application (p.19-22)
- Shows PAF framework retrieves Brewka's preferred sub-theories [21]
- Knowledge base Σ stratified into Σ_1 ∪ ... ∪ Σ_n
- Preferred sub-theory: S = S_1 ∪ ... ∪ S_n, maximal consistent subbase of each stratum
- Theorem 13: Each pref-stable extension of (Arg(Σ), R_as, ≥_WLP) is built from a unique preferred sub-theory
- Theorem 14: Conversely, each preferred sub-theory yields a pref-stable extension
- Full correspondence established (Corollary 1)

### Section 8: Related work (p.22-24)
- Two roles of preferences: (1) building the AF, (2) selecting among extensions
- Criticizes [6] Amgoud-Cayrol and [17] Bench-Capon: only correct when attack is symmetric
- Discusses answer set programming connection — principle from [22] about critical attacks
- Example 10: Shows their approach handles the critical attack principle correctly

## NEXT
Read pages 24-35 (conclusion, proofs in appendix). Then write all paper artifacts.

