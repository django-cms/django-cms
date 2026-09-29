"""Moved to :mod:`cms.wizards.wizard_base`.

The wizard pool itself is gone: wizards are registered with ``cms_wizards`` in
``cms_config.py``. The helpers that lived here stay importable from this path.
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "Wizard": "cms.wizards.wizard_base.Wizard",
        "entry_choices": "cms.wizards.wizard_base.entry_choices",
        "get_entries": "cms.wizards.wizard_base.get_entries",
        "get_entry": "cms.wizards.wizard_base.get_entry",
    },
    since="6.0",
    fallback="cms.wizards.wizard_base",
)
