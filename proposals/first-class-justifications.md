# Proposal: First-Class Justifications in Propstore

**Date:** 2026-03-27
**Status:** Draft
**Grounded in:** scout-argumentation-ontology.md (11 papers), scout-propstore-justification-internals.md (propstore codebase)

---

## Problem

Propstore derives justifications ephemerally from claims + stances. This loses structure that the upstream extraction pipeline can provide and that the ASPIC+ literature says is necessary for correct argumentation:

1. **Multi-premise inference is invisible.** All derived justifications have exactly one premise (single `supports`/`explains` stance). "Claims A, B, and C together entail D via causal explanation" cannot be expressed.

2. **Inference types are impoverished.** Only three rule_kinds exist: `reported_claim`, `supports`, `explains`. The literature (Walton 2015) catalogs 60+ argumentation schemes.

3. **Undercuts are indiscriminate.** An undercut targeting claim C hits all inference-rule arguments for C. Cannot say "this undercut defeats the methodological inference to C but not the empirical inference to C." (Modgil 2014 p.35: ASPIC+'s naming function exists precisely for this.)

4. **Strict vs defeasible is unrepresented.** All justifications are implicitly defeasible. Mathematical definitions and logical derivations should be strict — unattackable by undercuts. (Modgil 2014 p.35: "the framework distinguishes strict from defeasible rules.")

5. **No import path.** The upstream pipeline now produces `justifications.yaml` per paper, but `import_papers` only reads `claims.yaml`.

6. **aspic.py is stranded.** A complete ASPIC+ implementation (948 lines, Defs 1-22) exists but has no bridge to the claim/stance data model.

---

## Proposal

Make `Justification` a first-class stored entity type: imported from papers, persisted in SQLite, and consumed by the argumentation backends.

---

## 1. Justification Entity

### Schema (LinkML addition to `schema/claim.linkml.yaml`)

```yaml
Justification:
  attributes:
    id:
      identifier: true
      range: string
      description: Globally unique ID (prefixed at import, e.g. "Dung_1995:just1")
    conclusion_claim_id:
      range: string
      required: true
      description: Claim ID this justification supports or attacks
    premise_claim_ids:
      range: string
      multivalued: true
      required: true
      description: Claim IDs that together form the premises
    rule_kind:
      range: RuleKindEnum
      required: true
    rule_strength:
      range: RuleStrengthEnum
      required: true
      description: "strict (definitional/logical, cannot be undercut) or defeasible (empirical/presumptive, can be undercut)"
    attack_target:
      range: AttackTarget
      description: Present only for critique justifications
    provenance:
      range: Provenance

RuleKindEnum:
  permissible_values:
    # Existing (relabeled from stance-derived)
    reported_claim:
      description: Base justification for each active claim (auto-generated)
    support:
      description: Generic support (from supports stances, when no richer kind available)
    explanation:
      description: Mechanistic/causal account (from explains stances)
    # Science-domain inference patterns
    empirical_support:
      description: Experimental data directly supports conclusion
    causal_explanation:
      description: Mechanism explains why a result holds
    methodological_inference:
      description: Methodological choice leads to validity conclusion
    statistical_inference:
      description: Statistical test/model produces a finding
    definition_application:
      description: Applying formal definition to classify or derive
    scope_limitation:
      description: Evidence narrows applicability of a claim
    comparison_based_inference:
      description: Comparative reasoning across methods/systems/findings
    # From Walton's taxonomy (scout-argumentation-ontology.md)
    expert_testimony:
      description: "Argument from expert opinion / position to know (Walton 2015 p.10)"
    abductive_inference:
      description: "Inference to best explanation (Walton 2015 p.20)"

RuleStrengthEnum:
  permissible_values:
    strict:
      description: "Definitional/logical — cannot be undercut (ASPIC+ strict rules, Modgil 2014 p.35)"
    defeasible:
      description: "Empirical/presumptive — can be undercut (ASPIC+ defeasible rules, Modgil 2014 p.35)"

AttackTarget:
  attributes:
    kind:
      range: AttackTargetKindEnum
      required: true
    target_claim_id:
      range: string
      required: true

AttackTargetKindEnum:
  permissible_values:
    conclusion:
      description: "Attacks the conclusion directly (rebut in ASPIC+)"
    premise:
      description: "Attacks evidence/premise quality (undermine in ASPIC+)"
    inference_rule:
      description: "Attacks the reasoning step itself (undercut in ASPIC+)"
```

### rule_strength semantics

- **strict**: The inference is definitional, mathematical, or logical. It cannot be undercut — only its premises can be undermined. `definition_application` is typically strict. A mathematical derivation is strict.
- **defeasible**: The inference is empirical, presumptive, or abductive. It can be undercut (the methodology attacked, the reasoning questioned). `empirical_support`, `statistical_inference`, `expert_testimony`, `abductive_inference` are typically defeasible.

This maps directly to ASPIC+'s `Rs` (strict rules) vs `Rd` (defeasible rules) partition (Modgil 2014 p.35).

---

## 2. SQLite Table

Add to `build_sidecar.py`:

```sql
CREATE TABLE justification (
    id                  TEXT PRIMARY KEY,
    conclusion_claim_id TEXT NOT NULL REFERENCES claim(id),
    rule_kind           TEXT NOT NULL,
    rule_strength       TEXT NOT NULL DEFAULT 'defeasible',
    attack_target_kind  TEXT,
    attack_target_claim TEXT REFERENCES claim(id),
    provenance_paper    TEXT,
    provenance_page     INTEGER,
    provenance_section  TEXT,
    provenance_quote    TEXT,
    source_paper        TEXT
);

CREATE TABLE justification_premise (
    justification_id TEXT NOT NULL REFERENCES justification(id),
    premise_claim_id TEXT NOT NULL REFERENCES claim(id),
    seq              INTEGER NOT NULL,
    PRIMARY KEY (justification_id, premise_claim_id)
);
```

Separate premise table because premises are multi-valued. `seq` preserves ordering.

---

## 3. Import Pipeline Changes

### `import_papers` additions (`compiler_cmds.py`)

After processing `claims.yaml`, check for `{paper_dir}/justifications.yaml`. If present:

1. Read and parse.
2. Prefix justification IDs: `just1` -> `PaperName:just1`.
3. Prefix all claim references (conclusion, premises, attack_target.target_claim) with the same paper prefix used for claims.
4. Write resolved justifications alongside resolved claims.

### `build_sidecar` additions

After populating the `claim` and `claim_stance` tables, populate `justification` and `justification_premise` from the resolved justification files.

---

## 4. Structured Argument Builder Changes

### `structured_argument.py`

Currently `_canonical_justifications()` / `claim_justifications_from_active_graph()` derives justifications from stances. Change to:

1. **Load stored justifications first.** Read from the `justification` + `justification_premise` tables.
2. **Fall back to stance-derived justifications** for claims/stances that have no explicit justification. This preserves backward compatibility — papers without `justifications.yaml` still work.
3. **Merge:** If a stored justification and a stance-derived justification cover the same conclusion, prefer the stored one (it's richer).

### `StructuredArgument` additions

Add `rule_strength` field to `StructuredArgument`:

```python
rule_strength: str = "defeasible"  # "strict" or "defeasible"
```

Strict arguments cannot be undercut. The defeat computation in `build_argumentation_framework` should skip undercut attacks against strict-rule arguments. This is already how ASPIC+ works (Modgil 2014 p.39-40: "undercutting only targets defeasible rules").

### Targeted undercutting

Change `_target_argument_ids` for `undercuts` stances:

```python
if stance_type == "undercuts":
    target_just_id = stance.get("target_justification_id")
    return {
        arg.arg_id
        for arg in arguments
        if arg.claim_id == target_claim_id
        and arg.attackable_kind == "inference_rule"
        and arg.rule_strength == "defeasible"  # strict rules immune
        and (target_just_id is None or arg.justification_id == target_just_id)
    }
```

If the stance specifies a `target_justification_id`, only that justification's arguments are hit. Otherwise, all defeasible inference-rule arguments for the claim are hit (backward compatible).

---

## 5. ASPIC+ Bridge (Future)

The stored justifications provide the data needed to bridge to `aspic.py`:

- Each justification with `rule_strength="strict"` maps to a strict rule in `Rs`
- Each justification with `rule_strength="defeasible"` maps to a defeasible rule in `Rd` with name = justification ID
- Each claim maps to a literal in `L`
- `Kn` (necessary premises) = claims marked as axioms (see below)
- `Kp` (ordinary premises) = all other claims

This bridge is not part of this proposal but this proposal creates the prerequisites for it. The justification IDs serve as the naming function `n: Rd -> L` that ASPIC+ requires.

---

## 6. Claim Additions (Smaller Scope)

### Necessary vs Ordinary

Add to the `claim` table:

```sql
premise_kind TEXT NOT NULL DEFAULT 'ordinary'  -- 'necessary' or 'ordinary'
```

- **necessary**: Axioms, definitions, mathematical identities. Cannot be undermined. Maps to ASPIC+'s `Kn`.
- **ordinary**: Empirical observations, reported measurements. Can be undermined. Maps to ASPIC+'s `Kp`.

This is a column addition, not a schema rewrite. Backward compatible — all existing claims default to `ordinary`.

### Upstream representation

In `claims.yaml`:

```yaml
- id: claim5
  type: observation
  premise_kind: necessary  # optional, defaults to ordinary
  statement: "By definition, a systematic review must include..."
```

---

## 7. What This Does NOT Do

- **Full ASPIC+ evaluation.** The aspic.py engine remains standalone. This proposal adds the data layer; bridging is future work.
- **Practical reasoning.** No goal-directed, value-based, or consequence-based rule_kinds. Wrong domain for now. (Walton 2015 p.13-16)
- **Accrual.** Multiple justifications for the same conclusion don't formally accumulate. They produce multiple arguments that independently participate in the framework. (Prakken 2019 — future work.)
- **Preference orderings.** No explicit ordering over rules or premises beyond strict/defeasible. (Modgil 2014 p.42-44 — future work.)
- **Contrariness function.** Asymmetric conflict remains unrepresented. (Modgil 2018 p.8 — future work.)

---

## 8. Implementation Order

1. **LinkML schema**: Add Justification, RuleKindEnum, RuleStrengthEnum, AttackTarget to `schema/claim.linkml.yaml`
2. **SQLite tables**: Add `justification` and `justification_premise` tables to `build_sidecar.py`
3. **Import pipeline**: Extend `import_papers` to read `justifications.yaml`
4. **Structured argument builder**: Load stored justifications, add `rule_strength`, implement strict-rule immunity and targeted undercutting
5. **Claim extension**: Add `premise_kind` column
6. **Validation**: Extend `pks claim validate-file` to also validate `justifications.yaml`
7. **Tests**: For each step

Steps 1-3 are mechanical. Step 4 is the behavioral change. Steps 5-6 are small additions. Each step is independently committable and testable.

---

## 9. Upstream Compatibility

The research-papers-plugin already produces `justifications.yaml` per paper with this format:

```yaml
source:
  paper: PaperDirName

justifications:
  - id: just1
    conclusion: claim12
    premises:
      - claim3
      - claim8
    rule_kind: causal_explanation
    provenance:
      page: 14
      section: Discussion
      quote_fragment: "..."
```

This proposal adds `rule_strength` (defaulting to `defeasible`) and optionally `attack_target`. The upstream skill should be updated to emit `rule_strength` per justification. Existing `justifications.yaml` files without `rule_strength` will default to `defeasible` at import.

---

## References

- Modgil & Prakken 2014 — ASPIC+ framework (strict/defeasible rules, naming function, three attack types)
- Modgil & Prakken 2018 — General account of argumentation with preferences
- Walton & Macagno 2015 — Classification system of ~28 argumentation schemes
- Prakken et al. 2013 — Formalization of argumentation schemes in ASPIC+ for legal reasoning
- Pollock 1987 — Rebutting vs undercutting defeaters
- Dauphin 2018 — ASPIC-END (explanations, intuitively strict rules)
- Prakken 2019 — Accrual of arguments in ASPIC+
