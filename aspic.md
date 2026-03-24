\# Implement ASPIC+ Argumentation Semantics in Propstore



\## Context



The propstore is a propositional knowledge store that manages scientific claims extracted from research papers. Claims can conflict (different values for the same concept under the same conditions), and the system needs to determine which claims survive scrutiny.



Currently, conflict resolution uses a naive weighted-score approach (`\_resolve\_stance` in `propstore/world/resolution.py`). This must be replaced with formal argumentation semantics grounded in Dung's abstract argumentation framework and the ASPIC+ structured argumentation framework.



The theoretical foundation is in `papers/Modgil\_2018\_GeneralAccountArgumentationPreferences/notes.md`. Read this file first — it contains the definitions, theorems, and design rationale you need. The key references in the collection are:



\- `papers/Dung\_1995\_AcceptabilityArguments/` — Dung's original abstract argumentation (grounded/preferred/stable extensions)

\- `papers/Modgil\_2018\_GeneralAccountArgumentationPreferences/` — ASPIC+ with preferences (THIS IS YOUR PRIMARY REFERENCE)

\- `papers/Modgil\_2014\_ASPICFrameworkStructuredArgumentation/` — Tutorial introduction to ASPIC+

\- `papers/Pollock\_1987\_DefeasibleReasoning/` — Rebutting vs undercutting defeaters



Read the notes.md for each before writing code.



\## What Exists Now



\### Stance graph (the attack/support relation)



The `claim\_stance` table stores pairwise epistemic relationships between claims:



```sql

CREATE TABLE claim\_stance (

&#x20;   claim\_id TEXT NOT NULL,           -- the source of the attack/support

&#x20;   target\_claim\_id TEXT NOT NULL,    -- the target

&#x20;   stance\_type TEXT NOT NULL,        -- rebuts|undercuts|undermines|supports|explains|supersedes

&#x20;   strength TEXT,                    -- strong|moderate|weak

&#x20;   conditions\_differ TEXT,

&#x20;   note TEXT,

&#x20;   resolution\_method TEXT,           -- nli\_first\_pass|nli\_second\_pass

&#x20;   resolution\_model TEXT,

&#x20;   embedding\_model TEXT,

&#x20;   embedding\_distance REAL,

&#x20;   pass\_number INTEGER,

&#x20;   confidence REAL

);

```



\*\*Stance types map to ASPIC+ attack types as follows:\*\*



| Propstore stance | ASPIC+ attack type | Preference-dependent? | Reference |

|---|---|---|---|

| `undermines` | Undermining (Def 8.i, p.11) | Yes — fails if attacker is strictly weaker | Def 9, p.12 |

| `rebuts` | Rebutting (Def 8.ii, p.11) | Yes — fails if attacker is strictly weaker | Def 9, p.12 |

| `undercuts` | Undercutting (Def 8.iii, p.11) | \*\*No — always succeeds\*\* | Def 9, p.12 |

| `supports` | Not in ASPIC+ (bipolar extension) | N/A | Cayrol 2005 |

| `explains` | Not in ASPIC+ (bipolar extension) | N/A | Cayrol 2005 |

| `supersedes` | Special case: unconditional defeat | No — always succeeds | Propstore-specific |



\### Current resolution (`propstore/world/resolution.py`)



The `\_resolve\_stance` function sums weighted scores across stance types and picks the claim with the highest net score. This has no formal backing. The full resolution dispatch is in `resolve()`, which selects between strategies: `recency`, `sample\_size`, `stance`, `override`.



\### Conflict detection (`propstore/conflict\_detector.py`)



The conflict detector identifies pairs of claims that bind to the same concept with incompatible values. It classifies pairs as `CONFLICT`, `PHI\_NODE`, `OVERLAP`, or `PARAM\_CONFLICT`. This module does NOT need to change — it detects conflicts. The argumentation module resolves them.



\### World model (`propstore/world/`)



\- `model.py` — `WorldModel`: read-only access to the sidecar SQLite

\- `bound.py` — `BoundWorld`: condition-bound view, filters active claims

\- `resolution.py` — `resolve()` and strategy implementations

\- `hypothetical.py` — `HypotheticalWorld`: in-memory overlay

\- `types.py` — dataclasses and protocols



\## What to Build



\### 1. Dung Extension Computation (`propstore/dung.py`)



