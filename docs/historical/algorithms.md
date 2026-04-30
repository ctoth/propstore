\# Algorithm Claims: AST-Based Procedural Knowledge for Propstore



\## Context



You are working on `propstore`, a field compiler — a system that compiles scattered, inconsistent, multi-notation research literature into a typed, scoped, consistency-checked structure. The codebase is a Python package (`propstore/`) with a Click CLI (`pks`), a deterministic compiler pipeline, SQLite sidecar output, Z3-based condition classification, SymPy-based parameterization checking, and a WorldModel reasoner.



Read and understand the existing codebase before making changes. Key files:



\- `propstore/validate\_claims.py` — claim validation, claim types, LoadedClaimFile

\- `propstore/conflict\_detector.py` — COMPATIBLE/CONFLICT/PHI\_NODE/OVERLAP/PARAM\_CONFLICT classification

\- `propstore/build\_sidecar.py` — SQLite sidecar compilation

\- `propstore/world\_model.py` — WorldModel, BoundWorld, HypotheticalWorld, value\_of, derived\_value

\- `propstore/cel\_checker.py` — CEL condition type-checking

\- `propstore/z3\_conditions.py` — Z3 translation of CEL for satisfiability

\- `propstore/description\_generator.py` — auto-summary generation

\- `propstore/propagation.py` — SymPy evaluation for parameterization chains

\- `schema/claim.linkml.yaml` — LinkML schema for claims

\- `schema/generated/claim.schema.json` — generated JSON Schema

\- `forms/\*.yaml` — form definitions (frequency, pressure, duration\_ratio, etc.)

\- `design-spikes/` — hand-written claim extraction attempts showing schema gaps



The five existing claim types: parameter, equation, observation, model, measurement.



Observation claims are a prose dump for everything that resists the other four types. Many "DOESN'T FIT" annotations in the design spikes describe procedural/algorithmic knowledge that has no structured representation. This feature fills that gap.



\## What to Build



A sixth claim type: \*\*algorithm\*\*. Algorithm claims represent procedural knowledge as Python AST with variable bindings to propstore concepts.



The key insight is a \*\*four-tier equivalence comparison ladder\*\*:



1\. \*\*Canonical AST match\*\* — alpha-normalize variable names to concept IDs, light canonicalization, compare AST dumps. Definitional equivalence.

2\. \*\*Bytecode match\*\* — compile both bodies after alpha-normalization, compare normalized bytecode instruction sequences. Catches constant folding, range normalization, peephole optimizations that CPython's compiler handles for free.

3\. \*\*Partial-evaluated bytecode match\*\* — substitute known parameter values from `BoundWorld.value\_of()` into the algorithm body before compilation. Two algorithms that differ only in how they compute a constant that propstore already knows collapse to identical residual programs. \*\*This connects the parametric and procedural layers.\*\*

4\. \*\*Structural similarity\*\* — tree edit distance fallback for near-misses. Reports a \[0, 1] score for triage.



Each tier is strictly more powerful than the previous. The ConflictRecord reports which tier matched, so you know the strength of the equivalence evidence.



Tier 3 is what makes this non-trivial: the comparison becomes \*\*condition-dependent\*\*. Under `sample\_rate=44100`, two algorithms might be equivalent (because a branch involving sample rate collapses after substitution). Under `sample\_rate=16000`, they might diverge. The conflict detector would report: COMPATIBLE under 44.1kHz, CONFLICT under 16kHz. That's a φ-node on \*algorithms\*.



\### 1. Data Model



An algorithm claim in YAML:



```yaml

\- id: claim42

&#x20; type: algorithm

&#x20; name: "spectral peak picker"

&#x20; concept: concept15          # the concept this algorithm computes/implements

&#x20; stage: peak\_picking         # pipeline stage identifier (free text, for grouping)

&#x20; body: |

&#x20;   peaks = \[]

&#x20;   for i in range(1, len(spectrum) - 1):

&#x20;       if spectrum\[i] > spectrum\[i-1] and spectrum\[i] > spectrum\[i+1]:

&#x20;           if spectrum\[i] > threshold:

&#x20;               peaks.append((i \* freq\_resolution, spectrum\[i]))

&#x20;   return peaks

&#x20; variables:

&#x20;   - symbol: spectrum

&#x20;     concept: concept20       # magnitude\_spectrum

&#x20;     role: input

&#x20;   - symbol: threshold

&#x20;     concept: concept21       # peak\_threshold\_db

&#x20;     role: parameter

&#x20;   - symbol: freq\_resolution

&#x20;     concept: concept22       # frequency\_resolution

&#x20;     role: parameter

&#x20;   - symbol: peaks

&#x20;     concept: concept15       # spectral\_peak\_list

&#x20;     role: output

&#x20; conditions:

&#x20;   - "sample\_rate == 44100"

&#x20; provenance:

&#x20;   paper: Wang\_2003\_IndustrialStrengthFingerprinting

&#x20;   page: 3

&#x20;   section: "Peak Picking"

```



Key fields:

\- `body`: valid Python source code (function body, no def line). Parsed by `ast.parse()`. Must parse without errors.

\- `variables`: list of variable bindings mapping local names in `body` to concept IDs. Same structure as equation claim variables but with `role` extended to include `input`, `output`, `parameter`, `intermediate`.

\- `stage`: optional pipeline stage name for grouping algorithm claims into ordered pipelines.

