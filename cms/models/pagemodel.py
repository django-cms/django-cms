import copy
from collections import OrderedDict
from logging import getLogger
from os.path import join

from django.contrib.sites.models import Site
from django.db import models
from django.db.models.base import ModelState
from django.db.models.functions import Concat
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import (
    get_language, gettext_lazy as _, override as force_language,
)
from treebeard.mp_tree import MP_Node

from cms import constants
from cms.cache.permissions import clear_permission_cache
from cms.constants import (
    PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY, PUBLISHER_STATE_PENDING,
    TEMPLATE_INHERITANCE_MAGIC,
)
from cms.exceptions import (
    LanguageError, PublicIsUnmodifiable, PublicVersionNeeded,
)
from cms.models.managers import PageManager, PageNodeManager
from cms.utils import i18n
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_current_language
from cms.utils.page import get_clean_username
from menus.menu_pool import menu_pool

logger = getLogger(__name__)


class TreeNode(MP_Node):

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        db_index=True,
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        verbose_name=_("site"),
        related_name='djangocms_nodes',
        db_index=True,
    )

    objects = PageNodeManager()

    class Meta:
        app_label = 'cms'
        ordering = ('path',)
        default_permissions = []

    def __str__(self):
        return self.path

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        # Paving the way...
        return Page.objects.get(node=self, publisher_is_draft=True)

    @property
    def is_branch(self):
        return bool(self.numchild)

    def get_ancestor_paths(self):
        paths = frozenset(
            self.path[0:pos]
            for pos in range(0, len(self.path), self.steplen)[1:]
        )
        return paths

    def add_child(self, **kwargs):
        if len(kwargs) == 1 and 'instance' in kwargs:
            kwargs['instance'].parent = self
        else:
            kwargs['parent'] = self
        return super().add_child(**kwargs)

    def add_sibling(self, pos=None, *args, **kwargs):
        if len(kwargs) == 1 and 'instance' in kwargs:
            kwargs['instance'].parent_id = self.parent_id
        else:
            kwargs['parent_id'] = self.parent_id
        return super().add_sibling(pos, *args, **kwargs)

    def update(self, **data):
        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(**data)

        for field, value in data.items():
            setattr(self, field, value)
        return

    def get_cached_ancestors(self):
        if self._has_cached_hierarchy():
            return self._ancestors
        return []

    def get_cached_descendants(self):
        if self._has_cached_hierarchy():
            return self._descendants
        return []

    def _reload(self):
        """
        Reload a page node from the database
        """
        return self.__class__.objects.get(pk=self.pk)

    def _has_cached_hierarchy(self):
        return hasattr(self, '_descendants') and hasattr(self, '_ancestors')

    def _set_hierarchy(self, nodes, ancestors=None):
        if self.is_branch:
            self._descendants = [
                node for node in nodes
                if node.path.startswith(self.path) and node.depth > self.depth
            ]
        else:
            self._descendants = []

        if self.is_root():
            self._ancestors = []
        else:
            self._ancestors = ancestors

        children = (node for node in self._descendants
                    if node.depth == self.depth + 1)

        for child in children:
            child._set_hierarchy(self._descendants, ancestors=([self] + self._ancestors))


