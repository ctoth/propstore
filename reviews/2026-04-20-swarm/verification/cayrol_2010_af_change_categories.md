# Cayrol 2010 AF change categories verification

Workstream item: T6.3. The workstream labels this as "Baumann-Brewka 2010 AF revision categories"; the implemented production surface cites Cayrol, de Saint-Cyr, and Lagasquie-Schiex 2010/2014, not Baumann-Brewka. I verified the actual implemented citation.

Opened page images:
- `papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/pngs/page-006.png` (printed p.55).
- `papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/pngs/page-007.png` (printed p.56).
- `papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/pngs/page-008.png` (printed p.57).

Verified paper content:
- Definition 8 defines decisive change.
- Table 1 and Definition 9 define restrictive change as a strict decrease in the number of extensions while at least two extensions remain.
- Definition 10 defines questioning change as an increase in the number of extensions.
- Definition 11 defines destructive change when the result has no extension or only the empty extension.

Implementation checked:
- `C:/Users/Q/code/argumentation/src/argumentation/af_revision.py::_classify_extension_change`.
- Paper-image verification exposed a boundary bug: a shrink from three extensions to two was classified as `ALTERING`.
- Upstream commits:
  - `76c84e6 test(af-revision): Cayrol restrictive changes allow two extensions`
  - `adedb7e fix(af-revision): classify two-extension Cayrol shrink as restrictive`

Verification:
- `uv run pytest tests/test_af_revision.py -k "restrictive_classification" -vv`: 2 passed.
- `uv run pytest tests/test_af_revision.py -vv`: 10 passed.
- `uv run pyright src`: 0 errors.
- Propstore wrapper: `powershell -File scripts/run_logged_pytest.ps1 -Label T12-cayrol-af-revision-dep tests/test_af_revision_postulates.py`: 4 passed, `created: 16/16 workers`.

Result: fixed and matches the opened PDF pages.
