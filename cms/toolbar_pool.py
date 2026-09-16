"""Moved to :mod:`cms.toolbar.pool`.

``toolbar_pool`` is how every ``cms_toolbars.py`` in the ecosystem registers, so
this path keeps working (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "ToolbarPool": "cms.toolbar.pool.ToolbarPool",
        "toolbar_pool": "cms.toolbar.pool.toolbar_pool",
    },
    since="6.0",
)
