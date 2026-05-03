from __future__ import annotations

import functools
import inspect
import warnings
from collections.abc import Callable, Mapping
from typing import Any, TypeVar, cast


_F = TypeVar("_F", bound=Callable[..., Any])


def scope_policy(
    *,
    extract_from: str,
    extract_step: str | None = None,
    degrade: Mapping[str, tuple[str, ...]] = (),
    require: Mapping[str, tuple[str, ...]] = (),
) -> Callable[[_F], _F]:
    degrade = dict(degrade) if degrade else {}
    require = dict(require) if require else {}

    def _missing(scope: object, fields: tuple[str, ...]) -> list[str]:
        return [field for field in fields if not getattr(scope, field, None)]

    def decorator(func: _F) -> _F:
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            obj = bound.arguments[extract_from]
            if extract_step is not None:
                obj = obj.entries[bound.arguments[extract_step]].state_out
            scope = obj.state.scope

            for kw, fields in require.items():
                if bound.arguments.get(kw) and (missing := _missing(scope, fields)):
                    raise ValueError(
                        f"{func.__qualname__}({kw}=True) requires "
                        f"snapshot.scope to have {fields}; missing: {missing}"
                    )
            for kw, fields in degrade.items():
                if bound.arguments.get(kw) and (missing := _missing(scope, fields)):
                    warnings.warn(
                        f"{func.__qualname__}({kw}=True) requested but "
                        f"snapshot.scope is missing {missing}; degrading to "
                        f"{kw}=False",
                        stacklevel=2,
                    )
                    kwargs[kw] = False
            return func(*args, **kwargs)

        return cast(_F, wrapper)

    return decorator