New module. Implements Dung's abstract argumentation semantics over a directed attack graph.



\*\*Input:\*\* A set of arguments (claim IDs) and a defeat relation (directed edges where attacks survive preference filtering).



\*\*Output:\*\* Extensions under different semantics.



```python

@dataclass

class ArgumentationFramework:

&#x20;   """Dung's abstract argumentation framework AF = (Args, Defeats)."""

&#x20;   arguments: set\[str]         # claim IDs

&#x20;   defeats: dict\[str, set\[str]]  # arg -> set of args it defeats



def grounded\_extension(af: ArgumentationFramework) -> set\[str]:

&#x20;   """Compute the unique grounded extension.



&#x20;   The grounded extension is the least fixed point of the characteristic

&#x20;   function F(S) = {A | A is defended by S}.



&#x20;   Start with S = unattacked arguments. Iterate: add arguments defended

&#x20;   by S. Stop when fixed point reached.



&#x20;   Reference: Dung 1995, Definition 20 + Theorem 25.

&#x20;   """



def preferred\_extensions(af: ArgumentationFramework) -> list\[set\[str]]:

&#x20;   """Compute all preferred extensions.



&#x20;   A preferred extension is a maximal (w.r.t. set inclusion) admissible set.

&#x20;   An admissible set is conflict-free and defends all its members.



&#x20;   Reference: Dung 1995, Definition 8.

&#x20;   """



def stable\_extensions(af: ArgumentationFramework) -> list\[set\[str]]:

&#x20;   """Compute all stable extensions.



&#x20;   A stable extension is conflict-free and defeats every argument not in it.



&#x20;   Reference: Dung 1995, Definition 12.

&#x20;   WARNING: Stable extensions may not exist. Preferred always exist.

&#x20;   """

```



\*\*Implementation notes:\*\*



\- The grounded extension is polynomial (iterate characteristic function to fixed point).

\- Preferred/stable extension enumeration is coNP-complete in general. For propstore's scale (hundreds to low thousands of claims), brute-force enumeration with pruning is acceptable. If this becomes a bottleneck, implement the algorithm from Nofal et al. 2014 ("Algorithms for argumentation semantics"). But don't optimize prematurely — get it correct first.

\- The `defeats` dict is the FILTERED attack relation (after preference ordering converts attacks to defeats per Def 9, p.12). Raw attacks where the attacker is strictly weaker are excluded.



\### 2. Preference Ordering (`propstore/preference.py`)



New module. Computes the preference ordering over claims that determines which attacks succeed as defeats.



\*\*The core operation:\*\* Given two claims A and B where A attacks B, determine whether A is "not strictly weaker than" B. If A IS strictly weaker, the attack fails (does not become a defeat). If A is not strictly weaker, the attack succeeds as a defeat.



Implement BOTH preference principles from Modgil \& Prakken 2018:



\#### Last-link (Def 20, p.21)



Compare arguments by their most recent defeasible inference step. In propstore terms: compare claims by the quality of the methodology/source that produced them.



```python

def last\_link\_preference(claim\_a: dict, claim\_b: dict, set\_comparison: str = "elitist") -> bool:

&#x20;   """Return True if claim\_a is strictly preferred to claim\_b under last-link.



&#x20;   Last-link compares the 'last defeasible rules' — in propstore terms,

&#x20;   the immediate source/methodology of the claim.



&#x20;   Ordering signals (highest to lowest within each axis):

&#x20;   - Methodology: direct measurement > derived/computed > estimated > assumed

&#x20;   - Publication recency (as proxy for methodology currency)

&#x20;   - Journal impact / peer review status



&#x20;   Reference: Def 20, p.21

&#x20;   """

```



\#### Weakest-link (Def 21, p.21)



Compare arguments by their weakest component. In propstore terms: a claim is only as strong as its weakest input — the least reliable premise or the least rigorous inference step.



```python

def weakest\_link\_preference(claim\_a: dict, claim\_b: dict, set\_comparison: str = "elitist") -> bool:

&#x20;   """Return True if claim\_a is strictly preferred to claim\_b under weakest-link.



&#x20;   Weakest-link considers ALL components: premises AND inference steps.

&#x20;   A claim derived from 10 excellent sources but one terrible one is

&#x20;   weaker than a claim derived from 5 good sources.



&#x20;   Ordering signals:

&#x20;   - sample\_size (larger is stronger)

&#x20;   - uncertainty/uncertainty\_type (smaller uncertainty is stronger)

&#x20;   - provenance quality (peer-reviewed > preprint > informal)

&#x20;   - source paper recency



&#x20;   Reference: Def 21, p.21

&#x20;   """

```



