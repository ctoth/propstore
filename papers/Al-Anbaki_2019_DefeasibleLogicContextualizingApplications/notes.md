---
title: "A Defeasible Logic-based Framework for Contextualizing Deployed Applications"
authors: "Noor Sami Al-Anbaki, Nadim Obeid, Khair Eddin Sabri"
year: 2019
venue: "International Journal of Advanced Computer Science and Applications (IJACSA), Vol. 10, No. 9, pp. 176-186"
affiliation: "King Abdullah II School for Information Technology, University of Jordan, Amman, Jordan"
pages: 11
doi_url: null
citation: "Al-Anbaki, N. S., Obeid, N., & Sabri, K. E. (2019). A Defeasible Logic-based Framework for Contextualizing Deployed Applications. (IJACSA) International Journal of Advanced Computer Science and Applications, 10(9), 176-186."
---

# A Defeasible Logic-based Framework for Contextualizing Deployed Applications

## One-Sentence Summary

A four-tuple defeasible-logic theory `L = ⟨G, β, D, λ⟩` (Triggers, Concerns, Domain rules, Priorities) for layering contextual reasoning on top of an *already-deployed* application without re-architecting it, supporting multiple administrative authorities, conflicting concerns, and dynamic context — with derivation tags `+Δ / −Δ / +δ / −δ` inherited from Antoniou-style ambiguity-blocking defeasible logic.

## Problem Addressed

Deployed applications are typically built on classical / monotonic logic and assume a single administrative authority. They cannot easily adapt to ubiquitous environments where:
- multiple (possibly competing) authorities supply context;
- sensors and stakeholders contribute partial, conflicting information;
- rules themselves may need to be added/removed/changed at runtime (e.g., emergency "break-glass");
- new evidence may force *retraction* of previously inferred conclusions.

Existing frameworks (Henricksen-style context modelling, CONON / SOUPA ontologies, Schilit, Dey toolkits) either don't scale to multi-authority settings, can't tolerate inconsistency, or only describe the *integration* of context without giving the deployed system a uniform reasoning surface over its context providers. *(p.176-178, p.180)*

## Key Contributions

1. **Augments deployed applications post-hoc.** The framework wraps an existing rule base `Cᵘ` with contextual extensions `Cʰ` and observational triggers `Cᵒ`, *without* requiring the original system to be redesigned. *(p.181)*
2. **Concern-based context model.** Stakeholder *concerns* `β` are first-class — separate from rules and facts — so each authority's contribution is scoped by the concern it serves and conflicting concerns can coexist. *(p.181-182)*
3. **Distributed multi-authority reasoning.** Each authority contributes its own slice of the domain rule-base `D = D^A ∪ D^B ∪ …` and its own priorities `λ`; conflicts across authorities are mediated by the global superiority relation, preserving consistency through ambiguity-blocking DL. *(p.182)*
4. **Three-layer "spectrum of context"** — observational `Cᵒ`, undertaken `Cᵘ`, hidden `Cʰ` — clarifies provenance of every contextual attribute. *(p.181, Fig. 2)*
5. **Standard derivability tags lifted intact.** Derivation conditions `+Δ`, `−Δ`, `+δ`, `−δ` (definite-provable, definite-rejected, defeasibly-provable, defeasibly-rejected) are reused from Antoniou et al. so existing DL theorem-proving machinery applies directly to `L`. *(p.183)*
6. **Worked illustrative analysis.** The phone-call management scenario is fully formalised as a `⟨G^A, β^A, D^A, λ^A⟩` for the anti-disturbance authority plus `⟨G^B, β^B, D^B, λ^B⟩` for personal-preference authorities, showing how `>` resolves international-vs-unknown conflicts. *(p.179-180, p.184)*

## Methodology

Theoretical / formal. Builds on classical Defeasible Logic (Nute 1994; Antoniou, Maher & Billington 2000) over first-order ground literals — FOPC plus the defeasible implication `⇒`, defeater arrow `⤳`, and ambiguity-blocking priority `>`. The classical DL triple `⟨F, R, >⟩` is generalised to a four-tuple `⟨G, β, D, λ⟩`. Demonstrated on a single illustrative scenario — a university phone-call management application — and analysed with the standard `±Δ / ±δ` proof system. *(p.179, p.183-184)*

## Key Equations / Definitions

### Classical Defeasible Logic (background)

A defeasible theory is a triple
$$
D = \langle F, R, > \rangle
$$
Where:
- `F`: finite set of literals representing indisputable statements (Facts).
- `R = R_s ∪ R_d ∪ R_f`: strict rules, defeasible rules, defeaters.
- `> ⊆ R_d × R_d`: superiority relation; acyclic (transitive closure irreflexive).
*(p.179)*

Generic rule form
$$
R: \mathrm{Ant}(R) \;\bullet\!\!\to\; \mathrm{Conseq}(R)
$$
Where `R` is a unique label, `Ant(R)` is a conjunction of literals, `•→` is one of `→` (strict), `⇒` (defeasible), `⤳` (defeater), and `Conseq(R)` is the head. `R[B]` denotes the rules in `R` with consequent `B`. *(p.179)*

Canonical examples:
- Strict — `R₁: equatorial(X) ∧ during_summer(X) → very_hot(X)` *(p.179)*
- Defeasible — `R₂: coastal(X) ∧ during_summer(X) ⇒ very_hot(X)` *(p.179)*
- Conflicting — `R₃: raining_at(X) ∧ during_summer(X) ⇒ ¬very_hot(X)` *(p.179)*
- Defeater — `R₂': coastal(X) ∧ during_spring(X) ⤳ ¬very_hot(X)` *(p.179)*
- Priority — `R₃ > R₂` lets `¬very_hot` win in coastal+rainy+summer. *(p.179)*

### Proposed framework

$$
L = \langle G, \beta, D, \lambda \rangle
$$
*(p.181)*

#### A. Triggers `G`
Finite set of positive/negative ground literals representing **external basic contextual attributes** acquired from the application domain. Imported from the system's *global* knowledge — not necessarily known to participating entities. May be issued by multiple sub-domains/authorities.

Constraint: a valid framework has **no two complementary triggers** — there is no `α` such that both `α ∈ G` and `¬α ∈ G`.

A trigger's effect can extend beyond a single rule — it can add/remove/change rules and regulations across components (e.g., emergency situations triggering a break-glass procedure). *(p.181)*

#### B. Concerns `β` (the base system)
A **base system** is the actual deployed application — defined by rules that reflect obligations, set at design time to achieve a purpose. A concern is the slice of the rule base owned by one administrative authority for one purpose.

