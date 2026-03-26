# Docstring Audit: propstore utility modules

Audited 2026-03-24 by Scout agent.

Each finding cites file, line, the docstring claim (quoted), what the code actually does, and a severity rating.

---

## 1. validate.py

### Finding 1.1 -- Module docstring claims JSON Schema validation
- **File/Line**: `propstore/validate.py`, line 3
- **Docstring claim**: `"Loads all concepts/*.yaml files, validates against the JSON Schema, then runs the compiler contract checks that JSON Schema can't express."`
- **What the code actually does**: The module never performs JSON Schema validation. There is no jsonschema import, no schema loading, no schema-based validation anywhere in this file. Only compiler contract checks (structural/cross-reference checks) are performed in `validate_concepts()`.
- **Severity**: LIE -- JSON Schema validation is entirely absent from this module. (JSON Schema validation of claims happens in `validate_claims.py`, not here.)

### Finding 1.2 -- Module docstring claims "Exits nonzero on any error"
- **File/Line**: `propstore/validate.py`, line 7
- **Docstring claim**: `"Exits nonzero on any error."`
- **What the code actually does**: The module defines `validate_concepts()` which returns a `ValidationResult` object. No `sys.exit()` call exists anywhere. The exit behavior would be in the CLI caller, not this module.
- **Severity**: HALF-TRUTH -- The module itself does not exit. The CLI wrapper likely does this, but the docstring attributes the behavior to this module.

### Finding 1.3 -- load_concepts excludes .counters
- **File/Line**: `propstore/validate.py`, line 69
- **Docstring claim**: `"Load all .yaml files from the concept directory (excluding .counters)."`
- **What the code actually does**: Delegates to `load_yaml_dir()` which iterates `directory.iterdir()` filtering on `.yaml` suffix. There is no explicit `.counters` exclusion. However, since `.counters` files would not have `.yaml` suffix, they are implicitly excluded by the suffix filter. The parenthetical is misleading -- it implies there is special exclusion logic when there is not.
- **Severity**: HALF-TRUTH -- The exclusion happens because `.counters` files lack `.yaml` suffix, not because of any explicit exclusion logic.

---

## 2. validate_claims.py

### Finding 2.1 -- Module docstring claims JSON Schema validation
- **File/Line**: `propstore/validate_claims.py`, line 3
- **Docstring claim**: `"Loads all claims/*.yaml files, validates against the JSON Schema, then runs the compiler contract checks that JSON Schema can't express."`
- **What the code actually does**: This module DOES perform JSON Schema validation (line 119: loads schema, line 150: `jsonschema.validate()`), so the claim is accurate here. No issue.
- **Severity**: (no finding)

### Finding 2.2 -- Module docstring claims "Exits nonzero on any error"
- **File/Line**: `propstore/validate_claims.py`, line 7
- **Docstring claim**: `"Exits nonzero on any error."`
- **What the code actually does**: Same as validate.py -- returns a `ValidationResult`. No `sys.exit()` call exists.
- **Severity**: HALF-TRUTH -- exit behavior belongs to the CLI layer, not this module.

### Finding 2.3 -- build_concept_registry docstring incomplete
- **File/Line**: `propstore/validate_claims.py`, line 603-604
- **Docstring claim**: `"Load concepts and build {concept_id: concept_data} mapping."`
- **What the code actually does**: Delegates to `build_concept_registry_from_paths` which builds a registry keyed by concept ID, canonical_name, AND aliases (line 590-599). The single-line docstring on `build_concept_registry` says `{concept_id: concept_data}` which omits the canonical_name and alias indexing.
- **Severity**: HALF-TRUTH -- The parent function `build_concept_registry_from_paths` (line 564) has an accurate docstring. But this wrapper's docstring misleads about the key structure.

### Finding 2.4 -- load_claim_files excludes .counters
- **File/Line**: `propstore/validate_claims.py`, line 54
- **Docstring claim**: `"Load all .yaml files from claims directory (excluding .counters)."`
- **What the code actually does**: Same pattern as validate.py finding 1.3 -- no explicit .counters exclusion, just `.yaml` suffix filtering.
- **Severity**: HALF-TRUTH

---

## 3. validate_contexts.py