\#### Set comparison (Def 19, p.21)



Both principles use a set comparison operator. Implement both options:



```python

def elitist\_comparison(set\_a: list\[float], set\_b: list\[float]) -> bool:

&#x20;   """Elitist: set\_a < set\_b iff EXISTS x in set\_a such that FORALL y in set\_b, x < y.



&#x20;   One bad apple spoils the barrel — if any element of set\_a is worse

&#x20;   than ALL elements of set\_b, set\_a loses.



&#x20;   Reference: Def 19, p.21

&#x20;   """



def democratic\_comparison(set\_a: list\[float], set\_b: list\[float]) -> bool:

&#x20;   """Democratic: set\_a < set\_b iff FORALL x in set\_a, EXISTS y in set\_b, x < y.



&#x20;   Every element of set\_a is beaten by some element of set\_b.



&#x20;   Reference: Def 19, p.21

&#x20;   """

```



\#### Mapping claim metadata to ordinal strength



The preference ordering operates on an ordinal scale. Define a function that maps claim metadata to a comparable strength value:



```python

def claim\_strength(claim: dict) -> float:

&#x20;   """Compute a scalar strength for preference ordering.



&#x20;   Compose from available metadata:

&#x20;   - sample\_size: log-scaled (sample of 1000 vs 10 matters; 10000 vs 1000 less so)

&#x20;   - uncertainty: inverse (lower uncertainty = stronger)

&#x20;   - recency: year from provenance, normalized

&#x20;   - confidence: from the stance classification (NLI pass confidence)



&#x20;   Claims with more metadata dimensions populated are NOT automatically stronger.

&#x20;   Missing metadata = no opinion on that axis, not weakness.



&#x20;   Return a float where higher = stronger. The absolute scale doesn't matter,

&#x20;   only the ordering.

&#x20;   """

```



\*\*Critical design decision:\*\* The preference ordering must satisfy the "reasonable" criterion (Def 18, p.16-17):

1\. Strict+firm arguments (claims from axiom premises with only strict inference) dominate all others

2\. Strict+firm arguments are never dominated by anything

3\. Strict continuation preserves preference



In propstore terms: claims with `conditions: \[]` (unconditional) derived from well-established sources with large sample sizes and low uncertainty should be treated as near-axiomatic. Claims with conditions, small samples, or high uncertainty are defeasible.



\### 3. Attack-to-Defeat Conversion (`propstore/argumentation.py`)



New module. The bridge between the stance graph (raw attacks) and the argumentation framework (filtered defeats).



```python

def build\_argumentation\_framework(

&#x20;   conn: sqlite3.Connection,

&#x20;   active\_claim\_ids: set\[str],

&#x20;   preference\_principle: str = "last\_link",  # or "weakest\_link"

&#x20;   set\_comparison: str = "elitist",          # or "democratic"

) -> ArgumentationFramework:

&#x20;   """Build a Dung AF from the stance graph filtered through preferences.



&#x20;   Steps:

&#x20;   1. Load all stances between active claims from claim\_stance table

&#x20;   2. For each attack stance (rebuts, undermines):

&#x20;      - Compute preference ordering between attacker and target

&#x20;      - If attacker is NOT strictly weaker: attack becomes defeat (include edge)

&#x20;      - If attacker IS strictly weaker: attack fails (exclude edge)

&#x20;      (Reference: Def 9, p.12)

&#x20;   3. For each undercutting stance:

&#x20;      - ALWAYS include as defeat (preference-independent)

&#x20;      (Reference: Def 9, p.12)

&#x20;   4. For each supersedes stance:

&#x20;      - ALWAYS include as defeat (propstore-specific, unconditional)

&#x20;   5. Support/explains stances are NOT attacks — exclude from defeat relation

&#x20;      (These could feed a bipolar framework in the future but not now)

&#x20;   6. Return ArgumentationFramework(arguments=active\_claim\_ids, defeats=defeat\_edges)

&#x20;   """



def compute\_justified\_claims(

&#x20;   conn: sqlite3.Connection,

&#x20;   active\_claim\_ids: set\[str],

&#x20;   semantics: str = "grounded",  # or "preferred" or "stable"

&#x20;   preference\_principle: str = "last\_link",

&#x20;   set\_comparison: str = "elitist",

) -> set\[str] | list\[set\[str]]:

&#x20;   """End-to-end: build AF, compute extensions, return justified claim IDs.



&#x20;   For grounded semantics: returns a single set (the unique grounded extension).

&#x20;   For preferred/stable: returns a list of sets (multiple possible extensions).

&#x20;   """

```



