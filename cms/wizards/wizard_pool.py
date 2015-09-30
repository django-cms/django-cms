# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _

from cms.utils.django_load import load

from .wizard_base import Wizard


class AlreadyRegisteredException(Exception):
    pass


class WizardPool(object):
    _entries = {}
    _discovered = False

    def __init__(self):
        self._reset()

    # PRIVATE METHODS -----------------

    def _discover(self):
        if not self._discovered:
            load('cms_wizards')
            self._discovered = True

    def _clear(self):
        """Simply emties the pool but does not clear the discovered flag."""
        self._entries = {}

    def _reset(self):
        """Clears the wizard pool and clears the discovered flag."""
        self._clear()
        self._discovered = False

    # PUBLIC METHODS ------------------

    def is_registered(self, entry):
        """
        Returns True if the provided entry is registered. NOTE: this method will
        also trigger the discovery process, if it hasn't already been done.
        """
        self._discover()
        return entry.id in self._entries

    def register(self, entry, force=False):
        """
        Registers the provided «entry». If the entry.id is already in the pool,
        this method raises an AlreadyRegistered Exception.
        The exception can be bypassed by setting «force» to true. This will
        unceremoniously replace any existing wizard with the same underlying
        content-type.
        """
        assert isinstance(entry, Wizard), u"entry must be an instance of Wizard"
        if not force and self.is_registered(entry):
            raise AlreadyRegisteredException(
                _(u"A wizard has already been registered for model: %s") %
                entry.model.__name__)
        else:
            self._entries[entry.id] = entry

    def unregister(self, entry):
        """
        If «entry» is registered into the pool, remove it.
        :param entry: a wizard
        :return: True if a wizard was successfully removed, else False
        """
        assert isinstance(entry, Wizard), u"entry must be an instance of Wizard"
        if self.is_registered(entry):
            del self._entries[entry.id]
            return True
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
        return self._entries[entry]

    def get_entries(self):
        """Returns all entries in weight-order."""
        self._discover()
        return [value for (key, value) in sorted(
            self._entries.items(), key=lambda e: getattr(e[1], 'weight'))]

wizard_pool = WizardPool()
