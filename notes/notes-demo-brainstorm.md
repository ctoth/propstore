# Demo Brainstorm Session

## GOAL
Figure out what propstore can do vs what demos show, brainstorm creative demo ideas.

## DONE
- Read demos scout report (notes-demos-current.md) — complete inventory of physics demo
- Read propstore engine source: ATMS, hypothetical world, resolution strategies, Dung AF, sensitivity

## KEY OBSERVATIONS — What The Engine Can Do That Demos Don't Show

### 1. ATMS Engine (atms.py) — MASSIVELY underdemoed
The ATMS engine is the crown jewel nobody sees. It does:
- **Label propagation** — every datum gets minimal assumption sets (de Kleer 1986)
- **Nogood detection** — inconsistent assumption combos are tracked
- **Future analysis** — `future_environments()`, `node_future_statuses()` — "what COULD change if we added these assumptions?"
- **Stability analysis** — `is_stable()`, `concept_stability()` — "will this answer hold up?"
- **Status flip witnesses** — `status_flip_witnesses()` — "here's the MINIMAL set of assumptions that would change this answer"
- **Relevance analysis** — `relevant_queryables()` — "which questions are worth asking next?"
- **Why-out explanations** — `why_out()` — "this claim is OUT because..."
- **Could-become-in/out** — bounded replay over hypothetical futures

NONE of this is demoed. The physics demo only uses grounded extension argumentation.

### 2. Hypothetical World (hypothetical.py)
- Add/remove claims without mutating source
- `diff()` — compare base vs hypothetical value states
- Synthetic claims injection
- Demo only tests removing CODATA G — doesn't show adding competing claims or diff()

### 3. Resolution Strategies (resolution.py)
Five strategies exist:
- OVERRIDE — manual winner selection
- RECENCY — provenance date comparison
- SAMPLE_SIZE — largest sample wins
- ARGUMENTATION — Dung/ASPIC+/ATMS backends
- ATMS_SUPPORT — ATMS label-based resolution

Demo only uses ARGUMENTATION with grounded semantics. Never shows switching strategies or comparing outcomes across strategies.

### 4. Multiple Reasoning Backends
- CLAIM_GRAPH — direct Dung AF over claims
- STRUCTURED_PROJECTION — ASPIC+ structured argumentation
- ATMS — label-based resolution
Only CLAIM_GRAPH is demoed.

### 5. Sensitivity Analysis (sensitivity.py)
- Symbolic partial derivatives
- Numerical elasticity computation
- "Which input most influences this output?"
Physics demo tests it but doesn't showcase it visually or narratively.

### 6. Dung Extensions (dung.py)
- Grounded, preferred, stable, complete semantics all implemented
- Only grounded is demoed

## CURRENT STATE OF DEMOS
- ONE demo (physics), CLI-only, no notebooks
- Tests prove features work but don't SHOW them
- No narrative walkthrough
- No visualization
- No domain beyond physics

## REAL CONFLICTS IN PHYSICS KNOWLEDGE BASE (from sidecar queries)

222 total claims, 112 concepts, 16 stances.

### Genuine value disagreements (CONFLICT rows):
1. **Speed of light (concept26)** — 4 claims, GOLD MINE:
   - CODATA: 299,792,458 m/s (modern, unconditional)
   - Maxwell 1865 claim2: 310,740,000 m/s (from EM measurement, unconditional)
   - Maxwell 1865 claim3: 314,858,000 m/s (Fizeau, regime=='classical')
   - Maxwell 1865 claim4: 298,000,000 m/s (Foucault, regime=='classical')
   - PLUS derivable from epsilon_0 + mu_0 → PARAM_CONFLICT at 299,792,458.000007

2. **Gravitational constant G (concept11)** — 4 claims:
   - CODATA: 6.6743e-11
   - Boys: 6.658e-11
   - Cavendish (original): 6.754e-11
   - Cavendish 1798 paper claim: 6.74e-11
   - Already has supersession stances (CODATA > Boys > Cavendish)

3. **Boltzmann constant (concept51)** — 2 claims:
   - CODATA: 1.380649e-23
   - Goldstein 2019 paper: 1.381e-23
   - NO stances exist between these!

4. **Planck constant (concept52)** — 2 claims:
   - CODATA: 6.62607015e-34
   - de Broglie 1924: 6.545e-34
   - NO stances exist between these!