Formally, the base system in the proposed notation is associated with:
- a non-contextual baseline rule set acquired before context is integrated;
- a set of **static, non-conflicting** rules `Cᵘ` (the "undertaken" slice of the spectrum of context);
- a concern label that can be referenced when adding contextual rules.

Each concern represents a coherent stakeholder viewpoint — e.g., the deployer's anti-disturbance concern in the phone scenario, the user's personalisation concern. Concerns can be **compatible**, **orthogonal**, or **crosscutting** with respect to one another, and the same contextual attribute can be re-used across concerns. *(p.181-182)*

#### C. Domain Knowledge `D`
The aggregated rule base, partitioned by authority/concern:
$$
D = D^{A} \cup D^{B} \cup \cdots
$$
where `D^A`, `D^B`, … are the contextual rule-sets contributed by distinct authorities. Each `D^X` may include strict, defeasible, and defeater rules that extend or override the base system's `Cᵘ`. *(p.182)*

The integration discipline is concern-driven: when collected contextual knowledge belongs to a *crosscutting* concern or is owned by a *different* administrative authority, it is encapsulated in a separate sub-theory rather than being merged into the base system's rule set. Consistency of the integrated theory is then attained by the standard defeasible-theory machinery rather than by manual conflict resolution. *(p.182)*

#### D. Priorities `λ` (superiority relation)
A binary priority relation over the union of defeasible rules in `D`. `λ` is **statically defined** by the participating authorities (and is therefore part of the design-time configuration of the augmented system). It enables resolution of conflicts that arise both *within* an authority's rule set and *across* authorities' rule sets.

Like classical DL's `>`, `λ` is acyclic and its transitive closure is irreflexive. *(p.179, p.182)*

### Spectrum of Context (Fig. 2, p.181)

Three concentric layers inside the system's domain knowledge `C`:
- `Cᵒ` — **observational** context: arrives through sensors / external sources.
- `Cᵘ` — **undertaken** context: locally rule-governed knowledge owned by the deployed application; static design-time semantics.
- `Cʰ` — **hidden** context: embedded contextual knowledge attached to the running system either implicitly or explicitly; can re-contextualize the base rules when added by the same authority and serving the same concern.

### Contextual attribute taxonomy (p.180-181)

| Axis | Categories |
|------|-----------|
| How gathered | **Basic** (direct sensor) vs. **Complex** (logically constructed) |
| How manipulated | **Internal** (within the entity/admin domain) vs. **External** (outside) |

Examples:
- Basic: `Humidity(basement, 40%)`, `Temperature(basement, 65 F)`. *(p.181)*
- Complex: `Humidity(basement,40%) ∧ Temperature(basement,65F) ⇒ Comfortable(basement)`. *(p.181)*
- Conflict resolution by priority: `Noise(basement, 120 dB) ⇒ ¬Comfortable(basement)` overrides comfort. *(p.181)*

### Derivation conditions (Section VIII, Illustrative Proof, p.183)

A **proof in `D`** is a finite sequence `P = (P[1], …, P[n])` where each step `P[i]` is a tagged literal of one of four forms `+Δq`, `−Δq`, `+δq`, `−δq`. The conditions follow Antoniou-Maher-Billington 2000 verbatim:

**Definite provability:**
- `+Δq` ∈ P[i+1] iff
  - (1) `q ∈ F`, or
  - (2) ∃ `R ∈ R_s[q]` such that ∀ `a ∈ Ant(R)`, `+Δa ∈ P[1..i]`.
- `−Δq` ∈ P[i+1] iff
  - (1) `q ∉ F`, and
  - (2) ∀ `R ∈ R_s[q]`, ∃ `a ∈ Ant(R)` with `−Δa ∈ P[1..i]`.

**Defeasible provability:**
- `+δq` ∈ P[i+1] iff either `+Δq ∈ P[1..i]` (already definitely proved); or
  - (1) `−Δ¬q ∈ P[1..i]` (the complement is definitely rejected), and
  - (2) ∃ `R ∈ R_s[q] ∪ R_d[q]` such that ∀ `a ∈ Ant(R)`, `+δa ∈ P[1..i]`, and
  - (3) for every conflicting rule `R' ∈ R[¬q]`, either some `a' ∈ Ant(R')` has `−δa' ∈ P[1..i]`, or there exists `R'' ∈ R_s[q] ∪ R_d[q]` with `R'' > R'` whose antecedents are all defeasibly provable.
- `−δq` ∈ P[i+1] iff `−Δq ∈ P[1..i]` and:
  - (1) ∀ `R ∈ R_s[q] ∪ R_d[q]`, ∃ `a ∈ Ant(R)` with `−δa ∈ P[1..i]`, or
  - (2) `+Δ¬q ∈ P[1..i]`, or
  - (3) ∃ `R' ∈ R[¬q]` such that ∀ `a' ∈ Ant(R')`, `+δa' ∈ P[1..i]`, and for no `R ∈ R_s[q] ∪ R_d[q]` is `R > R'` with antecedents defeasibly provable.
*(p.183)*

These four tags are the proof certificates the framework outputs — they are the "justifiable decisions" promised by Section IV.

## Illustrative Scenario — Full Formalisation

**Setting** — a smart phone-call management application installed on University-of-Jordan lecturers'/employees' mobiles, filtering calls during online lectures based on the *identity* of the caller (urgent / unknown) and *location* of the call (international / local). *(p.179-180, p.184)*