\### 4. Integration with Resolution (`propstore/world/resolution.py`)



Replace `\_resolve\_stance` with the argumentation-based resolver:



```python

def \_resolve\_argumentation(

&#x20;   claims: list\[dict],

&#x20;   world: WorldModel,

&#x20;   semantics: str = "grounded",

&#x20;   preference\_principle: str = "last\_link",

&#x20;   set\_comparison: str = "elitist",

) -> tuple\[str | None, str | None]:

&#x20;   """Resolve a conflicted concept using ASPIC+ argumentation semantics.



&#x20;   1. Get active claim IDs for this concept

&#x20;   2. Build ArgumentationFramework from stance graph + preferences

&#x20;   3. Compute extension(s) under chosen semantics

&#x20;   4. If exactly one claim for this concept survives in the extension: winner

&#x20;   5. If multiple survive: still conflicted (but reduced conflict set)

&#x20;   6. If none survive: underdetermined



&#x20;   Returns (winning\_claim\_id, reason\_string).

&#x20;   """

```



Add a new `ResolutionStrategy`:



```python

class ResolutionStrategy(Enum):

&#x20;   RECENCY = "recency"

&#x20;   SAMPLE\_SIZE = "sample\_size"

&#x20;   STANCE = "stance"               # legacy naive scoring — KEEP for backward compat

&#x20;   OVERRIDE = "override"

&#x20;   ARGUMENTATION = "argumentation" # NEW: formal ASPIC+ semantics

```



Wire it into `resolve()` alongside the existing strategies. Do NOT remove the existing `stance` strategy — keep it for backward compatibility but document it as deprecated.



\### 5. CLI Integration (`propstore/cli/compiler\_cmds.py`)



Add `--semantics`, `--preference`, and `--set-comparison` options to `world resolve`:



```

pks world resolve concept1 domain=example --strategy argumentation --semantics grounded --preference last\_link

pks world resolve concept1 domain=example --strategy argumentation --semantics preferred --preference weakest\_link --set-comparison democratic

```



Add a new `world extensions` command:



```

pks world extensions \[--semantics grounded|preferred|stable] \[--preference last\_link|weakest\_link] \[--set-comparison elitist|democratic] \[bindings...]

```



This should show the full extension(s) — all claims that survive — not just resolution of a single concept. This is the "what does the world look like if we accept this argumentation framework?" view.



\### 6. Sidecar Schema Extension (`propstore/build\_sidecar.py`)



Add a `defeat` table to cache the computed defeat relation:



```sql

CREATE TABLE defeat (

&#x20;   attacker\_id TEXT NOT NULL,

&#x20;   target\_id TEXT NOT NULL,

&#x20;   attack\_type TEXT NOT NULL,     -- rebuts|undermines|undercuts|supersedes

&#x20;   preference\_principle TEXT NOT NULL, -- last\_link|weakest\_link

&#x20;   set\_comparison TEXT NOT NULL,       -- elitist|democratic

&#x20;   attacker\_strength REAL,

&#x20;   target\_strength REAL,

&#x20;   FOREIGN KEY (attacker\_id) REFERENCES claim(id),

&#x20;   FOREIGN KEY (target\_id) REFERENCES claim(id)

);

```



This is a materialized view — recomputed on `pks build`. The extension computation queries this table rather than recomputing preferences on every query.



\## Testing Strategy



\### Unit tests for Dung semantics (`tests/test\_dung.py`)



Test against known examples from Dung 1995:



