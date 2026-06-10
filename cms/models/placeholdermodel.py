import warnings
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models, transaction
from django.template.defaultfilters import title
from django.utils.encoding import force_str
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _

from cms.cache import invalidate_cms_page_cache
from cms.cache.placeholder import clear_placeholder_cache
from cms.constants import EXPIRE_NOW, MAX_EXPIRATION_TTL
from cms.exceptions import LanguageError
from cms.models.managers import PlaceholderManager
from cms.utils import get_language_from_request, permissions
from cms.utils.conf import get_cms_setting, get_site_id
from cms.utils.i18n import get_language_object

if TYPE_CHECKING:
    from cms.models.pluginmodel import CMSPlugin


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
    source = GenericForeignKey("content_type", "object_id")
    cache_placeholder = True  #: Flag caching the palceholder's content
    is_static = False  #: Set to "True" for static placeholders (by the template tag)
    edit_message = _("Edit object")  #: Message used in the frontend editing UI for static placeholder edit link
    static_message = _("This is an external placeholder")  #: Message used in the frontend editing UI for static placeholder tooltip
    is_editable = True  #: If False the content of the placeholder is not editable in the frontend

    objects = PlaceholderManager()

    class Meta:
        app_label = "cms"
        default_permissions = []
        permissions = (("use_structure", "Can use Structure mode"),)

    def __str__(self):
        return self.slot

    def __repr__(self):
        display = (
            f"<{self.__module__}.{self.__class__.__name__} id={self.pk} slot='{self.slot}' object at {hex(id(self))}>"
        )
        return display

    def clear(self, language=None):
        """Deletes all plugins from the placeholder"""
        self.get_plugins(language).delete()

    def get_label(self):
        from cms.models import PageContent
        from cms.utils.placeholder import get_placeholder_conf

        template = None
        if isinstance(self.source, PageContent):
            # Make the database access lazy, so that it only happens if needed.
            template = lazy(self.source.get_template, str)()
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

        if not self.object_id:
            # technically if placeholder is not attached to anything,
            # user should not be able to change it but if is superuser
            # then we "should" allow it.
            return user.is_superuser

        try:
            return self.source.has_placeholder_change_permission(user)
        except AttributeError:
            model = type(self.source)
            change_perm = get_model_permission_codename(model, "change")
            return user.has_perm(change_perm) or user.has_perm(change_perm, self.source)

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
            self.cmsplugin_set.filter(language__in=languages)
            # exclude the clipboard plugin
            .exclude(plugin_type="PlaceholderPlugin")
            .values_list("plugin_type", flat=True)
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
        if self.object_id is None:
            return
        return next(f for f in self.source._meta.get_fields() if f.related_model == Placeholder)

    def check_source(self, user):
        remote_field = self._get_source_remote_field()
        if remote_field is None:
            return True
        return remote_field.run_checks(self, user)

    def _get_attached_model(self):
        if self.source:
            return self.source._meta.model
        return None

    def page_getter(self):
        if not hasattr(self, "_page"):
            from cms.models.contentmodels import PageContent
            # Check if the GenericForeignKey is cached by looking for the _source_cache attribute
            if "source" in self._state.fields_cache and isinstance(self.source, PageContent):
                self._page = self.source.page
            else:
                try:
                    # Directly go through PageContent to avoid having to get the source and the page in separate queries
                    self._page = PageContent.admin_manager.filter(placeholders=self).select_related("page").first().page
                except AttributeError:
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

    def get_filled_languages(self, site_id=None):
        """
        Returns language objects for every language for which the placeholder
        has plugins.

        This is not cached as it's meant to be used in the frontend editor.
        """

        if site_id is None:
            site_id = get_site_id(self.page.site_id if self.page else None)

        languages = []
        for lang_code in set(self.get_plugins().values_list("language", flat=True)):
            try:
                languages.append(get_language_object(lang_code, site_id=site_id))
            except LanguageError:
                pass
        return languages

    def get_cached_plugins(self):
        return getattr(self, "_plugins_cache", [])

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

        if not self.cache_placeholder or not get_cms_setting("PLUGIN_CACHE"):
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
            if hasattr(self, "_all_plugins_cache"):
                for instance in self._all_plugins_cache:
                    plugin = instance.get_plugin_class_instance()
                    yield instance, plugin
            else:
                for plugin_item in self.get_plugins(lang):
                    yield plugin_item.get_plugin_instance()

        language = get_language_from_request(request, self.page)
        for instance, plugin in inner_plugin_iterator(language):
            plugin_expiration = plugin.get_cache_expiration(request, instance, self)

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
                            "Plugin %(plugin_class)s (%(pk)d) returned a naive "
                            "datetime : %(value)s for get_cache_expiration(), "
                            "ignoring."
                            % {
                                "plugin_class": plugin.__class__.__name__,
                                "pk": instance.pk,
                                "value": force_str(plugin_expiration),
                            }
                        )
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
                        "Plugin %(plugin_class)s (%(pk)d) returned "
                        "unexpected value %(value)s for "
                        "get_cache_expiration(), ignoring."
                        % {
                            "plugin_class": plugin.__class__.__name__,
                            "pk": instance.pk,
                            "value": force_str(plugin_expiration),
                        }
                    )
                    continue

            min_ttl = min(ttl, min_ttl)
            if min_ttl <= 0:
                # No point in continuing, we've already hit the minimum
                # possible expiration TTL
                return EXPIRE_NOW

        return min_ttl

    def clear_cache(self, language, site_id=None):
        if get_cms_setting("PAGE_CACHE"):
            # Clears all the page caches
            invalidate_cms_page_cache()

        if not site_id and self.page:
            site_id = self.page.site_id
        clear_placeholder_cache(self, language, get_site_id(site_id))

    def get_plugin_tree_order(self, language, parent_id=None):
        """
        Returns a list of plugin ids matching the given language
        ordered by plugin position.
        """
        plugin_tree_order = (
            self.get_plugins(language).filter(parent=parent_id).order_by("position").values_list("pk", flat=True)
        )
        return list(plugin_tree_order)

    def get_vary_cache_on(self, request):
        """
        Returns a list of VARY headers.
        """

        def inner_plugin_iterator(lang):
            """See note in get_cache_expiration.inner_plugin_iterator()."""
            if hasattr(self, "_all_plugins_cache"):
                for instance in self._all_plugins_cache:
                    plugin = instance.get_plugin_class_instance()
                    yield instance, plugin
            else:
                for plugin_item in self.get_plugins(lang):
                    yield plugin_item.get_plugin_instance()

        if not self.cache_placeholder or not get_cms_setting("PLUGIN_CACHE"):
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
                        "Plugin %(plugin_class)s (%(pk)d) returned "
                        "unexpected value %(value)s for "
                        "get_vary_cache_on(), ignoring."
                        % {
                            "plugin_class": plugin.__class__.__name__,
                            "pk": instance.pk,
                            "value": force_str(vary_on),
                        }
                    )

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

    def add_plugin(self, instance: "CMSPlugin"):
        """
        .. versionadded:: 4.0

        Adds a plugin to the placeholder. The plugin's position field must be set to the target
        position. Positions are enumerated from the start of the placeholder's plugin tree (1) to
        the last plugin (*n*, where *n* is the number of plugins in the placeholder).

        It is discouraged to call this method directly from outside the CMS. Use the
        :func:`cms.api.add_plugin` function instead.

        :param instance: Plugin to add. It's position parameter needs to be set.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance

        .. note::
            As of version 4 of django CMS the position counter does not re-start at 1 for the first
            child plugin. The ``position`` field  and ``language`` field are unique for a placeholder.

        Example::

            new_child = MyCoolPlugin()
            new_child.position = (
                parent_plugin.position + 1
            )  # add as first child: directly after parent
            parent_plugin.placeholder.add(new_child)

        """

        # A plugin needs a reference to the placeholder it is in.
        instance.placeholder = self

        last_position = self.get_last_plugin_position(instance.language) or 0
        # A shift is only needed if the distance between the new plugin
        # and the last plugin is greater than 1 position.
        needs_shift = (instance.position - last_position) < 1

        if needs_shift:
            # shift to the right
            shift_offset = last_position - instance.position + 2  # behind last_position plus one to shift back
            self._shift_plugin_positions(
                instance.language,
                start=instance.position,
                offset=shift_offset,
            )

        instance.save()

        if needs_shift:
            # The plugin tree was shifted to the right to make space, now squash all plugins in the
            # tree to close any holes. The shift moved the former last plugin to its highest
            # possible position, which is the parking offset the squash needs.
            self._recalculate_plugin_positions(instance.language, base=last_position + shift_offset)
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
        last_position = self.get_last_plugin_position(plugin.language)  # only the position is needed
        source_plugin_desc_count = plugin._get_descendants_count()
        # Attn: The following line assumes that all children and grand-children have consecutive positions!
        source_plugin_range = (plugin.position, plugin.position + source_plugin_desc_count)

        # A single shift is enough to establish the final ordering: the moved block is left in
        # place while everything it has to jump over is pushed a full tree-length out of the way.
        # That already yields the correct *relative* order (the only thing the renumbering below
        # depends on, since it sorts by position); the previous, complementary second shift only
        # changed the absolute — and partly negative — intermediate values without affecting that
        # order, so it was redundant. ``_recalculate_plugin_positions`` is order-independent and
        # collision-free for any intermediate state (positive, negative or gapped), so it closes
        # the resulting hole regardless. See GitHub issue #8665.
        if target_position < plugin.position:
            # Moving left: push everything from the target position onwards (except the moved
            # block) far to the right. The block then sorts immediately after position
            # ``target_position - 1``, i.e. it lands at ``target_position``.
            target_tree.filter(position__gte=target_position).exclude(position__range=source_plugin_range).update(
                position=models.F("position") + last_position
            )
        else:
            # Moving right: mirror image — push everything up to the end of the target region
            # (except the moved block) far to the left. The block then sorts immediately after
            # them. The right edge of that region is ``target_position`` in the common case, but
            # the closest node to the right of the moved block's last descendant if it has any.
            target_tree.filter(position__lte=target_position + source_plugin_desc_count).exclude(
                position__range=source_plugin_range
            ).update(position=models.F("position") - last_position)

        if plugin.parent != target_plugin:
            # Plugin is being moved to another tree (under another parent)
            # OR plugin is being moved to the root (no parent)
            plugin.update(parent=target_plugin)
        # The plugin tree was shifted to make space; squash all plugin positions to close any holes.
        # The left shift adds ``last_position`` to positions that are at most ``last_position``, so no
        # position can exceed twice that — a safe parking offset (the right shift only subtracts, so
        # it cannot exceed it either).
        self._recalculate_plugin_positions(plugin.language, base=2 * last_position)

    def _move_plugin_to_placeholder(self, plugin, target_position, target_placeholder, target_plugin=None):
        from cms.models.pluginmodel import CMSPlugin

        # Only the last positions are needed (for the parking bounds), not the whole rows.
        source_last_position = self.get_last_plugin_position(plugin.language)
        target_last_position = target_placeholder.get_last_plugin_position(plugin.language)

        # Fetch the descendant ids once and reuse them for both the count and the bulk update; calling
        # ``get_descendants()`` and then ``len()`` on it would run the descendant query twice.
        descendant_ids = plugin._get_descendants_ids()
        plugins_to_move_count = 1 + len(descendant_ids)  # parent plus descendants

        if target_last_position is not None:
            # Open a gap at ``target_position`` by shifting the target's tail (positions >=
            # target_position) far above its last position. A large offset keeps the shift
            # collision-free — the shifted band is disjoint from every current position, so it cannot
            # transiently duplicate one whatever order the rows are processed in (see #8665). The
            # block drops into the freed gap and the target squash below pulls everything back to a
            # dense ``1..n``, also healing any pre-existing gaps in the target.
            park_offset = target_last_position + plugins_to_move_count
            target_placeholder._shift_plugin_positions(plugin.language, start=target_position, offset=park_offset)
            block_position = target_position
            # Highest position the target now holds (the shifted tail's top); a valid parking bound.
            target_base = target_last_position + park_offset
        else:
            # Empty target: the block simply becomes positions 1..plugins_to_move_count.
            block_position = 1
            target_base = plugins_to_move_count

        # Move the block (parent and descendants) into the gap. The block is contiguous in the source,
        # so a single uniform shift preserves its internal order; moving only the block leaves a plain
        # gap in the source that the source squash below closes.
        moved_position = models.F("position") + (block_position - plugin.position)
        plugin.update(parent=target_plugin, placeholder=target_placeholder, position=moved_position)
        # TODO: More efficient is to do raw sql update
        CMSPlugin.objects.filter(pk__in=descendant_ids).update(placeholder=target_placeholder, position=moved_position)

        # Squash both placeholders back to a dense 1..n: the source to close the hole the block left,
        # the target to seat the block at ``target_position`` and heal any gaps. Both maxima are known
        # (source can only have shrunk; target is the shifted tail's top), so neither needs a query.
        self._recalculate_plugin_positions(plugin.language, base=source_last_position)
        target_placeholder._recalculate_plugin_positions(plugin.language, base=target_base)

    def delete_plugin(self, instance):
        """
        .. versionadded:: 4.0

        Removes a plugin and its descendants from the placeholder and database.

        :param instance: Plugin to add. It's position parameter needs to be set.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance
        """
        with transaction.atomic():
            # We're using raw sql - make the whole operation atomic
            stats = self.get_plugins(language=instance.language).aggregate(  # 1st hit: count + max position
                count=models.Count("pk"), max_position=models.Max("position")
            )
            plugins = stats["count"]
            descendants = instance._get_descendants_ids()  # 2nd hit: Get descendant ids
            to_delete = [instance.pk] + descendants  # Instance plus descendants pk
            self.cmsplugin_set.filter(pk__in=to_delete).delete()  # 3rd hit: Delete all plugins in one query

            last_position = instance.position + len(descendants)  # Last position of deleted plugins
            if last_position < plugins:
                # Close the gap in the plugin tree. The shift lifts the remaining plugins by
                # ``plugins``, so the old maximum plus that offset is a valid parking bound and the
                # squash needs no extra MAX/COUNT query.
                self._shift_plugin_positions(
                    instance.language,
                    start=instance.position,
                    offset=plugins,
                )
                self._recalculate_plugin_positions(instance.language, base=stats["max_position"] + plugins)

    def get_last_plugin(self, language):
        return self.get_plugins(language).last()

    def get_next_plugin_position(self, language, parent=None, insert_order="first"):
        """
        .. versionadded:: 4.0

        Helper to calculate plugin positions correctly.

        :param str language: language for which the position is to be calculated
        :param parent: Parent plugin or ``None`` (if position is on top level)
        :type parent: :class:`cms.models.pluginmodel.CMSPlugin` instance
        :param str insert_order: Either ``"first"`` (default) or ``"last"``
        """
        if insert_order == "first":
            position = self.get_first_plugin_position(language, parent=parent)
        else:
            position = self.get_last_plugin_position(language, parent=parent)

        if parent and position is None:
            return parent.position + 1

        if insert_order == "last":
            return (position or 0) + 1
        return position or 1

    def get_first_plugin_position(self, language, parent=None):
        tree = self.get_plugins(language)

        if parent:
            tree = tree.filter(parent=parent)
        return tree.values_list("position", flat=True).first()

    def get_last_plugin_position(self, language, parent=None):
        if parent is None:
            tree = self.get_plugins(language)
        elif parent.placeholder == self:
            tree = parent.get_descendants()
        else:  # No last plugin if parent is not in this placeholder's plugin tree
            return None
        return tree.values_list("position", flat=True).last()

    def _shift_plugin_positions(self, language, start, offset=None):
        if offset is None:
            offset = self.get_last_plugin_position(language) or 0

        self.get_plugins(language).filter(position__gte=start).update(position=models.F("position") + offset)

    def _recalculate_plugin_positions(self, language, base=None):
        """Closes gaps in the plugin tree by re-calculating the positions of all plugins of this
        placeholder/language back to a dense ``1..n`` sequence, ordered by the current ``position``
        (ties broken by ``id``).

        :param base: Optional pre-computed parking offset. It only has to be an **upper bound**: any
            value ``>=`` both the largest current ``position`` in the group and the number of plugins
            in it is safe. Callers that just shifted by a known amount already know the resulting
            maximum position and can pass it to skip the ``SELECT MAX(position), COUNT(*)`` round
            trip. When ``None`` (default) it is queried.

        The two phases below must run as a unit, so callers are expected to wrap the operation in a
        transaction (``add_plugin``, ``move_plugin``, ``delete_plugin`` and
        ``copy_plugins_to_placeholder`` all do, as do the atomic admin views). The compaction runs as
        two block moves:

        1. *Park*: every plugin of the group is moved to its final rank ``1..n`` shifted up by
           ``base`` into a band ``[base + 1 .. base + n]`` that lies strictly **above** every current
           position (``base >= max(position)``). Because the whole target band is above all existing
           positions, no target can equal the position another, not-yet-moved row still holds, so the
           statement cannot collide on the ``(placeholder, language, position)`` unique constraint —
           whatever order the database processes the rows in.
        2. *Unpark*: the parked band is shifted back down to ``1..n``. ``base`` is also kept ``>= n``,
           so the source band ``[base + 1 .. base + n]`` and the target ``1..n`` are disjoint and this
           statement cannot collide either.

        Because neither phase can self-collide regardless of the database's row-processing order or
        of any pre-existing gaps, this is safe under *any* starting state (including the negative or
        far-shifted intermediate positions ``move_plugin`` produces) and turns a successful
        recalculation into a self-heal of existing gaps. Previously the compaction ran as a single
        statement that could intermittently raise an ``IntegrityError`` (duplicate position) on
        PostgreSQL/SQLite — and likewise on MySQL/Oracle — whenever the position sequence contained a
        gap. See GitHub issue #8665.

        .. note::
            The intermediate positions reach at most ``max(position) + n``. ``position`` is a signed
            ``SmallIntegerField``, so this stays safe well beyond any realistic plugin count.
        """

        from cms.models.pluginmodel import (
            CMSPlugin,
            _get_database_cursor,
            _get_database_vendor,
        )

        cursor = _get_database_cursor("write")
        db_vendor = _get_database_vendor("write")
        table = connection.ops.quote_name(CMSPlugin._meta.db_table)

        if db_vendor not in ("sqlite", "postgresql", "mysql", "oracle"):
            raise RuntimeError(f"{connection.vendor} is not supported by django-cms")

        # ``base`` puts the parking band [base + 1 .. base + n] strictly above every current
        # position (so phase 1 cannot collide) while staying >= n (so phase 2's source band and
        # the 1..n target are disjoint and it cannot collide either). When the caller did not supply
        # an upper bound, query the maximum position and plugin count to derive the tightest one.
        if base is None:
            cursor.execute(
                f"SELECT COALESCE(MAX(position), 0), COUNT(*) FROM {table} "
                "WHERE placeholder_id=%s AND language=%s",
                [self.pk, language],
            )
            max_position, count = cursor.fetchone()
            if not count:
                # Nothing to recalculate (empty placeholder for this language).
                return
            base = max(max_position, count)

        if db_vendor in ("sqlite", "postgresql"):
            # Phase 1: park each row at (its rank) + base using a window function.
            park_sql = (
                f"UPDATE {table} "
                "SET position = subquery.new_pos + %s "
                "FROM ("
                "  SELECT id, ROW_NUMBER() OVER (ORDER BY position, id) AS new_pos "
                f"  FROM {table} WHERE placeholder_id=%s AND language=%s "
                ") subquery "
                f"WHERE {table}.id=subquery.id"
            )
        else:  # mysql, oracle
            # Phase 1: park each row at (its rank) + base. ``t`` is a snapshot of the current
            # positions, so the rank is computed independently of the rows already parked.
            # Positions are unique within a (placeholder, language) group, so counting the rows
            # strictly below each row yields a stable rank.
            park_sql = (
                f"UPDATE {table} "
                "SET position = %s + ("
                f"SELECT COUNT(*)+1 FROM (SELECT * FROM {table}) t "
                f"WHERE placeholder_id={table}.placeholder_id AND language={table}.language "
                f"AND {table}.position > t.position"
                ") WHERE placeholder_id=%s AND language=%s"
            )
        cursor.execute(park_sql, [base, self.pk, language])

        # Phase 2: shift the whole parked band back down to a dense 1..n. Every row of the group was
        # parked, so an unconditional shift by ``base`` is enough — a plain update with no window
        # function, so it needs no raw SQL. It runs on the same write connection, hence inside the
        # caller's transaction, right after the park above.
        self.get_plugins(language).update(position=models.F("position") - base)
