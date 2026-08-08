"""Repository history owner cores — ``pks log`` / ``diff`` / ``show`` / ``checkout``.

This package holds the owner-layer functions behind the (Phase-10) history Click
adapters. They read quire's git log / diff / show and the build pipeline's
rebuild-from-commit, returning typed report objects. No Click, no stdout, no
``sys.exit`` (CLI-adapter discipline, CLAUDE.md): the CLI maps these reports and
typed errors to output and exit codes.
"""
