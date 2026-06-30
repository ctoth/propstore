"""Owner-layer render view tier (CLAUDE.md layer 5).

The ``app`` package holds the typed *view-builders* that both the ``pks`` CLI and
the web routes consume. A view-builder takes an already-open
:class:`~propstore.world.WorldQuery` and a :class:`~propstore.world.RenderPolicy`
and returns a typed, JSON-ready view object. They emit no Click, no FastAPI, no
stdout, and never reconstruct a policy from flags — the single flag-to-policy
construction path is :func:`propstore.app.rendering.build_render_policy`, which the
adapters call before handing the policy down.

Discipline (CLAUDE.md):

* **Render-time filtering.** Visibility is decided here, over the full sidecar row
  set, never at build time. A present-but-hidden row is filtered, not dropped.
* **Honest ignorance.** An absent field renders as a vacuous / unknown view
  state, never a fabricated number. The view tier owns one state vocabulary,
  :class:`propstore.app.view_state.ViewState`, whose ``UNKNOWN`` member is
  distinct from ``BLOCKED`` (policy-hidden) and ``MISSING`` (no data authored).
"""
