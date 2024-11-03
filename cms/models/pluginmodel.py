import json
import os
import warnings
from datetime import date
from functools import cache

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, connections, models, router
from django.db.models.base import ModelBase
from django.urls import NoReverseMatch
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from cms.exceptions import DontUsePageAttributeWarning
from cms.models.placeholdermodel import Placeholder
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse


@cache
def _get_descendants_cte():
    db_vendor = _get_database_vendor('read')
    if db_vendor == 'oracle':
        sql = (
            "WITH descendants (id, cms_plugin_position, cms_plugin_parent_id) as ("
            "SELECT {0}.id, {0}.position, {0}.parent_id  "
            "FROM {0} WHERE {0}.parent_id = %s "
            "UNION ALL "
            "SELECT {0}.id, {0}.position, {0}.parent_id "
            "FROM descendants, {0} WHERE {0}.parent_id = descendants.id"
            ")"
        )
    else:
        sql = (
            "WITH RECURSIVE descendants as ("
            "SELECT {0}.id, {0}.position, {0}.parent_id  "
            "FROM {0} WHERE {0}.parent_id = %s "
            "UNION ALL "
            "SELECT {0}.id, {0}.position, {0}.parent_id "
            "FROM descendants, {0} WHERE {0}.parent_id = descendants.id"
            ")"
        )
    return sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))


def _get_database_connection(action):
    return {
        'read': connections[router.db_for_read(CMSPlugin)],
        'write': connections[router.db_for_write(CMSPlugin)]
    }[action]


def _get_database_vendor(action):
    return _get_database_connection(action).vendor


def _get_database_cursor(action):
    return _get_database_connection(action).cursor()


@cache
def plugin_supports_cte():
    # This has to be as function because when it's a var it evaluates before
    # db is connected and we get OperationalError. MySQL version is retrieved
    # from db, and it's cached_property.
    connection = _get_database_connection('write')
    db_vendor = _get_database_vendor('write')
    sqlite_no_cte = (
        db_vendor == 'sqlite' and connection.Database.sqlite_version_info < (3, 8, 3)
    )

    if sqlite_no_cte:
        return False
    return not (db_vendor == 'mysql' and connection.mysql_version < (8, 0))


class BoundRenderMeta:
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
        super_new = super().__new__
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
                    on_delete=models.CASCADE,
                )

        # create a new class (using the super-metaclass)
        new_class = super_new(cls, name, bases, attrs)

        # if there is a RenderMeta in attrs, use this one
        # else try to use the one from the superclass (if present)
        meta = attr_meta or getattr(new_class, '_render_meta', None)
        # set a new BoundRenderMeta to prevent leaking of state
        new_class._render_meta = BoundRenderMeta(meta)
        return new_class


