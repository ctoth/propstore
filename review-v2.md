The biggest problems are not stylistic. Several of them are semantic faults that will produce wrong derivations.



\### Highest-confidence bugs



1\. \*\*The system does not have Herbrand-style constants; it has Python scalars that collapse into each other.\*\*

&#x20;  Files: `gunray/parser.py:372-405`, `gunray/semantics.py:22-25`, `propstore/aspic.py:22-45`.



&#x20;  This is the deepest issue in the codebase.



&#x20;  `gunray.parser.\_normalize\_scalar\_value()` re-parses \*\*quoted strings\*\* as unquoted scalars. So `"1"` becomes `1`, `"true"` becomes `True`, `"1.0"` becomes `1.0`, and `"01"` becomes `1`. Then the model uses normal Python equality, so `True == 1 == 1.0`, and set membership/hash semantics collapse them further.



&#x20;  Concrete consequences:



&#x20;  \* `parse\_atom\_text('p("1")')` yields an integer constant, not a string constant.

&#x20;  \* `normalize\_facts({"p": \[("01",), ("true",), ("1.0",)]})` collapses those into one row.

&#x20;  \* In `propstore`, `GroundAtom("p", (True,)) == GroundAtom("p", (1,))` is `True`.



&#x20;  That is not a harmless implementation detail. It breaks syntactic identity of constants, which is foundational in Datalog/DeLP/ASPIC-style formalisms.



2\. \*\*Arithmetic parsing is wrong for `+`/`-` chains.\*\*

&#x20;  File: `gunray/parser.py:163-178`, helper at `309-333`.



&#x20;  `\_find\_top\_level\_binary()` returns the \*\*leftmost\*\* operator, and `parse\_value\_term()` always tries `+` before `-`. That makes expressions right-associative in the wrong places.



&#x20;  Concrete example: `1-2-3` parses as `1-(2-3)` and evaluates to `2`, not `-4`.

&#x20;  Mixed expressions are also wrong in some cases because precedence/associativity is being encoded by recursive split order rather than an actual expression grammar.



3\. \*\*Unsafe negation is accepted, and then interpreted with wildcard-like semantics.\*\*

&#x20;  File: `gunray/evaluator.py:124-137`, runtime effect at `544-579`, `582-593`, `633-658`.



&#x20;  `\_validate\_program()` allows variables that appear \*\*only inside a single negated literal\*\*. Example:



&#x20;  ```prolog

&#x20;  ok(X) :- person(X), not banned(X,Y).

&#x20;  ```



&#x20;  This passes validation.



&#x20;  At runtime, `Y` is treated as unbound during matching, so `not banned(X,Y)` becomes “there does not exist any `Y` such that `banned(X,Y)`”, which is a domain-dependent existential reading of an otherwise unsafe rule. Standard safe stratified Datalog would reject this.



4\. \*\*Strong negation is silently stripped in the Gunray grounding translator.\*\*

&#x20;  File: `propstore/grounding/translator.py:217-248`.



&#x20;  `\_stringify\_atom()` explicitly ignores `AtomDocument.negated`. Unlike `negative\_body`, `strict`, and `defeater`, which are loudly refused with `NotImplementedError`, strong negation is just dropped.



&#x20;  That is semantic corruption, not merely “feature deferred”.



5\. \*\*`\_literal\_for\_atom()` keys literals only by `repr(GroundAtom)` and ignores polarity.\*\*

&#x20;  File: `propstore/aspic\_bridge.py:290-311`.



&#x20;  This is severe.



&#x20;  \* Positive and negative literals for the same atom share the same key.

&#x20;  \* The first polarity encountered wins.

&#x20;  \* Later requests for the opposite polarity return the already-stored literal.



&#x20;  So if a negated occurrence is seen first, a later positive occurrence can be interned as negative, and vice versa. That makes semantics depend on encounter order.



&#x20;  This is compounded by `GroundAtom.\_\_repr\_\_` collisions:



&#x20;  \* `GroundAtom("p", (True,))` and `GroundAtom("p", ("True",))` both render as `p(True)`.

