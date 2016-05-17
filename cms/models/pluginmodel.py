# -*- coding: utf-8 -*-
from datetime import date
import json
from operator import itemgetter
import os
import warnings

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import signals, Model, ManyToManyField
from django.db.models.base import model_unpickle, ModelBase
from django.db.models.query_utils import DeferredAttribute
from django.utils import six, timezone
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.six.moves import filter
from django.utils.translation import ugettext_lazy as _

from cms.exceptions import DontUsePageAttributeWarning
from cms.models.placeholdermodel import Placeholder
from cms.plugin_rendering import PluginContext, render_plugin
from cms.utils import get_cms_setting
from cms.utils.helpers import reversion_register
from cms.utils.urlutils import admin_reverse

from treebeard.mp_tree import MP_Node


class BoundRenderMeta(object):
    def __init__(self, meta):
        self.index = 0
        self.total = 1
        self.text_enabled = getattr(meta, 'text_enabled', False)


class PluginModelBase(ModelBase):
    """
    Metaclass for all CMSPlugin subclasses. This class should not be used for
    any other type of models.
    """

    def __new__(cls, name, bases, attrs):
        # remove RenderMeta from the plugin class
        attr_meta = attrs.pop('RenderMeta', None)

        # create a new class (using the super-metaclass)
        new_class = super(PluginModelBase, cls).__new__(cls, name, bases, attrs)

        # if there is a RenderMeta in attrs, use this one
        # else try to use the one from the superclass (if present)
        meta = attr_meta or getattr(new_class, '_render_meta', None)
        treebeard_view_fields = (f for f in new_class._meta.fields
                                 if f.name in ('depth', 'numchild', 'path'))
        for field in treebeard_view_fields:
            field.editable = False
        # set a new BoundRenderMeta to prevent leaking of state
        new_class._render_meta = BoundRenderMeta(meta)
        return new_class


