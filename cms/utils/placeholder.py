# -*- coding: utf-8 -*-
import operator

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query_utils import Q
from django.utils import six
from sekizai.helpers import get_varname

from cms.utils import get_cms_setting
from cms.utils.compat.dj import force_unicode


def get_toolbar_plugin_struct(plugins_list, slot, page, parent=None):
    """
    Return the list of plugins to render in the toolbar.
    The dictionary contains the label, the classname and the module for the
    plugin.
    Names and modules can be defined on a per-placeholder basis using
    'plugin_modules' and 'plugin_labels' attributes in CMS_PLACEHOLDER_CONF

    :param plugins_list: list of plugins valid for the placeholder
    :param slot: placeholder slot name
    :param page: the page
    :param parent: parent plugin class, if any
    :return: list of dictionaries
    """
    template = None
    if page:
        template = page.template
    main_list = []
    for plugin in plugins_list:
        allowed_parents = plugin().get_parent_classes(slot, page)
        if parent:
            ## skip to the next if this plugin is not allowed to be a child
            ## of the parent
            if allowed_parents and parent.__name__ not in allowed_parents:
                continue
        else:
            if allowed_parents:
                continue
        modules = get_placeholder_conf("plugin_modules", slot, template, default={})
        names = get_placeholder_conf("plugin_labels", slot, template, default={})
        main_list.append({'value': plugin.value,
                          'name': force_unicode(names.get(plugin.value, plugin.name)),
                          'module': force_unicode(modules.get(plugin.value, plugin.module))})
    return sorted(main_list, key=operator.itemgetter("module"))


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
            conf = get_cms_setting('PLACEHOLDER_CONF').get(key)
            if not conf:
                continue
            value = conf.get(setting)
            if value is not None:
                return value
            inherit = conf.get('inherit')
            if inherit :
                if ' ' in inherit:
                    inherit = inherit.split(' ')
                else:
                    inherit = (None, inherit,)
                value = get_placeholder_conf(setting, inherit[1], inherit[0], default)
                if value is not None:
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
    if not isinstance(name, six.string_types):
        raise ImproperlyConfigured("Placeholder identifier names need to be of type string. ")

    if not all(ord(char) < 128 for char in name):
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
        cache = {}
        new_plugins = []
        for p in plugins:
            new_plugins.append(p.copy_plugin(target_placeholder, target_language, cache))
        return new_plugins

    def get_copy_languages(self, placeholder, model, fieldname, **kwargs):
        manager = model.objects
        src = manager.get(**{fieldname: placeholder})
        query = Q(master=src.master)
        query &= Q(**{'%s__cmsplugin__isnull' % fieldname: False})
        query &= ~Q(pk=src.pk)

        language_codes = manager.filter(query).values_list('language_code', flat=True).distinct()
        return [(lc, dict(settings.LANGUAGES)[lc]) for lc in language_codes]


def restore_sekizai_context(context, changes):
    varname = get_varname()
    sekizai_container = context.get(varname)
    for key, values in changes.items():
        sekizai_namespace = sekizai_container[key]
        for value in values:
            sekizai_namespace.append(value)
