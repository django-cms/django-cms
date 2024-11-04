import warnings
from logging import getLogger
from os.path import join

from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Prefetch
from django.db.models.base import ModelState
from django.db.models.functions import Concat
from django.forms import model_to_dict
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import get_language, gettext_lazy as _, override as force_language
from treebeard.mp_tree import MP_Node

from cms import constants
from cms.exceptions import LanguageError
from cms.models.managers import PageManager, PageNodeManager, PageUrlManager
from cms.utils import i18n
from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
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
        return Page.objects.get(node=self)

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
        return super().add_sibling(*args, **kwargs)

    def update(self, **data):
        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(**data)

        for field, value in data.items():
            setattr(self, field, value)

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
    A ``Page`` is the basic unit of site structure in django CMS. The CMS uses a hierarchical page model: each page
    stands in relation to other pages as parent, child or sibling. This hierarchy is managed by the `django-treebeard
    <http://django-treebeard.readthedocs.io/en/latest/>`_ library.

    A ``Page`` also has language-specific properties - for example, it will have a title and a slug for each language
    it exists in. These properties are managed by the :class:`~cms.models.contentmodel.PageContent` model.
    """

    created_by = models.CharField(
        _("created by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    changed_by = models.CharField(
        _("changed by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    changed_date = models.DateTimeField(auto_now=True)

    #
    # Please use toggle_in_navigation() instead of affecting this property
    # directly so that the cms page cache can be invalidated as appropriate.
    #
    reverse_id = models.CharField(_("id"), max_length=40, db_index=True, blank=True, null=True, help_text=_(
        "A unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("attached menu"), max_length=80, db_index=True, blank=True, null=True)

    login_required = models.BooleanField(_("login required"), default=False)
    is_home = models.BooleanField(editable=False, db_index=True, default=False)
    application_urls = models.CharField(_('application'), max_length=200, blank=True, null=True, db_index=True)
    application_namespace = models.CharField(_('application instance name'), max_length=200, blank=True, null=True)
    languages = models.CharField(max_length=255, editable=False, blank=True, null=True)

    # Flag that marks a page as page-type
    is_page_type = models.BooleanField(default=False)

    node = models.ForeignKey(
        'TreeNode',
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
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        app_label = 'cms'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urls_cache = {}
        self.page_content_cache = {}
        self.admin_content_cache = {}

    def __str__(self):
        try:
            title = self.get_menu_title(fallback=True)
        except LanguageError:
            try:
                title = self.pagecontent_set(manager="admin_manager").current()[0]
            except IndexError:
                title = None
        if title is None:
            title = ""
        return force_str(title)

    def __repr__(self):
        display = f'<{self.__module__}.{self.__class__.__name__} id={self.pk} object at {hex(id(self))}>'
        return display

    def _clear_node_cache(self):
        if Page.node.is_cached(self):
            Page.node.field.delete_cached_value(self)

    def _clear_internal_cache(self):
        self.urls_cache = {}
        self.page_content_cache = {}
        self.admin_content_cache = {}
        self._clear_node_cache()

        if hasattr(self, '_prefetched_objects_cache'):
            del self._prefetched_objects_cache

    @cached_property
    def parent_page(self):
        return self.get_parent_page()

    def has_valid_url(self, language):
        return self.urls.filter(language=language, path__isnull=False).exists()

    def set_as_homepage(self, user=None):
        """
        Sets the given page as the homepage.
        Updates the url paths for all affected pages.
        Returns the old home page (if any).
        """
        if user:
            changed_by = get_clean_username(user)
        else:
            changed_by = constants.SCRIPT_USERNAME

        changed_date = now()

        try:
            old_home = self.__class__.objects.get(
                is_home=True,
                node__site=self.node.site_id,
            )
        except self.__class__.DoesNotExist:
            old_home_tree = []
        else:
            old_home.update(
                is_home=False,
                changed_by=changed_by,
                changed_date=changed_date,
            )
            old_home_tree = old_home._set_title_root_path()

        self.update(
            is_home=True,
            changed_by=changed_by,
            changed_date=changed_date,
        )
        new_home_tree = self._remove_title_root_path()
        return (new_home_tree, old_home_tree)

    def _get_path_sql_value(self, base_path=''):
        if base_path:
            new_path = Concat(
                models.Value(base_path),
                models.Value('/'),
                models.F('slug'),
                output_field=models.CharField(),
            )
        elif base_path is None:
            new_path = None
        else:
            # the homepage
            new_path = models.F('slug')
        return new_path

    def _update_url_path(self, language):
        parent_page = self.get_parent_page()
        base_path = parent_page.get_path(language) if parent_page else ''
        new_path = self._get_path_sql_value(base_path)

        (PageUrl
         .objects
         .filter(language=language, page=self)
         .exclude(managed=False)
         .update(path=new_path))  # TODO: Update or create?

    def _update_url_path_recursive(self, language):
        if self.node.is_leaf() or language not in self.get_languages():
            return

        pages = self.get_child_pages()
        base_path = self.get_path(language)
        new_path = self._get_path_sql_value(base_path)

        (PageUrl
         .objects
         .filter(language=language, page__in=pages)
         .exclude(managed=False)
         .update(path=new_path))  # TODO: Update or create?

        for child in pages.filter(urls__language=language).iterator():
            child._update_url_path_recursive(language)

    def _set_title_root_path(self):
        node_tree = TreeNode.get_tree(self.node)
        page_tree = self.__class__.objects.filter(node__in=node_tree)
        page_urls = PageUrl.objects.filter(page__in=page_tree, managed=True, path__isnull=False)

        for language, slug in self.urls.values_list('language', 'slug'):
            # Update the translations for all descendants of this page
            # to include this page's slug as its path prefix
            (page_urls
             .filter(language=language)
             .update(path=Concat(models.Value(slug), models.Value('/'), 'path')))
            self.update_urls(language, path=slug)
        return page_tree

    def _remove_title_root_path(self):
        node_tree = TreeNode.get_tree(self.node)
        page_tree = self.__class__.objects.filter(node__in=node_tree)
        page_urls = PageUrl.objects.filter(page__in=page_tree, managed=True, path__isnull=False)

        for language, slug in self.urls.values_list('language', 'slug'):
            # Use 2 because of 1 indexing plus the fact we need to trim
            # the "/" character.
            trim_count = len(slug) + 2
            sql_func = models.Func(
                models.F('path'),
                models.Value(trim_count),
                function='substr',
            )
            (page_urls
             .filter(language=language, path__startswith=slug)
             .update(path=sql_func))
        return page_tree

    def is_potential_home(self):
        """
        Encapsulates logic for determining if this page is eligible to be set
        as `is_home`. This is a public method so that it can be accessed in the
        admin for determining whether to enable the "Set as home" menu item.
        :return: Boolean
        """
        # Only root nodes are eligible for homepage
        return not self.is_home and bool(self.node.is_root())

    def get_absolute_url(self, language=None, fallback=True):
        if not language:
            language = get_current_language()

        with force_language(language):
            if self.is_home:
                return reverse('pages-root')
            path = self.get_path(language, fallback) or self.get_slug(language, fallback)  # TODO: Disallow get_slug
            return reverse('pages-details-by-slug', kwargs={"slug": path}) if path else None

    def set_tree_node(self, site, target=None, position='first-child'):
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
        assert isinstance(target_node, TreeNode)

        inherited_template = self.template == constants.TEMPLATE_INHERITANCE_MAGIC

        if inherited_template and target_node.is_root() and position in ('left', 'right'):
            # The page is being moved to a root position.
            # Explicitly set the inherited template on the titles
            # to keep all plugins / placeholders.
            template = self.get_template()
            self.update_translations(template=template)

        # Don't use a cached node. Always get a fresh one.
        self._clear_internal_cache()

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

        # Update the urls for the page being moved
        # and is descendants.
        languages = (
            self
            .urls
            .filter(language__in=self.get_languages())
            .values_list('language', flat=True)
        )

        for language in languages:
            if not self.is_home:
                self._update_url_path(language)
            self._update_url_path_recursive(language)
        self.clear_cache(menu=True)
        return self

    def _clear_placeholders(self, language):
        from cms.models import CMSPlugin

        placeholders = self.get_placeholders(language)
        placeholder_ids = (placeholder.pk for placeholder in placeholders)
        plugins = CMSPlugin.objects.filter(placeholder__in=placeholder_ids, language=language)
        models.query.QuerySet.delete(plugins)
        return placeholders

    def copy(self, site, parent_node=None, language=None,
             translations=True, permissions=False, extensions=True, user=None):
        from cms.models import PageContent
        from cms.utils.page import get_available_slug

        if not user:
            raise ValueError("Since django CMS 4 the page.copy method requires a user argument")

        if parent_node:
            new_node = parent_node.add_child(site=site)
            parent_page = parent_node.item
        else:
            new_node = TreeNode.add_root(site=site)
            parent_page = None

        new_page = model_to_dict(self)
        new_page.pop("id", None)  # Remove PK
        new_page["node"] = new_node
        # new_page["publisher_public_id"] = None
        new_page["is_home"] = False
        new_page["reverse_id"] = None
        new_page["languages"] = ""
        new_page = self.__class__.objects.create(**new_page)
        new_page._state = ModelState()
        new_page._clear_internal_cache()

        # Have the node remember its page.
        # This is done to save some queries
        # when the node's descendants are copied.
        new_page.node.__dict__['item'] = new_page

        if language and translations:
            page_urls = self.urls.filter(language=language)
            translations = self.pagecontent_set(manager="admin_manager").filter(language=language)
        elif translations:
            page_urls = self.urls.all()
            translations = self.pagecontent_set(manager="admin_manager")
        else:
            page_urls = self.urls.none()
            translations = self.pagecontent_set(manager="admin_manager").none()
        translations = translations.prefetch_related('placeholders')

        for page_url in page_urls:
            new_url = model_to_dict(page_url)
            new_url.pop("id", None)  # No PK
            new_url["page"] = new_page

            if parent_page:
                base = parent_page.get_path(page_url.language)
                path = '%s/%s' % (base, page_url.slug) if base else page_url.slug
            else:
                base = ''
                path = page_url.slug

            new_url["slug"] = get_available_slug(site, path, page_url.language)
            new_url["path"] = '%s/%s' % (base, new_url["slug"]) if base else new_url["slug"]
            PageUrl.objects.with_user(user).create(**new_url)

        # copy titles of this page
        for title in translations.current_content():
            new_title = model_to_dict(title)
            new_title.pop("id", None)  # No PK
            new_title["page"] = new_page
            new_title = PageContent.objects.with_user(user).create(**new_title)

            for placeholder in title.placeholders.all():
                # copy the placeholders (and plugins on those placeholders!)
                new_placeholder = new_title.placeholders.create(
                    slot=placeholder.slot,
                    default_width=placeholder.default_width,
                )
                placeholder.copy_plugins(new_placeholder, language=new_title.language)
            new_page.page_content_cache[new_title.language] = new_title
        new_page.update_languages([trans.language for trans in translations])

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
                              copy_permissions=True, target_site=None, user=None):
        """
        Copy a page [ and all its descendants to a new location ]
        """
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
        from cms.models import PageContent
        descendants = list(
            self.get_descendant_pages()
            .select_related('node')
            .prefetch_related(
                'urls',
                Prefetch('pagecontent_set', queryset=PageContent.admin_manager.all()),
            )
        )
        new_root_page = self.copy(target_site, parent_node=parent_node, user=user)
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
                user=user
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

        self.pagecontent_set(manager="admin_manager").filter(language__in=languages).delete()

    def save(self, **kwargs):
        if self.reverse_id == "":
            self.reverse_id = None
        if self.application_namespace == "":
            self.application_namespace = None

        created = not bool(self.pk)
        from cms.utils.permissions import get_current_user_name
        self.changed_by = get_current_user_name()
        if created:
            self.created_by = self.changed_by

        super().save(**kwargs)

    def update(self, refresh=False, **data):
        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(**data)

        if refresh:
            return self.reload()
        else:
            for field, value in data.items():
                setattr(self, field, value)
        return

    def update_translations(self, language=None, **data):
        if language:
            translations = self.pagecontent_set.filter(language=language)
        else:
            translations = self.pagecontent_set.all()
        return translations.update(**data)

    def has_translation(self, language):
        return self.pagecontent_set.filter(language=language).exists()

    def clear_cache(self, language=None, menu=False, placeholder=False):
        from cms.cache import invalidate_cms_page_cache

        if get_cms_setting('PAGE_CACHE'):
            # Clears all the page caches
            invalidate_cms_page_cache()

        if placeholder and get_cms_setting('PLACEHOLDER_CACHE'):
            assert language, 'language is required when clearing placeholder cache'

            placeholders = self.get_placeholders(language)

            for placeholder in placeholders:
                placeholder.clear_cache(language, site_id=self.node.site_id)

        if menu:
            # Clears all menu caches for this page's site
            menu_pool.clear(site_id=self.node.site_id)

    def get_child_pages(self):
        nodes = self.node.get_children()
        pages = (
            self
            .__class__
            .objects
            .filter(node__in=nodes)
            .order_by('node__path')
        )
        return pages

    def get_ancestor_pages(self):
        nodes = self.node.get_ancestors()
        pages = (
            self
            .__class__
            .objects
            .filter(node__in=nodes)
            .order_by('node__path')
        )
        return pages

    def get_descendant_pages(self):
        nodes = self.node.get_descendants()
        pages = (
            self
            .__class__
            .objects
            .filter(node__in=nodes)
            .order_by('node__path')
        )
        return pages

    def get_root(self):
        node = self.node
        return self.__class__.objects.get(node__path=node.path[0:node.steplen])

    def get_parent_page(self):
        if not self.node.parent_id:
            return None

        pages = Page.objects.filter(node=self.node.parent_id)
        return pages.select_related('node').first()

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
        languages = ",".join(set(languages))
        # Update current instance
        self.languages = languages
        # Commit. It's important to not call save()
        # we'd like to commit only the languages field and without
        # any kind of signals.
        self.update(languages=languages)

    def get_published_languages(self):
        return self.get_languages()

    def set_translations_cache(self):
        warnings.warn(
            "Method `set_translations_cache` is deprecated. Use `get_content_obj` instead. "
            "For admin views use `set_admin_content_cache` instead.",
            RemovedInDjangoCMS43Warning,
            stacklevel=2,
        )
        for translation in self.pagecontent_set.all():
            self.page_content_cache.setdefault(translation.language, translation)

    def set_admin_content_cache(self):
        for translation in self.pagecontent_set(manager="admin_manager").current_content().all():
            self.admin_content_cache.setdefault(translation.language, translation)

    def get_admin_content(self, language, fallback=False):
        from cms.models.contentmodels import EmptyPageContent

        if not self.admin_content_cache:
            self.set_admin_content_cache()
        page_content = self.admin_content_cache.get(language, EmptyPageContent(language=language, page=self))
        if not page_content and fallback:
            for lang in i18n.get_fallback_languages(language):
                page_content = self.admin_content_cache.get(lang)
                if page_content:
                    return page_content
            page_content = EmptyPageContent(language=language, page=self)
            if fallback == "force":
                # Try any page content object
                for item in self.admin_content_cache.values():
                    if item:
                        return item
        return page_content

    def get_path_for_slug(self, slug, language):
        if self.is_home:
            return ''

        if self.parent_page:
            base = self.parent_page.get_path(language, fallback=True)
            # base can be empty when the parent is a home-page
            path = '%s/%s' % (base, slug) if base else slug
        else:
            path = slug
        return path

    def get_url(self, language):
        return self.get_urls().get(language=language)

    def get_urls(self):
        return self.urls.all()

    def update_urls(self, language=None, **data):
        if language:
            page_urls = self.get_urls().filter(language=language)
        else:
            page_urls = self.get_urls().all()
        return page_urls.update(**data)

    def get_fallbacks(self, language):
        return i18n.get_fallback_languages(language, site_id=self.node.site_id)

    # ## PageContent object access

    def get_content_obj(self, language=None, fallback=True, force_reload=False):
        """Helper function for accessing wanted / current title.
        If wanted title doesn't exist, EmptyPageContent instance will be returned.
        """
        language = self._get_page_content_cache(language, fallback, force_reload)
        if language in self.page_content_cache:
            return self.page_content_cache[language]
        from cms.models import EmptyPageContent

        return EmptyPageContent(language=language, page=self)

    def get_page_content_obj_attribute(self, attrname, language=None, fallback=True, force_reload=False):
        """Helper function for getting attribute or None from wanted/current page content."""
        try:
            attribute = getattr(self.get_content_obj(language, fallback, force_reload), attrname)
            return attribute
        except AttributeError:
            return None

    def get_path(self, language, fallback=True):
        """Get the path of the page depending on the given language"""
        languages = [language]

        if fallback:
            languages.extend(self.get_fallbacks(language))

        page_languages = self.get_languages()

        for _language in languages:
            if _language in page_languages:
                language = _language
                break

        if language not in self.urls_cache:
            self.urls_cache.update({
                url.language: url for url in self.urls.filter(language__in=languages)  # TODO: overwrites multiple urls
            })

            for _language in languages:
                self.urls_cache.setdefault(_language, None)

        try:
            return self.urls_cache[language].path
        except (AttributeError, KeyError):
            return None

    def get_slug(self, language, fallback=True):
        languages = [language]

        if fallback:
            languages.extend(self.get_fallbacks(language))

        page_languages = self.get_languages()

        for _language in languages:
            if _language in page_languages:
                language = _language
                break

        if language not in self.urls_cache:
            self.urls_cache.update({
                url.language: url for url in self.urls.filter(language__in=languages)
            })

            for _language in languages:
                self.urls_cache.setdefault(_language, None)

        try:
            return self.urls_cache[language].slug
        except (AttributeError, KeyError):
            return None

    def get_title(self, language=None, fallback=True, force_reload=False):
        """
        get the title of the page depending on the given language
        """
        return self.get_page_content_obj_attribute("title", language, fallback, force_reload)

    def get_menu_title(self, language=None, fallback=True, force_reload=False):
        """
        get the menu title of the page depending on the given language
        """
        menu_title = self.get_page_content_obj_attribute("menu_title", language, fallback, force_reload)
        if not menu_title:
            return self.get_title(language, True, force_reload)
        return menu_title

    def get_placeholders(self, language):
        from cms.models import PageContent, Placeholder

        page_content = PageContent.objects.get(language=language, page=self)
        return Placeholder.objects.get_for_obj(page_content)

    def get_changed_date(self, language=None, fallback=True, force_reload=False):
        """
        get when this page was last updated
        """
        return self.get_page_content_obj_attribute("changed_date", language, fallback, force_reload)

    def get_changed_by(self, language=None, fallback=True, force_reload=False):
        """
        get user who last changed this page
        """
        return self.get_page_content_obj_attribute("changed_by", language, fallback, force_reload)

    def get_page_title(self, language=None, fallback=True, force_reload=False):
        """
        get the page title of the page depending on the given language
        """
        page_title = self.get_page_content_obj_attribute("page_title", language, fallback, force_reload)

        if not page_title:
            return self.get_title(language, True, force_reload)
        return page_title

    def get_meta_description(self, language=None, fallback=True, force_reload=False):
        """
        get content for the description meta tag for the page depending on the given language
        """
        return self.get_page_content_obj_attribute("meta_description", language, fallback, force_reload)

    def get_application_urls(self, language=None, fallback=True, force_reload=False):
        """
        get application urls conf for application hook
        """
        return self.application_urls

    def get_redirect(self, language=None, fallback=True, force_reload=False):
        """
        get redirect
        """
        return self.get_page_content_obj_attribute("redirect", language, fallback, force_reload)

    def _get_page_content_cache(self, language, fallback, force_reload):
        def get_fallback_language(page, language):
            fallback_langs = i18n.get_fallback_languages(language)
            for lang in fallback_langs:
                if page.page_content_cache.get(lang):
                    return lang

        if not language:
            language = get_language()

        # Update page_content_cache from _prefetched_objects_cache if available
        prefetch_cache = getattr(self, "_prefetched_objects_cache", {})
        cached_page_content = prefetch_cache.get("pagecontent_set", [])
        for page_content in cached_page_content:
            self.page_content_cache[page_content.language] = page_content

        # Reload if explicitly needed or language not in content cache
        if force_reload or language not in self.page_content_cache:
            for page_content in self.pagecontent_set.all():
                self.page_content_cache[page_content.language] = page_content

        if self.page_content_cache.get(language):
            return language

        use_fallback = all([
            fallback,
            not self.page_content_cache.get(language),
            get_fallback_language(self, language)
        ])
        if use_fallback:
            # language can be in the cache but might be an EmptyPageContent instance
            return get_fallback_language(self, language)
        return language

    @property
    def template(self):
        return self.get_page_content_obj_attribute("template")

    @property
    def soft_root(self):
        return self.get_page_content_obj_attribute("soft_root")

    def get_template(self, language=None, fallback=True, force_reload=False):
        content = self.get_content_obj(language, fallback, force_reload)
        if content:
            return content.get_template()
        return get_cms_setting('TEMPLATES')[0][0]

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
            restrictions = (
                PagePermission
                .objects
                .for_page(self)
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
        from cms.utils.page_permissions import user_can_change_page_advanced_settings
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

    def rescan_placeholders(self, language):
        return self.get_content_obj(language=language).rescan_placeholders()

    def get_declared_placeholders(self):
        # inline import to prevent circular imports
        from cms.utils.placeholder import get_placeholders

        return get_placeholders(self.get_template())

    def get_xframe_options(self, language=None, fallback=True, force_reload=False):
        title = self.get_content_obj(language, fallback, force_reload)
        if title:
            return title.get_xframe_options()

    def get_soft_root(self, language=None, fallback=True, force_reload=False):
        return self.get_page_content_obj_attribute("soft_root", language, fallback, force_reload)

    def get_in_navigation(self, language=None, fallback=True, force_reload=False):
        return self.get_page_content_obj_attribute("in_navigation", language, fallback, force_reload)

    def get_limit_visibility_in_menu(self, language=None, fallback=True, force_reload=False):
        return self.get_page_content_obj_attribute("limit_visibility_in_menu", language, fallback, force_reload)


class PageUrl(models.Model):
    slug = models.SlugField(_("slug"), max_length=255, db_index=True)
    path = models.CharField(_("Path"), max_length=255, db_index=True, null=True)
    language = models.CharField(_("language"), max_length=15, db_index=True)
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        verbose_name=_("page"),
        related_name="urls",
    )
    managed = models.BooleanField(default=False)
    objects = PageUrlManager()

    class Meta:
        app_label = 'cms'
        default_permissions = []

    def __str__(self):
        return "%s (%s)" % (self.path or self.slug, self.language)

    def get_absolute_url(self, language=None, fallback=True):
        if not language:
            language = get_current_language()

        with force_language(language):
            if self.path == '':
                return reverse('pages-root')
            return reverse('pages-details-by-slug', kwargs={"slug": self.path})

    def get_path_for_base(self, base_path=''):
        old_base, sep, slug = self.path.rpartition('/')
        return '%s/%s' % (base_path, slug) if base_path else slug


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
