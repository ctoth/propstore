# Spec: ASPIC+ Bridge — Connecting the Claim Graph to the Formal Engine

**Date:** 2026-03-27
**Status:** Draft
**Depends on:** proposals/first-class-justifications.md (data layer)
**Implements:** CLAUDE.md "Known Limitation" re ASPIC+ argument construction
**Grounded in:** Modgil & Prakken 2018 Defs 1-22; propstore aspic.py, structured_argument.py

---

## Situation

Three pieces exist independently:

1. **aspic.py** (948 lines) — a complete, tested ASPIC+ engine: `Literal`, `Rule`, `KnowledgeBase`, `ArgumentationSystem`, `PreferenceConfig`, `build_arguments()`, `compute_attacks()`, `compute_defeats()`, `CSAF`. Implements Defs 1-22 of Modgil & Prakken 2018. Has no connection to the claim graph.

2. **structured_argument.py** — the live bridge from claims/stances to Dung AF. Builds `StructuredArgument` objects from `CanonicalJustification` records. Uses a heuristic `metadata_strength_vector` (3-dim: log_sample_size, inverse_uncertainty, confidence) for preference comparison. Produces working argumentation but with flat structure and no strict/defeasible distinction.

3. **first-class-justifications proposal** — adds stored `Justification` entities with `rule_strength` (strict/defeasible), `rule_kind` (12 types), multi-premise support, `premise_kind` on claims (necessary/ordinary), and targeted undercutting. Creates the data prerequisites for a bridge. Every paper has or will have `justifications.yaml`.

This spec defines the translation layer that connects (3) to (1), replacing (2).

---

## Translation Rules

### T1. Claims to Literals

Each claim becomes a `Literal` in the ASPIC+ language L.

```
claim with id "C" and concept "X"
  -> Literal(atom="C", negated=False)
```

The atom is the claim ID, not the concept ID. Two claims about the same concept are different literals — they may conflict, but that conflict is expressed through the contrariness function, not by sharing an atom.

Negated literals arise from the contrariness function (T3), not from claim data.

**Rationale:** Claims are the atomic unit of assertion in propstore. Concepts are what claims are *about*, but two claims about the same concept may agree, disagree, or be orthogonal. ASPIC+'s language needs one literal per assertable proposition (Def 1, p.8).

### T2. Justifications to Rules

Each stored justification becomes an ASPIC+ rule.

```
Justification(
    id="paper:just1",
    conclusion_claim_id="C_target",
    premise_claim_ids=["C_1", "C_2"],
    rule_kind="causal_explanation",
    rule_strength="defeasible",
)
->
Rule(
    antecedents=(Literal("C_1"), Literal("C_2")),
    consequent=Literal("C_target"),
    kind="defeasible",
    name="paper:just1",     # naming function n(r) for undercutting
)
```

- `rule_strength="strict"` -> `kind="strict"`, `name=None` (strict rules have no name, cannot be undercut; Def 8c, p.11)
- `rule_strength="defeasible"` -> `kind="defeasible"`, `name=justification_id` (the justification ID *is* the naming function)

**Implicit rules from stances (backward compatibility):** Claims/stances without stored justifications generate rules via the existing `_canonical_justifications()` logic. These are always defeasible with name = the generated justification_id.

**`reported_claim` justifications do NOT generate rules.** They generate premise arguments (T4). A reported claim is a premise in K, not an inference step.

### T3. Contrariness Function from Stances

Attack-type stances define the contrariness function:

| Stance type | ASPIC+ mapping | Symmetric? |
|-------------|---------------|------------|
| `rebuts` | **Contradictories**: Literal("C_source") and Literal("C_target") are contradictory | Yes (Def 2, p.8) |
| `contradicts` | **Contradictories**: same as rebuts | Yes |
| `supersedes` | **Contraries**: Literal("C_source") is a contrary of Literal("C_target") | No (Def 2, p.8) — the newer claim displaces the older, but not vice versa |
| `undermines` | **Contraries**: Literal("C_source") is a contrary of Literal("C_target") | No — the underminer attacks the target's premise status |
| `undercuts` | Not in contrariness function | N/A — undercutting targets the *rule name*, not a literal in L (Def 8c, p.11) |

