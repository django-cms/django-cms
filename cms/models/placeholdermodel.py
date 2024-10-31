import warnings
from datetime import datetime, timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.template.defaultfilters import title
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from cms.cache import invalidate_cms_page_cache
from cms.cache.placeholder import clear_placeholder_cache
from cms.constants import EXPIRE_NOW, MAX_EXPIRATION_TTL
from cms.exceptions import LanguageError
from cms.models.managers import PlaceholderManager
from cms.utils import get_language_from_request, permissions
from cms.utils.conf import get_cms_setting, get_site_id
from cms.utils.i18n import get_language_object


class Placeholder(models.Model):
    """

    ``Placeholders`` can be filled with plugins, which store or generate content.

    """
    #: slot name that appears in the frontend
    slot = models.CharField(_("slot"), max_length=255, db_index=True, editable=False)
    #: A default width is passed to the templace context as ``width``
    default_width = models.PositiveSmallIntegerField(_("width"), null=True, editable=False)
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    source = GenericForeignKey('content_type', 'object_id')
    cache_placeholder = True  #: Flag caching the palceholder's content
    is_static = False  #: Set to "True" for static placeholders (by the template tag)
    is_editable = True  #: If False the content of the placeholder is not editable in the frontend

    objects = PlaceholderManager()

    class Meta:
        app_label = 'cms'
        default_permissions = []
        permissions = (
            ("use_structure", "Can use Structure mode"),
        )

    def __str__(self):
        return self.slot

    def __repr__(self):
        display = f"<{self.__module__}.{self.__class__.__name__} id={self.pk} slot='{self.slot}' object at {hex(id(self))}>"
        return display

    def clear(self, language=None):
        """Deletes all plugins from the placeholder"""
        self.get_plugins(language).delete()

    def get_label(self):
        from cms.utils.placeholder import get_placeholder_conf

        template = self.page.get_template() if self.page else None
        name = get_placeholder_conf("name", self.slot, template=template, default=title(self.slot))
        name = _(name)
        return name

    def get_extra_context(self, template=None):
        from cms.utils.placeholder import get_placeholder_conf
        return get_placeholder_conf("extra_context", self.slot, template, {})

    def get_extra_menu_items(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_extra_placeholder_menu_items(self)

    def has_change_permission(self, user):
        """
        Returns ``True`` if user has permission to change all models attached to this placeholder.
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
        """
        Returns ``True`` if user has permission to add ``plugin_type`` to this placeholder.
        """
        if not permissions.has_plugin_permission(user, plugin_type, "add"):
            return False

        if not self.has_change_permission(user):
            return False
        return True

    def has_add_plugins_permission(self, user, plugins):
        """
        Returns ``True`` if user has permission to add **all** plugins in ``plugins`` to this placeholder.
        """
        if not self.has_change_permission(user):
            return False

        for plugin in plugins:
            if not permissions.has_plugin_permission(user, plugin.plugin_type, "add"):
                return False
        return True

    def has_change_plugin_permission(self, user, plugin):
        """
        Returns ``True`` if user has permission to change ``plugin`` to this placeholder.
        """
        if not permissions.has_plugin_permission(user, plugin.plugin_type, "change"):
            return False

        if not self.has_change_permission(user):
            return False
        return True

    def has_delete_plugin_permission(self, user, plugin):
        """
        Returns ``True`` if user has permission to delete ``plugin`` to this placeholder.
        """
        if not permissions.has_plugin_permission(user, plugin.plugin_type, "delete"):
            return False

        if not self.has_change_permission(user):
            return False
        return True

    def has_move_plugin_permission(self, user, plugin, target_placeholder):
        """
        Returns ``True`` if user has permission to move ``plugin`` to the ``target_placeholder``.
        """
        if not permissions.has_plugin_permission(user, plugin.plugin_type, "change"):
            return False

        if not target_placeholder.has_change_permission(user):
            return False

        if self != target_placeholder and not self.has_change_permission(user):
            return False
        return True

    def has_clear_permission(self, user, languages):
        """
        Returns ``True`` if user has permission to delete all plugins in this placeholder
        """
        if not self.has_change_permission(user):
            return False
        return self.has_delete_plugins_permission(user, languages)

    def has_delete_plugins_permission(self, user, languages):
        """
        Returns ``True`` if user has permission to delete all plugins in this placeholder
        """
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

    def _get_source_remote_field(self):
        if self.source is None:
            return
        return next(
            f for f in self.source._meta.get_fields()
            if f.related_model == Placeholder
        )

    def check_source(self, user):
        remote_field = self._get_source_remote_field()
        if remote_field is None:
            return True
        return remote_field.run_checks(self, user)

    def _get_related_objects(self):
        fields = self._meta._get_fields(
            forward=False, reverse=True,
            include_parents=True,
            include_hidden=False,
        )
        return list(obj for obj in fields)

    def _get_attached_fields(self):
        """
        Returns a list of all non-cmsplugin reverse related fields.
        """
        from cms.models import CMSPlugin

        if not hasattr(self, '_attached_fields_cache'):
            self._attached_fields_cache = []
            relations = self._get_related_objects()
            for rel in relations:
                if issubclass(rel.field.model, CMSPlugin):
                    continue

                field = getattr(self, rel.get_accessor_name())

                try:
                    if field.exists():
                        self._attached_fields_cache.append(rel.field)
                except:  # NOQA
                    pass
        return self._attached_fields_cache

    def _get_attached_field(self):
        try:
            return self._get_attached_fields()[0]
        except IndexError:
            return None

    def _get_attached_model(self):
        if self.source:
            return self.source._meta.model
        return None

    def _get_attached_models(self):
        """
        Returns a list of models of attached to this placeholder.
        """
        if hasattr(self, '_attached_models_cache'):
            return self._attached_models_cache

        self._attached_models_cache = [field.model for field in self._get_attached_fields()]

        if self.source:
            self._attached_models_cache += [self.source._meta.model]
        return self._attached_models_cache

    def _get_attached_objects(self):
        """
        Returns a list of objects attached to this placeholder.
        """
        objs = [obj for field in self._get_attached_fields()
                for obj in getattr(self, field.remote_field.get_accessor_name()).all()]

        if not objs and self.source:
            return [self.source]
        return objs

    def page_getter(self):
        if not hasattr(self, '_page'):
            from cms.models.pagemodel import Page
            try:
                self._page = Page.objects.distinct().get(pagecontent_set__placeholders=self)
            except (Page.DoesNotExist, Page.MultipleObjectsReturned):
                self._page = None
        return self._page

    def page_setter(self, value):
        self._page = value

    #: Gives the page object if the placeholder belongs to a :class:`cms.models.titlemodels.PageContent` object
    #: (and not to some other model.) If the placeholder is not attached to a page it returns ``None``
    page = property(page_getter, page_setter)

    def get_plugins_list(self, language=None):
        """Returns a list of plugins attached to this placeholder. If language is given only plugins
        in the given language are returned."""
        return list(self.get_plugins(language))

    def get_plugins(self, language=None):
        """Returns a queryset of plugins attached to this placeholder. If language is given only plugins
        in the given language are returned."""
        if language:
            return self.cmsplugin_set.filter(language=language)
        return self.cmsplugin_set.all()

    def has_plugins(self, language=None):
        """Checks if placeholder is empty (``False``) or populated (``True``)"""
        return self.get_plugins(language).exists()

    def get_filled_languages(self):
        """
        Returns language objects for every language for which the placeholder
        has plugins.

        This is not cached as it's meant to be used in the frontend editor.
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

        This method must return: ``EXPIRE_NOW <= int <= MAX_EXPIRATION_IN_SECONDS``

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
                                'value': force_str(plugin_expiration),
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
                            'value': force_str(plugin_expiration),
                        })
                    continue

            min_ttl = min(ttl, min_ttl)
            if min_ttl <= 0:
                # No point in continuing, we've already hit the minimum
                # possible expiration TTL
                return EXPIRE_NOW

        return min_ttl

    def clear_cache(self, language, site_id=None):
        if get_cms_setting('PAGE_CACHE'):
            # Clears all the page caches
            invalidate_cms_page_cache()

        if not site_id and self.page:
            site_id = self.page.node.site_id
        clear_placeholder_cache(self, language, get_site_id(site_id))

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
            if isinstance(vary_on, str):
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
                            'value': force_str(vary_on),
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

    def add_plugin(self, instance):
        """
        .. versionadded:: 4.0

        Adds a plugin to the placeholder. The plugin's position field must be set to the target
        position. Positions are enumerated from the start of the palceholder's plugin tree (1) to
        the last plugin (*n*, where *n* is the number of plugins in the placeholder).

        :param instance: Plugin to add. It's position parameter needs to be set.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance

        .. note::
            As of version 4 of django CMS the position counter does not re-start at 1 for the first
            child plugin. The ``position`` field  and ``language`` field are unique for a placeholder.

        Example::

            new_child = MyCoolPlugin()
            new_child.position = parent_plugin.position + 1  # add as first child: directly after parent
            parent_plugin.placeholder.add(new_child)

        """
        last_position = self.get_last_plugin_position(instance.language) or 0
        # A shift is only needed if the distance between the new plugin
        # and the last plugin is greater than 1 position.
        needs_shift = (instance.position - last_position) < 1

        if needs_shift:
            # shift to the right
            self._shift_plugin_positions(
                instance.language,
                start=instance.position,
                offset=last_position - instance.position + 2,  # behind last_position plus one to shift back
            )

        instance.save()

        if needs_shift:
            # The plugin tree was shifted to the right to make space,
            # now squash all plugins in the tree to close any holes.
            self._recalculate_plugin_positions(instance.language)
        return instance

    def move_plugin(self, plugin, target_position, target_placeholder=None, target_plugin=None):
        """
        .. versionadded:: 4.0

        Moves a plugin within the placeholder (``target_placeholder=None``) or to another placeholder.

        :param plugin: Plugin to move
        :type plugin: :class:`cms.models.pluginmodel.CMSPlugin` instance
        :param int target_position: The plugin's new position
        :param  target_placeholder: Placeholder to move plugin to (or ``None``)
        :type target_placeholder: :class:`cms.models.placeholdermodel.Placeholder` instance
        :param target_plugin: New parent plugin (or ``None``). The target plugin must be in the same placeholder
           or in the ``target_placeholder`` if one is given.
        :type target_plugin: :class:`cms.models.pluginmodel.CMSPlugin` instance

        The ``target_position`` is enumerated from the start of the palceholder's plugin tree (1) to
        the last plugin (*n*, where *n* is the number of plugins in the placeholder).
        """

        if target_placeholder:
            return self._move_plugin_to_placeholder(
                plugin=plugin,
                target_position=target_position,
                target_placeholder=target_placeholder,
                target_plugin=target_plugin,
            )

        target_tree = self.get_plugins(plugin.language)
        last_plugin = self.get_last_plugin(plugin.language)
        source_plugin_desc_count = plugin._get_descendants_count()
        # Attn: The following line assumes that all children and grand-children have consecutive positions!
        source_plugin_range = (plugin.position, plugin.position + source_plugin_desc_count)

        if target_position < plugin.position:
            # Moving left
            # Make a big hole on the right side of the current plugin's position
            # by shifting all right nodes further to the right, excluding the current plugin
            # but including the target plugin and its descendants.
            (target_tree
             .filter(position__gte=target_position)
             .exclude(position__range=source_plugin_range)
             ).update(position=(models.F('position') + last_plugin.position))

            # Make a big hole on the left side of the current plugin's position
            # by shifting all right nodes further the right, including the current plugin
            # and its descendants.
            target_tree.filter(
                position__lte=source_plugin_range[1]
            ).update(position=models.F('position') - last_plugin.position)
        else:
            # Moving right
            # Make a big hole on the left side of the target position,
            # by shifting all left nodes further to the left, excluding the current plugin
            # but including the target plugin and its descendants.
            # Left node in the common case is target_position but if the current plugin
            # has descendants then left node is the closest node to the right side of the
            # last descendant.
            (target_tree
             .filter(position__lte=target_position + source_plugin_desc_count)
             .exclude(position__range=source_plugin_range)
             ).update(position=(models.F('position') - last_plugin.position))

            # Make a big hole on the right side of the current plugin's position
            # by shifting all right nodes further the right, including the current plugin
            # and its descendants.
            target_tree.filter(
                position__gte=plugin.position
            ).update(position=models.F('position') + last_plugin.position)

        if plugin.parent != target_plugin:
            # Plugin is being moved to another tree (under another parent)
            # OR plugin is being moved to the root (no parent)
            plugin.update(parent=target_plugin)
        # The plugin tree was shifted to the right to make space,
        # Squash all plugin positions in the tree to close any holes.
        self._recalculate_plugin_positions(plugin.language)

    def _move_plugin_to_placeholder(self, plugin, target_position, target_placeholder, target_plugin=None):
        source_last_plugin = self.get_last_plugin(plugin.language)
        target_last_plugin = target_placeholder.get_last_plugin(plugin.language)

        plugin_descendants = plugin.get_descendants()
        if target_last_plugin:
            source_length = source_last_plugin.position
            target_length = target_last_plugin.position
            plugins_to_move_count = 1 + len(plugin_descendants)  # parent plus descendants

            source_offset = max(
                # far enough to shift behind current last source position
                source_length,
                # far enough to be shifted behind last target position plus no. of moved plugins
                target_length + plugins_to_move_count
            ) - plugin.position + 1

            # move target position counter to at least behind
            target_offset = max(
                # far enough to shift behind current last target position
                target_length - target_position + 1,
                # far enough to leave enough space to move back
                plugin.position + source_offset - target_position + plugins_to_move_count
            )
            target_placeholder._shift_plugin_positions(
                plugin.language,
                start=target_position,
                offset=target_offset,
            )
        else:
            # moving to empty placeholder:
            # Move out (remaining) plugins right behind last source position to be able to recalculate
            source_offset = source_last_plugin.position

        # Shift all plugins whose position is greater than or equal to
        # the plugin being moved. This includes the plugin itself.
        # This is to create enough space in-between for the squashing
        # to work without conflicts.
        self._shift_plugin_positions(
            plugin.language,
            start=plugin.position,
            offset=source_offset,
        )

        plugin.update(parent=target_plugin, placeholder=target_placeholder)
        # TODO: More efficient is to do raw sql update
        plugin_descendants.update(placeholder=target_placeholder)
        self._recalculate_plugin_positions(plugin.language)
        target_placeholder._recalculate_plugin_positions(plugin.language)

    def delete_plugin(self, instance):
        """
        .. versionadded:: 4.0

        Removes a plugin and its descendants from the placeholder and database.

        :param instance: Plugin to add. It's position parameter needs to be set.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance
        """
        instance.get_descendants().delete()
        instance.delete()
        last_plugin = self.get_last_plugin(instance.language)

        if last_plugin:
            self._shift_plugin_positions(
                instance.language,
                start=instance.position,
                offset=last_plugin.position,
            )
            self._recalculate_plugin_positions(instance.language)

    def get_last_plugin(self, language):
        return self.get_plugins(language).last()

    def get_next_plugin_position(self, language, parent=None, insert_order='first'):
        """
        .. versionadded:: 4.0

        Helper to calculate plugin positions correctly.

        :param str language: language for which the position is to be calculated
        :param parent: Parent plugin or ``None`` (if position is on top level)
        :type parent: :class:`cms.models.pluginmodel.CMSPlugin` instance
        :param str insert_order: Either ``"first"`` (default) or ``"last"``
        """
        if insert_order == 'first':
            position = self.get_first_plugin_position(language, parent=parent)
        else:
            position = self.get_last_plugin_position(language, parent=parent)

        if parent and position is None:
            return parent.position + 1

        if insert_order == 'last':
            return (position or 0) + 1
        return position or 1

    def get_first_plugin_position(self, language, parent=None):
        tree = self.get_plugins(language)

        if parent:
            tree = tree.filter(parent=parent)
        return tree.values_list('position', flat=True).first()

    def get_last_plugin_position(self, language, parent=None):
        if parent is None:
            tree = self.get_plugins(language)
        elif parent.placeholder == self:
            tree = parent.get_descendants()
        else:  # No last plugin if parent is not in this placeholder's plugin tree
            return None
        return tree.values_list('position', flat=True).last()

    def _shift_plugin_positions(self, language, start, offset=None):
        if offset is None:
            offset = self.get_last_plugin_position(language) or 0

        self.get_plugins(language).filter(
            position__gte=start
        ).update(position=models.F('position') + offset)

    def _recalculate_plugin_positions(self, language):
        from cms.models.pluginmodel import (
            CMSPlugin,
            _get_database_cursor,
            _get_database_vendor,
        )

        cursor = _get_database_cursor('write')
        db_vendor = _get_database_vendor('write')

        if db_vendor == 'sqlite':
            sql = (
                'CREATE TEMPORARY TABLE temp AS '
                'SELECT ID, ('
                'SELECT COUNT(*)+1 FROM {0} t WHERE '
                'placeholder_id={0}.placeholder_id AND language={0}.language '
                'AND {0}.position > t.position'
                ') AS new_position '
                'FROM {0} WHERE placeholder_id=%s AND language=%s'
            )
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk, language])

            sql = (
                'UPDATE {0} '
                'SET position = (SELECT new_position FROM temp WHERE id={0}.id) '
                'WHERE placeholder_id=%s AND language=%s'
            )
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk, language])

            sql = 'DROP TABLE temp'
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql)
        elif db_vendor == 'postgresql':
            sql = (
                'UPDATE {0} '
                'SET position = RowNbrs.RowNbr '
                'FROM ('
                'SELECT  ID, ROW_NUMBER() OVER (ORDER BY position) AS RowNbr '
                'FROM {0} WHERE placeholder_id=%s AND language=%s '
                ') RowNbrs '
                'WHERE {0}.id=RowNbrs.id'
            )
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk, language])
        elif db_vendor == 'mysql':
            sql = (
                'UPDATE {0} '
                'SET position = ('
                'SELECT COUNT(*)+1 FROM (SELECT * FROM {0}) t '
                'WHERE placeholder_id={0}.placeholder_id AND language={0}.language '
                'AND {0}.position > t.position'
                ') WHERE placeholder_id=%s AND language=%s'
            )
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk, language])
        elif db_vendor == 'oracle':
            sql = (
                'UPDATE {0} '
                'SET position = ('
                'SELECT COUNT(*)+1 FROM (SELECT * FROM {0}) t '
                'WHERE placeholder_id={0}.placeholder_id AND language={0}.language '
                'AND {0}.position > t.position'
                ') WHERE placeholder_id=%s AND language=%s'
            )
            sql = sql.format(connection.ops.quote_name(CMSPlugin._meta.db_table))
            cursor.execute(sql, [self.pk, language])
        else:
            raise RuntimeError(
                f'{connection.vendor} is not supported by django-cms'
            )
