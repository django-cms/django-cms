from django.apps import apps
from django.utils.translation import gettext as _

from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning
from cms.wizards.wizard_base import Wizard, entry_choices, get_entries, get_entry  # noqa: F401


class AlreadyRegisteredException(Exception):
    pass


class WizardPool:
    """
    .. deprecated:: 4.0
    """

    def is_registered(self, entry, **kwargs):
        """
        .. deprecated:: 4.0

        Returns True if the provided entry is registered.
        """
        # TODO: Add deprecation warning
        return entry.id in apps.get_app_config('cms').cms_extension.wizards

    def register(self, entry):
        """
        .. deprecated:: 4.0

        You may notice from the example above that the last line in the sample code is::

            wizard_pool.register(my_app_wizard)

        This sort of thing should look very familiar, as a similar approach is used for
        cms_apps, template tags and even Django's admin.

        Calling the wizard pool's ``register`` method will register the provided wizard
        into the pool, unless there is already a wizard of the same module and class
        name. In this case, the register method will raise a
        ``cms.wizards.wizard_pool.AlreadyRegisteredException``.
        """
        import warnings

        warnings.warn(
            "Using wizard_pool is deprecated. Use the cms_config instead.",
            RemovedInDjangoCMS51Warning,
            stacklevel=2,
        )
        assert isinstance(entry, Wizard), "entry must be an instance of Wizard"
        if self.is_registered(entry, passive=True):
            model = entry.get_model()
            raise AlreadyRegisteredException(
                _("A wizard has already been registered for model: %s") %
                model.__name__)
        else:
            apps.get_app_config('cms').cms_extension.wizards[entry.id] = entry

    def unregister(self, entry):
        """
        .. deprecated:: 4.0

        If «entry» is registered into the pool, remove it.

        Returns True if the entry was successfully registered, else False.
        """
        # TODO: Add deprecation warning
        assert isinstance(entry, Wizard), "entry must be an instance of Wizard"
        if self.is_registered(entry):
            del apps.get_app_config('cms').cms_extension.wizards[entry.id]
            return True
        return False

    def get_entry(self, entry):
        """
        .. deprecated:: 4.0 use :func:`cms.wizards.helpers.get_entry` instead

        Returns the wizard from the pool identified by «entry», which may be a
        Wizard instance or its "id" (which is the PK of its underlying
        content-type).
        """
        # TODO: Deprecated warning
        return get_entry(entry)


wizard_pool = WizardPool()
"""
..  warning::
    .. deprecated:: 4.0

    Using wizard_pool is deprecated. Use `cms.wizards.helper` functions instead.
    Since django CMS version 4 wizards are registered with the cms using
    :class:`cms.app_base.CMSAppConfig` in ``cms_config.py``.
"""
