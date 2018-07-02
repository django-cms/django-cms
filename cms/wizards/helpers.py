# -*- coding: utf-8 -*-
from django.apps import apps


def get_entries():
    wizards = apps.get_app_config('cms').cms_extension.wizards
    return [value for (key, value) in sorted(
            wizards.items(), key=lambda e: getattr(e[1], 'weight'))]
