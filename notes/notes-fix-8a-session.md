# Fix 8A: WorldModel Boilerplate DRY — Session Notes

## GOAL
Extract repeated WorldModel/sidecar-not-found boilerplate into shared helper in `propstore/cli/helpers.py`.

## OBSERVATIONS

### Baseline
- `uv run pytest tests/test_cli.py -q` => 62 passed

### Pattern 1: WorldModel try/except (14 instances)
Lines: 569-573, 590-594, 627-631, 675-679, 709-713, 1323-1327, 1372-1376, 1434-1438, 1637-1641, 1687-1691, 1733-1737, 1773-1777, 1837-1841
Each does:
```python
try:
    wm = WorldModel(repo)
except FileNotFoundError:
    click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
    sys.exit(1)
# ... use wm ...
wm.close()
```

### Pattern 2: _bind_atms_world try/except (9 instances)
Lines: 813-817, 847-851, 890-894, 938-942, 999-1003, 1057-1061, 1116-1120, 1181-1185, 1259-1263
Each does:
```python
try:
    wm, bound, _bindings, concept_id = _bind_atms_world(repo, args, context=context)
except FileNotFoundError:
    click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
    sys.exit(1)
# ... use wm, bound ...
wm.close()
```

### WorldModel already has context manager support
- `__enter__` and `__exit__` in `propstore/world/model.py` lines 57-63
- So `with WorldModel(repo) as wm:` works and auto-closes

### Plan
1. Add `open_world_model` context manager to `propstore/cli/helpers.py` (handles FileNotFoundError + auto-close)
2. Replace all Pattern 1 instances with `with open_world_model(repo) as wm:`
3. For Pattern 2: update `_bind_atms_world` to use the helper internally, but the callers still need the try/except wrapping since `_bind_atms_world` itself can raise FileNotFoundError. Better approach: make `_bind_atms_world` use `open_world_model` internally and return it — but then the caller needs to close. Actually, since WorldModel already has __enter__/__exit__, the context manager approach from the prompt is the cleanest.

### Key concern
- Many commands have early returns with `wm.close()` before the final `wm.close()`. Using a context manager (`with`) handles all of those automatically.
- The `build` command (line 182-207) uses WorldModel in a different pattern (try/except where FileNotFoundError is a fallback, not an error). Should NOT be refactored.

## DONE
- Added `open_world_model` context manager to `propstore/cli/helpers.py`
- Added import of `open_world_model` to `compiler_cmds.py`
- Replaced `world_status` (line 562)
- Replaced `world_query` (line 582)

## IN PROGRESS
- Need to replace: world_bind, world_explain, world_algorithms, and all remaining Pattern 1 instances
- Need to replace: all 9 `_bind_atms_world` Pattern 2 instances
- Then run full test suite

## APPROACH
- Doing one-at-a-time edits is very slow with this many instances (23 total)
- Better approach: read remaining sections, do larger batch replacements
- The `_bind_atms_world` function itself should use `open_world_model` internally, which eliminates the FileNotFoundError from all 9 callers automatically

## NEXT
- Replace remaining Pattern 1 instances (world_bind, world_explain, world_algorithms, + later ones)
- Update `_bind_atms_world` to use `open_world_model`
- Replace all Pattern 2 callers to remove try/except
- Run tests, commit