**Original base-system rules** (deployer Sami's anti-disturbance concern `Cᵘ`):
1. If caller is on the urgent list → phone rings.
2. If call is international → phone rings.
3. If caller is unknown → phone does not ring.

**Conflict** — a caller can be simultaneously *unknown* and *international*. Sami sets a base-system priority making international beat unknown ⇒ phone rings. *(p.180)*

**Augmentation (formal phase, p.184).**

Anti-disturbance authority `A`:
- `G^A = {calling(X), urgent_list(X), international(X), unknown(X), …}`
- `β^A = {anti-disturbance}`
- `D^A` collects the three base rules above as defeasible rules.
- `λ^A` orders international > unknown.

Personalisation authority `B` (a particular user — e.g., role-based, location-based, or schedule-based override):
- `G^B` extends with attributes from three context providers (role, location/proximity, schedule).
- `β^B` declares a personal-preference concern.
- `D^B` adds rules of the form
  $$
  \mathrm{role}(X, \text{manager}) \wedge \mathrm{calling}(X) \;\Rightarrow\; \mathrm{ringing}(X)
  $$
  and analogous rules for proximity (`location("university", near)`) and meeting schedule.
- `λ^B` declares user-side priorities (e.g., manager-call beats anti-disturbance for one user; library-meeting context suppresses ring for another).

**Cross-authority resolution.** Conflicts between `D^A` and `D^B` are resolved by the global `λ`, which makes the augmented theory's verdict explicit: e.g., a manager-international call to a user inside the library will or will not ring depending on whether `λ` ranks `B`'s library-suppress rule above `A`'s international rule. The `±δ` derivation conditions then certify the verdict. *(p.184)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Classical DL theory | `D = ⟨F,R,>⟩` | — | — | — | 179 | Background |
| Proposed framework theory | `L = ⟨G,β,D,λ⟩` | — | — | — | 181 | The four-tuple |
| Rule classes | `R_s, R_d, R_f` | — | 3 | strict / defeasible / defeater | 179 | `R = R_s ∪ R_d ∪ R_f` |
| Spectrum-of-context layers | `Cᵒ, Cᵘ, Cʰ` | — | 3 | observational / undertaken / hidden | 181 | Fig. 2 |
| Superiority relation property | `>` / `λ` | — | acyclic | irreflexive transitive closure | 179, 182 | Conflict resolution |
| Trigger consistency constraint | — | — | — | no `α` and `¬α` both in `G` | 181 | Validity |
| Domain partition | `D = ⋃ D^X` | — | per-authority | one part per concern/authority | 182 | Distributed reasoning |
| Concern-relationship kinds | — | — | 3 | compatible / orthogonal / crosscutting | 181 | Integration discipline |
| Derivation tags | `±Δ, ±δ` | — | 4 | definite-prov, definite-rej, def-prov, def-rej | 183 | Antoniou-Maher-Billington 2000 |
| Phone scenario authorities | `A, B` | — | 2 | anti-disturb / personalisation | 180, 184 | Illustrative scenario |
| Phone scenario triggers (sample) | — | — | — | calling, urgent_list, international, unknown, role, location, meeting | 184 | `G^A`, `G^B` |

## Methods & Implementation Details

- **Knowledge representation** — first-order ground literals with name+value, e.g. `location("university", near)`, `role("mary", manager)`, `connected_users(5)`. `¬α` is the complement of atom `α`. *(p.181)*
- **Reasoning machinery** — ambiguity-blocking defeasible logic with the standard four-tag proof system (`+Δ, −Δ, +δ, −δ`). *(p.183)*
- **Distributed reasoning** — each authority contributes its own `(G^X, β^X, D^X, λ^X)`; cross-authority conflicts resolved by the union priority `λ = ⋃ λ^X` extended with cross-authority entries. *(p.182, p.184)*
- **Trigger semantics are meta-level.** A trigger may add/remove/change rules in `D` (e.g., emergency break-glass) — not just enable a derivation step. *(p.181)*
- **Concern-based encapsulation** — when added knowledge is crosscutting or comes from a different authority, it is encapsulated in its own concern slice rather than merged into the base. Consistency is preserved by the defeasible-theory machinery, not by hand-resolving conflicts. *(p.182)*
- **Pseudo-code / algorithmic procedure** — none provided. The proof system in §VIII is the operational specification. *(p.183)*

## Figures of Interest

- **Fig. 1 (p.179)** — Classical Defeasible Logic. Block diagram: Facts feed into Strict / Defeasible / Defeater rules; output passes through a `>`-resolver and emerges as a Justifiable Decision.
- **Fig. 2 (p.181)** — Spectrum of Context. Concentric regions inside Domain Knowledge `C`, with arrows for `Cᵒ` (sensor-input), `Cᵘ` (locally undertaken), `Cʰ` (hidden / embedded).

## Results Summary

The paper is purely formal/illustrative. Its "result" is the worked phone-call scenario in which:
- Sami's base-system priority `international > unknown` correctly produces `+δ ringing(X)` when caller is both international and unknown. *(p.180, p.184)*
- A user-side concern `B` can introduce a stronger rule (e.g., `meeting(library) ⇒ ¬ringing(X)`) that, if `λ` ranks it above `A`'s rules, produces `+δ ¬ringing(X)` even for international calls — and the proof system makes the verdict justifiable. *(p.184)*
- The framework therefore satisfies the design goal of letting deployed-application behaviour adapt per-user without re-architecting the deployed application itself.

## Limitations

- **No empirical evaluation.** A single hand-worked scenario; no implementation, no benchmarks, no scalability data. *(p.185, "Future Work")*
- **Static priorities.** `λ` is set at design time by participating authorities. Run-time priority *learning* / dynamic re-prioritisation is left as future work. *(p.185)*
- **No revision semantics.** When new triggers contradict prior rules, the framework's response is the proof-system's `−δ` outcome, not AGM-style belief revision. The authors note "future work could investigate revision of defeasible rules." *(p.185)*
- **Trust / authentication of authorities is out of scope.** The framework assumes participating authorities are well-formed; malicious or Byzantine authorities are not addressed. *(p.185)*
- **No worked treatment of concern-relationship classification.** Compatible/orthogonal/crosscutting are described informally; no decision procedure for placing two concerns into one of the three buckets is given. *(p.181)*

## Arguments Against Prior Work

- **Classical/monotonic logic frameworks** "neither scale well nor can be used in environments with multiple administrative authorities" — they require global consistency. *(p.179)*
- **Ontology-based context-awareness** (CONON, SOUPA family) "ignore the significance of generic frameworks for manipulating context flow in smart environments." *(p.178)*
- **Henricksen-style context modelling** [10][11] handles context capture but not behavioural adaptation under conflicting context. *(p.178)*
- **Bikakis & Antoniou** non-monotonic distributed reasoning [16][22] *characterises* contextual reasoning rather than *applying* it; their AGENTS-style cooperation model differs from the deployed-application setting. *(p.178)*
- **Schilit / Dey toolkits** [27][28] support rapid prototyping but bake context-aware behaviour into bespoke applications rather than offering a uniform reasoning surface above the application. *(p.178)*
- **Earlier concern-based context approaches (Sami)** "discuss how to enhance deployed applications using context. Rather than considering it under the uniform interface where all of the context-providers are attached to a reasoner where all the reasoning methods can be employed." *(p.180)*
- **Probabilistic / Bayesian context reasoning** is not chosen because it lacks the natural-language affordance of rules and obscures *why* a decision was made; the authors prefer DL because it is "expressive, natural, not ambiguous and programmable." *(p.178)*

## Design Rationale

- **Why defeasible logic (not classical FOL or probabilistic)?** Skeptical non-monotonic reasoning supports retractable conclusions, a hard requirement for ubiquitous environments. DL is "expressive, natural, not ambiguous and programmable." *(p.178)*
- **Why ambiguity-blocking specifically?** Preserves consistency under conflict and gives a deterministic answer through `>` / `λ` rather than committing to multi-extension semantics. *(p.179)*
- **Why a separate concerns layer `β`?** Decouples stakeholder concerns from rules so the same rule can support different decisions under different active concerns; required for multi-authority distributed reasoning. *(p.181-182)*
- **Why the three-layer `Cᵒ / Cᵘ / Cʰ` spectrum?** Makes provenance explicit at the formalism level — the system can reason about the *source* of a contextual attribute, not just its truth. *(p.181)*
- **Why static priorities `λ`?** Authors deliberately avoid run-time priority shuffling because it would compromise the justifiability guarantees of the proof system. *(p.182, p.185)*
- **Why per-authority `D^X`?** Encapsulating each authority's contribution prevents one authority's bugs/conflicts from invalidating another's reasoning, in line with software-engineering separation of concerns. *(p.182)*

## Testable Properties

- **(P1) Trigger consistency.** For every `α`: `α ∈ G ⇒ ¬α ∉ G`. *(p.181)*
- **(P2) Acyclic priority.** `λ` is acyclic; transitive closure of `λ` is irreflexive. *(p.179, p.182)*
- **(P3) Strict undefeatable.** Conclusions of strict rules cannot be defeated by any number of defeasible rules. *(p.179, p.183)*
- **(P4) Defeater non-supporting.** Defeaters never produce a `+δ` conclusion on their own; they only block. *(p.179)*
- **(P5) Proof-tag exclusivity.** For a literal `q`, `+Δq` and `−Δq` cannot both occur in a valid proof; same for `+δq` and `−δq`. *(p.183, by construction)*
- **(P6) Definite ⇒ defeasible.** `+Δq ∈ P` entails `+δq ∈ P` (definite provability subsumes defeasible). *(p.183, condition (1) of `+δ`)*
- **(P7) Cross-authority conflicts handled.** For any `α ∈ Conseq(D^A)` and `¬α ∈ Conseq(D^B)`, the augmented theory produces exactly one of `+δα`, `−δα`, `+δ¬α`, `−δ¬α` per the proof system, never two contradictory `+δ` tags. *(p.183-184)*
- **(P8) Trigger meta-effect.** A trigger may add/remove rules; an implementation must re-derive over the updated `D` rather than caching old derivations. *(p.181)*
- **(P9) Concern encapsulation.** Adding `D^B` for a new authority should not change the set of conclusions provable inside `D^A` *unless* a cross-authority `λ` entry is added. *(p.182, claim about concern encapsulation)*
- **(P10) Phone scenario verdicts.** Worked example: `international(X) ∧ unknown(X) ⇒ +δ ringing(X)` under base priorities; under user `B` with `meeting(library) ⇒ ¬ringing` of higher priority, the verdict flips to `+δ ¬ringing`. *(p.184)*

## Relevance to Project

**High.** The paper is squarely in propstore's contextualisation lane and offers near-direct vocabulary for several existing modules:

- The `L = ⟨G, β, D, λ⟩` shape mirrors propstore's separation of **contexts** (`ist(c, p)` qualifiers, structured assumption documents), **concerns / perspective** (the `perspective` field on context documents), **domain rule bases** (DeLP rules per paper / per context), and **superiority** (mapped to ASPIC+ rule priorities and CKR-style justifiable exceptions in `propstore.defeasibility`).
- The `Cᵒ / Cᵘ / Cʰ` spectrum gives a literature-grade phrasing for propstore's distinction between **observed** (sensor-acquired or imported) attributes, **rule-governed** local knowledge, and **embedded contextual knowledge** added by the same authority (compare propstore's source-branch finalize/promote chain with hidden-context publication).
- The trigger-consistency constraint (P1) and the acyclic-priority constraint (P2) are properties propstore should already enforce, but the explicit citations are useful for tightening those test surfaces in `propstore.belief_set` and `propstore.aspic_bridge`.
- The paper's `±Δ / ±δ` proof system is exactly the certificate format propstore's `query_claim()` / `build_arguments_for()` should be producing for backward-chaining queries.
- The argument **against probabilistic context reasoning** is congenial to propstore's "honest ignorance over fabricated confidence" principle — one more anchor for that design stance.
- The paper's distributed multi-authority story is a near-direct cite for propstore's per-paper context bridges (lifting rules in `research-papers:author-lifting-rules`) and for the import-with-provenance principle in `feedback_imports_are_opinions.md`.

