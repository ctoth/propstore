"""Datalog/DeLP grounding: predicate registry, fact extraction, gunray bridge.

This package lowers the authored predicate/rule substrate
(:mod:`propstore.families.predicates`, :mod:`propstore.families.rules`) into the
``gunray`` defeasible-logic engine and projects the grounded result back into a
non-committal bundle and sidecar. The package ``__init__`` stays shallow
(CLAUDE.md): import the concrete modules at the call site that owns the behavior.
"""
