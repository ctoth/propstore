# propstore

Papers disagree. propstore finds out who's right.

A compiler and query engine for scientific claims — with formal argumentation, conflict detection, and counterfactual reasoning. Feed it structured claims from research papers, and it builds an argumentation framework that tracks who said what, under what conditions, with what evidence — then resolves the disagreements using real semantics, not vibes.

> 315 concepts | 410 claims | 26 papers | 2050 auto-classified stances

## What does this look like?

Point it at a corpus of papers on argumentation theory and ask: which claims survive scrutiny?

```
$ pks world extensions --semantics grounded

Backend: claim_graph
Semantics: grounded
Set comparison: elitist
Active claims: 410
Stances: 2050 total, 126 included as attacks, 0 vacuous, 1924 non-attack

Accepted (252 claims):
  measurement (11):
    Mayer_2020:claim2 = 0.87
    Mayer_2020:claim3 = 0.68
    ...
  observation (241):
    Alchourron_1985:claim4: The Levi identity defines revision in terms of contraction...
    Cayrol_2005:claim3: An indirect defeat for argument B is a sequence where an...
    Dung_1995:claim1: An argumentation framework is a pair AF = (AR, attacks)...
    Pollock_1987:claim1: Prima facie reasons create a presumption but can be defeated...
    ...

Rejected (158 claims):
  deKleer_1986:claim6: The ATMS has three primitive operations...
    defeated by: Dixon_1993:claim10, Dixon_1993:claim11, McDermott_1983:claim15
  deKleer_1986:claim8: Circular justifications are handled by...
    defeated by: Alchourron_1985:claim1, Dixon_1993:claim1, [60+ more]
```

410 claims from 26 papers. 2050 stance relations auto-classified by LLM. 126 attacks derived through preference ordering. The grounded extension — the set of claims that survive all attacks — contains 252. Every rejected claim shows exactly what defeated it and why.

## The problem

Scientific papers make claims. Often, those claims disagree. Sometimes the disagreement is real — two papers measured the same thing and got different numbers. Sometimes it's not — the claims hold under different conditions (male vs female speakers, different datasets, different experimental paradigms).

Across dozens of papers and hundreds of claims, you need machinery to tell the difference. And when the conflict is real, you need a principled way to resolve it — not "the most recent paper wins" but formal argumentation semantics grounded in decades of theory (Dung 1995, Pollock 1987, Modgil & Prakken 2018).

propstore is that machinery.

## Capabilities

**Conflict detection** — Z3-backed condition analysis classifies claim pairs as compatible, condition-disjoint, genuinely conflicting, or overlapping. Catches transitive conflicts through parameterization chains.
```bash
pks claim conflicts
```

**Formal argumentation** — Dung frameworks with grounded, preferred, and stable semantics. ASPIC+ preference ordering (elitist and democratic comparison). MaxSMT optimization for large conflict sets.
```bash
pks world extensions --semantics grounded
pks world extensions --semantics preferred --set-comparison democratic
```

**Counterfactual reasoning** — Remove or inject claims and see what changes.
```bash
pks world hypothetical --remove claim42
pks world hypothetical --add '{"id":"synth1","concept_id":"concept1","value":150,"conditions":[]}'
```

**Derivation and sensitivity** — Compute values through parameterization chains. Symbolic partial derivatives and elasticities via SymPy.
```bash
pks world derive concept5 task=speech
pks world sensitivity concept5 task=speech
```

**Algorithm equivalence** — AST canonicalization, SymPy algebraic comparison, and partial evaluation determine whether two papers describe the same computation differently (via [ast-equiv](../ast-equiv)).
```bash
pks claim compare claim50 claim51 -b T0=0.008
```

**Stance classification** — LLM-classified epistemic relations (rebuts, undercuts, undermines, supports, explains, supersedes) feed the argumentation framework automatically.
```bash
pks claim relate --all --model gemini/gemini-2.0-flash
```

**ATMS belief tracking** — Assumption-labeled truth maintenance with stability analysis, relevance detection, and intervention planning over bounded future environments.
```bash
pks world atms-status domain=argumentation
pks world atms-stability claim_id domain=argumentation
```

## Installation

Requires Python 3.11+. Uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync
uv run pks --help
```

Depends on [ast-equiv](../ast-equiv) (sibling package, resolved from `../ast-equiv` in `uv.lock`).

Optional for embeddings and stance classification: `uv pip install 'propstore[embeddings]'`

## Quick start

```bash
# Initialize and import claims from a papers collection
pks init
pks import-papers --papers-root ../papers/

# Validate and compile to a queryable sidecar database
pks build
# => Build complete: 315 concepts, 410 claims, 0 conflicts, 0 warnings

# What do we know?
pks world status
# => Concepts: 315  Claims: 410  Conflicts: 0

# Which claims survive formal scrutiny?
pks world extensions --semantics grounded

# What's the value of a concept under specific conditions?
pks world query fundamental_frequency
pks world bind task=speech speaker_sex=male fundamental_frequency

# Resolve a conflict
pks world resolve fundamental_frequency --strategy argumentation
```

## How it works

`pks build` runs a six-stage compiler pipeline:

1. **Form validation** — dimensional type signatures for all quantity kinds
2. **Concept validation** — ID uniqueness, deprecation chains, CEL type-checking, form compatibility
3. **Context validation** — hierarchy cycles, exclusion consistency, parent resolution
4. **Claim validation** — schema, concept resolution (by ID/name/alias), unit compatibility via dimensional analysis, algorithm AST cross-checks
5. **Sidecar build** — SQLite database with FTS5 indexes, content-hash addressed (incremental rebuilds)
6. **Conflict detection** — Z3 condition classification, direct and transitive conflicts

## Data model

Nine claim types, all with provenance tracking:

| Type | What it captures |
|------|-----------------|
| `parameter` | Numeric value for a concept under conditions |
| `equation` | Mathematical relationship with variable bindings |
| `measurement` | Perceptual or behavioral measurement |
| `observation` | Qualitative claim that resists parameterization |
| `model` | Parameterized equation system |
| `algorithm` | Procedural computation as Python function body |
| `mechanism` | Causal or explanatory process linking concepts |
| `comparison` | Comparative claim between approaches or systems |
| `limitation` | Known boundary, failure case, or applicability constraint |

Claims are scoped by CEL conditions (type-checked against the concept registry) and connected by stances (ASPIC+ attack/support taxonomy). See [docs/data-model.md](docs/data-model.md) for full YAML examples.

## Documentation

- [Data Model](docs/data-model.md) — concepts, forms, claim types, conditions, stances, contexts
- [Argumentation](docs/argumentation.md) — Dung frameworks, ASPIC+, MaxSMT, ATMS backend, semantic axes
- [CLI Reference](docs/cli-reference.md) — complete command reference
- [Integration](docs/integration.md) — research-papers-plugin workflow, reconciliation, embeddings, algorithm comparison

## Dependencies

| Package | Role |
|---------|------|
| [Z3](https://github.com/Z3Prover/z3) | SMT solving — condition disjointness, extension computation, MaxSMT |
| [SymPy](https://www.sympy.org/) | Symbolic math — parameterization, sensitivity, equation validation |
| [LinkML](https://linkml.io/) | Schema definition and JSON Schema generation |
| [click](https://click.palletsprojects.com/) | CLI framework |
| [ast-equiv](../ast-equiv) | Algorithm canonicalization and equivalence comparison |
| [litellm](https://github.com/BerriAI/litellm) | *(optional)* Unified LLM API for embeddings and stance classification |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | *(optional)* Vector search in SQLite |
