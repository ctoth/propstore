# Core Fixed-Point Iterations - 2026-05-21

## Iteration 1 - `propstore/core/__init__.py`

Slice files read:

- `propstore/core/__init__.py`
- `propstore/context_lifting.py` as the caller exposed by the slice gate

Actions executed:

- `propstore/core/__init__.py`
  - Decision: `keep`.
  - Final owner: `propstore.core`.
  - Edit: none. The file is already a shallow package initializer with no
    eager imports and empty `__all__`.
  - Reason: package initializer does not preserve old production surfaces or
    pull unrelated runtime owners into core.
  - Gate: `rg -n -- "^(from|import)\s" propstore/core/__init__.py` is zero-hit.

- `from propstore.core import assertions as _assertions` in
  `propstore/context_lifting.py`
  - Decision: `delete`.
  - Final owner: concrete assertion reference module.
  - Edit: replaced the package-level import with
    `from propstore.core.assertions.refs import ContextReference` and updated
    typed uses.
  - Reason: package-level import kept a broad core convenience/re-export path
    alive. Callers must import the exact owner module.
  - Gate:
    `rg -n -- "propstore\.core import|from propstore\.core import" propstore tests`
    is zero-hit after the edit.

Gate results:

- Pass: no eager imports in `propstore/core/__init__.py`.
- Pass: `__all__` is empty.
- Pass: no `from propstore.core import ...` or `propstore.core import` callers
  remain under `propstore tests`.

Derived file disposition:

- `propstore/core/__init__.py`: `keep-file`.
- `propstore/context_lifting.py`: `split-file`; only the package-import surface
  was deleted in this iteration.

Next slice:

- Continue with the next tracked core file after
  `propstore/core/__init__.py`.