**Where it falls short for propstore:**
- No revision (AGM/IC) — propstore already has `propstore.belief_set.ic_merge` and AGM modules that go beyond.
- No probabilistic argumentation — propstore's subjective-logic / Jøsang opinion algebra is orthogonal and out-of-scope here.
- No formal extension semantics (Dung AF, ASPIC+) — propstore goes considerably further on this axis.

## Open Questions

- [ ] Can `λ` be derived (rather than declared) from concern-relationship classification (compatible/orthogonal/crosscutting)? Useful follow-up for propstore's lifting-rule authoring.
- [ ] How does `L` interact with AGM revision when `G` itself changes contradictorily over time? Authors note as future work; propstore's `belief_set` work could supply the answer.
- [ ] Is there a normal-form / decidability result for `L` analogous to Antoniou's complexity bounds for plain DL?
- [ ] Concrete decision procedure for compatible/orthogonal/crosscutting concern classification — currently informal.
- [ ] Implementation: any plans for a tool / DSL? (Authors mention future work but no link/code.)

## Related Work Worth Reading

- Antoniou, Maher & Billington (2000), "Defeasible logic versus logic programming without negation as failure," *J. Logic Programming* 42(1):47-57. **Ref [38] — canonical proof-tag system used here.** → NOW IN COLLECTION: [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md)
- Bikakis & Antoniou — "Defeasible Contextual Reasoning with Arguments in Ambient Intelligence." **Refs [16][22] — closest competitor for distributed DL.** → NOW IN COLLECTION: [Defeasible Contextual Reasoning with Arguments in Ambient Intelligence](../Bikakis_2010_DefeasibleContextualReasoningArguments/notes.md)
- Henricksen, Indulska — context modelling for pervasive computing. **Refs [10][11].**
- Governatori, Olivieri, Scannapieco & Cristani (2012) — "Revision of defeasible logic preferences" arXiv:1206.5833. **Ref [24] — directly addresses the static-priority limitation called out above.** → NOW IN COLLECTION: [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md)
- Dastani, Governatori, Rotolo, Song, Van Der Torre (2007) — "Contextual agent deliberation in defeasible logic." **Ref [34] — agent-side companion of this framework.** → NOW IN COLLECTION: [Contextual Agent Deliberation in Defeasible Logic](../Dastani_2007_ContextualAgentDeliberationDefeasible/notes.md)
- Uddin, Rakib, Haque, Vinh (2018) — "Modeling and reasoning about preference-based context-aware agents over heterogeneous knowledge sources," *Mobile Networks and Applications* 23(1):13-26. **Ref [32] — peer of this paper, also targeting heterogeneous sources.**
- García & Simari (2014) — "Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers," *Argument & Computation* 5(1):63-88. **Ref [40] — DeLP execution model directly relevant to propstore's backward-chaining queries.** → NOW IN COLLECTION: [Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers](../García_2014_DefeasibleLogicProgrammingDeLP-servers/notes.md)
- Nute (1994) — defeasible logic foundations.
- Antoniou, Billington, Governatori & Maher (2001) — "Representation results for defeasible logic," *ACM TOCL* 2(2):255-287. **Ref [13] — representation-theoretic grounding for the proof system.** → NOW IN COLLECTION: [Representation Results for Defeasible Logic](../Antoniou_2000_RepresentationResultsDefeasibleLogic/notes.md)

