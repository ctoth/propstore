"""The import subsystem: typed import contract + repository import.

An import is non-committal: every external row becomes a defeasible source-branch
claim with honest provenance, never a privileged canonical fact
([[feedback_imports_are_opinions]]). :mod:`contract` defines the typed manifest
an importer must provide; :mod:`repository_import` lands it on a source branch via
the ordinary source-authoring path.
"""
