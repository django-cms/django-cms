# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy  as _
from sekizai.helpers import validate_template


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

    # Ensure templates are set, and more than just the inheritance setting.
    cms_templates_length = len(settings.CMS_TEMPLATES)
    if (cms_templates_length < 1 or
        (cms_templates_length == 1 and settings.CMS_TEMPLATES[0][0] == settings.CMS_TEMPLATE_INHERITANCE_MAGIC)):
        raise ImproperlyConfigured('Please make sure you specified a CMS_TEMPLATES setting.')
    
    # check if is user middleware installed
    if settings.CMS_PERMISSION and not 'cms.middleware.user.CurrentUserMiddleware' in settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('CMS Permission system requires cms.middleware.user.CurrentUserMiddleware.\n'
            'Please put it into your MIDDLEWARE_CLASSES in settings file')
    
    # check sekizai namespaces
    try:
        from django.template.loaders.app_directories import Loader
    except ImportError:
        return # south...
    for template in settings.CMS_TEMPLATES:
        if template[0] == settings.CMS_TEMPLATE_INHERITANCE_MAGIC:
            continue
        if not validate_template(template[0], ['js', 'css']):
            raise ImproperlyConfigured(
                "The 'js' and 'css' sekizai namespaces must be present in each template, "
                "- or a template it inherits from - defined in CMS_TEMPLATES. "
                "I can't find the namespaces in %r."
                % template[0]
            )