5. **Cavendish concept1** — 2 claims: 158.0 vs 0.73 (likely torsion balance readings)
6. **Cavendish concept103** — 2 claims: 900 vs 420 (conditioned on regime=='classical')

### Condition-based splits (PHI_NODE):
- concept12 (g): earth/moon/mars/jupiter
- concept14 (mass): earth/moon/mars/jupiter
- concept15 (radius): earth/moon/mars/jupiter

### Existing stances (16 total):
- 3 supersession chains (G constant, ether→Maxwell)
- 1 rebuttal (vdW rebuts ideal gas)
- 2 undercuts (newtonian_breakdown, fma_limitation undercut F=ma)
- Multiple supports (Einstein→Lorentz, Maxwell→EM waves, etc.)

### MISSING stances (opportunities):
- Boltzmann: CODATA should supersede Goldstein 2019
- Planck: CODATA should supersede de Broglie 1924
- Speed of light: CODATA should supersede Maxwell's measurements
- Cavendish claim14 (G=6.74e-11) has no stance vs the other G values

### KEY INSIGHT FOR DEMOS:
Speed of light is THE demo concept. It has:
- 4 competing measurements from different eras
- A derivation path (from epsilon_0 + mu_0)
- Param conflicts (derived vs measured)
- Condition-gated claims (regime=='classical')
- Support chains (Maxwell→EM waves→c derivation)
- An attack chain (ether theory undermines EM interpretation)
- Missing stances that could be added live

## API EXPLORATION FINDINGS (from Python REPL testing)

### How to load the world (friction point #1)
- `WorldModel(path)` does NOT work — requires a `Repository` object
- Must do: `Repository(Path('knowledge'))` then `WorldModel(repo)`
- Then `w.bind()` to get a BoundWorld
- **Friction:** 3 objects to construct before you can query anything. A convenience constructor like `WorldModel.from_path('knowledge/')` would help notebooks.

### What works well from Python:
- `w.claims_for(concept_id)` — returns list of claim dicts ✓
- `w.bind(**conditions)` → BoundWorld ✓
- `bound.value_of(concept_id)` → ValueResult with status + claims ✓
- `bound.resolved_value(concept_id)` → ResolvedResult ✓ (needs policy on BoundWorld)
- `bound.derived_value(concept_id)` → DerivedResult with value, formula, inputs ✓
- `bound.explain(claim_id)` → list of stance dicts ✓
- `bound.atms_engine()` → ATMSEngine ✓
- `engine.claim_status(claim_id)` → ATMSInspection ✓
- `HypotheticalWorld(bound, remove=[...], add=[...])` → overlay ✓
- `hyp.diff()` → dict of changed concepts ✓
- `analyze_sensitivity(w, concept_id, bound)` → SensitivityResult ✓
- `build_knowledge_graph(w, bound)` → graph with DOT export ✓