### Finding 3.1 -- is_visible docstring incomplete
- **File/Line**: `propstore/validate_contexts.py`, lines 146-150
- **Docstring claim**: `"A claim is visible if claim_ctx is the querying context itself or one of its ancestors."`
- **What the code actually does**: This is accurate for what it describes, but it OMITS the fact that claims with NO context (None/empty) are not handled. The method only checks equality or ancestor membership. A claim with `claim_ctx=None` would not match `querying_ctx` (unless it is also None), and `None in self.ancestors(...)` would be False. This means contextless claims are invisible when querying from any named context.
- **Severity**: OMISSION -- The docstring does not explain what happens with contextless claims, which is a critical edge case for a knowledge store.

---

## 4. cel_checker.py

### Finding 4.1 -- Module docstring accurate
- **File/Line**: `propstore/cel_checker.py`, lines 1-8
- **Docstring claim**: `"Parses a subset of CEL sufficient for the condition expressions..."`
- **What the code actually does**: Implements a tokenizer, recursive descent parser, and type checker for CEL subset. Accurate.
- **Severity**: (no finding)

### Finding 4.2 -- build_cel_registry return key claim
- **File/Line**: `propstore/cel_checker.py`, line 44
- **Docstring claim**: `"Returns a dict mapping canonical_name -> ConceptInfo."`
- **What the code actually does**: When `concept_registry` is keyed by BOTH concept_id and canonical_name (as `build_concept_registry_from_paths` produces), this function iterates ALL keys. So for a concept with ID "concept1" and canonical_name "temperature", the function processes the same concept data TWICE -- once from the concept_id key and once from the canonical_name key. The second iteration overwrites the first in `registry[name]`. The net result is correct (keyed by canonical_name), but the iteration is wasteful and could be surprising if concept_registry had non-dict values.
- **Severity**: OMISSION -- Does not document that it expects a concept_registry potentially with duplicate entries for the same concept under different keys, and silently overwrites.

---

## 5. z3_conditions.py

### Finding 5.1 -- Module docstring claims "z3.EnumSort for category concepts"
- **File/Line**: `propstore/z3_conditions.py`, lines 6-7
- **Docstring claim**: `"Uses z3.Real for quantity concepts, z3.EnumSort for category concepts, and z3.Bool for boolean concepts."`
- **What the code actually does**: For categories with no known values (empty category_values), it falls back to an uninterpreted sort via `z3.DeclareSort` (line 76), not `z3.EnumSort`. The docstring omits this fallback.
- **Severity**: HALF-TRUTH -- The EnumSort claim is only true when category_values are populated.

### Finding 5.2 -- partition_equivalence_classes complexity claim
- **File/Line**: `propstore/z3_conditions.py`, lines 333-335
- **Docstring claim**: `"Complexity: O(n * k) where k is the number of distinct classes, compared to O(n^2) for pairwise checking."`
- **What the code actually does**: The algorithm compares each new element against all existing representatives until a match is found. In the worst case (all elements in distinct classes), k=n and this becomes O(n^2). The claim "O(n*k)" is technically correct as stated but misleadingly suggests it's better than O(n^2) in general.
- **Severity**: HALF-TRUTH -- The complexity statement is technically accurate but the comparison "compared to O(n^2)" implies a speedup that does not exist in the worst case.

---

## 6. condition_classifier.py

### Finding 6.1 -- Module docstring claims three classifications
- **File/Line**: `propstore/condition_classifier.py`, lines 3-4
- **Docstring claim**: `"Classifies pairs of condition sets as CONFLICT, PHI_NODE, or OVERLAP"`
- **What the code actually does**: `classify_conditions()` returns `ConflictClass.CONFLICT`, `ConflictClass.PHI_NODE`, or `ConflictClass.OVERLAP`. The `ConflictClass` enum is imported from `propstore.conflict_detector.models`. The actual enum may have more members (like `PARAM_CONFLICT`), but this function only returns these three. Accurate for this function.
- **Severity**: (no finding)