For undercutting: the attacker's conclusion must conflict with the literal `n(r)` representing the rule's applicability. This means:

```
undercuts stance from C_source to C_target via justification J
->
ContrarinessFn entry: Literal("C_source") is contrary of Literal("J")
```

where `Literal("J")` is the name-literal for the defeasible rule. This is how ASPIC+ encodes "this evidence says that inference step J is not applicable" (Def 8c, p.11; Modgil 2014 p.35).

**Language closure:** L must contain all claim literals, their contraries (negated literals), and all rule-name literals. This is the closure requirement from Def 1 (p.8).

### T4. Claims to Knowledge Base

```
claim with premise_kind="necessary"  -> K_n (axioms, unattackable)
claim with premise_kind="ordinary"   -> K_p (ordinary premises, attackable)
```

All claims that have a `reported_claim` justification (i.e., are directly asserted, not solely derived) contribute their literal to K.

Claims that *only* appear as conclusions of inference rules (never directly asserted) are NOT in K — they can only be established by firing rules. This distinction matters: a claim that is both directly reported and inferentially supported will have both a premise argument and one or more rule-based arguments.

### T5. Preference Orderings from Claim Metadata

This is the part the justifications proposal explicitly defers. Here is the mapping:

#### Over premises (K_p ordering)

Claim metadata provides three dimensions: `sample_size`, `uncertainty`, `confidence`. These induce a partial order over ordinary premises:

```
Literal("C_1") < Literal("C_2") in premise_order iff
    metadata_strength_vector(C_1) is strictly dominated by
    metadata_strength_vector(C_2) component-wise
```

Component-wise domination is strict: all three components of C_1 must be less than the corresponding components of C_2. This yields a strict partial order (irreflexive, transitive) as required by Def 22 (p.22).

**Why component-wise:** The existing `strictly_weaker()` in `preference.py` uses Elitist/Democratic set comparison over a vector. But that's comparing *sets of scalars*. ASPIC+ Def 19 compares *sets of rules/premises*. The premise ordering is a binary relation over individual premises, not a comparison of vectors. The vectors are used to *induce* the binary relation.

#### Over defeasible rules (R_d ordering)

Rule ordering is harder — the `rule_kind` and source metadata must combine:

```
Rule r1 < Rule r2 in rule_order iff
    r1 and r2 share a comparable dimension AND
    r1 is strictly weaker on that dimension
```

Comparable dimensions for rules:
- If both rules come from the same paper: compare by provenance specificity (section depth, directness of support)
- If rules come from different papers: compare by the metadata of their premise claims (transitively — a rule is as strong as its weakest premise under weakest-link)
- If `rule_kind` types have a natural hierarchy (e.g., `empirical_support` > `expert_testimony` > `abductive_inference`): that hierarchy induces ordering

**Open question for Q:** Should rule ordering be explicitly stored (like premise ordering derives from metadata), or should it be a render-time policy? The non-commitment principle suggests: store the raw metadata, compute the ordering at render time based on a policy. Multiple policies can coexist.

#### Comparison and link modes

`PreferenceConfig.comparison` ("elitist" or "democratic") and `PreferenceConfig.link` ("last" or "weakest") are **render-time policy choices**, not stored facts. Different world queries can use different configurations over the same underlying data.

This aligns with propstore's resolution strategies — `comparison` and `link` become parameters of the argumentation resolution strategy, alongside `semantics` (grounded/preferred/stable).

### T6. Argument Construction

With T1-T5 defined, argument construction is a direct call:

