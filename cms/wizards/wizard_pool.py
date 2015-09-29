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

    def unregister(self, entry):
        """
        If «entry» is registered into the pool, remove it.
        :param entry: a wizard
        :return: True if a wizard was successfully removed, else False
        """
        assert isinstance(entry, Wizard), "entry must be an instance of Wizard"
        if self.is_registered(entry):
            try:
                del self.entries[entry.id]
                return True
            except KeyError:
                pass
        return False

    def get_entry(self, entry):
        """
        :param entry: Accepts a Wizard instance or its "id" (which is the PK of
                      its content-type).
        :return: The Wizard instance, if registered else raises IndexError.
        """
        self._discover()

        if isinstance(entry, Wizard):
            entry = entry.id
        return self.entries[entry]

    def get_entries(self):
        """Returns all entries in weight-order."""
        self._discover()
        return [value for (key, value) in sorted(
            self.entries.items(), key=lambda e: getattr(e[1], 'weight'))]

wizard_pool = WizardPool()
