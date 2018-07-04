# -*- coding: utf-8 -*-
from django.apps import apps

from cms.wizards.wizard_base import Wizard


def get_entries():
    wizards = apps.get_app_config('cms').cms_extension.wizards
    return [value for (key, value) in sorted(
            wizards.items(), key=lambda e: getattr(e[1], 'weight'))]


def get_entry(entry_key):
    if isinstance(entry_key, Wizard):
        entry_key = entry_key.id
    return apps.get_app_config('cms').cms_extension.wizards[entry_key]