class CMSPlugin(models.Model, metaclass=PluginModelBase):
    """
    The base class for a CMS plugin model. When defining a new custom plugin, you should
    store plugin-instance specific information on a subclass of this class. (An example for this
    would be to store the number of pictures to display in a gallery.)

    Two restrictions apply when subclassing this to use in your own models:

    1. Subclasses of CMSPlugin **cannot be further subclassed**
    2. Subclasses of CMSPlugin cannot define a "text" field.
    """

    #: :class:`django:django.db.models.ForeignKey`: Placeholder the plugin belongs to
    placeholder = models.ForeignKey(Placeholder, on_delete=models.CASCADE, editable=False, null=True)
    #: :class:`django:django.db.models.ForeignKey`: Parent plugin or ``None`` for plugins at root level in
    #: the placeholder
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    #: :class:`django:django.db.models.SmallIntegerField`: Position (unique for placeholder and language)
    #: starting with 1 for the first plugin in the placeholder
    position = models.SmallIntegerField(_("position"), default=1, editable=False)
    #: :class:`django:django.db.models.CharField`: Language of the plugin
    language = models.CharField(_("language"), max_length=15, blank=False, db_index=True, editable=False)
    #: `django:django.db.models.CharField`: Plugin type (name of the class as string)
    plugin_type = models.CharField(_("plugin_name"), max_length=50, db_index=True, editable=False)
    #: `django:django.db.models.DateTimeField`: Datetime the plugin was created
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=timezone.now)
    #: `django:django.db.models.DateTimeField`: Datetime the plugin was last changed
    changed_date = models.DateTimeField(auto_now=True)
    child_plugin_instances = None

    class Meta:
        app_label = 'cms'
        ordering = ('position',)
        indexes = [
            models.Index(fields=['placeholder', 'language', 'position']),
        ]
        unique_together = ('placeholder', 'language', 'position')

    class RenderMeta:
        index = 0
        total = 1
        text_enabled = False

    def __str__(self):
        return force_str(self.pk)

    def __repr__(self):
        display = f"<{self.__module__}.{self.__class__.__name__} id={self.pk} plugin_type='{self.plugin_type}' object at {hex(id(self))}>"
        return display

    def get_plugin_name(self):
        from cms.plugin_pool import plugin_pool

        return plugin_pool.get_plugin(self.plugin_type).name

    def get_short_description(self):
        instance = self.get_plugin_instance()[0]
        if instance is not None:
            return force_str(instance)
        return _("<Empty>")

    def get_plugin_class(self):
        from cms.plugin_pool import plugin_pool

        return plugin_pool.get_plugin(self.plugin_type)

    def get_plugin_class_instance(self, admin=None):
        plugin_class = self.get_plugin_class()
        # needed so we have the same signature as the original ModelAdmin
        return plugin_class(plugin_class.model, admin)

    def get_plugin_instance(self, admin=None):
        """
        For a plugin instance (usually as a CMSPluginBase), this method
        returns the downcasted (i.e., correctly typed subclass of CMSPluginBase) instance and the plugin class

        :return: Tuple (instance, plugin)

        instance: The instance AS THE APPROPRIATE SUBCLASS OF CMSPluginBase and not necessarily just 'self', which is
        often just a CMSPluginBase,

        plugin: the associated plugin class instance (subclass of CMSPlugin)
        """
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
            'position': self.position,
            'placeholder_id': str(self.placeholder_id),
            'plugin_name': force_str(plugin_name) or '',
            'plugin_type': self.plugin_type,
            'plugin_id': str(self.pk),
            'plugin_language': self.language or '',
            'plugin_parent': str(self.parent_id or ''),
            'plugin_restriction': children or [],
            'plugin_parent_restriction': parents or [],
            'urls': self.get_action_urls(),
        }
        return data

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)

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
        return plugin.icon_src(instance) if instance else ''

    def get_instance_icon_alt(self):
        """
        Get alt text for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        return force_str(plugin.icon_alt(instance)) if instance else ''

    def update(self, refresh=False, **fields):
        CMSPlugin.objects.filter(pk=self.pk).update(**fields)
        if refresh:
            return self.reload()
        return

    def reload(self):
        return CMSPlugin.objects.get(pk=self.pk)

    def _get_descendants_count(self):
        if plugin_supports_cte():
            cursor = _get_database_cursor('write')
            sql = _get_descendants_cte() + '\n'
            sql += 'SELECT COUNT(*) FROM descendants;'
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk])
            return cursor.fetchall()[0][0]
        return self.get_descendants().count()

    def _get_descendants_ids(self):
        if plugin_supports_cte():
            cursor = _get_database_cursor('write')
            sql = _get_descendants_cte() + '\n'
            sql += 'SELECT id FROM descendants;'
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk])
            descendants = [item[0] for item in cursor.fetchall()]
        else:
            children = self.get_children().values_list('pk', flat=True)
            descendants = list(children)
            while children:
                children = CMSPlugin.objects.filter(
                    parent__in=children,
                ).values_list('pk', flat=True)
                descendants.extend(children)
        return descendants

    def get_children(self):
        return self.cmsplugin_set.all()

    def get_descendants(self):
        return CMSPlugin.objects.filter(pk__in=self._get_descendants_ids())

    def set_base_attr(self, plugin):
        for attr in ['parent_id', 'placeholder', 'language', 'plugin_type', 'creation_date', 'pk', 'position']:
            setattr(plugin, attr, getattr(self, attr))

    def post_copy(self, old_instance, new_old_ziplist):
        """
        Can (should) be overridden to handle the copying of plugins which contain children plugins after the original
        parent has been copied.

        E.g., TextPlugins use this to correct the references in the text to child plugins.
        copied
        """
        pass

    def copy_relations(self, old_instance):
        """
        Handle copying of any relations attached to this plugin. Custom plugins have
        to do this themselves.

        See also: :ref:`Handling-Relations`, :meth:`post_copy`.

        :param old_instance: Source plugin instance
        :type old_instance: :class:`CMSPlugin` instance
        """
        pass

    @classmethod
    def _get_related_objects(cls):
        fields = cls._meta._get_fields(
            forward=False, reverse=True,
            include_parents=True,
            include_hidden=False,
        )
        return list(obj for obj in fields if not isinstance(obj.field, models.ManyToManyField))

    def get_breadcrumb(self):
        from cms.models import Page

        model = self.placeholder._get_attached_model() or Page
        breadcrumb = []
        for parent in self.get_ancestors():
            try:
                url = force_str(
                    admin_reverse("%s_%s_edit_plugin" % (model._meta.app_label, model._meta.model_name),
                                  args=[parent.pk]))
            except NoReverseMatch:
                url = force_str(
                    admin_reverse("%s_%s_edit_plugin" % (Page._meta.app_label, Page._meta.model_name),
                                  args=[parent.pk]))
            breadcrumb.append({'title': force_str(parent.get_plugin_name()), 'url': url})
        try:
            url = force_str(
                admin_reverse("%s_%s_edit_plugin" % (model._meta.app_label, model._meta.model_name),
                              args=[self.pk]))
        except NoReverseMatch:
            url = force_str(
                admin_reverse("%s_%s_edit_plugin" % (Page._meta.app_label, Page._meta.model_name),
                              args=[self.pk]))
        breadcrumb.append({'title': force_str(self.get_plugin_name()), 'url': url})
        return breadcrumb

    def get_breadcrumb_json(self):
        result = json.dumps(self.get_breadcrumb())
        result = mark_safe(result)
        return result

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

    def get_action_urls(self, js_compat=True):
        """
        .. versionadd: 4.0

        :return: dict of action urls for edit, add, delete, copy, and move plugin.

        This method replaces the set of legacy methods `get_add_url`, ``get_edit_url`, `get_move_url`,
        `get_delete_url`, `get_copy_url`.
        """
        if js_compat:
            # TODO: Remove this condition
            # once the javascript files have been refactored
            # to use the new naming schema (ending in _url).
            data = {
                'edit_plugin': admin_reverse('cms_placeholder_edit_plugin', args=(self.pk,)),
                'add_plugin': admin_reverse('cms_placeholder_add_plugin'),
                'delete_plugin': admin_reverse('cms_placeholder_delete_plugin', args=(self.pk,)),
                'move_plugin': admin_reverse('cms_placeholder_move_plugin'),
                'copy_plugin': admin_reverse('cms_placeholder_copy_plugins'),
            }
        else:
            data = {
                'edit_url': admin_reverse('cms_placeholder_edit_plugin', args=(self.pk,)),
                'add_url': admin_reverse('cms_placeholder_add_plugin'),
                'delete_url': admin_reverse('cms_placeholder_delete_plugin', args=(self.pk,)),
                'move_url': admin_reverse('cms_placeholder_move_plugin'),
                'copy_url': admin_reverse('cms_placeholder_copy_plugins'),
            }
        return data


def get_plugin_media_path(instance, filename):
    """
    Django requires that unbound function used in fields' definitions to be
    defined outside the parent class.
     (see https://docs.djangoproject.com/en/dev/topics/migrations/#serializing-values)
    This function is used within field definition:

        file = models.FileField(_("file"), upload_to=get_plugin_media_path)

    and it invokes the bounded method on the given instance at runtime
    """
    return instance.get_media_path(filename)
