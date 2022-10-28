from django.apps import apps
from django.utils.translation import gettext as _

from cms.wizards.helpers import get_entries, get_entry
from cms.wizards.wizard_base import Wizard


class AlreadyRegisteredException(Exception):
    pass


def entry_choices(user, page):
    """
    Yields a list of wizard entries that the current user can use based on their
    permission to add instances of the underlying model objects.
    """
    for entry in get_entries():
        if entry.user_has_add_permission(user, page=page):
            yield (entry.id, entry.title)


class WizardPool():

    def is_registered(self, entry, **kwargs):
        """
        Returns True if the provided entry is registered.

        NOTE: This method is for backwards compatibility only
        """
        # TODO: Add deprecation warning
        return entry.id in apps.get_app_config('cms').cms_extension.wizards

    def register(self, entry):
        """
        Registers the provided «entry».

        Raises AlreadyRegisteredException if the entry is already registered.
        """
        # TODO: Add deprecation warning
        assert isinstance(entry, Wizard), u"entry must be an instance of Wizard"
        if self.is_registered(entry, passive=True):
            model = entry.get_model()
            raise AlreadyRegisteredException(
                _(u"A wizard has already been registered for model: %s") %
                model.__name__)
        else:
            apps.get_app_config('cms').cms_extension.wizards[entry.id] = entry

    def unregister(self, entry):
        """
        If «entry» is registered into the pool, remove it.

        Returns True if the entry was successfully registered, else False.

        NOTE: This method is here for backwards compatibility only.
        """
        # TODO: Add deprecation warning
        assert isinstance(entry, Wizard), u"entry must be an instance of Wizard"
        if self.is_registered(entry):
            del apps.get_app_config('cms').cms_extension.wizards[entry.id]
            return True
        return False

    def get_entry(self, entry):
        """
        Returns the wizard from the pool identified by «entry», which may be a
        Wizard instance or its "id" (which is the PK of its underlying
        content-type).

        NOTE: This method is here for backwards compatibility only.
        Use cms.wizards.helpers.get_enty when possible.
        """
        # TODO: Deprecated warning
        return get_entry(entry)


wizard_pool = WizardPool()
