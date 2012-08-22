# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ImproperlyConfigured
from django.db.models.query_utils import Q

def get_placeholder_conf(setting, placeholder, template=None, default=None):
    """
    Returns the placeholder configuration for a given setting. The key would for
    example be 'plugins'  or 'name'.
    
    If a template is given, it will try
    CMS_PLACEHOLDER_CONF['template placeholder'] and
    CMS_PLACEHOLDER_CONF['placeholder'], if no template is given only the latter
    is checked.
    """
    if placeholder:
        keys = []
        if template:
            keys.append("%s %s" % (template, placeholder))
        keys.append(placeholder)
        for key in keys:
            conf = settings.CMS_PLACEHOLDER_CONF.get(key)
            if not conf:
                continue
            value = conf.get(setting)
            if value:
                return value
    return default

def get_page_from_placeholder_if_exists(placeholder):
    import warnings
    warnings.warn(
        "The get_page_from_placeholder_if_exists function is deprecated. Use placeholder.page instead",
        DeprecationWarning
    )
    return placeholder.page if placeholder else None

def validate_placeholder_name(name):
    try:
        name.decode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        raise ImproperlyConfigured("Placeholder identifiers names may not "
           "contain non-ascii characters. If you wish your placeholder "
           "identifiers to contain non-ascii characters when displayed to "
           "users, please use the CMS_PLACEHOLDER_CONF setting with the 'name' "
           "key to specify a verbose name.")

    
class PlaceholderNoAction(object):
    can_copy = False
    
    def copy(self, **kwargs):
        return False
    
    def get_copy_languages(self, **kwargs):
        return []
    
    
class MLNGPlaceholderActions(PlaceholderNoAction):
    can_copy = True

    def copy(self, target_placeholder, source_language, fieldname, model, target_language, **kwargs):
        trgt = model.objects.get(**{fieldname: target_placeholder})
        src = model.objects.get(master=trgt.master, language_code=source_language)

        source_placeholder = getattr(src, fieldname, None)
        if not source_placeholder:
            return False
        plugins = source_placeholder.get_plugins_list()
        ptree = []
        new_plugins = []
        for p in plugins:
            new_plugins.append(p.copy_plugin(target_placeholder, target_language, ptree))
        return new_plugins
    
    def get_copy_languages(self, placeholder, model, fieldname, **kwargs):
        manager = model.objects
        src = manager.get(**{fieldname: placeholder})
        query = Q(master=src.master)
        query &= Q(**{'%s__cmsplugin__isnull' % fieldname: False})
        query &= ~Q(pk=src.pk)
        
        language_codes = manager.filter(query).values_list('language_code', flat=True).distinct()
        return [(lc, dict(settings.LANGUAGES)[lc]) for lc in language_codes]