## Quotes Worth Preserving

- *"It is fair to say that the ubiquitous computing paradigm revolutionized our understanding of computing and what it can deliver. It morphs computer devices and sensors in an environment with the aim of providing the user with enhanced accessibility to information resources. The advances of context-aware applications easily represent and manage different behaviors of the application in different contexts."* (p.176)
- *"Augmenting such a system with context awareness can considerably improve its functionality by making it adaptable to the processing environment in order to provide a better experience to the user, better utilization of resources, etc."* (p.181)
- *"A context-aware system should be carefully designed to permit distributed reasoning and at the same time make justifiable decisions in spite of the fact that the distributed entities might have conflicting concerns."* (p.181)
- *"Defeasible logic [DL] [22] is a well-known skeptical nonmonotonic logic that can be used in dynamic environments due to its characteristics: it is expressive, natural, not ambiguous and programmable. It has attracted many researchers to incorporate it in different application domains such as modelling of contracts [23], legal reasoning [24], modelling social agents [25], modelling social commitments [15] [17] [18], etc."* (p.178)

---

## Workflow Checkpoint (paper-reader skill, in-progress)

**State of the world:**
- All 11 page images read (page-000.png … page-010.png).
- `notes.md` (this file) — written, exhaustive across all sections of the paper.
- `metadata.json` — written.
- `description.md` — written with five tags: `defeasible-reasoning`, `context-logic`, `distributed-reasoning`, `nonmonotonic-reasoning`, `knowledge-representation` (all confirmed present in existing collection-wide tag set).
- `abstract.md` — *next* (verbatim text from page-000.png plus our interpretation).
- `citations.md` — *next* (full reference list from pp.9-10, refs [1]-[40]).
- `reconcile` skill — pending after citations.
- `papers/index.md` update — pending after reconcile.

**Observations worth recording:**
- The collection already uses tag `context-logic` (Bozzato_2020_DatalogDefeasibleDLLite vicinity) and `distributed-reasoning` — both ideal fits.
- The reference list in pp.9-10 is dense (40 entries) with several refs already in the collection (Antoniou, Bikakis, Governatori, García/Simari) — reconcile should produce healthy bidirectional links.
- The paper's IJACSA URL is the canonical landing page; no DOI is stamped in the PDF.

**Current blocker:** none. Continuing with abstract.md and citations.md.

### Checkpoint (reconcile in-progress, post-cross-reference write)

- All paper artifacts written: notes.md (this file), metadata.json, description.md, abstract.md, citations.md.
- Reconcile Step 1 (validate) — done.
- Reconcile Step 2 (forward cross-references) — done. Confirmed direct citation of McCarthy_1993_FormalizingContext (ref [19]). Eleven new leads recorded.
- Reconcile Step 3 (reverse cited-by) — done. `grep -rl "Al-Anbaki" papers/` returned no hits → "Cited By" section is `(none found)`.
- Reconcile Step 4 (conceptual links) — done. Strong: Bozzato_2018, Bozzato_2020, Ghidini_2001. Moderate: Giunchiglia_1994, Kallem_2006, McCarthy_1997, Morris_2020, Goldszmidt_1992, Fang_2025.
- **Pending:** Reconcile Step 4.5 (bidirectional annotation in the three Strong-link target papers); Reconcile Step 5 (no citing papers, so trivially nothing to reconcile); Step 6 (report); then Step 8 of the parent paper-reader skill (`papers/index.md` update).
- **Observation worth recording:** No collection paper currently cites Al-Anbaki et al. 2019 — this paper enters the collection as a fresh contributor rather than a fulfilled lead.
- **Blocker:** none. Proceeding to bidirectional annotation in Bozzato_2018, Bozzato_2020, and Ghidini_2001.

### Checkpoint (post-bidirectional, pre-index)

- **Bidirectional Conceptual-Links annotation done** in all three Strong-link target papers:
  - `papers/Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md` — appended a "Concern-based / multi-authority defeasible context" subsection naming this paper.
  - `papers/Bozzato_2020_DatalogDefeasibleDLLite/notes.md` — appended an Al-Anbaki entry to the existing Conceptual Links list.
  - `papers/Ghidini_2001_LocalModelsSemanticsContextual/notes.md` — created a new `## Collection Cross-References` section with the Al-Anbaki conceptual link (the file had no prior cross-ref section).
- **Reverse cited-by:** confirmed by grep — no collection paper cites Al-Anbaki et al. 2019.
- **Stylistic note worth recording:** existing Bozzato notes use `[[wikilink]]` style for cross-paper refs; the reconcile spec mandates markdown links. I followed the spec for the new entries (markdown links pointing at `../<dir>/notes.md`) — this is the format propstore wants going forward, even though it visually diverges from the older wikilink entries already present in those files.
- **Index format observation:** `papers/index.md` predominantly uses `## Dir_Name  (tags)\nbody` — not the markdown-link header form the skill spec defines. The skill spec's stricter form (`## [<pretty title>](<dir>/notes.md)  (tags)`) is more useful for navigation, so I'll use it for the new entry. Skill says use markdown links; index.md is the natural place to demonstrate that.
- **Sort key:** ASCII `Al-` < `Alf` (because `-` (0x2D) < `f` (0x6C)), so the new entry slots between Aarts_2015 and Alfano_2017.
- **Pending step:** insert the entry at line 4 of `papers/index.md`.
- **Blocker:** none.

## Collection Cross-References

### Already in Collection

- [Notes on Formalizing Context](../McCarthy_1993_FormalizingContext/notes.md) — cited as ref [19]; the canonical `ist(c, p)` source whose context formalisation this paper extends with defeasible rules and concerns.

### Now in Collection (previously listed as leads)

- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — cited as ref [24]; directly addresses the static-priority limitation this paper acknowledges as future work. Provides the eight auxiliary proof tags, NP-completeness result, three canonical revision cases, and AGM-postulate audit for `>`-only revision in DL.
- [Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers](../García_2014_DefeasibleLogicProgrammingDeLP-servers/notes.md) — cited as ref [40]; the DeLP-Server execution model with contextual-query operators ⊕ ⊗ ⊖ over (Π, Δ) program pairs, four-valued answers (YES/NO/UNDECIDED/UNKNOWN), and δ-Explanation as a triple of marked dialectical trees. The closest computational precedent for context-aware defeasible query execution that this paper's L = ⟨G, β, D, λ⟩ multi-authority architecture extends. Directly relevant to propstore's `query_claim()` / `build_arguments_for()` backward-chaining surface.
- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — cited as ref [38]; the canonical source of the `±Δ / ±∂` proof-tag system this paper reuses verbatim. Provides Theorem 4.1 (LPwNF ⊆ DL under translation `T(P)`), the team-of-rules trumping argument (Example 3, platypus) showing DL is strictly stronger than sceptical LPwNF, Theorem 5.1 embedding courteous logic programs into DL, and the boundary marker that priority logic (Wang/You/Yuan) is in a different school because it propagates ambiguity. Load-bearing upstream cite for `propstore.defeasibility` and any propstore work that wants formal grounding for defeasible derivation tags.
- [Propositional Defeasible Logic has Linear Complexity](../Maher_2001_PropositionalDefeasibleLogicLinearComplexity/notes.md) — cited as ref [15]; supplies the O(N) inference algorithm (Theorem 5) and linear-blowup `Basic` transformations (Theorem 4) for the four-tag DL system this paper reuses. The complexity ceiling Al-Anbaki et al.'s `L = ⟨G, β, D, λ⟩` framework inherits when grounded in propositional DL. Algorithmic counterpart to Antoniou_2000_Representation's representation result; the implementation pseudocode (Figure 1) and rule data structure (Figure 2) are the canonical reference for propstore's DL evaluator.
- [Contextual Agent Deliberation in Defeasible Logic](../Dastani_2007_ContextualAgentDeliberationDefeasible/notes.md) — cited as ref [34]; the agent-side companion of this framework. Extends DL with modal operators (BEL, OBL, INT, DES), an ⊗-on-rules connective Q (literal-PREF lifted to whole rules), and a meta-rule layer R^C whose consequents are themselves rules. Conversions c ⊆ MOD × MOD allow one modality's rule to act as another's, and proof procedures with new tags ±Δ_C^{▷X} / ±∂_C^{▷X} let the agent defeasibly derive *which rules-for-goals fire in the current context* before applying them. Two worked examples (Frodo agent, office-assistant context detection) show context-driven rule selection. Together with Al-Anbaki et al. 2019 it covers the full storage-plus-deliberation contract: Al-Anbaki says *what* a contextualised KB stores; Dastani et al. say *how* an agent picks among rules in a given context.

### New Leads (Not Yet in Collection)