&#x20;  \* `GroundAtom("p", (1,))` and `GroundAtom("p", ("1",))` both render as `p(1)`.



6\. \*\*`\_parse\_ground\_atom\_key()` is not actually an inverse of `GroundAtom.\_\_repr\_\_`.\*\*

&#x20;  File: `propstore/aspic\_bridge.py:438-475`.



&#x20;  Problems:



&#x20;  \* It parses \*\*all arguments as strings\*\*.

&#x20;  \* It naively splits on commas.

&#x20;  \* It does not understand quoting/escaping.

&#x20;  \* It cannot round-trip booleans, ints, floats, commas inside strings, or parentheses inside strings.



&#x20;  So query fallback on unknown literals can synthesize the wrong goal atom. `p(1)` becomes string `"1"`, not integer `1`. `p("a,b")` becomes two arguments.



7\. \*\*`build\_arguments\_for(..., include\_attackers=True)` is not closed under attack relevance.\*\*

&#x20;  File: `propstore/aspic.py:841-889`.



&#x20;  It does:



&#x20;  \* goal arguments,

&#x20;  \* attackers of those,

&#x20;  \* attackers of those attackers,

&#x20;  \* and then stops.



&#x20;  That is not enough for reinstatement chains of arbitrary depth.



&#x20;  I confirmed this with a small executable example in the leaf ASPIC module:



&#x20;  \* goal: `p`

&#x20;  \* attacker: `q => \~p`

&#x20;  \* counter-attacker: `r => \~q`

&#x20;  \* counter-counter-attacker: `s => \~r`



&#x20;  `build\_arguments\_for(..., include\_attackers=True)` returned conclusions `{p, \~p, \~q}` and \*\*missed `\~r`\*\*, while exhaustive construction contained it. Any acceptability/status result based on the focused subset can therefore be wrong.



8\. \*\*`query\_claim()` mislabels “arguments against” the goal.\*\*

&#x20;  File: `propstore/aspic\_bridge.py:1110-1112`.



&#x20;  ```python

&#x20;  args\_against = frozenset(a for a in arguments if conc(a) != goal)

&#x20;  ```



&#x20;  That is simply wrong.



&#x20;  It classifies every non-goal subargument as “against”, including neutral supporting premises and intermediate derivations. In a chain `p -> q`, querying `q` will put the premise-argument for `p` into `arguments\_against`, even though it supports `q`.



9\. \*\*The CSAF `framework` drops the attack relation even though the Dung layer can use it.\*\*

&#x20;  Files: `propstore/aspic\_bridge.py:924-935`, `propstore/dung.py:125-153`.



&#x20;  `build\_bridge\_csaf()` computes both `attacks` and `defeats`, but constructs:



&#x20;  ```python

&#x20;  framework = ArgumentationFramework(arguments=..., defeats=...)

&#x20;  ```



&#x20;  without the `attacks=` field.



&#x20;  In `dung.py`, `admissible()`, `complete\_extensions()`, and `stable\_extensions()` use `framework.attacks` for conflict-freeness when present; otherwise they fall back to `defeats`. So downstream extension semantics on the CSAF framework silently degrade from attack-based conflict-freeness to defeat-based conflict-freeness.



10\. \*\*`preferred\_extensions(..., backend="brute")` does not reliably honor the requested backend.\*\*

&#x20;   File: `propstore/dung.py:239-259`.



&#x20;   In the brute branch, it calls `complete\_extensions(framework)` without passing the resolved backend. So an explicit `backend="brute"` can still recurse into `auto` behavior.



11\. \*\*`justifications\_to\_rules()` silently drops empty-premise rules.\*\*

&#x20;   File: `propstore/aspic\_bridge.py:151-156`.



&#x20;   ```python

&#x20;   if not j.premise\_claim\_ids:

&#x20;       continue

&#x20;   ```



&#x20;   That means zero-antecedent strict/defeasible rules disappear entirely. In every formalism you cite, empty-body rules are meaningful. If you want to ban them, reject them. Silently dropping them is wrong.



