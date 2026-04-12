"""Phase-1 translator from propstore rule/fact documents to gunray theories.

This module is the Phase-1 surface that bridges propstore's structured
``RuleDocument`` / ``AtomDocument`` / ``TermDocument`` source types and
the gunray ``DefeasibleTheory`` schema consumed by
``gunray.parser.parse_defeasible_theory``. The sole public entry point
is :func:`translate_to_theory`.

The gunray schema stores rule heads and bodies as *strings*, not
structured atoms (see ``gunray.schema.Rule``). Gunray parses them back
into structured ``Atom`` objects at evaluation time via
``gunray.parser.parse_atom_text``. This translator is therefore also an
*atom stringifier*: it renders each propstore ``AtomDocument`` into the
surface syntax ``predicate(arg1, arg2, ...)`` that
``parse_atom_text`` round-trips correctly.

Theoretical sources:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is a
      finite set of ground atoms ``p(c_1,...,c_n)`` keyed by predicate
      id. The translator produces exactly this shape for the
      ``DefeasibleTheory.facts`` slot: a dict keyed by predicate id
      whose values are lists of argument tuples.
    - Section 3 (Definition 9): the ground substitution set is a
      function of the program and its fact base. The translator must
      NOT ground rules itself — grounding is gunray's job at evaluation
      time. Rule heads and bodies therefore keep their variables intact
      in the stringified output.
    - Section 4: stratified negation is an extension layered over the
      base Datalog surface. Phase 1 refuses to silently strip a
      non-empty ``negative_body`` channel because doing so would change
      the rule's semantics; it raises ``NotImplementedError`` instead.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): a DeLP program is a pair ``(Facts, Rules)``
      (plus a superiority relation ``>``) where ``Rules`` is partitioned
      into strict rules (``<-``) and defeasible rules (``-<``); the
      canonical toy example is ``bird(tweety) ∈ Facts`` and the
      defeasible rule ``flies(X) -< bird(X)``. Phase 1 of this
      translator targets that pair directly: defeasible rules become
      ``DefeasibleTheory.defeasible_rules`` entries, and facts become
      ``DefeasibleTheory.facts`` rows keyed by predicate id.
    - Section 3 (p.3-4): rule surface syntax uses variables as
      uppercase identifiers and constants as lowercase tokens or
      literals. The gunray parser does NOT share the lowercase-as-
      constant convention — every unquoted non-numeric token is parsed
      as a ``Variable``. This translator therefore quotes string
      constants when stringifying term tuples so ``parse_atom_text``
      round-trips them as ``Constant`` values.
    - Section 3.1 (p.4): ground instances are obtained by substituting
      constants from the Herbrand base into rule variables. Phase 1
      emits schema rules that are still quantified — gunray performs
      the substitution.
    - Section 4 (Defs 4.1-4.2, p.16): defeaters are a distinct
      rule-like object from strict and defeasible rules. Phase 1 defers
      them to a later chunk; ``kind == "defeater"`` raises
      ``NotImplementedError`` so the deferral is explicit, not silent.
    - Section 6.1 (p.29-31): default negation travels in a separate
      body channel. Phase 1 refuses to translate rules with a non-empty
      ``negative_body`` so the Phase-1 output is semantically exact.
"""

from __future__ import annotations

from collections.abc import Sequence

from gunray import schema as gunray_schema

from collections.abc import Iterable

from propstore.aspic import GroundAtom
from propstore.grounding.predicates import PredicateRegistry
from propstore.rule_documents import AtomDocument, LoadedRuleFile, TermDocument

# ``gunray.schema.Scalar`` and ``propstore.aspic.Scalar`` are both
# ``str | int | float | bool``; use the gunray alias here because the
# grouped-facts dict is passed straight into ``gunray_schema.DefeasibleTheory``
# and ``PredicateFacts`` is typed against gunray's ``FactTuple``.
_FactTuple = tuple[gunray_schema.Scalar, ...]


