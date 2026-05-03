"""``@scope_policy`` decorator — declarative scope-completeness policy.

Per quire/plans/worldline-journal-bridge-2026-05-02.md section 13.

Snapshots whose ``scope`` (a ``RevisionScope``) is partially-populated
arise naturally for synthetic / test journals and for snapshots authored
before propstore captured every scope field. Methods that consume
snapshots can declare per-kwarg policy:

- ``degrade={kwarg: (required_fields,)}`` — when ``kwarg`` is truthy and
  any required field is unset, force ``kwarg=False`` and emit a
  ``UserWarning``. Use when the fallback (``kwarg=False``) gives a
  *meaningful* answer (e.g. ``rebind=True → rebind=False`` still returns
  a correct claim view).
- ``require={kwarg: (required_fields,)}`` — when ``kwarg`` is truthy and
  any required field is unset, raise ``ValueError``. Use when no
  fallback gives a meaningful answer (e.g. ``heavy=True`` without
  ``scope.commit`` — the entire point of ``heavy`` is rebuilding from
  that commit).

The scope is extracted from a named argument (``extract_from``) — for a
journal-bearing method this is typically the journal kwarg, in which
case ``extract_step`` names the step-index kwarg used to walk
``journal.entries[step].state_out.state.scope``.
"""

from __future__ import annotations

import functools
import inspect
import warnings
from collections.abc import Mapping
from typing import Any, Callable


def scope_policy(
    *,
    extract_from: str,
    extract_step: str | None = None,
    degrade: Mapping[str, tuple[str, ...]] | None = None,
    require: Mapping[str, tuple[str, ...]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory enforcing scope-completeness policy on a method.

    See module docstring for semantics. The decorator is order-independent
    over ``degrade``/``require`` rules: ``require`` rules raise before
    ``degrade`` rules degrade.
    """
    degrade_rules = dict(degrade or {})
    require_rules = dict(require or {})

    def _missing(scope: Any, fields: tuple[str, ...]) -> list[str]:
        return [f for f in fields if not getattr(scope, f, None)]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            obj = bound.arguments[extract_from]
            if extract_step is not None:
                obj = obj.entries[bound.arguments[extract_step]].state_out
            scope = obj.state.scope

            for kw, fields in require_rules.items():
                if bound.arguments.get(kw):
                    miss = _missing(scope, fields)
                    if miss:
                        raise ValueError(
                            f"{func.__qualname__}({kw}=True) requires "
                            f"snapshot.scope to have {list(fields)}; missing: {miss}"
                        )
            for kw, fields in degrade_rules.items():
                if bound.arguments.get(kw):
                    miss = _missing(scope, fields)
                    if miss:
                        warnings.warn(
                            f"{func.__qualname__}({kw}=True) requested but "
                            f"snapshot.scope is missing {miss}; degrading to "
                            f"{kw}=False",
                            UserWarning,
                            stacklevel=2,
                        )
                        kwargs[kw] = False
                        # If the kwarg was supplied positionally, drop the
                        # positional binding so the kwargs override wins.
                        bound.arguments[kw] = False
                        args = bound.args
            return func(*args, **kwargs)

        return wrapper

    return decorator
