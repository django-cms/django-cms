# -*- coding: utf-8 -*-
import warnings

from django import template

from classytags.arguments import Argument
from classytags.core import Options
from classytags.helpers import AsTag

from cms.wizards.wizard_pool import wizard_pool

register = template.Library()


@register.tag(name='cms_wizard')
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
        warnings.warn(
            "Templatetag cms_wizard will be removed in django CMS 3.5",
            PendingDeprecationWarning
        )
        try:
            wizard = wizard_pool.get_entry(wizard_id)
            return wizard.widget_attributes.get(property, wizard)
        except ValueError:
            return None