- ~~**Bikakis & Antoniou (2010) — "Defeasible contextual reasoning with arguments in ambient intelligence," *IEEE TKDE* 22(11):1492-1506.** Ref [16]. The closest competitor to this framework on multi-context distributed defeasible reasoning.~~ → **Now in Collection** as [Defeasible Contextual Reasoning with Arguments in Ambient Intelligence](../Bikakis_2010_DefeasibleContextualReasoningArguments/notes.md). Confirms the lead's framing as the closest competitor: provides MCS extended with local defeasible theories, defeasible mapping rules, and per-context total preference orderings; argumentation semantics over Dung-style attack/defeat with context-preference comparison; sound/complete/terminating P2P_DR distributed algorithm. Authors explicitly position the work as a *characterisation* of distributed defeasible reasoning rather than a deployed-application framework, exactly the gap Al-Anbaki et al. identify and try to close with `L = ⟨G, β, D, λ⟩`. Total-ordering and propositional-only limitations of Bikakis & Antoniou are precisely what Al-Anbaki's per-concern `D^X` partition and `λ`-driven authority structure try to relax along a different axis.
- **Bikakis & Antoniou (2008) — "Distributed defeasible contextual reasoning in ambient computing," in *Ambient Intelligence*, pp. 308-325.** Ref [22]. Earlier paper from the same line; pairs with [16].
- ~~**Governatori, Olivieri, Scannapieco & Cristani (2012) — "Revision of defeasible logic preferences," arXiv:1206.5833.** Ref [24]. Directly addresses the static-priority limitation Al-Anbaki et al. acknowledge as future work.~~ → **Now in Collection** as [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md). Confirms the lead's framing: the paper provides eight new auxiliary proof tags ($\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$) for locating where superiority changes can flip a defeasible conclusion, proves NP-completeness of the `>`-revision decision problem via 3-SAT reduction, enumerates three canonical revision cases, and audits the resulting operators against the AGM postulates — finding only some hold and that both Levi and Harper identities fail. Direct successor to this paper's static-priority limitation.
- ~~**Dastani, Governatori, Rotolo, Song & Van Der Torre (2007) — "Contextual agent deliberation in defeasible logic," *Pacific Rim Multi-Agents*, pp. 98-109.** Ref [34]. Agent-side companion of this framework.~~ → **Now in Collection** as [Contextual Agent Deliberation in Defeasible Logic](../Dastani_2007_ContextualAgentDeliberationDefeasible/notes.md). Confirms the lead's framing as the agent-side companion: provides modal-DL extension (BEL/INT/DES/OBL), the ⊗-on-rules connective Q (PREF lifted from literals to rules), and the meta-rule layer R^C whose consequents are themselves rules — together giving proof procedures for which rules-for-goals fire under contextualised conditions. Conversions c ⊆ MOD × MOD let one modality's rule act as another's. Two worked examples (a Frodo agent and an office-assistant context-detector) illustrate context-driven rule selection. Closes the agent-side gap Al-Anbaki et al. 2019 leave open: their `L = ⟨G, β, D, λ⟩` says *what* the contextualised KB stores; Dastani et al. 2007 say *how* an agent picks among rules in a given context.
- ~~**García & Simari (2014) — "Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers," *Argument & Computation* 5(1):63-88.** Ref [40]. DeLP-server execution model directly relevant to propstore's `query_claim()` / `build_arguments_for()` backward-chaining surface.~~ → **Now in Collection** as [Defeasible logic programming: DeLP-servers, contextual queries, and explanations for answers](../García_2014_DefeasibleLogicProgrammingDeLP-servers/notes.md). Confirms the lead's framing: the paper formalises three concrete merge operators ⊕ ⊗ ⊖ over (Π, Δ) program pairs (private-wins / public-wins / subtract) for contextual queries, defines δ-Explanations as the triple of marked dialectical trees `(T*_U(Q), T*_U(Q̄), T*_D(Q))` returned alongside a four-valued answer (YES / NO / UNDECIDED / UNKNOWN), and establishes the DeLP-Server architecture as the per-query merge mechanism that Al-Anbaki's L = ⟨G, β, D, λ⟩ generalises with multi-authority concerns.
- **Buvac & Mason (1993) — "Propositional logic of context," *AAAI*, pp. 412-419.** Ref [20]. Companion to McCarthy [19] for the propositional layer of `ist`.
- **Giunchiglia (1993) — "Contextual reasoning," *Epistemologia* 16(3):345-364.** Ref [21]. Earlier framing piece; collection already has Giunchiglia (1994) Multilanguage Hierarchical Logics, but not this one.
- **Henricksen, Indulska & Rakotonirainy (2002) — "Modeling context information in pervasive computing systems," *Pervasive Computing*, pp. 167-180.** Ref [11]. Foundational context-modelling cite this paper positions itself against.
- **Uddin, Rakib, Haque & Vinh (2018) — "Modeling and reasoning about preference-based context-aware agents over heterogeneous knowledge sources," *Mobile Networks and Applications* 23(1):13-26.** Ref [32]. Peer of this paper, also targeting heterogeneous sources.
- ~~**Antoniou, Billington, Governatori & Maher (2001) — "Representation results for defeasible logic," *ACM TOCL* 2(2):255-287.** Ref [13]. Representation-theoretic grounding for the proof system.~~ → **Now in Collection** as [Representation Results for Defeasible Logic](../Antoniou_2000_RepresentationResultsDefeasibleLogic/notes.md). Confirms the lead's framing: the paper proves that facts, defeaters, and the superiority relation are all eliminable by modular or incremental transformations (`normal`, `elim_dft`, `elim_sup`) while preserving the four-tagged conclusion set on the original language; classifies per-literal outcomes into six classes A-F and per-pair outcomes into 16 acyclic-realizable cases; gives non-existence theorems showing strict and defeasible rules cannot be eliminated; and supplies a simplified post-transformation proof theory underpinning the linear-time Delores consequence engine. Direct theoretical foundation for any propstore engine that wants to normalize Al-Anbaki-style L = ⟨G, β, D, λ⟩ theories before reasoning.
- ~~**Maher (2001) — "Propositional defeasible logic has linear complexity," *TPLP* 1(6):691-711.** Ref [15]. Complexity bound for the proof system propstore would inherit.~~ → **Now in Collection** as [Propositional Defeasible Logic has Linear Complexity](../Maher_2001_PropositionalDefeasibleLogicLinearComplexity/notes.md). Confirms the lead's framing exactly: Maher proves propositional defeasible logic — strict + defeasible rules + defeaters + acyclic programmable superiority — admits an O(N) inference algorithm (Theorem 5, p.17) via a transition system over basic defeasible logic with auxiliary tags `+σ, −σ`, the Delores worklist algorithm with body-tracking data structures (Figure 1, Figure 2), and linear-time / linear-blowup `Basic` transformations to reduce arbitrary theories to basic form (Theorem 4, p.13). The complexity ceiling propstore inherits when defeasible logic is the substrate of `propstore.defeasibility` and the ASPIC+ bridge — and a reusable proof technique (auxiliary tags + Dowling–Gallier-style worklist + linear-blowup transformations) for related propstore bounds. Direct algorithmic counterpart to Antoniou_2000_RepresentationResultsDefeasibleLogic's representation result.

### Supersedes or Recontextualizes

- (none) — this paper extends classical DL but does not supersede a paper already in the collection.

### Cited By (in Collection)

- (none found) — `grep -rl Al-Anbaki papers/` returns no hits outside this directory.

### Conceptual Links (not citation-based)

**CKR-style contextual defeasibility (direct mechanism overlap):**
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — Strong. Bozzato et al.'s CKR `ist`-context with justifiable exceptions and Al-Anbaki et al.'s `L = ⟨G, β, D, λ⟩` are two independent answers to the same question: how do you let local context override global rules without losing consistency? CKR uses a clearance/justifiability semantics; this paper uses ambiguity-blocking DL with concern-encapsulated `D^X`. Different formalisms, near-identical engineering goal — propstore's `propstore.defeasibility` module is the convergence point that should cite both.
- [A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility](../Bozzato_2020_DatalogDefeasibleDLLite/notes.md) — Strong. Bozzato et al. give a Datalog operationalisation of CKR-style defeasible context reasoning; Al-Anbaki et al. give the same kind of theory in pure DL form without an execution backend. Useful pair for propstore: Bozzato 2020 supplies a candidate execution layer for the Al-Anbaki rule shape.

**Local models / multi-context contextual reasoning:**
- [Local Models Semantics, or Contextual Reasoning = Locality + Compatibility](../Ghidini_2001_LocalModelsSemanticsContextual/notes.md) — Strong. Ghidini & Giunchiglia provide LMS — the canonical multi-context semantics. Al-Anbaki et al.'s per-authority `D^A`, `D^B` partition is essentially LMS's local-models partitioning, with `λ` playing the role of LMS's compatibility relation but specialised to defeasible-rule priorities.
- [Multilanguage hierarchical logics, or: how we can do without modal logics](../Giunchiglia_1994_MultilanguageHierarchicalLogics/notes.md) — Moderate. Earlier Giunchiglia framing of multi-context reasoning without modal logic; Al-Anbaki et al.'s framework can be read as a defeasibility-aware specialisation of the same impulse.
- [Microtheories](../Kallem_2006_Microtheories/notes.md) — Moderate. Cyc microtheories are another `ist`-style context formalism; the `Cᵒ / Cᵘ / Cʰ` spectrum maps loosely onto microtheory hierarchies.
- [Formalizing Context (Expanded Notes)](../McCarthy_1997_FormalizingContextExpanded/notes.md) — Moderate. The expanded version of cite [19]; Al-Anbaki cites the 1993 IJCAI paper but the 1997 expanded notes are the more complete reference for `ist`.

