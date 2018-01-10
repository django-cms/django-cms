# -*- coding: utf-8 -*-

import warnings

from datetime import datetime, timedelta

from django.contrib import admin
from django.db import models
from django.template.defaultfilters import title
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, force_text

from cms.cache.placeholder import clear_placeholder_cache
from cms.exceptions import LanguageError
from cms.utils import get_site_id
from cms.utils.compat import DJANGO_1_8
from cms.utils.i18n import get_language_object
from cms.utils.urlutils import admin_reverse
from cms.constants import (
    EXPIRE_NOW,
    MAX_EXPIRATION_TTL,
    PUBLISHER_STATE_DIRTY,
)
from cms.utils import get_language_from_request
from cms.utils import permissions
from cms.utils.conf import get_cms_setting


@python_2_unicode_compatible
class Placeholder(models.Model):
    """
    Attributes:
        is_static       Set to "True" for static placeholders by the template tag
        is_editable     If False the content of the placeholder is not editable in the frontend
    """
    slot = models.CharField(_("slot"), max_length=255, db_index=True, editable=False)
    default_width = models.PositiveSmallIntegerField(_("width"), null=True, editable=False)
    cache_placeholder = True
    is_static = False
    is_editable = True

    class Meta:
        app_label = 'cms'
        permissions = (
            (u"use_structure", u"Can use Structure mode"),
        )

    def __str__(self):
        return self.slot

    def __repr__(self):
        display = "<{module}.{class_name} id={id} slot='{slot}' object at {location}>".format(
            module=self.__module__,
            class_name=self.__class__.__name__,
            id=self.pk,
            slot=self.slot,
            location=hex(id(self)),
        )
        return display

    def clear(self, language=None):
        if language:
            qs = self.cmsplugin_set.filter(language=language)
        else:
            qs = self.cmsplugin_set.all()
        qs = qs.order_by('-depth').select_related()
        for plugin in qs:
            inst, cls = plugin.get_plugin_instance()
            if inst and getattr(inst, 'cmsplugin_ptr', False):
                inst.cmsplugin_ptr._no_reorder = True
                inst._no_reorder = True
                inst.delete(no_mp=True)
            else:
                plugin._no_reorder = True
                plugin.delete(no_mp=True)

    def get_label(self):
        from cms.utils.placeholder import get_placeholder_conf

        template = self.page.get_template() if self.page else None
        name = get_placeholder_conf("name", self.slot, template=template, default=title(self.slot))
        name = _(name)
        return name

    def get_extra_context(self, template=None):
        from cms.utils.placeholder import get_placeholder_conf
        return get_placeholder_conf("extra_context", self.slot, template, {})

    def get_add_url(self):
        return self._get_url('add_plugin')

    def get_edit_url(self, plugin_pk):
        return self._get_url('edit_plugin', plugin_pk)

    def get_move_url(self):
        return self._get_url('move_plugin')

    def get_delete_url(self, plugin_pk):
        return self._get_url('delete_plugin', plugin_pk)

    def get_changelist_url(self):
        return self._get_url('changelist')

    def get_clear_url(self):
        return self._get_url('clear_placeholder', self.pk)

    def get_copy_url(self):
        return self._get_url('copy_plugins')

    def get_extra_menu_items(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_extra_placeholder_menu_items(self)

    def _get_url(self, key, pk=None):
        model = self._get_attached_model()
        args = []
        if pk:
            args.append(pk)
        if not model:
            return admin_reverse('cms_page_%s' % key, args=args)
        else:
            app_label = model._meta.app_label
            model_name = model.__name__.lower()
            return admin_reverse('%s_%s_%s' % (app_label, model_name, key), args=args)

    def has_change_permission(self, user):
        """
        Returns True if user has permission
        to change all models attached to this placeholder.
        """
        from cms.utils.permissions import get_model_permission_codename

        attached_models = self._get_attached_models()

        if not attached_models:
            # technically if placeholder is not attached to anything,
            # user should not be able to change it but if is superuser
            # then we "should" allow it.
            return user.is_superuser

        attached_objects = self._get_attached_objects()

        for obj in attached_objects:
            try:
                perm = obj.has_placeholder_change_permission(user)
            except AttributeError:
                model = type(obj)
                change_perm = get_model_permission_codename(model, 'change')
                perm = user.has_perm(change_perm)

            if not perm:
                return False
        return True

    def has_add_plugin_permission(self, user, plugin_type):
        if not permissions.has_plugin_permission(user, plugin_type, "add"):
            return False

        if not self.has_change_permission(user):
            return False
        return True

    def has_add_plugins_permission(self, user, plugins):
        if not self.has_change_permission(user):
            return False

        for plugin in plugins:
            if not permissions.has_plugin_permission(user, plugin.plugin_type, "add"):
                return False
        return True

    def has_change_plugin_permission(self, user, plugin):
        if not permissions.has_plugin_permission(user, plugin.plugin_type, "change"):
            return False

        if not self.has_change_permission(user):
            return False
        return True

    def has_delete_plugin_permission(self, user, plugin):
        if not permissions.has_plugin_permission(user, plugin.plugin_type, "delete"):
            return False

        if not self.has_change_permission(user):
            return False
        return True

    def has_move_plugin_permission(self, user, plugin, target_placeholder):
        if not permissions.has_plugin_permission(user, plugin.plugin_type, "change"):
            return False

        if not target_placeholder.has_change_permission(user):
            return False

        if self != target_placeholder and not self.has_change_permission(user):
            return False
        return True

    def has_clear_permission(self, user, languages):
        if not self.has_change_permission(user):
            return False
        return self.has_delete_plugins_permission(user, languages)

    def has_delete_plugins_permission(self, user, languages):
        plugin_types = (
            self
            .cmsplugin_set
            .filter(language__in=languages)
            # exclude the clipboard plugin
            .exclude(plugin_type='PlaceholderPlugin')
            .values_list('plugin_type', flat=True)
            .distinct()
            # remove default ordering
            .order_by()
        )

        has_permission = permissions.has_plugin_permission

        for plugin_type in plugin_types.iterator():
            if not has_permission(user, plugin_type, "delete"):
                return False
        return True

    def _get_related_objects(self):
        fields = self._meta._get_fields(
            forward=False, reverse=True,
            include_parents=True,
            include_hidden=False,
        )
        return list(obj for obj in fields)

    def _get_attached_fields(self):
        """
        Returns an ITERATOR of all non-cmsplugin reverse related fields.
        """
        from cms.models import CMSPlugin, UserSettings
        if not hasattr(self, '_attached_fields_cache'):
            self._attached_fields_cache = []
            relations = self._get_related_objects()
            for rel in relations:
                if issubclass(rel.model, CMSPlugin):
                    continue
                from cms.admin.placeholderadmin import PlaceholderAdminMixin
                related_model = rel.related_model

                try:
                    admin_class = admin.site._registry[related_model]
                except KeyError:
                    admin_class = None

                # UserSettings is a special case
                # Attached objects are used to check permissions
                # and we filter out any attached object that does not
                # inherit from PlaceholderAdminMixin
                # Because UserSettings does not (and shouldn't) inherit
                # from PlaceholderAdminMixin, we add a manual exception.
                is_user_settings = related_model == UserSettings

                if is_user_settings or isinstance(admin_class, PlaceholderAdminMixin):
                    field = getattr(self, rel.get_accessor_name())
                    try:
                        if field.exists():
                            self._attached_fields_cache.append(rel.field)
                    except:
                        pass
        return self._attached_fields_cache

    def _get_attached_field(self):
        from cms.models import CMSPlugin, StaticPlaceholder, Page
        if not hasattr(self, '_attached_field_cache'):
            self._attached_field_cache = None
            relations = self._get_related_objects()
            for rel in relations:
                parent = rel.related_model
                if parent == Page or parent == StaticPlaceholder:
                    relations.insert(0, relations.pop(relations.index(rel)))
            for rel in relations:
                if issubclass(rel.model, CMSPlugin):
                    continue
                from cms.admin.placeholderadmin import PlaceholderAdminMixin
                parent = rel.related_model
                if parent in admin.site._registry and isinstance(admin.site._registry[parent], PlaceholderAdminMixin):
                    field = getattr(self, rel.get_accessor_name())
                    try:
                        if field.exists():
                            self._attached_field_cache = rel.field
                            break
                    except:
                        pass
        return self._attached_field_cache

    def _get_attached_field_name(self):
        field = self._get_attached_field()
        if field:
            return field.name
        return None

    def _get_attached_model(self):
        if hasattr(self, '_attached_model_cache'):
            return self._attached_model_cache
        if self.page or self.page_set.exists():
            from cms.models import Page
            self._attached_model_cache = Page
            return Page
        field = self._get_attached_field()
        if field:
            self._attached_model_cache = field.model
            return field.model
        self._attached_model_cache = None
        return None

    def _get_attached_admin(self, admin_site=None):
        from django.contrib.admin import site

        if not admin_site:
            admin_site = site

        model = self._get_attached_model()

        if not model:
            return
        return admin_site._registry.get(model)

    def _get_attached_models(self):
        """
        Returns a list of models of attached to this placeholder.
        """
        if hasattr(self, '_attached_models_cache'):
            return self._attached_models_cache
        self._attached_models_cache = [field.model for field in self._get_attached_fields()]
        return self._attached_models_cache

    def _get_attached_objects(self):
        """
        Returns a list of objects attached to this placeholder.
        """
        if DJANGO_1_8:
            return [obj for field in self._get_attached_fields()
                    for obj in getattr(self, field.related.get_accessor_name()).all()]
        else:
            return [obj for field in self._get_attached_fields()
                    for obj in getattr(self, field.remote_field.get_accessor_name()).all()]

    def page_getter(self):
        if not hasattr(self, '_page'):
            from cms.models.pagemodel import Page
            try:
                self._page = Page.objects.get(placeholders=self)
            except (Page.DoesNotExist, Page.MultipleObjectsReturned,):
                self._page = None
        return self._page

    def page_setter(self, value):
        self._page = value

    page = property(page_getter, page_setter)

    def get_plugins_list(self, language=None):
        return list(self.get_plugins(language))

    def get_plugins(self, language=None):
        if language:
            return self.cmsplugin_set.filter(language=language).order_by('path')
        else:
            return self.cmsplugin_set.all().order_by('path')

    def get_filled_languages(self):
        """
        Returns language objects for every language for which the placeholder
        has plugins.

        This is not cached as it's meant to eb used in the frontend editor.
        """

        languages = []
        for lang_code in set(self.get_plugins().values_list('language', flat=True)):
            try:
                languages.append(get_language_object(lang_code))
            except LanguageError:
                pass
        return languages

    def get_cached_plugins(self):
        return getattr(self, '_plugins_cache', [])

    @property
    def actions(self):
        from cms.utils.placeholder import PlaceholderNoAction

        if not hasattr(self, '_actions_cache'):
            field = self._get_attached_field()
            self._actions_cache = getattr(field, 'actions', PlaceholderNoAction())
        return self._actions_cache

    def get_cache_expiration(self, request, response_timestamp):
        """
        Returns the number of seconds (from «response_timestamp») that this
        placeholder can be cached. This is derived from the plugins it contains.

        This method must return: EXPIRE_NOW <= int <= MAX_EXPIRATION_IN_SECONDS

        :type request: HTTPRequest
        :type response_timestamp: datetime
        :rtype: int
        """
        min_ttl = MAX_EXPIRATION_TTL

        if not self.cache_placeholder or not get_cms_setting('PLUGIN_CACHE'):
            # This placeholder has a plugin with an effective
            # `cache = False` setting or the developer has explicitly
            # disabled the PLUGIN_CACHE, so, no point in continuing.
            return EXPIRE_NOW

        def inner_plugin_iterator(lang):
            """
            The placeholder will have a cache of all the concrete plugins it
            uses already, but just in case it doesn't, we have a code-path to
            generate them anew.

            This is made extra private as an inner function to avoid any other
            process stealing our yields.
            """
            if hasattr(self, '_all_plugins_cache'):
                for instance in self._all_plugins_cache:
                    plugin = instance.get_plugin_class_instance()
                    yield instance, plugin
            else:
                for plugin_item in self.get_plugins(lang):
                    yield plugin_item.get_plugin_instance()

        language = get_language_from_request(request, self.page)
        for instance, plugin in inner_plugin_iterator(language):
            plugin_expiration = plugin.get_cache_expiration(
                request, instance, self)

            # The plugin_expiration should only ever be either: None, a TZ-
            # aware datetime, a timedelta, or an integer.
            if plugin_expiration is None:
                # Do not consider plugins that return None
                continue
            if isinstance(plugin_expiration, (datetime, timedelta)):
                if isinstance(plugin_expiration, datetime):
                    # We need to convert this to a TTL against the
                    # response timestamp.
                    try:
                        delta = plugin_expiration - response_timestamp
                    except TypeError:
                        # Attempting to take the difference of a naive datetime
                        # and a TZ-aware one results in a TypeError. Ignore
                        # this plugin.
                        warnings.warn(
                            'Plugin %(plugin_class)s (%(pk)d) returned a naive '
                            'datetime : %(value)s for get_cache_expiration(), '
                            'ignoring.' % {
                                'plugin_class': plugin.__class__.__name__,
                                'pk': instance.pk,
                                'value': force_text(plugin_expiration),
                            })
                        continue
                else:
                    # Its already a timedelta instance...
                    delta = plugin_expiration
                ttl = int(delta.total_seconds() + 0.5)
            else:  # must be an int-like value
                try:
                    ttl = int(plugin_expiration)
                except ValueError:
                    # Looks like it was not very int-ish. Ignore this plugin.
                    warnings.warn(
                        'Plugin %(plugin_class)s (%(pk)d) returned '
                        'unexpected value %(value)s for '
                        'get_cache_expiration(), ignoring.' % {
                            'plugin_class': plugin.__class__.__name__,
                            'pk': instance.pk,
                            'value': force_text(plugin_expiration),
                        })
                    continue

            min_ttl = min(ttl, min_ttl)
            if min_ttl <= 0:
                # No point in continuing, we've already hit the minimum
                # possible expiration TTL
                return EXPIRE_NOW

        return min_ttl

    def clear_cache(self, language, site_id=None):
        if not site_id and self.page:
            site_id = self.page.node.site_id
        clear_placeholder_cache(self, language, get_site_id(site_id))

    def mark_as_dirty(self, language, clear_cache=True):
        """
        Utility method to mark the attached object of this placeholder
        (if any) as dirty.
        This allows us to know when the content in this placeholder
        has been changed.
        """
        from cms.models import Page, StaticPlaceholder, Title

        if clear_cache:
            self.clear_cache(language)

        # Find the attached model for this placeholder
        # This can be a static placeholder, page or none.
        attached_model = self._get_attached_model()

        if attached_model is Page:
            Title.objects.filter(
                page=self.page,
                language=language,
            ).update(publisher_state=PUBLISHER_STATE_DIRTY)

        elif attached_model is StaticPlaceholder:
            StaticPlaceholder.objects.filter(draft=self).update(dirty=True)

    def get_plugin_tree_order(self, language, parent_id=None):
        """
        Returns a list of plugin ids matching the given language
        ordered by plugin position.
        """
        plugin_tree_order = (
            self
            .get_plugins(language)
            .filter(parent=parent_id)
            .order_by('position')
            .values_list('pk', flat=True)
        )
        return list(plugin_tree_order)

    def get_vary_cache_on(self, request):
        """
        Returns a list of VARY headers.
        """
        def inner_plugin_iterator(lang):
            """See note in get_cache_expiration.inner_plugin_iterator()."""
            if hasattr(self, '_all_plugins_cache'):
                for instance in self._all_plugins_cache:
                    plugin = instance.get_plugin_class_instance()
                    yield instance, plugin
            else:
                for plugin_item in self.get_plugins(lang):
                    yield plugin_item.get_plugin_instance()

        if not self.cache_placeholder or not get_cms_setting('PLUGIN_CACHE'):
            return []

        vary_list = set()
        language = get_language_from_request(request, self.page)
        for instance, plugin in inner_plugin_iterator(language):
            if not instance:
                continue
            vary_on = plugin.get_vary_cache_on(request, instance, self)
            if not vary_on:
                # None, or an empty iterable
                continue
            if isinstance(vary_on, six.string_types):
                if vary_on.lower() not in vary_list:
                    vary_list.add(vary_on.lower())
            else:
                try:
                    for vary_on_item in iter(vary_on):
                        if vary_on_item.lower() not in vary_list:
                            vary_list.add(vary_on_item.lower())
                except TypeError:
                    warnings.warn(
                        'Plugin %(plugin_class)s (%(pk)d) returned '
                        'unexpected value %(value)s for '
                        'get_vary_cache_on(), ignoring.' % {
                            'plugin_class': plugin.__class__.__name__,
                            'pk': instance.pk,
                            'value': force_text(vary_on),
                        })

        return sorted(list(vary_list))

    def copy_plugins(self, target_placeholder, language=None, root_plugin=None):
        from cms.utils.plugins import copy_plugins_to_placeholder

        new_plugins = copy_plugins_to_placeholder(
            plugins=self.get_plugins_list(language),
            placeholder=target_placeholder,
            language=language,
            root_plugin=root_plugin,
        )
        return new_plugins
