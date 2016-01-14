# -*- coding: utf-8 -*-
import re

from django.contrib.sites.models import SITE_CACHE, Site
from .compat.dj import is_installed

SITE_VAR = "site__exact"


# modify reversions to match our needs if required...
def reversion_register(model_class, fields=None, follow=(), format="json", exclude_fields=None):
    """CMS interface to reversion api - helper function. Registers model for
    reversion only if reversion is available.

    Auto excludes publisher fields.

    """

    # reversion's merely recommended, not required
    if not is_installed('reversion'):
        return

    if fields and exclude_fields:
        raise ValueError("Just one of fields, exclude_fields arguments can be passed.")

    opts = model_class._meta
    local_fields = opts.local_fields + opts.local_many_to_many
    if fields is None:
        fields = [field.name for field in local_fields]

    exclude_fields = exclude_fields or []

    fields = filter(lambda name: not name in exclude_fields, fields)

    from cms.utils import reversion_hacks
    reversion_hacks.register_draft_only(model_class, fields, follow, format)


def make_revision_with_plugins(obj, user=None, message=None):
    """
    Only add to revision if it is a draft.
    """
    from cms.models.pluginmodel import CMSPlugin
    # we can safely import reversion - calls here always check for
    # reversion in installed_applications first
    from cms.utils.reversion_hacks import revision_context, revision_manager
    cls = obj.__class__
    if hasattr(revision_manager, '_registration_key_for_model'):
        model_key = revision_manager._registration_key_for_model(cls)
    else:
        model_key = cls

    if model_key in revision_manager._registered_models:

        placeholder_relation = find_placeholder_relation(obj)

        if revision_context.is_active():
            if user:
                revision_context.set_user(user)
            if message:
                revision_context.set_comment(message)
            # add toplevel object to the revision
            adapter = revision_manager.get_adapter(obj.__class__)
            revision_context.add_to_context(revision_manager, obj, adapter.get_version_data(obj))
            # add placeholders to the revision
            for ph in obj.get_placeholders():
                phadapter = revision_manager.get_adapter(ph.__class__)
                revision_context.add_to_context(revision_manager, ph, phadapter.get_version_data(ph))
            # add plugins and subclasses to the revision
            filters = {'placeholder__%s' % placeholder_relation: obj}
            for plugin in CMSPlugin.objects.filter(**filters):
                plugin_instance, admin = plugin.get_plugin_instance()
                if plugin_instance:
                    padapter = revision_manager.get_adapter(plugin_instance.__class__)
                    revision_context.add_to_context(revision_manager, plugin_instance, padapter.get_version_data(plugin_instance))
                bpadapter = revision_manager.get_adapter(plugin.__class__)
                revision_context.add_to_context(revision_manager, plugin, bpadapter.get_version_data(plugin))


def find_placeholder_relation(obj):
    return 'page'


class classproperty(object):
    """Like @property, but for classes, not just instances.

    Example usage:

        >>> from cms.utils.helpers import classproperty
        >>> class A(object):
        ...     @classproperty
        ...     def x(cls):
        ...         return 'x'
        ...     @property
        ...     def y(self):
        ...         return 'y'
        ...
        >>> A.x
        'x'
        >>> A().x
        'x'
        >>> A.y
        <property object at 0x2939628>
        >>> A().y
        'y'

    """
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def current_site(request):
    site_pk = request.GET.get(SITE_VAR, None) if request.GET.get(SITE_VAR, None) else request.POST.get(SITE_VAR, None)
    if not site_pk:
        site_pk = request.session.get('cms_admin_site', None)
    if site_pk:
        try:
            site = SITE_CACHE.get(site_pk) or Site.objects.get(pk=site_pk)
            SITE_CACHE[site_pk] = site
            return site
        except Site.DoesNotExist:
            return None
    else:
        return Site.objects.get_current()


def normalize_name(name):
    """
    Converts camel-case style names into underscore seperated words. Example::

        >>> normalize_name('oneTwoThree')
        'one_two_three'
        >>> normalize_name('FourFiveSix')
        'four_five_six'

    taken from django.contrib.formtools
    """
    new = re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', name)
    return new.lower().strip('_')
