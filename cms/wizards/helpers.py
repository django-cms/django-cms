from django.apps import apps


def get_entries():
    """
    Returns a list of (wizard.id, wizard) tuples (for all registered
    wizards) ordered by weight

    ``get_entries()`` is useful if it is required to have a list of all registered
    wizards. Typically, this is used to iterate over them all. Note that they will
    be returned in the order of their ``weight``: smallest numbers for weight are
    returned first.::

        for wizard_id, wizard in get_entries():
            # do something with a wizard...
    """
    wizards = apps.get_app_config('cms').cms_extension.wizards
    return [value for (key, value) in sorted(
            wizards.items(), key=lambda e: e[1].weight)]


def get_entry(entry_key):
    """
    Returns a wizard object based on its :attr:`~.cms.wizards.wizard_base.Wizard.id`.
    """
    return apps.get_app_config('cms').cms_extension.wizards[entry_key]