```python
system = ArgumentationSystem(
    language=language,           # from T1 + T3 closure
    contrariness=contrariness,   # from T3
    strict_rules=strict_rules,   # from T2 where rule_strength="strict"
    defeasible_rules=def_rules,  # from T2 where rule_strength="defeasible"
)
kb = KnowledgeBase(
    axioms=axioms,               # from T4 necessary claims
    premises=premises,           # from T4 ordinary claims
)
pref = PreferenceConfig(
    rule_order=rule_order,       # from T5
    premise_order=premise_order, # from T5
    comparison=comparison,       # render-time policy
    link=link,                   # render-time policy
)

arguments = build_arguments(system, kb)
attacks = compute_attacks(arguments, system)
defeats = compute_defeats(attacks, arguments, system, kb, pref)
```

This produces a `CSAF` with full recursive argument structure, proper ASPIC+ attacks/defeats, and preference-filtered results.

### T7. Output — Back to the Pipeline

The CSAF's `framework` field is a `dung.ArgumentationFramework`. This slots directly into the existing extension computation:

```python
csaf = build_csaf(system, kb, pref)  # T6
# csaf.framework is a Dung AF — use existing semantics
grounded = grounded_extension(csaf.framework)
preferred = preferred_extensions(csaf.framework)
```

To map results back to claims:

```python
justified_claims = {
    conc(csaf.id_to_arg[arg_id]).atom  # atom = claim_id per T1
    for arg_id in grounded
}
```

For sidecar integration, the justified claim IDs feed into the existing world model resolution strategies. The existing `argumentation` resolution strategy switches from the flat structured_argument path to the ASPIC+ bridge:

1. Build the CSAF from active claims + stored justifications
2. Compute extensions per the chosen semantics
3. Return the accepted claim IDs

---

## Relationship to structured_argument.py

**Replacement, not parallel path.**

Every paper has (or will have) `justifications.yaml`. The universal availability of stored justifications means there is no "papers without justifications" case to fall back to. `structured_argument.py` is the legacy path to retire.

The migration path:

1. Build the ASPIC+ bridge (`aspic_bridge.py`) with the same external contract: takes active claims, returns a Dung AF and claim-to-argument mappings.
2. Make `build_structured_projection()` delegate to the bridge internally. Callers (bipolar/PrAF/DF-QuAD) continue to get a `StructuredProjection`, but it's built from CSAF output rather than from flat `CanonicalJustification` records.
3. Once all callers are verified, remove the flat construction code.

**What `StructuredProjection` becomes:** A view over the CSAF, not an independent construction. The `StructuredArgument` dataclass may survive as a simpler projection of `aspic.py`'s recursive `Argument` type for consumers that don't need the full tree (e.g., sidecar serialization). But the construction logic moves to aspic.py.

**`CanonicalJustification` becomes:** The intermediate type that the bridge reads from the justification store and translates into ASPIC+ rules (T2). It gains `rule_strength` and richer `rule_kind` per the first-class-justifications proposal. Its role narrows from "the thing arguments are built from" to "the thing ASPIC+ rules are translated from."

---

## Interaction with ATMS

The ATMS (de Kleer 1986) maintains assumption labels on every datum. The bridge interacts with it at two points:

1. **Input:** Active claims are determined by the current ATMS context (assumption set). The ASPIC+ bridge only sees claims that are active in the current context. Different contexts may produce different CSAFs.

2. **Output:** Extension membership is a new kind of label. A claim's ATMS label could be augmented with "in grounded extension under context C with policy P." This is a derived fact, not a stored one — computed at render time.

The ATMS and ASPIC+ are complementary: ATMS tracks *which assumptions support which conclusions* (dependency-directed). ASPIC+ determines *which arguments survive conflict* (defeat-directed). Dixon 1993 establishes the formal connection: ATMS context switching corresponds to AGM revision operations, and the entrenchment ordering can be derived from justification structure — which is exactly what the ASPIC+ preference ordering provides.

---

## What Strict Rules Mean for the Claim Graph

Strict rules (from `rule_strength="strict"` justifications) have consequences:

1. **Their conclusions are as strong as their premises.** If all premises of a strict rule are in K_n, the conclusion is firm+strict — unattackable. A mathematical definition applied to established facts produces an unassailable conclusion.

