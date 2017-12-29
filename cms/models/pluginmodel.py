# -*- coding: utf-8 -*-
from datetime import date
import json
from operator import itemgetter
import os
import warnings

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import signals, Model, ManyToManyField
from django.db.models.base import ModelBase
try:
    # Django >= 1.8, < 1.9
    from django.db.models.fields.related import (
        ReverseSingleRelatedObjectDescriptor as ForwardManyToOneDescriptor
    )
except ImportError:
    # Django >= 1.9
    from django.db.models.fields.related import ForwardManyToOneDescriptor
from django.utils import six, timezone
from django.utils.six import text_type
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.six.moves import filter
from django.utils.translation import ugettext_lazy as _

from cms.exceptions import DontUsePageAttributeWarning
from cms.models.placeholdermodel import Placeholder
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse

from treebeard.mp_tree import MP_Node


class BoundRenderMeta(object):
    def __init__(self, meta):
        self.index = 0
        self.total = 1
        self.text_enabled = getattr(meta, 'text_enabled', False)


class ForwardOneToOneDescriptor(ForwardManyToOneDescriptor):
    """
    Accessor to the related object on the forward side
    of a one-to-one relation.

    In the example::

        class MyPlugin(CMSPlugin):
            cmsplugin_ptr = ForeignKey(CMSPlugin, parent_link=True)

    ``myplugin.cmsplugin_ptr`` is a ``ForwardOneToOneDescriptor`` instance.
    """

    # This class is necessary to backport the following Django fix
    # https://github.com/django/django/commit/38575b007a722d6af510ea46d46393a4cda9ca29
    # into the CMS.

    def get_inherited_object(self, instance):
        """
        Returns an instance of the subclassed model
        in a multi-table inheritance scenario.
        """
        # This is an exact copy of the code for get_object()
        # provided in the commit above.
        deferred = instance.get_deferred_fields()
        # Because it's a parent link, all the data is available in the
        # instance, so populate the parent model with this data.
        rel_model = self.field.rel.model
        fields = [field.attname for field in rel_model._meta.concrete_fields]

        # If any of the related model's fields are deferred, fallback to
        # fetching all fields from the related model. This avoids a query
        # on the related model for every deferred field.
        if not any(field in fields for field in deferred):
            kwargs = {field: getattr(instance, field) for field in fields}
            return rel_model(**kwargs)
        return

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        if not hasattr(instance, self.cache_name):
            # No cached object is present on the instance.
            val = self.field.get_local_related_value(instance)

            if None not in val:
                # Fetch the inherited object instance
                # using values from the current instance.
                # This avoids an extra db call because we already
                # have the data.
                # This can be None if a field from the base class (CMSPlugin)
                # was deferred.
                rel_obj = self.get_inherited_object(instance)

                if not rel_obj is None:
                    # Populate the internal relationship cache.
                    setattr(instance, self.cache_name, rel_obj)
        return super(ForwardOneToOneDescriptor, self).__get__(instance, instance_type)


class PluginModelBase(ModelBase):
    """
    Metaclass for all CMSPlugin subclasses. This class should not be used for
    any other type of models.
    """

    def __new__(cls, name, bases, attrs):
        super_new = super(PluginModelBase, cls).__new__
        # remove RenderMeta from the plugin class
        attr_meta = attrs.pop('RenderMeta', None)

        # Only care about subclasses of CMSPlugin
        # (excluding CMSPlugin itself).
        parents = [b for b in bases if isinstance(b, PluginModelBase)]

        if parents and 'cmsplugin_ptr' not in attrs:
            # The current class subclasses from CMSPlugin
            # and has not defined a cmsplugin_ptr field.
            meta = attrs.get('Meta', None)
            proxy = getattr(meta, 'proxy', False)

            # True if any of the base classes defines a cmsplugin_ptr field.
            field_is_inherited = any(hasattr(parent, 'cmsplugin_ptr') for parent in parents)

            # Skip proxied classes which are not autonomous ORM objects
            # We don't skip abstract classes because when a plugin
            # inherits from an abstract class, we need to make sure the
            # abstract class gets the correct related name, otherwise the
            # plugin inherits the default related name and then the
            # field_is_inherited check above will prevent us from adding
            # the fixed related name.
            if not proxy and not field_is_inherited:
                # It's important to set the field as if it was set
                # manually in the model class.
                # This is because Django will do a lot of operations
                # under the hood to set the forward and reverse relations.
                attrs['cmsplugin_ptr'] = models.OneToOneField(
                    to='cms.CMSPlugin',
                    name='cmsplugin_ptr',
                    related_name='%(app_label)s_%(class)s',
                    auto_created=True,
                    parent_link=True,
                )

        # create a new class (using the super-metaclass)
        new_class = super_new(cls, name, bases, attrs)

        # Skip abstract and proxied classes which are not autonomous ORM objects
        if parents and not new_class._meta.abstract and not new_class._meta.proxy:
            # Use our patched descriptor regardless of how the one to one
            # relationship was defined.
            parent_link_field = new_class._meta.get_field('cmsplugin_ptr')
            setattr(new_class, 'cmsplugin_ptr', ForwardOneToOneDescriptor(parent_link_field))

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
    placeholder = models.ForeignKey(Placeholder, on_delete=models.CASCADE, editable=False, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, editable=False)
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

    def __str__(self):
        return force_text(self.pk)

    def __repr__(self):
        display = "<{module}.{class_name} id={id} plugin_type='{plugin_type}' object at {location}>".format(
            module=self.__module__,
            class_name=self.__class__.__name__,
            id=self.pk,
            plugin_type=(self.plugin_type),
            location=hex(id(self)),
        )
        return display

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

        try:
            instance = self.get_bound_plugin()
        except ObjectDoesNotExist:
            instance = None
            self._inst = None
        return (instance, plugin)

    def get_bound_plugin(self):
        """
        Returns an instance of the plugin model
        configured for this plugin type.
        """
        if hasattr(self, "_inst"):
            return self._inst

        plugin = self.get_plugin_class()

        if plugin.model != self.__class__:
            self._inst = plugin.model.objects.get(cmsplugin_ptr=self)
            self._inst._render_meta = self._render_meta
        else:
            self._inst = self
        return self._inst

    def get_plugin_info(self, children=None, parents=None):
        plugin_name = self.get_plugin_name()
        data = {
            'type': 'plugin',
            'placeholder_id': text_type(self.placeholder_id),
            'plugin_name': force_text(plugin_name) or '',
            'plugin_type': self.plugin_type,
            'plugin_id': text_type(self.pk),
            'plugin_language': self.language or '',
            'plugin_parent': text_type(self.parent_id or ''),
            'plugin_restriction': children or [],
            'plugin_parent_restriction': parents or [],
            'urls': self.get_action_urls(),
        }
        return data

    def refresh_from_db(self, *args, **kwargs):
        super(CMSPlugin, self).refresh_from_db(*args, **kwargs)

        # Delete this internal cache to let the cms populate it
        # on demand.
        try:
            del self._inst
        except AttributeError:
            pass

    def get_media_path(self, filename):
        pages = self.placeholder.page_set.all()
        if pages.exists():
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
            DontUsePageAttributeWarning,
            stacklevel=2,
        )
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
        return self.placeholder.get_add_url()

    def get_edit_url(self):
        return self.placeholder.get_edit_url(self.pk)

    def get_delete_url(self):
        return self.placeholder.get_delete_url(self.pk)

    def get_move_url(self):
        return self.placeholder.get_move_url()

    def get_copy_url(self):
        return self.placeholder.get_copy_url()


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