### What's awkward:
1. **Resolution requires policy at bind time:** `w.bind(policy=RenderPolicy(strategy=...))`. You can't switch strategy on an existing BoundWorld — need to rebind. Makes side-by-side comparison verbose.
2. **w.conflicts() takes no args** — can't filter by concept. Must get all conflicts and filter yourself.
3. **Sensitivity returns None when inputs are conflicted** — correct but means most concepts can't be analyzed without overrides. Only concepts with all-determined inputs work (like c from ε₀/μ₀).
4. **ATMS: all premise claims are OUT/MISSING_SUPPORT** — this is correct (they're assumptions, not derived), but it means ATMS status is most interesting for DERIVED nodes, not for the raw measurement claims you'd want to showcase first.

### Key data findings:
- **concept26 (c):** 4 claims, NO supersession stances → argumentation can't resolve (all 4 survive grounded extension)
- **concept11 (G):** 4 claims, 3 supersession stances, but Cavendish_1798_DensityOfEarth:claim2 has NO stance → 2 survive grounded extension (not 1!)
- **Recency fails everywhere** — provenance_json has no `date` fields → "tied recency ()"
- **Derivation c = 1/√(ε₀·μ₀) = 299,792,458.000007** works perfectly
- **Sensitivity: ε₀ and μ₀ both have elasticity -0.5** (correct, equal influence)
- **KE sensitivity works with overrides** — velocity elasticity 2.0, mass elasticity 1.0 (correct)
- **Graph: 334 nodes (112 concepts, 222 claims), 85 edges, DOT export works**
- **Hypothetical diff only detects VALUE SET changes** — adding a confirming measurement (same value) shows 0 changes. Need disagreeing value.

### What this means for demos:
1. **Speed of light is great for:** query, derivation, sensitivity, hypothetical, graph
2. **Speed of light DOESN'T work for:** argumentation resolution (no stances), recency (no dates), ATMS stability (premise nodes)
3. **G constant is great for:** argumentation (has stances), explain, supersession chains
4. **G constant has a gap:** Cavendish paper claim has no stance
5. **Before building demos that show argumentation resolving c, we'd need to add stances**
6. **Before demos that show recency, we'd need dates in provenance**

## MORE API FINDINGS (round 2)

### Chain query:
- `w.chain_query(concept_id, strategy, **bindings)` — NOT `w.chain_query(concept_id, bound)`
- Returns ChainResult with `.result`, `.steps`, `.bindings_used`, `.unresolved_dependencies`
- c derivation works: finds path through ε₀, μ₀ → 299,792,458.000007
- Gravitational force fails: G (concept11) has 2 surviving claims → chain can't resolve
- KE fails: concept1 (mass) is conflicted in the KB

### Extensions:
- **Grounded extension: FAST, works perfectly** — 217 of 222 claims survive
- **5 defeated claims:** boys_G, cavendish_G, ether_theory, ideal_gas_law, newton_second_law
- Three defeat types visible: supersession (G), rebuttal (ideal gas), undercutting (F=ma)
- **Preferred/stable: BLOW UP** — 222 claims too many, timed out at 2 minutes
- Demo must use grounded only, or scope to subset for preferred/stable

### Explain chains:
- `explain(claim_id)` shows stances FROM that claim (what it attacks/supports)
- To see what DEFEATED a claim, call explain on its attackers
- **Ether theory cycle is the best narrative:**
  - ether_theory --undermines--> maxwell_em_waves (0.7)
  - maxwell_em_waves --supersedes--> ether_theory (0.99)
  - maxwell_em_waves --supports--> speed_of_light_from_em (0.95)
  - Mutual attack resolved by preference ordering (0.99 > 0.7)

### Friction summary for notebook authors:
1. 3 objects to construct (Path → Repository → WorldModel → bind → BoundWorld)
2. Can't switch resolution strategy on existing BoundWorld — must rebind
3. Sensitivity needs all inputs determined — returns None otherwise
4. Chain query needs all dependencies resolvable
5. Preferred/stable extensions don't scale to 222 claims
6. explain() direction is from attacker perspective, not victim

### What WORKS GREAT for demos today (no KB changes needed):
1. Query conflicted concepts (c, G)
2. Grounded extension — shows 5 defeated claims with 3 defeat types
3. Ether theory explain chain — beautiful mutual attack narrative
4. c derivation from ε₀, μ₀
5. Sensitivity on c (equal ε₀/μ₀ influence)
6. Sensitivity with overrides (KE: velocity matters 2x more than mass)
7. Hypothetical remove + diff
8. Hypothetical add (synthetic claims)
9. Condition binding (location=earth/moon/mars/jupiter for g, mass, radius)
10. Graph export to DOT
11. ATMS claim status (shows support quality distinctions)

### What NEEDS KB changes to demo:
1. Argumentation resolving c → needs supersession stances
2. Recency resolution → needs dates in provenance
3. G resolving to exactly 1 winner → needs stance for Cavendish paper claim
4. Preferred/stable extensions → needs smaller claim set or scoped computation

## NOTEBOOK PLAN (based on what actually works)

Separate notebooks, each self-contained:

### Notebook 1: "Conflicting Measurements" (concept26 + concept11)
- Load world, query c and G
- Show 4 competing c values, 4 competing G values
- Explain where they came from (provenance)
- This is the "wow, it holds disagreement" notebook

### Notebook 2: "Who Wins? Resolution Strategies"
- G constant: argumentation resolves to 2 survivors (CODATA + paper claim)
- Show grounded extension: 5 defeated claims
- Explain WHY each was defeated (supersession, rebuttal, undercutting)
- The ether theory mutual attack story

### Notebook 3: "Derivation and Sensitivity"
- Derive c from ε₀, μ₀
- Sensitivity: both contribute equally
- KE with overrides: velocity matters 2x
- Chain query for c

### Notebook 4: "What If? Hypothetical Reasoning"
- Remove CODATA c, see what survives
- Add a synthetic competing measurement
- diff() to see what changed
- "What if we retracted the ether theory?" → ether comes back?

### Notebook 5: "The ATMS: What Knows What"
- ATMS claim status for c claims
- Support quality distinctions
- (If we can find interesting derived nodes)

### Notebook 6: "Conditions: Same Concept, Different Worlds"
- g on earth/moon/mars/jupiter
- regime=classical activating historical measurements
- Context switching

## INFRASTRUCTURE FINDINGS (round 3)

- propstore-demos/physics has NO notebooks directory, NO jupyter dependency
- propstore/__init__.py is EMPTY — no public API surface at all
- Users must import internal modules directly: `from propstore.world.model import WorldModel`
- The project is entirely CLI-driven today
- .gitignore excludes *.pdf and *.png only

### Implications for notebook plan:
1. Need to add jupyter to physics pyproject.toml dependencies
2. Need to create notebooks/ directory
3. Every notebook needs the same 3-line boilerplate to get a BoundWorld
4. No convenience API exists — could be friction point worth noting but NOT fixing yet
5. Q said "don't change anything yet" — exploration/understanding only

## PHASE 0 COMPLETE — API FIXES

All 4 friction fixes implemented and verified (1057 tests pass):

1. **from_path()** — `WorldModel.from_path('knowledge')` works
2. **strategy switching** — `bound.resolved_value('concept11', strategy=ResolutionStrategy.ARGUMENTATION)` works
3. **concept_name()** — `w.concept_name('concept26')` → 'speed_of_light', `w.concept_names()` → dict of 112
4. **filtered conflicts** — `w.conflicts('concept26')` → 10 rows vs 32 total

Public API exports in `propstore/__init__.py`: WorldModel, BoundWorld, HypotheticalWorld, RenderPolicy, ResolutionStrategy, ReasoningBackend, SyntheticClaim, ValueResult, DerivedResult, ResolvedResult.

NEXT: Commit, then Phase 1 (notebook infrastructure), then Phase 2 (notebooks).

## WHY PREFERRED/STABLE BLOW UP

`complete_extensions()` in dung.py (line 172) enumerates ALL subsets:
```python
for size in range(len(args) + 1):
    for subset in combinations(sorted(args), size):
```
With 222 args → 2^222 subsets. That's brute force, polynomial in nothing.

Grounded is fast: fixed-point iteration of characteristic function. Polynomial.

There IS a z3 backend (dung_z3.py) for complete/preferred/stable that uses constraint
solving instead of enumeration. TESTED: handles 224 args in 0.04s. Now the default.

## COMPLETED WORK

### Phase 0: API fixes (committed to propstore)
- WorldModel.from_path() — skip Repository ceremony
- Public exports in __init__.py
- resolved_value() accepts per-call strategy kwarg
- concept_name() / concept_names()
- conflicts(concept_id) filtering
- Fixed build_sidecar crash on non-Eq sympy expressions
- Defaulted extension computation to z3 backend (was brute_force, 2^n explosion)

### Physics KB improvements (committed to propstore-demos/physics)
- Relativistic momentum + KE claims (regime=='relativistic')
- Relativistic rebuts classical stances
- CODATA c supersedes Maxwell x3 stances
- 224 claims, 21 stances, 10 defeated in grounded extension

### Notebooks (committed to propstore-demos/notebooks)
All 6 execute cleanly. Key findings from outputs:
- Grounded: 214 survive, 10 defeated
- Preferred: 1 extension (same as grounded)
- Stable: 3 extensions — ether/Maxwell ambiguity creates multiple worldviews
- c resolves to CODATA via argumentation (sole survivor)
- Removing maxwell_em_waves brings ether_theory BACK in hypothetical
- sample_size resolves G where argumentation can't (CODATA has n=12000)

### Friction points fixed along the way:
- Windows junction vs symlink: symlink works fine, junction was unnecessary
- PYTHONUTF8=1 needed for notebook execution on Windows
- Hung preferred/stable processes from brute_force backend locked sidecar file
