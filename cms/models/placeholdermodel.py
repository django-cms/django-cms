# -*- coding: utf-8 -*-
from django.db.models import ManyToManyField

from cms.utils.compat import DJANGO_1_7, DJANGO_1_8
from django.contrib import admin
from django.contrib.auth import get_permission_codename
from django.db import models
from django.template.defaultfilters import title
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from cms.exceptions import LanguageError
from cms.utils.helpers import reversion_register
from cms.utils.i18n import get_language_object
from cms.utils.urlutils import admin_reverse


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
        name = get_placeholder_conf("name", self.slot, default=title(self.slot))
        name = _(name)
        return name

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

    def _get_permission(self, request, key):
        """
        Generic method to check the permissions for a request for a given key,
        the key can be: 'add', 'change' or 'delete'. For each attached object
        permission has to be granted either on attached model or on attached object.
          * 'add' and 'change' permissions on placeholder need either on add or change
            permission on attached object to be granted.
          * 'delete' need either on add, change or delete
        """
        if getattr(request, 'user', None) and request.user.is_superuser:
            return True
        perm_keys = {
            'add': ('add', 'change',),
            'change': ('add', 'change',),
            'delete': ('add', 'change', 'delete'),
        }
        if key not in perm_keys:
            raise Exception("%s is not a valid perm key. "
                            "'Only 'add', 'change' and 'delete' are allowed" % key)
        objects = [self.page] if self.page else self._get_attached_objects()
        obj_perm = None
        for obj in objects:
            obj_perm = False
            for key in perm_keys[key]:
                if self._get_object_permission(obj, request, key):
                    obj_perm = True
                    break
            if not obj_perm:
                return False
        return obj_perm

    def _get_object_permission(self, obj, request, key):
        if not getattr(request, 'user', None):
            return False
        opts = obj._meta
        perm_code = '%s.%s' % (opts.app_label, get_permission_codename(key, opts))
        return request.user.has_perm(perm_code) or request.user.has_perm(perm_code, obj)

    def has_change_permission(self, request):
        return self._get_permission(request, 'change')

    def has_add_permission(self, request):
        return self._get_permission(request, 'add')

    def has_delete_permission(self, request):
        return self._get_permission(request, 'delete')

    def render(self, context, width, lang=None, editable=True, use_cache=True):
        '''
        Set editable = False to disable front-end rendering for this render.
        '''
        from cms.plugin_rendering import render_placeholder
        if not 'request' in context:
            return '<!-- missing request -->'
        width = width or self.default_width
        if width:
            context['width'] = width
        return render_placeholder(self, context, lang=lang, editable=editable,
                                  use_cache=use_cache)

    def _get_related_objects(self):
        if DJANGO_1_7:
            return list(self._meta.get_all_related_objects())
        else:
            fields = self._meta._get_fields(
                forward=False, reverse=True,
                include_parents=True,
                include_hidden=False,
            )
            return list(obj for obj in fields if not isinstance(obj.field, ManyToManyField))

    def _get_attached_fields(self):
        """
        Returns an ITERATOR of all non-cmsplugin reverse foreign key related fields.
        """
        from cms.models import CMSPlugin
        if not hasattr(self, '_attached_fields_cache'):
            self._attached_fields_cache = []
            relations = self._get_related_objects()
            for rel in relations:
                if issubclass(rel.model, CMSPlugin):
                    continue
                from cms.admin.placeholderadmin import PlaceholderAdminMixin
                if DJANGO_1_7:
                    parent = rel.model
                else:
                    parent = rel.related_model
                if parent in admin.site._registry and isinstance(admin.site._registry[parent], PlaceholderAdminMixin):
                    field = getattr(self, rel.get_accessor_name())
                    try:
                        if field.count():
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
                if DJANGO_1_7:
                    parent = rel.model
                else:
                    parent = rel.related_model
                if parent == Page or parent == StaticPlaceholder:
                    relations.insert(0, relations.pop(relations.index(rel)))
            for rel in relations:
                if issubclass(rel.model, CMSPlugin):
                    continue
                from cms.admin.placeholderadmin import PlaceholderAdminMixin
                if DJANGO_1_7:
                    parent = rel.model
                else:
                    parent = rel.related_model
                if parent in admin.site._registry and isinstance(admin.site._registry[parent], PlaceholderAdminMixin):
                    field = getattr(self, rel.get_accessor_name())
                    try:
                        if field.count():
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
        if self.page or self.page_set.all().count():
            from cms.models import Page
            self._attached_model_cache = Page
            return Page
        field = self._get_attached_field()
        if field:
            self._attached_model_cache = field.model
            return field.model
        self._attached_model_cache = None
        return None

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

reversion_register(Placeholder)