```python

def test\_grounded\_nixon\_diamond():

&#x20;   """Nixon diamond: A attacks B, B attacks A. Grounded = empty set."""

&#x20;   af = ArgumentationFramework(

&#x20;       arguments={"A", "B"},

&#x20;       defeats={"A": {"B"}, "B": {"A"}},

&#x20;   )

&#x20;   assert grounded\_extension(af) == set()



def test\_grounded\_unattacked\_wins():

&#x20;   """A attacks B, nothing attacks A. Grounded = {A}."""

&#x20;   af = ArgumentationFramework(

&#x20;       arguments={"A", "B"},

&#x20;       defeats={"A": {"B"}},

&#x20;   )

&#x20;   assert grounded\_extension(af) == {"A"}



def test\_preferred\_nixon\_diamond():

&#x20;   """Nixon diamond has two preferred extensions: {A} and {B}."""

&#x20;   af = ArgumentationFramework(

&#x20;       arguments={"A", "B"},

&#x20;       defeats={"A": {"B"}, "B": {"A"}},

&#x20;   )

&#x20;   exts = preferred\_extensions(af)

&#x20;   assert len(exts) == 2

&#x20;   assert {"A"} in exts

&#x20;   assert {"B"} in exts



def test\_stable\_may\_not\_exist():

&#x20;   """A attacks B, B attacks C, C attacks A. No stable extension."""

&#x20;   af = ArgumentationFramework(

&#x20;       arguments={"A", "B", "C"},

&#x20;       defeats={"A": {"B"}, "B": {"C"}, "C": {"A"}},

&#x20;   )

&#x20;   assert stable\_extensions(af) == \[]



def test\_grounded\_reinstatement():

&#x20;   """A attacks B, B attacks C. A reinstates C. Grounded = {A, C}."""

&#x20;   af = ArgumentationFramework(

&#x20;       arguments={"A", "B", "C"},

&#x20;       defeats={"A": {"B"}, "B": {"C"}},

&#x20;   )

&#x20;   assert grounded\_extension(af) == {"A", "C"}



def test\_grounded\_floating\_acceptance():

&#x20;   """A attacks B, A attacks C, B attacks C, C attacks B.

&#x20;   Grounded = {A}. C and B both defeated by A."""

&#x20;   af = ArgumentationFramework(

&#x20;       arguments={"A", "B", "C"},

&#x20;       defeats={"A": {"B", "C"}, "B": {"C"}, "C": {"B"}},

&#x20;   )

&#x20;   ext = grounded\_extension(af)

&#x20;   assert "A" in ext

&#x20;   assert "B" not in ext

&#x20;   assert "C" not in ext

```



\### Unit tests for preference ordering (`tests/test\_preference.py`)



```python

def test\_elitist\_comparison():

&#x20;   """Elitist: {1,5} < {3,4} because 1 < 3 and 1 < 4."""

&#x20;   assert elitist\_comparison(\[1, 5], \[3, 4]) is True



def test\_democratic\_comparison():

&#x20;   """Democratic: {1,2} < {3,4} because 1<3 and 2<4."""

&#x20;   assert democratic\_comparison(\[1, 2], \[3, 4]) is True



def test\_democratic\_not\_satisfied():

&#x20;   """Democratic: {1,5} NOT < {3,4} because 5 is not < any element of {3,4}."""

&#x20;   assert democratic\_comparison(\[1, 5], \[3, 4]) is False



def test\_undercutting\_always\_defeats():

&#x20;   """Undercutting attack succeeds regardless of preference ordering."""

&#x20;   # Even if attacker is strictly weaker, undercutting succeeds



def test\_rebutting\_fails\_if\_weaker():

&#x20;   """Rebutting attack by a weaker argument does not become a defeat."""

&#x20;   # Claim A (sample\_size=10) rebuts Claim B (sample\_size=1000)

&#x20;   # Under last-link with sample\_size as the ordering signal,

&#x20;   # A is strictly weaker, so the attack fails.

```



\### Integration tests (`tests/test\_argumentation\_integration.py`)



Build a small knowledge base with known conflicts and verify that:



1\. The grounded extension excludes defeated claims

2\. Preference ordering correctly filters weak attacks

3\. `pks world resolve --strategy argumentation` returns the expected winner

4\. The `defeat` table in the sidecar is populated correctly

5\. Undercutting attacks are never filtered by preferences

6\. Supersedes stances always produce defeats



\### Property tests with Hypothesis