def translate_to_theory(
    rule_files: Sequence[LoadedRuleFile],
    facts: tuple[GroundAtom, ...],
    registry: PredicateRegistry,
) -> gunray_schema.DefeasibleTheory:
    """Translate propstore rule/fact inputs into a gunray DefeasibleTheory.

    Walks every ``RuleDocument`` in ``rule_files`` (in file order, then
    authored order within each file) and stringifies each defeasible
    rule into the gunray schema's string surface syntax. Groups the
    ``facts`` tuple by predicate id into the
    ``PredicateFacts`` shape that ``gunray.schema.DefeasibleTheory``
    stores.

    Phase 1 scope — pinned by
    ``tests/test_grounding_translator.py``:

    - Only ``kind == "defeasible"`` rules are translated. Rules with
      ``kind == "strict"`` or ``kind == "defeater"`` raise
      ``NotImplementedError`` (Garcia & Simari 2004 §3 admits both in
      a DeLP program, but Phase 1 defers them so gunray's
      ``strict_rules`` and ``defeaters`` slots stay empty).
    - Rules with a non-empty ``negative_body`` raise
      ``NotImplementedError`` (Garcia & Simari 2004 §6.1, p.29-31:
      default negation has distinct semantics from positive body
      literals; silently dropping it would change the rule's meaning).
    - ``strict_rules``, ``defeaters``, ``superiority``, and
      ``conflicts`` are always empty on the output theory.
    - The ``registry`` parameter is threaded through for future
      validation (Diller, Borg, Bex 2025 §4 requires arity discipline
      at the grounder boundary), but Phase 1 performs no additional
      validation against it — the tests are agnostic about registry
      interaction in this chunk.

    Args:
        rule_files: Sequence of ``LoadedRuleFile`` envelopes — each
            carries an ordered tuple of ``RuleDocument`` values
            (``propstore.rule_documents``). Rule order within a file is
            preserved across the YAML round-trip because authored order
            can carry preference information downstream.
        facts: Tuple of ``GroundAtom`` values as produced by
            ``propstore.grounding.facts.extract_facts`` — ground atoms
            ``p(c_1,...,c_n)`` drawn from the propstore concept graph
            (Diller, Borg, Bex 2025 §3 Definition 7).
        registry: ``PredicateRegistry`` providing predicate
            declarations. Threaded through but not heavily validated in
            Phase 1.

    Returns:
        A populated ``gunray.schema.DefeasibleTheory`` with
        stringified defeasible rules, grouped fact rows, and empty
        Phase-2+ slots.

    Raises:
        NotImplementedError: when a rule's ``kind`` is ``"strict"`` or
            ``"defeater"``, or when its ``negative_body`` is non-empty.
    """

    defeasible_rules: list[gunray_schema.Rule] = []
    for rule_file in rule_files:
        for rule_doc in rule_file.rules:
            if rule_doc.kind == "strict":
                # Garcia & Simari 2004 §3: strict rules are part of a
                # DeLP program but have distinct (indefeasible)
                # semantics; they belong in gunray's ``strict_rules``
                # slot. Phase 1 does not populate that slot.
                raise NotImplementedError(
                    f"Strict rules are deferred to Phase 4 "
                    f"(rule {rule_doc.id!r})"
                )
            if rule_doc.kind == "defeater":
                # Garcia & Simari 2004 §4 Defs 4.1-4.2: defeaters are a
                # distinct rule-like object from defeasible rules.
                # Phase 1 does not populate gunray's ``defeaters`` slot.
                raise NotImplementedError(
                    f"Defeater rules are deferred to Phase 4 "
                    f"(rule {rule_doc.id!r})"
                )
            if rule_doc.negative_body:
                # Garcia & Simari 2004 §6.1 (p.29-31): default negation
                # has distinct semantics from positive body literals;
                # Diller, Borg, Bex 2025 §4 treats stratified negation
                # as an extension over the base Datalog surface.
                raise NotImplementedError(
                    f"Default negation (negative_body) is deferred to "
                    f"Phase 4 (rule {rule_doc.id!r})"
                )

            # Stringify the head and each body atom into gunray's
            # surface syntax. Diller, Borg, Bex 2025 §3 Definition 9
            # makes the ground-substitution pass gunray's job, so the
            # stringified form keeps variables intact.
            defeasible_rules.append(
                gunray_schema.Rule(
                    id=rule_doc.id,
                    head=_stringify_atom(rule_doc.head),
                    body=[_stringify_atom(atom) for atom in rule_doc.body],
                )
            )

    # Group facts by predicate id. Diller, Borg, Bex 2025 §3
    # Definition 7 shape: ``PredicateFacts`` maps each predicate id to
    # an iterable of argument tuples. ``extract_facts`` already
    # deduplicates and sorts the input tuple; we preserve the incoming
    # order so the sidecar build stays reproducible.
    #
    # The dict value type is annotated as ``Iterable[_FactTuple]`` (not
    # ``list[_FactTuple]``) so the literal matches
    # ``gunray.schema.PredicateFacts`` exactly. ``dict`` is invariant in
    # its value parameter, so a ``dict[str, list[...]]`` is not
    # assignable to ``dict[str, Iterable[...]]`` even though
    # ``list[X] <: Iterable[X]``.
    grouped_facts: dict[str, Iterable[_FactTuple]] = {}
    fact_rows: dict[str, list[_FactTuple]] = {}
    for fact in facts:
        fact_rows.setdefault(fact.predicate, []).append(tuple(fact.arguments))
    for predicate_id, rows in fact_rows.items():
        grouped_facts[predicate_id] = rows

    # ``gunray.schema.PredicateFacts`` is typed as
    # ``dict[str, Iterable[tuple[Scalar, ...]]]`` — ``list`` satisfies
    # ``Iterable`` and the test suite converts rows via ``list(rows)``
    # / ``tuple(row)`` before asserting membership.
    return gunray_schema.DefeasibleTheory(
        facts=grouped_facts,
        strict_rules=[],
        defeasible_rules=defeasible_rules,
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _stringify_atom(atom: AtomDocument) -> str:
    """Render an ``AtomDocument`` into gunray surface syntax.

    Produces ``"predicate(t1, t2, ...)"`` for arity ≥ 1 and
    ``"predicate"`` (no parens) for arity 0. The format is the surface
    syntax ``gunray.parser.parse_atom_text`` accepts: predicate name
    followed by an optional parenthesised comma-separated term list
    (Diller, Borg, Bex 2025 §3 fixes the ``p(t_1,...,t_n)`` shape;
    Garcia & Simari 2004 §3 fixes the same shape at the DeLP language
    level).

    Phase 1 does NOT render strong negation (``AtomDocument.negated``)
    — no Phase 1 test exercises it and the gunray parser's ``~``
    handling is itself partial. A later chunk will layer that in once
    contrariness routing is defined.

    Args:
        atom: The propstore atom to stringify.

    Returns:
        A surface-syntax string that ``parse_atom_text`` round-trips.
    """

    if not atom.terms:
        # Arity-0 atom: ``parse_atom_text`` parses a bare identifier
        # as ``Atom(predicate=<id>, terms=())``. Emitting ``p()``
        # instead would raise because the parser requires non-empty
        # inner content between the parens.
        return atom.predicate

    rendered_terms = [_stringify_term(term) for term in atom.terms]
    return f"{atom.predicate}({', '.join(rendered_terms)})"


def _stringify_term(term: TermDocument) -> str:
    """Render a single ``TermDocument`` into gunray surface syntax.

    Variable terms render as their bare name. Constant terms render
    via the gunray scalar grammar (Diller, Borg, Bex 2025 §3 fixes the
    constant term form as a ``Scalar`` literal):

    - ``bool``: ``"true"`` / ``"false"``.
    - ``int`` / ``float``: the Python ``repr`` of the numeric value
      (both round-trip through ``gunray.parser._parse_unquoted_scalar``
      which delegates to ``int()`` / ``float()``).
    - ``str``: a JSON-style double-quoted literal. Garcia & Simari
      2004 §3 permits lowercase-identifier constants at the DeLP
      language level, but the gunray parser parses every unquoted
      non-numeric token as a ``Variable`` — see
      ``gunray.parser.parse_value_term``. Quoting strings is therefore
      the only faithful way to preserve the variable/constant
      discrimination across the string round-trip.

    Args:
        term: The propstore term to stringify.

    Returns:
        A surface-syntax string.

    Raises:
        ValueError: when a variable term has no ``name`` or a constant
            term has ``value is None``. Both would indicate a
            malformed ``TermDocument``; the Phase 1 translator refuses
            to silently drop broken terms.
    """

    if term.kind == "var":
        if term.name is None:
            raise ValueError(
                "variable TermDocument is missing its 'name' field"
            )
        return term.name

    # term.kind == "const"
    if term.value is None:
        raise ValueError(
            "constant TermDocument is missing its 'value' field"
        )

    value = term.value
    if isinstance(value, bool):
        # Must come before ``int`` because ``bool`` subclasses ``int``.
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    # ``str`` branch. Emit a JSON-style double-quoted literal so
    # ``gunray.parser._parse_scalar`` round-trips it via
    # ``ast.literal_eval``.
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
