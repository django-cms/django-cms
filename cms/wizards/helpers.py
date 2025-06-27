import warnings

from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning

from .wizard_base import get_entries, get_entry  # noqa: F401

warnings.warn(
    "The cms.wizards.helpers module is deprecated and will be removed in django CMS 5.1. "
    "Use cms.wizards.wizard_base.get_entries and cms.wizards.wizard_pool.get_entry instead.",
    RemovedInDjangoCMS51Warning,
    stacklevel=2,
)