2. **Transposition closure applies.** If `A, B -> C` is strict, then `A, ~C -> ~B` and `B, ~C -> ~A` must also be in R_s (Def 12, p.13). `aspic.py` already computes this via `transposition_closure()`. The bridge must ensure the generated language L includes the transposition-generated literals.

3. **They create sub-argument structure.** A strict chain `A -> B -> C` means arguments for C include sub-arguments for B and A. Attacks on A propagate to C (attack on sub-argument). This is the recursive structure that the "flat" limitation refers to — and aspic.py already handles it via `build_arguments()`.

**Practical implication:** When a paper marks a justification as `strict`, it's claiming that the inference is logically valid. The extraction pipeline should be conservative about this — most scientific inferences are defeasible. Strict should be reserved for: formal definitions, mathematical derivations, logical tautologies, and definitional applications.

---

## Implementation Sequence

This spec depends on the first-class-justifications proposal being implemented first (steps 1-4 of that proposal). After that:

1. **Translation module** (`aspic_bridge.py`): Implement T1-T5 as pure functions that take stored justifications + claims and produce aspic.py input types. No side effects, fully testable.

2. **CSAF builder** (`aspic_bridge.py`): Implement T6 as a function that calls T1-T5 then aspic.py's `build_arguments`/`compute_attacks`/`compute_defeats`. Returns a `CSAF`.

3. **Resolution strategy**: Add `argumentation_aspic` to the world model resolution strategies. Implement T7.

4. **Tests against PyArg**: For each test case, build the same framework in both propstore's aspic.py and PyArg, compare extensions. This validates correctness without taking a dependency.

5. **Preference policy system**: Make comparison/link/rule-ordering configurable at render time. This is where the "multiple render policies over the same corpus" principle manifests.

---

## Open Questions

1. **Rule ordering policy**: Should rule ordering be stored or computed? Proposal: computed at render time from metadata + a policy function. Multiple policies can coexist. Q to decide.

2. **Transposition-generated claims**: When transposition closure creates rules with negated literals, do those negated literals correspond to "virtual claims" that don't exist in the claim store? Proposal: yes, they exist only in the ASPIC+ language L, not as stored claims. They're ephemeral, computed at bridge time.

3. **Scale**: `build_arguments()` enumerates all possible arguments. For N claims with M rules, this could be exponential. The existing Z3 backend for Dung extensions helps with extension computation but not argument construction. Need to profile on real paper collections. PyArg's approach is the same (exhaustive enumeration), so this is an inherent complexity, not an implementation issue.

4. **Interaction with bipolar support**: Cayrol 2005 support relations create derived defeats. ASPIC+'s argument construction propagates support through rule chaining — if A supports B via a defeasible rule, an attack on A propagates to B through sub-argument structure. This subsumes Cayrol's "secondary attacks" for the support-through-inference case. But Cayrol's "mediated attacks" (if A supports B and C attacks A, then C derived-attacks B) may still add value for support relations that aren't expressible as inference rules. Proposal: once the bridge is live, profile whether Cayrol derived defeats ever produce defeats that ASPIC+ sub-argument attacks don't already capture. If redundant, retire the bipolar layer for the ASPIC+ path.

5. **Accrual**: Multiple justifications for the same conclusion produce multiple arguments. ASPIC+ doesn't formally accrue them (Prakken 2019). Should the bridge count the number of surviving arguments for a claim as a signal? This could feed into the opinion/subjective-logic layer.

---

## References

- Modgil & Prakken 2018 — Defs 1-22, the complete ASPIC+ framework
- Modgil & Prakken 2014 — Tutorial introduction to ASPIC+
- Pollock 1987 — Rebutting vs undercutting defeaters
- de Kleer 1986 — ATMS assumption labels
- Dixon 1993 — ATMS context switching = AGM operations
- Cayrol 2005 — Bipolar argumentation, derived defeats
- Walton 2015 — Argumentation scheme taxonomy
- Prakken 2019 — Accrual of arguments in ASPIC+
- Jøsang 2001 — Subjective logic opinions (for accrual question)