### Finding 6.2 -- classify_conditions docstring says "Z3 is the primary path when cel_registry is provided"
- **File/Line**: `propstore/condition_classifier.py`, line 108
- **Docstring claim**: `"Z3 is the primary path when cel_registry is provided. Existing interval arithmetic is the fallback when Z3 isn't installed or fails."`
- **What the code actually does**: Before trying Z3, the function first checks if `normalized_a == normalized_b` (line 113) and returns CONFLICT immediately if so. Z3 is NOT the primary path for identical conditions. The docstring omits this fast path.
- **Severity**: OMISSION -- The identical-conditions fast path bypasses Z3 entirely and is not documented.

---

## 7. form_utils.py

### Finding 7.1 -- Module docstring
- **File/Line**: `propstore/form_utils.py`, line 1
- **Docstring claim**: `"Shared helpers for form metadata, kind mapping, and JSON-safe serialization."`
- **What the code actually does**: Also includes form file schema validation (`validate_form_files`), form definition loading, allowed unit extraction, and form caching. The docstring significantly understates the module's scope.
- **Severity**: HALF-TRUTH -- The module does far more than "helpers."

### Finding 7.2 -- json_safe docstring
- **File/Line**: `propstore/form_utils.py`, line 132
- **Docstring claim**: `"Recursively convert date objects to ISO strings for JSON serialization."`
- **What the code actually does**: It recursively traverses dicts and lists, converting `datetime.date` and `datetime.datetime` objects to ISO strings. But it also passes through ALL other types unchanged (line 139: `return obj`). The docstring implies it only handles dates, but it is a general recursive traversal that returns non-date types as-is.
- **Severity**: HALF-TRUTH -- Technically accurate about what it converts, but misleadingly narrow about what it does with the rest of the object tree.

### Finding 7.3 -- load_form docstring omits complex is_dimensionless logic
- **File/Line**: `propstore/form_utils.py`, lines 33-34
- **Docstring claim**: `"Load a single form definition and return a FormDefinition, or None."`
- **What the code actually does**: The function contains substantial logic for determining `is_dimensionless` (lines 79-87) via multiple fallback heuristics: explicit `dimensionless` field, then `base == "ratio"`, then whether `unit_symbol is None and kind == QUANTITY and form_name not in ("structural",)`. This last heuristic means that ANY quantity form without a unit_symbol is treated as dimensionless, which seems potentially surprising.
- **Severity**: OMISSION -- The docstring hides complex dimensionless-determination logic that has non-obvious defaults.

---

## 8. unit_dimensions.py

### Finding 8.1 -- Module docstring accurate
- **File/Line**: `propstore/unit_dimensions.py`, lines 1-10
- **What the code actually does**: Matches the description. Loads physgen_units.json, resolves units to dimensions, supports extra_units from forms.
- **Severity**: (no finding)

### Finding 8.2 -- dimensions_compatible docstring
- **File/Line**: `propstore/unit_dimensions.py`, lines 102-107
- **Docstring claim**: `"Check if a unit's dimensions are compatible with a form's dimensions. Both are dicts like {'M': 1, 'L': -1, 'T': -2}. Empty dict = dimensionless. Missing keys are treated as exponent 0."`
- **What the code actually does**: Delegates entirely to `bridgman.dims_equal()` (line 108). The docstring claims about empty dict and missing key semantics are actually promises about bridgman's behavior, not this code. If bridgman does not treat missing keys as exponent 0, this docstring would be lying.
- **Severity**: HALF-TRUTH -- The docstring describes bridgman's contract, not this function's. The reader must trust that bridgman implements these semantics.

---

## 9. value_comparison.py

### Finding 9.1 -- Module docstring claims "No propstore imports"
- **File/Line**: `propstore/value_comparison.py`, line 4
- **Docstring claim**: `"No propstore imports -- only stdlib."`
- **What the code actually does**: The module has no import statements beyond `from __future__ import annotations` (line 8). This is accurate.
- **Severity**: (no finding)

---

## 10. equation_comparison.py

### Finding 10.1 -- Module docstring claims "canonical signature building"
- **File/Line**: `propstore/equation_comparison.py`, lines 1-6
- **Docstring claim**: `"Extracted from conflict_detector.py -- provides SymPy-based equation normalization for equivalence checking and canonical signature building for grouping equations by their variable structure."`
- **What the code actually does**: Provides `equation_signature()` and `canonicalize_equation()`. Both functions match the description. Accurate.
- **Severity**: (no finding)

