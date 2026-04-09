"""Core package.

Import concrete modules directly, for example ``propstore.core.graph_types`` or
``propstore.core.id_types``. This package intentionally avoids eager re-exports
so submodule imports do not pull in unrelated runtime surfaces.
"""

__all__: list[str] = []