\- `concept`: the concept this algorithm produces or implements (similar to equation's dependent variable).

\- `name`: human-readable name for the algorithm.



\### 2. Schema Changes



\*\*`schema/claim.linkml.yaml`\*\*: Add algorithm-specific fields to the Claim class:



\- `body` (string, optional) — Python source for algorithm claims

\- `stage` (string, optional) — pipeline stage identifier



The `variables` field already exists (from equation claims). The `name` field already exists (from model claims). The `concept` field already exists (from parameter claims). Reuse them.



Add `algorithm` to the `ClaimType` enum.



Regenerate JSON Schema after changes: `uv run python schema/generate.py`



\### 3. AST Validation (`propstore/validate\_claims.py`)



Add `\_validate\_algorithm()` called from the type dispatch in `validate\_claims()`.



Checks:

\- `body` is present and is a string

\- `body` parses via `ast.parse(body, mode='exec')` without SyntaxError

\- `variables` is present and non-empty

\- Each variable's `concept` exists in concept\_registry

\- Each variable's `symbol` actually appears as a `Name` node in the parsed AST (warning if not — might be unused binding)

\- Every `ast.Name` node in the body that isn't a Python builtin or standard library name should be in the variables list (warning for unbound names — helps catch extraction errors)

\- `concept` field references an existing concept



Python builtins to exclude from unbound-name checking: `range`, `len`, `enumerate`, `zip`, `map`, `filter`, `sorted`, `reversed`, `min`, `max`, `sum`, `abs`, `int`, `float`, `str`, `bool`, `list`, `dict`, `set`, `tuple`, `print`, `True`, `False`, `None`, `append`, `extend`, `items`, `keys`, `values`. Also standard math names: `log`, `exp`, `sqrt`, `sin`, `cos`, `pi`. Keep this as a frozenset constant.



\### 4. AST Canonicalization and Comparison (`propstore/ast\_canonicalizer.py`) — NEW FILE



This module implements the four-tier comparison ladder. All operations are deterministic and never execute algorithm bodies.



\#### Tier 1: Canonical AST



\##### `parse\_algorithm(body: str) -> ast.Module`

Parse body string into AST. Raises `AlgorithmParseError` on failure.



\##### `extract\_names(tree: ast.Module) -> set\[str]`

Walk the AST and return all `ast.Name` node ids.



\##### `normalize\_to\_concepts(tree: ast.Module, bindings: dict\[str, str]) -> ast.Module`

Deep-copy the AST. Replace every `ast.Name` where `node.id` is in `bindings` with the concept ID. This is the alpha-normalization step.



```python

class ConceptNormalizer(ast.NodeTransformer):

&#x20;   def \_\_init\_\_(self, bindings: dict\[str, str]):

&#x20;       # bindings: local\_name -> concept\_id

&#x20;       self.bindings = bindings



&#x20;   def visit\_Name(self, node):

&#x20;       if node.id in self.bindings:

&#x20;           return ast.copy\_location(

&#x20;               ast.Name(id=self.bindings\[node.id], ctx=node.ctx),

&#x20;               node

&#x20;           )

&#x20;       return node

```



\##### `canonicalize(tree: ast.Module) -> ast.Module`

Light normalization pass on the AST to catch trivial syntactic variants:



1\. \*\*Range normalization\*\*: `range(0, N, 1)` → `range(N)`, `range(0, N)` → `range(N)`

2\. \*\*Boolean normalization\*\*: `x == True` → `x`, `x == False` → `not x`

3\. \*\*Constant folding\*\*: evaluate `ast.BinOp` on two `ast.Constant` nodes

4\. \*\*Strip comments and docstrings\*\*: remove `ast.Expr(ast.Constant(str))` nodes

5\. \*\*Normalize comparison chains\*\*: sort commutative operands (`a + b` same as `b + a` for `Add` and `Mult`)



This does NOT need to be comprehensive. CPython's compiler catches more in Tier 2.



\##### `canonical\_dump(body: str, bindings: dict\[str, str]) -> str`

Convenience: parse → normalize\_to\_concepts → canonicalize → `ast.dump()`. This is the string stored in the sidecar for comparison.



\##### `structural\_match(dump\_a: str, dump\_b: str) -> bool`

Exact match on canonical dumps.



\#### Tier 2: Bytecode Comparison



CPython's compiler already does constant folding, peephole optimization, and dead code elimination. Two ASTs that differ syntactically but compute identically often converge at the bytecode level.



```python

\# These are different ASTs but identical bytecode:

x = 2 \* 3 \* n        # BinOp(BinOp(2, Mult, 3), Mult, n)

x = 6 \* n            # BinOp(6, Mult, n)

\# CPython constant-folds 2\*3 → 6



\# Also identical bytecode:

for i in range(0, N, 1): ...

for i in range(N): ...

```



\##### `normalized\_bytecode(body: str, bindings: dict\[str, str]) -> list\[tuple\[str, object]]`



1\. Alpha-normalize the source: apply `normalize\_to\_concepts` then `ast.unparse` back to source

2\. `compile(normalized\_source, '<claim>', 'exec')` — safe because we never `exec()`, only inspect

3\. Extract instruction sequence via `dis.get\_instructions(code)`

4\. Normalize the instruction tuples: for `LOAD\_FAST`/`STORE\_FAST`/`LOAD\_NAME`/`STORE\_NAME`, replace argval with concept ID from bindings. For `LOAD\_CONST`, keep the constant value. For all other opcodes, keep opname only.



```python

import dis



def normalized\_bytecode(body: str, bindings: dict\[str, str]) -> list\[tuple\[str, object]]:

&#x20;   """Compile alpha-normalized source and extract name-normalized bytecode."""

&#x20;   tree = parse\_algorithm(body)

&#x20;   tree = normalize\_to\_concepts(tree, bindings)

&#x20;   ast.fix\_missing\_locations(tree)

&#x20;   source = ast.unparse(tree)

&#x20;   code = compile(source, '<claim>', 'exec')

&#x20;   result = \[]

&#x20;   for instr in dis.get\_instructions(code):

&#x20;       if instr.opname in ('LOAD\_FAST', 'STORE\_FAST', 'LOAD\_NAME',

&#x20;                           'STORE\_NAME', 'LOAD\_GLOBAL', 'STORE\_GLOBAL'):

&#x20;           result.append((instr.opname, instr.argval))

&#x20;       elif instr.opname == 'LOAD\_CONST':

&#x20;           result.append((instr.opname, instr.argval))

&#x20;       else:

&#x20;           result.append((instr.opname, None))

&#x20;   return result

```



\##### `bytecode\_match(body\_a: str, bindings\_a: dict, body\_b: str, bindings\_b: dict) -> bool`

Exact match on normalized bytecode sequences.



\*\*Important\*\*: bytecode is CPython-version-dependent. Both bodies are always compiled in the same process, so comparison is valid within a session. Do NOT store bytecode in the sidecar — store the canonical AST dump (portable) and recompute bytecode comparison at query time (cheap).



\#### Tier 3: Partial-Evaluated Bytecode



This is the key innovation. Propstore already knows parameter values under current condition bindings via `BoundWorld.value\_of()`. Substituting those known values before compilation lets CPython's constant folder collapse parameter-dependent expressions, making two algorithms that differ only in how they compute a known constant produce identical residual bytecode.



\##### `ParameterSubstituter(ast.NodeTransformer)`



```python

class ParameterSubstituter(ast.NodeTransformer):

&#x20;   def \_\_init\_\_(self, known\_values: dict\[str, float]):

&#x20;       # concept\_id -> resolved numeric value

&#x20;       self.known\_values = known\_values



&#x20;   def visit\_Name(self, node):

&#x20;       if node.id in self.known\_values:

&#x20;           return ast.copy\_location(

&#x20;               ast.Constant(value=self.known\_values\[node.id]),

&#x20;               node

&#x20;           )

&#x20;       return node

```



\##### `partial\_eval\_bytecode(body: str, bindings: dict\[str, str], known\_values: dict\[str, float]) -> list\[tuple\[str, object]]`



Full normalization chain:

1\. \*\*Alpha-normalize\*\*: replace local names with concept IDs via `normalize\_to\_concepts`

2\. \*\*Partial-evaluate\*\*: apply `ParameterSubstituter` with known values — only substitute concept IDs that appear in `known\_values` AND have determined scalar values. If `value\_of` returns conflicted or no\_claims for a concept, leave that name alone. The residual is always at least as compilable as the original.

3\. \*\*Unparse → compile\*\*: `ast.unparse()` → `compile()` — CPython does constant folding on the residual

4\. \*\*Extract bytecode\*\*: same `dis.get\_instructions` normalization as Tier 2



```python

def partial\_eval\_bytecode(

&#x20;   body: str,

&#x20;   bindings: dict\[str, str],

&#x20;   known\_values: dict\[str, float],

) -> list\[tuple\[str, object]]:

&#x20;   """Alpha-normalize, substitute known values, compile, extract bytecode."""

&#x20;   tree = parse\_algorithm(body)

&#x20;   tree = normalize\_to\_concepts(tree, bindings)

&#x20;   tree = ParameterSubstituter(known\_values).visit(tree)

&#x20;   ast.fix\_missing\_locations(tree)

&#x20;   source = ast.unparse(tree)

&#x20;   code = compile(source, '<claim>', 'exec')

&#x20;   result = \[]

&#x20;   for instr in dis.get\_instructions(code):

&#x20;       if instr.opname in ('LOAD\_FAST', 'STORE\_FAST', 'LOAD\_NAME',

&#x20;                           'STORE\_NAME', 'LOAD\_GLOBAL', 'STORE\_GLOBAL'):

&#x20;           result.append((instr.opname, instr.argval))

&#x20;       elif instr.opname == 'LOAD\_CONST':

&#x20;           result.append((instr.opname, instr.argval))

&#x20;       else:

&#x20;           result.append((instr.opname, None))

&#x20;   return result

```



\##### `partial\_eval\_match(body\_a, bindings\_a, body\_b, bindings\_b, known\_values) -> bool`

Exact match on partial-evaluated bytecode sequences.



\*\*Safety note\*\*: this never executes code. `compile()` produces a code object; we only inspect it via `dis`. The algorithm body could contain anything — we only read the bytecode, we don't run it.



\#### Tier 4: Structural Similarity



\##### `structural\_similarity(tree\_a: ast.Module, tree\_b: ast.Module) -> float`

Tree edit distance normalized to \[0, 1]. Use a simple node-sequence comparison:

1\. Flatten both trees via `ast.walk()` into sequences of node type names

2\. Compute longest common subsequence length

3\. Return `2 \* lcs\_len / (len(seq\_a) + len(seq\_b))`



This is crude but sufficient for triage. A similarity > 0.9 with different canonical dumps suggests near-miss that warrants investigation.



\#### Top-Level Comparison Entry Point



\##### `compare\_algorithms(claim\_a, claim\_b, known\_values=None) -> ComparisonResult`



```python

@dataclass

class ComparisonResult:

&#x20;   equivalent: bool

&#x20;   tier: int          # 1-4, which tier established the result (0 if not equivalent)

&#x20;   tier\_name: str     # "canonical\_ast" | "bytecode" | "partial\_eval" | "none"

&#x20;   similarity: float  # structural similarity \[0, 1] — always computed

```



Runs the tiers in order, short-circuiting on first match:

1\. Try canonical AST match → if equal, return `ComparisonResult(True, 1, "canonical\_ast", 1.0)`

2\. Try bytecode match → if equal, return `ComparisonResult(True, 2, "bytecode", 1.0)`

3\. If `known\_values` provided, try partial-eval match → if equal, return `ComparisonResult(True, 3, "partial\_eval", 1.0)`

4\. Compute structural similarity → return `ComparisonResult(False, 0, "none", similarity)`



\### 5. Conflict Detection (`propstore/conflict\_detector.py`)



Add algorithm claim comparison. Algorithm claims are grouped by `concept` (what they compute), similar to parameter claims grouped by concept.



\#### Collection function:

```python

def \_collect\_algorithm\_claims(claim\_files) -> dict\[str, list\[dict]]:

&#x20;   """Group algorithm claims by concept across all claim files."""

```



\#### Comparison logic in `detect\_conflicts()`:



For each concept with 2+ algorithm claims:

1\. For each pair (i, j), call `compare\_algorithms(claim\_i, claim\_j)` — without known\_values at this stage (Tier 3 is used by WorldModel at query time, not during static conflict detection)

2\. If `result.equivalent` → COMPATIBLE (skip)

3\. If not equivalent → classify conditions using existing `\_classify\_conditions()`

4\. Emit ConflictRecord with:

&#x20;  - `value\_a` and `value\_b` set to `"algorithm:{claim\_id}"` (not the full AST dump)

&#x20;  - `derivation\_chain` set to `f"similarity:{result.similarity:.3f} tier:{result.tier\_name}"`



The conflict detector uses Tiers 1-2 only (static analysis, no condition bindings needed). Tier 3 (partial evaluation) is used by the WorldModel at query time when condition bindings are available.



\#### WorldModel-level comparison with Tier 3:



When comparing algorithm claims through `BoundWorld`, the comparison has access to `value\_of()` results for parameter concepts. This is where Tier 3 fires:



1\. Collect known values: for each concept referenced in the algorithm's variables with role `parameter`, call `self.value\_of(concept\_id)`. If status is `determined`, add to `known\_values`.

2\. Call `compare\_algorithms(claim\_a, claim\_b, known\_values=known\_values)`

3\. This enables condition-dependent equivalence: the same two algorithms might be COMPATIBLE under one binding and CONFLICT under another.



\### 6. Sidecar Storage (`propstore/build\_sidecar.py`)



In `\_populate\_claims()`, handle `type == "algorithm"`:



\- Store `body` in a new `body` column on the claim table (TEXT)

\- Store `canonical\_ast` — the output of `canonical\_dump()` — in a new column (TEXT). This is the portable representation for cross-session comparison.

\- Store `stage` in a new `stage` column (TEXT, nullable)

\- Store `name` in the existing `name` column (already there from model claims)

\- Store `concept` in the existing `concept\_id` column



Add the columns to `\_create\_claim\_tables()`:



```sql

body TEXT,

canonical\_ast TEXT,

stage TEXT,

```



Add index: `CREATE INDEX idx\_claim\_stage ON claim(stage);`



Do NOT store bytecode in the sidecar. Bytecode is CPython-version-dependent and must be recomputed at query time. The canonical AST dump is the stable, portable representation.



\### 7. WorldModel (`propstore/world\_model.py`)



The `value\_of()` method currently checks numeric value agreement. For algorithm claims, "agreement" means equivalence as determined by the comparison ladder.



Extend `value\_of()` in `BoundWorld`: when active claims for a concept are all algorithm type, use `compare\_algorithms()` with Tier 3 (partial evaluation using known parameter values from the current bindings). If all pairs match → determined. If any pair differs → conflicted. If mixed types (some parameter, some algorithm) → treat as separate evidence channels, don't cross-compare.



The Tier 3 wiring:



```python

def \_collect\_known\_values(self, variable\_concepts: list\[str]) -> dict\[str, float]:

&#x20;   """Resolve parameter values for partial evaluation."""

&#x20;   known = {}

&#x20;   for cid in variable\_concepts:

&#x20;       vr = self.value\_of(cid)

&#x20;       if vr.status == "determined":

&#x20;           val = vr.claims\[0].get("value") if vr.claims else None

&#x20;           if val is not None:

&#x20;               known\[cid] = float(val)

&#x20;   return known

```



Add `algorithm\_for(concept\_id)` method to BoundWorld:

```python

def algorithm\_for(self, concept\_id: str) -> dict | None:

&#x20;   """Return the active algorithm claim for a concept, or None."""

&#x20;   active = self.active\_claims(concept\_id)

&#x20;   algo\_claims = \[c for c in active if c.get("type") == "algorithm"]

&#x20;   if len(algo\_claims) == 1:

&#x20;       return algo\_claims\[0]

&#x20;   return None  # zero or conflicted

```



\### 8. Description Generator (`propstore/description\_generator.py`)



Add handler for algorithm claims:



```python

elif ctype == "algorithm":

&#x20;   name = claim.get("name", "unnamed algorithm")

&#x20;   stage = claim.get("stage", "")

&#x20;   stage\_str = f" \[{stage}]" if stage else ""

&#x20;   return f"Algorithm: {name}{stage\_str}"

```



\### 9. CLI Extensions



\#### `pks claim compare <claim\_id\_a> <claim\_id\_b> \[bindings...]`



New subcommand. Loads both claims from the sidecar. Runs the full comparison ladder. Reports:

\- Equivalence result and which tier matched

\- Structural similarity score

\- If bindings provided and Tier 3 fires: which parameter values were substituted

\- Side-by-side diff of the canonical ASTs (unified diff of `ast.dump(indent=2)` output)



Example output:

```

claim42 vs claim87: EQUIVALENT (tier 2: bytecode)

&#x20; structural similarity: 1.000

&#x20; canonical AST: DIFFERENT (trivial syntactic variant)

&#x20; bytecode: MATCH (CPython constant folding resolved difference)

```



Or with partial evaluation:

```

claim42 vs claim87: EQUIVALENT (tier 3: partial\_eval)

&#x20; bindings: sample\_rate=44100

&#x20; substituted: concept22=44100 (frequency\_resolution)

&#x20; structural similarity: 0.847

&#x20; canonical AST: DIFFERENT

&#x20; bytecode: DIFFERENT

&#x20; partial-eval bytecode: MATCH (parameter substitution collapsed branch)

```



\#### `pks world algorithms \[--stage <stage>] \[--concept <concept\_id>] \[bindings...]`



List algorithm claims active under bindings, optionally filtered by stage or concept. Groups by stage if stage is set, showing the pipeline structure.



\### 10. Tests (`tests/test\_ast\_canonicalizer.py`) — NEW FILE



TDD. Write these tests FIRST, before implementation.



```python

class TestParseAlgorithm:

&#x20;   def test\_valid\_python\_parses(self):

&#x20;       """Simple valid Python body parses without error."""



&#x20;   def test\_syntax\_error\_raises(self):

&#x20;       """Invalid Python raises AlgorithmParseError."""



&#x20;   def test\_empty\_body\_raises(self):

&#x20;       """Empty string raises AlgorithmParseError."""



class TestExtractNames:

&#x20;   def test\_finds\_all\_names(self):

&#x20;       """Extracts all Name nodes from a body."""



&#x20;   def test\_ignores\_builtins\_in\_extraction(self):

&#x20;       """range, len, etc. are still extracted (filtering is caller's job)."""



class TestNormalizeToConcepts:

&#x20;   def test\_replaces\_bound\_names(self):

&#x20;       """Variables in bindings are replaced with concept IDs."""



&#x20;   def test\_preserves\_unbound\_names(self):

&#x20;       """Names not in bindings (builtins, etc.) are unchanged."""



&#x20;   def test\_handles\_nested\_scopes(self):

&#x20;       """Names inside list comprehensions and nested loops are replaced."""



&#x20;   def test\_preserves\_attribute\_access(self):

&#x20;       """x.append is not renamed even if x is bound — only the Name node."""



class TestCanonicalize:

&#x20;   def test\_range\_normalization(self):

&#x20;       """range(0, N, 1) canonicalizes to range(N)."""



&#x20;   def test\_strips\_docstrings(self):

&#x20;       """Leading string expression is removed."""



&#x20;   def test\_constant\_folding(self):

&#x20;       """2 \* 3 becomes 6 in the AST."""



&#x20;   def test\_commutative\_normalization(self):

&#x20;       """a + b and b + a produce the same canonical form."""



class TestAlphaEquivalence:

&#x20;   def test\_same\_algorithm\_different\_names(self):

&#x20;       """Two bodies implementing peak picking with different variable names

&#x20;       but same concept bindings produce identical canonical dumps."""

&#x20;       body\_a = """

peaks = \[]

for i in range(1, len(spectrum) - 1):

&#x20;   if spectrum\[i] > threshold:

&#x20;       peaks.append(i)

"""

&#x20;       body\_b = """

output = \[]

for k in range(1, len(X) - 1):

&#x20;   if X\[k] > T:

&#x20;       output.append(k)

"""

&#x20;       bindings\_a = {"spectrum": "concept1", "threshold": "concept2", "peaks": "concept3"}

&#x20;       bindings\_b = {"X": "concept1", "T": "concept2", "output": "concept3"}



&#x20;       dump\_a = canonical\_dump(body\_a, bindings\_a)

&#x20;       dump\_b = canonical\_dump(body\_b, bindings\_b)

&#x20;       assert dump\_a == dump\_b



&#x20;   def test\_different\_algorithms\_different\_dumps(self):

&#x20;       """Structurally different algorithms produce different dumps."""



&#x20;   def test\_same\_structure\_different\_concepts\_different\_dumps(self):

&#x20;       """Same code but different concept bindings are NOT equivalent."""



class TestBytecodeComparison:

&#x20;   def test\_constant\_folding\_equivalence(self):

&#x20;       """'x = 2 \* 3 \* n' and 'x = 6 \* n' match at bytecode tier."""

&#x20;       body\_a = "x = 2 \* 3 \* n"

&#x20;       body\_b = "x = 6 \* n"

&#x20;       bindings = {"x": "concept1", "n": "concept2"}

&#x20;       assert bytecode\_match(body\_a, bindings, body\_b, bindings)



&#x20;   def test\_range\_normalization\_at\_bytecode(self):

&#x20;       """'for i in range(0, N, 1)' and 'for i in range(N)' match at bytecode."""

&#x20;       body\_a = "for i in range(0, N, 1):\\n    x = i"

&#x20;       body\_b = "for i in range(N):\\n    x = i"

&#x20;       bindings = {"N": "concept1", "x": "concept2"}

&#x20;       assert bytecode\_match(body\_a, bindings, body\_b, bindings)



&#x20;   def test\_different\_logic\_no\_bytecode\_match(self):

&#x20;       """Genuinely different algorithms don't match at any tier."""

&#x20;       body\_a = "x = a + b"

&#x20;       body\_b = "x = a \* b"

&#x20;       bindings = {"x": "concept1", "a": "concept2", "b": "concept3"}

&#x20;       assert not bytecode\_match(body\_a, bindings, body\_b, bindings)



&#x20;   def test\_ast\_different\_but\_bytecode\_same(self):

&#x20;       """Bodies that differ at AST level but match at bytecode level."""

&#x20;       body\_a = "x = 1 + 2 + y"

&#x20;       body\_b = "x = 3 + y"

&#x20;       bindings = {"x": "concept1", "y": "concept2"}

&#x20;       assert canonical\_dump(body\_a, bindings) != canonical\_dump(body\_b, bindings)

&#x20;       assert bytecode\_match(body\_a, bindings, body\_b, bindings)



class TestPartialEvaluation:

&#x20;   def test\_known\_parameter\_substituted(self):

&#x20;       """When a parameter concept has a known value, it's substituted

&#x20;       before compilation, enabling equivalence detection."""

&#x20;       body\_a = "thresh = sample\_rate / 4\\nresult = amplitude > thresh"

&#x20;       body\_b = "thresh = 11025\\nresult = amplitude > thresh"

&#x20;       bindings\_a = {"sample\_rate": "concept10", "amplitude": "concept11",

&#x20;                     "thresh": "concept12", "result": "concept13"}

&#x20;       bindings\_b = {"amplitude": "concept11",

&#x20;                     "thresh": "concept12", "result": "concept13"}

&#x20;       known = {"concept10": 44100.0}

&#x20;       assert partial\_eval\_match(body\_a, bindings\_a, body\_b, bindings\_b, known)



&#x20;   def test\_different\_known\_value\_diverges(self):

&#x20;       """Same algorithms with different parameter values are NOT equivalent."""

&#x20;       body\_a = "thresh = sample\_rate / 4\\nresult = amplitude > thresh"

&#x20;       body\_b = "thresh = 11025\\nresult = amplitude > thresh"

&#x20;       bindings\_a = {"sample\_rate": "concept10", "amplitude": "concept11",

&#x20;                     "thresh": "concept12", "result": "concept13"}

&#x20;       bindings\_b = {"amplitude": "concept11",

&#x20;                     "thresh": "concept12", "result": "concept13"}

&#x20;       known = {"concept10": 16000.0}

&#x20;       assert not partial\_eval\_match(body\_a, bindings\_a, body\_b, bindings\_b, known)



&#x20;   def test\_no\_known\_values\_skips\_partial\_eval(self):

&#x20;       """Without known values, partial eval is same as plain bytecode."""

&#x20;       body = "x = a + b"

&#x20;       bindings = {"x": "c1", "a": "c2", "b": "c3"}

&#x20;       bc\_plain = normalized\_bytecode(body, bindings)

&#x20;       bc\_partial = partial\_eval\_bytecode(body, bindings, {})

&#x20;       assert bc\_plain == bc\_partial



&#x20;   def test\_partial\_eval\_never\_executes(self):

&#x20;       """A body with dangerous code compiles but never runs."""

&#x20;       body = "import os\\nos.system('rm -rf /')\\nx = param"

&#x20;       bindings = {"param": "concept1", "x": "concept2"}

&#x20;       known = {"concept1": 42.0}

&#x20;       result = partial\_eval\_bytecode(body, bindings, known)

&#x20;       assert isinstance(result, list)



&#x20;   def test\_undetermined\_concept\_left\_as\_name(self):

&#x20;       """Concepts without determined values are NOT substituted."""

&#x20;       body = "x = a + b"

&#x20;       bindings = {"x": "c1", "a": "c2", "b": "c3"}

&#x20;       known = {"c2": 5.0}

&#x20;       result = partial\_eval\_bytecode(body, bindings, known)

&#x20;       load\_names = \[name for op, name in result

&#x20;                     if op in ('LOAD\_NAME', 'LOAD\_FAST', 'LOAD\_GLOBAL')

&#x20;                     and name == 'c3']

&#x20;       assert len(load\_names) > 0



class TestComparisonLadder:

&#x20;   def test\_tier\_1\_match\_short\_circuits(self):

&#x20;       """Canonical AST match returns tier 1 without computing bytecode."""

&#x20;       body = "x = a + b"

&#x20;       bindings = {"x": "c1", "a": "c2", "b": "c3"}

&#x20;       claim\_a = {"body": body, "variables": \_bindings\_to\_vars(bindings)}

&#x20;       claim\_b = {"body": body, "variables": \_bindings\_to\_vars(bindings)}

&#x20;       result = compare\_algorithms(claim\_a, claim\_b)

&#x20;       assert result.equivalent

&#x20;       assert result.tier == 1

&#x20;       assert result.tier\_name == "canonical\_ast"



&#x20;   def test\_tier\_2\_match\_when\_ast\_differs(self):

&#x20;       """Bytecode match catches constant folding that AST misses."""

&#x20;       claim\_a = {"body": "x = 2 \* 3 \* n",

&#x20;                  "variables": \_bindings\_to\_vars({"x": "c1", "n": "c2"})}

&#x20;       claim\_b = {"body": "x = 6 \* n",

&#x20;                  "variables": \_bindings\_to\_vars({"x": "c1", "n": "c2"})}

&#x20;       result = compare\_algorithms(claim\_a, claim\_b)

&#x20;       assert result.equivalent

&#x20;       assert result.tier == 2

&#x20;       assert result.tier\_name == "bytecode"



&#x20;   def test\_tier\_3\_match\_with\_known\_values(self):

&#x20;       """Partial eval catches parameter-dependent equivalence."""

&#x20;       claim\_a = {"body": "x = rate / 4",

&#x20;                  "variables": \_bindings\_to\_vars({"x": "c1", "rate": "c2"})}

&#x20;       claim\_b = {"body": "x = 11025",

&#x20;                  "variables": \_bindings\_to\_vars({"x": "c1"})}

&#x20;       known = {"c2": 44100.0}

&#x20;       result = compare\_algorithms(claim\_a, claim\_b, known\_values=known)

&#x20;       assert result.equivalent

&#x20;       assert result.tier == 3

&#x20;       assert result.tier\_name == "partial\_eval"



&#x20;   def test\_no\_match\_returns\_similarity(self):

&#x20;       """Non-equivalent algorithms get similarity score."""

&#x20;       claim\_a = {"body": "x = a + b",

&#x20;                  "variables": \_bindings\_to\_vars({"x": "c1", "a": "c2", "b": "c3"})}

&#x20;       claim\_b = {"body": "for i in range(n):\\n    x = i \* a",

&#x20;                  "variables": \_bindings\_to\_vars({"x": "c1", "a": "c2", "n": "c4"})}

&#x20;       result = compare\_algorithms(claim\_a, claim\_b)

&#x20;       assert not result.equivalent

&#x20;       assert result.tier == 0

&#x20;       assert result.tier\_name == "none"

&#x20;       assert 0.0 <= result.similarity <= 1.0



class TestStructuralSimilarity:

&#x20;   def test\_identical\_trees\_score\_one(self):

&#x20;       """Same tree has similarity 1.0."""



&#x20;   def test\_completely\_different\_trees\_score\_low(self):

&#x20;       """Unrelated algorithms score below 0.5."""



&#x20;   def test\_minor\_variant\_scores\_high(self):

&#x20;       """An algorithm with one extra line scores above 0.8."""



class TestConflictDetection:

&#x20;   def test\_alpha\_equivalent\_algorithms\_compatible(self):

&#x20;       """Two algorithm claims that are alpha-equivalent -> COMPATIBLE."""



&#x20;   def test\_bytecode\_equivalent\_algorithms\_compatible(self):

&#x20;       """Two algorithm claims that differ at AST but match bytecode -> COMPATIBLE."""



&#x20;   def test\_different\_algorithms\_same\_conditions\_conflict(self):

&#x20;       """Different algorithms for same concept, same conditions -> CONFLICT."""



&#x20;   def test\_different\_algorithms\_different\_conditions\_phi\_node(self):

&#x20;       """Different algorithms for same concept, different conditions -> PHI\_NODE."""



&#x20;   def test\_conflict\_record\_includes\_tier(self):

&#x20;       """ConflictRecord derivation\_chain reports comparison tier and similarity."""



class TestValidation:

&#x20;   def test\_valid\_algorithm\_claim\_passes(self):

&#x20;       """Well-formed algorithm claim validates."""



&#x20;   def test\_missing\_body\_fails(self):

&#x20;       """Algorithm claim without body fails validation."""



&#x20;   def test\_unparseable\_body\_fails(self):

&#x20;       """Algorithm claim with syntax error in body fails validation."""



&#x20;   def test\_unbound\_variable\_warning(self):

&#x20;       """Variable in body not in bindings list produces warning."""



&#x20;   def test\_unused\_binding\_warning(self):

&#x20;       """Variable in bindings not found in body produces warning."""



class TestSidecar:

&#x20;   def test\_algorithm\_claim\_stored\_with\_canonical\_ast(self):

&#x20;       """After build, claim table has body and canonical\_ast columns populated."""



&#x20;   def test\_canonical\_ast\_deterministic(self):

&#x20;       """Same body + bindings always produces same canonical\_ast."""



&#x20;   def test\_no\_bytecode\_in\_sidecar(self):

&#x20;       """Sidecar does NOT store bytecode (CPython-version-dependent)."""

```



Helper for test readability:

```python

def \_bindings\_to\_vars(bindings: dict\[str, str]) -> list\[dict]:

&#x20;   """Convert {name: concept\_id} to variables list format."""

&#x20;   return \[{"symbol": name, "concept": cid} for name, cid in bindings.items()]

```



Also add algorithm claim tests to existing test files:

\- `tests/test\_conflict\_detector.py` — TestAlgorithmConflicts class

\- `tests/test\_validate\_claims.py` — TestAlgorithmClaimValidation class

\- `tests/test\_build\_sidecar.py` — TestAlgorithmClaimTable class

\- `tests/test\_world\_model.py` — TestAlgorithmWorldModel class (including Tier 3 condition-dependent equivalence)



\### 11. Hypothesis Property Tests (`tests/test\_ast\_canonicalizer.py`)



```python

@given(

&#x20;   name\_a=st.from\_regex(r"\[a-z]\[a-z0-9\_]{0,8}", fullmatch=True),

&#x20;   name\_b=st.from\_regex(r"\[a-z]\[a-z0-9\_]{0,8}", fullmatch=True),

&#x20;   concept\_id=st.from\_regex(r"concept\\d{1,4}", fullmatch=True),

)

def test\_alpha\_equivalence\_is\_symmetric(name\_a, name\_b, concept\_id):

&#x20;   """If rename(a->c) == rename(b->c), then rename(b->c) == rename(a->c)."""



@given(body=st.from\_regex(r"x = \\d+\\n", fullmatch=True))

def test\_canonicalize\_idempotent(body):

&#x20;   """Canonicalizing twice produces same result as once."""



@given(

&#x20;   bindings\_a=st.dictionaries(

&#x20;       st.from\_regex(r"\[a-z]{1,5}", fullmatch=True),

&#x20;       st.from\_regex(r"concept\\d{1,3}", fullmatch=True),

&#x20;       min\_size=1, max\_size=5,

&#x20;   ),

)

def test\_normalization\_preserves\_tree\_structure(bindings\_a):

&#x20;   """Normalization changes Name nodes but not tree shape (same number of nodes)."""



@given(

&#x20;   val=st.floats(min\_value=1.0, max\_value=1e6, allow\_nan=False, allow\_infinity=False),

)

def test\_partial\_eval\_with\_value\_equals\_constant\_substitution(val):

&#x20;   """Substituting a known value and folding equals writing the constant directly."""

&#x20;   body\_param = "x = param + 1"

&#x20;   body\_const = f"x = {val} + 1"

&#x20;   bindings = {"x": "c1", "param": "c2"}

&#x20;   bindings\_const = {"x": "c1"}

&#x20;   known = {"c2": val}

&#x20;   bc\_partial = partial\_eval\_bytecode(body\_param, bindings, known)

&#x20;   bc\_const = normalized\_bytecode(body\_const, bindings\_const)

&#x20;   assert bc\_partial == bc\_const



@given(

&#x20;   val\_a=st.floats(min\_value=1.0, max\_value=1000.0, allow\_nan=False, allow\_infinity=False),

&#x20;   val\_b=st.floats(min\_value=1.0, max\_value=1000.0, allow\_nan=False, allow\_infinity=False),

)

def test\_different\_partial\_eval\_values\_produce\_different\_bytecode(val\_a, val\_b):

&#x20;   """Different known values produce different residual bytecode."""

&#x20;   assume(abs(val\_a - val\_b) > 0.001)

&#x20;   body = "x = param \* 2"

&#x20;   bindings = {"x": "c1", "param": "c2"}

&#x20;   bc\_a = partial\_eval\_bytecode(body, bindings, {"c2": val\_a})

&#x20;   bc\_b = partial\_eval\_bytecode(body, bindings, {"c2": val\_b})

&#x20;   assert bc\_a != bc\_b



@given(

&#x20;   body=st.sampled\_from(\[

&#x20;       "x = a + b",

&#x20;       "x = a \* b",

&#x20;       "x = a - b",

&#x20;       "for i in range(n):\\n    x = i + a",

&#x20;   ]),

&#x20;   bindings=st.just({"x": "c1", "a": "c2", "b": "c3", "n": "c4"}),

)

def test\_comparison\_ladder\_reflexive(body, bindings):

&#x20;   """Every algorithm is equivalent to itself at Tier 1."""

&#x20;   vars\_list = \_bindings\_to\_vars(bindings)

&#x20;   claim = {"body": body, "variables": vars\_list}

&#x20;   result = compare\_algorithms(claim, claim)

&#x20;   assert result.equivalent

&#x20;   assert result.tier == 1

```



\## Implementation Order



1\. Write `tests/test\_ast\_canonicalizer.py` (TDD — all tests fail)

2\. Write `propstore/ast\_canonicalizer.py` — Tier 1 first (parse, normalize, canonicalize, dump)

3\. Make Tier 1 tests pass

4\. Add Tier 2 (bytecode comparison) to `ast\_canonicalizer.py`

5\. Make Tier 2 tests pass

6\. Add Tier 3 (partial evaluation) to `ast\_canonicalizer.py`

7\. Make Tier 3 tests pass

8\. Add `ComparisonResult` and `compare\_algorithms()` top-level entry point

9\. Make comparison ladder tests pass

10\. Add `\_validate\_algorithm()` to `propstore/validate\_claims.py`

11\. Add algorithm tests to `tests/test\_validate\_claims.py`

12\. Add algorithm handling to `propstore/build\_sidecar.py`

13\. Add algorithm tests to `tests/test\_build\_sidecar.py`

14\. Add algorithm comparison to `propstore/conflict\_detector.py` (Tiers 1-2 for static detection)

15\. Add algorithm tests to `tests/test\_conflict\_detector.py`

16\. Extend WorldModel for algorithm claims (Tier 3 wiring via `\_collect\_known\_values`)

17\. Add algorithm tests to `tests/test\_world\_model.py`

18\. Update `propstore/description\_generator.py`

19\. Update LinkML schema and regenerate JSON Schema

20\. Add CLI commands (`claim compare`, `world algorithms`)

21\. Run full test suite, fix regressions

22\. Run `pks validate` and `pks build --force` on the repository



\## Principles



\- \*\*TDD\*\*: write tests before implementation for each module

\- \*\*No LLM in the compiler path\*\*: all AST operations are deterministic Python

\- \*\*No execution\*\*: algorithm bodies are parsed and compiled for inspection but NEVER executed. `compile()` yes, `exec()` never.

\- \*\*Validation before write\*\*: algorithm bodies must parse before claims are accepted

\- \*\*Conflicts are data\*\*: two different algorithms for the same concept under the same conditions is a CONFLICT, not an error

\- \*\*Existing tests must not break\*\*: run `uv run pytest tests/ -v` after each step

\- \*\*The compiler never produces output from an invalid state\*\*: if any algorithm body fails to parse, the entire build fails

\- \*\*Portable vs ephemeral\*\*: canonical AST dumps are stored in the sidecar (portable across Python versions). Bytecode comparisons are computed at query time (CPython-version-dependent).

\- \*\*Tiers are additive\*\*: each tier strictly adds detection power. Tier 2 catches everything Tier 1 catches plus more. Tier 3 catches everything Tier 2 catches plus more. No false positives are introduced.



\## Non-Goals for This Phase



\- Full Python semantic analysis (type inference, control flow analysis beyond what CPython's compiler does for free)

\- Optimization or transformation of algorithm ASTs

\- Execution of algorithm bodies (ever)

\- Pipeline topology representation (stage ordering, data flow between stages) — stage is a label, not a structural relationship. Pipeline formalization is a separate feature.

\- Extraction from papers — that's the research-papers-plugin side. This phase builds the compiler backend only.

\- Cross-Python-version bytecode comparison — both sides are always compiled in the same process

