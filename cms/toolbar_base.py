"""Moved to :mod:`cms.toolbar.base`.

``CMSToolbar`` is the base class every ``cms_toolbars.py`` in the ecosystem
subclasses, so this path keeps working (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {"CMSToolbar": "cms.toolbar.base.CMSToolbar"},
    since="6.0",
)