class Page(models.Model):
    """
    A simple hierarchical page model
    """
    LIMIT_VISIBILITY_IN_MENU_CHOICES = (
        (constants.VISIBILITY_USERS, _('for logged in users only')),
        (constants.VISIBILITY_ANONYMOUS, _('for anonymous users only')),
    )
    TEMPLATE_DEFAULT = TEMPLATE_INHERITANCE_MAGIC if get_cms_setting('TEMPLATE_INHERITANCE') else get_cms_setting('TEMPLATES')[0][0]

    X_FRAME_OPTIONS_INHERIT = constants.X_FRAME_OPTIONS_INHERIT
    X_FRAME_OPTIONS_DENY = constants.X_FRAME_OPTIONS_DENY
    X_FRAME_OPTIONS_SAMEORIGIN = constants.X_FRAME_OPTIONS_SAMEORIGIN
    X_FRAME_OPTIONS_ALLOW = constants.X_FRAME_OPTIONS_ALLOW
    X_FRAME_OPTIONS_CHOICES = (
        (constants.X_FRAME_OPTIONS_INHERIT, _('Inherit from parent page')),
        (constants.X_FRAME_OPTIONS_DENY, _('Deny')),
        (constants.X_FRAME_OPTIONS_SAMEORIGIN, _('Only this website')),
        (constants.X_FRAME_OPTIONS_ALLOW, _('Allow'))
    )

    template_choices = [(x, y) for x, y in get_cms_setting('TEMPLATES')]

    created_by = models.CharField(
        _("created by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    changed_by = models.CharField(
        _("changed by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    changed_date = models.DateTimeField(auto_now=True)

    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_(
        'When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True,
                                                help_text=_('When to expire the page. Leave empty to never expire.'),
                                                db_index=True)
    #
    # Please use toggle_in_navigation() instead of affecting this property
    # directly so that the cms page cache can be invalidated as appropriate.
    #
    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(_("soft root"), db_index=True, default=False,
                                    help_text=_("All ancestors will not be displayed in the navigation"))
    reverse_id = models.CharField(_("id"), max_length=40, db_index=True, blank=True, null=True, help_text=_(
        "A unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("attached menu"), max_length=80, db_index=True, blank=True, null=True)
    template = models.CharField(_("template"), max_length=100, choices=template_choices,
                                help_text=_('The template used to render the content.'),
                                default=TEMPLATE_DEFAULT)

    login_required = models.BooleanField(_("login required"), default=False)
    limit_visibility_in_menu = models.SmallIntegerField(_("menu visibility"), default=None, null=True, blank=True,
                                                        choices=LIMIT_VISIBILITY_IN_MENU_CHOICES, db_index=True,
                                                        help_text=_("limit when this page is visible in the menu"))
    is_home = models.BooleanField(editable=False, db_index=True, default=False)
    application_urls = models.CharField(_('application'), max_length=200, blank=True, null=True, db_index=True)
    application_namespace = models.CharField(_('application instance name'), max_length=200, blank=True, null=True)

    # Placeholders (plugins)
    placeholders = models.ManyToManyField('cms.Placeholder', editable=False)

    # Publisher fields
    publisher_is_draft = models.BooleanField(default=True, editable=False, db_index=True)
    # This is misnamed - the one-to-one relation is populated on both ends
    publisher_public = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        related_name='publisher_draft',
        null=True,
        editable=False,
    )
    languages = models.CharField(max_length=255, editable=False, blank=True, null=True)

    # X Frame Options for clickjacking protection
    xframe_options = models.IntegerField(
        choices=X_FRAME_OPTIONS_CHOICES,
        default=get_cms_setting('DEFAULT_X_FRAME_OPTIONS'),
    )

    # Flag that marks a page as page-type
    is_page_type = models.BooleanField(default=False)

    node = models.ForeignKey(
        TreeNode,
        related_name='cms_pages',
        on_delete=models.CASCADE,
    )

    # Managers
    objects = PageManager()

    class Meta:
        default_permissions = ('add', 'change', 'delete')
        permissions = (
            ('view_page', 'Can view page'),
            ('publish_page', 'Can publish page'),
            ('edit_static_placeholder', 'Can edit static placeholders'),
        )
        unique_together = ('node', 'publisher_is_draft')
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        app_label = 'cms'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_cache = {}

    def __str__(self):
        try:
            title = self.get_menu_title(fallback=True)
        except LanguageError:
            try:
                title = self.title_set.all()[0]
            except IndexError:
                title = None
        if title is None:
            title = u""
        return force_str(title)

    def __repr__(self):
        display = '<{module}.{class_name} id={id} is_draft={is_draft} object at {location}>'.format(
            module=self.__module__,
            class_name=self.__class__.__name__,
            id=self.pk,
            is_draft=self.publisher_is_draft,
            location=hex(id(self)),
        )
        return display

    def _clear_node_cache(self):
        if Page.node.is_cached(self):
            Page.node.field.delete_cached_value(self)

    def _clear_internal_cache(self):
        self.title_cache = {}
        self._clear_node_cache()

        if hasattr(self, '_prefetched_objects_cache'):
            del self._prefetched_objects_cache

    @cached_property
    def parent_page(self):
        return self.get_parent_page()

    def set_as_homepage(self, user=None):
        """
        Sets the given page as the homepage.
        Updates the title paths for all affected pages.
        Returns the old home page (if any).
        """
        assert self.publisher_is_draft

        if user:
            changed_by = get_clean_username(user)
        else:
            changed_by = constants.SCRIPT_USERNAME

        changed_date = now()

        try:
            old_home = self.__class__.objects.get(
                is_home=True,
                node__site=self.node.site_id,
                publisher_is_draft=True,
            )
        except self.__class__.DoesNotExist:
            old_home_tree = []
        else:
            old_home.update(
                draft_only=False,
                is_home=False,
                changed_by=changed_by,
                changed_date=changed_date,
            )
            old_home_tree = old_home._set_title_root_path()

        self.update(
            draft_only=False,
            is_home=True,
            changed_by=changed_by,
            changed_date=changed_date,
        )
        new_home_tree = self._remove_title_root_path()
        return (new_home_tree, old_home_tree)

    def _update_title_path(self, language):
        from cms.utils.page import get_available_slug

        parent_page = self.get_parent_page()

        if parent_page:
            base = parent_page.get_path(language, fallback=True)
        else:
            base = ''

        title_obj = self.get_title_obj(language, fallback=False)
        title_obj.slug = get_available_slug(title_obj.page.node.site, title_obj.slug, title_obj.language, current=title_obj.page)
        if not title_obj.page.is_home:
            title_obj.path = '%s/%s' % (base, title_obj.slug) if base else title_obj.slug
        title_obj.save()

    def _update_title_path_recursive(self, language, slug=None):
        assert self.publisher_is_draft
        from cms.models import Title

        if self.node.is_leaf() or language not in self.get_languages():
            return

        pages = self.get_child_pages()
        if slug:
            base = self.get_path_for_slug(slug, language)
        else:
            base = self.get_path(language, fallback=True)

        if base:
            new_path = Concat(models.Value(base), models.Value('/'), models.F('slug'))
        else:
            # User is moving the homepage
            new_path = models.F('slug')

        (Title
         .objects
         .filter(language=language, page__in=pages)
         .exclude(has_url_overwrite=True)
         .update(path=new_path))

        for child in pages.filter(title_set__language=language).iterator():
            child._update_title_path_recursive(language)

    def _set_title_root_path(self):
        from cms.models import Title

        node_tree = TreeNode.get_tree(self.node)
        page_tree = self.__class__.objects.filter(node__in=node_tree)
        translations = Title.objects.filter(page__in=page_tree, has_url_overwrite=False)

        for language, slug in self.title_set.values_list('language', 'slug'):
            # Update the translations for all descendants of this page
            # to include this page's slug as its path prefix
            (translations
             .filter(language=language)
             .update(path=Concat(models.Value(slug), models.Value('/'), 'path')))

            # Explicitly update this page's path to match its slug
            # Doing this is cheaper than a TRIM call to remove the "/" characters
            if self.publisher_public_id:
                # include the public translation
                current_translations = Title.objects.filter(page__in=[self.pk, self.publisher_public_id])
            else:
                current_translations = self.title_set.all()
            current_translations.filter(language=language).update(path=slug)
        return page_tree

    def _remove_title_root_path(self):
        from cms.models import Title

        node_tree = TreeNode.get_tree(self.node)
        page_tree = self.__class__.objects.filter(node__in=node_tree)
        translations = Title.objects.filter(page__in=page_tree, has_url_overwrite=False)

        for language, slug in self.title_set.values_list('language', 'slug'):
            # Use 2 because of 1 indexing plus the fact we need to trim
            # the "/" character.
            trim_count = len(slug) + 2
            sql_func = models.Func(
                models.F('path'),
                models.Value(trim_count),
                function='substr',
            )
            (translations
             .filter(language=language, path__startswith=slug)
             .update(path=sql_func))
        return page_tree

    def is_dirty(self, language):
        state = self.get_publisher_state(language)
        return state == PUBLISHER_STATE_DIRTY or state == PUBLISHER_STATE_PENDING

    def is_potential_home(self):
        """
        Encapsulates logic for determining if this page is eligible to be set
        as `is_home`. This is a public method so that it can be accessed in the
        admin for determining whether to enable the "Set as home" menu item.
        :return: Boolean
        """
        assert self.publisher_is_draft
        # Only root nodes are eligible for homepage
        return not self.is_home and bool(self.node.is_root())

    def get_absolute_url(self, language=None, fallback=True):
        if not language:
            language = get_current_language()

        with force_language(language):
            if self.is_home:
                return reverse('pages-root')
            path = self.get_path(language, fallback) or self.get_slug(language, fallback)
            return reverse('pages-details-by-slug', kwargs={"slug": path})

    def get_public_url(self, language=None, fallback=True):
        """
        Returns the URL of the published version of the current page.
        Returns empty string if the page is not published.
        """
        try:
            return self.get_public_object().get_absolute_url(language, fallback)
        except:  # noqa: E722
            return ''

    def get_draft_url(self, language=None, fallback=True):
        """
        Returns the URL of the draft version of the current page.
        Returns empty string if the draft page is not available.
        """
        try:
            return self.get_draft_object().get_absolute_url(language, fallback)
        except (AttributeError, NoReverseMatch, TypeError):
            return ''

    def set_tree_node(self, site, target=None, position='first-child'):
        assert self.publisher_is_draft
        assert position in ('last-child', 'first-child', 'left', 'right')

        new_node = TreeNode(site=site)

        if target is None:
            self.node = TreeNode.add_root(instance=new_node)
        elif position == 'first-child' and target.is_branch:
            self.node = target.get_first_child().add_sibling(pos='left', instance=new_node)
        elif position in ('last-child', 'first-child'):
            self.node = target.add_child(instance=new_node)
        else:
            self.node = target.add_sibling(pos=position, instance=new_node)

    def move_page(self, target_node, position='first-child'):
        """
        Called from admin interface when page is moved. Should be used on
        all the places which are changing page position. Used like an interface
        to django-treebeard, but after move is done page_moved signal is fired.

        Note for issue #1166: url conflicts are handled by updated
        check_title_slugs, overwrite_url on the moved page don't need any check
        as it remains the same regardless of the page position in the tree
        """
        assert self.publisher_is_draft
        assert isinstance(target_node, TreeNode)

        inherited_template = self.template == constants.TEMPLATE_INHERITANCE_MAGIC

        if inherited_template and target_node.is_root() and position in ('left', 'right'):
            # The page is being moved to a root position.
            # Explicitly set the inherited template on the page
            # to keep all plugins / placeholders.
            self.update(refresh=False, template=self.get_template())

        # Don't use a cached node. Always get a fresh one.
        self._clear_node_cache()

        # Runs the SQL updates on the treebeard fields
        self.node.move(target_node, position)

        if position in ('first-child', 'last-child'):
            parent_id = target_node.pk
        else:
            # moving relative to sibling
            # or to the root of the tree
            parent_id = target_node.parent_id
        # Runs the SQL updates on the parent field
        self.node.update(parent_id=parent_id)

        # Clear the cached node once again to trigger a db query
        # on access.
        self._clear_node_cache()

        # Update the descendants to "PENDING"
        # If the target (parent) page is not published
        # and the page being moved is published.
        titles = (
            self
            .title_set
            .filter(language__in=self.get_languages())
            .values_list('language', 'published')
        )
        parent_page = self.get_parent_page()

        if parent_page:
            parent_titles = (
                parent_page
                .title_set
                .exclude(publisher_state=PUBLISHER_STATE_PENDING)
                .values_list('language', 'published')
            )
            parent_titles_by_language = dict(parent_titles)
        else:
            parent_titles_by_language = {}

        for language, published in titles:
            parent_is_published = parent_titles_by_language.get(language)

            # Update draft title path
            self._update_title_path(language)
            self._update_title_path_recursive(language)

            if published and parent_is_published:
                # this looks redundant but it's necessary
                # for all the descendants of the page being
                # moved to be set to the correct state.
                self.publisher_public._update_title_path(language)
                self.mark_as_published(language)
                self.mark_descendants_as_published(language)
            elif published and parent_page:
                # page is published but it's parent is not
                # mark the page being moved (source) as "pending"
                self.mark_as_pending(language)
                # mark all descendants of source as "pending"
                self.mark_descendants_pending(language)
            elif published:
                self.publisher_public._update_title_path(language)
                self.mark_as_published(language)
                self.mark_descendants_as_published(language)
        self.clear_cache(menu=True)
        if get_cms_setting('PERMISSION'):
            clear_permission_cache()
        return self

    def _copy_titles(self, target, language, published):
        """
        Copy the title matching language to a new page (which must have a pk).
        :param target: The page where the new title should be stored
        """
        source_title = self.title_set.get(language=language)

        try:
            target_title_id = (
                target
                .title_set
                .filter(language=language)
                .values_list('pk', flat=True)[0]
            )
        except IndexError:
            target_title_id = None

        source_title_id = source_title.pk

        # If an old title exists, overwrite. Otherwise create new
        source_title.pk = target_title_id
        source_title.page = target
        source_title.publisher_is_draft = target.publisher_is_draft
        source_title.publisher_public_id = source_title_id
        source_title.published = published
        source_title._publisher_keep_state = True

        if published:
            source_title.publisher_state = PUBLISHER_STATE_DEFAULT
        else:
            source_title.publisher_state = PUBLISHER_STATE_PENDING
        source_title.save()
        return source_title

    def _clear_placeholders(self, language=None):
        from cms.models import CMSPlugin

        placeholders = list(self.get_placeholders())
        placeholder_ids = (placeholder.pk for placeholder in placeholders)
        plugins = CMSPlugin.objects.filter(placeholder__in=placeholder_ids)

        if language:
            plugins = plugins.filter(language=language)
        models.query.QuerySet.delete(plugins)
        return placeholders

    def _copy_contents(self, target, language):
        """
        Copy all the plugins to a new page.
        :param target: The page where the new content should be stored
        """
        cleared_placeholders = target._clear_placeholders(language)
        cleared_placeholders_by_slot = {pl.slot: pl for pl in cleared_placeholders}

        for placeholder in self.get_placeholders():
            try:
                target_placeholder = cleared_placeholders_by_slot[placeholder.slot]
            except KeyError:
                target_placeholder = target.placeholders.create(
                    slot=placeholder.slot,
                    default_width=placeholder.default_width,
                )

            placeholder.copy_plugins(target_placeholder, language=language)

    def _copy_attributes(self, target, clean=False):
        """
        Copy all page data to the target. This excludes parent and other values
        that are specific to an exact instance.
        :param target: The Page to copy the attributes to
        """
        if not clean:
            target.publication_date = self.publication_date
            target.publication_end_date = self.publication_end_date
            target.reverse_id = self.reverse_id
        target.changed_by = self.changed_by
        target.login_required = self.login_required
        target.in_navigation = self.in_navigation
        target.soft_root = self.soft_root
        target.limit_visibility_in_menu = self.limit_visibility_in_menu
        target.navigation_extenders = self.navigation_extenders
        target.application_urls = self.application_urls
        target.application_namespace = self.application_namespace
        target.template = self.template
        target.xframe_options = self.xframe_options
        target.is_page_type = self.is_page_type

    def copy(self, site, parent_node=None, language=None,
             translations=True, permissions=False, extensions=True):
        from cms.utils.page import get_available_slug

        if parent_node:
            new_node = parent_node.add_child(site=site)
            parent_page = parent_node.item
        else:
            new_node = TreeNode.add_root(site=site)
            parent_page = None

        new_page = copy.copy(self)
        new_page._state = ModelState()
        new_page._clear_internal_cache()
        new_page.pk = None
        new_page.node = new_node
        new_page.publisher_public_id = None
        new_page.is_home = False
        new_page.reverse_id = None
        new_page.publication_date = None
        new_page.publication_end_date = None
        new_page.languages = ''
        new_page.save()

        # Have the node remember its page.
        # This is done to save some queries
        # when the node's descendants are copied.
        new_page.node.__dict__['item'] = new_page

        if language and translations:
            translations = self.title_set.filter(language=language)
        elif translations:
            translations = self.title_set.all()
        else:
            translations = self.title_set.none()

        # copy titles of this page
        for title in translations:
            title = copy.copy(title)
            title.pk = None
            title.page = new_page
            title.published = False
            title.publisher_public = None

            if parent_page:
                base = parent_page.get_path(title.language)
                path = '%s/%s' % (base, title.slug) if base else title.slug
            else:
                base = ''
                path = title.slug

            title.slug = get_available_slug(site, path, title.language)
            title.path = '%s/%s' % (base, title.slug) if base else title.slug
            title.save()

            new_page.title_cache[title.language] = title
        new_page.update_languages([trans.language for trans in translations])

        # copy the placeholders (and plugins on those placeholders!)
        for placeholder in self.placeholders.iterator():
            new_placeholder = copy.copy(placeholder)
            new_placeholder.pk = None
            new_placeholder.save()
            new_page.placeholders.add(new_placeholder)
            placeholder.copy_plugins(new_placeholder, language=language)

        if extensions:
            from cms.extensions import extension_pool
            extension_pool.copy_extensions(self, new_page)

        # copy permissions if requested
        if permissions and get_cms_setting('PERMISSION'):
            permissions = self.pagepermission_set.iterator()
            permissions_new = []

            for permission in permissions:
                permission.pk = None
                permission.page = new_page
                permissions_new.append(permission)

            if permissions_new:
                new_page.pagepermission_set.bulk_create(permissions_new)
        return new_page

    def copy_with_descendants(self, target_node=None, position=None,
                              copy_permissions=True, target_site=None):
        """
        Copy a page [ and all its descendants to a new location ]
        """
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable("copy page is not allowed for public pages")

        if position in ('first-child', 'last-child'):
            parent_node = target_node
        elif target_node:
            parent_node = target_node.parent
        else:
            parent_node = None

        if target_site is None:
            target_site = parent_node.site if parent_node else self.node.site

        # Evaluate the descendants queryset BEFORE copying the page.
        # Otherwise, if the page is copied and pasted on itself, it will duplicate.
        descendants = list(
            self.get_descendant_pages()
            .select_related('node')
            .prefetch_related('title_set')
        )
        new_root_page = self.copy(target_site, parent_node=parent_node)
        new_root_node = new_root_page.node

        if target_node and position in ('first-child'):
            # target node is a parent and user has requested to
            # insert the new page as its first child
            new_root_node.move(target_node, position)
            new_root_node.refresh_from_db(fields=('path', 'depth'))

        if target_node and position in ('left', 'last-child'):
            # target node is a sibling
            new_root_node.move(target_node, position)
            new_root_node.refresh_from_db(fields=('path', 'depth'))

        nodes_by_id = {self.node.pk: new_root_node}

        for page in descendants:
            parent = nodes_by_id[page.node.parent_id]
            new_page = page.copy(
                target_site,
                parent_node=parent,
                translations=True,
                permissions=copy_permissions,
            )
            nodes_by_id[page.node_id] = new_page.node
        return new_root_page

    def delete(self, *args, **kwargs):
        TreeNode.get_tree(self.node).delete_fast()

        if self.node.parent_id:
            (TreeNode
             .objects
             .filter(pk=self.node.parent_id)
             .update(numchild=models.F('numchild') - 1))
        self.clear_cache(menu=True)

    def delete_translations(self, language=None):
        if language is None:
            languages = self.get_languages()
        else:
            languages = [language]

        self.title_set.filter(language__in=languages).delete()

        for language in languages:
            self.mark_descendants_pending(language)

    def save(self, **kwargs):
        # delete template cache
        if hasattr(self, '_template_cache'):
            delattr(self, '_template_cache')

        created = not bool(self.pk)
        if self.reverse_id == "":
            self.reverse_id = None
        if self.application_namespace == "":
            self.application_namespace = None
        from cms.utils.permissions import get_current_user_name

        self.changed_by = get_current_user_name()

        if created:
            self.created_by = self.changed_by
        super().save(**kwargs)
        if created and get_cms_setting('PERMISSION'):
            clear_permission_cache()

    def save_base(self, *args, **kwargs):
        """Overridden save_base. If an instance is draft, and was changed, mark
        it as dirty.

        Dirty flag is used for changed nodes identification when publish method
        takes place. After current changes are published, state is set back to
        PUBLISHER_STATE_DEFAULT (in publish method).
        """
        keep_state = getattr(self, '_publisher_keep_state', None)
        if self.publisher_is_draft and not keep_state and self.is_new_dirty():
            self.title_set.all().update(publisher_state=PUBLISHER_STATE_DIRTY)
        if keep_state:
            delattr(self, '_publisher_keep_state')
        return super().save_base(*args, **kwargs)

    def update(self, refresh=False, draft_only=True, **data):
        assert self.publisher_is_draft

        cls = self.__class__

        if not draft_only and self.publisher_public_id:
            ids = [self.pk, self.publisher_public_id]
            cls.objects.filter(pk__in=ids).update(**data)
        else:
            cls.objects.filter(pk=self.pk).update(**data)

        if refresh:
            return self.reload()
        else:
            for field, value in data.items():
                setattr(self, field, value)
        return

    def update_translations(self, language=None, **data):
        if language:
            translations = self.title_set.filter(language=language)
        else:
            translations = self.title_set.all()
        return translations.update(**data)

    def has_translation(self, language):
        return self.title_set.filter(language=language).exists()

    def is_new_dirty(self):
        if self.pk:
            fields = [
                'publication_date', 'publication_end_date', 'in_navigation', 'soft_root', 'reverse_id',
                'navigation_extenders', 'template', 'login_required', 'limit_visibility_in_menu'
            ]
            try:
                old_page = Page.objects.get(pk=self.pk)
            except Page.DoesNotExist:
                return True
            for field in fields:
                old_val = getattr(old_page, field)
                new_val = getattr(self, field)
                if not old_val == new_val:
                    return True
            return False
        return True

    def is_published(self, language, force_reload=False):
        title_obj = self.get_title_obj(language, fallback=False, force_reload=force_reload)
        return title_obj.published and title_obj.publisher_state != PUBLISHER_STATE_PENDING

    def toggle_in_navigation(self, set_to=None):
        '''
        Toggles (or sets) in_navigation and invalidates the cms page cache
        '''
        old = self.in_navigation
        if set_to in [True, False]:
            self.in_navigation = set_to
        else:
            self.in_navigation = not self.in_navigation
        self.save()

        # If there was a change, invalidate the cms page cache
        if self.in_navigation != old:
            self.clear_cache()
        return self.in_navigation

    def get_publisher_state(self, language, force_reload=False):
        try:
            return self.get_title_obj(language, False, force_reload=force_reload).publisher_state
        except AttributeError:
            return None

    def set_publisher_state(self, language, state, published=None):
        title = self.title_set.get(language=language)
        title.publisher_state = state
        if published is not None:
            title.published = published
        title._publisher_keep_state = True
        title.save()
        if language in self.title_cache:
            self.title_cache[language].publisher_state = state
        return title

    def publish(self, language):
        """
        :returns: True if page was successfully published.
        """
        from cms.utils.permissions import get_current_user_name

        # Publish can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be published. Use draft.')

        if not self._publisher_can_publish(language):
            return False

        if self.publisher_public_id:
            public_page = Page.objects.get(pk=self.publisher_public_id)
            public_languages = public_page.get_languages()
        else:
            public_page = Page(created_by=self.created_by)
            public_languages = [language]

        self._copy_attributes(public_page, clean=False)

        if language not in public_languages:
            public_languages.append(language)

        # TODO: Get rid of the current user thread hack
        public_page.changed_by = get_current_user_name()
        public_page.is_home = self.is_home
        public_page.publication_date = self.publication_date or now()
        public_page.publisher_public = self
        public_page.publisher_is_draft = False
        public_page.languages = ','.join(public_languages)
        public_page.node = self.node
        public_page.save()

        # Copy the page translation (title) matching language
        # into a "public" version.
        public_title = self._copy_titles(public_page, language, published=True)

        # Ensure this draft page points to its public version
        self.update(
            draft_only=True,
            changed_by=public_page.changed_by,
            publisher_public=public_page,
            publication_date=public_page.publication_date,
        )

        # Set the draft page translation matching language
        # to point to its public version.
        # Its important for draft to be published even if its state
        # is pending.
        self.update_translations(
            language,
            published=True,
            publisher_public=public_title,
            publisher_state=PUBLISHER_STATE_DEFAULT,
        )
        self._copy_contents(public_page, language)

        if self.node.is_branch:
            self.mark_descendants_as_published(language)

        if language in self.title_cache:
            del self.title_cache[language]

        # fire signal after publishing is done
        import cms.signals as cms_signals

        cms_signals.post_publish.send(sender=Page, instance=self, language=language)

        public_page.clear_cache(
            language,
            menu=True,
            placeholder=True,
        )
        return True

    def clear_cache(self, language=None, menu=False, placeholder=False):
        from cms.cache import invalidate_cms_page_cache

        if get_cms_setting('PAGE_CACHE'):
            # Clears all the page caches
            invalidate_cms_page_cache()

        if placeholder and get_cms_setting('PLACEHOLDER_CACHE'):
            assert language, 'language is required when clearing placeholder cache'

            placeholders = self.get_placeholders()

            for placeholder in placeholders:
                placeholder.clear_cache(language, site_id=self.node.site_id)

        if menu:
            # Clears all menu caches for this page's site
            menu_pool.clear(site_id=self.node.site_id)

    def unpublish(self, language, site=None):
        """
        Removes this page from the public site
        :returns: True if this page was successfully unpublished
        """
        # Publish can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be unpublished. Use draft.')

        self.update_translations(
            language,
            published=False,
            publisher_state=PUBLISHER_STATE_DIRTY,
        )

        public_page = self.get_public_object()
        public_page.update_translations(language, published=False)
        public_page._clear_placeholders(language)
        public_page.clear_cache(language)

        self.mark_descendants_pending(language)

        from cms.signals import post_unpublish
        post_unpublish.send(sender=Page, instance=self, language=language)

        return True

    def get_child_pages(self):
        nodes = self.node.get_children()
        pages = (
            self
            .__class__
            .objects
            .filter(
                node__in=nodes,
                publisher_is_draft=self.publisher_is_draft,
            )
            .order_by('node__path')
        )
        return pages

    def get_ancestor_pages(self):
        nodes = self.node.get_ancestors()
        pages = (
            self
            .__class__
            .objects
            .filter(
                node__in=nodes,
                publisher_is_draft=self.publisher_is_draft,
            )
            .order_by('node__path')
        )
        return pages

    def get_descendant_pages(self):
        nodes = self.node.get_descendants()
        pages = (
            self
            .__class__
            .objects
            .filter(
                node__in=nodes,
                publisher_is_draft=self.publisher_is_draft,
            )
            .order_by('node__path')
        )
        return pages

    def get_root(self):
        node = self.node
        return self.__class__.objects.get(
            node__path=node.path[0:node.steplen],
            publisher_is_draft=self.publisher_is_draft,
        )

    def get_parent_page(self):
        if not self.node.parent_id:
            return None

        pages = Page.objects.filter(
            node=self.node.parent_id,
            publisher_is_draft=self.publisher_is_draft,
        )
        return pages.select_related('node').first()

    def mark_as_pending(self, language):
        assert self.publisher_is_draft
        assert self.publisher_public_id

        self.get_public_object().title_set.filter(language=language).update(published=False)

        if self.get_publisher_state(language) == PUBLISHER_STATE_DEFAULT:
            # Only change the state if the draft page is published
            # and it's state is the default (0), to avoid overriding a dirty state.
            self.set_publisher_state(language, state=PUBLISHER_STATE_PENDING)

    def mark_descendants_pending(self, language):
        from cms.models import Title

        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be altered. Use draft.')

        node_descendants = self.node.get_descendants()
        page_descendants = self.__class__.objects.filter(node__in=node_descendants)

        if page_descendants.filter(publisher_is_draft=True).exists():
            # Only change the state if the draft page is not dirty
            # to avoid overriding a dirty state.
            Title.objects.filter(
                published=True,
                language=language,
                page__in=page_descendants.filter(publisher_is_draft=True),
                publisher_state=PUBLISHER_STATE_DEFAULT,
            ).update(publisher_state=PUBLISHER_STATE_PENDING)

        if page_descendants.filter(publisher_is_draft=False).exists():
            Title.objects.filter(
                published=True,
                language=language,
                page__in=page_descendants.filter(publisher_is_draft=False),
            ).update(published=False)

    def mark_as_published(self, language):
        from cms.models import Title

        (Title
         .objects
         .filter(page=self.publisher_public_id, language=language)
         .update(publisher_state=PUBLISHER_STATE_DEFAULT, published=True))

        draft = self.get_draft_object()

        if draft.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
            # A check for pending is necessary because the page might have
            # been modified after it was marked as pending.
            draft.set_publisher_state(language, PUBLISHER_STATE_DEFAULT)

    def mark_descendants_as_published(self, language):
        from cms.models import Title

        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be published. Use draft.')

        base = self.get_path(language, fallback=True)
        node_children = self.node.get_children()
        page_children = self.__class__.objects.filter(node__in=node_children)
        page_children_draft = page_children.filter(publisher_is_draft=True)
        page_children_public = page_children.filter(publisher_is_draft=False)

        # Set public pending titles as published
        unpublished_public = Title.objects.filter(
            language=language,
            page__in=page_children_public,
            publisher_public__published=True,
        )

        if base:
            new_path = Concat(models.Value(base), models.Value('/'), models.F('slug'))
        else:
            # User is moving the homepage
            new_path = models.F('slug')

        # Update public title paths
        unpublished_public.exclude(has_url_overwrite=True).update(path=new_path)

        # Set unpublished pending titles to published
        unpublished_public.filter(published=False).update(published=True)

        # Update drafts
        Title.objects.filter(
            published=True,
            language=language,
            page__in=page_children_draft,
            publisher_state=PUBLISHER_STATE_PENDING
        ).update(publisher_state=PUBLISHER_STATE_DEFAULT)

        # Continue publishing descendants, one branch at a time.
        published_children = page_children_draft.filter(
            title_set__published=True,
            title_set__language=language,
        )

        for child in published_children.iterator():
            child.mark_descendants_as_published(language)

    def revert_to_live(self, language):
        """Revert the draft version to the same state as the public version
        """
        if not self.publisher_is_draft:
            # Revert can only be called on draft pages
            raise PublicIsUnmodifiable('The public instance cannot be reverted. Use draft.')

        public = self.get_public_object()

        if not public:
            raise PublicVersionNeeded('A public version of this page is needed')

        public._copy_attributes(self)
        public._copy_contents(self, language)
        public._copy_titles(self, language, public.is_published(language))

        self.update_translations(
            language,
            published=True,
            publisher_state=PUBLISHER_STATE_DEFAULT,
        )
        self._publisher_keep_state = True
        self.save()

    def get_draft_object(self):
        if not self.publisher_is_draft:
            return self.publisher_draft
        return self

    def get_public_object(self):
        if not self.publisher_is_draft:
            return self
        return self.publisher_public

    def get_languages(self):
        if self.languages:
            return sorted(self.languages.split(','))
        else:
            return []

    def remove_language(self, language):
        page_languages = self.get_languages()

        if language in page_languages:
            page_languages.remove(language)
            self.update_languages(page_languages)

    def update_languages(self, languages):
        languages = ",".join(languages)
        # Update current instance
        self.languages = languages
        # Commit. It's important to not call save()
        # we'd like to commit only the languages field and without
        # any kind of signals.
        self.update(draft_only=False, languages=languages)

    def get_published_languages(self):
        if self.publisher_is_draft:
            return self.get_languages()
        return sorted([language for language in self.get_languages() if self.is_published(language)])

    def set_translations_cache(self):
        for translation in self.title_set.all():
            self.title_cache.setdefault(translation.language, translation)

    def get_path_for_slug(self, slug, language):
        if self.is_home:
            return ''

        if self.parent_page:
            base = self.parent_page.get_path(language, fallback=True)
            # base can be empty when the parent is a home-page
            path = u'%s/%s' % (base, slug) if base else slug
        else:
            path = slug
        return path

    # ## Title object access

    def get_title_obj(self, language=None, fallback=True, force_reload=False):
        """Helper function for accessing wanted / current title.
        If wanted title doesn't exists, EmptyTitle instance will be returned.
        """
        language = self._get_title_cache(language, fallback, force_reload)
        if language in self.title_cache:
            return self.title_cache[language]
        from cms.models.titlemodels import EmptyTitle

        return EmptyTitle(language)

    def get_title_obj_attribute(self, attrname, language=None, fallback=True, force_reload=False):
        """Helper function for getting attribute or None from wanted/current title.
        """
        try:
            attribute = getattr(self.get_title_obj(language, fallback, force_reload), attrname)
            return attribute
        except AttributeError:
            return None

    def get_path(self, language=None, fallback=True, force_reload=False):
        """
        get the path of the page depending on the given language
        """
        return self.get_title_obj_attribute("path", language, fallback, force_reload)

    def get_slug(self, language=None, fallback=True, force_reload=False):
        """
        get the slug of the page depending on the given language
        """
        return self.get_title_obj_attribute("slug", language, fallback, force_reload)

    def get_title(self, language=None, fallback=True, force_reload=False):
        """
        get the title of the page depending on the given language
        """
        return self.get_title_obj_attribute("title", language, fallback, force_reload)

    def get_menu_title(self, language=None, fallback=True, force_reload=False):
        """
        get the menu title of the page depending on the given language
        """
        menu_title = self.get_title_obj_attribute("menu_title", language, fallback, force_reload)
        if not menu_title:
            return self.get_title(language, True, force_reload)
        return menu_title

    def get_placeholders(self):
        if not hasattr(self, '_placeholder_cache'):
            self._placeholder_cache = self.placeholders.all()
        return self._placeholder_cache

    def _validate_title(self, title):
        from cms.models.titlemodels import EmptyTitle
        if isinstance(title, EmptyTitle):
            return False
        if not title.title or not title.slug:
            return False
        return True

    def get_admin_tree_title(self):
        from cms.models.titlemodels import EmptyTitle
        language = get_language()

        if not self.title_cache:
            self.set_translations_cache()

        if language not in self.title_cache or not self._validate_title(self.title_cache.get(language, EmptyTitle(language))):
            fallback_langs = i18n.get_fallback_languages(language)
            found = False
            for lang in fallback_langs:
                if lang in self.title_cache and self._validate_title(self.title_cache.get(lang, EmptyTitle(lang))):
                    found = True
                    language = lang
            if not found:
                language = None
                for lang, item in self.title_cache.items():
                    if not isinstance(item, EmptyTitle):
                        language = lang
        if not language:
            return _("Empty")
        title = self.title_cache[language]
        if title.title:
            return title.title
        if title.page_title:
            return title.page_title
        if title.menu_title:
            return title.menu_title
        return title.slug

    def get_changed_date(self, language=None, fallback=True, force_reload=False):
        """
        get when this page was last updated
        """
        return self.changed_date

    def get_changed_by(self, language=None, fallback=True, force_reload=False):
        """
        get user who last changed this page
        """
        return self.changed_by

    def get_page_title(self, language=None, fallback=True, force_reload=False):
        """
        get the page title of the page depending on the given language
        """
        page_title = self.get_title_obj_attribute("page_title", language, fallback, force_reload)

        if not page_title:
            return self.get_title(language, True, force_reload)
        return page_title

    def get_meta_description(self, language=None, fallback=True, force_reload=False):
        """
        get content for the description meta tag for the page depending on the given language
        """
        return self.get_title_obj_attribute("meta_description", language, fallback, force_reload)

    def get_application_urls(self, language=None, fallback=True, force_reload=False):
        """
        get application urls conf for application hook
        """
        return self.application_urls

    def get_redirect(self, language=None, fallback=True, force_reload=False):
        """
        get redirect
        """
        return self.get_title_obj_attribute("redirect", language, fallback, force_reload)

    def _get_title_cache(self, language, fallback, force_reload):
        if not language:
            language = get_language()

        force_reload = (force_reload or language not in self.title_cache)

        if force_reload:
            for title in self.title_set.all():
                self.title_cache[title.language] = title

        if fallback and not self.title_cache.get(language):
            fallback_langs = i18n.get_fallback_languages(language)
            for lang in fallback_langs:
                if self.title_cache.get(lang):
                    return lang

        return language

    def get_template(self):
        """
        get the template of this page if defined or if closer parent if
        defined or DEFAULT_PAGE_TEMPLATE otherwise
        """
        if hasattr(self, '_template_cache'):
            return self._template_cache

        if self.template != constants.TEMPLATE_INHERITANCE_MAGIC:
            self._template_cache = self.template or get_cms_setting('TEMPLATES')[0][0]
            return self._template_cache

        templates = (
            self
            .get_ancestor_pages()
            .exclude(template=constants.TEMPLATE_INHERITANCE_MAGIC)
            .order_by('-node__path')
            .values_list('template', flat=True)
        )

        try:
            self._template_cache = templates[0]
        except IndexError:
            self._template_cache = get_cms_setting('TEMPLATES')[0][0]
        return self._template_cache

    def get_template_name(self):
        """
        get the textual name (2nd parameter in get_cms_setting('TEMPLATES'))
        of the template of this page or of the nearest
        ancestor. failing to find that, return the name of the default template.
        """
        template = self.get_template()
        for t in get_cms_setting('TEMPLATES'):
            if t[0] == template:
                return t[1]
        return _("default")

    def has_view_permission(self, user):
        from cms.utils.page_permissions import user_can_view_page
        return user_can_view_page(user, page=self)

    def has_view_restrictions(self, site):
        from cms.models import PagePermission

        if get_cms_setting('PERMISSION'):
            page = self.get_draft_object()
            restrictions = (
                PagePermission
                .objects
                .for_page(page)
                .filter(can_view=True)
            )
            return restrictions.exists()
        return False

    def has_add_permission(self, user):
        """
        Has user ability to add page under current page?
        """
        from cms.utils.page_permissions import user_can_add_subpage
        return user_can_add_subpage(user, self)

    def has_change_permission(self, user):
        from cms.utils.page_permissions import user_can_change_page
        return user_can_change_page(user, page=self)

    def has_delete_permission(self, user):
        from cms.utils.page_permissions import user_can_delete_page
        return user_can_delete_page(user, page=self)

    def has_delete_translation_permission(self, user, language):
        from cms.utils.page_permissions import user_can_delete_page_translation
        return user_can_delete_page_translation(user, page=self, language=language)

    def has_publish_permission(self, user):
        from cms.utils.page_permissions import user_can_publish_page
        return user_can_publish_page(user, page=self)

    def has_advanced_settings_permission(self, user):
        from cms.utils.page_permissions import (
            user_can_change_page_advanced_settings,
        )
        return user_can_change_page_advanced_settings(user, page=self)

    def has_change_permissions_permission(self, user):
        """
        Has user ability to change permissions for current page?
        """
        from cms.utils.page_permissions import user_can_change_page_permissions
        return user_can_change_page_permissions(user, page=self)

    def has_move_page_permission(self, user):
        """Has user ability to move current page?
        """
        from cms.utils.page_permissions import user_can_move_page
        return user_can_move_page(user, page=self)

    def has_placeholder_change_permission(self, user):
        if not self.publisher_is_draft:
            return False
        return self.has_change_permission(user)

    def get_media_path(self, filename):
        """
        Returns path (relative to MEDIA_ROOT/MEDIA_URL) to directory for storing
        page-scope files. This allows multiple pages to contain files with
        identical names without namespace issues. Plugins such as Picture can
        use this method to initialise the 'upload_to' parameter for File-based
        fields. For example:
            image = models.ImageField(
                _("image"), upload_to=CMSPlugin.get_media_path)

        where CMSPlugin.get_media_path calls self.page.get_media_path

        This location can be customised using the CMS_PAGE_MEDIA_PATH setting
        """
        return join(get_cms_setting('PAGE_MEDIA_PATH'), "%d" % self.pk, filename)

    def reload(self):
        """
        Reload a page from the database
        """
        return self.__class__.objects.get(pk=self.pk)

    def _publisher_can_publish(self, language):
        """Is parent of this object already published?
        """
        if self.is_page_type:
            return False

        if not self.parent_page:
            return True

        if self.parent_page.publisher_public_id:
            return self.parent_page.get_public_object().is_published(language)
        return False

    def rescan_placeholders(self):
        """
        Rescan and if necessary create placeholders in the current template.
        """
        existing = OrderedDict()
        placeholders = [pl.slot for pl in self.get_declared_placeholders()]

        for placeholder in self.placeholders.all():
            if placeholder.slot in placeholders:
                existing[placeholder.slot] = placeholder

        for placeholder in placeholders:
            if placeholder not in existing:
                existing[placeholder] = self.placeholders.create(slot=placeholder)
        return existing

    def get_declared_placeholders(self):
        # inline import to prevent circular imports
        from cms.utils.placeholder import get_placeholders

        return get_placeholders(self.get_template())

    def get_declared_static_placeholders(self, context):
        # inline import to prevent circular imports
        from cms.utils.placeholder import get_static_placeholders

        return get_static_placeholders(self.get_template(), context)

    def get_xframe_options(self):
        """ Finds X_FRAME_OPTION from tree if inherited """
        xframe_options = self.xframe_options or self.X_FRAME_OPTIONS_INHERIT

        if xframe_options != self.X_FRAME_OPTIONS_INHERIT:
            return xframe_options

        # Ignore those pages which just inherit their value
        ancestors = self.get_ancestor_pages().order_by('-node__path')
        ancestors = ancestors.exclude(xframe_options=self.X_FRAME_OPTIONS_INHERIT)

        # Now just give me the clickjacking setting (not anything else)
        xframe_options = ancestors.values_list('xframe_options', flat=True)

        try:
            return xframe_options[0]
        except IndexError:
            return None


class PageType(Page):

    class Meta:
        proxy = True
        default_permissions = []

    @classmethod
    def get_root_page(cls, site):
        pages = Page.objects.on_site(site).filter(
            node__depth=1,
            is_page_type=True,
        )
        return pages.first()

    def is_potential_home(self):
        return False
