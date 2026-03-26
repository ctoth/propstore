# Argumentation

propstore uses formal argumentation to resolve disagreements between scientific claims. This document covers the reasoning backends, conflict detection, and belief tracking systems.

## Dung abstract argumentation

The core engine implements Dung's abstract argumentation framework AF = (Args, Defeats). Given a set of arguments (claims) and a defeat relation (derived from stances filtered through preference ordering), it computes:

- **Grounded extension** — the unique minimal complete extension (skeptical reasoning)
- **Preferred extensions** — maximal admissible sets (credulous reasoning)
- **Stable extensions** — conflict-free sets that defeat all external arguments

Two backends: brute-force enumeration (`dung.py`) and Z3 SAT encoding (`dung_z3.py`) for scalability.

## Claim-graph bridge

The bridge layer (`argumentation.py`) converts raw stances into a Dung AF:

1. Load stances between active claims with confidence above threshold
2. Undercutting and supersedes attacks always become defeats
3. Rebutting and undermining attacks become defeats only if the attacker is at least as strong as the target (elitist comparison) or the attacking set is at least as strong (democratic comparison)
4. Build the Dung AF from surviving defeats
5. Compute extensions under chosen semantics

propstore currently ships one reasoning backend: a claim-graph backend. It builds a Dung AF over active claim rows, uses heuristic claim metadata for preferences, and uses claim conditions only to determine activity. This is inspired by Dung and ASPIC+ style reasoning, but it is not a full structured-argument ASPIC+ implementation.

## Conflict detection

When two claims bind to the same concept, the conflict detector classifies them:

| Class | Meaning |
|-------|---------|
| `COMPATIBLE` | Values consistent (within tolerance or overlapping ranges). Not reported. |
| `PHI_NODE` | Values differ, conditions fully disjoint (Z3-verified). Not a conflict — they describe different regimes. |
| `CONFLICT` | Values differ, conditions identical or both unconditional. Genuine disagreement. |
| `OVERLAP` | Values differ, conditions partially overlapping. Needs investigation. |
| `PARAM_CONFLICT` | Conflict detected via parameterization chain: claim A and claim B individually consistent, but deriving through a shared formula produces contradictory outputs. |

Condition disjointness is checked via Z3 satisfiability. Category concepts get EnumSorts, quantity concepts get Reals, boolean concepts get Bools. Condition pairs are first grouped into equivalence classes by structural similarity, so Z3 is only called once per unique condition pattern.

## MaxSMT conflict resolution

For large conflict sets, `maxsat_resolver.py` uses Z3's Optimize with weighted soft constraints to find the maximally consistent subset of claims. Each claim gets a soft constraint weighted by its strength score — the solver keeps as many strong claims as possible while eliminating all conflicts.

## Semantic axes

- `reasoning_backend` selects the argumentation backend used when a render policy asks for argumentation-based conflict resolution.
- `claim_graph` remains the default backend and preserves the current claim-row projection and behavior.
- `structured_projection` is a first structured-argument projection over active claims plus exact support metadata. It is a bridge toward ASPIC+, not full ASPIC+ execution.
- `atms` is a global label/nogood propagation backend over the active belief space. It is an ATMS-style engine pass, not a full de Kleer runtime manager, not AGM entrenchment, and not full ASPIC+.
- `resolution_strategy` selects how to pick a winner when a conflicted concept still has multiple active claims after belief-space reasoning.
- `comparison` selects the preference-comparison rule used inside the claim-graph argumentation backend.

## ATMS backend

The ATMS (Assumption-based Truth Maintenance System) backend provides label propagation and nogood pruning over the active belief space. It tracks exact support only — which assumptions justify each claim.

The `atms` backend does not expose Dung extensions. `pks world extensions --backend atms` is rejected by design. Use the ATMS-native commands instead:

```bash
# Show ATMS status, support quality, and essential support
pks world atms-status domain=argumentation

# Show which exactly supported claims hold in the current bound environment
pks world atms-context domain=argumentation

# Run ATMS label self-checks
pks world atms-verify domain=argumentation

# Show bounded future environments for a claim or concept
pks world atms-futures claim_id domain=argumentation --queryable framework=general

# Explain whether an OUT status is missing support or nogood-pruned
pks world atms-why-out claim_id domain=argumentation --queryable framework=general

# Show bounded stability and witness futures
pks world atms-stability claim_id domain=argumentation --queryable framework=general

# Show which queryables matter, with witness flips
pks world atms-relevance claim_id domain=argumentation --queryable framework=general

# Show bounded additive intervention plans over declared queryables
pks world atms-interventions claim_id domain=argumentation --target-status IN --queryable framework=general

# Show next-query suggestions derived from actual minimal intervention plans
pks world atms-next-query claim_id domain=argumentation --target-status IN --queryable framework=general
```

### Capabilities by layer

The labelled core and `atms` backend track exact support only. Semantically compatible Z3 activation and context visibility are preserved for activity, but not upgraded into exact labels or unconditional support by fiat.

- **Label propagation** — `TRUE`, `IN`, and `OUT` statuses exposed directly from propagated labels
- **Essential support** — shared core across compatible supporting environments
- **Justification traces** — nogood provenance exposed for inspection
- **Future analysis** — bounded candidate environments that could activate or block exact support; `OUT` statuses distinguish missing support from nogood-pruned
- **Stability and relevance** — whether a claim keeps the same status across all bounded consistent future replays, and which declared queryables can flip it
- **Intervention planning** — minimal bounded additive queryable sets that reach a requested target status; next-query suggestions derived from actual minimal plans

These remain bounded replay over admitted future queryables. This is not AGM revision, entrenchment maintenance, or full structured-argument dynamics.

## Extensions CLI

```bash
# Show the grounded extension (claims that survive all attacks)
pks world extensions --semantics grounded

# Preferred extensions under condition bindings
pks world extensions domain=argumentation --semantics preferred

# Stable extensions with democratic set comparison
pks world extensions --semantics stable --set-comparison democratic
```

The grounded extension is unique and represents the skeptically justified claims. Preferred extensions are maximal admissible sets — each represents a credulous position. Stable extensions (when they exist) are the strongest: conflict-free sets that defeat every non-member.

## Future work

AGM-style revision semantics and full ASPIC+ execution remain future work. The current implementation maps claims 1:1 to arguments (flat structure). Full ASPIC+ per Modgil & Prakken 2018 Defs 3-7 requires: strict/defeasible rules, recursive argument building from sub-arguments, and last-link/weakest-link comparison (Defs 20-21).
