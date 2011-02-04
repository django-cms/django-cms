# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy  as _
from django.core.exceptions import ImproperlyConfigured
from warnings import warn

def pre_patch():
    """Patch settings befere adding global cms defaults
    """
    
    # append some usefull properties to settings
    append_properties = {
        'i18n_installed': 'cms.middleware.multilingual.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES
    }
    
    for attr, value in append_properties.items():
        if not hasattr(settings, attr):
            setattr(settings._wrapped, attr, value)
    
    
def post_patch():
    """Patch settings after global are adde
    """
    if settings.CMS_TEMPLATE_INHERITANCE:
        # Append the magic inheritance template
        settings.CMS_TEMPLATES = tuple(settings.CMS_TEMPLATES) + (
            (settings.CMS_TEMPLATE_INHERITANCE_MAGIC, _('Inherit the template of the nearest ancestor')),
        ) 


def post_patch_check():
    """Post patch check, just make sure there isn't any misconfiguration. All
    the code for checking settings should go here.
    """
    if settings.CMS_TEMPLATES is None:
        raise ImproperlyConfigured('Please make sure you specified a CMS_TEMPLATES setting.')
    
    # check if is user middleware installed
    if settings.CMS_PERMISSION and not 'cms.middleware.user.CurrentUserMiddleware' in settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('CMS Permission system requires cms.middleware.user.CurrentUserMiddleware.\n'
            'Please put it into your MIDDLEWARE_CLASSES in settings file')