**Defeasible reasoning machinery (proof-system convergence):**
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — Moderate. Morris et al. operationalise KLM-style defeasibility over Datalog; Al-Anbaki et al.'s ambiguity-blocking DL is a different but cousin formalism. Both are candidate execution backends for propstore's defeasibility lane.
- [Deciding Consistency of Databases Containing Defeasible and Strict Information](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — Moderate. Goldszmidt's strict-vs-defeasible consistency results are a foundational hygiene check that any framework partitioning rules into `R_s ∪ R_d ∪ R_f` (as Al-Anbaki does) inherits.
- [LLM-ASPIC+: A Neuro-Symbolic Framework for Defeasible Reasoning](../Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/notes.md) — Moderate. Fang et al. wire LLMs into ASPIC+ for defeasible reasoning; Al-Anbaki et al.'s `L` is a candidate target formalism for the same kind of LLM-extracted rule pipeline propstore already uses.

### Checkpoint (post-parallel-swarm, 2026-05-06)

**State of the world:**
- Three top-priority leads retrieved + read + reconciled in parallel via Opus subagents:
  1. `papers/Antoniou_2000_DefeasibleLogicVersusLogic/` — ref [38]; canonical `±Δ / ±∂` proof-tag system. 35KB notes, sci-hub.ru retrieval, all artifacts present.
  2. `papers/García_2014_DefeasibleLogicProgrammingDeLP-servers/` — ref [40]; DeLP-Server execution model with `⊕ ⊗ ⊖` operators and four-valued answers. 28pp PDF, retrieved via Chrome+sci-hub.
  3. `papers/Governatori_2012_RevisionDefeasibleLogicPreferences/` — ref [24]; superiority-relation revision via eight new auxiliary proof tags, NP-completeness, AGM-postulate audit. 41pp arXiv-direct.
- All three "New Leads" entries above marked `→ NOW IN COLLECTION` with strikethrough + bidirectional cross-reference link. New `### Now in Collection (previously listed as leads)` subsection added with substantive synopses.
- `papers/index.md` updated with three new entries in alphabetical order.
- Empty stub directory `papers/Antoniou_2000_DefeasibleLogicVersusLogicProgramming/` (created by linter or one of the agents from a dangling cross-ref) removed; canonical directory is `Antoniou_2000_DefeasibleLogicVersusLogic`.
- Forward cross-references from each new paper to existing collection members were also written by the swarm:
  - Antoniou_2000 → Cited By: Al-Anbaki_2019, Governatori_2012; 11 new leads recorded
  - García_2014 → Already in Collection: McCarthy_1980, Reiter_1980, Moore_1985; Modgil_2014 conceptual link; Thimm_2020 lead promoted
  - Governatori_2012 → Cited By: Al-Anbaki_2019; conceptual links to Baumann_2019_AGMContractionDung and Rotstein_2008_ArgumentTheoryChangeRevision; Antoniou_2000 forward link fixed (was previously dangling)

**Observation worth recording:**
- The Spanish n-tilde character in `García_2014_*` produces a directory name that some Windows tools treat oddly — flag if it surfaces as a portability issue later.
- 7 leads remain unprocessed (Bikakis 2008/2010, Dastani 2007, Buvac 1993, Giunchiglia 1993, Henricksen 2002, Uddin 2018) after Antoniou 2001 was retrieved + read on 2026-05-07 and Maher 2001 on 2026-05-07. Defer the rest until Q asks for more.

**Blocker:** none. Collection is in a consistent state.

### Checkpoint (post-second-swarm, 2026-05-06)

**State of the world:**
- Four more leads retrieved + read + reconciled in parallel via Opus subagents:
  4. `papers/Bikakis_2010_DefeasibleContextualReasoningArguments/` — ref [16]; IEEE TKDE 22(11), 15pp. Closest competitor — multi-context defeasible argumentation in ambient intelligence.
  5. `papers/Antoniou_2000_RepresentationResultsDefeasibleLogic/` — ref [13]; ACM TOCL 2(2), 30pp (arxiv cs.LO/0003082). Note: dir name uses arxiv year 2000; frontmatter records canonical 2001 publication year. Sister to Antoniou_2000_DefeasibleLogicVersusLogic — together they constitute the canonical "what tags exist + which primitives are essential" formal program for DL.
  6. `papers/Maher_2001_PropositionalDefeasibleLogicLinearComplexity/` — ref [15]; TPLP 1(6), 20pp (arxiv cs/0405090). Linear-complexity bound — algorithmic counterpart to Antoniou 2001 representation result.
  7. `papers/Dastani_2007_ContextualAgentDeliberationDefeasible/` — ref [34]; PRIMA 2007, 12pp. Agent-side companion of Al-Anbaki framework. Retrieved via ORBilu Luxembourg postprint after S2/sci-hub failed.

**All seven retrieved papers (3 from first swarm + 4 from second) have bidirectional Cited By → Al-Anbaki backlinks confirmed by grep.**

**Cross-references richened during this swarm:**
- `Antoniou_2000_DefeasibleLogicVersusLogic` ↔ `Antoniou_2000_RepresentationResultsDefeasibleLogic` — bidirectional Sister Paper section added by the Antoniou_2001 agent.
- `Bikakis_2010` → conceptual links to Bozzato_2018, Bozzato_2020, Governatori_2012, Antoniou_2000 (DL vs LP), Antoniou_2000 (representation), McCarthy_1993, McCarthy_1997.
- `Maher_2001` → 27 new leads recorded (largest reference list of the four), 13 conceptual links (5 Strong, 8 Moderate) including Modgil_2014_ASPIC, Morris_2020_DefeasibleDisjunctiveDatalog, Forbus_1993, Doyle_1979.
- `Dastani_2007` → Strong conceptual links to Antoniou_2000 (DL vs LP) and Governatori_2012 (Governatori is co-author on both).

**Lead status update (Al-Anbaki citations.md):**
- Of 12 originally surfaced leads, 7 are now in the collection (refs [13], [15], [16], [24], [34], [38], [40]).
- 5 remain unprocessed: Bikakis-Antoniou 2008 (ref [22] — subsumed by 2010, low yield), Buvac-Mason 1993 (ref [20]), Giunchiglia 1993 (ref [21]), Henricksen 2002 (ref [11]), Uddin 2018 (ref [32]). All LOW-MEDIUM priority. None are blocking propstore work.

**Observation worth recording:**
- Two parallel agents (Antoniou_2001 and Maher_2001) independently noticed and corrected the same dangling cross-reference in Governatori_2012 — a benign artefact of the Governatori agent's earlier work.
- Sci-hub retrieval continues to need Chrome `fetch().blob()` rather than direct curl — DDoS-Guard blocks curl. ORBilu (Luxembourg) is a useful self-archive fallback when sci-hub fails (worked for Dastani 2007).
- arXiv API is rate-limited often enough that subagents should default to direct PDF download + hand-written metadata.json from title-page text.

**Blocker:** none. Collection is in a consistent state. Seven new defeasible-logic / contextual-reasoning papers landed cleanly with bidirectional cross-references.