12\. \*\*`extract\_facts()` ignores the predicate registry’s arity discipline and always emits unary atoms.\*\*

&#x20;   Files: `propstore/grounding/facts.py:145-160`, registry validator at `grounding/predicates.py:330-355`.



&#x20;   The extractor docs talk about respecting declared arity, but the implementation unconditionally emits:



&#x20;   ```python

&#x20;   GroundAtom(predicate=predicate.id, arguments=(record.canonical\_name,))

&#x20;   ```



&#x20;   There is no `registry.validate\_atom(...)` call. If a `concept\_relation` predicate is declared with arity other than 1, the code still emits it as unary.



13\. \*\*String escaping is incomplete in the Gunray translator.\*\*

&#x20;   File: `propstore/grounding/translator.py:302-306`.



&#x20;   `\_stringify\_term()` escapes backslashes and quotes, but not other control characters. A string containing a newline becomes an invalid Gunray surface literal. This should use a real string-literal encoder, not ad hoc escaping.



14\. \*\*Ground-rule names are not robustly unique.\*\*

&#x20;   File: `propstore/aspic\_bridge.py:314-325`, usage at `423-425`.



&#x20;   `\_canonical\_substitution\_key()` concatenates `k=v` pairs without escaping. Distinct substitutions can collide if values contain delimiters.



&#x20;   Example for the same variable names `X, Y`:



&#x20;   \* `X = "a,Y=b"`, `Y = "c"` → `X=a,Y=b,Y=c`

&#x20;   \* `X = "a"`, `Y = "b,Y=c"` → `X=a,Y=b,Y=c`



&#x20;   Since these names drive undercutting, that is not cosmetic.



15\. \*\*Undercutting grounded rules is structurally awkward and may be impossible at the authored-ID level.\*\*

&#x20;   Files: ground rule naming at `propstore/aspic\_bridge.py:423-425`; matching at `582-605`.



&#x20;   Grounded rule names are `rule\_id#σ`, but undercut stances match `target\_justification\_id` by exact equality with `rule.name`. An authored base justification id like `r1` will not match grounded instances `r1#X=tweety`, `r1#X=opus`, etc. If multiple instances share the same consequent, the bridge raises ambiguity unless the caller already knows the internal ground-instance naming scheme.



\---



\### Semantic choices I would challenge before trusting the results



These are not all “bugs” in the same sense, but they are strong commitments that either diverge from the literature or need to be made explicit.



16\. \*\*`transposition\_closure()` globally deletes all strict rules if any singleton strict closure is inconsistent.\*\*

&#x20;   File: `propstore/aspic.py:381-393`.



&#x20;   I verified a simple example (`\~p -> q`, `q -> p`) where this returns `frozenset()`. One bad strict fragment wipes out the entire strict theory, including unrelated rules. That is an extremely aggressive repair strategy.



17\. \*\*`transposition\_closure()` ignores the provided contrariness relation and uses `Literal.contrary` mechanically.\*\*

&#x20;   File: `propstore/aspic.py:306-393`.



&#x20;   The function even says the `contrariness` parameter is unused. That is only sound if your language is strictly classical negation by boolean flag and never uses richer contraries.



18\. \*\*The closure evaluator is a toy algorithm exposed under public policies.\*\*

&#x20;   Files: `gunray/closure.py:48-80`, `186-192`; public dispatch in `gunray/adapter.py:25-31`.



&#x20;   It enumerates all propositional worlds by `product((False, True), repeat=len(atoms))`. That is `2^n`. Since `Policy.RATIONAL\_CLOSURE`, `LEXICOGRAPHIC\_CLOSURE`, and `RELEVANT\_CLOSURE` are public policies, this is a public scalability trap.



19\. \*\*Closure policies disagree internally on vacuous antecedents / impossible contexts.\*\*

&#x20;   Files: `gunray/closure.py:268-279`, `359-371`.



&#x20;   `\_ranked\_formula\_entails()` returns `False` when the antecedent has no satisfying worlds. `\_classically\_entails()` returns `True` on an empty satisfying set via vacuous `all(...)`. So different closure policies can disagree on impossible antecedents for implementation reasons, not because of a deliberate semantic choice.