```python

@given(st.lists(st.text(min\_size=1, max\_size=5), min\_size=2, max\_size=10, unique=True))

def test\_grounded\_is\_subset\_of\_every\_preferred(args):

&#x20;   """The grounded extension is a subset of every preferred extension.

&#x20;   Reference: Dung 1995, Theorem 25."""

&#x20;   # Generate random AF and verify this property



@given(...)

def test\_preferred\_is\_admissible(args):

&#x20;   """Every preferred extension is admissible (conflict-free + self-defending).

&#x20;   Reference: Dung 1995, Definition 8."""



@given(...)

def test\_stable\_implies\_preferred(args):

&#x20;   """Every stable extension is a preferred extension.

&#x20;   Reference: Dung 1995, Theorem 13."""

```



\## File Layout (new and modified)



```

propstore/

&#x20; dung.py                    # NEW: Dung extension computation

&#x20; preference.py              # NEW: preference ordering (last-link, weakest-link)

&#x20; argumentation.py           # NEW: attack→defeat conversion, AF construction

&#x20; world/

&#x20;   resolution.py            # MODIFIED: add ARGUMENTATION strategy

&#x20;   types.py                 # MODIFIED: add ResolutionStrategy.ARGUMENTATION

&#x20; build\_sidecar.py           # MODIFIED: add defeat table

&#x20; cli/

&#x20;   compiler\_cmds.py         # MODIFIED: add --semantics/--preference/--set-comparison to resolve; add world extensions



tests/

&#x20; test\_dung.py               # NEW

&#x20; test\_preference.py         # NEW

&#x20; test\_argumentation\_integration.py  # NEW

```



\## Constraints



1\. \*\*Do not break existing tests.\*\* Run the existing test suite before and after. The `stance` resolution strategy must continue to work unchanged.

2\. \*\*Do not modify the claim\_stance schema.\*\* The stance table is populated by `propstore/relate.py` via LLM classification. Your code consumes it, not produces it.

3\. \*\*Read the paper notes.\*\* The notes in `papers/Modgil\_2018\_GeneralAccountArgumentationPreferences/notes.md` contain every definition, theorem number, and page reference you need. If you're unsure about a formal detail, read the notes rather than guessing.

4\. \*\*The preference ordering is the hard part.\*\* Dung extension computation is well-understood algorithms. The novel design work is mapping propstore claim metadata (sample\_size, uncertainty, recency, confidence) to the ordinal preference ordering that ASPIC+ requires. Make this mapping explicit, configurable, and documented.

5\. \*\*Grounded extension is the default.\*\* It's unique, polynomial, and skeptical (only includes claims that survive all attacks). Preferred and stable are options for users who want credulous reasoning.

6\. \*\*Support stances are not attacks.\*\* The `supports` and `explains` stance types do NOT participate in defeat computation. They are recorded in the stance graph but excluded from the ArgumentationFramework. A future bipolar extension (per Cayrol 2005) may use them, but not this implementation.

7\. \*\*`supersedes` is unconditional defeat.\*\* Like undercutting, it always succeeds regardless of preferences. Unlike undercutting (which attacks an inference method), supersedes means "this claim replaces that claim entirely."

8\. \*\*Confidence threshold.\*\* Only stances with `confidence >= 0.5` should be treated as attacks. Lower-confidence stances are too uncertain to ground defeat relations. This threshold should be configurable.



\## Definition Reference (from Modgil \& Prakken 2018 notes)



These are the key formal definitions. Page numbers reference the paper.



\- \*\*Def 8 (p.11):\*\* Three attack types — undermining, rebutting, undercutting

\- \*\*Def 9 (p.12):\*\* Defeat = attack that survives preference filtering. Undercutting always succeeds. Rebutting/undermining succeed iff attacker is not strictly weaker.

\- \*\*Def 13 (p.14):\*\* Defeat-based conflict-free (DEPRECATED by this paper)

\- \*\*Def 14 (p.14):\*\* Attack-based conflict-free (RECOMMENDED — use this)

\- \*\*Def 18 (p.16):\*\* Reasonable argument ordering

\- \*\*Def 19 (p.21):\*\* Elitist and Democratic set comparisons

\- \*\*Def 20 (p.21):\*\* Last-link preference principle

\- \*\*Def 21 (p.21):\*\* Weakest-link preference principle

\- \*\*Prop 16 (p.19):\*\* Under reasonable orderings, attack-based and defeat-based conflict-free yield the same extensions

\- \*\*Thms 12-15 (p.18-19):\*\* Rationality postulates (sub-argument closure, strict rule closure, direct consistency, indirect consistency) — these are properties your implementation must satisfy, not things you implement directly

