"""Moved to :mod:`cms.toolbar.middleware`.

Every project names this module in ``MIDDLEWARE``, and ``cms.utils.check``
verifies that exact string, so the path keeps working (see :mod:`cms.compat`).
Django resolves middleware by importing the module and reading the attribute,
which a :pep:`562` shim serves.
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {"ToolbarMiddleware": "cms.toolbar.middleware.ToolbarMiddleware"},
    since="6.0",
)