20\. \*\*The rational/relevant closure constructions do not look literature-faithful.\*\*

&#x20;   Files: `gunray/closure.py:144-169`, `281-336`.



&#x20;   `\_ranked\_defaults()` ranks defaults by existence of a supporting world under the remaining defaults. `\_minimal\_relevant\_rule\_ids()` searches subsets of defaults combinatorially. These may be acceptable heuristics for a reduced fragment, but I would not trust them as faithful implementations of rational closure / lexicographic closure / relevant closure without a benchmark suite against the standard examples.



21\. \*\*Specificity and defeat are heavily simplified relative to DeLP/ASPIC+.\*\*

&#x20;   Files: `gunray/defeasible.py:429-470`, `568-599`.



&#x20;   `\_is\_more\_specific()` compares strict closures of rule bodies. `\_supporter\_survives()` implements a very strong “one surviving attacker kills the supporter unless directly outranked” model. If this is intended, it should be documented as a semantic choice, because it is not a neutral implementation of the broader literature.



22\. \*\*Negative-status sections are extensionally incomplete over possible ground instances.\*\*

&#x20;   Files: `gunray/defeasible.py:68-69`, `112-141`, `\_ground\_rules()` at `276-299`.



&#x20;   Candidates for `not\_defeasibly` / `undecided` are generated from grounded rules found via the support model. If a head instance never appears in `rules\_by\_head`, it may never be classified at all.



&#x20;   Example shape: `flies(X) <= bird(X), injured(X)` with only `bird(tweety)` in the facts. `flies(tweety)` is a natural query point, but it may never appear in any negative section because no grounded rule instance is produced.



23\. \*\*ASPIC preference semantics are intentionally altered in a few places.\*\*

&#x20;   Files: empty-set handling in `\_set\_strictly\_less()` at `1009-1065`; self-attack rule in `compute\_defeats()` at `1189-1198`.



&#x20;   Those may be pragmatic choices, but they are not neutral. They change the induced ordering and defeat relation in edge cases.



\---



\### Cleanup and architecture debt



24\. \*\*The literal map mixes claim IDs and ground-atom surface strings in one namespace.\*\*

&#x20;   Files: `claims\_to\_literals()` at `101-121`; `\_literal\_for\_atom()` at `290-311`.



&#x20;   An authored claim with id `"bird(tweety)"` collides with the ground-atom key for `bird(tweety)`. Those are different ontological objects being forced into one dictionary keyspace.



25\. \*\*The query API contract is inconsistent with the implementation.\*\*

&#x20;   File: `propstore/aspic\_bridge.py:1029-1031` versus `1053-1075`.



&#x20;   The docstring says unknown `claim\_id` raises `KeyError`. The implementation synthesizes a goal literal and returns an empty result instead.



26\. \*\*The phase-boundary discipline is inconsistent.\*\*

&#x20;   `negative\_body`, `strict`, and `defeater` are loudly refused in some places; strong negation is silently erased in another; strong negation is half-threaded in the ASPIC bridge but broken by keying. That is a classic sign that the same concept is crossing layers before its representation is stable.



\---



\### What I would fix first



1\. \*\*Scalar semantics\*\*: stop normalizing quoted strings into numbers/bools, and stop relying on raw Python equality/hash for logical constants.

2\. \*\*Literal identity\*\*: replace `repr(GroundAtom)` as the canonical key with a typed structural key that includes polarity.

3\. \*\*Goal-directed completeness\*\*: make attacker inclusion a fixed-point over relevance, not a hardcoded two-pass expansion.

4\. \*\*Query correctness\*\*: fix `arguments\_against`, and include `attacks` when constructing the CSAF framework.

5\. \*\*Parser/evaluator soundness\*\*: repair arithmetic parsing and tighten negation safety.

6\. \*\*Unsupported-feature handling\*\*: anywhere a phase is deferred, refuse loudly rather than silently changing meaning.



The first rewrite target should be the scalar model and literal-keying. Those two defects contaminate almost every other layer.