@python_2_unicode_compatible
class CMSPlugin(six.with_metaclass(PluginModelBase, MP_Node)):
    '''
    The base class for a CMS plugin model. When defining a new custom plugin, you should
    store plugin-instance specific information on a subclass of this class.

    An example for this would be to store the number of pictures to display in a galery.

    Two restrictions apply when subclassing this to use in your own models:
    1. Subclasses of CMSPlugin *cannot be further subclassed*
    2. Subclasses of CMSPlugin cannot define a "text" field.

    '''
    placeholder = models.ForeignKey(Placeholder, editable=False, null=True)
    parent = models.ForeignKey('self', blank=True, null=True, editable=False)
    position = models.PositiveSmallIntegerField(_("position"), default = 0, editable=False)
    language = models.CharField(_("language"), max_length=15, blank=False, db_index=True, editable=False)
    plugin_type = models.CharField(_("plugin_name"), max_length=50, db_index=True, editable=False)
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=timezone.now)
    changed_date = models.DateTimeField(auto_now=True)
    child_plugin_instances = None
    translatable_content_excluded_fields = []

    class Meta:
        app_label = 'cms'

    class RenderMeta:
        index = 0
        total = 1
        text_enabled = False

    def __reduce__(self):
        """
        Provide pickling support. Normally, this just dispatches to Python's
        standard handling. However, for models with deferred field loading, we
        need to do things manually, as they're dynamically created classes and
        only module-level classes can be pickled by the default path.
        """
        data = self.__dict__
        # The obvious thing to do here is to invoke super().__reduce__()
        # for the non-deferred case. Don't do that.
        # On Python 2.4, there is something wierd with __reduce__,
        # and as a result, the super call will cause an infinite recursion.
        # See #10547 and #12121.
        deferred_fields = [f for f in self._meta.fields
                           if isinstance(self.__class__.__dict__.get(f.attname),
                                         DeferredAttribute)]
        model = self._meta.proxy_for_model
        return (model_unpickle, (model, deferred_fields), data)

    def __str__(self):
        return force_text(self.pk)

    def get_plugin_name(self):
        from cms.plugin_pool import plugin_pool

        return plugin_pool.get_plugin(self.plugin_type).name

    def get_short_description(self):
        instance = self.get_plugin_instance()[0]
        if instance is not None:
            return force_text(instance)
        return _("<Empty>")

    def get_plugin_class(self):
        from cms.plugin_pool import plugin_pool

        return plugin_pool.get_plugin(self.plugin_type)

    def get_plugin_class_instance(self, admin=None):
        plugin_class = self.get_plugin_class()
        # needed so we have the same signature as the original ModelAdmin
        return plugin_class(plugin_class.model, admin)

    def get_plugin_instance(self, admin=None):
        '''
        Given a plugin instance (usually as a CMSPluginBase), this method
        returns a tuple containing:

            instance - The instance AS THE APPROPRIATE SUBCLASS OF
                       CMSPluginBase and not necessarily just 'self', which is
                       often just a CMSPluginBase,

            plugin   - the associated plugin class instance (subclass
                       of CMSPlugin)
        '''
        plugin = self.get_plugin_class_instance(admin)
        if hasattr(self, "_inst"):
            return self._inst, plugin
        if plugin.model != self.__class__:  # and self.__class__ == CMSPlugin:
            # (if self is actually a subclass, getattr below would break)
            try:
                instance = plugin.model.objects.get(cmsplugin_ptr=self)
                instance._render_meta = self._render_meta
            except (AttributeError, ObjectDoesNotExist):
                instance = None
        else:
            instance = self
        self._inst = instance
        return self._inst, plugin

    def render_plugin(self, context=None, placeholder=None, admin=False, processors=None):
        instance, plugin = self.get_plugin_instance()
        request = None
        current_app = None
        if context:
            request = context.get('request', None)
            if request:
                current_app = getattr(request, 'current_app', None)
            if not current_app:
                current_app = context.current_app if context else None

        if instance and not (admin and not plugin.admin_preview):
            if not placeholder or not isinstance(placeholder, Placeholder):
                placeholder = instance.placeholder
            placeholder_slot = placeholder.slot
            context = PluginContext(context, instance, placeholder, current_app=current_app)
            context = plugin.render(context, instance, placeholder_slot)
            page = None
            if request:
                page = request.current_page
            plugin.cms_plugin_instance = instance
            context['allowed_child_classes'] = plugin.get_child_classes(placeholder_slot, page)
            context['allowed_parent_classes'] = plugin.get_parent_classes(placeholder_slot, page)
            if plugin.render_plugin:
                template = plugin._get_render_template(context, instance, placeholder)
                if not template:
                    raise ValidationError("plugin has no render_template: %s" % plugin.__class__)
            else:
                template = None
            return render_plugin(context, instance, placeholder, template, processors, current_app)
        else:
            from cms.middleware.toolbar import toolbar_plugin_processor

            if processors and toolbar_plugin_processor in processors:
                if not placeholder:
                    placeholder = self.placeholder
                context = PluginContext(context, self, placeholder, current_app=current_app)
                template = None
                return render_plugin(context, self, placeholder, template, processors, current_app)
        return ""

    def get_media_path(self, filename):
        pages = self.placeholder.page_set.all()
        if pages.count():
            return pages[0].get_media_path(filename)
        else:  # django 1.0.2 compatibility
            today = date.today()
            return os.path.join(get_cms_setting('PAGE_MEDIA_PATH'),
                                str(today.year), str(today.month), str(today.day), filename)

    @property
    def page(self):
        warnings.warn(
            "Don't use the page attribute on CMSPlugins! CMSPlugins are not "
            "guaranteed to have a page associated with them!",
            DontUsePageAttributeWarning)
        return self.placeholder.page if self.placeholder_id else None

    def get_instance_icon_src(self):
        """
        Get src URL for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        return plugin.icon_src(instance) if instance else u''

    def get_instance_icon_alt(self):
        """
        Get alt text for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        return force_text(plugin.icon_alt(instance)) if instance else u''

    def update(self, refresh=False, **fields):
        CMSPlugin.objects.filter(pk=self.pk).update(**fields)
        if refresh:
            return self.reload()
        return

    def save(self, no_signals=False, *args, **kwargs):
        if not self.depth:
            if self.parent_id or self.parent:
                self.parent.add_child(instance=self)
            else:
                if not self.position and not self.position == 0:
                    self.position = CMSPlugin.objects.filter(parent__isnull=True,
                                                             language=self.language,
                                                             placeholder_id=self.placeholder_id).count()
                self.add_root(instance=self)
            return
        super(CMSPlugin, self).save(*args, **kwargs)

    def reload(self):
        return CMSPlugin.objects.get(pk=self.pk)

    def move(self, target, pos=None):
        super(CMSPlugin, self).move(target, pos)
        self = self.reload()

        try:
            new_pos = max(CMSPlugin.objects.filter(parent_id=self.parent_id,
                                                   placeholder_id=self.placeholder_id,
                                                   language=self.language).exclude(pk=self.pk).order_by('depth', 'path').values_list('position', flat=True)) + 1
        except ValueError:
            # This is the first plugin in the set
            new_pos = 0
        return self.update(refresh=True, position=new_pos)

    def set_base_attr(self, plugin):
        for attr in ['parent_id', 'placeholder', 'language', 'plugin_type', 'creation_date', 'depth', 'path',
                     'numchild', 'pk', 'position']:
            setattr(plugin, attr, getattr(self, attr))

    def copy_plugin(self, target_placeholder, target_language, parent_cache, no_signals=False):
        """
        Copy this plugin and return the new plugin.

        The logic of this method is the following:

         # get a new generic plugin instance
         # assign the position in the plugin tree
         # save it to let mptt/treebeard calculate the tree attributes
         # then get a copy of the current plugin instance
         # assign to it the id of the generic plugin instance above;
           this will effectively change the generic plugin created above
           into a concrete one
         # copy the tree related attributes from the generic plugin to
           the concrete one
         # save the concrete plugin
         # trigger the copy relations
         # return the generic plugin instance

        This copy logic is required because we don't know what the fields of
        the real plugin are. By getting another instance of it at step 4 and
        then overwriting its ID at step 5, the ORM will copy the custom
        fields for us.
        """
        try:
            plugin_instance, cls = self.get_plugin_instance()
        except KeyError:  # plugin type not found anymore
            return

        # set up some basic attributes on the new_plugin
        new_plugin = CMSPlugin()
        new_plugin.placeholder = target_placeholder
        # we assign a parent to our new plugin
        parent_cache[self.pk] = new_plugin
        if self.parent:
            parent = parent_cache[self.parent_id]
            parent = CMSPlugin.objects.get(pk=parent.pk)
            new_plugin.parent_id = parent.pk
            new_plugin.parent = parent
        new_plugin.language = target_language
        new_plugin.plugin_type = self.plugin_type
        if no_signals:
            from cms.signals import pre_save_plugins

            signals.pre_save.disconnect(pre_save_plugins, sender=CMSPlugin, dispatch_uid='cms_pre_save_plugin')
            signals.pre_save.disconnect(pre_save_plugins, sender=CMSPlugin)
            new_plugin._no_reorder = True
        new_plugin.save()
        if plugin_instance:
            # get a new instance so references do not get mixed up
            plugin_instance = plugin_instance.__class__.objects.get(pk=plugin_instance.pk)
            plugin_instance.pk = new_plugin.pk
            plugin_instance.id = new_plugin.pk
            plugin_instance.placeholder = target_placeholder
            plugin_instance.cmsplugin_ptr = new_plugin
            plugin_instance.language = target_language
            plugin_instance.parent = new_plugin.parent
            plugin_instance.depth = new_plugin.depth
            plugin_instance.path = new_plugin.path
            plugin_instance.numchild = new_plugin.numchild
            plugin_instance._no_reorder = True
            plugin_instance.save()
            old_instance = plugin_instance.__class__.objects.get(pk=self.pk)
            plugin_instance.copy_relations(old_instance)
        if no_signals:

            signals.pre_save.connect(pre_save_plugins, sender=CMSPlugin, dispatch_uid='cms_pre_save_plugin')

        return new_plugin

    @classmethod
    def fix_tree(cls, destructive=False):
        """
        Fixes the plugin tree by first calling treebeard fix_tree and the
        recalculating the correct position property for each plugin.
        """
        from cms.utils.plugins import reorder_plugins

        super(CMSPlugin, cls).fix_tree(destructive)
        for placeholder in Placeholder.objects.all():
            for language, __ in settings.LANGUAGES:
                order = CMSPlugin.objects.filter(
                        placeholder_id=placeholder.pk, language=language,
                        parent_id__isnull=True
                    ).order_by('position', 'path').values_list('pk', flat=True)
                reorder_plugins(placeholder, None, language, order)

                for plugin in CMSPlugin.objects.filter(
                        placeholder_id=placeholder.pk,
                        language=language).order_by('depth', 'path'):
                    order = CMSPlugin.objects.filter(
                            parent_id=plugin.pk
                        ).order_by('position', 'path').values_list('pk', flat=True)
                    reorder_plugins(placeholder, plugin.pk, language, order)

    def post_copy(self, old_instance, new_old_ziplist):
        """
        Handle more advanced cases (eg Text Plugins) after the original is
        copied
        """
        pass

    def copy_relations(self, old_instance):
        """
        Handle copying of any relations attached to this plugin. Custom plugins
        have to do this themselves!
        """
        pass

    @classmethod
    def _get_related_objects(cls):
        fields = cls._meta._get_fields(
            forward=False, reverse=True,
            include_parents=True,
            include_hidden=False,
        )
        return list(obj for obj in fields if not isinstance(obj.field, ManyToManyField))

    def has_change_permission(self, request):
        page = self.placeholder.page if self.placeholder else None
        if page:
            return page.has_change_permission(request)
        elif self.placeholder:
            return self.placeholder.has_change_permission(request)
        return False

    def get_position_in_placeholder(self):
        """
        1 based position!
        """
        return self.position + 1

    def get_breadcrumb(self):
        from cms.models import Page

        model = self.placeholder._get_attached_model() or Page
        breadcrumb = []
        for parent in self.get_ancestors():
            try:
                url = force_text(
                    admin_reverse("%s_%s_edit_plugin" % (model._meta.app_label, model._meta.model_name),
                                  args=[parent.pk]))
            except NoReverseMatch:
                url = force_text(
                    admin_reverse("%s_%s_edit_plugin" % (Page._meta.app_label, Page._meta.model_name),
                                  args=[parent.pk]))
            breadcrumb.append({'title': force_text(parent.get_plugin_name()), 'url': url})
        try:
            url = force_text(
                admin_reverse("%s_%s_edit_plugin" % (model._meta.app_label, model._meta.model_name),
                              args=[self.pk]))
        except NoReverseMatch:
            url = force_text(
                admin_reverse("%s_%s_edit_plugin" % (Page._meta.app_label, Page._meta.model_name),
                              args=[self.pk]))
        breadcrumb.append({'title': force_text(self.get_plugin_name()), 'url': url})
        return breadcrumb

    def get_breadcrumb_json(self):
        result = json.dumps(self.get_breadcrumb())
        result = mark_safe(result)
        return result

    def num_children(self):
        return self.numchild

    def notify_on_autoadd(self, request, conf):
        """
        Method called when we auto add this plugin via default_plugins in
        CMS_PLACEHOLDER_CONF.
        Some specific plugins may have some special stuff to do when they are
        auto added.
        """
        pass

    def notify_on_autoadd_children(self, request, conf, children):
        """
        Method called when we auto add children to this plugin via
        default_plugins/<plugin>/children in CMS_PLACEHOLDER_CONF.
        Some specific plugins may have some special stuff to do when we add
        children to them. ie : TextPlugin must update its content to add HTML
        tags to be able to see his children in WYSIWYG.
        """
        pass

    def get_translatable_content(self):
        """
        Returns {field_name: field_contents} for translatable fields, where
        field_contents > ''
        """
        fields = (f for f in self._meta.fields
                  if isinstance(f, (models.CharField, models.TextField)) and
                     f.editable and not f.choices and
                     f.name not in self.translatable_content_excluded_fields)
        return dict(filter(itemgetter(1),
                           ((f.name, getattr(self, f.name)) for f in fields)))

    def set_translatable_content(self, fields):
        for field, value in fields.items():
            setattr(self, field, value)
        self.save()
        return all(getattr(self, field) == value
                   for field, value in fields.items())

    def delete(self, no_mp=False, *args, **kwargs):
        if no_mp:
            Model.delete(self, *args, **kwargs)
        else:
            super(CMSPlugin, self).delete(*args, **kwargs)

    def get_action_urls(self, js_compat=True):
        if js_compat:
            # TODO: Remove this condition
            # once the javascript files have been refactored
            # to use the new naming schema (ending in _url).
            data = {
                'edit_plugin': self.get_edit_url(),
                'add_plugin': self.get_add_url(),
                'delete_plugin': self.get_delete_url(),
                'move_plugin': self.get_move_url(),
                'copy_plugin': self.get_copy_url(),
            }
        else:
            data = {
                'edit_url': self.get_edit_url(),
                'add_url': self.get_add_url(),
                'delete_url': self.get_delete_url(),
                'move_url': self.get_move_url(),
                'copy_url': self.get_copy_url(),
            }
        return data

    def get_add_url(self):
        if self.add_url:
            warnings.warn(
                'The add_url property is deprecated, '
                'and it will be removed in version 3.4; '
                'please use the get_add_url method instead.',
                DeprecationWarning
            )
            return self.add_url
        return self.placeholder.get_add_url()

    def get_edit_url(self):
        if self.edit_url:
            warnings.warn(
                'The edit_url property is deprecated, '
                'and it will be removed in version 3.4; '
                'please use the get_edit_url method instead.',
                DeprecationWarning
            )
            return self.edit_url
        return self.placeholder.get_edit_url(self.pk)

    def get_delete_url(self):
        if self.delete_url:
            warnings.warn(
                'The delete_url property is deprecated, '
                'and it will be removed in version 3.4; '
                'please use the get_delete_url method instead.',
                DeprecationWarning
            )
            return self.delete_url
        return self.placeholder.get_delete_url(self.pk)

    def get_move_url(self):
        if self.move_url:
            warnings.warn(
                'The move_url property is deprecated, '
                'and it will be removed in version 3.4; '
                'please use the get_move_url method instead.',
                DeprecationWarning
            )
            return self.move_url
        return self.placeholder.get_move_url()

    def get_copy_url(self):
        if self.copy_url:
            warnings.warn(
                'The copy_url property is deprecated, '
                'and it will be removed in version 3.4; '
                'please use the get_copy_url method instead.',
                DeprecationWarning
            )
            return self.copy_url
        return self.placeholder.get_copy_url()

    @property
    def add_url(self):
        """
        Returns a custom url to add plugin instances
        """
        return None

    @property
    def edit_url(self):
        """
        Returns a custom url to edit plugin instances
        """
        return None

    @property
    def move_url(self):
        """
        Returns a custom url to move plugin instances
        """
        return None

    @property
    def delete_url(self):
        """
        Returns a custom url to delete plugin instances
        """
        return None

    @property
    def copy_url(self):
        """
        Returns a custom url to copy plugin instances
        """
        return None

reversion_register(CMSPlugin)


def get_plugin_media_path(instance, filename):
    """
    Django requires that unbound function used in fields' definitions to be
    defined outside the parent class.
     (see https://docs.djangoproject.com/en/dev/topics/migrations/#serializing-values)
    This function is used withing field definition:

        file = models.FileField(_("file"), upload_to=get_plugin_media_path)

    and it invokes the bounded method on the given instance at runtime
    """
    return instance.get_media_path(filename)
