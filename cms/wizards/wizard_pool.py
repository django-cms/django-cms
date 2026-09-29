from django.apps import apps
from django.utils.translation import gettext as _

from cms.wizards.wizard_base import Wizard, entry_choices, get_entries, get_entry  # noqa: F401


class AlreadyRegisteredException(Exception):
    pass

