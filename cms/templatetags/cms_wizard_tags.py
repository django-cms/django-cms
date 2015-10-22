# -*- coding: utf-8 -*-

from django import template

from classytags.arguments import Argument
from classytags.core import Options
from classytags.helpers import AsTag

from cms.wizards.wizard_pool import wizard_pool

register = template.Library()


class WizardProperty(AsTag):
    name = 'cms_wizard'

    options = Options(
        Argument('wizard_id'),
        Argument('property', required=False, default=None),
        'as',
        Argument('varname', required=False, resolve=False),
    )

    def get_value(self, context, wizard_id, property=None):
        """
        If called with a «property» returns the property of the wizard
        identified by «wizard_id». If no «property», just return the entire
        wizard object.
        """
        try:
            wizard = wizard_pool.get_entry(wizard_id)
        except ValueError:
            wizard = None

        if wizard:
            if property in ['description', 'title', 'weight']:
                # getters
                getter = getattr(wizard, "get_{0}".format(property), None)
                return getter()
            elif property in ['id', 'form', 'model', 'template_name']:
                # properties
                return getattr(wizard, property, None)
            else:
                return wizard
        return None

register.tag(WizardProperty)
