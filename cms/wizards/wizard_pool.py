# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from cms.utils.django_load import load

from .wizard_base import Wizard


class WizardPool(object):

    def __init__(self):
        self.entries = {}
        self._discovered = False

    def _discover(self):
        if self._discovered:
            return
        load('cms_wizards')
        self._discovered = True

    def is_registered(self, entry):
        self._discover()
        return entry.id in self.entries

    def register(self, entry):
        assert isinstance(entry, Wizard), "entry must be an instance of Wizard"

        self.entries[entry.id] = entry

    # accepts Wizard instance or its "id", which is the PK of its content-type.
    def get_entry(self, entry):
        self._discover()

        if isinstance(entry, Wizard):
            entry = entry.id
        return self.entries[entry]

    def get_entries(self):
        self._discover()
        # we can simplify (or complicate) this by implementing comparison
        # methods on ContentEntry class
        return [value for (key, value) in sorted(
            self.entries.items(), key=lambda e: getattr(e[1], 'weight'))]

wizard_pool = WizardPool()
