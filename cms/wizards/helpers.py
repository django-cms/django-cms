from django.apps import apps


def get_entries():
    """
    Returns a list of (wizard.id, wizard) tuples (for all registered
    wizards) ordered by weight
    """
    wizards = apps.get_app_config('cms').cms_extension.wizards
    return [value for (key, value) in sorted(
            wizards.items(), key=lambda e: getattr(e[1], 'weight'))]


def get_entry(entry_key):
    """
    Returns a wizard object based on its id.
    """
    return apps.get_app_config('cms').cms_extension.wizards[entry_key]