### Finding 10.2 -- canonicalize_equation handles more than "lhs - rhs"
- **File/Line**: `propstore/equation_comparison.py`, lines 44-47
- **Docstring claim**: `"Returns a canonical string representation of the equation (as simplified lhs - rhs)"`
- **What the code actually does**: First tries the explicit `sympy` field (line 72), preprocessing with `^` to `**`. Only if there's no explicit sympy field does it fall back to splitting on `=`. The docstring says "lhs - rhs" but for the sympy field path, it only does lhs - rhs if the parsed result is an `Equality` (line 77-80). If it's not an Equality, the parsed result just passes through without simplification (note: the function returns None from the `except` on failure, but the docstring doesn't mention the sympy-field-first path at all).
- **Severity**: HALF-TRUTH -- The docstring describes only the fallback path, not the primary path via the explicit `sympy` field.

---

## 11. embed.py

### Finding 11.1 -- Module docstring
- **File/Line**: `propstore/embed.py`, line 1
- **Docstring claim**: `"Claim embedding generation and storage via litellm + sqlite-vec."`
- **What the code actually does**: Also handles concept embedding (functions `embed_concepts`, `find_similar_concepts`, `find_similar_concepts_agree`, `find_similar_concepts_disagree`), embedding snapshot/restore, and multi-model agreement/disagreement analysis. The module docstring only mentions claims.
- **Severity**: HALF-TRUTH -- The module handles both claim AND concept embeddings, plus snapshot/restore, but the docstring only mentions claims.

### Finding 11.2 -- _embedding_text_for_claim docstring
- **File/Line**: `propstore/embed.py`, line 56
- **Docstring claim**: `"Build text to embed for a claim. Uses best available field."`
- **What the code actually does**: Tries fields in order: `auto_summary`, `statement`, `expression`, `name`. Falls back to `claim.get("id", "unknown")`. The word "best" is subjective but the priority order is fixed and hardcoded. The docstring does not specify the priority order.
- **Severity**: OMISSION -- The priority order of fields (auto_summary > statement > expression > name > id) is important behavior that the docstring hides.

---

## 12. relate.py

### Finding 12.1 -- Module docstring
- **File/Line**: `propstore/relate.py`, line 1
- **Docstring claim**: `"NLI stance classification via litellm -- classify epistemic relationships between claims."`
- **What the code actually does**: Also includes: two-pass NLI with a second pass for high-similarity "none" verdicts, confidence scoring, YAML stance file I/O, bulk relate-all functionality, and shared concept detection. The module docstring significantly understates the scope.
- **Severity**: HALF-TRUTH -- The module does far more than classification.

### Finding 12.2 -- _classify_stance_async docstring
- **File/Line**: `propstore/relate.py`, lines 122-124
- **Docstring claim**: `"Always returns a dict -- 'none' verdicts included with type='none'."`
- **What the code actually does**: This is accurate. On API failure (line 156-171) or JSON parse failure (line 176-191), it returns a dict with `type="none"`. On success, it validates against `VALID_STANCE_TYPES` and falls back to "none" if invalid (line 194-195).
- **Severity**: (no finding)

### Finding 12.3 -- _find_shared_concepts docstring
- **File/Line**: `propstore/relate.py`, line 100
- **Docstring claim**: `"Find concept names referenced by both claims."`
- **What the code actually does**: Only checks if the `concept_id` column of the two claims in the sidecar database is identical (lines 101-108). The comment on line 107 says "Also check for concept overlap in auto_summary text (rough heuristic)" but NO such check is implemented. The function only compares a single concept_id per claim.
- **Severity**: LIE -- The comment promises a heuristic that does not exist. The function finds shared concept IDs (singular), not concept names (plural) -- it can return at most one shared concept ID.

---

## 13. resources.py

### Finding 13.1 -- Module docstring
- **File/Line**: `propstore/resources.py`, lines 1-7
- **Docstring claim**: `"Pattern from polyarray: uses importlib.resources for installed packages, direct Path access for development (source tree)."`
- **What the code actually does**: Matches the description. `_is_development_mode()` checks for `.git` directory, `_get_resource_root()` returns Path or importlib.resources Traversable accordingly.
- **Severity**: (no finding)

### Finding 13.2 -- _get_resource_root docstring
- **File/Line**: `propstore/resources.py`, lines 29-32
- **Docstring claim**: `'Development: Path("<repo>/propstore/_resources") / Installed: importlib.resources.files("propstore") / "_resources"'`
- **What the code actually does**: Matches. Development mode returns `Path(__file__).resolve().parent / "_resources"`, installed mode returns `files("propstore") / "_resources"`.
- **Severity**: (no finding)

---

## 14. build_sidecar.py

### Finding 14.1 -- Module docstring omits many tables
- **File/Line**: `propstore/build_sidecar.py`, lines 1-12
- **Docstring claim**: Lists tables: concept, alias, relationship, parameterization, FTS5, claim, conflicts, claim FTS5.
- **What the code actually does**: Also creates: `parameterization_group` (line 378), `context` (line 499), `context_assumption` (line 507), `context_exclusion` (line 514), `claim_stance` (line 641), `embedding_model`, `embedding_status`, `concept_embedding_status` (via embedding restore).
- **Severity**: STALE -- The docstring was probably accurate when first written but the module has grown to create many more tables.

### Finding 14.2 -- build_sidecar docstring claims
- **File/Line**: `propstore/build_sidecar.py`, lines 212-217
- **Docstring claim**: `"When claim_files is provided, also creates claim, conflicts, and claim_fts tables."`
- **What the code actually does**: Also creates `claim_stance` table (line 641), populates stances from both inline stances and stance YAML files (line 313), and restores embeddings (lines 299-309). The docstring omits stance and embedding handling.
- **Severity**: STALE -- The docstring has not been updated to reflect stance table creation and embedding restore.

### Finding 14.3 -- _concept_content_hash docstring
- **File/Line**: `propstore/build_sidecar.py`, lines 96-99
- **Docstring claim**: `"Identity fields: canonical_name, domain, definition."`
- **What the code actually does**: Hashes exactly `canonical_name`, `domain`, and `definition` (lines 102-104). Accurate.
- **Severity**: (no finding)

### Finding 14.4 -- _claim_content_hash docstring
- **File/Line**: `propstore/build_sidecar.py`, lines 108-113
- **Docstring claim**: `"Identity fields: type, concept/target_concept, value, conditions (sorted), source paper, expression (for equations), statement (for observations)."`
- **What the code actually does**: Also hashes `lower_bound`, `upper_bound` (lines 123-126), `name` (line 136), and `measure` (line 137). The docstring omits these fields.
- **Severity**: STALE -- The hash includes more fields than the docstring lists.

### Finding 14.5 -- _resolve_algorithm_storage undocumented behavior
- **File/Line**: `propstore/build_sidecar.py`, lines 958-972
- **What the code actually does**: The function passes `variables` (from `claim.get("variables", {})`) to `canonical_dump` as `bindings`, but only if `variables` is a dict. If variables is a list (which is the normal claim format based on validate_claims.py), `bindings` would be an empty dict `{}` (line 968: `bindings = variables if isinstance(variables, dict) else {}`). This seems like a bug or at minimum surprising behavior -- algorithm claims have variables as a LIST of dicts, not a dict.
- **Severity**: OMISSION -- No docstring at all on this function, and the variables-to-bindings conversion has a silent fallback that likely always triggers.

---

## 15. graph_export.py

### Finding 15.1 -- Module docstring
- **File/Line**: `propstore/graph_export.py`, lines 1-5
- **Docstring claim**: `"Exports concept and claim nodes plus parameterization, relationship, stance, and claim_of edges."`
- **What the code actually does**: Also supports DOT and JSON output formats as stated. Also supports filtering by `BeliefSpace` and `group_id`. Accurate but incomplete.
- **Severity**: OMISSION -- Does not mention group filtering or belief-space scoping in the module docstring.

### Finding 15.2 -- to_dot docstring
- **File/Line**: `propstore/graph_export.py`, line 42
- **Docstring claim**: `"Render the graph as a Graphviz DOT string."`
- **What the code actually does**: Creates a `graphviz.Digraph(format="png")` (line 45). The format is set to "png" but the method returns `dot.source` which is the DOT string. The "format=png" is misleading since the method returns DOT source text, not a PNG. If the caller later calls `dot.render()`, it would try to produce a PNG. But the returned `.source` attribute IS the DOT string.
- **Severity**: OMISSION -- The `format="png"` on the Digraph is a dead parameter since only `.source` is returned. This is confusing but the docstring claim itself is accurate.

---

## 16. description_generator.py

### Finding 16.1 -- Module docstring claims about observation claims
- **File/Line**: `propstore/description_generator.py`, lines 4-5
- **Docstring claim**: `"Observation claims return their existing statement unchanged."`
- **What the code actually does**: The function first checks if `claim.get("statement")` is truthy (line 25) and returns it for ANY claim type before even checking the type. The observation-specific branch (line 34-36) is ONLY reached if the claim has no statement, at which point it returns `claim.get("statement")` again (which would be None/falsy). So for observation claims WITH statements, the generic early return handles them, not the observation branch. For observation claims WITHOUT statements, the function returns None (or empty string).
- **Severity**: HALF-TRUTH -- The docstring is misleading about the mechanism. Observation claims return their statement via the early return, not via the observation-specific branch. The observation branch is dead code for claims with statements.

### Finding 16.2 -- generate_description return type
- **File/Line**: `propstore/description_generator.py`, line 22
- **Docstring claim**: `"Returns: A description string, or None if the claim type is unrecognized."`
- **What the code actually does**: Can also return None for observation claims without a statement (line 36), or return an empty string for equation claims with no expression (line 103: `claim.get("expression", "")` returns `""`). The "None if unrecognized" framing is incomplete.
- **Severity**: HALF-TRUTH -- Returns None for more cases than just unrecognized types. Returns empty string for equations without expressions.

### Finding 16.3 -- _describe_algorithm docstring incomplete
- **File/Line**: `propstore/description_generator.py`, line 138
- **Docstring claim**: `"Generate description for an algorithm claim."`
- **What the code actually does**: Uses `claim.get("name", "unnamed")` but algorithm claims (per validate_claims.py) do not have a `name` field -- they have `body` and `variables`. The `name` field belongs to model claims. This means algorithm claims will almost always get "Algorithm: unnamed" unless they happen to have a stray `name` field.
- **Severity**: OMISSION -- The function silently falls back to "unnamed" because it reads a field that algorithm claims do not typically have.

---

## 17. sensitivity.py

### Finding 17.1 -- Parameter type names wrong
- **File/Line**: `propstore/sensitivity.py`, lines 44-49
- **Docstring claim**: `"world : WorldModel"` and `"bound : BoundWorld"`
- **What the code actually does**: The function accepts `world` and `bound` without type annotations (just bare names). Based on usage: `world.parameterizations_for()` matches `ArtifactStore` (from graph_export.py imports), and `bound.is_param_compatible()`, `bound.value_of()`, `bound.derived_value()` match `BeliefSpace`. The docstring says "WorldModel" and "BoundWorld" which are not class names that exist in the codebase.
- **Severity**: LIE -- "WorldModel" and "BoundWorld" are not the actual class names. They appear to be `ArtifactStore` and `BeliefSpace` (or similar from `propstore.world`).

---

## 18. sympy_generator.py

### Finding 18.1 -- Module docstring accurate
- **File/Line**: `propstore/sympy_generator.py`, lines 1-6
- **What the code actually does**: Auto-generates SymPy expressions from human-readable math strings for claim validation and sidecar building.
- **Severity**: (no finding)

### Finding 18.2 -- generate_sympy docstring
- **File/Line**: `propstore/sympy_generator.py`, lines 57-64
- **Docstring claim**: `"Returns: SymPy-parseable string of the RHS, or None if parsing fails."`
- **What the code actually does**: Only returns the RHS when the expression contains `=`. If there is no `=`, the ENTIRE expression is parsed and returned (line 49: `text` is the whole expression after `^` to `**` substitution). The docstring says "RHS" but it returns the whole expression when there's no `=`.
- **Severity**: HALF-TRUTH -- "of the RHS" is only true when the expression contains `=`.

---

## 19. param_conflicts.py

### Finding 19.1 -- Module docstring
- **File/Line**: `propstore/param_conflicts.py`, lines 1-6
- **Docstring claim**: `"Detects PARAM_CONFLICT via single-hop and multi-hop parameterization chains: _detect_param_conflicts: single-hop derivation conflict detection / detect_transitive_conflicts: multi-hop chain conflict detection"`
- **What the code actually does**: `detect_transitive_conflicts` (line 406-416) can also emit context-based conflict classes (not just `PARAM_CONFLICT`) via `_classify_pair_context()` (line 400). So the module does not exclusively produce PARAM_CONFLICT.
- **Severity**: HALF-TRUTH -- The module can produce conflict classes other than PARAM_CONFLICT for transitive conflicts.

### Finding 19.2 -- detect_transitive_conflicts docstring
- **File/Line**: `propstore/param_conflicts.py`, lines 202-209
- **Docstring claim**: `"Only emits conflicts for concepts reachable via 2+ hops to avoid duplicating the single-hop conflicts already found by _detect_param_conflicts."`
- **What the code actually does**: The single-hop detection logic (lines 373-388) checks if the source claim IDs are a subset of direct input claim IDs for any edge. This heuristic can fail if the same claim provides values for multiple input concepts, potentially missing some single-hop cases or incorrectly classifying them.
- **Severity**: HALF-TRUTH -- The 2+ hop filtering is attempted but the heuristic is not airtight.

---

## 20. parameterization_groups.py

### Finding 20.1 -- Docstring claims singleton groups
- **File/Line**: `propstore/parameterization_groups.py`, line 19
- **Docstring claim**: `"Concepts with no parameterization links appear as singleton groups."`
- **What the code actually does**: Every concept ID is added to `all_ids` (line 34) and initialized in the union-find (line 38). The component collection (lines 69-74) iterates all IDs and finds their root. Concepts with no parameterization links will indeed be singletons since they were never unioned. Accurate.
- **Severity**: (no finding)

---

## 21. parameterization_walk.py

### Finding 21.1 -- Module docstring
- **File/Line**: `propstore/parameterization_walk.py`, lines 1-6
- **Docstring claim**: `"Used by worldline_runner (pre-resolve conflicts) and param_conflicts (transitive conflict detection)."`
- **What the code actually does**: The module provides `reachable_concepts` and `parameterization_edges_from_registry`. Checking param_conflicts.py confirms it imports `parameterization_edges_from_registry` (line 228). The claim about `worldline_runner` cannot be verified from the files I read, but it is plausible.
- **Severity**: (no finding -- cannot fully verify worldline_runner usage without reading that file, but the param_conflicts usage is confirmed)

### Finding 21.2 -- reachable_concepts docstring
- **File/Line**: `propstore/parameterization_walk.py`, lines 14-31
- **Docstring claim**: `"Walks the parameterization graph breadth-first from the starting concepts"`
- **What the code actually does**: Uses `queue.pop()` (line 37) which pops from the END of the list, making this depth-first, not breadth-first. BFS would use `queue.pop(0)` or `collections.deque.popleft()`.
- **Severity**: LIE -- The traversal is depth-first (stack), not breadth-first (queue). The result set is the same (all reachable nodes) but the traversal order differs from what is documented.

---

## Summary by severity

| Severity | Count |
|----------|-------|
| LIE | 3 |
| HALF-TRUTH | 14 |
| STALE | 3 |
| OMISSION | 8 |
| **Total findings** | **28** |

### LIE findings (completely wrong):
1. `validate.py:3` -- Claims JSON Schema validation that does not exist in this module
2. `sensitivity.py:44-49` -- Names class types "WorldModel" and "BoundWorld" that do not exist
3. `parameterization_walk.py:15` -- Claims breadth-first traversal but code is depth-first

### Most impactful findings:
- `relate.py:107` comment promises a heuristic that is not implemented (dead comment/code)
- `build_sidecar.py:1-12` module docstring is significantly stale, missing ~6 tables
- `description_generator.py:138` reads wrong field for algorithm claims (always "unnamed")
- `build_sidecar.py:967-968` variables-to-bindings conversion silently falls back for list-type variables
